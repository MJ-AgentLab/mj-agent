# infra/docker/CLAUDE.md

> Docker compose conventions for `infra/docker/`. Loaded additively after root CLAUDE.md.
> Phase M5 will move this directory to `docker/` (per blueprint §10) — this file becomes
> `docker/CLAUDE.md` at that time.
> See root `CLAUDE.md` + `policies/docker-runtime.md` for prod red lines.

## Compose Quirk（必须显式 `--env-file .env`）

`docker compose` CLI looks for `.env` in the **project directory** = directory of the first
`-f` file = `infra/docker/` (this subdir). It does NOT walk up to find the developer's `.env`
in repo root. Therefore:

```bash
# WRONG — VAR substitution falls through to `:-default` sentinels;
# postgres init script bakes a placeholder password into the volume.
docker compose -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml up -d

# CORRECT — pass --env-file .env explicitly
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml up -d
```

`override.yml` auto-load is ALSO disabled because base file lives in subdir + base loaded via
explicit `-f`. All 3 profiles MUST use explicit `-f base -f overlay` chain (per ADR-026).

## 3 Profile 启动命令

| Profile | Host | Command |
|---|---|---|
| DEV | 本地 | `docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml up -d` |
| TEST | 192.168.0.179 | `docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.test.yml up -d` |
| PROD | 192.168.0.106 | `docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.prod.yml up -d` |

Pre-req：mj-system 栈已 up（`mj-system-backend-network` external network + `mj-postgres` 已存
在）.

## Teardown 3-level Safety

用 `/mj-agent-infra-env-teardown` skill；3-level safety：

- Level 1: `down`（保 volume + image；最安全）
- Level 2: `down -v`（删 volume；mj-agent-postgres / mj-agent-redis 数据全失）
- Level 3: `down -v --rmi local`（同时清 local image）

H3 hard-confirm 在 Level 2/3 — skill 必须先询问 user 确认 destination + 影响范围.

## 4 项专属必停（任一触发 HITL）

| Hard Stop | 路径 | 触发原因 |
|---|---|---|
| Prod compose | `infra/docker/docker-compose.prod.yml` 任何字段修改 | 生产 runtime 红线（详 `policies/docker-runtime.md` §4；canonical enum `secrets-grants-or-prod-config` per `policies/ai-agent.md §4`） |
| External network | `mj-system-backend-network` external 配置变更 | 跨仓边界（per ADR-008） |
| Healthcheck | mj-agent / mj-agent-postgres / mj-agent-redis healthcheck 字段变更 | 生产可观测性 |
| Image base | Dockerfile FROM 行 / `base_image_allowlist` 变更 | supply-chain |

## 本子目录最小可执行命令集

```bash
# 构建（dev）
docker build -f infra/docker/Dockerfile -t mj-agent:0.1 .

# 配置检查（dry-run；不启动容器）
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml config

# 健康自检
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml ps
```

## CI Gates 触及（本 subdir 路径）

- **V5 docker contracts** — BLOCKING (Stage C C-a; commit `02b1cc8`); validates
  `capabilities/infrastructure/docker-compose/contracts/{docker,compose}.contract.yml`
  against `infra/docker/Dockerfile` + 4 compose YAML; sub-flags `--bdd --tdd --compose-config`
  exercised
- **V6 runtime expected** — warning (SKELETON BY DESIGN; Phase M4 full probe impl)
- Truth source: `.github/workflows/ci.yml` (per-job `continue-on-error` 状态)

## Anti-patterns

- ❌ 省略 `--env-file .env`（导致 postgres init 烘焙 placeholder 密码进 volume）
- ❌ 用 `docker compose up` 不带 `-f`（不会自动 load override；与 ADR-026 4-file 分层冲突）
- ❌ 修改 `docker-compose.prod.yml` 不 HITL（违反 prod 红线）
- ❌ Dockerfile 用 root user（违反 docker.contract.yml `user_required: non-root`）

## See Also

- 根级：`CLAUDE.md`（repo-wide map）
- `policies/docker-runtime.md`（Docker 运行时红线）
- `sdd/adapters/docker-container.md`（Docker adapter contract）
- ADR-026（Multi-Environment Compose Profile）
- ADR-008（Co-Deployment with Upstream Business Warehouse）
- HITL canonical: `policies/ai-agent.md §4` (Canonical 10-Enum; `secrets-grants-or-prod-config`
  enum 覆盖 prod compose) + `§7` (Pre-flight Verification Discipline)
- A2 hook: `.claude/hooks/stop-claude-md-improver/`

---

> *Phase M0 skeleton — Phase M5 末本 file 重命名为 `docker/CLAUDE.md` 后内容刷新.*
