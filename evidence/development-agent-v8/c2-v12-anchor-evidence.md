---
type: evidence
summary: >-
  Epic #499 PR-C2 V12 anchor registration —— 把 V12 "Cross-Carrier Structure"
  的 `policies/ci-gates.md` §4.1.1 五要素注册落到真值载体：**CI 首挂锚
  `2fbf700` 2026-08-27 14:11:11 +0900**（§4.1.2 run-命令 pickaxe 单一命中），
  **epoch 起点 = 该 commit 上的首次真实 CI** run `33041866036`（event=push，
  `05:14:15Z`；V12 step job `98417034436` `05:14:57Z`→`05:14:58Z`，输出
  `EXECUTED_CLEAN` 7/7）。同 head SHA 的 run `33041907780`（pull_request）
  输出**逐字节相同** → 去重后合计 **1 次观测**，这正是 §5.8「head-SHA-
  deduplicated」措辞存在的原因（不去重则 streak 恒高估一倍）。⚠ 实测
  **merge commit `d810746` 触发 0 次 run**（`develop` 不在 ci.yml push
  过滤器内），故 anchor 只能取 PR head run。本单元**零 behavior diff**：
  刻意不改 `ci.yml` / `check_cross_carrier.py` / 任何测试，diff 仅含
  `plans/` + `sdd/gates.md` + 本文件三处**登记与证据**。残余 PENDING
  标识串登记为 F16。分析与实测由 Claude Code 执行、值由 Owner 拍板。
owner: ranzuozhou
created: 2026-08-27
updated: 2026-08-27
state: active
track: agent
---

# V12 Anchor Registration — Epic #499 (PR-C2)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.8（V12 registration field 表）
> 与 §5.7 末段（**C2 changes only registration/evidence** —— gate id、real mount
> commit/time、run-command/path、applicability、threshold/epoch、self-exclusion
> 与 clean predicate；**If behavior/config changes are needed, stop and open repair
> before C2**）。Delivery unit = **PR-C2**，AC = **AC-11**，merge condition =
> **anchor reproducible + zero behavior diff**（§5.1 row 12）。approval =
> **exact anchor-value approval**；rollback = **anchor-only correction PR**（§5.1.1）。

## 0. 入场锚点与 Owner 拍板记录

| 项 | 实测值 |
|---|---|
| 前序单元 PR-C1 | #517 **MERGED**，head `2fbf700b6f5e1b4b5929f0d8f07478244d64533a`，merge `d81074621be79224730ee4b937cf0e2a987d5a8e`，`2026-08-27T06:14:02Z` |
| develop 三方 | local = origin = gitee = `d810746`（逐一 `rev-parse` 复验） |
| C1 Stage 17 ledger | `#499#issuecomment-5435190727`，body **23605 B**、纯 LF（`'\r\n' not in body` 实测）、SHA-256 `1c8c455aeb8842d00e35d75f6fd988f0587f95c454e0a4e35b8ad79db8847c0a` **逐字节复算吻合**；18 records 连续 0–17 且**全终态**（仅 `EXECUTED_CLEAN` / `EXECUTED_WITH_OWNER_DECISION` 两种） |
| Task-0 preflight | `CONTROLLED_SURFACE_CHANGED` / **rc 1**，identity `a0124cff7e2ea306abc38043208dfa44afc8a62905da068302204ef29ecff0c4`，hard-frozen **58 零 diff** —— 这是 C1 用掉 §1.1 授权 hunk 后的**预期授权态**，不是回归 |
| 工作树 EOL | `.claude/skills/*/SKILL.md` + `.agents/skills/*/SKILL.md` 共 **55/55 `w/lf`**，零 `w/crlf`（治理事实 3 的刷新口径在本工作树已成立，无需重刷） |
| 其他 | #499 / #504 均 OPEN；无 open PR；worktree 数 2 → 建分支后 3 |

**Gate 1（三问一次呈清，Owner 全取推荐项）**：

