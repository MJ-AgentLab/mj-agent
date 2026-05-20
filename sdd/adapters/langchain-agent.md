---
type: sdd-adapter
artifact: langchain-agent
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: agent
ai_visibility: source-of-truth
---

# Adapter: LangChain Agent

> Phase M0 skeleton — LangChain Agent adapter 治理 `agent.py` + tools + middleware + memory.
> 完整 contract schema + HITL config + §BDD Rules + §TDD Rules 在 Phase M2 内容填充.

## Scope

- `src/mj_agent/agent.py`（`make_graph()` / `_build_system_prompt()` / `_ACTIVE_SKILLS`）
- `src/mj_agent/tools/__init__.py` ALL_TOOLS 注册
- `src/mj_agent/middleware/`（含 ADR-029 `handle_sql_tool_errors`）
- `src/mj_agent/memory/checkpointer.py`（AsyncPostgresSaver）

## Contract Output

`<capability>/contracts/agent.contract.yml`（schema 见 `sdd/templates/contracts/
agent.contract.yml.template`）.

## §Standards

> TBD: Phase M2 — graph_symbol 字段 / tools 列表 / tool_call_order_hint / middleware 链 /
> hitl_required 字段对齐 §"mj-agent specific hard stops".

## §BDD Rules

> TBD: Phase M2 — 用户意图 → 拒绝 / 接受行为 .feature 化；高风险绝必填.

## §TDD Rules

> TBD: Phase M2 — tool boundary test 先写；agent.py refactor 必须不改 behavior.feature.

## CI Gate

`scripts/sdd/check_agent_contracts.py`（Phase M2 warning / M3 blocking）.

---

> *Phase M0 skeleton — `state: draft`.*
