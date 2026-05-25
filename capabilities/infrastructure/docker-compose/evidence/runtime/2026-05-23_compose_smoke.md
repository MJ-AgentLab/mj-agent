# docker-compose Smoke Test (2026-05-23)

- **Stage**: Phase M4 Stage C unit C-4
- **Branch**: `documentation/spec-anchored-refactor-m4-bc`
- **Outcome**: 3 services × 5 smoke check dimensions audited (mj-agent + mj-agent-postgres + mj-agent-redis); §3 basis Mixed (yaml config Empirical via `docker compose config` + live container Reference); **2 SUT-internal-docstring drifts surfaced** — (a) C-4 specific: `docker-compose.mj-agent.yml:2` references archived ADR-025 (should be ADR-026 Multi-Env Compose Profile); (b) cross-cap C-3 #C3-4 expansion: `.env.example:54` references archived ADR-025 in LLM Provider section (extends C-3 drift scope 3-file → 4-file)
- **Cluster**: docker-compose C-4 per-capability runtime check; **3rd file in runtime/ subdir overall** (after C-2 biz-catalog + C-3 llm-provider)

## §1 Goal + Scope

Verify docker-compose smoke test path per `spec.yml` REQ-001 (--env-file + explicit -f chain mandatory) + REQ-002 (psql healthcheck NOT pg_isready) + REQ-003 (no secrets baked into image) + B-4 commit `c8f37d6` §6.1 Volume Backup/Restore SOP + §6.2 Postgres Init Failure Recovery SOP empirical follow-up record. **C-4 sets capability category corrected path per #C4-1** (`capabilities/infrastructure/docker-compose/...` NOT `data-agent/`); reuses C-2/C-3 runtime/ subdir convention precedent (NO YAML frontmatter; H1 + Stage/Branch/Outcome/Cluster bullets; 6 sections) with §3 format: per-service smoke check status matrix。

**Out of scope**: live `docker compose up + healthcheck` empirical verification (network/runtime actions; requires live Docker daemon + 镜像 pull); deployment automation (Dockerfile + entrypoint.sh canonical layer; out of mj-agent capability governance).

## §2 Method

Per-source canonical implementation + B-4 SOP intermediate layer cross-ref:

