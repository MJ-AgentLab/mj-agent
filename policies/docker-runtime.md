---
type: policy
artifact: docker-runtime
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-04
track: shared
ai_visibility: source-of-truth
---

# Policy: Docker Runtime

> Phase M0 skeleton — Docker 运行时红线政策.
> 完整 secret 禁入 image + 非 root + network 隔离 + healthcheck 必填 + prod 变更 HITL 在 Phase
> M2 内容填充.

## §1 Image 红线

> TBD: Phase M2:
> - secrets / .env 禁入 image
> - 非 root 用户（USER directive 必填）
> - base_image 固定引用（builder / runtime stage + uv 工具镜像）
> - .dockerignore 配置规则
> 详 `sdd/templates/contracts/docker.contract.yml.template`.

## §2 Network 隔离

> TBD: Phase M2:
> - mj-agent 独立 compose project（ADR-008）
> - `mj-system-backend-network` external 依赖
> - mj-agent-postgres + mj-agent-redis 独立 network
> 详 `sdd/templates/contracts/compose.contract.yml.template` + ADR-026.

## §3 Healthcheck 必填

> TBD: Phase M2 — 每容器（mj-agent / mj-agent-postgres / mj-agent-redis）的 healthcheck 字段
> 必填 + 运行时 expected 状态（per `runtime.expected.yaml`）.

## §4 生产变更 HITL 触发条件

`docker/compose.prod.yml`（Phase M5 平移自 `infra/docker/docker-compose.prod.yml`）任何修改
**必须** HITL：

| 触发 | HITL 级别 |
|---|---|
| compose.prod.yml 字段修改 | ≥ 2 reviewer + 项目负责人 |
| Dockerfile 在 prod 部署影响范围内修改 | ≥ 2 reviewer |
| network 配置（external network / internal network）变更 | ≥ 2 reviewer + 上游业务系统 DRI 联络 |

## §5 与其他 policy 联动

- `policies/data-boundary.md` §1 数据-LLM 三原则 — 通道隔离原则的 Docker 落地表现
- `policies/security.md` — secret 红线 + 2-bundle secrets 信任边界

---

> *Phase M0 skeleton — `state: draft`.*
