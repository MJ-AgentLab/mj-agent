<#
.SYNOPSIS
  Sanitized .env key-presence check for mj-agent infra skills.

.DESCRIPTION
  Reads .env locally and reports ONLY key names with PRESENT / EMPTY / MISSING
  status - sanitized output, values are never echoed (dual-agent-compat plan
  section 5.2: scripts return missing key names, boolean status and sanitized
  diagnostics; agents of any harness must call this script instead of parsing
  .env themselves).

.PARAMETER EnvFile
  Path to the .env file (default: ./.env).

.PARAMETER Keys
  Extra keys to check in addition to the provider-aware default set.

.OUTPUTS
  One line per key: "PRESENT <key>" / "EMPTY <key>" / "MISSING <key>".
  Exit 0 when all checked keys are PRESENT; exit 1 otherwise.
#>
[CmdletBinding()]
param(
    [string]$EnvFile = ".env",
    [string[]]$Keys = @()
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $EnvFile)) {
    Write-Output "MISSING-FILE $EnvFile (run scripts/setup-env.ps1 first)"
    exit 1
}

# Parse KEY=VALUE pairs; values stay in local scope and are never printed.
$pairs = @{}
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$') {
        $pairs[$Matches[1]] = $Matches[2].Trim().Trim('"')
    }
}

$provider = if ($pairs.ContainsKey("LLM_PROVIDER") -and $pairs["LLM_PROVIDER"]) {
    $pairs["LLM_PROVIDER"]
} else { "ark" }
Write-Output "INFO LLM_PROVIDER resolved: $provider"

$requiredSecrets = @("POSTGRES_ANALYST_USER", "POSTGRES_ANALYST_PASSWORD")
switch ($provider) {
    "ark"                 { $requiredSecrets += "ARK_API_KEY" }
    "local-openai-compat" { $requiredSecrets += "LLM_BASE_URL" }
}
$requiredPlain = @(
    "MJ_CONFIG_PROFILE", "POSTGRES_DEV_HOST", "POSTGRES_DEV_PORT",
    "LLM_MODEL_ID", "LLM_PROVIDER", "NO_PROXY"
)

$failed = $false
$allKeys = @($requiredSecrets + $requiredPlain + $Keys | Select-Object -Unique)
foreach ($k in $allKeys) {
    if (-not $pairs.ContainsKey($k)) {
        Write-Output "MISSING $k"
        $failed = $true
    } elseif (-not $pairs[$k]) {
        Write-Output "EMPTY $k"
        $failed = $true
    } else {
        Write-Output "PRESENT $k"
    }
}

if ($failed) { exit 1 } else { exit 0 }
