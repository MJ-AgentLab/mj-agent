---
type: adr
domain: OPS
summary: mj-agent 是独立的 compose project（自带 postgres + redis 存储栈），通过 `mj-system-backend-network` (external=true) Docker network 仅以 consumer 身份访问上游业务系统 biz pg；环境矩阵与上游业务系统时间表对齐
owner: 项目负责人
created: 2026-04-24
updated: 2026-05-11
state: active
decision: accepted
track: code
---

# ADR-008: Co-Deployment with Upstream Business Warehouse

> **术语**："上游业务系统 / Upstream Business Warehouse" 指 mj-agent 通过 `analyst` 只读 PostgreSQL 角色消费的外部业务数据仓库；定义见 [[../glossary/upstream_business_warehouse|glossary]]。代码层 literal（Docker network 名 `mj-system-backend-network`、容器名 `mj-postgres` 等）保留原始命名作为真实部署对象的精确引用。
>
> **Note (2026-05-07 update)**: 本 ADR 最初命名为 "Co-Deployment with Upstream Warehouse"，描述
> mj-agent 作为上游业务系统子服务部署的形态。Storage-stack PR 系列
> (#42 → #44 → #45 → #46) 在 Phase 1 阶段实质改变了决策：mj-agent 演进为
> **完全独立的 compose project**，仅通过 external network 作为 consumer 访问
> 上游业务系统的 biz pg。本 ADR 的 Decision / Consequences 块**已重写**以反映最终
> 形态；原"兄弟服务"语义仅作为历史背景在 §Architectural evolution 中保留。

## Context

mj-agent 只读访问上游业务系统的 biz 域数据库（见 [[decisions/ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]]）。访问路径上存在多个运维问题需要决定：

- **网络**：mj-agent 需要访问 PostgreSQL，是部署在上游业务系统同网络内还是跨 VPC
- **环境**：上游业务系统有三套环境（DEV/TEST/PROD），mj-agent 是复用还是独立搭建
- **密钥**：`POSTGRES_ANALYST_USER/PASSWORD`、`ARK_API_KEY` 等配置的分发策略
- **生命周期**：mj-agent 的 deploy / restart / rollback 是否受上游业务系统节奏牵制

两个项目当前由同一团队维护，但仓库、代码所有权、版本号、CI 流程独立（[[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]）。

### Architectural evolution

| 阶段 | 形态 | 决策驱动 |
|---|---|---|
| 初稿 (2026-04-24) | "兄弟服务"——mj-agent 加入上游业务系统的 `docker-compose.*.yml` 作为 service；同一 compose project；共用 .env | 复用上游业务系统的运维栈 + 环境矩阵；最小投入 |
| Phase 1 sub 1.H (PR #40) | mj-agent 仍在上游业务系统 compose project 下，但有自己的 Dockerfile + entrypoint + drop-in compose snippet | 引入 Chainlit + memory pg 后单 service 不够 |
| Storage-stack PR (#42) | mj-agent 自带 mj-agent-postgres（langgraph 检查点）+ mj-agent-redis（预留），与上游业务系统的 `mj-postgres` 容器解耦 | 防 read-only analyst 与 RW checkpointer 共连接池；上游 DBA 不需审计 mj-agent 写流量 |
| Standalone PR (#44) | mj-agent 改为**独立 compose project** (`name: mj-agent`)，从 mj-agent 仓根目录单 -f 启动；上游业务系统栈作为前置依赖（network 必须存在） | Docker Desktop / Portainer 视图独立；防"兄弟服务"框架引发的项目名混淆；上游业务系统完全不受 mj-agent compose 操作影响 |
| Hardened PR (#45) | mj-agent-postgres healthcheck 改 `psql -tc 'SELECT 1'`（防 DB-not-exist 假阳性）；mj-agent-redis healthcheck 按 requirepass 分支 | 防 init script 失败导致 mj-agent 看似 healthy 实际崩 |
| CI gates PR (#46) | ruff / mypy / pytest 进 CI mandatory step | Phase 1 末治理基线 |

## Decision

mj-agent 与上游业务系统是**独立项目，独立 compose project，独立 lifecycle**：

- **Compose project 边界**：mj-agent 的 `docker-compose.mj-agent.yml` 顶层声明 `name: mj-agent`，从 mj-agent 仓根目录单 `-f` 启动；上游业务系统用自己的 `docker-compose.yml` 启动；两边各自 `up` / `down`，互不耦合
- **网络拓扑**：mj-agent attach `mj-system-backend-network` 作为 `external: true`（消费方；保留原 Docker network literal 名以匹配上游栈），仅用于访问 `mj-postgres:5432`（保留原容器 literal 名）；mj-agent 拥有自家 `mj-agent-storage` 内部网络承载 mj-agent-postgres + mj-agent-redis
- **存储栈独立**：
    - 业务查询：→ 上游业务系统的 `mj-postgres` 容器（analyst RO role；数据 + 权限定义在上游侧）
    - Agent 状态（langgraph 检查点）：→ mj-agent 的 mj-agent-postgres（RW；mj-agent 完全自管）
    - 未来 cache / 速率限制：→ mj-agent 的 mj-agent-redis（容器就绪，Python 客户端待 Phase 2 引入）
- **环境矩阵**：DEV / TEST / PROD 三套**时间表与上游业务系统对齐**（避免分析师跨环境切换混乱），但部署单元各自独立
- **配置**：mj-agent 的 `.env` 字段命名与上游业务系统对齐（`POSTGRES_{DEV,TEST,PROD}_HOST/PORT`、`MJ_CONFIG_PROFILE`），目的是**运维便利与环境矩阵一致性**——**不**意味"共用 .env 文件"。每个项目有独立的 secrets 解密管道（独立 `secrets.enc` + 独立团队口令）
- **依赖前置**：mj-agent `up` 前必须上游业务系统栈已起（具体而言：`mj-system-backend-network` 网络存在 + `mj-postgres` 容器 healthy）；缺则 mj-agent 报 `network not found` fail-fast
- **发布**：仓库独立，各自发版（[[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]）；部署可独立操作或通过协同脚本

## Consequences

**正面**

- mj-agent 故障 / 误部署不影响上游业务系统；上游升级不强制 mj-agent 协同 review
- Docker Desktop / Portainer / `docker compose ls` 视图清晰：mj-agent 与上游业务系统栈是两个并列 group，分析师 / 试用者一眼看到 mj-agent 状态
- mj-agent 的 RW checkpointer 与上游业务系统的 RO analyst 完全分离（不同 pg 实例 + 不同 connection pool），降低权限边界事故面
- 上游业务系统 DBA 不需为 mj-agent 写流量审计；备份策略分离
- 环境变量命名对齐 + 解密管道独立 → 运维体感统一，安全边界清晰

**负面**

- mj-agent 起容器前依赖上游业务系统栈先起；启动顺序需运维流程明示（runbook + Day-One GUIDE 都已写）
- 分析师两个 compose project 都要会用（`docker compose -f` 命令路径不同）；onboarding 需两套
- mj-agent 与上游业务系统在 biz schema 漂移时仍需对账，但同步机制是**未来工作**（Phase 2，见 §References）；Phase 1 阶段通过 contract 测试 + 静态 catalog YAML + manual review 维持

**中性**

- mj-agent 的 RW 状态完全自管 → 备份 / 归档 / 数据合规由 mj-agent 团队自行负责
- 独立 lifecycle 的代价：mj-agent 节奏不再"搭便车"——但 Phase 1 阶段团队规模可承担

## Alternatives considered

**保留"兄弟服务"形态（Phase 1 早期）**：拒绝（PR #44）——Docker Desktop 视图把 mj-agent 容器折叠在上游业务系统 group 下、`name: mj-agent` 加在被串联 compose 文件中会污染上游业务系统项目名（容器命名前缀冲突），运维风险高于复用收益。

**独立 Docker 环境（完全隔离 + 自家 biz pg 复制）**：拒绝——biz pg 是上游业务系统拥有的数据资产，mj-agent 复制 = 治理混乱 + 数据延迟；mj-agent 仅做 consumer 是正解。

**部署在 Kubernetes 集群（而非 docker-compose）**：保留 Phase 4 以后评估的可能；Phase 0-1 尊重上游业务系统现有的 compose 栈。

**同一 Docker service 组合进上游单容器**：拒绝——违反进程边界，mj-agent 的 Python 运行时（GIL、event loop、requirements）不应与上游业务系统应用耦合；且 LLM 服务的资源 / 故障特征与上游主程序差异大。

## References

- [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]（4 层数据访问边界 L1-L4）
- [[decisions/ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]]（仅 biz_dws + 2 张 biz_dwd dim 表）
- [[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]（独立仓库 + 生态复用）
- mj-agent `infra/docker/docker-compose.mj-agent.yml`（独立 compose project 定义）
- mj-agent `infra/docker/README.md` §Standalone deploy（启动 / 拆栈步骤）
- mj-agent `docs/runbook/dev_deployment.md` §2.3（DEV 部署 runbook）
- **Future work** — biz schema 同步机制规划在 Phase 2（见 [[../../plans/mj-agent-roadmap-v1.6|roadmap v1.6]] §4.4 "schema 自动同步"）；Phase 1 阶段通过 `tests/contract/*` + `qcm_catalog.yaml` 静态镜像 + manual review 维持
- 上游业务系统 `docker-compose.yml`（被 attach 的 `mj-system-backend-network` Docker network 创建方）
- PR #42 (storage-stack) / #44 (standalone project) / #45 (hardened healthcheck) / #46 (CI gates) — Architectural evolution 实施链
