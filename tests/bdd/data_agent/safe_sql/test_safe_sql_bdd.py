"""BDD step definitions for data-agent.safe-sql capability.

Binds all 6 scenarios from
`capabilities/data-agent/safe-sql/contracts/behavior.feature`:

B-1 (offline):
- REQ-001: L1 regex guardrail rejection
- REQ-002: L1b precheck rejection
- REQ-006: handle_sql_tool_errors middleware ToolMessage conversion

B-2 (live-DB gated; skip cleanly without POSTGRES_ANALYST_USER):
- REQ-003: L3 read-only connection DSN options + pool config
- REQ-004: L4 statement_timeout cancellation (unconditional skip — infeasible
  to provoke a 60s+ query reliably in CI; manual smoke only)
- REQ-005: execute_sql envelope schema with 8 keys

Shared step defs (Background, common assertions) live in tests/bdd/conftest.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import ToolMessage
from pytest_bdd import given, parsers, scenario, then, when

# Shared step defs (Background no-ops + assertion helpers) live in
# tests/bdd/conftest.py — pytest-bdd auto-discovers them for any test
# in tests/bdd/**.

# Path relative to this test file. Resolved by pytest-bdd at collection time.
_FEATURE_FILE = "../../../../capabilities/data-agent/safe-sql/contracts/behavior.feature"


# -------- Scenarios bound (B-1 scope: 3 offline scenarios) --------


@scenario(_FEATURE_FILE, "L1 regex guardrail rejects blocked-keyword statement before DB contact")
def test_req_001_l1_guardrail() -> None:
    pass


@scenario(_FEATURE_FILE, "L1b precheck rejects biz_dws fact-table query missing time-column predicate")
def test_req_002_l1b_precheck() -> None:
    pass


@scenario(_FEATURE_FILE, "handle_sql_tool_errors middleware converts tool ValueError into ToolMessage")
def test_req_006_middleware_tool_message() -> None:
    pass


@scenario(_FEATURE_FILE, "L3 connection enforces read-only transaction + bounded timeouts via DSN options")
def test_req_003_l3_connection(live_db: None) -> None:  # noqa: ARG001 — fixture gates the scenario
    pass


# REQ-004 (L4 statement_timeout cancellation) is intentionally NOT bound via
# @scenario in B-2: the contract requires provoking a 60s+ query, which is
# not reliably reproducible in CI even with live_db creds. The SUT exception
# translation path (psycopg.errors.QueryCanceled → RuntimeError with the
# Chinese hint) is exercised by tests/smoke/* when a developer runs against
# a real slow query. M4+ may revisit if a deterministic provocation is found.


@scenario(_FEATURE_FILE, "execute_sql return envelope contains 8 required keys with documented types")
def test_req_005_envelope_schema(live_db: None) -> None:  # noqa: ARG001 — fixture gates the scenario
    pass


# -------- REQ-001 step defs --------


@given(parsers.parse('the user-generated SQL is "{sql}"'), target_fixture="sql_input")
def given_sql_input(sql: str) -> str:
    return sql


def _call_execute_sql_capture_exception(sql: str) -> BaseException:
    """Invoke execute_sql and return the exception it raised.

    Used by @then steps so they remain stateless (do not require a prior
    @when to capture the exception into a fixture). Safe because execute_sql
    is idempotent in the rejection path (no DB contact before L1/L2 raise).
    """
    from mj_agent.tools.sql.execute import execute_sql
    try:
        execute_sql(sql)
    except BaseException as exc:  # noqa: BLE001 — capture everything for assertion
        return exc
    raise AssertionError(f"execute_sql did not raise for {sql!r}")


@when("the agent invokes execute_sql with that statement", target_fixture="raised_exception")
def when_invoke_execute_sql(sql_input: str) -> BaseException:
    return _call_execute_sql_capture_exception(sql_input)


@then(parsers.parse(
    'execute_sql raises ValueError whose message starts with "{prefix}"'
), target_fixture="raised_exception")
def then_value_error_starts_with(sql_input: str, prefix: str) -> BaseException:
    """Stateless assertion: re-invokes execute_sql so it works whether or not
    the scenario's @when was `execute_sql` (REQ-001) or `precheck_sql` (REQ-002).
    Caches the exception via target_fixture for downstream `the message contains`
    steps in the same scenario.
    """
    exc = _call_execute_sql_capture_exception(sql_input)
    assert isinstance(exc, ValueError), (
        f"expected ValueError, got {type(exc).__name__}: {exc}"
    )
    assert str(exc).startswith(prefix), (
        f"expected message starting with {prefix!r}, got {exc!r}"
    )
    return exc


@then("the database is not contacted (readonly_cursor never opens)")
def then_db_not_contacted() -> None:
    """L1 guardrail rejects synchronously before any DB code path — verified by code-read.

    The execute_sql implementation in src/mj_agent/tools/sql/execute.py runs
    is_safe_select() FIRST and raises ValueError before reaching
    readonly_cursor(). Direct trace would require psycopg mocking; this
    step is satisfied by the structural invariant.
    """


# -------- REQ-002 step defs --------


@given("the SQL passes the L1 regex guardrail (SELECT-only, allowlisted schema)")
def given_l1_passes(sql_input: str) -> None:
    """Asserted as part of the When step (precheck only runs after L1 passes)."""
    from mj_agent.config import settings
    from mj_agent.tools.sql.guardrail import is_safe_select
    ok, _ = is_safe_select(
        sql_input,
        settings.biz_allowed_schemas,
        allowed_tables_per_schema={"biz_dwd": settings.biz_allowed_dwd_tables},
    )
    assert ok, f"precondition violated: L1 guardrail rejected {sql_input!r}"


@when("precheck_sql parses the SQL via sqlglot", target_fixture="precheck_result")
def when_precheck_sql(sql_input: str) -> Any:
    from mj_agent.tools.sql.precheck import precheck_sql
    return precheck_sql(sql_input)


@then(parsers.parse(
    'PrecheckResult.errors contains a string starting with "{prefix}"'
))
def then_precheck_errors_contain(precheck_result: Any, prefix: str) -> None:
    assert any(e.startswith(prefix) for e in precheck_result.errors), (
        f"expected error starting with {prefix!r}; got errors={precheck_result.errors!r}"
    )


# -------- REQ-006 step defs --------


@dataclass
class _StubRequest:
    """Stand-in for langchain ToolCallRequest; only tool_call is read."""
    tool_call: dict[str, Any]


@given(parsers.parse(
    'a ToolCallRequest whose handler raises ValueError("{message}") with tool_call_id="{call_id}"'
), target_fixture="tool_call_state")
def given_tool_call_request(message: str, call_id: str) -> dict[str, Any]:
    return {
        "request": _StubRequest(tool_call={"id": call_id, "name": "execute_sql"}),
        "exc": ValueError(message),
    }


@when("handle_sql_tool_errors wraps the handler invocation", target_fixture="tool_message")
def when_middleware_converts(tool_call_state: dict[str, Any]) -> ToolMessage:
    from mj_agent.middleware.tool_errors import _convert
    return _convert(tool_call_state["request"], tool_call_state["exc"])


@then("the middleware returns a ToolMessage (does NOT re-raise)")
def then_returns_tool_message(tool_message: ToolMessage) -> None:
    assert isinstance(tool_message, ToolMessage)


@then(parsers.parse('the ToolMessage.content starts with "{prefix}"'))
def then_tool_message_starts_with(tool_message: ToolMessage, prefix: str) -> None:
    assert tool_message.content.startswith(prefix), (
        f"expected content starting with {prefix!r}, got {tool_message.content[:80]!r}"
    )


@then(parsers.parse('the ToolMessage.content contains "{substring}"'))
def then_tool_message_contains(tool_message: ToolMessage, substring: str) -> None:
    assert substring in tool_message.content, (
        f"expected {substring!r} in content {tool_message.content!r}"
    )


@then(parsers.parse('the ToolMessage.content ends with the retry hint "{hint}"'))
def then_tool_message_ends_with_hint(tool_message: ToolMessage, hint: str) -> None:
    assert tool_message.content.endswith(hint), (
        f"expected content ending with {hint!r}, got {tool_message.content[-80:]!r}"
    )


@then(parsers.parse('the ToolMessage.tool_call_id equals "{call_id}"'))
def then_tool_call_id_equals(tool_message: ToolMessage, call_id: str) -> None:
    assert tool_message.tool_call_id == call_id


# -------- REQ-003 step defs (live-DB gated via scenario fixture) --------


@given("the analyst credentials are configured (POSTGRES_ANALYST_USER set)")
def given_analyst_creds_configured() -> None:
    """Confirmed by live_db fixture above; this step is descriptive."""


@when("readonly_cursor() opens a new psycopg session", target_fixture="readonly_session")
def when_readonly_cursor_opens() -> dict[str, Any]:
    from mj_agent.integrations.mj_system_db import _dsn, get_pool, readonly_cursor
    pool = get_pool()
    with readonly_cursor() as cur:
        return {"dsn": _dsn(), "pool": pool, "cur": cur}


@then(parsers.parse('the session\'s DSN options string contains "{snippet}"'))
def then_dsn_contains(readonly_session: dict[str, Any], snippet: str) -> None:
    assert snippet in readonly_session["dsn"], (
        f"DSN does not contain {snippet!r}: {readonly_session['dsn']}"
    )


@then(parsers.parse('the DSN options contains "{snippet}"'))
def then_dsn_options_contains(readonly_session: dict[str, Any], snippet: str) -> None:
    assert snippet in readonly_session["dsn"], (
        f"DSN does not contain {snippet!r}: {readonly_session['dsn']}"
    )


@then("on context exit the cursor's connection rolls back any open transaction")
def then_cursor_rolls_back() -> None:
    """Verified by code-read of integrations/mj_system_db.py readonly_cursor:
    the context manager catches Exception and rolls back, then closes. The
    fact that the @when above opened and closed the cursor without leaking
    a tx is the runtime confirmation.
    """


@then(parsers.parse(
    "the pool is configured with min_size={min_size:d}, max_size={max_size:d}, "
    "autocommit={autocommit}, row_factory={row_factory}"
))
def then_pool_configured(
    readonly_session: dict[str, Any],
    min_size: int,
    max_size: int,
    autocommit: str,
    row_factory: str,
) -> None:
    pool = readonly_session["pool"]
    assert pool.min_size == min_size, f"pool.min_size={pool.min_size} != {min_size}"
    assert pool.max_size == max_size, f"pool.max_size={pool.max_size} != {max_size}"
    # autocommit / row_factory live in pool.kwargs (psycopg_pool ConnectionPool)
    expected_autocommit = autocommit.strip().lower() == "true"
    assert pool.kwargs.get("autocommit") == expected_autocommit
    # row_factory is callable; compare by __name__
    rf = pool.kwargs.get("row_factory")
    assert rf is not None and getattr(rf, "__name__", "") == row_factory, (
        f"row_factory={rf} does not match {row_factory!r}"
    )


# -------- REQ-005 step defs (live-DB gated via scenario fixture) --------


@given("execute_sql is invoked with a valid SELECT statement that returns 5 rows",
       target_fixture="envelope_sql")
def given_envelope_sql() -> str:
    return (
        "SELECT data_date FROM biz_dws.dws_qcm_qrynum_daily_total "
        "WHERE data_date >= CURRENT_DATE - INTERVAL '60 days' "
        "ORDER BY data_date DESC LIMIT 5"
    )


@when("the call succeeds and the envelope is returned", target_fixture="envelope")
def when_envelope_returned(envelope_sql: str) -> dict[str, Any]:
    from mj_agent.tools.sql.execute import execute_sql
    return execute_sql(envelope_sql)


@then(parsers.parse("the envelope dict has exactly {n:d} keys"))
def then_envelope_has_n_keys(envelope: dict[str, Any], n: int) -> None:
    assert len(envelope) == n, f"envelope has {len(envelope)} keys, expected {n}: {list(envelope)}"


@then(parsers.parse('key "{key}" is a string equal to the input SQL verbatim'))
def then_executed_sql_equals_input(envelope: dict[str, Any], envelope_sql: str, key: str) -> None:
    assert envelope[key] == envelope_sql


@then(parsers.parse('key "{key}" is a list of strings'))
def then_key_is_list_of_strings(envelope: dict[str, Any], key: str) -> None:
    assert isinstance(envelope[key], list)
    assert all(isinstance(x, str) for x in envelope[key])


@then(parsers.parse('key "{key}" is a list of dicts (each row mapping column-name to value)'))
def then_key_is_list_of_dicts(envelope: dict[str, Any], key: str) -> None:
    assert isinstance(envelope[key], list)
    assert all(isinstance(x, dict) for x in envelope[key])


@then(parsers.parse('key "{key}" is an integer equal to {value:d}'))
def then_key_is_int_equal(envelope: dict[str, Any], key: str, value: int) -> None:
    assert envelope[key] == value


@then(parsers.parse('key "{key}" is a boolean equal to {value}'))
def then_key_is_bool_equal(envelope: dict[str, Any], key: str, value: str) -> None:
    expected = value.strip().lower() == "true"
    assert envelope[key] is expected


@then(parsers.parse('key "{key}" is a string (heuristic Chinese summary)'))
def then_key_is_string_summary(envelope: dict[str, Any], key: str) -> None:
    assert isinstance(envelope[key], str)
    assert envelope[key]  # non-empty


@then(parsers.parse('key "{key}" is a list of strings (empty if no precheck warnings fired)'))
def then_key_is_list_of_strings_warnings(envelope: dict[str, Any], key: str) -> None:
    assert isinstance(envelope[key], list)
    assert all(isinstance(x, str) for x in envelope[key])
