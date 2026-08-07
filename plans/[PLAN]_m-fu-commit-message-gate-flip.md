---
type: plan
slug: m-fu-commit-message-gate-flip
summary: >-
  M-FU 注册工件 `M-FU-COMMIT-MESSAGE-GATE-FLIP` —— 为 check-commit-messages gate 注册明文观察期
  （CI 首挂锚、适用口径、阈值、资格公式、自排除规则），满足 policies/ci-gates.md §4.1.1 注册制 +
  policies/ai-agent.md §4 对 ci-blocking-gate-toggle 的「M-FU plan 必先 register」前置；
  与 gate 本体同批落地（出生即注册），消费者 = 将来的 warning→blocking 翻转 issue
owner: ranzuozhou
created: 2026-08-07
updated: 2026-08-07
state: active
version: 1.0
track: engineering-workflow
---

# [PLAN] M-FU-COMMIT-MESSAGE-GATE-FLIP — `check-commit-messages` gate 观察期注册

> **标识**：`M-FU-COMMIT-MESSAGE-GATE-FLIP`（per `policies/ci-gates.md` §4.1.1 注册制 +
> `policies/ai-agent.md` §4 `ci-blocking-gate-toggle` 的「M-FU plan 必先 register」）。
> **性质**：**出生即注册** —— 观察期与 gate 本体在同一个 PR 落地，注册**不晚于**首挂。
> Issue: [#444](https://github.com/MJ-AgentLab/mj-agent/issues/444)（gate 本体 + 本注册）。
> 消费者 = 将来的 blocking 翻转 issue（尚未创建；翻转本体是独立的 Owner 拍板）。

## 1 为何需要本工件

`policies/ci-gates.md` §4.1.1 把「明文观察期」定义为**注册制**：gate 恰好以 warning 跑了一段时间
**不**构成观察期，未注册者**不享** §4.1 的时序吸收，回落 §4 表「Gate 启用前」行（切换前 1 周 DRI
dry-run，且**无**连续次数阈值）。

本仓已经在同一个坑上摔过两次，方向相反：

- **`docker-build`（#296 → #403）**：2026-07-23 落地 warning，**12 天后**才补注册。补注册时才发现
  它是本仓首个 path-triggered gate，§4.1.3 的计数口径对它根本没定义，只好临时新增 §4.1.4 —— 一次
  本可以在落地当天完成的规则设计，被推迟成了翻转前的阻塞项。
- **`check-stale-docs`（#440）**：自 2026-05-09 在 CI 跑，**从未**进注册表，其「4 周后转 blocking」
  的承诺既未按 §4.1.1 注册、又因执行体恒 `return 0` 而机械上不可兑现，悬空近 3 个月无人负责。

故 #444 把注册**前置到 gate 出生的同一个 PR**：本工件与 `scripts/check_commit_messages.py`、
`.github/workflows/check-commit-messages.yml`、`sdd/gates.md` §2 注册行同批合入。

## 2 注册项（对齐 `policies/ci-gates.md` §4.1.1 表）

| 注册项 | 值 |
|---|---|
| **gate 标识** | `sdd/gates.md` §2 行名 `check-commit-messages`；workflow 名 `check-commit-messages`；job 名 `check-commit-messages`（三者**逐字同名**，有意为之 —— V10 那次正是因 step 名被改写而令 pickaxe 误指 `b8f43d3`） |
| **CI 首挂锚** | `cd79b5c` · **2026-08-07 11:46:10 +0900**（判据见 §3） |
| **适用口径** | `policies/ci-gates.md` §4.1.3（head-SHA 去重）。**§4.1.4 不适用** —— 见 §3.2 |
| **阈值 + 资格公式** | §5（两腿 **AND**） |
| **自排除规则** | §5.3 |
| **触发路径集**（§4.1.4 额外义务） | **不适用** —— 本 gate 非 path-triggered，见 §3.2 |

## 3 起点锚判据

### 3.1 锚 commit

`policies/ci-gates.md` §4.1.2 的规范判据是「以该 gate 在 CI 内的**首次出现**为准，用 **run 命令
片段**做 pickaxe，不用 step/job **名**（名可能被改写而误指）」。§4.1.2 的命令示例写的是
`-- .github/workflows/ci.yml`，因为成文时全部 gate 都住在 ci.yml；本 gate 自始住在**自己的
workflow**，故 pathspec 相应替换：

```bash
git log --oneline --reverse -S "scripts/check_commit_messages.py" \
  -- .github/workflows/check-commit-messages.yml
# → cd79b5c infra: add check-commit-messages gate (warning-first) for #444
```

> **判据不变，只换 pathspec**：`docker-image-build` 在 #438 迁出 ci.yml 后同样保留了原锚
> （`3faaec7`，仍在 ci.yml 里），说明「锚属于 gate、不属于文件」。本 gate 从未在 ci.yml 出现过，
> 因此不存在双 pathspec 歧义。
>
> **分支重写会使锚失效**：若本 PR 的分支被 force-push / rebase 重写，上述 SHA 会改变 ——
> 复核时以 pickaxe 命令的**当次输出**为准，并回写本节。合入 develop 后 SHA 即固定
> （本仓用 merge commit，feature commit 的 SHA 不被合并改写）。

### 3.2 本 gate **非** path-triggered（§4.1.4 明确不适用）

`.github/workflows/check-commit-messages.yml` 的 `on.pull_request` **没有 `paths:` 过滤器** ——
**每个 PR 都起 job**，恒产出恰好一个 check run，永不出现 job 级 `skipped`。（判定 step 上确有一个
条件，即 §3.3 的 release PR 豁免；它在 **step 层**，不改变「job 必起、check run 必在」这一性质。）故：

- 适用 §4.1.3 的朴素口径：计数域 = 该 workflow 的全部 run，按 head SHA 去重，计数条件 =
  **执行体输出 clean**（不是 run 级 conclusion —— 本 gate job 层带 `continue-on-error: true`，
  会把失败掩成绿 run）。
- **不**适用 §4.1.4 的三态口径：本 gate 的 job 永不产生 `skipped` conclusion，没有「job 未触发」
  的情形。**但有一个必须分列的中性桶** —— 见 §3.3。

### 3.3 release PR 中性桶（本 gate 专属的计数细则）

`policies/release.md:58` 定义 Phase 1+ 的 release PR 是 **develop → main**。`main` 是旧发布点、
落后 develop 数百个 commit，故此类 PR 的 `origin/main..<head>` **不是**「该 PR 自身的提交」，
而是自上次发布以来的全部历史 —— 判它会把存量违规一次性点亮，令 gate 在 release PR 上**恒红**，
正是 #444 校验范围表明令禁止的「不得因历史存量而恒红」。而这些 commit **每一条都已在各自并入
develop 的 PR 上被本 gate 判过**，重判是重复而非覆盖。

故 workflow 以**精确谓词**（`base == main` **AND** `head == develop`）在 **step 层**跳过判定
（step 层而非 job 层：job 仍执行、仍产出恰好一个 check run，不产生 `skipped` 从而不破坏 §3.2 的
「每 PR 必执行」性质）。**hotfix PR 不豁免** —— 其 head 是 `hotfix/*`，`base..head` 确是自身提交。

**计数义务**：release PR 产生的 run 是**空绿**（vacuously clean），**必须从 streak 中剔除**，
与 §4.1.4 把 `skipped` 记为中性同一精神。审计时须**分列**「真实判定绿」与「release 豁免」两个
计数，不得合并 —— 否则阈值会被空绿充满。识别判据 = PR 的 `base=main` 且 `head=develop`。

> **历史校准**：截至 2026-08-07 本仓**尚未发生过** release PR（4 个 base=main 的已合并 PR
> 全部是 hotfix / 单分支 maintain / bugfix）。故本桶当前为空，但规则先立 —— 首个 release PR
> 出现时不应临时解释。

**计数域的度量命令**（替代 §4.1.3 的 `--workflow ci.yml`）：

```bash
gh run list --workflow check-commit-messages.yml --limit 100 \
  --json conclusion,createdAt,headSha,event,databaseId
# 按 headSha 去重后，自 §3.1 的锚起，逐 SHA 核该 job 执行体的输出（不看 run conclusion）
```

> **`push` 事件下本 workflow 不产生任何 run**（仅 `pull_request` 触发），故不存在
> `docker-image-build` 在 #438 之前那种「同一 head SHA 的 push/PR 双 run 互相掩蔽」问题。

## 4 观察期实测

**空 —— 观察期自锚 `cd79b5c`（2026-08-07）起算，注册时尚无任何 run。**

> **时钟属于锚 commit，不属于合并日**（§4.1.2：「以该 gate 在 CI 内的首次出现为准」）。本工件与
> gate 同批落地，故二者相差不超过本 PR 的存续时间；如需精确，以 §3.1 pickaxe 输出的 commit 日期
> 为准。**gate 在本 PR 上的首跑不计入 streak** —— 那是本分支自造的 run，被 §5.3 自排除规则剔除。

这是「出生即注册」相对于补注册的唯一形式差异：docker 那份注册工件在 §4 携带了 12 天的基线快照，
本工件没有可快照的历史。翻转拍板时须按 §3.2 的度量命令**当场重跑**并产出证据账本
`evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（per §4.1 「产物保留」）。

## 5 资格公式

### 5.1 两腿（AND）

| 腿 | 判据 | 现状（注册时） |
|---|---|---|
| **日历腿** | 锚日 + **≥14 自然日**，连续、跑真实流量 | 锚 2026-08-07 → 最早 **2026-08-21** |
| **计数腿** | §4.1.3 口径（head-SHA 去重、执行体 clean）**≥20** | **0 / 20**（本 PR 自身的 run 按 §5.3 自排除） |

**资格 = 两腿同时满足**；任一未满足即不构成资格，**不得**以单腿满足代替。

> **日历腿读法**：`policies/ci-gates.md` §4.1 只写「≥14 自然日」，未规定日期算术是取**日期差**
> 还是取**时刻差**。#385 翻转时 Owner 于 2026-08-06 拍板取**日期算术**读法（推翻其 07-24 的严读），
> 并在账本 / 执行记录 / commit 三处留痕「未宣称两读皆满足」。**本工件不预设读法** —— 若翻转时刻
> 落在两读的差值区间内，须比照 #385 的处理如实留痕，不得只报有利的一读。

### 5.2 本 gate 的 streak 语义（与既有 gate 的关键差异，务必读）

`docker-image-build` / V8 / V9 / V10 的执行体在正常开发下**恒 clean**，streak 重置意味着出了事故。
**本 gate 不然**：只要某个 PR 里有一条不合规的 commit message，执行体就非 clean，streak 归零。

**这是设计意图，不是噪声。** 计数腿在这里衡量的正是「新提交是否已经收敛」——它就应该由「连续 20
次 PR 无人写错」来证明。因此：

- **不得**把 streak 重置当作「gate 误报」而放宽阈值或改判定口径；
- **不得**用「历史存量违规」质疑本 gate —— 判定域是 `<base>..<head>`，`develop` 上那 157 条历史
  违规（105 scope + 33 type + 18 双括号 + 1 header-format）**永远**不进入计数；
- 每次重置须在证据账本中登记**具体 commit + 违规类别**，作为「规范哪一条最常被违反」的输入。

### 5.3 自排除规则（防循环论证）

翻转 PR 自身分支产生的 run **不计入**其自身的资格证据 —— 计数须锚在**翻转分支之前的那个
commit**。本 gate 每个 PR 必执行，故翻转 PR 必然自造 run；该规则在此比 path-triggered 的
`docker-image-build` 更容易被误用，须显式排除。

### 5.4 翻转的**额外**前置（本 gate 专属）

除两腿外，翻转拍板前须确认下列两项，因为它们是本 gate 特有的「翻转后才会疼」的面：

1. **§4.5 责任归属已在实践中被遵守** —— STANDARD §4.5 规定「新增顶层目录 / 模块的那个 PR 同批更新
   §4.1-§4.2 表格」。若该纪律未被遵守，blocking 姿态会把一个**本应改 STANDARD** 的 PR 卡在
   commit message 上，而修复要同时改 STANDARD **并**重写已推分支。翻转前应核对观察期内是否发生过
   「新目录落地但 scope 未同批加入」。
2. **判定面是否要扩** —— 本期只判 type/scope。§2.2 的外观规则与 §5.2 分支×type 矩阵若在翻转的
   同时启用，会把一次 posture 变更和一次判定面扩张混在一起，届时无法归因。**若要扩判定面，
   应先以 warning 姿态扩、另起观察期**，不与本次翻转合并。

## 6 翻转执行清单（消费者 = 将来的翻转 issue）

翻转本体属 `ci-blocking-gate-toggle` **必停**，须 Owner 独立拍板 + 独立执行记录 comment。

1. `.github/workflows/check-commit-messages.yml` 的 **job 层** `continue-on-error: true` →
   **`false`**（写显式 `false`，不删键 —— 保留键使回滚是一行值变更）。
   ⚠ **不是 step 层** —— `check-stale-docs` 的 `continue-on-error` 在
   `jobs.check-stale-docs.steps[-1]`，照搬那个先例会改错位置且不产生任何效果。
2. 无阈值轴可翻（执行体无 `--fail-on` 旗标；单轴，与 V10 / `docker-image-build` 同型）。
3. 同批更新 `sdd/gates.md` §2 该行 posture 真值 + `version` bump + 版本脚注新增一条。
4. 产出证据账本 `evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（violation 数量 + 影响范围 +
   §5.2 要求的重置明细 + §5.1 日历腿读法留痕）。
5. 本工件 `state` → `completed` + 补 `completed:` 字段（走独立的 plan-state-flip PR，
   先例 #358 / #361 / #364 / #432）。

## 7 已知边界（翻转**不**改变的事实）

- **不锁 merge 按钮**：`protect-develop` / `protect-main` 的 required contexts 各只要求 `ci`，
  本 gate 不在其中。翻转令其变红，但不机械阻断合并。把它加入 required contexts 是**可选硬化**，
  属独立决定，**非**翻转前置。
- **不追溯历史**：判定域恒为 `<base>..<head>`，`develop` / `main` 上的存量违规不会因翻转而变红。
  唯一会让「存量」落进判定域的 PR 形态是 **release PR（develop → main）**，已按 §3.3 显式豁免；
  该豁免是这条边界成立的**前提**，不是补丁 —— 移除它，本条即不再为真。
- **不改 STANDARD**：本 gate 是 STANDARD 的**消费者**，白名单/type/别名全部从其表格派生。
  改规则永远只改 STANDARD，不改 gate。

## 8 Risk Control

| 风险 | 缓解 |
|---|---|
| STANDARD 结构调整令解析器取不到白名单 | 执行体 fail-closed 退出 2 并打印诊断；`tests/unit/test_check_commit_messages.py` 有三条 fail-closed 用例 + 真实树钉线（35 scope / 7 type / 23 alias） |
| 诊断层（§4.3 / §4.6 散文）被改写 | 有意**不** fail-closed：提示降级为通用文案，判定不变；`test_diagnostics_degrade_but_do_not_fail_closed` 钉住该分层 |
| 翻转后合法 PR 被卡 | §5.4 第 1 项前置核对 + §7 第 1 条（不在 required contexts，仍可合并） |
| 注册工件与 gate 现状漂移 | 本工件 §2 的 gate 标识与 workflow / job / gates.md 行名逐字同名，任一改名都会让 §3.1 的 pickaxe 落空而被发现 |

## 9 Verification

```bash
# 注册项齐全（§4.1.1 五字段）
grep -c "gate 标识\|CI 首挂锚\|适用口径\|阈值 + 资格公式\|自排除规则" \
  "plans/[PLAN]_m-fu-commit-message-gate-flip.md"

# 锚 SHA 可由 pickaxe 复现（§3.1）
git log --oneline --reverse -S "scripts/check_commit_messages.py" \
  -- .github/workflows/check-commit-messages.yml

# posture 真值 = job 层 warning
python -c "import yaml;d=yaml.safe_load(open('.github/workflows/check-commit-messages.yml',encoding='utf-8'));\
print(d['jobs']['check-commit-messages']['continue-on-error'])"   # → True

# 注册行存在
grep -c 'check-commit-messages' sdd/gates.md
```

## 10 闭合条件

本工件在**翻转落地**后 `state` → `completed`（per §6 第 5 项）。若将来改判「不追求 blocking」，
则按 `check-stale-docs`（#440）的体例：在 `sdd/gates.md` 注册行写明长期 warning 立场与理由，
本工件同样转 `completed` 并在此记录改判依据 —— **两条路径都不留悬空**。
