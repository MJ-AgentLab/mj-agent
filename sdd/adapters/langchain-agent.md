---
type: sdd-adapter
artifact: langchain-agent
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-21
track: agent
ai_visibility: source-of-truth
---

# Adapter: LangChain Agent

> Phase M2 内容化 — LangChain Agent adapter 治理 mj-agent 的 graph 装配 + tool 注册 +
> middleware 链 + memory checkpointer 的 behavior contract. §Standards / §BDD Rules / §TDD
> Rules 各段顶部 cross-ref 蓝图 `spec-anchored-calm-lampson.md` 手册 §22.4 Agent Adapter
> Standards.

## §Scope

**Included** — LangChain Agent adapter 治理：

- `src/mj_agent/agent.py` — `make_graph()`（langgraph.json 入口）/ `_build_system_prompt()`
  （system prompt + 3 SKILL 拼接）/ `_ACTIVE_SKILLS` 列表（runtime SKILL 静态全量加载）
- `src/mj_agent/tools/__init__.py` — `ALL_TOOLS` 注册顺序（system prompt tool-call order hint
  的 reference）
- `src/mj_agent/middleware/**/*.py` — middleware 链（ADR-029 + #288 amendment：单
  `SQLToolErrorMiddleware` 同时 override `wrap_tool_call`/`awrap_tool_call` 双 hook，
  单例 `handle_sql_tool_errors`；禁止拆回单侧 `@wrap_tool_call` decorator 形态）
- `src/mj_agent/memory/checkpointer.py` — `AsyncPostgresSaver` 实例化 + DSN + schema 配置
- Tool 调用流转契约：`find_biz_context` → `list_biz_tables` / `describe_biz_table` →
  `execute_sql`（LLM 按 system prompt 的 hint 顺序，非硬代码强制）

**Excluded** — 其他 adapter 治理：

- Prompt body 内容（→ `prompt` adapter；`prompts/system.md` body 是 invariant，不是 agent
  行为契约的载体）
- SKILL.md body 内容（→ `runtime-skill` adapter；frontmatter strip 契约 per Agent_Side §7.5）
- Python 模块级公开符号（→ `python` adapter；本 adapter 只管 graph 装配的"组合行为"）
- Tool 内部实现（如 `is_safe_select` 函数体）→ `python` adapter

**Adapter boundary 边界场景**：

- middleware 链顺序变更 → `langchain-agent` adapter（行为契约）+ `python` adapter（符号契约）
  双触发
- 新加 tool 注册 → `langchain-agent` adapter + `python` adapter（`ALL_TOOLS` 是 Python 顶层
  常量）双触发

## §Contract Output

`<capability>/contracts/agent.contract.yml` — per capability one file，描述本 capability 的
graph + tools + middleware + checkpointer + HITL gate 引用集（schema 见
`sdd/templates/contracts/agent.contract.yml.template`）.

M1 实测：`safe-sql` capability 的 agent 行为已隐式被 `execute-sql.contract.yml` 覆盖；M2 期 V2
smoke-only（无 `agent.contract.yml` input；`ruff` + `mypy` + `discover-test` PASS 已是质量证
据 per Q-A4）；M3 起单独 `agent.contract.yml` 落地后跑实测.

## §Standards

> 本节对应蓝图手册 §22.4 Agent Adapter Standards.

**Required fields** (contract YAML schema)：

- `graph_symbol` — graph 工厂函数名（默认 `make_graph`，langgraph.json 必须指向此符号）
- `tools[]` — `ALL_TOOLS` 注册顺序的镜像（与 `python.contract.yml` 内
  `src.mj_agent.tools.__init__` 模块的 `_extract_list_items(ALL_TOOLS)` 校验）
- `tool_call_order_hint` — 自然语言描述 LLM 按 system prompt 的 tool-call 顺序 hint（不是硬代
  码约束；scenario 行为验证依据）
- `middleware_chain[]` — 已挂载 middleware 列表（M1 仅含 `handle_sql_tool_errors`；ADR-029）
- `checkpointer` — memory checkpointer 配置 `{type, schema}`（默认 `AsyncPostgresSaver` +
  `mj_agent_memory` schema；storage-stack PR 解耦后独立 pg container）
- `hitl_required[]` — gate ID 引用列表（**仅 ID**；canonical trigger 描述保留在
  `sdd/gates.md` §4；hyphen 命名 per C5 canonical 统一）

**`hitl_required[]` gate ID 引用模式** — Design call 2 clarification 落地：

```yaml
hitl_required:
  - sql-guardrail-relax              # 触发条件 / 影响范围 / detection 全部 lookup gates.md §4
  - prompt-version-bump              # adapter contract 仅携带 "本 capability 受这些 gate 约束"
  - biz-catalog-sync                 # signal；不复制 trigger 描述（drift 收敛单点）
  - runtime-skill-content-change     # M3 contract test 按 ID lookup gates.md 校验 trigger 一致
```

M3 contract test 实装策略：

1. 读 `agent.contract.yml` 的 `hitl_required[]`
2. 对每个 ID，到 `sdd/gates.md` §4 找定义；缺失 → FAIL
3. 不在 contract 内复制 trigger 描述（避免双源不一致）

**Optional fields**：

- `tool_schema` — langchain Pydantic schema 与 contract 的双向校验（M2 期 TBD；M3 起落地）
- `ratelimit` / `timeout` / `retry` — agent 行为边界（M3-M4 起落地）
- `subgraph[]` — multi-graph 拓扑（M5+ 起落地；mj-agent 当前单 graph）

