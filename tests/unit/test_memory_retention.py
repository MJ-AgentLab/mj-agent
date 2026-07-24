"""Unit tests for memory checkpoint TTL/retention eviction (mechanism C; ADR-038, REQ-005).

Container-free: the pure uuid6 -> epoch extraction plus the eviction control-flow driven through a
fake saver (no Postgres). The real-DB selective-eviction proof (incl. that SQL ``MAX`` picks a
thread's newest checkpoint) lands in ``tests/smoke/test_memory_retention_smoke.py``.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from langgraph.checkpoint.base.id import UUID as _LangGraphUUID
from langgraph.checkpoint.base.id import uuid6

from mj_agent.memory.retention import (
    _GREGORIAN_UNIX_OFFSET_100NS,
    EvictionResult,
    checkpoint_id_epoch_seconds,
    evict_stale_threads,
    stale_thread_ids,
)

_DAY = 86400.0


def _uuid6_at(epoch: float) -> str:
    """A uuid6 string whose embedded write-time is ``epoch`` (test builder for aged threads).

    Places the 60-bit timestamp into the v6 field positions; ``UUID(int=..., version=6)`` then
    stamps the version + variant bits (leaving the time bits intact), so it round-trips through
    ``checkpoint_id_epoch_seconds``.
    """
    ticks = round(epoch * 1e7) + _GREGORIAN_UNIX_OFFSET_100NS
    time_low = (ticks >> 28) & 0xFFFFFFFF
    time_mid = (ticks >> 12) & 0xFFFF
    time_hi = ticks & 0x0FFF
    node = 0x1234567890AB
    clock_seq = 0x3FFF
    raw = (time_low << 96) | (time_mid << 80) | (time_hi << 64) | (clock_seq << 48) | node
    # stdlib uuid.UUID rejects version=6; langgraph's subclass permits v6-8 and stamps the
    # version + RFC-4122 variant bits (leaving the time bits intact) — the same class that mints
    # real checkpoint_ids.
    return str(_LangGraphUUID(int=raw, version=6))


# ----- checkpoint_id_epoch_seconds (pure) -----


def test_epoch_matches_langgraph_uuid6_time() -> None:
    """The stdlib extraction agrees with langgraph's own UUID.time (pin-verify vs langgraph 1.1.8)."""
    u = uuid6()
    expected = (u.time - _GREGORIAN_UNIX_OFFSET_100NS) / 1e7
    assert checkpoint_id_epoch_seconds(str(u)) == pytest.approx(expected)


def test_epoch_close_to_generation_time() -> None:
    before = time.time()
    u = uuid6()
    got = checkpoint_id_epoch_seconds(str(u))
    after = time.time()
    assert before - 1 <= got <= after + 1


def test_uuid6_at_builder_round_trips() -> None:
    epoch = 1_700_000_000.0
    assert checkpoint_id_epoch_seconds(_uuid6_at(epoch)) == pytest.approx(epoch, abs=1e-3)


def test_epoch_rejects_non_uuid6() -> None:
    with pytest.raises(ValueError, match="not a uuid6"):
        checkpoint_id_epoch_seconds(str(uuid.uuid4()))


# ----- eviction control-flow via a fake saver -----


class _FakeCursor:
    def __init__(self, scan: dict[str, str], recheck: dict[str, str]) -> None:
        self._scan = scan
        self._recheck = recheck
        self._params: Any = None

    async def execute(self, sql: str, params: Any = None) -> None:
        self._params = params

    async def fetchall(self) -> list[dict[str, Any]]:
        # the GROUP BY scan query (no params)
        return [{"thread_id": t, "latest": c} for t, c in self._scan.items()]

    async def fetchone(self) -> dict[str, Any] | None:
        # the per-thread re-check query: params == (thread_id,)
        tid = self._params[0] if self._params else None
        return {"latest": self._recheck.get(tid)}


