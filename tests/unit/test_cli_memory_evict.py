"""Unit tests for the ``mj-agent memory-evict`` CLI (mechanism C; #386).

Covers the CLI-only glue that guards an IRREVERSIBLE delete: the opt-in gate (TTL <= 0 -> no-op),
the accurate opt-out message when ``--older-than 0`` is passed, the creds-absent SKIP, the
``--older-than`` override of the config default, the days->seconds conversion, and dry-run vs real
message selection. ``open_checkpointer`` + ``evict_stale_threads`` are stubbed at the function seam
(the command imports them lazily) so no DB is touched.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from pydantic import SecretStr
from typer.testing import CliRunner

from mj_agent import config as cfg
from mj_agent.config import Settings
from mj_agent.memory.retention import EvictionResult
from mj_agent.server.cli import app

runner = CliRunner()


@pytest.fixture()
def _restore_event_loop_policy() -> AsyncIterator[None]:
    """Restore the process-global loop policy (run_async may set it on Windows)."""
    previous = asyncio.get_event_loop_policy()
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(previous)


def _creds_settings(isolated_settings: Settings, **overrides: Any) -> Settings:
    return isolated_settings.model_copy(
        update={
            "mj_agent_memory_user": "u",
            "mj_agent_memory_password": SecretStr("p"),
            **overrides,
        }
    )


def _stub_eviction(monkeypatch: pytest.MonkeyPatch, calls: dict[str, Any], *, evicted: int) -> None:
    @asynccontextmanager
    async def _fake_open() -> AsyncIterator[object]:
        yield object()  # dummy saver; evict_stale_threads is stubbed so it is never used

    async def _fake_evict(
        saver: object, *, older_than_seconds: float, now_epoch: float, dry_run: bool = False
    ) -> EvictionResult:
        calls["older_than_seconds"] = older_than_seconds
        calls["dry_run"] = dry_run
        return EvictionResult(
            scanned_threads=3,
            stale_thread_ids=("a", "b"),
            evicted=0 if dry_run else evicted,
            dry_run=dry_run,
            cutoff_epoch=0.0,
        )

    monkeypatch.setattr("mj_agent.memory.open_checkpointer", _fake_open)
    monkeypatch.setattr("mj_agent.memory.retention.evict_stale_threads", _fake_evict)


def test_opt_out_when_ttl_zero_default(monkeypatch: pytest.MonkeyPatch, isolated_settings: Settings) -> None:
    monkeypatch.setattr(cfg, "settings", isolated_settings.model_copy(update={"mj_agent_memory_ttl_days": 0}))
    result = runner.invoke(app, ["memory-evict"])
    assert result.exit_code == 0
    assert "nothing to do (opt-in)" in result.output


def test_opt_out_message_accurate_for_explicit_zero(
    monkeypatch: pytest.MonkeyPatch, isolated_settings: Settings
) -> None:
    # finding #3: an explicit `--older-than 0` must NOT claim "no --older-than".
    monkeypatch.setattr(cfg, "settings", isolated_settings)
    result = runner.invoke(app, ["memory-evict", "--older-than", "0"])
    assert result.exit_code == 0
    assert "nothing to do (opt-in)" in result.output
    assert "no --older-than" not in result.output  # the old misleading wording is gone


def test_creds_absent_skips(monkeypatch: pytest.MonkeyPatch, isolated_settings: Settings) -> None:
    # TTL set via --older-than, but memory creds absent -> SKIP, exit 0, no DB touched.
    monkeypatch.setattr(cfg, "settings", isolated_settings)  # creds wiped by the fixture
    result = runner.invoke(app, ["memory-evict", "--older-than", "30"])
    assert result.exit_code == 0
    assert "SKIP: memory DB credentials absent" in result.output


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_real_run_older_than_overrides_default(
    monkeypatch: pytest.MonkeyPatch, isolated_settings: Settings
) -> None:
    monkeypatch.setattr(cfg, "settings", _creds_settings(isolated_settings, mj_agent_memory_ttl_days=90))
    calls: dict[str, Any] = {}
    _stub_eviction(monkeypatch, calls, evicted=2)

    result = runner.invoke(app, ["memory-evict", "--older-than", "30"])
    assert result.exit_code == 0
    assert calls["older_than_seconds"] == 30 * 86400  # --older-than beats the 90-day default
    assert calls["dry_run"] is False
    assert "evicted 2" in result.output


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_dry_run_threads_flag_and_reports(
    monkeypatch: pytest.MonkeyPatch, isolated_settings: Settings
) -> None:
    monkeypatch.setattr(cfg, "settings", _creds_settings(isolated_settings, mj_agent_memory_ttl_days=90))
    calls: dict[str, Any] = {}
    _stub_eviction(monkeypatch, calls, evicted=2)

    result = runner.invoke(app, ["memory-evict", "--dry-run"])  # no --older-than -> default 90
    assert result.exit_code == 0
    assert calls["dry_run"] is True
    assert calls["older_than_seconds"] == 90 * 86400  # config default used when flag absent
    assert "DRY-RUN" in result.output
    assert "would be evicted" in result.output