| # | 问题 | Owner 拍板 |
|---|---|---|
| Q1 | §4.1.1 五要素注册的载体 | **kernel plan §5.8 表即注册表**（补齐 anchor + 明写自排除）；`policies/ci-gates.md` **不**登记逐 gate 值（该文件自述「规则 + 指针层，不复制姿态真值」，实测其中无任何 gate 的 anchor/适用口径/资格公式）；耐久性缺口明写 |
| Q2 | `PENDING_PR_C1_FIRST_CI` 残余（可执行/配置面 **5 行 / 3 文件**，见 §8.1） | **ci.yml 与脚本一处不碰** —— 守住零 behavior diff，尊重 C1 在 `ci.yml:386` 的明写指令；残余登记为 F16 |
| Q3 | 原始实测值的证据载体 | **`evidence/development-agent-v8/c2-v12-anchor-evidence.md`**（本文件），与 p1a/p1b/c0 同族同构 |

## 1. 交付面（Gate 1 批准的 exact scope）

| 文件 | 动作 | 依据 |
|---|---|---|
| `plans/[PLAN]_codex_cross_carrier_kernel.md` | §5.8 表 4 个 cell 补齐 + 表下「注册载体声明」段 | Gate 1 Q1；§5.7「registration」 |
| `sdd/gates.md` | §2 新增 **V12 Cross-Carrier-Structure** 行（插在 V11 与 `docker-bdd-scenario-check` 之间） | §2 承载逐 gate 真值；§4.1.1 要求 gate 标识与 ci.yml step 名一一对应 |
| `evidence/development-agent-v8/c2-v12-anchor-evidence.md` | 新建（本文件） | Gate 1 Q3 |
| `policies/ci-gates.md` | **1 处诱发性 stale 修复**：§6 引言的 `V1-V11` → `V1-V12`（:310） | 见下方说明 |

> **关于 `policies/ci-gates.md` 的 1 行改动（与 Gate 1 Q1 的关系，明写以便 Owner 复核）**：
> Gate 1 Q1 判定该文件**不作注册载体**（不登记逐 gate 值）—— 本改动**不违反**该判定，它没有
> 写入任何 anchor / 适用口径 / 资格公式 / 自排除值。它修的是**本 PR 自己造成的**陈述失真：
> §6 引言称原 TBD「遗漏了 `V1-V11`」，而 V12 一旦进入 `sdd/gates.md` §2，该范围表述即刻为假。
> 按本仓判例「**诱发性 stale 在造成它的 PR 内修**」（与「独立既存缺陷另立单」是两类）处置。
> 由 Stage 11 lens 3 抓出。**若 Owner 认为它超出 anchor-only 边界，单独 revert 这一行即可，
> 不影响其余交付面。**

**刻意不碰**（每一项都是有意识的选择，不是遗漏）：

- `.github/workflows/ci.yml` —— 不改 step 名、不改 `continue-on-error`、不改 run 命令。
- `scripts/sdd/check_cross_carrier.py` —— 不改 `OBSERVATION_ANCHOR` 或任何常量。
- `tests/**` —— 无测试新增或修改。
- `policies/ci-gates.md` 的**注册内容** —— 一个 gate 值都不写（见 §3 末段）；该文件唯一的改动是上表
  那 1 行诱发性 stale 修复。§1.1「姿态载体」表与 §6.2 的两处计数**不动**（钉在 `f29f501` 的定格
  快照，见 §6 第 2 条）。
- `.agents/**` / `.agents.lock.json` / `.codex/config.toml` —— 本单元零 sync、零产物变更。
- `AGENTS.md` —— §1.1 只授权 PR-C1 与 PR-D1a 两个具名 hunk，**C2 无授权额度**。

## 2. Anchor 实测值（原始证据）

全部经 GitHub API 现场复测，**不采信任何转述**（AC-11 要求 exact values，故照抄即是风险面）。

### 2.1 CI 首挂锚（§4.1.2）

```bash
git log --oneline --reverse -S "check_cross_carrier.py" -- .github/workflows/ci.yml
# → 2fbf700 feat: cut over to manifest v2 with 18 Codex carriers   （单一命中）
git log -1 --format='%H %aI' 2fbf700
# → 2fbf700b6f5e1b4b5929f0d8f07478244d64533a 2026-08-27T14:11:11+09:00
```

**锚 = `2fbf700` 2026-08-27 14:11:11 +0900 #499**。判据用 **run 命令片段**而非 step 名
（§4.1.2 明载「名称可能后续被改写而误指」；V10 行即因 step 名在 #330 改过而专门注记）。
锚为**非 merge 的实现 commit**，与 V8/V9/V10/docker-build 各行惯例一致。

### 2.2 首次真实 CI（epoch 起点）

