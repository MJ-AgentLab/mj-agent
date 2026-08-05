---
type: plan
summary: Phase D-3 — Agent_Side v1.1→v1.2 archive ceremony；§4 EVAL Authoring 完整规范；ADR-024；Phase D 收尾
owner: 项目负责人
created: 2026-05-09
updated: 2026-08-05
state: completed
track: shared
---

# [PLAN] Phase D-3 — EVAL framework spec + Agent_Side v1.2

> Phase D 子包 3/3（**Phase D 收尾**）。Issue: [#95](https://github.com/MJ-AgentLab/mj-agent/issues/95)。

## Scope

- 新建 ADR-024（EVAL framework spec 决策）
- Agent_Side v1.1 → v1.2 archive ceremony（substantive 演进 §5.9 trigger #2）
  - v1.1 archive 至 `docs/archive/rule/[DEPRECATED]_..._v1.1.md`
  - v1.2 在原 stable path（per ADR-018）
- §4 EVAL Authoring 完整规范（4 子类 + body 八段 + frontmatter schema）
- check_frontmatter.py 加 EVAL type-conditional
- 同步 docs/INDEX.md / CLAUDE.md / CHANGELOG.md

预计 ~10 文件改动。

## 严格守约

- **不实跑 EVAL runtime**（Phase E）
- **不关闭 A8/A11 transitional waiver**（前置条件 4 项；Phase E）
- **不创建 sample EVAL 文档**（Phase E）
- **不修改 TEMPLATE_EVAL.md**（Phase E align）

## Phase D 收尾

- ✅ D-1（PR #91）— templates 补齐
- ✅ D-2（PR #93 + #94 hotfix）— scripts/infra
- 🔄 **D-3（本 PR）** — EVAL framework spec **（Phase D 收尾）**

## 累计成果

mj-agent 文档治理 P0/P1/P2/P3 全项完成；10 PRs / 9 ADRs（ADR-017 → ADR-024）；mj-system v5.2 派生 + mj-agent 原生 EVAL spec 一体。
