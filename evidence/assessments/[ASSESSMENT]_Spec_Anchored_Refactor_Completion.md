---
type: assessment
domain: SDD
summary: 蓝图 26 维对照评估 spec-anchored refactor 完成度（意图达成 ~92%）；六项登记外缺口经 5-PR 链 #247-#251 对账闭环
tags:
  - assessment
  - sdd
  - governance
  - completion-audit
aliases:
  - Spec-Anchored Refactor Completion Assessment
  - 重构完成度评估
created: 2026-06-10
updated: 2026-06-11
state: draft
version: v1.1
track: shared
owner: ranzuozhou
dimensions:
  - blueprint-conformance
  - debt-disposition
  - gate-baseline-truth
  - registry-reconciliation
period: 2026-05-20 ~ 2026-06-11
---

# mj-agent Spec-Anchored Refactor：目标蓝图 vs 实际状态 完成度评估

> **评估范围**：mj-agent Spec-Anchored Refactor（ADR-031；M0-M6 全周期）——三柱结构 /
> 治理 gate / AI 上下文工程 A1-A6 / 蓝图 §21 全 26 维度
> **评估周期**：2026-05-20 ~ 2026-06-11（M0 启动 → M6 closure → completion-audit 链 #247-#251 合入）
> **评估维度**：blueprint-conformance / debt-disposition / gate-baseline-truth / registry-reconciliation
> **版本**：v1.1（2026-06-11）——§4.2 补"处置去向"列与 repo registry 对账闭环 + §4.3 v1.1 收口段；
> v1.0（2026-06-10）为原始评估快照，§0-§3 / §5 / §6 保持 v1.0 原文不动（历史记录）
> **对比基线**：蓝图 `mj-agent-refactored-structure.md` v2.2（vault `sdd-development/mj-agent/`，
> 2026-05-20）§1-§21
> **被评对象**：mj-agent `develop` @ 4df3c83（M6 closure 后，PR #245 之后）；v1.1 对账态 @
> 3683d10（#251 合入后）
> **撰写**：Claude Code（3 个 Explore agent 全仓盘点 + 定点核验；v1.1 对账经 11-agent
> 对抗性验证 workflow 复核）。源稿 = vault 同名草稿（v1.0/v1.1），经 `/mj-agent-doc-author`
> 升格入库。

---

## §0 TL;DR

**总判断：重构主体达成。** 蓝图 §21 的 26 个关键变更维度中：

| 状态 | 计数 | 含义 |
|---|---|---|
| ✅ 完成 | **19** | 与蓝图一致落地（个别带轻微备注） |
| 🔄 部分 / 等效实现 | **3** | trace.yml（结构成、内容占位未兑现）、CI Gate（定义全、接线部分）、LSP A5（声明成、激活机制存疑） |
| ⏳ 显式 defer | **2** | Skill 42 终态（evidence-4 → Phase-2 有登记）、TDD test list（G23 flip → M6-FU#9 有登记） |
| ❌ 缺口（无登记） | **2** | tests/ 矩阵 7/11、branch/commit type 11 扩充未做 |

**三柱结构（sdd/ kernel + capabilities/ + policies/）100% 建成**；归档 ceremony、CLAUDE.md 601→150、
AGENTS.md/Codex 边界、A1-A6 大代码库实践、8 类 issue 模板、PR 模板 7 字段全部落地。

**最值得关注的 4 个"登记外"事实**（既不在 Phase-2 defer 也不在 M6-FU register；v1.1 注：
已全部闭环，见 §4.2 处置去向列）：

1. **trace.yml 占位未兑现且与现实脱钩**：5 个 pilot 的 trace.yml 全部 BDD 条目
   `automation_status: unautomated`，30+ 个 `TBD-M3/M4` 测试/证据占位指名的文件
   （`tests/unit/test_llm.py`、`test_dsn_options.py`、`tests/docker/*` 等）**至今不存在**；
   而 tests/bdd 的 pytest-bdd 自动化（9P/7SKIP）已在 CI blocking 运行却未回写 trace。
2. **4 个 gate 有定义无执行体**：G20（BDD step coverage）/ G27-G28（TDD refactor/contract-test-first）
   无脚本；G4（plan-vs-diff）以 PR 模板人工声明替代；G7（secret exposure）无脚本化；
   G3（check_contracts）仍 M0 skeleton（注释称 "Phase M4 real impl tracked separately"，但 M4 已闭）。
3. **branch/commit type 11 扩充未做**：`policies/git-branching.md` 内留 "Phase M6 扩充至 11 type" TBD，
   M6 已闭未执行、未入任何 register。
4. **tests/ 矩阵 7/11**：db/、data_quality/、agents/、prompts/、docker/ 五个子目录未建；
   `tests/contract`（单数）未改名复数、未按 capability 分组。

---

## §1 方法与证据源

- **基线**：蓝图 v2.2 全文；§21 "关键变更汇总" 26 行作为评估主轴（§2），§1-§20 逐域差异收进附录（§5）。
- **状态四分类**：
  - ✅ **完成** — 与蓝图一致落地；
  - 🔄 **部分/等效** — native 变体或部分达成（机制不同但目标达成，或结构成内容欠）；
  - ⏳ **显式 defer** — 未做但在 `plans/[PLAN]_spec_anchored_refactor.md` 的 Phase-2 defer / M6-FU register 有登记；
  - ❌ **缺口** — 蓝图有、实际无、且**无登记**（或 in-file TBD 已超期）。
