---
type: intake
summary: 双工具兼容 v5 首个执行切片（P0）的 Stage 0 Intake 落盘——maintain/High/3-PR 链；7 项 Owner 拍板记录（Stage 0 三项 + Stage 3 四项）；对应 issue #313（总锚 #312）
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-13
completed: 2026-07-13
state: completed
track: shared
---

# [INTAKE] 双工具兼容 v5 — P0 切片（issue #313）

> Stage 0 输出于 2026-07-13 会话内产生并当日落盘；触发 §2.1 落盘判定三条（risk=High + HITL 点≥3 + 多迭代周期）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]]（Owner 2026-07-13 拍板；vault 评估文档为其裁决依据存档，不入仓）。

## 1 Task Classification

- Type: **maintain**（工程编排 skills / hook 脚本 / settings / CI / PR 模板 / sdd adapters——不触 `src/mj_agent/` 运行时代码）
- Base branch: develop；G1 worktree `maintain/313-dual-agent-compat-p0`
- 影响范围：`.claude/skills/`×10 + `SKILL_INDEX` · `.claude/scripts/guard-git-workflow.ps1` · `.claude/settings.json` · `.github/`（PR 模板 / ci.yml / agent.md）· `AGENTS.md` / `CLAUDE.md` · `policies/claude-code-skill.md` · `sdd/adapters/claude-code-skill.md` · `docs/`（INDEX / SPEC-Authoring GUIDE / 模板）· 冻结契约 yml · `tests/unit/`（新增 2 件）

## 2 Risk Assessment

- Level: **High**
- Triggered §3.1 必停项：#5（secrets 处理流程变更——去 Agent 读 env 路径，无 secret 值读取）· #6（CI / PR 模板 / settings / hook 工程配置面）；另有 harness 级 protected-path 拍板（`.claude/**` 交互模式逐写 prompt）
- mj-agent 专属 4 项（trigger 10-13）：均不触及
- 升档原因：冻结 infra skill 编辑（3/8，须 re-freeze）+ `.claude/**` 保护面 + hook 行为变更 + CI/模板口径收敛

## 3 Documentation Decision（粗评；Stage 3 细化为完整 10 行表）

Plan=Create（v5 port + P0 执行计划 + 本 intake）；GUIDE=Update（SPEC_Authoring §6）；INDEX=Update；ADR=None（ADR-036 留 P1/S0）；其余 None。

## 4 Issue

- 总锚 #312（P0-P4 + S0-S3 逐阶段勾选 + 3 独立拍板议题）；P0 执行 #313（Issue Draft 全文即 #313 body）
- 拆分：单 P0 issue + stacked 3-PR 链（PR-1 边界 / PR-2 HITL+guard / PR-3 口径+fixtures）

## 5 Owner 拍板记录（2026-07-13）

| # | 阶段 | 决策 |
|---|---|---|
| 1 | Stage 0 | 总锚 issue + P0 issue + stacked 3-PR 链 |
| 2 | Stage 0 | v5 port 为 `plans/[PLAN]_dual-agent-compat.md`（F1-F18 全表留 vault，正文指针引用） |
| 3 | Stage 0 | ADR-036 留 P1/S0 期立（收 D-001~D-017） |
| 4 | Stage 3 | P0 只收教学面；settings `mcp__pg-mj-system-biz-*`×5 allow 不动，权限收窄另登记（S2 同期评估） |
| 5 | Stage 3 | G1 regex 已知绕过 PR-2 顺手收紧 |
| 6 | Stage 3 | `read_only_by_design` → 改名 `owner_approval_required`（adapter spec 文本迁移，无 yml 实例） |
| 7 | Stage 3 | 裸 Bash 白名单取开发常用档（git/gh/uv/python/rg/ls 六条前缀） |

## 6 Verification Plan

见 [[[PLAN]_dual-agent-compat_p0|P0 执行计划]] §6（Level A 全量 + 3 项 per-PR 附加；Level B 无）。

## 7 Next Step

Stage 4 计划已同日落盘 → Stage 5 Gate 拍板 → Stage 8 实施（PR-1 起）。P0 merge 后本文件 state flip completed（Rule 12）。
