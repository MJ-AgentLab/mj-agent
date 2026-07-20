"""Unit tests for RedactingAsyncPostgresSaver's redaction transform.

Capability data-agent.memory-checkpointer (REQ-001/002/004). These are container-free: they
exercise the pure transform (_redact_tool_message / _redact_value / _redact_checkpoint), not the
Postgres persistence — the on-disk both-paths canary + smoke round-trip need the mj-agent-postgres
container and land in the follow-up build step.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from mj_agent.memory.redaction import (
    RedactingAsyncPostgresSaver,
    _redact_tool_message,
    _redact_value,
)


def _execute_sql_msg(rows: list[dict[str, Any]]) -> ToolMessage:
    envelope = {
        "executed_sql": "SELECT tenant_id FROM biz_dws.x WHERE ...",
        "columns": ["tenant_id"],
        "rows": rows,
        "row_count": len(rows),
        "truncated": False,
        "statement_timeout_hit": False,
        "business_summary": "共若干行；请基于这些行向用户给出业务化结论。",
        "precheck_warnings": [],
    }
    return ToolMessage(
        content=json.dumps(envelope, ensure_ascii=False),
        tool_call_id="c1",
        name="execute_sql",
    )


def test_execute_sql_rows_replaced_by_digest() -> None:
    msg = _execute_sql_msg([{"tenant_id": "ACME-CORP"}, {"tenant_id": "BETA-LLC"}])
    red = _redact_tool_message(msg)
    assert red is not msg  # a clone
    # REQ-001: no verbatim biz value survives
    assert "ACME-CORP" not in red.content
    assert "BETA-LLC" not in red.content
    env = json.loads(red.content)
    assert env["rows"] == []
    assert env["rows_redacted"] is True
    assert env["row_digest"]["tenant_id"] == {"non_null": 2, "distinct": 2}
    # REQ-003: executed_sql retained for recoverable-by-refetch
    assert env["executed_sql"] == "SELECT tenant_id FROM biz_dws.x WHERE ..."


def test_error_path_message_untouched() -> None:
    # error-path ToolMessage content is a plain string, not a JSON envelope
    msg = ToolMessage(content="SQL 执行失败：syntax error", tool_call_id="c1", name="execute_sql")
    assert _redact_tool_message(msg) is msg


def test_non_execute_sql_message_untouched() -> None:
    msg = ToolMessage(
        content=json.dumps({"executed_sql": "x", "rows": [], "row_count": 0}),
        tool_call_id="c1",
        name="describe_biz_table",
    )
    assert _redact_tool_message(msg) is msg  # name != execute_sql


def test_non_envelope_message_untouched() -> None:
    # a chart/excel-style envelope lacks the rows/executed_sql/row_count triple
    msg = ToolMessage(
        content=json.dumps({"file_path": "/tmp/x.png", "kind": "chart"}),
        tool_call_id="c1",
        name="execute_sql",
    )
    assert _redact_tool_message(msg) is msg


def test_redaction_is_idempotent() -> None:
    red1 = _redact_tool_message(_execute_sql_msg([{"tenant_id": "ACME"}]))
    red2 = _redact_tool_message(red1)
    assert red2 is red1  # already redacted → unchanged


def test_redact_value_list_unchanged_preserves_identity() -> None:
    msgs = [HumanMessage(content="hi"), AIMessage(content="ok")]
    assert _redact_value(msgs) is msgs  # nothing to redact → same list object


def test_redact_value_list_clones_only_execute_sql() -> None:
    human = HumanMessage(content="q")
    tool = _execute_sql_msg([{"tenant_id": "ACME"}])
    msgs = [human, tool]
    out = _redact_value(msgs)
    assert out is not msgs  # changed → new list
    assert out[0] is human  # untouched message keeps identity
    assert out[1] is not tool  # redacted clone
    assert json.loads(out[1].content)["rows_redacted"] is True
    # REQ-002: original list + message untouched (live in-memory state preserved)
    assert msgs[1] is tool
    assert json.loads(tool.content)["rows"] == [{"tenant_id": "ACME"}]


def test_redact_checkpoint_live_state_untouched() -> None:
    tool = _execute_sql_msg([{"tenant_id": "ACME"}])
    checkpoint = {"channel_values": {"messages": [tool], "step": 1}, "id": "ck-1"}
    red = RedactingAsyncPostgresSaver._redact_checkpoint(checkpoint)  # type: ignore[arg-type]
    assert red is not checkpoint
    assert json.loads(red["channel_values"]["messages"][0].content)["rows_redacted"] is True
    assert red["channel_values"]["step"] == 1
    # original untouched
    assert json.loads(checkpoint["channel_values"]["messages"][0].content)["rows"] == [
        {"tenant_id": "ACME"}
    ]


def test_redact_checkpoint_noop_returns_original() -> None:
    checkpoint = {"channel_values": {"messages": [HumanMessage(content="hi")]}, "id": "ck-2"}
    assert RedactingAsyncPostgresSaver._redact_checkpoint(checkpoint) is checkpoint  # type: ignore[arg-type]
