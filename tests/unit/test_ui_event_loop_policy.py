"""Regression tests for issue #283 — Windows event-loop policy guard in ``ui.py``.

psycopg's async mode cannot run on Windows' default ``ProactorEventLoop``;
the Chainlit entry module must switch the process to
``WindowsSelectorEventLoopPolicy`` before uvicorn creates its event loop,
otherwise ``AsyncPostgresSaver``'s pool never opens a single connection and
``on_chat_start`` dies with ``PoolTimeout`` after 30s.
"""

from __future__ import annotations

import asyncio
import sys

import pytest


@pytest.fixture()
def _restore_event_loop_policy():
    """Snapshot + restore the process-global policy so tests don't leak."""
    previous = asyncio.get_event_loop_policy()
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(previous)


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_importing_ui_applies_selector_policy_on_windows() -> None:
    if sys.platform != "win32":
        pytest.skip("Windows-only import side effect")
    # Reset to the platform default (Proactor on Windows) and force a fresh
    # module exec so the import-time guard actually runs under this test.
    asyncio.set_event_loop_policy(None)
    sys.modules.pop("mj_agent.ui", None)

    import mj_agent.ui  # noqa: F401

    assert isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
    )


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_policy_guard_switches_proactor_to_selector_on_windows() -> None:
    if sys.platform != "win32":
        pytest.skip("Windows-only behaviour")
    from mj_agent.ui import _apply_windows_event_loop_policy

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    _apply_windows_event_loop_policy()
    assert isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
    )


@pytest.mark.usefixtures("_restore_event_loop_policy")
def test_policy_guard_is_noop_off_windows() -> None:
    if sys.platform == "win32":
        pytest.skip("covers non-Windows platforms")
    from mj_agent.ui import _apply_windows_event_loop_policy

    before = type(asyncio.get_event_loop_policy())
    _apply_windows_event_loop_policy()
    assert type(asyncio.get_event_loop_policy()) is before
