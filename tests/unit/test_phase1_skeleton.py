"""Phase 1 sub 1.A skeleton sanity — config / memory / agent / cli surfaces."""

from __future__ import annotations

import inspect

from typer.testing import CliRunner

from mj_agent.agent import make_graph
from mj_agent.config import Settings
from mj_agent.memory import memory_conn_string
from mj_agent.server.cli import app


def test_settings_has_phase1_fields() -> None:
    s = Settings()
    assert hasattr(s, "mj_agent_memory_db")
    assert hasattr(s, "mj_agent_memory_user")
    assert hasattr(s, "mj_agent_memory_password")
    assert hasattr(s, "mj_agent_memory_pool_max")
    assert hasattr(s, "chainlit_host")
    assert hasattr(s, "chainlit_port")


def test_settings_default_memory_db_name() -> None:
    s = Settings()
    assert s.mj_agent_memory_db == "mj_agent_memory"
    assert s.mj_agent_memory_pool_max >= 1


def test_settings_default_chainlit_bind() -> None:
    s = Settings()
    assert s.chainlit_host == "127.0.0.1"
    assert s.chainlit_port == 8000


def test_memory_conn_string_assembly(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """memory_conn_string assembles a valid libpq URI (no DB connect).

    storage-stack PR: memory host/port now read from dedicated
    MJ_AGENT_MEMORY_HOST/PORT (decoupled from biz pg).
    """
    monkeypatch.setenv("MJ_AGENT_MEMORY_USER", "memuser")
    monkeypatch.setenv("MJ_AGENT_MEMORY_PASSWORD", "p@ss/word")
    monkeypatch.setenv("MJ_AGENT_MEMORY_DB", "mj_agent_memory")
    monkeypatch.setenv("MJ_AGENT_MEMORY_HOST", "127.0.0.1")
    monkeypatch.setenv("MJ_AGENT_MEMORY_PORT", "5432")
    # Re-instantiate Settings to pick up monkeypatched env (`settings`
    # singleton is module-scoped; bypass by reading via fresh Settings()).
    import mj_agent.config as cfg
    monkeypatch.setattr(cfg, "settings", Settings())

    uri = memory_conn_string()
    assert uri.startswith("postgresql://memuser:")
    assert "@127.0.0.1:5432/mj_agent_memory" in uri
    # special chars must be percent-encoded so libpq parses correctly
    assert "p%40ss%2Fword" in uri


def test_memory_conn_string_independent_of_biz_pg(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """biz pg env vars must NOT leak into memory conn string (storage-stack PR)."""
    monkeypatch.setenv("MJ_AGENT_MEMORY_USER", "memuser")
    monkeypatch.setenv("MJ_AGENT_MEMORY_PASSWORD", "memsecret")
    monkeypatch.setenv("MJ_AGENT_MEMORY_HOST", "memory-host")
    monkeypatch.setenv("MJ_AGENT_MEMORY_PORT", "5433")
    # Set biz pg to an obviously different host/port.
    monkeypatch.setenv("POSTGRES_DEV_HOST", "biz-host-should-not-leak")
    monkeypatch.setenv("POSTGRES_DEV_PORT", "9999")
    monkeypatch.setenv("MJ_CONFIG_PROFILE", "dev")
    import mj_agent.config as cfg
    monkeypatch.setattr(cfg, "settings", Settings())

    uri = memory_conn_string()
    assert "@memory-host:5433/" in uri
    assert "biz-host-should-not-leak" not in uri
    assert "9999" not in uri


def test_make_graph_accepts_checkpointer_kwarg() -> None:
    sig = inspect.signature(make_graph)
    assert "checkpointer" in sig.parameters
    assert sig.parameters["checkpointer"].default is None


def test_cli_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.output
    assert "check" in result.output


def test_cli_check_reports_missing_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """`mj-agent check` exits non-zero with explicit reasons when creds absent."""
    for k in (
        "POSTGRES_ANALYST_USER",
        "ARK_API_KEY",
        "MJ_AGENT_MEMORY_USER",
    ):
        monkeypatch.delenv(k, raising=False)
    import mj_agent.config as cfg
    monkeypatch.setattr(cfg, "settings", Settings())

    runner = CliRunner()
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1
    assert "POSTGRES_ANALYST_USER not set" in result.output
    assert "ARK_API_KEY not set" in result.output
    assert "MJ_AGENT_MEMORY_USER not set" in result.output
