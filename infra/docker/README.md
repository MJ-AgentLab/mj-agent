# MJ-Agent — Docker 部署

> Phase 1 sub 1.H — 路线图 v1.6 §4 退出标准 **E2** ("mj-agent 容器稳定运行在 DEV，Chainlit 内网可访问")。

本目录提供 mj-agent 的容器化运行制品：

| 文件 | 用途 |
|---|---|
| `Dockerfile` | 多阶段 production 镜像（Python 3.13-slim + uv；non-root；TZ=Asia/Shanghai） |
| `entrypoint.sh` | 子命令路由 (`serve` / `check` / `shell` / passthrough) |
| `.dockerignore` | 构建上下文过滤（.venv / .git / docs / artifacts / 密钥） |
| `docker-compose.mj-agent.yml` | drop-in service 定义；co-deploy mj-system DEV 栈 |

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

mj-agent 加进同一 `mj-system-backend-network`：

```bash
# from mj-system repo root, with mj-agent checked out at ../mj-agent
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f ../mj-agent/infra/docker/docker-compose.mj-agent.yml \
  up -d mj-agent
```

Chainlit 暴露在 host:**8001**（避开 mj-app 占用的 8000）。容器内 mj-agent 通过 service name `mj-postgres:5432` 直连数据库——`POSTGRES_DEV_HOST` 在 compose 文件里被覆盖为 `mj-postgres`。

> **mj-system 仓 PR 协调**（详见 plan §3.H）：当前 `docker-compose.mj-agent.yml` 走 mj-agent 仓侧 drop-in 形态，**不**强制 mj-system 仓收编 service 定义。如需把 mj-agent 写进 mj-system `docker-compose.yml` 主文件（以便 Portainer 一键 stack 部署），起 mj-system 配套 PR：拷贝本文件 services 段进 mj-system `docker-compose.yml` + 把 `mj-system-backend-network` 上 `external: true` 改回主 compose 内。本仓 PR 不依赖 mj-system 改动；任何一边都能独立 review/合并。

## 端口约定

| 容器内 | 宿主机 | 说明 |
|---|---|---|
| 8000 (chainlit) | 8001 | mj-agent UI；避开 mj-system mj-app 的 8000 |
| 5432 (postgres) | 5432 | mj-system 已映射；mj-agent 不再映射 |

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

- **本地 dev**: `scripts/setup-env.ps1` 解密 `config/secrets.enc` (AES-256-CBC + PBKDF2)，注入 4 个密钥到 `.env`
- **Docker 容器**: 不解密；密钥通过 `--env-file .env` / Compose `environment` / Portainer Stack 变量 / Docker secrets 注入；`config/secrets.enc` 不打包进镜像（被 `.dockerignore` 排除）

理由：`setup-env.ps1` 依赖 OpenSSL CLI + 团队口令，不适合容器场景；orchestrator-side secrets 是更标准做法。

## Troubleshooting

| 现象 | 排查 |
|---|---|
| `mj-agent check` 容器内退出码 1 | `docker logs mj-agent`；常见：`POSTGRES_ANALYST_USER` 未注入 / `ARK_API_KEY` 未注入 / mj-postgres 还没起 healthy |
| Chainlit 访问 connection refused | 确认 host port 8001 → container 8000，且 `CHAINLIT_HOST=0.0.0.0`（默认在 Dockerfile 里设了）|
| 容器内 `host.docker.internal` 解析不了（Linux） | 加 `--add-host=host.docker.internal:host-gateway`，或共部署到 mj-system 网络用 `mj-postgres` service name |
| 镜像构建失败 in `uv sync --frozen` | 检查 `uv.lock` 是否提交；本仓不允许漂移 lock |

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
