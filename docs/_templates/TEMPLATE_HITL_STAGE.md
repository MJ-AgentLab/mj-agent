---
type: standard
domain: WORKFLOW
summary: HITL_Prompt §4 stage prompt 模板（mj-agent 工程流程编排专用），匹配 §2 通用结构
tags:
  - template
  - hitl
  - stage
  - workflow
aliases: []
created: 2026-05-08
updated: 2026-05-08
state: draft
version: v0.1
track: shared
owner: 项目负责人
---

# TEMPLATE: HITL_Prompt 单 Stage Prompt

> **何时复制本模板**：
>
> 1. 在 `[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md` 的 §4 中**新增** stage（如 mj-agent 实际需要 stage 7.5）
> 2. **派生** 子规范时（如新建 `[STANDARD]_MJ_Agent_AI_Engineering_Intake_v1.0.md` 时，每个 sub-step 用本模板）
> 3. 复用本模板创建 `.claude/skills/mj-agent-flow-*/SKILL.md` 的 Workflow 段（不要照搬本模板进 SKILL.md frontmatter；SKILL.md frontmatter 走 ADR-013 native schema）
>
> **不**用本模板：
>
> - 起草普通 SPEC（用 [[TEMPLATE_SPEC|TEMPLATE_SPEC]]）
> - 起草 ADR（用 [[TEMPLATE_ADR|TEMPLATE_ADR]]）
> - 起草 SKILL.md body 主体（参考 `[[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.10.2` 给出的 `## Overview / ## Workflow / ## Output Format` 风格）

---

> **使用方法**：复制下方 **fenced markdown block** 内容到目标位置（`docs/rule/[STANDARD]_..._HITL_Prompt_v*.md` 的 §4.X 子节，或 `.claude/skills/mj-agent-*/SKILL.md` 的 `## Workflow` 段）。把占位符替换为实际内容。

---

## Stage Prompt 模板

````markdown
### 4.X <Stage 名称>

```markdown
## Task

<一段话说明本 stage 要完成什么。明确"做什么"+ "不做什么"边界（如"不要创建 Issue / 不要写文件 / 不要修改代码"）。>

## Reference Docs

### Must Follow
- `<必须遵守的规范文档 wikilink 或路径>`
- `<...>`

### Use As Template
- `<输出结构模板（如 TEMPLATE_PLAN.md / TEMPLATE_SPEC.md）>`

### Consult If Affected
- `<仅当涉及对应领域时参考的文档>`
- `<...>`

## Skill Hint

Preferred Skill:
- `/mj-agent-<group>-<verb>`（首位编排器；说明 phase B+ 落地状态）
- `/mj-agent-<group>-<verb-2>`（下游或互补 skill，可省略）

Use When:
- <用户请求 / 触发条件 1>
- <用户请求 / 触发条件 2>

Fallback:
- 若 skill 不可用，按本 prompt Rules 手动执行<具体指引>
- 或回落到下位子 skill：<降级路径，可省略>

## Rules

请<动作动词>：

1. <规则 1>
2. <规则 2>
3. <规则 3>
...
N. <规则 N>

mj-agent 专属规则（如有；可删此段）：

- **<mj-agent 专属硬约束 1>**：<细节>
- **<mj-agent 专属硬约束 2>**：<细节>

以下情况暂停（任意触发 → HITL）：

- <HITL 触发条件 1>
- <HITL 触发条件 2>
- <...>

## Output

输出：

- <输出项 1>
- <输出项 2>
- <...>
- HITL Questions
```

---
````

---

## 字段说明

| 字段 | 说明 | 示例 |
|---|---|---|
| `### 4.X <Stage 名称>` | stage 编号；mj-agent 17-stage 闭环已分配 §4.1-§4.15；新增 stage 用 4.16+；子 stage 用 §4.X.Y | `### 4.16 Studio E2E Probe` |
| `## Task` | 本 stage 的目标语句 + "不做什么"边界 | "请进行 Studio E2E 探针。不要创建 Issue ..." |
| `### Must Follow` | 必须遵守的规范文档（不可少） | `docs/runbook/dev_studio_walkthrough.md` |
| `### Use As Template` | 输出结构模板（可选；某些 stage 没有模板就省略此子段） | `docs/_templates/TEMPLATE_REPO_SCAN_RESULT.md` |
| `### Consult If Affected` | 仅当涉及对应领域时参考的文档 | `docs/adr/[ADR]_006_Fail_Safe_Reads.md` |
| `Preferred Skill` | 首选 skill，加状态注释（"PR-B2 落地"等） | `/mj-agent-flow-intake`（PR-B2 落地） |
| `Use When` | 何时使用 skill；用户请求短语示例（pushy 风格） | "用户请求'评估任务' / 'intake'" |
| `Fallback` | skill 不可用时手动 / 降级路径 | "若 skill 不可用，按本 prompt Rules 手动评估..." |
| `## Rules` | 阻塞式硬约束 + HITL 触发条件 | 编号列表 |
| `## Output` | 期望输出项 + 必须含 `HITL Questions` 末项 | 列表 |

---

## 命名约定

- Stage 编号沿用 mj-agent HITL_Prompt v1.0 §1 的 17-stage 闭环（不要重新编号）
- Stage 名称：动作 + 名词（如"Repo Scan"、"Plan"）；不要用动名词（不要"Scanning Repo"）
- 跨 stage 的子流程：用 `§4.X.Y`（如 `§4.10.1 Level A 只读`）
- 新增 stage：编号从 `§4.16` 开始

---

## §1 Reference Docs 规则（沿用 HITL_Prompt §2.1）

- 标准文档用于约束行为
- 模板文档用于约束输出结构
- Plan / SPEC / ADR 用于约束任务边界
- 代码与真实数据流用于校验文档是否仍然成立
- 不要写"参考所有 docs/**"
- 如果参考文档、Issue、Plan、代码现状冲突，必须触发 HITL

## §2 Skill Hint 规则（沿用 HITL_Prompt §2.2）

若某阶段已有对应 mj-agent-* skill，应在 Prompt 中标记推荐 slash command，但不把它作为唯一执行路径。Fallback 段必须给出"skill 不可用时"的手动执行指引。

---

## 关联文档

- [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]]（本模板的目标使用场景）
- [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.10（in-tree workflow SKILL 的 schema 与 body 风格）
- [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]（v2.1 tri-track + engineering-workflow track）

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-08 | v0.1 | 初稿（与 HITL_Prompt v1.0 同 PR 落地） |
