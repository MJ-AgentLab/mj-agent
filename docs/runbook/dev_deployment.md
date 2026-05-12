---
type: runbook
domain: RUNBOOK
summary: mj-agent DEV 容器化部署 runbook —— 把 PR #40 的镜像跑进 上游业务系统 docker-compose 栈，验证 Chainlit 内网可达 + healthcheck OK，作为 sub 1.I 试用闭环的部署起点
owner: 项目负责人
created: 2026-05-07
updated: 2026-05-12
state: active
track: code
last-verified: 2026-05-12
---

# DEV Deployment Runbook — mj-agent (Phase 1 1.I 试用前置)

> **范围**: 把 mj-agent (PR #40 镜像) 部署进 上游业务系统 DEV docker-compose 栈，让 3-5 名分析师能在内网通过 Chainlit 入口使用。Phase 1 退出标准 **E2** ("mj-agent 容器稳定运行在 DEV，Chainlit 内网可访问") 的实操路径。
>
> **路线图位置**: 1.I 试用闭环 (plan §3.I) 的前置；本 runbook 完成后才能邀分析师上线。

## 1. 前置条件

| 依赖 | 检查命令 | 缺失时的处置 |
|---|---|---|
| Docker Engine ≥ 24 | `docker --version` | `winget install Docker.DockerDesktop` (Win) / 装 Docker CE (Linux) |
| Docker Compose v2 | `docker compose version` | 通常随 Docker Desktop / Engine 自带 |
| 上游业务系统 DEV 栈已起 | `docker ps --filter name=mj-system-postgres` 看到 healthy + `docker network ls --filter name=mj-system-backend-network` 见网络存在 | 先在 上游业务系统 repo 跑 `docker compose up -d` |
| `analyst` 角色凭据 | `.env` 中 `POSTGRES_ANALYST_USER/PASSWORD` 非空 | `scripts\setup-env.ps1` 解密 secrets.enc |
| Volcengine Ark API key | `.env` 中 `ARK_API_KEY` 非空 | 同上 |
| Memory DB 角色密码 | `.env` 中 `MJ_AGENT_MEMORY_USER/PASSWORD` 非空（首次 up 时被 init script 用来创 role；不需在 上游业务系统 pg 上预建任何东西——storage-stack PR 后 mj-agent 自带 postgres 容器自动 bootstrap）| `.env.example` 已给 DEV 默认值，照抄即可 |
| 内网入口端口 (host:8001) 未被占用 | `netstat -ano \| findstr :8001` 空 | 改 docker-compose.mj-agent.yml ports 映射 |
| host 5433 / 6379 未被占用 | `netstat -ano \| findstr ":5433 :6379"` 空 | mj-agent-postgres / mj-agent-redis 端口；改 ports 映射 |

## 2. 部署步骤

### 2.1 mj-agent 镜像构建

mj-agent repo 根目录：

```bash
docker build -f infra/docker/Dockerfile -t mj-agent:0.1 .
docker image ls mj-agent:0.1   # 验证镜像存在；体积 ~ 780MB
```

### 2.2 .env 准备

```bash
cp .env.example .env
.\scripts\setup-env.ps1        # 注入 4 个团队密钥（Windows）

# .env 需要的 6 个键（前 4 个由 setup-env.ps1 注入；后 2 个是 .env.example 默认值，照抄即可改）：
#   POSTGRES_ANALYST_USER  / POSTGRES_ANALYST_PASSWORD   ← 团队密钥
#   ARK_API_KEY                                          ← 团队密钥
#   LANGSMITH_API_KEY                                    ← 团队密钥
#   MJ_AGENT_MEMORY_USER=mj_agent_app                    ← .env.example 默认；首次 up 时被 mj-agent-postgres 容器 init 用来创 role
#   MJ_AGENT_MEMORY_PASSWORD=local-dev-only-replace-in-prod ← 同上；DEV 占位密码可保留
#
# Compose 文件已自动覆盖 POSTGRES_DEV_HOST / MJ_AGENT_MEMORY_HOST / MJ_AGENT_REDIS_HOST 为 service name；不需手动改。
```

### 2.3 启动 mj-agent 栈（独立 compose project）

mj-agent 是**独立 compose project**（`name: mj-agent`，per ADR-008），与 上游业务系统 解耦。前提：上游业务系统 栈已在跑（`mj-system-backend-network` 网络存在 + `mj-system-postgres` healthy）。

**从 mj-agent 仓根目录跑**（ADR-026 4-file profile 分层；DEV 显式 `-f base -f override` + `--env-file .env` 让 compose CLI `${VAR}` substitution 找到仓根 `.env`，避免 `mj-agent-postgres` init 烤入 `:-default` sentinel 密码）：

```bash
docker compose --env-file .env \
               -f infra/docker/docker-compose.mj-agent.yml \
               -f infra/docker/docker-compose.override.yml up -d
docker compose --env-file .env \
               -f infra/docker/docker-compose.mj-agent.yml \
               -f infra/docker/docker-compose.override.yml ps
```

`up -d` 会自动拉起 mj-agent + mj-agent-postgres + mj-agent-redis（depends_on 等 storage healthy 后启动 mj-agent）。首次 up 时 mj-agent-postgres 跑 init script 建 mj_agent_memory DB + role + GRANT。Docker Desktop / Portainer 视图里 上游业务系统 与 mj-agent 是 **2 个独立 compose project group**。

期望输出：

```
NAMES                STATUS                      PORTS
mj-agent             Up 30 seconds (healthy)     0.0.0.0:8001->8000/tcp
mj-agent-postgres    Up 45 seconds (healthy)     0.0.0.0:5433->5432/tcp
mj-agent-redis       Up 45 seconds (healthy)     0.0.0.0:6379->6379/tcp
```

`up -d mj-agent` 会自动拉起 mj-agent-postgres + mj-agent-redis（depends_on）。首次 up 时 mj-agent-postgres 跑 init script 建 mj_agent_memory DB + role + GRANT；mj-agent 容器看到 storage 栈 healthy 后才 start。

### 2.4 内网入口验证

```bash
# 容器内 healthcheck（与 docker inspect 一致）
docker exec mj-agent mj-agent check
# 期望：CHECK OK + profile/biz host/memory db/chainlit/langsmith 5 行摘要

# 内网浏览器：http://<DEV-host-ip>:8001
# 期望：Chainlit "Welcome" 页面 + 输入框
```

## 3. 验证矩阵

部署完成 = 下表全绿：

| ID | 验证 | 命令 / 操作 | 期望 |
|----|------|-------------|------|
| V1 | 3 容器 healthy | `docker ps --filter name=mj-agent --format "{{.Names}}: {{.Status}}"` | mj-agent / mj-agent-postgres / mj-agent-redis 全 `healthy` |
| V2 | biz DB 可达 | `docker exec mj-agent mj-agent check` | `CHECK OK` |
| V3 | memory DB 可达 | 同 V2，输出含 `memory db = mj_agent_memory` | OK |
| V3b | mj-agent-postgres 可直连 | `psql -h localhost -p 5433 -U postgres -d mj_agent_memory -c '\dt'` | 列出 langgraph 检查点表 (checkpoints / checkpoint_writes / checkpoint_blobs / checkpoint_migrations) |
| V3c | redis 可 ping | `docker exec mj-agent-redis redis-cli ping` | `PONG` |
| V4 | Chainlit 监听 | `docker logs mj-agent \| grep "available at"` | `http://0.0.0.0:8000` |
| V5 | 内网访问 | 浏览器打开 `http://<DEV-IP>:8001` | Chainlit Welcome |
| V6 | 一次最小问答 | 在 Chainlit 输入"biz 域有哪些表？" | LLM 调用 list_biz_tables → 输出 65+ 张表 |
| V7 | 数据边界 | 输入"select * from biz_ods.foo" | L1 guardrail 友好拒绝 |
| V8 | LangSmith trace | 上述 V6 完成后看 LangSmith UI mj-agent-dev project | 有新 trace 含 4 个工具调用 |
| V9 | 容器 OOM 阈值 | `docker stats mj-agent mj-agent-postgres mj-agent-redis` | 三容器内存合 < 1GB（无大查询时） |

## 4. 故障排查

> **Chainlit 502 类诊断分流**：先跑 `docker exec mj-agent python -c "import urllib.request as r; print(r.urlopen('http://127.0.0.1:8000/').status)"`
> - 返 `200` → 容器内 OK，问题在 host → 见"Host curl 502 但浏览器 / 容器内 urllib 200"行（**代理类**）
> - 抛异常 / 进不去 → 容器内进程未起或绑错 → 见"Chainlit 502 / connection refused（容器内也不通）"行（**绑定 / 进程类**）

| 现象 | 根因排查 | 处置 |
|------|---------|------|
| 容器启动 30s 后 unhealthy | `docker logs mj-agent`；常见 `ARK_API_KEY not set` / `POSTGRES_ANALYST_USER not set` | 重跑 setup-env.ps1，确认 .env 注入；`docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml up -d --force-recreate mj-agent` |
| Chainlit 502 / connection refused（容器内也不通）| `docker exec mj-agent ss -tlnp \| grep 8000` 看是否监听；CHAINLIT_HOST 必须 `0.0.0.0` 而非 `127.0.0.1` | Dockerfile 已设默认；如被 .env 覆盖 → 移除 .env 中 CHAINLIT_HOST |
| Host curl 502 但浏览器 / 容器内 urllib 200 | host shell 有 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`（如 Clash / v2ray 系统代理）+ 未设 `NO_PROXY`；curl 走代理而代理对 localhost 返 502；浏览器有 implicit localhost bypass | 单次：`curl --noproxy '*' http://localhost:8001/`；持久：`$env:NO_PROXY="localhost,127.0.0.1,::1"`（PowerShell）或 `export NO_PROXY=localhost,127.0.0.1,::1`（bash）；mj-agent 应用本身无问题 |
| `mj-agent check` 报 `memory DB unreachable` | mj-agent-postgres 没起 healthy 或凭据错 | `docker logs mj-agent-postgres` 看 init script 是否跑通；如 .env 改过 MJ_AGENT_MEMORY_USER/PASSWORD 但 volume 持久了旧值 → `docker volume rm mj-agent-postgres-data` 重建（**会丢 checkpoint 历史**）|
| `network mj-system-backend-network not found` | 上游业务系统 栈没起；mj-agent 单独跑会报这个 | 先在 上游业务系统 仓 `docker compose up -d`；再回 mj-agent 跑 up |
| 容器内连 mj-agent-postgres 走 5432 但 host 端口 5433 → 不一致引发误解 | 这是**正常**的：mj-agent → 容器名 mj-agent-postgres:5432（容器内端口）；DBA 从 host 走 5433 是 ports 映射 | 文档写清楚即可，不动配置 |
| 跑 SQL 触发 `statement_timeout` | 单查询 > 60s，DB 侧 GRANT 强制超时 | 改用 aggregate / drill_down 工具拆分；或加 LIMIT |
| LangSmith trace 看不到 | `.env` 中 `LANGSMITH_TRACING=false` | 改 `true` + 验 `LANGSMITH_API_KEY` 非空；`docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml restart mj-agent` |

## 5. 回滚 / 拆栈

mj-agent 是独立 compose project（per ADR-008），拆栈用 mj-agent 自家的 `-f` 链，**不要** 引用上游业务系统的 docker-compose 文件。推荐走 `/mj-agent-infra-env-teardown` SKILL 的 3-level safety（H3 hard-confirm Level 2/3 with 数据丢失告警），手动等价命令：

```bash
# Level 1 — 软停（保留 volume 中的 checkpoint 数据 + redis AOF）
docker compose --env-file .env \
               -f infra/docker/docker-compose.mj-agent.yml \
               -f infra/docker/docker-compose.override.yml \
               down

# Level 2 — 拆栈 + 删 volume（⚠️ 丢 langgraph checkpointer 历史 + redis AOF；仅 dev/test）
docker compose --env-file .env \
               -f infra/docker/docker-compose.mj-agent.yml \
               -f infra/docker/docker-compose.override.yml \
               down -v

# Level 3 — 完全清干净（含本地构建镜像；下次 up 需 --build 重建 ~30s）
docker compose --env-file .env \
               -f infra/docker/docker-compose.mj-agent.yml \
               -f infra/docker/docker-compose.override.yml \
               down -v --rmi local --remove-orphans
```

> **回滚不影响 上游业务系统**：mj-agent + storage 栈走独立 compose project（name: `mj-agent`），仅 attach 到 `mj-system-backend-network`（`external: true`）以消费 biz pg；不持有该网络的 lifecycle。`docker compose down` 只拆 mj-agent / mj-agent-postgres / mj-agent-redis 三容器 + `mj-agent-storage` 内部网络，**不会**带走 `mj-system-postgres` / `mj-system-app` / `mj-system-n8n`。

## 6. 与试用闭环的衔接

部署完毕后启动 1.I 流程（plan §3.I）：

1. 把 V5 内网 URL 发给 3-5 名试用分析师
2. 引导分析师走 [[GUIDE]_Analyst_Day_One|Analyst Day-One GUIDE]] day-1 流程
3. 周度对账（plan §3.I）：
   - bug list（按 P0/P1/P2，模板见 vault `[TEMPLATE]_Trial_Issue.md`）
   - 缺 skill 列表
   - token 预算告警次数（LangSmith trace 统计）
   - 实体解析 miss 列表
