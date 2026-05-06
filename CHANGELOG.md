# Changelog

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added — MVP (data-agent-mvp PR1-PR4, branched off develop@9f0cdfe)

- **PR1 — biz 域语义上下文层（`feat(agent)`，6a0206c）**：新增 `src/mj_agent/biz_catalog/` 包（`qcm_catalog.yaml` 静态镜像 mj-system `[STANDARD]_Biz_DWS_Naming_Stability.md` §2-§4 + `loader.py` + `finder.py`）；新增 LLM 工具 `find_biz_context(question)` 一次性回吐候选 metric / period / dimension / 时间列 / 同环比列 / 信号表 / 维表 join key；表级 allowlist 收紧——`BIZ_ALLOWED_DWD_TABLES=dwd_dim_product_interface,dwd_dim_institution`，guardrail/`introspect`/`execute_sql` 全部走 `settings.is_table_allowed`；prompt v1.0→v1.1 + skill v0.1→v0.2 钉死工具调用顺序 `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`；新增 `pyyaml` 运行时依赖与 `types-PyYAML` 开发依赖；新增 27 单元测试。
- **PR2 — sqlglot AST 预校验 + execute_sql envelope 扩展（`feat(sql)`，16ab5f9）**：新增 `src/mj_agent/tools/sql/precheck.py`（与 `[PROMPT]_component_judge.md` 的 P0/P1 规则**共用规则源**：`no_select_star`、`require_time_range` on biz_dws fact tables、`require_limit` 非聚合明细、`limit_too_large > 1000`，parse 失败优雅降级到 DB 校验）；`execute_sql` envelope 扩展为 `executed_sql / columns / rows / row_count / truncated / statement_timeout_hit / business_summary / precheck_warnings`；显式捕获 `psycopg.errors.QueryCanceled` 并重抛友好错误（提示加聚合 / 缩时间 / 减 JOIN）；新增 `sqlglot>=25.0` 运行时依赖；prompt v1.1→v1.2 文档新 envelope 与 AST precheck；新增 13 单元测试。
- **PR3 — query-writing 拆 3 skill（`feat(skill)`，806db05）**：`src/mj_agent/skills/{biz-domain-context,qcm-analysis,safe-sql-analysis}/SKILL.md` 各自 v0.1 active；MVP 阶段静态全载（`agent.py:_ACTIVE_SKILLS` 元组），dynamic skill selector 推迟到 1.5；老 `query-writing` 标 `state: deprecated` + `deprecated_in_favor_of`，文件保留作历史参考但 agent 不再加载；`qcm-analysis` 的 curated NL→SQL examples 来源指向 `golden_seed.jsonl` 的 reference_sql 字段；新增 6 单元测试（active skill 加载 + 系统提示拼装）。
- **PR4 — Evals + Studio runbook（`feat(eval)`，d1e5cbc）**：`tests/eval/golden_seed.jsonl`（15 case，从 vault 复制入库）+ `test_golden_seed_schema.py`（结构 / id 唯一 / 难度分布 / 查询 vs 澄清拆分）+ `test_component_against_seed.py`（precheck 跑遍 reference_sql，与 PR2 规则源共享）；smoke 扩展 #2-#4（`describe_biz_table` / `find_biz_context→execute_sql` Top-N / 拒绝 `biz_ods` 请求）；GUIDE §6.1 6 条 psql 案例镜像为 smoke 直接 `execute_sql`（合并 Plan C 的 C1）；`docs/runbook/dev_studio_walkthrough.md` 引用 Plan A 的 H1/H2/H3/R1/R2 evidence（不重写）；`plans/[PLAN]_mj-agent-data-agent-mvp-framework.md` v2 入库；新增 47 单元 + eval 测试，6 smoke 测试（marker gated）。

> 累计：162 unit/eval 测试 ✅，ruff + mypy strict ✅，6 smoke 测试 marker gated 等待 DB+LLM 凭据。

### Added — MVP 端到端验证后的修订（DEV profile 实测后落地）

- **Catalog 漂移修正（`fix(agent)`，593b803）**：端到端验证发现 staged STANDARD 草案与实际 DEV DB schema 显著漂移——时间列 `stat_date / stat_week / stat_month / stat_quarter / stat_year` 实际为 `data_date / week / month / quarter / year`；metric 列 `qrynum / tntcnt` 在 daily 周期实为 `<period>_<metric>`（如 `day_qrynum`）、weekly+ 实为 `<period>_<metric>_sum + daily_<metric>_avg/max/min/std/q25/median/q75` 分位数族；`biz_dwd.dwd_dim_institution` join key 实为 `tenant_id` 而非 STANDARD §4 的 `tenant_code`。`biz_catalog/qcm_catalog.yaml` v0.1.0→v0.2.0：mirror 实际 DB；`source.status: drift_detected` + `drift_notes`；新增 `metric_column_shapes` 块说明各周期 metric 列形状。3 个 SKILL.md 全部重写 SQL 示例；prompt v1.1→v1.2 文档漂移；7 个测试文件断言更新到实际列名；`tests/integration/test_mj_system_db.py` 第二个用例补时间谓词；smoke GUIDE §6.1 case 1 用 `data_date` 替代 `stat_date`。新增运行时依赖 `socksio>=1.0` 修 SOCKS proxy 环境；`tests/conftest.py` 模块导入时 `load_dotenv()` 让 skip-gates 看到 `.env` 凭据。
- **Plan A walkthrough evidence 回填（`docs(runbook)`，ffad3b5）**：新增 `scripts/capture_walkthrough_evidence.py` 5-case 捕获脚本（H1/H2/H3 happy path + R1/R2 red line 各跑一次）；`docs/runbook/walkthrough_evidence.md` 入库实测快照；`docs/runbook/dev_studio_walkthrough.md` §4 表格从 reference 升级为 inline 预期 vs 实际并列。首次跑捕获到两个软拒绝问题：R1 silent substitute、R2 4-call gradual degradation；安全合规口径未被穿透，但 prompt 应硬化（即下一条）。
- **Prompt v1.3 hard refusal + clarifying turn（`feat(prompt)`，0f99672）**：system.md hard rule 2 显式要求"碰到 `biz_ods` / `biz_ads` / `ops_*` 时首句声明边界 + 引用 ADR-006/008 + 提供 DWS 替代"；hard rule 3 显式要求"无界请求必须先反询时间窗 / 聚合 / Top-N，禁止任何探索性 `execute_sql`"。重跑 capture 实测：R1 60s/3-call silent → 48s/3-call explicit-boundary（"根据数据治理策略，`biz_ods.ods_query_volume_daily` 原始数据层对分析师角色不可访问"）；R2 53s/4-call gradual → **10s/0-call clarifying turn**（直接列时间窗 / 聚合 / 数据量控制 3 选 1）。

