---
type: skill
domain: SKILL
summary: biz 域 DDD 语义层 — 把"业务概念（查询量 / 机构数 / 同环比）"映射到具体物理列；把 catalog 召回结果转成可写 SQL 的字段清单
owner: 项目负责人
created: 2026-05-07
updated: 2026-05-07
state: active
version: v0.1
track: agent
activation:
  when_to_use: 拿到 find_biz_context 候选表后，需要决定"用户问的'查询量'到底指哪个物理列"——day_qrynum 还是 day_qrynum_sum 还是 daily_qrynum_avg？
  when_not_to_use: 还没召回到候选表（先走 biz-domain-context）；问题是事实查询（具体某机构代号 → 走 entity_lookup 即可）；非 QCM 表族
tool_dependencies:
  - find_biz_context
  - describe_biz_table
  - entity_lookup
related_prompts:
  - system
related_skills:
  - biz-domain-context
  - qcm-analysis
  - safe-sql-analysis
---

# Skill: mj-ddd-semantics

## Purpose

biz 域用户问的"查询量"、"机构数"、"同比"是**业务概念**；DB 里实际存在的是**物理列**——daily 周期叫 `day_qrynum`，weekly+ 周期叫 `<period>_<metric>_sum + daily_<metric>_avg/max/min/std/q25/median/q75` 一族 8 列。**本 skill 的职责是把业务概念翻译成正确的物理列选择**，让 LLM 在写 SQL 之前就避免选错列。

与上下游 skill 的边界：

| Skill | 职责 |
|---|---|
| `biz-domain-context` | 召回候选表（"用户问月度趋势 → 候选 `dws_qcm_qrynum_monthly_total`"） |
| **`mj-ddd-semantics`（本 skill）** | **把候选表的物理列翻译成业务语义** |
| `qcm-analysis` | 把翻译结果落成 5 类高频 SQL 模板 |
| `safe-sql-analysis` | SQL 撰写守则与 envelope 解读 |

## When to use

触发：拿到 `find_biz_context` 候选表后，问题里有以下任一形态——
- "查询量"/"机构数"等指标词
- "同比"/"环比"/"对比上月"等周期比较
- "增长率"/"占比"等相对量
- "活跃机构"/"新增机构"/"首次出现" 等机构生命周期概念
- "分位数"/"中位数"/"P75" 等统计分布概念

不触发：纯事实查询（具体名字、代码、ID 映射 → entity_lookup）；DDL/DML 类问题（不允许）；元数据问题（直接读信号表）。

## Planning workflow

1. **从 `find_biz_context` 取候选表**。识别 `period` 槽位：daily / weekly / monthly / quarterly / yearly。
2. **决定 metric_part**（关键步骤）：参见 §Common patterns 的 metric 列形态表。
3. **决定 time_column**：`data_date` (daily) / `week` / `month` / `quarter` / `year`（实际 DB 命名，drift from STANDARD §2.1；见 `qcm_catalog.yaml` source.drift_notes）。
4. **决定同环比列**：catalog 里的 `prev_<period>_<metric_column>` / `<abbrev>_<metric_part>_diff` / `<abbrev>_<metric_part>_rate` 已在表里（`yoy_*` 在 monthly+ 表上也有）；**禁用** LAG 自己算，除非 catalog 没该列。
5. **决定维表 JOIN**：按 dimension suffix 决定 join 哪张维表 + join key（见 §维表 JOIN 速查）。
6. **把决策结果交给 `qcm-analysis` 落成 SQL**，再交给 `safe-sql-analysis` 执行。

## Common patterns

### 模式 1：metric 列形态 by period（**最重要**）

`<metric>` ∈ {qrynum, tntcnt}；`<period>` ∈ {day, week, month, quarter, year}。

| 周期 | _total 主指标列 | 分位数族（仅 weekly+ 有） |
|---|---|---|
| daily | `day_<metric>` (单值；e.g. `day_qrynum`) | — |
| weekly | `week_<metric>_sum` (周累计) | `daily_<metric>_{avg,max,min,std,q25,median,q75}` |
| monthly | `month_<metric>_sum` | `daily_<metric>_{avg,max,min,std,q25,median,q75}` |
| quarterly | `quarter_<metric>_sum` | 同上 |
| yearly | `year_<metric>_sum` | 同上 |

**业务概念 → 物理列**：

| 用户说 | period=daily | period=monthly+（推荐） |
|---|---|---|
| "上海银行 4 月查询量" | `day_qrynum`（按日 SUM 后） | `month_qrynum_sum`（直接读，无需聚合） |
| "上海银行 4 月日均查询量" | `AVG(day_qrynum)` | `daily_qrynum_avg`（直接读） |
| "上海银行 4 月查询量峰值" | `MAX(day_qrynum)` | `daily_qrynum_max`（直接读） |
| "上海银行 4 月查询量波动" | 自己 stddev | `daily_qrynum_std`（直接读） |
| "上海银行 4 月查询量分布 P75" | 自己 percentile_cont | `daily_qrynum_q75`（直接读） |

