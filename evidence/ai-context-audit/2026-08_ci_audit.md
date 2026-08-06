---
type: evidence
summary: >-
  2026-08 月度 CI blocking-flip 计数账本 —— `docker-build` gate（registry 工件
  `plans/[PLAN]_m-fu-docker-build-gate-flip.md`）观察期的 head-SHA 去重 streak、violation 数、
  影响范围与流量构成披露，作为 issue #385 warning→blocking 翻转的 `ci-blocking-gate-toggle`
  拍板依据。flip-time 权威实测：streak 33 / 阈值 20、reset 0、violation 0
owner: ranzuozhou
created: 2026-08-06
updated: 2026-08-06
state: active
track: shared
---

# 2026-08 CI Audit — `docker-build` blocking-flip 计数账本

> **这是什么**：`policies/ci-gates.md` §4.1 要求 blocking 切换保留可核验产物；
> `plans/[PLAN]_m-fu-docker-build-gate-flip.md` §6(6) 指定该产物为本文件。它记录
> `ci.yml` `docker-build` gate 在 warning 姿态下的连续-clean streak、violation 数与影响范围，
> 作为 issue #385 翻转拍板的依据。**本文件不翻转该 gate**——翻转是独立的
> `ci-blocking-gate-toggle` Owner 拍板 + #385 执行记录 comment。
>
> **落位说明**：文件名 `2026-08_ci_audit.md` 与 `check_ai_context_audit.py` 的
> `CYCLE_FILE_RE`(`YYYY-QN.md`) / `INVESTIGATION_FILE_RE`(`YYYY-MM-DD_*.md`) **皆不命中** → 落
> validator「other」桶，仅打印一行 `skip`、**不做 schema 校验、不 FAIL**；`evidence/` 亦在
> `check_frontmatter.py` `SCAN_ROOTS` 之外。**故本文件的 frontmatter 由人工核验**，两个 gate
> 都不管它。沿用 `2026-07_ci_audit.md` 的月度命名，与季度 A6 audit / ad-hoc investigation 区分。

## 1. 观察窗口与锚点（plan §3.1）

时钟属于 **gate**（钉「该 gate 在 warning 模式下无误报跑了多久」）。

| 项 | 值 |
|---|---|
| Gate | `ci.yml` `docker-build` job（registry: `sdd/gates.md` §2 `docker-image-build` 行） |
| CI 首挂 commit | `3faaec7` — `infra(ci): add docker-build gate (warning-first) for #296` |
| 首挂时刻 | **2026-07-23T07:55:16Z** / 15:55:16 +0800 |
| 锚判据 | plan §3.1 —— `git log -S "docker/Dockerfile" -- .github/workflows/ci.yml` 首命中（run 命令片段 pickaxe） |
| 窗口终点（flip-time 实测） | **2026-08-06T02:50Z** |
| 日历腿判据（**采日期算术读法**） | `2026-07-23 + 14 天 = 2026-08-06` → 08-06 当日达成 |
| 翻转执行时刻 | **2026-08-06T02:50Z** |

> **两种读法、裁定变更与诚实交代（必读）**：注册工件 §5.1 字面写「锚 + **≥14 自然日**」，
> 该措辞存在两种读法 ——
>
> - **日期算术读法**：`2026-07-23 + 14 天 = 2026-08-06`，则 08-06 当日 00:00Z 起即达标；
> - **严读（14×24h）**：门槛为 **2026-08-06T07:55:16Z**（锚 `3faaec7` 挂于 07-23T07:55:16Z）。
>
> 二者相差约 8 小时。**2026-07-24 Owner 曾拍板取严读**（比照 #399「日历腿不放宽」先例）；
> **2026-08-06 Owner 改判，明确改采日期算术读法并授权即时翻转**。本次翻转执行于 **02:50Z**,
> 即**早于严读门槛 07:55:16Z 约 5 小时 05 分**。
>
> **本账本不粉饰此点**：它**不**声称「翻转时严读门槛已满足」—— 事实上没有。成立的是：
> plan §5.1 的**字面判据**（≥14 自然日，按日期算术）已满足，且该读法由 Owner 于翻转当日
> 显式拍板选定，推翻其此前的严读裁定。记此以免日后把「按当时选定口径合规」误读成
> 「两种读法都满足」。**计数腿与读法无关**，按任一读法均为 33 / 20（余量 +13）。

