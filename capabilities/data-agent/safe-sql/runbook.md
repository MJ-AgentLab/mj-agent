---
type: capability-runbook
capability: data-agent.safe-sql
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-23
last_verified: 2026-05-20
---

# Runbook: Safe SQL 4-Layer Guardrails

> Phase M1 baseline. ≥ 3 sections per quality baseline. References existing
> `docs/runbook/dev_studio_walkthrough.md` for shared startup context (M5
> migration will dissolve docs/runbook/ into capability runbooks).

## §1 Startup

### Local DEV

```bash
# 1. Install deps + decrypt secrets to .env
uv sync
.\scripts\setup-env.ps1

# 2. Verify L3 connection wiring (no DB call; just import-level check)
uv run python -c "from src.mj_agent.integrations.mj_system_db import get_pool; print('pool factory loaded')"

# 3. Verify L1 guardrail + L1b precheck modules importable
uv run python -c "from src.mj_agent.tools.sql import guardrail, precheck, execute; print('safe-sql modules loaded')"

# 4. Start LangGraph Studio (loads agent.py make_graph with middleware wiring)
uv run langgraph dev
```

### TEST / PROD profiles

Per `infra/docker/CLAUDE.md` (Phase M5 will become `docker/CLAUDE.md`). 4-file
profile chain; `--env-file .env` explicit.

```bash
# DEV
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml up -d

# TEST (192.168.0.179)
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.test.yml up -d

# PROD (192.168.0.106)
docker compose --env-file .env -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.prod.yml up -d
```

## §2 Health Check

```bash
# Lightweight smoke (no DB; checks LLM creds + module imports)
uv run mj-agent check

# Full pre-flight (requires POSTGRES_ANALYST_USER + biz pg reachable)
uv run pytest tests/unit/test_guardrail.py tests/unit/test_precheck.py tests/unit/test_tool_error_middleware.py -q
# Expected: ~30+ tests passed; ~25-30 seconds

# Integration test (skip-clean without DB creds)
uv run pytest tests/integration -q

# Contract tests for cross-cap deps (biz-catalog freshness; skip-clean without DB)
uv run pytest tests/contract -m contract -q
```

**Expected outcomes**：

| Command | DB creds present | DB creds absent |
|---|---|---|
| `mj-agent check` | LLM + DB OK | LLM OK + DB warning |
| `pytest tests/unit` (sql tests) | all pass | all pass (no DB needed) |
| `pytest tests/integration` | all pass | session-skip (clean) |
| `pytest tests/contract -m contract` | all pass | 12 skipped (clean) |

## §3 Troubleshooting

### Symptom: `ValueError: SQL rejected by guardrail: ...`

**Diagnostic**：L1 regex caught a write keyword / disallowed schema / multi-statement /
non-SELECT / empty SQL / out-of-allowlist biz_dwd table.

**Resolution**：

- If LLM generates write SQL → check `prompts/system.md` body (do NOT modify — `prompt-version-bump` 必停; instead file an `[AGENT]` issue with the prompt-vs-output drift evidence)
- If SQL targets `biz_ods` / `biz_ads` → these are not visible to mj-agent; ADR-009 constraint
- If targeting unlisted biz_dwd table → check `settings.biz_allowed_dwd_tables` (currently 2 dim tables); expansion requires sql-guardrail-relax HITL + cross-capability change

### Symptom: `ValueError: SQL rejected by precheck: <rule_id>: ...`

**Diagnostic**：L1b sqlglot AST rule fired. 5 rule IDs (per spec.yml REQ-002):

- `require_time_range: ...` — biz_dws fact table without time-column predicate (rule fires on schema=biz_dws + name starts_with dws_qcm_ + NOT in signal_tables)
- `no_select_star: ...` — `SELECT *` not allowed (use COUNT(*) if aggregation needed)
- `require_limit: ...` — non-aggregate detail query without LIMIT clause; **warning only** (surfaces in `envelope.precheck_warnings`; not blocking; REQ-005)
- `limit_too_large: ...` — LIMIT > threshold (currently 10000); **warning only**; tunable per query pattern
- `sqlglot_parse_failed: ...` — graceful fallback when sqlglot cannot parse; not blocking but surfaces

**Resolution**：

- Add a `WHERE` predicate on a column listed in `qcm_catalog.yaml periods.*.time_column` (currently `data_date`, `month`, etc.)
- Replace `*` with explicit columns
- For warnings (require_limit / limit_too_large): adjust query to match expected pattern OR accept warning (LLM sees them in envelope)

### Symptom: `RuntimeError: ... statement_timeout=60s ...`

**Diagnostic**：L4 — query took > 60s and DB cancelled per `R__analyst_permissions.sql`
upstream config.

**Resolution** (Chinese self-correction hint already in error message; LLM will
attempt these on retry)：

