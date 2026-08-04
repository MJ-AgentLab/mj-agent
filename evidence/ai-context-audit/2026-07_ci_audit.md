---
type: evidence
summary: 2026-07 月度 CI blocking-flip 计数账本（program plan §11.2(4) 强制工件）——V8/V9/V10 观察期
  gate 的 per-gate 连续-clean streak + violation 数 + 影响范围；P4 双轴翻转拍板的可核验依据。§7 记
  flip-time 权威重跑（2026-08-03，issue 399）：streak 55/55/49、violation 0、zero-delta 复验、
  exit-0 warning 盲区闭合，并按 §11.2(3) 登记窗口内无关 job 失败（dependabot docker 生态 ×4）
owner: ranzuozhou
created: 2026-07-24
updated: 2026-08-03
state: active
track: shared
---

# 2026-07 CI Audit — dual-agent-compat P4 blocking-flip 计数账本

> **这是什么**：`plans/[PLAN]_dual-agent-compat.md` §11.2(4) 强制的 `<YYYY-MM>_ci_audit.md` 计数工件
> ——记录 warning-期 gate（V8/V9/V10）的 violation 数 + 影响范围，作为 P4 blocking 翻转拍板的可核验依据。
> 它吸收了 `policies/ci-gates.md` §4.1「blocking 切换前 1 周 dry-run」的**产物**要求（时序被 14 日 warning
> 窗口真超集吸收，见 §11.2(4)）。**本文件不翻转任何 gate**（P4 双轴翻转是独立的 07-28 动作，逐 gate
> `ci-blocking-gate-toggle` 拍板）。
>
> **落位说明**：文件名 `2026-07_ci_audit.md` 匹配 `check_ai_context_audit.py` 的
> `CYCLE_FILE_RE`(`YYYY-QN.md`) 与 `INVESTIGATION_FILE_RE`(`YYYY-MM-DD_*.md`) **皆不命中** → 落
> validator「other」桶 → 仅打印一行 `skip`、**不做 schema 校验、不 FAIL**。`evidence/` 亦在
> `check_frontmatter.py` `SCAN_ROOTS` 之外。本账本故意用**月度**命名与季度 A6 audit / ad-hoc
> investigation 两类 schema'd 条目区分。

## 1. 观察窗口与锚点（§11.2(2)）

时钟属于 **gate**（钉「该 gate 在 warning 模式下无误报跑了多久」）。三 gate 同日首挂 → 绑定时钟 = 2026-07-14。

| Gate | CI 首挂 commit | 首挂时刻（UTC / +0800） | 计数窗口（distinct head-SHA） |
|---|---|---|---|
| V8 `check_development_agent.py --all --fail-on error` | `42037bd` | 2026-07-14 01:29Z / 09:29 | 50（窗口全程） |
| V9 `check_agents_projection.py --all` | `42037bd` | 2026-07-14 01:29Z / 09:29 | 50（窗口全程） |
| V10 `agents_sync.py --check --surface skills` | `36d185d` | 2026-07-14 03:39Z / 11:39 | 44（36d185d 起；6 个更早 run 无 V10 step） |
| V11 `agents_sync.py --check --surface mcp` | `b8f43d3` | 2026-07-14 09:09Z / 17:09 | **N/A — day-1 blocking**（D-016 豁免，不入本计数） |

- **本快照时刻**：2026-07-24（最新 run `d3df47b` @ 02:55Z）。
- **最早翻转资格 = 2026-07-28**（14 自然日，2026-07-14 + 14；本快照日 = 锚点 +10 日）。

## 2. 计数口径（§11.2(3)）

- **计数域**：`ci.yml` 全部 run（任意分支），**按 head SHA 去重**（同 commit 的 `push`+`pull_request` 对只计一次）。
  合入 `develop` 的 merge commit **不触发** `ci.yml`（push 触发仅限 5 类工作分支前缀 + PR→main/develop），
  故计数只随工作分支提交涨——本窗口 50 个 head-SHA **全部 `push` 事件**。
- **clean 判据**：被观察 gate 的 **step 输出**为 SoT（`ci.yml:292`），**非** job 结论——V8/V9/V10 均
  `continue-on-error: true`，job 恒 `success` 即使某 gate step 内部告警。clean 信号：
  - V8/V9：step 输出 `=== Summary === errors: 0 / warnings: 0`
  - V10：step 输出 `OK: projection in sync (surface=skills, 5 skills, lock consistent)`
