# guard-git-workflow.ps1 - PreToolUse hook for mj-agent Git workflow rules.
#
# Enforces:
#   Rule G1: 'git checkout -b/-B' / 'git switch -c/-C' forbidden (use 'git worktree add').
#   Rule G2: 'gh pr create' must specify --base / -B (non-hotfix -> develop, hotfix -> main).
#   Input protocol (fail-closed, dual-agent-compat v5 section 5.4): non-JSON, empty,
#   missing-field or unknown-schema stdin is REJECTED with exit 2 - a payload the
#   guard cannot parse must never be silently allowed.
#
# The rules are tool-neutral (they bind any agent whose harness wires this hook);
# Codex runs under its own harness and self-enforces the same G1/G2 rules via
# AGENTS.md prose (ADR-035).
#
# See:
#   CLAUDE.md "Repo conventions" / AGENTS.md (Git workflow discipline)
#   policies/git-branching.md (G1/G2 canonical rules)
#   .claude/skills/mj-agent-git-pr/SKILL.md          (G2 HARD REQUIREMENT)
#   .claude/skills/mj-agent-git-branch/SKILL.md      (G1 HARD REQUIREMENT)
#   plans/[PLAN]_g1_g2_workflow_enforcement.md       (root cause analysis)
#   plans/[PLAN]_dual-agent-compat_p0.md             (fail-closed + G1 tightening, PR-2)
#   tests/unit/test_guard_git_workflow_hook.py       (contract fixtures)
#
# Wired in .claude/settings.json -> hooks.PreToolUse[matcher=Bash].
# Exit codes: 0 = allow, 2 = block with stderr shown to the agent.
# NOTE: running this script manually without a valid hook payload on stdin
# exits 2 by design (fail-closed); that is not a defect.

$ErrorActionPreference = 'Stop'

function Deny-Payload([string]$Reason) {
    [Console]::Error.WriteLine("[GUARD FAIL-CLOSED] $Reason")
    [Console]::Error.WriteLine('Expected PreToolUse JSON on stdin: {"tool_name":"Bash","hook_event_name":"PreToolUse","tool_input":{"command":"..."}}')
    exit 2
}

function Deny-G1 {
    [Console]::Error.WriteLine("[G1 VIOLATION] 'git checkout -b/-B' / 'git switch -c/-C' is forbidden.")
    [Console]::Error.WriteLine("Use 'git worktree add' instead for new branches:")
    [Console]::Error.WriteLine("  git worktree add ../<branch-name> -b <branch-name>")
    [Console]::Error.WriteLine("See policies/git-branching.md (G1), CLAUDE.md / AGENTS.md, and .claude/skills/mj-agent-git-branch/SKILL.md.")
    exit 2
}

function Deny-G2 {
    [Console]::Error.WriteLine("[G2 VIOLATION] 'gh pr create' requires explicit --base.")
    [Console]::Error.WriteLine("  Non-hotfix branches: --base develop")
    [Console]::Error.WriteLine("  Hotfix branches:     --base main")
    [Console]::Error.WriteLine("See policies/git-branching.md (G2), CLAUDE.md / AGENTS.md, and .claude/skills/mj-agent-git-pr/SKILL.md.")
    exit 2
}

try {
    # #317: read stdin as UTF-8 explicitly. [Console]::In follows the inherited
    # console codepage (CP936 on Chinese Windows), which mis-decodes the UTF-8
    # hook payload and made the fail-closed guard mis-block every command
    # containing non-ASCII text. Claude Code always emits UTF-8 JSON.
    $reader = New-Object System.IO.StreamReader(
        [Console]::OpenStandardInput(),
        (New-Object System.Text.UTF8Encoding($false))
    )
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { Deny-Payload 'empty stdin' }

    $payload = $null
    try { $payload = $raw | ConvertFrom-Json } catch { Deny-Payload 'non-JSON stdin' }
    if ($null -eq $payload) { Deny-Payload 'null/empty JSON payload' }

    if ($payload.tool_name -ne 'Bash') { Deny-Payload "unknown schema: tool_name is not 'Bash'" }
    if ($payload.hook_event_name -ne 'PreToolUse') { Deny-Payload "unknown schema: hook_event_name is not 'PreToolUse'" }

    $cmd = $payload.tool_input.command
    if (-not $cmd) { Deny-Payload 'missing tool_input.command' }

    # Token-based per-segment analysis: split on shell separators so that
    # 'cd x && git checkout -b y' is caught while 'echo git checkout -b' and
    # 'git commit -m "... checkout -b ..."' are not (subcommand position check).
    $segments = $cmd -split '(?:\|\||&&|;|\||&|\r?\n)'
    foreach ($segment in $segments) {
        $tokens = @($segment.Trim() -split '\s+' | Where-Object { $_ })
        if ($tokens.Count -lt 2) { continue }

        if ($tokens[0] -eq 'git') {
            # Locate the git subcommand, skipping global options (value-taking
            # ones consume the following token).
            $valueOpts = @('-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path')
            $i = 1
            while ($i -lt $tokens.Count) {
                $t = $tokens[$i]
                if ($valueOpts -contains $t) { $i += 2; continue }
                if ($t.StartsWith('-')) { $i += 1; continue }
                break
            }
            if ($i -ge $tokens.Count) { continue }
            $sub = $tokens[$i]
            $rest = @($tokens | Select-Object -Skip ($i + 1))
            if ($sub -eq 'checkout' -and (($rest -contains '-b') -or ($rest -contains '-B'))) { Deny-G1 }
            if ($sub -eq 'switch' -and (($rest -contains '-c') -or ($rest -contains '-C'))) { Deny-G1 }
        }

        if ($tokens[0] -eq 'gh' -and $tokens.Count -ge 3 -and $tokens[1] -eq 'pr' -and $tokens[2] -eq 'create') {
            $rest = @($tokens | Select-Object -Skip 3)
            $hasBase = $false
            foreach ($t in $rest) {
                if ($t -eq '--base' -or $t -like '--base=*' -or $t -ceq '-B' -or $t -clike '-B=*') { $hasBase = $true; break }
            }
            if (-not $hasBase) { Deny-G2 }
        }
    }

    exit 0
} catch {
    # Unexpected internal errors must not fall through to allow (fail-closed).
    [Console]::Error.WriteLine("[GUARD FAIL-CLOSED] internal error: $($_.Exception.Message)")
    exit 2
}