**关键启发式**：用户问"日均/峰值/波动/分位数"时，**优先选 monthly+ 的 `_total` 表里的 `daily_*_avg/max/std/q25/median/q75` 列**——它们已经按月预聚合，省一次窗口函数 + token 预算更友好。

### 模式 2：同环比列直接读

| 用户说 | 列（取自 catalog `period_over_period_columns`） |
|---|---|
| "上月查询量" | `prev_<period>_<metric_column>`（e.g. `prev_month_daily_qrynum_avg`） |
| "环比变化" | `<abbrev>_<metric_part>_diff` (e.g. `mom_daily_avg_diff`) |
| "环比增长率" | `<abbrev>_<metric_part>_rate` |
| "去年同期" / "yoy" | monthly+ 表上有 `yoy_<metric_part>_{diff,rate}` 列（即便 abbrev 是 mom/qoq） |

**禁用**：`LAG(metric) OVER (...)` 自算，除非 catalog 该表没对应的 `prev_*` 列。

### 模式 3：机构生命周期概念

| 用户说 | 物理列（仅 `_total` 表上有） |
|---|---|
| "活跃机构数" / "活跃天数" | `hist_active_<period>s_count` (e.g. `hist_active_days_count`) |
| "首次出现" | `first_used_at` |
| "最近一次出现" | `last_used_at` |
| "历史累计查询量" | `hist_qrynum_sum` |
| "当日占累计百分比" | `hist_day_qrynum_pct` |

### 模式 4：信号表是元数据，不是 fact

碰到"今天数据准备好了吗 / ETL 是否成功"问题：

| 用户问题 | 表 |
|---|---|
| 当批 ETL 是否就绪 | `dws_qcm_ready_signal` |
| ETL 阶段执行明细 | `dws_qcm_etl_metrics` |
| 预处理状态 | `dws_qcm_preprocessed_data` |

**禁止**用 fact 表 `COUNT(*)` 推断就绪；信号表是契约。

### 模式 5：维表 JOIN 速查

| dimension suffix | join 表 | join key |
|---|---|---|
| `_by_tenant` / `_by_tenant_pcat_l1` / `_by_tenant_pcat_l2` | `biz_dwd.dwd_dim_institution` | `tenant_id` |
| 其它 by_* (industry / pcat_l1 / pcat_l2 / scenario) | 不需要 JOIN（dim 列就在 fact 表里） |
| 涉及 `interface_id` 字段 | `biz_dwd.dwd_dim_product_interface` | `interface_id` |

**注意**：用户给的"上海银行" → 先 `entity_lookup` 拿 `tenant_id`，再 JOIN dim 表取 `tenant_name` 显示。

## Anti-patterns

- **不要在 daily 周期用 `_sum` 列**：daily `_total` 表只有 `day_<metric>`，没有 `day_<metric>_sum`；用错会 ColumnNotFound。
- **不要在 daily 周期找 `daily_<metric>_avg`**：分位数族仅 weekly+ 才有；daily 已经是单日值无需"日均"。
- **不要用 LAG 算同环比**：catalog 已经把 prev/diff/rate 固化在表上，省一次窗口函数 + 与 STANDARD 命名一致。
- **不要假设 metric_part 等于 metric**：在 weekly+ 上 `mom_daily_avg_diff` 的 `metric_part` 是 `daily_avg`（衍生量），不是 `<metric>` 本身。
- **不要从 fact 表 COUNT(*) 估当批就绪状态**：用 `dws_qcm_ready_signal`。
- **不要 JOIN `_by_industry / _by_pcat_l1 / _by_pcat_l2 / _by_scenario` 到 dim 表**：dim 列直接在 fact 表，JOIN 浪费。

## Related

- Prompts: `system`
- Tools: `find_biz_context`, `describe_biz_table`, `entity_lookup`
- Upstream skill: `biz-domain-context`
- Downstream skills: `qcm-analysis`（落 SQL 模板）、`safe-sql-analysis`（执行守则）
- Catalog: `src/mj_agent/biz_catalog/qcm_catalog.yaml`
- 维护（Phase 1 阶段）：`scripts/fetch_biz_schema.py` + `scripts/diff_biz_schema.py` 是**手动**对账工具，由维护者本地按需运行；schema 漂移的自动同步机制规划在 **Phase 2**（见 `plans/mj-agent-roadmap-v1.6.md` §4.4 "schema 自动同步"）。Phase 1 阶段，schema 漂移由 `tests/contract/*` 测试 fail 触发分析师手动修正 catalog / SKILL
- Evals: Phase 2 起引用 outcome / component eval；契约测试在 Phase 1 sub 1.G 落地