- **streak 重置**：仅因被观察 gate 的 step 非 clean 而重置；无关 job 失败 / flake 不重置（须在本账本登记——本窗口无）。

## 3. 度量方法（双证据法；本快照的具体实现）

`gh run view <id> --log` 全量抓取在本次采集时触发 GitHub **secondary rate-limit**（logs 端点），无法一次性
逐 run 抓 step 输出。故采**双独立证据法**，并按 §11.2(3)「到期前实测勿外推」将**权威计数留待 07-28 翻转时**
以下述命令重跑：

1. **check-run annotations 全窗扫描**（core REST，未受限）——`continue-on-error` step 一旦**非零退出**
   （V10 drift → `exit 1`；V8/V9 error → `exit 1`）即在 ci check-run 留 failure annotation。
   ```bash
   # 对 50 个 head-SHA 逐一：
   crid=$(gh api "repos/MJ-AgentLab/mj-agent/commits/<sha>/check-runs" \
            --jq '.check_runs[]|select(.name=="ci")|.id')
   gh api "repos/MJ-AgentLab/mj-agent/check-runs/$crid/annotations"    # 期望空
   gh api "repos/MJ-AgentLab/mj-agent/check-runs/$crid" --jq '.conclusion'  # 期望 success
   ```
   **结果：50/50 run — `conclusion=success` 且 annotations = 空（0 个）。** → 全窗口无任一 gate 非零退出。
2. **本地 HEAD 复现**（develop @ `2dde848`）——gate 是确定性静态校验器：
   ```
   check_development_agent.py --all      → errors: 0 / warnings: 0 / info: 0   (V8 clean)
   check_agents_projection.py --all      → errors: 0 / warnings: 0 / info: 0   (V9 clean)
   agents_sync.py --check --surface skills → OK: projection in sync (5 skills, lock consistent) (V10 clean)
   ```
3. **最新 run 直抓 step-log 佐证**（rate-limit 前成功一次，run `d3df47b`/`30062880262`）：
   V8 `errors: 0 / warnings: 0` · V9 `errors: 0 / warnings: 0` · V10 `OK: projection in sync` — 三 gate 全 clean。

**权威计数重跑命令（07-28 翻转拍板时按 §11.2(3) 实测）**：
```bash
gh run list --workflow ci.yml --limit 100 --json conclusion,createdAt,headSha,event,databaseId
# 按 headSha 去重后，自各 gate 锚点起逐 run 抓被观察 gate 的 step 输出核 clean
```

## 4. 计数结果（本快照 2026-07-24）

| Gate | 计数窗 | job-success | annotation-clean（非零退出=0） | 本地 HEAD 复现 | 最新 run step-log | **连续-clean（保守下界）** | violation 数 |
|---|---|---|---|---|---|---|---|
| **V8** | 50 | 50/50 | 50/50 | clean(0E/0W) | clean | **≥ 50**（annotation 法）；见 §5 caveat | **0** |
| **V9** | 50 | 50/50 | 50/50 | clean(0E/0W) | clean | **≥ 50**（annotation 法）；见 §5 caveat | **0** |
| **V10** | 44 | 44/44 | 44/44 | clean(in sync) | clean | **44**（V10 `exit 1`-on-drift 被 annotation 完整覆盖） | **0** |

- **影响范围（§11.2(4)）**：无 violation → 无影响范围。窗口内触及 gate 输入面的提交均为已 clean-合并的
  dual-agent 里程碑 PR（#326 S1 / #330 S2 / #333 P2 / #337 P3 / #350 doctor / #353 memory×5）+ #383
  （AGENTS.md/post-merge），无 drift-引入编辑（`git log` 核实：gate 输入面自锚点起仅这些 clean-merged 变更）。
- **两腿达标判定（本快照）**：run-count 腿 ——V8/V9 = 50、V10 = 44，**均 ≥ 20** ✓；calendar 腿 ——14 日
  于 **2026-07-28** 达成（本快照 +10 日，未达）。→ 07-28 两腿俱满足，届时按 §11.2(3) 重跑权威计数即可翻转。

## 5. 诚实边界（caveat；不掩盖）

