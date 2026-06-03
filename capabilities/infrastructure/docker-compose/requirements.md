---
type: capability-requirements
capability: infrastructure.docker-compose
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Requirements: Docker Compose 4-File Profile

> Phase M1 baseline. 3 REQs @risk:high. Per ADR-026 + ADR-008.

## REQ-001 — 4-file profile loading + explicit --env-file

**Priority**：high

**Statement**：Each profile SHALL be invoked via explicit `-f base -f overlay` chain (no `override.yml` auto-load); `--env-file .env` SHALL be supplied at every invocation; DEV layers `override.yml`, TEST layers `test.yml`, PROD layers `prod.yml`.

**Rationale**：

Two compose quirks force explicit `-f` chain even for DEV:

1. **Auto-load disabled by subdir + explicit -f**: `compose.override.yml` auto-load only fires when CLI is invoked in the SAME directory as `compose.yaml`. Compose files live in `docker/`, not repo root → DEV must use explicit `-f compose.override.yml`.

2. **`--env-file .env` required for CLI substitution**: `${VAR}` substitution in compose YAML reads `.env` from compose's `project_directory` (= directory of first `-f` file = `docker/`), NOT developer's cwd. Without `--env-file .env`, the postgres init script reads `MJ_AGENT_MEMORY_PASSWORD:-local-dev-only-replace-in-prod` (sentinel default) and bakes it into the volume → password mismatch + cascade failure.

`env_file: ../.env` inside service definition is a **separate mechanism** — injects vars into running container, NOT into CLI-level `${...}` substitution that happens before container starts. Both layers required.

**Acceptance**：

- 4 compose files exist:
  - `docker/compose.yaml` (base; 247 lines; `name: mj-agent`)
  - `docker/compose.override.yml` (DEV overlay; 40 lines; local `build:` + dev env)
  - `docker/compose.test.yml` (TEST; 54 lines; Harbor image + test resource limits)
  - `docker/compose.prod.yml` (PROD; 70 lines; Harbor image + prod resource limits + json-file logging)
- DEV invocation:
  ```bash
  docker compose --env-file .env \
    -f docker/compose.yaml \
    -f docker/compose.override.yml up -d
  ```
- TEST invocation: same chain with `test.yml` as 2nd `-f`
- PROD invocation: same chain with `prod.yml`
- `mj-system-backend-network` declared `external: true` in base file
- 3 services running per profile: `mj-agent` (port 8001:8000) + `mj-agent-postgres` (5433:5432) + `mj-agent-redis` (6379:6379)

**BDD Examples**：

- **Given** clean docker daemon, mj-system stack up, `.env` populated with `MJ_AGENT_MEMORY_*` + `MJ_AGENT_PG_SUPERUSER_PASSWORD`
- **When** `docker compose --env-file .env -f docker-compose.mj-agent.yml -f docker-compose.override.yml up -d` is invoked
- **Then** all 3 services reach `Up (healthy)` state within 60s; mj-agent connects to `mj-agent-postgres:5432` on `mj-agent-storage` network AND to `mj-postgres:5432` on `mj-system-backend-network`

**Trace**：REQ-001 → `contracts/compose.contract.yml` (file layering) + `contracts/behavior.feature` Scenario 1 + **TBD-M3** `tests/docker/test_compose_dev_profile_up.py`

---

## REQ-002 — Healthcheck + startup order

**Priority**：high

**Statement**：`mj-agent` SHALL `depends_on: service_healthy` for both `mj-agent-postgres` and `mj-agent-redis`; postgres healthcheck SHALL use `psql -U postgres -d $MJ_AGENT_MEMORY_DB -tc 'SELECT 1'` (NOT `pg_isready`).

**Rationale**：

`pg_isready` greenlights the postgres server before the init script's `CREATE DATABASE mj_agent_memory` finishes. mj-agent then starts, tries to connect to the non-existent DB, and fails with cascade. `psql -tc 'SELECT 1' -d mj_agent_memory` queries the target DB itself — only succeeds after init completes.

**Acceptance**：

