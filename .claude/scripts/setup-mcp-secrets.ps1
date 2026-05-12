<#
.SYNOPSIS
    Decrypt secrets-mcp.enc and set OS environment variables for mj-agent MCP servers

.DESCRIPTION
    Decrypts config/secrets-mcp.enc using a team-shared password and sets each
    variable as a User-level OS environment variable (HKCU\Environment). The
    decrypted secrets-mcp.conf is deleted immediately after use.

    No .env file is written — all MCP secrets live only as User-level OS env
    vars. This is the canonical injection path for `.mcp.json` ${VAR}
    substitution (read by claude.exe at startup).

    Mirrors mj-system's setup-sys-ops-env.ps1 pattern (per ADR-030 bundle split;
    aligns mj-agent with mj-system v2.3 secrets injection model). Supersedes
    the deleted `.claude/scripts/setup-mcp-env.ps1` which mirrored .env to OS
    env — that path is no longer needed because MCP secrets are now in their
    own .enc and never land in .env.

    Two modes:
      Default  — decrypt -> set OS env vars (no file is written)
      -Reload  — report current OS env var state against config/secrets-mcp.example
                 (no password needed; checks which expected vars are SET vs MISSING)

.PARAMETER Force
    Skip confirmation prompts when overwriting existing OS env vars.

.PARAMETER Reload
    Skip decryption; report current OS env var state against secrets-mcp.example.

.EXAMPLE
    .\.claude\scripts\setup-mcp-secrets.ps1
    .\.claude\scripts\setup-mcp-secrets.ps1 -Force
    .\.claude\scripts\setup-mcp-secrets.ps1 -Reload
#>

param(
    [switch]$Force,
    [switch]$Reload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Locate project root (in-tree skills mode) ─────────────────────────
# This script lives at <repo>/.claude/scripts/ ; project root is two levels up.
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# ── Paths ─────────────────────────────────────────────────────────────
$EncFile     = Join-Path $ProjectRoot "config\secrets-mcp.enc"
$ConfFile    = Join-Path $ProjectRoot "config\secrets-mcp.conf"
$ExampleFile = Join-Path $ProjectRoot "config\secrets-mcp.example"

# ── OpenSSL lookup ────────────────────────────────────────────────────
function Find-OpenSSL {
    # Prefer Git for Windows' OpenSSL — standard build, consistent behavior.
    # Anaconda/conda OpenSSL in PATH can cause "bad decrypt" due to build differences.
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $dir = Split-Path $gitCmd.Source
        for ($i = 0; $i -lt 4; $i++) {
            $candidate = Join-Path $dir "usr\bin\openssl.exe"
            if (Test-Path $candidate) { return $candidate }
            $dir = Split-Path $dir
        }
    }
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

# ── Helper: parse KEY=VALUE file into hashtable ───────────────────────
function Read-EnvFile([string]$Path) {
    $vars = @{}
    foreach ($line in Get-Content $Path -Encoding UTF8) {
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
            $vars[$key] = $val
        }
    }
    return $vars
}

# ── Helper: extract KEY list from .example (ignores values) ───────────
function Read-ExampleKeys([string]$Path) {
    $keys = @()
    foreach ($line in Get-Content $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
        $eqIdx = $trimmed.IndexOf("=")
        if ($eqIdx -gt 0) { $keys += $trimmed.Substring(0, $eqIdx).Trim() }
    }
    return $keys
}

# ── Header ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "MJ-Agent MCP Secrets — Environment Setup (ADR-030)" -ForegroundColor Cyan
Write-Host ("-" * 60)