- **annotation 法只覆盖非零退出**：V8/V9 带 `--fail-on error`，**warning 不致非零退出**（`exit 0`）→ 一个纯
  warning 的 V8/V9 step **不产生 annotation**、本法看不见。缓解：本地 HEAD 复现与最新 run step-log 均显式
  `warnings: 0`，且窗口内 gate 输入面无 drift-引入变更——故「V8/V9 存在未见 warning」的风险极低但**非零证否**。
  V10（`agents_sync --check`，任何 drift 即 `exit 1`）**无此盲区**，annotation 法对其完整。
- **本快照未逐 run 抓 V8/V9 step 文本**（rate-limit）→ V8/V9 的「≥50 连续 clean」是 annotation+复现的**推断
  下界**，非 50 份逐 run step-log 直证。按 §11.2(3)「实测勿外推」，**权威计数以 07-28 翻转时重跑为准**；本账本
  确立工件 + 方法 + 当前证据，指示强资格，不代替 flip-time 实测。
- **修正既有口径**：本轮实测**推翻**了 brief 沿用的「V10 14/20 as of 07-16」——实测全窗口 V10 无任一 drift
  annotation（44/44 clean）。旧数疑为更早一次保守/部分计数，此处按实测更正。

## 6. 与 P4 翻转的关系（本账本不做翻转）

P4 翻转是**双轴**动作（§11.2(1)），本切片**均不涉及**：

- **blocking 轴** `continue-on-error: true→false`：V8 / V9 / V10 各自独立 `ci-blocking-gate-toggle` 拍板 + 执行记录。
- **阈值轴** `--fail-on error→warning`：V8 改现有旗标值；V9 新增旗标；V10 无此轴。

翻转前置（§11.1 P4 资格）：14 日（07-28）+ 每 gate ≥20 连续 clean + 零 waiver/误报/未关闭 warning + Owner 逐 gate 批准。
本账本为该拍板提供计数依据；翻转本身另行执行（S3 blocking 转正腿，calendar-gated ~07-28）。

> **后续**：翻转已于 **2026-08-03** 执行（issue #399）——见下方 §7 flip-time 权威重跑。本节（§1-§6）
> 保留 2026-07-24 快照原貌，不回改。

## 7. Flip-time 权威重跑（2026-08-03；履行 §11.2(3)「实测勿外推」）

P4 双轴翻转于 **2026-08-03** 执行（执行 issue #399）。§5 caveat 与 §11.2(3) 均要求**权威计数以
flip-time 重跑为准**，本节即该重跑记录，接续 §4 快照（2026-07-24）而非取代它。

### 7.1 计数（delta 法 = §4 快照 + 其后新增 head-SHA）

| Gate | §4 快照（07-24） | flip-time delta | **flip-time 合计** | 门槛 | 判定 |
|---|---|---|---|---|---|
| V8 | 50 | +5 | **55** | ≥20 | ✅ |
| V9 | 50 | +5 | **55** | ≥20 | ✅ |
| V10 | 44 | +5 | **49** | ≥20 | ✅ |

delta 的 5 个 head-SHA（§4 快照后至 2026-08-03 的全部 `ci.yml` run，按 headSha 去重）：

| head-SHA | 分支 | 事件 | `ci` 结论 | failure annotations |
|---|---|---|---|---|
| `c82a2bc` | `feature/391-dual-agent-negative-tests` | push + PR | success | **0** |
| `f662c01` | `documentation/312-ac10-live-verification` | push + PR | success | **0** |
| `d2052a4` | `dependabot/…/gha-minor-patch-7a5a078ad4` | PR | success | **0** |
| `a5987f6` | `dependabot/…/actions/setup-python-7` | PR | success | **0** |
| `69bc709` | `dependabot/…/astral-sh/setup-uv-9.0.0` | PR | success | **0** |

`863ec4f` 是 merge commit——按 §2 既定口径 merge-to-develop 不触发 `ci.yml`，不计入。

### 7.2 exit-0 warning 盲区的闭合（履行 §5 caveat）

§5 诚实记录：annotation 法**只覆盖非零退出**，纯 warning 的 V8/V9 step（`exit 0`）不产生 annotation，
本法看不见。本次翻转**以本地实跑直接闭合该盲区**——在 flip-time HEAD `863ec4f` 上按**翻转后的阈值**
跑全部四个 gate：

