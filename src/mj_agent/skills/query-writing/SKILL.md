---
type: skill
domain: SKILL
summary: 针对 mj-system biz 域编写与精炼 SQL 查询：表选择、时间谓词、聚合优先、可审计输出
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
version: v0.1
track: agent
activation:
  when_to_use: 用户提出需要查询业务数据的自然语言问题（指标、排名、同比、明细查看）
  when_not_to_use: 非 SQL 场景（如解释业务概念、查看系统状态、讨论方案）
tool_dependencies:
  - list_biz_tables
  - describe_biz_table
  - execute_sql
related_prompts:
  - system
---

# Skill: query-writing

Use this skill whenever you need to write or refine SQL against the
mj-system biz domain.

## Planning workflow

1. **Scope the question.** What dimension(s) and time period does the
   user care about? What is the output unit (count, sum, ratio)?
2. **Find the right table.** If you are not sure, call
   `list_biz_tables` to enumerate candidates, then `describe_biz_table`
   to pick one. Prefer DWS aggregates over DWD/ODS whenever possible.
3. **Write the SQL.**
   - Always qualify tables: `biz_dws.dws_xxx` or `biz_dwd.dwd_dim_xxx`.
   - Always include a time predicate if the table has one; unbounded
     scans are expensive and can truncate.
   - Prefer ordered, limited output: `ORDER BY ... LIMIT N`.
   - Avoid `SELECT *` on wide tables; list the columns you actually need.
4. **Execute.** Call `execute_sql(sql=...)`.
5. **Interpret.** Explain the result in a sentence or two; cite the
   column names, not raw numbers out of context.

## Common patterns

- **Daily totals:** start from a `*_daily_total` table.
- **Ranking by dimension:** use the matching `*_daily_by_<dim>` table and
  add `ORDER BY <metric> DESC LIMIT N`.
- **Joining to dimensions:** the two visible dimension tables are
  `biz_dwd.dwd_dim_product_interface` (join key `interface_id`) and
  `biz_dwd.dwd_dim_institution` (join key `tenant_code`).
- **Period-over-period:** DWS tables already carry `prev_*_*` and
  `*_diff` / `*_rate` columns — use them instead of computing yourself.

## Things to avoid

- Do NOT use `biz_ods.*` — you lack permission; the call will fail.
- Do NOT reference the `ops_*` schemas; they are out of scope.
- Do NOT emit multi-statement SQL (the `;` separator is rejected).
- Do NOT run `SELECT *` that would return more than ~500 rows; the
  result will be truncated and the `truncated` flag will trip.