`head_sha=2fbf700` 上共 **5** 个 run，其中 `ci` workflow **2 个**：

| run id | event | `run_started_at` | conclusion | V12 step job | V12 step 起止 | V12 输出 |
|---|---|---|---|---|---|---|
| `33041866036` | **push** | `2026-08-27T05:14:15Z` | success | `98417034436` | `05:14:57Z` → `05:14:58Z` | `EXECUTED_CLEAN` |
| `33041907780` | pull_request | `2026-08-27T05:15:04Z` | success | `98417167238` | `05:15:42Z` → `05:15:42Z` | `EXECUTED_CLEAN` |

另 3 个为 `check-stale-docs` / `check-commit-messages` / `docker-build`（均 `05:15:04Z`、success），
不属 V12 观测面。

> **对 C1 ledger 的一处精化（非纠错）**：C1 治理事实 2 与 §5.8 交接段只记了 PR run 的
> V12 step 时间 `05:15:42Z`。实测 **push run 的 V12 step 更早**（`05:14:57Z`），故
> 「首次真实 CI」的严格值取 push run。两者同 head SHA、去重后本就合计 1 次观测，
> 故此精化**不改变任何计数**，只把 anchor 的 exact value 钉准。

### 2.3 两次执行的输出（逐字节相同 → 「anchor reproducible」）

两个 job 的 V12 step stdout 完全一致：

```text
=== V12 Cross-Carrier Structure (warning telemetry; anchor PENDING_PR_C1_FIRST_CI) ===
  [PASS] X02 translated<->registry bijection closed (13 capabilities)
  [PASS] X03 carrier<->artifact closed (18 SKILL.md present)
  [PASS] X04 carrier<->lock closed (18 entries, kind+owner consistent)
  [PASS] X05 no orphan skill entries in the lock
  [PASS] X08 .agents/README.md present and lock-owned
  [PASS] X07 fidelity index covers exactly the translated set (13)
  [PASS] X09 registry edge closure holds (38 edges: every no-carrier target has a substitute)
=== Summary === pass: 7 / warnings: 0 / errors: 0
status written = .mj-agent-local/status/cross-carrier.json
EXECUTED_CLEAN
```

clean run 打印 **7 行 PASS**，顺序为 X02/X03/X04/X05/X08/X07/X09。
⚠ **「7 行 PASS」≠「7 个 join ID」** —— 执行体实际发出的 ID 是 **X02–X09 共 8 个**（无 X01）：
`X06`（artifact 目录反向孤儿）是 **WARN-only**，与 X03 共用同一条 PASS，只在触发时现身，
因此它在任何 clean 输出里都不可见（源 `scripts/sdd/check_cross_carrier.py:233`，钉线
`tests/unit/test_cross_carrier_v12.py:97`）。**登记必须按执行体源而非 clean 输出**：X06 能产出
finding → `EXECUTED_WITH_FINDINGS` → **重置 streak**，漏登它就会给未来 flip 单元留下一个
注册表里查不到的重置源。gates.md 行已按 8 个 ID 登记。
合并条件「anchor reproducible」由**两次独立执行输出逐字节相同**满足。

### 2.4 merge commit 不触发 CI（决定 anchor 只能取 PR head run）

```bash
gh api "repos/MJ-AgentLab/mj-agent/actions/runs?head_sha=d81074621be79224730ee4b937cf0e2a987d5a8e"
# → total_count = 0
```

成因是结构性的：`ci.yml` 的 `push` 分支过滤器只含 5 个临时分支类型（`feature` / `bugfix` /
`documentation` / `maintain` / `hotfix`），**不含 `develop`**；`pull_request` 只对 base 为
main 或 develop 的 PR 触发。**后续单元（含 PR-D1b 的 V13 anchor）不要去找一条不存在的
merge-commit run。**

### 2.5 实际 run 命令 vs plan 声明（AC-11 的核心）

AC-11 原文（plan **§7.1 Program-level AC**；**刻意不写行号** —— 本 PR 自身的 §5.8 编辑就把它从
:1483 推到 :1493，行号锚是无 gate 可查的诱发性 stale）：「V12/V13 records **name actual
command/path**」。实测二者**逐字节相等**：

