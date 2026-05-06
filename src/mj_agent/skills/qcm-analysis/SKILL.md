---
type: skill
domain: SKILL
summary: 把 catalog 候选转成 QCM 高频分析模板（趋势、Top-N、同环比、ETL 信号、Ready 信号），含 curated NL→SQL 示例
owner: 项目负责人
created: 2026-05-06
updated: 2026-05-06
state: active
version: v0.1
track: agent
activation:
  when_to_use: biz-domain-context 已经给出"目标表+目标列"提案，要把它落成具体 QCM 分析 SQL（趋势 / Top-N / 同环比 / 信号）
  when_not_to_use: 非 QCM 域问题（QCM 之外的业务表家族），或 SQL 已写好只需校验时
tool_dependencies:
  - describe_biz_table
  - execute_sql
related_prompts:
  - system
related_skills:
  - biz-domain-context
  - safe-sql-analysis
---

# Skill: qcm-analysis

## Purpose

mj-agent 在 biz 域最常见的分析模式都收敛到 QCM 表族（`biz_dws.dws_qcm_*`）。本
skill 把"目标表+目标列"提案转成五类 SQL 模板：(1) 时间趋势 (2) Top-N (3) 同环比
(4) ETL 健康度 (5) Ready 信号。

本 skill 与 `biz-domain-context` 的边界：上游决定**用哪张表**，本 skill 决定
**写成什么 SQL 形态**；细节守则交给 `safe-sql-analysis`。

## When to use

触发：`biz-domain-context` 已经给出 1-2 张目标表，需要把它们落成具体的 QCM 分析
模板。常见问题形态：

- "最近 N 天/周/月的查询量趋势"
- "Top K 机构 / 行业 / 产品分类的查询量"
- "X 维度的同比 / 环比 / 趋势对比"
- "今天 QCM 数据是否就绪 / ETL 是否成功"

不触发：单纯的事实查询（"具体某机构的代码是什么"——直接走维表查询）；非 QCM 表族。

## Planning workflow

1. 从 `biz-domain-context` 拿到目标表 + 目标列 + 同环比标记。
2. 按以下五个模板择一（或组合）：见 §Common patterns。
3. 用 `describe_biz_table` 复核列名拼写——QCM 表都已加 `COMMENT ON`，列含义可信。
4. 把 SQL 草稿交给 `safe-sql-analysis` 执行（确保时间谓词、LIMIT、不 SELECT *）。
5. 拿到结果后：用 `business_summary` 字段作为基线，**重写**成业务结论（点出
   关键数字、趋势方向、是否截断）。

## Common patterns

> 以下示例使用**实际 DB 列名**（与 staged STANDARD 草案漂移；详见
> `qcm_catalog.yaml` 的 `source.drift_notes`）。**实际 SQL 中表名与列名应根据
> `find_biz_context` + `describe_biz_table` 复核后再写**——不要照搬。

### 模式 1：日度总量趋势

```sql
SELECT data_date, day_qrynum
FROM biz_dws.dws_qcm_qrynum_daily_total
WHERE data_date BETWEEN '2026-04-25' AND '2026-05-01'
ORDER BY data_date
```

### 模式 2：Top-N 机构 + 维表 JOIN

```sql
SELECT i.tenant_id,
       i.tenant_name,            -- 列名以 describe_biz_table 复核为准
       a.month_qrynum_sum
FROM biz_dws.dws_qcm_qrynum_monthly_by_tenant a
JOIN biz_dwd.dwd_dim_institution i
  ON i.tenant_id = a.tenant_id
WHERE a.month = '2026-04-01'
ORDER BY a.month_qrynum_sum DESC
LIMIT 10
```

### 模式 3：行业月度同比

```sql
SELECT ana_ind_name,
       month_qrynum_sum,
       daily_qrynum_avg,
       prev_month_daily_qrynum_avg,
       mom_daily_avg_diff,
       mom_daily_avg_rate,
       yoy_daily_avg_diff,
       yoy_daily_avg_rate
FROM biz_dws.dws_qcm_qrynum_monthly_by_industry
WHERE month = '2026-04-01'
ORDER BY yoy_daily_avg_rate DESC
LIMIT 20
```

> 注意：catalog 已经把同环比写进列里（`prev_<period>_<metric_column>` /
> `<period_abbrev>_<metric_part>_diff` / `<period_abbrev>_<metric_part>_rate`），
> **不要用窗口函数自己算**。weekly+ 表上同时存在 mom/qoq/yoy 多个对比口径。

### 模式 4：ETL 健康度

```sql
SELECT etl_batch_at, phase, table_name, status, rows_inserted, duration_ms
FROM biz_dws.dws_qcm_etl_metrics
WHERE etl_batch_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY etl_batch_at DESC
LIMIT 50
```

### 模式 5：Ready 信号

```sql
SELECT etl_batch_at, status, table_name, phase, rows_inserted, tables_processed, duration_ms
FROM biz_dws.dws_qcm_ready_signal
WHERE etl_batch_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY etl_batch_at DESC
LIMIT 20
```

## Anti-patterns

- 不要在表里没有该列时去用 `prev_*` / `*_diff` / `*_rate`——只有按维度拆分的表
  会带，先 `describe_biz_table` 确认。
- 不要为了"求精确"用 LAG() 窗口函数自己算同比——QCM 已经把列固化在表里。
- 不要把 fact 表的 COUNT(*) 当作就绪信号——用 `dws_qcm_ready_signal` 才是契约。
- 不要 JOIN 维表却忘记加 fact 侧时间谓词（按周期：`data_date / week / month /
  quarter / year`）——会触发 `require_time_range` 拦截。

## Related

- Prompts: `system`
- Tools: `describe_biz_table`, `execute_sql`
- Upstream skill: `biz-domain-context`
- Downstream skill: `safe-sql-analysis`
- Curated examples source: `D:\Document\My-Local-Vault\temp-ai-chat\mj-agent\golden_seed.jsonl`
- Evals: Phase 2 起引用 outcome / component eval
