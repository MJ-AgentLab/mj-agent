---
type: runbook
domain: RUNBOOK
summary: mj-agent DEV 容器化部署 runbook —— 把 PR #40 的镜像跑进 mj-system docker-compose 栈，验证 Chainlit 内网可达 + healthcheck OK，作为 sub 1.I 试用闭环的部署起点
owner: 项目负责人
created: 2026-05-07
updated: 2026-05-07
state: active
track: code
---

# DEV Deployment Runbook — mj-agent (Phase 1 1.I 试用前置)

> **范围**: 把 mj-agent (PR #40 镜像) 部署进 mj-system DEV docker-compose 栈，让 3-5 名分析师能在内网通过 Chainlit 入口使用。Phase 1 退出标准 **E2** ("mj-agent 容器稳定运行在 DEV，Chainlit 内网可访问") 的实操路径。
>
> **路线图位置**: 1.I 试用闭环 (plan §3.I) 的前置；本 runbook 完成后才能邀分析师上线。

## 1. 前置条件

| 依赖 | 检查命令 | 缺失时的处置 |
|---|---|---|
| Docker Engine ≥ 24 | `docker --version` | `winget install Docker.DockerDesktop` (Win) / 装 Docker CE (Linux) |
| Docker Compose v2 | `docker compose version` | 通常随 Docker Desktop / Engine 自带 |
| mj-system DEV 栈已起 | `docker ps --filter name=mj-system` 看到 `mj-app` + `mj-postgres` healthy | 先在 mj-system repo 跑 `docker compose up -d` |
| `analyst` 角色凭据 | `.env` 中 `POSTGRES_ANALYST_USER/PASSWORD` 非空 | `scripts\setup-env.ps1` 解密 secrets.enc |
| Volcengine Ark API key | `.env` 中 `ARK_API_KEY` 非空 | 同上 |
| `mj_agent_memory` DB 已建 | `psql ... -c '\\l mj_agent_memory'` 命中 | 跑 `src/mj_agent/memory/migrations/001_checkpoint_tables.sql` 中 DBA 段 |
| 内网入口端口 (host:8001) 未被占用 | `netstat -ano \| findstr :8001` 空 | 改 docker-compose.mj-agent.yml ports 映射 |

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
# 编辑 .env，将 POSTGRES_DEV_HOST 改为 docker compose 内的 service name：
#     POSTGRES_DEV_HOST=mj-postgres
# (compose 文件已自动覆盖此值，但本地 docker run 模式需要手动改)
```

### 2.3 加入 mj-system DEV 栈

mj-system repo 根目录（mj-agent checkout 在同级 `../mj-agent/`）：

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f ../mj-agent/infra/docker/docker-compose.mj-agent.yml \
  up -d mj-agent

docker ps --filter name=mj-agent --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

期望输出：

```
NAMES       STATUS                      PORTS
mj-agent    Up 30 seconds (healthy)     0.0.0.0:8001->8000/tcp
```

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
| V1 | 容器 healthy | `docker inspect mj-agent --format '{{.State.Health.Status}}'` | `healthy` |
| V2 | biz DB 可达 | `docker exec mj-agent mj-agent check` | `CHECK OK` |
| V3 | memory DB 可达 | 同 V2，输出含 `memory db = mj_agent_memory` | OK |
| V4 | Chainlit 监听 | `docker logs mj-agent \| grep "available at"` | `http://0.0.0.0:8000` |
| V5 | 内网访问 | 浏览器打开 `http://<DEV-IP>:8001` | Chainlit Welcome |
| V6 | 一次最小问答 | 在 Chainlit 输入"biz 域有哪些表？" | LLM 调用 list_biz_tables → 输出 65+ 张表 |
| V7 | 数据边界 | 输入"select * from biz_ods.foo" | L1 guardrail 友好拒绝 |
| V8 | LangSmith trace | 上述 V6 完成后看 LangSmith UI mj-agent-dev project | 有新 trace 含 4 个工具调用 |
| V9 | 容器 OOM 阈值 | `docker stats mj-agent` | 内存 < 800MB（无大查询时） |

## 4. 故障排查

| 现象 | 根因排查 | 处置 |
|------|---------|------|
| 容器启动 30s 后 unhealthy | `docker logs mj-agent`；常见 `ARK_API_KEY not set` / `POSTGRES_ANALYST_USER not set` | 重跑 setup-env.ps1，确认 .env 注入；`docker compose up -d --force-recreate mj-agent` |
| Chainlit 502 / connection refused | `docker exec mj-agent ss -tlnp \| grep 8000` 看是否监听；CHAINLIT_HOST 必须 `0.0.0.0` 而非 `127.0.0.1` | Dockerfile 已设默认；如被 .env 覆盖 → 移除 .env 中 CHAINLIT_HOST |
| `mj-agent check` 报 `memory DB unreachable` | mj_agent_memory DB 未建 / 凭据错 | 跑 migrations/001_checkpoint_tables.sql 中 DBA bootstrap 段 |
| 跑 SQL 触发 `statement_timeout` | 单查询 > 60s，DB 侧 GRANT 强制超时 | 改用 aggregate / drill_down 工具拆分；或加 LIMIT |
| LangSmith trace 看不到 | `.env` 中 `LANGSMITH_TRACING=false` | 改 `true` + 验 `LANGSMITH_API_KEY` 非空；`docker compose restart mj-agent` |

## 5. 回滚 / 拆栈

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f ../mj-agent/infra/docker/docker-compose.mj-agent.yml \
  rm -sf mj-agent
docker image rm mj-agent:0.1   # 可选；保留则下次 up 秒级
```

> **回滚不影响 mj-system**：mj-agent service 走 drop-in compose 文件，只附 `mj-system-backend-network` 不持有它。`docker compose down` 不会带走 mj-postgres。

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
- **Portainer 一键 stack** —— 需 mj-system 配套 PR 把 service 段抄进主 compose；本 runbook 走 drop-in 形态
- **GPU / 本地 LLM 推理** —— mj-agent 纯 Ark API；无 GPU 路径

## 关联文档

- [[infra/docker/README|infra/docker README]]: build / run / co-deploy 详情
- [[GUIDE]_Analyst_Day_One|Analyst Day-One GUIDE]]: 1.I 试用阶段 day-1 流程
- [[adr/[ADR]_006_Mj_System_Db_Boundary|ADR-006]]: 4 层数据边界
- [[adr/[ADR]_009_Read_Only_Connection|ADR-009]]: 只读连接策略
- mj-system docker-compose: `D:/workspace/10-software-project/projects/mj-system/develop/docker-compose.yml`

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-07 | v0.1 | 初稿；sub 1.I 试用前置部署 runbook |
