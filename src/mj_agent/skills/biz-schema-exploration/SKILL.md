---
type: skill
domain: SKILL
summary: 当用户问"biz 域有哪些表/字段/含义"等元问题时，主导 list_biz_tables / find_biz_context / describe_biz_table 路线，避免直接进 SQL
owner: 项目负责人
created: 2026-05-07
updated: 2026-05-07
state: active
version: v0.1
track: agent
activation:
  when_to_use: 用户提问明显是探索型 — "有哪些表"、"看下 X 表的字段"、"我能查什么"、"biz_dws 里都有什么"；或第一轮交互时分析师对 catalog 结构不熟
  when_not_to_use: 已经定位到具体表 + 列；问题是指标查询；问题是事实/排名等
tool_dependencies:
  - find_biz_context
  - list_biz_tables
  - describe_biz_table
related_prompts:
  - system
related_skills:
  - biz-domain-context
  - mj-ddd-semantics
---

# Skill: biz-schema-exploration

## Purpose

分析师上手 mj-agent 时常问"biz 域有哪些表 / 我能查什么 / X 表里有什么字段"——这类**元问题**不需要 SQL，需要的是**导航**。本 skill 把元问题路由到 catalog 召回 + 表清单 + 列描述三件套，避免 LLM 在没目标的情况下提前写 SQL。

与 `biz-domain-context` 边界：domain-context 是**指标问题前置**的 catalog 召回；本 skill 是**元问题主导**的 catalog 罗列。前者输入是"想算什么"，后者输入是"想知道什么"。

## When to use

触发：用户问题里出现以下任一形态——
- "biz_dws 有哪些表"
- "X 表都有什么字段 / 列"
- "我可以查什么"
- "QCM 是什么 / 包含哪些指标"
- "ETL 表都长啥样"
- 第一轮交互且分析师明显对 catalog 结构不熟

不触发：用户已经在问具体指标（→ biz-domain-context）；用户已经给了具体表名 + 想看数据（→ qcm-analysis / safe-sql-analysis）。

## Planning workflow

1. **判定问题层级**：
   - "有哪些表" / "biz_dws 里有什么" → §模式 1
   - "X 表的字段是什么" → §模式 2
   - "QCM 是什么 / 包含什么" → §模式 3
2. 调用相应工具组合，**用清晰罗列回复**——表名 + 一句简介；列名 + 类型 + comment。
3. **结尾给一个"下一步建议"**：分析师看完目录后能立即顺势提出"那帮我查 X 的 Y"，路由到下一轮指标问题。

## Common patterns

### 模式 1：表清单查询

工具序列：`list_biz_tables()` → 直接列举（按 schema 分组 + 表名 + comment）。

简化输出（避免一口气列 60+ 表）：分类汇总 + 抽样列举：
- `biz_dws.dws_qcm_*_total`：5 周期 × 2 metric = 10 张总量表
- `biz_dws.dws_qcm_*_by_<dim>`：5 周期 × 6 维度 ≈ 55 张分维表
- 3 张信号表 + 2 张维表
末了给一个"想看哪个家族 / 哪个具体表" 反询。

### 模式 2：单表字段查询

工具序列：`describe_biz_table("biz_dws.<table>")` → 列出 `name / type / nullable / comment`。补一句话"该表对应业务概念是 X"（结合 mj-ddd-semantics §模式 1）。

### 模式 3：QCM 元问题

工具序列：`find_biz_context("biz_dws QCM 包含什么")` → 用召回结果的 `metrics / periods / dimensions / signal_tables / dimension_tables` 字段总结 + 给一份"快速入门" 5 个问题候选（"最近 7 天查询量"、"Top 10 机构"、"今天数据就绪了吗"等）。

## Anti-patterns

- 不要在元问题里直接 `execute_sql`。
- 不要把整张 65 表清单一口气贴给用户——分类汇总 + 反询更可读。
- 不要重复 mj-ddd-semantics 里"业务概念→物理列"的内容；本 skill 管的是"有什么"，不是"具体怎么用"。
- 不要在已经定位表后还再次 `list_biz_tables`——浪费 token 与轮次。

## Related

- Prompts: `system`
- Tools: `find_biz_context`, `list_biz_tables`, `describe_biz_table`
- Sibling skills: `biz-domain-context`（指标前置召回）、`mj-ddd-semantics`（业务概念→物理列）
- Evals: Phase 2
