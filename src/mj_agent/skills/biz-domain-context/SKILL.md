---
type: skill
domain: SKILL
summary: 当用户提问业务指标时先用 find_biz_context 召回语义层，再把候选转成"目标表+目标列"提案
owner: 项目负责人
created: 2026-05-06
updated: 2026-05-06
state: active
version: v0.1
track: agent
activation:
  when_to_use: 用户问及任何 biz 域指标（查询量、机构数、行业排名、产品分类、ETL/Ready 信号），需要把自然语言映射到 catalog
  when_not_to_use: 已经明确给出目标表和目标列的精准 SQL 请求；非 biz 域问题
tool_dependencies:
  - find_biz_context
  - list_biz_tables
  - describe_biz_table
related_prompts:
  - system
---

# Skill: biz-domain-context

## Purpose

把分析师的自然语言诉求映射到 mj-system biz 域的 **catalog 语义**：哪个 metric 家族
（`qrynum` / `tntcnt`）、哪个周期（`daily/weekly/monthly/quarterly/yearly`）、哪个
维度后缀（`_total / _by_industry / _by_tenant / _by_pcat_l1 / _by_pcat_l2 /
_by_tenant_pcat_l1 / _by_tenant_pcat_l2 / _by_scenario`），再据此提出"目标表+目标列"
草案——交给下游 skill 完成 SQL 撰写与执行。

本 skill 的边界：**只做语义召回与表族提案，不写 SQL，不下断言**。

## When to use

触发：用户提到任何 biz 域指标、机构、行业、产品分类、场景、同/环比、ETL 状态、
数据就绪信号——只要问题落到"业务数据"四个字，本 skill 就是入口。

不触发：用户已经精确指定 `biz_dws.dws_qcm_<X>_<period>_<dim>` 表名时；非业务的
对话（解释概念、讨论方案、查看进程状态）。

## Planning workflow

1. **召回 catalog**：调用 `find_biz_context(question="<原问题>")`。结果含
   `candidate_metrics / candidate_periods / candidate_dimensions / time_columns /
   period_abbreviations / period_over_period_patterns / signal_tables /
   dimension_tables / candidate_table_names / forbidden_access / runtime_constraints`。
2. **看 notes 字段**：若 `notes` 含"未识别明确指标关键词，返回全部候选"等提示，
   表明问题语义不清——优先回到用户澄清，而非盲选。
3. **挑表族**：从 `candidate_table_names` 取 1-2 个最像目标的表名。一般原则：
   - 单一指标，无维度拆分 → `_total` 后缀
   - "Top N <对象>" → `_by_<对象>` 后缀
   - 出现"同比/环比/对比" → `needs_period_over_period=True` 时调用方应保留
     `period_over_period_patterns` 字段供后续 SQL 撰写
4. **校验可见性**：若不确定候选表是否真的可查，调用 `list_biz_tables`，匹配
   schema + table_name；只关注 `is_table_allowed = True` 的表。
5. **取目标表的列结构**：选定 1-2 张表后调用 `describe_biz_table(name=<schema.table>)`
   拿到列清单。把"目标表+目标列+时间列+同环比列"以结构化形式交给 `qcm-analysis`
   或 `safe-sql-analysis`。

## Common patterns

- **指标 + 总量**："最近 7 天的查询量" →
  `find_biz_context` → 候选 `dws_qcm_qrynum_daily_total` → `describe_biz_table` 取
  `stat_date / qrynum` → 交给下游 skill 写 SQL。
- **指标 + 维度**："Top 10 机构月度查询量" →
  候选 `dws_qcm_qrynum_monthly_by_tenant` → 列含 `stat_month / tenant_code / qrynum` →
  下游 SQL 加 `ORDER BY qrynum DESC LIMIT 10`，并 JOIN
  `biz_dwd.dwd_dim_institution` (`tenant_code`) 取机构名称。
- **同环比**："某行业月度同比变化" →
  候选 `dws_qcm_qrynum_monthly_by_industry`；列含 `prev_month_qrynum / mom_qrynum_diff
  / mom_qrynum_rate`——直接取列，不要自己 LAG()。
- **信号检查**："今天的 QCM 数据准备好了吗" → 只读 `signal_tables` 列表里的 3 张表
  （`dws_qcm_preprocessed_data` / `dws_qcm_etl_metrics` / `dws_qcm_ready_signal`），
  **不要去 fact 表用 COUNT 推断**。

## Anti-patterns

- 不要跳过 `find_biz_context` 直接 `list_biz_tables` ——你会得到 65+3+2 张表，
  浪费 token 与轮次。
- 不要把 `find_biz_context` 的输出原封不动塞进 SQL 上下文——它是导航地图，不是答案。
- 不要在本 skill 里写 SQL；本 skill 的唯一产物是"目标表+目标列+时间列"清单。
- 不要尝试访问 `forbidden_access` 中列出的 schema (`biz_ods` / `biz_ads` /
  `ops_*`)——L1 guardrail 会拒绝。
- 不要把 `biz_dwd.*` 当 fact 表来读；目前只暴露 `dwd_dim_product_interface` /
  `dwd_dim_institution` 两张维表。

## Related

- Prompts: `system`
- Tools: `find_biz_context`, `list_biz_tables`, `describe_biz_table`
- Downstream skills: `qcm-analysis`（QCM 模板）、`safe-sql-analysis`（撰写守则）
- Catalog: `src/mj_agent/biz_catalog/qcm_catalog.yaml`
- Evals: Phase 2 起引用 outcome / component eval
