"""Process-level asyncio runtime helpers (event-loop policy + sync bridge).

Extracted from ``ui.py`` (issue #283) so any *sync* entry point that later
drives psycopg's async mode — Chainlit's import of ``ui.py`` and the
``mj-agent check --live`` CLI probe — applies the same Windows event-loop
policy **before** an event loop is created.

Why this must live outside ``ui.py``: importing ``ui.py`` drags in Chainlit
and applies the policy as an import side effect. The CLI probe needs the same
guard without that dependency, so both call into this module instead.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Coroutine
from typing import Any


def apply_event_loop_policy() -> None:
    """Force ``SelectorEventLoop`` on Windows (issue #283). No-op elsewhere.

    psycopg's async mode cannot run on Windows' default ``ProactorEventLoop`` —
    every connect raises ``InterfaceError`` and an ``AsyncConnectionPool`` dies
    with ``PoolTimeout``. Must run before any event loop is created: import
    time for ``ui.py`` (Chainlit imports it before uvicorn builds the loop),
    and before ``asyncio.run`` for the CLI probe. Idempotent.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    """Apply the event-loop policy, then run ``coro`` to completion.

    The sync -> async bridge for CLI commands: applies the Windows guard first
    so the loop ``asyncio.run`` creates is a ``SelectorEventLoop`` (psycopg-async
    compatible). Not for use inside an already-running event loop.
    """
    apply_event_loop_policy()
    return asyncio.run(coro)
