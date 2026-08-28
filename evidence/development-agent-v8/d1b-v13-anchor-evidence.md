---
type: evidence
summary: >-
  Epic #499 PR-D1b V13 anchor registration —— 把 V13 "Codex Enforcement Drift"
  的 `policies/ci-gates.md` §4.1.1 五要素注册落到真值载体：**CI 首挂锚
  `c485f8d` 2026-08-28 13:49:48 +0900**（§4.1.2 run-命令 pickaxe；⚠ 片段取
  **全命令**而非脚本路径 —— `agents_sync.py` 按 `--surface` 承载 V10/V11/V13，
  脚本路径 pickaxe 得 3 个 commit、会把锚提前 45 天），**epoch 起点 = 该 commit
  上的首次真实 CI** run `33144504658`（event=push，`05:21:16Z`；V13 step job
  `98762485194` `05:21:57Z`→`05:21:58Z`，输出 `EXECUTED_CLEAN`）。同 head SHA 的
  run `33146015449`（pull_request）输出**逐字节相同** → 去重后合计 **1 次观测**，
  且该次是 **epoch 标记而非计数腿的观测 #1**（计数腿按 plan §5.10 自 PR-D1b merge
  之后起算；2026-08-28 实测可计数 streak = **0**）。⚠ 实测 **merge commit `56188fa`
  触发 0 次 run**，故 anchor 只能取 PR head run。⚠ **V13 与 V12 三处不同型**：
  pickaxe 片段、双起点资格公式、以及 **5 个字面 token / 4 个登记组**且 **drift
  优先于 skip 分类**（V12 相反）。本单元**零 behavior diff**：不改 `ci.yml` /
  `agents_sync.py` / 任何测试 / 任何生成产物，diff 仅含 `plans/` + `sdd/gates.md`
  + `policies/ci-gates.md` + 本文件四处**登记与证据**。分析与实测由 Claude Code
  执行、值由 Owner 拍板。
owner: ranzuozhou
created: 2026-08-28
updated: 2026-08-28
state: active
track: agent
---

# V13 Anchor Registration — Epic #499 (PR-D1b)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.9（V13 registration field 表）
> 与 §5.10（observation / PR-D2）。Delivery unit = **PR-D1b**，AC = **AC-11**，
> merge condition = **anchor reproducible + zero behavior diff**（§5.1 row 14）。
> approval = **exact anchor-value approval**；rollback = **anchor-only correction PR**
> （§5.1.1）。§3.3 把本单元的 owned surface 界定为 **"V13 anchor registration only"**。

## 0. 入场锚点与 Owner 拍板记录

| 项 | 实测值 |
|---|---|
| 前序单元 PR-D1a | #519 **MERGED**，head `c485f8d42bb7684bd9918bddd5eaf4388c63a9a3`（**1 commit**，17 文件），merge `56188fa31e3b3bdffcf92aef1e2a106bd797c111`，`2026-08-28T05:57:26Z`（ranzuozhou，admin bypass） |
| develop 三方 | local = origin = gitee = `56188fa31e3b3bdffcf92aef1e2a106bd797c111` |
| D1a Stage 17 ledger | `#499#issuecomment-5449077209`，body **27580 B**、纯 LF（`'\r\n' not in body` 实测）、SHA-256 `2cc37a249ce4dd89b01a858bee4a595c0a0ce61965ca8db71403b47d1ac9222b` **逐字节复算吻合**（口径 = API `body` 去尾换行）；18 records 全终态；反引号 311 |
| Task-0 preflight | `CONTROLLED_SURFACE_CHANGED` / **rc 1**，identity `3bb781e2b184cfff3d8f34c6403fdd14da825c7854f981257be832a577aa0fac`，hard-frozen **58 零 diff** —— D1a 用掉 §1.1 最后一个授权 hunk 后的**预期授权态**；本单元不碰 `AGENTS.md`，故 identity 全程不变 |
| 工作树 EOL | 三个被改文件均 `i/lf w/crlf attr/text=auto`（index 侧恒 LF）；新建 evidence 文件 `git check-attr` 得 `text: auto`，同 6 个同族 evidence 文件 —— **无需 `.gitattributes` 动作** |
| 其他 | #499 / #504 均 OPEN；无 open PR；worktree 数 2 → 建分支后 3 |

**Gate 1（四问一次呈清，Owner 全取推荐项）**：

| # | 问题 | 拍板 |
|---|---|---|
| Q1 | F17（V12+V13 注册表 re-home）是否在本单元并做 | **推迟到 OBSERVATION 窗口内的独立单元**；本单元只做交接（§10.1） |
| Q2 | `policies/ci-gates.md` 修复范围 | **`:310` 范围串 + `:317` M2 arity 两处**；有意不碰 `:46` / `:51-52` / `:236` / §6.2（§4.2 给出判据） |
| Q3 | §5.8 与 `sdd/gates.md` V12 行那句「日历腿到期时注册表已在闭合记录中」经查为假 | **本单元不改它**（既存缺陷、且属 V12 的活体注册面）；§5.9 声明段不克隆该措辞，更正列入 F17 |
| Q4 | 「PR-D2 挂载 byte-identical predicate」与 D1a 留给 D2 的「恢复 bare `--check`」冲突 | **按 §5.10 登记**；不动 blocking route 行 / AC-11 / ADR-039，冲突作为 D2 的 follow-up（§10.2） |

## 1. 交付面（Gate 1 批准的 exact scope）

**4 个 markdown 文件，零可执行文件**：

1. `plans/[PLAN]_codex_cross_carrier_kernel.md` —— §5.9 表 6 个 cell 填实测值 + 新增注册载体声明段 + frontmatter `updated`。
   **有意未动的 2 个 cell**：`Exact execution`（已与 `ci.yml` 逐字节相等，见 §2.5）与 `blocking route`（PR-0a 的设计行，非 anchor 值）。这与 PR-C2 对 V12 的处置**同构** —— C2 亦改 6 行、留 `Exact execution` 与 `v8 disposition` 逐字未动。
2. `sdd/gates.md` —— §2 新增 `V13 Codex-Enforcement-Drift` 行（插在 V12 与 `docker-bdd-scenario-check` 之间）+ **升版三件套**（`version "0.13"→"0.14"` / `updated 2026-08-27→2026-08-28` / changelog 顶部新增 v0.14 条目）。
3. `policies/ci-gates.md` —— 两行（§4.2）。
4. `evidence/development-agent-v8/d1b-v13-anchor-evidence.md` —— 本文件（新建）。

**不入任何 INDEX**：全仓 9 个 `INDEX.md` 中**没有任何一个** evidence 文件被登记（`c0` / `c2` / `d1a` / `p1a` / `p1b` / `task0-baseline` 逐个复核，零命中）；`docs/INDEX.md` 只登记 ASSESSMENT 体裁的 `evidence/assessments/`。
取而代之的是 **PR-C2 实际使用的两处指针尾**：plan §5.9 的 Observation anchor cell 与 `sdd/gates.md` V13 行末尾各挂一条 `原始实测值 → evidence/development-agent-v8/d1b-v13-anchor-evidence.md`（已落）。

