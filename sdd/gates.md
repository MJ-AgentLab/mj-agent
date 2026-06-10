---
type: sdd-kernel
artifact: gates
state: active
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-10
track: shared
ai_visibility: source-of-truth
---

# SDD CI Gates

> v0.2 truth-up（post-M6 completion-audit PR2; M6-FU-GATES-TRUTH-UP）：阻塞模式列改为
> **真值集合**，逐 gate 按 `.github/workflows/ci.yml` 实况填写。运行态 SoT 永远是
> ci.yml（per-step `continue-on-error`）；本文为含义 + 指针层。真值集合定义：
>
> - `blocking@ci` — ci.yml 有 step 且无 `continue-on-error: true`
> - `warning@ci` — ci.yml 有 step 且 `continue-on-error: true`
> - `manual-canonical(<指针>)` — 无脚本；由人工流程 / hook / 模板段承载（指针给出载体）
> - `covered-by(<gate>)` — 无独立 step；语义被另一 gate 的执行体覆盖
> - `deferred(<slug>)` — 未实装；登记在案（plans/[PLAN]_spec_anchored_refactor.md registry）
> - `withdrawn(<date>)` — 撤销；不再追求实装（理由随行内注）
> - `reserved` — 预留位

## §1 全局 Gate（G1-G17）

| Gate | 脚本 | 含义 | 阻塞模式（真值） |
|---|---|---|---|
| G1 | `scripts/sdd/check_capability_schema.py` | spec.yml schema 合规 | blocking@ci |
| G2 | `scripts/sdd/check_traceability.py` | trace.yml REQ→BDD→CONTRACT→TEST 链路完整 | blocking@ci |
| G3 | `scripts/sdd/check_contracts.py` | contracts/ 非空 + *.contract.yml 可解析 + behavior.feature 存在性（critical\|high REQ 必填） | warning@ci（completion-audit PR2 实装落地；blocking flip 另走 ci-blocking-gate-toggle HITL）|
| G4 | — 无脚本 | PR scope 与 plan 漂移 | manual-canonical(PR 模板 "Plan-vs-Diff Scope Declaration" 段 + Stage 9 `mj-agent-flow-scope-drift` skill) |
| G5 | `scripts/sdd/check_traceability.py` | trace.yml schema 合规 | covered-by(G2)（同脚本同 step）|
| G6 | （内置 §4 hard stops）| 4 项专属必停拦截 | manual-canonical(`.claude/scripts/guard-git-workflow.ps1` PreToolUse hook + runtime SKILL anti-patterns + HITL 人审) |
| G7 | `scripts/sdd/check_secret_exposure.py` | **解密产物**（.env / config/secrets*.conf / *.pem / *.key）不入 git；.gitignore 钉子；docker build-context 暴露检查。`config/secrets*.enc` 密文 per ADR-030 **有意入库**，不在禁止面 | warning@ci（completion-audit PR2 实装落地；含 1 个已知根目录 .dockerignore 缺失 WARN — owner 决策项）|
| G8 | `scripts/sdd/check_capability_evidence_required.py` | capability `lifecycle_state: active` 后 evidence/ 至少 1 文件 | blocking@ci |
| G9 | `scripts/sdd/generate_index.py --check` | capabilities/INDEX.auto.md 幂等 | blocking@ci |
| G10 | reserved | — | reserved |
| G11 | `scripts/sdd/check_archive_manifest.py` | archive.yml + ai_visibility 必填 | blocking@ci（M6 PR4-flip）|
| G12 | `scripts/sdd/check_archive_manifest.py` | 同上（5 必填 + enum 校验）| blocking@ci（与 G11 同 step）|
| G13 | reserved | — | reserved |
| G14 | `scripts/sdd/check_archived_references.py` | active 文件不引用 archived 路径 | warning@ci（M6-FU-G14G15-BLOCKING-FLIP 待 archive/legacy + archive/capabilities 子树建成）|
| G15 | 同 G14 | — | warning@ci（与 G14 同 step）|
| G16 | reserved | — | reserved |
| G17 | （archive ai_visibility）| archived 文档 ai_visibility 解析（reference→OK / hidden→WARN）| covered-by(G14/G15 ai_visibility 解析；warning@ci) |

