# .claude/hooks/stop-claude-md-improver/

> Phase M0 skeleton — A2 (Anthropic 大型代码库最佳实践) Stop hook self-improvement.
> Phase M2 内容填充 — 详 `mj-agent-refactored-structure.md` §17.4.

## Purpose

每次 Claude Code session 结束时触发：

1. 读取本次 session 实际命中的 HITL gate / 误判 / 命令失败模式
2. 对照当前 CLAUDE.md（root + 4 subdir）找出"缺失提示"或"过时提示"
3. 产出 **diff 草案** 写入 `evidence/ai-context-audit/<YYYY-MM-DD>_session_<id>_proposed_claude_md_update.md`
4. **不自动 commit / 不自动 Edit CLAUDE.md** —— 草案由 user review + Edit 落地（防自改失控；R-G21 mitigation）

## Hook Wiring (Phase M2)

Phase M2 will wire this hook via `.claude/settings.json` `hooks.Stop` field:

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "pwsh -NoProfile -File ${CLAUDE_PROJECT_DIR}/.claude/hooks/stop-claude-md-improver/on-stop.ps1"
      }
    ]
  }
}
```

> Phase M0 does NOT wire this hook into settings.json — wiring lives in Phase M2.

## Output Location

`evidence/ai-context-audit/<YYYY-MM-DD>_session_<id>_proposed_claude_md_update.md`

This evidence file is read by `mj-agent-doc-sync` skill at Phase 末 to batch-apply proposed updates (per `policies/documentation.md` §Review Cadence; per `policies/ci-gates.md` §Review Cadence).

## Anti-patterns

- ❌ Do NOT have this hook auto-Edit CLAUDE.md
- ❌ Do NOT have this hook auto-commit
- ❌ Do NOT have this hook read `archive/` content (waste of context budget)
- ✅ Do produce diff drafts for human review

## Related

- `policies/documentation.md` §Review Cadence (A6)
- `policies/ci-gates.md` §Review Cadence (A6)
- `mj-agent-refactored-structure.md` §17.4
- `spec-anchored-calm-lampson.md` §10 R-G21 (Stop hook 自改失控)

---

> *Phase M0 skeleton — script implementation in Phase M2.*