## 2. 计数口径（plan §4.1.3 + §4.1.4）

- **计数域**：`ci.yml` 全部 run（任意分支），**按 head SHA 去重**（同 commit 的 `push`+`pull_request`
  对只计一次）。`ci.yml` 的 `on.push` 只含 5 类工作分支前缀（`feature/` `bugfix/` `documentation/`
  `maintain/` `hotfix/`），**不含 `develop` / `main`** → **合入 develop 的 merge commit 不产生 run**
  （实测核验：`08d53bb` / `1aecfc3` / `0aac07e` 在窗口 run 集中命中数皆为 0）。
- **clean 判据 = step 级，不是 job 级**（关键）：本 gate 带 job-level `continue-on-error: true`，
  **job 结论恒 `success`**，即使构建失败。SoT = job 内 **`Build image (no push)` step 的
  `conclusion`**。
- **三态归类**（plan §4.1.4）：
  - `success` → **executed & clean**，计 1；
  - `failure` / `cancelled` → **violation**，重置 streak；
  - `skipped` → **未触发，中性**，不计数也不重置；
  - **step 不存在** → 该 ref 上无本 gate，**剔除**（不入分母）。

## 3. 度量方法（本次实测的具体实现）

**不使用 `gh run view --log`** —— 该 logs 端点在批量抓取时会触发 GitHub **secondary rate-limit**
（2026-07 账本 §3 已记录同一教训）。改用 core REST 的 jobs 端点逐 run 读 step 结论：

```bash
gh run list --workflow ci.yml --limit 200 \
  --json databaseId,headSha,createdAt,status,conclusion,event,headBranch
# 过滤 createdAt >= 2026-07-23T07:55:16Z 且 status=completed，逐 run：
gh api repos/MJ-AgentLab/mj-agent/actions/runs/<id>/jobs \
  --jq '.jobs[].steps[]|select(.name=="Build image (no push)")|.conclusion'
# 按 head SHA 聚合三态 → 去重计数
```

> **实施注记**：`.../jobs` 端点会偶发 EOF，须**重试**——把一次失败读成「没构建」会污染计数。
> 本次采集实现了 5 次退避重试；实际 61 个 run 全部一次成功，无重试触发。

## 4. 计数结果（flip-time 权威实测 2026-08-06T02:50Z）

| 项 | 值 |
|---|---|
| 窗口内 `ci.yml` run 总数 | 61（全部 `status=completed`） |
| distinct head-SHA | 35 |
| ├─ **剔除**（ref 上无本 gate） | 1 |
| ├─ **中性**（仅 `skipped`，未触发） | 1 |
| ├─ **executed & clean** | **33** |
| └─ **violation**（executed 且非 clean） | **0** |
| **streak（去重后连续 clean）** | **33** |
| streak 重置次数 | **0** |

**两腿判定（plan §5.1，AND）**：

| 腿 | 门槛 | 实测 | 判定 |
|---|---|---|---|
| 日历腿 | plan §5.1 字面：锚 + ≥14 自然日 → **2026-08-06**（日期算术读法；Owner 2026-08-06 改判选定） | 翻转执行于 **2026-08-06T02:50Z** | ✅（按选定读法；**严读门槛 07:55:16Z 当时未到**，见 §1 注） |
| 计数腿 | ≥20（§4.1.3 去重 + §4.1.4 三态） | **33**（余量 +13） | ✅ |

> **度量的独立复核**：本次计数由**两套彼此独立编写的脚本**分别求得，结果逐项一致
> （35 distinct SHA → 33 clean / 0 violation / 1 中性 / 1 剔除，reset 0，Dependabot 8/33）。
> 枚举型结论单口径易错，故按纪律换第二实现复核后才写入本账本。

### 4.1 两个非 clean-executed 条目的逐条交代

