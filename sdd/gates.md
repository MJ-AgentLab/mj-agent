---
type: sdd-kernel
artifact: gates
state: active
version: 0.7
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-06
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
| V8 Development-Agent | `scripts/sdd/check_development_agent.py --fail-on warning` | development-agent.yml（manifest；`sdd/adapters/development-agent.md`） | **blocking@ci（P4 双轴翻转 #399，2026-08-03；`ci-blocking-gate-toggle` Owner 执行记录 = issue #399 comment）**。落地时为 warning 首发 per D-009；**CI 首挂锚 `42037bd` 2026-07-14 09:28 +0800 #320**。**翻转机制 = 双轴**（plan §11.2(1)）：blocking 轴 `continue-on-error: true→false` + 阈值轴 `--fail-on error→warning`（**仅改阈值轴不产生 blocking**）——**两轴已于 #399 同时翻转**。资格实测（2026-08-03）：锚点 +20 日 / 连续 clean **55** 次（≥20）/ 零 waiver / 账本 `evidence/ai-context-audit/2026-07_ci_audit.md`；判定口径（起点锚 / 20-CI 度量 / DRI 周关系）见 plan §11.2 |
| V9 Agents-Projection | `scripts/sdd/check_agents_projection.py --fail-on warning` | development-agent.yml `projection` 域（`.agents/` + `.agents.lock.json` + S2 #330 起 `.codex/config.toml` PJ04x：键配对/server reconcile/保留键 hash/PJ044 never 档泄漏） | **blocking@ci（P4 双轴翻转 #399，2026-08-03；`ci-blocking-gate-toggle` Owner 执行记录 = issue #399 comment）**。落地时同 V8 为 warning；**CI 首挂锚 `42037bd` 2026-07-14 09:28 +0800 #320**。**翻转机制 = 双轴**（同 V8，plan §11.2(1)）：blocking 轴 `continue-on-error: true→false` + 阈值轴 `--fail-on error→warning`——**本脚本 argparse 有 `--fail-on`（`check_agents_projection.py:396`，`default="error"`），翻转前 CI 未显式传参而靠默认值生效**，故阈值轴翻转是**新增**旗标而非改值（#399 已新增）。资格实测（2026-08-03）：锚点 +20 日 / 连续 clean **55** 次（≥20）/ 零 waiver。MCP 产物面 day-1 blocking 由 V11 独立承载 per D-016，执行记录 #330 |
| V10 Agents-Sync-Drift | `scripts/sdd/agents_sync.py --check --surface skills` | 生成产物 ↔ 源/模板/lock 一致性（skills 面：`.agents/skills/` + `.agents/README.md` + lock 技能键；LF 归一比较，D-012 regenerate-and-diff；S2 #330 起 CI 调用收窄 `--surface skills`，本地裸 `--check` 仍双面全查） | **blocking@ci（S3 转正 = P4 翻转 #399，2026-08-03；`ci-blocking-gate-toggle` Owner 执行记录 = issue #399 comment）**。落地时为 warning 首发（S1 #326 per D-016 skills 面惯例）；**CI 首挂锚 `36d185d` 2026-07-14 11:39 +0800 #326**——step 名在 S2 #330 变更过，pickaxe 须用 run 命令片段而非 step 名，详 plan §11.2(2)。**翻转机制**：仅 blocking 轴 `continue-on-error: true→false`（**无 `--fail-on` 旗标**，plan §11.2(1)）；判定口径见 plan §11.2。资格实测（2026-08-03）：锚点 +20 日 / 连续 clean **49** 次（≥20，锚点晚于 V8/V9 故基数较小）/ 零 waiver。**真值注记**：`tests/unit/test_agents_sync.py` 真实树钉线令同一不变量经 blocking Tests step 事实硬约束（与 V8/V9 真实树钉线同族先例；翻转后 gate step 自身亦为 blocking，两者互为冗余）|
| V11 Codex-MCP-Projection | `scripts/sdd/agents_sync.py --check --surface mcp` | emitter B 产物 ↔ 源一致性（`.codex/config.toml` ↔ `.mcp.json` × manifest `mcp` 三档 + `codex.posture` 转写 + lock 保留键；生成/校验零 env 解析，fork/无 secrets 不假红） | **blocking@ci（day-1 per D-016，不设 warning 观察期；`ci-blocking-gate-toggle` Owner 执行记录 = issue #330 comment 2026-07-14；CI 首挂锚 `b8f43d3` 2026-07-14 17:08 +0800 #330）**。**豁免注记**：day-1 blocking 未走 `policies/ci-gates.md` §4:41 的「切换前 1 周 DRI dry-run」，属 D-016「信任面不设观察期」的**明确豁免**而非疏漏（plan §11.2(4) + §18 D-016 补记）。翻转机制不适用（既无 `continue-on-error` 键也无 `--fail-on`）。真值注记：`test_real_tree_mcp_projection_in_sync` 真实树钉线双保险（同族）|
| docker-bdd-scenario-check | `check_bdd_scenario_trace.py --scope docker` | docker behavior.feature | covered-by(G19)（CI 跑 `--scope full` 全集；docker 子集为其真子集）|
| docker-tdd-contract-test | `check_tdd_refactor_contract.py`（未建）| docker contract change | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER)（与 G27/G28 同执行体家族）|
| docker-image-build | `docker build -f docker/Dockerfile`（`.github/workflows/docker-build.yml` `docker-build` job——**#438 起独立 workflow 仅 `pull_request` 触发**，原居 ci.yml；非 G/V spec-gate，属 CI infra 构建门，同 Tests/Contract 步）| Dockerfile 实际可构建（#294 防复发第二层；V5 只 lint 不 build）| **blocking@ci（翻转 = #385，2026-08-06；`ci-blocking-gate-toggle` Owner 执行记录 = issue #385 comment）**。落地时为 warning 首发（#296 per `policies/ci-gates.md` §4.1）；**CI 首挂锚 `3faaec7` 2026-07-23 15:55:16 +0800 #296**——pickaxe 判据用 run 命令片段（`-S "docker/Dockerfile"`），详注册工件 §3.1。观察期按 §4.1.1 注册于 `plans/[PLAN]_m-fu-docker-build-gate-flip.md`（**本仓首个 path-triggered gate**，故适用 §4.1.4 三态口径：`skipped` = 未触发中性、step 不存在 = 剔除）。资格实测（2026-08-06）：锚 +≥14 自然日 / head-SHA 去重连续 clean **33** 次（≥20）/ violation 0 / streak 重置 0 / 零 waiver；证据账本 `evidence/ai-context-audit/2026-08_ci_audit.md`。**翻转机制**：仅 blocking 轴 job-level `continue-on-error: true→false`（**无 `--fail-on` 旗标**，与 V10 同型）。path-scoped 到 Dockerfile 构建输入面〔`docker/`（#438 起剔除其下 `*.md` 纯文档——COPY 面下 `docker/` 仅 `entrypoint.sh`）+ `.dockerignore` + `pyproject.toml`/`uv.lock` + `README.md` + workflow 自身（`docker-build.yml`；原自引用 `ci.yml` 随迁）；`src/` 有意排除，由 ci job compileall/ruff/mypy/pytest 兜底〕，diff base 不可解时 fail-open 构建。**#438 触发面收窄**（2026-08-06）：迁出 ci.yml 后 push run 不再产生本 job——根除新分支首推 all-zeros fail-open 无条件构建、及同一 head SHA push/PR 双 run 下绿 skip 盖住红构建的掩蔽（账本 §6 / flip-plan §7 记录的两个暴露面）；§4.1.4 三态口径不变，审计度量改用 `gh run list --workflow docker-build.yml`。**边界注记**：本 gate 不在 `protect-develop`/`protect-main` 的 required contexts 内（两者各只要求 `ci`），翻转令其变红但不机械锁死 merge 按钮；加入 required contexts = 可选硬化，非翻转前置|
| check-stale-docs | `scripts/find_stale_docs.py`（`.github/workflows/check-stale-docs.yml` `check-stale-docs` job；非 G/V spec-gate，属 CI infra 文档守卫，同 `docker-image-build` 体例）| PR diff 中 rename/delete 的旧路径，在 `docs/**` / `plans/**` + `CLAUDE.md`/`CHANGELOG.md`/`README.md` 里是否仍有 backtick 残留引用 | **warning@ci（长期姿态；明确不追求 blocking flip —— #440，2026-08-06 Owner 拍板）**。**CI 首挂锚 `d56f64e` 2026-05-09 #92**（与执行体 `scripts/find_stale_docs.py` 同批落地；本 gate 自始为独立 workflow，pickaxe 用 `-- .github/workflows/check-stale-docs.yml`，**不**在 ci.yml 内）。**不追求翻转的理由**：(1) 执行体 `main()` 每条路径 `return 0`、且无 `--fail-on` / `--strict` 旗标 —— 单翻 `continue-on-error: true→false` 是**空操作**（step 恒绿）。**注意本 gate 的 `continue-on-error` 在 step 层**（`jobs.check-stale-docs.steps[-1]`），与 `docker-image-build` 的 job 层**不同型**，照搬 docker 先例会找错位置，真翻转须先改退出码语义 + 补测试（当前零覆盖）；(2) 检测算法是 backtick 字面量 grep 的启发式，误报会卡住散文类 PR，收益/成本不对称。**故不按 `policies/ci-gates.md` §4.1.1 注册观察期** —— 不追求翻转即无注册义务；原 ADR-023「4 周后评估升级 blocking」的承诺随该 ADR 于 2026-05-11 归档而失效（其 `replaced-by` 指向两个 script 而非后继 ADR），且从未按 §4.1.1 注册，故本就不构成明文观察期。path-triggered（`on.pull_request.paths`，同 `docker-image-build` 族）：**若将来改判追求 blocking**，须补齐 §4.1.1 五字段注册并适用 §4.1.4 三态口径。检测面覆盖缺口（SDD kernel 四目录在触发面与扫描面双双缺席）= #441|
| check-commit-messages | `scripts/check_commit_messages.py`（`.github/workflows/check-commit-messages.yml` `check-commit-messages` job；非 G/V spec-gate，属 CI infra 提交规范守卫，同 `docker-image-build` / `check-stale-docs` 体例）| PR **自身新增**的 non-merge commit（`<base>..<head>`）header：type ∈ `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §3 的 7 项 + scope ∈ §4 的 35 项闭合白名单；白名单 / type / §4.6 别名**从 STANDARD 表格派生**（按表头单元格定位，非章节号或标题），脚本内**无任何 scope 字面量** | **warning@ci（首发姿态；**追求 blocking flip** —— 观察期已按 `policies/ci-gates.md` §4.1.1 于**落地同批**注册：`plans/[PLAN]_m-fu-commit-message-gate-flip.md`，五字段齐全）**。**CI 首挂锚 `cd79b5c` 2026-08-06 #444**（与执行体同批落地；本 gate 自始为独立 workflow，pickaxe 用 `-S "scripts/check_commit_messages.py" -- .github/workflows/check-commit-messages.yml`，**不**在 ci.yml 内）。**非 path-triggered**（`on.pull_request` 无 `paths:` 过滤器 → 每 PR 必起 job、恒产出恰好一个 check run，永不 `skipped`）：适用 §4.1.3 head-SHA 去重口径，**不**适用 §4.1.4 三态口径。**唯一中性桶 = release PR**（`base=main` 且 `head=develop`）：`main` 是旧发布点，`origin/main..develop` 是全部累积历史而非该 PR 自身提交，判它会因存量而恒红（#444 明令禁止），且其每条 commit 早已在并入 develop 的各自 PR 上判过 —— 故 workflow 以精确谓词在 **step 层**跳过判定（step 层而非 job 层，以免产生 `skipped` check），此类 run 为空绿，**审计须从 streak 剔除并分列**（详注册工件 §3.3）；hotfix→main **不**豁免。**翻转机制**：仅 blocking 轴 **job 层** `continue-on-error: true→false`（无 `--fail-on` 阈值轴，与 V10 / `docker-image-build` 同型；⚠ **与 `check-stale-docs` 的 step 层不同型**，照搬那个先例会改错位置）。**fail-closed**：STANDARD 不可读 / §4 表格解析出 0 个 scope / 提交范围不可解析 → exit 2 + 诊断（per #429 判例，「取不到输入就当没问题」是缺陷）；**诊断层**（§4.3 / §4.6 散文派生的提示语）有意**不** fail-closed，散文改写只降级提示、不改判定。**本期判定面**：只判 type/scope；§5.2 分支×type 矩阵、以及 §2.2 中**独立于这两张表**的外观规则（`:` 后空格 / 句号 / 72 字符）**有意不判**（一次判太多会令 warning 输出不可读，扩面须另起观察期，详注册工件 §5.4）。⚠ **大小写是例外、实际被判**：派生集取自小写表格，`Feat(agent)` / `feat(AGENT)` 因成员检查失败而报 `unknown-type` / `unknown-scope`（消息附小写形提示）—— 这是「派生」的必然结果而非独立规则（§2.2 亦把大小写列在首条），**不得**把本 gate 描述成「不判大小写」。`fixup!` / `squash!` / `amend!`（git 三个 autosquash 标记）单列 warning 桶，**不**触发非零退出。**已知判定面边界**（明写而非默默吸收）：§3.1 表外 blockquote 的 `merge` 伪 type 不在派生集内（真 merge commit 已被 `--no-merges` 排除，仅手写 `merge:` 于非 merge commit 才误报，全历史 0 例）；`Revert "…"` 默认主题不符 §2.1 判 `header-format`（全历史 0 例；STANDARD 对 revert 未表态，要豁免应改 §3 而非在 gate 里造例外）。**streak 语义注记**：与恒 clean 的 V8/V9/V10/`docker-image-build` 不同，本 gate 的 streak 重置 = 有人写错了 commit message，**是设计意图非误报**，不得据此放宽阈值（详注册工件 §5.2）。**边界注记**：不在 `protect-develop`/`protect-main` 的 required contexts 内（两者各只要求 `ci`），翻转令其变红但不机械锁死 merge|

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

> *v0.7（2026-08-06）：#444 — §2 新增 `check-commit-messages` 行（commit message 规范此前**零机器
> 强制**：全仓无 commitlint / conventional 配置，`9ae9ec6` 上 462 条可解析提交中 **132 条（28.6%）**
> 带 type/scope 违规）。**该比率须按 v1.1 白名单读**：#444 issue 正文写的 51% 是按 **v1.0 的 12 项**
> 白名单测的，#443 把 §4 重建为 35 项后同一锚重测即降至 28.6% —— 引用旧率等于描述一个已不存在的
> 白名单。
> posture `warning@ci` 首发，**追求 blocking flip**，故观察期按 `policies/ci-gates.md` §4.1.1 于
> **落地同批**注册（`plans/[PLAN]_m-fu-commit-message-gate-flip.md`）—— 出生即注册，正是 #403 在
> `docker-image-build` 上补注册、#440 在 `check-stale-docs` 上完全缺注册所暴露的坑。**新增 warning
> gate ≠ `ci-blocking-gate-toggle`**（该 enum 的触发语义是 `continue-on-error` 翻转或新增 blocking
> gate，本次两者皆非）。*
> *v0.6（2026-08-06）：#440 — §2 新增 `check-stale-docs` 行。该 gate 自 `d56f64e`（2026-05-09）
> 起在 CI 运行，却从未进入本注册表；posture 据实记为 `warning@ci` 并声明为**长期姿态**（Owner
> 拍板不追求 blocking flip，理由随行内注）。同批把 workflow header 与 `find_stale_docs.py`
> docstring 中引用已归档 ADR-023 的「4 周后转 blocking」承诺真值化。**`continue-on-error` 值未变
> → 非 `ci-blocking-gate-toggle`**（同 #438 判例：只改载体/措辞不动 posture 值）。*
> *v0.5（2026-08-06）：#438 — §2 `docker-image-build` 行触发面收窄：job 迁独立 workflow
> `.github/workflows/docker-build.yml` 仅 `pull_request` 触发（push run 不再产生本 job）+
> 触发路径剔除 `docker/` 下 `*.md` 纯文档；posture 不变（非 `ci-blocking-gate-toggle`）。*
> *v0.4（2026-08-06）：#385 — §2 `docker-image-build` 行 posture `warning@ci` → **`blocking@ci`**
> （`ci-blocking-gate-toggle`；观察期注册工件 `plans/[PLAN]_m-fu-docker-build-gate-flip.md`，
> 账本 `evidence/ai-context-audit/2026-08_ci_audit.md`；streak 33 / 阈值 20、violation 0）。*
> *v0.3（2026-07-23）：#296 — §2 新增 `docker-image-build` 行（CI 实际 build docker/Dockerfile；
> #294 防复发第二层；warning-first per §4.1，blocking flip 另走 ci-blocking-gate-toggle）。*
> *v0.2（2026-06-10）：completion-audit PR2 truth-up — 阻塞模式真值化 + G3/G7/G25 实装登记 +
> G26 withdrawn + G27/G28 deferred。详细 gate 例外处理见 `policies/ci-gates.md`。
> 历史：v0.1 Phase M0 skeleton（state: draft）。*
