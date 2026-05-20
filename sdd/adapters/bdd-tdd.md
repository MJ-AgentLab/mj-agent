---
type: sdd-adapter
artifact: bdd-tdd
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Adapter: BDD/TDD (Cross-Cutting)

> Phase M0 skeleton — 第 7 启用 adapter；横切准则（Gherkin 标签约定 / step definitions
> location / red-green-refactor evidence schema / 自动化覆盖率门槛 / contract-test-first 规则）.
> 完整 §Standards / §Automation Strategy / §Evidence Schema 在 Phase M2 内容填充.

## Scope

横切所有 capability 的 BDD scenario + TDD test list；不绑定单一 capability；
其余 6 adapter 文档内 §BDD Rules / §TDD Rules 子节是本 adapter 的 per-stack 落地表现.

## Contract Output

`bdd-tdd.contract.yml`（cross-cutting 准则；不绑定单一 capability）.

## §Standards（TBD: Phase M2）

- Gherkin 标签约定：`@REQ-NNN / @CTR-<slug> / @risk:critical|high|medium|low / @adapter:<name> /
  @hitl`（详 `mj-agent-refactored-structure.md` §19.2 behavior.feature）
- Scenario scope：哪些行为必须 .feature 化（高风险 REQ critical/high → MUST）
- Step definitions location：`tests/bdd/<capability>/steps/`；shared step 在 `tests/bdd/
  shared/`

## §Test Pyramid Integration（TBD: Phase M2）

| Layer | Coverage | Driver |
|---|---|---|
| Unit test（`tests/unit/`）| 函数 / 类公开 API | `pytest` |
| Contract test（`tests/contracts/<dom>/<cap>/`）| capability contract schema | `pytest -m contract` |
| BDD（`tests/bdd/<dom>/<cap>/`）| 业务行为边界 | `pytest-bdd` |
| Integration（`tests/integration/`）| 跨组件 + 真实依赖 | `pytest` + `live_db` fixture |
| Smoke（`tests/smoke/`）| 端到端 + LLM | `pytest -m smoke` |

## §Automation Strategy（TBD: Phase M2）

- 推荐框架：`pytest-bdd`
- 自动化阈值：高风险 critical → 100%（M4 blocking）；high → 70%（M3 warning / M4 blocking）；
  medium / low → manual 可接受（runbook 写原因）
- shared step 提取规则（避免重复 step definitions 跨 capability）

## §Evidence Schema（TBD: Phase M2）

- `evidence/bdd/YYYY-MM-DD_<scenario_or_feature>_pass.md`
- `evidence/tdd/YYYY-MM-DD_<task_or_module>_red_green.md`
- frontmatter 含 `subtype: bdd` 或 `subtype: tdd`；TDD 必填 `tdd_phase: [red / green / refactor
  / contract-test-first]`

## §Red-Green-Refactor Workflow（TBD: Phase M2）

每 high-risk task 的 3 阶段证据要求：

1. **Red** — failing test 截图 + commit SHA
2. **Green** — passing test 截图 + commit SHA
3. **Refactor** — 行为测试不变（同 test list） + structural improvement diff

R-G19 mitigation：AI-generated code 场景下接受 "test alongside code"（red 阶段软要求；G28
contract-test-first 仍严格执行）.

## §Contract-Test-First Rule（TBD: Phase M2）

contract 变更必须先有 failing test（G28 blocking from Phase M3）.

## §Cross-Adapter Rules（TBD: Phase M2）

与现 6 adapter 文档内 §BDD Rules / §TDD Rules 子节互引；本 adapter 是元规则，
具体 stack 落地见各 adapter 文档.

## CI Gate

- G19-G22（BDD 系列）：详 `sdd/gates.md` §3
- G23-G28（TDD 系列）：详 `sdd/gates.md` §3
- 6 个新检测脚本（Phase M2 起逐步落地）：详 `mj-agent-refactored-structure.md` §13.1

---

> *Phase M0 skeleton — `state: draft`. 第 7 启用 adapter；横切准则.*
