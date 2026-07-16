---
type: intake
summary: 双工具兼容 v5 第十执行切片（#312 P4 等待期填充）的 Stage 0 Intake 落盘——F(policies/ci-gates.md ADR-034 同步 :67/:68/:88/:38) + A(补跑逾期 2026-Q3 A6 审计 + SCHEMA 推导规则 + M-FU 补注册)；documentation/Medium/1 PR；对应 issue #347（总锚 #312）；4 项 Owner 拍板（锚 F+A / D1 快照面=23 / F 范围四行 / D3 改推导规则）+ Stage 0 核查对 brief 多处失真的更正
owner: ranzuozhou
created: 2026-07-16
updated: 2026-07-16
state: active
track: shared
---

# [INTAKE] 双工具兼容 v5 — ci-gates ADR-034 同步 + Q3 审计补跑切片（issue #347）

> Stage 0 输出于 2026-07-16 会话内产生并当日落盘（worktree 内，保 develop 干净）；触发 §2.1
> 落盘判定（HITL 点 ≥ 3〔锚拍板 + D1 拍板 + F 范围/D3 拍板 + commit/push/PR〕 + 治理面
> 〔A13 = PR 阻塞 ruleset〕变更）。
> 上游输入：总锚 #312「P4 观察期」等待窗口（P4 最早资格 2026-07-28，见 §5）+ 前序 #344 保留项
> 判据对 2026-Q4 审计的依赖（`plans/[PLAN]_dual-agent-compat_settings-narrow.md:83`）。
> 前序全闭环：P0/P1/S0/S1/S2/P2/P3 + settings 收窄切片 #344（PR #345 `07e1be6` + flip #346 `a576eea`）。

## 1 Task Classification

- Type: **documentation**（policies + evidence + schema + plans；非代码行为、非 config 面）
- Base branch: develop @ `a576eea`；G1 worktree `documentation/347-a6q3-cigates-sync`
- 影响范围：`policies/ci-gates.md`（4 行）· `evidence/ai-context-audit/{2026-Q3.md 新建,SCHEMA.md}`
  · `plans/` 4 件〔本 INTAKE + PLAN + 2 M-FU〕· `CHANGELOG.md`。**不触** `src/mj_agent/**`、
  `.claude/settings.json`（只改**描述**该文件的文档，不动文件本身）、`.mcp.json`、
  `sdd/development-agent.yml`、任何 gate 脚本、任何 CI gate 姿态。
- 仓外产物：无（vault fact-verify 工作流为 Stage 0 内部核查，不入仓）

## 2 锚选定（Step 1）

Owner 拍板锚 = **F+A 组合**（AskUserQuestion 确认，2026-07-16）—— 非「仅 A」/ 非 C（S3a
doctor）/ 非 B（pg-default）/ 非 E（ssh-manager）/ 非 D（P4 本体）。

**排序依赖（F 必先于 A，非任意捆绑）**：`policies/ci-gates.md:38` 令 A6 季度审计的检查对象 =
「`permissions.deny` 红线列表」，而该红线由 `:67` 定义为「4 项必停文件 + secrets.enc」。
ADR-034 已把 5 必停面由 `deny` 移到 `ask`——若不先修 F，A（= 本次 A6 审计）就会**按已退休的
定义建基线**，Q3 快照与真实覆盖面自相矛盾。故 F 先修定义、A 后按修正后定义审计。

**各候选出局系实测核实，非援引 brief**（详 §3 失真更正）：

| 候选 | 出局/降级理由（实测） |
|---|---|
| **D（P4 本体）** | §11.1 逐字「同时满足」= AND：V10 腿 **14/20**（绑定腿）、日历腿 **2026-07-28** 未到 → 今日结构性不合格 |
| **C（S3a doctor）** | brief 称「4 处设计未决」，实核其唯一 *blocking* 未决为**假**：`DA059` 不存在（grep scripts/ tests/ 零命中）、`test_real_tree_v8_all_passes:135-136` 是第二道 blocking 执行者 → 比 brief ready，但写 `agents_sync.py` 代码面且 S3 另一半受观察期约束 |
| **B（pg-default）** | 需 Owner 先拍 A/B；且**范围比 brief 大**：10 pg server 的 `env` 均为 `{}`，args-only 传名会投影出 Codex 取不到值的坏配置 → 须 args+env 双改 ≈20 处 |
| **E（ssh-manager）** | 范围已由 #341 §7 拍板项 6 归入 #312 议题 2「一并拍」；且「两个宽面」为**假**（实测 9 条无退出判据的宽 allow） |

## 3 Stage 0 核查产出——brief 多处失真更正

> 承 `feedback_wrong_premise_voids_decision` + brief 自身「数字过期即须重测」告诫；Stage 0 用
> fact-verify 工作流（10 agent，含对抗 refute 腿）+ 亲手复核。以下均 `file:line` 溯源，留档不覆盖。

