---
type: sdd-adapter
artifact: python
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-21
track: code
ai_visibility: source-of-truth
---

# Adapter: Python

> Phase M2 内容化 — Python adapter 治理 `src/mj_agent/` 全部 Python 模块的 public symbol
> contract. §Standards / §BDD Rules / §TDD Rules 各段顶部 cross-ref 蓝图
> `spec-anchored-calm-lampson.md` 手册 §22.1 Python Adapter Standards.

## §Scope

**Included** — Python adapter 治理：

- `src/mj_agent/**/*.py` — 业务代码（tools / middleware / memory / integrations / config / LLM
  factory / agent / server / skills 加载逻辑）
- 公开符号契约：`__all__` 显式 + 模块顶层 `def` / `class` / `UPPERCASE` 顶层常量
- Exception 类型契约：tool surface `ValueError` / `RuntimeError`（ADR-029 envelope 范围）
- 模块到文件路径映射：`src.mj_agent.<package>.<module>` ↔ `src/mj_agent/<package>/<module>.py`
- Type hints（PEP 484）声明的公开签名（参数类型 + 返回类型）

**Excluded** — 其他 adapter 治理：

- `tests/**/*.py` — test 代码本身是 BDD/TDD adapter 维度（→ `sdd/adapters/bdd-tdd.md`）
- `scripts/**/*.py` — SDD 自治理（validator 脚本是 SDD Kernel 实现；不重复治理）
- `infra/**/*` — `docker-container` adapter（Dockerfile / compose / postgres-init）
- `.claude/scripts/**/*.ps1` — Claude Code workflow 自治理（hooks / setup scripts）

**Adapter boundary** — Python adapter **不**治理：

- Prompt body content（由 `prompt` adapter 治理；frontmatter strip 契约 per Agent_Side §7.5）
- Agent 行为契约（由 `langchain-agent` adapter 治理；tool 顺序 + middleware 链 + HITL trigger）
- Runtime SKILL body content（由 `runtime-skill` adapter；in-source canonical 双 contract pattern）

## §Contract Output

`<capability>/contracts/python.contract.yml` — per capability one file，描述本 capability 涵盖的
公开 Python 符号契约（schema 见 `sdd/templates/contracts/python.contract.yml.template`）.

实测形态参考 `capabilities/data-agent/safe-sql/contracts/python.contract.yml` — M1 已落地 153 行
6-module contract（`guardrail` / `precheck` / `execute` / `introspect` / `mj_system_db` /
`tool_errors`），覆盖 REQ-001..006.

## §Standards

> 本节对应蓝图手册 §22.1 Python Adapter Standards.

**Required fields** (contract YAML schema)：

- `contract_id` — 固定为 `python`
- `adapter` — 固定为 `python`（cross-check 本 adapter doc）
- `covers_requirements: [REQ-XXX, ...]` — 反向追溯 capability 的 `requirements.md` 条目
- `modules[]` — 模块列表，每模块包含：
  - `path` — dotted import path（如 `src.mj_agent.tools.sql.guardrail`）
  - `freeze_anchor` — 物理文件路径字符串（M1 style，如
    `src/mj_agent/tools/sql/guardrail.py`）；M2 新 contract（4 必停 surface）扩展为复合对象
    `{file, line_range, content_hash, frozen_at}`，body sha256 双锁
  - `exports[]` — 公开符号清单：`name` / `signature`（PEP 484）/ optional `raises[]` /
    optional `kind`（`dataclass` / `class` / `frozenset` / `constant`）/ optional `public: true`
  - `public_invariants[]` — 公开行为不变量（自然语言；M3 contract test 反向校验）

**Optional fields**：

- `non_actions[]` — 显式声明"本模块**不**做什么"（防 AI hallucination；reverse-engineered from
  doc comments）
- `constants[]` — 模块级常量契约（`name` + `value` + `contract: stable` + `anchor: file:line`）
- `behavior[]` — 中间件 / decorator 行为契约（`catches` / `action` / `anchor`）
- `wiring` — 跨模块依赖描述（如 middleware 在 `agent.py make_graph` 处挂载）
- `hitl_required[]` — 触发本 capability 的 gate ID 列表（**仅引用 ID**；canonical trigger 描述
  保留在 `sdd/gates.md` §4 单点；hyphen 命名 per C5 canonical 统一）

**`freeze_anchor` 重签触发** — 任一以下情况触发 contract YAML `frozen_at` 时间戳重签：

- 公开 API 签名变更（增删参数 / 类型变化）
- `__all__` 增删
- `raises[]` 类型增删（异常契约变更）
- M2 新 contract 的 body `content_hash` 变化（必停 surface 命中）

**私有符号规则**：

- `_` 前缀符号（`_extract_assign_value` / `_VALIDATION_PREFIX`）**通常不入 contract**
- 例外：跨模块或跨测试断言的私有常量（如 `_VALIDATION_PREFIX` 被
  `test_tool_error_middleware.py` 断言）需要进入 `constants[]` 字段并标 `contract: stable`

**HITL 触发字段** — `hitl_required[]` gate ID 引用模式（per Q-A2 Design call 2 clarification）：

```yaml
hitl_required:
  - sql-guardrail-relax              # 不复制 trigger 描述
  - prompt-version-bump              # canonical 描述在 sdd/gates.md §4
  - biz-catalog-sync                 # M3 contract test 按 ID lookup
  - runtime-skill-content-change     # drift 收敛到单点
```

