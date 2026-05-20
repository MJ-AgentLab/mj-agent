---
type: sdd-adapter
artifact: claude-code-skill
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: engineering-workflow
ai_visibility: source-of-truth
---

# Adapter: Claude Code Skill (in-tree workflow)

> Phase M0 skeleton — Claude Code Skill adapter 治理 `.claude/skills/mj-agent-*` 32 in-tree
> workflow skill. 完整 ADR-013 native schema + §BDD Rules + §TDD Rules 在 Phase M2 内容填充.

## Scope

- `.claude/skills/mj-agent-<group>-<verb>/SKILL.md`（per ADR-016 namespace）
- 32 skill 终态（5 family：flow 9 / git 9 / doc 6 / runtime 4 / infra 4）
- Phase M6 新增 evidence family 4 skill → 36 终态

## Contract Output

`<capability>/contracts/claude-skill.contract.yml`（schema 见 `sdd/templates/contracts/
claude-skill.contract.yml.template`）.

## §Standards

> TBD: Phase M2 — schema 严格使用 ADR-013 **native 2-field**（`name` + `description` only；NOT
> the 13-field Agent_Side schema）；description ≥ 200 chars；含 reverse-trigger block
> "Do not use for:"；sections required: `## Overview` + `## Workflow`（其他段灵活）.

## §BDD Rules

> TBD: Phase M2 — 工作流 skill 的读写范围安全性 .feature 化（A11/A12 gate）.

## §TDD Rules

> TBD: Phase M2 — scope test 先写（workflow skill 不应越界 capability）；mj-agent-runtime-*
> read-only by design enforce.

## CI Gate

`scripts/sdd/check_claude_skill_contracts.py`（Phase M2 warning / M3 blocking）+ A12-A14 PR
gate（per `policies/claude-code-skill.md` §A12-A14 checklist）.

---

> *Phase M0 skeleton — `state: draft`.*
