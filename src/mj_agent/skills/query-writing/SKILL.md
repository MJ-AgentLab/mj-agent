---
type: skill
domain: SKILL
summary: 通用 SQL 撰写指引——biz 域 ad-hoc 查询的列选择、JOIN 取舍、时间窗收敛；与 mj-ddd-semantics + safe-sql-analysis 协作但不重叠
owner: 项目负责人
created: 2026-04-24
updated: 2026-05-07
state: active
version: v1.0
track: agent
revival_history:
  - 2026-04-24 v0.1 created (Phase 0 monolith)
  - 2026-05-06 v0.2 deprecated (MVP PR3 split into 3 skills)
  - 2026-05-07 v1.0 revived & narrowed (Phase 1 sub 1.E; scope shrunk to "通用 SQL 撰写指引")
activation:
  when_to_use: 用户问"非 QCM 模板"的 ad-hoc SQL（自由 JOIN、自定义聚合、临时探索）；或 qcm-analysis 的 5 模板都不命中时
  when_not_to_use: 用户问 QCM 五大模板（→ qcm-analysis）；用户问业务概念→列映射（→ mj-ddd-semantics）；用户问 envelope/守则（→ safe-sql-analysis）
tool_dependencies:
  - find_biz_context
  - describe_biz_table
  - execute_sql
related_prompts:
  - system
related_skills:
  - mj-ddd-semantics
  - qcm-analysis
  - safe-sql-analysis
---

# Skill: query-writing

## Purpose

Phase 0 的 monolith；MVP PR3 deprecated；Phase 1 sub 1.E **复活但职责收窄**。
本 skill 现在只承担"**ad-hoc SQL 撰写**"的部分——`qcm-analysis` 5 模板没覆盖、
但仍落在 biz 域的自由查询。

清晰的边界：

| 场景 | 归属 |
|---|---|
| QCM 五模板（趋势 / Top-N / 同环比 / ETL / Ready） | `qcm-analysis` |
| 业务概念 → 物理列选择 | `mj-ddd-semantics` |
| 撰写守则 + envelope 解读 + 失败修正回路 | `safe-sql-analysis` |
| **其它 ad-hoc 自由查询的"列怎么挑、JOIN 怎么连、时间窗怎么定"** | **本 skill** |

## When to use

触发：用户问的查询**落在 biz 域但不是 QCM 五模板**。常见形态：
- 多 metric 横向对比（同时取 qrynum + tntcnt 看占比）
- 跨周期聚合（"最近 90 天周度峰值"）
- 临时维度组合（"行业 × 产品分类"双下钻）
- 信号表 + fact 表关联（"已就绪的月份里 Top 3 机构"）

不触发：单指标 / 单维度 / 同环比 — 走 `qcm-analysis` 模板。

## Planning workflow

1. **catalog 召回**：先 `find_biz_context` 拿候选表族 + 时间列 + 同环比列。
2. **业务概念翻译**：交给 `mj-ddd-semantics` 决定 metric_part 与 time_column。
3. **本 skill 做的事**：
   - 决定 JOIN 拓扑（fact + dim / fact + signal / 多 fact 自联）
   - 收敛时间窗到合理范围（默认 ≤ 30 天明细 / ≤ 12 月聚合）
   - 选 `SELECT` 列（不 `*`；避免冗余）
4. **撰写守则**：交给 `safe-sql-analysis` 校验 + 执行 + 解读。

## Common patterns

### 模式 A：双 metric 横向对比

```sql
SELECT a.month, a.month_qrynum_sum, b.month_tntcnt_sum,
       (a.month_qrynum_sum::float / NULLIF(b.month_tntcnt_sum, 0)) AS qry_per_tenant
FROM biz_dws.dws_qcm_qrynum_monthly_total a
JOIN biz_dws.dws_qcm_tntcnt_monthly_total b USING (month)
WHERE a.month >= '2026-01-01'
ORDER BY a.month
```

### 模式 B：跨周期聚合（agg 工具兜底）

如果 catalog 直接没现成"周度峰值"列，先 daily 拉数 + 工具 `aggregate(rows, group_by=['week'], aggregations={'day_qrynum': 'max'})`。但**首选**：换到 `dws_qcm_qrynum_weekly_total` 的 `daily_qrynum_max` 列（mj-ddd-semantics §模式 1）。

### 模式 C：信号 + fact 关联

```sql
WITH ready AS (
  SELECT DISTINCT DATE_TRUNC('month', etl_batch_at) AS month
  FROM biz_dws.dws_qcm_ready_signal
  WHERE status = 'success'
)
SELECT i.tenant_name, a.month, a.month_qrynum_sum
FROM biz_dws.dws_qcm_qrynum_monthly_by_tenant a
JOIN biz_dwd.dwd_dim_institution i ON i.tenant_id = a.tenant_id
JOIN ready r ON r.month = a.month
ORDER BY a.month_qrynum_sum DESC
LIMIT 30
```

## Anti-patterns

- 不要复述 `qcm-analysis` 的 5 模板——本 skill 不是 QCM 模板替身。
- 不要重新定义"业务概念→物理列"——交给 `mj-ddd-semantics`。
- 不要重新写 envelope / 拒绝/降级守则——交给 `safe-sql-analysis`。
- 不要为了"复杂"加多层嵌套子查询——优先 CTE，每层单一职责。
- 不要 `SELECT *`（precheck 会拒）。

## Related

- Prompts: `system`
- Tools: `find_biz_context`, `describe_biz_table`, `execute_sql`
- Sibling skills: `mj-ddd-semantics`（列选择决策）、`qcm-analysis`（五模板）、`safe-sql-analysis`（撰写守则）
- Evals: Phase 2
