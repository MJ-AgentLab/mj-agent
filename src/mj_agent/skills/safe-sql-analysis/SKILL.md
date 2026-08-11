---
type: skill
domain: SKILL
summary: SQL 撰写守则与执行 envelope：时间谓词必填、SELECT * 禁用、LIMIT 策略、失败修正回路
owner: 项目负责人
created: 2026-05-06
updated: 2026-08-11
state: active
version: v0.2
track: agent
activation:
  when_to_use: 已有 SQL 草稿（来自 qcm-analysis 或用户直接给出），需要校验+执行+解读
  when_not_to_use: 还没决定目标表（先走 biz-domain-context），或问题不是 SQL 类
tool_dependencies:
  - execute_sql
related_prompts:
  - system
related_skills:
  - biz-domain-context
  - qcm-analysis
---

# Skill: safe-sql-analysis

## Purpose

SQL 在 mj-agent 是穿越四层防线的最后一公里：L1 hybrid guardrail（regex 关键字扫描 + AST allowlist） → L1b sqlglot AST
预校验 → L3 read-only 连接 → L4 DB GRANT。本 skill 教 agent **怎样写一条不会被拦
下的 SQL**，并给出执行后的 envelope 解读规范与失败时的修正回路。

本 skill 的边界：**不挑表（biz-domain-context 管），不写业务模板（qcm-analysis 管）**，
只关心 SQL 形态合规与结果解读。

## When to use

触发：已有 SQL 草稿（来自 `qcm-analysis` 模板生成、或用户直接给出），准备执行。

不触发：还在思考要不要查（先走 `biz-domain-context`）；用户问的不是 SQL 类问题。

## Planning workflow

1. **撰写守则自检**（不调工具，agent 自己跑一遍清单）：
   - [ ] **【最关键 — precheck 必查】时间列谓词必填**（按周期，**实际 DB 列名**：
     `data_date`(daily) / `week` / `month` / `quarter` / `year`；STANDARD 草案
     的 `stat_*` 在实际 DB 不存在）。**用户没说窗口** → 默认最近 30 天 (daily) /
     3 月 (monthly) / 4 季 (quarterly) / 3 年 (yearly)，并在回复里说明所选窗口。
     Top-N 明细查询同样需要时间谓词 — precheck 与 `LIMIT` 无关。详见
     `prompts/system.md` Hard rule #9。
   - [ ] 全部 schema 限定：`biz_dws.<table>` 或 `biz_dwd.<table>`
   - [ ] 仅 `dwd_dim_product_interface` / `dwd_dim_institution` 两张维表
   - [ ] 没有 `SELECT *`（含 `JOIN` 时也是）
   - [ ] 明细查询带 `LIMIT N`（N ≤ 1000）；聚合查询免 LIMIT
   - [ ] 单语句，不带分号链
2. **调 `execute_sql(sql=...)`** ——成功返回 envelope；失败返回 `ValueError`/`RuntimeError`。
3. **读 envelope**：
   - `executed_sql`：核对实际执行的 SQL（用于审计）
   - `columns / rows / row_count`：结果数据
   - `truncated=True`：被截断到 SQL_MAX_ROWS；告诉用户"还有更多，请加聚合或缩范围"
   - `statement_timeout_hit=True` 或 `RuntimeError` 含"statement_timeout"：
     用户友好提示 + 建议聚合或缩时间范围
   - `precheck_warnings`：P1 级别，**不阻断**但要在回复里向用户提示
   - `business_summary`：启发式占位句，**必须重写**成业务结论
4. **失败修正回路**：
   - `no_select_star` → 改成显式列名后重试
   - `require_time_range` → 加上时间谓词（按周期 `data_date / week / month /
     quarter / year`）后重试
   - `multi-statement` → 拆成单语句
   - `schema/table not in allowlist` → 检查表名拼写；返回 `find_biz_context` 重新选表
   - `database error: ... permission denied` → 该表分析师角色无权访问，告诉用户
   - `database error: ... does not exist` → 表名错；用 `list_biz_tables` 确认

## Common patterns

### 模式 A：聚合优先

```sql
SELECT ana_ind_name, SUM(month_qrynum_sum) AS total_qrynum
FROM biz_dws.dws_qcm_qrynum_monthly_by_industry
WHERE month = '2026-04-01'
GROUP BY ana_ind_name
ORDER BY total_qrynum DESC
LIMIT 20
```

### 模式 B：明细查询带 LIMIT

```sql
SELECT data_date, tenant_id, day_qrynum
FROM biz_dws.dws_qcm_qrynum_daily_by_tenant
WHERE data_date >= '2026-04-25'
ORDER BY data_date DESC, day_qrynum DESC
LIMIT 100
```

### 模式 C：维表 JOIN（注意时间谓词在 fact 侧）

```sql
SELECT i.tenant_id, i.tenant_name, a.month_qrynum_sum
FROM biz_dws.dws_qcm_qrynum_monthly_by_tenant a
JOIN biz_dwd.dwd_dim_institution i ON i.tenant_id = a.tenant_id
WHERE a.month = '2026-04-01'
ORDER BY a.month_qrynum_sum DESC
LIMIT 10
```

### 模式 D：Top-N 用户没说窗口（默认最近 30 天 + 回复里说明）

用户问 "查 top 10 产品的成交量" 没给时间窗口时，**不要**生成无时间谓词的
SELECT（会被 precheck 拒绝、白浪费一个 turn），按 system.md Hard rule #9
默认最近 30 天 (daily fact) / 3 月 (monthly fact) 等，并在最终回复里
说明所选窗口（"以最近 30 天为窗口"）。

```sql
-- 用户问：top 10 产品的成交量（没说时间窗口）
-- → 默认最近 30 天 + 回复说明
SELECT pcat_l1, SUM(day_qrynum) AS qrynum_30d
FROM biz_dws.dws_qcm_qrynum_daily_by_product
WHERE data_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY pcat_l1
ORDER BY qrynum_30d DESC
LIMIT 10
```

## Anti-patterns

- 不要在 `JOIN` 里写 `biz_dwd.dwd_qvl_*` / `biz_dwd.dwd_fact_*` 之类——L1 即拒。
- 不要为了避开 `require_time_range` 把时间列写进 `SELECT` 但不进 `WHERE`——
  precheck 看的是 WHERE 中的列引用。
- 不要直接把 `business_summary` 原样回给用户——它是模板提示，不是业务结论。
- 不要在结果里用"约 N 条"等模糊措辞——`row_count` / `truncated` 字段是精确的，
  说清楚"返回 30 行；未截断"或"返回 500 行；已被截断到 500，仍有更多"。
- 不要忽略 `precheck_warnings`——`limit_too_large` / `require_limit` 等出现时
  应建议用户聚合或缩窄。

## Related

- Prompts: `system`
- Tools: `execute_sql`
- Upstream skills: `biz-domain-context`, `qcm-analysis`
- Defense layers: L1 `tools/sql/guardrail.py`, L1b `tools/sql/precheck.py`,
  L2 本 SKILL.md 的可见表语义, L3 `integrations/mj_system_db.py`,
  L4 mj-system `R__analyst_permissions.sql`
- Evals: Phase 2 起引用 outcome / component eval
