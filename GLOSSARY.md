# mj-agent 术语表 (Glossary)

> 本文档定义 mj-agent 项目中使用的术语、缩写及项目特定概念。
> **每个定义仅描述术语在 mj-agent 项目中的含义，不作通用百科解释。**
> **最后更新**：2026-05-18 | **维护**：任何人引入新术语时均可更新（[docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) v2.2）
> **职能边界**：本表是**全项目术语索引**；专题深度词典在 [`docs/glossary/<topic>.md`](docs/glossary/)（如 `upstream_business_warehouse.md`）。条目中如有专题深度补充，会 link 到对应专题词典。

---

## 目录（快速跳转）

[A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [L](#l) · [M](#m) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v) · [W](#w)

---

## A

### Active path stability（活跃路径稳定原则）

**定义**：[Meta_Framework v2.2](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) §4.4 引入的规则：active canonical 文件名**默认不带** `_vX.Y` 后缀；版本只在 frontmatter `version` 字段。例外仅"多 active 主版本并存"。Legacy 归档反向**必带**版本后缀。drop-suffix rename 视为 rule application，非 §5.9 trigger #4。
**相关术语**：Canonical / archive ceremony / Stable path

### ADR / Architecture Decision Record

**定义**：架构决策记录；记录为什么做某决策及其取代关系。mj-agent ADR 位于 `docs/adr/[ADR]_NNN_*.md`；frontmatter `decision: accepted | superseded | rejected`。Cross-repo decoupling 后 9 个继承自上游的 ADR 已 archive 至 `docs/archive/adr/`。
**相关术语**：Canonical / Document Type Tags / supersedes

### Agent Side（Track B）

**定义**：三轨道治理中的「智能体侧」轨道；治理 `src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md` 两类 in-source canonical + agent-facing CONTRACT / EVAL。主 STANDARD：[Agent_Side v1.1](docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md)。失败模式**沉默**（错误业务输出）。
**相关术语**：Track / Code Side / Engineering-workflow / SKILL

### analyst（PostgreSQL role）

**定义**：mj-agent 访问上游业务系统 biz pg 的**只读** PostgreSQL role；GRANT 见上游 `R__analyst_permissions.sql`。仅可 SELECT `biz_dws` 全表 + `biz_dwd` 2 张维度表（`dwd_dim_product_interface` / `dwd_dim_institution`）。data boundary 4 层防御之 L4。
**相关术语**：biz domain / Data boundary / RO connection

---

## B

### biz domain（业务指标域）

**定义**：上游业务系统的 schema 域；mj-agent 唯一访问入口。包含 `biz_dws` 汇总层 + `biz_dwd` 维度层。详见 [docs/glossary/upstream_business_warehouse.md](docs/glossary/upstream_business_warehouse.md)。
**相关术语**：biz_dws / biz_dwd / upstream business warehouse / analyst

### biz_dws / biz_dwd（schemas）

**定义**：mj-agent 可访问的两个上游 schema。`biz_dws` 全表 SELECT 可见；`biz_dwd` 仅 2 张白名单维度表可见。L1 regex guardrail + L1b sqlglot precheck + L4 GRANT 三层强制。
**相关术语**：biz domain / Data boundary / Guardrail

---

## C

### Canonical 文档

**定义**：[Meta_Framework v2.2](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) §2.2 中的「权威层」；路径在 `docs/**`（排除 `archive/legacy/`）+ `src/mj_agent/{skills,prompts}/**` + `.claude/skills/**` + `.claude/settings.json` + `.mcp.json`。受强治理；frontmatter 必填；A1-A14 PR 门禁适用。
**相关术语**：Working 文档 / Legacy 文档 / Frontmatter / Track

### Chainlit

**定义**：mj-agent 前端 UI 选型；Phase 1 终态 entry。源 `src/mj_agent/ui.py`；启动 `uv run mj-agent serve`。
**相关术语**：LangGraph Studio / make_graph

### CLAUDE.md

**定义**：项目根 markdown 之一；定位为 AI 高频上下文缓存。**非信息源**，是从各 canonical STANDARD / 关键 GUIDE 摘录的副本，目的是提升 AI 单上下文窗口的信息密度。同步策略见 [Meta v2.2 §6.4](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) 4 类 allowlist。
**相关术语**：Project root markdown / A6 / Meta_Framework

### Commit type

**定义**：commit message 的 `<type>` 字段；mj-agent 7 类 allowlist：`feat / fix / perf / refactor / test / docs / infra`。完整规范见 [Commit_Message_Convention](docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md) §4。
**相关术语**：Conventional Commits / Branch type

### Code Side（Track A）

**定义**：三轨道治理中的「代码侧」轨道；治理 GUIDE / ADR-code / SPEC-code / RUNBOOK / POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code 8 类 canonical。主 STANDARD：[Code_Side v1.1](docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md)。失败模式**响亮**（compile / test / deploy break）。
**相关术语**：Track / Agent Side / Engineering-workflow

---

## D

### Data boundary（L1-L4）

**定义**：mj-agent 访问 biz domain 的 4 层防御机制（[ADR-006](decisions/ADR-006_Fail_Safe_Reads.md)）：
- L1 regex guardrail（`tools/sql/guardrail.py`）：single-statement + SELECT-only + schema/table 白名单
- L1b sqlglot AST precheck（`tools/sql/precheck.py`）：`no_select_star` / `require_time_range` / `require_limit`
- L2 SKILL semantics（`skills/*/SKILL.md` + `qcm_catalog.yaml`）
- L3 read-only connection（`integrations/mj_system_db.py`）+ L4 GRANT
**相关术语**：Guardrail / analyst / biz domain

### DGX-Spark

**定义**：内网 GPU 节点（192.168.0.189），运行 vLLM / SGLang / Ollama 等 OpenAI 兼容 LLM endpoint；mj-agent 通过 `LLM_PROVIDER=local-openai-compat` 消费。**非**部署 profile —— DGX 不部署 mj-agent，仅作算力供应方（[ADR-027](decisions/ADR-027_LLM_Provider_Abstraction.md)）。
**相关术语**：LLM provider / local-openai-compat / vLLM

---

## E

### Engineering-workflow（Track C）

**定义**：三轨道治理中的「工程编排侧」轨道；治理 `.claude/skills/mj-agent-*/SKILL.md` + `.claude/settings.json` + `.mcp.json` + HITL_Prompt + 工程流程 STANDARDs。主 STANDARD：[HITL_Prompt v1.1](docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md)。失败模式**流程漂移**（HITL 跳过 / 错 skill / settings 退化）。
**相关术语**：Track / Code Side / Agent Side / HITL gates

---

## F

### find_biz_context（tool）

**定义**：mj-agent tool 之一（`src/mj_agent/tools/biz_context.py`）；输入自然语言 / 关键词，召回 `qcm_catalog.yaml` 中对应的 metric / period / dimension / 时间列 / 同环比列 / 信号表 / 维表 join key。是 agent 调用工具链的第一步（per system prompt 强制顺序）。
**相关术语**：QCM catalog / Skills

### Frontmatter

**定义**：受治理 markdown 文件开头的 YAML 元数据块。canonical 必填 `type / domain / summary / owner / created / updated / state`；带 `version` 类（STANDARD/SPEC/EVAL/CONTRACT/ASSESSMENT）还需 `version`；agent track SKILL 用 13 字段 schema；engineering-workflow `.claude/skills/` 用 ADR-013 native 2 字段。项目根 5 文件**不要求** frontmatter（[Meta v2.2 §2.6](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md)）。
**相关术语**：Canonical / track / Project root markdown

---

## G

### Guardrail（L1 regex）

**定义**：data boundary 第一层防御；`tools/sql/guardrail.py` 用正则强制 single-statement + SELECT-only + schema/biz_dwd 表白名单（`BIZ_ALLOWED_DWD_TABLES`）。任何放宽是必停 HITL 项（[HITL_Prompt §3.1](docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md)）。
**相关术语**：Data boundary / Precheck / SQL execute

### G1 / G2（PreToolUse hook 规则）

**定义**：`.claude/scripts/guard-git-workflow.ps1` PreToolUse hook 强制的两条 git 工作流规则。G1 worktree-required（拦 `git checkout -b`，引导 `git worktree add`）；G2 base=develop-except-hotfix（拦 `gh pr create` 不带 `--base`）。事故起源 PR #158 / #154。
**相关术语**：Worktree / Hook / Branch type

---

## H

### handle_sql_tool_errors（middleware）

**定义**：[ADR-029](decisions/ADR-029_Tool_Error_Surfacing_To_LLM.md) 引入的 LangChain 1.x `@wrap_tool_call` middleware（`src/mj_agent/middleware/tool_errors.py`）；把 SQL tool ValueError / RuntimeError 转为 `ToolMessage` 喂回 LLM 自纠错，避免 graph crash 引发的 frontend hang。`make_graph` 装载为 `middleware=[handle_sql_tool_errors]`。
**相关术语**：Middleware / make_graph / SQL execute

### HITL gates（5 / 7 / 9 / 11 / 13）

**定义**：[HITL_Prompt v1.1](docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md) §1 17-stage 闭环中**强制暂停等人**的 5 个 stage：5 Plan confirm / 7 SPEC + ADR confirm / 9 Scope Drift / 11 AI Self-review / 13 Push。其他 stage 按 §3.1 通用规则 + 4 项 mj-agent 专属规则按需 HITL。
**相关术语**：HITL_Prompt / Engineering-workflow

---

## I

### in-source canonical

**定义**：位于 `src/mj_agent/` 但属于 canonical 治理范围的 markdown 文件；当前 5 个（`skills/biz-domain-context/SKILL.md` + `skills/qcm-analysis/SKILL.md` + `skills/safe-sql-analysis/SKILL.md` + `prompts/system.md` + `biz_catalog/qcm_catalog.yaml`）。由 Python loader 剥 frontmatter 后喂给 LLM。修改是 [HITL_Prompt §3.1](docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md) 4 项专属必停项之一。
**相关术语**：Canonical / Frontmatter strip / SKILL / Track B

### INDEX.md

**定义**：mj-agent canonical 文档的人工入口：`docs/INDEX.md` 顶层 + `docs/<sub>/INDEX.md` 局部 index。Phase 2 接入自动生成（按 frontmatter `summary` 扫描重建）。
**相关术语**：Canonical / Frontmatter / A5

---

## L

### LangChain / LangGraph

**定义**：mj-agent agent 框架；LangChain 1.x + LangGraph 1.1.8。Agent 在 `src/mj_agent/agent.py:make_graph()` 中用 `langchain.agents.create_agent(model, tools, system_prompt, checkpointer, middleware)` 编译。`langgraph.json` 指向 `make_graph` 作为 Studio 入口。
**相关术语**：make_graph / LangGraph Studio

### LangGraph Studio

**定义**：LangGraph 自带的本地开发 UI；启动 `uv run langgraph dev`；默认 `http://127.0.0.1:2024`。完整 walkthrough 见 [docs/runbook/dev_studio_walkthrough.md](docs/runbook/dev_studio_walkthrough.md)。
**相关术语**：Chainlit / make_graph

### LangSmith

**定义**：LangChain 配套的 trace / eval 平台；mj-agent 通过 `LANGSMITH_API_KEY` 启用，可选。诊断时启 trace；A11 EVAL framework 落地后承担 baseline 跑 runner（Phase 2）。
**相关术语**：EVAL / LangChain

### Living vs Frozen 引用

**定义**：[ADR-011](decisions/ADR-011_Doc_Versioning_And_Archive_Convention.md) §5.6 引入的 archive 后的引用语义。Living 引用随版本自动跟到最新 active 路径；Frozen 引用 pin 到归档版本路径 + 必须带 archive 前缀。`scripts/check_wikilinks.py` 强制 Frozen 引用必须含 `archive/rule/` 路径前缀。
**相关术语**：Archive ceremony / Active path stability / supersedes

### local-openai-compat（LLM provider）

**定义**：`LLM_PROVIDER` 二选项之一（另一为 `ark`）；驱动 mj-agent 消费 OpenAI 兼容端点（vLLM / SGLang / Ollama / TGI / llama.cpp）。`LLM_BASE_URL` 必填；不传 `thinking` extra_body（vLLM 不接受）。健康检查用 `/mj-agent-infra-llm-endpoint-probe`。
**相关术语**：LLM provider / DGX-Spark / vLLM

---

## M

### make_graph / make_llm（factories）

**定义**：`src/mj_agent/agent.py:make_graph()` 是 LangGraph 编译入口，`langgraph.json` 指向；惰性导入，import 模块不强制初始化 LLM。`src/mj_agent/llm.py:make_llm()` 是 LLM provider 分支 factory（[ADR-027](decisions/ADR-027_LLM_Provider_Abstraction.md)）；按 `LLM_PROVIDER` 分支 ark / local-openai-compat。缺凭据时 raise `LLMConfigError`。
**相关术语**：LangChain / LLM provider / LangGraph Studio

### Memory checkpointer

**定义**：LangGraph state 持久化机制；mj-agent 用 `AsyncPostgresSaver`（Phase 1 sub 1.A），写入独立的 `mj-agent-postgres` 容器（与上游业务 pg 解耦）。Async 变体因 Chainlit 驱动 `graph.astream`，sync `PostgresSaver` 缺 `aget_tuple`。
**相关术语**：PostgresSaver / Chainlit / storage stack

### Middleware

**定义**：LangChain 1.x 的 tool 调用拦截器；mj-agent 当前 1 个 middleware：`handle_sql_tool_errors`（[ADR-029](decisions/ADR-029_Tool_Error_Surfacing_To_LLM.md)）。`make_graph` 调 `create_agent(..., middleware=[handle_sql_tool_errors])`。
**相关术语**：handle_sql_tool_errors / make_graph

---

## O

### Onboarding（Developer / Analyst）

**定义**：mj-agent 两份角色 day-1 GUIDE：[Developer_Onboarding](docs/guide/[GUIDE]_Developer_Onboarding.md) 面向开发者 15 分钟端到端；[Analyst_Day_One](docs/guide/[GUIDE]_Analyst_Day_One.md) 面向分析师试用闭环。配套 5 分钟赶时间版 [Quick_Start_Setup](docs/guide/[GUIDE]_Quick_Start_Setup.md)。
**相关术语**：GUIDE / Quick Start

---

## P

### PostgresSaver / AsyncPostgresSaver

**定义**：LangGraph 提供的 checkpointer 实现，落 PostgreSQL 表。mj-agent 用 async 变体，对接独立的 `mj-agent-postgres` 容器（`mj_agent_memory` DB，不与上游 biz pg 共享连接池）。
**相关术语**：Memory checkpointer / Storage stack

### PROMPT version

**定义**：`src/mj_agent/prompts/*.md` 的 frontmatter `version` 字段；每次正文实质变更必 bump（[Agent_Side §3.2](docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md)）；`state: active` 时需 `eval_references` 非空（Phase 2 起强制）。修改是 [HITL_Prompt §3.1](docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md) 必停项。
**相关术语**：in-source canonical / EVAL / Frontmatter strip

### Project root markdown

**定义**：项目根 5 个具名 markdown：`README.md` / `CONTRIBUTING.md` / `CHANGELOG.md` / `GLOSSARY.md` / `CLAUDE.md`。**不进入 canonical 治理表**；不写 frontmatter；A1-A3 不适用；A4 + A6 仍适用。详见 [Meta v2.2 §2.6](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) + [GitHub_Markdown §14](docs/rule/[STANDARD]_GitHub_Markdown.md)。
**相关术语**：Canonical / Frontmatter / track

---

## Q

### QCM catalog (qcm_catalog.yaml)

**定义**：`src/mj_agent/biz_catalog/qcm_catalog.yaml`；静态镜像上游业务系统数据字典 STANDARD §2-§4（metric / period / dimension / 同环比列 / 信号表 / 维表 join key）。由 `find_biz_context` 召回；漂移检测见 [HITL_Prompt §4.4](docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md)（mj-agent 专属必停项）。
**相关术语**：find_biz_context / biz domain / Mirror

---

## R

### RO connection（read-only PG）

**定义**：data boundary L3；`integrations/mj_system_db.py` psycopg pool 强制 `default_transaction_read_only=on` + `lock_timeout=5s` + `idle_in_transaction_session_timeout=10s`。任何写操作在事务级别被拒。
**相关术语**：Data boundary / analyst / Guardrail

### Runtime skill（Track B in-source）

**定义**：`src/mj_agent/skills/<name>/SKILL.md`；运行时直接进 LLM 上下文驱动业务回答。13 字段 schema + 五段式 body（[Agent_Side §2](docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md)）。当前 3 个 active：`biz-domain-context` / `qcm-analysis` / `safe-sql-analysis`。
**相关术语**：SKILL / Workflow skill / Marketplace plugin SKILL / Three-source SKILL distinction

---

## S

### SKILL（三类区分）

**定义**：mj-agent 共有 3 类同名同形的 SKILL.md：(1) **in-source runtime**（`src/mj_agent/skills/`；13 字段；Python loader 剥 frontmatter）；(2) **in-tree workflow**（`.claude/skills/mj-agent-*/`；ADR-013 native 2 字段；Claude Code 主进程加载）；(3) **marketplace plugin**（`mj-agentlab-marketplace/`；2 字段；plugin loader）。**严格区分**——混淆会施加错误约束 / 套错 schema。
**相关术语**：Runtime skill / Workflow skill / ADR-013

### Stable path（active canonical）

**定义**：[Meta v2.2 §4.4](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) 引入的命名规则；active canonical 文件名**默认不带** `_vX.Y` 后缀。例外仅"多 active 主版本并存"。legacy 反向必带后缀。
**相关术语**：Active path stability / Archive ceremony

### setup-env.ps1 / setup-mcp-secrets.ps1（PowerShell 脚本）

**定义**：mj-agent 两条 secrets 解密脚本（[ADR-030](decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation.md) 2-bundle trust-boundary split）。`setup-env.ps1` 解密 `config/secrets.enc` 写 `.env`（app 凭据）；`.claude/scripts/setup-mcp-secrets.ps1` 解密 `config/secrets-mcp.enc` 直写 OS env（MCP secrets，bypass `.env`）。
**相关术语**：Secrets bundle / .env / .mcp.json

### SQL execute（envelope）

**定义**：`src/mj_agent/tools/sql/execute.py:execute_sql()`；返回 envelope `{executed_sql, columns, rows, row_count, truncated, statement_timeout_hit, business_summary, precheck_warnings}`。`statement_timeout` 60s 由上游 GRANT 兜底；超时 catch 后 re-raise 友好中文提示。
**相关术语**：Data boundary / Guardrail / Precheck

---

## T

### track（frontmatter 字段）

**定义**：[Meta v2.2 §4.3.1](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) 引入的 4 值 enum 字段：`code` / `agent` / `engineering-workflow` / `shared`。决定 reviewer + PR 门禁子集 + CLAUDE.md sync 段位。`scripts/check_frontmatter.py` 强制枚举值。项目根 markdown 不适用 track（§2.6 + §4.3.1 决策树第 0 条）。
**相关术语**：Track A / Track B / Track C / Frontmatter

### Three-source SKILL distinction

**定义**：mj-agent 3 类 SKILL.md 来源严格区分的简称；见上文 [SKILL](#skill三类区分)。完整速查表见 [CLAUDE.md](CLAUDE.md) §"Three-source SKILL distinction"。
**相关术语**：SKILL / Runtime skill / Workflow skill

---

## U

### Upstream business warehouse（上游业务系统）

**定义**：mj-agent 通过 analyst RO 角色访问的外部业务数据仓库；mj-agent 仅 read-only 消费者，无 schema 演进权。详细定义 + 引用规则见 [docs/glossary/upstream_business_warehouse.md](docs/glossary/upstream_business_warehouse.md)。
**相关术语**：biz domain / analyst / ADR-006 / ADR-009

### uv（依赖管理器）

**定义**：[Astral uv](https://github.com/astral-sh/uv)；mj-agent 唯一支持的 Python 依赖 / 锁文件管理工具。`pyproject.toml` + `uv.lock` 为权威。本项目不支持 pip / pipenv / poetry 直接管理。
**相关术语**：pyproject.toml

---

## V

### vLLM（OpenAI 兼容 LLM 端点）

**定义**：DGX-Spark 上运行的 LLM 推理引擎之一；mj-agent 通过 `LLM_PROVIDER=local-openai-compat` 消费。启动时**必须** `--api-key` 启用（不要用 `EMPTY` sentinel 在 TEST/PROD）。
**相关术语**：DGX-Spark / local-openai-compat / LLM provider

### Volcengine Ark（火山方舟）

**定义**：mj-agent 默认 LLM provider（`LLM_PROVIDER=ark`）；端点 `https://ark.cn-beijing.volces.com/api/v3`；模型 `deepseek-v3-2-251201`。合规路径为 Ark 企业协议 + ZDR（已确认）。`thinking` extra_body 由 `LLM_THINKING_ENABLED` 控制。
**相关术语**：LLM provider / DeepSeek V3 / make_llm

---

## W

### Wikilink（[[...]] 链接）

**定义**：Obsidian 内链格式 `[[文档名|显示文本]]` 或 `[[#章节]]`；GitHub Web **不解析** `[[...]]` 会原样显示文本。mj-agent 文档允许混用 wikilink（canonical 内引）+ 相对链接（INDEX / README / PR description）；[Meta v2.2 §6.3](docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md) + [GitHub_Markdown §5.4](docs/rule/[STANDARD]_GitHub_Markdown.md) 定义边界。A4 PR 门禁检查 wikilink 目标存在。
**相关术语**：A4 / Markdown link / Frozen vs Living 引用

### Worktree（git worktree）

**定义**：mj-agent 用 git worktree 多分支布局：`mj-agent/.bare`（bare repo） + `mj-agent/develop`（默认 worktree） + `mj-agent/<type>/<branch>/`（每条 PR 一个 worktree）。G1 worktree-required 规则禁用 `git checkout -b`。
**相关术语**：G1 / G2 / Bare repo / Branch type

---

## 派生说明

本文档结构借鉴 mj-system `GLOSSARY.md` A-W 字母分段 + 「定义 + 相关术语」二字段格式；术语条目内容**全部**按 mj-agent 自身资产派生（`pyproject.toml` / `src/mj_agent/` 结构 / ADR / STANDARD / CLAUDE.md），无一来自 mj-system。

跨项目 attribution 见 [docs/glossary/upstream_business_warehouse.md](docs/glossary/upstream_business_warehouse.md) §跨项目文档治理结构借鉴 attribution。
