# mj-agent

MJ-AgentLab **数据智能体** — 公司内部数据分析团队使用，基于 LangChain 1.x +
LangGraph 1.1.8 构建。Python 3.13、使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖。

当前阶段：**Phase 0 Foundation**（见 `docs/mj-agent-roadmap-v1.6.md`）。

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
powershell -ExecutionPolicy Bypass -File .\mj-agent-clone-bare.ps1 `
    -RepoUrl https://github.com/MJ-AgentLab/mj-agent
```

## Quick start

```bash
# 1. 安装依赖
uv sync

# 2. 准备 .env（Phase 0：手工 copy .env.example；PR2 起用 setup-env.ps1）
cp .env.example .env
#  然后把 POSTGRES_ANALYST_USER / POSTGRES_ANALYST_PASSWORD 填好

# 3. 启动 LangGraph Studio
uv run langgraph dev
#  浏览器打开 Studio 提示的本地 URL，选 "mj_agent" 图
```

## LLM provider

mj-agent 仅使用**火山方舟 (Volcengine Ark) 的 OpenAI 兼容端点 + DeepSeek V3**。

需要在 `.env` 里配置（`.env.example` 已给好 Ark 端点默认值）：

```dotenv
LLM_MODEL_ID=deepseek-v3-2-251201
LLM_THINKING_ENABLED=false
LLM_TIMEOUT_SEC=120
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=<团队方舟 key>
```

没有 `ARK_API_KEY` 时 agent 会直接 `LLMConfigError` fail fast，不做静默降级。合规路径为 Ark 企业协议 + ZDR（已由合规团队确认）。

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

mj-agent 仅访问 mj-system 业务指标域：

- `biz_dws` — analyst 可 SELECT 全部汇总表
- `biz_dwd` — analyst 仅可 SELECT 2 张维度表（`dwd_dim_product_interface`、`dwd_dim_institution`）

权威权限定义位于 mj-system 仓库
`sql/migrations/repeatable/R__analyst_permissions.sql`。

## 项目结构（Phase 0）

```
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