class _FakeSaver:
    """Mimics the saver surfaces retention.py touches: ``_cursor()`` (fetchall for the GROUP BY
    scan + fetchone for the per-thread re-check) + ``adelete_thread()``. ``recheck_latest`` lets a
    test simulate a TOCTOU race where a thread's delete-time age differs from its scan-time age."""

    def __init__(
        self, scan_latest: dict[str, str], recheck_latest: dict[str, str] | None = None
    ) -> None:
        self._scan = dict(scan_latest)
        self._recheck = dict(recheck_latest) if recheck_latest is not None else dict(scan_latest)
        self.deleted: list[str] = []

    @asynccontextmanager
    async def _cursor(self, *, pipeline: bool = False) -> AsyncIterator[_FakeCursor]:
        yield _FakeCursor(self._scan, self._recheck)

    async def adelete_thread(self, thread_id: str) -> None:
        self.deleted.append(thread_id)


@pytest.mark.asyncio
async def test_evict_deletes_only_stale_threads() -> None:
    now = 1_000_000_000.0
    saver = _FakeSaver(
        {"old-thread": _uuid6_at(now - 100 * _DAY), "fresh-thread": _uuid6_at(now - 1 * _DAY)}
    )
    res = await evict_stale_threads(
        saver, older_than_seconds=30 * _DAY, now_epoch=now, dry_run=False  # type: ignore[arg-type]
    )
    assert saver.deleted == ["old-thread"]  # fresh-thread untouched
    assert res.evicted == 1
    assert res.scanned_threads == 2
    assert res.stale_thread_ids == ("old-thread",)
    assert res.dry_run is False
    assert isinstance(res, EvictionResult)


@pytest.mark.asyncio
async def test_dry_run_deletes_nothing() -> None:
    now = 1_000_000_000.0
    saver = _FakeSaver({"old-thread": _uuid6_at(now - 100 * _DAY)})
    res = await evict_stale_threads(
        saver, older_than_seconds=30 * _DAY, now_epoch=now, dry_run=True  # type: ignore[arg-type]
    )
    assert saver.deleted == []  # nothing deleted on dry-run
    assert res.evicted == 0
    assert res.stale_thread_ids == ("old-thread",)  # but still reported
    assert res.dry_run is True


@pytest.mark.asyncio
async def test_stale_boundary_is_strict() -> None:
    now = 1_000_000_000.0
    ttl = 30 * _DAY
    saver = _FakeSaver(
        {"just-old": _uuid6_at(now - ttl - 60), "just-new": _uuid6_at(now - ttl + 60)}
    )
    ids = await stale_thread_ids(saver, older_than_seconds=ttl, now_epoch=now)  # type: ignore[arg-type]
    assert ids == ["just-old"]  # exactly-at-cutoff side is retained (strict <)


@pytest.mark.asyncio
async def test_empty_db_scans_zero() -> None:
    saver = _FakeSaver({})
    res = await evict_stale_threads(
        saver, older_than_seconds=_DAY, now_epoch=1_000_000_000.0  # type: ignore[arg-type]
    )
    assert res.scanned_threads == 0
    assert res.stale_thread_ids == ()
    assert res.evicted == 0


@pytest.mark.asyncio
async def test_non_uuid6_row_skipped_not_whole_pass_aborted() -> None:
    # A corrupt / non-uuid6 checkpoint_id must not crash the pass — the rest still evicts.
    now = 1_000_000_000.0
    saver = _FakeSaver({"good": _uuid6_at(now - 100 * _DAY), "corrupt": str(uuid.uuid4())})
    res = await evict_stale_threads(
        saver, older_than_seconds=30 * _DAY, now_epoch=now, dry_run=False  # type: ignore[arg-type]
    )
    assert saver.deleted == ["good"]  # corrupt id skipped (never aged), not a ValueError crash
    assert res.scanned_threads == 1   # the corrupt row is excluded from the aged set


@pytest.mark.asyncio
async def test_raced_fresh_thread_skipped_at_delete() -> None:
    # Stale at scan, but a fresh checkpoint lands before the delete: the re-check sees it fresh
    # and the thread is NOT wiped (TOCTOU mitigation).
    now = 1_000_000_000.0
    saver = _FakeSaver(
        {"raced": _uuid6_at(now - 100 * _DAY)},
        recheck_latest={"raced": _uuid6_at(now - 1 * _DAY)},
    )
    res = await evict_stale_threads(
        saver, older_than_seconds=30 * _DAY, now_epoch=now, dry_run=False  # type: ignore[arg-type]
    )
    assert saver.deleted == []                  # not wiped — active again
    assert res.stale_thread_ids == ("raced",)   # still reported as stale-at-scan
    assert res.evicted == 0                      # but not evicted
