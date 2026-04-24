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