## §2 Stack-Specific Gate（adapter validators）

| Gate | 脚本 | Adapter | 阻塞模式（真值） |
|---|---|---|---|
| V1 Python | `scripts/sdd/check_python_contracts.py` | python.contract.yml | blocking@ci |
| V2 Agent | `scripts/sdd/check_agent_contracts.py` | agent.contract.yml | warning@ci（SKIP-CLEAN；Phase 2+ agent.contract.yml 落地后再议 flip）|
| V3 Prompt | `scripts/sdd/check_prompt_contracts.py` | prompt.contract.yml | blocking@ci |
| V4 Claude-Skill | `scripts/sdd/check_claude_skill_contracts.py` | claude-skill.contract.yml | blocking@ci |
| V5 Docker | `scripts/sdd/check_docker_contracts.py --bdd --tdd --compose-config` | docker / compose.contract.yml | blocking@ci |
| V6 Runtime-Expected | `scripts/sdd/check_runtime_expected.py` | runtime.expected.yaml | warning@ci（SKELETON BY DESIGN；full probe → Phase-2）|
| V7 Runtime-Skill | `scripts/sdd/check_runtime_skill_contracts.py` | runtime-skill.contract.yml | blocking@ci |
| docker-bdd-scenario-check | `check_bdd_scenario_trace.py --scope docker` | docker behavior.feature | covered-by(G19)（CI 跑 `--scope full` 全集；docker 子集为其真子集）|
| docker-tdd-contract-test | `check_tdd_refactor_contract.py`（未建）| docker contract change | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER)（与 G27/G28 同执行体家族）|

## §3 BDD/TDD Gate（G19-G28）

