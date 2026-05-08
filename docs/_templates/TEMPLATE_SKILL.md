---
type: skill
domain: SKILL
summary: 20-60 字摘要，一句话说这个 skill 什么时候用、干什么
owner: 项目负责人
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v0.1
track: agent
activation:
  when_to_use: 用户问题触发此 skill 的典型情形
  when_not_to_use: 明显不应该走这个 skill 的情形
tool_dependencies: []
related_prompts: []
---

# Skill: <skill-name>

> **此模板用于 `src/mj_agent/skills/<skill-name>/SKILL.md`**（in-source runtime SKILL；Track B；Agent_Side §2 13-field schema + 五段式 body；由 `load_skill()` Python loader 加载并剥 frontmatter 注入 LLM 上下文）。
>
> **不**用本模板：
> - 起草 `.claude/skills/mj-agent-<group>-<verb>/SKILL.md`（in-tree workflow skill；engineering-workflow track；ADR-013 native 2-field schema；由 Claude Code 主进程发现）→ 用 [[TEMPLATE_WORKFLOW_SKILL|TEMPLATE_WORKFLOW_SKILL]]
> - 起草 marketplace plugin SKILL.md（出本仓 governance）→ 参考 [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] §Decision 内嵌范本
>
> 三类 SKILL 区分速查见 [[../../CLAUDE|CLAUDE.md]] §"Three-source SKILL distinction"（in-source / in-tree / marketplace plugin 三类同名同形不同义；治理 track / loader / schema 各异，必须严格区分）。
>
> 复制本模板后：文件名固定为 `SKILL.md`，**目录名**即 skill 身份（与 frontmatter 中的身份一致）。目录名使用全小写带连字符：`query-writing`、`mj-ddd-semantics`。

## Purpose

一段描述：这个 skill 存在的原因。它解决什么类别的问题？
和其他 skill 的分工边界在哪里？

## When to use

列出典型触发场景（多用场景描述而非关键词列表）。

## Planning workflow

该 skill 在被激活后，agent 应当按以下步骤工作：

1. 步骤一
2. 步骤二
3. ...

## Common patterns

- **模式 A**：简述该模式适用的情形与 SQL/工具调用范式
- **模式 B**：...

## Anti-patterns

- 不要做的事 1
- 不要做的事 2

## Related

- Prompts: 列出会激活此 skill 的 prompt（与 frontmatter.related_prompts 对齐）
- Tools: 列出此 skill 频繁使用的 tool（与 frontmatter.tool_dependencies 对齐）
- Evals: Phase 2 起引用该 skill 的 `[EVAL]` 文档
