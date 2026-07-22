"""BDD step definitions for data-agent.memory-checkpointer (REQ-001/002/003).

Binds the 3 offline scenarios from
``capabilities/data-agent/memory-checkpointer/contracts/behavior.feature`` — they exercise
the pure redaction transform (``_redact_tool_message``; no container). REQ-004 (both on-disk
write paths) is intentionally NOT bound here: it needs the ``mj-agent-postgres`` container and
is covered by ``tests/smoke/test_memory_redaction_canary.py`` (trace.yml marks it unautomated).
"""

from __future__ import annotations

import json

from langchain_core.messages import ToolMessage
from pytest_bdd import given, parsers, scenario, then, when

from mj_agent.memory.redaction import _redact_tool_message

# Path relative to this test file; resolved by pytest-bdd at collection time.
_FEATURE = "../../../../capabilities/data-agent/memory-checkpointer/contracts/behavior.feature"


# -------- Scenarios bound (3 offline; REQ-004 canary is smoke-only) --------


@scenario(_FEATURE, "Persisting an execute_sql ToolMessage replaces biz rows with a per-column digest")
def test_req_001_rows_replaced_by_digest() -> None:
    pass


@scenario(_FEATURE, "Redaction clones the message so the live in-process state is untouched")
def test_req_002_live_state_untouched() -> None:
    pass


@scenario(_FEATURE, "The digested envelope retains executed_sql for recoverable-by-refetch")
def test_req_003_retains_executed_sql() -> None:
    pass


# -------- Step definitions --------


@given("the RedactingAsyncPostgresSaver is installed as the memory checkpointer")
def _saver_installed() -> None:
    """Background — the redacting saver is the persistence hook (feature-flagged in
    checkpointer.py). Descriptive; the offline transform is exercised directly below."""


@given(
    parsers.parse('an execute_sql ToolMessage whose rows contain the verbatim value "{value}"'),
    target_fixture="live_message",
)
def _live_message(value: str) -> ToolMessage:
    envelope = {
        "executed_sql": "SELECT tenant_id FROM biz_dws.dws_x WHERE data_date >= '2026-01-01'",
        "columns": ["tenant_id"],
        "rows": [{"tenant_id": value}],
        "row_count": 1,
        "truncated": False,
        "statement_timeout_hit": False,
        "business_summary": "共 1 行。",
        "precheck_warnings": [],
    }
    return ToolMessage(
        content=json.dumps(envelope, ensure_ascii=False), tool_call_id="c1", name="execute_sql"
    )


@when("the redacting saver prepares the message for persistence", target_fixture="redacted_message")
def _redact(live_message: ToolMessage) -> ToolMessage:
    return _redact_tool_message(live_message)


@then("the persisted content contains no verbatim value from the original rows")
def _no_verbatim(live_message: ToolMessage, redacted_message: ToolMessage) -> None:
    original_value = json.loads(live_message.content)["rows"][0]["tenant_id"]
    assert original_value not in redacted_message.content


@then("the persisted envelope carries rows_redacted true and a per-column row_digest")
def _digest_present(redacted_message: ToolMessage) -> None:
    env = json.loads(redacted_message.content)
    assert env["rows_redacted"] is True
    assert env["rows"] == []
    assert isinstance(env["row_digest"], dict) and env["row_digest"]


@then("the redacted message is a different object from the live message")
def _clone(live_message: ToolMessage, redacted_message: ToolMessage) -> None:
    assert redacted_message is not live_message


@then(parsers.parse('the live message still contains the verbatim value "{value}"'))
def _live_untouched(live_message: ToolMessage, value: str) -> None:
    assert value in live_message.content
    assert json.loads(live_message.content)["rows"] == [{"tenant_id": value}]


@then("the persisted envelope retains executed_sql verbatim")
def _executed_sql_retained(live_message: ToolMessage, redacted_message: ToolMessage) -> None:
    original_sql = json.loads(live_message.content)["executed_sql"]
    assert json.loads(redacted_message.content)["executed_sql"] == original_sql