```text
ci.yml:394 (actual)  uv run python scripts/sdd/check_cross_carrier.py --status-json .mj-agent-local/status/cross-carrier.json
plan:1364  (declared) uv run python scripts/sdd/check_cross_carrier.py --status-json .mj-agent-local/status/cross-carrier.json
BYTE-EQUAL: True
```

路径注记：`--status-json` 落点在 **gitignored** 的 `.mj-agent-local/`（`.gitignore:73`，
`git check-ignore` 复验），脚本自建父目录（CI 不 mkdir），产物永不入仓。

## 3. 五要素注册对位（`policies/ci-gates.md` §4.1.1）

| §4.1.1 注册项 | V12 值 | 载体 |
|---|---|---|
| gate 标识 | `V12 Cross-Carrier-Structure`（gates.md 行名）↔ ci.yml step 名 `V12 cross-carrier structure (WARNING per plan §5.8; anchor PENDING_PR_C1_FIRST_CI)` | gates.md §2 行 |
| CI 首挂锚 | `2fbf700` 2026-08-27 14:11:11 +0900 #499 | plan §5.8 + gates.md 行 |
| 适用口径 | 非 path-triggered → **§4.1.3**（head-SHA 去重）；**不**适用 §4.1.4 三态 | plan §5.8 + gates.md 行 |
| 阈值 + 资格公式 | **两腿 AND**：≥14 natural days **AND** ≥20 consecutive head-SHA-deduplicated `EXECUTED_CLEAN` | plan §5.8 |
| 自排除规则 | PR-C1 mount / PR-C2 anchor / 未来 blocking-flip PR；且 §4.1.3 末条（翻转 PR 自身分支 run 不计入自身资格，计数锚在翻转分支前一 commit）**已明写** | plan §5.8 |

**为什么载体是 plan 而不是 `policies/ci-gates.md`**：该文件 :18-19 自述「本文件是规则 + 指针层，
**不复制姿态真值**（逐 gate 真值列在 `sdd/gates.md` §1-§3）」，实测其中不存在任何一个 gate 的
anchor / 适用口径 / 资格公式 / 自排除值 —— 它是 schema 而非 instance。§4.1.1 要求「构成要件 =
**事先在 `plans/` 注册**」，本 plan（created 2026-08-12）早于首挂（2026-08-27），满足「事先」。

## 4. 「零 behavior diff」的自证

合并条件之一是 **zero behavior diff**。本单元把它做成**可由 diff 本身检验**的性质，而不是一句声明：

1. **diff 不含任何可执行文件**：改动集恰为 `plans/*.md` + `sdd/gates.md` + `policies/ci-gates.md`
   + `evidence/**.md` **四个 markdown 面**；无 `.py`、无 `.yml`、无 `tests/`、无生成产物。
2. **无测试新增/修改** —— 因此没有「用测试把 warning gate 从后门变成实质 blocking」的风险
   （C1 在 Stage 11 抓到过一次 `test_v12_real_tree_is_clean`，Tests 步是 blocking）。
3. **gate 姿态位不变**：ci.yml 中 V12 的 `continue-on-error: true` 逐字未动 → 按 gates.md 头注
   定义仍是 `warning@ci`。本单元**不是** posture 翻转，故不需 `ci-blocking-gate-toggle` 拍板。
4. **gate 标识未变** → §4.1.2 的 pickaxe 判据（run 命令片段）与 step 名双双稳定，观测 epoch
   在登记时刻**无接缝**。

**为此付出的代价（明写，逐行可复算）**：`PENDING_PR_C1_FIRST_CI` 字面量继续留在**可执行/配置面
5 行 / 3 文件** —— `.github/workflows/ci.yml:386`（注释）、`:392`（step 名）、
`scripts/sdd/check_cross_carrier.py:28`（docstring）、`:74`（`OBSERVATION_ANCHOR` 常量）、
`tests/unit/test_cross_carrier_v12.py:67`（断言）。
Gate 1 Q2 判定：**登记后它是首挂期的历史标识串，不是活体断言**；真值以 §5.8 表与 gates.md 行为准，
两处都已明写这一点。残余清理登记为 **F16**（见 §8.1）。

> **口径说明（避免下次数错）**：本 PR 另在 `sdd/gates.md:64` 与本文件中各写有该字面量 ——
> 前者是**登记转写**（gate 标识必须与 step 名一一对应），后者是**证据引用**，二者都**不是**
> F16 的清理对象，故不计入上述 5 行。另 `.mj-agent-local/status/cross-carrier.json` 是本地
> gitignored 运行产物，不入仓、不计数。初稿曾写「6 行 / 5 文件」并把「plan §5.8 的历史措辞」
> 列为一处 —— **那一处正是被本 PR 自己删掉的**，现予更正。

