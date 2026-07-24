"""Real-DB smoke test for memory checkpoint TTL/retention eviction (mechanism C; ADR-038, REQ-005).

Container-gated: hits the dedicated ``mj-agent-postgres`` container and skips cleanly without
``MJ_AGENT_MEMORY_USER`` (``memory_db`` fixture), so CI (no container) does not run it. Run locally
with the storage stack up::

    docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml up -d mj-agent-postgres
    uv run pytest tests/smoke -m smoke -k memory_retention

Proves selective eviction end-to-end, including the SQL ``MAX(checkpoint_id)`` semantics the unit
tests cannot exercise: a thread seeded with BOTH an old and a fresh checkpoint survives (its newest
activity is fresh), while a purely-old thread is fully removed from all three checkpoint tables.
Threads are seeded with crafted uuid6 ids so age is controlled without waiting real time.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import empty_checkpoint
from langgraph.checkpoint.base.id import UUID as _LangGraphUUID
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from mj_agent.memory.checkpointer import memory_conn_string
from mj_agent.memory.redaction import RedactingAsyncPostgresSaver
from mj_agent.memory.retention import _GREGORIAN_UNIX_OFFSET_100NS, evict_stale_threads
from mj_agent.runtime import apply_event_loop_policy

# psycopg async needs a SelectorEventLoop on Windows (issue #283) — set before the test loop.
apply_event_loop_policy()

pytestmark = [pytest.mark.smoke, pytest.mark.usefixtures("memory_db")]

_DAY = 86400.0


def _uuid6_at(epoch: float) -> str:
    """A uuid6 string whose embedded write-time is ``epoch`` (controls a seeded thread's age)."""
    ticks = round(epoch * 1e7) + _GREGORIAN_UNIX_OFFSET_100NS
    raw = (
        (((ticks >> 28) & 0xFFFFFFFF) << 96)
        | (((ticks >> 12) & 0xFFFF) << 80)
        | ((ticks & 0x0FFF) << 64)
        | (0x3FFF << 48)
        | 0x1234567890AB
    )
    return str(_LangGraphUUID(int=raw, version=6))


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


async def _persist(
    saver: AsyncPostgresSaver, thread_id: str, checkpoint_id: str, version: str = "1"
) -> None:
    """Persist one checkpoint with a caller-chosen ``checkpoint_id`` (so age is controllable)."""
    checkpoint = empty_checkpoint()
    checkpoint["id"] = checkpoint_id
    checkpoint["channel_values"]["messages"] = [HumanMessage("hi")]
    checkpoint["channel_versions"]["messages"] = version
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    next_config = await saver.aput(config, checkpoint, {}, {"messages": version})
    await saver.aput_writes(next_config, [("messages", HumanMessage("hi"))], task_id=f"task-{version}")


async def _rowcounts(pool: AsyncConnectionPool, thread_id: str) -> tuple[int, int, int]:
    """(checkpoints, checkpoint_blobs, checkpoint_writes) row counts for a thread."""
    counts: list[int] = []
    async with pool.connection() as conn, conn.cursor() as cur:
        for table in ("checkpoints", "checkpoint_blobs", "checkpoint_writes"):
            await cur.execute(f"SELECT count(*) AS n FROM {table} WHERE thread_id = %s", (thread_id,))
            row = await cur.fetchone()
            counts.append(row["n"] if row else 0)
    return counts[0], counts[1], counts[2]


@pytest.mark.asyncio
async def test_evict_removes_only_stale_threads() -> None:
    """A purely-old thread is fully evicted; a fresh thread and an old+fresh thread survive."""
    now = time.time()
    suffix = uuid.uuid4().hex
    t_old = f"evict-old-{suffix}"
    t_fresh = f"evict-fresh-{suffix}"
    t_mixed = f"evict-mixed-{suffix}"  # old + fresh checkpoints; newest is fresh -> must survive
    async with _pool() as pool:
        saver = RedactingAsyncPostgresSaver(pool)
        await saver.setup()
        try:
            await _persist(saver, t_old, _uuid6_at(now - 100 * _DAY))
            await _persist(saver, t_fresh, _uuid6_at(now - 1 * _DAY))
            await _persist(saver, t_mixed, _uuid6_at(now - 200 * _DAY), version="1")
            await _persist(saver, t_mixed, _uuid6_at(now - 2 * _DAY), version="2")

            assert (await _rowcounts(pool, t_old))[0] >= 1  # sanity: seeded

            result = await evict_stale_threads(
                saver, older_than_seconds=30 * _DAY, now_epoch=now, dry_run=False
            )

            assert t_old in result.stale_thread_ids
            assert t_fresh not in result.stale_thread_ids
            assert t_mixed not in result.stale_thread_ids  # MAX(checkpoint_id) is the fresh one
            # the old thread is gone from ALL THREE tables
            assert await _rowcounts(pool, t_old) == (0, 0, 0)
            # the fresh + mixed threads survive
            assert (await _rowcounts(pool, t_fresh))[0] >= 1
            assert (await _rowcounts(pool, t_mixed))[0] >= 1
        finally:
            for t in (t_old, t_fresh, t_mixed):
                await saver.adelete_thread(t)


@pytest.mark.asyncio
async def test_dry_run_reports_but_deletes_nothing() -> None:
    """Dry-run reports the stale thread yet leaves its rows on disk."""
    now = time.time()
    thread_id = f"evict-dry-{uuid.uuid4().hex}"
    async with _pool() as pool:
        saver = RedactingAsyncPostgresSaver(pool)
        await saver.setup()
        try:
            await _persist(saver, thread_id, _uuid6_at(now - 100 * _DAY))
            result = await evict_stale_threads(
                saver, older_than_seconds=30 * _DAY, now_epoch=now, dry_run=True
            )
            assert thread_id in result.stale_thread_ids
            assert result.evicted == 0
            assert (await _rowcounts(pool, thread_id))[0] >= 1  # still on disk
        finally:
            await saver.adelete_thread(thread_id)
