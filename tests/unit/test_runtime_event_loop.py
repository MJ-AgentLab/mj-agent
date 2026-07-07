"""Unit tests for ``mj_agent.runtime`` — the event-loop guard + sync->async bridge.

The guard was extracted from ``ui.py`` (issue #283) so both Chainlit's import and
the ``mj-agent check --live`` CLI probe apply the same Windows event-loop policy.
See ``test_ui_event_loop_policy.py`` for the ui-import-side-effect regression.
"""

from __future__ import annotations

import asyncio
import sys

import pytest

from mj_agent.runtime import apply_event_loop_policy, run_async


@pytest.fixture()
def _restore_event_loop_policy():
    """Snapshot + restore the process-global policy so tests don't leak."""
    previous = asyncio.get_event_loop_policy()
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(previous)


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_apply_switches_proactor_to_selector_on_windows() -> None:
    if sys.platform != "win32":
        pytest.skip("Windows-only behaviour")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    apply_event_loop_policy()
    assert isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
    )


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_apply_is_noop_off_windows() -> None:
    if sys.platform == "win32":
        pytest.skip("covers non-Windows platforms")
    before = type(asyncio.get_event_loop_policy())
    apply_event_loop_policy()
    assert type(asyncio.get_event_loop_policy()) is before


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_run_async_runs_coroutine_to_completion() -> None:
    async def _echo(value: int) -> int:
        return value

    assert run_async(_echo(5)) == 5


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_run_async_applies_policy_before_running_on_windows() -> None:
    if sys.platform != "win32":
        pytest.skip("Windows-only behaviour")

    async def _noop() -> None:
        return None

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    run_async(_noop())
    assert isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
    )
