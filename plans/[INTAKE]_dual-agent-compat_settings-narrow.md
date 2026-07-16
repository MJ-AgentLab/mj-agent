---
type: intake
summary: 双工具兼容 v5 第九执行切片（#312 递延议题 4 实施 = settings biz allow prod 面收窄 A′ + 保留项退出判据；议题 3 = pg 凭据 default 单一真相仅备料）的 Stage 0 Intake 落盘——maintain/Medium/1 PR（#345 `07e1be6`）；3 项 Owner 拍板（锚 = A′+pg-default 评估 / 保留项判据一并定 / 判据窗口 Q3→Q4 前提更正后重确认，§7.2）+ brief 三处失真更正（§3）；对应 issue #344（总锚 #312）
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
completed: 2026-07-16
state: completed
track: shared
---

# [INTAKE] 双工具兼容 v5 — settings biz allow 收窄切片（issue #344）

> Stage 0 输出于 2026-07-16 会话内产生并当日落盘（worktree 内）；触发 §2.1 落盘判定
> （HITL 点≥3〔锚拍板 + 判据拍板 + commit/push/PR〕 + 治理面〔protected path `.claude/**`〕变更）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §11.2（P4 判定口径，#341）+ 总锚 #312「独立拍板议题」
> 4 项；前序：P0/P1/S0/S1/S2/P2/P3 全闭环，P4 门定义硬化切片 #341 closed（PR #342 `d7bf7b3` +
> flip #343 `2d0c4e3`）。
> Vault 拍板依据：`[ASSESSMENT]_settings-biz-allow-narrowing-2026-07-14.md`（S2 #330 AC10 产物）。

## 1 Task Classification

- Type: **maintain**（`.claude/` 配置面；非代码行为、非纯文档）
- Base branch: develop @ `2d0c4e3`；G1 worktree `maintain/344-settings-biz-allow-narrow`
- 影响范围：`.claude/settings.json`（删 2 行）· `CHANGELOG.md`（`[Unreleased]` 条目）·
  `plans/` 2 件〔本文件 + PLAN〕。**不触** `src/mj_agent/**`、`.mcp.json`、
  `sdd/development-agent.yml`、`.github/workflows/**`、任何 gate 脚本。
- 仓外产物：vault pg-default 评估（不入仓，per §7 落点纪律）

## 2 锚选定（Step 1）

Owner 拍板锚 = **A′ + pg-default 评估**（AskUserQuestion 确认，2026-07-16）——非「仅 A′ 收窄」/
非「仅 pg-default 评估」/ 非「S3a doctor 只读版」/ 非「P4 本体」。

**P4 本体出局系实测核实，非援引 brief**：

| 判据（`plan` §11.2） | 要求 | 实测值 | 证据 |
|---|---|---|---|
| 观察期自然日 | ≥14 | **2 / 14**（07-14 → 07-16） | 锚 = V10 CI 首挂 `36d185d` 2026-07-14 |
| 20 次连续 CI（**按 head SHA 去重**） | ≥20 | **12**（V10 腿，绑定）/ 18（V8/V9 腿） | `gh run list --workflow ci.yml --limit 100 --json createdAt,headSha --jq '[.[] \| select(.createdAt >= "2026-07-14T03:39:45Z")] \| map(.headSha[0:8]) \| unique \| length'` |
| 判据连接词 | **AND**（`plan:324` 逐字「同时满足」） | 两腿均未达 | — |

→ **最早资格仍为 2026-07-28**（受最年轻 gate V10 约束，per §11.2(2)）。

## 3 Stage 0 核查产出——brief 三处失真更正

按「先核实事实再信 brief」纪律，本切片 brief 的可溯断言全部经 file:line 复核；三处为假：

| # | brief 断言 | 实测事实 | 证据 |
|---|---|---|---|
| F1 | 「自 07-14 锚点起 …按 ③ 去重后仅约 **9 个 distinct SHA**」 | **12**（V10 腿）/ **18**（V8/V9 腿） | 上表 `gh run list` 命令 |
| F2 | 「日历腿 07-28 到期时 20-run 腿**大概率未达标** → 日历腿可能不是绑定约束」 | **恰相反：日历腿绑定**。累积速率实测 07-14=5 / 07-15=5 / 07-16=2 distinct SHA·日⁻¹；余 8 个 SHA ≈ 2 个活跃工作日 ≪ 12 个日历日。且 `ci.yml` **不在 merge-to-develop 上触发**（`on.push.branches` 仅 5 类分支前缀 + `on.pull_request` 仅 main/develop）→ 计数随工作分支提交累积 | `gh run list ... \| group_by(.createdAt[0:10])`；`.github/workflows/ci.yml:3-12` |
| F3 | 「`agents_sync.py:265-271` 对 args 中任何 `${` fail-close」 | 行号错：实为 **`agents_sync.py:262-268`**；`:269-273` 是**另一道独立 guard**（`_ARG_USERINFO`，URL userinfo 凭据形状，正则定义在 `:87`）。**行为本身属实**（`if "${" in arg` 无条件 `raise FatalCheckError`） | `scripts/sdd/agents_sync.py:262-268` / `:269-273` / `:87` |

