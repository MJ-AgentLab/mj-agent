---
type: policy
artifact: docker-runtime
state: draft
version: 0.3
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-04
track: shared
ai_visibility: source-of-truth
---

# Policy: Docker Runtime

> Docker 运行时红线政策. **§4 是 live 的**——它是 `docker/` 下**审批级别**（谁必须签字）的
> kernel SoT，含生产红线与供应链面。§1-§3（镜像内容 / network 隔离 / healthcheck）的内容填充
> 仍未落地，见各节状态说明。

## §1 Image 红线

镜像**内容**约束（secrets / 用户 / 构建面固定引用）。**审批级别不在本节**——任何 Dockerfile
改动该找谁签字，一律见 §4。

> TBD (Phase-2) — **内容填充未落地**。原标记写作 `TBD: Phase M2`，但 Phase M2 已**于**
> 2026-05-21 收口（`plans/[PLAN]_spec_anchored_refactor.md` `M2: completed # tag
> phase-m2-complete`，该 plan 自身 `state: completed`），phase 名已失效故改标 Phase-2；
> 债务本身仍登记在同 plan 的 `M6-FU-POLICIES-TBD-SWEEP`（🟡 active，明列 docker-runtime 三处）。
> 待填条目：
> - secrets / .env 禁入 image
> - 非 root 用户（USER directive 必填）
> - base_image 固定引用（builder / runtime stage + uv 工具镜像）——**引用如何固定**属本节；
>   **改动如何审批**见 §4 的「外部 registry 镜像引用」行
> - .dockerignore 配置规则
> 详 `sdd/templates/contracts/docker.contract.yml.template`.

## §2 Network 隔离

> TBD (Phase-2) — **内容填充未落地**（phase 名同 §1 改标）。待填条目：
> - mj-agent 独立 compose project（ADR-008）
> - `mj-system-backend-network` external 依赖
> - mj-agent-postgres + mj-agent-redis 独立 network
> 详 `sdd/templates/contracts/compose.contract.yml.template` + ADR-026.

## §3 Healthcheck 必填

> TBD (Phase-2) — **内容填充未落地**（phase 名同 §1 改标）——每容器（mj-agent /
> mj-agent-postgres / mj-agent-redis）的 healthcheck 字段必填 + 运行时 expected 状态
> （per `runtime.expected.yaml`）。**审批级别**：healthcheck 面的必停由 `docker/AGENTS.md`
> §Hard stops / `docker/CLAUDE.md` §专属必停 承载，§4 尚无对应行——见该节说明.

## §4 变更 HITL 触发条件（生产红线 + 供应链面）

本节是 `docker/` 下**审批级别的 kernel SoT**。`docker/AGENTS.md` §Hard stops 与
`docker/CLAUDE.md` §专属必停 是它的两个 entry adapter——它们**点名对象**、回指本节取级别。
下表列出 `docker/` 各触发面及其 HITL 级别（`docker/compose.prod.yml` 为 Phase M5 自
`infra/docker/docker-compose.prod.yml` 平移）：

| 触发 | HITL 级别 |
|---|---|
| compose.prod.yml 字段修改 | ≥ 2 reviewer + 项目负责人 |
| `docker/Dockerfile` **外部 registry 镜像引用**变更：`FROM <image>` + `COPY --from=<registry image>`（内部 `COPY --from=<stage>` 如 `--from=builder` **不**在内） | `OWNER_APPROVAL_REQUIRED`（改前 Owner 拍板）+ ≥ 2 reviewer |
| `docker/Dockerfile` 其余修改 | ≥ 2 reviewer |
| network 配置（external network / internal network）变更 | ≥ 2 reviewer + 上游业务系统 DRI 联络 |

> **两条 Dockerfile 行按「被点名的对象」划分，不按「影响范围」判断**（per #408 / #413）：Owner
> 拍板只挂在外部 registry 镜像引用上；其余 Dockerfile 行——含 `COPY --from=builder` 一类内部
> stage 拷贝——留在 ≥ 2 reviewer 档，**级别未上调，不是新增必停**。
> 原措辞「Dockerfile 在 prod 部署影响范围内修改」已废除：该谓词需逐次判断且没有可检查的边界，
> 实际会把整份 Dockerfile 悄悄纳入必停面，与 #408 明确排除内部 stage 拷贝的裁定冲突。
> **口径变化如实记录**：级别不变，但覆盖面由条件谓词「prod 影响范围内」**收敛为无条件全文件**
> ——原先需逐次判断的行，现在一律 ≥ 2 reviewer。
> **本表尚未覆盖 healthcheck 面**（§3 待填）：该面的必停暂由两个 entry adapter 自带级别承载，
> 不受上面「其余修改」行辖制。
> canonical enum 锚点 = `secrets-grants-or-prod-config`（`policies/ai-agent.md` §4）。

## §5 与其他 policy 联动

- `policies/data-boundary.md` §1 数据-LLM 三原则 — 通道隔离原则的 Docker 落地表现
- `policies/security.md` — secret 红线 + 2-bundle secrets 信任边界

---

> *`state: draft` — §4 已是 live SoT；§1-§3 待内容填充（各节标注状态）.*
