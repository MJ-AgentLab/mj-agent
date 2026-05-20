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

## §4 Runtime Family Read-Only by Design

`.claude/skills/mj-agent-runtime-*` 4 个 skill **必须 read-only by design** — 提议 diff，不
直接写 `src/mj_agent/skills/`、`prompts/`、`agent.py`、`tools/`、`biz_catalog/`.

执行机制：A12 description quality gate + SKILL.md ## Anti-patterns 段 + `.claude/settings.json`
deny-list 三重保险（详 `policies/data-boundary.md` §3）.

## §5 A12-A14 PR Gate Self-Check Checklist

> TBD: Phase M2 — 详 `mj-agent-refactored-structure.md` §17 + Meta v2.x §7.7.

## §6 MCP Server Governance

> TBD: Phase M2 — 与 `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`
> 互引（per ADR-028）；A14 PR gate 实施细则.

---

> *Phase M0 skeleton — `state: draft`.*
