---
type: capability-runbook
capability: infrastructure.docker-compose
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
last_verified: 2026-05-20
---

# Runbook: Docker Compose 4-File Profile

> Phase M1 baseline.

## §1 Startup

### Pre-requisites

- mj-system stack up (provides `mj-system-backend-network`)
- `.env` populated at repo root via `setup-env.ps1` (decrypts `config/secrets.enc`)
- `setup-mcp-secrets.ps1` ran once (per ADR-030; injects MCP secrets to OS env)
- docker engine ≥ 20.10 (compose v2)

### Per-profile commands

```bash
# DEV (local; builds image)
docker compose --env-file .env \
  -f infra/docker/docker-compose.mj-agent.yml \
  -f infra/docker/docker-compose.override.yml up -d

# TEST (192.168.0.179; pulls Harbor image)
docker compose --env-file .env \
  -f infra/docker/docker-compose.mj-agent.yml \
  -f infra/docker/docker-compose.test.yml up -d

# PROD (192.168.0.106; pulls Harbor image)
docker compose --env-file .env \
  -f infra/docker/docker-compose.mj-agent.yml \
  -f infra/docker/docker-compose.prod.yml up -d
```

**REQ-001 enforcement**：every invocation MUST include both `--env-file .env` AND the explicit `-f base -f overlay` chain. Forgetting either causes silent regression.

Use the `/mj-agent-infra-docker-compose` skill for guided lifecycle.

## §2 Health Check

```bash
# Service status
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.<overlay>.yml ps

# Expected after ≤ 90s (REQ-002):
# - mj-agent        Up (healthy)
# - mj-agent-postgres   Up (healthy)
# - mj-agent-redis  Up (healthy)

# Logs
docker compose <chain> logs -f mj-agent
docker compose <chain> logs -f mj-agent-postgres

# Healthcheck output
docker inspect --format='{{.State.Health.Status}}' mj-agent
```

## §3 Troubleshooting

### Symptom: `password authentication failed for user "mj_agent_app"`

**Diagnostic**：likely `--env-file .env` was forgotten in compose invocation → CLI substitution fell back to sentinel default `local-dev-only-replace-in-prod` → postgres init baked sentinel into volume → real `.env` password mismatches.

**Resolution**：

```bash
# Tear down + delete volume + restart with --env-file
docker compose <chain> down -v
docker compose --env-file .env <chain> up -d
```

Use `/mj-agent-infra-env-teardown` skill for 3-level safety teardown (Level 2 = down -v).

### Symptom: `mj-agent` service stuck in "Created" or restarting

**Diagnostic**：`mj-agent` is waiting on `depends_on: service_healthy` for postgres or redis. Check healthcheck status:

```bash
docker inspect --format='{{json .State.Health}}' mj-agent-postgres
docker inspect --format='{{json .State.Health}}' mj-agent-redis
```

**Resolution**：

- If postgres healthcheck failing → check init script logs: `docker logs mj-agent-postgres | grep -i error`
- If init script complains about password mangling → see Symptom "Postgres password with `$` / backticks fails"
- If redis healthcheck failing → check auth config: `MJ_AGENT_REDIS_PASSWORD` set vs unset

### Symptom: `Error: network mj-system-backend-network declared as external, but could not be found`

**Diagnostic**：mj-system stack is not up. mj-agent depends on the external network created by mj-system.

**Resolution**：

```bash
# Verify network presence
docker network ls | grep mj-system-backend-network

# If absent: bring up mj-system stack first (per upstream mj-system runbook)
# OR: temporarily declare a placeholder network (DEV only; do NOT do in TEST/PROD)
```

### Symptom: Postgres password with `$`, backticks, or quotes fails init

**Diagnostic**：REQ-003 contract violation; should NOT happen with current shell-safe init pattern. If it does → regression.

**Resolution**：

- Verify init script is current: `cat infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh | grep -E "<<-'EOSQL'|\\\\getenv|\\\\gexec"`
- Should see all 3 patterns. If any missing → file `[BUG]` against this capability with init script SHA
- Workaround: temporarily change password to ASCII-only; restart stack; investigate

### Symptom: Production deployment timeout / extreme slow start

**Diagnostic**：PROD has tighter resource limits (4C/12G). If initial load > limit → start_period stretches.

**Resolution**：

- Check resource usage: `docker stats mj-agent --no-stream`
- If CPU sustained near limit → consider raising PROD resource limit (HITL — prod compose modification per `policies/docker-runtime.md`)

### Symptom: `image: 8.135.38.175/mj-agent/mj-agent:0.1` pull failure

**Diagnostic**：TEST/PROD pull Harbor image. CI publishes after PR merge; if registry unreachable from host:

**Resolution**：

- Verify Harbor reachability: `curl -I https://8.135.38.175`
- If unreachable: VPN required for Harbor access from PROD host
- Build locally (DEV pattern) as emergency fallback (not recommended for PROD — bypass CI image signing)

## §4 Related Artifacts

- `contracts/docker.contract.yml` — Dockerfile lint + entrypoint contract
- `contracts/compose.contract.yml` — 4-file layering + healthcheck + env injection
- `contracts/runtime.expected.yaml` — expected post-up state
- `contracts/behavior.feature` — 3 Gherkin scenarios
- `/mj-agent-infra-docker-compose` skill — lifecycle (up / config / down)
- `/mj-agent-infra-storage-stack` skill — postgres + redis specifics
- `/mj-agent-infra-env-setup` skill — first-time setup (decrypt + compose up)
- `/mj-agent-infra-env-teardown` skill — 3-level safety teardown
- ADR-026 / ADR-008 / ADR-030 — design records
- `docs/runbook/dev_studio_walkthrough.md` — broader Studio context (Phase M5 dissolves)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` when:

- REQ-001 silent regression (operator forgets `--env-file .env` in CI → prod pwd mismatch)
- REQ-002 pg_isready regression sneaks in via Dependabot update → cascade failures
- REQ-003 secret accidentally baked into image (visible in `docker history mj-agent`)
- Network: `mj-system-backend-network` accidentally removed → all mj-agent biz queries fail

Path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per `policies/archive.md` retention class permanent.

---

> Phase M1 baseline. ADR-026 + ADR-008 + ADR-030 governance.
