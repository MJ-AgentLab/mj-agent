"""Smoke test — ``mj-agent check --live`` end to end (issue #290).

Run with: ``uv run pytest tests/smoke -m smoke -k check_live``. Gated by the
``live_db`` fixture (biz analyst creds present) plus a memory-creds guard.

On a Windows dev box this is the CLI-level regression gate for issue #283: the
``async memory`` probe passes only because ``mj_agent.runtime`` switched the
process to a SelectorEventLoop. Regress that guard and this probe FAILs here.
"""

from __future__ import annotations

import os

import pytest
from typer.testing import CliRunner

from mj_agent.server.cli import app

pytestmark = [pytest.mark.smoke, pytest.mark.usefixtures("live_db")]

runner = CliRunner()


def test_check_live_end_to_end() -> None:
    if not os.environ.get("MJ_AGENT_MEMORY_USER"):
        pytest.skip("MJ_AGENT_MEMORY_USER not set — skipping async-memory probe")

    result = runner.invoke(app, ["check", "--live"])

    assert result.exit_code == 0, result.output
    # The async checkpointer path (issue #283 catcher) must pass.
    assert "async memory" in result.output
    assert "0 FAIL" in result.output
    assert "FAIL" not in result.output
