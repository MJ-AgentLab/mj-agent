---
type: sdd-workflow
artifact: new-capability
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Workflow: New Capability

> Phase M0 skeleton — 完整 sub-step + safe-sql 落地经验校准 在 Phase M1 内容填充
> （per Phase M1 §4 "sdd/workflows/new-capability.md (Phase 0 skeleton → 完整 sub-step)"）.

## Purpose

新 capability 从 idea → active 的端到端流程；替代 HITL_Prompt v1.x §4.0-§4.16 主线.

## Trigger

- 用户提出新业务能力需求
- 现有 capability 拆分（如 tool-chain 拆 analysis / charts / excel / sql）
- 跨 capability 横切关注点显化（如 secrets-pipeline / memory-checkpointer）

## High-Level Steps

1. **Intake** — issue 起草，识别 capability 边界（domain + slug）.
2. **Spec** — `capabilities/<domain>/<slug>/spec.yml` 起草 + schema 校验.
3. **Requirements** — `requirements.md` 起草，含 `bdd.examples[]`（高风险 REQ 必填）.
4. **Design** — `design.md` 起草（Context / Decision / Architecture / Tradeoffs）.
5. **Contracts** — `contracts/` 至少 1 件 + `behavior.feature`（高风险 REQ 必填）.
6. **Tasks** — `tasks.md` 拆分，含 `tdd.test_list[]`（高风险 task 必填）.
7. **HITL Gate-1** — plan-vs-spec 对齐 review.
8. **Implementation** — 编码 + 测试落地（per `sdd/workflows/` 选择 flavor A/B/C；
   per HITL_Prompt v1.x §4.8）.
9. **Verification** — contract test + bdd-step + tdd green + evidence 写入.
10. **HITL Gate-2** — PR review.
11. **Activate** — `spec.yml lifecycle_state: active` + `trace.yml` 完整链路.

## HITL Gates

- **Gate-1（plan-vs-spec）**：tasks.md 起草后；reviewer 验证 plan 与 spec 一致
- **Gate-2（PR review）**：PR open；reviewer + domain expert 共审 capability artifact 套件
- **触发 4 项专属必停 any → 永久 HITL**（参 `sdd/gates.md` §4）

## Outputs

新 capability 完整 12-artifact 套件（per `mj-agent-refactored-structure.md` §4.5）：

```
capabilities/<domain>/<slug>/
├── spec.yml
├── requirements.md
├── design.md
├── contracts/{<adapter>.contract.yml, behavior.feature}
├── tasks.md
├── runbook.md
├── trace.yml
└── evidence/{verification, reports, security, runtime, postmortems, bdd, tdd}/
```

## TBD: Phase M1 内容填充

- 每步骤的输入 / 输出 / HITL 触发条件细化
- safe-sql / biz-catalog / llm-provider 5 pilot 落地经验回填
- 与 `mj-agent-flow-*` skill family 的 stage 映射表

---

> *Phase M0 skeleton — `state: draft`.*
