# mj-agent Data-Agent MVP Framework

## Summary

构建目标：把现有 `mj-agent` 从 Phase 0 SQL 骨架推进到一个**开发态可用的 mj-system biz 域数据分析智能体 MVP**，作为路线图 v1.6 中 **Phase 1 之内的子里程碑**——本里程碑入口为 **Claude Code 开发 + LangGraph Studio 调试/试用**；路线图 v1.6 Phase 1 终态（Chainlit UI + 5 skills + 3-5 试用用户）保持不变，由后续 plan 推进。LangGraph Studio 仅作为本里程碑的开发期 Web 聊天与 trace 入口，不替代 Phase 1 的 Chainlit。

参考案例采用四条成熟模式：

- [LangChain SQL agent](https://docs.langchain.com/oss/python/langchain/sql-agent)：表发现 → schema 检索 → SQL 生成 → 校验 → 执行 → 错误修正。
- [LangGraph Studio](https://docs.langchain.com/oss/python/langgraph/studio)：本地可视化调试 agent、tool call、prompt、结果。
- [Wren AI](https://docs.getwren.ai/oss/overview/introduction)：在数据库 schema 之上增加业务语义/context layer。
- [Vanna AI](https://vanna.ai/docs)：沉淀成功 SQL/工具模式作为可复用查询记忆，并坚持权限贯穿。

## Key Changes

- 保持 Python-only LangGraph runtime，不引入前端 agent 逻辑；MVP 使用现有 `langgraph.json` + `uv run langgraph dev`。
- 在现有 SQL 三工具之上新增一个轻量 **biz semantic context layer**：QCM 指标族、周期粒度、维度后缀、同环比列、两张维表 join key、可见 schema 边界。
- 增强分析流程为：理解问题 → 召回语义上下文 → 表/列 introspection → 生成 SQL → 本地 guardrail/可选 dry-run → 执行有限结果 → 输出 SQL + 业务解释。
- 把 `query-writing` skill 拆/扩为 MVP 能力包：`biz-domain-context`、`qcm-analysis`、`safe-sql-analysis`；Phase 1 仍可静态加载，后续再做 dynamic skill selector。
- 控制数据出网：默认只返回 top-N/聚合/少量 preview rows；拒绝”全量导出”类请求，要求转成聚合或限定条件。
- **PR4 复用现有 eval 资产**而非重新设计：以 `evals-design.md` v1.1 为权威设计，以 `golden_seed.jsonl`（16 case）为种子集，以 `outcome/trajectory/component_judge.md` 为 LLM-as-judge 规则源；本 plan 不在 PR4 中重新发明 eval 架构。
- **PR2 的 SQL 预校验与 PR4 的 Component eval 共用同一规则源**（即 `component_judge.md` 中的 P0/P1 规则），避免运行时 guardrail 与 eval 检查双套漂移。

## Implementation Plan

### PR1: Semantic Context

- **Catalog 形态**：混合方案。基础 enumeration（QCM 指标族 `qrynum/tntcnt`、5 周期 `daily/weekly/monthly/quarterly/yearly`、8 维度后缀、5 时间列、5 同环比列模板 `prev_<period>_<metric>` / `<period_abbrev>_<metric>_diff` / `<period_abbrev>_<metric>_rate`、3 信号表 `dws_qcm_preprocessed_data` / `_etl_metrics` / `_ready_signal`、2 维表 join key `interface_id` / `tenant_code`）以静态 YAML 形态 mirror mj-system `[STANDARD]_Biz_DWS_Naming_Stability.md` §2–§4；具体表列与样本值走 live introspection（复用现有 `describe_biz_table`）。
- **Catalog 文件位置**：`src/mj_agent/biz_catalog/qcm_catalog.yaml`，引用 mj-system OUTPUT bundle 中 GUIDE/STANDARD 相对锚点。
- **Allowlist 收紧**：把 `BIZ_ALLOWED_SCHEMAS` 从 schema 级（`biz_dws,biz_dwd`）改为表级 allowlist；新增 `BIZ_ALLOWED_DWD_TABLES=dwd_dim_product_interface,dwd_dim_institution`；guardrail 同步检查表名。
- **新工具 `find_biz_context(question)`**：返回候选指标族、表族、周期粒度、维度后缀、时间列、同环比列、信号表 hint、join key——一次性把语义层全部交给 LLM。
- **Prompt/Skill 改写**：要求工具调用顺序为 `find_biz_context` → `list_biz_tables`（按提示过滤） → `describe_biz_table`（取 1-2 张目标表） → 写 SQL。

### PR2: Safer SQL Loop

- **预校验层**：在 `execute_sql` 之前新增 sqlglot AST 静态分析，规则源**直接复用** `component_judge.md` 中的 P0/P1 检查（`biz_domain_only`、`exclude_internal`、`require_time_range`、`use_stat_dt_not_create_dt`、`no_select_star`、合理 `LIMIT` 等）。
- **Envelope 字段**：`execute_sql` 返回必须包含 `executed_sql`、`columns`、`row_count`、`truncated`、`statement_timeout_hit`、`business_summary`（业务解释，由 LLM 生成的 1-2 句结论）。
- **拒绝/降级矩阵**：无时间谓词 → 提示加时间窗；`SELECT *` → 拒绝并要求显式列；`LIMIT > 1000` → 降级为聚合或 top-N 建议；触发 `statement_timeout` (60s) → 友好错误并建议加聚合。
- **保留** L1 正则 guardrail 作为兜底；预校验失败优先返回原因。

### PR3: MVP Analysis Skills

把现有 `query-writing` skill 拆为 3 skill，**MVP 阶段 3 skill 同时静态全载**（不引入 dynamic skill selector，待观察 token 压力后于 1.5 阶段评估）：

| Skill | 职责（hard boundary） |
|---|---|
| `biz-domain-context` | 何时调用 `find_biz_context`；如何把语义层结果转成"目标表+目标列"提案；信号表使用规则 |
| `qcm-analysis` | QCM 高频分析模板：日/周/月趋势、top tenant、行业/产品分类排行、同环比、ready signal 检查、ETL 指标检查；含 **curated NL→SQL 示例（源头：`golden_seed.jsonl`，含 reference_sql 字段）** |
| `safe-sql-analysis` | SQL 撰写守则与 envelope 输出格式；时间谓词必填；SELECT * 禁用；LIMIT/聚合策略；失败 → 修正回路 |

- 成功样例**不**写入运行时记忆；新增样例先经人工 PR 进入 `golden_seed.jsonl` 或独立的 `examples.jsonl`，再被 `qcm-analysis` skill 引用。
- 输出统一 envelope：结论、SQL、关键字段解释、数据边界/截断提示。

### PR4: Evals & Studio Runbook

**本 PR 的 eval 工作以消费现有资产为主，而非重新设计**：

- **L1 outcome eval**：用 `golden_seed.jsonl`（16 case）跑 outcome 检查，集成进 pytest（`tests/eval/test_outcome.py`）；所有 P0 case 进 smoke。
- **L3 component eval**：以 `component_judge.md` 中的 P0/P1 规则做 sqlglot 程序化检查（与 PR2 预校验共用），LLM 仅做歧义 fallback。
- **smoke 测试**：(a) 镜像 mj-system GUIDE §6.1 6 条 psql 用例；(b) 加 4 条 trajectory smoke：表发现、top-N、月度同比、拒绝 ODS/DML（与 Plan C C1 范围**合并**——见 Coordination 段）；(c) 与 `golden_seed.jsonl` 中标 P0 的 case 互查覆盖。
- **Runbook**：`docs/runbook/dev_studio_walkthrough.md`，**直接引用 Plan A 输出的 H1/H2/H3/R1/R2 evidence**，不重写；包含 `.env` 配置、`uv run langgraph dev`、Studio 打开、LangSmith tracing 开关。
- **判定**：每个 PR 都跑 `uv run pytest tests/unit`；有 DB+LLM 环境跑 `tests/integration` + `tests/eval` + `tests/smoke -m smoke`。

## Test Plan

- Unit: SQL guardrail、context retrieval、SQL envelope、prompt/skill loader。
- Integration: `list_biz_tables` 只返回 `biz_dws`/允许的 `biz_dwd`；known QCM 表可 describe；DML/ODS 被拒绝。
- Smoke: Studio/agent 可回答 “biz_dws 有哪些日度总量表”、“最近 7 天查询量趋势”、“Top 10 机构查询量”、“某行业月度同比变化”。
- Manual acceptance: 每个回答必须展示实际 SQL；不能访问 `ops_*`、`biz_ods`、非白名单 `biz_dwd`；遇到全量导出必须改问限定/聚合。
- **L1 Outcome eval**：所有 16 条 `golden_seed.jsonl` case 必须通过 outcome 检查（result_checks 全过）；难度 hard 的 3 条允许 1 条 known_failure_modes 命中。
- **L3 Component eval**：所有 P0 规则在 16 条 case 上 100% 通过；P1 规则 ≥80%。
- **GUIDE §6.1 mirror**：6 条 psql 验收 case 全部通过 mj-agent smoke 镜像版本。

## Assumptions

- 本里程碑入口使用 LangGraph Studio + Claude Code，不做生产级 Web UI；Chainlit + 5 skills 留在 Phase 1 终态由后续 plan 推进（见 Summary 顶部声明）。
- 使用现有 Volcengine Ark + DeepSeek V3 provider，不切换模型。
- 数据范围只包含 `biz_dws.*` 和两张 `biz_dwd` 维表。
- **mj-system 上游契约状态**：截至本 plan 起草时，mj-system 的 `[GUIDE]_Biz_Domain_External_Consumer_Contract.md`、`[ADR]_008_Biz_Domain_External_Consumer_Boundary.md`、`[STANDARD]_Biz_DWS_Naming_Stability.md` 仅以 staged 草稿形态存在于 `D:\Document\My-Local-Vault\temp-ai-chat\mj-system\Biz_Domain_External_Support_For_MJ_Agent_OUTPUT` bundle，**尚未合并到 mj-system/develop**。本 plan 在合并前以该 bundle 路径作为权威引用；**mj-system PR1/PR2 一旦合并，由 mj-agent owner（@ranzuozhou）触发一次 catalog 同步 PR**，把所有引用切到 mj-system 仓库相对路径，并 diff 检查 enumeration 是否被 mj-system 端微调（特别是 §6.1 用例 SQL 与 §3 命名条款）。
- **破坏性 schema 变更**：本 MVP 暂不实现"双写迁移期检测"等高级机制；若 mj-system 触发 R-3.x 类破坏性变更（rename/drop/type narrowing），mj-agent catalog 与 prompt 由 owner 手动同步；自动化检测列入 Phase 1 之后工作。

## Coordination with Parallel Plans

本 MVP plan 与 mj-agent vault 中其它 plan 的关系：

| 平行 plan | 关系 | 处理 |
|---|---|---|
| `[PLAN]_A_Studio_Walkthrough_Execution.md` | PR4 runbook 直接消费其 H1/H2/H3/R1/R2 evidence | **Plan A 应在本 plan PR4 之前完成**；PR4 runbook 不重写 walkthrough，只 reference |
| `[PLAN]_B_PR2_DB_Access_Doc.md` | PR1 catalog 文档与 db_access.md 都描述四层可见性 | PR1 catalog 文档以 Plan B 的 db_access.md 为镜像，权威源指向 mj-system GUIDE |
| `[PLAN]_C_Smoke_Expansion_and_ADR_Backfill.md` | C1（smoke #2-#4）与 PR4 smoke 完全重叠 | **C1 并入本 plan PR4**，Plan C 此后只剩 C2（ADR backfill），独立执行 |
| `[PLAN]_G_Phase_0_5_Governance_And_Onboarding_Skeleton.md` | PR3 拆 skill 需要 SKILL Authoring 模板 | 若 Plan G 在 PR3 之前完成则 PR3 使用其模板；否则 PR3 用现有 `_templates/TEMPLATE_SKILL.md`，并把 PR3 的 3 个新 skill 作为 Plan G 模板的首批使用者反哺 |
| `[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md` | 与 Plan A 关系待确认（疑似同主题不同版本） | **执行前需确认这两份 plan 是否合并**；若是同一件事保留 Plan A，废弃 Phase0 walkthrough |
| `[PLAN]_Post_PR4_Phase_0_5_Branch_Plan.md` | 描述 PR4 之后的分支策略 | 本 plan PR4 完成判定与 Post-PR4 plan 入口条件需对齐 |
| `mj-agent-roadmap.md` v1.6 | 路线图 Phase 1 = Chainlit MVP | 本 plan = Phase 1 子里程碑（已在 Summary 顶部声明） |
