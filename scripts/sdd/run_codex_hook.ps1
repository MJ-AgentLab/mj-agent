# Direct-maintained project hook bootstrap; P1 candidate, not activated.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.codex/hooks.json'))) { throw 'Missing root' }
    & uv --directory $repoRoot run --frozen --no-sync python (Join-Path $PSScriptRoot 'codex_hook_guard.py')
    if ($LASTEXITCODE -ne 0) { throw 'Handler failure' }
} catch {
    [Console]::Out.WriteLine('{"decision":"block","reason":"UNKNOWN: native hook bootstrap failed"}')
}
