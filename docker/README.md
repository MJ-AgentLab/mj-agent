# MJ-Agent — Docker 部署

> Phase 1 sub 1.H — 路线图 v1.6 §4 退出标准 **E2** ("mj-agent 容器稳定运行在 DEV，Chainlit 内网可访问")。

本目录提供 mj-agent 的容器化运行制品：

| 文件 | 用途 |
|---|---|
| `Dockerfile` | 多阶段 production 镜像（Python 3.13-slim + uv；non-root；TZ=Asia/Shanghai） |
| `entrypoint.sh` | 子命令路由 (`serve` / `check` / `shell` / passthrough) |
| `.dockerignore` | 构建上下文过滤（.venv / .git / docs / artifacts / 密钥） |
| `compose.yaml` | **BASE**（env-agnostic；总是加载）；**独立** compose project (`name: mj-agent`)；自带存储栈（postgres + redis）；attach mj-system biz pg via external network |
| `compose.override.yml` | **DEV** override（auto-loaded；build + 本地 Dockerfile + dev profile env 注入）|
| `compose.test.yml` | **TEST** override（`-f` 显式；Harbor pull + 8C/12G + `MJ_CONFIG_PROFILE=test`）|
| `compose.prod.yml` | **PROD** override（`-f` 显式；Harbor pull + 4C/12G + json-file logging + `MJ_CONFIG_PROFILE=prod`）|
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
                                       (langgraph AsyncPostgresSaver)

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

## Compose 4-file profile 分层（PR-1 / ADR-025）

mj-agent compose 拆分为 4 个文件，对标 mj-system v3.2.2 模式（base + override + test + prod）：

| Profile | 加载方式（**全部用显式 `-f` 链**） | 关键差异 | 资源限制 |
|---|---|---|---|
| **dev** | `-f compose.yaml -f compose.override.yml` | `build:` 本地 Dockerfile + `MJ_CONFIG_PROFILE=dev` + `POSTGRES_DEV_HOST: mj-postgres` | 无 |
| **test** | `-f compose.yaml -f compose.test.yml` | Harbor pull + `MJ_CONFIG_PROFILE=test` + `POSTGRES_TEST_HOST: mj-postgres` + `MJ_AGENT_LOG_LEVEL=debug` | mj-agent 8C/12G；mj-agent-postgres 4C/8G |
| **prod** | `-f compose.yaml -f compose.prod.yml` | Harbor + `MJ_CONFIG_PROFILE=prod` + `POSTGRES_PROD_HOST: mj-postgres` + `MJ_DEBUG=false` + json-file logging | mj-agent 4C/12G；mj-agent-postgres 4C/8G；mj-agent-redis 1C/1G |

> **为什么 dev 也要显式 `-f override`？** docker compose 的 override.yml auto-load 仅在 cwd default 模式触发（默认查找 `docker-compose.yml` + `compose.override.yml` 同目录）。本仓 compose 文件在 `docker/` 子目录 + 用 `-f` 显式 base，auto-load 不生效。让 dev 与 test/prod 命令保持一致 `-f base -f overlay` 形态，反而更可读。

> **DGX 算力消费侧支持** 不需要新 compose 文件：在任一 profile 的 `.env` 把 `LLM_PROVIDER=local-openai-compat` + `LLM_BASE_URL=http://192.168.0.189:8000/v1` 即可走 DGX 上的本地 vLLM/SGLang/Ollama endpoint（详见 PR-2 / ADR-025）。

**Compose project 名称**：`name: mj-agent` 在 base 中声明，跨 4 profile 不变。Docker Desktop / Portainer 视图始终显示 1 个 mj-agent project，与 mj-system 隔离（per ADR-008）。

**Pre-flight TEST/PROD 主机**：mj-system 栈必须先在同主机 up（`mj-system-backend-network` 由 mj-system 创建；mj-agent 仅 attach 为 external consumer）。

## Quick start

### 单独跑 (no mj-system stack)