## 2. Anchor 实测值（原始证据）

### 2.1 CI 首挂锚（§4.1.2）+ **pickaxe 片段选择的判据**

```bash
git log --oneline --reverse -S "agents_sync.py --check --surface enforcement" -- .github/workflows/ci.yml
# → c485f8d feat: render Codex enforcement carrier and mount V13      （单一命中）
git log -1 --format='%H %aI' c485f8d
# → c485f8d42bb7684bd9918bddd5eaf4388c63a9a3 2026-08-28T13:49:48+09:00
```

⚠ **V12 的片段形状不能照搬。** §4.1.2 只规定「用**该 gate 的 run 命令片段**做 pickaxe，不用 step 名」；
它是参数化的，并未规定必须用脚本路径。V12 用脚本路径能成立是巧合（`check_cross_carrier.py` 只挂一次），
V13 不成立。**逐候选实测**（`grep -o … | wc -l` 数**出现次数**，不是 `grep -c` 的**命中行数**）：

| 候选片段 | 在 `ci.yml` 的出现次数 | pickaxe 命中 commit | 判定 |
|---|---:|---|---|
| `scripts/sdd/agents_sync.py` | **3**（`:362` / `:365` / `:426`） | **3** —— `36d185d`(V10 #326) / `b8f43d3`(V11 #330) / `c485f8d`(V13) | ❌ 会把锚定到 2026-07-14，**提前 45 天** |
| `agents_sync.py`（裸文件名） | **5**（另含注释行 `:332` / `:347`） | **3** —— 同上 | ❌ 同上 |
| `--surface enforcement` | **2**（`:408` 注释行 + `:426` run 行）| 1 —— `c485f8d` | ⚠ 今日正确，但注释改写即扰动出现次数、可能新增命中，「单一命中」断言会诱发性 stale |
| `agents_sync.py --check --surface enforcement` | **1**（仅 run 行）| 1 —— `c485f8d` | ✅ **采用** |

**正确的选择判据是「该片段在 `ci.yml` 内的出现次数历史是否隔离本 gate」，不是「执行体是否唯一挂载」** ——
`git log -S` 对出现次数的**任何**变化（含纯计数增减）都会触发。反例实证：

```bash
git log --oneline --reverse -S "--check --surface" -- .github/workflows/ci.yml
# → b8f43d3   （0 → 2 次）
# → c485f8d   （2 → 3 次）      ← 纯计数增加也会命中
```

`agents_sync.py` 承载多 gate 这一事实本就是 kernel 明文（`policies/ci-gates.md` §6.1 M2）；本单元把该条
从 "V10 + V11" 更正为 "V10 + V11 + V13"（§4.2）。

### 2.2 首次真实 CI（epoch 起点）

`c485f8d` 上的全部 `ci.yml` run（`gh api .../actions/workflows/ci.yml/runs?head_sha=…`，`total_count = 2`）：

| run id | event | `run_started_at` | conclusion | V13 step job | V13 step 起止 |
|---|---|---|---|---|---|
| `33144504658` | **push** | `2026-08-28T05:21:16Z` | success | `98762485194` | `05:21:57Z` → `05:21:58Z` |
| `33146015449` | pull_request | `2026-08-28T05:51:07Z` | success | `98767116571` | `05:51:40Z` → `05:51:40Z` |

**epoch 起点 = push run `33144504658`**（早于 PR run）。

⚠ **step 序号有两个口径，差 1**：Actions API / 日志里 V13 是 **step 43**（该列表以隐式的 `Set up job`
为 step 1）；而对 `.github/workflows/ci.yml` 做 `yaml.safe_load` 后，`jobs.ci.steps` 共 45 项、V13 是
**第 42 个 authored step**（V12 为第 41 个）。两个口径都对，但**引用时必须写明是哪一个**，且任何插入的
step 都会推移它 —— 本注册表用它只为说明「V13 排在多个 blocking 步之后」，该结论不依赖具体序号。

⚠ **push↔PR 的间隔不是固定值**：本次 **1791 秒（29.9 分钟）**（= Owner 的 push / PR-create 批准窗口），
C2 实测 **49 秒**。⚠ PR-D1a 的交接口径把 C2 那次转述为「约 45 秒」—— 那是四舍五入而非实测值；本单元按
两条 run 的 `run_started_at` 重算得 49 秒。稳定的只有**顺序**（push 先），间隔不是不变式。

### 2.3 两次执行的输出（逐字节相同 →「anchor reproducible」）

两个 job 的 V13 step stdout（从 `actions/jobs/<id>/logs` 取，去掉行首时间戳后）：

```text
OK: projection in sync (surface=enforcement, 18 skills, lock consistent)
EXECUTED_CLEAN
```

两次**完全相同** → 按 §4.1.3 head-SHA 去重口径合计 **1 次观测**。

⚠ `OK:` 行里的 **`18 skills` 是 project-set 的技能总数，与 enforcement 面无关** —— 它由通用的
`OK: projection in sync (surface=…, N skills, …)` 模板打印，三个 surface 共用同一句。不要把它读成
「enforcement 面有 18 个成员」。

⚠ **V12 与 V13 在同一个 `ci` job 的日志里相隔约 1 秒先后打印**（V12 `05:21:57Z` / V13 `05:21:58Z`），
且**五个 token 里有四个与 V12 共用字面量**（只有 `SKIP_NO_ENFORCEMENT_SOURCE` 是 V13 独有）。
未来的 streak 度量**必须按 step 切分日志**；对整个 job log 做 grep 会把 V12 的输出计成 V13 的。

### 2.4 merge commit 不触发 CI（决定 anchor 只能取 PR head run）

```bash
gh api "repos/MJ-AgentLab/mj-agent/actions/runs?head_sha=56188fa31e3b3bdffcf92aef1e2a106bd797c111" --jq '.total_count'
# → 0        （全 workflow，不只 ci.yml）
```

成因结构性未变：`ci.yml` 的 push 过滤器只含 5 类临时分支前缀（不含 `develop`），`pull_request` 只对
base 为 main/develop 的 PR 触发。

⚠ **计数口径**：本 Epic 至今共 **3 个 merge commit**（`d810746` C1 / `70a9db4` C2 / `56188fa` D1a），
**三者全部实测为 0 次 run**。PR-D1a 的 ledger 已就 `56188fa` 记过一次，**本单元是对同一实例的独立复测，
不是第 4 个实例** —— 初稿曾写「第 4 次独立实证，前三次为 `d810746` / `70a9db4` / `56188fa` 自身」，
该表述把同一个 commit 同时列为「前三次之一」和「本次」，自相矛盾，现予更正。

### 2.5 实际 run 命令 vs plan 声明（AC-11 的核心）

AC-11 原文（plan **§7.1 Program-level AC**；**刻意不写行号** —— 本 PR 自身的 §5.9 编辑就会推移它，
行号锚是无 gate 可查的诱发性 stale）：「V12/V13 records **name actual command/path**；D2 predicate
equals observed predicate byte-for-byte」。程序化复核：

```text
ci.yml:426  (actual)   uv run python scripts/sdd/agents_sync.py --check --surface enforcement
plan §5.9   (declared) uv run python scripts/sdd/agents_sync.py --check --surface enforcement
BYTE-EQUAL: True   len = 70   sha256 = 6c37a7309dee0e61f6b3b9f5cdc44c7d0381eca9ec9e6f069bab95a23abf5841
```

plan §5.10 的复述句与二者同串。**故 `Exact execution` cell 无需改动**，本单元只是把这一相等性**证明**下来。

⚠ **V12 的 `--status-json` 路径注记不适用于 V13**：V13 的执行体不写任何 status 文件，无 `.mj-agent-local/` 产物。

### 2.6 streak 状态（**时点测量**）

```bash
gh api "repos/MJ-AgentLab/mj-agent/actions/workflows/ci.yml/runs?per_page=8" --jq '.workflow_runs[] | "\(.id) \(.event) \(.head_branch) \(.run_started_at)"'
# 最新两条即 c485f8d 上的那两次；此后 ci.yml 无任何 run
```

**实测于 2026-08-28（PR-D1b 登记时刻）**：自 anchor 起 `ci.yml` **零次新 run**。按 §5.10「计数腿自
PR-D1b merge 之后起算」，**当时可计数 streak = 0**；那 1 次去重观测是 **epoch 标记**，不是计数腿的观测 #1。
⚠ 这是**时点测量**、随后必然增长 —— 引用时须连同其测量时点一并引用，不得当作恒定值。

## 3. 五要素注册对位（`policies/ci-gates.md` §4.1.1）

| §4.1.1 注册项 | V13 值 | 载体 |
|---|---|---|
| gate 标识 | `V13 Codex-Enforcement-Drift`（gates.md 行名）↔ ci.yml step 名 `V13 codex enforcement drift (WARNING per plan §5.9)` ↔ plan §5.9 表 | gates.md §2 行 + plan §5.9 |
| CI 首挂锚 | `c485f8d` 2026-08-28 13:49:48 +0900 #499（判据 = 全命令 pickaxe，见 §2.1）| plan §5.9 + gates.md 行 |
| 适用口径 | 非 path-triggered → **§4.1.3**（head-SHA 去重）；**不**适用 §4.1.4 三态 | plan §5.9 + gates.md 行 |
| 阈值 + 资格公式 | **两腿 AND，且两腿起点不同**：日历腿 = 锚 + ≥14 自然日 → 最早 **2026-09-11**；计数腿 = ≥20 连续去重 `EXECUTED_CLEAN`，**自 PR-D1b merge 之后**起算 | plan §5.9 + §5.10 |
| 自排除规则 | PR-D1a mount / PR-D1b anchor / PR-D2 toggle；且 §4.1.3 末条（翻转 PR 自身分支 run 不计入自身资格，计数锚在翻转分支前一 commit）**已明写** | plan §5.9 + gates.md 行 |

**为什么载体是 plan 而不是 `policies/ci-gates.md`**：该文件自述「本文件是规则 + 指针层，**不复制姿态真值**
（逐 gate 真值列在 `sdd/gates.md` §1-§3）」，实测其中不存在任何一个 gate 的 anchor / 适用口径 / 资格公式 /
自排除值 —— 它是 schema 而非 instance。§4.1.1 要求「构成要件 = **事先在 `plans/` 注册**」，本 plan
（created 2026-08-12）早于首挂（2026-08-28），满足「事先」。

**本行登记 ≠ posture 翻转**（#444 判例）：`continue-on-error: true` 与 run 命令逐字未动 → **不需**
`ci-blocking-gate-toggle` 拍板。

### 3.1 gates.md 行名的连字符是**必需**，不是风格

`policies/ci-gates.md` §6.1 公布的「可复跑推导」左侧命令是：

```bash
grep -oE '^\| (G[0-9]+|V[0-9]+ [A-Za-z-]+|[a-z][a-z0-9-]+) \| `?[^|]*\.py' sdd/gates.md
```

V 分支是 `V[0-9]+ [A-Za-z-]+` —— 数字后只允许**一个**字母/连字符 token。

⚠ **负测试必须带上「其余各行仍命中」这个前提，否则结论说不通**：单独把空格形写进一个只有它一行的
文件时，grep 选不中任何行、**退出码是 1**（初稿写成「零输出且仍 exit 0」，两者不可能同时成立，现予更正）。
真正要证明的是**在真实表里**的行为 —— 把空格形放进含其他 V 行的表中：

```text
输入两行：  | V13 Codex Enforcement Drift | `…agents_sync.py …` | x |
            | V13 Codex-Enforcement-Drift | `…agents_sync.py …` | x |
输出一行：  | V13 Codex-Enforcement-Drift | `scripts/sdd/agents_sync.py
退出码：    0
```

即：**其他行仍命中 ⇒ grep 照常 exit 0，而 V13 行被静默漏掉** —— fail-open 漏行，不是报错。
落盘后在真实文件上复跑，与 develop 基线逐行 diff，唯一差异就是新增的 V13 行（§6）。

⚠ **该命名约束没有任何执行体**：全仓无脚本 / workflow / 测试读取 `sdd/gates.md` 的行名（`V[0-9]+`
在 `*.md` 之外零命中），仅靠本注记与合并审查兜底。

## 4. 「零 behavior diff」的自证

合并条件之一是 **zero behavior diff**。本单元把它做成**可由 diff 本身检验**的性质：

1. **diff 不含任何可执行文件**：改动集恰为 `plans/*.md` + `sdd/gates.md` + `policies/ci-gates.md`
   + `evidence/**.md` **四个 markdown 面**；无 `.py`、无 `.yml`、无 `tests/`、无生成产物。
2. **无测试新增/修改** —— 因此没有「用测试把 warning gate 从后门变成实质 blocking」的风险。
   这条对 V13 **格外要紧**：`Tests` 步是 blocking，而 PR-D1a 正是因为 real-tree 钉线裸跑 `--check`
   （surface=all）而不得不把它收窄到 `skills`+`mcp`（F20）。**本单元不得恢复它** —— 那是 PR-D2
   的事，且其本身即 blocking 扩面，须携带独立 `ci-blocking-gate-toggle` 记录。
3. **gate 姿态位不变**：`ci.yml` 中 V13 的 `continue-on-error: true` 逐字未动 → 仍是 `warning@ci`。
4. **gate 标识未变** → §4.1.2 的 pickaxe 判据与 step 名双双稳定，观测 epoch 在登记时刻**无接缝**。
5. **task0 identity 不变**：`3bb781e2…`，hard-frozen 58 零 diff；`evidence/` 只是 surface 分类标签，
   不在 `HARD_FROZEN_*` / `CONTROLLED_FROZEN_*` 任一集合内，故新建 evidence 文件对 identity 摘要零贡献。
   ⚠ 口径注记：`task0_freeze.py --check` 读的是 **HEAD**，不是工作树 —— 本项在 commit 后复验（§6）。

### 4.1 「markdown-only ⇒ 零 behavior diff」**并不自动成立** —— 三个 policy_ref 是反例

`sdd/adapters/codex-enforcement.yml` 声明：

```yaml
policy_refs:
  - AGENTS.md
  - policies/ai-agent.md
  - policies/git-branching.md
```

同文件注释自述：「The renderer hashes each file's raw bytes into `policy_refs_sha256`, which is a
required lock input on every codex-hook / codex-rule entry -- so editing any file below is a
re-render trigger.」故**编辑这三个纯 markdown 文件中的任何一个**都会：

- 若**不**重跑 `sync` → `--check --surface enforcement` 报 drift → **V13 在登记自己 anchor 的那个 PR 上打
  `EXECUTED_WITH_FINDINGS`，亲手重置它正在注册的 epoch**；
- 若**重跑** `sync` → `.codex/hooks.json` + `.codex/rules/mj-agent.rules` + `.agents.lock.json` 三个生成
  产物进 diff → 直接违反零 behavior diff。

`AGENTS.md` 另有一道独立的门：plan §1.1 只授权两个 controlled-freeze hunk（PR-C1 carrier ownership +
PR-D1a hooks/rules cooperative scope），**两者均已用尽**，此后任何编辑都是 Task-0 漂移。

**本单元四个交付文件均不在 `policy_refs[]` 内**（逐项比对确认），故计划的交付面安全。
顺带登记一处**不在本单元处置范围**的观察：`AGENTS.md` 的 "Drift gates:" 条目枚举了 V9 / `--surface skills`
/ `--surface mcp` 而**未含 V13** —— 修它需要一个手上已有授权 `AGENTS.md` hunk 的单元，本单元没有。

### 4.2 `policies/ci-gates.md` 的两处改动，与**有意不改**的四处

**改（2 处）**：

| 位置 | 改动 | 性质 |
|---|---|---|
| §6 开篇 | `V1-V12`（#499 PR-C2 起含 V12）→ `V1-V13`（#499 PR-C2 起含 V12、PR-D1b 起含 V13）| 该范围跟踪的是「进入 `sdd/gates.md` §2 的成员」，**归注册单元**。判据（D1a 治理事实 4）：`git log -S "V1-V12" -- policies/ci-gates.md` 只有 `e63f19c`（= PR-C2，注册单元），而 PR-C1（V12 的 mount 单元）未碰 `policies/` 任何文件。⚠ **范围串与其后的括注一起改** —— C2 的先例正是两者同改；只换范围串会留下一句只解释 V12 的半截话 |
| §6.1 M2 | `agents_sync.py` → V10 + V11 → **V10 + V11 + V13** | **本 PR 诱发的假 arity 陈述**：V13 行一进 `sdd/gates.md` §2，该括注即为假。按「诱发性 stale 在成因 PR 内修」处理 |

**有意不改（4 处，逐条给判据）** —— 记录在此以便评审看到这是推理过的省略，而非遗漏：

| 位置 | 内容 | 不改的理由 |
|---|---|---|
| §1.1 `:46` | step 级 `continue-on-error` 成员名单，缺 V12 **和** V13 | **不完整的举例清单**，非被证伪的断言。V12 当年也未被 PR-C2 补入；本 PR 并不使其为假。属**既存**缺陷，另立单 |
| §1.1 `:51-52` | 「无阈值轴」名单，缺 V12 **和** V13 | 同上。（`agents_sync.py` 确无 `--fail-on`，V13 也确实无阈值轴）|
| §4.1.4 `:236` | 「§4.1.3 成文时面对的 gate（V8/V9/V10）」 | **定格的历史陈述**（描述该节写作时的情形），改它才是造假 |
| §6.2 | 「6 个 CI 执行体没有 gate 行（实测 `f29f501`）」 | 定格快照，且 `agents_sync.py` 本就已有 gate 行，V13 不改变该差集 |

判据的分界线是：**「被证伪的 arity 断言」修，「不完整的举例清单 / 定格快照」不修。**

## 5. result_code：按**执行体源**登记（5 个 token / 4 个登记组）

D1a 交接口径称 V13 为「四态」。**按状态类计是对的，按 token 枚举是不足的** —— 执行体
`scripts/sdd/agents_sync.py` 定义 **5 个字面 token**：

```python
RESULT_EXECUTED_CLEAN = "EXECUTED_CLEAN"
RESULT_EXECUTED_WITH_FINDINGS = "EXECUTED_WITH_FINDINGS"
RESULT_ERROR_UNREADABLE = "ERROR_UNREADABLE"
RESULT_SKIP_MANIFEST_V1 = "SKIP_MANIFEST_V1"
RESULT_SKIP_NO_ENFORCEMENT_SOURCE = "SKIP_NO_ENFORCEMENT_SOURCE"
```

`SKIP_NO_ENFORCEMENT_SOURCE` **是 V13 独有的**（V12 的执行体 `check_cross_carrier.py` 只有四个，
`sdd/gates.md` 的 V12 行登记的也是四个）。一个只匹配四个字面量的 streak 度量脚本会把它静默判成
「无 token」—— 正是 §4.1.4 要防的空绿失效模式。

| token | rc | streak 作用 | 触发条件（源码语义，实测） |
|---|---:|---|---|
| `EXECUTED_CLEAN` | 0 | **计 1** | 无 drift，且 manifest v2 + typed source 是常规文件 |
| `SKIP_MANIFEST_V1` | 0 | 中性 | **仅** `schema_version == 1` **且 lock 与之相容**时可达 |
| `SKIP_NO_ENFORCEMENT_SOURCE` | 0 | 中性 | typed source **不是常规文件**（缺失、或被替换成目录）|
| `EXECUTED_WITH_FINDINGS` | 1 | **重置** | 检出 drift；**以及 lock 的任何故障态**（见下） |
| `ERROR_UNREADABLE` | 2 | **重置** | manifest 加载失败（缺失 / YAML 错误 / 未知 `schema_version`）· typed source **存在但不可解析** · 任一 `policy_ref` 不可读 · workflow registry 缺失 · desired-state 渲染所需的任一其他输入缺失（translation map / preface / `.mcp.json` / 任一 skills 投影源）|

必须随注册一起登记的边界：

1. **前三个 token 同为 rc 0**，且 step 带 `continue-on-error: true` → **run/step conclusion 不可作判据**，
   只能读 stdout。执行体源码注释自己就写着「PR-D1b must read THIS stdout token」。
2. **⚠ `lock` 不属于 `ERROR_UNREADABLE`。** 实测：lock 的**每一种**故障态 —— 缺失、JSON 格式错误、
   被替换成目录、v1 扁平映射、`schema_version` 不符、重复键、BOM、条目摘要不符 —— **一律**产出
   `EXECUTED_WITH_FINDINGS` + **rc 1**，而非 `ERROR_UNREADABLE` + rc 2。成因是 lock 的校验错误在
   scoped 路径上被吸收成一条 drift 字符串。**两者同为「重置」，故 streak 算术不受影响；但诊断指向相反** ——
   初稿在 `sdd/gates.md` 与本表把 `lock` 写进 rc 2 一档，若 PR-D2 据此写一条「lock 故障 ⇒ rc 2」的
   负向测试会直接变红。现予更正。
3. **优先级与 V12 相反。** V12 先判 manifest 版本再判 findings（SKIP 抢占）；V13 **先判 drift，再判 skip
   分类**。后果：在 v1-manifest 的树上一旦有 drift，V13 打 `EXECUTED_WITH_FINDINGS`（**重置**）而 V12 会
   打中性 SKIP。**§5.8 的该段不能逐字复用到 §5.9。**
4. **`ERROR_UNREADABLE` 可由 enforcement 面之外的故障触发。** desired-state 无条件渲染全部 surface，
   故一次 **skills 面**的投影源缺失就会让 V13 打 rc 2 并重置 epoch。
5. **第六种结局 = 无 token，且其成因列表是下界而非穷举。** 至少含：未捕获异常（如 manifest / lock 为
   **非 UTF-8 字节**引发的 `UnicodeDecodeError`，traceback + rc 1，被 `continue-on-error` **抹绿**）·
   参数用法错误（rc 2，在打出 token 前即返回）· 本步因**更早的 blocking 步失败而未执行** · job 取消或超时。
   **无 token 的 run 一律不是可计数观测，须调查**，不得按「没打印就是没事」计入。
   ⚠ 其中**被抹绿**的那几类才真正危险；「更早的步失败」那一类**job 本身是红的**，自带信号。
6. **⚠ 两个粒度别混：`check` 与 `step`。** `ci` **check run** 因无 path 过滤器而永不 `skipped`，故本 gate
   **不**适用 §4.1.4 的三态口径；但本 gate 的 **step** 在更早 blocking 步失败时**确实会拿到
   `conclusion: skipped`**（实测先例：run `31773569400` / job `94684255167`，step 42 failure 之后 43/44
   均为 `skipped`）。**该 `skipped` step 不是 §4.1.4 的中性桶，而是上面第 5 条的「无 token」结局 —— 须调查，
   不得当作中性吸收。** 初稿把这一句压缩成「本 gate 永不产生 `skipped`」，丢掉了 `check` 这个限定词，现予更正。

### 5.1 姿态事实：**无 blocking 兜底的是两个维度，不是整个 gate**

初稿写「V13 没有任何 blocking 兜底」，**经实测证伪，现予更正**。准确的分维度表述：

| 维度 | 有无 blocking 兜底 | 依据（实测） |
|---|---|---|
| artifact ↔ desired-render 的**内容漂移** | **无** | V9 从不读取 `.codex/hooks.json` / `.codex/rules/*.rules` 的**内容**；无任何测试对这两个产物做真实树钉线 |
| **输入 digest 闭合**（`policy_refs_sha256` / `renderer_module_sha256` 等）| **无** | 同上；纯 digest 篡改时 V13 rc 1 而 V9 rc 0 全绿 |
| 已存在 lock 条目的 **schema**（`entry_kind` / `owner` / `strategy` / `normalization_policy` / `inputs` 键集 / `output_sha256` 格式）| **有，两重** | V9 的 **PJ031**（整锁 `verify_lock_v2`，error 级，`--fail-on warning` 下 blocking）+ blocking `Tests` 步内 `tests/unit/test_v2_engine.py` 的真实树 `verify_lock_v2` |
| lock 条目**被整条删除** | **无** | 两个载体都只做正向断言，不要求 enforcement 条目必须存在 |
| typed source **被删除或不可解析** | **有** | `tests/unit/test_codex_enforcement_d1a.py` 在**模块层**加载真实的 `sdd/adapters/codex-enforcement.yml` —— 缺失即 collection error、不可解析即抛错，blocking `Tests` 步直接变红 |

故与 §5.8 为 V12 的 X07 登记的情形相比，正确表述是「**V13 的未覆盖维度不同且更窄**」，
而不是「V13 完全无兜底」。

⚠ 另更正一处口径：PR-D1a 收窄的 real-tree 钉线是**一处**调用点（原本裸跑 `--check`），
同组另一处**本来就是** mcp-scoped。**F20 要恢复的是那一处**，不是两处。

⚠ `SKIP_NO_ENFORCEMENT_SOURCE` 的危害比「streak 停滞」更大：typed source 一旦不是常规文件，执行体
仍**逐字打印** `OK: … lock consistent` 并 rc 0，而两个产物**及其 lock 条目从此不被任何 CI 面校验**。

## 6. 验证结果

全部在 `maintain/499-v13-anchor` 工作树、改动落盘后执行（fresh evidence，非改前快照）。

| 检查 | 命令口径 | 结果 |
|---|---|---|
| V8 | `check_development_agent.py --all --fail-on warning` | rc 0 · **0E / 0W / 0info** |
| V9 | `check_agents_projection.py --all --fail-on warning` | rc 0 · **0E / 0W / 0info** |
| V10 | `agents_sync.py --check --surface skills` | rc 0 · `OK: projection in sync` |
| V11 | `agents_sync.py --check --surface mcp` | rc 0 · `OK: projection in sync` |
| V12 | `check_cross_carrier.py --status-json …` | rc 0 · **7 PASS / 0W / 0E** · `EXECUTED_CLEAN` |
| **V13** | `agents_sync.py --check --surface enforcement` | rc 0 · `OK` · **`EXECUTED_CLEAN`** |
| A2/A3 frontmatter | `check_frontmatter.py` | rc 0 · **138 canonical docs 全过**（⚠ 覆盖面注记见 §6.2）|
| A4 wikilinks | `check_wikilinks.py` | rc 0 · **0 unresolved** |
| kernel-section-refs | `check_loop_section_refs.py` | rc 0 · **0 violations / 20 sections** —— 与 develop 基线相同 |
| G14/G15 archived-refs | `check_archived_references.py` | **118P / 21W / 0F —— 与 develop 基线逐字相同（零 delta）** |
| Task-0 | `task0_freeze.py --check` | `CONTROLLED_SURFACE_CHANGED` / rc 1 · identity **`3bb781e2…` 不变** · hard-frozen **58 零 diff** |
| §6.1 可复跑推导 | 原文 grep 跑真实 `sdd/gates.md`，与 develop 逐行 diff | 唯一差异 = **新增的 V13 行**；无任何既有行停止解析 |
| AC-11 byte-equality | 程序化比对 `ci.yml` run 行 ↔ plan §5.9 cell | **True**，len 70，sha256 `6c37a730…` |
| **表结构完整性** | 见 §6.1 | 4 文件全部 arity-clean；3 处既存违规不在本 diff 内 |
| **渲染无回归** | 见 §6.1 | 四文件 emphasis 泄漏 delta **全为 0** |
| ruff / mypy / compileall | CI 同口径 | `All checks passed!` · `Success: no issues found in 48 source files` · rc 0 |
| offline pytest（CI 口径）| `run_offline_pytest.py tests --ignore tests/bdd` | **1442 passed / 9 skipped / 82 deselected / 0 failed** |
| offline pytest（全量口径）| `run_offline_pytest.py tests` | **1455 passed / 16 skipped / 82 deselected / 0 failed** —— 与 PR-D1a 记录的基线数字**完全一致** |

### 6.1 表结构完整性与渲染回归（本单元特有风险：新增的是**高密度表格 cell**）

高密度 cell 里一个未转义的 `|` 会让整行**静默错列**而 markdown 仍能渲染，故此项单独验。
按未转义竖线切分每行、与表头 arity 比对（`sdd/gates.md` §2 最大 cell 约 3.9 KB）：

```text
sdd/gates.md                        5 table blocks, 0 arity violations   (§2 = 4-cell 表头 x 19 数据行)
plans/[PLAN]_codex_cross_carrier_kernel.md   26 blocks, 1 violation  ← :62，develop 上同样存在
policies/ci-gates.md                13 blocks, 2 violations          ← :139 / :293，develop 上同样存在
evidence/…/d1b-v13-anchor-evidence.md        15 blocks, 0 violations
```

三处 arity 违规在 develop 上**逐行同样存在**（成因都是 `[[wikilink|alias]]` 或 `` `a|b|c` `` 里的竖线），
**非本 diff 引入**，故不在 anchor-only 单元内修 —— 登记给 F17（其本已获授权编辑这三个文件），见 §10.1。

⚠ **arity 干净不等于渲染干净。** 本单元初稿有**两处 emphasis 泄漏**、arity 检查完全看不到：
`sdd/gates.md` 的 V13 行里 `**同一 predicate**` / `**全命令**` 因**两侧都是 CJK 字符**（既可开也可闭，
CommonMark 优先闭合外层未闭的 `**`）而被吞掉，各留下一个字面 `**`；v0.14 changelog 条目里
`与**「…」**` 的 `**` 前接 CJK、后接 `「`（标点）成为**只能闭合**的 run，提前吃掉了整条条目的斜体开标记，
使最后三行不再是斜体并漏出 3 个字面 `*`。故本单元额外加一条**渲染断言**（CommonMark 口径，
排除 code span 内的 glob 星号）：

```text
文件                                    develop → 本工作树（code span 外的字面 * 个数）
sdd/gates.md                            7 → 7      <em> 13 → 14（新增 v0.14 条目，成对）
plans/[PLAN]_codex_cross_carrier_kernel.md   1 → 1
policies/ci-gates.md                    0 → 0
evidence/…/d1b-v13-anchor-evidence.md   —   0
```

**四个文件的泄漏 delta 全为 0。** 这条断言是 PR-C2 的表结构检查清单**没有覆盖**的失效类别，
建议后续同型单元一并沿用。

### 6.2 doc gate 的**真实覆盖边界**（避免把「全过」读成「已被校验」）

`scripts/check_frontmatter.py` 的 `SCAN_ROOTS` = `docs` / `plans` / `decisions` /
`src/mj_agent/skills` / `src/mj_agent/prompts`。**四个交付文件里只有 plan 一个在其中**；
`sdd/gates.md`、`policies/ci-gates.md`、本 evidence 文件**全部在外**（实测 worktree 与 develop
同为「138 canonical docs」，即新文件**没有进入任何 gate**）。`sdd/gates.md` 的升版三件套同样无 gate。
`check_loop_section_refs.py` 虽扫 `sdd/`，但只判署名 kernel 的章节引用与位号，新增行零命中。
—— 故 §6 表里那句「138 canonical docs 全过」**不代表本次交付被 schema 校验过**；
本单元四个文件的 frontmatter 与格式，实际由**纪律 + 合并审查 + §6.1 的两条自建断言**兜底。

## 7. 本单元明确**未**证明的事（§1.3 assurance 分层）

**本单元自身**：

1. **本单元不产生任何新的运行时证明。** 它只登记 PR-D1a 已经发生的一次 CI 观测。V13 的执行体、
   `.codex/` 产物、hook / rule 语义**一律未被本单元重新验证**。
2. **「anchor reproducible」的口径是「pickaxe + API 值可被第三方复跑得到相同结果」**，不是
   「那次 CI 可以重放」。GitHub 的 run 日志是本单元引用的**外部不可变记录**。
3. **未来 streak 的度量脚本尚不存在。** §5 登记的五 token 语义目前只有散文载体；没有任何 gate
   或测试会校验一个未来的 streak 审计是否按这五个字面量匹配、是否按 step 切分日志。
4. **§5 的 token 触发条件来自源码阅读 + 隔离 fixture 探针**，不是生产 CI 上的观测 ——
   生产上只观测到 `EXECUTED_CLEAN` 一种。

**从 PR-D1a 继承、且与本注册表直接相关的 3 条**（其余 7 条为指针，见 D1a evidence §9）：

| # | D1a 未证明项 | 为何本注册表必须转述 |
|---|---|---|
| D1a-§9.1 | 「Codex harness 在副作用前拒绝」**未被证明**（本仓不执行 Codex harness）| V13 度量的是 **render/reconcile 侧的 drift**，不是 harness 的强制力。任何据 V13 全绿主张「Codex 侧强制生效」的推论都是越界 |
| D1a-§9.2 | **hook 执行腿 = SKIP**（`SKIP_HOOK_NOT_REVIEWED`，per-hook 哈希信任门控，且 D-015 禁止仓内脚本代写信任）| 同上；且解释了为什么 CI 里 V13 恒为纯 Python 检查 |
| D1a-§9.5 | **CI 里跑不到 codex**（四个 workflow 均无 node/codex 安装步骤，`codex execpolicy` 腿恒 SKIP）| 这是 V13 predicate **能**在 CI 稳定执行的前提，也界定了它**不**覆盖什么 |

⚠ **引用纪律（承 F13）**：本文件不据 PR-C0 主张「独立第三方已确认语义保真」。

## 8. Stage 11 对抗性自评审记录

分两趟跑完，**因为第一趟有 3 个镜头中途死于 API 连接错误** —— 这一点如实登记，不粉饰。

| | 计划 agent | 完成 | 失败 | findings | must_fix | 进入证伪 | 驳倒 / 未驳倒 |
|---|---:|---:|---:|---:|---:|---:|---|
| Part A | 14（6 finder + 8 refuter）| 11 | **3**（`anchor-value-fidelity` / `claims-honesty-audit` / `markdown-and-gate-mechanics` 均为连接错误）| 41（0 high / 7 med / 17 low / 17 info）| 9 | 8 | 3 / 5 |
| Part B（补跑上述 3 镜头）| 8（3 finder + 5 refuter）| 7 | **1**（一个 refuter 触发安全拦截）| 20（2 high / 7 med / 7 low / 4 info）| 8 | 4 | 2 / 2 |
| **合计** | **22** | **18** | **4** | **61** | **17** | **12** | **5 / 7** |

**⚠ 覆盖缺口如实披露**：Stage 3 repo scan refuter cap = 5，**133 findings 未经对抗性证伪**；
Stage 11 两趟 refuter 合计 cap = 13、实际完成 12，**48 findings 未经对抗性证伪**。
两者的闭合判据均仅为**作者逐条复核 + 独立复测**。**F15 纪律已遵守** —— 两趟 refuter 运行期间全程未改树。

**本轮闭合的关键缺陷**（全部由本单元自己的新文本诱发，故按判例在本 PR 内修）：

| # | 缺陷 | 处置 |
|---|---|---|
| 1 | **两处 markdown emphasis 泄漏**（V13 行 + v0.14 changelog 条目），arity 检查完全看不见 | 已修；新增 §6.1 渲染断言，实测 delta 归 0 |
| 2 | 「V13 没有任何 blocking 兜底」**被证伪** —— V9 PJ031 与 blocking `Tests` 内的真实树 `verify_lock_v2` 硬约束已存在条目的 schema；且删除/破坏 typed source 会让 blocking `Tests` 变红 | 已按维度改写（§5.1），4 个陈述面同改 |
| 3 | 「lock 不可读 → `ERROR_UNREADABLE` + rc 2」**被证伪**（实测 8 种 lock 故障态全走 rc 1）| 已改（§5 表 + `sdd/gates.md` fail-closed 句）|
| 4 | pickaxe 候选的出现次数把一个字符串的计数挂到了另一个字符串上（`scripts/sdd/agents_sync.py` = 3，裸 `agents_sync.py` = 5）| 已按两个字面量分别登记（§2.1），3 个陈述面同改 |
| 5 | 「本 gate 永不产生 `skipped`」丢了 `check` 限定词 —— step 级 `skipped` 真实存在 | 已按粒度改写（§5 第 6 条），并给出实测先例 run |
| 6 | 「第 4 次独立实证」把同一个 commit 同时列为「前三次之一」与「本次」 | 已更正为「3 个 merge commit 全部实测 0 run，本次是对 `56188fa` 的复测」（§2.4）|
| 7 | 「空格形零输出且 grep 仍 exit 0」自相矛盾（选不中时 grep 退出码是 1）| 已补上「其余各行仍命中」这一前提（§3.1）|
| 8 | 「C2 时约 45 秒」是转述未复测的数字 | 已按两条 run 的 `run_started_at` 重算为 **49 秒**（§2.2）|
| 9 | 「两处 real-tree 钉线已由 D1a 收窄」—— 实际只有一处被收窄 | 已更正（§5.1 末注）|
| 10 | 「当前可计数 streak = 0」是无时点的活体数字 | 已锚定测量时点并声明其时点性质（§2.6）|

**三条被驳倒、未采纳的建议**（读了理由正文，不只看布尔值）：

- 「删掉 `PENDING_PR_D1A_FIRST_CI` 字面量以免自我指涉」—— **驳回**。删掉它会毁掉该测量的 grep 可复现性，
  而改写成「现存两处元引用」会把一个**冻结于 `56188fa` 的事实**换成一个**活体计数**，下一个提到该字面量的
  单元就会让它 stale。改为**锚定时点**（§10.3）。
- 「§4.1.2 的 pickaxe 配方对 V13 失效」—— **驳回**。规则本身是参数化的，逐字套用即得正确单一命中；
  真正的问题只是**片段选择**（已采纳为 §2.1）。
- 「`sdd/gates.md` 升版三件套历史 12/12 一致」（继承自 C2 与 D1a 的措辞）—— **驳回**：
  `updated` 那一条腿按 diff 口径只有 **4/12**、按值口径 **11/12**；且唯一一次写错（`f65442b`）
  是**同分支 16 分钟后修掉、从未进 develop**。本文件因此**不复述** 12/12 这个说法。

## 9. AC 对位

| AC | 要求 | 本单元兑现 |
|---|---|---|
| **AC-11** | V12/V13 records name **actual** command/path；D2 predicate equals observed predicate byte-for-byte | §2.5 程序化证明 `ci.yml` run 行与 plan §5.9 `Exact execution` cell **逐字节相等**（len 70，sha256 `6c37a730…`），§5.10 复述句同串；§2.1 给出 anchor 的可复跑判据与片段选择理由；§3 完成五要素对位 |

其余 AC 不属本单元（§5.1.1 只把 AC-11 分配给 PR-D1b）。

## 10. 与后续 unit 的接口

### 10.1 F17 交接（Gate 1 Q1 拍板：**不在本单元做**）

**结论：F17 推迟到 OBSERVATION 窗口内的一个独立单元，不在 PR-D1b 内做。** 判据：

1. **「D1b 是最后一个低成本窗口」经查为假。** PR-G 之前还隔着 PR-D2 / PR-E / PR-F 三个单元，
   且 D1b 与 D2 之间有一段 **≥14 天**、§5.1 明文「no active implementation goal」的 OBSERVATION 空窗 ——
   那正是天然槽位。
2. **在 D1b 内做会浪费观察窗。** §5.9 把 **PR-D1b anchor 自身**列为自排除项，故本单元的 CI run
   **不计入** V13 streak；一个独立单元的 run **计入**。
3. **越出 scope 定义。** §3.3 / §5.1 row 14 / §5.1.1 三处都把本单元界定为「V13 anchor registration only /
   exact anchor-value approval / 不得夹带行为变化」。re-home 必然要改 **V12** 的活体注册面（§5.8 与
   `sdd/gates.md` 的 V12 行），那不是 V13 registration —— 须先修订这三处再重开 Gate 1。
4. **成本量级不匹配。** 两个仓内 M-FU 注册工件先例分别为 226 行与 236 行；新建一份合并注册工件
   数倍于本单元的全部交付。

**给 F17 执行者的交接包**：

- **两条实测日历腿**：V12 = 2026-09-10（锚 `2fbf700` 2026-08-27）；V13 = **2026-09-11**（锚 `c485f8d` 2026-08-28）。
- **推荐槽位**：PR-D1b 合并之后、PR-D2 之前的 OBSERVATION 窗口内，独立 `maintain/` 或 `documentation/` 单元。
- **推荐形态**：新建一份合并的 M-FU 注册工件（沿用两个先例的结构），把 §5.8 与 §5.9 两张表整体迁入，
  plan 侧留指针；或提升为 `policies/` 原生条文（#403 先例提升的是**规则**不是逐 gate 值，需注意这一差异）。
- ⚠ **硬护栏**：re-home 可以自由改 `plans/**`、`sdd/gates.md`、`policies/ci-gates.md`；
  **绝不可**改 `AGENTS.md` / `policies/ai-agent.md` / `policies/git-branching.md` —— 它们是 `policy_refs`，
  改动即强制 enforcement re-render（理由见 §4.1）。把注册表「顺手提升到 `policies/ai-agent.md`」是最自然
  也最危险的直觉。
- ⚠ **顺带更正一处既存假陈述**：§5.8 与 `sdd/gates.md` V12 行都写着「日历腿到期时注册表已在闭合记录中」。
  实测**为假** —— PR-D2 的入场即要求 V13 日历腿 ≥ 2026-09-11，而 PR-G 排在 D2/E/F 之后，故 PR-G 合并必
  ≥ 2026-09-11，**两条日历腿都在 plan 闭合之前成熟**。真正的缺口是「**PR-G 之后**才动作的消费者会引用到
  一份已退休的记录」。本单元的 §5.9 声明段已按更正后的措辞书写；两处旧措辞属**既存**缺陷（非本单元诱发），
  按判例不在 anchor-only 单元内改 V12 的活体注册面，随 F17 一并更正。
- ⚠ **顺带修三处既存表格 arity 违规**（§6.1 实测，develop 上同样存在，本 diff 未引入）：
  `plans/[PLAN]_codex_cross_carrier_kernel.md:62`、`policies/ci-gates.md:139`、`:293` ——
  成因都是 cell 内未转义的 `|`（`[[wikilink|alias]]` 或 `` `a|b|c` ``），各需一个 `\|` 转义。
  F17 本已获授权编辑这三个文件。
- ⚠ **F17 至今没有 GitHub issue**：它只活在两个 evidence 文件与 Epic #499 里，而 **PR-G 会关闭 #499**。
  建议 F17 执行前先给它开一个真 issue。

### 10.2 给 PR-D2 的三条 follow-up

⚠ **ID 命名注记**：本仓已有**两条互不相干的 F 序列**（Epic #499 自己的，以及 ADR-036 / dual-agent-compat
的 F1-F18），二者的 F10 / F11 / F18 已经撞号。故本单元新开的编号一律**带 Epic 前缀**书写。

**`#499-F21` —— D1a 留下的两种「predicate」读法未收口。**
plan §5.9 `blocking route` / §5.10 / ADR-039 / AC-11 都说 D2 挂载 **byte-identical predicate**
（= `--check --surface enforcement`）；而 D1a 留给 D2 的测试 docstring 与 evidence F20 都写「恢复
bare `--check`」。⚠ **二者可分离，不是矛盾**：D2 可以既挂 `--check --surface enforcement`（argv 逐字节
相同，满足 AC-11），又**独立地**恢复 bare `--check` 以找回整份 lock 的钉线。D1a 自己的 `ci.yml` 注释
（"mounts the byte-identical predicate"）站在 plan 一边。**本单元按 §5.10 登记，不动 blocking route 行、
AC-11 或 ADR-039**（后两者均在本单元 4 文件交付面之外，且 PR-C2 对 V12 的同位行也逐字未动）。
D2 须在其 `ci-blocking-gate-toggle` 记录里把这两件事分开写清。

**`#499-F22` —— bare `--check` 独有的整份 lock 规范文本比对已被静默移除。**
`surface == "all"` 会额外比对**整份 canonical lock 文本**（envelope 字段、顺序、规范格式），
而任何 scoped surface 只比对自己 in-scope 的条目。D1a 把那一处 real-tree 钉线收窄为 `skills`+`mcp` 时，
因此**一并移除了一条曾经 blocking 的 whole-lock-envelope 断言**；其补偿断言（「每个 lock entry 至少属于
一个 surface」）**不覆盖 envelope 级规范文本**。该缺口**今日无门可查**。应与 F20 一起在 PR-D2 恢复
bare `--check` 时闭合，且**不要**与 F20 混为一谈 —— F20 说的是「那一处钉线的 surface 收窄」，
F22 说的是「收窄顺带丢掉的 envelope 断言」。

**`#499-F23` —— Stage 11 在执行体上查出的三处缺陷（均属 PR-D1a 面，不在 anchor-only 单元内修）。**

| 子项 | 实测 |
|---|---|
| (a) | `scripts/sdd/agents_sync.py` **模块 docstring** 仍写 `--surface skills\|mcp\|all`，漏了 D1a 新增的 `enforcement`（argparse 的 help 是对的）|
| (b) | **v1-manifest 树上 `--surface enforcement` 会跑 MCP 的 reserved-lock-key 检查**，并打印 enforcement 的补救提示 —— 旧路径按 `skills` / `else: mcp` 二分，`enforcement` 落进 mcp 分支。后果：一个纯 MCP 面的故障能重置 V13 的 epoch，且提示把读者指向 `codex-enforcement.yml` |
| (c) | **非 UTF-8 的 manifest / lock 会抛出未捕获的 `UnicodeDecodeError`** —— 无 token、rc 1、被 `continue-on-error` 抹绿（即 §5 第 5 条的「无 token」结局的一个真实成因）|

三者都要改共享执行体（同时承载 **blocking** 的 V10/V11），故**本单元的零 behavior diff 条件排除了在此修复**。

### 10.3 承接的 follow-up 表

F2 / F3 / F4 / F7 / F8 / F10 / F11 / F12 / F13 / F14 / F15 / F16 / F18 / F19 保持 PR-D1a ledger 的状态；
F17 见 §10.1；F20 保持「必须在 PR-D2 内」；本单元新增 **`#499-F21` / `#499-F22` / `#499-F23`**（§10.2）。

**F16 复核（本单元实测）**：`PENDING_PR_C1_FIRST_CI` 的清理面仍为 **5 行 / 3 文件**，本单元一处未动。
另实测：**在 develop `56188fa` 上**，`PENDING_PR_D1A_FIRST_CI` 全仓只有 **1 处** —— 就在 plan §5.9 的
Observation anchor cell 里，**已被本单元覆写消除**。V13 的 step 名刻意不含占位串（`ci.yml` 注释自述理由），
故 **V13 不产生 F16 式残余，本单元也不开同类 follow-up**。
⚠ 上句刻意**保留**该字面量而不改写成「现存 N 处」：保留字面量才使这条测量可被 grep 复现，
而写活体计数会在下一个提到它的单元手里立刻 stale（这正是本仓「引结构事实、不引当期措辞」的纪律）。
