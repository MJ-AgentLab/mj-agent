---
type: sdd-adapter
artifact: bdd-tdd
state: draft
version: 0.3
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-01
track: shared
ai_visibility: source-of-truth
---

# Adapter: BDD/TDD (Cross-Cutting)

> Phase M2 内容化 — 第 7 启用 adapter；横切准则.
> 7 子节固定结构：§Standards / §Test Pyramid Integration / §Automation Strategy /
> §Evidence Schema / §Red-Green-Refactor Workflow / §Contract-Test-First Rule /
> §Cross-Adapter Rules.
> cross-ref 蓝图 `spec-anchored-calm-lampson.md` **手册 §25** TDD/BDD 与 SDD 的结合机制
> （8 子节 §25.1-§25.8 全部覆盖；mapping 详各 §X 顶部 cross-ref 行）.

横切定位：不绑定单一 capability；前 6 adapter 文档内 §BDD Rules / §TDD Rules 子节是本 adapter
的 per-stack 落地；本 adapter 是 canonical 源，冲突时以本节为准.

## §Standards

> 本节对应蓝图手册 §25.1 定位 + §25.3 BDD 引入规则（when to add）+ §25.8 不强制 TDD/BDD
> 的场景.

**手册 §25.1 BDD/TDD/SDD 三者关系**（mj-agent 落地）：SDD = 治理骨架（能力/契约/追踪/证据/归
档）；BDD = 行为契约机制（需求理解 + 验收）；TDD = 实现反馈机制（契约满足 + 安全重构）.

**Gherkin 标签约定（5 类；语法 + scope）**：

- `@REQ:<id>` — REQ-NNN 追溯锚；每 scenario 必标（与 `requirements.md` 双向追溯）
- `@CTR:<id>` — contract slug 追溯锚（如 `@CTR:execute-sql`；与 `contracts/*.yml` 双向追溯）
- `@risk:<level>` — `critical` / `high` / `medium` / `low`；触发自动化阈值（详
  §Automation Strategy）
- `@adapter:<name>` — adapter 触发边界；**BDD + contract test 出现；unit test 强制不挂**
- `@hitl` — 触发 4 项专属必停 surface（`sql-guardrail-relax` / `prompt-version-bump` /
  `biz-catalog-sync` / `runtime-skill-content-change`）或 HITL #8（生产 compose 变更）等
  workflow 层 gate

**标签互斥**：`@adapter:X` + `@adapter:Y` 同 scenario 可共存但 BDD 职责分离描述；
`@risk:<level>` 同 scenario 唯一；`@hitl` + `@adapter:<name>` 可共存（hitl 标识触达必停）；
`@REQ` + `@CTR` 可共存（缺一时 traceability gate warning）.

**BDD 引入条件**（per 手册 §25.3 "BDD required when..."）：

- 用户可见行为 / 跨系统行为 / 权限-安全-合规 / Agent-Prompt-Skill 行为 / 数据口径 /
  高风险运维流程 / Docker-runtime 启动与失败行为 / Hotfix 后回归场景

**BDD/TDD 不强制场景**（per 手册 §25.8）：

- 纯文档格式修复 / README 拼写修正 / archive manifest 元数据修复 / 低风险 UI 文案 / 一次性
  spike-research / 历史报告整理 / 无行为变化的依赖注释调整
- 但仍应满足 trace 不被破坏 + CI 基础检查通过 + 不引入 secret + 不误用 archive

## §Test Pyramid Integration

> 本节对应蓝图手册 §25.2 两层循环（BDD 外层 + TDD 内层 + 合并执行链路）.

**两层循环**：

```text
BDD 外层：Discovery → Formulation → Automation → Evidence → Feedback
TDD 内层：Test List → Red → Green → Refactor → Commit → Evidence
```

**合并 SDD 执行链路**：