```bash
# 1. 配 .env（用 setup-env.ps1 注密钥；或手填 POSTGRES_ANALYST_USER/PASSWORD + ARK_API_KEY）
cp .env.example .env
.\scripts\setup-env.ps1            # Windows 团队成员
# (手动填 .env 也行；Docker 容器读 env-file 即可)

# 2. 把 .env 里 POSTGRES_DEV_HOST 指向宿主机 DB（Docker Desktop）：
#    POSTGRES_DEV_HOST=host.docker.internal

# 3. 构建 + 跑
docker build -f docker/Dockerfile -t mj-agent:0.1 .
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

### Standalone deploy (推荐；mj-agent 独立 compose project)

**前提**：mj-system 栈已经在跑（mj-postgres 容器存在 + `mj-system-backend-network` 网络存在）。验证：

```bash
docker network ls --filter name=mj-system-backend-network    # 应见 mj-system-backend-network
docker ps --filter name=mj-system-postgres                    # 应见 healthy
```

**启动 mj-agent 栈**（**从 mj-agent 仓根目录**，独立 project；profile 详见上文 §Compose 4-file profile 分层）：

```bash
# DEV (显式 -f base -f override; override.yml 不自动加载因 -f 显式)
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.override.yml up -d
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.override.yml ps
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.override.yml logs -f mj-agent
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.override.yml down       # 拆栈，保留 volume

# TEST (192.168.0.179)
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.test.yml up -d

