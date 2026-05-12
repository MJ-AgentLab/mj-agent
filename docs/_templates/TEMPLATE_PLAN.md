---
type: template
domain: WORKFLOW
summary: HITL Stage 4 Plan body 模板（写到 plans/[PLAN]_*.md；不写到 docs/plans/）；轻量级 5-6 段结构，从 plans/ 既有范例综合
tags:
  - template
  - workflow
  - plan
  - hitl-stage-4
aliases:
  - mj-agent Plan Template
created: 2026-05-11
updated: 2026-05-11
state: draft
version: v0.1
track: shared
owner: 项目负责人
---

# TEMPLATE: Plan body（HITL Stage 4）

> **使用方法**：复制本模板**主体段**到 `plans/[PLAN]_<topic>.md`（**不**写到 `docs/plans/`，per HITL_Prompt §4.5 Rules）。
>
> **何时复制本模板**：
> - Stage 4 Plan body 编写或更新（基于 Stage 3 Repo Scan Result）
> - 用户请求 "写 plan / 执行计划 / 任务拆解"
>
> **不**用本模板：
> - 详细接口契约（归 SPEC，用 [[TEMPLATE_SPEC|TEMPLATE_SPEC]]）
> - 长期架构决策（归 ADR，用 [[TEMPLATE_ADR|TEMPLATE_ADR]]）
> - Stage 0 Intake 准入评估（用 mj-agent-flow-intake 输出 Intake Result）
>
> **plans/ 既有 18 份范例**可参考为不同任务规模的具体形态（PR / Phase 子包 / 多 PR bundle 等）。本模板提供**最小可用骨架**；实际可按需增段。

---

## Plan body 模板

```markdown
---
type: plan
summary: 20-60 字摘要，一句话说本 Plan 解决什么任务、所属 Phase / PR 子包
owner: 项目负责人
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
track: shared / code / agent / engineering-workflow
---

# [PLAN] <Topic>

> Issue: [#NNN](https://github.com/MJ-AgentLab/mj-agent/issues/NNN)（如有）
> 关联 Repo Scan Result: <对话输出日期 / 摘要>

## Scope

- **In-scope**：
  - <具体动作 1>
  - <具体动作 2>
  - <具体动作 N>
- **Out-of-scope**：
  - <相邻但不做的项>
  - <留 follow-up 的项>

## Task Breakdown

按推进顺序：

1. <Step 1：动作 + 涉及文件 / 模块>
2. <Step 2：...>
3. <Step N：...>

## Risk Control

- **Risk level**：Low / Medium / High（如触 §3.1 必停 4 项 mj-agent 专属 → High）
- **缓解措施**：
  - <Risk 1 → 缓解>
  - <Risk 2 → 缓解>
- **HITL gates**：<本 Plan 触发的 Stage 5/7/9/11/13 HITL 点>

## Verification

- **Level A 必跑**：`uv run ruff check && uv run mypy src/mj_agent && uv run pytest tests/unit`
- **Level B HITL-confirm 按需**：`uv run pytest tests/{integration,smoke}` / `uv run mj-agent check` / Studio 探针
- **文档校验**：`scripts/check_frontmatter.py` + `scripts/check_wikilinks.py`（如本 Plan 涉及 docs/）
- **Acceptance Criteria**：
  - [ ] AC 1（可验证；对应 Verification 命令）
  - [ ] AC 2
  - [ ] AC N
```

---

## 段说明

| 段 | 必填 | 说明 |
|---|---|---|
| frontmatter | ✅ | type=plan / state=draft 起步 / track 按改动域选 |
| Issue 引用 | 推荐 | 与 GitHub Issue 关联；无 Issue 时省略 |
| Scope | ✅ | In-scope + Out-of-scope 双向声明（防 scope drift） |
| Task Breakdown | ✅ | 推进顺序的 Step 列表；过大任务可拆 Phase 子包 |
| Risk Control | ✅ | Risk level + 缓解 + HITL gates |
| Verification | ✅ | Level A 必跑 + Level B 按需 + AC checklist |

**可选增段**（按 plans/ 既有范例）：
- **Phase 子包**：多 PR bundle 时列出 ✅ 完成 / 🔄 进行中 / ⏭ 待办
- **严格守约**：明确不做的项（与 Out-of-scope 互补；强约束）
- **累计成果**：里程碑摘要（适合 Phase 收尾 plan）
- **Open Questions**：起草时未定项

---

## 命名约定

- 文件名：`plans/[PLAN]_<topic_in_snake_or_kebab_case>.md`
- 不带版本号（per ADR-018 active path stability；plan 是 working doc）
- state 演进：`draft` → `active` → `completed` → `archived`（per ADR-021 4 态机）
- post-merge 后由 `/mj-agent-flow-post-merge` Step 9 自动 active → completed

---

## 关联文档

- [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]] §4.5（Stage 4 Plan prompt）
- `.claude/skills/mj-agent-flow-plan/SKILL.md`（Plan body 编排器）
- [[../adr/[ADR]_021_Working_Doc_Lifecycle|ADR-021]]（plans/ 4 态机）
- [[TEMPLATE_REPO_SCAN_RESULT|TEMPLATE_REPO_SCAN_RESULT]]（Plan 上游 Stage 3 输出）

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-11 | v0.1 | 初稿（PR-118 commit-3 落地；G2 gap 修复；从 plans/ 既有 18 份范例综合） |