```text
REQ → BDD Discovery → Acceptance Example → Gherkin / Behavior Contract →
TDD Test List → Red-Green-Refactor → Contract / Unit / Eval / Smoke / Runtime Test →
CI Gate → Evidence → Active / Evolve / Archive
```

**三层职责边界**（mj-agent test layer 对照）：

| Layer | 路径 | Coverage | Driver | `@adapter:<name>` |
|---|---|---|---|---|
| Unit | `tests/unit/` | 函数 / 类公开 API；internal helper；私有符号 | `pytest` | **不挂** |
| Contract | `tests/contracts/<dom>/<cap>/` | capability contract schema；freeze drift | `pytest -m contract` | 挂 |
| BDD | `tests/bdd/<dom>/<cap>/` | 业务行为边界；端到端用户视角 | `pytest-bdd` | 挂 |
| Integration | `tests/integration/` | 跨组件 + 真实依赖 | `pytest` + `live_db` fixture | 视情况 |
| Smoke | `tests/smoke/` | 端到端 + LLM | `pytest -m smoke` | 视情况 |
| Eval | `tests/eval/` | LLM regression（M4+ baseline） | `pytest` | 视情况 |

**`@adapter:<name>` tag 域**：仅 BDD scenario + contract test docstring 出现；Unit test 强制
不挂（防计数膨胀；与 `python.md` §BDD Rules "internal helper → plain pytest" 对偶）；
Integration/Smoke/Eval 视是否触达 adapter 行为边界决定.

## §Automation Strategy

> 本节对应蓝图手册 §25.3 BDD 引入规则 Adoption Criteria + §25.6 CI Gates BDD 部分.

**推荐框架**：`pytest-bdd`（与 mj-agent 现有 `tests/` 框架一致；不引入 `behave` /
`radish` 等并行框架；防 step definition 跨框架不通用）.

**Step definitions 强制位置**：capability 专属 `tests/bdd/<domain>/<capability>/steps/`；shared
`tests/bdd/shared/`（≥ 2 capability 复用同一 step → promote；shared step 命名 prefix
`shared_` 防 namespace 碰撞）.

**自动化阈值（per `@risk:<level>` tag）**：

| Risk | 自动化阈值 | M2 节奏 | M3-M4 节奏 |
|---|---|---|---|
| `critical` | **100%** 强制 | warning | blocking (G19/G20) |
| `high` | **70%** baseline；**100%** 目标；RD9=B 试行降到 50% advisory（M3 末批观察 1 月再定） | warning | blocking (G21) |
| `medium` | **50%** | advisory | warning |
| `low` | manual 可接受（`runbook.md` 写不自动化原因） | advisory | advisory |

**Scenario-to-step 命名约定**：

- `.feature` Scenario 标题 → snake_case step 函数名（`given_` / `when_` / `then_` 前缀）
- Step 命名 behavior-specific 不命名 stage-specific（如 `then_guardrail_rejects_drop_statement`
  优于 `then_step_5_passes`）
- 每 capability ≤ 50 step definition；超阈值触发 refactor 到 `shared/`（防 step explosion）

**未自动化 scenario justification**（手册 §25.6 `bdd-unautomated-justification`；mj-agent
G22）：任何 `@risk:critical` / `@risk:high` 未自动化 scenario → `runbook.md` 必含 justification
段落（原因 / 替代验证手段 / 升级触发条件 / 预计时间）；M3 warning / M4 blocking.

## §Evidence Schema

> 本节对应蓝图手册 §25.7 Evidence（8 项 evidence 要求）+ §25.6 CI Gates evidence 子集.

**目录命名规则**：

- BDD evidence：`evidence/bdd/YYYY-MM-DD_<scenario_or_feature>_pass.md`
- TDD evidence：`evidence/tdd/YYYY-MM-DD_<task_or_module>_<phase>.md`
- 跨 capability 的 evidence 放各 capability 下 `evidence/` 子目录（per capability 自治）
- M5+ archive 时 evidence 跟随 capability 迁移（不抽离到顶层 `archive/`）

