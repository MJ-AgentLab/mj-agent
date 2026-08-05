---
type: plan
summary: Phase C-3-3 — plans/ working 文档 4 态机（ADR-021；mj-system §10.5 派生）；Phase C-3 P1 三联包收尾
owner: 项目负责人
created: 2026-05-09
updated: 2026-08-05
state: completed
track: shared
---

# [PLAN] Phase C-3-3 — Working doc 4 态机（C.2.3）

> Phase C-3 P1 三联包子包 3/3（收尾）。
> Issue: [#86](https://github.com/MJ-AgentLab/mj-agent/issues/86)

## Scope

- 新建 ADR-021（working doc 4 态机决策；不 supersede 任何 ADR）
- Meta v2.2 §5.11 加 working doc 4 态机条款（in-place）
- `mj-agent-flow-post-merge` SKILL Step 9 cross-ref 从 "Meta v2.0 §10.5"（forward-ref）改 "Meta v2.2 §5.11"（实落）
- retroactive 标 7 plans state: completed（5 PLAN_doc_governance_* + PLAN_F + PLAN_G）
- 同步：docs/INDEX.md（ADR-021 row）+ CLAUDE.md（Versioning rule 段）+ CHANGELOG.md（收尾入条）

`scripts/check_frontmatter.py` STATE_VALUES 已含 `completed`（早期预先添加）— 本 PR 仅文档化规则。

## 不在本 PR

- `archived` 物理归档实现（移 plans/archive/；GC trigger）— Phase D
- 5 个长期 draft 旧 plans（PLAN_A/B/C/E/Phase0）保留 draft（per mj-system §10.5.5 "abandon 余地"）
- mvp-framework + roadmap 保留 active（长期资产）

## 验证

- check_frontmatter（plans/* 含 completed state 不报错；canonical 仍仅 3 态）
- check_wikilinks（应 OK 0 violations）
- ruff/mypy/pytest

## Phase C-3 收尾

3-PR P1 三联包全部完成：
- ✅ C-3-1（PR #83）— check_wikilinks.py 通用化（ADR-020）
- ✅ C-3-2（PR #85）— archive banner 标准化（无新 ADR）
- 🔄 **C-3-3（本 PR）** — working doc 4 态机（ADR-021）
