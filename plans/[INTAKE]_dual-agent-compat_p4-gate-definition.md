---
type: intake
summary: 双工具兼容 v5 第八执行切片（P4 门定义硬化——修 5 处已核实的 gate 判定口径缺口）的 Stage 0 Intake 落盘——documentation/Low/1 PR；4 项 Owner 拍板（D1 双轴分离 / D2 起点锚 / D3 20-CI 口径 / D4 DRI 周吸收）+ D1 前提更正重确认（§7.1，2026-07-16）；对应 issue #341（总锚 #312）
owner: ranzuozhou
created: 2026-07-15
updated: 2026-07-16
completed: 2026-07-16
state: completed
track: shared
---

# [INTAKE] 双工具兼容 v5 — P4 门定义硬化切片（issue #341）

> Stage 0 输出于 2026-07-15 会话内产生并当日落盘（worktree 内）；触发 §2.1 落盘判定
> （HITL 点≥3〔4 项判定口径拍板 + commit/push/PR〕 + 治理口径变更）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §11.1 晋级条件 + §18 D-009/D-016（逐字为准）；
> 前序：P0/P1/S0/S1/S2/P2/P3 全闭环（P3 执行 #337 closed AC 6/6，flip #339 merged）。

## 1 Task Classification

- Type: **documentation**（治理文档判定口径补全）——不触 `.github/workflows/ci.yml`、不翻转任何 gate 姿态、不触 `.claude/**`、`.mcp.json`、manifest `mcp`/`codex.posture` 段、4 必停面
- Base branch: develop @ `147f619`；G1 worktree `documentation/341-p4-gate-definition`
- 影响范围：`plans/[PLAN]_dual-agent-compat.md`（§11.1 + §18 D-009/D-016 + frontmatter `updated`）· `sdd/gates.md`（§2 V8/V9/V10/V11 posture 行）· `policies/ci-gates.md`（§4 交叉引用 + V11 豁免补记）· `plans/` 2 件〔本文件 + PLAN〕

## 2 锚选定（Step 1）与观察期硬约束核实

Owner 拍板锚 = **E（P4 门定义硬化）**——AskUserQuestion 确认；非 A（settings biz-allow 收窄）/ 非 B（S3 doctor 只读版）/ 非 C（3 独立拍板议题评估）/ 非 D（P4 本体）。

**观察期硬约束已实测核实 → D 与 S3-blocking 出局**：

| 事实 | 实测值 | 证据 |
|---|---|---|
| 今日 | 2026-07-15 | `date` |
| V10 CI step 首挂 | `36d185d`，2026-07-14 11:39 +0800（#326） | `git log -S "agents_sync.py --check" -- .github/workflows/ci.yml` |
| V10 首次实际执行 | 2026-07-14T03:39:45Z（= 11:39 +0800） | `gh run list --branch maintain/326-s1-agents-sync` |
| 已历自然日 | **1 / ≥14** | 07-14 → 07-15 |
| 07-14 起连续 CI 成功 | ~18 runs 全 success（去重前） | `gh run list --workflow ci.yml` |
| 判据连接词 | **`同时满足`（AND）** | `plan:324` 逐字 |

→ 日历腿硬性未达；run 腿无法代偿。**最早资格 2026-07-28**（见 D2）。

## 3 Stage 0 核查产出——5 处已核实缺口

