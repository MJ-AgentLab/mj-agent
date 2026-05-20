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

$ErrorActionPreference = 'Continue'

Write-Host "[skeleton] stop-claude-md-improver: Phase M0 placeholder; no analysis run."
Write-Host "[skeleton] See .claude/hooks/stop-claude-md-improver/README.md + Phase M2 backfill."

exit 0
