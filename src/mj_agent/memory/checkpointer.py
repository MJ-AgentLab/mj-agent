"""LangGraph AsyncPostgresSaver wiring for thread persistence.

Phase 1 sub 1.A — checkpointer goes against a **separate** PostgreSQL
database from the biz domain (per roadmap §4 ``mj_agent_memory``);
credentials are independent so the read-only analyst role used for biz
queries is never asked to write checkpoint rows.

Async variant rationale: the Chainlit entry (`mj_agent.ui`) drives
`graph.astream(...)` end-to-end. LangGraph's async loop awaits
`checkpointer.aget_tuple(...)` inside `__aenter__`; the sync
`PostgresSaver` raises `NotImplementedError` for that method and the
front-end hangs forever. Switching to `AsyncPostgresSaver` +
`AsyncConnectionPool` aligns the saver with the consumer.

Usage::

    from mj_agent.memory import open_checkpointer
    from mj_agent.agent import make_graph

    async with open_checkpointer() as ckpt:
        graph = make_graph(checkpointer=ckpt)
        # ... use graph

The first ``open_checkpointer()`` call invokes
``AsyncPostgresSaver.setup()`` which creates the ``checkpoints`` /
``checkpoint_writes`` / ``checkpoint_blobs`` tables idempotently
(langgraph migrations). ``migrations/001_checkpoint_tables.sql`` is the
schema reference for ops review; the actual DDL is owned by langgraph.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote_plus

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from mj_agent import config as _cfg
from mj_agent.memory.redaction import RedactingAsyncPostgresSaver


def memory_conn_string() -> str:
    """Build the libpq URI for the memory DB.

    Reads dedicated ``MJ_AGENT_MEMORY_HOST/PORT`` (storage-stack PR);
    biz-domain pg credentials are not reused so a hostile checkpointer
    leak cannot reach biz tables. ``settings`` is looked up via the
    module so tests can ``monkeypatch.setattr(config, "settings", ...)``
    to inject overrides.
    """
    s = _cfg.settings
    user = quote_plus(s.mj_agent_memory_user)
    password = quote_plus(s.mj_agent_memory_password.get_secret_value())
    host = s.mj_agent_memory_host
    port = s.mj_agent_memory_port
    db = s.mj_agent_memory_db
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@asynccontextmanager
async def open_checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    """Yield a ready-to-use AsyncPostgresSaver; close pool on exit.

    Tables are created on first invocation (idempotent ``setup()``).
    ``autocommit=True`` + ``prepare_threshold=0`` are langgraph's
    recommended pool kwargs to avoid prepared-statement gotchas in
    long-lived sessions; ``open=False`` + ``async with pool:`` is the
    pattern psycopg_pool 3.2+ wants (the implicit-open path emits a
    deprecation warning).
    """
    conn_string = memory_conn_string()
    pool: AsyncConnectionPool[AsyncConnection[dict[str, Any]]] = AsyncConnectionPool(
        conninfo=conn_string,
        max_size=_cfg.settings.mj_agent_memory_pool_max,
        min_size=1,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        open=False,
    )
    async with pool:
        saver: AsyncPostgresSaver
        if _cfg.settings.mj_agent_memory_redact_biz_rows:
            saver = RedactingAsyncPostgresSaver(pool)
        else:
            saver = AsyncPostgresSaver(pool)
        await saver.setup()
        yield saver
