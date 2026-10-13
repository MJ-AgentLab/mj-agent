---
type: sdd-workflow
artifact: new-capability
state: draft
version: "0.3"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-12
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
7. **基线检查点** — plan-vs-spec 对齐 review.
8. **Implementation** — 编码 + 测试落地（per `sdd/workflows/` 选择 flavor A/B/C；
   per HITL_Prompt v1.x §4.8）.
9. **Verification** — contract test + bdd-step + tdd green + evidence 写入.
10. **独立核验/平台审核** — PR review.
11. **Activate** — `spec.yml lifecycle_state: active` + `trace.yml` 完整链路.

## 决定与授权

接受基线和任务授权先明确；普通spec/contract/实现自主。安全/业务/权限/breaking/AC/gate实质变化才先决定，runtime路径本身不审批。验证及独立核验/平台批准分别留证。

## Outputs

新 capability 完整 12-artifact 套件（历史目标蓝图 `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` v2.2 §4.5，2026-05-20，本机 vault）：

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
>
> *v0.2（2026-10-10）：#498 补全历史蓝图的本机 vault 路径与已核验版本，保留既有 §4.5 出处归属；规则、契约、执行命令和 `state` 不变。仓外来源不作为当前可执行规则入口。*
