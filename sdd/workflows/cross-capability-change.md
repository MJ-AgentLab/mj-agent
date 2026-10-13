---
type: sdd-workflow
artifact: cross-capability-change
state: draft
version: "0.2"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-12
track: shared
ai_visibility: source-of-truth
---

# Workflow: Cross-Capability Change

> Phase M0 skeleton — 跨 capability 边界变更（共享 contract / qcm_catalog 影响 safe-sql 等）.
> 替代 HITL_Prompt v1.x cross-cutting 场景. 完整流程在 Phase M2 内容填充.

## Purpose

Capability 间共享 contract 变更（schema / 行为边界 / 数据契约）的协调流程；每 cross-capability PR 核依赖、AC与真实影响.

## Trigger

- 共享 contract（如 biz-catalog 被 safe-sql 引用）schema 变更
- 跨多 capability 的 shared step definition 修改（tests/bdd/shared/）
- adapter 文档变更影响 ≥ 2 capability
- 四类runtime面存在真实跨域依赖或语义影响

## High-Level Steps

1. **Impact scope** — 跑 `scripts/sdd/check_capability_impact.py` 输出受影响 capability 列表
   （输入 = 计划触及的文件清单；实现中可用 `git diff --name-only | ... --stdin`）；unmapped
   文件由Agent核实际scope + `/mj-agent-flow-scope-drift` 判定.
2. **Cross-cap review preparation** — 每受影响 capability 各起草 evolve plan
   （per `evolve-capability.md`）.
3. **联合基线检查点** — 独立核验覆盖领域与SDD视角；实质取舍由Owner决定.
4. **Bundled PR** — 倾向单 PR 同时改完所有受影响 capability；split PR 仅在依赖图清晰且
   review 成本可控时考虑（per memory `feedback_post_merge_ac_defer` lessons）.
5. **Joint Verification** — 每受影响 capability 各跑 contract test + bdd + tdd；evidence
   分别写入各 evidence/.
6. **Joint 独立核验/平台审核** — PR review；每 reviewer 限定看自己 capability scope.
7. **trace.yml update across capabilities** — 每受影响 capability 的 trace.yml 都更新
   cross-capability ref 段（schema v1.2+）.

## 决定与授权

跨capability不是自动人工停点。协调者对真实影响列依赖与每域AC，按可独立交付选择单/独立/分层PR；安全/业务/权限/breaking/AC实质变化先决定。

## TBD: Phase M2 内容填充

- `check_capability_impact.py` 映射全量化（spec.yml `owned_paths[]` 字段 + G1 schema 扩展；
  当前轻量版 unmapped 交人判）
- shared step definition / shared contract 集中管理位置（tests/bdd/shared/ + contracts/shared/）

---

> *Phase M0 skeleton — `state: draft`.*
