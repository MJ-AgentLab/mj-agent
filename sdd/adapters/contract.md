---
type: sdd-adapter
artifact: contract
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-06-04
updated: 2026-06-04
track: agent
ai_visibility: source-of-truth
---

# Adapter: Contract (agent-facing tool)

> Phase M6 内容化 — Contract adapter 治理 agent-facing tool CONTRACT 文档的 authoring 深度 +
> A10 PR gate rule body（`state: active` ⇒ `schema_ref` 存在且指向存在 schema 文件）+
> `contract_kind` enum. ported from Agent_Side §5 + §7.1 A10（这是 kernel home；Agent_Side
> 后续 archive）. §Standards / §BDD Rules / §TDD Rules 各段顶部 cross-ref 蓝图
> `spec-anchored-calm-lampson.md` 手册 Contract Adapter Standards.

## §Scope

**Included** — Contract adapter 治理：

- **agent-facing tool CONTRACT 文档**（`docs/contracts/[CONTRACT]_<Kind>_<Name>_vX.Y.md`）—
  描述 LLM 实际调用的工具接口的输入 / 输出 / 错误模式 / 版本策略
- mj-agent 的 agent-facing tool surface（per `langchain-agent.md` §Scope 调用流转契约）：
  - `find_biz_context` — biz 上下文检索（`ALL_TOOLS` 第 1 个）
  - `list_biz_tables` / `describe_biz_table` — schema introspection
  - `execute_sql` — SQL 执行 + result envelope（`executed_sql` / `columns` / `rows` /
    `row_count` / `truncated` / `statement_timeout_hit` / `business_summary` /
    `precheck_warnings`）
- CONTRACT frontmatter schema 治理：`contract_kind` enum + `schema_ref` + `parties[]` +
  `state` 转换
- **A10 PR gate rule body**（此前 named-but-undefined）：`state: active` 的 CONTRACT 必须有
  `schema_ref` 且指向存在的机器可读 schema 文件

**Excluded** — 其他 adapter 治理：

- Tool 内部 Python 实现（如 `is_safe_select` 函数体 / `execute_sql` 实现）→ `python` adapter
- Tool 注册 / agent graph 拼接 / middleware（→ `langchain-agent` adapter；CONTRACT 治理的是
  接口 invariant，行为契约是 agent adapter 的职责）
- cross-service / MCP server CONTRACT 的 **trust posture 维度**（→ `claude-code-skill` /
  infra adapter + MCP server governance STANDARD）；本 adapter 治理 agent-facing tool 维度
- SKILL / PROMPT body invariant（→ `runtime-skill` / `prompt` adapter）

**`contract_kind` enum 与本 adapter 的关系**（ported from `docs/_templates/TEMPLATE_CONTRACT.md`
+ Agent_Side §0 类型表）：

| `contract_kind` | 含义 | 本 adapter scope |
|---|---|---|
| `tool` | 进程内工具接口（LLM ↔ mj-agent tool） | **本 adapter 主体**（agent-facing） |
| `cross-service` | 跨仓库 / 跨服务接口 | 边界：agent-facing 部分本 adapter；纯服务间走 Code_Side |
| `mcp` | MCP server 接口 | 边界：trust posture 走 MCP governance；接口 schema 维度本 adapter |

agent-facing tool CONTRACT 的 `contract_kind` 几乎总是 `tool`（mj-agent 当前 4 个 tool 全是
进程内 `tool` kind）.

## §Contract Output

`<capability>/contracts/contract.contract.yml` — per capability one file，描述本 capability
涉及的 agent-facing tool CONTRACT 集合 + 其 `schema_ref` freeze（schema 见
`sdd/templates/contracts/contract.contract.yml.template`；M6-FU 落地 —— 当前 templates 目录
尚无此 template，本 adapter spec 先行，template + script 由后续小 PR 补）.

预期首批 contract（M6+ 落地）：

- `capabilities/data-agent/safe-sql/contracts/contract.contract.yml` — freeze `execute_sql`
  result envelope schema（8 字段：`executed_sql` / `columns` / `rows` / `row_count` /
  `truncated` / `statement_timeout_hit` / `business_summary` / `precheck_warnings`）
- `capabilities/data-agent/biz-catalog/contracts/contract.contract.yml` — freeze
  `find_biz_context` + `list_biz_tables` + `describe_biz_table` 接口 schema

## §Standards

> 本节对应蓝图手册 Contract Adapter Standards. agent-facing tool CONTRACT authoring 深度 ported
> from Agent_Side §5（这是 kernel home）.

**CONTRACT 文档 authoring 深度**（ported from Agent_Side §5 + `TEMPLATE_CONTRACT.md` body 结构）—
每个 agent-facing tool CONTRACT body 至少含：