```text
check_development_agent.py --all --fail-on warning → === Summary === errors: 0 / warnings: 0 / info: 0   exit 0
check_agents_projection.py --all --fail-on warning → === Summary === errors: 0 / warnings: 0 / info: 0   exit 0
agents_sync.py --check --surface skills            → OK: projection in sync (surface=skills, 5 skills, lock consistent)  exit 0
agents_sync.py --check --surface mcp               → OK: projection in sync (surface=mcp, 5 skills, lock consistent)     exit 0
```

→ 翻转在 flip-time HEAD 为 **zero-delta**：阈值收紧**不产生任何新失败**，`warnings: 0` 由实测直证
（不再是 §5 所述的推断下界）。

**阈值轴非 vacuous 佐证**（防 false-green——若 `--fail-on warning` 是空操作，上述全绿将毫无信息量）：
两 checker 的阈值判定同构
`at_threshold = summary["error"] > 0 or (args.fail_on == "warning" and summary["warning"] > 0)`
（`check_development_agent.py:608` / `check_agents_projection.py:449`）；且 committed test **双向**钉——
warning 树 `exit 1`（`test_sdd_development_agent.py:256,275` 为 V8；`:348` 为 V9），clean 树 `exit 0`
（`:338`）。

### 7.3 violation 数 + 影响范围（履行 `policies/ci-gates.md` §4.1「产物保留」）

- **violation 数 = 0**——三 gate 全窗口零非零退出、零 warning。
- **影响范围**：翻转在 flip-time HEAD zero-delta，故**对现存代码零影响、零 PR 受阻**。此后影响面 =
  任何引入 manifest / projection drift 或 manifest warning 的 PR 将被**阻断**而非仅告警。
- **回退成本**：单行 `continue-on-error: false → true`（每 gate 可独立回退）。
- **冗余安全网**：`ci.yml` 块注释所载 real-tree pins（`test_real_tree_*`）早已令同批不变量经 blocking
  Tests step 实质生效；翻转后 gate step 与测试钉线互为冗余（本地复验 `pytest -k real_tree` 9 passed）。

### 7.4 无关 job 失败登记（§11.2(3) 强制项）

§11.2(3) 规定：「streak 重置**仅**因被观察 gate 的 step 非 clean 而重置；无关 job 失败 / flake
**不重置**，**但须在审计产物中登记**」。观察窗内登记如下：

| 时间（UTC） | job | 生态 | 结论 | 重置 streak？ |
|---|---|---|---|---|
| 2026-07-27T01:07:18Z | `docker in /infra/docker` | dependabot `docker` | failure | **否** |
| 2026-07-27T01:07:17Z | `docker_compose in /infra/docker` | dependabot `docker-compose` | failure | **否** |
| 2026-08-03T01:06:15Z | `docker in /infra/docker` | dependabot `docker` | failure | **否** |
| 2026-08-03T01:06:15Z | `docker_compose in /infra/docker` | dependabot `docker-compose` | failure | **否** |

- **不重置的判据**：这些是 Dependabot 生态更新 job（`event=dynamic`），**不是 `ci.yml` 的 run**，
  不含 V8/V9/V10 任何 step——§11.2(3) 计数域明确限定为「`ci.yml` 的全部 run」。
- **根因（已核实）**：Dependabot 从**默认分支**读取配置；默认分支 `main` 的 `.github/dependabot.yml`
  中 `docker` / `docker-compose` 两个 ecosystem 的 `directory` 仍为 `/infra/docker`（本仓无 `infra/`
  目录，实际路径为 `/docker`；`develop` 分支已修正但因 Dependabot 只读默认分支而未生效）。
- **归属**：根因修复另立 `maintain` issue（Low；须落到 `main` 才生效）。本账本只履行登记义务。

### 7.5 翻转执行记录

- **执行 issue**：#399。**拍板**：三次**独立**的 `ci-blocking-gate-toggle` Owner 拍板（V8 / V9 / V10
  各一，不合并、不自判 N/A），执行记录 = #399 comment（先例 = V11 的 #330 comment）。
- **改动面**：`.github/workflows/ci.yml` 恰 3 个 step + 其块注释；**V11 逐字未动**；其余 9 条
  warning-mode gate 零改动。
- **镜像面同步**：`sdd/gates.md` 的 V8/V9/V10 行 `warning@ci → blocking@ci`；`AGENTS.md` 漂移 gate
  段落 + dated 脚注。
