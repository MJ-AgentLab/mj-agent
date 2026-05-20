---
type: sdd-adapter
artifact: runtime-skill
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: agent
ai_visibility: source-of-truth
---

# Adapter: Runtime Skill (in-source canonical)

> Phase M0 skeleton — Runtime Skill adapter 治理 `src/mj_agent/skills/*` 9 in-source canonical
> skill. 完整 frontmatter strip 契约 + §BDD Rules + §TDD Rules 在 Phase M2 内容填充.

## Scope

- `src/mj_agent/skills/<name>/SKILL.md`（9 个 in-source canonical skill；MVP 启用 3 个：
  biz-domain-context / qcm-analysis / safe-sql-analysis）

## Contract Output

`<capability>/contracts/runtime-skill.contract.yml`（schema 见 `sdd/templates/contracts/
runtime-skill.contract.yml.template`）.

## §Standards

> TBD: Phase M2 — sections_required 列表（## Purpose / ## When to use / ## Planning workflow /
> ## Common patterns / ## Anti-patterns）；frontmatter_strip_contract: true（loader 必须 strip
> via `python-frontmatter`）；loader 函数明示（`load_skill` from `src.mj_agent.skills`）.

## Frontmatter Strip 契约（硬约束）

```python
# src/mj_agent/skills/__init__.py 已有 load_skill 实现
from src.mj_agent.skills import load_skill
body = load_skill("safe-sql-analysis")  # frontmatter 已 strip，仅 body 进 LLM input
```

任何代码绕过 `load_skill` 直接 `open().read()` SKILL.md → 违反契约 → A11 PR gate（Phase M3 起
blocking）.

## §BDD Rules

> TBD: Phase M2 — 触发条件 / 行为边界 .feature 化；与 system.md 联动测试.

## §TDD Rules

> TBD: Phase M2 — runtime-skill content 演进的 EVAL regression case（per ADR-024）.

## CI Gate

`scripts/sdd/check_runtime_skill_contracts.py`（Phase M2 起；与 A11 PR gate 联动）.

## HITL Trigger

任意 `skills/*/SKILL.md` body 修改 → `runtime-skill-content-change` 永久 manual blocking
（per `sdd/gates.md` §4）.

---

> *Phase M0 skeleton — `state: draft`.*
