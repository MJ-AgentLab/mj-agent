---
type: adr
domain: OPS
summary: docker-compose 4-file 分层 (base + override + test + prod) 实现 dev/test/prod 三环境部署；compose project name 跨 profile 不变；dev 也用显式 -f 链（auto-load 不生效的 quirk）
owner: 项目负责人
created: 2026-05-11
updated: 2026-05-11
state: active
decision: accepted
track: code
tags:
  - adr
  - infrastructure
  - docker
  - multi-environment
  - profile
---

# ADR-026: Multi-Environment Compose Profile (4-file Layering)

> **历史**：本 ADR 与 [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] / [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]] 由历史 ADR-025 拆分而来（ADR-025 已 archive 至 `archive/decisions/superseded/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction.md`）。本 ADR 聚焦 docker-compose 多环境部署一题。

## Context

Phase 1 sub 1.H（PR #40）落地 mj-agent dev compose 后，mj-agent 一直处于 dev-only 形态。具体缺口：

- [[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] §Decision 已经明确 "环境矩阵 DEV/TEST/PROD 时间表对齐"；但 `docker/compose.yaml` 单文件硬编码 dev profile（`POSTGRES_DEV_HOST: mj-postgres` / `com.mj-agent.environment: "development"` 写死、无 `MJ_CONFIG_PROFILE` 注入、无资源限制）
- TEST/PROD 覆盖文件从未补齐，无法在 192.168.0.179 (TEST) / .106 (PROD) 主机部署
- 项目负责人 2026-05-09 决策：**mj-agent 容器栈跟随上游业务系统在 TEST/PROD 同主机部署**；DGX (192.168.0.189) 仅作算力节点，**不部署任何应用服务（含 mj-agent）** → DGX 支持本质是 LLM provider 抽象（[[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]），**不**在本 ADR 引入 dgx profile

## Decision

### D.1 docker-compose 4-file 分层

| 文件 | 加载 | 关键差异 | 资源限制 |
|---|---|---|---|
| `compose.yaml` | 始终 | env-agnostic base；env vars `${VAR:-default}`；`name: mj-agent`；通用 env (`MJ_AGENT_MEMORY_HOST` / `CHAINLIT_HOST=0.0.0.0`)；networks + volumes 声明 | 无 |
| `compose.override.yml` | dev `-f` 显式 | `build:` 本地 Dockerfile；`MJ_CONFIG_PROFILE=dev`；`POSTGRES_DEV_HOST=mj-postgres`；`MJ_AGENT_LOG_LEVEL=debug` | 无 |
| `compose.test.yml` | test `-f` 显式 | Harbor pull `8.135.38.175/mj-agent/mj-agent:0.1`；`MJ_CONFIG_PROFILE=test`；`POSTGRES_TEST_HOST=mj-postgres` | mj-agent 8C/12G；mj-agent-postgres 4C/8G |
| `compose.prod.yml` | prod `-f` 显式 | Harbor pull；`MJ_CONFIG_PROFILE=prod`；`POSTGRES_PROD_HOST=mj-postgres`；`MJ_DEBUG=false`；`MJ_AGENT_LOG_LEVEL=warning`；json-file logging | mj-agent 4C/12G；mj-agent-postgres 4C/8G |

### D.2 重要 quirk：dev 也用显式 `-f base -f override`

原因：本仓 compose 文件位于 `docker/` 子目录 + 用 `-f` 显式 base 时，docker compose 的 override.yml auto-load **不生效**（auto-load 仅在 cwd default 模式触发；compose 文件不在仓根时触发不到）。让 dev/test/prod 都用相同 `-f base -f overlay` 形态反而更可读、与 test/prod 命令模式一致。

### D.3 Compose project name 跨 profile 不变

`name: mj-agent` 跨 4 profile 不变（per [[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] 独立 compose project）。Docker Desktop / Portainer 视图中 mj-agent 始终显示为单一 group。

### D.4 操作命令矩阵

```bash
# DEV (本地 / Studio mode 替代见 mj-agent-infra-studio-probe SKILL)
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.override.yml up -d

# TEST (192.168.0.179)
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.test.yml up -d

# PROD (192.168.0.106)
docker compose --env-file .env -f docker/compose.yaml \
               -f docker/compose.prod.yml up -d
```

teardown 同模式（同 -f 链 + `down` / `down -v` / `down -v --rmi local`，per `mj-agent-infra-env-teardown` SKILL）。

## Consequences

### 正面

- **operational consistency**：mj-agent 4 profile compose 模式可类比上游业务系统的多环境实践，分析师切环境心智负担低；3 主机（dev / test / prod）部署语义清晰
- **reviewer-friendly**：compose 改动 diff 按 profile 颗粒度可独立审查
- **failsafe**：上游业务系统栈作为前置依赖（network 必须存在），缺则 mj-agent 报 `network not found` fail-fast

### 负面

- **dev 命令更长**：dev 也用显式 `-f base -f override`（auto-load 不生效）— quirk 文档化在 base header / `docker/README.md` §Profile Matrix / `mj-agent-infra-env-teardown` SKILL `Do not use for:`
- **4 profile compose 维护负担**：base 改 service 结构需要同步审查 3 个 overlay 是否冲突 — 接受
- **Harbor image 依赖**：test/prod profile 引用 `8.135.38.175/mj-agent/mj-agent:0.1`；CI build & push 流程 + Harbor namespace 创建是本 ADR 范围之外的依赖

### 暂未实现（用户决策；out-of-scope）

- **`docker-compose.dgx.yml`**：DGX 不部署 mj-agent；无 profile 概念
- **`Profile = Literal[..., "dgx"]`**：DGX 不部署 mj-agent，无 profile 概念
- **`POSTGRES_DGX_HOST/PORT`**：DGX 上无 biz pg；mj-agent 在 DGX 模式下访问 biz pg 仍走 PROD/TEST `POSTGRES_*_HOST`

## Alternatives considered

- **A. 单一 compose 文件 + 多 `MJ_CONFIG_PROFILE` 分支**（sed/template 在 entrypoint 切换）：拒绝。compose 4-file 模式更易 reviewer 视角清晰；4-file 是行业成熟实践（Docker 官方文档示例 + 多数生产部署）。
- **B. 加 `Profile = "dgx"` 到 enum + 写 `docker-compose.dgx.yml`**：用户决策 2 否决。DGX 仅算力，无 biz pg / 应用服务部署，加 profile 只会引入混淆。
- **C. mj-agent 部署 LLM serving 容器（vLLM in compose）**：拒绝。GPU runtime + 模型权重 mount + 显存预留 = 大幅扩 compose 范围；mj-agent 仅 LLM 消费侧（详见 [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]）。

## References

- [[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] — 独立 compose project + 独立 secrets pipeline；4-file 分层不破坏 `name: mj-agent`
- [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] — DGX 算力消费侧抽象（与本 ADR 同期落地，原 ADR-025 拆分姊妹）
- [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]] — MCP 13 servers + governance STANDARD（同期落地，原 ADR-025 拆分姊妹）
- [[archive/decisions/superseded/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction|ADR-025（archive）]] — 历史 bundle ADR；本 ADR 是其拆分子项之一
- `docker/compose.yaml` + `docker/compose.{override,test,prod}.yml` — 4-file 实文件
- `mj-agent-infra-env-teardown` SKILL — teardown 流程（同 -f 链；3-level 安全模式）
- 实施 PRs：[#99](https://github.com/MJ-AgentLab/mj-agent/pull/99)（compose layering 落地）+ [#104](https://github.com/MJ-AgentLab/mj-agent/pull/104)（env-teardown SKILL + ADR-025 originally）