> MVP 验证后累计：167 unit/eval/integration 测试 ✅（5 条 live DB integration 实跑），ruff + mypy strict ✅，6+4 = 10 条 smoke 全过（GUIDE §6.1 6 条镜像 + agent trajectory 4 条 H1-H3+R1）。

### Added — earlier Phase 0
- **Phase 0 Foundation 垂直切片**：最小可跑通的 agent 骨架 —— LangChain 1.2.* + LangGraph 1.1.8；`langchain.agents.create_agent` 驱动；`src/mj_agent/{agent,config,llm,state}.py` + `integrations/mj_system_db.py` + `tools/sql/{guardrail,execute,introspect}.py` + `prompts/system.md` + `skills/query-writing/SKILL.md`；`langgraph.json` 指向 `make_graph` 工厂供 LangGraph Studio 使用
- **Volcengine Ark + DeepSeek V3 作为唯一 LLM provider**：`src/mj_agent/llm.py:make_llm` 构造 `ChatOpenAI`（OpenAI 兼容端点），环境变量 `ARK_API_KEY` / `ARK_BASE_URL` / `LLM_MODEL_ID` / `LLM_THINKING_ENABLED` / `LLM_TIMEOUT_SEC`；缺 key 时 `LLMConfigError` fail-fast
- **biz 域只读访问与四层防护（ADR-006）**：连接层 `default_transaction_read_only=on` + 角色层 analyst GRANT（DB 侧兜底，mj-system `R__analyst_permissions.sql`）+ 应用 guardrail（单语句 SELECT / 关键字黑名单 / schema allowlist `biz_dws,biz_dwd`）+ skill 语义层（`mj-ddd-semantics` 待 PR3 补齐，当前由 `query-writing` 承载基本规则）
- **`.env.example` 对齐 mj-system**：`##### N. Title #####` 分节风格、`POSTGRES_{DEV,TEST,PROD}_HOST/PORT` + `POSTGRES_ANALYST_USER/PASSWORD` 变量命名；`POSTGRES_USER/PASSWORD` 保留为空并注明"mj-agent 运行时不使用，勿填 admin 凭据"
- **测试脚手架**：`tests/unit/`（21 cases，guardrail + prompt loader）+ `tests/integration/test_mj_system_db.py`（live biz 域，`live_db` fixture 按 `POSTGRES_ANALYST_USER` 存在性 skip）+ `tests/smoke/test_agent_smoke.py`（end-to-end，按 `ARK_API_KEY` 存在性 skip）；pytest marker `smoke` 默认不跑
- **依赖锁定与复现**：`pyproject.toml` pin `langchain==1.2.*` / `langgraph==1.1.8` / `langchain-openai>=1.0,<2`；`uv.lock` 入库
- **开发者文档**：`README.md` 重写（Quick start + LLM provider + 测试矩阵 + 数据边界摘要 + Phase 0 结构图）、`CLAUDE.md` 升级为 Phase 0 架构说明、`plans/[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md` 新增 run-book 风格 Studio 端到端手册（前置 / 步骤 / happy-path+red-line case / 9 项故障矩阵 / 完成标志）
- **`.gitignore` 对齐 mj-system**：分节风格 + `.claude/settings.local.json` 窄忽略保留 marketplace 配置 + mj-agent 独有节（pytest/mypy/ruff 缓存、LangGraph Studio `.langgraph_api/`）
- **Phase 0 setup-env 加密注入工具链（PLAN D）**：`scripts/setup-env.ps1` + `scripts/encrypt-secrets.ps1`（OpenSSL AES-256-CBC + PBKDF2，复用 mj-system 已上线骨架）+ `config/{secrets.example,README.md,secrets.enc}` 4-key schema（`POSTGRES_ANALYST_{USER,PASSWORD}` + `ARK_API_KEY` + `LANGSMITH_API_KEY`）+ `README.md` Quick start §2 切到脚本注入；与 mj-system 独立口令（ADR-006 数据边界精神）；§端到端验证 §1-§6 + §8 通过
- **`.env.example` 转 ASCII**：解决 python-dotenv 在 langgraph_api 内部 `DotEnv()` 不传 encoding 时，中文 Windows GBK 撞 UTF-8 字节导致 `uv run langgraph dev` `UnicodeDecodeError` 启动失败；所有中文注释翻成英文，`##### N. Title #####` 章节风格 / 变量名 / 默认值 / 章节顺序 0 改动

### Removed
- 删除 `main.py` Hello World 占位（由 `langgraph dev` 启动入口取代）
