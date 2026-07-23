---
type: sdd-kernel
artifact: gates
state: active
version: 0.3
owner: ranzuozhou
created: 2026-05-20
updated: 2026-07-23
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
| G6 | （内置 §4 hard stops）| 4 项专属必停拦截 | manual-canonical(`.claude/settings.json` `permissions.ask` 逐写拍板门 + runtime SKILL propose→拍板→apply 工作流 + A13/A14 PR 合并审查 + HITL 人审；ADR-034 deny→ask) |
| G7 | `scripts/sdd/check_secret_exposure.py` | **解密产物**（.env / config/secrets*.conf / *.pem / *.key）不入 git；.gitignore 钉子；docker build-context 暴露检查（根目录 `.dockerignore` 须存在**且覆盖** `config/secrets*.conf`）。`config/secrets*.enc` 密文 per ADR-030 **有意入库**，不在禁止面 | warning@ci（completion-audit PR2 实装；根目录 .dockerignore owner-approved 落地 2026-06-11 → 基线 3P/0W/0F）|
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
| V8 Development-Agent | `scripts/sdd/check_development_agent.py --fail-on error` | development-agent.yml（manifest；`sdd/adapters/development-agent.md`） | warning@ci（P1 首发 per D-009；**CI 首挂锚 `42037bd` 2026-07-14 09:28 +0800 #320**）。**翻转机制 = 双轴**（plan §11.2(1)）：blocking 轴 `continue-on-error: true→false` + 阈值轴 `--fail-on error→warning`（**仅改阈值轴不产生 blocking**）——P4 观察期满 + Owner 批准后按 `ci-blocking-gate-toggle` **逐 gate** 翻转；判定口径（起点锚 / 20-CI 度量 / DRI 周关系）见 plan §11.2 |
| V9 Agents-Projection | `scripts/sdd/check_agents_projection.py` | development-agent.yml `projection` 域（`.agents/` + `.agents.lock.json` + S2 #330 起 `.codex/config.toml` PJ04x：键配对/server reconcile/保留键 hash/PJ044 never 档泄漏） | warning@ci（同 V8；**CI 首挂锚 `42037bd` 2026-07-14 09:28 +0800 #320**）。**翻转机制 = 双轴**（同 V8，plan §11.2(1)）：blocking 轴 `continue-on-error: true→false` + 阈值轴 `--fail-on error→warning`——**注意本脚本 argparse 有 `--fail-on`（`check_agents_projection.py:396`，`default="error"`），CI 未显式传参而靠默认值生效**（故 `ci.yml:290` 注释「V8/V9 run at --fail-on error」准确）；阈值轴翻转须**新增**旗标而非改值。MCP 产物面 day-1 blocking 由 V11 独立承载 per D-016，执行记录 #330 |
| V10 Agents-Sync-Drift | `scripts/sdd/agents_sync.py --check --surface skills` | 生成产物 ↔ 源/模板/lock 一致性（skills 面：`.agents/skills/` + `.agents/README.md` + lock 技能键；LF 归一比较，D-012 regenerate-and-diff；S2 #330 起 CI 调用收窄 `--surface skills`，本地裸 `--check` 仍双面全查） | warning@ci（S1 首发 #326 per D-016 skills 面惯例；**CI 首挂锚 `36d185d` 2026-07-14 11:39 +0800 #326**——step 名在 S2 #330 变更过，pickaxe 须用 run 命令片段而非 step 名，详 plan §11.2(2)；blocking 转正属 S3/P4，届时按 `ci-blocking-gate-toggle` 另立执行记录）。**翻转机制**：仅 blocking 轴 `continue-on-error: true→false`（**无 `--fail-on` 旗标**，plan §11.2(1)）；判定口径见 plan §11.2。**真值注记**：`tests/unit/test_agents_sync.py` 真实树钉线令同一不变量经 blocking Tests step 事实硬约束（与 V8/V9 真实树钉线同族先例；gate step 本身保持 warning 姿态）|
| V11 Codex-MCP-Projection | `scripts/sdd/agents_sync.py --check --surface mcp` | emitter B 产物 ↔ 源一致性（`.codex/config.toml` ↔ `.mcp.json` × manifest `mcp` 三档 + `codex.posture` 转写 + lock 保留键；生成/校验零 env 解析，fork/无 secrets 不假红） | **blocking@ci（day-1 per D-016，不设 warning 观察期；`ci-blocking-gate-toggle` Owner 执行记录 = issue #330 comment 2026-07-14；CI 首挂锚 `b8f43d3` 2026-07-14 17:08 +0800 #330）**。**豁免注记**：day-1 blocking 未走 `policies/ci-gates.md` §4:41 的「切换前 1 周 DRI dry-run」，属 D-016「信任面不设观察期」的**明确豁免**而非疏漏（plan §11.2(4) + §18 D-016 补记）。翻转机制不适用（既无 `continue-on-error` 键也无 `--fail-on`）。真值注记：`test_real_tree_mcp_projection_in_sync` 真实树钉线双保险（同族）|
| docker-bdd-scenario-check | `check_bdd_scenario_trace.py --scope docker` | docker behavior.feature | covered-by(G19)（CI 跑 `--scope full` 全集；docker 子集为其真子集）|
| docker-tdd-contract-test | `check_tdd_refactor_contract.py`（未建）| docker contract change | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER)（与 G27/G28 同执行体家族）|
| docker-image-build | `docker build -f docker/Dockerfile`（ci.yml `docker-build` job；非 G/V spec-gate，属 CI infra 构建门，同 Tests/Contract 步）| Dockerfile 实际可构建（#294 防复发第二层；V5 只 lint 不 build）| warning@ci（#296 首发 warning-first per `policies/ci-gates.md` §4.1；path-scoped 到 Dockerfile 构建输入面〔`docker/` + `.dockerignore` + `pyproject.toml`/`uv.lock` + `README.md` + `ci.yml`；`src/` 有意排除，由 ci job compileall/ruff/mypy/pytest 兜底〕，diff base 不可解时 fail-open 构建 + job-level `continue-on-error: true`；blocking flip 另走 `ci-blocking-gate-toggle` + evidence/ai-context-audit 记录）|

