<#
.SYNOPSIS
    Sync .mcp.json-referenced env vars from .env to User-level OS env.

.DESCRIPTION
    Reads <project-root>/.env and <project-root>/.mcp.json. Auto-derives
    the set of ${VAR} references from .mcp.json (handling :-default
    fallbacks) and pushes the matching values from .env to
    HKCU\Environment via [Environment]::SetEnvironmentVariable(..., 'User').

    No file written, no decryption — purely .env-derived OS env mirror
    for Claude Code MCP variable substitution. Mirror of the mj-system
    setup-sys-ops-env.ps1 pattern, adapted to read .env (already
    decrypted by scripts/setup-env.ps1) instead of running a parallel
    encryption pipeline.

    Workflow:
        secrets.enc -[scripts/setup-env.ps1]-> .env
                   -[.claude/scripts/setup-mcp-env.ps1]-> User OS env
                   -[docker compose env_file]-> mj-agent container
                   -[pydantic-settings]-> Python runtime

    .env stays canonical for Docker / Python; this script ONLY adds an
    OS env mirror for the subset referenced by .mcp.json so claude code
    MCP variable substitution can resolve at startup.

.PARAMETER Force
    Skip per-key confirmation when overwriting existing User-level env
    vars with different values.

.PARAMETER Reload
    Skip writes; report current OS env state against the
    .mcp.json-derived expected list. Useful for diagnosing why /doctor
    still complains.

.EXAMPLE
    .\.claude\scripts\setup-mcp-env.ps1
    .\.claude\scripts\setup-mcp-env.ps1 -Force
    .\.claude\scripts\setup-mcp-env.ps1 -Reload
#>

param(
    [switch]$Force,
    [switch]$Reload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Locate paths (in-tree mode: <repo>/.claude/scripts/)
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$EnvFile     = Join-Path $ProjectRoot ".env"
$McpFile     = Join-Path $ProjectRoot ".mcp.json"

# Helpers (ported from mj-system setup-sys-ops-env.ps1 L74-97)
function Format-MaskedValue([string]$Value) {
    if ($Value.Length -le 4) { return "****" }
    return $Value.Substring(0, 4) + "****"
}

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

# Auto-derive ${VAR} references from .mcp.json.
# Handles both ${VAR} and ${VAR:-fallback} forms, dedups, returns sorted.
function Read-McpVarRefs([string]$Path) {
    $content = Get-Content $Path -Raw -Encoding UTF8
    $regex = [regex]'\$\{([A-Z_][A-Z0-9_]*)(?::-[^}]*)?\}'
    $refs = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($m in $regex.Matches($content)) {
        [void]$refs.Add($m.Groups[1].Value)
    }
    return $refs | Sort-Object
}

# Header
Write-Host ""
Write-Host "MJ-Agent MCP Env Sync (.env -> User OS env)" -ForegroundColor Cyan
Write-Host ("-" * 60)

# Reload mode: report current OS env state against .mcp.json refs
if ($Reload) {
    if (-not (Test-Path $McpFile)) {
        Write-Host "[ERROR] $McpFile not found." -ForegroundColor Red
        exit 1
    }
    $expected = Read-McpVarRefs $McpFile
    Write-Host "[Reload] Checking User-level OS env vars vs .mcp.json refs ($($expected.Count) total)" -ForegroundColor Yellow
    $set = 0
    $missing = 0
    foreach ($key in $expected) {
        $val = [Environment]::GetEnvironmentVariable($key, "User")
        if ($null -eq $val) {
            Write-Host "  [MISSING] $key" -ForegroundColor Red
            $missing++
        } else {
            Write-Host "  [SET]     $key = $(Format-MaskedValue $val)" -ForegroundColor Green
            $set++
        }
    }
    Write-Host ("=" * 60)
    Write-Host "[Done] $set / $($expected.Count) set, $missing missing." -ForegroundColor Cyan
    if ($missing -gt 0) {
        Write-Host "Run without -Reload to sync from .env." -ForegroundColor White
    }
    return
}

# Default mode: read .env, sync .mcp.json-referenced subset to User env
if (-not (Test-Path $EnvFile)) {
    Write-Host "[ERROR] $EnvFile not found. Run scripts/setup-env.ps1 first." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $McpFile)) {
    Write-Host "[ERROR] $McpFile not found." -ForegroundColor Red
    exit 1
}

$envVars = Read-EnvFile $EnvFile
$expected = Read-McpVarRefs $McpFile

Write-Host "Syncing $($expected.Count) .mcp.json-referenced vars from .env to User OS env:" -ForegroundColor White
$wrote = 0
$skipped = 0
$absent = 0
foreach ($key in $expected) {
    if (-not $envVars.ContainsKey($key)) {
        Write-Host "  [ABSENT]  $key - not in .env (skip)" -ForegroundColor DarkYellow
        $absent++
        continue
    }
    $newVal = $envVars[$key]
    $oldVal = [Environment]::GetEnvironmentVariable($key, "User")
    if ($null -ne $oldVal -and $oldVal -eq $newVal) {
        Write-Host "  [SKIP]    $key = $(Format-MaskedValue $newVal)" -ForegroundColor DarkGray
        $skipped++
        continue
    }
    if ($null -ne $oldVal -and -not $Force) {
        $confirm = Read-Host "[CHANGED] $key - overwrite? [y/N]"
        if ($confirm -notin @('y', 'Y', 'yes', 'Yes')) {
            Write-Host "  [SKIP]    $key (kept old value)" -ForegroundColor DarkGray
            $skipped++
            continue
        }
    }
    [Environment]::SetEnvironmentVariable($key, $newVal, "User")
    $marker = if ($null -eq $oldVal) { "[NEW]    " } else { "[CHANGED]" }
    Write-Host "  $marker $key = $(Format-MaskedValue $newVal)" -ForegroundColor Green
    $wrote++
}

Write-Host ("=" * 60)
Write-Host "[Done] $wrote wrote, $skipped skipped, $absent absent in .env." -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Restart terminal / IDE so User env vars take effect (current PS won't see new values)." -ForegroundColor White
Write-Host "  2. Restart claude code; /doctor should report 0 'Missing environment variables'." -ForegroundColor White
Write-Host "  3. After rotating .env (re-run setup-env.ps1), re-run this script." -ForegroundColor White
