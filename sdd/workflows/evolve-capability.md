---
type: sdd-workflow
artifact: evolve-capability
state: draft
version: "0.2"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-12
track: shared
ai_visibility: source-of-truth
---

# Workflow: Evolve Capability

> Phase M0 skeleton — Capability `active → evolving → active` 演进流程.
> 替代 HITL_Prompt v1.x §4.17 evolve 分支. 详细 sub-step 在 Phase M2 内容填充.

## Purpose

已有 active capability 的 REQ 变更 / contract 扩展 / 依赖升级 / adapter coverage 调整.

## Trigger

- 现有 REQ 行为边界调整
- contract schema 演进（不破坏向后兼容）
- 新 adapter 引入（如 data-agent.safe-sql 增 tdd-bdd adapter coverage）
- 依赖库主版本升级（如 LangChain 2.x）

## High-Level Steps

1. **Diff scope** — 评估变更影响：本 capability 内 / cross-capability / data boundary.
2. **Spec evolve** — `requirements.md` REQ-NNN 追加变更条款（不 in-place rewrite，保历史）.
3. **Contracts diff** — `contracts/` 新增 / 修改字段；保 backward compat 或显式声明 breaking.
4. **Tasks** — `tasks.md` 追加演进 task；含 `tdd.test_list[]` red-green-refactor 计划.
5. **基线检查点** — evolve plan review（特别看是否 breaking → 触发 cross-capability workflow）.
6. **Implementation + Verification** — contract test + bdd-step + tdd evidence.
7. **独立核验/平台审核** — PR review.
8. **trace.yml update** — REQ-NNN links 追加新 evidence / contracts / tests.

## 决定与授权

兼容contract扩展、必要重构和基线内runtime自主；breaking承诺、安全/业务/外发/权限或接受标准变化由Owner决定，跨capability按依赖协调。

## TBD: Phase M2 内容填充

- 与 `evolve-capability` workflow 联动的 ADR 起草触发条件
- backward-compat 校验脚本（per `scripts/sdd/check_contracts.py` 演进模式）

---

> *Phase M0 skeleton — `state: draft`.*
