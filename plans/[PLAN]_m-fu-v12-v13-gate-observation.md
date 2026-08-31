---
type: plan
slug: m-fu-v12-v13-gate-observation
summary: >-
  M-FU 注册工件 M-FU-V12-V13-GATE-OBSERVATION —— 把 V12 Cross-Carrier-Structure 与 V13
  Codex-Enforcement-Drift 两个 CI gate 的明文观察期注册表（gate 标识 / CI 首挂锚 / 适用口径 /
  阈值+资格公式 / 自排除规则）自 plans/[PLAN]_codex_cross_carrier_kernel.md §5.8/§5.9 re-home
  出来，满足 policies/ci-gates.md §4.1.1 注册制 + policies/ai-agent.md §4 对
  ci-blocking-gate-toggle 的「M-FU plan 必先 register」前置；消费者 = Epic #499 PR-D2（V13 flip）
  与将来的独立 V12 flip 单元；两条 flip 路径均收口后闭合
owner: ranzuozhou
created: 2026-08-31
updated: 2026-08-31
state: active
version: 1.0
track: engineering-workflow
---

# [PLAN] M-FU-V12-V13-GATE-OBSERVATION — V12 / V13 gate 观察期注册

> 标识：`M-FU-V12-V13-GATE-OBSERVATION`（per `policies/ci-gates.md` §4.1.1 注册制 +
> `policies/ai-agent.md` §4 `ci-blocking-gate-toggle` 的「M-FU plan 必先 register」）。
> 性质：**re-home** —— 非新注册、非补注册。两张表的规范内容自 Epic
> [#499](https://github.com/MJ-AgentLab/mj-agent/issues/499) 的
> `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.8/§5.9 迁入，**锚 / 口径 / 阈值 / 自排除规则零变更**。
> Issue：[#522](https://github.com/MJ-AgentLab/mj-agent/issues/522)（Epic #499 follow-up 表 F17）。
> 消费者：**V13** → Epic #499 PR-D2；**V12** → 将来的独立 flip 单元（§5.8 明确排除出该 Epic）。

## 1 为何需要本工件

`policies/ci-gates.md` §4.1.1 把「明文观察期」定义为**注册制**：gate 恰好以 warning 跑了一段时间
**不**构成观察期，未注册者**不享** §4.1 的时序吸收，回落 §4 表「Gate 启用前」行（切换前 1 周 DRI
dry-run，且**无**连续次数阈值）。

两个 gate 原本都注册在 Epic #499 的 kernel plan 里（§5.8 / §5.9），而
`decisions/ADR-039` 第 11 条与该 plan §5.12 规定 **PR-G 在 PR-F 合并后把它翻 `active → completed`**。
届时注册表将位于一份**已闭合的项目记录**中，**任何在 PR-G 之后才动作的消费者**都会引用到一份已退休
的记录 —— 这正是 `policies/ci-gates.md` §4.1.2/§4.1.3 因 issue #403 从
`plans/[PLAN]_dual-agent-compat.md` 逐字提升为政策原生条文的**同一失效模式**。

⚠ 缺口的**形状**须写准，本工件不复述迁入前那句已被证伪的措辞。旧 §5.8 写「日历腿到期时注册表已在
闭合记录中」—— 实测**为假**：PR-D2 的入场即要求 V13 日历腿 ≥ 2026-09-11，而 PR-G 排在 D2/E/F 之后，
故两条日历腿（V12 2026-09-10 / V13 2026-09-11）**都在 plan 闭合之前**成熟。真正的缺口是
「**PR-G 之后**才动作的消费者引用到一份已退休的记录」。
⚠ 该推论是**条件性投影而非必然**：它成立的前提是 §5 交付图与 §5.10 资格公式**未经修订**。
`policies/ci-gates.md` §3 W1/W2 把「观察期豁免」编纂为 `ci-blocking-gate-toggle` 拍板的一种，
且仓内有过把**日历腿改判为 run-based early-accept** 的执行先例（`plans/stage-f-m4-closure-prep.md`
与 `plans/stage-e-alpha-prime-e-4-soak.md`）。故正确表述是「按当前注册的公式，PR-G 不早于
2026-09-11」，不是「PR-G 必然不早于」。

⚠ **「事先」要件在 re-home 后仍满足，且这一点必须写在活体载体上。** §4.1.1 的构成要件是
「**事先**在 `plans/` 注册」。两个 gate 的**首次注册**发生于 kernel plan 的创建日 **2026-08-12**，
早于两条 CI 首挂锚（V12 `2fbf700` 2026-08-27 / V13 `c485f8d` 2026-08-28）—— 故它们是**前瞻注册**，
不是 retroactive 补登。**本工件 frontmatter 的 `created: 2026-08-31` 是载体迁移日，不是注册日**；
re-home 不重置、也不能重置该要件（§4.1.1 约束的是注册时点与首挂时点的先后，不是载体文件的诞生日）。
两个先例把同一事实写在活体正文里（docker §1「前瞻注册（非 retroactive 补登）」/ commit-message §1
「出生即注册」），本工件沿用。

**为何不提升到 `policies/`**：`policies/ci-gates.md` 自述为「规则 + 指针层，**不复制姿态真值**」
（逐 gate 真值列在 `sdd/gates.md` §1-§3），且 §4.1.1 的构成要件字面要求「事先在 `plans/` 注册」。
#403 那次提升的是**规则**（§4.1.2/§4.1.3 的度量口径），**不是逐 gate 值** —— 两者不同型，不可援引为先例。

**为何合并成一份而非两份**：两个 gate 共享同一政策依据（§4.1.1/§4.1.3）、同一 head-SHA 去重口径、
同一自排除结构，且两条注册表本来就靠「与对方有意不同型」互相定义（§5.1 的两腿起点、§5.2 的优先级
相反）。拆成两份会让这些对照失去落点。

## 2 注册项（对齐 `policies/ci-gates.md` §4.1.1 表）

> §4.1.1 的五要素中，**阈值 + 资格公式**与**自排除规则**在下面两张表里是**指针**，其真值分别写在
> §5.1 与 §5.3。这与两个既有 M-FU 先例同构。⚠ §4.1.1 对自排除规则的要求是「注册时须**明写**」——
> 故 §5.3 是实体条文而非再一次转指，读者不得只读本节即认为注册完整。

### 2.1 V12 Cross-Carrier-Structure

| 注册项 | 值 |
|---|---|
| **gate 标识** | `sdd/gates.md` §2 行名 `V12 Cross-Carrier-Structure` ↔ `.github/workflows/ci.yml` step 名 `V12 cross-carrier structure (WARNING per plan §5.8; anchor PENDING_PR_C1_FIRST_CI)`（逐字转写）。⚠ step 名里的 `PENDING_…` 是**首挂期的历史标识串，非活体断言** —— PR-C2 刻意不改 ci.yml 以守住「零 behavior diff」，真值以本工件为准（残余登记为 Epic #499 follow-up `F16`） |
| **CI 首挂锚** | `2fbf700` · **2026-08-27 14:11:11 +0900**（PR #517；判据见 §3.1） |
| **适用口径** | `policies/ci-gates.md` §4.1.3（head-SHA 去重）。**§4.1.4 不适用** —— 见 §3.3 |
| **阈值 + 资格公式** | §5.1（两腿 **AND**） |
| **自排除规则** | §5.3 |
| **触发路径集**（§4.1.4 额外义务） | **不适用** —— 本 gate 非 path-triggered，见 §3.3 |
| **执行体** | `uv run python scripts/sdd/check_cross_carrier.py --status-json .mj-agent-local/status/cross-carrier.json` |
| **姿态真值** | `warning@ci`（首发姿态）。**本 Epic 内明确不追求 blocking flip** —— §5.8 保留至今的交付散文原文「A future V12 blocking flip is a separate plan/toggle」；其 **F17 前**的注册表另有 `\| v8 disposition \| warning-only; no blocking flip in this plan \|` 一行（该行随本次 re-home 迁入本表，故 `warning-only` 的字面自 F17 起只存在于此处与 `sdd/gates.md` V12 行）。**新增 warning gate ≠ posture 翻转**（#444 判例），故首挂与本次 re-home 均不需 `ci-blocking-gate-toggle` 拍板 |

### 2.2 V13 Codex-Enforcement-Drift

| 注册项 | 值 |
|---|---|
| **gate 标识** | `sdd/gates.md` §2 行名 `V13 Codex-Enforcement-Drift` ↔ `.github/workflows/ci.yml` step 名 `V13 codex enforcement drift (WARNING per plan §5.9)` ↔ 本工件 §2.2（**三元组的第三条腿自 F17 起由本工件承担**，此前指向 kernel plan §5.9 表）。⚠ `sdd/gates.md` 行名的**连字符是必需的**：`policies/ci-gates.md` §6.1 公布的可复跑推导左侧正则为 `V[0-9]+ [A-Za-z-]+`，写成空格形时该 grep **仍 exit 0** 而该行被**静默漏掉** —— fail-open 漏行，不是报错。⚠ 该命名约束**没有任何执行体**，仅靠本注记与合并审查 |
| **CI 首挂锚** | `c485f8d` · **2026-08-28 13:49:48 +0900**（PR #519 的实现 commit，非 merge commit；判据见 §3.2） |
| **适用口径** | `policies/ci-gates.md` §4.1.3（head-SHA 去重）。**§4.1.4 不适用** —— 见 §3.3 |
| **阈值 + 资格公式** | §5.1（两腿 **AND**，且**两腿起点不同**） |
| **自排除规则** | §5.3 |
| **触发路径集**（§4.1.4 额外义务） | **不适用** —— 本 gate 非 path-triggered，见 §3.3 |
| **执行体** | `uv run python scripts/sdd/agents_sync.py --check --surface enforcement` |
| **姿态真值** | `warning@ci`（首发姿态）。blocking 由 Epic #499 **PR-D2** 在既有 blocking `Tests` 路径挂载 byte-identical predicate，**不是**翻本 step 的 `continue-on-error`；须独立 `ci-blocking-gate-toggle` Owner 记录 |

## 3 起点锚判据

### 3.1 V12 锚 commit

```bash
git log --oneline --reverse -S "check_cross_carrier.py" -- .github/workflows/ci.yml
# → 2fbf700 feat: cut over to manifest v2 with 18 Codex carriers   （单一命中）
git show -s --format='%H %ad' --date=iso 2fbf700
# → 2fbf700b… 2026-08-27 14:11:11 +0900
```

片段取**脚本路径**即可，因为 `check_cross_carrier.py` 在 `ci.yml` 内只挂一次。
⚠ **这是巧合，不是可照搬的形状** —— 见 §3.2。

### 3.2 V13 锚 commit

```bash
git log --oneline --reverse -S "agents_sync.py --check --surface enforcement" -- .github/workflows/ci.yml
# → c485f8d feat: render Codex enforcement carrier and mount V13   （单一命中）
git show -s --format='%H %ad' --date=iso c485f8d
# → c485f8d4… 2026-08-28 13:49:48 +0900
```

⚠ **片段选择有判据，勿照抄 V12 的形状。** 判据是「该片段在 `ci.yml` 内的**出现次数历史**是否隔离本
gate」——`git log -S` 对出现次数的**任何**变化（含纯计数增减）都会触发 —— 而**不是**「执行体是否唯一挂载」。
`agents_sync.py` 按 `--surface` 同时承载 V10 / V11 / V13（per `policies/ci-gates.md` §6.1 M2），实测：

| 候选片段 | 在 ci.yml 出现次数 | pickaxe 得到的 commit 数 | 可用 |
|---|---|---|---|
| `scripts/sdd/agents_sync.py` | 3 | 3（`36d185d` V10 / `b8f43d3` V11 / `c485f8d` V13） | 否 —— 把锚提前 45 天 |
| 裸 `agents_sync.py` | 5（多出两次在注释行） | 3 | 否 —— 同上 |
| `--surface enforcement` | 2（`:408` 注释 + `:426` run 行） | 1 | 否 —— 注释改写即扰动计数 |
| **全命令**（上方） | **1，且只在 run 行** | **1** | **是** |

### 3.3 两 gate 均**非** path-triggered（§4.1.4 明确不适用）

两个 step 都在 `ci` job 内，该 job **无 `paths:` 过滤器**，故随每个 PR 必跑 → 适用 §4.1.3 的
head-SHA 去重口径，**不**适用 §4.1.4 的三态（执行且 clean / 执行且非 clean / 未触发中性）口径。

⚠ **但「§4.1.4 不适用」不等于「不需要中性桶」。** 两个执行体都对 `SKIP_*` 结局返回 rc 0，
vacuous-streak 的风险从另一扇门进来 —— 中性桶按 stdout token 定义，见 §5.2。

⚠ **两个粒度务必分开：`check` 与 `step`。**

- `ci` **check run** 因无 path 过滤器而**永不** `skipped`。
- 但 gate 的 **step** 在更早的 blocking 步失败时**确实会拿到 `conclusion: skipped`**
  （实测先例：run `31773569400` / job `94684255167` 的 step 42 failure 之后，43 / 44 均为 `skipped`）。
  **该 `skipped` step 不是 §4.1.4 的中性桶，而是「无 token」结局 —— 须调查，不得当作中性吸收。**

⚠ **`develop` 上的 merge commit 不产生 `ci` run**（措辞须限定到 workflow —— 见下方谓词注记，
它**确实**会被归属到别的 workflow 的 run）：`ci.yml` 的 push 过滤器只含 5 类临时分支前缀
（不含 `develop`），`pull_request` 只对 base 为 main 或 develop 的 PR 触发。故 merged 单元的
「首次真实 CI」只能取其 **PR head SHA** 上的 run。复核谓词（勿转抄计数）：

```bash
gh api "repos/MJ-AgentLab/mj-agent/actions/workflows/ci.yml/runs?head_sha=<merge-sha>" \
  --jq .total_count
# → 0   （本 Epic 全部 19 个 merge commit 实测均为 0）
```

⚠ **谓词必须锚在 `ci.yml` 这个 workflow 上；裸 `.../actions/runs?head_sha=…` 的 `total_count`
不可用。** 后者统计**该 head SHA 上的全部 workflow run**，而 Dependabot 按
`.github/dependabot.yml` 的 `weekly / monday / 09:00 Asia/Shanghai`（= **01:00 UTC**）+
`target-branch: develop` 定时触发，GitHub 会把那些 `dynamic` run 归属到**当时恰为 develop 头**的
那个 SHA。实测两个反例：`fb7ae7d` 得 **3**（一个周一 tick）、`33dd984` 得 **6**（跨两个周一
tick：2026-08-17 与 2026-08-24）—— 19 个 merge commit 里有 **2 个**如此。
收窄到 `ci.yml` 后**全部 19 个都是 0**。

⚠ **该谓词以 SHA 钉死使用时是安全的**（C2 与 D1b 两个 ledger 正是这样用的，其记录值至今仍复现
为 0）；**危险的是把它推广成「每个 merge commit 恒 0」的全称命题** —— 那个全称自
`33dd984` 于 2026-08-17 起就已为假，比本单元早两周。**这不是「测量后变陈旧」，是「未测量就推广」。**

## 4 观察期实测（时点快照，**非**翻转拍板依据）

> ⚠ 本节是**时点测量**，随后必然增长；引用时须连同测量时点一并引用，不得当作恒定值。
> 翻转拍板的证据工件是 `evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（per §4.1）。

**快照时点：2026-08-31T01:13Z。**

| 项 | V12 | V13 |
|---|---|---|
| 日历腿到期（锚 + ≥14 自然日） | **2026-09-10** | **2026-09-11** |
| 计数腿起点 | 锚 `2fbf700` 上的首次真实 CI 之后 | **Epic #499 PR-D1b merge commit `fb7ae7d` 之后** |
| Epoch 标记观测 | run `33041866036`（push，`2026-08-27T05:14:15Z`；job `98417034436`，step `05:14:57Z`→`05:14:58Z`）输出 `EXECUTED_CLEAN` 7/7 join；同 head SHA 的 run `33041907780`（pull_request）输出逐字节相同 → 去重后合计 **1 次观测** | run `33144504658`（push，`2026-08-28T05:21:16Z`；job `98762485194`，step #43 `05:21:57Z`→`05:21:58Z`）输出 `OK: projection in sync (surface=enforcement, 18 skills, lock consistent)` + `EXECUTED_CLEAN`；同 head SHA 的 run `33146015449`（pull_request，`05:51:07Z`）输出逐字节相同 → 去重后合计 **1 次观测**。⚠ 该次是 **epoch 标记，不是计数腿的观测 #1** |
| 快照时点的可计数 streak | **未测量**（见下方说明） | **1**（见下方明细） |

**V12 计数腿：本单元有意不测量。** 理由：(a) V12 的 blocking flip 明确在 Epic #499 之外
（§5.8 交付散文），无消费者在等这个数；(b) 迁入前的 §5.8 Eligibility cell **未规定计数腿起点**，
而 `sdd/gates.md` V12 行把锚上那次观测登记为「去重后合计 1 次观测」—— 两处对「锚那次算不算观测 #1」
**口径未收口**（与 V13 不同：V13 明写该次是 epoch 标记、不计入计数腿）。**F17 是 re-home，不解决该
语义问题**，否则就不是零变更。⇒ 登记为**未收口项**，由将来的 V12 flip 单元在其 toggle 记录里先收口
起点口径、再测量。⚠ 在此之前**不得**引用任何 V12 streak 数字。

**V13 计数腿明细（2026-08-31 实测）**：计数腿自 `fb7ae7d` 之后起算。

- `fb7ae7d` 本身触发 **0** 次 **`ci.yml`** run（merge commit，见 §3.3）。⚠ 其 head SHA 上另有 **3** 次 `dynamic/dependabot/dependabot-updates` run，但它们 `event=dynamic`、由周一 cron 在**合并三天后**创建，**非** merge push 所致，且不含 V12/V13 step ⇒ 不是观测。**引用任何「触发 N 次 run」时必须写明是哪个 workflow 的计数。**
- `c485f8d` → `fb7ae7d` 之间，`maintain/499-v13-anchor`（head `029d1e5`）产生 2 次 run
  —— 按 §5.3 自排除（PR-D1b anchor）**不计入**。
- `fb7ae7d` 之后第一个可计数观测：head `d201538e`，分支
  `dependabot/docker/docker/develop/python-7ce4b6d`（PR #521），run `33346811871`
  （event=pull_request，`2026-08-31T01:11:07Z`；job `99352366505`，step #43
  `01:11:42Z`→`01:11:43Z`），stdout 为
  `OK: projection in sync (surface=enforcement, 18 skills, lock consistent)` + `EXECUTED_CLEAN`。
  ⇒ **计 1**。
- ⚠ 该 head SHA 只产生 **1 次** run（`dependabot/*` 不在 push 过滤器内）—— 这正是 §5.2
  「成对是可能不是保证」的实例，也证明**不得**用「run 数 ÷ 2」反推观测数。

**度量命令**（§4.1.3）：

```bash
gh run list --workflow ci.yml --limit 100 \
  --json conclusion,createdAt,headSha,event,databaseId
# 按 headSha 去重后，自 §3 的锚起，逐 SHA 核被观察 gate 执行体的 stdout token
```

⚠ **stdout token 必须按 step 切分日志读取**，理由见 §5.2。实操句柄：job 日志里的
step 分组行是按**命令**标注的，不是按 step 名 —— 形如
`##[group]Run uv run python scripts/sdd/agents_sync.py --check --surface enforcement`。
**按 step 名 grep 会零命中**，按命令锚定则稳定。

⚠ **step 编号有两个口径，引用时须写明是哪个**（本节与 §5.2 出现的 `#42` / `#43` **一律是 Actions
API 口径**）：Actions API / 日志的编号**含隐式 `Set up job`**，故 V12 = **#42**、V13 = **#43**；
而 `ci.yml` 内的 **authored step** 编号比它**小 1**。两个口径差 1，且**任何插入的 step 都会推移
两者**。⇒ 编号是**易腐句柄**，可复跑的稳定句柄是上面那行 `##[group]Run …` 命令。

## 5 资格公式

### 5.1 两腿（AND）—— 两 gate **起点不同型**

**V12**：日历腿 = 锚 + ≥14 自然日 **AND** 计数腿 = ≥20 次连续 head-SHA 去重的 `EXECUTED_CLEAN` run。
（单起点措辞在此**无害** —— V12 的 blocking flip 明确在 Epic #499 之外。）

**V13**：**两腿 AND，且两腿起点不同**：

- **日历腿** = mount anchor `c485f8d`（2026-08-28）+ ≥14 自然日 → 最早 **2026-09-11**；
- **计数腿** = ≥20 次连续 head-SHA 去重的 `EXECUTED_CLEAN` run，**自 PR-D1b merge commit `fb7ae7d`
  之后**起算。

⚠ **V13 的这一 cell 与 V12 有意不同型，不可照抄。** V13 的 flip 是 Epic #499 内的 PR-D2；若照抄
单起点措辞，会把 mount → anchor 期间的 run 计入计数腿而提前达阈值 —— 正是 `policies/ci-gates.md`
§4.1.4 「vacuous streak」要防的失效模式。

**两腿之外的合取项**（per Epic #499 plan §5.10）：零 waiver、零未关闭 warning；
predicate / schema / route / self-trigger 语义变更**开启新 epoch**。

### 5.2 clean predicate 与 streak 语义

**共同原则**：**执行体输出是 SoT，不是 run / step 级 conclusion**（§4.1.3）。两个 step 都带
`continue-on-error: true`，会把非 clean 掩成绿 run。

**V12** —— 4 个字面 token：

| token | rc | 对 streak |
|---|---|---|
| `EXECUTED_CLEAN` | 0 | **计 1** |
| `SKIP_MANIFEST_V1` | 0 | 中性 |
| `EXECUTED_WITH_FINDINGS` | 1 | **重置** |
| `ERROR_UNREADABLE` | 2 | **重置** |

⚠ 前两者**同为 rc 0**，只能由 stdout 的 result_code 区分。
⚠ V12 的 join `X06`（artifact 目录反向孤儿）是 **WARN-only 且与 X03 共用同一条 PASS** —— clean run
只打印 **7** 行 PASS，X06 仅在触发时现身。登记它是必要的：它能产出 finding →
`EXECUTED_WITH_FINDINGS` → 重置 streak。

**V13** —— **5 个字面 token，归 4 个登记组**：

| token | rc | 对 streak |
|---|---|---|
| `EXECUTED_CLEAN` | 0 | **计 1** |
| `SKIP_MANIFEST_V1` | 0 | 中性（仅 `schema_version == 1` 且 lock 相容时可达） |
| `SKIP_NO_ENFORCEMENT_SOURCE` | 0 | 中性（typed source **不是常规文件** —— 缺失、或被替换成目录） |
| `EXECUTED_WITH_FINDINGS` | 1 | **重置** |
| `ERROR_UNREADABLE` | 2 | **重置** |

⚠ **两个 SKIP 是两个不同字面量**，streak 脚本必须同时匹配；只 grep 四个会把
`SKIP_NO_ENFORCEMENT_SOURCE` 静默判成「无 token」。

⚠ **按输入面分开登记，勿笼统写「不可读即 rc 2」**：`ERROR_UNREADABLE` + rc 2 来自 **manifest**
加载失败（缺失 / YAML 错误 / 未知 `schema_version`）、**typed source 存在但不可解析**、任一
**`policy_ref` 不可读**、**workflow registry 缺失**、任一 **skills 投影源缺失**；而 **lock 的任何
故障态**（缺失 / 格式错误 / 信封 schema 不符 / 重复键 / BOM / 条目摘要不符）实测一律走
`EXECUTED_WITH_FINDINGS` + **rc 1**（同为重置，但**诊断指向相反** —— 据「rc 2 ⇒ lock 问题」写负向
测试会红）。

⚠ **`ERROR_UNREADABLE` 可由 enforcement 面之外的故障触发**，因为 desired-state 无条件渲染全部
surface —— 一次 skills 面的源缺失就会重置 V13 的 epoch。

⚠ **优先级与 V12 相反**：V12 先判 manifest 版本再判 findings（SKIP 抢占）；V13 **先判 drift 再判
skip 分类**，故 v1-manifest 树上一旦有 drift，V13 打 `EXECUTED_WITH_FINDINGS`（重置）而非 V12 那样
的中性 SKIP。

⚠ **五个 token 里有四个与 V12 共用字面量，且两个 step 在同一个 `ci` job 的日志里相继落盘**
（实测 anchor job `98762485194`：V12 step #42 与 V13 step #43 的 `started_at` **同为**
`05:21:57Z`，`completed_at` 分别为 `:57Z` / `:58Z`）—— **streak 度量必须按 step 切分日志**；
对整个 job log 做 grep 会把 V12 的输出计成 V13 的。

⚠ **第六种结局 = 无 token**，其成因列表是**下界而非穷举**，至少含：未捕获异常（如 manifest / lock
为非 UTF-8 字节引发的 `UnicodeDecodeError`，traceback + rc 1，被 `continue-on-error` **抹绿**）·
参数用法错误（rc 2，token 前即返回）· 本步因更早的 blocking 步失败而未执行（step
`conclusion: skipped`，此时 job **是红的**、自带信号）· job 取消或超时。
**无 token 的 run 一律不是可计数观测，须调查**，不得按「没打印就是没事」计入；其中**抹绿**的那几类
才是真正危险的。

⚠ **head-SHA 去重是必需而非可选**：`ci.yml` 同时挂 `pull_request` 与
`push[feature/bugfix/documentation/maintain/hotfix]`，故**分支名命中该 5 类前缀**的 PR 每个 head SHA
产生 **2 次** `ci` run；不去重会把 streak **高估近一倍**（静默失效，无 gate 可查）。
⚠ **但成对是「可能」不是「保证」**：`dependabot/*` 等不在 push 过滤器内的分支同样能对 develop 开 PR，
只产生 **1 次**（pull_request）—— §4 的 V13 观测 #1 即此情形。故计数一律按 head SHA 归并，
**不得**用「run 数 ÷ 2」反推观测数。

**streak 重置的边界**（§4.1.3）：**仅**因被观察 gate 的执行体非 clean 而重置；无关 job 失败 / flake
**不重置**，但须在审计产物中**登记**（含成因与影响范围）。

### 5.3 自排除规则（防循环论证）

> `policies/ci-gates.md` §4.1.3 末条要求本规则**注册时须明写**，故此处是实体条文，不是转指。

**规则**：翻转 PR **自身分支产生的 run 不计入其自身的资格证据** —— 计数须锚在**翻转分支之前的那个
commit**。

**V12 的自排除集**：PR-C1 mount（首挂）、PR-C2 anchor（登记）、以及**任何**未来的 blocking-flip PR。

**V13 的自排除集**：PR-D1a mount（首挂）、PR-D1b anchor（登记）、PR-D2 toggle（翻转）。

⚠ **F17（本工件的落地单元，issue #522）不在任一自排除集内** —— 它既非 mount、非 anchor、亦非
toggle，且**零 behavior diff、零执行体改动**。故 F17 自身 PR 产生的 run **计入**两个 gate 的 streak。
这是 PR-D1b Gate 1 把 F17 推迟到 OBSERVATION 空窗执行的判据之一。

## 6 翻转执行清单

### 6.1 V13 → blocking（消费者 = Epic #499 PR-D2）

1. 复核两腿：日历腿 ≥ 2026-09-11 **AND** 计数腿 ≥20（按 §4 度量命令 + §5.2 token 口径，按 step 切分日志）。
2. 复核零 waiver / 零未关闭 warning；产出 `evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`。
3. 取得**独立**的 `ci-blocking-gate-toggle` Owner 执行记录（issue / PR comment，per §3 W1 三要件）。
4. **翻转机制**：在既有 blocking `Tests` 路径挂载 **byte-identical predicate**
   （`--check --surface enforcement`），**不是**翻 V13 step 的 `continue-on-error`。
   本 gate 无 `--fail-on` 阈值轴（与 V10/V11 同型）。
5. 计数锚在**翻转分支之前**那个 commit（§5.3）。
6. ⚠ PR-D2 须在其 toggle 记录里把三件事**分开**写清（Epic #499 follow-up
   `#499-F21` / `F20` / `#499-F22`）：
   - `#499-F21` —— 「挂 byte-identical predicate」与「恢复 bare `--check`」是**两件可分离的事**，不是矛盾；
   - `F20` —— 恢复 PR-D1a 收窄的 real-tree 钉线。⚠ **是两处，不是一处**（见 §7 已知边界 (5)）；
   - `#499-F22` —— bare `--check`（surface=all）独有的**整份 canonical lock 文本**比对，
     在那次收窄时被一并移除，补偿断言不覆盖 envelope 级，今日无门可查。

### 6.2 V12 → blocking（消费者 = 将来的独立单元）

Epic #499 **不**追求 V12 的 blocking flip（§5.8 原文：a separate plan/toggle）。将来的翻转单元按
§6.1 同型执行，另加：

- **翻转机制**：仅 blocking 轴，**step 层** `continue-on-error: true→false`（无阈值轴 —— 脚本无
  severity 旗标）。step 层 = 与 `check-stale-docs` / `kernel-section-refs` 同型，
  **与** `docker-image-build` / `check-commit-messages` 的 **job 层不同型**。
- 翻转前须先闭合 `F16`（ci.yml step 名内嵌的 `PENDING_PR_C1_FIRST_CI` 历史标识串）或明确声明保留。

## 7 已知边界与随迁更正

> 条目 1 / 2 / 4 / 6 / 7 是**翻转不改变的不变量**；条目 3 与 **5 是随 re-home 一并更正的历史记录**，
> 且条目 5 直接构成 PR-D2 的交付义务（见 §6.1 第 6 条）—— 两类**有意并列**在此，勿当作同质。

1. **fail-closed**（per #429 判例）：任一面不可读不当作 pass —— 但两个 gate 的 rc 分派不同型，见 §5.2。
2. **V12 的第五面无 blocking owner**：五面中四面已有（V8 / V9 PJ050-053 / V10 / V9 PJ030-034），
   **fidelity 面没有** —— `check_fidelity_attestations.py` 真实树 rc 0 但**无任何 CI 挂载**
   （Epic #499 follow-up `F11` 未闭；⚠ 其 gate 编号须取 **V14+**，V12/V13 已用）。故 X07 是该面
   **唯一 CI 可见信号**。
3. **V13 无 blocking 兜底的是两个具体维度，不是整个 gate**（勿笼统写「完全无兜底」）：
   (a) artifact ↔ desired-render 的**内容漂移**、(b) **输入 digest 闭合**。V9 从不读取
   `.codex/hooks.json` / `.codex/rules/*.rules` 的**内容**，且无任何测试对这两个产物做真实树钉线。
   **但已存在的 lock 条目其 schema 仍受两个 blocking 载体硬约束**：V9 的 **PJ031**（整锁
   `verify_lock_v2`，error 级）与 blocking `Tests` 步内 `tests/unit/test_v2_engine.py` 的真实树
   `verify_lock_v2`。⚠ 条目**被整条删除**则两者皆不触发，该情形仍无兜底。
   ⇒ 与 V12 的 X07 相比，正确表述是「**V13 的未覆盖维度不同且更窄**」。
4. **`SKIP_NO_ENFORCEMENT_SOURCE` 在已提交的树上是告警态而非常态**：`sdd/adapters/codex-enforcement.yml`
   已入库，该 token 只可能出现在 typed source **不再是常规文件**时；届时执行体仍逐字打印
   `OK: … lock consistent` 且 rc 0，两个产物**及其 lock 条目不再被任何 CI 面校验**，streak 静默停滞。
   ⚠ **「破坏」不属此桶**：typed source 存在而不可解析 → `ERROR_UNREADABLE` + rc 2；
   且**删除或破坏它都会让 blocking `Tests` 步变红**（`tests/unit/test_codex_enforcement_d1a.py` 在
   **模块层**加载该真实文件，缺失即 collection error、不可解析即抛错），故这一路**有**红色信号。
5. **PR-D1a 收窄的 real-tree 钉线是两处，不是一处。** 实测（`git show c485f8d -- tests/`，两个同形
   `-` 行；且该 commit message 自述 "TWO pre-existing real-tree pins"）：
   - `tests/unit/test_agents_sync.py::test_real_tree_projection_in_sync`
   - `tests/unit/test_v2_engine.py::test_real_tree_now_takes_the_v2_paths`

   两处原本都裸跑 `--check`（surface=all），`c485f8d` 都收窄为 `skills` + `mcp`。在 `70a9db4`
   （PR-D1a 之前）上 `git grep 'sync_main(\["--check"\], repo_root=REPO_ROOT)' -- tests/` 得 **2** 处；
   在 develop `fb7ae7d` 上得 **0** 处。
   ⚠ 迁入前的 §5.9 与 `sdd/gates.md` V13 行都写「F20 要恢复的是**一处**，不是两处」——**该更正本身
   有误**：它把 `test_agents_sync.py::test_real_tree_mcp_projection_in_sync`（同文件内**本来就是**
   mcp-scoped、不在恢复面内）误当成了第二处，而漏掉了 `test_v2_engine.py` 里那一处。
   **F20 要恢复的是上列两处。**
6. **ID 碰撞非漂移**：`plans/[PLAN]_E_Phase0_Docs_Governance_Verification.md` 另有一对无关的历史
   `V12` / `V13`（wikilink 目标存在性检查 / CLAUDE.md 段落可读性验证），`decisions/ADR-012` 的两处
   `V1-V13` 引用的正是后者。按 `V12` / `V13` 做仓内 grep 复核时会命中，属预期假阳性。
7. ⚠ **blocking 翻转会机械阻断合并 —— 与两个 M-FU 先例相反，勿照搬它们的结论。**两个先例的 §7 都写「不锁 merge 按钮」（`docker-image-build` / `check-commit-messages` 都是**独立 workflow / job**，不在 required context 内）。但 **V12 与 V13 是 `ci` job 内的 step**（`ci.yml:392` / `:424`），而两个 ruleset 的 required status check 恰为 `ci`（实测 `gh api repos/MJ-AgentLab/mj-agent/rulesets/<id> --jq '[.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context]'` → `["ci"]`）⇒ 翻 V12 的 step 层 `continue-on-error` 会令**必需 check 变红并机械阻断合并**（仅 `bypass_actors` 可越，per `policies/ci-gates.md` §1.2）。**同型先例是 #399（V8/V9/V10，同为 `ci` job 内的 step），不是本节引用的那两份 M-FU。**
8. **没有任何执行体校验本工件的注册内容**（⚠ 措辞须精确 —— 不是「没有执行体读 `plans/**`」）：实测有 **4 个 CI 挂载的执行体**读 `plans/**` —— `scripts/check_frontmatter.py`（**blocking**，SCAN_ROOTS 含 `plans`）· `scripts/find_old_completed_plans.py` · `scripts/sdd/check_archived_references.py --all`（`_WALK_DIRS` 含 `plans`）· `scripts/find_stale_docs.py`（`WALK_DIRS` 含 `plans`，其 workflow 的 `paths:` 亦含 `plans/**`）。但四者分别只校验 frontmatter schema / completed-GC 候选 / `archive/` 路径引用 / 重命名与删除的反引号路径 —— **与 §4.1.1 五要素、章节指针、token 口径全部正交**。反向亦然：`scripts/check_loop_section_refs.py` 的 `WALK_DIRS` **刻意不含** `plans`，`scripts/check_wikilinks.py` 的 A4 解析只覆盖 5 个根文件。且全仓无脚本 / workflow / 测试读取 `sdd/gates.md` 的行名。⇒ §2 的 gate 标识三元组、§3 的 pickaxe 判据、§5 的 token 口径**都只靠合并审查与本文注记维持**。
   §2 的 gate 标识三元组、§3 的 pickaxe 判据、§5 的 token 口径**都只靠合并审查与本文注记维持**。

## 8 Risk Control

| 风险 | 处置 |
|---|---|
| re-home 误碰 `sdd/adapters/codex-enforcement.yml` 的三个 `policy_ref`（`AGENTS.md` / `policies/ai-agent.md` / `policies/git-branching.md`），强制 enforcement re-render → V13 报 drift、**在保护该 epoch 的 PR 上重置它**（且 step 带 `continue-on-error` ⇒ run 仍绿，静默重置） | 落地单元零字节触达该三文件；以**显式 sha 绊线**核验（§9）。⚠ `task0_freeze.py --check` **不可**充当此绊线 —— 它已在 `AGENTS.md` 上饱和（两处授权 hunk 用尽，`CONTROLLED_SURFACE_CHANGED` 恒真），对新增编辑无鉴别力 |
| 把逐 gate 值提升到 `policies/ci-gates.md` | 该文件自述不复制姿态真值，且 §4.1.1 字面要求「事先在 `plans/` 注册」。#403 提升的是**规则**不是值 —— 不同型，见 §1 |
| 删除或renumber kernel plan §5.8/§5.9 | 两节的**编号是活体引用目标**：`ci.yml` 的 V12/V13 **step 名**内嵌 `plan §5.8` / `§5.9`（且 ci.yml 内自带两处「Do NOT rename this step」），`sdd/adapters/codex-enforcement.yml` 另有 3 处 `plan SS5.9`（该文件为 `policy_ref` 之外的第四个不可碰面 —— 其自身字节即 lock 输入）。故两节**保留标题 + 开头散文 + 指针存根**，只迁走表格 |
| 新工件把两腿资格指回 kernel plan §5.10 | 会把耐久性缺口原样降一层。§5.1 **复制**两腿定义，不指回 |
| 高密度 CJK 表格 cell 的 markdown 渲染泄漏（表格 arity 检查对此全盲） | §9 的渲染断言：整文件 CommonMark 渲染 → 剔除 code span → 数字面 `*`，与 base 比 delta 必须为 0。⚠ **不得逐行渲染** —— `sdd/gates.md` 的 changelog 条目是跨行 blockquote 单斜体块，逐行法会把基线严重误报 |
| table cell 内未转义的 `\|` 拆列（inline code 内也拆） | 按 `docs/rule/[STANDARD]_GitHub_Markdown.md` §7.3 一律写 `\|`；§9 的 arity 断言按未转义 `\|` 切分复扫 |

## 9 Verification

```bash
# 注册项齐全（§4.1.1 五要素；⚠ 后两项须为实体节而非指针）
grep -n "gate 标识\|CI 首挂锚\|适用口径\|阈值 + 资格公式\|自排除规则" \
  "plans/[PLAN]_m-fu-v12-v13-gate-observation.md"

# 两条锚 SHA 可由 pickaxe 复现（§3.1 / §3.2），各得 1 个 commit
git log --oneline --reverse -S "check_cross_carrier.py" -- .github/workflows/ci.yml
git log --oneline --reverse -S "agents_sync.py --check --surface enforcement" -- .github/workflows/ci.yml

# posture 真值 = step 层 warning（运行态 SoT 永远是 ci.yml）
grep -n -A 3 "V12 cross-carrier structure\|V13 codex enforcement drift" .github/workflows/ci.yml

# 注册行存在且回指本工件
grep -n "m-fu-v12-v13-gate-observation" sdd/gates.md

# 护栏绊线：三个 policy_ref 与 lock digest 逐字未变（diff 前后各跑）
uv run --frozen --no-sync python scripts/sdd/agents_sync.py --check --surface enforcement

# 两个 gate 自身仍 clean
uv run --frozen --no-sync python scripts/sdd/check_cross_carrier.py \
  --status-json .mj-agent-local/status/cross-carrier.json
```

## 10 闭合条件

本工件为**双消费者**工件，**两条路径都收口后**方可翻 `state: completed`：

1. **V13 路径**：Epic #499 PR-D2 完成 warning → blocking 翻转，并留下独立
   `ci-blocking-gate-toggle` Owner 执行记录；
2. **V12 路径**：将来的独立 V12 flip 单元完成翻转，或 Owner 明确判定**不再追求** V12 的
   blocking flip —— 后者的落地形式是把 `sdd/gates.md` §2 的 V12 行**阻塞模式**标注为
   `withdrawn(<date>)`（该 gate-disposition 取值由该文件表头定义，理由随行内注），
   本工件随后翻 `completed`。
   ⚠ **`withdrawn` 不是 frontmatter `state` 的合法取值** —— `scripts/check_frontmatter.py` 的
   `STATE_VALUES` 只含 `draft` / `active` / `deprecated` / `completed` / `archived`，且该 gate
   **blocking**。本工件自身的 `state` 在任一路径下都只会是 `active` → `completed`。

⚠ **只有一条路径收口时不得闭合** —— 那会让另一条路径重蹈本工件所修复的失效模式（引用一份已闭合
的记录）。若两条路径的时间差过大，正确做法是**拆分**本工件而非提前闭合。
