<#
Native project MCP maintenance candidate. Default: decrypt the existing MCP bundle
and update only its six allowed User environment variables. -Reload reports presence.
Neither mode imports user/plugin MCP definitions or application credentials.
Execution is a separate Owner-approved action; P1 validates code with synthetic data.
#>
param([switch]$Force, [switch]$Reload)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$AllowedKeys = @('GITHUB_PERSONAL_ACCESS_TOKEN', 'MJ_AGENT_PG_MEMORY_DEV_URL',
    'MJ_AGENT_PG_MEMORY_TEST_LAN_URL', 'MJ_AGENT_PG_MEMORY_TEST_WAN_URL',
    'MJ_AGENT_PG_MEMORY_PROD_LAN_URL', 'MJ_AGENT_PG_MEMORY_PROD_WAN_URL')

function Format-MaskedValue([string]$Value) { return '[REDACTED]' }

function ConvertFrom-McpEnv([string[]]$Lines) {
    $values = @{}
    foreach ($line in $Lines) {
        $item = $line.Trim()
        if (-not $item -or $item.StartsWith('#')) { continue }
        $index = $item.IndexOf('=')
        if ($index -lt 1) { continue }
        $key = $item.Substring(0, $index).Trim()
        if ($key -cnotin $AllowedKeys) { continue }
        $value = $item.Substring($index + 1).Trim()
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'")))) { $value = $value.Substring(1, $value.Length - 2) }
        if ($value) { $values[$key] = $value }
    }
    return $values
}

function Find-OpenSSL {
    $gitCommand = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCommand) {
        $directory = Split-Path $gitCommand.Source
        for ($i = 0; $i -lt 4 -and $directory; $i++) {
            $candidate = Join-Path $directory 'usr/bin/openssl.exe'
            if (Test-Path -LiteralPath $candidate) { return $candidate }
            $directory = Split-Path $directory
        }
    }
    $command = Get-Command openssl -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw 'OpenSSL unavailable'
}

if (-not $IsWindows) { [Console]::Error.WriteLine('[ERROR] Windows User environment required'); exit 2 }
if ($Reload) {
    foreach ($key in $AllowedKeys) {
        $value = [Environment]::GetEnvironmentVariable($key, 'User')
        if ([string]::IsNullOrWhiteSpace($value)) { Write-Host "[MISSING] $key" }
        else { Write-Host "[SET] $key [REDACTED]" }
    }
    return
}

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$bundle = Join-Path $projectRoot 'config/secrets-mcp.enc'
$pointer = [IntPtr]::Zero
$password = $null
$plaintext = $null
$values = $null
try {
    if (-not (Test-Path -LiteralPath $bundle)) { throw 'Missing MCP bundle' }
    $openssl = Find-OpenSSL
    $secure = Read-Host 'Enter team decryption password' -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    # Keep plaintext in memory; never create or overwrite a plaintext .conf/.env.
    $plaintext = $password | & $openssl enc -aes-256-cbc -pbkdf2 -md sha256 -d -in $bundle -pass stdin 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Decryption failed' }
    $values = ConvertFrom-McpEnv $plaintext
    if ($values.Count -eq 0) { throw 'No project MCP values' }
    foreach ($key in $AllowedKeys) {
        if (-not $values.ContainsKey($key)) { Write-Host "[MISSING] $key"; continue }
        $oldValue = [Environment]::GetEnvironmentVariable($key, 'User')
        if ($oldValue -ceq $values[$key]) { Write-Host "[SKIP] $key [REDACTED]"; continue }
        if ($null -ne $oldValue -and -not $Force) {
            $answer = Read-Host "Overwrite $key? [y/N]"
            if ($answer -notin @('y', 'yes')) { Write-Host "[SKIP] $key"; continue }
        }
        [Environment]::SetEnvironmentVariable($key, $values[$key], 'User')
        Write-Host "[SET] $key [REDACTED]"
    }
    Write-Host 'Restart Codex to inherit updated variables; verify each project MCP separately.'
} catch {
    [Console]::Error.WriteLine('[ERROR] MCP setup failed; inspect prerequisites without logging secrets')
    exit 1
} finally {
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    $password = $null
    $plaintext = $null
    $values = $null
}
