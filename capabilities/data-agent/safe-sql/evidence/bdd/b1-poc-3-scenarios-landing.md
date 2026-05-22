# BDD Step Definitions — B-1 Framework + safe-sql POC

**Stage:** Phase M3 Stage B Unit-1 (framework landing + 3 offline scenarios)
**Branch:** `documentation/spec-anchored-refactor-m3`
**Outcome:** pytest-bdd 8.1 wired into the existing pytest harness; 3 safe-sql scenarios (REQ-001 / REQ-002 / REQ-006) PASS end-to-end without live DB or LLM.

## Framework

| Decision | Choice | Rationale |
|---|---|---|
| BDD library | `pytest-bdd==8.1` | Native pytest plugin — shares fixtures and CI with existing `tests/unit/`. Step defs are Python functions, easier to maintain than `behave`'s separate runner. |
| Subdir layout | `tests/bdd/<domain>/<capability>/` | Mirrors `capabilities/<domain>/<capability>/`. 5 capability subdirs total (not 11 as initial outline assumed). |
| Step sharing | `tests/bdd/conftest.py` | pytest-bdd 8.x discovers steps from parent conftest.py for all child tests. `tests/bdd/_shared/steps.py` reserved for ordinary Python helpers (non-step) imported as utilities. |
| Gherkin literal `{` `}` `[` `]` | `parsers.re(re.escape(text))` | pytest-bdd's default parser treats `{name}` as a placeholder; the safe-sql Background contains literal `biz_dwd.{dwd_dim_product_interface, dwd_dim_institution}` so regex matching with escaped text is required. |
| Marker tag warnings | `filterwarnings = ["ignore::pytest.PytestUnknownMarkWarning"]` in `pyproject.toml` | Gherkin tags like `@REQ-001` / `@CTR-sql-guardrail` / `@risk:critical` / `@adapter:python` are informational traceability — not real pytest markers. ~20 noisy warnings per BDD run otherwise. |
| `@then` stateless re-invocation | Some `@then` steps re-invoke `execute_sql` directly | Allows the SAME assertion step text to work for REQ-001 (where the `@when` invokes `execute_sql`) and REQ-002 (where the `@when` invokes `precheck_sql`). `execute_sql` is idempotent in the rejection path — no DB contact. |

## Scenarios bound (B-1 scope; offline-only)

| REQ | Gherkin scenario name | Underlying SUT | Pass status |
|---|---|---|---|
| REQ-001 | L1 regex guardrail rejects blocked-keyword statement before DB contact | `is_safe_select` + `execute_sql` exception path | ✅ PASS |
| REQ-002 | L1b precheck rejects biz_dws fact-table query missing time-column predicate | `precheck_sql` + `execute_sql` exception path | ✅ PASS |
| REQ-006 | handle_sql_tool_errors middleware converts tool ValueError into ToolMessage | `_convert` middleware helper | ✅ PASS |

REQ-003 (L3 read-only connection requires live DB), REQ-004 (L4 statement_timeout requires live DB + slow query), REQ-005 (envelope full-run requires live DB) are deferred to **B-2** with conditional skip markers.

## Minor SUT improvement

REQ-001 scenario asserts `the message contains the blocked keyword name "DROP"` for SQL `DROP TABLE biz_dws.dws_qcm_qrynum_daily_total`. Prior `guardrail.is_safe_select` rejected via the "non-SELECT start" check first and returned a generic `only SELECT or WITH ... SELECT is allowed` reason that did not mention DROP.

Updated `src/mj_agent/tools/sql/guardrail.py`: when the SQL doesn't match `_STMT_START` AND `_BLOCKED.search` matches, surface the blocked keyword name in the reason (e.g., `blocked keyword DROP detected`). This makes the rejection reason more informative for analyst self-correction without changing the security boundary.

Existing 23 unit tests in `tests/unit/test_guardrail.py` all still PASS (no test broke from the message change — assertions check the prefix `SQL rejected by guardrail:` only, not the full reason string).

## Regression checks

- `uv run pytest tests -q` → **332 passed, 5 skipped (DB), 22 deselected (smoke)** (baseline was 236 + 3 BDD + existing unit increment from prior phases)
- `uv run ruff check` → clean (after auto-fix on import ordering)
- `uv run mypy src/mj_agent` → clean
- `uv run pytest tests/unit/test_guardrail.py` → 23/23 PASS (no regression from SUT message change)

## Files added/changed

| File | Change |
|---|---|
| `pyproject.toml` | `pytest-bdd>=8.1` added to `[dependency-groups].dev`; `filterwarnings = [...]` added |
| `uv.lock` | pytest-bdd + gherkin-official + mako + parse + parse-type pinned |
| `src/mj_agent/tools/sql/guardrail.py` | `_BLOCKED.search` used to surface keyword name in reason text |
| `tests/bdd/__init__.py` | new (package marker) |
| `tests/bdd/conftest.py` | new — shared Background step defs + assertion helpers |
| `tests/bdd/_shared/__init__.py` | new (package marker) |
| `tests/bdd/_shared/steps.py` | new — placeholder for cross-capability Python utility helpers (non-step) |
| `tests/bdd/data_agent/__init__.py` | new (package marker) |
| `tests/bdd/data_agent/safe_sql/__init__.py` | new (package marker) |
| `tests/bdd/data_agent/safe_sql/test_safe_sql_bdd.py` | new — 3 scenario bindings + capability-local step defs |
| `capabilities/data-agent/safe-sql/evidence/bdd/b1-poc-3-scenarios-landing.md` | this file |