| Gate | 脚本 | 含义 | 阻塞模式（真值） |
|---|---|---|---|
| G19 | `scripts/sdd/check_bdd_scenario_trace.py` | 关键 scenario 绑定 REQ/CTR | blocking@ci |
| G20 | — 无脚本（`check_bdd_step_coverage.py` 未建）| 自动化 scenario 有 step definition | manual-canonical(pytest-bdd 收集期 `StepDefinitionNotFoundError` 在 BLOCKING `tests/bdd` step 天然强制；未自动化集合由 G22 兜底) |
| G21 | `scripts/sdd/check_bdd_acceptance.py --strict` | `@risk:critical\|high` 验收：evidence pass_rate 1.0 或 runbook justification fallback | blocking@ci |
| G22 | `scripts/sdd/check_bdd_unautomated.py --strict` | 未自动化 critical\|high scenario 必有 runbook 4-field justification | blocking@ci |
| G23 | `scripts/sdd/check_tdd_test_list.py --check g23` | 高风险 task 有 tdd.test_list | warning@ci（M6 blocking flip 未执行 — 见 §5 历史注）|
| G24 | 同 G23（`--check g24`）| bugfix PR 必有 regression test | blocking@ci（branch-conditional：仅 bugfix/* 触发）|
| G25 | 同 G23（`--check g25`）| 改动 src/mj_agent Python 必有对应 tests/ 变更 | warning@ci（completion-audit PR2 实装落地；仅 PR context 触发）|
| G26 | —（red-green-evidence）| 高风险 task evidence/tdd/ 有 red+green | withdrawn(2026-06-10)（R-G19 缓解已软化为 AI-代码场景软要求；PR 模板 "Verification Plan" 段承载等效证据；复活条件：EVAL Phase-2 evidence harness 落地后重评）|
| G27 | `check_tdd_refactor_contract.py`（未建）| refactor PR 行为测试不变 | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER → Phase-2) |
| G28 | 同 G27（contract-test-first）| contract 变更必须有 failing test 证据 | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER → Phase-2)（原 §5 "M3 blocking 严格执行" 从未接线 — 真值化为 deferred）|

## §4 mj-agent specific hard stops（4 项 in-source 专属必停；canonical enum subset）

以下 in-source 文件任何变更**永久 manual blocking**（不可绕过；不在 CI gate 自动化覆盖范围 — 由
`.claude/scripts/guard-git-workflow.ps1` PreToolUse hook + 各 runtime SKILL anti-patterns 段
+ A12 description gate + HITL 强制人审）. 这 4 项是 `policies/ai-agent.md §4 HITL Required
Scenarios — Canonical 10-Enum` 的 in-source 子集（前 4 行）：

| Hard Stop Enum | 路径 | 工作流 |
|---|---|---|
| `sql-guardrail-relax` | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | `sdd/workflows/cross-capability-change.md`（safe-sql 跨 4 层影响）|
| `runtime-skill-content-change` | `src/mj_agent/skills/*/SKILL.md` body | `mj-agent-runtime-skill-doc-improve` skill（read-only 提议 diff）|
| `prompt-version-or-body-change` | `src/mj_agent/prompts/system.md` version 或 body | `mj-agent-runtime-prompt-version-bump` skill（含义吸收原 `prompt-version-bump` + body 行为边界变更）|
| `biz-catalog-sync` | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | `mj-agent-runtime-biz-catalog-sync` skill |

> 4 项必停的细化触发条件 + HITL 模板见 `policies/data-boundary.md` §"4 项专属必停" 段.
> 其余 6 项 HITL canonical enum（`mcp-server-trust-posture-change` / `declared-contract-change`
> / `database-migration` / `secrets-grants-or-prod-config` / `ci-blocking-gate-toggle` /
> `bulk-content-purge-or-migration`）见 `policies/ai-agent.md §4`.

## §5 Gate 启用策略（历史阶段计划；现状 SoT = ci.yml）

> **本表是 M0-M6 期间的阶段计划存档，不再描述现状。** 现状以 §1-§3 真值列 +
> `.github/workflows/ci.yml` per-step `continue-on-error` 为准。历史表与最终真值的已知偏差
> （completion-audit 对账结论）：G7 实际 completion-audit PR2 才实装（计划写 M2）；G20 从未建脚本
> （manual-canonical 化）；G23/G25 的 "M6 blocking" 未执行（保 warning@ci；flip 是独立 HITL）；
> G26 withdrawn；G27/G28 deferred（"G28 M3 blocking 严格执行" 从未接线）。

| 阶段（历史计划） | 策略（历史计划原文） |
|---|---|
| Phase M0 | G1 / G2 / G9 **warning-only**；其余未启用 |
| Phase M1 | G3 / G5 warning |
| Phase M2 | G1 / G2 / G5 → blocking；G7 启用 blocking；8 adapter gate warning |
| Phase M3 | adapter gate → blocking；G19 / G20 warning；G28 blocking |
| Phase M4 | G8 evidence required → blocking；G21 / G22 启用；G23 / G24 warning |
| Phase M5 | G11 / G12 / G14 / G15 / G17 → blocking（archive ceremony 配套）|
| Phase M6 | G23 / G25 → blocking；G26 软要求；G27 blocking |

启用 / 关闭任何 blocking gate 必须 HITL（per `policies/ai-agent.md` §HITL Required Scenarios
`ci-blocking-gate-toggle`）.

---

> *v0.2（2026-06-10）：completion-audit PR2 truth-up — 阻塞模式真值化 + G3/G7/G25 实装登记 +
> G26 withdrawn + G27/G28 deferred。详细 gate 例外处理见 `policies/ci-gates.md`。
> 历史：v0.1 Phase M0 skeleton（state: draft）。*
