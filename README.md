# mj-agent

MJ-AgentLab **数据智能体** — 公司内部数据分析团队使用，基于 LangChain 1.x +
LangGraph 1.1.8 构建。Python 3.13、使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖。

当前阶段：**Phase 0 Foundation**（路线图：[plans/mj-agent-roadmap-v1.6.md](./plans/mj-agent-roadmap-v1.6.md)；canonical 文档入口：[docs/INDEX.md](./docs/INDEX.md)）。

> **Spec-Anchored Refactor in progress（per ADR-031 / plans/[PLAN]_spec_anchored_refactor.md）**:
> - **[sdd/](./sdd/)** — SDD Kernel（治理元规则；constitution / lifecycle / gates / workflows / adapters / templates）.
> - **[capabilities/](./capabilities/)** — Capability Package（Phase M1 起填充 5 pilot；当前仅 INDEX 占位）.
> - **[policies/](./policies/)** — Business Policy（9 native 文件）.
> - **[decisions/](./decisions/)** — ADR 新址（Phase M5 整体平移自 `docs/adr/`；当前仅 ADR-031 draft + INDEX 占位）.
> - **[AGENTS.md](./AGENTS.md)** — Codex 边界声明（Codex NOT in dev workflow / read-only review only）.
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

使用 PowerShell 脚本克隆 bare 仓库（worktree 工作流）：

```powershell
powershell -ExecutionPolicy Bypass -File ..\mj-agent-clone-bare.ps1 `
    -RepoUrl https://github.com/MJ-AgentLab/mj-agent
```

## Quick start

```bash
# 1. 安装依赖
uv sync

# 2. 准备 .env（解密团队密钥注入）
.\scripts\setup-env.ps1
# 没有团队口令？向管理员申请，或手工 copy .env.example 并填入本地可用的 ARK_API_KEY（不推荐）

# 3. 启动 LangGraph Studio
uv run langgraph dev
#  浏览器打开 Studio 提示的本地 URL，选 "mj_agent" 图
```

## LLM provider

mj-agent 通过 `LLM_PROVIDER` 支持两种 provider（ADR-027 LLM Provider Abstraction；DGX 不是部署 profile，仅作为 LLM 端点供应方）：

| Provider | 端点 | 用途 |
|---|---|---|
| `ark`（默认） | `ARK_BASE_URL`（默认 `https://ark.cn-beijing.volces.com/api/v3`） | 公网 Volcengine Ark + DeepSeek V3；合规路径为 Ark 企业协议 + ZDR（已由合规团队确认） |
| `local-openai-compat` | `LLM_BASE_URL`（必填；e.g. `http://192.168.0.189:8000/v1`） | DGX-Spark 上的 vLLM / SGLang / Ollama / TGI / llama.cpp OpenAI 兼容端点 |

**默认（Ark）`.env` 配置**（`.env.example` 已给好默认值；团队密钥由 `setup-env.ps1` 注入）：

```dotenv
LLM_PROVIDER=ark
LLM_MODEL_ID=deepseek-v3-2-251201
LLM_THINKING_ENABLED=false
LLM_TIMEOUT_SEC=120
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=<团队方舟 key>
```

**切到 DGX（local-openai-compat）`.env` 配置**：

```dotenv
LLM_PROVIDER=local-openai-compat
LLM_BASE_URL=http://192.168.0.189:8000/v1
LLM_API_KEY=<真实 key>                # TEST/PROD 必填；vLLM 应启用 --api-key。EMPTY 仅限本地隔离 DEV
LLM_MODEL_ID=<与 vLLM --served-model-name 一致>
```

**切换 DGX 前**请跑 `/mj-agent-infra-llm-endpoint-probe` 验证 endpoint（reachability + model id 匹配 + 1-token chat smoke；Ollama 自动 fallback `/api/tags`）。

**fail-fast 语义**：
- `ark` 缺 `ARK_API_KEY`（或 `LLM_API_KEY`）→ `LLMConfigError`
- `local-openai-compat` 缺 `LLM_BASE_URL` → `LLMConfigError`

**数据边界不放宽**：即使 LLM 在内网 DGX，仍走相同 4 层可见性（L1 regex guardrail + L1b sqlglot precheck + L2 SKILL semantics + L3 read-only connection + L4 GRANT），不因"本地模型"把大批明细直接塞给 LLM。

## Testing

```bash
# 单元测试（快；无外部依赖）
uv run pytest tests/unit

# 集成测试（需 POSTGRES_ANALYST_USER 已设置）
uv run pytest tests/integration

# Smoke 测试（需真实 biz 域 + LLM provider）
uv run pytest tests/smoke -m smoke
```

## Data boundary

mj-agent 仅访问 上游业务系统 业务指标域：

- `biz_dws` — analyst 可 SELECT 全部汇总表
- `biz_dwd` — analyst 仅可 SELECT 2 张维度表（`dwd_dim_product_interface`、`dwd_dim_institution`）

权威权限定义位于 上游业务系统 仓库
`sql/migrations/repeatable/R__analyst_permissions.sql`。

## 项目结构（Phase 0）

```text
src/mj_agent/
├── agent.py              # create_agent — LangGraph 编译入口
├── config.py             # pydantic-settings
├── prompts/system.md     # 身份 + ADR-000 三原则
├── skills/               # SKILL.md progressive disclosure
├── tools/sql/            # guardrail / execute / introspect
└── integrations/         # 只读 psycopg 连接池

tests/
├── unit/                 # 无外部依赖
├── integration/          # 需 biz 域可达
└── smoke/                # 需 biz 域 + LLM
```