## §3 BDD/TDD Gate（G19-G28）

| Gate | 脚本 | 含义 | 阻塞模式（真值） |
|---|---|---|---|
| G19 | `scripts/sdd/check_bdd_scenario_trace.py` | 关键 scenario 绑定 REQ/CTR | blocking@ci |
| G20 | — 无脚本（`check_bdd_step_coverage.py` 未建）| 自动化 scenario 有 step definition | manual-canonical(pytest-bdd `StepDefinitionNotFoundError` 在 BLOCKING `tests/bdd` step 对**实际执行**的 scenario 强制；env-gated skip 的 scenario 在 CI 不触发该检查——本地带创跑覆盖；未自动化集合由 G22 兜底) |
| G21 | `scripts/sdd/check_bdd_acceptance.py --strict` | `@risk:critical\|high` 验收：evidence pass_rate 1.0 或 runbook justification fallback | blocking@ci |
| G22 | `scripts/sdd/check_bdd_unautomated.py --strict` | 未自动化 critical\|high scenario 必有 runbook 4-field justification | blocking@ci |
| G23 | `scripts/sdd/check_tdd_test_list.py --check g23` | 高风险 task 有 tdd.test_list | warning@ci（M6 blocking flip 未执行 — 见 §5 历史注）|
| G24 | 同 G23（`--check g24`）| bugfix PR 必有 regression test | blocking@ci（branch-conditional：仅 bugfix/* 触发）|
| G25 | 同 G23（`--check g25`）| 改动 src/mj_agent Python 必有对应 tests/ 变更 | warning@ci（completion-audit PR2 实装落地；仅 PR context 触发）|
| G26 | —（red-green-evidence）| 高风险 task evidence/tdd/ 有 red+green | withdrawn(2026-06-10)（R-G19 缓解已软化为 AI-代码场景软要求；PR 模板 "Verification Plan" 段承载等效证据；复活条件：EVAL Phase-2 evidence harness 落地后重评）|
| G27 | `check_tdd_refactor_contract.py`（未建）| refactor PR 行为测试不变 | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER → Phase-2) |
| G28 | 同 G27（contract-test-first）| contract 变更必须有 failing test 证据 | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER → Phase-2)（原 §5 "M3 blocking 严格执行" 从未接线 — 真值化为 deferred）|

## §4 mj-agent specific hard stops（4 项 in-source 专属必停；canonical enum subset）

以下 in-source 文件任何变更**manual ask-gated（逐写拍板，不可静默绕过）**；不在 CI gate 自动化
覆盖范围 — 由 `.claude/settings.json` `permissions.ask` 列表（逐写权限 prompt = Owner 拍板）+ 各
runtime SKILL 工作流（propose → 拍板 → apply）+ A12 description gate + A13/A14 PR 合并审查兜底
enforce（ADR-034：原 `deny` 物理硬锁已解除为 `ask` 拍板门；`guard-git-workflow.ps1` 仅管 G1/G2
git，不拦这 4 面 Edit/Write）. 这 4 项是 `policies/ai-agent.md §4 HITL Required
Scenarios — Canonical 10-Enum` 的 in-source 子集（前 4 行）：

| Hard Stop Enum | 路径 | 工作流 |
|---|---|---|
| `sql-guardrail-relax` | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | `sdd/workflows/cross-capability-change.md`（safe-sql 跨 4 层影响）|
| `runtime-skill-content-change` | `src/mj_agent/skills/*/SKILL.md` body | `mj-agent-runtime-skill-doc-improve` skill（propose → 拍板 → apply）|
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

> *v0.3（2026-07-23）：#296 — §2 新增 `docker-image-build` 行（CI 实际 build docker/Dockerfile；
> #294 防复发第二层；warning-first per §4.1，blocking flip 另走 ci-blocking-gate-toggle）。*
> *v0.2（2026-06-10）：completion-audit PR2 truth-up — 阻塞模式真值化 + G3/G7/G25 实装登记 +
> G26 withdrawn + G27/G28 deferred。详细 gate 例外处理见 `policies/ci-gates.md`。
> 历史：v0.1 Phase M0 skeleton（state: draft）。*
