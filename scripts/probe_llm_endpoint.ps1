<#
.SYNOPSIS
  Sanitized 4-step probe for the local-openai-compat LLM endpoint (mj-agent).

.DESCRIPTION
  Reads .env internally (LLM_PROVIDER / LLM_BASE_URL / LLM_MODEL_ID /
  LLM_API_KEY) and performs the ADR-027 consumer-side healthcheck:
    STEP1 reachability via GET /models (Ollama /api/tags fallback)
    STEP2 model-id match against the endpoint's loaded models
    STEP3 1-token chat completion smoke (no extra_body)
    STEP3B tool-calling smoke - auto tool choice first, then one named
           tool_choice discriminating retry (parser missing vs model unable)
  Output is sanitized: key names, PASS/FAIL/WARN per step and truncated
  response snippets only - credential values are never printed. Agents of any
  harness must call this script instead of reading .env / process env to
  assemble requests themselves (dual-agent-compat plan section 5.2).

.OUTPUTS
  Report lines "STEPn PASS|FAIL|WARN|NOT-APPLICABLE ...".
  Exit 0 = all pass (or not applicable); exit 3 = pass with tool-calling
  warning; exit 2 = config missing; exit 1 = probe failure.
#>
[CmdletBinding()]
param(
    [string]$EnvFile = ".env",
    [int]$TimeoutSec = 30
)

$ErrorActionPreference = "Stop"

function Read-DotEnv([string]$Path) {
    $map = @{}
    if (Test-Path $Path) {
        foreach ($line in Get-Content $Path) {
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$') {
                $map[$Matches[1]] = $Matches[2].Trim().Trim('"')
            }
        }
    }
    return $map
}

function Invoke-Curl([string[]]$CurlArgs) {
    # Native stderr under -ErrorActionPreference Stop throws in Windows
    # PowerShell 5.1 when redirected; relax locally for the curl call.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $out = & curl.exe -sS -m $TimeoutSec @CurlArgs 2>&1
        return [pscustomobject]@{
            Ok   = ($LASTEXITCODE -eq 0)
            Text = (($out | Out-String)).Trim()
        }
    } finally {
        $ErrorActionPreference = $prevEap
    }
}

function Get-Snippet([string]$Text, [int]$Max = 160) {
    if ($Text.Length -le $Max) { return $Text }
    return $Text.Substring(0, $Max) + "..."
}

# ---- STEP0: config (sanitized: only set|EMPTY for the key) -----------------
$dotenv   = Read-DotEnv $EnvFile
$provider = if ($dotenv["LLM_PROVIDER"]) { $dotenv["LLM_PROVIDER"] } else { "ark" }
$baseUrl  = $dotenv["LLM_BASE_URL"]
$modelId  = $dotenv["LLM_MODEL_ID"]
$apiKey   = $dotenv["LLM_API_KEY"]   # local scope only; never printed

Write-Output "STEP0 CONFIG LLM_PROVIDER=$provider"
if ($provider -ne "local-openai-compat") {
    Write-Output "STEP0 NOT-APPLICABLE probe targets local-openai-compat only (ark is covered by 'mj-agent check')"
    exit 0
}
if (-not $baseUrl) { Write-Output "STEP0 FAIL LLM_BASE_URL EMPTY/MISSING"; exit 2 }
if (-not $modelId) { Write-Output "STEP0 FAIL LLM_MODEL_ID EMPTY/MISSING"; exit 2 }
$keyState = if ($apiKey) { "set" } else { "EMPTY" }
Write-Output "STEP0 PASS LLM_BASE_URL=$baseUrl LLM_MODEL_ID=$modelId LLM_API_KEY=$keyState"

$authArgs = @()
if ($apiKey) { $authArgs = @("-H", "Authorization: Bearer $apiKey") }

# ---- STEP1: reachability + /models (Ollama fallback) -----------------------
$models = Invoke-Curl (@("$baseUrl/models") + $authArgs)
$modelIds = @()
if ($models.Ok) {
    try {
        $json = $models.Text | ConvertFrom-Json
        if ($json.data) { $modelIds = @($json.data | ForEach-Object { $_.id }) }
    } catch { $models.Ok = $false }
}
if (-not $models.Ok -and $baseUrl -match ":11434") {
    $baseHost = $baseUrl -replace "/v1/?$", ""
    $tags = Invoke-Curl @("$baseHost/api/tags")
    if ($tags.Ok) {
        try {
            $json = $tags.Text | ConvertFrom-Json
            $modelIds = @($json.models | ForEach-Object { $_.name })
            $models = $tags
        } catch { }
    }
}
if (-not $models.Ok) {
    Write-Output ("STEP1 FAIL endpoint unreachable or non-JSON: " + (Get-Snippet $models.Text))
    exit 1
}
Write-Output ("STEP1 PASS models endpoint reachable (" + $modelIds.Count + " model(s) loaded)")

