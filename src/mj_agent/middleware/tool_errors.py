"""Convert SQL tool exceptions into ``ToolMessage`` so the LLM can self-correct.

The SQL tool chain (``tools/sql/execute.py``, ``tools/sql/introspect.py``)
raises ``ValueError`` on validation rejections (L1 guardrail, L2 precheck,
allowlist) and ``RuntimeError`` on execution failures (60s statement_timeout,
DB errors). LangGraph's default ``ToolNode`` re-raises these — the graph
step fails and the Chainlit UI hangs waiting for a ``ToolMessage`` that
never arrives.

This middleware wraps every tool invocation that flows through the agent
graph and converts those exceptions into ``ToolMessage`` content the LLM
sees as normal tool output. The LLM is then expected to revise its SQL
(add a time predicate, narrow the query, etc.) and retry.

Direct callers of the tool functions (unit / smoke tests, internal code)
still observe the raw exception — the middleware intercepts only the
agent's tool-call path, preserving the existing test contract documented
in ``tests/smoke/test_agent_smoke.py``.

See ADR-029 for the policy rationale and ADR-006 §L1/§L1b for where the
errors originate.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

_VALIDATION_PREFIX = "工具调用未通过校验"
_EXECUTION_PREFIX = "工具执行失败"
_RETRY_HINT = "请根据错误信息调整 SQL 或工具参数后重试。"


def _format_validation_error(exc: ValueError) -> str:
    return f"{_VALIDATION_PREFIX}：{exc}\n{_RETRY_HINT}"


def _format_execution_error(exc: RuntimeError) -> str:
    return f"{_EXECUTION_PREFIX}：{exc}"


def _convert(request: Any, exc: BaseException) -> ToolMessage:
    """Build a ToolMessage from a tool exception, carrying the call id."""
    if isinstance(exc, ValueError):
        content = _format_validation_error(exc)
    elif isinstance(exc, RuntimeError):
        content = _format_execution_error(exc)
    else:
        # Defensive: anything else (TypeError, KeyError, etc.) is a bug in
        # the tool implementation; surface it but don't crash the graph.
        content = f"{_EXECUTION_PREFIX}（意外异常 {type(exc).__name__}）：{exc}"
    return ToolMessage(content=content, tool_call_id=request.tool_call["id"])


@wrap_tool_call
def handle_sql_tool_errors(
    request: Any,
    handler: Callable[[Any], Any],
) -> Any:
    """Sync wrapper — convert ValueError/RuntimeError to ToolMessage."""
    try:
        return handler(request)
    except (ValueError, RuntimeError) as exc:
        return _convert(request, exc)


@wrap_tool_call  # type: ignore[call-overload]
async def ahandle_sql_tool_errors(
    request: Any,
    handler: Callable[[Any], Awaitable[Any]],
) -> Any:
    """Async wrapper — same semantics for ``agraph.astream`` / Chainlit.

    ``wrap_tool_call`` overloads only type-cover sync handlers; the
    decorator's runtime impl branches on ``iscoroutinefunction`` and
    installs this as ``awrap_tool_call`` on the resulting middleware.
    The ``type: ignore`` mirrors the same pattern langchain uses
    internally (``types.py:2015``).
    """
    try:
        return await handler(request)
    except (ValueError, RuntimeError) as exc:
        return _convert(request, exc)