| # | brief 断言 | 实测更正 | 证据 |
|---|---|---|---|
| F1 | 「A 最 ready，机械活」 | **非机械**：`SCHEMA.md` 自身构成规则已腿（`:42-44` 写「6 infra」但盘上 8 冻结；写「3 runtime」但盘上 9）；Q2 列表仍含已重命名的 `infra/docker/CLAUDE.md`。D1 快照面 15/17/22/23 是 Owner 决策 | `evidence/ai-context-audit/SCHEMA.md:42-44` vs `ls .claude/skills/mj-agent-infra-*` = 8 |
| F2 | 「C：4 处设计未决」 | C 唯一 blocking 未决为假：`DA059` 不存在 | `grep -rn DA059 scripts/ tests/` = 0 命中；实际是 `DA060`（`check_development_agent.py:419,424`） |
| F3 | （brief 二.1）「`${` guard 在 `:262-268`」 | 属实，本切片不涉；但顺带核实 fact-verify 复现无误 | `agents_sync.py:263` `if "${" in arg` |
| F4 | 「E：仅存两个宽面之一」 | **假**：settings.json allow 有 **9** 条无退出判据的宽 `mcp__*__*`（github/serena/memory×5/playwright/ssh-manager） | `.claude/settings.json` allow 枚举 |
| F5 | 「P4 最早 07-28，V8/V9 20-run 已达标易误判可动」 | 属实且**关键**：绑定腿是 V10（**14/20**），非 V8/V9（20/20）；日历腿 AND → 07-28 前不合格 | `gh run list` 实测 2026-07-16 |
| F6 | 「D1 快照面」未在 brief 出现 | 新发现：SCHEMA「15-surface」硬编码已与磁盘 23 面脱节 → 升为独立 Owner 决策 | 本 INTAKE §7 D1 |

## 4 Risk Assessment

- Level: **Medium**（governance 描述面正确性；A13 = PR 阻塞 ruleset，改其引用需 lockstep）
- Triggered §3.1 必停项：**无 mj-agent 专属 4 项**——本切片不改 guardrail/precheck/system.md/
  SKILL body/qcm_catalog。通用必停 6（生产/CI/部署）**不触**：改的是**描述** CI gate 的文档，
  非 gate 姿态本身（无 `ci-blocking-gate-toggle`）。
- 特殊风险：`evidence/` 在 frontmatter SCAN_ROOTS 外 → **须手动核验**（`reference_mj_agent_vault`）；
  write-once evidence 纪律（`2026-Q2.md` 不得回改）；hash 算法坑（`reference_infra_skill_freeze_hash`：
  `body_section_heads` NAIVE 扫）——本切片已**先复现 Q2 既有 hash** 证明算法实现正确。
- 方向 = **修正/收敛**，非 permission widening → agent 可 commit。

## 5 环境事实（2026-07-16 Intake 核验）

- develop @ `a576eea`，clean，单 worktree（+ 本切片新建 `documentation/347-*`）。
- **P4 两腿实测**：V10 腿（锚 `36d185d` 2026-07-14T03:39:45Z）= **14**；V8/V9 腿（锚 `42037bd`
  2026-07-14T01:29:00Z）= **20**。日历腿 = 2026-07-28（三 gate 同日首挂 07-14；§11.1 AND）。
  → **P4 今日结构性出局**。
- gitee/develop @ `7d36fb2` 落后 origin **21 commits / 10 merges**（扩大中；留 §9 交办）。
- `~/.claude/projects/` transcripts：36 目录；E1 精确 pattern = 2 / 裸名 = 1136。

## 6 Documentation Decision（粗评）

- Plan: **Create**（本 INTAKE 的成对 PLAN）
- ADR: None（无难逆决策新增；引用既有 ADR-034/032）
- 其他: evidence 新建 `2026-Q3.md` + 2 M-FU plan（`state: completed`/`active`）+ CHANGELOG 条目

## 7 Owner 拍板记录（2026-07-16，AskUserQuestion；写进选项的事实均 file:line 溯源）

| # | 决策 | 结论 | 备选（未选） |
|---|---|---|---|
| 1 | **锚** | **F+A 组合** | 仅 A / C(S3a doctor) / B(pg-default) |
| 2 | **D1 快照面** | **23**（5 CLAUDE.md + 9 runtime SKILL.md + system.md + 8 infra）[^d1] | 22（`_ACTIVE_SKILLS`）/ 17[^17] / 15（Q2 原集） |
| 3 | **F 范围** | **`:67`+`:68`+`:88`+`:38`** | `:67`+`:68`+`:88` / `:68` only |
| 4 | **D3 SCHEMA** | **改成推导规则**（数量降为观测值） | 只更新硬编码数字 / 不改仅记 finding |