**Evidence frontmatter schema**：

```yaml
---
type: evidence
subtype: bdd | tdd
date: 2026-05-21
commit_sha: <40-char SHA>           # 与现 mj-agent evidence frontmatter 约定一致（git 术语 SHA）
scenario_count: <int>               # BDD only
pass_rate: <float>                  # 0.0-1.0
tdd_phase: red | green | refactor | contract-test-first  # TDD only
hitl_triggered: bool
risk_breakdown: { critical: <int>, high: <int>, medium: <int>, low: <int> }
adapter_coverage: [<adapter_name>, ...]
---
```

**高风险变更必录 8 项**（per 手册 §25.7）：

- BDD scenario 结果 + TDD test list + red/green 结果 + refactor 后验证 + CI 结果 + 未自动化
  场景说明 + 人工验收结论 + 后续动作

**BDD evidence 子契约**：

- `.feature` 路径 + pytest-bdd JUnit XML / HTML 报告链接
- 未自动化 scenario 的 justification（per `bdd-unautomated-justification` gate）
- `@risk:high` / `@risk:critical` scenario 必含 `pass_rate: 1.0` 或 justification（source：`runbook.md`，G21+G22 共用，per L121 + L160；R-15-1 resolution）

**TDD evidence 子契约**：

- `tdd_phase: red` → failing test commit SHA + pytest error trace
- `tdd_phase: green` → passing test commit SHA + diff link
- `tdd_phase: refactor` → behavior-stable assertion（同 test list 全 green）+ structural diff
- `tdd_phase: contract-test-first` → contract YAML diff + test diff + green PASS（G28 强制
  pair）

## §Red-Green-Refactor Workflow

> 本节对应蓝图手册 §25.4 TDD 引入规则 + §25.2 TDD 内层循环 Red-Green-Refactor 部分.

**TDD 必走条件**（per 手册 §25.4 "TDD required when..."）：

- 核心业务逻辑 / public interface / bugfix / refactor / contract implementation / ETL
  transformation / Agent tool boundary / Prompt output schema / Docker runtime contract /
  **AI-generated implementation**（mj-agent 主要场景）

**High-risk task 3 阶段证据**：

