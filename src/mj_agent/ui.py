"""Chainlit entry point for mj-agent (Phase 1 sub 1.A).

Run::

    chainlit run src/mj_agent/ui.py
    # or
    mj-agent serve

The handlers wrap the existing ``make_graph()`` factory (so MVP's 3 active
skills + 4 tools come along for free) and add:

  - PostgreSQL checkpointer per-thread (so conversations persist across
    page reloads / restarts)
  - per-message streaming of the agent reply
  - LangSmith tracing (auto-enabled when ``LANGSMITH_TRACING=true`` in
    .env via langsmith's standard env hooks; nothing to wire here)

Chainlit re-imports this module in its own subprocess, so we only do
imports + register handlers at module level — no graph build until
``on_chat_start``.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import chainlit as cl
from langchain_core.messages import AIMessage, AIMessageChunk

from mj_agent.agent import make_graph
from mj_agent.config import settings
from mj_agent.memory import open_checkpointer

# Module-level singletons reused across chat sessions in the same process.
_GRAPH: Any | None = None
_CHECKPOINTER_CTX: Any | None = None
_CHECKPOINTER: Any | None = None


def _ensure_langsmith_env() -> None:
    """Mirror pydantic-settings values to LangChain's expected env vars.

    LangSmith reads ``LANGCHAIN_TRACING_V2`` / ``LANGCHAIN_PROJECT`` /
    ``LANGCHAIN_API_KEY`` (the legacy ``LANGCHAIN_*`` family) at import
    time of langchain modules. Our ``.env`` uses the newer
    ``LANGSMITH_*`` family; bridge them so a single env var flips
    tracing on. Idempotent.
    """
    if settings.langsmith_tracing:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.langsmith_endpoint)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
        if settings.langsmith_api_key is not None:
            os.environ.setdefault(
                "LANGCHAIN_API_KEY", settings.langsmith_api_key.get_secret_value()
            )


def _get_or_build_graph() -> Any:
    """Lazy build the graph + checkpointer the first time a chat starts.

    Both are kept at module scope so multiple Chainlit chat sessions
    in the same process reuse one connection pool.
    """
    global _GRAPH, _CHECKPOINTER_CTX, _CHECKPOINTER
    if _GRAPH is not None:
        return _GRAPH
    _ensure_langsmith_env()
    _CHECKPOINTER_CTX = open_checkpointer()
    _CHECKPOINTER = _CHECKPOINTER_CTX.__enter__()
    _GRAPH = make_graph(checkpointer=_CHECKPOINTER)
    return _GRAPH


@cl.on_chat_start
async def on_chat_start() -> None:
    graph = _get_or_build_graph()
    thread_id = str(uuid.uuid4())
    cl.user_session.set("graph", graph)
    cl.user_session.set("thread_id", thread_id)
    await cl.Message(
        content=(
            "👋 你好，我是 mj-agent。可以问我 mj-system biz 域的指标、趋势、Top-N、"
            "同环比等问题；不可访问 `biz_ods.*` / `biz_ads.*` / `ops_*` 与 `biz_dwd` "
            "中除两张维表外的事实表（详见 ADR-006 / ADR-008 数据治理边界）。"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    graph = cl.user_session.get("graph")
    thread_id = cl.user_session.get("thread_id")
    if graph is None or thread_id is None:
        await cl.Message(content="⚠️ 会话尚未初始化，请刷新页面。").send()
        return

    config = {"configurable": {"thread_id": thread_id}}
    reply = cl.Message(content="")
    await reply.send()

    async for stream_mode, chunk in graph.astream(
        {"messages": [{"role": "user", "content": message.content}]},
        config=config,
        stream_mode=["messages", "updates"],
    ):
        if stream_mode == "messages":
            msg_chunk, _meta = chunk
            if isinstance(msg_chunk, AIMessageChunk) and msg_chunk.content:
                token = msg_chunk.content
                if isinstance(token, list):
                    token = "".join(part.get("text", "") for part in token if isinstance(part, dict))
                if token:
                    await reply.stream_token(str(token))
        elif stream_mode == "updates":
            for node, payload in (chunk or {}).items():
                tool_msgs = (payload or {}).get("messages") or []
                for tm in tool_msgs:
                    name = getattr(tm, "name", None)
                    if name:
                        await cl.Message(
                            content=f"🔧 tool `{name}`",
                            author="tools",
                            parent_id=reply.id,
                        ).send()
                del node

    if not reply.content:
        # Graph returned without streaming any AI tokens (e.g. tool-only
        # turn that ended without a final assistant message); fetch the
        # latest state and surface its last AI message.
        snapshot = graph.get_state(config)
        last = next(
            (m for m in reversed(snapshot.values.get("messages", [])) if isinstance(m, AIMessage)),
            None,
        )
        reply.content = (
            last.content if last and isinstance(last.content, str) else "(空回复)"
        )
    await reply.update()


@cl.on_chat_end
async def on_chat_end() -> None:
    # Connection pool is module-scoped; do not close here so subsequent
    # chats reuse it. Process-level cleanup happens at chainlit shutdown.
    return
