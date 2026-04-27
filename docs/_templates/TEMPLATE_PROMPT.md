---
type: prompt
domain: PROMPT
summary: 20-60 字摘要，一句话说这是哪个 prompt、什么目的
owner: 项目负责人
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v1.0
model_binding: deepseek-v3
token_budget_estimate: 0
eval_references: []
supersedes: []
---

# Prompt: <prompt-name>

> **当前活跃版**位置：`src/mj_agent/prompts/<prompt-name>.md`（无 `[PROMPT]_` 前缀）
> **历史/实验版**位置：`docs/design/prompts/[PROMPT]_<Name>_vX.Y.md`
>
> `state: active` 的新版本必须在 `eval_references` 列出至少一个 `[EVAL]` 文档（A8）。
> 版本交替时，旧版 `state` 改为 `deprecated`、移动到 `docs/design/prompts/` 并补 `supersedes: [..]` 反向链接。

## Identity

Agent 在此 prompt 中扮演的身份与上下文范围。

## Principles

- 原则 1（简短）
- 原则 2

## Tools at disposal

简述 agent 可以调用的 tool 集合，并链接到对应 `[CONTRACT]` 文档（如有）。

## Hard rules

1. 硬性规则（例如"永不修改数据库"）
2. ...

## Soft rules

- 软性建议（例如"尽量用聚合而非明细"）
- ...

## Change log

| 版本 | 日期 | 变更 | EVAL 结果 |
|------|------|------|-----------|
| v1.0 | YYYY-MM-DD | 初始版本 | `[EVAL]_...` |
