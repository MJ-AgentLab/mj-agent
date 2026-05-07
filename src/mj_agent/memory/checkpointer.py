"""LangGraph PostgresSaver wiring for thread persistence.

Phase 1 sub 1.A — checkpointer goes against a **separate** PostgreSQL
database from the biz domain (per roadmap §4 ``mj_agent_memory``);
credentials are independent so the read-only analyst role used for biz
queries is never asked to write checkpoint rows.

Usage::

    from mj_agent.memory import open_checkpointer
    from mj_agent.agent import make_graph

    with open_checkpointer() as ckpt:
        graph = make_graph(checkpointer=ckpt)
        # ... use graph

The first ``open_checkpointer()`` call invokes ``PostgresSaver.setup()``
which creates the ``checkpoints`` / ``checkpoint_writes`` /
``checkpoint_blobs`` tables idempotently (langgraph migrations).
``migrations/001_checkpoint_tables.sql`` is the schema reference for ops
review; the actual DDL is owned by langgraph.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import quote_plus

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from mj_agent import config as _cfg


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


@contextmanager
def open_checkpointer() -> Iterator[PostgresSaver]:
    """Yield a ready-to-use PostgresSaver; close pool on exit.

    Tables are created on first invocation (idempotent ``setup()``).
    The connection pool autocommit + ``prepare_threshold=0`` are the
    settings langgraph recommends to avoid prepared-statement gotchas in
    long-lived sessions.
    """
    conn_string = memory_conn_string()
    # PostgresSaver needs dict-row connections; the pool generic parameter
    # is set explicitly so the saver's incoming-type expectation lines up
    # with what kwargs={"row_factory": dict_row} actually produces.
    pool: ConnectionPool[Connection[dict[str, Any]]] = ConnectionPool(
        conninfo=conn_string,
        max_size=_cfg.settings.mj_agent_memory_pool_max,
        min_size=1,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )
    with pool:
        saver = PostgresSaver(pool)
        saver.setup()
        yield saver