## 5. 验证结果

全部在 `maintain/499-v12-anchor` 工作树、改动落盘后执行（fresh evidence，非改前快照）。

| 检查 | 命令口径 | 结果 |
|---|---|---|
| **V8** Development-Agent | `--all --fail-on warning` | `errors: 0 / warnings: 0 / info: 0 (mode=all)`，rc 0 |
| **V9** Agents-Projection | `--all --fail-on warning` | `errors: 0 / warnings: 0 / info: 0 (mode=all)`，rc 0 |
| **V10** Sync-Drift | `--check --surface skills` | `OK: projection in sync (surface=skills, 18 skills, lock consistent)`，rc 0 |
| **V11** Codex-MCP | `--check --surface mcp` | `OK: projection in sync (surface=mcp, 18 skills, lock consistent)`，rc 0 |
| （本地全面） | `--check`（surface=all） | `OK: projection in sync (surface=all, 18 skills, lock consistent)` |
| **V12** Cross-Carrier | CI 逐字命令 | **`EXECUTED_CLEAN`，pass 7 / warn 0 / err 0**，rc 0 |
| fidelity | `check_fidelity_attestations.py --all` | rc 0 |
| **Task-0** | `task0_freeze.py --check` | `CONTROLLED_SURFACE_CHANGED` / rc 1，identity `a0124cff…` **未变**，hard-frozen **58 零 diff**（= 预期授权态；本单元未新增 controlled 改动） |
| ruff | `ruff check` | `All checks passed!` |
| mypy(strict) | `mypy src/mj_agent` | `Success: no issues found in 48 source files`，rc 0 |
| compileall | `-m compileall -q src scripts tests` | rc 0 |
| offline pytest | `run_offline_pytest.py tests --ignore tests/bdd` | **1356 passed / 9 skipped / 82 deselected / 0 failed**（与 C1 Stage 17 基线逐数相同 → 零回归） |
| contract band | `-m contract` | 63 passed / 1 skipped |
| bdd band | `tests/bdd` | 13 passed / 7 skipped |
| offline boundary | `check_test_offline_boundary.py` | `OFFLINE_BOUNDARY: GREEN` |
| frontmatter | `check_frontmatter.py` | `OK: 138 canonical docs` |
| wikilinks | `MJ_AGENT_A4_STRICT=1` | 0 archive-ref violations + **0 unresolved A4 targets** |
| kernel section refs | `check_loop_section_refs.py` | `violations: 0, sections: 20` |
| stale docs | `find_stale_docs.py` | `OK: no rename/move/delete in origin/develop...HEAD` |
| cross-repo refs | `check_no_cross_repo_refs.py`（warning 态） | **15 warnings / 11 files —— 与 C1 基线逐数相同**，且与本 PR **4 个**改动文件**零重叠**（11 个命中文件逐一比对，见 §5.2）|

### 5.1 表结构完整性（本单元特有风险：新增的是**高密度表格 cell**）

程序化校验（非目测，脚本按不变量断言而非记录当期总数 —— 总数会被下一次追加作废）：

- plan §5.8 表：**每行恰 2 列**，无参差。
- `sdd/gates.md` §2 表：**每行恰 4 列**，V12 行落在 **V11 与 `docker-bdd-scenario-check` 之间**
  （按相邻行名断言位置，不钉行号）。
- 本文件：**每张表自身列数一致**（逐表比对，允许不同表列数不同）。
- 每个改动 markdown：**反引号数为偶数**（奇数即有未闭合的 inline code）。

—— 高密度 cell 里一个未转义的 `|` 就会让整行静默错列而 markdown 仍能渲染，故此项单独验。

### 5.2 关于 cross-repo 「零重叠」结论的口径纠正（自查记录）

首次用正则解析 checker 输出只得到 **2** 个文件，与 C1 ledger 记载的 11 个不符 —— 复查发现
解析器按 `/` 匹配路径，而 checker 在 Windows 上打印 `docs\guide\…` 反斜杠分隔，**漏掉 9 个**。
改以直接读原始输出复核：**15 warnings / 11 files**，逐一比对确认无一是本 PR 改动文件。
结论不变，但**先前的成立理由是错的**；非空断言在位（解析空集会让任何「零重叠」结论 vacuous
通过 —— C1 在同一处踩过一次）。

