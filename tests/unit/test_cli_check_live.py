"""Unit tests for ``mj-agent check --live`` (issue #290).

Covers the two contracts that keep ``--live`` from becoming a *new* false-green:

1. **SKIP is non-fatal + visible** — with all creds absent every probe SKIPs,
   the exit code is driven only by the base creds failures, and an explicit
   all-skipped WARNING is emitted (a silent all-skip must never look like OK).
2. **Attempted-FAIL gates the exit code** — a probe that raises becomes a FAIL
   row, is surfaced in the output, and forces exit 1 even when base checks pass.

Probes are stubbed at the *function seam* (``cli._probe_*`` / ``cli._memory_sync_ping``)
because ``mj_system_db``/``llm`` bind ``settings`` at import time, so monkeypatching
``config.settings`` alone would not redirect their connections. No network is hit.
"""

from __future__ import annotations

import asyncio

import pytest
from typer.testing import CliRunner

from mj_agent import config as cfg
from mj_agent.config import Settings
from mj_agent.server import cli
from mj_agent.server.cli import app

runner = CliRunner()


@pytest.fixture()
def _restore_event_loop_policy():
    """Restore the process-global loop policy (run_async may set it on Windows)."""
    previous = asyncio.get_event_loop_policy()
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(previous)


def test_check_live_all_creds_absent_skips_all_probes(monkeypatch) -> None:
    for key in (
        "POSTGRES_ANALYST_USER",
        "POSTGRES_ANALYST_PASSWORD",
        "MJ_AGENT_MEMORY_USER",
        "MJ_AGENT_MEMORY_PASSWORD",
        "ARK_API_KEY",
        "LLM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(cfg, "settings", Settings(_env_file=None))

    result = runner.invoke(app, ["check", "--live"])

    # Base creds are absent, so exit 1 as before — unchanged healthcheck contract.
    assert result.exit_code == 1
    # All three live probes SKIP (each row carries a "SKIP (reason)" detail),
    # the tally confirms zero PASS/FAIL, and the all-skip WARNING fires.
    assert result.output.count("SKIP (") == 3
    assert "0 PASS / 3 SKIP / 0 FAIL" in result.output
    assert "all live probes skipped" in result.output


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_check_live_probe_failure_forces_exit_1(monkeypatch) -> None:
    # Base checks all pass (creds present) so the exit code is driven solely by
    # a live probe. Stub the sync memory ping so no real DB is contacted.
    settings = Settings(
        postgres_analyst_user="u",
        postgres_analyst_password="p",
        mj_agent_memory_user="mu",
        mj_agent_memory_password="mp",
        llm_provider="ark",
        ark_api_key="k",
        _env_file=None,
    )
    monkeypatch.setattr(cfg, "settings", settings)
    monkeypatch.setattr(cli, "_memory_sync_ping", lambda _s: None)

    async def _ok_async() -> None:
        return None

    def _boom() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "_probe_memory_async", _ok_async)
    monkeypatch.setattr(cli, "_probe_biz_sync", _boom)
    monkeypatch.setattr(cli, "_probe_llm_sync", lambda: None)

    result = runner.invoke(app, ["check", "--live"])

    assert result.exit_code == 1
    assert "biz db" in result.output
    assert "FAIL" in result.output
    assert "boom" in result.output
    # The non-failing probes still ran and passed.
    assert "async memory" in result.output
    assert "2 PASS / 0 SKIP / 1 FAIL" in result.output


def test_check_without_live_is_unchanged(monkeypatch) -> None:
    """Plain `check` must not run any live probe (Docker healthcheck path)."""
    for key in ("POSTGRES_ANALYST_USER", "ARK_API_KEY", "MJ_AGENT_MEMORY_USER"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(cfg, "settings", Settings(_env_file=None))

    # Any call into a live probe would blow up this sentinel.
    def _fail(*_a, **_k):
        raise AssertionError("live probe ran without --live")

    monkeypatch.setattr(cli, "_run_live_probes", _fail)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    assert "[live]" not in result.output
