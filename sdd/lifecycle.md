---
type: sdd-kernel
artifact: lifecycle
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# SDD Lifecycle

> Phase M0 skeleton — Capability 9-state + Archive 5-state machine.
> 详细 transition 规则在 Phase M2 内容填充.

## §1 Capability Lifecycle（9 态）

```
idea ─► specified ─► contracted ─► planned ─► implementing ─► verifying ─► active ─► evolving
                                                                              ▲          │
                                                                              └──────────┘
                                                                                 │
                                                                                 ▼
                                                                            deprecated
```

| 状态 | 含义 | 进入条件 | 退出条件 |
|---|---|---|---|
| idea | 新需求未规格化 | 用户/SDR 提出 | spec.yml 起草 |
| specified | spec.yml + requirements.md 起草 | spec.yml schema 通过 | contracts/ 起草 |
| contracted | contracts/ 至少 1 件 + behavior.feature（高风险） | check_contracts.py PASS | tasks.md 拆分 |
| planned | tasks.md 任务清单完整（含 tdd.test_list 高风险） | HITL Gate-1 plan-vs-spec 对齐 | 实施开工 |
| implementing | 代码实施中 | 单 PR open | 单 PR ready-to-merge |
| verifying | contract test + bdd + tdd 跑 | 测试 PASS | evidence/ 写入 |
| active | 全套 artifact 就绪 | trace.yml 完整链路 | HITL 触发 evolve / deprecate |
| evolving | REQ 变更 / contract 扩展 / 依赖升级 | evolve-capability workflow | 回到 active |
| deprecated | 弃用宣告（不再演进） | HITL + ADR | Phase M5 进入 archive ceremony |

> TBD: Phase M2 — 每态的 evidence 要求 + CI gate 联动.

## §2 Archive State（5 态；archive.yml `archive_state`）

```
active ─► deprecated ─► frozen ─► archived ─► purge-eligible
```

| 状态 | 含义 | AI 可读性（archive.yml `ai_visibility`） |
|---|---|---|
| active | 在用 | source-of-truth |
| deprecated | 弃用宣告，仍有引用 | reference |
| frozen | 不再修改，仅作历史 | reference |
| archived | 已迁入 `archive/` 目录 | hidden（默认） / reference（按需） |
| purge-eligible | 保留期满，可物理删除（per `policies/archive.md` retention_class） | hidden |

> TBD: Phase M5 archive ceremony — frozen → archived transition 流程详见
> `sdd/workflows/archive-capability.md` + `policies/archive.md`.

## §3 状态转移触发条件

| Transition | 触发 | 必经 gate |
|---|---|---|
| idea → specified | spec.yml 起草 + schema 校验 | G1 check_capability_schema |
| specified → contracted | contracts/ 文件 ≥ 1 + 高风险加 behavior.feature | G3 check_contracts |
| contracted → planned | tasks.md `tdd.test_list[]` 完整（高风险）| G23 check_tdd_test_list（Phase M3 起 warning；M6 blocking） |
| planned → implementing | PR open + HITL Gate-1 | — |
| implementing → verifying | contract test + bdd-step + tdd green | G2/G5/G19-G28 |
| verifying → active | evidence 写入 + trace.yml 链路完整 | G8 evidence required（Phase M4 起 blocking） |
| active → deprecated | ADR + HITL | A12-A14 PR gate（per Meta v2.x §7.7） |
| deprecated → archived | archive ceremony + archive.yml | G11/G12 check_archive_manifest |

## §4 与 sdd/workflows/ 联动

每个状态转移对应一个或多个 workflow：

| Transition 起点 | Workflow |
|---|---|
| idea / specified | `sdd/workflows/new-capability.md` |
| active → evolving | `sdd/workflows/evolve-capability.md` |
| 任意态触发 bugfix | `sdd/workflows/bugfix-drift.md` |
| 跨 capability 共享 contract 变更 | `sdd/workflows/cross-capability-change.md` |
| 生产紧急 | `sdd/workflows/hotfix.md` |
| deprecated → archived | `sdd/workflows/archive-capability.md` |

---

> *Phase M0 skeleton — `state: draft`. 详细 transition gate 联动 + evidence 模式见 Phase M2
> 内容填充.*