[^d1]: **标签精化（Stage 11 对抗审查逮出，2026-07-16）**：D1 选项原标「门所护之面」，严格讲 `ask`
    门所护的**全部** 5 类面 = **26**（另含 3 个**非-markdown** 必停面 `guardrail.py`/`precheck.py`/
    `qcm_catalog.yaml`）。但 D1 四选项（15/17/22/23）**枚举逐字均为 markdown 面**，`.py`/`.yaml` 3 面
    **从未在任一选项内** → Owner 的具体选择（23 个枚举文件）**不受影响**、动作面**不扩**；26 非可选项且
    技术上非可行（regex-strip-frontmatter 算法不适用 `.py`/`.yaml`）。故精化 = 把标签从「门所护之面」
    改为「ask 门所护的 **markdown/AI-context 面**」，并在 `SCHEMA.md §2.1` 的必停轨规则加 `.md` 过滤器
    使其可机械推导出 23（详 `2026-Q3.md` §5.3）。此为**规则措辞更正以匹配已拍板的集合**，非决策反转。

[^17]: 「17」= 决策时把 `SCHEMA.md` 旧规则（「3 runtime + infra」）照搬到当时磁盘（infra 已 8）=
    5 CLAUDE.md + 3 runtime + system.md + 8 infra。系**决策时**的历史推算值；终态 §2.1 规则（markdown 口径）
    产出 23，与此无关。

### 7.1 D5 由读代码解决（非 Owner 问题）

fact-verify 提出「D5：Q3 是否记 E1/E2 锚点」。实核为**非开放问题**：
`plans/[PLAN]_dual-agent-compat_settings-narrow.md:83` 逐字「它须记录本切片的 E1/E2 锚点值」
→ 是**要求**、非选择。故 Q3 §7 直接落 E1/E2，不占 Owner 拍板额度。

### 7.2 拍板前提溯源

D1 选 23 的锚点事实（写进选项）：`Edit(./src/mj_agent/skills/**/SKILL.md)` ask glob 实测命中
**9** 个 SKILL.md、contract 头逐字「freezes **8**」、`git ls-files` 命中 **5** 个 CLAUDE.md ——
均现场 `file:line` 核验，非从 brief/memory 推断。

## 8 Verification Plan

- Level A（只读）：`uv run pytest tests/unit tests/eval` · `ruff` · `mypy` ·
  `check_frontmatter.py --all` · `check_wikilinks.py` · `check_claude_skill_contracts.py --all` ·
  `check_development_agent.py --all` · `check_agents_projection.py --all`
- Level B（有副作用）：无（docs/evidence-only）
- hash 自证：**先复现 Q2 既有 hash**（4 面逐字复现 → 证明实现即 canonical 算法）再算新面

## 9 交办事项（本切片范围外，登记以免丢失）

- **gitee 落后扩大**：origin `a576eea` vs gitee `7d36fb2` = 21 commits / 10 merges；
  若非有意镜像节奏，Owner `git push gitee develop`（gitee 偶发 TLS 握手失败，重试即可）。
- **`origin/bugfix/119`**：PR #120 CLOSED 未合、issue #119 OPEN，是该修复唯一副本；留弃 = Owner 决策。
- **容器目录空遗留**：`mj-agent/{documentation,maintain}/` 下 `research-mj-agent`/
  `fix-doctor-mcp-env-warnings` 两空目录，无 `.git`、未注册 worktree → 无害未删。
- **`policies/security.md:72` ADR-034 stale gloss（Stage 11 对抗审查补登）**：该行
  `- policies/ci-gates.md §Settings 边界 — permissions.deny 红线列表` 是**指针**，本身**不**复述
  「4 项必停文件」断言（故仍在本切片 F 范围之外），但其 gloss「`permissions.deny` 红线列表」在
  ci-gates §5 改为 `deny ∪ ask` 后**变陈**。**未在本 PR 改**（越出 Owner 已拍板的 4 行 F 范围 =
  避免 scope drift）；登记为 ADR-034 同步 follow-up，Owner 可决定并入本 PR 或另起。
  （`sdd/adapters/claude-code-skill.md:71` 经复核只复述 A13 的 secret-pattern 半边，**仍准确**，不涉。）
- **#312 议题 1/2/3 + S3 + P4**：本切片均不涉，续切片候选。

## 10 Next Step

- 已过 HITL Gate（4 项拍板）→ 已建 issue #347 + worktree（Stage 1/2 完成）
- 实施完成后：full-suite verify + 5-lens 对抗审查 → Owner-gated commit/push/PR
- merge 后独立小 PR flip 本 INTAKE + PLAN `state: completed` + 加 `completed:` 字段
