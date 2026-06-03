# .claude/hooks/stop-claude-md-improver/on-stop.ps1
#
# Phase M0 skeleton — placeholder. Phase M2 will implement the actual analysis.
#
# Contract (per README.md):
#   1. Read recent HITL gate triggers / command failures / scope-drift signals
#      from the current Claude Code session
#   2. Diff against root CLAUDE.md + 4 subdir CLAUDE.md
#   3. Write proposed update draft to:
#        evidence/ai-context-audit/<YYYY-MM-DD>_session_<id>_proposed_claude_md_update.md
#   4. Exit 0 always (advisory; never blocks Stop event)
#
# DO NOT have this script auto-Edit CLAUDE.md or auto-commit. The output is a
# draft for user review; mj-agent-doc-sync skill applies it at Phase 末.
#
# Phase M0 behavior: print a stub line + exit 0.
# Stage D D-1b augment (2026-05-21): prepend bypass + allowlist/denylist defense
# function. The stubbed body (Write-Host x2 + exit 0) is unchanged; defense
# function `Test-PathAllowed` is defined for use by M3-FU-A2-HOOK-IMPROVER-BODY
# real body (M4 deferred).

# Bypass 双通道 (OR logic; 任一触发即 short-circuit exit 0)
if ($env:CLAUDE_MD_IMPROVER_SKIP -eq '1') { exit 0 }
$sentinel = Join-Path $PSScriptRoot '..\..\.skip-claude-md-improver'
if (Test-Path $sentinel) { exit 0 }

# Write 路径 allowlist (per existing draft-producer 设计 commit 550e46b)
$WriteAllowlist = @(
    'evidence/ai-context-audit/*_session_*_proposed_claude_md_update.md'
)

# Write 路径 denylist (defense-in-depth; deny 优先)
$WriteDenylist = @(
    # 10 必停 surface (per policies/ai-agent.md §4 + sdd/gates.md §4)
    'src/mj_agent/skills/safe-sql-analysis/SKILL.md',
    'src/mj_agent/skills/biz-domain-context/SKILL.md',
    'src/mj_agent/skills/qcm-analysis/SKILL.md',
    'src/mj_agent/prompts/system.md',
    '.claude/skills/mj-agent-infra-docker-compose/SKILL.md',
    '.claude/skills/mj-agent-infra-env-setup/SKILL.md',
    '.claude/skills/mj-agent-infra-env-teardown/SKILL.md',
    '.claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md',
    '.claude/skills/mj-agent-infra-storage-stack/SKILL.md',
    '.claude/skills/mj-agent-infra-studio-probe/SKILL.md',
    # root + subdir CLAUDE.md (现 design 明示 hook 永不 write CLAUDE.md;
    # 输出走 evidence/ai-context-audit/ draft 由 user manual apply)
    'CLAUDE.md',
    'src/CLAUDE.md',
    'capabilities/CLAUDE.md',
    'tests/CLAUDE.md',
    'docker/CLAUDE.md',
    # 全 SKILL.md 防御 (含未来新增)
    '.claude/skills/**/SKILL.md',
    # 配置
    '.claude/settings.json'
)

function Test-PathAllowed {
    param([string]$Path)
    # Deny 优先: 任一 denylist 模式命中 → false
    foreach ($pattern in $WriteDenylist) {
        if ($Path -like $pattern) { return $false }
    }
    # Allow: 任一 allowlist 模式命中 → true
    foreach ($pattern in $WriteAllowlist) {
        if ($Path -like $pattern) { return $true }
    }
    # 默认 deny (closed-world)
    return $false
}

$ErrorActionPreference = 'Continue'

Write-Host "[skeleton] stop-claude-md-improver: Phase M0 placeholder; no analysis run."
Write-Host "[skeleton] See .claude/hooks/stop-claude-md-improver/README.md + Phase M2 backfill."

exit 0