> **F3 溯源**：该错误行号系承自 [[[INTAKE]_dual-agent-compat_p4-gate-definition|P4 门定义切片 INTAKE]]
> §9 交办事项第 4 条（`:113`）。按家族惯例**不改写已 completed 切片的记录**，故在此更正、不回改；
> 后续引用以本节为准。

**brief 未提及、但对议题 3 结论有实质影响的事实（F4）**：该 `${` guard 今日对 memory×5
**dormant** —— `agents_sync.py:237` 仅遍历 `mcp_project`，而 `mcp_project` 只收
`policy == "project"`（`check_agents_projection.py:137`）；memory×5 现为 `project-with-adr`
（`sdd/development-agent.yml:731-735`）→ guard **一经 promotion 方触发**。故「memory×5 硬依赖
pg-default 先决」**成立但条件化**：它不是今日的活故障，而是 promotion 的前置闸。

## 4 Risk Assessment

- Level: **Medium**
- Triggered §3.1 必停项：**无**（不触 guardrail/precheck/system.md/SKILL.md body/qcm_catalog 4 项）
- Protected path `.claude/**`：交互模式写入必弹权限 prompt（= 拍板，`allow` 不可抑制）。
  **方向为收窄** → classifier 不硬拦，AI 可改 + commit（放宽才拦，per 2026-06-20 PR #258 口径）
- A13 **适用**（`.claude/settings.json` allowlist diff 须走 PR 合并审查）；A14 不适用（不动
  `.mcp.json`）；D-017 不适用（不动 manifest `mcp`/`codex.posture`）；`ci-blocking-gate-toggle`
  不适用（不改 gate 姿态）
- **数据边界方向为收紧**（ADR-006/009/000 不变）：prod 面由免 prompt 自动放行 → 弹 prompt
- Gated actions：commit/push/PR 逐次拍板；merge 交 Owner（classifier 拦 agent 直合 develop）

## 5 环境事实（2026-07-16 Intake 核验）

- develop @ `2d0c4e3`（与 brief 一致）；worktree 仅 `develop`（brief 一致）
- origin 分支：`develop` / `main` / `bugfix/119-env-example-ascii-only`（brief 称「只剩 develop/main/bugfix/119」属实）
- gitee/develop @ `7d36fb2`，**落后 origin/develop 5 个 merge**（brief 一致；Owner 本轮不追平）
- `.claude/settings.json` `permissions.allow` = **26 条**（`:5-30`）；`deny` = 9（`:33-41`）；`ask` = 5（`:44-48`）
  → 收窄后 allow = **24**，biz 子集 5 → 3
- 目标两行实读：`:25` `"mcp__pg-mj-system-biz-prod-lan__*",` · `:26` `"mcp__pg-mj-system-biz-prod-wan__*",`
- 保留三行实读：`:22` biz-dev · `:23` biz-test-lan · `:24` biz-test-wan
- `:27` `"mcp__ssh-manager__*"` = **单条通配**，覆盖 ssh-manager 全部工具（含
  `ssh_execute_sudo` / `ssh_db_import` / `ssh_deploy` 写面），`deny` 无兜底 → 本切片**不动**（见 §7）
- **零自动依赖**（决定性负向事实）：`grep -rn "settings\.json" scripts/ .github/workflows/` = 0 hits；
  仓内无任何 `.py` 读 `.claude/settings.json`。`check_development_agent.py:71-72` 命中 biz-prod 名
  系 `MCP_FORCED_NEVER` 硬编码常量（对 `.mcp.json` 名做 never-tier 校验），**同名不同面**，false lead
- 唯一例外（对 verdict 无影响）：`.github/workflows/check-stale-docs.yml:24` path-filter 含
  `.claude/**` → 跑 `scripts/find_stale_docs.py`；但仅 rename/delete 面、恒 exit 0、`continue-on-error: true`

## 6 Documentation Decision（粗评；Stage 3 已细化）

Plan=Create（`plans/[PLAN]_dual-agent-compat_settings-narrow.md`，PR 携带）；
**CHANGELOG=Update**（`[Unreleased]`；依家族先例而非成文规则——`CHANGELOG.md:46`/`:85`/`:123`
三次 settings.json 改动均留条目）；INDEX=None（`plans/` 按 `policies/archive.md:230` +
`sdd/lifecycle.md:73` 不入 INDEX）；SPEC/ADR/RUNBOOK/GUIDE/STANDARD/ISSUE/ASSESSMENT=None。