| head-SHA | 分支 | 归类 | 判据 |
|---|---|---|---|
| `1ac2118` | `hotfix/400-dependabot-directory-main` | **剔除** | 该分支基于 `main`，而 `main` 的 `ci.yml` **不含**本 gate（实测 `git show origin/main:.github/workflows/ci.yml \| grep -c docker-build` → **0**）。两个 run 里根本没有 `Build image (no push)` step，非「跳过」而是「gate 不存在」。 |
| `1964db4` | `maintain/413-docker-stop-visibility` | **中性** | 非首推、diff base 可解析、改动仅根 `AGENTS.md`（1 file / +15-3）→ 未命中触发路径集 → `skipped`。按 §4.1.4 不计数亦不重置。 |

### 4.2 violation 数 + 影响范围

- **violation 数 = 0** —— 窗口内 33 个真实构建全部 `success`，零重置。
- **影响范围**：翻转在 flip-time HEAD 为 **zero-delta** —— 现存代码无任何 PR 会因翻转而受阻。
  此后影响面 = 任何令 `docker build -f docker/Dockerfile` 失败的 PR 将被**阻断**而非仅告警。
- **回退成本**：单行 `continue-on-error: false → true`。

## 5. 流量构成披露（plan §5.2 强制）

plan §5.2 要求披露而非隐去以下三项：

1. **Dependabot 占比**：33 个 streak SHA 中 **8 个来自 Dependabot 分支（24%）**，25 个人工。
   Dependabot 的 GitHub-Actions / docker-compose 版本升级会改 `ci.yml` 或 `docker/**` = 触发路径
   → 产生**真实**构建而非空绿，故计入合法。
2. **零-run 间隙（两段，非一段）**：窗口 61 个 run 只落在 **6 个自然日**上
   —— `07-23`(6) / `07-24`(10) / `07-27`(3) / `08-03`(4) / `08-04`(12) / `08-05`(26)，
   存在**两段**空档：
   - **2026-07-25 → 07-26，2 个自然日**；
   - **2026-07-28 → 08-02，6 个自然日**（前一个 run `69bc709` @ 07-27T01:08:00Z，
     后一个 `4f132a5` @ 08-03T07:57:01Z）。

   二者均不违反「连续、跑真实流量」（#399 已受理的窗口含后一段同一间隙），但按 §5.2
   须**全部**明载 —— 只披露最长的一段即构成选择性披露。**诚实读法**：本窗口的「连续」
   是*姿态连续*（gate 全程挂在 CI 上、每个触发都执行）而非*每日有流量*；14 个自然日中
   8 天无任何 run。计数腿的 33 因此高度集中在 08-04 / 08-05 两天的密集 PR 活动上。
3. **无关 job 失败登记（不重置 streak）**：见 §5.1。

### 5.1 无关 job 失败登记

计数域限定为 `ci.yml` 的 run；下列失败属 `Dependabot Updates` workflow（`event=dynamic`），
**不含本 gate 的任何 step** → **不重置 streak**，但须登记：

| 时间（UTC） | job | 结论 | 重置？ |
|---|---|---|---|
| 2026-07-27T01:07:18Z | `docker in /infra/docker` | failure | 否 |
| 2026-07-27T01:07:17Z | `docker_compose in /infra/docker` | failure | 否 |
| 2026-08-03T01:06:15Z | `docker in /infra/docker` | failure | 否 |
| 2026-08-03T01:06:15Z | `docker_compose in /infra/docker` | failure | 否 |
| 2026-08-05T06:16:47Z | `docker_compose in /docker` | failure | 否 |

**状态更正（相对 2026-07 账本 §7.4）**：该账本把上述失败整体归因于 #400（`main` 的
`dependabot.yml` 仍指 `/infra/docker`）。#400 已由 **PR#419 于 2026-08-05T06:16:41Z 合入 `main`**
修复，**但只止血了一半**：

| ecosystem | PR#419 后结论 |
|---|---|
| `github_actions in /.` | success |
| `docker in /docker` | **success**（#400 修复生效） |
| `docker_compose in /docker` | **仍 failure** |

`docker_compose` 的残留失败是**独立的既有缺陷**，与 #400 的目录错指无关：`docker/compose.yaml:77`
的 `image: mj-agent:0.1`（无 registry 前缀 → 被按 Docker Hub `library/mj-agent` 解析 → 401）与
`docker/compose.{test,prod}.yml:13` 的 `image: 8.135.38.175/mj-agent/mj-agent:0.1`（私有 Harbor，
runner 不可达 → `private_source_timed_out`）都是**首方镜像引用，Dependabot 永远解析不了**。
已另立 issue **#433**（`maintain`）。本账本只履行登记义务。