## §BDD Rules

> 本节对应蓝图手册 §22.1 BDD Rules（Python adapter behavioral scenario tagging）.

**`@adapter:python` 何时用** — 公开 API 行为契约 scenario：

- `ValueError` / `RuntimeError` 抛出条件（如 `execute_sql` 在 L4 timeout 触发 `RuntimeError`）
- `ToolMessage` envelope 拦截行为（`middleware.tool_errors` ADR-029 contract）
- 公开 invariant 反向验证（如 `is_safe_select` "never raises; all rejection paths return
  `(False, reason)`"）

**`@adapter:python` 何时 NOT 用** — 防 scenario 爆炸：

- Unit-level internal helper 调用 → 用 plain pytest，不挂 `@adapter:python` tag
- 私有符号（`_` 前缀）行为 → 用 unit test 即可
- Type-check / lint 行为 → 由 `ruff` / `mypy` 工具 gate 覆盖，不入 BDD

**标签组合规则**：

- `@risk:high` tag 必须有配套 BDD scenario（per `sdd/adapters/bdd-tdd.md` §Test Pyramid
  Integration；M3-M4 高风险 100% BDD 自动化阈值）
- `@adapter:python` + `@hitl` 双标签 — 用于必停 surface 触达的 Python 代码 scenario（如
  guardrail relax 必停被某重构间接触发）

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:python @risk:high
Scenario: execute_sql raises ValueError on guardrail rejection
  Given guardrail rejects the SQL "DROP TABLE foo"
  When tool execute_sql is invoked with that SQL
  Then a ValueError is raised
  And the middleware tool_errors converts it to ToolMessage envelope
```

**反向追溯** — 每 `@adapter:python` scenario 必须能追溯到至少一个 `modules[].exports[]` 条目；
M3 traceability gate G2 反向校验.

## §TDD Rules

> 本节对应蓝图手册 §22.1 TDD Rules（contract-test-first + red-green-refactor）.

**Contract-test-first 流程**：

1. 改 `module_path` / `exports[]` / `raises[]` / `__all__` **必先**有 failing contract test
   （per G28 contract-test-first blocking；M3 强制）
2. 测试期望（test list）在 `tasks.md` 顶部声明
3. Failing test landed → implementation change landed → test green → contract YAML `frozen_at`
   更新 → PR ready

**Red-Green-Refactor 软模式** (per RD10=C；适配 AI-generated code 现实)：

- AI-generated code 允许 "test alongside code"（同一 PR 内含 test + 实装；不强制先 commit
  failing test）
- 人工编写代码仍走严格 red-green-refactor
- M4 evidence required gate G8 校验：PR body 含 test list + green pass 证据

**`_common.ast_helpers` 真实 API 接口** (M2 Stage A 已实装；本 validator 用)：

```python
# scripts/sdd/_common/ast_helpers.py 当前公开符号：

module_path_to_file(dotted_path: str, repo_root: Path) -> Path | None
    # 把 "src.mj_agent.tools.sql.guardrail" 解析为
    # Path("src/mj_agent/tools/sql/guardrail.py")

parse_module_safe(file_path: Path) -> ast.Module | None
    # 读 + ast.parse；语法错误返回 None；不抛异常

extract_top_level_names(tree: ast.AST) -> set[str]
    # 提取模块顶层 def/class/Assign 名（不含函数体内部）

check_constant_literal(tree: ast.AST, name: str, expected_value: str) -> bool
    # 验证模块顶层常量赋值 = 期望字面量
```

**未来 promote 候选** — `scripts/sdd/check_agent_contracts.py` 内 local helpers
`_extract_assign_value` / `_extract_list_items`（AST-based `agent.py` inspection）M3+ 视跨脚本复
用需求 promote 到 `_common/ast_helpers.py`（非 M3-FU 单独 task；由 M3 主线工作自然收纳）.

**G28 contract-test-first blocking 联动** (M3 起)：

- 任意 `python.contract.yml` 增删 `exports[]` 条目 → 必须配套 `tests/contracts/<capability>/
  test_python_contract.py` 内 failing→green 转变
- PR diff 检测 + AST diff；不通过 → blocking

## §CI Gate

**Script gate**: `scripts/sdd/check_python_contracts.py`

- **Phase**: M2 warning / **M3 blocking**（per `sdd/gates.md` G3 切换节奏）
- **Triggers**: `capabilities/*/contracts/python.contract.yml` 任一存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误位置（文件 + 行号 + 期望 vs 实际）
- **Implementation**: AST-based reverse inspection — 把 `module_path` 解析为文件 → `ast.parse`
  → 比对 `exports[]` 声明 vs 实际顶层符号
- **依赖**: `_common.ast_helpers` 全部公开 API + `_common.discovery` capability 扫描器 +
  `_common.yaml_io` contract 解析

**Baseline noise** — V1 已实测 PASS（Stage A 末 in `capabilities/data-agent/safe-sql/`）；M2 期
warning mode 下预期 0 noise；M3 切 blocking 不引入新 friction.

**M2 → M3 切换条件**：

- `--all` 模式在所有 M1 5 pilot capability 上跑通 PASS
- 0 false-positive（不应误判 dataclass field 为缺失 export）
- `_common.ast_helpers` 接口稳定（无 M3 中期 breaking change）

---

> *Phase M2 content — `state: draft`.*
