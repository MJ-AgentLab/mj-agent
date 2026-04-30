<#
.SYNOPSIS
    Encrypt secrets.conf into secrets.enc for mj-agent

.DESCRIPTION
    Encrypts config/secrets.conf into config/secrets.enc using
    AES-256-CBC with PBKDF2. The encrypted file is safe to commit
    to the repository.

    After encrypting, delete secrets.conf and share the password
    with the team through a secure channel.

.EXAMPLE
    .\scripts\encrypt-secrets.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Locate project root ──────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# ── Paths ─────────────────────────────────────────────────────────────
$ConfFile = Join-Path $ProjectRoot "config\secrets.conf"
$EncFile  = Join-Path $ProjectRoot "config\secrets.enc"

# ── Pre-flight checks ────────────────────────────────────────────────
if (-not (Test-Path $ConfFile)) {
    Write-Host "[ERROR] $ConfFile not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "To create it:" -ForegroundColor White
    Write-Host "  1. Copy config\secrets.example -> config\secrets.conf" -ForegroundColor White
    Write-Host "  2. Fill in all values" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
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

# ── Password prompt (double input) ───────────────────────────────────
Write-Host ""
Write-Host "mj-agent — Encrypt Secrets" -ForegroundColor Cyan
Write-Host ("-" * 60)

$SecurePassword1 = Read-Host "Enter encryption password" -AsSecureString
$SecurePassword2 = Read-Host "Confirm encryption password" -AsSecureString

$Password1 = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword1))
$Password2 = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword2))

if ($Password1 -ne $Password2) {
    Write-Host "[ERROR] Passwords do not match." -ForegroundColor Red
    exit 1
}
$Password = $Password1

# ── Encrypt ───────────────────────────────────────────────────────────
$Password | & $OpenSSL enc -aes-256-cbc -pbkdf2 -md sha256 -salt -in $ConfFile -out $EncFile -pass stdin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Encryption failed." -ForegroundColor Red
    exit 1
}

# ── Summary ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host ("=" * 60)
Write-Host "[Done] Encrypted successfully: config\secrets.enc" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. git add config\secrets.enc" -ForegroundColor White
Write-Host "  2. Delete config\secrets.conf (NEVER commit plaintext)" -ForegroundColor White
Write-Host "  3. Share the password with the team via a secure channel" -ForegroundColor White
Write-Host ("=" * 60)
