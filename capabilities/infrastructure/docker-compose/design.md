---
type: capability-design
capability: infrastructure.docker-compose
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Design: Docker Compose 4-File Profile

> Phase M1 baseline (≤ 200 lines per R-G3). Per ADR-026 + ADR-008 + ADR-030.

## §1 Context

mj-agent is deployed independently of mj-system (per ADR-008): own compose project, own postgres (memory checkpointer), own redis (reserved). Three environments share one base compose file, differ via overlay:

- **DEV** (local): `override.yml` — local build via `Dockerfile`, dev env, debug logs
- **TEST** (192.168.0.179): `test.yml` — Harbor image, test env, 8C/12G resource limits
- **PROD** (192.168.0.106): `prod.yml` — Harbor image, prod env, 4C/12G limits, json-file logging

**Threats**：

1. Mistake one overlay for another (DEV envs leak into PROD)
2. `override.yml` auto-load misfires in DEV → wrong env / wrong build path
3. `--env-file .env` forgotten → postgres init bakes sentinel password
4. `pg_isready` healthcheck greenlights too early → cascade failure
5. Secrets in image layers → permanent leak
6. Postgres password with `$ / backticks / quotes` mangled by shell → role creation fails silently
7. `mj-system-backend-network` external dep — mj-agent up'd before mj-system stack → mj-agent fails to start

## §2 Decision

**Explicit 4-file `-f` chain + `--env-file` flag + psql-based healthcheck + shell-safe init**.

| Component | File | Purpose |
|---|---|---|
| Base | `infra/docker/docker-compose.mj-agent.yml` | `name: mj-agent`; 3 services; networks (internal + external); volumes |
| DEV overlay | `infra/docker/docker-compose.override.yml` | `build: ../../`; dev env vars; debug logs |
| TEST overlay | `infra/docker/docker-compose.test.yml` | Harbor image; test env; 8C/12G |
| PROD overlay | `infra/docker/docker-compose.prod.yml` | Harbor image; prod env; 4C/12G; json-file logging |
| Image | `infra/docker/Dockerfile` | Multi-stage; non-root appuser; tini; `mj-agent check` healthcheck |
| Entrypoint | `infra/docker/entrypoint.sh` | Subcommand router (serve/check/shell/passthrough); no secret decryption |
| PG init | `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` | Idempotent; heredoc `<<-'EOSQL'` + `\getenv` + `format()` + `\gexec` |

**Why explicit `-f` chain even for DEV**：

Compose's auto-load of `override.yml` fires only when CLI is invoked in the same dir as `docker-compose.yml`. Our compose files are in `infra/docker/`, not repo root. CLI from repo root with `-f infra/docker/docker-compose.mj-agent.yml` does NOT auto-load `override.yml`. Therefore even DEV requires explicit `-f override.yml`. Documentation in this capability + CLAUDE.md + `/mj-agent-infra-docker-compose` skill explicitly call this out.

**Why `--env-file .env` always required**：

Compose YAML's `${VAR}` substitution happens at CLI level, before any container starts. Compose looks for `.env` in `project_directory` (= directory of the first `-f` file = `infra/docker/`), NOT in developer's cwd. Without `--env-file .env` (which overrides project_directory lookup), `${MJ_AGENT_MEMORY_PASSWORD:-local-dev-only-replace-in-prod}` substitutes to the sentinel — postgres init bakes that as password → mj-agent connection fails with `password authentication failed`.

`env_file: ../../.env` inside the service definition is SEPARATE — that injects env vars into the running container, not into CLI substitution. Both layers needed.

**Why psql instead of pg_isready**：

`pg_isready` checks "is server accepting connections". The init script runs `CREATE DATABASE mj_agent_memory` AFTER the server starts accepting connections. So `pg_isready` greenlights before the DB exists → mj-agent service starts → mj-agent tries to connect to `mj_agent_memory` → fails. `psql -tc 'SELECT 1' -d $MJ_AGENT_MEMORY_DB` queries the target database directly — only succeeds after init creates it.

## §3 Architecture

