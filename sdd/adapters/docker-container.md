---
type: sdd-adapter
artifact: docker-container
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: code
ai_visibility: source-of-truth
---

# Adapter: Docker Container

> Phase M0 skeleton — Docker Container adapter 治理 Dockerfile + 4 compose file + runtime.
> 完整 lint / runtime expected 规则 + §BDD Rules + §TDD Rules 在 Phase M2 内容填充.

## Scope

- `docker/Dockerfile`（Phase M5 平移自 `infra/docker/Dockerfile`）
- `docker/compose.yaml` + `compose.override.yml` + `compose.test.yml` + `compose.prod.yml`
  （Phase M5 平移自 `infra/docker/docker-compose*.yml`）
- 容器运行时状态（healthcheck / network / port）

## Contract Output

3 个 contract file per capability infrastructure/docker-compose:
- `docker.contract.yml`（Dockerfile lint）
- `compose.contract.yml`（compose 字段校验）
- `runtime.expected.yaml`（运行时状态 expected）

## §Standards

> TBD: Phase M2 — Dockerfile lint（非 root user / .dockerignore / ARG 无 secret /
> base_image_allowlist）；compose 字段（--env-file 显式 / networks 显式 / healthcheck 必填）；
> runtime expected（容器列表 / 端口 / 健康检查）.

## §BDD Rules

> TBD: Phase M2 — 运行时健康 + 启动 .feature 化；3 profile 启动 scenario 强制；
> `docker-bdd-scenario-check` gate 联动.

## §TDD Rules

> TBD: Phase M2 — contract 一致性检查；compose 变更必先 dry-run；
> `docker-tdd-contract-test` gate（contract-test-first 严格执行）.

## CI Gate

- `scripts/sdd/check_docker_contracts.py`（Phase M2 warning / M3 blocking）
- `scripts/sdd/check_runtime_expected.py`（Phase M3）
- `docker-bdd-scenario-check`（Phase M3 warning / M4 blocking）
- `docker-tdd-contract-test`（Phase M3 blocking）

## HITL Trigger

`docker/compose.prod.yml` 任何修改 → 生产 Docker 红线 HITL（per `policies/docker-runtime.md`）.

---

> *Phase M0 skeleton — `state: draft`.*
