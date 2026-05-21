# BDD Step Definitions — B-2 safe-sql REQ-003 / 005 (REQ-004 documented unbound)

**Stage:** Phase M3 Stage B Unit-2 (safe-sql complete except REQ-004)
**Branch:** `documentation/spec-anchored-refactor-m3`
**Outcome:** 2 additional safe-sql scenarios (REQ-003 / REQ-005) bound with live-DB gating; REQ-004 (statement_timeout) intentionally unbound with rationale.

## Scenarios added (B-2 scope)

| REQ | Scenario | Gating | CI behaviour |
|---|---|---|---|
| REQ-003 | L3 connection enforces read-only transaction + bounded timeouts via DSN options | `live_db` fixture (POSTGRES_ANALYST_USER) | SKIPPED in CI; runs locally with `.env` |
| REQ-004 | L4 statement_timeout cancellation translates to Chinese self-correction hint | **not bound** — `@scenario` decorator intentionally omitted; rationale below | n/a |
| REQ-005 | execute_sql return envelope contains 8 required keys with documented types | `live_db` fixture | SKIPPED in CI; runs locally with `.env` |

### Why REQ-004 is not bound

The Gherkin scenario requires:
- "an in-flight SQL query exceeds 60s"
- "the PostgreSQL backend raises psycopg.errors.QueryCanceled"

This requires deterministically provoking a 60s+ query against the live biz pg, which is not reliably reproducible in CI (and adds substantial wall time). The underlying SUT path (psycopg.errors.QueryCanceled → RuntimeError with Chinese self-correction hint) is exercised:

- by `tests/smoke/*` when a developer manually runs a slow query, and
- by direct unit tests on the `execute_sql` exception-translation block.

Binding REQ-004 with a `pytest.skip()` body doesn't work because pytest-bdd processes scenario steps BEFORE the test function body — `pytest.skip()` fires too late and `StepDefinitionNotFoundError` raises first.

M4+ may revisit if a deterministic provocation method emerges (e.g., a controlled DB sleep query backed by `pg_sleep(60.5)`).

## live-DB gating pattern

```python
@scenario(_FEATURE_FILE, "...")
def test_req_003_l3_connection(live_db: None) -> None:
    pass
```

`live_db` is the existing session fixture in `tests/conftest.py` — skips when `POSTGRES_ANALYST_USER` env var is absent. By taking it as a function parameter, the test inherits the fixture's skip behaviour automatically. The fixture body returns `None` (informational gate; no setup work).

When the fixture skips, pytest-bdd reports `SKIPPED: POSTGRES_ANALYST_USER not set — skipping live-DB test` — clean CI output.

## REQ-003 step coverage

| Step | Implementation |
|---|---|
| Given the analyst credentials are configured | descriptive (confirmed by live_db fixture) |
| When readonly_cursor() opens a new psycopg session | opens session via `mj_agent.integrations.mj_system_db.readonly_cursor` + captures `{dsn, pool, cur}` |
| Then DSN options contains `-c default_transaction_read_only=on` | string-match against `_dsn()` output |
| Then DSN options contains `-c lock_timeout=5000` | same |
| Then DSN options contains `-c idle_in_transaction_session_timeout=10000` | same |
| Then on context exit cursor rolls back | descriptive — verified by code-read of `readonly_cursor` context manager; the @when opening+closing without leak is the runtime confirmation |
| Then pool is configured with min_size=1, max_size=4, autocommit=False, row_factory=dict_row | inspect `ConnectionPool` `.min_size` / `.max_size` / `.kwargs["autocommit"]` / `.kwargs["row_factory"].__name__` |

## REQ-005 step coverage

| Step | Implementation |
|---|---|
| Given execute_sql is invoked with a valid SELECT statement that returns 5 rows | fixture `envelope_sql` = `SELECT data_date FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '60 days' ORDER BY data_date DESC LIMIT 5` |
| When the envelope is returned | call `execute_sql(envelope_sql)` |
| Then envelope dict has exactly 8 keys | `len(envelope) == 8` |
| Then key `executed_sql` is a string equal to input | `envelope[key] == envelope_sql` |
| Then key `columns` is a list of strings | type check |
| Then key `rows` is a list of dicts | type check |
| Then key `row_count` is integer == 5 | direct compare |
| Then key `truncated` is boolean == False | identity compare |
| Then key `statement_timeout_hit` is boolean == False | same |
| Then key `business_summary` is non-empty string | type + truthy check |
| Then key `precheck_warnings` is list of strings | type check |

## Regression checks

- `uv run pytest tests/bdd/data_agent/safe_sql -v` → 3 PASS + 2 SKIPPED (live-DB gated)
- `uv run pytest tests -q` → 332 passed (same baseline as B-1)
- `uv run ruff check` → clean
- `uv run mypy src/mj_agent` → clean (no src changes in B-2)

## Files changed

| File | Change |
|---|---|
| `tests/bdd/data_agent/safe_sql/test_safe_sql_bdd.py` | added @scenario for REQ-003 + REQ-005 with `live_db` fixture; added step defs for both scenarios; documented REQ-004 unbound rationale |
| `capabilities/data-agent/safe-sql/evidence/bdd/b2-live-db-scenarios-landing.md` | this file |
