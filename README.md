# mj-agent

MJ-AgentLab **数据智能体** — 公司内部数据分析团队使用，基于 LangChain 1.x +
LangGraph 1.1.8 构建。Python 3.13、使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖。

当前阶段：**Phase 0 Foundation**（路线图：[plans/mj-agent-roadmap-v1.6.md](./plans/mj-agent-roadmap-v1.6.md)；canonical 文档入口：[docs/INDEX.md](./docs/INDEX.md)）。

> **Spec-Anchored Refactor in progress（per ADR-031 / plans/[PLAN]_spec_anchored_refactor.md）**:
> - **[sdd/](./sdd/)** — SDD Kernel（治理元规则；constitution / lifecycle / gates / workflows / adapters / templates）.
> - **[capabilities/](./capabilities/)** — Capability Package（Phase M1 起填充 5 pilot；当前仅 INDEX 占位）.
> - **[policies/](./policies/)** — Business Policy（9 native 文件）.
> - **[decisions/](./decisions/)** — ADR 新址（Phase M5 整体平移自 `docs/adr/`；当前仅 ADR-031 draft + INDEX 占位）.
> - **[AGENTS.md](./AGENTS.md)** — Codex 参与契约（standalone Codex 授权为完整开发参与者，可运行命令 + 做开发、自守 必停/数据边界；per ADR-035）.
> - **[GLOSSARY.md](./GLOSSARY.md)** — 全仓领域术语表.

## Clone

GitHub（默认 `origin`）：

```bash
git clone https://github.com/MJ-AgentLab/mj-agent.git
cd mj-agent
```

Gitee 镜像（远端名 `gitee`）：

```bash
git clone https://gitee.com/ranzuozhou/mj-agent.git
cd mj-agent
```

为已克隆的仓库追加双远端：

```bash
git remote add origin https://github.com/MJ-AgentLab/mj-agent.git
git remote add gitee  https://gitee.com/ranzuozhou/mj-agent.git
```

使用 PowerShell 脚本克隆 bare 仓库（worktree 工作流；在 `mj-agent/` 仓库的**父目录**运行）：

```powershell
powershell -ExecutionPolicy Bypass -File .\mj-agent-clone-bare.ps1 `
    -RepoUrl https://github.com/MJ-AgentLab/mj-agent
```

脚本会在父目录下创建 `mj-agent/.bare`（bare repo 实体）+ `mj-agent/develop`（默认 worktree）；后续按 5 分支模型用 `git -C develop worktree add ../<branch> -b <branch> develop` 起其他分支。

## 技术栈

| 类别 | 选型 | 版本 | 关键文档 |
|---|---|---|---|
| 运行时 | Python | 3.13 | [pyproject.toml](./pyproject.toml) |
| 依赖管理 | uv | latest | [astral-sh/uv](https://github.com/astral-sh/uv) |
| Agent 框架 | LangChain + LangGraph | 1.x / 1.1.8 | [CLAUDE.md §Architecture](./CLAUDE.md) |
| 前端 UI | Chainlit | latest | [src/mj_agent/ui.py](./src/mj_agent/ui.py) |
| 状态存储 | PostgreSQL（AsyncPostgresSaver） | 15+ | [ADR-006](./decisions/ADR-006_Fail_Safe_Reads.md) |
| 容器化 | Docker Compose（4-file profile） | latest | [ADR-026](./decisions/ADR-026_Multi_Environment_Compose_Profile.md) |
| LLM provider | Volcengine Ark / local-openai-compat | DeepSeek V3 / vLLM / SGLang / Ollama | [ADR-027](./decisions/ADR-027_LLM_Provider_Abstraction.md) |

## 前置条件

| 工具 | 用途 | 验证命令 |
|---|---|---|
| Python 3.13 | 运行时 | `python --version` |
| uv | 依赖管理 | `uv --version` |
| Git | 版本控制 | `git --version` |
| PowerShell 5.1+ | 解密 secrets / worktree 脚本 | `$PSVersionTable.PSVersion` |
| Docker Desktop（可选） | 起本地 postgres + redis | `docker --version` |

完整环境搭建步骤见 [docs/guide/[GUIDE]_Quick_Start_Setup.md](./docs/guide/[GUIDE]_Quick_Start_Setup.md)（5 分钟速查版）或 [docs/guide/[GUIDE]_Developer_Onboarding.md](./docs/guide/[GUIDE]_Developer_Onboarding.md)（15 分钟完整版）。

## Quick start

```bash
# 1. 安装依赖
uv sync

# 2. 准备 .env（解密团队密钥注入；-LlmProfile ark|dgx 选 LLM provider 套装，
#    无 DGX 隧道的机器一律 ark）
.\scripts\setup-env.ps1 -LlmProfile ark
# 没有团队口令？向管理员申请，或手工 copy .env.example 并填入本地可用的 ARK_API_KEY（不推荐）

