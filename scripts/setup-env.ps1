<#
.SYNOPSIS
    Decrypt secrets and generate .env for mj-agent

.DESCRIPTION
    Decrypts config/secrets.enc using a team-shared password,
    then merges the secrets into .env (copied from .env.example).

    The decrypted secrets.conf is automatically deleted after use.
    All variables present in secrets.conf are injected into .env
    (replacing matching keys in .env.example); remaining .env.example
    values are preserved as-is.

    If .env already exists and -Force is not specified, the script
    compares each variable and asks for confirmation before overwriting.

.PARAMETER Force
    Overwrite .env without confirmation even if it already exists

.EXAMPLE
    .\scripts\setup-env.ps1
    .\scripts\setup-env.ps1 -Force
#>

param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Locate project root ──────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Verify we are inside the mj-agent project
if (-not (Test-Path (Join-Path $ProjectRoot "pyproject.toml"))) {
    Write-Host "[ERROR] pyproject.toml not found in $ProjectRoot — script must live in scripts/." -ForegroundColor Red
    exit 1
}

# ── Paths ─────────────────────────────────────────────────────────────
$EncFile      = Join-Path $ProjectRoot "config\secrets.enc"
$ConfFile     = Join-Path $ProjectRoot "config\secrets.conf"
$EnvExample   = Join-Path $ProjectRoot ".env.example"
$EnvFile      = Join-Path $ProjectRoot ".env"

# ── Pre-flight checks ────────────────────────────────────────────────
if (-not (Test-Path $EncFile)) {
    Write-Host "[ERROR] $EncFile not found. Ask the team admin for the encrypted file." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $EnvExample)) {
    Write-Host "[ERROR] $EnvExample not found." -ForegroundColor Red
    exit 1
}

# ── OpenSSL lookup ────────────────────────────────────────────────────
function Find-OpenSSL {
    # Prefer Git for Windows' OpenSSL — standard build, consistent behavior.
    # Anaconda/conda OpenSSL in PATH can cause "bad decrypt" due to build differences.
    # 1. Derive from git.exe location (works for any Git install path)
    #    git.exe may be at <root>/cmd/, <root>/bin/, or <root>/mingw64/bin/
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $dir = Split-Path $gitCmd.Source
        for ($i = 0; $i -lt 4; $i++) {
            $candidate = Join-Path $dir "usr\bin\openssl.exe"
            if (Test-Path $candidate) { return $candidate }
            $dir = Split-Path $dir
        }
    }
    # 2. Last resort: PATH (may find Anaconda — known to cause issues)
    $cmd = Get-Command openssl -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    Write-Host "[ERROR] openssl not found. Install Git for Windows or add openssl to PATH." -ForegroundColor Red
    exit 1
}
$OpenSSL = Find-OpenSSL
Write-Host "  Using OpenSSL: $OpenSSL" -ForegroundColor DarkGray

# ── Helper: mask value for display ────────────────────────────────────
function Format-MaskedValue([string]$Value) {
    if ($Value.Length -le 4) { return "****" }
    return $Value.Substring(0, 4) + "****"
}

# ── Password prompt ───────────────────────────────────────────────────
Write-Host ""
Write-Host "mj-agent — .env Setup" -ForegroundColor Cyan
Write-Host ("-" * 60)

$SecurePassword = Read-Host "Enter team decryption password" -AsSecureString
$Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword))

