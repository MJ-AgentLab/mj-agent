"""TTL/retention eviction for the memory checkpointer (mechanism C; ADR-038).

Capability ``data-agent.memory-checkpointer`` (REQ-005; ADR-038 mechanism **C** — the optional
TTL stack-on on top of mechanism B's persist-time digest). Deletes whole checkpoint *threads*
whose most-recent activity is older than a TTL, bounding how long the at-rest residual lives in
the ``mj_agent_memory`` DB — including the answer-side biz values echoed in ``AIMessage`` natural
language that mechanism B's row-digest deliberately does NOT cover (ADR-038 negative limitation #1).

OPT-IN + irreversible: eviction only happens when ``mj-agent memory-evict`` is run with a positive
TTL (``MJ_AGENT_MEMORY_TTL_DAYS`` or ``--older-than``). Deletion is a hard DELETE via langgraph's
``adelete_thread`` (``checkpoints`` + ``checkpoint_blobs`` + ``checkpoint_writes``); always
``--dry-run`` first. Default-off because eviction is destructive — unlike mechanism B's
non-destructive forward digest, which shipped default-on.

Thread age comes from the langgraph uuid6 ``checkpoint_id`` (time-ordered), so no schema change and
no ``created_at`` column are needed. The extraction matches langgraph's own ``UUID.time`` — pinned
against langgraph 1.1.8 in ``tests/unit/test_memory_retention.py``.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)

# 100-ns intervals between the UUID Gregorian epoch (1582-10-15) and the Unix epoch
# (1970-01-01). UUIDv6, like v1, counts 100-ns ticks from the Gregorian epoch.
_GREGORIAN_UNIX_OFFSET_100NS = 0x01B21DD213814000  # == 122_192_928_000_000_000


def checkpoint_id_epoch_seconds(checkpoint_id: str) -> float:
    """Unix epoch seconds encoded in a langgraph uuid6 ``checkpoint_id`` (its write time).

    Pure. UUIDv6 packs a 60-bit 100-ns Gregorian timestamp; reconstruct it from the standard
    ``time_low`` / ``time_mid`` / ``time_hi_version`` fields (v6 layout — verified byte-identical to
    langgraph's ``UUID.time`` in the unit tests) and shift to the Unix epoch. Raises ``ValueError``
    on a non-uuid6 id so a stray v4 thread id can never be mis-aged into an eviction.
    """
    parsed = uuid.UUID(checkpoint_id)
    if parsed.version != 6:
        raise ValueError(
            f"checkpoint_id is not a uuid6 (version={parsed.version}): {checkpoint_id!r}"
        )
    ticks = (
        (parsed.time_low << 28) | (parsed.time_mid << 12) | (parsed.time_hi_version & 0x0FFF)
    )
    return (ticks - _GREGORIAN_UNIX_OFFSET_100NS) / 1e7


@dataclass(frozen=True)
class EvictionResult:
    """Outcome of one eviction pass. ``evicted`` is 0 on a dry run."""

    scanned_threads: int
    stale_thread_ids: tuple[str, ...]
    evicted: int
    dry_run: bool
    cutoff_epoch: float


async def _thread_latest_epochs(saver: AsyncPostgresSaver) -> list[tuple[str, float]]:
    """``(thread_id, newest-activity epoch)`` for every thread in the memory DB.

    Newest activity = the max uuid6 ``checkpoint_id`` per thread. uuid6's canonical string form
    sorts lexicographically by time (the time bits are the most significant hex, version nibble is
    constant), so SQL ``MAX(checkpoint_id)`` yields the thread's latest checkpoint across all
    namespaces. Uses the saver's own cursor — the same internal path ``adelete_thread`` uses.
    """
    async with saver._cursor() as cur:
        await cur.execute(
            "SELECT thread_id, MAX(checkpoint_id) AS latest "
            "FROM checkpoints GROUP BY thread_id"
        )
        rows = await cur.fetchall()
    latest: list[tuple[str, float]] = []
    for row in rows:
        checkpoint_id = row["latest"]
        if checkpoint_id is None:
            continue
        try:
            latest.append((row["thread_id"], checkpoint_id_epoch_seconds(checkpoint_id)))
        except ValueError:
            # A non-uuid6 id (corrupt / hand-inserted / a future langgraph uuid7-8) must not
            # abort the whole pass — skip that one thread so retention still runs for the rest.
            # Fail-safe: an un-aged thread is simply never evicted.
            logger.warning(
                "memory-evict: thread %s has a non-uuid6 checkpoint_id %r; skipping (never evicted)",
                row["thread_id"],
                checkpoint_id,
            )
    return latest


async def _latest_epoch(saver: AsyncPostgresSaver, thread_id: str) -> float | None:
    """Newest-activity epoch for a single thread, or None if it has no (uuid6) checkpoints.

    Used to re-check a thread's age immediately before deleting it (TOCTOU mitigation).
    """
    async with saver._cursor() as cur:
        await cur.execute(
            "SELECT MAX(checkpoint_id) AS latest FROM checkpoints WHERE thread_id = %s",
            (thread_id,),
        )
        row = await cur.fetchone()
    checkpoint_id = row["latest"] if row else None
    if checkpoint_id is None:
        return None
    try:
        return checkpoint_id_epoch_seconds(checkpoint_id)
    except ValueError:
        return None


async def stale_thread_ids(
    saver: AsyncPostgresSaver, *, older_than_seconds: float, now_epoch: float
) -> list[str]:
    """Thread ids whose newest activity is strictly older than ``now_epoch - older_than_seconds``.

    Strict ``<`` so a thread aged exactly at the cutoff is retained, not evicted.
    """
    cutoff = now_epoch - older_than_seconds
    return [tid for tid, ts in await _thread_latest_epochs(saver) if ts < cutoff]


async def evict_stale_threads(
    saver: AsyncPostgresSaver,
    *,
    older_than_seconds: float,
    now_epoch: float,
    dry_run: bool = False,
) -> EvictionResult:
    """Delete every thread older than the TTL — or, on ``dry_run``, only report them.

    Deletion goes through langgraph's ``adelete_thread`` (checkpoints + checkpoint_blobs +
    checkpoint_writes for the thread). **IRREVERSIBLE.**

    TOCTOU mitigation: ``adelete_thread`` wipes a whole thread with no age predicate, so a thread
    that was stale at scan time but receives a fresh checkpoint before its delete would lose that
    write. Each thread's age is therefore **re-checked immediately before its delete** and skipped
    if it is no longer stale — shrinking (not fully closing) the window. For a hard guarantee run
    eviction while the app is quiescent (see runbook §6); durable resume is not shipped today.
    ``evicted`` may be less than ``len(stale_thread_ids)`` when a thread is skipped this way.
    """
    latest = await _thread_latest_epochs(saver)
    cutoff = now_epoch - older_than_seconds
    stale = tuple(tid for tid, ts in latest if ts < cutoff)
    evicted = 0
    if not dry_run:
        for tid in stale:
            recheck = await _latest_epoch(saver, tid)
            if recheck is None or recheck >= cutoff:
                # raced fresh (or already gone) since the scan — do not wipe a now-active thread
                logger.warning(
                    "memory-evict: thread %s is no longer stale (fresh activity since scan); skipping",
                    tid,
                )
                continue
            await saver.adelete_thread(tid)
            evicted += 1
    return EvictionResult(
        scanned_threads=len(latest),
        stale_thread_ids=stale,
        evicted=evicted,
        dry_run=dry_run,
        cutoff_epoch=cutoff,
    )
