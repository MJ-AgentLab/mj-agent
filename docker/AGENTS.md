# docker/AGENTS.md

> Tool-neutral local constraints for `docker/` — binds every AI agent working here (roster in
> root `AGENTS.md`). Codex discovers this file hierarchically (root → cwd); Claude Code
> imports it via the sibling `docker/CLAUDE.md`. Rules live once in the kernel
> (`policies/docker-runtime.md` + ADR-008 / ADR-026 + docker contracts) — this file only points.

## Hard stops (OWNER_APPROVAL_REQUIRED before any edit)

| Surface | Why |
|---|---|
| `docker/compose.prod.yml` (any field) | prod red line — canonical enum `secrets-grants-or-prod-config` (`policies/ai-agent.md` §4) |
| `mj-system-backend-network` external wiring | cross-repo boundary (ADR-008) |
| healthcheck fields (mj-agent / mj-agent-postgres / mj-agent-redis) | production observability |
| `docker/Dockerfile` external image refs — `FROM <image>` + `COPY --from=<registry image>` (internal `COPY --from=<stage>`, e.g. `--from=builder`, is NOT in scope); contract mirror = `docker.contract.yml` `base_image` | supply chain — canonical enum `secrets-grants-or-prod-config` (`policies/ai-agent.md` §4); approval level `policies/docker-runtime.md` §4 |

> **This table names surfaces; the kernel sets the levels.** Approval levels for the
> compose.prod.yml, image-ref and external-network rows live in `policies/docker-runtime.md` §4;
> the healthcheck row still has no §4 entry, so it keeps this section header's
> `OWNER_APPROVAL_REQUIRED` until the kernel covers it. (§3 was filled in v0.4, but the row was
> **deliberately** not added to §4 — which canonical enum anchors that surface is an Owner posture
> call; the criterion and trigger are recorded at the end of that file's §3.) Note the §4 split:
> only the external registry image refs above carry `OWNER_APPROVAL_REQUIRED`
> **among `docker/Dockerfile` lines** —
> **every other `docker/Dockerfile` line is ≥ 2 reviewer and is not a hard stop** (per #408 AC-4 /
> #413). That statement is about Dockerfile lines only; it does not touch the other three rows.
> Codex: this file loads only once your cwd is under `docker/`
> — the same stop is restated in the repo-root `AGENTS.md` §Self-enforced boundaries item 3, which
> always loads.

## Env & secrets carrier rule

- Agents must NOT read `.env` / `config/secrets*.enc` themselves (root `AGENTS.md`
  boundary 2). Passing `--env-file .env` to `docker compose` is the sanctioned carrier: the
  docker process parses the file; the agent never sees values.
- Compose quirk: the project directory is `docker/`, so repo-root `.env` is only picked up
  via an explicit `--env-file .env`; overlays never auto-load — always chain
  `-f docker/compose.yaml -f docker/compose.<overlay>.yml` (ADR-026).

## Destructive teardown

`down -v` (and `--rmi`) destroys mj-agent-postgres / mj-agent-redis volumes — Owner
confirmation is required before a Level 2/3 teardown, whichever tool executes it.

## Verification (either tool, from repo root)

```bash
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml config
uv run python scripts/sdd/check_docker_contracts.py --all --bdd --tdd --compose-config
```

## See also

- Root `AGENTS.md` · `docker/CLAUDE.md` (same layer) · `policies/docker-runtime.md`
- `sdd/adapters/docker-container.md` · ADR-026 / ADR-008 (in `decisions/`)
