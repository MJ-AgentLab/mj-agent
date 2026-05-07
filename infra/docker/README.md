# MJ-Agent — Docker 部署

> Phase 1 sub 1.H — 路线图 v1.6 §4 退出标准 **E2** ("mj-agent 容器稳定运行在 DEV，Chainlit 内网可访问")。

本目录提供 mj-agent 的容器化运行制品：

| 文件 | 用途 |
|---|---|
| `Dockerfile` | 多阶段 production 镜像（Python 3.13-slim + uv；non-root；TZ=Asia/Shanghai） |
| `entrypoint.sh` | 子命令路由 (`serve` / `check` / `shell` / passthrough) |
| `.dockerignore` | 构建上下文过滤（.venv / .git / docs / artifacts / 密钥） |
| `docker-compose.mj-agent.yml` | drop-in service 定义；mj-agent + 自带存储栈（postgres + redis）；co-deploy mj-system DEV 栈 |
| `postgres-init/01-bootstrap-mj-agent-memory.sh` | mj-agent-postgres 容器首次初始化时自动建 mj_agent_memory DB + role + GRANT |

## 存储栈架构 (storage-stack PR)

mj-agent 现在自带 2 个存储容器，与 mj-system 的 mj-postgres 完全分离：

```
mj-system 仓                        mj-agent 仓 (本仓)
─────────────────                   ────────────────────────────
mj-postgres (biz)  ◄────────────────  mj-agent (chainlit + agent)
  analyst RO                            │ ▲
                                        │ │ memory checkpointer (RW)
                                        ▼ │
                                     mj-agent-postgres
                                       (langgraph PostgresSaver)

                                     mj-agent-redis (future use;
                                       container ready，no Python
                                       client wired yet)
```

| 容器 | 用途 | 网络 |
|---|---|---|
| `mj-agent` | chainlit UI + agent runtime | `mj-system-backend-network` (访问 biz pg) + `mj-agent-storage` (访问 memory/redis) |
| `mj-agent-postgres` | langgraph 检查点 / 线程持久化 | `mj-agent-storage`（**没**有 biz 域可见性） |
| `mj-agent-redis` | 预留（session cache / streaming buffer / rate limit；当前无业务）| `mj-agent-storage` |

理由：mj-agent 的状态生命周期（线程 / 检查点 / 未来缓存）与 mj-system 的业务数据生命周期完全脱钩；存储栈分离让 mj-system DBA 不需要为 mj-agent 的写流量审计；备份策略也分离。

设计约束 mirror mj-system v3.2.2：相同 Python 基础镜像 / 时区 / non-root uid / healthcheck 节奏，方便分析师在同一台开发机/同一 Portainer Stack 共部署。

## Quick start

### 单独跑 (no mj-system co-deploy)

```bash
# 1. 配 .env（用 setup-env.ps1 注密钥；或手填 POSTGRES_ANALYST_USER/PASSWORD + ARK_API_KEY）
cp .env.example .env
.\scripts\setup-env.ps1            # Windows 团队成员
# (手动填 .env 也行；Docker 容器读 env-file 即可)

# 2. 把 .env 里 POSTGRES_DEV_HOST 指向宿主机 DB（Docker Desktop）：
#    POSTGRES_DEV_HOST=host.docker.internal

# 3. 构建 + 跑
docker build -f infra/docker/Dockerfile -t mj-agent:0.1 .
docker run --rm \
  --env-file .env \
  -p 8001:8000 \
  mj-agent:0.1

# Chainlit 现在监听 http://localhost:8001（容器内 0.0.0.0:8000）
```

健康检查 (一次性 probe)：

```bash
docker run --rm --env-file .env mj-agent:0.1 check
# 等价于 uv run mj-agent check —— 探活 biz DB + Ark + memory DB
```

调试 shell：

```bash
docker run --rm -it --env-file .env mj-agent:0.1 shell
```

### Co-deploy with mj-system (推荐 DEV)

mj-system 已经在 `docker-compose.yml` + `docker-compose.override.yml` 起了：

- `mj-postgres` — biz 数据库（mj-agent 走 analyst role）
- `mj-app` — FastAPI 主程序，host:8000
- `mj-n8n` — workflow 平台，host:5678

mj-agent + 存储栈加进同一 stack：

```bash
# from mj-system repo root, with mj-agent checked out at ../mj-agent
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f ../mj-agent/infra/docker/docker-compose.mj-agent.yml \
  up -d mj-agent
```

