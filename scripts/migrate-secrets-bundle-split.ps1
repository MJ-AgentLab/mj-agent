<#
.SYNOPSIS
    ONE-TIME migration: split legacy secrets.enc into secrets.enc + secrets-mcp.enc (ADR-030)

.DESCRIPTION
    Prior to ADR-030, all mj-agent secrets (app + MCP infrastructure) lived
    in a single config/secrets.enc bundle. ADR-030 splits these into two
    trust-boundary-isolated bundles:
      - config/secrets.enc       (app: analyst pg / memory pg / ARK / LangSmith)
      - config/secrets-mcp.enc   (MCP: 5 SSH passwords + 10 PG URLs)

    This script is a ONE-TIME migration helper that:
      1. Decrypts the legacy 17-key secrets.enc with the team password
      2. Splits keys into APP_KEYS (6) and MCP_KEYS (15) sets
      3. Re-encrypts each set with the same team password
      4. Writes new secrets.enc (overwrite) + new secrets-mcp.enc
      5. Cleans up temp files

    After running, the team admin commits both new .enc files and notifies
    the team. Existing team members then pull, run setup-env.ps1 (gets the
    6 app secrets) + setup-mcp-secrets.ps1 (gets the 15 MCP secrets into OS env).

    AFTER MIGRATION the script is no longer needed and can be removed in a
    follow-up cleanup PR.

.PARAMETER DryRun
    Decrypt the legacy bundle and print key-set composition without writing
    new .enc files. Useful for verifying the split before committing.

.EXAMPLE
    .\scripts\migrate-secrets-bundle-split.ps1
    .\scripts\migrate-secrets-bundle-split.ps1 -DryRun
#>

param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Locate project root ──────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# ── Paths ─────────────────────────────────────────────────────────────
$LegacyEnc     = Join-Path $ProjectRoot "config\secrets.enc"
$LegacyConf    = Join-Path $ProjectRoot "config\secrets.conf"
$AppEnc        = Join-Path $ProjectRoot "config\secrets.enc"      # overwrite
$AppConf       = Join-Path $ProjectRoot "config\secrets.conf"
$McpEnc        = Join-Path $ProjectRoot "config\secrets-mcp.enc"
$McpConf       = Join-Path $ProjectRoot "config\secrets-mcp.conf"

# ── Key partition ─────────────────────────────────────────────────────
# Per ADR-030: app = identity / data layer; MCP = infrastructure secrets.
$AppKeys = @(
    "POSTGRES_ANALYST_USER",
    "POSTGRES_ANALYST_PASSWORD",
    "ARK_API_KEY",
    "LLM_API_KEY",
    "LANGSMITH_API_KEY",
    "MJ_AGENT_MEMORY_USER",
    "MJ_AGENT_MEMORY_PASSWORD",
    "MJ_AGENT_REDIS_PASSWORD"
)
$McpKeys = @(
    "MJ_AGENT_SSH_SERVER_CLOUD_PASSWORD",
    "MJ_AGENT_SSH_SERVER_RUNNER_PASSWORD",
    "MJ_AGENT_SSH_SERVER_TEST_PASSWORD",
    "MJ_AGENT_SSH_SERVER_PROD_PASSWORD",
    "MJ_AGENT_SSH_SERVER_DGX_PASSWORD",
    "MJ_AGENT_PG_MEMORY_DEV_URL",
    "MJ_AGENT_PG_MEMORY_TEST_LAN_URL",
    "MJ_AGENT_PG_MEMORY_TEST_WAN_URL",
    "MJ_AGENT_PG_MEMORY_PROD_LAN_URL",
    "MJ_AGENT_PG_MEMORY_PROD_WAN_URL",
    "MJ_AGENT_PG_BIZ_DEV_URL",
    "MJ_AGENT_PG_BIZ_TEST_LAN_URL",
    "MJ_AGENT_PG_BIZ_TEST_WAN_URL",
    "MJ_AGENT_PG_BIZ_PROD_LAN_URL",
    "MJ_AGENT_PG_BIZ_PROD_WAN_URL"
)

# ── Pre-flight ────────────────────────────────────────────────────────
if (-not (Test-Path $LegacyEnc)) {
    Write-Host "[ERROR] $LegacyEnc not found. Cannot run migration without legacy bundle." -ForegroundColor Red
    exit 1
}
if (-not $DryRun -and (Test-Path $McpEnc)) {
    Write-Host "[WARN] $McpEnc already exists. This script will overwrite it." -ForegroundColor Yellow
    $confirm = Read-Host "Continue? [y/N]"
    if ($confirm -notin @("y", "Y", "yes", "Yes")) {
        Write-Host "[ABORT] No changes made." -ForegroundColor Yellow
        exit 0
    }
}