4. ≥ 2 周后跑 [[../[CHECKLIST]_Phase_1_Exit|Phase 1 Exit Checklist]] 11 项对账

## 7. Out of scope

- **Production 部署** —— 本 runbook 仅 DEV；prod 走 Phase 2/3（HA / TLS / SSO / observability）
- **多租户隔离** —— roadmap §F.4 永远不做
- **Portainer 一键 stack** —— 需 上游业务系统 配套 PR 把 service 段抄进主 compose；本 runbook 走 drop-in 形态
- **GPU / 本地 LLM 推理** —— mj-agent 纯 Ark API；无 GPU 路径

## 关联文档

- [[infra/docker/README|infra/docker README]]: build / run / standalone 部署详情
- [[GUIDE]_Analyst_Day_One|Analyst Day-One GUIDE]]: 1.I 试用阶段 day-1 流程
- [[adr/[ADR]_006_Mj_System_Db_Boundary|ADR-006]]: 4 层数据边界
- [[adr/[ADR]_009_Read_Only_Connection|ADR-009]]: 只读连接策略
- 上游业务系统 docker-compose: `D:/workspace/10-software-project/projects/上游业务系统/develop/docker-compose.yml`

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-07 | v0.1 | 初稿；sub 1.I 试用前置部署 runbook |
| 2026-05-12 | v0.2 | 结构性刷新：compose 命令切到 ADR-026 4-file profile 链 + 加 `--env-file .env`（PR #155 一致性）；网络名 `上游业务系统-backend-network` → `mj-system-backend-network`（literal Docker artifact）；`docker ps --filter` 改用 `mj-system-postgres` 容器名；§5 回滚段从 pre-ADR-008 drop-in compose 模式重写为独立 compose project 3-level teardown + cross-ref `/mj-agent-infra-env-teardown` |
