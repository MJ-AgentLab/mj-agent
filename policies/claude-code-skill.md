---
type: policy
artifact: claude-code-skill
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: Claude Code Skill Governance

> Phase M0 skeleton — in-tree workflow skill 治理政策.
> 完整 3 SKILL 来源严格区分 + ADR-013 native schema + A12-A14 PR gate self-check 在 Phase M2
> 内容填充.

## §1 3 SKILL 来源严格区分

> TBD: Phase M2 — 详 `sdd/constitution.md` §3.3 3 SKILL 来源严格区分表 + 各源的 governance
> 入口.

## §2 ADR-013 Native Schema

> TBD: Phase M2 — `.claude/skills/` 严格 2 字段（name + description）；NOT 13-field Agent_Side
> schema；详 `sdd/adapters/claude-code-skill.md`.

## §3 Namespace Convention（ADR-016）

> TBD: Phase M2 — `mj-agent-<group>-<verb>` 5 family 模式.

## §4 Runtime Family Propose→拍板→Apply（ADR-034）

`.claude/skills/mj-agent-runtime-*` 4 个 skill 遵循 **propose→拍板→apply**：先提议 diff +
impact，停在工具中立 `OWNER_APPROVAL_REQUIRED` 停点；Owner 拍板后由 skill 直接落盘（Claude Code
载体 = AskUserQuestion + settings `ask` 权限门；Codex 载体 = AGENTS.md 自守 prose）。未经拍板
不写 `src/mj_agent/skills/`、`prompts/`、`agent.py`、`tools/`、`biz_catalog/`.

执行机制：A12 description quality gate + SKILL.md ## Anti-patterns 段 + `.claude/settings.json`
`ask` 逐写拍板门三重保险（ADR-034 deny→ask；详 `policies/data-boundary.md` §3）.

## §5 A12-A14 PR Gate Self-Check Checklist

> TBD: Phase M2 — 详 `mj-agent-refactored-structure.md` §17 + Meta v2.x §7.7.

## §6 MCP Server Governance

> TBD: Phase M2 — 与 `capabilities/infrastructure/mcp-server-governance/`（capability；former MCP STANDARD archived M6 X5）
> 互引（per ADR-028）；A14 PR gate 实施细则.

---

> *Phase M0 skeleton — `state: draft`.*