## 6. 诚实边界（caveat；不掩盖）

- **「PR-event run 必 skip / 只有 push run 真构建」是错的**——本次实测明确证否：窗口内
  **14 个 `pull_request` run 真实执行了构建**（Dependabot 的 docker/gha 升级、改 `ci.yml` 的 PR、
  改 `docker/**` 文档的 PR），而 **1 个 `push` run 反而 skip**（`1964db4`）。真正的决定因素是
  **触发路径集 + fail-open**，不是事件类型：新分支首推 base 为 all-zeros → fail-open 无条件构建；
  非首推且 diff base 可解析时按路径过滤。**据事件类型推断构建与否会误计**——必须逐 run 读 step 结论。
- **fail-open SHA 的掩蔽（plan §7，翻转不改变）**：`/mj-agent-git-check-merge` 按 check name 去重取
  `startedAt` 最晚者。fail-open 类 SHA 上 push run 构建、PR run skip 且更晚开始 → **绿 skip 会盖住
  红构建**。该缺陷**不因本次翻转而消除**；根治法（把本 job 收窄为仅 `pull_request` 触发）属
  #385 明列的 out-of-scope。
- **本 gate 不在 required status checks 内**（plan §7）：`protect-develop` / `protect-main` 两个
  ruleset 各只要求 `[{"context":"ci"}]`。翻转后本 gate 会**红**且会令
  `/mj-agent-git-check-merge` 判 “Not Ready to Merge ❌”，但**不**机械锁死 GitHub merge 按钮。
  是否加入 required contexts = 可选硬化，非翻转前置。
- **触发路径集过宽（plan §3.2）**：`^docker/` 亦匹配 `docker/{AGENTS,CLAUDE,README}.md` 等纯文档
  —— 翻转后 docs-only PR 也会被暴露给外部构建依赖的抖动。收窄与否是独立决定。

## 7. 自排除（plan §5.3，防循环论证）

翻转 PR 自身改 `ci.yml` = 命中触发路径，其分支会产生新的 head-SHA。**这些 run 不计入其自身的
资格证据**。本账本 §4 的计数窗口终点为 **2026-08-06T02:50Z**，最后一个计入的 head-SHA 为
`eb36fac`（`documentation/429-plan-state-flip`，PR#432 @ 2026-08-05T13:48Z），**早于翻转分支
`maintain/385-docker-build-gate-flip` 创建**——满足 §5.3。

翻转分支自身的 run（其首推为新分支 all-zeros base → fail-OPEN 无条件构建，且本 PR 改
`ci.yml` 本就命中触发路径）**不进入上表任何一格**。该 run 的意义是 **AC-4 验证**
（「翻转后 gate 以 blocking 姿态跑通」），不是资格证据 —— 两者不可混用。

## 8. 翻转执行记录

- **执行 issue**：#385
- **翻转日期**：**2026-08-06**（执行时刻 02:50Z）
- **拍板**：`ci-blocking-gate-toggle` —— Owner 独立拍板 1 次（本次仅 1 个 gate），
  执行记录 = #385 comment
- **日历腿读法**：Owner 于 2026-08-06 改判，改采**日期算术读法**并授权即时翻转，
  推翻其 2026-07-24 的严读裁定；翻转早于严读门槛 07:55:16Z 约 5h05m。详 §1 注。
- **registry 工件**：`plans/[PLAN]_m-fu-docker-build-gate-flip.md` §10 闭合 ——
  `state: active → completed` 走**独立** `documentation/385-plan-state-flip` PR
  （家族惯例，先例 #358 / #361 / #364 / #432），不混入本翻转 PR。
- **改动面**：`.github/workflows/ci.yml`（job name + `continue-on-error` + 块注释）·
  `sdd/gates.md`（`docker-image-build` 行 + frontmatter v0.4 + 版本脚注）·
  `docker/CLAUDE.md`（`:88` / `:93`）· `plans/[PLAN]_m-fu-docker-build-gate-flip.md`
  （§6(5) 行号更正）· 本账本 · PR 模板勾选
