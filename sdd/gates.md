---
type: sdd-kernel
artifact: gates
state: active
version: "0.16"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-02
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
| V12 Cross-Carrier-Structure | `scripts/sdd/check_cross_carrier.py --status-json .mj-agent-local/status/cross-carrier.json` | manifest ↔ registry ↔ artifact ↔ lock ↔ fidelity 的**跨面 join**（Epic #499 plan §5.8）。**是 reporter 不是第二实现**：它不重做任一面的校验，只持有「没有任何单一 blocking gate 端到端承载」的跨面闭合。**8 个 join ID（X02–X09，无 X01）**：X02 translated↔registry 双射 / X03 carrier↔artifact / X04 carrier↔lock / X05 lock 无孤儿 skill 条目 / **X06 artifact 目录反向孤儿（`.agents/skills/<dir>` 无 manifest carrier）** / X07 fidelity 索引恰覆盖 translated 集 / X08 `.agents/README.md` 存在且 lock-owned / X09 registry 边闭包。⚠ **X06 是 WARN-only 且与 X03 共用同一条 PASS** —— clean run 只打印 **7** 行 PASS，X06 仅在触发时现身（钉线 `test_cross_carrier_v12.py:97`）。**登记它是必要的**：它能产出 finding → `EXECUTED_WITH_FINDINGS` → **重置 streak**，若只按 clean 输出登记「7 个 join」，未来 flip 单元会遇到一个注册表里没有的重置源。五面中**四面**已有 blocking owner（V8 / V9 PJ050-053 / V10 / V9 PJ030-034）；**第五面 fidelity 没有** —— `check_fidelity_attestations.py` 真实树 rc 0 但**无任何 CI 挂载**（follow-up F11 未闭），故 X07 是该面**唯一 CI 可见信号**，且在索引缺失时 **warn 而非 pass** | **warning@ci（首发姿态；**本 plan 内明确不追求 blocking flip** —— plan §5.8 保留至今的交付散文「A future V12 blocking flip is a separate plan/toggle」（其 **F17 前**的注册表另有 `v8 disposition = warning-only` 一行，已随 re-home 迁入新载体 §2.1））**。**新增 warning gate ≠ posture 翻转**（#444 判例）故首挂不需 `ci-blocking-gate-toggle` 拍板。**CI 首挂锚 `2fbf700` 2026-08-27 14:11:11 +0900 #499**（PR #517；判据 = §4.1.2 run-命令 pickaxe `-S "check_cross_carrier.py" -- .github/workflows/ci.yml`，单一命中，**不**用 step 名）。**已按 `policies/ci-gates.md` §4.1.1 注册观察期**，五要素载体 = **`plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.1**（连同 §3.1 锚判据、§5.1 两腿、§5.2 streak 语义、§5.3 自排除）⚠ **「事先」要件仍满足**：首次注册在 kernel plan 创建日 **2026-08-12**，早于本 gate 2026-08-27 的首挂；新载体的 `created` 是**迁移日**不是注册日，re-home 不重置该要件——**自 F17（issue #522）起自 `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.8 表 re-home 而来**，锚 / 口径 / 阈值 / 自排除规则零变更；原载体会被 PR-G 翻 `completed`（同 #403 失效模式）。`policies/ci-gates.md` 自述「规则 + 指针层，不复制姿态真值」故不在该处登记。**Epoch 起点 = 首挂 commit 上的首次真实 CI**：run `33041866036`（event=push，`05:14:15Z`；job `98417034436`，V12 step `05:14:57Z`→`05:14:58Z`）输出 `EXECUTED_CLEAN` 7/7；同 head SHA 的 run `33041907780`（pull_request）输出逐字节相同，**去重后合计 1 次观测**。⚠ **`develop` 上的 merge commit 不产生 `ci` run**（`develop` 不在 ci.yml push 过滤器内；实测 `d810746` 于**裸** `actions/runs?head_sha=` 端点 `total_count = 0`，裸形为 0 即可推出各 workflow 皆 0 per `policies/ci-gates.md` §4.1.3）—— 后续单元不要去找一条不存在的 merge-commit run。**非 path-triggered**（随 `ci` job 每 PR 必跑）→ 适用 §4.1.3 head-SHA 去重口径，**不**适用 §4.1.4 三态口径；⚠ 去重是**必需而非可选**：ci.yml 同时挂 `pull_request` 与 `push[feature/bugfix/documentation/maintain/hotfix]`，故**分支名命中该 5 类前缀**的 PR 每个 head SHA 产生 **2 次** `ci`（push + pull_request），不去重会把 streak **高估近一倍**。⚠ 但**这不是恒等式**：`dependabot/*` 等不在 push 过滤器内的分支照样能对 develop 开 PR，只产生 **1 次**（pull_request）——故正确表述是「成对是**可能**而非**保证**」，计数一律按 head SHA 归并，不得按 run 数除以 2 反推。**clean predicate**（执行体输出是 SoT，非 run conclusion）：`EXECUTED_CLEAN` 计 1 · `SKIP_MANIFEST_V1` 中性 · `EXECUTED_WITH_FINDINGS`(rc 1) / `ERROR_UNREADABLE`(rc 2) 重置 —— ⚠ 前两者**同为 rc 0**，只能由 stdout result_code 区分，且 step 带 `continue-on-error: true` 会把非 clean 掩成绿 run。**自排除**：PR-C1 mount（本行首挂）、PR-C2 anchor（本行登记）、及任何未来 blocking-flip PR；§4.1.3 末条 = 翻转 PR 自身分支的 run 不计入自身资格，计数锚在翻转分支之前那个 commit。**翻转机制**（若将来改判）：仅 blocking 轴 **step 层** `continue-on-error: true→false`（无 `--fail-on` 阈值轴——脚本无 severity 旗标；step 层 = 与 `check-stale-docs` / `kernel-section-refs` 同型，**与** `docker-image-build` / `check-commit-messages` 的 **job 层不同型**）。**fail-closed**（per #429 判例）：任一面不可读 → `ERROR_UNREADABLE` + rc 2，不当作 pass。**已知边界（有意，写明而非默默吸收）**：(1) gate 标识仍为首挂时的 step 名，其中 `anchor PENDING_PR_C1_FIRST_CI` 字样是**首挂期的历史标识串**，非活体断言——真值以本行与 `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.1 为准，PR-C2 刻意不改 ci.yml / 脚本以守住「零 behavior diff」（残余登记为 F16）；(2) **ID 碰撞非漂移**：`plans/[PLAN]_E_Phase0_Docs_Governance_Verification.md` 另有一个无关的历史 `V12`（wikilink 目标存在性检查），属已闭档计划的 ID，与本注册表无关；(3) **注册载体已 re-home（F17 / issue #522，缺口已闭）**：本行的 §4.1.1 五要素载体现为 `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.1，不再是那份会被 PR-G 翻 `completed` 的 Epic #499 plan。⚠ 将来的 V12 flip 单元**引用新工件**，不得再回指 kernel plan §5.8（该节自 F17 起只余指针存根）。原始实测值 → `evidence/development-agent-v8/c2-v12-anchor-evidence.md`|
| V13 Codex-Enforcement-Drift | `scripts/sdd/agents_sync.py --check --surface enforcement` | typed enforcement source ↔ 生成产物 ↔ lock 的三面一致性（`sdd/adapters/codex-enforcement.yml` 及其 `policy_refs[]` 声明的文件 → `.codex/hooks.json` + `.codex/rules/*.rules`；lock 侧闭合同一组 digest，含 `policy_refs_sha256` 与 `renderer_module_sha256`。Epic #499 plan §5.9） | **warning@ci（首发姿态；**本 plan 内明确保持 warning** —— plan §5.9「V13 remains warning」；blocking 由 **PR-D2** 在既有 blocking `Tests` 路径挂载同一 predicate，须独立 `ci-blocking-gate-toggle`）**。**新增 warning gate ≠ posture 翻转**（#444 判例）故首挂与本行登记**均不需**拍板。**CI 首挂锚 `c485f8d` 2026-08-28 13:49:48 +0900 #499**（PR #519；判据 = §4.1.2 run-命令 pickaxe，片段取全命令 `-S "agents_sync.py --check --surface enforcement"`，单一命中，**不**用 step 名、**也不**用脚本路径 —— `agents_sync.py` 按 `--surface` 同时承载 V10/V11/V13，实测 `scripts/sdd/agents_sync.py` 在 ci.yml 出现 **3** 次、裸 `agents_sync.py` 出现 **5** 次，两者 pickaxe 均得 **3** 个 commit，会把锚提前 45 天；`--surface enforcement` 出现 **2** 次（其一为注释行），唯全命令片段出现 **1** 次且只在 run 行）。**gate 标识三元组**：本行名 `V13 Codex-Enforcement-Drift` ↔ ci.yml step 名 `V13 codex enforcement drift (WARNING per plan §5.9)` ↔ `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.2（第三条腿自 F17 起由该工件承担；step 名内嵌的 `plan §5.9` 是 ci.yml 侧的字面量，**不改** —— 该文件自带「Do NOT rename this step」）。⚠ **本行名的连字符是必需的**：`policies/ci-gates.md` §6.1 公布的可复跑推导左侧正则为 `V[0-9]+ [A-Za-z-]+`，实测在真实 `sdd/gates.md`（其余各行仍命中）上写成空格形时，该 grep **仍 exit 0** 而 V13 行被**静默漏掉** —— fail-open 漏行，不是报错。⚠ 该命名约束**没有任何执行体**：全仓无脚本 / workflow / 测试读取 `sdd/gates.md` 的行名，仅靠本注记与合并审查。⚠ 与 V12 不同，本 step 名**不含** anchor 占位串（刻意为之；V12 内嵌的 `PENDING_…` 已成 F16），故本 gate 无同类残余需清理。**已按 `policies/ci-gates.md` §4.1.1 注册观察期**，五要素载体 = **`plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.2**（连同 §3.2 锚判据、§5.1 两腿、§5.2 streak 语义、§5.3 自排除、§6.1 翻转执行清单）⚠ **「事先」要件仍满足**：首次注册在 kernel plan 创建日 **2026-08-12**，早于本 gate 2026-08-28 的首挂；新载体的 `created` 是**迁移日**不是注册日，re-home 不重置该要件——**自 F17（issue #522）起自 `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.9 表 re-home 而来**，锚 / 口径 / 阈值 / 自排除规则零变更。**Epoch 起点 = 首挂 commit 上的首次真实 CI**：run `33144504658`（event=push，`05:21:16Z`；job `98762485194`，V13 step `05:21:57Z`→`05:21:58Z`）输出 `EXECUTED_CLEAN`；同 head SHA 的 run `33146015449`（pull_request，`05:51:07Z`）输出逐字节相同 → **去重后合计 1 次观测**，且该次是 **epoch 标记，不是计数腿的观测 #1**。⚠ **`develop` 上的 merge commit 不产生 `ci` run**（`develop` 不在 ci.yml push 过滤器内；实测 `56188fa` 于**裸** `actions/runs?head_sha=` 端点 `total_count = 0`（源工件 `evidence/development-agent-v8/d1b-v13-anchor-evidence.md` 原注「全 workflow，不只 ci.yml」，本行此前转写时漏收），裸形为 0 即可推出各 workflow 皆 0 per `policies/ci-gates.md` §4.1.3）。**非 path-triggered**（随 `ci` job 每 PR 必跑）→ 适用 §4.1.3 head-SHA 去重口径，**不**适用 §4.1.4 三态口径；去重必需而非可选，且「同 head SHA 恒 2 次 run」**不是恒等式**（仅当分支名命中 5 类 push 前缀时才成对），计数一律按 head SHA 归并、**不得**用「run 数 ÷ 2」反推。**资格公式 = 两腿 AND，且两腿起点不同**：日历腿 = 锚 + ≥14 自然日 → 最早 **2026-09-11**；计数腿 = ≥20 连续去重 `EXECUTED_CLEAN`，**自 PR-D1b merge 之后**起算（plan §5.10 明写；与 V12 行的单起点措辞**有意不同型** —— V12 的 flip 在本 plan 之外，V13 的 flip 是 Epic 内的 PR-D2）。**clean predicate（执行体输出是 SoT，非 run conclusion）**：执行体定义 **5 个字面 token / 4 个登记组** —— `EXECUTED_CLEAN`(rc 0) 计 1 · `SKIP_MANIFEST_V1`(rc 0) 与 `SKIP_NO_ENFORCEMENT_SOURCE`(rc 0) 中性 · `EXECUTED_WITH_FINDINGS`(rc 1) 与 `ERROR_UNREADABLE`(rc 2) 重置。⚠ 前三者**同为 rc 0** 且 step 带 `continue-on-error: true`，只能由 stdout 区分；**两个 SKIP 是两个不同字面量**，只匹配四个会把 `SKIP_NO_ENFORCEMENT_SOURCE` 误判成「无 token」。⚠ **五个 token 里有四个与 V12 共用字面量，且两个 step 在同一个 `ci` job 的日志里相继落盘**（实测 anchor job `98762485194`：V12 step#42 与 V13 step#43 的 `started_at` 同为 `05:21:57Z`，`completed_at` 分别为 `:57Z` / `:58Z` —— 原记的「约 1 秒」是拿 completed_at 比 started_at，非两步间隔）—— streak 度量**必须按 step 切分日志**，对整个 job log 做 grep 会把 V12 的输出计成 V13 的。⚠ **优先级与 V12 相反**：V13 **先判 drift 再判 skip 分类**，故 v1-manifest 树上一旦有 drift 即打 `EXECUTED_WITH_FINDINGS`（重置）而非 V12 那样的中性 SKIP —— **不可逐字复用 V12 行的该段**。⚠ `ERROR_UNREADABLE` 可由 enforcement 面**之外**的故障触发（manifest / workflow registry / 任一 `policy_ref` / 任一 skills 投影源缺失），因 desired-state 无条件渲染全部 surface。⚠ **第六种结局 = 无 token**（未捕获异常 traceback 被 `continue-on-error` 抹绿；或本步因更早的 blocking 步失败而未执行）：**不是可计数观测，须调查**，不得按「没打印就是没事」计入。**自排除**：PR-D1a mount（本行所登记的首挂）、PR-D1b anchor（本行本身）、PR-D2 toggle；§4.1.3 末条 = 翻转 PR **自身分支**的 run 不计入自身资格，计数锚在翻转分支之前那个 commit。**翻转机制**：仅 blocking 轴（脚本无 `--fail-on` 阈值轴，与 V10/V11 同型），且 PR-D2 的形态是在既有 blocking `Tests` 路径挂载 byte-identical predicate，**不是**翻本 step 的 `continue-on-error`。**fail-closed**（per #429 判例）—— ⚠ **按输入面分开登记，勿笼统写「不可读即 rc 2」**：`ERROR_UNREADABLE` + rc 2 来自 **manifest** 加载失败（缺失 / YAML 错误 / 未知 `schema_version`）、**typed source 存在但不可解析**、任一 **`policy_ref` 不可读**、**workflow registry 缺失**、任一 **skills 投影源缺失**；而 **lock 的任何故障态**（缺失 / 格式错误 / 信封 schema 不符 / 重复键 / BOM / 条目摘要不符）实测一律走 `EXECUTED_WITH_FINDINGS` + **rc 1**（同为重置，非 rc 2）。两者都不当作 pass，但**诊断指向不同**。**已知边界（有意，写明而非默默吸收；⚠ 逐维度写，勿笼统写「完全无兜底」）**：(1) **无 blocking 兜底的是两个具体维度** —— artifact ↔ desired-render 的**内容漂移**与**输入 digest 闭合**：V9 从不读取 `.codex/hooks.json` / `.codex/rules/*.rules` 的**内容**，且无任何测试对这两个产物做真实树钉线；PR-D1a 又把原本裸跑 `--check`（surface=all）的**两处** real-tree 钉线收窄为 `skills`+`mcp`（F20，PR-D2 须**两处一并**恢复）：`tests/unit/test_agents_sync.py::test_real_tree_projection_in_sync` 与 `tests/unit/test_v2_engine.py::test_real_tree_now_takes_the_v2_paths`。⚠ 此处原写「那一处 …… 同组另一处本就是 mcp-scoped」，**该更正本身有误**：它把同文件内**本来就是** mcp-scoped、不在恢复面内的 `test_real_tree_mcp_projection_in_sync` 误当成了第二处，漏掉了 `test_v2_engine.py` 那一处。判据 = `git show c485f8d -- tests/` 两个同形 `-` 行，且该 commit message 自述 「TWO pre-existing real-tree pins」；在 `70a9db4` 上 `git grep 'sync_main(["--check"], repo_root=REPO_ROOT)' -- tests/` 得 2 处，在 `fb7ae7d` 上得 0 处。此类结局确是**全绿 job 下的静默 epoch 重置**。**但已存在的 lock 条目其 schema 仍受两个 blocking 载体硬约束**：V9 的 **PJ031**（整锁 `verify_lock_v2`，error 级，`--fail-on warning` 下 blocking）与 blocking `Tests` 步内 `tests/unit/test_v2_engine.py` 的真实树 `verify_lock_v2`。⚠ 条目**被整条删除**则两者皆不触发（正向断言不要求 enforcement 条目存在），该情形仍无兜底。故与 §5.8 V12 的 X07 相比，正确表述是「**V13 的未覆盖维度不同且更窄**」，而非「V13 完全无兜底」；(2) `SKIP_NO_ENFORCEMENT_SOURCE` 在已提交树上是**告警态非常态** —— 触发条件是 typed source **不是常规文件**（缺失、或被替换成目录），此时执行体照打 `OK: … lock consistent` 且 rc 0，产物与其 lock 条目**不再被任何 CI 面校验**，streak 静默停滞。⚠ **「破坏」不属此桶**：typed source 存在但不可解析 → `ERROR_UNREADABLE` + rc 2（重置）。⚠ 另注：**删除或破坏 typed source 会让 blocking `Tests` 步变红** —— `tests/unit/test_codex_enforcement_d1a.py` 在**模块层**加载真实的 `sdd/adapters/codex-enforcement.yml`，缺失即 collection error、不可解析即抛错，故这一路**有**红色信号，不属上述静默面；(3) **ID 碰撞非漂移**：`plans/[PLAN]_E_Phase0_Docs_Governance_Verification.md` 另有一个无关的历史 `V13`（CLAUDE.md 段落可读性验证），`decisions/ADR-012` 的两处 `V1-V13` 指的是它，与本注册表无关；(4) **注册载体已 re-home（F17 / issue #522，缺口已闭）**：本行的 §4.1.1 五要素载体现为 `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.2，不再是那份会被 PR-G 翻 `completed` 的 Epic #499 plan（同 #403 失效模式）。⚠ **勿再转述「V12 行也写着『日历腿到期时注册表已在闭合记录中』」** —— 该可证伪子句在 **F17 迁移前**实测**只存在于** kernel plan §5.8 的注册载体声明段（base `fb7ae7d` 的 `:1377`；`届时` / `才到期` / `已在闭合记录` 在 V12 行的出现次数均为 0，判据 `git show fb7ae7d:sdd/gates.md`）—— **F17 已随迁移删除该段**，故此后按 base commit 复核，不要在当前树上找它，V12 行原文的两个合取项各自为真；F17 已随迁移更正原句。按当前注册的公式，两条日历腿（V12 2026-09-10 / V13 2026-09-11）都在 plan 闭合之前成熟——⚠ 这是**条件性投影而非必然**，`policies/ci-gates.md` §3 W1/W2 允许 Owner 拍板豁免观察期，仓内亦有把日历腿改判为 run-based early-accept 的先例。原始实测值 → `evidence/development-agent-v8/d1b-v13-anchor-evidence.md`|
| docker-bdd-scenario-check | `check_bdd_scenario_trace.py --scope docker` | docker behavior.feature | covered-by(G19)（CI 跑 `--scope full` 全集；docker 子集为其真子集）|
| docker-tdd-contract-test | `check_tdd_refactor_contract.py`（未建）| docker contract change | deferred(M6-FU-G27-G28-TDD-REFACTOR-CONTRACT-DEFER)（与 G27/G28 同执行体家族）|
| docker-image-build | `docker build -f docker/Dockerfile`（`.github/workflows/docker-build.yml` `docker-build` job——**#438 起独立 workflow 仅 `pull_request` 触发**，原居 ci.yml；非 G/V spec-gate，属 CI infra 构建门，同 Tests/Contract 步）| Dockerfile 实际可构建（#294 防复发第二层；V5 只 lint 不 build）| **blocking@ci（翻转 = #385，2026-08-06；`ci-blocking-gate-toggle` Owner 执行记录 = issue #385 comment）**。落地时为 warning 首发（#296 per `policies/ci-gates.md` §4.1）；**CI 首挂锚 `3faaec7` 2026-07-23 15:55:16 +0800 #296**——pickaxe 判据用 run 命令片段（`-S "docker/Dockerfile"`），详注册工件 §3.1。观察期按 §4.1.1 注册于 `plans/[PLAN]_m-fu-docker-build-gate-flip.md`（**本仓首个 path-triggered gate**，故适用 §4.1.4 三态口径：`skipped` = 未触发中性、step 不存在 = 剔除）。资格实测（2026-08-06）：锚 +≥14 自然日 / head-SHA 去重连续 clean **33** 次（≥20）/ violation 0 / streak 重置 0 / 零 waiver；证据账本 `evidence/ai-context-audit/2026-08_ci_audit.md`。**翻转机制**：仅 blocking 轴 job-level `continue-on-error: true→false`（**无 `--fail-on` 旗标**，与 V10 同型）。path-scoped 到 Dockerfile 构建输入面〔`docker/`（#438 起剔除其下 `*.md` 纯文档——COPY 面下 `docker/` 仅 `entrypoint.sh`）+ `.dockerignore` + `pyproject.toml`/`uv.lock` + `README.md` + workflow 自身（`docker-build.yml`；原自引用 `ci.yml` 随迁）；`src/` 有意排除，由 ci job compileall/ruff/mypy/pytest 兜底〕，diff base 不可解时 fail-open 构建。**#438 触发面收窄**（2026-08-06）：迁出 ci.yml 后 push run 不再产生本 job——根除新分支首推 all-zeros fail-open 无条件构建、及同一 head SHA push/PR 双 run 下绿 skip 盖住红构建的掩蔽（账本 §6 / flip-plan §7 记录的两个暴露面）；§4.1.4 三态口径不变，审计度量改用 `gh run list --workflow docker-build.yml`。**边界注记**：本 gate 不在 `protect-develop`/`protect-main` 的 required contexts 内（两者各只要求 `ci`），翻转令其变红但不机械锁死 merge 按钮；加入 required contexts = 可选硬化，非翻转前置|
| check-stale-docs | `scripts/find_stale_docs.py`（`.github/workflows/check-stale-docs.yml` `check-stale-docs` job；非 G/V spec-gate，属 CI infra 文档守卫，同 `docker-image-build` 体例）| PR diff 中 rename/delete 的旧路径，在 `docs/**` / `plans/**` / SDD kernel 四目录（`capabilities/**` `decisions/**` `policies/**` `sdd/**`，#441）+ 项目根 5 文件 + `AGENTS.md` 里是否仍有 backtick 残留引用 | **warning@ci（长期姿态；明确不追求 blocking flip —— #440，2026-08-06 Owner 拍板）**。**CI 首挂锚 `d56f64e` 2026-05-09 #92**（与执行体 `scripts/find_stale_docs.py` 同批落地；本 gate 自始为独立 workflow，pickaxe 用 `-- .github/workflows/check-stale-docs.yml`，**不**在 ci.yml 内）。**不追求翻转的理由**：(1) 执行体 `main()` 每条路径 `return 0`、且无 `--fail-on` / `--strict` 旗标 —— 单翻 `continue-on-error: true→false` 是**空操作**（step 恒绿）。**注意本 gate 的 `continue-on-error` 在 step 层**（`jobs.check-stale-docs.steps[-1]`），与 `docker-image-build` 的 job 层**不同型**，照搬 docker 先例会找错位置，真翻转须先改退出码语义 + 改测试（#441 起 `tests/unit/test_find_stale_docs.py` 钉线：AC-4(d) 用例断言有 findings 仍 exit 0）；(2) 检测算法是 backtick 字面量 grep 的启发式，误报会卡住散文类 PR，收益/成本不对称。**故不按 `policies/ci-gates.md` §4.1.1 注册观察期** —— 不追求翻转即无注册义务；原 ADR-023「4 周后评估升级 blocking」的承诺随该 ADR 于 2026-05-11 归档而失效（其 `replaced-by` 指向两个 script 而非后继 ADR），且从未按 §4.1.1 注册，故本就不构成明文观察期。path-triggered（`on.pull_request.paths`，同 `docker-image-build` 族）：**若将来改判追求 blocking**，须补齐 §4.1.1 五字段注册并适用 §4.1.4 三态口径。检测面 #441（2026-08-07）已扩：扫描面补 kernel 四目录 + 根 5 文件 + `AGENTS.md`（ADR-035 例外件，其路径枚举 #416 已实际 stale 过一次）；触发面（`on.paths`）补同四目录 + `scripts/**` + `.github/**`（rename-**源**面，与扫描面的 grep **目标**面口径不同——#442 活体实证：为本 gate 补注册的 PR 自己触发不了本 gate）+ `CONTRIBUTING.md`/`GLOSSARY.md`/`AGENTS.md`。**触发面仍非穷举**（枚举白名单，未列出者一律不触发——`tests/` `config/` `docker/` `evidence/` `archive/` 等及根级非 .md 文件均在外；paths 只能枚举、枚举必陈旧）；彻底闭合 = 去掉 paths 过滤器每 PR 必跑（同 `check-commit-messages` 型），留作 Owner 改判候选；残余面同时明写于 workflow paths 注释。**输出口径注记（#447，2026-08-07）**：本 gate 的命中里，**历史记录 / provenance 体裁属预期输出，不作噪声治理** —— `decisions/**` 的决策正文陈述（`ADR-030:88` / `:100` 为「正文 + Amendment 成对」，`ADR-028:49` 为「正文 + archive pin 补记」）、`capabilities/**/evidence/**` 的定格快照、以及活体文档中「现路径（原 X，M5-PR2 平移）」式 provenance 括注（`policies/docker-runtime.md:56`、`sdd/adapters/docker-container.md:25` / `:85`、`capabilities/infrastructure/docker-compose/runbook.md:14`），按体裁本就该保留旧路径，命中不构成缺陷。**Owner 2026-08-07 拍板不加体裁 / 路径豁免**（不引入 `SKIP_PATH_PARTS`，与 `check_wikilinks.py` 排除 `plans/` 的做法**不同型**），三条理由：(1) gate 只判每个 PR 自身 diff，历史 rename 不会复现，实测 per-PR 噪声≈0（#447 复测 #441 AC-6 的近期窗口 `030f4dc`→HEAD：全窗口 1 个 rename、新增面仅 **2** 条命中，且那 2 条正是上述 ADR-030 成对陈述 = **正确输出**。⚠ 该锚的真实日期是 **2026-06-24**，#441 PR body 把它写成「7 月锚 2026-07-01」，引用时勿照抄）；(2) **体裁 ≠ 一定冻结** —— #447 实测 `decisions/ADR-008:97-98` 就藏在被 issue 归入「ADR 历史记录」的桶里，实为 M6 X3（`c82cd15`）漏改的**活体** stale ref（同一 References 列表的 `:99` 当时已 re-point），路径豁免会把这类漏改永久遮蔽；(3) warning-only gate 由人读输出，抑制只买到盲区、买不到安全。**配套书写惯例（#447 归纳）**：re-point 一条活体 stale ref 时，provenance 写**裸文件名 / 目录形**（如「原居 `infra/docker/`」），**不复制完整旧路径** —— 完整旧路径字面量会长期留在本 gate 输出里、成为下一轮 re-triage 的成本；范式源 = M6 X3（`c82cd15`）改写的 `ADR-008:99`，其「原 `dev_deployment.md`」正因写成裸文件名而从不命中。**检测面盲区（#449 归纳，2026-08-07）**：`grep_backtick_refs` 的匹配式是 ``f"`{old_path}`"`` —— **完整 repo-relative 路径的字面量**，故四种引用形态里只有第 1 种命中：① 完整路径 `` `docs/rule/[STANDARD]_X.md` `` ✅ ／ ② 目录形（「仍留在 `docs/rule/`」）❌ ／ ③ glob 或模式（`[STANDARD]_*_HITL_Prompt*.md` 这类）❌ ／ ④ 裸文件名（「原 `dev_deployment.md`」）❌。**②③④ 与上面那条书写惯例是同一机制的两面** —— 同一条设计既让 provenance 可以干净地不占输出（④，刻意利用），也让目录形 / glob 的真陈旧无声通过（②③）。活体实证（**修复前**实测）：#449 的两条债（`policies/documentation.md` §3/§3.1 的 4 个死 glob、`docs/_templates/TEMPLATE_HITL_STAGE.md` 指向已冻结件）在 `292a2de`→HEAD 窗口的 **78** 条命中里**一条都没有**。**是否为 ②③ 加检测 = 留待 Owner 的改判候选，不是本单动作**：`docs/rule/` 这类目录形字符串在散文里俯拾皆是，误报面会显著变大，而本 gate 长期 warning、明确不追 blocking（#440），扩面与抑制都只能靠人读输出兑现，收益/成本需单独判。**推论（对 re-triage 的实操含义）**：本 gate 的输出**不是**陈旧引用的全集，「gate 全绿」≠「无 stale ref」—— 归档 / 重组类 sweep 仍须按 `policies/archive.md` §1 手工扫一遍目录形与 glob 引用|
| check-commit-messages | `scripts/check_commit_messages.py`（`.github/workflows/check-commit-messages.yml` `check-commit-messages` job；非 G/V spec-gate，属 CI infra 提交规范守卫，同 `docker-image-build` / `check-stale-docs` 体例）| PR **自身新增**的 non-merge commit（`<base>..<head>`）header：type ∈ `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §3 的 7 项 + scope ∈ §4 的 35 项闭合白名单；白名单 / type / §4.6 别名**从 STANDARD 表格派生**（按表头单元格定位，非章节号或标题），脚本内**无任何 scope 字面量** | **warning@ci（首发姿态；**追求 blocking flip** —— 观察期已按 `policies/ci-gates.md` §4.1.1 于**落地同批**注册：`plans/[PLAN]_m-fu-commit-message-gate-flip.md`，五字段齐全）**。**CI 首挂锚 `cd79b5c` 2026-08-07 11:46:10 +0900 #444**（与执行体同批落地；本 gate 自始为独立 workflow，pickaxe 用 `-S "scripts/check_commit_messages.py" -- .github/workflows/check-commit-messages.yml`，**不**在 ci.yml 内）。**非 path-triggered**（`on.pull_request` 无 `paths:` 过滤器 → 每 PR 必起 job、恒产出恰好一个 check run，永不 `skipped`）：适用 §4.1.3 head-SHA 去重口径，**不**适用 §4.1.4 三态口径。**唯一中性桶 = release PR**（`base=main` 且 `head=develop`）：`main` 是旧发布点，`origin/main..develop` 是全部累积历史而非该 PR 自身提交，判它会因存量而恒红（#444 明令禁止），且其每条 commit 早已在并入 develop 的各自 PR 上判过 —— 故 workflow 以精确谓词在 **step 层**跳过判定（step 层而非 job 层，以免产生 `skipped` check），此类 run 为空绿，**审计须从 streak 剔除并分列**（详注册工件 §3.3）；hotfix→main **不**豁免。**翻转机制**：仅 blocking 轴 **job 层** `continue-on-error: true→false`（无 `--fail-on` 阈值轴，与 V10 / `docker-image-build` 同型；⚠ **与 `check-stale-docs` 的 step 层不同型**，照搬那个先例会改错位置）。**fail-closed**：STANDARD 不可读 / §4 表格解析出 0 个 scope / 提交范围不可解析 → exit 2 + 诊断（per #429 判例，「取不到输入就当没问题」是缺陷）；**诊断层**（§4.3 / §4.6 散文派生的提示语）有意**不** fail-closed，散文改写只降级提示、不改判定。**本期判定面**：只判 type/scope；§5.2 分支×type 矩阵、以及 §2.2 中**独立于这两张表**的外观规则（`:` 后空格 / 句号 / 72 字符）**有意不判**（一次判太多会令 warning 输出不可读，扩面须另起观察期，详注册工件 §5.4）。⚠ **大小写是例外、实际被判**：派生集取自小写表格，`Feat(agent)` / `feat(AGENT)` 因成员检查失败而报 `unknown-type` / `unknown-scope`（消息附小写形提示）—— 这是「派生」的必然结果而非独立规则（§2.2 亦把大小写列在首条），**不得**把本 gate 描述成「不判大小写」。`fixup!` / `squash!` / `amend!`（git 三个 autosquash 标记）单列 warning 桶，**不**触发非零退出。**已知判定面边界**（明写而非默默吸收）：§3.1 表外 blockquote 的 `merge` 伪 type 不在派生集内（真 merge commit 已被 `--no-merges` 排除，仅手写 `merge:` 于非 merge commit 才误报，全历史 0 例）；`Revert "…"` 默认主题不符 §2.1 判 `header-format`（全历史 0 例；STANDARD 对 revert 未表态，要豁免应改 §3 而非在 gate 里造例外）。**streak 语义注记**：与恒 clean 的 V8/V9/V10/`docker-image-build` 不同，本 gate 的 streak 重置 = 有人写错了 commit message，**是设计意图非误报**，不得据此放宽阈值（详注册工件 §5.2）。**边界注记**：不在 `protect-develop`/`protect-main` 的 required contexts 内（两者各只要求 `ci`），翻转令其变红但不机械锁死 merge|
| kernel-section-refs | `scripts/check_loop_section_refs.py`（`ci.yml` step `Kernel section refs (execution-loop)`；非 G/V spec-gate，属 CI infra 文档守卫，与 `check_frontmatter` / `check_wikilinks` 同居 `ci` job）| 两条规则：① `dangling-section` —— 署名 `execution-loop` 的 `§N.M`，其编号不在**从 `sdd/workflows/execution-loop.md` 正文解析出的**标题集内；② `positional-hitl-index` —— `必停 <n>` 位号（`必停 4 项` 一类**计数**不判）。三条豁免：归档署名行（`原 HITL_Prompt §4.7` 等，`ARCHIVED_SOURCE_MARKERS`）／自引用（`§N` 命中**本文件**标题集）／显式他文归属（`policies/documentation.md §5.3`；归属到 kernel 自身仍判）| **warning@ci（首发姿态；blocking flip = 候选，本单**不追求**故**未按** `policies/ci-gates.md` §4.1.1 注册）**。**CI 首挂锚 = 本 PR（#453）**。**新增 warning gate ≠ posture 翻转**（#444 判例）故不需 `ci-blocking-gate-toggle` 拍板。**未注册的后果**（§4.1.1 明载）：将来若改判追求 blocking，**不享** §4.1.1 的 streak 吸收，回落 §4 表「Gate 启用前」证据标准（切换前 1 周 DRI dry-run + violation 数量 + 影响范围）；届时须补齐五字段注册。**翻转机制**：仅 blocking 轴 **step 层** `continue-on-error: true→false`（无 `--fail-on` 阈值轴；⚠ step 层 = 与 `check-stale-docs` 同型，**与** `docker-image-build` / `check-commit-messages` 的 **job 层不同型**）。**非 path-triggered**（随 `ci` job 每 PR 必跑）。**fail-closed**（per #429 判例）：kernel 文件缺失 / 标题集解析为 0 / 文件不可读 → exit 2 —— 「取不到输入就当没问题」是缺陷。**已知判定面边界（有意，写明而非默默吸收）**：本 gate 只判「所引章节**是否存在**」，**不判**「章节**是否仍是那个意思**」—— `§4.1（Stage 0 Intake prompt）` 能干净解析却语义全错（§4.1 实为流程编排器映射表），这类**语义漂移只能靠人**：引 kernel 章节号前必须打开目标章节确认，不得照抄既有交叉引用（#453 实证：那批交叉引用本身就是错的）。**裸引用（无归属署名的 `§N.M`）同样不判（有意 —— #455）**：本 gate 只扫行内署名 `execution-loop` 的行，`§4.15 Rule 11` 一类裸编号天然在判定面外；理由 = 仓内同形态引用大量归属**别的文档**（Meta v2.2 / ADR / TEMPLATE_EVAL / Commit Convention 等章节号撞形），裸编号无法机器区分归属，扩判定面只产生误报——且 #455 已把 `.claude/skills/**` 的 21 处 HITL_Prompt 族裸引用全部改写（有 kernel 现址者重指向 `§7.3`/`§6`/`§5`，`§4.7` 族退回历史源署名），修后该类真阳残余为 0，扩面无收益。该边界由 `tests/unit/test_check_loop_section_refs.py::TestDanglingSection::test_ignores_lines_that_do_not_name_the_kernel` 钉线；书写纪律 = 新增引用必带归属（`execution-loop §N` 或 `per HITL_Prompt §4.N`），不再写裸编号。**扫描面 = 活体指令面**：`.claude/` + `capabilities/` + `decisions/` + `docs/` + `policies/` + `sdd/` + 根 5 文件中的 4 件（README / CONTRIBUTING / GLOSSARY / CLAUDE.md）+ `AGENTS.md`；**`CHANGELOG.md` / `plans/` / `evidence/` / `archive/` 有意在外** —— 它们是历史账本，如实记录着当时口径的编号，改写反而是造假，纳入只会产生永不可修的噪声（`tests/unit/test_check_loop_section_refs.py::TestScanFaceConfig::test_historical_ledgers_are_off_the_face` 结构断言钉线，防静默回加）|

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

> *v0.16（2026-09-02）：#528 — §2 V12 / V13 两行的 merge-commit 注记补端点口径：标题句自
> 「merge commit 不产生 run」限定为「`develop` 上的 merge commit 不产生 `ci` run」（与
> `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §3.3 措辞对齐），实测值标明取自**裸**
> `actions/runs?head_sha=` 端点。⚠ **本次是补回端点、不是改判口径**：两处的原始测量确由裸
> 端点做出（判据 = 源工件 `evidence/development-agent-v8/c2-v12-anchor-evidence.md` `:145`
> 与 `d1b-v13-anchor-evidence.md` `:144`，后者原本就注了「全 workflow，不只 ci.yml」，V13
> 行转写时漏收）—— 记成「`ci.yml` 谓词实测」会把裸形测量说成锚定形测量。裸形为 0 可推出各
> workflow 皆 0（`policies/ci-gates.md` §4.1.3），故原推理不受影响；而标题句的**全称**形确
> 在裸谓词下自 `33dd984` 于 2026-08-17 起为假（句式沿用该 plan §3.3 原文），限定到 workflow
> 后为真（2026-09-02 实测：Epic 期间 25 个 PR merge commit 的 `ci.yml` 谓词全为 0，裸谓词 2
> 个非 0）。**零姿态 delta**：未改 `ci.yml`、未动任何 `continue-on-error`、未改任何 gate 的
> 起点锚 / 阈值 / 五要素注册内容 ⇒ **非** `ci-blocking-gate-toggle`。*
>
> *v0.15（2026-08-31）：#522 F17 — §2 的 `V12 Cross-Carrier-Structure` 与
> `V13 Codex-Enforcement-Drift` 两行的 §4.1.1 **五要素注册载体自 Epic #499 kernel plan
> §5.8/§5.9 表 re-home 到 `plans/[PLAN]_m-fu-v12-v13-gate-observation.md` §2.1/§2.2**（新建的合并
> M-FU 注册工件）。动因：ADR-039 第 11 条与该 plan §5.12 规定 PR-G 把它翻 `completed`，
> **在 PR-G 之后**才动作的消费者会引用到一份已退休的记录 —— 同 issue #403 失效模式。
> **零 posture / 零执行体 / 零阈值 delta**，`continue-on-error` 与 run 命令逐字未动 →
> 按 #444 判例**不需** `ci-blocking-gate-toggle` 拍板。kernel plan 的 §5.8/§5.9 保留标题、
> 开头交付散文与指针存根：其**编号是活体引用目标**（`ci.yml` 两个 step 名内嵌 `plan §5.8`/`§5.9`
> 且自带「Do NOT rename this step」，`sdd/adapters/codex-enforcement.yml` 另有 3 处 `plan SS5.9`，
> 而该 typed source 的字节即 lock 输入、不可为修引用而编辑）。随迁更正三处**已知为错**的陈述：
> (1) V13 行原写「F20 要恢复的是一处，不是两处」—— 实为**两处**
> （`test_agents_sync.py::test_real_tree_projection_in_sync` 与
> `test_v2_engine.py::test_real_tree_now_takes_the_v2_paths`；`c485f8d` 的 commit message 自述
> 「TWO pre-existing real-tree pins」），原更正误把同文件内本就 mcp-scoped 的兄弟函数当成第二处；
> (2) 四处转述「V12 行也写着『日历腿到期时注册表已在闭合记录中』」属**误归属** —— 该子句只存在于
> kernel plan §5.8，V12 行的 `届时`/`才到期`/`已在闭合记录` 计数均为 0；
> (3) 「两个 step 相隔约 1 秒」是拿 completed_at 比 started_at —— 两者 `started_at` 同为
> `05:21:57Z`。v0.13/v0.14 条目内的历史载体指针**不改**（append-only 账），搬迁以本条为准。*
>
> *v0.14（2026-08-28）：#499 PR-D1b — §2 新增 `V13 Codex-Enforcement-Drift` 行（warning-first，`ci`
> job step 层）。**本行是 anchor 登记，不是姿态翻转**：V13 已由 PR-D1a（`c485f8d`）以
> `continue-on-error: true` 挂载，本单元只补**注册与证据**（gate 标识三元组 / 首挂锚 commit+日期 /
> 适用口径 / 阈值+资格公式 / 自排除 / clean predicate），`continue-on-error` 值与 run 命令逐字未动
> → 按 #444 判例「新增 warning gate ≠ posture 翻转」，**不需** `ci-blocking-gate-toggle` 拍板。
> §4.1.1 五要素的注册载体 = `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.9 表（该 plan 创建
> 2026-08-12，早于首挂）。**与 V12 行的三处有意不同型**（勿按 V12 照抄）：(1) pickaxe 片段取**全命令**
> 而非脚本路径 —— `agents_sync.py` 按 `--surface` 承载 V10/V11/V13，脚本路径片段 pickaxe 得 3 个
> commit、会把锚提前 45 天；(2) 资格公式**两腿起点不同**（日历腿锚首挂、计数腿自 PR-D1b merge 之后
> 起算，per plan §5.10），V12 的单起点措辞在其 flip 出本 plan 的前提下无害，V13 的 flip 是 Epic 内的
> PR-D2 故必须写死；(3) clean predicate 是 **5 个字面 token / 4 个登记组**（V12 只有 4 个 token，
> `SKIP_NO_ENFORCEMENT_SOURCE` 为 V13 独有），且 **V13 先判 drift 再判 skip 分类**，与 V12 的优先级
> 相反。另登记三条本 gate 独有的边界：无 blocking 兜底的**两个具体维度**（artifact 内容漂移与输入
> digest 闭合；已存在 lock 条目的 schema 仍由 V9 PJ031 与 blocking `Tests` 内的真实树 `verify_lock_v2`
> 硬约束）、lock 故障态走 rc 1 而非 rc 2、以及「无 token 的 run 不是可计数观测」。同单顺修本 PR 自身诱发的
> `policies/ci-gates.md` §6「`V1-V12`」范围陈述与 §6.1 M2「`agents_sync.py` → V10 + V11」arity 陈述。
> posture 零 delta。*
>
> *v0.13（2026-08-27）：#499 PR-C2 — §2 新增 `V12 Cross-Carrier-Structure` 行（warning-first，`ci`
> job step 层）。**本行是 anchor 登记，不是姿态翻转**：V12 已由 PR-C1（`2fbf700`）以
> `continue-on-error: true` 挂载，本单元只补**注册与证据**（gate 标识 / 首挂锚 commit+日期 /
> 适用口径 / 阈值+资格公式 / 自排除 / clean predicate），`continue-on-error` 值与 run 命令逐字未动
> → 按 #444 判例「新增 warning gate ≠ posture 翻转」，**不需** `ci-blocking-gate-toggle` 拍板。
> §4.1.1 五要素的注册载体 = `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.8 表（该 plan 创建
> 2026-08-12，早于首挂）；`policies/ci-gates.md` 按其自述「规则 + 指针层，不复制姿态真值」不登记逐
> gate 值。⚠ 明写耐久性缺口：PR-G 会把承载注册表的 plan 翻 `completed`，而日历腿最早 2026-09-10
> 到期 —— 未来 flip 单元须先 re-home 注册表（同 #403 失效模式）。同单顺修本 PR 自身诱发的
> `policies/ci-gates.md` §6「`V1-V11`」范围陈述。posture 零 delta。*
>
> *v0.12（2026-08-07）：#455 — §2 `kernel-section-refs` 行补「裸引用不判」边界（有意，非疏漏）：
> 行内未署名 `execution-loop` 的裸 `§N.M` 天然在扫描面外；理由 = 裸编号无法机器区分归属（仓内
> 同形态引用大量属 Meta v2.2 / ADR / TEMPLATE_EVAL / Commit Convention），扩判定面只余误报。
> 同单 #455 已把 `.claude/skills/**` 的 21 处 HITL_Prompt 族裸引用按修法(3)改写，重指向映射
> （历史源 HITL_Prompt 编号 → kernel 现址）：`§4.15 Rule 11`→`§7.3 Rule 11`、`§4.9 Rule 5x`→
> `§6 检查项 5x`、`§4.8`→`§5`；kernel 无对应物的 `§4.7` 族退回历史源署名，修后该类残余为 0。
> posture 零 delta（脚本 / workflow / `continue-on-error` 均未动）→ 非 `ci-blocking-gate-toggle`
> （#438/#440/#441/#447 判例族）。*
>
> *v0.11（2026-08-07）：#453 — §2 新增 `kernel-section-refs` 行（warning-first，`ci` job step）。
> 起因：kernel `execution-loop.md` 的 `§4` 在 M6 PR4 重构中**换义**（历史源 HITL_Prompt 的
> `§4.1`-`§4.15` 是 per-stage prompt、kernel 明写不 re-port；kernel `§4` 现为 Stage → Skill 映射表，
> port 自 HITL_Prompt `§5`），导致 19 个活体文件里 66 处交叉引用指向不存在的章节，而
> `check_wikilinks.py` **有意跳过 `#anchor`**、这些 `§N.M` 又根本不是 wikilink 而是散文，
> `find_stale_docs.py` 只匹配 backtick 路径，`check_frontmatter.py` 只读 frontmatter ——
> **三个既有 gate 全不覆盖章节号引用**。本行同时明写该 gate 的**语义盲区**（只判章节存在、不判
> 章节含义）与**历史账本排除面**，两者都配了结构断言钉线。承 v0.10 的推论「gate 全绿 ≠ 无 stale
> ref」：新增这条只把「章节不存在」这一子类机器化，语义漂移仍是人的义务。*
>
> *v0.10（2026-08-07）：#449 — §2 `check-stale-docs` 行补「检测面盲区」：`grep_backtick_refs` 只匹配
> **完整 repo-relative 路径字面量**，目录形与 glob / 模式引用**永不命中**，裸文件名同理（#447 的
> provenance 书写惯例正是刻意利用这一点）—— 三者是同一机制的两面。含活体实证（#449 的两条债在
> `292a2de`→HEAD 的 78 条命中里 0 命中）与推论「gate 全绿 ≠ 无 stale ref」。是否为目录形 / glob
> 加检测列为 Owner 改判候选，非本单动作；执行体与 workflow 均未改，`continue-on-error` 值不变
> → **非 `ci-blocking-gate-toggle`**（同 #438 / #441 / #447 判例）。⚠ **`version` 自本版起加引号**：
> 未加引号的 `0.10` 会被 YAML 解析成浮点 `0.1`（实测），看起来像从 0.9 降级；本文件无脚本消费该
> 字段，加引号是防未来解析器踩坑。*
> *v0.9（2026-08-07）：#447 — §2 `check-stale-docs` 行补「输出口径注记」：历史记录 / provenance
> 体裁的命中属**预期输出**，Owner 拍板**不加**体裁或路径豁免（不引入 `SKIP_PATH_PARTS`；与
> `check_wikilinks.py` 排除 `plans/` 的做法不同型）。关键反例：#447 复核发现 `decisions/ADR-008:97-98`
> 藏在被当作「ADR 历史记录」的桶里，实为 M6 X3（`c82cd15`）漏改的活体 stale ref（同列表 `:99`
> 当时已 re-point）—— **体裁 ≠ 一定冻结**，路径豁免会把这类漏改永久遮蔽。行为面零 delta（脚本
> 与 workflow 均未动），非 `ci-blocking-gate-toggle`。*
> *v0.8（2026-08-07）：#441 — §2 `check-stale-docs` 行检测面真值化（承 #440 A 路径「注册不碰行为面」
> 之后的行为面单）：扫描面 `WALK_DIRS` 补 SDD kernel 四目录、`WALK_FILES` 补齐根 5 文件 +
> `AGENTS.md`；触发面 `on.paths` 补同四目录 + `scripts/**` + `.github/**` 两个 rename-源面（#442
> 活体实证）+ `CONTRIBUTING.md`/`GLOSSARY.md`/`AGENTS.md`。AC-3 对照：kernel 文件 rename 的 8 处
> 残留引用旧面只见 1 处（仅 CLAUDE.md），新面全见。首补 `tests/unit/test_find_stale_docs.py`
>（19 用例，含 warning 姿态钉线）。posture 零 delta（step 层 `continue-on-error: true` 与 `main()`
> 恒 `return 0` 均未动）→ 非 `ci-blocking-gate-toggle`（#438/#440 同判例族）。*

> *v0.7（2026-08-07）：#444 — §2 新增 `check-commit-messages` 行（commit message 规范此前**零机器
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