1. **Red** — failing test commit SHA；必须真正失败（不能 `assert True`）；error 含 expectation
2. **Green** — passing test commit SHA；实装最小化（refactor 单独 commit）
3. **Refactor** (optional) — 行为测试不变（test list 全 green）+ structural diff；commit
   message "refactor:" type prefix（per `[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §4）

**Red-Green-Refactor 软模式 RD10=C**（canonical wording；与 batch 1-3 adapter §TDD Rules 共
用 canonical 表述）：

- AI-generated code 允许 "test alongside code"（同一 PR 内含 test + 实装；**不强制先 commit
  failing test**）
- 人工编写代码仍走严格 red-green-refactor（red commit + green commit + refactor commit 三独
  立 commit）
- R-G19 缓解路径；M4 evidence required gate G8 校验：PR body 含 test list + green pass 证据

**Bugfix regression**（手册 §25.6 `bugfix-regression-test`；mj-agent G24）：bugfix 修复前必先
有 failing test reproducing the bug；M3 warning / M4 blocking；仅 `bugfix/*` 分支触发；与 G28
不同维度（G28 针对 contract YAML diff，regression 针对 issue reproduction）.

**Refactor 行为不变**（手册 §25.6 `refactor-behavior-stable`；mj-agent G27）：`refactor` commit
前后所有 BDD scenario + contract test 必须 green；失败 → 立即 revert（refactor 是
behavior-invariant transformation）；AI-generated refactor 不豁免 RD10=C 软模式（仅适用 red→green
pair；refactor 无软模式）.

## §Contract-Test-First Rule

> 本节对应蓝图手册 §25.6 CI Gates（`contract-test-first` 是 11 个 gate 之一；mj-agent 本地
> 命名为 G28；M3 直接 blocking outlier）.

**G28 contract-test-first** — 是 TDD 唯一 **M3 直接 blocking** gate（其余 gate 走 M2 warning
→ M3 blocking 渐进节奏；G28 是 outlier 因 contract 变更不允许后补 test）.

**触发条件**：

- 任意 `capabilities/*/contracts/*.yml` 字段增删（`exports[]` / `tools[]` /
  `middleware_chain[]` / `hitl_required[]` / `skills[]` / `compose_files[]` 等任一）
- → 必须配套 `tests/contracts/<capability>/test_*_contract.py` 内 failing→green 转变
- → PR diff 检测 + AST diff；不通过 = blocking

**Schema-layer vs Behavior-layer test-first 二分**：

- **Schema-layer**（G28 范围）— contract YAML field 增删 / `freeze_anchor` 重签；validator
  反向校验；**M3 blocking**
- **Behavior-layer**（非 G28；走 BDD `.feature`）— LLM 行为 / `agent.py` 行为 / SKILL body
  行为；走 `@adapter:<name>` BDD scenario + EVAL regression；M4+ EVAL framework baseline 后
  强化（per ADR-024）

**G28 与 6 adapter validator 协同关系**：G28（PR-level test-first gate）强制 contract YAML
diff 配套 failing→green test 转变；6 adapter contract validator（schema 反向校验）做 CI-time
持续反向校验. 两者协同关系：PR-time 单点门 + CI-time 持续守卫；schema-layer drift 任一通道 block.

**手册 §25.6 完整 CI Gate 列表**（mj-agent 对应映射）：

- **BDD gates**：`bdd-feature-syntax` / `bdd-scenario-trace`（mj-agent G19）/
  `bdd-step-coverage`（mj-agent G20）/ `bdd-acceptance-pass`（mj-agent G21）/
  `bdd-unautomated-justification`（mj-agent G22）
- **TDD gates**：`tdd-test-list-required`（mj-agent G23）/ `bugfix-regression-test`
  （mj-agent G24）/ `changed-code-has-test`（mj-agent G25）/ `red-green-evidence`
  （mj-agent G26）/ `refactor-behavior-stable`（mj-agent G27）/
  **`contract-test-first`（mj-agent G28；M3 blocking outlier）**

## §Cross-Adapter Rules

> 本节对应蓝图手册 §25.5 Traceability 规则（6-node 追溯链）+ 元规则跨 adapter 一致性责任.

**Traceability 6-node 追溯链**（per 手册 §25.5）：

```text
REQ → CONTRACT → TEST → TASK → PR → EVIDENCE
```

- 每个关键 BDD scenario 必须能追溯到上述 6 节点（缺一不可作 SDD contract evidence；测试可
  存在但不算 contract evidence）
- 每个关键 TDD test 必须能追溯到 REQ 或 CONTRACT（最低要求；6 节点链推荐但非强制）
- mj-agent 实装路径：`trace.yml` 在各 capability 下维护 6-node mapping；M3 G2 traceability
  blocking 切换后强制 sync

**6-adapter 互引矩阵**（与前 6 adapter §BDD Rules / §TDD Rules 子节互引规则）：

| Adapter | §BDD Rules 触发边界 | §TDD Rules contract-test-first + RGR 软模式 |
|---|---|---|
| `python` | 公开 API 行为 / `ValueError` `RuntimeError` 抛出 / `ToolMessage` envelope；**不**为 lint 加 tag（走 ruff/mypy）；私有 `_` 符号走 plain pytest | `_common.ast_helpers` 4-API；RD10=C 软模式 + G28 联动 |
| `langchain-agent` | "意图 → 拒绝/接受 + tool call 顺序" 行为；`@risk:high` 绝对 BDD 必填；`agent.py` refactor must not change behavior `.feature`；middleware + `@hitl` 双标 | tool boundary test 先写；middleware 新增触发 G28；local `_extract_assign_value` / `_extract_list_items`（M3+ promote 候选） |
| `prompt` | **schema invariant only** per C4；`@adapter:prompt` + `@hitl` 必双标；**不**为 prose typo 加 tag | schema-layer test-first 限定；M4-FU EVAL framework 待 baseline；与 `runtime-skill` 共 `_common.frontmatter` |
| `runtime-skill` | body 加载 + system prompt 拼接 + loader strip 行为；`@adapter:runtime-skill` + `@hitl` 必双标；**不**为 frontmatter schema validation 加 tag | schema-layer test-first；body `content_hash` 双锁；与 `prompt` 共 `_common.frontmatter`；G28 联动 |
| `claude-code-skill` | trigger fidelity（`description` 正向 + 反向）；`@risk:high` SKILL（git-commit / git-push / env-teardown）必填；**不**为 ADR-013 schema validation 加 tag | schema-layer（`name` + dir + namespace + description ≥ 200 chars）；走 `Path.read_text` + `_common.parse_native_frontmatter` 读 ADR-013 2-field frontmatter，**无** markdown-body-only fallback 路径 |
| `docker-container` | 容器运行时 + compose 装配 + healthcheck + network attach；HITL #8 走 **workflow 层** NOT adapter 层（§CI Gate 不开 Manual HITL gate）；**不**为 Dockerfile lint 加 tag（走 hadolint） | schema-layer test-first；compose dry-run；`docker-bdd-scenario-check` + `docker-tdd-contract-test` 双 gate；`_common.yaml_io` 共享 |

**Matrix sync 责任**（M3 advisory → M4+ blocking 升级路径 per Q-A 加固点 2）：

- **M3 期**：matrix sync 作为 PR checklist 必勾项（advisory；reviewer 人工核对；与本节
  §Cross-Adapter Rules 正文一致性）
- **M4+**：视 M3 观察期 drift 实绩升级为 blocking gate（advisory 模式 > 1 次 drift 实例则
  触发升级；脚本化 matrix-vs-adapter-doc consistency check 是 M4 范围工作）
- 防 6 adapter §BDD/§TDD Rules 演进出现 drift；本节是 cross-adapter 一致性责任落地节

**导航规则简述**：撰写新 BDD/TDD → 查 capability + adapter → adapter §BDD/§TDD Rules → 本节
矩阵 → 写 test；修改 adapter §BDD/§TDD Rules 子节 → 同步本节矩阵 + 跑 validator；本文件是
canonical 源，冲突以本节为准（M5+ 新 adapter 走 matrix sync PR 同流程扩矩阵）.

---

> *Phase M2 content — `state: draft`.* 第 7 启用 adapter；横切准则；cross-ref 手册 §25 全 8 子节（§25.1-§25.8）.
>
> *v0.3（2026-09-01）：#497 ① 的 **matrix sync**（触发 = 本节自有规则「修改 adapter §BDD/§TDD
> Rules 子节 → 同步本节矩阵」，而 #497 改了 `claude-code-skill` adapter 的 §TDD Rules）。
> ⚠ **改动面比初判窄**：该单元格原文的三条机制断言**逐条为真**且未改 —— 执行体确实不调
> `load_frontmatter`（全仓无此函数，`_common` 提供的是 `parse_native_frontmatter`）、确实走
> `Path.read_text`（`:63`）、确实用正则（`:55` 的 namespace pattern）。唯一更正的是**形容词主语**
> 「markdown-body-only」—— 它暗示那些 SKILL 没有 frontmatter，而该状态从未存在（成因是 V4 执行体
> `yaml.safe_load()` 的 parser bug，`03f1bc7` / `a5614c4`）。矩阵其余 5 行未动。*