| # | 缺口 | 证据 |
|---|---|---|
| G1 | `plan:324` 规定的翻转动作**不产生 blocking**：V8 同时带 `continue-on-error: true` 与 `--fail-on error`，两者正交；仅改 `--fail-on` 后 `continue-on-error: true` 仍吞掉结果 | `.github/workflows/ci.yml:311-313` |
| G2 | **V10/V11 无 `--fail-on` 旗标**（`agents_sync.py` CLI 确无），`plan:324` 的机制对其完全不适用。**V9 则相反**：其脚本**有**该旗标（`check_agents_projection.py:396`，`default="error"`），只是 CI 未显式传参而靠默认值生效 → V9 的阈值轴翻转须**新增**旗标而非改值 | `check_agents_projection.py:396` + `ci.yml:317`（V9）；`agents_sync.py` CLI + `ci.yml:291`（V10/V11） |
| G3 | **观察期起点锚无任何治理文件写明**（`gates.md:62` 仅「S1 首发 #326」） | grep `观察期` across `plans/` `sdd/` `policies/` |
| G4 | **「20 次连续 CI」无度量口径、无计数器工件**；push/pull_request 双触发未定去重；「连续」重置规则未定义 | `plan:324` / `plan:444`(D-009) |
| G5 | `policies/ci-gates.md:41` 的 1 周 DRI dry-run 与 `plan §11.1` **互不引用**；V11(#330) day-1 blocking 已属既成绕过 | `policies/ci-gates.md:41` vs `plan:324` |

> **G1 是本切片的核心发现**：它不是措辞瑕疵而是**动作失效**——按 plan 字面执行完 P4，全部 gate 仍非 blocking。

## 4 Risk Assessment

- Level: **Low**（纯治理文档；无 schema/secret/prod/必停面实改；无新依赖；不改 `ci.yml`）
- Triggered §3.1 必停项：**无**。
- **不放宽任何门**：D1 的净效果是让 P4 的翻转**真正生效**（严于原字面）；D2/D3 是补全定义（原为空）；D4 保留产物义务。
- Gated actions：commit/push/PR 逐次拍板（恒定，per ADR-034 / AGENTS.md boundary 4）；merge 交 Owner（classifier 拦 agent 直合 develop）。
- **不触发 `ci-blocking-gate-toggle`**：本切片不改 gate 姿态。翻转本身留给 ~07-28 后的 P4 本体切片，届时每 gate 独立拍板。
- A13 不适用（不动 `.claude/settings.json`）；A14 不适用（不动 `.mcp.json`）；D-017 不适用（不动 manifest `mcp`/`codex.posture`）。

## 5 环境事实（2026-07-15 Intake 核验）

- develop @ `147f619`（**非** brief 所述 `6ab25f3`）——PR #340 当日 merge（`0e6fcf9`，`Write(path)`→`Edit(path)` 权限规则迁移 + secrets read-deny 加固）。
- 各 gate CI 首挂锚（实测）：V8/V9 = `42037bd` 2026-07-14 09:28 +0800（#320）；V10 = `36d185d` 2026-07-14 11:39 +0800（#326）；V11 = `b8f43d3` 2026-07-14 17:08 +0800（#330，day-1 blocking）。**三者同日**。
- 当前 CI 姿态（`ci.yml:311-324` 实读）：V8 `continue-on-error: true` + `--fail-on error`；V9 `continue-on-error: true`（无 `--fail-on`）；V10 `continue-on-error: true`（无 `--fail-on`）；V11 无 `continue-on-error` 键（= blocking）。
- **残留分支（brief 称"无"，实为有）**：`origin/maintain/330-s2-mcp-projection`（PR #331 MERGED）+ `origin/documentation/330-plan-state-flip`（PR #332 MERGED）= S2 post-merge 双清遗漏，可安全删；`origin/bugfix/119-env-example-ascii-only` = **不可删**（PR #120 CLOSED 未合，issue #119 仍 OPEN，是该修复的唯一副本）。→ 登记为 §9 交办事项，不在本切片范围。
- `plan` frontmatter `updated: 2026-07-13` 相对 2026-07-15 的正文改动（`2fae9b6`）已过期 → 本切片改正文，顺带修正。
- harness 冻结锚 `b1973a9` 对 HEAD `147f619` 仍字节同一（`git diff b1973a9 HEAD -- scripts/sdd/fixture_*.py tests/fixtures/development-agent/` = 空）——本切片不触 harness，仅记录。

## 6 Documentation Decision（粗评；Stage 3 已细化）

Plan=Create（`plans/[PLAN]_dual-agent-compat_p4-gate-definition.md`，PR 携带）；SPEC/ADR/RUNBOOK/Evidence=None——本切片是对既有 §11.1 判定口径的**补全**，不是新决策体，故不开 ADR；4 项拍板以 D1-D4 记入 §18 既有 D-009/D-016 的修订与本 INTAKE §7。

## 7 Owner 拍板记录（2026-07-15）

| # | 决策 | 结果 |
|---|---|---|
| 1 | **锚** | **E = P4 门定义硬化**（AskUserQuestion 确认）。 |
| 2 | **D1 翻转机制** | **双轴分离，两轴都归 P4**：blocking 轴 = `continue-on-error: true→false`（V8/V9/V10 通用，每 gate 独立 `ci-blocking-gate-toggle` 拍板）；阈值轴 = `--fail-on error→warning`，适用 **V8 + V9**（V8 改现有旗标值 / V9 新增旗标；V10/V11 无此轴）。**见 §7.1 前提更正**。 |
| 3 | **D2 观察期起点锚** | **各 gate 独立时钟**，锚 = 该 gate 的 **CI 首挂 commit**；批量翻转受**最年轻 gate** 约束。→ 最早资格 **2026-07-28**。 |
| 4 | **D3 20-CI 口径** | **全部 `ci.yml` run 按 head SHA 去重**，数 gate step clean；streak **仅因 gate step 非 clean 重置**，无关 job 失败/flake 不重置（但须登记）。 |
| 5 | **D4 DRI dry-run 周** | **吸收时序、保留产物**：14 日窗口是 1 周 dry-run 的真超集 → 时序被吸收；`evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（violation 数 + 影响范围）**仍须产出**，正是 D3 缺的可核验工件。 |
| 6 | **ssh-manager 行**（前瞻，非本切片） | **推给 #312「ssh-manager wrapper 方案」议题一并拍**；将来 A′（settings biz-allow 收窄）只动 2 条 prod biz 行 → 单次拍板、零耦合。 |

### 7.1 D1 前提更正与重确认（2026-07-16）

**留档理由**：D1 的首次拍板建立在 AI 提供的一项**错误事实**上。按 propose→拍板→apply 纪律
（ADR-034），错误前提下的拍板须**带更正后的事实回到 Owner 重确认**，不得由 AI 单方"顺理成章"
地改写已拍板记录。本节完整留下更正链，不覆盖原始记录。

| 项 | 内容 |
|---|---|
| **首次拍板（2026-07-15）** | 阈值轴 = `--fail-on error→warning`，**仅 V8**。 |
| **AI 当时提供的前提（错误）** | 「V9/V10 无 `--fail-on` 旗标」——据 CI 命令行未见该旗标推断。 |
| **实测更正（Stage 10，AC-8 grep 逼出）** | `check_agents_projection.py:396` 定义 `--fail-on {error,warning}`，`default="error"`，`:449` 消费之 → **V9 有阈值轴**，只是 CI 未显式传参而靠默认值生效。故 `ci.yml:290` 注释「V8/V9 run at `--fail-on error`」**本就准确**，是 AI 误读。`agents_sync.py`（V10/V11）确无该旗标 → 原判断对 V10/V11 成立。 |
| **重确认（2026-07-16）** | Owner 在**更正后的前提**下重新拍板：**阈值轴 = V8 + V9 都翻**（V8 改现有旗标值；V9 **新增** `--fail-on warning`；V10/V11 无此轴）。理由：两 checker 脚本 argparse 同模式、`at_threshold` 逻辑逐字相同、severity 语义同、今日均 0E/0W → 对称处理；V8 传参而 V9 不传看起来是挂载时的不一致而非决策。 |
| **影响** | P4 的阈值轴动作面由 1 个 gate 扩为 2 个（V9 将**新增**一个今日不存在的 CI 旗标）——该扩面已由本次重确认明确授权。 |
| **发现路径** | 本切片自身的 AC-8 自证 grep → 5-lens 对抗审查（facts / executability / scope-governance 三镜独立命中，adversarial verify 未能驳倒）。 |

## 8 Verification Plan

- Level A（read-only）：`check_frontmatter.py` · `check_wikilinks.py` · `check_development_agent.py --all --fail-on error`（V8）· `check_agents_projection.py --all`（V9）· `agents_sync.py --check`（V10+V11，本地裸 check 双面全查）· `pytest tests/unit tests/eval`（clean worktree 无 #298 假红）
- Level A（自证）：AC-8 grep——`plan` / `gates.md` / `ci.yml` 注释三处对翻转机制的表述必须一致，且无残留「仅改 `--fail-on`」口径
- Level B：无（本切片不跑 side-effect 动作；不改 CI，不翻 gate）

## 9 交办事项（本切片范围外，登记以免丢失）

1. **S2 残留远程分支双清**：`git push origin --delete maintain/330-s2-mcp-projection documentation/330-plan-state-flip`（PR #331/#332 均已 MERGED）。gitee 侧同查。
2. **`origin/bugfix/119-env-example-ascii-only` 不可当垃圾清**：PR #120 CLOSED 未合、issue #119 OPEN；该分支落后 develop 459 commits，修复需重做。是留是弃 = Owner 决策。
3. **gitee/develop 落后 origin/develop 3 个 merge**（`7d36fb2` vs `147f619`）——镜像节奏或漏推，待确认。
4. **#312 独立拍板议题实为 4 项而非 3 项**（第 4 项 = settings biz-allow 收窄，Owner 2026-07-13 追加）；且三者不独立：`agents_sync.py:265-271` 对 args 中任何 `${` fail-close，5 个 memory server 全以 `${MJ_AGENT_PG_MEMORY_*_URL}` 传 args → **memory×5 硬依赖 pg-default 先决**。建议后续切片按此依赖序推进。

## 10 Next Step

Stage 4 计划落盘（本 worktree）→ Gate 5 拍板 → Stage 8 实施（§11.1 + D-009/D-016 改写 + gates.md posture 行 + ci-gates.md 交叉引用）→ Stage 10/11 验证/自评（含 5-lens 对抗审查）→ Gate 13 PR → 交 Owner 合并。merge 后本文件 state flip completed（Rule 12）。