**不动 `evidence/ai-context-audit/2026-Q2.md:110`**（「`permissions.allow` count: 8」）：该处是
hash 锚定（`:107` `89333565f78cb2a7`）的 Q2 冻结快照，**在本切片之前即已漂移**（实为 26/9），
`SCHEMA.md` §1 定其为 write-once；改它等于污染审计链。Q3 re-baseline 是其正确处置面。

## 7 Owner 拍板记录（2026-07-16）

| # | 决策 | 结果 |
|---|---|---|
| 1 | **锚** | **A′ + pg-default 评估**（AskUserQuestion 确认）。A′ = 实施议题 4；pg-default = 议题 3 **仅备料**，本切片不拍板、不实施。 |
| 2 | **保留项退出判据** | **一并定**——为 `:22-24` dev/test×3 定四要素（窗口 / 指标 / 锚点 / 判定口径）落 plan。理由（Owner 采纳）：#341 的教训正是「自设治理门无可执行口径 → 按字面执行不产生效果」；留 3 条无判据的 allow 会复现同型洞。 |
| 2b | **判据窗口**（首次拍板 2026-07-16） | **复用 2026-Q3 A6 审计**。→ **该拍板已作废**，前提为假；更正与重确认见 §7.2。 |
| 3 | **ssh-manager 行**（承 #341 INTAKE §7 拍板项 6） | **不在本切片**——整体推 #312「ssh-manager wrapper 方案」议题一次拍板。本切片据此只动 2 条 prod biz 行。 |

### 7.1 拍板前提的溯源纪律