`up -d mj-agent` 会同时拉起 `mj-agent-postgres` + `mj-agent-redis`（mj-agent service depends_on 它们 healthy）。

容器内的 service-name DNS：
- biz 查询：`mj-postgres:5432`（在 `mj-system-backend-network`）
- memory checkpointer：`mj-agent-postgres:5432`（在 `mj-agent-storage`）
- redis（未来）：`mj-agent-redis:6379`（在 `mj-agent-storage`）

Compose 文件里 mj-agent 的 `environment:` 段已经把 `POSTGRES_DEV_HOST` / `MJ_AGENT_MEMORY_HOST` / `MJ_AGENT_REDIS_HOST` 都覆盖为各自的 service name，分析师只需在 .env 里填 `MJ_AGENT_MEMORY_USER` / `MJ_AGENT_MEMORY_PASSWORD`（首次 up 时被 init script 用来创 role）以及现有的 4 个团队密钥即可。

Chainlit 暴露在 host:**8001**（避开 mj-app 占用的 8000）；mj-agent-postgres 暴露 host:**5433**（避开 mj-postgres 的 5432，方便 DBA 用 psql 连查 checkpoint 表）；mj-agent-redis 暴露 host:**6379**（mj-system 无 redis，无冲突）。

> **mj-system 仓 PR 协调**（详见 plan §3.H）：当前 `docker-compose.mj-agent.yml` 走 mj-agent 仓侧 drop-in 形态，**不**强制 mj-system 仓收编 service 定义。如需把 mj-agent + 存储栈写进 mj-system `docker-compose.yml` 主文件（以便 Portainer 一键 stack 部署），起 mj-system 配套 PR：拷贝本文件 services 段（含 3 个服务 + `mj-agent-storage` network + 2 个 volume）进 mj-system `docker-compose.yml`。本仓 PR 不依赖 mj-system 改动；任何一边都能独立 review/合并。

## 端口约定

| 容器 | 容器内 | 宿主机 | 说明 |
|---|---|---|---|
| mj-agent | 8000 (chainlit) | **8001** | mj-agent UI；避开 mj-system mj-app 的 8000 |
| mj-postgres (mj-system) | 5432 | 5432 | mj-system 已映射；mj-agent 不再映射 |
| mj-agent-postgres | 5432 | **5433** | memory DB；避开 mj-postgres 的 5432 |
| mj-agent-redis | 6379 | 6379 | redis；mj-system 无冲突 |

## 数据边界 (ADR-006 / ADR-009)

容器化部署不改变 4 层可见性边界，只换了入口形态：

| 层 | 容器中位置 |
|---|---|
| L1 guardrail | 镜像里的 `tools/sql/guardrail.py` (regex) |
| L1b precheck | 镜像里的 `tools/sql/precheck.py` (sqlglot AST) |
| L2 SKILL semantics | 镜像里的 `skills/*/SKILL.md` + `biz_catalog/qcm_catalog.yaml` |
| L3 connection | `default_transaction_read_only=on` + `lock_timeout=5s` (`integrations/mj_system_db.py`) |
| L4 role | DB-side `GRANT` + `statement_timeout=60s`（mj-system R__analyst_permissions.sql；不在容器内） |

## 密钥处理 (Docker vs 本地)

- **本地 dev**: `scripts/setup-env.ps1` 解密 `config/secrets.enc` (AES-256-CBC + PBKDF2)，注入 4 个团队密钥（`POSTGRES_ANALYST_USER/PASSWORD`、`ARK_API_KEY`、`LANGSMITH_API_KEY`）到 `.env`
- **Docker 容器**: 不解密；密钥通过 `--env-file .env` / Compose `environment` / Portainer Stack 变量 / Docker secrets 注入；`config/secrets.enc` 不打包进镜像（被 `.dockerignore` 排除）

理由：`setup-env.ps1` 依赖 OpenSSL CLI + 团队口令，不适合容器场景；orchestrator-side secrets 是更标准做法。

### Memory / Redis 密钥（容器自管，不进 secrets.enc）

