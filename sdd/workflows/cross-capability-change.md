---
type: sdd-workflow
artifact: cross-capability-change
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Workflow: Cross-Capability Change

> Phase M0 skeleton — 跨 capability 边界变更（共享 contract / qcm_catalog 影响 safe-sql 等）.
> 替代 HITL_Prompt v1.x cross-cutting 场景. 完整流程在 Phase M2 内容填充.

## Purpose

Capability 间共享 contract 变更（schema / 行为边界 / 数据契约）的协调流程；每 cross-capability
PR 必须 HITL.

## Trigger

- 共享 contract（如 biz-catalog 被 safe-sql 引用）schema 变更
- 跨多 capability 的 shared step definition 修改（tests/bdd/shared/）
- adapter 文档变更影响 ≥ 2 capability
- 4 项专属必停文件变更（默认 cross-capability 性质：影响 agent.py + 多 tool）

## High-Level Steps

1. **Impact scope** — `scripts/sdd/check_plan_vs_diff.py` 输出受影响 capability 列表.
2. **Cross-cap review preparation** — 每受影响 capability 各起草 evolve plan
   （per `evolve-capability.md`）.
3. **Joint HITL Gate-1** — domain expert（每 capability owner）+ SDD reviewer 共审
   plan diff.
4. **Bundled PR** — 倾向单 PR 同时改完所有受影响 capability；split PR 仅在依赖图清晰且
   review 成本可控时考虑（per memory `feedback_post_merge_ac_defer` lessons）.
5. **Joint Verification** — 每受影响 capability 各跑 contract test + bdd + tdd；evidence
   分别写入各 evidence/.
6. **Joint HITL Gate-2** — PR review；每 reviewer 限定看自己 capability scope.
7. **trace.yml update across capabilities** — 每受影响 capability 的 trace.yml 都更新
   cross-capability ref 段（schema v1.2+）.

## HITL Triggers

- 任意 cross-capability change → 永久 HITL（per `policies/ai-agent.md` §HITL Required Scenarios #2）
- 数据-LLM 边界三原则相关 → 永久 HITL（per ADR-000）
- 同时触发 4 项专属必停中任 ≥ 1 项 → 永久 HITL（叠加）

## TBD: Phase M2 内容填充

- cross-capability impact scope 自动检测脚本（per scripts/sdd/check_plan_vs_diff.py 演进）
- shared step definition / shared contract 集中管理位置（tests/bdd/shared/ + contracts/shared/）

---

> *Phase M0 skeleton — `state: draft`.*