本次 AskUserQuestion 选项内的每条事实断言均于**提问前**完成 file:line 核验（allow 26 条 /
`:25-26` 行号 / 零自动依赖 grep / `agents_sync.py:262-268` / canary 集合相等 / doctor 退出码未定义 /
#312 议题 4 项）。**未**从 memory 或 brief 直接抄录未验断言——承
[[[INTAKE]_dual-agent-compat_p4-gate-definition|#341]] §7.1 教训：错误前提下的拍板作废。

**vault Option B ≠ 本切片（须显式区分，防措辞漂移）**：vault 评估 §三 的 B 行字面为
「删 `prod-lan/prod-wan` 2 条 **+ `ssh-manager` 通配**…」——含第三处删除。本切片 = **A′ = B 的
prod 面子集**。二者不矛盾：§四 建议正文自陈 ssh-manager「最终形态（工具子集白名单 vs 全删）
**建议与 #312 wrapper 议题合并一次拍板**」，即 §四 已把 ssh 面递延；A′ 遵循 §四 而非 §三 表格的
打包措辞。权威 scope 锚 = [[[INTAKE]_dual-agent-compat_p4-gate-definition|#341 INTAKE]] `:85`
「将来 A′（settings biz-allow 收窄）**只动 2 条 prod biz 行** → 单次拍板、零耦合」。

### 7.2 判据窗口的前提更正与重确认（2026-07-16）

**留档理由**：拍板 2b 建立在 AI 提供的**两条错误事实**上。按 ADR-034 propose→拍板→apply 纪律 +
[[[INTAKE]_dual-agent-compat_p4-gate-definition|#341]] §7.1 先例，错误前提下的拍板须**带更正后的事实
回 Owner 重确认**，不得由 AI 单方「顺理成章」改写——**尤其当更正后结论扩大动作面时**（本例即是：
更正后需补注册逾期审计 + 拉长窗口）。本节完整留下更正链，**不覆盖原始记录**（原拍板见 §7 行 2b）。

| 项 | 内容 |
|---|---|
| **首次拍板（2026-07-16）** | 判据窗口 = **复用 2026-Q3 A6 审计**。 |
| **AI 当时提供的前提（错误 ×2）** | ① 「Q3 审计 ≈ 2026-10-01，约 2.5 月」；② 「`M-FU-AI-AUDIT-<cycle>` 提醒机制已存在」。 |
| **实测更正（Stage 11 · 5-lens 对抗审查 scope-governance 镜命中）** | ① `evidence/ai-context-audit/2026-Q2.md:145` 逐字：「register `M-FU-AI-AUDIT-2026-Q3` plan **after 2026-06-30** (next quarter boundary)」→ Q3 到期 **2026-07-01**，今日**已逾期 ~15 日**（未及 SCHEMA §3 >30 日 lapse 门槛）。②`plans/` **无** `M-FU-AI-AUDIT-2026-Q3` 文件；全仓该串命中仅「机制引用」（`SCHEMA.md:54` / `ADR-032:109` / `2026-Q2.md:145` / 本切片）→ **Q3 提醒从未注册，机制已静默失效**。 |
| **失效后果** | 锚 Q3 = 关闭事件**已过** → 判据以**零观察**触发，默认删除它本要观察的三条 —— **与 #341 同型**（自设门按字面执行不产生预期效果）。且判据被锚在一个**当下已失效**的机制上。 |
| **重确认（2026-07-16）** | Owner 在**更正后的前提**下重新拍板：**改锚 2026-Q4 A6 审计**（到期 ≈ 2026-10-01，真实观察期 ≈ 2.5 月 —— 即 AI 上次**误描述为 Q3** 的那个时点）。逾期的 Q3 审计改任**基线快照记录者**（非窗口关闭者）。 |
| **影响（动作面扩大，已由本次重确认明示授权）** | (1) 窗口由「已关闭」变为 ≈2.5 月真实观察；(2) 新增 W6：登记补注册 `M-FU-AI-AUDIT-2026-Q3`（逾期）+ `-2026-Q4`（判据关闭者）；(3) **残余风险 Owner 明示接受**：A6 提醒已实证会失效，若 Q4 亦失效则判据永不触发——已写入 PLAN §4 与 §9 风险表，不藏。 |
| **发现路径** | 本切片 Stage 11 **5-lens 对抗审查**（raised 36 / survived 4）——scope-governance 镜独立命中，adversarial refuter 未能驳倒。**又一次由自评逮到作者本人的设计错误**（承 #341 同款价值）。 |

## 8 Verification Plan

- Level A（read-only）：`check_frontmatter.py` · `check_wikilinks.py` ·
  `check_development_agent.py --all`（V8）· `check_agents_projection.py --all`（V9）·
  `agents_sync.py --check --surface skills`（V10）· `--surface mcp`（V11）·
  `pytest tests/unit tests/eval`（clean worktree 无 #298 假红）· `ruff check` · `mypy src/mj_agent`
- Level A（自证）：AC-1/2/3/4/5 grep + JSON 解析（见 PLAN §验收）——**AC-5 在 PR 内重跑**
  「零自动依赖」grep，不承袭 Intake 结论
- Level B：无（本切片不跑 side-effect 动作；不改 CI、不翻 gate、不动容器）

## 9 交办事项（本切片范围外，登记以免丢失）

1. **#312 comment 数字失真**（2026-07-16 本人所发）：「~9 distinct SHAs」「20-run 腿可能先绑定」
   → 实测 12（V10）/ 18（V8/V9），且**日历腿绑定**。本切片 In-scope 第 4 项即更正此帖（AC-8）。
2. **`origin/bugfix/119-env-example-ascii-only` 不可当垃圾清**：PR #120 CLOSED 未合、issue #119
   OPEN；落后 develop 459 commits，复活需重做。是留是弃 = Owner 决策。（承 #341 §9-2，仍未决）
3. **gitee/develop 落后 origin 5 个 merge**（`7d36fb2` vs `2d0c4e3`）——若为有意镜像节奏则忽略。
4. **`policies/ci-gates.md:67-68` 描述不精**：该表把 `permissions.allow` 归属
   `settings.local.json`，而 `settings.json` 自 P0 #316 起实持 26 条 allow（含 6 条 Bash 前缀）。
   **先于本切片存在、与本切片正交** → 不折入（防 scope drift），登记待议。
5. **`evidence/ai-context-audit/` Q3 re-baseline —— 已逾期，且提醒从未注册**（W6 登记；与 PLAN §4 互引）：
   - 2026-Q2 快照（allow 8 / deny 6 / sha16 `89333565f78cb2a7`）相对实况（26→24 / 9 /
     `725012a3ef6aeee8`）已大幅漂移；write-once **不得改旧帖**，正确处置 = 出 Q3 新帖。
   - **Q3 到期 2026-07-01**（`2026-Q2.md:145`），今日**逾期 ~15 日**；`M-FU-AI-AUDIT-2026-Q3`
     **从未注册** → A6 提醒机制**已静默失效**（SCHEMA §1 用以反对 cron 的理由，在手工机制上同样发生）。
   - **本切片依赖它**：Q3 审计 = 退出判据的**基线快照记录者**；**Q4 审计 = 判据关闭者**（PLAN §4）。
   - 非本切片实施（A6 审计是独立产物，折入会撑大切片）→ 登记 M-FU：补注册 Q3 + Q4 提醒并补跑 Q3。
6. **#312 议题 3（pg-default）拍板**：本切片仅出 vault 评估；拍板与实施另起切片。议题 1
   （memory×5）依赖其先决（见 §3 F4）。

## 10 Next Step

Stage 4 计划落盘（本 worktree）→ Gate 5 拍板 → Stage 8 实施（settings 删 2 行 + CHANGELOG +
plan 判据节 + vault 评估）→ Stage 10/11 验证/自评（含 5-lens 对抗审查）→ Gate 13 PR → 交 Owner
合并。merge 后本文件 state flip completed（Rule 12）+ #312 议题 4 复选框勾选。