# 3. MCP secrets（Claude Code 的 .mcp.json ${VAR} 消费；写 OS User env，非 .env）
.\.claude\scripts\setup-mcp-secrets.ps1
# 跑完必须完全重启终端 + Claude Code（User env 只对新进程可见）

# 4. 启动 LangGraph Studio
uv run langgraph dev
#  浏览器打开 Studio 提示的本地 URL，选 "mj_agent" 图
```

两个加密 bundle 的完整治理（轮换 / 新增 key / cold-reset / 诊断）见 [config/README.md](./config/README.md)。

## 常用开发命令

```bash
uv sync                                # 装依赖、锁版本
uv run langgraph dev                   # LangGraph Studio
uv run mj-agent serve                  # Chainlit UI
uv run mj-agent check                  # 探测 DB + LLM 凭据（Docker healthcheck）
uv run pytest tests/unit               # 人类/IDE direct 路径；始终 offline
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit  # Agent/CI
uv run ruff check                      # Lint
uv run mypy src/mj_agent                # Type-check（strict）
```

完整命令矩阵（含 pytest 四档 + Docker compose 三 profile）见 [CLAUDE.md §Commands](./CLAUDE.md)。

## LLM provider

mj-agent 通过 `LLM_PROVIDER` 支持两种 provider（[ADR-027](./decisions/ADR-027_LLM_Provider_Abstraction.md)；DGX 不是部署 profile，仅作为 LLM 端点供应方）：

| Provider | 端点 | 用途 |
|---|---|---|
| `ark`（默认） | `ARK_BASE_URL`（默认 `https://ark.cn-beijing.volces.com/api/v3`） | 公网 Volcengine Ark + DeepSeek V3；合规路径为 Ark 企业协议 + ZDR（已由合规团队确认） |
| `local-openai-compat` | `LLM_BASE_URL`（必填；经隧道 `http://host.docker.internal:18000/v1`，见下） | DGX-Spark 上的 vLLM / SGLang / Ollama / TGI / llama.cpp OpenAI 兼容端点 |

**默认（Ark）`.env` 配置**（`.env.example` 已给好默认值；团队密钥由 `setup-env.ps1` 注入）：

```dotenv
LLM_PROVIDER=ark
LLM_MODEL_ID=deepseek-v3-2-251201
LLM_THINKING_ENABLED=false
LLM_TIMEOUT_SEC=120
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=<团队方舟 key>
```

**切到 DGX（local-openai-compat）`.env` 配置**——推荐直接 `.\scripts\setup-env.ps1 -Force -LlmProfile dgx`（bundle §2c 携带整套值），手工等价形态如下：

```dotenv
LLM_PROVIDER=local-openai-compat
LLM_BASE_URL=http://host.docker.internal:18000/v1
LLM_API_KEY=<真实 key>                # TEST/PROD 必填；vLLM 应启用 --api-key。EMPTY 仅限本地隔离 DEV
LLM_MODEL_ID=<与 vLLM --served-model-name 一致>   # 默认值是 Ark 云 id，切换必须覆写（ADR-033）
NO_PROXY=localhost,127.0.0.1,::1,host.docker.internal,192.168.0.189
```

**端点拓扑（重要）**：DGX 上的 vLLM 只绑 loopback——LAN 直连 `http://192.168.0.189:8000/v1` **不通**。
消费必须经 owner 终端跑的 SSH 隧道，且绑 `0.0.0.0` 让容器也进得来：

```bash
ssh -L 0.0.0.0:18000:127.0.0.1:8000 <user>@192.168.0.189
```

`host.docker.internal` 由 Docker Desktop 同时提供给 host 与容器（hosts 文件条目）——一个 URL 同时覆盖 `uv run` 与 compose 两种跑法；无 DGX 隧道的机器一律用 `-LlmProfile ark`。

**切换 DGX 前**请跑 `/mj-agent-infra-llm-endpoint-probe` 验证 endpoint（reachability + model id 匹配 + 1-token chat smoke；Ollama 自动 fallback `/api/tags`）。

**fail-fast 语义**：
- `ark` 缺 `ARK_API_KEY`（或 `LLM_API_KEY`）→ `LLMConfigError`
- `local-openai-compat` 缺 `LLM_BASE_URL` → `LLMConfigError`

**数据边界不放宽**：即使 LLM 在内网 DGX，仍走相同 4 层可见性（L1 hybrid guardrail + L1b sqlglot precheck + L2 SKILL semantics + L3 read-only connection + L4 GRANT），不因"本地模型"把大批明细直接塞给 LLM。

## Testing

```bash
# 单元测试（快；无外部依赖）
uv run pytest tests/unit

# 集成测试（需 POSTGRES_ANALYST_USER 已设置）
uv run pytest tests/integration        # offline；biz-live fixture structured-skip

# Smoke 测试（需真实 biz 域 + LLM provider）
uv run pytest tests/smoke -m smoke     # offline；external fixtures structured-skip
```

## 架构概览

