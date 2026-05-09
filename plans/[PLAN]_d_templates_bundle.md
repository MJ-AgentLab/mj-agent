---
type: plan
summary: Phase D-1 — 3 模板补齐（占位转 active）+ TEMPLATE_RUNBOOK 加 last-verified；ADR-022 C.3.1 字段对齐；Phase D 子包 1/3
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
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