| 变量 | 来源 | 说明 |
|---|---|---|
| `MJ_AGENT_MEMORY_USER` | `.env` | DEV 默认 `mj_agent_memory`；改它就改 init 创出来的 role 名 |
| `MJ_AGENT_MEMORY_PASSWORD` | `.env` | DEV 用 `local-dev-only-replace-in-prod` 占位；PROD 走 Docker secrets |
| `MJ_AGENT_PG_SUPERUSER_PASSWORD` | `.env`（可选） | mj-agent-postgres 自己的 super-user 密码；只在 DBA 直连查 checkpoint 表时用，可不设让其 fall back 到默认占位 |
| `MJ_AGENT_REDIS_PASSWORD` | `.env`（可选） | 留空 → redis 不开 requirepass（仅内部网络可达，DEV 可接受）；填值 → 启用 |

理由：这 3 个密钥是**容器自管**的，每个 mj-agent 部署实例可以有不同的值；不需要团队集中分发；不进 `secrets.enc`。PROD 阶段（Phase 2/3）会换成 Docker secrets。

## Troubleshooting

| 现象 | 排查 |
|---|---|
| `mj-agent check` 容器内退出码 1 | `docker logs mj-agent`；常见：`POSTGRES_ANALYST_USER` 未注入 / `ARK_API_KEY` 未注入 / mj-postgres 还没起 healthy / mj-agent-postgres 还没起 healthy |
| Chainlit 访问 connection refused | 确认 host port 8001 → container 8000，且 `CHAINLIT_HOST=0.0.0.0`（默认在 Dockerfile 里设了）|
| 容器内 `host.docker.internal` 解析不了（Linux） | 加 `--add-host=host.docker.internal:host-gateway`，或共部署到 mj-system 网络用 `mj-postgres` service name |
| 镜像构建失败 in `uv sync --frozen` | 检查 `uv.lock` 是否提交；本仓不允许漂移 lock |
| mj-agent-postgres 启动失败：`MJ_AGENT_MEMORY_USER missing` | `.env` 里没填这 2 个值；填上后 `docker compose up -d --force-recreate mj-agent-postgres` |
| 改了 `MJ_AGENT_MEMORY_USER` / `_PASSWORD` 后 connect 失败 | postgres 持久卷里 role 已用旧值创建；要么改回原值，要么 `docker volume rm mj-agent-postgres-data` 全清重建（**会丢所有 checkpoint 历史**）|
| mj-agent-redis 报 `Setting 'requirepass' is not allowed` | redis 命令注入 vs requirepass 冲突；通常是 .env 里的 `MJ_AGENT_REDIS_PASSWORD` 含特殊字符（` ` / `'` / `"` / `$`），换成 a-z A-Z 0-9 或 set 空 |

## 构建产出验证

```bash
docker build -f infra/docker/Dockerfile -t mj-agent:dev .

# 镜像体积参考（实测 ~ 780MB；mj-system 同栈 ~ 600MB，差额来自 chainlit + matplotlib + openpyxl + langgraph 体系）
docker image ls mj-agent:dev

# 启动 + 30s 后看 healthcheck
docker run -d --name mj-agent-test --env-file .env -p 8001:8000 mj-agent:dev
sleep 30
docker inspect --format='{{.State.Health.Status}}' mj-agent-test
docker rm -f mj-agent-test
```

## 与 Phase 1 其它 sub 的关系

| sub | 关系 |
|---|---|
| 1.A (Chainlit + memory + CLI) | 本镜像入口 = `mj-agent serve` (Chainlit) + `mj-agent check`（healthcheck）—— 复用 1.A 的 typer CLI |
| 1.F (charts + Excel) | `MJ_AGENT_CHART_TMPDIR=/var/lib/mj-agent/charts` 在 Dockerfile 里默认设好；非持久化（容器重启丢失），如需持久化 mount volume 即可 |
| 1.G (contract tests) | 镜像不包含 `tests/`；契约测试在 CI 跑或本地跑（参见 `tests/contract/`），不绑容器 |
| 1.I (试用闭环) | 部署完此镜像 + Chainlit 内网可达 = E2 退出条件，进入 1.I 试用 |

## Out of scope（明示）

- **Production 部署**：本镜像目标 = DEV 内网；prod 走 Phase 2/3 评审（HA、TLS、SSO、observability stack）
- **多租户隔离**：roadmap §F.4 永远不做
- **GPU 加速**：mj-agent 不本地推 LLM；纯 Ark API
- **历史 secrets 自动迁移**：`config/secrets.enc` 走团队口令分发；容器不解密

---

**References**: ADR-006 (data boundary)，ADR-009 (read-only connection)，plan `[PLAN]_Phase_1_Decomposition.md` §3.H，roadmap v1.6 §4 E2.
