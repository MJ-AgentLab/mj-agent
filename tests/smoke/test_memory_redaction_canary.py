"""On-disk both-paths canary + smoke round-trip for the checkpoint redaction.

Capability ``data-agent.memory-checkpointer`` (#365 AC4 + AC5; REQ-001/002/003/004).

The ``memory_db`` fixture returns ``SKIP_POLICY_EXTERNAL_DEPENDENCY`` for every
pytest invocation until a future separately Owner-approved non-biz external
profile exists. Credentials or a running container never enable this module.

The canary reads the raw ``BYTEA`` blobs straight out of ``checkpoint_blobs`` (aput path)
AND ``checkpoint_writes`` (aput_writes path) and asserts a distinctive verbatim cell value
never appears in either — the both-hooks-or-it-leaks guard (same class as ADR-029 #288:
overriding only one write path leaks rows through the other). ``test_plain_saver_leaks_on_
both_paths`` is the negative control: the stock saver DOES persist the value on both paths,
proving the canary genuinely detects a leak rather than passing vacuously.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.base import empty_checkpoint
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

import mj_agent.config as _cfg
from mj_agent.memory.checkpointer import memory_conn_string, open_checkpointer
from mj_agent.memory.redaction import RedactingAsyncPostgresSaver
from mj_agent.runtime import apply_event_loop_policy

# psycopg async needs a SelectorEventLoop on Windows (issue #283). Set the policy at
# import time — before pytest-asyncio creates the test loop — mirroring mj_agent.ui.
apply_event_loop_policy()

pytestmark = [pytest.mark.smoke, pytest.mark.usefixtures("memory_db")]

# The exact SQL kept verbatim in the digested envelope (REQ-003 recoverable-by-refetch).
_SQL = "SELECT tenant_id FROM biz_dws.dws_x WHERE data_date >= '2026-01-01'"
# Distinctive cell values that only surface in the persisted bytes if a verbatim biz value
# leaks through redaction. Deliberately NOT a digest count (avoids the '2'-substring class
# of false positives).
_CANARY = "CANARY-ACME-9973"
_OTHER = "CANARY-BETA-0428"


def _execute_sql_message() -> ToolMessage:
    envelope = {
        "executed_sql": _SQL,
        "columns": ["tenant_id"],
        "rows": [{"tenant_id": _CANARY}, {"tenant_id": _OTHER}],
        "row_count": 2,
        "truncated": False,
        "statement_timeout_hit": False,
        "business_summary": "共 2 行；请基于这些行给出业务化结论。",
        "precheck_warnings": [],
    }
    return ToolMessage(
        content=json.dumps(envelope, ensure_ascii=False), tool_call_id="c1", name="execute_sql"
    )


@asynccontextmanager
async def _pool() -> AsyncIterator[AsyncConnectionPool]:
    pool: AsyncConnectionPool = AsyncConnectionPool(
        conninfo=memory_conn_string(),
        max_size=2,
        min_size=1,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        open=False,
    )
    async with pool:
        yield pool


async def _persist_execute_sql(saver: AsyncPostgresSaver, thread_id: str) -> dict:
    """Persist one execute_sql ToolMessage via BOTH aput (→ checkpoint_blobs) and
    aput_writes (→ checkpoint_writes); return the checkpoint config for read-back.

    ``channel_versions["messages"]`` must equal ``new_versions["messages"]`` so
    ``aget_tuple`` reloads the blob (the on-disk blob is keyed by version).
    """
    checkpoint = empty_checkpoint()
    checkpoint["channel_values"]["messages"] = [_execute_sql_message()]
    checkpoint["channel_versions"]["messages"] = "1"
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    next_config = await saver.aput(config, checkpoint, {}, {"messages": "1"})
    await saver.aput_writes(next_config, [("messages", _execute_sql_message())], task_id="task-1")
    return config


async def _read_raw_blobs(pool: AsyncConnectionPool, thread_id: str) -> tuple[bytes, bytes]:
    """Return the raw concatenated BYTEA from checkpoint_blobs and checkpoint_writes."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute("SELECT blob FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
        blobs = b"".join(r["blob"] for r in await cur.fetchall() if r["blob"])
        await cur.execute("SELECT blob FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
        writes = b"".join(r["blob"] for r in await cur.fetchall() if r["blob"])
    return blobs, writes


@pytest.mark.asyncio
async def test_aput_path_no_verbatim_value() -> None:
    """AC4 — the aput path (checkpoint_blobs) carries no verbatim biz cell value."""
    thread_id = "canary-aput-" + uuid.uuid4().hex
    async with _pool() as pool:
        saver = RedactingAsyncPostgresSaver(pool)
        await saver.setup()
        try:
            await _persist_execute_sql(saver, thread_id)
            blob, _writes = await _read_raw_blobs(pool, thread_id)
        finally:
            await saver.adelete_thread(thread_id)
    assert blob, "checkpoint_blobs blob is empty — nothing was persisted"
    assert _CANARY.encode() not in blob
    assert _OTHER.encode() not in blob
    # the redacted envelope WAS persisted (proves redaction, not a silent drop)
    assert b"rows_redacted" in blob


@pytest.mark.asyncio
async def test_aput_writes_path_no_verbatim_value() -> None:
    """AC4 — the aput_writes path (checkpoint_writes) carries no verbatim biz cell value.

    Both paths are asserted because overriding only one leaks rows through the other.
    """
    thread_id = "canary-writes-" + uuid.uuid4().hex
    async with _pool() as pool:
        saver = RedactingAsyncPostgresSaver(pool)
        await saver.setup()
        try:
            await _persist_execute_sql(saver, thread_id)
            _blob, writes = await _read_raw_blobs(pool, thread_id)
        finally:
            await saver.adelete_thread(thread_id)
    assert writes, "checkpoint_writes blob is empty — nothing was persisted"
    assert _CANARY.encode() not in writes
    assert _OTHER.encode() not in writes
    assert b"rows_redacted" in writes


@pytest.mark.asyncio
async def test_plain_saver_leaks_on_both_paths() -> None:
    """Negative control — the stock AsyncPostgresSaver persists the verbatim value on
    BOTH paths, proving the canary above genuinely detects a leak (guards against a
    false-green where the value would never appear regardless of redaction)."""
    thread_id = "canary-plain-" + uuid.uuid4().hex
    async with _pool() as pool:
        saver = AsyncPostgresSaver(pool)
        await saver.setup()
        try:
            await _persist_execute_sql(saver, thread_id)
            blob, writes = await _read_raw_blobs(pool, thread_id)
        finally:
            await saver.adelete_thread(thread_id)
    assert _CANARY.encode() in blob, "plain saver should leak via aput (checkpoint_blobs)"
    assert _CANARY.encode() in writes, "plain saver should leak via aput_writes (checkpoint_writes)"


@pytest.mark.asyncio
async def test_smoke_round_trip_digested_on_resume() -> None:
    """AC5 — flag-on persist → cross-process resume reads back a digested envelope.

    A fresh saver instance (new process) reloads the thread; the reloaded ToolMessage is
    digested (rows_redacted, empty rows, no verbatim value) with executed_sql retained
    (REQ-003 recoverable-by-refetch).
    """
    thread_id = "smoke-roundtrip-" + uuid.uuid4().hex
    async with _pool() as pool:
        writer = RedactingAsyncPostgresSaver(pool)
        await writer.setup()
        try:
            config = await _persist_execute_sql(writer, thread_id)
            # a fresh saver instance simulates a new process resuming the thread
            reader = RedactingAsyncPostgresSaver(pool)
            tup = await reader.aget_tuple(config)
        finally:
            await writer.adelete_thread(thread_id)
    assert tup is not None
    messages = tup.checkpoint["channel_values"]["messages"]
    envelope = json.loads(messages[0].content)
    assert envelope["rows_redacted"] is True
    assert envelope["rows"] == []
    assert _CANARY not in messages[0].content
    assert _OTHER not in messages[0].content
    assert envelope["executed_sql"] == _SQL  # REQ-003
    assert "row_digest" in envelope


@pytest.mark.asyncio
async def test_open_checkpointer_routing_honors_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """The checkpointer wiring (checkpointer.py) selects the redacting saver iff the flag is on.

    Exercises the actual routing behind the config default this slice flips (default-on): with the
    flag True the live `open_checkpointer()` yields RedactingAsyncPostgresSaver; with it False it
    yields the stock AsyncPostgresSaver. `type(...) is` (not isinstance) distinguishes the subclass.
    """
    monkeypatch.setattr(_cfg.settings, "mj_agent_memory_redact_biz_rows", True)
    async with open_checkpointer() as ckpt:
        assert isinstance(ckpt, RedactingAsyncPostgresSaver)

    monkeypatch.setattr(_cfg.settings, "mj_agent_memory_redact_biz_rows", False)
    async with open_checkpointer() as ckpt:
        assert type(ckpt) is AsyncPostgresSaver  # exact type — Redacting is a subclass