- **Parties** — Provider（实现方，即 mj-agent tool 模块）+ Consumer（调用方，即 LLM / agent
  graph）；`parties[]` frontmatter 字段列出项目 / 服务名称
- **Interface schema** — 引用机器可读 schema（JSON Schema / Python 类型签名 / tool input-output
  签名）；schema 源文件相对路径放在 `schema_ref` 字段
- **Inputs / Outputs** — 人类语言解释每个字段语义与取值范围（机器 schema 负责结构校验，本节负责
  意图说明）
- **Error modes** — 错误类型 / 触发条件 / Consumer 应如何处理（如 `execute_sql` 的
  `statement_timeout` 60s 命中 → 友好中文提示；L1 guardrail 拒绝 → `ToolMessage` 回 LLM 自纠，
  per ADR-029）
- **Versioning policy** — 增量字段走 minor；删除 / 改语义字段走 major（major 升级保留旧版
  `state: deprecated` 至少一个发布周期）

**Required fields**（CONTRACT frontmatter schema；ported from Agent_Side §5 + TEMPLATE_CONTRACT）：

- `contract_kind` — `tool` | `cross-service` | `mcp`（agent-facing tool 几乎总是 `tool`）
- `parties[]` — 列出 Provider / Consumer 项目 / 服务名称
- `schema_ref` — 机器可读 schema 文件相对路径（**A10 强制条件见下**）
- `state` — `draft | active | deprecated`
- `version` — `_vX.Y`（CONTRACT 是带 `version` frontmatter 的类型，per Meta 版本规则）

**A10 PR gate rule body**（此前 named-but-undefined 任何地方；本 adapter 是 canonical 定义点；
ported from Agent_Side §7.1 A10 表行）：

> **A10**: CONTRACT `state: active` 时，frontmatter `schema_ref` **必须**（a）非空，**且**
> （b）指向一个**存在的**机器可读 schema 文件（相对仓库根的路径解析后文件实际存在）。
> 二者任一不满足 → **blocking** PR gate。
>
> - `state: draft` 时 `schema_ref` 可为空字符串 `""`（允许 spec 先于 schema 文件）
> - `state: active` 时 `schema_ref: ""` → FAIL（A10-a 违反）
> - `state: active` 时 `schema_ref: "schemas/execute_sql.json"` 但该文件不存在 → FAIL
>   （A10-b 违反）
> - 适用范围：`docs/contracts/**`（per Agent_Side §7.1 A10 表）

**`hitl_required[]`** — 仅 gate ID 引用（hyphen canonical per C5）：

```yaml
hitl_required:
  - tool-contract-schema-change         # agent-facing tool 接口 schema / schema_ref 变更触发
```

注：mj-agent 4 项专属必停（sql-guardrail-relax / prompt-version-bump / biz-catalog-sync /
runtime-skill-content-change）中，`sql-guardrail-relax` 与本 adapter 强相关 —— `execute_sql`
result envelope 或 guardrail 边界变更若改变 agent-facing 接口契约，触达 `sql-guardrail-relax`
必停 + 本 adapter `tool-contract-schema-change`（gate ID 命名 M6+ 在 `sdd/gates.md` §4 落地）.

**Optional fields**：

- `slo` — 延迟 p95 / 可用性 / 速率限制（`execute_sql` 的 `statement_timeout=60s` 是天然 SLO 边界）
- `eval_references[]` — 指向覆盖本 tool 接口的 EVAL（M4+ EVAL framework baseline 后；与
  ADR-024 联动）

## §BDD Rules

> 本节对应蓝图手册 Contract Adapter BDD Rules（agent-facing tool 接口契约 tagging）.

**`@adapter:contract` 何时用** — agent-facing tool 接口契约 scenario：

- `execute_sql` result envelope 字段集合 / 字段语义符合 frozen schema
- tool input 签名变更是否触发 `version` bump（minor / major 判定）
- A10 drift detection case（`state: active` 但 `schema_ref` 空 / 指向不存在文件）
- error mode 契约（如 `statement_timeout` 命中 → 友好中文提示而非裸异常）

**`@adapter:contract` 何时 NOT 用** — 避免与 agent / python adapter 重复：

- tool 内部实现行为（`is_safe_select` 正则逻辑 / SQL 执行细节）→ `@adapter:python`
- "改 prompt 后 LLM 选错 tool 顺序" / tool 调用流转 → `@adapter:langchain-agent`
- CONTRACT 文档纯 prose 改动（typo / 排版）→ 不加 tag；走人工 review

**`@adapter:contract` + `@hitl`** — agent-facing tool 接口 schema 变更触达
`tool-contract-schema-change`（+ SQL surface 时叠加 `sql-guardrail-relax`）；scenario 自带
hitl 信号.

