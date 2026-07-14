---
type: intake
summary: 双工具兼容 v5 第三执行切片（S1 skills 投影首批）的 Stage 0 Intake 落盘——maintain/High/stacked 2-PR 链；3 项 Owner 拍板记录（白名单全5+中立化4出边 / 2-PR stacked / issue+INTAKE 落盘）；对应 issue #326（总锚 #312）
owner: ranzuozhou
created: 2026-07-14
updated: 2026-07-14
completed: 2026-07-14
state: completed
track: shared
---

# [INTAKE] 双工具兼容 v5 — S1 切片（issue #326）

> Stage 0 输出于 2026-07-14 会话内产生并当日落盘；触发 §2.1 落盘判定（多 PR 链 + HITL 点≥3 + protected 邻接面）。
> 上游输入：[[[PLAN]_dual-agent-compat|v5 计划]] §8/§10/§11 S1/§11.1/§12；P1+S0 先例 #320（closed，develop @ 0cd1b2d）。

## 1 Task Classification

- Type: **maintain**（生成器脚本 / 生成产物 / tests / CI / 治理文档 / `.claude/skills` 工程编排技能源——不触 `src/mj_agent/` 运行时代码、`.mcp.json`）
- Base branch: develop；G1 worktree `maintain/326-s1-closure`（PR-B `maintain/326-s1-agents-sync` 从 PR-A 分支上 stacked 建）
- 影响范围：`.claude/skills/mj-agent-{flow-diagnose,git-delete,git-push}/SKILL.md` Handoff 段 · `scripts/sdd/agents_sync.py`〔新〕· `.agents.lock.json`〔新〕· `.agents/skills/` 5 投影〔新〕+ `.agents/README.md`〔新〕· `tests/unit/test_agents_sync.py`〔新〕· `.github/workflows/ci.yml` · 根 `AGENTS.md` · `sdd/gates.md` · `sdd/adapters/development-agent.md` · plans 2 件〔新〕

## 2 Risk Assessment

- Level: **High**（对齐 p1s0 族内判级）
- Triggered §3.1 必停项：#6（CI 工程配置面——新增 drift gate warning step，非 blocking flip，`ci-blocking-gate-toggle` 不触发且本切片无此授权）
- mj-agent 专属 4 项（trigger 10-13）：均不触及——`.claude/skills/**` 是 track C 工程编排技能（两类 skill 严格区分），编辑不构成 runtime-skill-content-change；白名单 5 技能均不在冻结 8（infra-*）内，不触 re-freeze
- 升档原因：CI workflow 变更 + `.claude/skills/**` protected-path 源编辑（交互 prompt 逐写拍板）+ `.agents/**` / `agents_sync.py` 受保护邻接面**创建**（后续修改必停，per program plan §17 v5 + D-017 anchor）

## 3 Documentation Decision（粗评；Stage 3 细化）

Plan=Create（本 2 件，PR-A 携带）；其余 9 类全 None（CHANGELOG=None 按 p1s0 先例；ADR=None——D-011~D-017 已由 ADR-036 收口；INDEX=None——无新 canonical 文档）。

## 4 Issue

- 总锚 #312（S1 为下一未勾阶段）；S1 执行 #326（Issue Draft 全文即 #326 body）
- 拆分：单执行 issue + stacked 2-PR 链（PR-A 闭包收口 / PR-B 生成器+产物+gate）；合并纪律 = A 先合 `--delete-branch` → 核对 B baseRefName 已翻 develop → 合 B（#314/#315、#322/#323 两次事故教训）

## 5 Owner 拍板记录（2026-07-14）

| # | 阶段 | 决策 |
|---|---|---|
| 1 | Stage 0 | 白名单定案 = **全 5 🟢**（flow-diagnose / git-commit / git-push / git-sync / git-delete；manifest 零改动）+ 中立化 3 文件 4 条集外 Handoff 出边为 kernel stage 指针（V9 实测闭包数学：git-commit 出边指向 git-push，任何含 git-commit 的收窄方案仍需中立化；零编辑方案仅剩 {git-sync} 单技能，低于 §4.4 的 3-5 口径） |
| 2 | Stage 0 | PR 拆分 = **2-PR stacked**（PR-A 闭包收口，protected 源编辑隔离便于审；PR-B 生成器+产物+gate；仅 1 个 retarget 点） |
| 3 | Stage 0 | 创建执行 issue #326 + 落盘本 INTAKE |

## 6 Verification Plan

见 [[[PLAN]_dual-agent-compat_s1|S1 执行计划]] §6（Level A 全量每 PR + PR-B 附加项；Level B 仅 Codex 实机发现验证——依赖 Owner trust（D-015），defer 至 post-merge 配合执行）。

## 7 Next Step

Stage 4 计划已同日落盘 → Stage 8 实施（PR-A 起；`.claude/skills` 逐写权限 prompt = 拍板载体）。S1 merge 后本文件 state flip completed（Rule 12，另开小 PR，#319/#325 先例）。