# ── Decrypt ───────────────────────────────────────────────────────────
try {
    $Password | & $OpenSSL enc -aes-256-cbc -pbkdf2 -md sha256 -d -in $EncFile -out $ConfFile -pass stdin 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Decryption failed" }

    # ── Parse secrets.conf ────────────────────────────────────────────
    $Secrets = @{}
    foreach ($line in Get-Content $ConfFile -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
        $eqIdx = $trimmed.IndexOf("=")
        if ($eqIdx -gt 0) {
            $key = $trimmed.Substring(0, $eqIdx).Trim()
            $val = $trimmed.Substring($eqIdx + 1).Trim()
            # Strip surrounding quotes if present
            if (($val.StartsWith("'") -and $val.EndsWith("'")) -or
                ($val.StartsWith('"') -and $val.EndsWith('"'))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            $Secrets[$key] = $val
        }
    }

    if ($Secrets.Count -eq 0) {
        Write-Host "[ERROR] No secrets found in decrypted file." -ForegroundColor Red
        exit 1
    }

    Write-Host "[OK] Decrypted $($Secrets.Count) secrets." -ForegroundColor Green

    # ── Existing .env comparison ──────────────────────────────────────
    if ((Test-Path $EnvFile) -and -not $Force) {
        Write-Host ""
        Write-Host "Existing .env detected — comparing variables:" -ForegroundColor Yellow

        # Parse existing .env
        $ExistingVars = @{}
        foreach ($line in Get-Content $EnvFile -Encoding UTF8) {
            $trimmed = $line.Trim()
            if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
            $eqIdx = $trimmed.IndexOf("=")
            if ($eqIdx -gt 0) {
                $key = $trimmed.Substring(0, $eqIdx).Trim()
                $val = $trimmed.Substring($eqIdx + 1).Trim()
                if (($val.StartsWith("'") -and $val.EndsWith("'")) -or
                    ($val.StartsWith('"') -and $val.EndsWith('"'))) {
                    $val = $val.Substring(1, $val.Length - 2)
                }
                $ExistingVars[$key] = $val
            }
        }

        $Changes = @()
        foreach ($key in $Secrets.Keys | Sort-Object) {
            $newVal = $Secrets[$key]
            if ($ExistingVars.ContainsKey($key)) {
                $oldVal = $ExistingVars[$key]
                if ($oldVal -eq $newVal) {
                    Write-Host "  [SKIP]    $key = $(Format-MaskedValue $newVal)" -ForegroundColor DarkGray
                } else {
                    Write-Host "  [CHANGED] $key = $(Format-MaskedValue $oldVal) -> $(Format-MaskedValue $newVal)" -ForegroundColor Yellow
                    $Changes += $key
                }
            } else {
                Write-Host "  [NEW]     $key = $(Format-MaskedValue $newVal)" -ForegroundColor Green
                $Changes += $key
            }
        }

        if ($Changes.Count -eq 0) {
            Write-Host ""
            Write-Host "[SKIP] .env is already up-to-date. No changes needed." -ForegroundColor DarkGray
            return
        }

        Write-Host ""
        $confirm = Read-Host "Overwrite .env with $($Changes.Count) change(s)? [y/N]"
        if ($confirm -notin @("y", "Y", "yes", "Yes")) {
            Write-Host "[ABORT] No changes made." -ForegroundColor Yellow
            return
        }
    }

    # ── Generate .env ─────────────────────────────────────────────────
    # Start from .env.example as the template
    $envContent = Get-Content $EnvExample -Raw -Encoding UTF8

    $injectedCount = 0
    foreach ($key in $Secrets.Keys) {
        $val = $Secrets[$key]
        # Regex replace: match the key line regardless of current value
        $pattern = "(?m)^$([regex]::Escape($key))=.*$"
        if ($envContent -match $pattern) {
            $envContent = $envContent -replace $pattern, "$key=$val"
            $injectedCount++
        } else {
            Write-Host "  [WARN] $key not found in .env.example — appending." -ForegroundColor Yellow
            $envContent = $envContent.TrimEnd() + "`n$key=$val`n"
            $injectedCount++
        }
    }

    # Write .env (UTF-8 no BOM)
    [System.IO.File]::WriteAllText($EnvFile, $envContent, [System.Text.UTF8Encoding]::new($false))

    # ── Summary ───────────────────────────────────────────────────────
    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "[Done] .env generated with $injectedCount secrets injected." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Review .env and adjust POSTGRES_DEV_HOST / MJ_CONFIG_PROFILE if needed" -ForegroundColor White
    Write-Host "  2. uv sync" -ForegroundColor White
    Write-Host "  3. uv run langgraph dev" -ForegroundColor White
    Write-Host ("=" * 60)

} catch {
    Write-Host "[ERROR] Decryption failed — wrong password or corrupted file." -ForegroundColor Red
    exit 1
} finally {
    if (Test-Path $ConfFile) { Remove-Item $ConfFile -Force }
}