**`graph_symbol` 重签触发**：

- `make_graph()` 签名变更（如新增 `middleware=` kwarg）
- `_ACTIVE_SKILLS` 列表增删（影响 system prompt 拼接）
- Tool 注册顺序变更（影响 LLM tool-call hint）

## §BDD Rules

> 本节对应蓝图手册 §22.4 BDD Rules（agent behavior scenario tagging）.

**`@adapter:langchain-agent` 何时用** — agent 行为级 scenario：

- "用户意图 → 拒绝 / 接受 + tool call 顺序" 端到端行为（如 "查上季度收入" → 触发
  find_biz_context → describe → execute_sql 序列）
- middleware 拦截行为（ValueError / RuntimeError 转 ToolMessage）
- checkpointer 状态恢复行为（中断 conversation 续接）

**`@risk:high` 绝对 BDD 必填** — `agent.py` 是 LLM 入口；高风险 case 必须 BDD 自动化覆盖（per
`sdd/adapters/bdd-tdd.md` §Automation Strategy；M3-M4 自动化阈值从 70% 降到 50% per RD9=B 试
行，**但 `@adapter:langchain-agent` 维度的 `@risk:high` 仍是 100% 自动化目标**）.

**`agent.py` refactor must not change behavior `.feature`** — 业务行为契约不变原则：

- Tool 注册顺序重构 → 行为 .feature 全部 green 才算 refactor 完成
- middleware 链顺序调整 → 同上
- system prompt 拼接逻辑重构 → 同上（prompt body 是 `prompt` adapter；拼接逻辑是
  `langchain-agent`）

**`@adapter:langchain-agent` + `@hitl` 双标签** — middleware 行为差异触达必停 surface 时
（如新 middleware 改变了 `sql-guardrail-relax` 行为信号路径）.

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:langchain-agent @risk:high
Scenario: agent routes biz query through find_biz_context first
  Given user asks "查询上季度产品收入 top 10"
  When agent processes the message
  Then tool find_biz_context is called before any SQL execution
  And tool execute_sql is only invoked after table description is resolved
```

## §TDD Rules

> 本节对应蓝图手册 §22.4 TDD Rules（agent contract-test-first + behavior preservation）.

**Tool boundary test 先写**：

- 新增 tool / 改 tool 签名 → 先写 `tests/contracts/<capability>/test_agent_contract.py` 内
  "调 tool X 应得 envelope Y" 失败用例
- Failing → green 后再 land tool 实装

**`agent.py` refactor 前置条件**：

- 强制先跑 existing behavior `.feature` 全部 green
- Refactor 改动 land 后再跑一次；任何 .feature 失败 → 立即 revert refactor commit（非 fix
  behavior；refactor 必须保 behavior invariant）

**新增 middleware 触发 contract-test-first**：

- 任何 `middleware/*.py` 文件新增 → `agent.contract.yml` 的 `middleware_chain[]` 必先增加
  对应条目；缺失 → G28 blocking
- 顺序变化 → 必须配套 unit test 验证拦截顺序

**`check_agent_contracts.py` 内 local helpers** — Stage A 实装：

```python
# scripts/sdd/check_agent_contracts.py 内（M3+ 视复用需求 promote 候选）：

_extract_assign_value(tree: ast.AST, name: str) -> ast.AST | None
    # 从 AST 提取 module-level 赋值表达式 RHS（如 ALL_TOOLS = [...] 的 list AST）

_extract_list_items(value_ast: ast.AST) -> list[str]
    # 把 list AST 解开为 string item（验证 ALL_TOOLS 的注册名顺序）
```

**Promote 路径** — M3+ 若 `check_agent_contracts.py` 与 `check_python_contracts.py` 共同需要
"提取顶层赋值 RHS" 时，promote 到 `_common/ast_helpers.py`；当前保持 local 不强制（非 M3-FU
单独 task）.

**G28 联动** — `agent.contract.yml` `tools[]` / `middleware_chain[]` / `hitl_required[]` 任一
增删 → 必须有 failing→green 转变 in `tests/contracts/<capability>/test_agent_contract.py`.

（RD10=C 软模式同 `python.md` §TDD Rules）

## §CI Gate

**Script gate**: `scripts/sdd/check_agent_contracts.py`

- **Phase**: M2 warning / **M3 blocking**（per `sdd/gates.md` G4 切换节奏）
- **Triggers**: `capabilities/*/contracts/agent.contract.yml` 任一存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（缺失 gate ID / `ALL_TOOLS` 顺序不匹配 /
  middleware 链不一致 / `_ACTIVE_SKILLS` 漂移）
- **Implementation**: AST inspection of `src/mj_agent/agent.py` + `tools/__init__.py` + `gates.md`
  parse + cross-validate

**Baseline noise** — M2 期 V2 smoke-only（M1 capability 暂无 `agent.contract.yml` input；ruff +
mypy + discover-test PASS 已是质量证据 per Q-A4）；M3 起 input contract 落地后跑实测；M2 期
warning mode 下预期 0 noise.

**M2 → M3 切换条件**：

- 至少 1 个 M1 capability 落地 `agent.contract.yml`（候选：`data-agent/safe-sql` 已隐式有
  agent 行为依据 `execute-sql.contract.yml`，可直接抽象）
- `_extract_assign_value` / `_extract_list_items` 在所有 M1 5 capability 上跑通
- `gates.md` §4 gate ID 完整 enum 化（C5 落地后；M3-FU-HITL-ENUM 完成）

---

> *Phase M2 content — `state: draft`.*
