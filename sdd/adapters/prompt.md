---
type: sdd-adapter
artifact: prompt
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: agent
ai_visibility: source-of-truth
---

# Adapter: Prompt

> Phase M0 skeleton — Prompt adapter 治理 `prompts/system.md` + 9 SKILL.md.
> 完整 version bump 必停规则 + §BDD Rules + §TDD Rules 在 Phase M2 内容填充.

## Scope

- `src/mj_agent/prompts/system.md`（agent system prompt body + frontmatter）
- `src/mj_agent/skills/*/SKILL.md` body（每 in-source canonical skill）

## Contract Output

`<capability>/contracts/prompt.contract.yml`（schema 见 `sdd/templates/contracts/
prompt.contract.yml.template`）.

## §Standards

> TBD: Phase M2 — prompt_path / version / variables / frontmatter_required /
> allowed_state_transitions 字段；version bump 触发 `prompt-version-bump` 专属必停的 PR gate
> hook 行为.

## §BDD Rules

> TBD: Phase M2 — 输入语境 → 期望输出行为 .feature 化；regression case 在每次 bump 必跑.

## §TDD Rules

> TBD: Phase M2 — prompt regression case 在 EVAL framework 落地后强制先写
> （per ADR-024 EVAL 框架联动）.

## CI Gate

`scripts/sdd/check_prompt_contracts.py`（Phase M2 warning / M3 blocking）.

## HITL Trigger

任意 `prompts/system.md` body 修改或 version bump → `prompt-version-bump` 永久 manual blocking
（per `sdd/gates.md` §4）.

---

> *Phase M0 skeleton — `state: draft`.*
