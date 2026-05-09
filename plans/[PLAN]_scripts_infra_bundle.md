---
type: plan
summary: Phase D-2 — scripts/infra：find_stale_docs.py 完整版 + plan GC infra + ADR-023；Phase D 子包 2/3
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] Phase D-2 — scripts/infra bundle

> Phase D 子包 2/3。Issue: [#92](https://github.com/MJ-AgentLab/mj-agent/issues/92)。

## Scope

- 新建 ADR-023（决策记录；不 supersede；落实 ADR-020 / ADR-021 follow-up）
- 新建 `scripts/find_stale_docs.py`（mj-system v5.2 §7.1.1 派生；path-level rename detection）
- 新建 `.github/workflows/check-stale-docs.yml`（warning-mode CI；4 周观察期）
- 新建 `scripts/find_old_completed_plans.py`（plan GC 候选检测；不实跑）
- Meta v2.2 §5.11.5 加 archive 实施指引段
- 同步 docs/INDEX.md / CLAUDE.md / CHANGELOG.md

预计 ~9 文件改动 / ~400 行净增。

## Phase D 子包

- ✅ D-1（PR #91）— templates 补齐
- 🔄 **D-2（本 PR）** — scripts/infra
- ⏭ D-3 — EVAL framework + A8/A11 transitional waiver 关闭（最大）

## 严格守约

- 本 PR **不实跑 GC**（mj-agent plans/ 距今 < 1 月）
- 本 PR find_stale_docs **warning 模式**（4 周观察期再评估升级 blocking）
- 本 PR **不实现 symbol-level rename detection**（Phase E+ 候选）
