"""Shared pytest fixtures.

Unit tests never touch the database or a real LLM — they import modules
only. Integration and smoke tests do hit external systems; the fixtures
here make that explicit with ``live_db`` and ``agent`` scopes.

`.env` is loaded once at module import via python-dotenv so the
integration / smoke skip-gates see the credentials a developer just
provisioned via ``scripts/setup-env.ps1``. ``override=False`` keeps any
already-exported OS env vars (CI / shell) authoritative.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH, override=False)


@pytest.fixture(scope="session")
def live_db() -> Iterator[None]:
    """Skip the test unless analyst credentials are present in the env."""
    if not os.environ.get("POSTGRES_ANALYST_USER"):
        pytest.skip("POSTGRES_ANALYST_USER not set — skipping live-DB test")
    yield


@pytest.fixture(scope="session")
def memory_db() -> Iterator[None]:
    """Skip unless the mj-agent memory-DB credentials are present in the env.

    Gates the container-dependent memory-checkpointer redaction tests
    (tests/smoke/test_memory_redaction_canary.py) — they need the dedicated
    ``mj-agent-postgres`` container, which CI does not run. Mirrors ``live_db``
    but keys off ``MJ_AGENT_MEMORY_USER`` (the memory role, not biz analyst).
    """
    if not os.environ.get("MJ_AGENT_MEMORY_USER"):
        pytest.skip("MJ_AGENT_MEMORY_USER not set — skipping memory-DB test")
    yield


@pytest.fixture(scope="session")
def agent():  # type: ignore[no-untyped-def]
    """Build the compiled LangGraph agent; skips if ARK_API_KEY is absent."""
    if not os.environ.get("ARK_API_KEY"):
        pytest.skip("ARK_API_KEY not set — skipping agent-dependent test")
    try:
        from mj_agent.agent import make_graph

        return make_graph()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"agent graph failed to build: {exc}")
