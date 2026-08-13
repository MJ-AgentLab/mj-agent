"""Phase 1 sub 1.A skeleton sanity — config / memory / agent / cli surfaces."""

from __future__ import annotations

import inspect

from typer.testing import CliRunner

from mj_agent.agent import make_graph
from mj_agent.config import OFFLINE_TEST_ENV, Settings
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


def test_settings_default_memory_db_name(isolated_settings: Settings) -> None:
    # ``isolated_settings`` (tests/unit/conftest.py) wipes the whole env surface
    # before building Settings, so these default assertions stay hermetic even on
    # a dev machine whose ``.env`` / shell sets ``MJ_AGENT_MEMORY_DB`` (issue #298
    # follow-up: the offline construction seam disables filesystem sources but
    # intentionally still reads ``os.environ``).
    assert isolated_settings.mj_agent_memory_db == "mj_agent_memory"
    assert isolated_settings.mj_agent_memory_pool_max >= 1


def test_settings_default_chainlit_bind(isolated_settings: Settings) -> None:
    # Hermetic via ``isolated_settings`` for the same reason (issue #298 follow-up).
    assert isolated_settings.chainlit_host == "127.0.0.1"
    assert isolated_settings.chainlit_port == 8000


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


def test_cli_check_reports_missing_env(monkeypatch, isolated_settings) -> None:  # type: ignore[no-untyped-def]
    """`mj-agent check` exits non-zero with explicit reasons when creds absent.

    Uses the ``isolated_settings`` fixture (``tests/unit/conftest.py``) so the
    whole mapped OS-variable surface is wiped before ``Settings`` is built.
    The root offline seam already disables dotenv and secrets-directory
    sources; clearing OS variables here closes pydantic's remaining source and
    keeps the expected missing-key report deterministic (issue #298).
    """
    import mj_agent.config as cfg
    monkeypatch.setattr(cfg, "settings", isolated_settings)

    runner = CliRunner()
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1
    assert "POSTGRES_ANALYST_USER not set" in result.output
    assert "ARK_API_KEY not set" in result.output
    assert "MJ_AGENT_MEMORY_USER not set" in result.output


def test_settings_offline_seam_disables_dotenv_and_secrets_dir(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """The offline marker closes both filesystem sources before construction."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MJ_AGENT_MEMORY_DB=leaked-from-dotenv\n"
        "CHAINLIT_PORT=65432\n",
        encoding="utf-8",
    )
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "mj_agent_memory_db").write_text(
        "leaked-from-secrets-dir", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    for k in ("MJ_AGENT_MEMORY_DB", "CHAINLIT_PORT"):
        monkeypatch.delenv(k, raising=False)

    monkeypatch.setenv(OFFLINE_TEST_ENV, "1")
    isolated = Settings(_env_file=env_file, _secrets_dir=secrets_dir)
    assert isolated.mj_agent_memory_db == "mj_agent_memory"
    assert isolated.chainlit_port == 8000


def test_settings_production_entry_keeps_default_dotenv_source(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """Without the pytest marker, the production dotenv behavior is unchanged."""
    (tmp_path / ".env").write_text(
        "MJ_AGENT_MEMORY_DB=synthetic-production-dotenv\n"
        "CHAINLIT_PORT=65432\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(OFFLINE_TEST_ENV, raising=False)
    for key in ("MJ_AGENT_MEMORY_DB", "CHAINLIT_PORT"):
        monkeypatch.delenv(key, raising=False)

    production = Settings()
    assert production.mj_agent_memory_db == "synthetic-production-dotenv"
    assert production.chainlit_port == 65432