```
Developer / CI                                ──── invokes
    │
    │  docker compose --env-file .env \
    │    -f infra/docker/docker-compose.mj-agent.yml \
    │    -f infra/docker/docker-compose.<overlay>.yml \
    │    up -d
    │
    ▼
[Compose CLI substitution layer]              ──── reads .env from --env-file flag
    │  ${MJ_AGENT_MEMORY_PASSWORD} resolved
    │  ${MJ_AGENT_REDIS_PASSWORD} resolved
    │  ${MJ_AGENT_PG_SUPERUSER_PASSWORD} resolved
    ▼
[Compose service definitions]                 ──── overlay merged with base
    │
    ├─► mj-agent (port 8001:8000)
    │    ├─► image: mj-agent:0.1 (DEV build) | Harbor image (TEST/PROD)
    │    ├─► env_file: ../../.env             ──── container env layer
    │    ├─► depends_on: service_healthy {mj-agent-postgres, mj-agent-redis}
    │    ├─► networks: [mj-system-network external, mj-agent-storage]
    │    └─► healthcheck: mj-agent check
    │
    ├─► mj-agent-postgres (port 5433:5432)
    │    ├─► image: postgres:18-alpine (digest-pinned)
    │    ├─► volumes: mj-agent-postgres-data + ./postgres-init
    │    ├─► healthcheck: psql -U postgres -d $MJ_AGENT_MEMORY_DB -tc 'SELECT 1'
    │    │                  (NOT pg_isready — REQ-002)
    │    └─► network: mj-agent-storage (internal only)
    │
    └─► mj-agent-redis (port 6379:6379)
         ├─► image: redis:8-alpine (digest-pinned)
         ├─► startup: branched on MJ_AGENT_REDIS_PASSWORD
         ├─► healthcheck: redis-cli ping (auth branch)
         └─► network: mj-agent-storage

Network topology:
    mj-system-backend-network (external; owned by mj-system) ──── biz pg access
        │
        ├─► mj-postgres:5432 (analyst RO role; per upstream R__analyst_permissions.sql)
        └─► mj-agent (consumer)
    
    mj-agent-storage (internal bridge; isolation: internal label)
        ├─► mj-agent-postgres
        ├─► mj-agent-redis
        └─► mj-agent (memory checkpointer + future redis use)
```

**Cross-capability dependencies (2 refs)**：

- **llm-provider** (inbound)：LLM env vars (`LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_API_KEY` / `ARK_API_KEY`) flow through `env_file: ../../.env` into mj-agent container
- **mcp-server-governance** (outbound)：`.mcp.json` WAN pg URLs (`MJ_AGENT_PG_*_WAN_URL`) reference the same host/port matrix as compose pg services

## §4 Tradeoffs

| Choice | Pros | Cons | Rationale |
|---|---|---|---|
| **A. 4-file overlay (chosen)** | Single base + explicit env divergence; reusable | 4 files to maintain; -f chain is verbose | Explicit env semantics; ADR-026 |
| B. Single compose with profiles | Fewer files | All-or-nothing profile activation; can't mix | Rejected — profiles less expressive than overlays |
| C. Template + render per env | Most flexible | Adds preprocessor; build step | Rejected — overkill |
| **D. Explicit -f chain even for DEV (chosen)** | Predictable; no auto-load surprises | Verbose CLI | Required given compose subdir + -f explicit interaction |
| E. Move compose files to repo root | Auto-load works | Pollutes root; conflicts with mj-system's compose files in shared workspace | Rejected — mj-agent must be self-contained per ADR-008 |
| **F. psql healthcheck (chosen)** | Catches init script completion | Slightly heavier than pg_isready | Necessary — pg_isready cascade failure was production incident |
| G. pg_isready + retry loop in app | Lighter health check | Adds startup latency + complexity | Rejected |
| **H. heredoc + format() + \\gexec (chosen)** | Shell-safe for any password chars | More complex SQL | Required per PR #144 incident |
| I. Bash interpolation | Simple | Mangles passwords with $/backticks/quotes | Rejected — incident history |

## §5 Open Questions

1. **Dockerfile pin: digest of python:3.14-slim with comment `# tag: 3.13-slim`** — actual Python is 3.13.13 inside that slim image (upstream slim digest). Should REQ-001 normatively pin digest OR tag? Currently digest is authoritative; comment is documentation only. Dependabot config track: `digest-with-tag-comment`.

2. **`--env-file .env` enforcement** — currently informational. Should there be a guard script (e.g. `scripts/check_compose_invocation.ps1`) that refuses to start if env vars look sentinel-like? Phase M4 evidence/runtime/ might surface this.

3. **Resource limits divergence**: TEST 8C/12G vs PROD 4C/12G — should REQ codify these or leave as profile tuning? Currently informational. PROD smaller because dedicated host has multiple tenants.

4. **Redis unused (no Python client wired)** — should REQ carry a placeholder that future redis-integration must not break the "unused but healthy" state? Likely out of scope for M1; track as Phase 2+ capability `data-agent.session-cache`.

> Phase M2 will fill in adapter §BDD Rules + §TDD Rules per `sdd/adapters/docker-container.md`.
