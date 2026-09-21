# Windows project MCP launcher. Only variable NAMES cross the command line.
param([Parameter(Mandatory=$true)][string]$VariableName)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$allowed = @('MJ_AGENT_PG_MEMORY_DEV_URL', 'MJ_AGENT_PG_MEMORY_TEST_LAN_URL',
    'MJ_AGENT_PG_MEMORY_TEST_WAN_URL', 'MJ_AGENT_PG_MEMORY_PROD_LAN_URL', 'MJ_AGENT_PG_MEMORY_PROD_WAN_URL')
if ($VariableName -cnotin $allowed) { [Console]::Error.WriteLine('[REJECTED] unknown MCP variable'); exit 2 }
if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($VariableName, 'Process'))) {
    [Console]::Error.WriteLine("[MISSING] $VariableName"); exit 3
}
try {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
    $wrapper = Join-Path $PSScriptRoot 'pg-server-wrapper.mjs'
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.codex/config.toml')) -or
        -not (Test-Path -LiteralPath $wrapper)) { throw 'Missing project files' }
    # Resolve the npx package's bin from PATH; do not delete or repair global caches.
    $discover = 'const fs=require("fs"),p=require("path");for(const d of process.env.PATH.split(p.delimiter)){const b=p.join(d,"mcp-server-postgres");if(fs.existsSync(b)){const n=p.dirname(d);if(fs.existsSync(p.join(n,"pg","package.json"))){console.log(n);process.exit(0)}}}process.exit(1)'
    $moduleRoot = & npx.cmd -y -p '@modelcontextprotocol/server-postgres' node -e $discover 2>$null
    if ($LASTEXITCODE -ne 0 -or @($moduleRoot).Count -ne 1 -or
        -not (Test-Path -LiteralPath (Join-Path $moduleRoot 'pg/package.json'))) { throw 'Package unavailable' }
    $env:NODE_PATH = $moduleRoot
    & node $wrapper $VariableName
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine('[ERROR] project PG MCP launch failed; verify installed dependencies'); exit 1
}
