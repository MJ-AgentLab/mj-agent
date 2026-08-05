---
type: plan
summary: Phase D-1 — 3 模板补齐（占位转 active）+ TEMPLATE_RUNBOOK 加 last-verified；ADR-022 C.3.1 字段对齐；Phase D 子包 1/3
owner: 项目负责人
created: 2026-05-09
updated: 2026-08-05
state: completed
track: shared
---

# [PLAN] Phase D-1 — 模板补齐 + frontmatter 对齐

> Phase D 子包 1/3（最简）。Issue: [#90](https://github.com/MJ-AgentLab/mj-agent/issues/90)。

## Scope

Templates 已存在（200-300 行 each；body 段落齐全）；本 PR 实际工作：

- 字段名对齐 ADR-022 C.3.1（短横线 vs 下划线）：
  - TEMPLATE_POSTMORTEM: `incident_date` → `incident-date`；`resolved_at` → `resolved-at`
  - TEMPLATE_ISSUE: `risk_level` → `risk-level`
- TEMPLATE_RUNBOOK 加 `last-verified` 字段（ADR-022 C.3.1 RUNBOOK 必填）
- docs/INDEX.md Templates 表 4 entries 移除 "(Phase D PR-D1)" 占位标记
- 同步 CHANGELOG.md

## Phase D 子包

- 🔄 **D-1（本 PR）** — 3 模板补齐（最小）
- ⏭ D-2 — archived 物理归档 + find_stale_docs.py 完整版（ADR-023）
- ⏭ D-3 — EVAL framework + A8/A11 transitional waiver 关闭（ADR-024；最大）

## 不引入新 ADR

实施 ADR-022 C.3.1 工作；规则已落 Code_Side v1.1 §3.x。

## 收口记录（2026-08-05；#424）

本 plan 自 2026-05-09 起停在 `state: active`，而其 issue #90 已于**同日** CLOSED/COMPLETED ——
属 Rule 12（PR-plan state 必标 completed）遗留。#424 逐项核实 §Scope 后收口：

| Scope 项 | 状态 | 证据 |
|---|---|---|
| POSTMORTEM `incident_date` / `resolved_at` 改短横线 | ✅ 已落地 | `TEMPLATE_POSTMORTEM.md:15-16` |
| ISSUE `risk_level` 改短横线 | ✅ 已落地 | `TEMPLATE_ISSUE.md:15` |
| RUNBOOK 加 `last-verified` | ✅ 已落地 | `TEMPLATE_RUNBOOK.md:14` |
| 同步 CHANGELOG.md | ✅ 已落地 | `CHANGELOG.md` Phase D-1 段 |
| docs/INDEX.md 移除标记 | ⚠ **当时未落地**，由 #424 补做 | 见下 |

唯一未落地项，及随之发现的三处订正：

1. **CHANGELOG 曾错报完成。** Phase D-1 段写「docs/INDEX.md Templates 表 4 entries 同步更新
   （移除 PR-D1 占位标记 + 注 ADR-022 C.3.1 frontmatter）」，但标记直至 #424 仍原样在表内。
   完成断言掩盖了未落地事实 —— 这正是该缺口三个月无人察觉的原因。
2. **计数偏差。** §Scope 写「4 entries」，实际带 D-1 字样的是 **5 行**（RUNBOOK / POSTMORTEM /
   ISSUE / ASSESSMENT / EVAL）；RUNBOOK 的 `Phase D-1 加 last-verified 字段` 是行内从句，易漏计。
3. **执行口径变更（Owner 2026-08-05 拍板）。** 这些括注与同表的 `(Phase A PR-A3)` /
   `(PR-118 commit-3)` / `(Phase B PR-B1)` 属**同一 provenance 体裁**，是准确的过去式事实，
   并非「占位」。只剥 D-1 那 5 处会让 15 行的表**更**不一致（5 带 / 10 不带）。故 #424 改为
   **全剥 10 处**、全表统一；括注承载的信息（`last-verified` 字段、`§0 Task Type
   Identification`、`mj-agent 原生`）在同行「用途」列均已覆盖，零信息损失。

Phase D 子包 D-2 / D-3 的状态不由本 plan 承载。