## 5b. Stage 11 对抗性自评审记录

**规模**：3 finder 镜头（exactness / zero-behavior-scope / governance-consistency）+ 12 refuter
（top-6 finding × 2 个不同镜头：correctness 与 consequence）= **15 计划 / 15 完成 / 0 失败**。
产出 **18 findings**（去重后仍 18，无重复 location+title 对）。

**F15 纪律已遵守**：refuter 运行期间**全程未改树**（Stage 10 结束到本节写入之间零编辑），
故 `refuted=false` 是干净的证伪信号，不存在 C1 那次「作者已修好」污染。

**结果**：进入 refutation 的 6 条**全部在两个镜头下均未被驳倒**（`refuted=[false, false]` ×6），
即 6/6 成立。cap 之外的 12 条由作者逐条独立复核，**同样全部成立并已修复**。
**合计 18/18 findings 判定为真、18/18 在本 PR 内闭合**（**0 high / 10 medium / 8 low**，
由 workflow 返回值程序化计数，非目测）。

**覆盖缺口（如实披露）**：cap = 6，故 **12 条未经对抗性证伪**，其闭合判据仅为作者复核 +
逐条实测复算；证伪强度弱于前 6 条。未失败的 agent = 0，无因失败造成的盲区。

**本轮改正的实质性错误**（均为作者原稿的事实错误，不是措辞问题）：

| # | 错误 | 复算结果 | 处置 |
|---|---|---|---|
| 1 | 断言「不存在 X01 与 **X06**」 | **X06 存在**（`check_cross_carrier.py:233`，WARN-only，与 X03 共用 PASS，钉线 `test_cross_carrier_v12.py:97`）。实际 ID 集 = X02–X09 共 8 个 | §2.3 改写；**gates.md 行改按 8 个 ID 登记** —— X06 能重置 streak，漏登会给 flip 单元留下查不到的重置源 |
| 2 | 「§6.2 计数恰由本 PR 复原（→6）」 | **不成立**。今日重跑 §6.1 推导得 **7**；第 7 个是 `run_offline_pytest.py`，于 `a733371`（2026-08-13）入 ci.yml，**非** `f29f501` 祖先 | §6 第 2 条撤回并改述；处置不变（快照体裁）；分派 **F18** |
| 3 | F16 残余「6 行 / 5 文件」，含「plan §5.8 历史措辞」 | 实际 **5 行 / 3 文件**；被列的第 6 处**正是本 PR 自己删掉的** | §4 / §8.1 改为逐行点名表；口径说明区分「残余 vs 登记转写」 |
| 4 | AC-11 引用钉 `plan:1483` | **本 PR 自身的 §5.8 编辑把它推到 :1493** —— 典型诱发性行号 stale | 改引 `plan §7.1`，**刻意不写行号** |
| 5 | 「每个非 develop 分支 PR **恒**产生 2 次 ci run」 | **伪不变式**：push 过滤器只含 5 类前缀，`dependabot/*` 等对 develop 开 PR 只产生 1 次 | 三处载体统一改为「成对是**可能**而非**保证**」，结论（必须按 head SHA 去重）不变 |
| 6 | `sdd/gates.md` 加行未按该文件惯例升版 | 历史 **12/12** 一致；两个同类先例（#453 v0.11、#444 v0.7）均升版 + 刷 `updated` + 写 changelog | 升 `0.12`→`0.13`、`updated` 刷 2026-08-27、补 v0.13 changelog 条目 |
| 7 | `policies/ci-gates.md` §6 引言「遗漏了 `V1-V11`」 | 本 PR 令 V12 进入 §2 后**该范围表述即为假**（诱发性 stale） | 改 `V1-V12` 并注 #499 PR-C2；见 §1 的边界说明 |
| 8 | 若干引用/转写不精确 | `ci-gates.md` 自述位于 `:18-19` 非 `:19-20`；V10/V11 输出漏 `surface=` 判别词；mypy 记为「零输出」实为 `Success: no issues found in 48 source files` | 全部按实测原文改正 |

