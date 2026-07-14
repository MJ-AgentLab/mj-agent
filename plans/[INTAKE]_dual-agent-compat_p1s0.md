---
type: intake
summary: 双工具兼容 v5 第二执行切片（P1+S0）的 Stage 0 Intake 落盘——maintain/High/stacked 3-PR 链；7 项 Owner 拍板记录（Stage 0 四项 + Stage 5 三项）；对应 issue #320（总锚 #312）
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-14
completed: 2026-07-14
state: completed
track: shared
---

# [INTAKE] 双工具兼容 v5 — P1+S0 切片（issue #320）

> Stage 0 输出于 2026-07-13 会话内产生并当日落盘；触发 §2.1 落盘判定（多 PR 链 + HITL 点≥3 + 跨多文档面）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §8/§9/§10/§11；P0 先例 #313（closed，develop @ f2850fa）。

## 1 Task Classification

- Type: **maintain**（sdd 文档 / scripts / tests / CI / 治理文档 / 根级入口文件——不触 `src/mj_agent/` 运行时代码、`.claude/**`、`.mcp.json`）
- Base branch: develop；G1 worktree `maintain/320-p1s0-agents-entry`（PR-2/PR-3 从前级 stack 分支上建）
- 影响范围：根 + 4 嵌套 `AGENTS.md` · 5 处 `CLAUDE.md` `@AGENTS.md` 引用 · `sdd/development-agent.yml`〔新〕· `sdd/adapters/development-agent.md`〔新〕· `scripts/sdd/` 两个新 checker · `tests/unit/` 新测试 · `.claudeignore` · `.github/workflows/ci.yml` · `sdd/gates.md` · `decisions/ADR-036` + `decisions/INDEX.md` · `policies/{documentation,ai-agent}.md` · `.github/PULL_REQUEST_TEMPLATE.md`

## 2 Risk Assessment

- Level: **High**
- Triggered §3.1 必停项：#6（CI 工程配置面——新增 warning gate，非 blocking flip，`ci-blocking-gate-toggle` 不触发且本切片无此授权）
- mj-agent 专属 4 项（trigger 10-13）：均不触及
- 升档原因：CI workflow 变更 + manifest `mcp`/`codex.posture` 段 = 受保护邻接面创建（后续修改必停，per program plan §17）+ ADR-036 与 D-017 anchor 扩展治理文档

## 3 Documentation Decision（粗评；Stage 3 细化为完整 10 行表）

Plan=Create（本 2 件，PR-1 携带）；ADR=Create（ADR-036，PR-3）；INDEX=Update（decisions/INDEX.md；docs/INDEX.md 不动，#277 先例）；其余 None。

## 4 Issue

- 总锚 #312（P1/S0 为下两个未勾阶段）；P1+S0 执行 #320（Issue Draft 全文即 #320 body）
- 拆分：单执行 issue + stacked 3-PR 链（PR-1 入口对等 / PR-2 机器 SoT / PR-3 门禁+决策收口）；plan §11 注明 S0「与 P1 同期，可同 PR」→ 合并为一条链

## 5 Owner 拍板记录（2026-07-13）

| # | 阶段 | 决策 |
|---|---|---|
| 1 | Stage 0 | 单执行 issue #320 + 落盘本 INTAKE |
| 2 | Stage 0 | D-017 anchor 扩展随本切片落地（ai-agent.md §4 + PR 模板；不等 S1/S2） |
| 3 | Stage 0 | S0 双发现 canary 以 unit test 承载（`.claude/skills/` 目录计数 ≟ manifest 计数；S3 迁入 doctor） |
| 4 | Stage 0 | PR 拆分粗方向 stacked 3-PR，自底向上依序合并（防 #314/#315 事故） |
| 5 | Stage 5 | 执行计划整体批准（闭包 Handoff 窄定义+空态降级 / §10 CLI 自建族 / 嵌套 AGENTS.md 治理注册 / gates.md V8/V9；state flip 按 #319 先例 post-merge 另 PR） |
| 6 | Stage 5 | manifest `required: true` = 闭环主路径 18 项（flow×10 + git×7 + doc-validate） |
| 7 | Stage 5 | `codex.posture` 初值 on-request / workspace-write / 65536（PR-2 review 再确认；该段后续修改必停） |

## 6 Verification Plan

见 [[[PLAN]_dual-agent-compat_p1s0|P1+S0 执行计划]] §6（Level A 全量每 PR + PR-2/PR-3 附加项；Level B 无）。

## 7 Next Step

Stage 4 计划已同日落盘 → Stage 5 Gate 已拍板（拍板项 5-7）→ Stage 8 实施（PR-1 起）。P1+S0 merge 后本文件 state flip completed（Rule 12，另开小 PR）。