# PROD (192.168.0.106)
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.prod.yml up -d
```

`up -d` 会拉起 mj-agent + mj-agent-postgres + mj-agent-redis（depends_on 自动等 storage healthy）。Docker Desktop / Portainer 视图里现在看到 **2 个独立的 compose project**：

```
mj-system    (mj-system 仓自管；含 mj-postgres / mj-app / mj-n8n / ...)
mj-agent     (本仓；含 mj-agent / mj-agent-postgres / mj-agent-redis)
```

容器内的 service-name DNS：
- biz 查询：`mj-postgres:5432`（在 mj-agent 跨 project attach 的 `mj-system-backend-network` 上）
- memory checkpointer：`mj-agent-postgres:5432`（在 `mj-agent-storage` 私有网络）
- redis（未来）：`mj-agent-redis:6379`（同上）

Compose 文件里 mj-agent 的 `environment:` 段已经把 `POSTGRES_DEV_HOST` / `MJ_AGENT_MEMORY_HOST` / `MJ_AGENT_REDIS_HOST` 都覆盖为各自的 service name，分析师只需在 `.env` 里填 6 把团队密钥（4 个走 secrets.enc 注入 + `MJ_AGENT_MEMORY_USER/PASSWORD` 也走 bundle）。

Chainlit 暴露在 host:**8001**；mj-agent-postgres host:**5433**；mj-agent-redis host:**6379**。

> **为何 standalone 而非 multi-`-f` chain（历史路径）？** 历史上 storage-stack PR + hotfix PR #43 推荐 "from mj-system root with multiple `-f`" 的形态，但那会把 mj-agent 全部容器并入 mj-system compose project（Docker Desktop 列表里看不到独立 mj-agent group）+ 强制使用 `${MJ_AGENT_ROOT}` 路径变量解决跨 project_directory 解析问题。PR #44 standalone 改造后：mj-agent 完全独立 compose project，路径相对当前 compose 文件位置（无需 env var），mj-system 栈不受任何影响。
>
> **不推荐**继续用 `docker compose -f mj-system.yml -f mj-agent.yml ...` 形态——会触发 `name: mj-agent` 与 mj-system 隐式 project name 的冲突，把 mj-system 容器名也重命名为 `mj-agent-*`。两边各自 `up`/`down`，仅靠 `mj-system-backend-network` (external) 串联。

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

- **本地 dev**: `scripts/setup-env.ps1` 解密 `config/secrets.enc` (AES-256-CBC + PBKDF2)，注入 **6 个团队密钥**到 `.env`
- **Docker 容器**: 不解密；密钥通过 `--env-file .env` / Compose `environment` / Portainer Stack 变量 / Docker secrets 注入；`config/secrets.enc` 不打包进镜像（被 `.dockerignore` 排除）

理由：`setup-env.ps1` 依赖 OpenSSL CLI + 团队口令，不适合容器场景；orchestrator-side secrets 是更标准做法。

### secrets.enc bundle（团队共管，6 把键）

| 变量 | 用途 |
|---|---|
| `POSTGRES_ANALYST_USER` | biz 域只读 role 用户名（ADR-006 L4） |
| `POSTGRES_ANALYST_PASSWORD` | biz 域只读 role 密码 |
| `ARK_API_KEY` | Volcengine Ark LLM 出口；缺则 LLMConfigError fail-fast |
| `LANGSMITH_API_KEY` | LangSmith tracing；可选（LANGSMITH_TRACING=false 时无关） |
| `MJ_AGENT_MEMORY_USER` | mj-agent-postgres 上的 RW role 用户名（storage-stack PR 加入） |
| `MJ_AGENT_MEMORY_PASSWORD` | 同上密码；首次 docker compose up 时 init script 用此创建 role |

更新流程：编辑 `config/secrets.conf`（解密后产物）→ 跑 `.\scripts\encrypt-secrets.ps1` 重打包 → `git commit config/secrets.enc`。

### 容器自管密钥（不在 secrets.enc，每实例独立）

| 变量 | 来源 | 说明 |
|---|---|---|
| `MJ_AGENT_PG_SUPERUSER_PASSWORD` | `.env`（可选） | mj-agent-postgres 自己的 super-user 密码；只在 DBA 直连查 checkpoint 表时用，可不设让其 fall back 到默认占位 |
| `MJ_AGENT_REDIS_PASSWORD` | `.env`（可选） | 留空 → redis 不开 requirepass（仅内部网络可达，DEV 可接受）；填值 → 启用 |

理由：这 2 个密钥是**容器自管**的——每个 mj-agent 部署实例可有不同的值（DBA 给不同 DBA 不同直连密码；redis password 按部署环境威胁面定）；不需要团队集中分发；不进 `secrets.enc`。PROD 阶段（Phase 2/3）会换成 Docker secrets。

## Troubleshooting

| 现象 | 排查 |
|---|---|
| `mj-agent check` 容器内退出码 1 | `docker logs mj-agent`；常见：`POSTGRES_ANALYST_USER` 未注入 / `ARK_API_KEY` 未注入 / mj-postgres 还没起 healthy / mj-agent-postgres 还没起 healthy |
| Chainlit 访问 connection refused | 确认 host port 8001 → container 8000，且 `CHAINLIT_HOST=0.0.0.0`（默认在 Dockerfile 里设了）|
| Host curl 502 但浏览器正常 | host shell `HTTP_PROXY` / `HTTPS_PROXY` 系统代理未排除 localhost（Clash / v2ray 常见）；用 `curl --noproxy '*' http://localhost:8001/` 单次绕过，或设 `NO_PROXY=localhost,127.0.0.1,::1` 持久化；详见 `capabilities/infrastructure/docker-compose/runbook.md` §3 |
| 容器内 `host.docker.internal` 解析不了（Linux） | 加 `--add-host=host.docker.internal:host-gateway`，或共部署到 mj-system 网络用 `mj-postgres` service name |
| 镜像构建失败 in `uv sync --frozen` | 检查 `uv.lock` 是否提交；本仓不允许漂移 lock |
| mj-agent-postgres 启动失败：`MJ_AGENT_MEMORY_USER missing` | `.env` 里没填这 2 个值；填上后 `docker compose up -d --force-recreate mj-agent-postgres` |
| 改了 `MJ_AGENT_MEMORY_USER` / `_PASSWORD` 后 connect 失败 | postgres 持久卷里 role 已用旧值创建；要么改回原值，要么 `docker volume rm mj-agent-postgres-data` 全清重建（**会丢所有 checkpoint 历史**）|
| mj-agent-redis 报 `Setting 'requirepass' is not allowed` | redis 命令注入 vs requirepass 冲突；通常是 .env 里的 `MJ_AGENT_REDIS_PASSWORD` 含特殊字符（` ` / `'` / `"` / `$`），换成 a-z A-Z 0-9 或 set 空 |

## 构建产出验证

```bash
docker build -f docker/Dockerfile -t mj-agent:dev .

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
- **GPU / local LLM serving**：mj-agent 自身不运行 vLLM；任一 dev/test/prod profile 都可通过 `.env` 设 `LLM_PROVIDER=local-openai-compat` + `LLM_BASE_URL` 切换到 DGX 外部 OpenAI 兼容 endpoint（ADR-027；DGX 不是部署 profile）
- **历史 secrets 自动迁移**：`config/secrets.enc` 走团队口令分发；容器不解密

---

**References**: ADR-006 (data boundary)，ADR-009 (read-only connection)，plan `[PLAN]_Phase_1_Decomposition.md` §3.H，roadmap v1.6 §4 E2.