另有 3 条 low 属文档自洽（plan frontmatter `updated` 未刷、§5.8 `Gate ID / name` 字段未填满
§4.1.1 要求的一一对应三元组、耐久性义务无 follow-up ID），已分别修复并登记 **F17**。

## 6. 本单元明确未证明的事（§1.3 assurance 分层）

1. **未证明 V12 会长期零误报** —— 本单元只钉 epoch 起点。截至登记时刻，V12 的 head-SHA 去重
   观测数 = **1**（即 §2.2 那一次），距 §5.8 的 ≥20 尚远，日历腿最早 2026-09-10 到期。
   任何「V12 已稳定」的说法在本单元都无证据支撑。
2. **`policies/ci-gates.md` 两处计数未动 —— 理由是「定格快照」，不是「数字仍成立」**：§1.1
   「姿态载体」表的 step 级现役实例列表与 §6.2「6 个 CI 执行体没有 gate 行」**都显式钉在
   `f29f501` 实测**，属定格快照体裁，按定义不随树漂移，故不改。
   ⚠ **自我更正**：本文件初稿曾写「§6.2 的数字恰由本 PR 复原（7 → 6）」。**该说法经复算不成立**，
   现予撤回。按 §6.1 自带的可复跑推导在今天的树上重算：`sdd/gates.md` 脚本列 29 个唯一 `.py`
   路径（已含 V12 行）vs `.github/workflows/` 下 33 个 —— 残余是 **7 而非 6**。差额的第 7 个是
   `scripts/sdd/run_offline_pytest.py`（ci.yml 三处调用，gates.md 脚本列零命中）；它于
   `a733371`（2026-08-13）进入 ci.yml，实测 **不是** `f29f501` 的祖先，即它在快照之后才出现，
   与本 PR 无关。本 PR 的真实效应是让 `check_cross_carrier.py` **退出**该残余集（−1）。
   处置不变（不改 `policies/ci-gates.md` 的两处快照），但**理由必须是快照体裁本身**。
   —— 这正是本仓「定义必须能重现自身记录值」的判例：数字在未重跑推导的情况下被断言。
   `run_offline_pytest.py` 无 gate 行一事登记为 **F18** 候选（不在本单元处置）。
3. **fidelity 面仍无 CI 守卫（F11 未闭）** —— V12 的 X07 是该面唯一 CI 可见信号，但 V12 自身是
   warning。本单元**不**挂 `check_fidelity_attestations.py`（新 gate 挂载是独立 Owner 治理动作，
   且需 gate 编号分配；V13 已被 §5.9 预留给 Codex Enforcement Drift，F11 须另取编号）。
4. **不得据 PR-C0 主张「独立第三方已确认语义保真」** —— F13 的独立性降级（reviewer = Owner =
   author）在本单元同样适用，本文件未以任何方式修复它。

## 7. AC 对位

| AC | 要求（plan §5.1.1 / §7.1） | 本单元如何满足 |
|---|---|---|
| **AC-11** | first real V12 CI | §2.2 —— run `33041866036` / job `98417034436` / step `05:14:57Z`，`EXECUTED_CLEAN`；实测非转述 |
| **AC-11** | mount SHA / time | §2.1 —— `2fbf700` 2026-08-27 14:11:11 +0900，§4.1.2 run-命令 pickaxe 单一命中 |
| **AC-11** | **actual** command/path | §2.5 —— ci.yml 实际 run 与 plan 声明**逐字节相等**（程序化比对），路径 gitignored 已注记 |
| **AC-11** | epoch / self-exclusion | §3 —— 两腿 AND 公式 + 三类自排除 + §4.1.3 末条明写；clean predicate 四码映射见 gates.md 行 |
| merge cond. | anchor **reproducible** | §2.3 —— 两次独立执行输出逐字节相同 |
| merge cond. | **zero behavior diff** | §4 —— diff 无可执行文件、无测试、姿态位与 gate 标识均未动 |

## 8. 与后续 unit 的接口

### 8.1 F16（新增 follow-up）—— PENDING 标识串残余

**F16 清理面 = 5 行 / 3 文件**（post-diff 树上 grep 复算，逐行点名）：