- **`infra/docker/docker-compose.mj-agent.yml`** (247 lines; BASE compose; canonical surface): 3 services (mj-agent L73-112 / mj-agent-postgres L117-169 / mj-agent-redis L175-213) + 2 networks (mj-system-network external L222-224 + mj-agent-storage bridge L226-231) + 2 volumes (mj-agent-postgres-data L237-241 + mj-agent-redis-data L242-246); 4-file profile layering per ADR-026 (mj-agent.yml + override.yml + test.yml + prod.yml per L4-12 header)
- **`infra/docker/Dockerfile`** (canonical; 60+ lines preview; Python 3.13-slim + uv + multi-stage builder→runtime; `mj-agent` console script + `mj-agent check` healthcheck entry per L11-12)
- **`infra/docker/entrypoint.sh`** + **`infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh`** (canonical scripts; postgres init handles REQ-003 shell-safe `\getenv` + `format` + `\gexec` chain)
- **`.env.example`** (canonical env template; 60+ lines preview; section markers per ADR refs)
- **B-4 `c8f37d6` runbook intermediate layer** (B-4 landed; full SOP richness per #C4-4):
  - §3 6 mature symptom blocks (password auth / mj-agent stuck Created / network not found / postgres metacharacter pwd / PROD timeout / Harbor pull failure)
  - §6.1 Volume Backup/Restore SOP (5-element Trigger/Pre-conditions/Steps/Verify/Rollback structure)
  - §6.2 Postgres Init Failure Recovery SOP (5-element structure)
  - §4 10 Related Artifacts entries (4 SKILLs + 3 ADRs + STANDARD + baselines + scripts)

Empirical run protocol per B-4 §1 Startup commands: `docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml config` (yaml parse + interpolation validation; Empirical in-process) → `docker compose ... up -d` (live container; Reference; requires Docker daemon) → `docker inspect --format='{{.State.Health.Status}}' mj-agent` (per B-4 §2 Health Check). No automated tests gate at Phase M1 (per Bash `ls tests/integration/ tests/contract/ | grep -iE "docker|compose|container"` returned empty; #C4-3).

## §3 Results

**Basis: Mixed** (yaml config Empirical via `docker compose config` in-process + live container Reference; ZERO docker-related automated tests in tests/ per #C4-3). Per-service smoke check status matrix:

| Service | Image | Healthcheck | Volume Mount | Network Bind | Env Injection | Per-row Basis |
|---|---|---|---|---|---|---|
| **mj-agent** | `mj-agent:0.1` (DEV build / TEST/PROD Harbor) | `mj-agent check` 30s interval / 10s timeout / 30s start_period / 3 retries (L102-107) | (none; stateless) | `mj-system-network` external + `mj-agent-storage` internal (L108-110) | `env_file: ../../.env` + 4 universal env vars (MJ_AGENT_MEMORY_HOST/PORT + MJ_AGENT_REDIS_HOST/PORT + CHAINLIT_HOST/PORT) per L80-93 | Empirical (yaml structure) |
| **mj-agent-postgres** | `postgres:18-alpine@sha256:96d56f...db88` (digest-pinned PR #52) | `psql -U postgres -d $${MJ_AGENT_MEMORY_DB:-mj_agent_memory} -tc 'SELECT 1'` 10s interval / 5s timeout / 30s start_period / 5 retries (L145-164; **per REQ-002 NOT pg_isready**) | `mj-agent-postgres-data:/var/lib/postgresql` + `./postgres-init:/docker-entrypoint-initdb.d:ro` (L139-141) | `mj-agent-storage` internal only (L166-167) | POSTGRES_USER + POSTGRES_PASSWORD + MJ_AGENT_MEMORY_DB/USER/PASSWORD per L122-129 (sentinel `:-local-dev-only-replace-in-prod` per REQ-001 --env-file enforcement) | Empirical (yaml + REQ-002 alignment confirmed) |
| **mj-agent-redis** | `redis:8-alpine@sha256:d146f...02d2` (digest-pinned PR #52) | `redis-cli ping` OR `redis-cli -a $PASS --no-auth-warning ping` 10s interval / 3s timeout / 5s start_period / 5 retries (L199-208; auth-conditional branch) | `mj-agent-redis-data:/data` (L194-195) | `mj-agent-storage` internal only (L210-211) | MJ_AGENT_REDIS_PASSWORD per L191 (optional; auth-conditional command) | Empirical (yaml + auth-conditional logic) |

Per-service aggregate: 3/3 services configured with healthcheck (mj-agent depends_on requires both postgres + redis service_healthy per L96-100); volumes scoped per service (no shared); networks segregated (mj-system-network external only for mj-agent; storage bridge internal only). REQ-001/002/003 alignment confirmed at yaml-config layer (Empirical); live smoke `up -d` outcome basis = Reference (out-of-scope per #1 limitation).

## §4 Observations

### §4.1 C-4 Specific SUT-Internal-Docstring Drift (NEW; ADR-025 Archived Reference)

3-source authoritative-vs-outlier triangulation:

- **`infra/docker/docker-compose.mj-agent.yml`** L2 (verbatim): `# mj-agent compose stack — BASE (env-agnostic; see ADR-008 + ADR-025)` — references archived **ADR-025**
- **Authoritative**: CLAUDE.md confirms ADR-025 ARCHIVED in PR-Γ 2026-05-11 (split into ADR-026/027/028). For multi-environment compose profile context, **ADR-026** (Multi-Environment Compose Profile) is the authoritative active record; spec.yml related_decisions for docker-compose capability would list ADR-026 (not archived ADR-025)
- **Cross-cap parallel**: Same pattern as C-1c execute.py L4-15 + C-3 llm.py L3 + config.py L62 + SKILL.md L3+L10 — in-source documentation references archived ADR post-split

**Disposition** (per C-1c §4.1 + C-3 §4.1 cumulative precedent): F-7 cluster amend observation candidate; **NOT new M4-FU entry** (orthogonal to existing 6 registry candidates); **NOT modified in C-4** (batch boundary 守约: 不动 docker-compose.mj-agent.yml canonical surface within current batch). Reconcile path: Phase F-7 closure cumulative amend OR independent post-M4-BC small docs PR — docker-compose.mj-agent.yml L2 `ADR-025` → `ADR-026` (1-line edit).

### §4.2 Cross-Cap Expansion: C-3 #C3-4 Drift Scope 3-File → 4-File (.env.example Discovered)

Step 1 finalize read of `.env.example` for docker-compose smoke env injection verification surfaced **4th file** with archived ADR-025 reference:

- **`.env.example` L54** (verbatim): `### 2. LLM Provider (multi-provider abstraction; ADR-025) ###` — references archived ADR-025 in LLM Provider section (same drift as C-3 #C3-4 LLM provider scope; should be ADR-027)
- **Cross-cap discovery**: this drift is **LLM provider scope** (not docker-compose), but surfaced during C-4 Step 1 because .env.example contains both docker-compose env vars (sections 0-1) AND LLM Provider env vars (section 2 starting L54)

**Cumulative C-3 #C3-4 expansion summary**:
- C-3 brief assumed 1-file (llm.py L3)
- C-3 Step 1 finalize surfaced 3-file (+ config.py L62 + SKILL.md L3+L10)
- **C-4 Step 1 finalize surfaced 4th file (.env.example L54)**

Disposition: extends C-3 §4.1 F-7 observation scope; reconcile path post-M4-BC small docs PR now requires **4-file edit** (not 3-file). NOT new M4-FU.

### §4.3 B-4 §6.1+§6.2 SOPs Empirical Application Confirmation

C-4 evidence file IS B-4 commit `c8f37d6` §6.1 Volume Backup/Restore + §6.2 Postgres Init Failure Recovery SOPs empirical follow-up record (类 C-2 with B-2 §6.1 SOP pattern; vs C-3 minimal direct-to-canonical due to B-3 frontmatter-only).

- §6.1 Volume Backup/Restore SOP: 2 named volumes verified (`mj-agent-postgres-data` + `mj-agent-redis-data` per yml L237-246; both labeled `com.mj-agent.volume.backup: "daily"` per L241+L246) — backup target identification ✅
- §6.2 Postgres Init Failure Recovery SOP: `postgres-init` mount confirmed (yml L141 `./postgres-init:/docker-entrypoint-initdb.d:ro`); init script reference per B-4 §6.2 SOP Step 5 (psql `SELECT 1` healthcheck per REQ-002) — recovery path identification ✅

### §4.4 Smoke Empirical Limitation (Per C-3 Endpoint Parallel)

Per #C4-3: ZERO docker-related automated tests in `tests/contract/` + `tests/integration/`. Smoke verification basis = **yaml-config Empirical** (`docker compose config` validates interpolation + service definitions in-process) + **live-container Reference** (requires Docker daemon + image pull + 30s+ healthcheck wait). Full empirical requires (a) live Docker daemon + `docker compose up -d` execution OR (b) Phase M3 BDD test landing per `behavior.feature` Phase M3 step definition target.

Parallel to **C-3 endpoint empirical limitation** (network actions out of SUT scope) + **C-1c L4 reference-contract limitation** (cross-repo R__analyst_permissions.sql)。

## §5 Cross-references

- `capabilities/infrastructure/docker-compose/spec.yml` — REQ-001 (--env-file + explicit -f chain mandatory) / REQ-002 (psql healthcheck NOT pg_isready) / REQ-003 (no secrets baked into image; postgres init handles shell metacharacters via `\getenv` + `format` + `\gexec`)
- `capabilities/infrastructure/docker-compose/contracts/behavior.feature` — 3 BDD scenarios `@risk:high @adapter:docker-container @adr:ADR-026` (L1 REQ-001 DEV profile / L2 REQ-002 postgres healthcheck rejects half-initialized DB / L3 REQ-003 shell metacharacter password unmangled)
- **B-4 commit `c8f37d6` `capabilities/infrastructure/docker-compose/runbook.md`** (RICH intermediate layer):
  - §3 6 symptom blocks (password auth / stuck Created / mj-system-backend-network not found / Postgres metacharacter pwd / PROD timeout / Harbor pull failure)
  - §6.1 Volume Backup/Restore SOP (L173-187)
  - §6.2 Postgres Init Failure Recovery SOP (L189-204)
  - §4 Related Artifacts 12 entries (incl. 2 cross-cap refs added in B-4)
- `infra/docker/docker-compose.mj-agent.yml` (canonical BASE; 247 lines; 3 services + 2 networks + 2 volumes; **★ L2 archived ADR-025 reference per §4.1 drift**)
- `infra/docker/docker-compose.{override,test,prod}.yml` (canonical profile overlays; per ADR-026 4-file layering)
- `infra/docker/Dockerfile` (canonical; Python 3.13-slim + uv multi-stage builder→runtime; `mj-agent` console script entry)
- `infra/docker/entrypoint.sh` + `infra/docker/postgres-init/01-bootstrap-mj-agent-memory.sh` (canonical scripts; REQ-003 shell-safe init)
- `.env.example` (canonical env template; **★ L54 archived ADR-025 reference per §4.2 cross-cap C-3 #C3-4 expansion**)
- `docs/adr/[ADR]_026_Multi_Environment_Compose_Profile.md` (**authoritative** active decision record per PR-Γ 2026-05-11 split; should be referenced in docker-compose.mj-agent.yml L2 instead of archived ADR-025 per §4.1)
- `docs/archive/adr/[DEPRECATED]_[ADR]_025_*.md` (historical reference; archived per PR-Γ; cited in §5 as drift context only)
- C-3 evidence file `2026-05-23_endpoint_probe.md` §4.1 (3-file scope drift; **now 4-file post-C-4 §4.2 expansion**)

## §6 Forward

This evidence file (C-4) is the **3rd runtime/ file overall** (after C-2 biz-catalog + C-3 llm-provider):

- **C-2** (`biz-catalog/evidence/runtime/2026-05-23_freshness_check.md`; 96 lines; commit `cf674a9`) — biz-catalog freshness check; documented-drift-only positive null
- **C-3** (`llm-provider/evidence/runtime/2026-05-23_endpoint_probe.md`; 98 lines; commit `e7e6646`) — llm-provider endpoint probe; SUT-internal-docstring 3-file scope (now **4-file** per C-4 §4.2 expansion)
- **C-4** (this file) — docker-compose smoke test; runtime/ 3rd file; C-4 specific drift (docker-compose.mj-agent.yml L2 ADR-025 → ADR-026) + cross-cap C-3 expansion (.env.example L54)
- **C-5** (next; **FINAL Stage C unit**) — mcp-server-governance Q2 audit evidence; `evidence/runtime/2026-05-23_quarterly_audit_q2.md`; ~120-180 lines; B-5 commit `46b0147` §1+§3+§4 micro 微调 anchor; **12th of 12 cumulative**; **closes Stage B+C cluster**

Stage C close (12 commits) → m4-bc → user-driven Step 13 (push + PR #M4-BC targeting develop)。Cumulative 6 distinct epistemic findings (C-1a SUT-spec / C-1b SUT-runbook / C-1c SUT-internal-docstring / C-2 documented-drift positive null / C-3 SUT-internal-docstring 3→4-file scope / C-4 SUT-internal-docstring NEW C-4-specific + cross-cap C-3 expansion) feed F-7 cluster amend **docstring drift detector** governance candidate template (per cumulative SUT-internal-docstring sub-type **3 units repeat = 60% sub-type rate**: C-1c + C-3 + C-4; total 6 source files across spec-anchored discipline scope)。