# ---- STEP2: model id match --------------------------------------------------
if ($modelIds -contains $modelId) {
    Write-Output "STEP2 PASS LLM_MODEL_ID matches a loaded model"
} else {
    Write-Output ("STEP2 FAIL LLM_MODEL_ID not in loaded models: [" + ($modelIds -join ", ") + "]")
    exit 1
}

# ---- STEP3: 1-token chat smoke (no extra_body) ------------------------------
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("mj-agent-probe-" + [IO.Path]::GetRandomFileName() + ".json")
try {
    $chatBody = @{
        model      = $modelId
        messages   = @(@{ role = "user"; content = "hi" })
        max_tokens = 1
    } | ConvertTo-Json -Depth 6 -Compress
    [IO.File]::WriteAllText($tmp, $chatBody)
    $chat = Invoke-Curl (@("$baseUrl/chat/completions", "-H", "Content-Type: application/json", "-d", "@$tmp") + $authArgs)
    $chatOk = $false
    if ($chat.Ok) {
        try {
            $cj = $chat.Text | ConvertFrom-Json
            if ($cj.choices -and $cj.choices[0].message) { $chatOk = $true }
        } catch { }
    }
    if (-not $chatOk) {
        Write-Output ("STEP3 FAIL chat smoke: " + (Get-Snippet $chat.Text))
        exit 1
    }
    Write-Output "STEP3 PASS 1-token chat completion returned choices[0].message"

    # ---- STEP3B: tool-calling smoke (auto, then named discriminating retry) --
    $toolDef = @{
        type     = "function"
        function = @{
            name        = "get_current_time"
            description = "Get the current time in a given IANA timezone"
            parameters  = @{
                type       = "object"
                properties = @{ timezone = @{ type = "string"; description = "IANA timezone name, e.g. Asia/Shanghai" } }
                required   = @("timezone")
            }
        }
    }
    $toolMessages = @(@{
        role    = "user"
        content = "What time is it in Asia/Shanghai? You MUST call the provided tool; do not answer directly."
    })

    function Test-ToolCall([hashtable]$Body) {
        $payload = $Body | ConvertTo-Json -Depth 10 -Compress
        [IO.File]::WriteAllText($tmp, $payload)
        $resp = Invoke-Curl (@("$baseUrl/chat/completions", "-H", "Content-Type: application/json", "-d", "@$tmp") + $authArgs)
        if (-not $resp.Ok) { return $false }
        try {
            $rj = $resp.Text | ConvertFrom-Json
            $choice = $rj.choices[0]
            if ($choice.finish_reason -ne "tool_calls") { return $false }
            $call = $choice.message.tool_calls[0]
            if ($call.function.name -ne "get_current_time") { return $false }
            $parsedArgs = $call.function.arguments | ConvertFrom-Json
            return [bool]$parsedArgs.timezone
        } catch { return $false }
    }

    $autoBody = @{
        model       = $modelId
        messages    = $toolMessages
        tools       = @($toolDef)
        temperature = 0.1
        max_tokens  = 128
    }
    if (Test-ToolCall $autoBody) {
        Write-Output "STEP3B PASS auto tool choice: finish_reason=tool_calls + parseable arguments"
        Write-Output "VERDICT PASS all steps green - 'mj-agent serve' should work with this endpoint"
        exit 0
    }

    $namedBody = $autoBody.Clone()
    $namedBody["tool_choice"] = @{ type = "function"; function = @{ name = "get_current_time" } }
    if (Test-ToolCall $namedBody) {
        Write-Output "STEP3B WARN auto failed but named tool_choice passed - endpoint tool parser missing (vLLM: --enable-auto-tool-choice --tool-call-parser <family>)"
        Write-Output "VERDICT WARN pass with tool-calling warning - mj-agent runtime NOT usable until parser enabled"
        exit 3
    }
    Write-Output "STEP3B WARN auto and named both failed - model lacks tool-calling (mj-agent ALL_TOOLS hard dependency; change model via dgx-mlops HITL-MODEL)"
    Write-Output "VERDICT WARN pass with tool-calling warning - model not suitable for mj-agent"
    exit 3
} finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
}