```text
LangGraph Studio / Chainlit / CLI
        │
        ▼
   make_graph()  ──► langchain.agents.create_agent(model, tools, system_prompt, middleware)
        │                              │
        │                              ├─ handle_sql_tool_errors（ADR-029；ValueError/RuntimeError → ToolMessage）
        │                              │
        ▼                              ▼
   Skills（in-source canonical）     Tools
   ├─ biz-domain-context             ├─ find_biz_context
   ├─ qcm-analysis                   ├─ list_biz_tables / describe_biz_table
   └─ safe-sql-analysis              └─ execute_sql  ──► L1 hybrid → L1b sqlglot → L3 RO conn → biz_dws / biz_dwd
```

完整架构图（Memory / CLI / Storage stack）见 [CLAUDE.md §Architecture](./CLAUDE.md)。

## 文档导航

| 主题 | 入口 |
|---|---|
| 5 分钟环境速查 | [docs/guide/[GUIDE]_Quick_Start_Setup.md](./docs/guide/[GUIDE]_Quick_Start_Setup.md) |
| 15 分钟新成员上手 | [docs/guide/[GUIDE]_Developer_Onboarding.md](./docs/guide/[GUIDE]_Developer_Onboarding.md) |
| 分析师 Day-One | [docs/guide/[GUIDE]_Analyst_Day_One.md](./docs/guide/[GUIDE]_Analyst_Day_One.md) |
| 项目入口 INDEX | [docs/INDEX.md](./docs/INDEX.md) |
| AI 高频上下文 | [CLAUDE.md](./CLAUDE.md) |

## Data boundary

mj-agent 仅访问 上游业务系统 业务指标域：

- `biz_dws` — analyst 可 SELECT 全部汇总表
- `biz_dwd` — analyst 仅可 SELECT 2 张维度表（`dwd_dim_product_interface`、`dwd_dim_institution`）

权威权限定义位于 上游业务系统 仓库
`sql/migrations/repeatable/R__analyst_permissions.sql`。

## 常见问题速查

<details>
<summary><strong>ARK_API_KEY 缺失 / LLMConfigError</strong></summary>

跑 `.\scripts\setup-env.ps1` 解密团队 secrets；无团队口令则 `cp .env.example .env` 后手填本地 `ARK_API_KEY`。

</details>

<details>
<summary><strong>LangGraph Studio 不弹浏览器 / 2024 端口占用</strong></summary>

端口默认 `http://127.0.0.1:2024`；占用时用 `uv run langgraph dev --port 2025`，浏览器手工打开。详细诊断见 [docs/guide/[GUIDE]_Developer_Onboarding.md §7](./docs/guide/[GUIDE]_Developer_Onboarding.md)。

</details>

<details>
<summary><strong>pytest smoke 全部 skip</strong></summary>

预期行为——`conftest.py` 不因凭据存在而启用外部测试：biz-live pytest 永久 structured-skip，
non-biz external 也在未来独立 Owner-approved profile 出现前返回
`SKIP_POLICY_EXTERNAL_DEPENDENCY`。`pyproject.toml` 默认排除 smoke；direct pytest 仅供
人类/IDE 且同样 offline，Agent/CI 必须使用 hardened runner。真实服务验证走
`mj-agent check` / Studio 等显式 HITL probe，而不是 pytest。

</details>

<details>
<summary><strong>Docker compose 起不来 / mj-system-backend-network 不存在</strong></summary>

mj-agent 依赖上游 `mj-system` compose 栈先 up（提供 external network）；详见 [docker/README.md](./docker/README.md) + [ADR-008](./decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse.md)。

</details>

<details>
<summary><strong>.env 中文字符报错（langgraph dev 启动失败）</strong></summary>

`.env.example` 保持 ASCII；中文注释会让 `python-dotenv` 在中文 Windows 上以默认 GBK 解码失败。注释改英文或删除。

</details>

## 贡献指南

- 提交 PR 前请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)（分支策略 / commit 规范 / PR 流程 / Code Review 标准）
- 文档贡献请按 [policies/documentation.md](./policies/documentation.md) 的三轨制治理（code / agent / engineering-workflow / shared）
- 术语澄清查 [GLOSSARY.md](./GLOSSARY.md)

## 项目结构（Phase 0）

```text
src/mj_agent/
├── agent.py              # make_graph — LangGraph 编译入口
├── llm.py                # make_llm — provider 分支 factory（ADR-027）
├── config.py             # pydantic-settings
├── prompts/system.md     # 身份 + ADR-000 三原则
├── skills/               # SKILL.md progressive disclosure（3 active）
├── tools/                # find_biz_context + sql/{guardrail,precheck,execute,introspect}
├── middleware/           # tool_errors.py（ADR-029）
├── memory/               # AsyncPostgresSaver checkpointer
└── integrations/         # 只读 psycopg 连接池

tests/
├── unit/                 # 无外部依赖
├── integration/          # 需 biz 域可达
└── smoke/                # 需 biz 域 + LLM
```
