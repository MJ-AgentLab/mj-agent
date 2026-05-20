---
type: sdd-adapter
artifact: python
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: code
ai_visibility: source-of-truth
---

# Adapter: Python

> Phase M0 skeleton — Python adapter 治理 `src/mj_agent/` 所有 Python 模块.
> 完整 contract schema + §BDD Rules + §TDD Rules 在 Phase M2 内容填充
> （per Phase M2 §3 "sdd/adapters/python.md (skeleton → 完整内容)"）.

## Scope

- `src/mj_agent/**/*.py`
- 公开接口（`__all__` 显式 / 模块顶层函数与类）
- 异常类型契约

## Contract Output

`<capability>/contracts/python.contract.yml`（schema 见 `sdd/templates/contracts/
python.contract.yml.template`）.

## §Standards

> TBD: Phase M2 — module signature schema / exports 字段 / public_invariants 列表规则.

## §BDD Rules

> TBD: Phase M2 — 公共 API / CLI 行为级 .feature 化的判定标准.

## §TDD Rules

> TBD: Phase M2 — public function red-green-refactor 流程；test list 在 tasks.md 起点；
> bugfix 强制先写 failing test（G24/G28 联动）.

## CI Gate

`scripts/sdd/check_python_contracts.py`（Phase M2 warning / M3 blocking）.

---

> *Phase M0 skeleton — `state: draft`.*