- Add GROUP BY (aggregate instead of detail)
- Narrow the time range in WHERE
- Reduce JOIN count
- If query is intrinsically slow → file `[RUNTIME]` issue; investigate upstream
  biz_dws index strategy (cross-repo to mj-system)

**Tuning parameters detail** (for §6.2 SOP reference):

- `statement_timeout` default `60s` set via upstream `R__analyst_permissions.sql` `ALTER ROLE analyst SET statement_timeout='60s'`; ANY adjustment 是 cross-repo change to mj-system + triggers canonical 10-enum `secrets-grants-or-prod-config` HITL (per `policies/ai-agent.md §4`)
- `lock_timeout` `5000ms` (5s) via DSN options in `mj_system_db.py`; pool factory-level config; adjustment requires `database-migration` enum (data-LLM boundary; ADR-006/009)
- `idle_in_transaction_session_timeout` `10000ms` (10s) via DSN options; rarely adjusted; preserves bounded resource consumption (REQ-003)
- See `§6.2 L3 Statement Timeout & Lock Timeout Tuning SOP` for the full workflow

### Symptom: `RuntimeError: database error: ...`

**Diagnostic**：Generic catch (non-`QueryCanceled` DB exception).

**Resolution**：

- Check `mj-agent-postgres` container health (for memory checkpointer) — `docker compose ps`
- Check biz pg reachability — `uv run mj-agent check` (provider-aware)
- Check `analyst` role auth — `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD` in `.env`
- Check `mj-system-backend-network` external network exists — `docker network ls | grep mj-system`

### Symptom: graph hangs / Chainlit frontend hangs after tool call

**Diagnostic**：potential middleware regression (ADR-029). REQ-006 contract says
`handle_sql_tool_errors` (sync) and `ahandle_sql_tool_errors` (async) catch
ValueError/RuntimeError and return ToolMessage instead of re-raising.

**Resolution**：

- Verify `make_graph()` in `agent.py` has `middleware=[handle_sql_tool_errors]`
- If using Chainlit (`graph.astream` path) → verify async variant wiring (TBD-M3
  per design.md §5 Q4)
- Check `tests/unit/test_tool_error_middleware.py` passes locally

### Symptom: catalog drift breaking REQ-002 `require_time_range`

**Diagnostic**：upstream biz_dws renamed a time column (e.g. `data_date` → `stat_date`)
but `qcm_catalog.yaml periods.*.time_column` still references the old name.

**Resolution**：

- This is the **intended drift detector** — the L1b precheck rule fails loudly
- Run `/mj-agent-runtime-biz-catalog-sync` skill (read-only diff) to compare
  `qcm_catalog.yaml` vs upstream DB
- File `[AGENT]` issue with biz-catalog-sync 必停 trigger
- Resolution touches `qcm_catalog.yaml` → HITL required

## §4 Related artifacts

