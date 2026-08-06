---
type: plan
slug: m-fu-docker-build-gate-flip
summary: >-
  M-FU 注册工件 `M-FU-DOCKER-BUILD-GATE-FLIP` —— 为 ci.yml `docker-build` gate 注册明文观察期
  （CI 首挂锚 3faaec7 / 2026-07-23、口径、阈值、资格公式、自排除与触发路径集），满足
  policies/ai-agent.md §4 对 ci-blocking-gate-toggle 的「M-FU plan 必先 register」前置；
  消费者 = issue #385（warning→blocking 翻转），本工件随该翻转落地而闭合
owner: ranzuozhou
created: 2026-08-04
updated: 2026-08-06
completed: 2026-08-06
state: completed
version: 1.0
track: engineering-workflow
---

# [PLAN] M-FU-DOCKER-BUILD-GATE-FLIP — `docker-build` gate 观察期注册

> **标识**：`M-FU-DOCKER-BUILD-GATE-FLIP`（per `policies/ci-gates.md` §4.1.1 注册制 +
> `policies/ai-agent.md` §4 `ci-blocking-gate-toggle` 的「M-FU plan 必先 register」）。
> **性质**：**前瞻注册**（非 retroactive 补登）—— 观察期 2026-07-23 开启，本工件于
> 2026-08-04 注册，翻转尚未发生。
> Issue: [#403](https://github.com/MJ-AgentLab/mj-agent/issues/403)（注册者）·
> [#385](https://github.com/MJ-AgentLab/mj-agent/issues/385)（消费者 / 翻转本体）

## 1 为何需要本工件

`policies/ai-agent.md:98` 对 `ci-blocking-gate-toggle` 明载「per Stage C C-a 流程；**M-FU plan
必先 register**」。截至 2026-08-04，`docker-build` gate **从未在任何 plan 注册**
（`grep -rn "docker-build\|docker-image-build" plans/` → exit 1）。

同时 `policies/ci-gates.md:48` 把 §4.1 的「吸收时序、保留产物」**条件化**于该 gate 曾跑过一个
**明文观察期**，`:60-61` 收口「**无明文观察期的 gate 不享此豁免，本行照常适用**」。故在本工件
落地前，`docker-build` 严格读法下**不受** §4.1 管辖，而回落 §4 表「Gate 启用前」行
（1 周 dry-run，**无连续次数阈值**）。

**Owner 2026-08-04 拍板**：接受「可辩护性优先于速度」的折衡 —— 注册即令 #385 落入 §4.1 管辖，
「20 次连续」由非强制变为**强制**（详见 §4 实测：现 16/20）。理由是 #385 issue body 本身已自标
14 日 / 20 连绿，注册只是为已接受的标准补上合法来源，而非新增负担。

## 2 注册项（对齐 `policies/ci-gates.md` §4.1.1 表）

| 注册项 | 值 |
|---|---|
| **gate 标识** | `sdd/gates.md` §2 行名 `docker-image-build`；`ci.yml` job 名 **`docker-build (warning)`**（翻转前**逐字**记录，per §6 重命名顺序陷阱） |
| **CI 首挂锚** | `3faaec7` · **2026-07-23 15:55:16 +0800**（判据见 §3） |
| **适用口径** | `policies/ci-gates.md` §4.1.3（head-SHA 去重）**＋ §4.1.4 path-triggered 细则**（`skipped` 中性） |
| **阈值 + 资格公式** | §5（两腿 **AND**） |
| **自排除规则** | §5.3 |
| **触发路径集**（§4.1.4 额外义务） | §3.2 |

## 3 起点锚判据

### 3.1 锚 commit

按 `policies/ci-gates.md` §4.1.2「以 `ci.yml` 内该 gate 的首次出现为准，用 **run 命令片段**
做 pickaxe」：

```bash
git log --oneline --reverse -S "docker/Dockerfile" -- .github/workflows/ci.yml
# → 3faaec7 infra(ci): add docker-build gate (warning-first) for #296
```

> **本 gate 两种 pickaxe 同解**：job **名** pickaxe（`-S "docker-build"`）亦返回 `3faaec7`，
> 与 V10 那次（step 名被 #330 改写致误指 `b8f43d3`）不同。**同解不等于判据可换** ——
> 规范判据仍是 run 命令片段；此处只是记录二者本轮恰好一致，供复核。

### 3.2 触发路径集（path-triggered gate 的额外注册义务）

`ci.yml` 的 detect step 正则（翻转前状态）：

```text
^(docker/|\.dockerignore$|pyproject\.toml$|uv\.lock$|README\.md$|\.github/workflows/ci\.yml$)
```

- **fail-OPEN**：diff base 缺失 / 不可解析（新分支首推 all-zeros、force-push、孤儿 base）时
  **无条件构建**，不静默 skip。
- **已知过宽面**：`^docker/` 亦匹配 `docker/{AGENTS,CLAUDE,README}.md` 等纯文档
  —— 文档改动会触发一次不可能回归的完整构建（`3faaec7` 本身即一例）。
  warning 姿态下仅费 runner 分钟；**blocking 姿态下会把 docs PR 暴露给外部构建依赖的抖动**。
  收窄与否属 #385 翻转拍板时的独立决定，**不在**本注册的规范内容内。

## 4 观察期实测（快照 2026-08-04，**非**翻转拍板依据）

> **`实测勿外推`** —— 翻转拍板须在**当时**按 §4.1.3 度量命令重跑（delta 法）。本节仅为注册时
> 的基线快照，**不**充当资格证明；正式证据工件 = `evidence/ai-context-audit/2026-08_ci_audit.md`
> （随 #385 翻转 PR 产出，**尚未创建**）。

| 项 | 值 |
|---|---|
| 窗口 | 2026-07-23（锚）→ 2026-08-04 |
| `ci.yml` run 总数（窗口内） | 41 |
| 其中**不含**本 gate（ref 早于锚） | 14 → 剔除 |
| 含本 gate 的 run | 27 |
| ├─ 构建执行体**真实执行且 clean** | 19 |
| └─ **未触发**（`skipped`，§4.1.4 中性） | 8 |
| **streak（head-SHA 去重后，真实执行绿）** | **16** |
| streak 重置次数 | **0** |
| 零 waiver / 零未关闭 warning | 是（全 27 run 的 check-run annotation 数 = 0） |
| 无关 job 失败（登记，不重置） | 「Dependabot Updates」workflow 4 次 —— 属 #400（main 的 `dependabot.yml` 未同步），与本 gate 无关 |

**口径分歧披露**（诚实边界）：若不按 §4.1.3 去重、也不按 §4.1.4 剔除未触发，则「窗口内无违规的
run 数」= **27**，会**误达**阈值。#385 issue body 的 Verification Plan 恰好写的是
「`gh run list` **green-run tally**」= 该宽口径。本注册**明确采用 16**（严口径），并把差异写在
此处，以免翻转时发生口径漂移。

## 5 资格公式

### 5.1 两腿（AND）

| 腿 | 判据 | 现状（2026-08-04） |
|---|---|---|
| **日历腿** | 锚 `2026-07-23` + **≥14 自然日**，连续、跑真实流量 | **12 / 14** → 最早资格 **2026-08-06** |
| **计数腿** | §4.1.3 + §4.1.4 口径 **≥20** | **16 / 20** → 差 4 |

**资格 = 两腿同时满足**。任一未满足即不构成资格；**不得**以单腿满足代替。

### 5.2 流量构成披露

窗口内 16 个 streak SHA 中 **5 个来自 Dependabot**（31%），11 个人工。2026-07-28 → 08-02 存在
**6 日零 run 间隙**。二者均**不**违反「连续、跑真实流量」（#399 已受理的窗口含同一间隙），
但须在证据工件中**披露**，不得隐去。Dependabot 每周一 ~01:0x UTC 触发，其
GitHub-Actions 版本升级会改 `ci.yml` = 触发路径 → 产生**真实**构建而非空绿。

### 5.3 自排除规则（防循环论证）

翻转 PR 自身会改 `ci.yml`（= 触发路径），其分支产生的 run 会制造新的 head-SHA。
**这些 run 不计入其自身的资格证据** —— 计数须锚在**翻转分支之前的那个 commit**。
（#399 已实践此法：其翻转分支 `4f132a5` 不在其 delta 表内，但未明写规则；本工件明写。）

## 6 翻转执行清单（消费者 = #385）

翻转本体属 `ci-blocking-gate-toggle` **必停**，须 Owner 逐 gate 独立拍板 + 独立执行记录 comment。

1. `.github/workflows/ci.yml:409` `continue-on-error: true` → **`false`**（写显式 `false`，
   **不删键** —— #399 先例）。
2. `ci.yml:407` `name: docker-build (warning)` → `docker-build`（#385 AC）。
   > **重命名顺序陷阱**：required status check 按 **check-run 名逐字**匹配。若将来把本 gate
   > 加入 ruleset required contexts（当前**未加**，见 §7），加 context 与改名的先后错位会留下
   > 一个**永不上报**的 required context（PR 永久 “Expected — waiting for status”）。
3. `ci.yml:373` + `:380-384` posture 注释块 → 改写为翻转后陈述（含窗口、streak、账本路径、
   Owner 执行记录指针）。
4. `sdd/gates.md:66` `docker-image-build` 行 posture → `blocking@ci`；`:127` 的 v0.3 dated
   脚注**不回改**（历史记录）。
5. `docker/CLAUDE.md:88` / `:93` posture 表述 → 同步（**#385 的 Scope/AC 现未覆盖此文件，须补**）。
   `docker/CLAUDE.md:94` 的 Registry 指针**不动**。
   > **行号更正（2026-08-06 翻转时实测，#385）**：本条原写 `:80` / `:85` / `:86` —— 那是本工件
   > 注册时（2026-08-04）的行号。#413/PR#415 `9eb9183` 向 `docker/CLAUDE.md` 前部加了内容，
   > 三处各**下移 8 行**。行号型指针会随无关改动腐化，复核时以内容锚为准。
   > 同理 `docker/CLAUDE.md:65`「该面无 `permissions.ask` 条目、**无审批类 CI gate**」一句
   > **不改** —— 它陈述的是 `docker/Dockerfile` 外部 registry 镜像引用面的审批载体；
   > `docker-build` 即便翻为 blocking 也仍只验「镜像可构建」、不判 Owner 拍板，故该句翻转后依然成立。
6. 产出 `evidence/ai-context-audit/2026-08_ci_audit.md`（violation 数 + 影响范围 + 分列
   「真实执行绿 / 未触发」两计数 + §5.2 披露 + 无关 job 失败登记）。
7. 勾选 `.github/PULL_REQUEST_TEMPLATE.md` 的 `ci-blocking-gate-toggle` 项，指向 #385 的
   Owner 执行记录 comment。

## 7 已知边界（翻转**不**改变的事实）

- **本 gate 不在 required status checks 内**。`protect-develop`(15606888) / `protect-main`(15606891)
  各只要求 `[{"context":"ci"}]`；`docker-build` 是**独立 job**，非 `ci` job 内的 step
  —— 故 #399（V8/V9/V10 = `ci` job 内 step）的先例**不平移**。翻转后该 gate 会**红**且会令
  `/mj-agent-git-check-merge` 判 “Not Ready to Merge ❌”（该 skill 不按 `isRequired` 过滤），
  但**不**机械锁死 GitHub merge 按钮。是否加入 required contexts = **可选硬化**，非翻转前置。
- 两个 ruleset 均带 `bypass_actors: [RepositoryRole 5, always]`，故「机械锁死」对 Owner 本就不成立
  —— 该标准对本仓任何 gate（含已 blocking 的 V8/V9/V10）都不成立。
- **fail-open SHA 的掩蔽**：`/mj-agent-git-check-merge` 按 check name 去重取 `startedAt` **最晚**。
  fail-open 类 SHA 上 push run 构建、PR run skip 且**更晚**开始 → 绿 skip 会**盖住**红构建。
  受影响面 = 窗口内 19 次真实构建中的 8 次（fail-open 类）。根治法 = 把本 job 收窄为仅
  `pull_request` 触发（属 trigger 逻辑，#385 明列 out-of-scope，需独立 scope 决定）。

## 8 Risk Control

- **Risk level**：Low（本工件为**纯注册**，不改 gate posture、不改 `ci.yml`）
- **HITL gates**：本工件自身无必停；其**消费者** #385 的翻转动作 = `ci-blocking-gate-toggle` 必停
- **缓解**：注册项与实测快照分离（§2 / §4），并显式声明 §4 **不**充当资格证明，避免快照过期后
  被误当依据

## 9 Verification

```bash
./.venv/Scripts/python.exe scripts/check_frontmatter.py
MJ_AGENT_A4_STRICT=1 ./.venv/Scripts/python.exe scripts/check_wikilinks.py
./.venv/Scripts/python.exe scripts/check_ai_context_audit.py
./.venv/Scripts/python.exe -m pytest tests/unit -q
grep -rn "docker-build\|docker-image-build" plans/     # 期望：有命中（注册生效）
```

- [ ] 本工件存在且 `grep plans/` 有命中 → §4.1.1 注册要件满足
- [ ] `policies/ai-agent.md:98`「M-FU plan 必先 register」前置满足
- [ ] 全 diff 不含 `.github/workflows/**`，无 `continue-on-error` 字样

## 10 闭合条件

`state: active` → `completed` 的条件 = **#385 翻转落地**（或 Owner 明示放弃翻转）。
闭合时补 `completed:` 字段，并在此处记录：实际翻转日期 / 最终 streak 计数 / 账本路径 /
Owner 执行记录 comment 链接。

### 10.1 闭合记录（2026-08-06）

**条件已满足 —— #385 翻转已落地，本工件闭合。**

| 项 | 值 |
|---|---|
| 实际翻转日期 | **2026-08-06**（执行时刻 02:50Z） |
| 落地 PR | [#434](https://github.com/MJ-AgentLab/mj-agent/pull/434)，merge commit `fd881ac`（2026-08-06T03:18:58Z） |
| 执行 issue | [#385](https://github.com/MJ-AgentLab/mj-agent/issues/385) —— 已 CLOSED-COMPLETED |
| 最终 streak 计数 | **33**（阈值 20，余量 +13）；violation **0** / streak 重置 **0** / 零 waiver |
| 计数明细 | 窗口 61 run → 35 distinct head-SHA → clean 33 / violation 0 / 中性 1（`1964db4`）/ 剔除 1（`1ac2118`） |
| 账本路径 | `evidence/ai-context-audit/2026-08_ci_audit.md` |
| Owner 执行记录 | https://github.com/MJ-AgentLab/mj-agent/issues/385#issuecomment-5199940202 |

**日历腿读法（如实留痕）**：翻转执行于 2026-08-06T02:50Z，**早于严读（14×24h）门槛
2026-08-06T07:55:16Z 约 5h05m**。Owner 2026-07-24 曾拍板取严读；**2026-08-06 改判改采
§5.1 字面的日期算术读法（`2026-07-23 + 14 天 = 2026-08-06`）并授权即时翻转**。
账本 §1 与执行记录 comment 均已明载，**未**宣称两种读法都满足。

**§9 Verification 勾项的最终状态**：三项均已满足 —— 本工件存在且 `grep plans/` 有命中；
`policies/ai-agent.md:98`「M-FU plan 必先 register」前置满足；注册 PR（#403/#404）自身的 diff
不含 `.github/workflows/**`。（**注**：末项约束的是**注册 PR**，不是翻转 PR —— 翻转 PR #434
当然改 `ci.yml`，那正是它的目的。）

**§4 快照与 §5.1「现状」列的时效说明**：二者是 **2026-08-04 注册时**的基线（16/20、12/14），
按 §4 抬头「实测勿外推」**不**充当资格证明；正式资格依据 = 上表的 flip-time 实测（33/20）
与账本。此处不回改历史快照数字。
