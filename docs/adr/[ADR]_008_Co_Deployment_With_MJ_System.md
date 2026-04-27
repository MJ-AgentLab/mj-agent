---
type: adr
domain: OPS
summary: mj-agent 作为 mj-system 的兄弟服务部署在同一 Docker 环境（DEV/TEST/PROD 三套）
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
---

# ADR-008: Co-Deployment with mj-system

## Context

mj-agent 只读访问 mj-system 的 biz 域数据库（见 [[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]]）。
访问路径上存在多个运维问题需要决定：
- 网络：mj-agent 需要访问 PostgreSQL，是部署在 mj-system 同网络内还是跨 VPC
- 环境：mj-system 有三套环境（DEV/TEST/PROD），mj-agent 是复用还是独立搭建
- 密钥：`POSTGRES_ANALYST_USER/PASSWORD`、`ARK_API_KEY` 等配置的分发策略

独立环境能带来部署隔离，但会让环境矩阵从 3 扩到 9，且需要重新实现 mj-system 已有的 CI/CD 管道与监控栈。
两个项目目前都在 MJ-AgentLab 治理下、由同一团队维护，独立部署的收益不明显。

## Decision

mj-agent 作为 **mj-system 的兄弟服务**部署：

- **环境矩阵**：复用 mj-system 的 DEV / TEST / PROD 三套，不新增环境
- **容器**：mj-agent 作为独立 Docker service 加入 mj-system 的 `docker-compose.*.yml`（命名如 `mj-agent-dev` / `mj-agent-test` / `mj-agent-prod`）
- **网络**：同一 Docker network，通过 service name 访问 PostgreSQL（不走公网）
- **配置合并**：mj-agent 的 `.env` 字段与 mj-system 命名对齐（`POSTGRES_{DEV,TEST,PROD}_HOST/PORT`、`POSTGRES_ANALYST_USER/PASSWORD`、`MJ_CONFIG_PROFILE`），使得两个服务可以共用同一份 `.env`
- **发布**：仓库独立，各自发版（ADR-010），但部署入口通过 mj-ops 的脚本协同

## Consequences

**正面**
- mj-agent 访问 biz 域不经过公网，降低数据出网面
- 运维栈零重建——复用 mj-system 的监控、日志、备份机制
- `.env` 兼容性使得新人只需要一份环境变量说明
- 环境矩阵简单（3 套而非 9 套）

**负面**
- mj-agent 的部署节奏受 mj-system docker-compose 升级影响；mj-system 的基础设施变动需要协同 review
- 两个项目共享单点故障（例如 Docker 宿主机宕机同时影响两者）
- 本 ADR 不适用 Phase 4 多团队场景——届时可能出现多租 mj-agent 实例，需要重新评估

**中性**
- mj-system 与 mj-agent 仓库、代码所有权、版本号、CI 流程仍然独立（ADR-010）；co-deployment 仅是部署层的协同

## Alternatives considered

**独立 Docker 环境（完全隔离）**：拒绝——收益不匹配投入，特别是 Phase 0-2 阶段团队规模和访问模式都很小。

**部署在 Kubernetes 集群（而非 docker-compose）**：保留 Phase 4 以后评估的可能；Phase 0 尊重 mj-system 现有的 compose 栈。

**同一 Docker service 组合进 mj-system 单 Pod**：拒绝——违反进程边界，mj-agent 的 Python 运行时（GIL、event loop、requirements）不应与 mj-system 耦合。

## References

- [[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]]
- ADR-010 独立仓库但生态复用（Phase 0.5 落地）
- ADR-011 biz schema 三层同步机制（Phase 0.5 落地）
- mj-system `docker/compose.*.yml`