| # | 位置 | 体裁 |
|---|---|---|
| 1 | `.github/workflows/ci.yml:386` | 注释 |
| 2 | `.github/workflows/ci.yml:392` | **step 名（= gate 标识）** |
| 3 | `scripts/sdd/check_cross_carrier.py:28` | 模块 docstring |
| 4 | `scripts/sdd/check_cross_carrier.py:74` | `OBSERVATION_ANCHOR` 常量 |
| 5 | `tests/unit/test_cross_carrier_v12.py:67` | blocking 带断言 |

**不计入的两类**（见 §4 口径说明）：`sdd/gates.md:64` 与本文件中的出现是**登记转写 / 证据引用**，
非残余；`.mj-agent-local/status/cross-carrier.json` 是 gitignored 本地产物。
plan §5.8 的旧措辞曾是第 6 处，**已由本 PR 删除**，不再存在。
清理它需要同时改**生产源码 + 一条 blocking 带测试 + workflow 配置**，正是 §5.7 要求
「stop and open repair」的形态，故**不在 anchor-only 的 C2 内做**。
实测补充（供未来判断成本）：该常量**验证过是纯 telemetry** —— 它只在 status payload 与 stdout
banner 两处被读，`run_checks` 从不引用它，改动不影响 exit code / result_code / 任一 join；
`.mj-agent-local/` gitignored 且**全仓无任何消费者**读该 JSON。即便如此，改它仍会触发
blocking Tests 步的断言，故必须与测试同改。

### 8.2 给 PR-D1b（V13 anchor）的现成口径

V13 与 V12 同型（每 PR 必跑、非 path-triggered、warning 首发、两腿 AND ≥14d + ≥20）。可**直接复用**
本单元的四条实测口径，不必重新发现：

1. **merge commit 不产生 run** —— anchor 必取 PR head SHA 上的 run（§2.4）。
2. **同 head SHA 可能 2 次 `ci` run**（push + pull_request）—— 去重后计 1；不去重高估近一倍（§2.2）。
   ⚠ **是「可能」不是「恒」**：push 过滤器只含 5 类临时分支前缀，`dependabot/*` 等分支对 develop
   开的 PR 只产生 1 次 run。故按 head SHA 归并，**不可**用「run 数 ÷ 2」反推观测数。
3. **首次真实 CI 取 push run**（它比 PR run 早约 50 秒），不要只看 PR run（§2.2 注记）。
4. **rc 0 有两种含义**（`EXECUTED_CLEAN` 与 `SKIP_*`），run conclusion 不可作判据，须读
   执行体 stdout 的 result_code（§4.1.3「执行体输出是 SoT」）。

### 8.3 给未来 blocking-flip 单元的移交

本注册表**寄居在一个将被 PR-G 翻 `completed` 的 plan 里**（ADR-039 第 11 条 + §5.12），而 V12 的
日历腿最早 2026-09-10 才到期。**flip 单元的第一步必须是把 §5.8 表 re-home**（到自己的 M-FU 注册
工件，或提升为 `policies/` 原生条文），不得引用已闭合 plan 作为活体注册表 —— 这正是
`policies/ci-gates.md` §4.1.2 / §4.1.3 因 issue #403 从 `plans/[PLAN]_dual-agent-compat.md`
逐字提升为政策原生条文的同一失效模式，本仓已在此摔过一次。

**该义务本身需要一个能活过 PR-G 的载体** —— 把它只写进将被关闭的 plan 里，正是它所描述的失效模式。
故本单元登记两个新 follow-up：

| # | Item | Origin | Blocking next unit? |
|---|---|---|---|
| **F16** | `PENDING_PR_C1_FIRST_CI` 残余 5 行 / 3 文件（见 §8.1）。清理需同改生产源码 + blocking 带测试 + workflow 配置 = §5.7 的「stop and open repair」形态 | PR-C2 Gate 1 Q2 | No |
| **F17** | **在 PR-G 翻 plan 为 `completed` 之前**，把 V12（§5.8）与 V13（§5.9）的观察期注册表 re-home 出 plan（自有 M-FU 工件或提升为 `policies/` 原生条文）。日历腿最早 2026-09-10 到期，晚于本 Epic 的收尾节奏 | PR-C2 Stage 11 | No（但**必须早于 PR-G**） |
| **F18** | `scripts/sdd/run_offline_pytest.py` 在 ci.yml 三处调用却无 `sdd/gates.md` 行（§6 第 2 条实测）。是否补 gate 行 / 编号是 `sdd/gates.md` 的独立变更 | PR-C2 Stage 11 | No |
