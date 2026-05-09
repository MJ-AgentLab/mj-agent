---
type: plan
summary: Phase C-4 — 5 P2 framework rule bundle (ADR-022)；mj-system v5.2 §3.6+§4.1+§4.4 派生
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] Phase C-4 — P2 framework enhancements bundle

> Phase C-4 是 P2 项目收尾。Issue: [#88](https://github.com/MJ-AgentLab/mj-agent/issues/88)。

## Scope

5 P2 项目 bundle 一个 PR：

| 项目 | mj-system 派生源 | 落地 |
|---|---|---|
| C.3.1 类型专属 frontmatter（4 类 8 字段） | §4.4 | Code_Side v1.1 §3.4-§3.8 |
| C.3.2 STANDARD placement 决策矩阵 | §3.6 | Meta v2.2 §3.7 |
| C.3.3 ISSUE NNN+DomainAbbr 命名 | §4.1 | Meta v2.2 §4.5 |
| C.3.4 supersedes list 文档化 | §4.4 | Meta v2.2 §4.6 |
| C.3.6 STANDARD 拆分阈值 | §3.6 | Meta v2.2 §3.8 |

同期：

- 新建 ADR-022（bundle 决策；不 supersede）
- 修改 `scripts/check_frontmatter.py`（type-conditional 校验）
- sync docs/INDEX.md / CLAUDE.md / CHANGELOG.md

## 风险等级：Low

- 现有 RUNBOOK / ASSESSMENT 检查可能漏字段（手工补 last-verified；ASSESSMENT 已含 dimensions/period）
- check_frontmatter.py 加 type-conditional：state: draft / deprecated 宽松；不 break 现有 draft 文档

## 验证

- check_frontmatter（含新 type-conditional；现有文件应不报错或仅报需补字段）
- check_wikilinks
- ruff/mypy/pytest

## 完成 mj-agent 文档治理 P0/P1/P2 全项

ADR-017 / 018 / 019 / 020 / 021 / 022 + Meta v2.2 + Code_Side v1.1 完整覆盖 mj-system v5.2 派生主线。Phase D 留给 EVAL framework + GC + 模板补齐实测。
