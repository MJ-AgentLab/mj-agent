"""Unit tests for ``mj_agent.middleware.tool_errors``.

The middleware converts ``ValueError`` / ``RuntimeError`` from the SQL
tool chain into ``ToolMessage`` so the LLM can self-correct. We test the
underlying ``_convert`` helper directly with a minimal stub request — no
LLM, no DB, no langgraph runtime required. The integration with
``create_agent`` is exercised by ``tests/smoke`` (when run with creds).

Issue #288 regression: the registered middleware instance must implement
BOTH ``wrap_tool_call`` (sync ``invoke``/``stream``) and ``awrap_tool_call``
(async ``ainvoke``/``astream`` — the Chainlit / Studio path). langchain's
factory routes a middleware that overrides either hook into *both* chains,
so a one-sided middleware raises ``NotImplementedError`` on the other side.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage

from mj_agent.middleware import handle_sql_tool_errors
from mj_agent.middleware.tool_errors import (
    _EXECUTION_PREFIX,
    _RETRY_HINT,
    _VALIDATION_PREFIX,
    _convert,
)


@dataclass
class _StubRequest:
    """Stand-in for ``ToolCallRequest``; only ``tool_call`` is used."""

    tool_call: dict[str, Any]


def _request(call_id: str = "call_abc123") -> _StubRequest:
    return _StubRequest(
        tool_call={"id": call_id, "name": "execute_sql", "args": {"sql": "..."}}
    )


class TestValueErrorConversion:
    def test_precheck_rejection_becomes_tool_message(self) -> None:
        exc = ValueError(
            "SQL rejected by precheck: require_time_range: biz_dws fact "
            "table query has no time-column predicate"
        )
        msg = _convert(_request("call_precheck"), exc)
        assert isinstance(msg, ToolMessage)
        assert msg.tool_call_id == "call_precheck"
        assert _VALIDATION_PREFIX in msg.content
        assert "require_time_range" in msg.content
        assert _RETRY_HINT in msg.content

    def test_guardrail_rejection_preserves_message(self) -> None:
        exc = ValueError("SQL rejected by guardrail: schema biz_ods not allowed")
        msg = _convert(_request("call_guard"), exc)
        assert msg.tool_call_id == "call_guard"
        assert "biz_ods" in msg.content


class TestRuntimeErrorConversion:
    def test_timeout_message_passed_through(self) -> None:
        exc = RuntimeError(
            "查询触发 statement_timeout=60s；请改用聚合（GROUP BY）、"
            "加上更窄的时间范围、或减少 JOIN 数量后重试。"
        )
        msg = _convert(_request("call_timeout"), exc)
        assert msg.tool_call_id == "call_timeout"
        assert _EXECUTION_PREFIX in msg.content
        assert "statement_timeout=60s" in msg.content

    def test_generic_db_error(self) -> None:
        exc = RuntimeError("database error: connection reset")
        msg = _convert(_request(), exc)
        assert "connection reset" in msg.content
        assert _EXECUTION_PREFIX in msg.content


class TestUnexpectedExceptionFallback:
    """Defensive: TypeError/KeyError shouldn't crash the graph either."""

    @pytest.mark.parametrize(
        "exc",
        [
            TypeError("unhashable type"),
            KeyError("missing_field"),
        ],
    )
    def test_other_exceptions_become_messages(self, exc: BaseException) -> None:
        msg = _convert(_request(), exc)
        assert isinstance(msg, ToolMessage)
        assert "意外异常" in msg.content
        assert type(exc).__name__ in msg.content


def _ok_message(call_id: str = "call_abc123") -> ToolMessage:
    return ToolMessage(content="ok", tool_call_id=call_id)


class TestSyncWrapToolCall:
    """The sync hook used by ``invoke`` / ``stream`` (smoke-test path)."""

    def test_value_error_converted(self) -> None:
        def handler(request: Any) -> ToolMessage:
            raise ValueError("SQL rejected by guardrail: schema biz_ods not allowed")

        msg = handle_sql_tool_errors.wrap_tool_call(_request("call_g"), handler)
        assert isinstance(msg, ToolMessage)
        assert msg.tool_call_id == "call_g"
        assert _VALIDATION_PREFIX in msg.content

    def test_runtime_error_converted(self) -> None:
        def handler(request: Any) -> ToolMessage:
            raise RuntimeError("database error: connection reset")

        msg = handle_sql_tool_errors.wrap_tool_call(_request("call_r"), handler)
        assert isinstance(msg, ToolMessage)
        assert _EXECUTION_PREFIX in msg.content

    def test_success_passthrough(self) -> None:
        def handler(request: Any) -> ToolMessage:
            return _ok_message()

        msg = handle_sql_tool_errors.wrap_tool_call(_request(), handler)
        assert isinstance(msg, ToolMessage)
        assert msg.content == "ok"


class TestAsyncAwrapToolCall:
    """The async hook used by ``ainvoke`` / ``astream`` (Chainlit / Studio path).

    Issue #288: these raised ``NotImplementedError`` because only the sync
    hook was registered — the exact failure that froze the Chainlit UI.
    """

    @pytest.mark.asyncio
    async def test_value_error_converted(self) -> None:
        async def handler(request: Any) -> ToolMessage:
            raise ValueError("SQL rejected by precheck: require_time_range")

        msg = await handle_sql_tool_errors.awrap_tool_call(_request("call_a"), handler)
        assert isinstance(msg, ToolMessage)
        assert msg.tool_call_id == "call_a"
        assert _VALIDATION_PREFIX in msg.content
        assert _RETRY_HINT in msg.content

    @pytest.mark.asyncio
    async def test_runtime_error_converted(self) -> None:
        async def handler(request: Any) -> ToolMessage:
            raise RuntimeError("查询触发 statement_timeout=60s")

        msg = await handle_sql_tool_errors.awrap_tool_call(_request("call_t"), handler)
        assert isinstance(msg, ToolMessage)
        assert _EXECUTION_PREFIX in msg.content

    @pytest.mark.asyncio
    async def test_success_passthrough(self) -> None:
        async def handler(request: Any) -> ToolMessage:
            return _ok_message()

        msg = await handle_sql_tool_errors.awrap_tool_call(_request(), handler)
        assert isinstance(msg, ToolMessage)
        assert msg.content == "ok"


class TestBothHooksOverridden:
    """Issue #288 registration pin: the registered instance must override
    BOTH hooks — langchain routes it into both chains regardless, and the
    non-overridden side raises ``NotImplementedError`` at runtime."""

    def test_sync_hook_overridden(self) -> None:
        assert (
            type(handle_sql_tool_errors).wrap_tool_call
            is not AgentMiddleware.wrap_tool_call
        )

    def test_async_hook_overridden(self) -> None:
        assert (
            type(handle_sql_tool_errors).awrap_tool_call
            is not AgentMiddleware.awrap_tool_call
        )
