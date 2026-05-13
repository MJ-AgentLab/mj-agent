# guard-git-workflow.ps1 - PreToolUse hook for mj-agent.
#
# Enforces:
#   Rule G1: 'git checkout -b' / 'git switch -c' forbidden (use 'git worktree add').
#   Rule G2: 'gh pr create' must specify --base / -B (non-hotfix -> develop, hotfix -> main).
#
# See:
#   CLAUDE.md "Repo conventions"
#   .claude/skills/mj-agent-git-pr/SKILL.md          (G2 HARD REQUIREMENT)
#   .claude/skills/mj-agent-git-branch/SKILL.md      (G1 HARD REQUIREMENT)
#   plans/[PLAN]_g1_g2_workflow_enforcement.md       (root cause analysis)
#
# Wired in .claude/settings.json -> hooks.PreToolUse[matcher=Bash].
# Exit codes: 0 = allow, 2 = block with stderr shown to the agent.

$ErrorActionPreference = 'Stop'

try {
    $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
} catch {
    # Non-JSON stdin -> not a Claude Code hook invocation; never block.
    exit 0
}

$cmd = $payload.tool_input.command
if (-not $cmd) { exit 0 }

# --- Rule G2: gh pr create without --base / -B ---
if ($cmd -match '(^|[\s;&|])gh\s+pr\s+create\b' -and `
    $cmd -notmatch '(^|\s)(--base|-B)(\s|=)') {
    [Console]::Error.WriteLine("[G2 VIOLATION] 'gh pr create' requires explicit --base.")
    [Console]::Error.WriteLine("  Non-hotfix branches: --base develop")
    [Console]::Error.WriteLine("  Hotfix branches:     --base main")
    [Console]::Error.WriteLine("See CLAUDE.md Rule G2 and .claude/skills/mj-agent-git-pr/SKILL.md.")
    exit 2
}

# --- Rule G1: git checkout -b / git switch -c (new branch without worktree) ---
if ($cmd -match '(^|[\s;&|])git\s+checkout\s+-[bB]\b' -or `
    $cmd -match '(^|[\s;&|])git\s+switch\s+-[cC]\b') {
    [Console]::Error.WriteLine("[G1 VIOLATION] 'git checkout -b/-B' / 'git switch -c/-C' is forbidden.")
    [Console]::Error.WriteLine("Use 'git worktree add' instead for new branches:")
    [Console]::Error.WriteLine("  git worktree add ../<branch-name> -b <branch-name>")
    [Console]::Error.WriteLine("See CLAUDE.md Rule G1 and .claude/skills/mj-agent-git-branch/SKILL.md.")
    exit 2
}

exit 0