- **实际状态证据源**：
  - `plans/[PLAN]_spec_anchored_refactor.md`（state: completed；`phase_progress` M0-M6 全 completed；
    M6 closure 段的 ✅/⏭Phase-2/🔁M6-FU 标注；M4-FU Registry 对账表）
  - `evidence/metrics/2026-06-08_sdd_structure_metrics.md`（M6 闭幕 metrics：5 capabilities / 21 contracts / 17-18 evidence）
  - `.github/workflows/ci.yml`（gate blocking/warning 实况）
  - git tags：`phase-m2/m4/m5/m6-complete`
  - 全仓目录实测清单（sdd/ 41 文件、policies/ 10、decisions/ 22、capabilities/ 97、archive/ 28、
    .claude/skills/ 34、tests/ 7 子目录、scripts/sdd/ 20）
- **注意**：蓝图自身的 Phase 0-6 编号与实施采用的 M0-M6 里程碑不是一一映射；凡蓝图标注
  "Phase 2+/4 落地" 的项（tool-chain / memory-checkpointer / entry-points / secrets-pipeline
  四个后续 capability）**不计入差异**。

---

## §2 蓝图 §21 spine 对照总表（26 维度）

| # | 蓝图维度（§21） | 蓝图目标 | 实际状态 | 判定 | 证据 |
|---|---|---|---|---|---|
| 1 | 组织单元 | Capability Package（~12 artifact 套件） | 5 pilot 全建，套件齐（spec/req/design/tasks/runbook/trace/contracts/evidence） | ✅ | `capabilities/{data-agent,infrastructure}/`；metrics 报告 §1 |
| 2 | 治理元规则 | sdd/ kernel（5 顶层 + workflows + adapters + templates） | 5 顶层 + 6 workflows（+execution-loop 第 7）+ 7 adapters（+contract.md 第 8）+ 22 templates | ✅（含增项） | `sdd/` 41 文件 |
| 3 | Business Policy | policies/ 9 文件 | 9/9 全齐 + release.md 额外 | ✅ | `policies/` 10 文件 |
| 4 | ADR 位置 | docs/adr/ → decisions/ | 平移完成（M5）；INDEX.md + ADR-031 + 22 active；docs/adr/ 已不存在 | ✅ | `decisions/`；蓝图写 "30 active" 系当时口径，9 个已按 decoupling 决策归档 + ADR-032 新增 |
| 5 | Contract | 每 capability ≥3（高风险含 behavior.feature） | 21 件（15 .contract.yml + 5 behavior.feature + 1 runtime.expected.yaml）；每 cap ≥4 | ✅ | metrics 报告 §2 |
| 6 | Traceability | trace.yml per capability（schema v1.2 含 BDD 层） | 结构 ✅：5/5 schema v1.2、7 层链（REQ→BDD→CONTRACT→TEST→TASK→PR→EVIDENCE）全有；**内容 ❌：BDD `automation_status` 全 unautomated、30+ TBD-M3/M4 占位指名的测试文件不存在、tests/bdd 已落的自动化未回写** | 🔄 部分 | 各 `capabilities/*/*/trace.yml`；llm-provider 自注 "0 existing tests; 12 TBD-M3 placeholders" |
| 7 | CI Gate | G1-G17 + 8 stack + G19-G28 ≈ 33 个 | **定义 ✅**：sdd/gates.md G1-G28（G10/13/16/17 RESERVED）+ 8 adapter §CI Gate + A1-A6/OB1-OB5；**接线部分**：blocking 14+（G1/G2/G9/G11-12/V1/V3/V4/V5/V7/G8/G19/G21/G22/G24+BDD），warning 5（G14/15、archive-INDEX、V2、V6、G23 → ⏳M6-FU），**无执行体 ❌：G3(skeleton)/G4/G7/G20/G25/G26/G27/G28** | 🔄 部分 | `sdd/gates.md`；`ci.yml`（grep 证实 G3/G20/G25-28 无 step） |
| 8 | Skill 分层 | SKILL_INDEX 5-layer + Phase 6 增 8 → 42 终态 | SKILL_INDEX.md 5-layer ✅；现 34 skill；**4 evidence-* → ⏳Phase-2（有登记）**；4 stack-*（蓝图自标 Phase 2-3）未建未登记（V5 `--compose-config` flag 部分覆盖其一） | ⏳（evidence 部分） | `.claude/skills/SKILL_INDEX.md`；plan |
| 9 | 旧 STANDARD 命运 | 整体 archive ceremony → archive/rule/ | 完成（M6 PR4，2026-06-04）：tri-track 全版本 + MCP gov 共 13 文件 + archive.yml + TOMBSTONE | ✅ | `archive/rule/` |
| 10 | CLAUDE.md 大小 | ~580 → ≤150 行 | **恰好 150 行**（#243：601→150，R-G4 6-case validated） | ✅ | 根 CLAUDE.md |
| 11 | AGENTS.md | 新建（Codex 非参与边界） | 68 行，Codex read-only roster 齐 | ✅ | `AGENTS.md` |
| 12 | Evidence | evidence/ per capability（含 bdd/+tdd/） | 5/5 有 evidence/，bdd/+tdd/ 子目录齐，17-18 文件；G8 blocking PASS | ✅ | metrics 报告 §3；postmortems/assessments 子目录部分 capability 缺（.gitkeep 级，轻微） |
| 13 | Archive 防误读 | archive.yml ai_visibility 必填 | 全部 archive.yml 含 ai_visibility（值 reference）；G11/G12 blocking | ✅ | `archive/*/archive.yml` |
| 14 | Tests 子目录 | 5 → 11 | **7/11**：unit/contract(单数)/bdd/eval/integration/smoke；缺 db/、data_quality/、agents/、prompts/、docker/；未改名 contracts/ 复数、未按 capability 分组 | ❌ | `tests/`；docker-compose trace.yml 的 TBD 正指向不存在的 tests/docker/* |
| 15 | Issue 模板 | 0 → 8 类（含 archive/runtime/agent） | 8/8 全建 | ✅ | `.github/ISSUE_TEMPLATE/` |
| 16 | Branch type | 5 → 11 | **仍 5**；git-branching.md 留 "Phase M6 扩充至 11 type" TBD；commit type 同样未扩 11；M6 已闭、未入 register | ❌ | `policies/git-branching.md` §1/§2 |
| 17 | Adapter | 隐式 → 7 启用（各加 §BDD/§TDD Rules） | 8 个（7 + contract.md），**全部含 §BDD Rules + §TDD Rules** | ✅ | `sdd/adapters/` |
| 18 | Codex 协作边界 | AGENTS.md + CLAUDE.md §Codex Status | 双文件齐 + policies/ai-agent.md §1 | ✅ | — |
| 19 | BDD 行为契约 | 5 pilot 各 ≥1 behavior.feature + steps 在 tests/bdd | 5/5 feature + tests/bdd 5 个 pytest-bdd 绑定模块（CI blocking 9P/7SKIP）；未自动化 scenario 走 G22 runbook justification（蓝图自身规则允许） | ✅ | `capabilities/*/contracts/behavior.feature`；`tests/bdd/` |
| 20 | TDD test list | tasks.md tdd.test_list[] 必填 + evidence/tdd/ | 机制在（G23/G24 脚本 + evidence/tdd/ 目录）；G23 仍 warning（15P/5W），tasks curation → **M6-FU#9 有登记**；G24 blocking ✅ | ⏳ | plan M-FU#9；`ci.yml` |
| 21 | 分层 CLAUDE.md（A1+B1） | root ≤150 + 4 subdir（≤100/≤100/≤80/≤80） | 5 个全建（150/83/114/74/98）；**长度软超**：capabilities 114>100、docker 98>80 | ✅（备注） | 各 CLAUDE.md |
| 22 | Stop hook 自改（A2） | hooks/stop-claude-md-improver → diff 草案 → user Edit | hook + on-stop.ps1 + settings.json Stop 配置 + evidence/ai-context-audit/ 产出齐；improver body 深化随 EVAL 链至 Phase-2（M4-FU-A2-HOOK-IMPROVER-BODY 有登记） | ✅（深化⏳） | `.claude/hooks/`；`evidence/ai-context-audit/` |
| 23 | Subagent explore vs edit（A3） | 写入 policies/ai-agent.md | §2 落地（含 a3-readiness-eval 证据） | ✅ | `policies/ai-agent.md` §2 |
| 24 | .claudeignore + codebase map（A4） | 仓库根 .claudeignore + docs/INDEX.md 升级 | 双双落地（INDEX.md 自述 codebase map 角色） | ✅ | 根 `.claudeignore`；`docs/INDEX.md` |
| 25 | LSP integration（A5） | plugins.json 启用 pyright-lsp + symbol-first 政策 | plugins.json 声明 4 插件（含 pyright-lsp）✅ + ai-agent.md §3 ✅；**但 settings.json `enabledPlugins: {}` 空对象，两文件未联动；当前实际 symbol-first 能力由 serena MCP 承担** | 🔄 | `.claude/plugins.json`；`.claude/settings.json` |
| 26 | Review cadence（A6） | 每 3-6 月审计 → evidence/ai-context-audit/ | 政策入 ci-gates.md §4 + documentation.md；2026-Q2.md 审计产出已在 | ✅ | `evidence/ai-context-audit/2026-Q2.md` |

---

## §3 差异明细（仅 🔄/⏳/❌ 展开）

### D-1 ❌ tests/ 矩阵 7/11（spine #14）

- **蓝图**：§9 — 11 子目录矩阵（unit / contracts复数 / bdd / db / data_quality / smoke / integration /
  agents / prompts / docker / eval）+ 关键迁移（qcm alignment test → `tests/contracts/data_agent/biz_catalog/`）。
- **实际**：7 子目录；`tests/contract/`（单数）未改名未分组；qcm alignment test 仍在
  `tests/contract/test_qcm_catalog_alignment.py`；db/、data_quality/、agents/、prompts/、docker/ 未建。
- **连锁影响**：docker-compose 与 mcp-gov 两个 capability 的 trace.yml TBD 占位（如
  `tests/docker/test_compose_config_dev.py`、`tests/contract/test_mcp_inventory.py`）指向**不存在的目录/文件**——
  目录缺失与 trace 占位是同一笔债的两面。
- **登记状态**：无（不在 Phase-2 defer / M6-FU）。
- **处置建议**：立 M-FU/Phase-2 issue 二选一：(a) 补建目录并迁移（结构迁移 PR 须跑全
  `pytest tests/unit tests/eval` 套件——前车之鉴 #217）；或 (b) 正式裁剪蓝图（ADR-031 amendment /
  blueprint v2.3 标注 "11→7 re-scope"），让 trace TBD 改指现存路径。**两者必居其一，否则 trace 永远无法兑现。**

### D-2 🔄 trace.yml：结构完成、内容占位未兑现（spine #6）

- **蓝图**：§19.3 — trace.yml v1.2 七层链 + automation_status: automated 时 tests[] 须含 tests/bdd 行。
- **实际**：
  - 结构：5/5 schema v1.2、七层全有、cross_capability_refs 有（R-G7 合规）——**超出最初骨架预期**；
  - 内容：全部 BDD 条目 `automation_status: unautomated`；约 30+ `TBD-M3/M4` 测试与 evidence 占位，
    指名文件（`tests/unit/test_llm.py`、`test_dsn_options.py`、`test_execute_sql_envelope.py`、
    `test_middleware_wrap_integration.py`、`tests/docker/*`、`scripts/sdd/check_a14_gate.py` 等）经核**全部不存在**；
  - 脱钩点:tests/bdd 5 模块已实际自动化部分 scenario（CI blocking 9P/7SKIP），trace 未回写
    automation_status / tests[]。
- **为何 CI 仍绿**：G2 校验链路结构而非占位兑现；G21/G22 在 Stage E 经 runbook justification
  curation（M-FU#7，#198）通过——属"按当前态校准 gate"而非"兑现蓝图自动化"。
- **登记状态**：无整体登记（M-FU#1 只修了 llm-provider REQ-003 单点绑定）。
- **处置建议**：立 "trace.yml refresh" 专项（可并入 D-1 的同一 issue）：刷 automation_status、
  把 tests/bdd 已落条目回写、TBD 占位逐条裁决（兑现 / 改指 / 删除 + runbook 说明）。
  这是**最影响 SDD 可信度**的一项——trace 是三柱的"可溯源"支柱，占位长期失实会让 G2 沦为形式校验。

### D-3 🔄 CI Gate：定义全集、执行体部分（spine #7）

- **蓝图**：§13.1 — 21 个 scripts/sdd 脚本，G4/G7/G20/G25-28 各有专属脚本。
- **实际**：scripts/sdd 19 脚本 + _common/（含蓝图外的 check_capability_evidence_required G8、
  check_runtime_skill_contracts V7）。缺 4 执行体 + 1 skeleton：
  | Gate | 蓝图脚本 | 现状 |
  |---|---|---|
  | G4 plan-vs-diff | check_plan_vs_diff.py | 无脚本；PR 模板 "Plan-vs-Diff Scope Declaration" 人工声明 + Stage 9 scope-drift skill 替代 |
  | G7 secret exposure | check_secret_exposure.py | 无脚本；依赖 .gitignore/.dockerignore + policies/security.md 纪律 |
  | G20 BDD step coverage | check_bdd_step_coverage.py | 无脚本（G22 runbook justification 间接兜底） |
  | G25/G26 | check_tdd_test_list 合并校验 | 脚本在但 ci.yml 只跑 `--check g23/g24` |
  | G27/G28 refactor/contract-test-first | check_tdd_refactor_contract.py | 无脚本 |
  | G3 contracts | check_contracts.py | M0 skeleton；注释 "Phase M4 real impl tracked separately" 但 M4 已闭、无 register 条目 |
- **另**（⏳ 已登记不重复展开）：G14/G15(/G17) + G23 blocking flip → M6-FU-G14G15-BLOCKING-FLIP；
  V2/V6 warning（SKIP-CLEAN / skeleton）。
- **登记状态**：G4/G7/G20/G25-28/G3 **无登记**。
- **处置建议**：在 M6-FU-G14G15-BLOCKING-FLIP issue 内追加一节 "gate 执行体缺口盘点"，
  逐个裁决：实装 / 以现替代机制为准（修订 sdd/gates.md 把替代机制写为 canonical）/ 撤销
  （走 M4-FU-V4-MODE-B-IMPL 同款 WITHDRAWN ceremony）。**defined-but-unenforced gate 留越久，
  gates.md 的权威性损耗越大。**

### D-4 ❌ branch/commit type 11 扩充未做（spine #16）

- **蓝图**：§21 行 16 + §5 git-branching（11 branch type + 11 commit type + 对齐矩阵，落地 Phase 0/6）。
- **实际**：`policies/git-branching.md` §1 仍 5 branch type，§2 留两处 TBD
  （"Phase M6 扩充至 11 type" / "TBD: Phase M6 — 扩充至 11 commit type"）；M6 闭幕未做、未登记。
  反讽点：**issue 模板 8 类（archive/runtime/agent）已建**，但对应 branch type 未扩——
  新三类 issue 落地时只能挂在现有 5 type 上。
- **处置建议**：三选一并更新 git-branching.md 去 TBD：(a) 补扩 11 type（牵动
  guard-git-workflow.ps1 + commit STANDARD + PR 模板）；(b) 正式裁剪为 5 type 维持
  （修订蓝图预期，TBD 改为 declined 记录）；(c) 折中只补 issue-template 对应的 3 类。
  按 mj-agent "门可改判定口径但须 owner 拍板 + 登记" 的先例，这属 owner 决策项。

### D-5 ⏳ Skill 42 终态（spine #8）

- **蓝图**：§20 — 34 + 8 = 42（4 evidence-* 标 Phase 6 新增；4 stack-* 标 Phase 2-3 新增）。
- **实际**：34；SKILL_INDEX.md 5-layer 双索引 ✅。
  - 4 evidence-*：**⏳ Phase-2 有登记**（plan M6 closure）。
  - 4 stack-*（docker-contract / compose-config / prompt-regression / agent-eval）：未建、未登记；
    其中 compose-config 用途已被 V5 `--compose-config` flag 部分覆盖；prompt-regression / agent-eval
    实质依赖 EVAL framework（已 Phase-2），事实上链式顺延。
- **处置建议**：在 Phase-2 规划时把 4 stack-* 显式并入 EVAL/evidence 工作包或显式撤销，
  消除"蓝图有、登记无"的悬置态。

### D-6 ⏳ TDD test list 兑现（spine #20）

- **实际**：G24（bugfix regression）blocking ✅；G23 warning（15P/5W —— 5 个 critical/high task
  缺 tdd.test_list）→ **M6-FU#9 G23-TASKS-CURATION 有登记**；evidence/tdd/ 目录在但多为占位。
- **处置建议**：随 M6-FU#9 执行即可；无额外缺口。

### D-7 🔄 LSP A5 激活链路（spine #25）

- **实际**：`.claude/plugins.json` 声明 enabledPlugins=[pyright-lsp, claude-md-management,
  superpowers, feature-dev]（learn-kit 留备用，季度 review 注明）；但 `.claude/settings.json`
  `enabledPlugins: {}` 为空对象，两文件未联动；当前会话的 symbol-first 实际由 **serena MCP** 承担
  （find_symbol / find_referencing_symbols 等），效果达成但与蓝图指定机制不同。
- **处置建议**：A6 季度审计时核一次 plugins.json 的实际生效性；若 serena 已是事实标准，
  修订 ai-agent.md §3 + plugins.json rationale 把 serena 写为 canonical symbol-first 通道。

### D-8 🔄 docs/ 过渡处置（§16，spine 外）

- **蓝图**：Phase 5 末 docs/ 整体归档（_templates Phase 3 弃用 / _baselines 迁 capability /
  infrastructure 拆解 / runbook+assessments 迁 capability）。
- **实际**：M5 **re-scope（#214）**：ADR 平移 ✅、tri-track 归档 ✅、INDEX→codebase map ✅、
  assessments 迁 capability evidence ✅（infrastructure/evidence/assessments/ 有实例）、
  runbook 并入 infrastructure/cicd ✅；但 docs/ 保留为 active 12-type canonical track
  （rule/ 2 个正交 STANDARD + _templates 15 文件 + guide/glossary/infrastructure），
  `docs/_templates` 未弃用（与 sdd/templates 双轨分工：canonical 文档模板 vs capability artifact 模板，
  CLAUDE.md 仍指向前者）。
- **判定**：🔄 等效实现，**有正式决策记录**（M5 re-scope #214 + policies/documentation.md
  path-to-track 树），非缺口。

### D-9 轻微缺口汇总（§5 附录细目，单列免漏）

| 项 | 蓝图位 | 实际 | 建议 |
|---|---|---|---|
| docker/healthchecks/healthcheck.sh | §10 | 无目录；healthcheck 内联 compose | 接受偏差（compose 内联为事实标准），蓝图侧标注 |
| db/ 占位 + grants.contract.yml | §11 | 未建 | 并入 Phase-2 memory-checkpointer capability 时一并裁决 |
| prompts/ 顶层 + INDEX.md | §12 | 未建（蓝图预留"评估后可不迁"分支；system.md 留 src/ 已演进至 v1.8） | 补一行显式评估记录（如 ADR-031 amendment 或 plan 备注），关闭悬置 |
| diff_biz_schema.py 改名并入 sdd/ | §13.2 | 未改名仍在 scripts/ 根 | 低优先；随下次 scripts 整理 |
| settings.json deny 4 必停双保险 | §15 | deny 仅 rm -rf/Remove-Item/del + .env 三态；无 Edit(guardrail/precheck) / Edit(secrets*.enc) 条目 | 实际由 guard-git-workflow.ps1 hook + HITL 纪律 + auto-mode classifier 承担；建议 A6 审计时补 deny 条目成本极低，可补 |
| CLAUDE.md 长度软超 | §17.1 | capabilities/ 114>100、docker/ 98>80 | OB1 级观察项，可不动 |
| GLOSSARY ~150 行 / README ~200 行软上限 | §2 | 349 / 251 | 软上限，接受 |

---

## §4 defer-register 对账

### 4.1 登记内（⏳ 合规顺延——不是缺口）

| 项 | 登记位 | 去向 |
|---|---|---|
| EVAL framework authoring-spec port | plan M6 closure | Phase-2（Q4 owner 决策） |
| EVAL baseline run | plan M6 closure | Phase-2 |
| 4 个 mj-agent-evidence-* skills | plan M6 closure | Phase-2 |
| scripts/sdd metrics 自动化 generator | plan M6 closure | Phase-2（M6 以手工 snapshot 交付 ✅） |
| G14/G15(/G17) + G23 blocking flip | plan M6-FU-G14G15-BLOCKING-FLIP | M6-FU（prereq: forward-ref rework + owner ci-blocking-gate-toggle 必停） |
| mcp-server-governance promotion（drafting→active） | M4-FU-MCP-GOV-PROMOTION-DEFER | M6-FU |
| GUIDE staleness sweeps | plan M6 closure | M6-FU（pre-existing） |
| A2 hook improver body 深化 | M4-FU-A2-HOOK-IMPROVER-BODY（blocked_by EVAL） | 链式随 EVAL → Phase-2 |
| V4 Mode B per-skill 校验 | M4-FU-V4-MODE-B-IMPL | **WITHDRAWN**（M5-PR6 正式撤销 + 理由：Mode A + content_hash freeze HITL 已足）——蓝图项被有记录地裁掉的范例 |

### 4.2 登记外（❌ 本评估新发现的缺口）→ v1.1 全部闭环

> v1.1 对账：6 项全部"修复或 ceremony 登记"，登记外状态清零。处置载体 = repo
> `plans/[PLAN]_spec_anchored_refactor.md` 的 **Post-M6 Completion-Audit Disposition
> Registry**（M6-FU batch；2026-06-10/11；12 行）。修复链：audit PR1 #247 → PR2 #248 →
> PR3 #249 → PR4 #250 →（验证 workflow 增补修正回灌各 PR）→ owner 决策 follow-up #251；
> 全部合入 develop（3683d10）。

| 项 | 严重度 | 建议处置（v1.0） | 处置去向（v1.1 对账） |
|---|---|---|---|
| trace.yml TBD 占位未兑现 + automation_status 脱钩（D-2） | **高**（侵蚀可溯源支柱可信度） | 专项 issue：refresh + 逐条裁决 | ✅ **已修复** #247（`M6-FU-TRACE-AUTOMATION-TRUTH-UP`）：13 翻 `automated` / 4 留 honest；~54 占位消灭（真绑定 / 新测试 / re-scope 指针）；G22 基线 15P→**4P/0W/0F**。v1.0 一处修正：`evidence/bdd/` 实际存在（safe-sql 3 份真实证据，已改指）。衍生发现另登记：兄弟文档 111 处 TBD-M3/M4 → `M6-FU-CAPABILITIES-TBD-SWEEP` 🟡 Phase-2 |
| tests/ 矩阵 7/11 + contract 未改名分组（D-1） | 高（与 D-2 同源） | 与 D-2 合并裁决：补建 or 裁剪蓝图 | ✅ **混合裁决落地**：3 个真缺口单测 #247 补建（test_llm / test_dsn_options / test_execute_sql_envelope，17 tests）；tests/docker → `M6-FU-TESTS-DOCKER-PHASE2-RESCOPE` ⏳；contract 改名 + 其余子目录 → `M6-FU-TESTS-CONTRACT-DIR-RENAME-RESCOPE` ⏳（均 #249 registry） |
| G4/G7/G20/G25-28 无执行体 + G3 skeleton（D-3） | 中（gates.md 权威性） | 并入 M6-FU gate issue：实装 / 替代机制 canonical 化 / WITHDRAWN | ✅ **对账+轻实装** #248（`M6-FU-GATES-TRUTH-UP`）：G3 重写实装（5P/0W/0F）+ G7 新建（实装时暴露 root .dockerignore gap，owner-approved #251 关闭 → 3P/0W/0F）+ G25 子旗；G4/G20 → manual-canonical；G26 → `M6-FU-G26-RED-GREEN-WITHDRAWN` ✅ WITHDRAWN；G27/G28 → `M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER` ⏳ Phase-2；gates.md v0.2 阻塞模式真值化（draft→active） |
| branch/commit type 11 扩充 TBD 超期（D-4） | 中（与 8 issue 模板不对称） | owner 三选一裁决 + 去 TBD | ✅ **DECLINED 裁决** #249（`M6-FU-BRANCH-TYPE-5LOCK`）：维持 5 branch type + 7 commit type，Decision 块含理由与复活条件；其余 in-file TBD → `M6-FU-POLICIES-TBD-SWEEP` 🟡（20 块 + 3 footer 全量登记，Phase-2） |
| 4 stack-* skills 悬置（D-5） | 低（事实链至 Phase-2 EVAL） | Phase-2 规划时显式并入或撤销 | ✅ **已登记** #250（`M6-FU-STACK-SKILLS-PHASE2` ⏳）：compose-config 已被 `check_docker_contracts --compose-config`（BLOCKING）部分覆盖；prompt-regression / agent-eval 链至 EVAL Phase-2 |
| D-9 轻微项 ×7 | 低 | 按表内建议分流 | ✅ **七项全分流**：settings deny 双保险 → #250（+12）+ #251（+2，5 必停面全硬锁）；prompts/ 评估记录 → `M6-FU-PROMPTS-TOPLEVEL-NO-MIGRATE` ✅（不迁，不开 ADR）；其余 5 残项 → `M6-FU-D9-RESIDUAL-ACCEPT` ✅ accepted+annotated（healthcheck 内联接受 / db/ 占位随 Phase-2 memory-checkpointer / diff_biz_schema 改名低优 / CLAUDE.md 软超 OB1 接受 / GLOSSARY-README 软上限接受） |

### 4.3 对账结论

M6 closure 的 defer 纪律**总体良好**——大额未完项（EVAL、evidence skills、gate flips、mcp-gov）
全部有登记有去向，且有 WITHDRAWN ceremony 先例。缺口集中在两类：
(1) **trace/tests 占位债**——结构先行、内容兑现被 gate-calibration 掩盖；
(2) **in-file TBD**（git-branching 11-type、G3 "tracked separately"）——写在文件里但没进 register，
M6 关闭时无人认领。建议后续 milestone 闭幕 checklist 加一条："grep 全仓 TBD-M<N> / Phase M<N>
字样，逐条入 register 或当场裁决"。

#### v1.1 收口（2026-06-11）

§4.2 六项缺口经 5-PR 链（#247-#251）**全部闭环**——每项要么修复、要么以 ceremony 登记
（defer / WITHDRAWN / DECLINED / accepted+annotated），"登记外"状态清零；处置总账见 repo
`plans/[PLAN]_spec_anchored_refactor.md` Post-M6 Completion-Audit Disposition Registry（12 行）。
三点补记：

1. **上述 checklist 建议已制度化**：落地为 `sdd/workflows/execution-loop.md` **§7.4
   Milestone/Phase closure 收幕清单**（TBD-M\<N\> 大扫除 / M-FU registry 对账批处理 /
   gates.md 阻塞模式 vs ci.yml 真值抽查）——正是堵住本评估所发现债务逃逸路径的机制。
2. **对账经对抗性验证复核**：合并前 11-agent 验证 workflow（8 审计 + 3 refuter）确认
   23/23 gate 基线复现、13 个翻面全部真实、零 gate 回退；refuter 抓到的 2 类 major
   登记缺口（D-9 残项 5/7 无持久载体、capabilities/ 兄弟文档 111 处 TBD 未登记）已修回
   链内再合并——验证本身产出了 registry 的最后 2 行。
3. **基线刷新**（后续引用本评估时以此为准）：G22 4P/0W/0F（未自动化集合 = safe-sql REQ-004 +
   docker-compose ×3）；G7 3P/0W/0F（root .dockerignore + 覆盖性校验）；G3 5P/0W/0F；
   unit+eval 452 passed；settings deny 20 条（5 必停面 + .env + 2 .enc 全硬锁）。
   仍开放的工作集中在 registry 🟡/⏳ 行（POLICIES/CAPABILITIES-TBD-SWEEP、G27/G28、
   TESTS-DOCKER、TESTS-CONTRACT-DIR、STACK-SKILLS → Phase-2）。

---

## §5 附录：蓝图 §1-§20 逐节简表

| 蓝图节 | 主题 | 判定 | 一句话 |
|---|---|---|---|
| §1 顶层目录树 | 整体形态 | ✅（-db/ -prompts/） | 三柱 + archive + evidence 全在；db/、prompts/ 顶层未建（见 D-9） |
| §2 根级 meta | 5 文件 | ✅ | CLAUDE.md 恰 150；GLOSSARY/AGENTS 新建齐；+CONTRIBUTING |
| §3.1 sdd 顶层 5 文件 | kernel | ✅ | constitution/lifecycle/gates + 2 schema 全在（constitution/gates state: draft——可在 Phase-2 promote；gates 已 v0.2 active per #248） |
| §3.2 6 workflows | 工作流 | ✅+ | 6/6 + execution-loop.md（17-stage HITL）第 7 个 native 增项 |
| §3.3 7 adapters | adapter | ✅+ | 7/7 全含 §BDD/§TDD Rules + contract.md 第 8 个 |
| §3.4 templates | 模板 | ✅ | 22 件（13 核心 + 9 contracts/），超蓝图清单 |
| §4 capabilities | 5 pilot | ✅（1 drafting） | 4 active + mcp-gov drafting（⏳登记）；Phase 2+ 四 capability 范围外 |
| §5 policies 9 文件 | policy | ✅+ | 9/9 + release.md |
| §6 decisions | ADR | ✅ | INDEX + ADR-031 + ADR-032；9 superseded 归档 |
| §7 archive | 归档 | ✅/🔄 | ceremony 完成；结构为扁平 [DEPRECATED]_ + 组级 archive.yml/TOMBSTONE（蓝图画的是 per-STANDARD [ARCHIVED]_ 目录）——等效变体；capabilities//releases//snapshots/ 子目录未来使用未建（合规） |
| §8 src/mj_agent | 运行时 | ✅ | 保留不动达成；9 skills（8 active + probe-fixture draft，蓝图当时 5 draft 已 promote）；tools 4 子族（analysis/charts/excel/sql）齐；system.md v1.3→v1.8 演进 |
| §9 tests 11 子目录 | 测试矩阵 | ❌ | 7/11（D-1） |
| §10 docker | 运行环境 | ✅（-healthchecks/） | 4-file compose + postgres-init 齐；healthchecks/ 目录无（内联） |
| §11 db 占位 | 只读 consumer | ❌轻 | 未建（D-9） |
| §12 prompts 顶层 | 提示词 | 🔄 | 蓝图预留不迁分支生效；缺显式评估记录（D-9） |
| §13 scripts | 自动化 | 🔄 | sdd/ 19+_common（缺 4 执行体，D-3）；保留脚本全在；diff_biz_schema 未改名 |
| §14 .github | CI/模板 | ✅ | ci.yml 渐进 gate + 8 issue 模板 + PR 模板 7 字段（legacy A1-A14 收进 `<details>`） |
| §15 .claude | AI 编排 | ✅/🔄 | settings/hooks/skills/SKILL_INDEX 齐；A5 联动 + deny 双保险两处差异（D-7、D-9） |
| §16 plans + docs 过渡 | 过渡 | 🔄 | plans/ 保留 ✅；docs/ M5 re-scope（D-8，有决策记录） |
| §17 CLAUDE.md 草案 + A1-A6 | AI 上下文 | ✅ | 150 行 + 4 subdir + A2/A3/A4/A6 全落（A5 见 D-7）；Output Requirements 入 ai-agent.md §6 |
| §18 AGENTS.md | agent 边界 | ✅ | 落地一致 |
| §19 schemas | contract/trace/evidence | ✅/🔄 | schema 全套在（trace v1.2 七层）；内容兑现见 D-2 |
| §20 42 skill 终态 | skill 清单 | ⏳ | 34 现状；evidence-4 Phase-2 登记；stack-4 悬置（D-5） |

---

## §6 总结

这次重构对蓝图的**结构性承诺基本全部兑现**（三柱、归档、治理 gate 框架、AI 上下文工程 A1-A6、
CI 渐进推进），且过程纪律可圈可点：defer 有登记、撤销有 ceremony、闭幕有 metrics。
真正的差异不在"没做"，而在三个模式：

1. **结构先行、内容滞后**：trace.yml / evidence 占位、G23 tasks curation——骨架是真的，
   血肉靠 Phase-2 与 M6-FU 兑现，其中 trace 占位是唯一**无登记**的高优先级债。
2. **gate 定义超前于执行体**：gates.md 写满 G1-G28，CI 只接线 ~2/3；"定义即承诺"的
   权威性需要靠 D-3 的逐条裁决来维持。
3. **in-file TBD 逃逸 register**：git-branching 11-type、G3 "tracked separately"——
   建议把 "TBD-M<N> 大扫除" 纳入 milestone 闭幕 checklist。

按四分类计：**26 维度 = 19 ✅ + 3 🔄 + 2 ⏳ + 2 ❌**；附录层另有 7 项轻微偏差（D-9）。
若以"蓝图意图达成度"口径（等效实现与有登记顺延均计为达成意图），达成度约 **24/26 ≈ 92%**；
未达成意图且无登记的实质缺口集中于 **tests/trace 兑现债** 与 **branch-type 扩充悬置** 两处。
（v1.1 注：两处实质缺口与全部登记外项已经 #247-#251 修复链闭环——见 §4.2 处置去向列与
§4.3 v1.1 收口。）

---

## 关联文档

- 相关 ADR：`decisions/[ADR]_031_*`（Spec-Anchored Refactor 框架决策）
- 相关 Plan：`plans/[PLAN]_spec_anchored_refactor.md`（phase_progress M0-M6 + Post-M6
  Completion-Audit Disposition Registry 12 行——本评估 §4.2 的处置 SoT）
- 相关 kernel：`sdd/gates.md` v0.2（阻塞模式真值表）、`sdd/workflows/execution-loop.md`
  §7.4（本评估催生的 closure 收幕清单）
- 相关 metrics：`evidence/metrics/2026-06-08_sdd_structure_metrics.md`（M6 闭幕结构度量，
  与本评估互补：它量结构、本评估量蓝图符合度）
- 相关 PR：#245（M6 closure）；#247-#250（completion-audit 修复链）；#251（owner 决策 follow-up）
- 源稿：vault `sdd-development/mj-agent/mj-agent-refactor-completion-assessment.md`
  （v1.0 2026-06-10 初评 / v1.1 2026-06-11 对账；本文件为其升格入库版，内容同 v1.1）

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-06-10 | v1.0 | vault 初稿：蓝图 26 维对照 + 6 项登记外缺口识别 |
| 2026-06-11 | v1.1 | §4.2 补"处置去向"列与 registry 对账闭环 + §4.3 v1.1 收口段 |
| 2026-06-11 | v1.1 | 经 `/mj-agent-doc-author` 升正式 ASSESSMENT 入库（`evidence/assessments/`） |
