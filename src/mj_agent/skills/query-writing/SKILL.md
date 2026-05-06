---
type: skill
domain: SKILL
summary: 针对 mj-system biz 域编写与精炼 SQL 查询：表选择、时间谓词、聚合优先、可审计输出
owner: 项目负责人
created: 2026-04-24
updated: 2026-05-06
state: deprecated
version: v0.2
track: agent
deprecated_in_favor_of:
  - biz-domain-context
  - qcm-analysis
  - safe-sql-analysis
activation:
  when_to_use: 历史保留；不再被 agent 加载
  when_not_to_use: 任何新场景（请走 biz-domain-context / qcm-analysis / safe-sql-analysis）
tool_dependencies:
  - find_biz_context
  - list_biz_tables
  - describe_biz_table
  - execute_sql
related_prompts:
  - system
---

# Skill: query-writing (deprecated)

**MVP PR3 把本 skill 拆成 3 个职责更清晰的 skill**：`biz-domain-context` /
`qcm-analysis` / `safe-sql-analysis`。本文件保留作历史参考，不再被
`agent.py:_build_system_prompt()` 加载。新增工作请去三个新 skill 之一。

---

Use this skill whenever you need to write or refine SQL against the
mj-system biz domain.

## Purpose

把分析师的自然语言诉求翻译成一条可审计、低成本、读 DWS 优先的 SQL，并
对结果做简短的业务化解读。该 skill 的边界严格落在 mj-system biz 域：
`biz_dws.*` 全部表 + `biz_dwd` 的两张维度表（`dwd_dim_product_interface`、
`dwd_dim_institution`）—— 由 `analyst` 角色 + L1 guardrail 双重把关。

## When to use

触发：用户提出指标、排名、同比、明细查看一类需要直接落到业务数据的问题
（"上周 Q1 销售榜"、"某机构本月接口调用量"、"同比环比"等）。

不触发：用户是在解释业务概念、查看系统/进程状态、讨论方案或追问上一次
查询的解读时——这些场景应留给会话上下文或其他 skill 处理，本 skill 不
应被激活。

## Planning workflow

1. **Recall the catalog.** Call `find_biz_context(question=...)` first.
   The result tells you which metric family (`qrynum` / `tntcnt`),
   period (`daily/weekly/monthly/quarterly/yearly`), dimension suffix
   (`_total / _by_industry / _by_tenant / ...`), time column
   (`stat_date / stat_week / ...`), period-over-period column pattern
   (`prev_<period>_<metric>` / `<period_abbrev>_<metric>_diff` /
   `<period_abbrev>_<metric>_rate`), and best-guess fact table names.
2. **Scope the question.** What dimension(s) and time period does the
   user care about? What is the output unit (count, sum, ratio)?
3. **Find the right table.** Use the catalog's `candidate_table_names`
   to pick 1-2 targets; call `list_biz_tables` only if you need to
   verify availability, and `describe_biz_table` to confirm columns.
   Prefer DWS aggregates over DWD/ODS whenever possible.
4. **Write the SQL.**
   - Always qualify tables: `biz_dws.dws_xxx` or `biz_dwd.dwd_dim_xxx`.
   - `biz_dwd` is restricted to `dwd_dim_product_interface` and
     `dwd_dim_institution`; other `biz_dwd.*` references will be rejected.
   - Always include a time predicate using the period's time column
     (e.g. `stat_date` for `_daily` tables); unbounded scans are
     expensive and can truncate.
   - Prefer ordered, limited output: `ORDER BY ... LIMIT N`.
   - Avoid `SELECT *` on wide tables; list the columns you actually need.
5. **Execute.** Call `execute_sql(sql=...)`.
6. **Interpret.** Explain the result in a sentence or two; cite the
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

## Anti-patterns

- Do NOT use `biz_ods.*` — you lack permission; the call will fail.
- Do NOT reference the `ops_*` schemas; they are out of scope.
- Do NOT emit multi-statement SQL (the `;` separator is rejected).
- Do NOT run `SELECT *` that would return more than ~500 rows; the
  result will be truncated and the `truncated` flag will trip.
