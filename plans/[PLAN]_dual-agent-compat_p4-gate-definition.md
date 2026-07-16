---
type: plan
summary: dual-agent-compat v5 P4 门定义硬化执行计划——修 5 处已核实的 gate 判定口径缺口（G1 翻转动作失效 / G2 机制不适用 / G3 起点锚未定义 / G4 20-CI 无口径 / G5 DRI 周互不引用）；新增 plan §11.2 判定口径节 + D-009/D-016 修订 + gates.md posture 行 + ci-gates.md 交叉引用；1 PR（#341 `documentation/341-p4-gate-definition`）；不改 ci.yml、不翻 gate 姿态；总锚 #312
owner: ranzuozhou
created: 2026-07-15
updated: 2026-07-16
state: active
track: shared
---

# [PLAN] 双工具兼容 v5 — P4 门定义硬化切片（issue #341）

## 1 Linked Artifacts

- Issue: #341（AC1–AC8）；总锚 #312 P4 项（承载本门的原始表述）
- Intake: [[[INTAKE]_dual-agent-compat_p4-gate-definition]]（4 项 Stage 0 拍板 D1–D4）
- Program plan: [[[PLAN]_dual-agent-compat]] §11.1 晋级条件 + §18 D-009/D-016（改写目标，逐字为准）
- 前序：P3 #337（closed，AC 6/6）+ flip #339，develop @ `147f619`

## 2 Context

P0/P1/S0/S1/S2/P2/P3 已全闭环；§11.1 P3→P4 晋级门于 2026-07-15 达成（#337/#339）。主轨道
下一阶段 = **P4**，但其 blocking 资格门受观察期约束（V10 CI 首挂 2026-07-14，1/14 自然日）
→ **最早资格 2026-07-28**，P4 本体不可做。

Stage 0 核查在确认该约束时，逐条核实出 P4 门本身的 **5 处缺口**（详 Intake §3）。其中 **G1 是
动作失效而非措辞瑕疵**：`plan:324` 把翻转规定为「把 CI 参数从 `--fail-on error` 改为
`--fail-on warning`」，但 V8 同时带 `continue-on-error: true`（`ci.yml:311-313`），该参数才是
决定「非零退出是否 fail job」的轴 —— 按 plan 字面执行完 P4，**全部 gate 仍非 blocking**。
G2 further：**V10/V11** 根本没有 `--fail-on` 旗标（`agents_sync.py` CLI 确无），该机制对其完全
不适用。（**V9 是易错点**：其脚本**有**该旗标而 CI 未传参、靠 `default="error"` 生效——详
[[[INTAKE]_dual-agent-compat_p4-gate-definition]] §7.1 前提更正。）

**时机论据**：判定口径应在观察窗口**关闭前**定，而非事后。事后定口径 = 已知结果再写规则，
正是自设治理门最容易滑向 structure theater 的地方。本切片落在窗口中段（1/14 天），是最后一个
「还不知道结果」的时点。故 P4 前置纵切 = 补全门定义，让 P4 在 ~07-28 可真正执行。

## 3 Scope

- 包含：见 issue #341 In-scope —— `plan` §11.1 收口 + 新增 §11.2 判定口径节 + §18 D-009 改写 /
  D-016 补记；`sdd/gates.md` §2 V8/V9/V10/V11 posture 行（翻转机制 + 首挂锚）；
  `policies/ci-gates.md` §4 双向交叉引用 + V11 豁免补记；本 INTAKE/PLAN 落盘。
- 不包含：**改 `.github/workflows/ci.yml`**（零接触）；**翻转任何 gate 姿态**（→ 本切片
  **不触发** `ci-blocking-gate-toggle`）；P4 本体（修 warning 期漂移 / 补 clean-clone + 负向
  证据 / 删重复规则与失效统计 / 删无引用 adapter）；S3 任一组件；#312 其余三项独立拍板议题
  （含 settings biz-allow 收窄）；harness / fixtures（零接触，冻结锚 `b1973a9` 仅记录）。

## 4 判定口径设计（D1–D4 落文，Owner 已拍板）

新增 **§11.2 「P4 blocking 门判定口径」**，四小节对位四项拍板；§11.1:324 收口为一行指针
（保留 14 日 / 20 次 / 零 waiver 三判据原文，翻转动作改指 §11.2）。

