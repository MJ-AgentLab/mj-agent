---
type: skill
domain: SKILL
summary: 用户要"上月报告 / 月报"时一键拼装：总量 + Top-N 机构 + 行业排行 + 同比环比 + 趋势 + ETL 就绪信号
owner: 项目负责人
created: 2026-05-07
updated: 2026-05-07
state: active
version: v0.1
track: agent
activation:
  when_to_use: 用户问 "上月报告" / "月报" / "X 月数据复盘" / "monthly report" — 需要把多个指标横切组合输出
  when_not_to_use: 单指标问询（→ qcm-analysis 模板 1-3）；周报 / 日报（节奏不同；本 skill 仅 Phase 1 月度）
tool_dependencies:
  - find_biz_context
  - describe_biz_table
  - execute_sql
  - aggregate
  - drill_down
  - estimate_tokens
related_prompts:
  - system
related_skills:
  - biz-domain-context
  - mj-ddd-semantics
  - qcm-analysis
  - safe-sql-analysis
---

# Skill: monthly-report

## Purpose

把"月报"这个高频复合问题拆成 5 块固定结构，每块对应一个 SQL 查询，最后拼成 Markdown 报告。这是 Phase 1 退出标准 E4（月报场景端到端跑通）的主载体。

## When to use

触发：用户明确说 "上月报告"、"月报"、"X 月数据复盘"、"做一份 4 月 report"、"monthly report"。

不触发：单指标查询（用 qcm-analysis 模板）；周报 / 日报（节奏不同；本 skill 只覆盖月度，周/日报留 Phase 1.5）。

## Planning workflow

1. **确认月份**：默认上一个完整月（CURRENT_DATE - INTERVAL '1 month' 的月份）。若用户明指（如"4 月"）按用户指定。
2. **确认范围**：默认全量；若用户给特定机构/行业/产品，先 `entity_lookup` 校准 → 把 `tenant_id` / `pcat_l1` 注入每个查询的 WHERE。
3. **依次跑 5 个模块**（每模块 1 SQL，全部 monthly 表 + 聚合列优先）：见 §Common patterns。
4. **拼装 Markdown 输出**：5 个 §小节 + 引用具体数字 + 关键变化标星 + 数据边界提示。

## Common patterns

### 模块 1：总量与同比

```sql
SELECT month, month_qrynum_sum, daily_qrynum_avg,
       prev_month_daily_qrynum_avg, mom_daily_avg_diff, mom_daily_avg_rate,
       yoy_prev_daily_qrynum_avg,   yoy_daily_avg_diff,  yoy_daily_avg_rate
FROM biz_dws.dws_qcm_qrynum_monthly_total
WHERE month = '<目标月>'
```

### 模块 2：Top 10 机构

```sql
SELECT i.tenant_id, i.tenant_name, a.month_qrynum_sum, a.daily_qrynum_avg,
       a.mom_daily_avg_rate, a.yoy_daily_avg_rate
FROM biz_dws.dws_qcm_qrynum_monthly_by_tenant a
JOIN biz_dwd.dwd_dim_institution i ON i.tenant_id = a.tenant_id
WHERE a.month = '<目标月>'
ORDER BY a.month_qrynum_sum DESC LIMIT 10
```

### 模块 3：行业排行

```sql
SELECT ana_ind_name, month_qrynum_sum, daily_qrynum_avg,
       mom_daily_avg_rate, yoy_daily_avg_rate
FROM biz_dws.dws_qcm_qrynum_monthly_by_industry
WHERE month = '<目标月>'
ORDER BY month_qrynum_sum DESC LIMIT 10
```

### 模块 4：日内趋势

```sql
SELECT data_date, day_qrynum, dod_qrynum_diff, dod_qrynum_rate
FROM biz_dws.dws_qcm_qrynum_daily_total
WHERE data_date >= DATE_TRUNC('month', '<目标月>'::date)
  AND data_date <  DATE_TRUNC('month', '<目标月>'::date) + INTERVAL '1 month'
ORDER BY data_date
```

### 模块 5：ETL 就绪 + 数据边界

```sql
SELECT etl_batch_at, status, table_name, phase, rows_inserted
FROM biz_dws.dws_qcm_ready_signal
WHERE etl_batch_at >= DATE_TRUNC('month', '<目标月>'::date)
ORDER BY etl_batch_at DESC LIMIT 5
```

## Output structure

```markdown
# <目标月> 月报

> 数据范围：<目标月> | 数据源：biz_dws.dws_qcm_*_monthly_*
> ETL 就绪：<状态摘要 from 模块 5>

## 总量
- 月度查询量：<month_qrynum_sum>，日均 <daily_qrynum_avg>
- 环比：<mom_diff> (<mom_rate>%)
- 同比：<yoy_diff> (<yoy_rate>%)

## Top 10 机构（按月度查询量）
| 排名 | 机构 | 月度查询量 | 日均 | 环比 | 同比 |

## 行业排行
| 行业 | 月度查询量 | 占比 | 同比 |

## 日内趋势
| 日期 | 当日查询量 | 环比变化 |

## 关注点
- <显著上涨 / 下跌 / 异常说明，引 detect_anomaly 标记若有>
```

## Anti-patterns

- 不要为了"全面"加更多模块（如 weekly 拆分 / 客户细分）——Phase 1 月报锁定 5 模块；要更多走单独 follow-up 问询。
- 不要重复跑 5 个查询都带相同 `WHERE month`——可以并行；但每模块独立 execute_sql（envelope 干净）。
- 不要把模块 1 的同比 / 环比再用 LAG 自算——直接读 `mom_*` / `yoy_*` 列（mj-ddd-semantics §模式 2）。
- 不要在 Output 里贴整张明细表（>50 行）——超 token 预算 + 用户难读。

## Related

- Prompts: `system`
- Tools: `find_biz_context`, `describe_biz_table`, `execute_sql`, `aggregate`, `drill_down`, `estimate_tokens`
- Sibling skills: `biz-domain-context`（前置）、`mj-ddd-semantics`（列选择）、`qcm-analysis`（5 模板）、`safe-sql-analysis`（执行守则）
- 退出标准映射：roadmap §4 E4（月报场景端到端跑通）
- Evals: Phase 2 起接 Outcome judge "monthly report" case
