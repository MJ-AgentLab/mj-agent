---
type: sdd-workflow
artifact: hotfix
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Workflow: Hotfix

> Phase M0 skeleton — 生产热修复（base = main + spec 债务偿还时限）.
> 替代 HITL_Prompt v1.x hotfix flavor. 完整流程在 Phase M2 内容填充.

## Purpose

生产环境紧急修复；允许临时绕过部分 spec-first 流程，但 spec 债务必须在合并后 N 工作日内偿还.

## Trigger

- 生产事故 / 高危漏洞 / 数据正确性紧急修复
- 上游业务系统紧急切换需要 mj-agent 配合
- LLM endpoint 紧急切换

## High-Level Steps

1. **Branch** — `git worktree add ../hotfix/<slug> -b hotfix/<slug> main`
   （per `.claude/skills/mj-agent-git-branch/SKILL.md` hotfix 6 步）.
2. **Minimal fix** — 最小变更面（仅一个 commit type，仅 fix；不夹带 refactor / feature）.
3. **HITL Gate-Emergency** — 1 reviewer 快速审；触及 4 项专属必停或 prod compose → 必须 +1
   reviewer.
4. **PR to main** — target = main；commit type 必须含 `fix(`.
5. **Tag** — merge 后 main 打 patch 版本 tag.
6. **Sync develop ← main** — `mj-agent-git-sync` skill；防 hotfix 在下次 main → develop 合并
   时引入冲突.
7. **Spec debt payment** — N 工作日内（默认 5 工作日；critical hotfix 3 工作日）补齐 capability
   `requirements.md` / `contracts/` 演进 + evidence/postmortems/ 写入；走标准
   `evolve-capability.md` 流程.

## HITL Triggers

- 任意 hotfix → 紧急 HITL（reviewer 优先级最高）
- 触及 prod compose → 必须 ≥ 2 reviewer
- 触及 4 项专属必停 → 必须 ≥ 2 reviewer + 1 domain expert
- 数据-LLM 边界相关 → 走 cross-capability workflow（不应走 hotfix 单线）

## TBD: Phase M2 内容填充

- "spec debt 超期未还" 的 stale issue 自动建单（per `scripts/find_old_completed_plans.py` 演进）
- hotfix 与 postmortem 的强制配对规则

---

> *Phase M0 skeleton — `state: draft`.*
