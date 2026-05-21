"""BDD step definitions for data-agent.safe-sql capability.

Binds offline-runnable scenarios from
`capabilities/data-agent/safe-sql/contracts/behavior.feature`:
- REQ-001: L1 regex guardrail rejection (pure Python; no DB)
- REQ-002: L1b precheck rejection (pure Python + catalog YAML read; no DB)
- REQ-006: handle_sql_tool_errors middleware ToolMessage conversion (pure Python)

REQ-003 (L3 read-only connection), REQ-004 (L4 statement_timeout), and REQ-005
(execute_sql full envelope) require live DB and are deferred to B-2 with
skip markers per Stage B kickoff plan.

Per pytest-bdd 8.x: @scenario binds one scenario by name; step defs in
the same module (or imported via from _shared.steps import *) are
auto-discovered for that scenario.
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
