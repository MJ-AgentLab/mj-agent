---
type: skill
domain: SKILL
summary: 看到慢 SQL（statement_timeout / 大行集 / 大量 JOIN）时建议加时间谓词、改写聚合、调 LIMIT 或换表族
owner: 项目负责人
created: 2026-05-07
updated: 2026-05-07
state: active
version: v0.1
track: agent
activation:
  when_to_use: 上一轮 execute_sql 命中 statement_timeout / 返回 truncated=True / 行集过大需 estimate_tokens 才能消化；或预校验 require_time_range/require_limit 触发降级
  when_not_to_use: SQL 一次跑通且行集 ≤ 预算；用户已要求"详细列表"接受 truncated；信号表查询（不需要优化）
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

# Skill: query-optimization

## Purpose

mj-agent 的 SQL 在 4 层防线下要么 60 秒超时、要么 token 预算溢出、要么 truncated。本 skill 教 agent **碰到这些信号时怎么改写**——不是经典 DB 索引调优（那是 mj-system DBA 的事），而是**业务面的查询改写**：换聚合 / 换表族 / 收紧时间窗。

与 `safe-sql-analysis` 边界：safe-sql 管的是"撰写守则 + envelope 解读"；本 skill 是"已经撞墙后的改写策略"。两者顺序：先 safe-sql 写出第一稿 → 跑 → 如撞预算/超时/截断 → 进 query-optimization 改写。

## When to use

触发（任一）：
- 上一轮 `execute_sql` 抛 `RuntimeError: ... statement_timeout`
- envelope `truncated=True`
- envelope `precheck_warnings` 含 `require_limit` / `limit_too_large`
- `estimate_tokens` 报 `within_budget=False`

不触发：SQL 一次跑通且行集 ≤ 预算；信号表查询（小表，不优化）；用户已经接受 truncated 显式说"就要这 500 行"。

## Planning workflow

1. **诊断瓶颈类型**（来自上一轮信号）：
   - 超时（60s）→ 走 §模式 A
   - truncated → 走 §模式 B
   - 预算超 / require_limit → 走 §模式 C
2. **选改写策略**（见 §Common patterns）。
3. 把新 SQL 交给 `safe-sql-analysis` 重跑。

## Common patterns

### 模式 A：60s 超时改写

| 症状 | 改写 |
|---|---|
| 大量行 + JOIN 维表 + 多月时间窗 | 缩时间窗到月度而不是日度 |
| daily 表跨多月 | 切到 monthly _total 表的 `month_<metric>_sum`（**优先**：mj-ddd-semantics §模式 1） |
| 嵌套子查询多层 | 改 CTE，且每层加时间谓词 |
| `BETWEEN` 大跨度 + `ORDER BY` | 限制时间窗到 ≤ 30 天 + `LIMIT N` |

### 模式 B：truncated 改写

| 症状 | 改写 |
|---|---|
| 想看 Top-N 但 LIMIT 后还截断 | 加 `ORDER BY metric DESC` + `LIMIT N`（catalog `_by_<dim>` 表） |
| 想看趋势 truncated | 不要明细，换 `_total` 或 `_by_industry` 等汇总表 |
| 想看明细但行 > 500 | 分时间段查 / 上聚合工具 `aggregate(rows, group_by=...)` |

### 模式 C：token 预算溢出 / require_limit

| 症状 | 改写 |
|---|---|
| 行 ≤ 500 但 token > 5000（列宽） | `SELECT` 列收窄；不用 `*` 风格的全列 |
| 明细查询 missing LIMIT | 加 `LIMIT 500`（precheck 默认上限） |
| 用户要"全部"但实际只看趋势 | 反询确认要时间窗 / 聚合 / Top-N（hard rule 3 触发） |

## Anti-patterns

- 不要建议加索引——那是 DB 层；本 skill 只在业务面改写。
- 不要把 daily fact 表跨多月查后用工具聚合——优先选 monthly+ 表的 `daily_*_avg/std/q25/q75/median` 列（mj-ddd-semantics §模式 1）；预聚合天然省内存 + token。
- 不要为绕过 truncated 而开 `SQL_MAX_ROWS`——上限是 ADR-006/012 的契约，不是性能开关。
- 不要在 statement_timeout 后立即重试同 SQL——分析师不是傻子，重试只重撞。

## Related

- Prompts: `system`
- Tools: `find_biz_context`, `describe_biz_table`, `execute_sql`
- Upstream skill: `safe-sql-analysis`（先撰写）
- Sibling skill: `mj-ddd-semantics`（决定换哪张表族）
- Defense layers: L1b sqlglot precheck + L4 statement_timeout=60s（触发本 skill 的信号源）
- Evals: Phase 2
