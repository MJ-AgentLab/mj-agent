---
type: capability-runbook
capability: data-agent.safe-sql
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
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

**Diagnostic**：L1b sqlglot AST rule fired. Common cases:

- `require_time_range: ...` — biz_dws fact table without time-column predicate (rule fires on schema=biz_dws + name starts_with dws_qcm_ + NOT in signal_tables)
- `no_select_star: ...` — `SELECT *` not allowed (use COUNT(*) if aggregation needed)

**Resolution**：

- Add a `WHERE` predicate on a column listed in `qcm_catalog.yaml periods.*.time_column` (currently `data_date`, `month`, etc.)
- Replace `*` with explicit columns

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

---

> Phase M1 baseline. Phase M2 will refine §3 troubleshooting with M3 contract test
> findings; Phase M5 will dissolve docs/runbook/dev_studio_walkthrough.md into this file.
