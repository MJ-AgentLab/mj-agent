"""Graph-level regression for issue #288 — async tool-call path.

Chainlit (``graph.astream``) and LangGraph Studio drive the agent
asynchronously. With a sync-only ``wrap_tool_call`` middleware, langchain's
factory still routes it into the async chain, whose base
``awrap_tool_call`` raises ``NotImplementedError`` — the graph dies inside
the tools node and the UI spins forever (the #288 incident).

These tests rebuild that exact path with a fake tool-calling model and a
stub tool that raises the same ``ValueError`` family as the L1 guardrail —
no DB, no LLM creds, no checkpointer required. Green means: on BOTH the
sync and async chains, the middleware converts the tool exception into a
``ToolMessage`` and the graph completes with a final AI reply.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from mj_agent.middleware import handle_sql_tool_errors
from mj_agent.middleware.tool_errors import _VALIDATION_PREFIX


@tool
def failing_sql_tool(sql: str) -> str:
    """Stub tool mimicking an L1 guardrail rejection."""
    raise ValueError("SQL rejected by guardrail: schema biz_ods not allowed")


class _FakeToolCallingModel(GenericFakeChatModel):
    """``GenericFakeChatModel`` that tolerates ``bind_tools``.

    ``create_agent`` binds the tool schemas onto the model; the generic fake
    doesn't implement ``bind_tools``, so return ``self`` — the scripted
    message sequence already contains the tool call.
    """

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> Any:
        return self


def _agent() -> Any:
    """One-tool agent whose scripted model calls the failing tool once."""
    model = _FakeToolCallingModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "failing_sql_tool",
                            "args": {"sql": "SELECT 1 FROM biz_ods.t"},
                            "id": "call_1",
                        }
                    ],
                ),
                AIMessage(content="已根据校验错误调整查询。"),
            ]
        )
    )
    return create_agent(
        model=model,
        tools=[failing_sql_tool],
        middleware=[handle_sql_tool_errors],
    )


def _assert_converted(result: dict[str, Any]) -> None:
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert tool_msgs, "expected a ToolMessage from the failing tool"
    assert any(_VALIDATION_PREFIX in str(m.content) for m in tool_msgs)
    final = result["messages"][-1]
    assert isinstance(final, AIMessage)
    assert final.content == "已根据校验错误调整查询。"


@pytest.mark.asyncio
async def test_ainvoke_tool_error_converted_not_raised() -> None:
    """#288 incident path: async run must not die in the tools node."""
    result = await _agent().ainvoke(
        {"messages": [{"role": "user", "content": "查 biz 数据"}]}
    )
    _assert_converted(result)


def test_invoke_tool_error_converted_not_raised() -> None:
    """Sync chain (smoke-test path) must keep working after the fix."""
    result = _agent().invoke(
        {"messages": [{"role": "user", "content": "查 biz 数据"}]}
    )
    _assert_converted(result)