# ── OpenSSL lookup ────────────────────────────────────────────────────
function Find-OpenSSL {
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

# ── Helpers ───────────────────────────────────────────────────────────
function Read-EnvFile([string]$Path) {
    $vars = [ordered]@{}
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

# ── Password prompt ───────────────────────────────────────────────────
Write-Host ""
Write-Host "mj-agent — Bundle Split Migration (ADR-030)" -ForegroundColor Cyan
Write-Host ("-" * 60)
Write-Host "This script splits the legacy 1-bundle secrets.enc into 2 bundles:" -ForegroundColor White
Write-Host "  - secrets.enc     (app: 6-8 keys)" -ForegroundColor White
Write-Host "  - secrets-mcp.enc (MCP: 15 keys)" -ForegroundColor White
Write-Host "Both .enc files use the SAME team password." -ForegroundColor White
Write-Host ""

$SecurePassword = Read-Host "Enter team decryption password" -AsSecureString
$Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword))

# ── Decrypt legacy bundle ─────────────────────────────────────────────
try {
    $Password | & $OpenSSL enc -aes-256-cbc -pbkdf2 -md sha256 -d -in $LegacyEnc -out $LegacyConf -pass stdin 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Decryption failed" }

    $Secrets = Read-EnvFile $LegacyConf
    if ($Secrets.Count -eq 0) {
        Write-Host "[ERROR] No secrets found in decrypted legacy bundle." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Decrypted legacy bundle: $($Secrets.Count) keys" -ForegroundColor Green

    # ── Partition keys ────────────────────────────────────────────────
    $AppPartition = [ordered]@{}
    $McpPartition = [ordered]@{}
    $Unknown = @()

    foreach ($k in $Secrets.Keys) {
        if ($AppKeys -contains $k) {
            $AppPartition[$k] = $Secrets[$k]
        } elseif ($McpKeys -contains $k) {
            $McpPartition[$k] = $Secrets[$k]
        } else {
            $Unknown += $k
        }
    }

    Write-Host ""
    Write-Host "Partition result:" -ForegroundColor White
    Write-Host "  App bundle: $($AppPartition.Count) keys" -ForegroundColor Cyan
    foreach ($k in $AppPartition.Keys) { Write-Host "    - $k" -ForegroundColor DarkCyan }
    Write-Host "  MCP bundle: $($McpPartition.Count) keys" -ForegroundColor Cyan
    foreach ($k in $McpPartition.Keys) { Write-Host "    - $k" -ForegroundColor DarkCyan }
    if ($Unknown.Count -gt 0) {
        Write-Host "  Unknown (will be kept in app bundle as safety net): $($Unknown.Count) keys" -ForegroundColor Yellow
        foreach ($k in $Unknown) {
            Write-Host "    - $k" -ForegroundColor Yellow
            $AppPartition[$k] = $Secrets[$k]
        }
    }

    if ($DryRun) {
        Write-Host ""
        Write-Host "[DRY RUN] Stopped before writing .enc files." -ForegroundColor Yellow
        return
    }

    # ── Write app .conf ───────────────────────────────────────────────
    $appLines = @("# Auto-generated by migrate-secrets-bundle-split.ps1 (ADR-030)")
    foreach ($k in $AppPartition.Keys) { $appLines += "$k=$($AppPartition[$k])" }
    [System.IO.File]::WriteAllText($AppConf, ($appLines -join "`n"), [System.Text.UTF8Encoding]::new($false))

    # ── Write mcp .conf ───────────────────────────────────────────────
    $mcpLines = @("# Auto-generated by migrate-secrets-bundle-split.ps1 (ADR-030)")
    foreach ($k in $McpPartition.Keys) { $mcpLines += "$k=$($McpPartition[$k])" }
    [System.IO.File]::WriteAllText($McpConf, ($mcpLines -join "`n"), [System.Text.UTF8Encoding]::new($false))

    # ── Encrypt app bundle (overwrite legacy secrets.enc) ─────────────
    $Password | & $OpenSSL enc -aes-256-cbc -pbkdf2 -md sha256 -salt -in $AppConf -out $AppEnc -pass stdin 2>&1
    if ($LASTEXITCODE -ne 0) { throw "App bundle encryption failed" }
    Write-Host ""
    Write-Host "[OK] Re-encrypted app bundle: $AppEnc ($($AppPartition.Count) keys)" -ForegroundColor Green

    # ── Encrypt mcp bundle ────────────────────────────────────────────
    $Password | & $OpenSSL enc -aes-256-cbc -pbkdf2 -md sha256 -salt -in $McpConf -out $McpEnc -pass stdin 2>&1
    if ($LASTEXITCODE -ne 0) { throw "MCP bundle encryption failed" }
    Write-Host "[OK] Created MCP bundle:        $McpEnc ($($McpPartition.Count) keys)" -ForegroundColor Green

    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "[Done] Bundle split complete." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps (team admin):" -ForegroundColor White
    Write-Host "  1. git add config\secrets.enc config\secrets-mcp.enc" -ForegroundColor White
    Write-Host "  2. git commit (no plaintext .conf will be staged — see .gitignore)" -ForegroundColor White
    Write-Host "  3. Push and notify team to pull + run setup-env.ps1 + setup-mcp-secrets.ps1" -ForegroundColor White
    Write-Host ("=" * 60)

} catch {
    Write-Host "[ERROR] Migration failed: $_" -ForegroundColor Red
    exit 1
} finally {
    foreach ($f in @($LegacyConf, $AppConf, $McpConf)) {
        if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
    }
}