| 小节 | 拍板 | 落文要点 |
|---|---|---|
| (1) 翻转动作 = 双轴分离 | D1（+ 2026-07-16 重确认） | 表格分列 blocking 轴（`continue-on-error: true→false`，V8/V9/V10）与阈值轴（`--fail-on error→warning`，**V8 + V9**——V8 改现有旗标值 / V9 **新增**旗标；**V10/V11 无此轴**）；明写「仅改阈值轴不产生 blocking」及其 `ci.yml:311-313` 依据；明写**两轴适用面按脚本而非按 gate 划分**及 V9 易错点（勿据 CI 命令行无旗标误判）；两轴均属 P4；每 gate 独立 `ci-blocking-gate-toggle` 拍板 + 执行记录；V11 不适用（day-1 blocking per D-016） |
| (2) 起点锚 = 各 gate CI 首挂 commit | D2 | 逐 gate 实测锚表（V8/V9 `42037bd` 2026-07-14 09:28 #320；V10 `36d185d` 2026-07-14 11:39 #326；V11 `b8f43d3` 2026-07-14 17:08 #330 不适用）；批量翻转受**最年轻 gate** 约束 → 最早资格 **2026-07-28**；附注三者同日 → 本轮「最年轻」与「最早」同解、规则代价为零，规则仍按 gate 计以约束将来新挂 gate；**附核验命令陷阱**：step **名**在 S2 #330 变更过，pickaxe 须用 **run 命令片段**否则误指 #330 |
| (3) 20-CI 度量口径 | D3 | 计数域 = `ci.yml` 全部 run（任意分支）**按 head SHA 去重**（push+pull_request 一对只计一次）；计数条件 = 被观察 gate 的 step 输出 clean（step output 是 SoT，per `ci.yml:292`）；streak **仅**因该 gate step 非 clean 重置，无关 job 失败/flake 不重置但须登记；给出可复跑 `gh run list` 度量命令，其输出即翻转证据 |
| (4) 与 `ci-gates.md` §4 的关系 | D4 | **吸收时序、保留产物**：14 日窗口是 1 周 dry-run 真超集 → 时序吸收，不另跑；`evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（violation 数 + 影响范围）**仍须产出**，正是 (3) 所需计数工件；V11 day-1 blocking 未走该 dry-run = D-016 明确豁免，非疏漏，执行记录 #330 comment |

## 5 Work Breakdown（1 PR，`documentation/341-p4-gate-definition`）

| # | 文件 | 动作 | AC |
|---|---|---|---|
| W1 | `plans/[PLAN]_dual-agent-compat.md` §11.1:324 | 收口为指针行（保三判据，翻转动作改指 §11.2） | AC-1 |
| W2 | `plans/[PLAN]_dual-agent-compat.md` 新增 §11.2 | 四小节全文（§4 设计） | AC-1/2/3/4 |
| W3 | `plans/[PLAN]_dual-agent-compat.md` §18 D-009 | 改写为双轴表述 + 指 §11.2 | AC-1 |
| W4 | `plans/[PLAN]_dual-agent-compat.md` §18 D-016 | 补记 MCP 面「不设观察期」同时是 `ci-gates.md` §4:41 的明确豁免 | AC-5 |
| W5 | `plans/[PLAN]_dual-agent-compat.md` frontmatter | `updated: 2026-07-13 → 2026-07-15`（正文改动顺带修正既有过期） | — |
| W6 | `sdd/gates.md` §2 V8/V9/V10/V11 行 | 各行补**翻转机制** + **首挂锚 commit**；V11 行补豁免指针 | AC-6 |
| W7 | `policies/ci-gates.md` §4 | :41 行补指向 plan §11.2 的交叉引用（时序吸收 / 产物保留）+ V11 豁免补记 | AC-4/5 |
| W8 | `plans/[INTAKE]_*` + `plans/[PLAN]_*`（本 2 件） | 落盘 | — |

## 6 Verification

- **Level A（read-only，全部本地跑）**
  - `uv run python scripts/check_frontmatter.py` · `uv run python scripts/check_wikilinks.py`
  - `uv run python scripts/sdd/check_development_agent.py --all --fail-on error`（V8）
  - `uv run python scripts/sdd/check_agents_projection.py --all`（V9）
  - `uv run python scripts/sdd/agents_sync.py --check`（V10+V11；本地裸 check 双面全查）
  - `uv run pytest tests/unit tests/eval`（clean worktree → 无 #298 本机 `.env` 2 假红）
- **AC-8 自证 grep**：`plan` / `gates.md` / `ci.yml` 注释三处对翻转机制的表述一致，且无残留
  「翻转 = 仅改 `--fail-on`」口径。
- **Level B**：无（不改 CI、不翻 gate、无 side-effect 动作）。
- **大闭幕**：5-lens 对抗审查（P3 教训：该审查在 P3 逮出 3 真洞）——重点验 §11.2 每条数字/
  commit/行号可回溯到实测，无凭空断言。

## 7 Risks / Anti-goals

- **不放宽任何门**。D1 净效果是让 P4 翻转**真正生效**（严于原字面）；D2/D3 是把空定义补实；
  D4 保留产物义务。任何把本切片读成"给 P4 减负"的表述都是误读，须在 PR body 明确。
- **不得顺手翻 gate**。姿态变更是独立 `ci-blocking-gate-toggle` 拍板，且日历腿未满（1/14）。
- **不得改 `ci.yml`**。`ci.yml:286-296` 的注释块目前**比 plan 更准**（已自陈 V10/V11 无
  `--fail-on`）；本切片让 plan 向 ci.yml 对齐，而非反向。若 AC-8 grep 发现 ci.yml 注释亦需
  改口径 → **升档为 maintain 类型 + 重新评估**，不在本 documentation 切片内静默改 CI 文件。
- **D2 的锚是实测值**，非从 memory 抄。memory 记「V10 首挂 2026-07-14 #326」为真，但其依据是
  `agents_sync.py` 脚本首次提交；本切片的锚重新以 **ci.yml 内 step 的首次出现**核实
  （`-S "agents_sync.py --check" -- .github/workflows/ci.yml` → `36d185d`），二者恰好同一 commit，
  但**理由不同且后者才是正确判据**（脚本可先于 step 落地）。此区分写进 §11.2(2) 的核验命令注。

## 8 Owner Gates

- Gate 5（Stage 5）：本 PLAN + Intake 拍板（D1–D4 已于 Stage 0 拍定，此处仅复核落文忠实度）
- Gate 13（Stage 13）：commit / push / PR 创建逐次拍板
- Merge：交 Owner 执行（classifier 拦 agent 直合 develop）+ `--delete-branch` + 合并确认用
  `gh pr view --json state` **独立验证**（不与清理串同一命令）+ merge 后 origin/gitee 手动双清

## 9 Next Step

Stage 8 实施（W1–W8）→ Stage 10 验证 → Stage 11 自评 + 5-lens 对抗审查 → Gate 13 PR →
交 Owner 合并 → merge 后 Intake/PLAN state flip completed（Rule 12）+ #341 勾 AC + #312 备注
（P4 门定义已硬化，本体待 ~07-28）。