- `contracts/sql-guardrail.contract.yml` — REQ-001 / REQ-002 details
- `contracts/execute-sql.contract.yml` — REQ-003 / REQ-004 / REQ-005 details
- `contracts/python.contract.yml` — module signatures + REQ-006 middleware
- `contracts/behavior.feature` — 6 Gherkin scenarios
- `docs/runbook/dev_studio_walkthrough.md` — broader Studio walkthrough (Phase M5 will dissolve into capability runbooks)
- `policies/data-boundary.md` — 数据-LLM 三原则 + 4 项必停 governance
- `§6.1 L2 Schema/Table Whitelist Extension SOP` — cross-ref `src/mj_agent/tools/sql/guardrail.py` `allowed_tables_per_schema` + `sql-guardrail-relax` canonical 10-enum HITL (per `policies/ai-agent.md §4`)
- `§6.2 L3 Statement Timeout & Lock Timeout Tuning SOP` — cross-ref behavior.feature REQ-003/REQ-004 + `mj_system_db.py` DSN options + upstream `R__analyst_permissions.sql`
- `§6.3 L4 Upstream DB Connection & Index Tuning SOP` — cross-ref spec.yml REQ-004 `reference_contract` + mj-system biz_dws index strategy (cross-repo)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` writeup when:

- REQ-001 rejects valid SQL (false positive at agent boundary) ≥ 3 times in same session
- REQ-002 `require_time_range` blocks query that has valid time predicate (false positive in fact-table detection)
- REQ-003 connection hangs > 30s (lock_timeout=5s should not allow this; investigate pool exhaustion)
- REQ-004 `statement_timeout` triggers on routine analyst query (DB-side timeout suggests slow upstream)
- REQ-005 envelope key missing or wrong type (LLM behavior break)
- REQ-006 middleware fails to catch (graph crashes) → highest priority; ADR-029 regression

Postmortem path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per
`policies/archive.md` retention class `permanent`.

## §6 Standard Operating Procedures (SOPs)

> Procedural how-to for the 3 most common safe-sql tuning / extension scenarios.
> Each SOP follows Trigger / Pre-conditions / Steps / Verify / Rollback structure.
> B-1 establishes this §6 SOPs pattern as **candidate precedent** for B-2..B-5 capability
> runbooks; **not mandated** per capability content needs.

### §6.1 L2 Schema/Table Whitelist Extension SOP

**Trigger**: New biz_dwd table (beyond current 2 dim tables) needs analyst exposure; OR new schema (beyond biz_dws + biz_dwd) needs allowlist.

**Pre-conditions**: Whitelist extension triggers canonical 10-enum **`sql-guardrail-relax`** HITL Gate-2 (per `policies/ai-agent.md §4`); Steps below MUST NOT execute before HITL Gate-2 ack obtained.

**Steps**:

1. **HITL Gate-2 question** — Open canonical 10-enum question; obtain user ack on enum trigger + scope + canonical surface impact
2. Edit `src/mj_agent/config.py` `biz_allowed_dwd_tables` (or `biz_allowed_schemas`) per requested expansion
3. Regression test: `uv run pytest tests/unit/test_guardrail.py::TestTableLevelAllowlist -q`; verify new table accepted, others still rejected
4. Update `runbook.md §3 L1 guardrail symptom block` if user-facing behavior changes

**Verify**: smoke test via `is_safe_select()` against new SQL referencing newly-allowlisted table → expect `(True, '')` accept tuple

**Rollback**: Revert `config.py` allowlist change; rerun regression test → expect old behavior restored

### §6.2 L3 Statement Timeout & Lock Timeout Tuning SOP

**Trigger**: `statement_timeout` cancellation 频繁 (§3 L4 symptom fires > 5 times in 1 day) OR query patterns systematically need > 60s; OR `lock_timeout` (5s) blocks legitimate longer-locked queries.

**Pre-conditions**: `statement_timeout` adjustment 是 **cross-repo change to mj-system `R__analyst_permissions.sql`** + triggers canonical 10-enum `secrets-grants-or-prod-config` HITL; `lock_timeout` adjustment via `mj_system_db.py` DSN options triggers `database-migration` enum (data-LLM boundary; ADR-006/009).

**Steps**:

1. HITL Gate-2 question per appropriate enum
2. For `statement_timeout`: file cross-repo PR to mj-system updating `R__analyst_permissions.sql` `ALTER ROLE analyst SET statement_timeout='<new>'`
3. For `lock_timeout`: edit `src/mj_agent/integrations/mj_system_db.py` `_dsn()` function DSN options
4. Coordinate deployment: upstream migration must precede mj-agent runtime restart for `statement_timeout`; for `lock_timeout`, mj-agent compose restart suffices
5. Regression: behavior.feature REQ-003/REQ-004 scenarios still pass with new values

**Verify**: `psql -c "SHOW statement_timeout" -U analyst` against biz pg → expect new value; mj-agent fixture test with adjusted lock_timeout

**Rollback**: Revert upstream R__ migration + mj-agent DSN edit; deploy in same coordinated order

### §6.3 L4 Upstream DB Connection & Index Tuning SOP

**Trigger**: `RuntimeError: database error` 频繁 (§3 generic DB error symptom > 3/day) OR specific biz_dws query routinely hits `statement_timeout=60s` despite tuning attempts (per §6.2).

**Pre-conditions**: Upstream tuning 是 **cross-repo coordination with mj-system team**; mj-agent SUT side cannot directly modify upstream biz_dws indexes / connection pool. File `[RUNTIME]` issue with reproducible query + impact scope; awaits upstream owner ack.

**Steps**:

1. Run `EXPLAIN ANALYZE <problem-query>` via analyst psql against biz pg → capture query plan + 实测 execution time
2. Identify missing index: cross-ref `biz_dws.dws_qcm_<table>` 与 typical WHERE predicate columns
3. File `[RUNTIME]` issue with evidence — propose specific index (e.g. `CREATE INDEX ON biz_dws.dws_qcm_qrynum_daily_total (data_date, institution_id)`)
4. mj-system team review + applies index migration via their migration mechanism
5. Post-deploy: rerun problem query; verify reduced execution time + no `statement_timeout` fires

**Verify**: mj-agent integration test re-run problem query under `uv run pytest tests/integration -q`; query envelope `row_count` returned without `statement_timeout_hit=true`

**Rollback**: If index causes write/maintenance regressions on biz_dws → mj-system team drops index; documenting drop rationale in issue

---

> Phase M1 baseline. Phase M2 will refine §3 troubleshooting with M3 contract test
> findings; Phase M5 will dissolve docs/runbook/dev_studio_walkthrough.md into this file.
