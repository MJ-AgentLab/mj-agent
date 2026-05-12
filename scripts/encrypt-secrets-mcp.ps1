<#
.SYNOPSIS
    Encrypt secrets-mcp.conf into secrets-mcp.enc for mj-agent (MCP secrets bundle)

.DESCRIPTION
    Encrypts config/secrets-mcp.conf into config/secrets-mcp.enc using
    AES-256-CBC with PBKDF2. The encrypted file is safe to commit
    to the repository.

    Per ADR-030 bundle split: this is the parallel of encrypt-secrets.ps1
    for the MCP-only secrets bundle. The team-shared password is the SAME
    one used for secrets.enc (so team members only need to remember one
    password); two separate .enc files exist for trust-boundary isolation,
    not for password isolation.

    After encrypting, delete secrets-mcp.conf and (if password rotated)
    share the new password with the team through a secure channel.

.EXAMPLE
    .\scripts\encrypt-secrets-mcp.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Locate project root ──────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# ── Paths ─────────────────────────────────────────────────────────────
$ConfFile = Join-Path $ProjectRoot "config\secrets-mcp.conf"
$EncFile  = Join-Path $ProjectRoot "config\secrets-mcp.enc"

# ── Pre-flight checks ────────────────────────────────────────────────
if (-not (Test-Path $ConfFile)) {
    Write-Host "[ERROR] $ConfFile not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "To create it:" -ForegroundColor White
    Write-Host "  1. Copy config\secrets-mcp.example -> config\secrets-mcp.conf" -ForegroundColor White
    Write-Host "  2. Fill in all values" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    exit 1
}

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

# ── Password prompt (double input) ───────────────────────────────────
Write-Host ""
Write-Host "mj-agent — Encrypt MCP Secrets (ADR-030)" -ForegroundColor Cyan
Write-Host ("-" * 60)

$SecurePassword1 = Read-Host "Enter encryption password (same as secrets.enc)" -AsSecureString
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
Write-Host "[Done] Encrypted successfully: config\secrets-mcp.enc" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. git add config\secrets-mcp.enc" -ForegroundColor White
Write-Host "  2. Delete config\secrets-mcp.conf (NEVER commit plaintext)" -ForegroundColor White
Write-Host "  3. If password rotated, share new password via secure channel" -ForegroundColor White
Write-Host ("=" * 60)
