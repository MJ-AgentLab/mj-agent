---
type: intake
summary: 双工具兼容 v5 第十执行切片（#312 独立拍板议题 2 = ssh-manager settings allow 收窄）的 Stage 0 Intake 落盘——maintain/Medium/预计 1 PR；收窄 .claude/settings.json 单条 mcp__ssh-manager__* allow 通配（覆盖 37 工具含 ssh_execute_sudo/ssh_deploy/ssh_db_import 等写面，deny 无兜底）；「wrapper 方案」经 Owner 拍板读作 settings allow-list 收窄（非自建 proxy）；收窄口径（A 全删 / B 子集白名单 / C 全删+deny-floor）留 Gate 5 拍板；对应 issue #356（总锚 #312）
owner: ranzuozhou
created: 2026-07-17
updated: 2026-07-17
state: active
track: shared
---

# [INTAKE] 双工具兼容 v5 — ssh-manager settings allow 收窄切片（issue #356）

> Stage 0 输出于 2026-07-17 会话内产生并当日落盘（worktree 内，保 develop 干净）；触发 §2.1 落盘判定
> （HITL 点 ≥3〔scope-interpretation 拍板 + Gate-5 收窄口径拍板 + commit/push/PR〕 + 治理面
> 〔protected path `.claude/**`〕变更）。
> 上游输入：总锚 [[[PLAN]_dual-agent-compat|v5 计划]] §17「独立拍板议题」第 2 项（ssh-manager wrapper 方案）；
> scope 由 [[[INTAKE]_dual-agent-compat_p4-gate-definition|#341 INTAKE]] §7 拍板项 6 +
> [[[INTAKE]_dual-agent-compat_settings-narrow|#344 settings-narrow]] §7 拍板项 3 归入本 issue。
> 前序：P0/P1/S0/S1/S2/P2/P3 + 议题 1/3/4（memory×5 / pg-default / settings biz 收窄）全闭环，
> develop @ `0dab463`。
> Vault 依据：`[ASSESSMENT]_settings-biz-allow-narrowing-2026-07-14.md` §四（ssh 最终形态框定）。

## 1 Task Classification

- Type: **maintain**（`.claude/` 配置面；非代码行为、非纯文档）——与 #344 同类
- Base branch: develop @ `0dab463`；G1 worktree `maintain/356-ssh-manager-allow-narrow`（已建 @ `0dab463`）
- 影响范围：`.claude/settings.json`（allow 收窄，口径待 Gate 5）· `CHANGELOG.md`（`[Unreleased]` 条目）·
  `plans/` 2 件〔本文件 + PLAN〕。**不触** `src/mj_agent/**`、`.mcp.json`、`sdd/development-agent.yml`、
  `.github/workflows/**`、任何 gate 脚本、`.agents/**`、`.codex/**`。

## 2 锚选定（Step 1）+ scope-interpretation 拍板（2026-07-17）

Owner 拍板锚 = **建专属 issue + worktree → 出评估**（AskUserQuestion 确认，2026-07-17）——非「仅出评估文档不建 issue」/
非「自建 proxy-wrapper 更大切片」。

**「wrapper 方案」的 scope 解读（拍板前提，file:line 溯源）**：

| 依据 | 内容 | 溯源 |
|---|---|---|
| 总锚措辞 | §17 仅列「ssh-manager wrapper 方案」为独立拍板议题标签，**未定义**「wrapper」为具体机制 | `plans/[PLAN]_dual-agent-compat.md:315,522` |
| vault 评估框定 | ssh-manager「最终形态（工具子集白名单 vs 全删）建议与 #312 wrapper 议题合并一次拍板」= **settings allow-list 收窄** | vault §四 |
| 仓内无 proxy 机制 | ssh-manager 是直接 `npx @iflow-mcp/mcp-ssh-manager` stdio server（`.mcp.json:112-115`），**不经任何 wrapper 脚本**（区别于 pg-* 的 `pg-server-wrapper.mjs` 凭据 wrapper） | `.mcp.json:112-171` |
| 前序处置 | #341/#344 均把 ssh 行当作「settings.json 一行」递延 | `[INTAKE]_…_settings-narrow.md:112,125-126` |

→ Owner 确认：**「wrapper 方案」= settings allow-list 收窄**，非自建 MCP proxy。若将来确需 proxy（过滤 ssh 工具/主机面），
另立更大切片重新 intake（本切片不预设）。

## 3 影响范围（mj-agent 7 模块 + 跨边界）

- 7 模块：**均不触**（不动 agent/llm/prompt/skill/sql/db/config 任一 `src/` 面）。
- 跨边界：`.claude/settings.json` 是 Claude Code **harness 权限面**——决定会话内 MCP 工具是否免 prompt。
  本切片方向为**收紧**（宽面 → prompt / deny），数据边界 ADR-006/009/000 姿态不变、只更严。
- **零自动依赖**（决定性负向事实，2026-07-17 实测）：全仓无任何 skill/script/src **调用** ssh-manager 工具；
  `grep -rn "mcp__ssh-manager__ssh_\|ssh_execute_sudo(\|ssh_deploy(\|ssh_db_import(" .claude/skills/ .claude/scripts/ scripts/ src/` = **0 命中**。
  唯一功能引用为 `.claude/skills/mj-agent-infra-app-start/SKILL.md:110,315` 的**否定**引用（agent 不驱动 SSH，
  owner 自己终端起隧道，且「ssh-manager tunnel 有 bug——转发即 reset」）。

## 4 Risk Assessment

- Level: **Medium**（与 #344 同）
- Triggered §3.1 必停项：**无**（不触 guardrail/precheck/system.md/SKILL.md body/qcm_catalog 4 项）
- Protected path `.claude/**`：交互模式写入必弹权限 prompt（= 拍板，`allow` 不可抑制）。
  **方向为收窄** → classifier 不硬拦，AI 可改 + commit（放宽才拦，per 2026-06-20 PR #258 口径 REFINE：
  protected paths 交互模式只弹 prompt、`allow` 不可抑制、收窄可 commit）
- A13 **适用**（`.claude/settings.json` allowlist diff 须走 PR 合并审查，`policies/ci-gates.md` §5.1）；
  A14 **不适用**（不动 `.mcp.json`）；D-017 **不适用**（不动 manifest `mcp`/`codex.posture`/`.agents`/`.codex`）；
  `ci-blocking-gate-toggle` **不适用**（不改 gate 姿态）
- **数据边界方向为收紧**（ADR-006/009/000 不变）：ssh-manager 全部工具由免 prompt 自动放行 → 弹 prompt（A/B）
  或 destructive 子集 hard-deny（C）
- Gated actions：commit/push/PR 逐次拍板；merge 交 Owner（classifier 拦 agent 直合 develop）

## 5 环境事实（2026-07-17 Intake 核验）

- develop @ `0dab463`（与 brief 一致）；worktree 仅 `develop` + 本切片新建 `maintain/356-ssh-manager-allow-narrow`
- `.claude/settings.json` `permissions.allow` = **24 条**（`:5-28`，#344 后）；`deny` = 9（`:31-39`）；`ask` = 5（`:42-46`）
- 目标行实读：`:25` `"mcp__ssh-manager__*",` = **单条通配**
- ssh-manager `deny` / `ask` 兜底：**无**（`deny` 仅 rm/Remove-Item/del + .env/secrets×3；`ask` 仅 4 必停面）
- ssh-manager 工具面：本会话 harness 枚举 **37 个** `ssh_*` 工具（vault 2026-07-14 记 38；计数随 MCP server 版本浮动，**非决策载体**）。
  分类见 PLAN §3。
- `.mcp.json:112-171` ssh-manager server def（9-host aggregation，per-host env 密码按名 `${VAR}`）→ 本切片**不动**
- **零自动依赖**：见 §3；PR 内 AC 重跑该 grep（不承袭 Intake 结论）
- ssh-manager Codex 投影：已 `never`-tier（D-013，`sdd/development-agent.yml` mcp 段）→ Codex 侧已封，本切片仅 Claude 侧

## 6 Documentation Decision（粗评；Stage 3/4 已细化）

Plan=Create（`plans/[PLAN]_dual-agent-compat_ssh-manager.md`，PR 携带）；**CHANGELOG=Update**（`[Unreleased]`；
依家族先例——`CHANGELOG.md` 历次 settings.json 改动均留条目）；INDEX=None（`plans/` 不入 INDEX，
`policies/archive.md` + `sdd/lifecycle.md`）；SPEC/ADR/RUNBOOK/GUIDE/STANDARD/ISSUE/ASSESSMENT=None
（评估正文入 PLAN body，非独立 ASSESSMENT 工件——vault 已有 §四 框定，本切片深化其 ssh 面）。

**不动 `evidence/ai-context-audit/`**：Q2 快照是 hash 锚定 write-once 冻结（`SCHEMA.md` §1），Q3 re-baseline
是其正确处置面（承 #344 Intake §9-5，与本切片正交）。

## 7 Owner 拍板记录

| # | 决策 | 结果 |
|---|---|---|
| 1 | **锚 + scope 解读** | **建专属 issue + worktree → 出评估**；「wrapper 方案」= settings allow-list 收窄（非 proxy）。AskUserQuestion 确认 2026-07-17。 |
| 2 | **收窄口径（A/B/C）** | **拍板 = A 全删**（Gate 5，AskUserQuestion 确认 2026-07-17）——删 `settings.json:25` 一行 → allow 24→23、ssh 全部工具弹 prompt；与 #344 biz-prod 同构。C（destructive deny-floor）的无-L3/L4-floor 理据已呈 Owner（PLAN §5.2），Owner 选 A（简洁/可逆/一致优先）。 |

### 7.1 拍板前提的溯源纪律

本次 AskUserQuestion 选项内每条事实断言均于**提问前**完成 file:line 核验（`settings.json:25` 通配 / 零自动调用 grep /
`.mcp.json:112-171` server def / vault §四 框定 / app-start `:110,315` 否定引用 / #344 收窄先例）。承「错误前提下的
拍板作废」纪律（#341 §7.1 先例）：拍板前提为假则原拍板作废，须带更正后的事实回 Owner 重确认，不单方改写。

## 8 Verification Plan

- Level A（read-only）：`check_frontmatter.py` · `check_wikilinks.py` · `check_development_agent.py --all`（V8）·
  `check_agents_projection.py --all`（V9）· `agents_sync.py --check --surface skills`（V10）· `--surface mcp`（V11）·
  `pytest tests/unit tests/eval`（clean worktree 无 #298 假红）· `ruff check` · `mypy src/mj_agent`
- Level A（自证）：AC grep + JSON 解析（见 PLAN §验收）——**「零自动依赖」grep 在 PR 内重跑**
- Level B：无（本切片不跑 side-effect；不改 CI、不翻 gate、不动容器）

## 9 交办事项（本切片范围外，登记以免丢失）

1. **自建 ssh proxy-wrapper（若将来需要）**：过滤 ssh 工具/主机面的独立 MCP proxy = 更大工程，另立切片。本切片不预设。
2. **user-level Codex config 镜像收窄**（vault §四 登记）：owner 个人 harness 全局接了 ssh-manager/postgres-*——
   属 owner 个人决定，仅登记提示，不在仓治理内。
3. **承前序未决项**（非本切片）：`origin/bugfix/119-env-example-ascii-only`（PR #120 CLOSED/issue #119 OPEN，Owner 决策）·
   gitee/develop 落后 origin（有意镜像则忽略）· `policies/security.md:72` ADR-034 stale gloss（#347 INTAKE §9 登记）·
   INDEX ADR 表 drift（ADR-031/032/035/036 未入 `docs/INDEX.md`，pre-existing）· A6 审计提醒静默失效（M-FU-AI-AUDIT-2026-Q3/Q4 未注册）。

## 10 Next Step

Stage 3/4 计划落盘（本 worktree，同 PR）→ **Gate 5 拍板收窄口径 A/B/C** → Stage 8 实施（settings 收窄 + CHANGELOG）→
Stage 10/11 验证/自评（含 5-lens 对抗审查 + 全 diff credential 扫描）→ Gate 13 PR → 交 Owner 合并 →
Stage 17 post-merge（state flip PR + #312 议题 2 复选框勾选 + 分支 origin/gitee 双清 + worktree remove）。
