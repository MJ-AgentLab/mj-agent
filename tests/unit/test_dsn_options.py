"""_dsn() read-only DSN options — offline unit tests (safe-sql REQ-003, ADR-006 L3).

No DB connect: `_dsn()` is pure string assembly. A fresh Settings built from
monkeypatched env is installed on mj_agent.integrations.mj_system_db so the
module-level `settings` reference (bound at import) is bypassed.
"""

from __future__ import annotations

import pytest

from mj_agent.config import Settings


def _dsn_with_test_settings(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("POSTGRES_ANALYST_USER", "analyst_test")
    monkeypatch.setenv("POSTGRES_ANALYST_PASSWORD", "test-password")
    monkeypatch.setenv("POSTGRES_BIZ_DB", "mj_system_db")
    monkeypatch.setenv("MJ_CONFIG_PROFILE", "dev")
    monkeypatch.setenv("POSTGRES_DEV_HOST", "127.0.0.1")
    monkeypatch.setenv("POSTGRES_DEV_PORT", "5432")
    import mj_agent.integrations.mj_system_db as db_mod
    monkeypatch.setattr(db_mod, "settings", Settings(_env_file=None))
    return db_mod._dsn()


def test_dsn_contains_default_transaction_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L3 read-only enforcement: any non-SELECT rejected at the transaction level."""
    assert "default_transaction_read_only=on" in _dsn_with_test_settings(monkeypatch)


def test_dsn_contains_lock_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Client-side lock_timeout guards against rogue lock waits (5s)."""
    assert "lock_timeout=5000" in _dsn_with_test_settings(monkeypatch)


def test_dsn_contains_idle_in_transaction_session_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Idle-in-transaction sessions are reaped after 10s (pool hygiene)."""
    assert "idle_in_transaction_session_timeout=10000" in _dsn_with_test_settings(monkeypatch)


def test_dsn_contains_application_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """application_name=mj-agent makes analyst sessions attributable in pg_stat_activity."""
    assert "application_name=mj-agent" in _dsn_with_test_settings(monkeypatch)


def test_dsn_pins_analyst_credentials_and_profile_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DSN carries the analyst RO role + profile-selected host/port/db."""
    dsn = _dsn_with_test_settings(monkeypatch)
    assert "user=analyst_test" in dsn
    assert "host=127.0.0.1" in dsn
    assert "port=5432" in dsn
    assert "dbname=mj_system_db" in dsn