# ══════════════════════════════════════════════════════════════════════
# Reload mode: report current OS env var state against .example
# ══════════════════════════════════════════════════════════════════════
if ($Reload) {
    if (-not (Test-Path $ExampleFile)) {
        Write-Host "[ERROR] $ExampleFile not found." -ForegroundColor Red
        exit 1
    }

    Write-Host "[Reload] Checking OS env vars against $ExampleFile" -ForegroundColor Yellow
    $expected = Read-ExampleKeys $ExampleFile

    $setCount = 0
    $missingCount = 0
    foreach ($key in $expected | Sort-Object) {
        $val = [Environment]::GetEnvironmentVariable($key, "User")
        if ($null -eq $val) {
            Write-Host "  [MISSING] $key" -ForegroundColor Red
            $missingCount++
        } else {
            Write-Host "  [SET]     $key = $(Format-MaskedValue $val)" -ForegroundColor Green
            $setCount++
        }
    }

    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "[Done] $setCount / $($expected.Count) OS env vars set ($missingCount missing)." -ForegroundColor Cyan
    if ($missingCount -gt 0) {
        Write-Host "Run without -Reload to decrypt and set missing variables." -ForegroundColor White
    }
    Write-Host ("=" * 60)
    return
}

# ══════════════════════════════════════════════════════════════════════
# Default mode: decrypt -> set OS env vars (no .env written)
# ══════════════════════════════════════════════════════════════════════
if (-not (Test-Path $EncFile)) {
    Write-Host "[ERROR] $EncFile not found. Ask the team admin for the encrypted file." -ForegroundColor Red
    exit 1
}

# ── Password prompt ───────────────────────────────────────────────────
$SecurePassword = Read-Host "Enter team decryption password" -AsSecureString
$Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword))

# ── Decrypt ───────────────────────────────────────────────────────────
try {
    $Password | & $OpenSSL enc -aes-256-cbc -pbkdf2 -md sha256 -d -in $EncFile -out $ConfFile -pass stdin 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Decryption failed" }

    # ── Parse secrets ─────────────────────────────────────────────────
    $Secrets = Read-EnvFile $ConfFile

    if ($Secrets.Count -eq 0) {
        Write-Host "[ERROR] No secrets found in decrypted file." -ForegroundColor Red
        exit 1
    }

    Write-Host "[OK] Decrypted $($Secrets.Count) MCP secrets." -ForegroundColor Green

    # ── Set OS env vars (no .env file written) ────────────────────────
    Write-Host ""
    Write-Host "Setting OS environment variables (User level):" -ForegroundColor White
    $setCount = 0
    $changedCount = 0
    foreach ($key in $Secrets.Keys | Sort-Object) {
        $newVal = $Secrets[$key]
        $oldVal = [Environment]::GetEnvironmentVariable($key, "User")

        if ($null -eq $oldVal) {
            Write-Host "  [NEW]     $key = $(Format-MaskedValue $newVal)" -ForegroundColor Green
            $changedCount++
        } elseif ($oldVal -eq $newVal) {
            Write-Host "  [SKIP]    $key = $(Format-MaskedValue $newVal)" -ForegroundColor DarkGray
        } else {
            if (-not $Force) {
                $confirm = Read-Host "[CHANGED] $key — overwrite? [y/N]"
                if ($confirm -notin @("y", "Y", "yes", "Yes")) {
                    Write-Host "  [SKIP]    $key (kept old value)" -ForegroundColor DarkGray
                    continue
                }
            }
            Write-Host "  [CHANGED] $key = $(Format-MaskedValue $oldVal) -> $(Format-MaskedValue $newVal)" -ForegroundColor Yellow
            $changedCount++
        }
        [Environment]::SetEnvironmentVariable($key, $newVal, "User")
        $setCount++
    }

    # ── Summary ───────────────────────────────────────────────────────
    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "[Done] OS env vars set: $setCount processed ($changedCount written)." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Restart terminal / IDE / Claude Code for OS env vars to take effect." -ForegroundColor White
    Write-Host "     (Windows User-level env vars are only visible to newly-launched processes.)" -ForegroundColor DarkGray
    Write-Host "  2. Verify with claude /doctor (expect 0 'Missing environment variables')." -ForegroundColor White
    Write-Host "  3. Use -Reload to recheck OS env var state later (no password needed)." -ForegroundColor White
    Write-Host ("=" * 60)

} catch {
    Write-Host "[ERROR] Decryption failed — wrong password or corrupted file." -ForegroundColor Red
    exit 1
} finally {
    if (Test-Path $ConfFile) { Remove-Item $ConfFile -Force }
}