**`@risk:high` 配套 BDD 必填** — `execute_sql` 是 high risk（直接对 biz 数据库执行；envelope
字段是 LLM 下游业务摘要的 input；契约 drift = 业务 risk）.

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:contract @hitl @risk:high
Scenario: active tool CONTRACT must point at an existing schema file (A10)
  Given a CONTRACT docs/contracts/[CONTRACT]_Tool_Execute_Sql_v1.0.md
  And its frontmatter state is "active"
  And its schema_ref is "schemas/execute_sql.json"
  When schemas/execute_sql.json does not exist on disk
  Then the A10 PR gate result is FAIL
  And the error message references A10-b (schema_ref points at a missing file)
```

## §TDD Rules

> 本节对应蓝图手册 Contract Adapter TDD Rules（agent-facing tool contract-test-first +
> A10 schema-existence check）.

**Contract-test-first 限于 schema layer**：

- `contract.contract.yml` 的 tool 接口 schema / `schema_ref` 字段变更 → 必先有 failing test
- A10 校验（`state: active` ⇒ `schema_ref` 非空 AND 文件存在）是纯 schema-layer check →
  test-first 适用
- 不要求 CONTRACT prose 改动跑 test-first（走人工 review）

**A10 双条件实现**（schema-existence check）：

```python
# A10-a：state: active 时 schema_ref 非空
# A10-b：解析 schema_ref（相对仓库根）后文件实际存在
from src.mj_agent.skills import load_skill  # 仅示意；CONTRACT 校验用 _common.frontmatter
# 实装走 scripts/sdd/_common/frontmatter.load_frontmatter(contract_path)
#   → fm = {"state": ..., "schema_ref": ...}
#   → if fm["state"] == "active":
#         assert fm["schema_ref"], "A10-a: schema_ref empty"
#         assert (repo_root / fm["schema_ref"]).exists(), "A10-b: schema file missing"
```

**`_common.frontmatter` 共享接口** — 与 prompt / runtime-skill adapter 共用 Stage A 实装：

```python
# scripts/sdd/_common/frontmatter.py 公开符号（contract adapter 复用）：

load_frontmatter(file_path: Path) -> dict | None
    # 安全加载 CONTRACT frontmatter；取 state / schema_ref / contract_kind 字段
```

**Red-Green-Refactor 软模式 (RD10=C)** — 同其他 adapter；schema-layer test（A10 双条件 +
envelope 字段集合）必先 failing；CONTRACT prose 走人工 review.

**G28 contract-test-first blocking 联动**（M6+ 起）：

- `contract.contract.yml` tool 接口 schema / `schema_ref` 变更 → 必须配套
  `tests/contracts/<capability>/test_tool_contract.py` 内 failing→green 转变

## §CI Gate

**Script gate**: `scripts/sdd/check_tool_contracts.py`（M6-FU 落地；当前 spec 先行）

- **Phase**: M6 **skeleton / spec-only**（template + script 由后续小 PR 补）；后续 warning →
  blocking（per `sdd/gates.md` 切换节奏）
- **Triggers**: `capabilities/*/contracts/contract.contract.yml` 任一存在；或 `docs/contracts/
  **/*.md` 任一为 `state: active`（A10 校验）
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（A10-a `schema_ref` 空 / A10-b 文件不存在 /
  `contract_kind` 不在 enum / envelope 字段集合 drift）
- **Implementation**: `_common.frontmatter` 加载 CONTRACT frontmatter + A10 双条件校验 +
  （envelope freeze 时）比对 `contract.contract.yml` schema

**Manual HITL gate**（permanent blocking；M6 不可 script 完全 auto-detect）：

- Gate ID: `tool-contract-schema-change`（M6+ 在 `sdd/gates.md` §4 命名落地）；SQL surface 变更
  时叠加 `sql-guardrail-relax`
- Triggers: agent-facing tool 接口 schema / result envelope 字段 / error mode 契约变更
- Detection: PR reviewer mandatory check + script `check_tool_contracts.py` 提前预警
- Rationale: tool 接口契约改动可能改变 LLM 下游业务摘要行为但 schema 仍合规；script 看不出语义
  drift；必须 human review + M4+ EVAL regression 配套

**M6 → 后续切换条件**：

- `contract.contract.yml.template` + `check_tool_contracts.py` 落地（M6-FU 独立小 PR）
- 首批 `safe-sql/contract.contract.yml` + `biz-catalog/contract.contract.yml` schema layer PASS
- `tool-contract-schema-change` gate 在 `gates.md` §4 完整定义

---

> *Phase M6 content — `state: draft`. A10 rule body kernel home (ported from Agent_Side §5 +
> §7.1).*