- `mj-agent` service in base file: `depends_on: { mj-agent-postgres: { condition: service_healthy }, mj-agent-redis: { condition: service_healthy } }`
- `mj-agent-postgres` healthcheck: `CMD ["sh", "-c", "psql -U postgres -d $MJ_AGENT_MEMORY_DB -tc 'SELECT 1'"]`
  - NOT `pg_isready`
  - interval 30s / start_period 30s / retries 3 / timeout 10s
- `mj-agent-redis` healthcheck: branched on `MJ_AGENT_REDIS_PASSWORD` — `redis-cli -a "$MJ_AGENT_REDIS_PASSWORD" --no-auth-warning ping` if set, else `redis-cli ping`
- `mj-agent` healthcheck (Dockerfile): `mj-agent check` (interval 30s / timeout 10s / start_period 20s / retries 3)
- Init script (`postgres-init/01-bootstrap-mj-agent-memory.sh`) runs idempotently:
  - `CREATE ROLE if missing` (or `ALTER ROLE if exists`; per PR #138)
  - `CREATE DATABASE if missing`
  - `GRANT CONNECT + CREATE` to app user

**BDD Examples**：

- **Given** `mj-agent-postgres` is starting + init script has CREATEd role but not yet CREATEd database
- **When** healthcheck probe runs `psql -tc 'SELECT 1' -d mj_agent_memory`
- **Then** probe exits non-zero (DB doesn't exist); mj-agent's `depends_on: service_healthy` does NOT fire until DB exists

**Trace**：REQ-002 → `contracts/compose.contract.yml` (healthcheck section) + `contracts/runtime.expected.yaml` (healthy state) + `behavior.feature` Scenario 2 + **TBD-M3** `tests/docker/test_postgres_healthcheck_timing.py`

---

## REQ-003 — Secrets not exposed to image / env

**Priority**：high

**Statement**：Container images SHALL NOT bake secrets; orchestrator SHALL inject via `--env-file .env` (CLI substitution) + `env_file: ../.env` (container env); `config/secrets.enc` SHALL NOT be decrypted inside image; postgres-init script SHALL safely handle passwords containing shell metacharacters.

**Rationale**：

Secrets-in-image is a permanent leak (image layers immutable). Two-layer injection (CLI + container) keeps secrets out of image. Postgres init must handle passwords with `$ / backticks / quotes / parens / spaces` unmangled — historical bug (#144 / #150) caused agent connection failures when password contained `$`.

**Acceptance**：

- Dockerfile uses `ENV` only for non-secret defaults (`PYTHONUNBUFFERED=1` etc.); no `ARG` for secrets; no `COPY` of `config/secrets*.enc`
- `entrypoint.sh` does NOT decrypt secrets; comment block explicit:
  > does NOT decrypt config/secrets.enc; orchestrator injects via --env-file .env / Compose env / Portainer Stack vars / Docker secrets
- `postgres-init/01-bootstrap-mj-agent-memory.sh` shell-safe pattern:
  - heredoc `<<-'EOSQL'` (single-quoted; disables bash expansion entirely)
  - psql `\getenv` reads env var directly (no shell intermediary)
  - `format('%I %L', name, password)` SQL-escapes identifier + literal
  - `\gexec` executes the formatted DDL
- Compose file `env_file: ../.env` reference is relative to compose file dir (`docker/`), so resolves to repo root `.env`
- DEV `override.yml` adds `MJ_CONFIG_PROFILE: dev` + `MJ_AGENT_LOG_LEVEL: debug` env (no secrets in YAML literal)

**BDD Examples**：

- **Given** `MJ_AGENT_MEMORY_PASSWORD='p@$$`w""ord'` (contains $, backticks, double quotes)
- **When** the init script runs
- **Then** `CREATE ROLE` is dispatched with the literal password unmangled; subsequent `\password mj_agent_app` login from agent succeeds

**Trace**：REQ-003 → `contracts/docker.contract.yml` (Dockerfile lint) + `contracts/compose.contract.yml` (env injection) + `behavior.feature` Scenario 3 + **TBD-M3** `tests/docker/test_secret_injection.py` + `tests/docker/test_password_special_chars.py`

---

> Phase M1 baseline. ADR-026 + ADR-008 + ADR-030 + ADR-031.
> No existing pytest tests for docker layer — all TBD-M3.
