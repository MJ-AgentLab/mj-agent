# Changelog

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- **Phase 0 Foundation 垂直切片**：最小可跑通的 agent 骨架 —— LangChain 1.2.* + LangGraph 1.1.8；`langchain.agents.create_agent` 驱动；`src/mj_agent/{agent,config,llm,state}.py` + `integrations/mj_system_db.py` + `tools/sql/{guardrail,execute,introspect}.py` + `prompts/system.md` + `skills/query-writing/SKILL.md`；`langgraph.json` 指向 `make_graph` 工厂供 LangGraph Studio 使用
- **Volcengine Ark + DeepSeek V3 作为唯一 LLM provider**：`src/mj_agent/llm.py:make_llm` 构造 `ChatOpenAI`（OpenAI 兼容端点），环境变量 `ARK_API_KEY` / `ARK_BASE_URL` / `LLM_MODEL_ID` / `LLM_THINKING_ENABLED` / `LLM_TIMEOUT_SEC`；缺 key 时 `LLMConfigError` fail-fast
- **biz 域只读访问与四层防护（ADR-006）**：连接层 `default_transaction_read_only=on` + 角色层 analyst GRANT（DB 侧兜底，mj-system `R__analyst_permissions.sql`）+ 应用 guardrail（单语句 SELECT / 关键字黑名单 / schema allowlist `biz_dws,biz_dwd`）+ skill 语义层（`mj-ddd-semantics` 待 PR3 补齐，当前由 `query-writing` 承载基本规则）
- **`.env.example` 对齐 mj-system**：`##### N. Title #####` 分节风格、`POSTGRES_{DEV,TEST,PROD}_HOST/PORT` + `POSTGRES_ANALYST_USER/PASSWORD` 变量命名；`POSTGRES_USER/PASSWORD` 保留为空并注明"mj-agent 运行时不使用，勿填 admin 凭据"
- **测试脚手架**：`tests/unit/`（21 cases，guardrail + prompt loader）+ `tests/integration/test_mj_system_db.py`（live biz 域，`live_db` fixture 按 `POSTGRES_ANALYST_USER` 存在性 skip）+ `tests/smoke/test_agent_smoke.py`（end-to-end，按 `ARK_API_KEY` 存在性 skip）；pytest marker `smoke` 默认不跑
- **依赖锁定与复现**：`pyproject.toml` pin `langchain==1.2.*` / `langgraph==1.1.8` / `langchain-openai>=1.0,<2`；`uv.lock` 入库
- **开发者文档**：`README.md` 重写（Quick start + LLM provider + 测试矩阵 + 数据边界摘要 + Phase 0 结构图）、`CLAUDE.md` 升级为 Phase 0 架构说明、`plans/[PLAN]_Phase0_LangGraph_Studio_Walkthrough.md` 新增 run-book 风格 Studio 端到端手册（前置 / 步骤 / happy-path+red-line case / 9 项故障矩阵 / 完成标志）
- **`.gitignore` 对齐 mj-system**：分节风格 + `.claude/settings.local.json` 窄忽略保留 marketplace 配置 + mj-agent 独有节（pytest/mypy/ruff 缓存、LangGraph Studio `.langgraph_api/`）

### Removed
- 删除 `main.py` Hello World 占位（由 `langgraph dev` 启动入口取代）
