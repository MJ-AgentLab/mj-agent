"""execute_sql envelope schema — offline unit tests (safe-sql REQ-005).

`readonly_cursor` is replaced with a fake contextmanager so no DB is contacted;
the SQL still passes the REAL L1 guardrail + L1b precheck (schema-qualified
biz_dws fact table + data_date time predicate + LIMIT), exercising the genuine
execution path up to the cursor boundary.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import pytest

from mj_agent.config import Settings

_ENVELOPE_KEYS = (
    "executed_sql",
    "columns",
    "rows",
    "row_count",
    "truncated",
    "statement_timeout_hit",
    "business_summary",
    "precheck_warnings",
)

# Passes L1 (single SELECT, schema-qualified, allowlisted schema) and L1b
# (no star; data_date is a catalog periods.*.time_column; LIMIT present).
_COMPLIANT_SQL = (
    "SELECT data_date, qry_cnt FROM biz_dws.dws_qcm_qrynum_daily_total "
    "WHERE data_date >= DATE '2026-01-01' LIMIT 10"
)


@dataclass(frozen=True)
class _FakeColumn:
    name: str


class _FakeCursor:
    """Minimal cursor double: description + fetchmany over canned rows."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.description = [_FakeColumn("data_date"), _FakeColumn("qry_cnt")]
        self.executed: list[str] = []

    def execute(self, sql: str) -> None:
        self.executed.append(sql)

    def fetchmany(self, size: int) -> list[dict[str, Any]]:
        return self._rows[:size]


def _install_fake_cursor(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str, Any]],
    *,
    sql_max_rows: int | None = None,
) -> _FakeCursor:
    import mj_agent.tools.sql.execute as execute_mod

    fake = _FakeCursor(rows)

    @contextmanager
    def fake_readonly_cursor() -> Iterator[_FakeCursor]:
        yield fake

    monkeypatch.setattr(execute_mod, "readonly_cursor", fake_readonly_cursor)
    if sql_max_rows is not None:
        monkeypatch.setenv("SQL_MAX_ROWS", str(sql_max_rows))
        monkeypatch.setattr(execute_mod, "settings", Settings(_env_file=None))
    return fake


def _make_rows(n: int) -> list[dict[str, Any]]:
    return [{"data_date": f"2026-01-{i + 1:02d}", "qry_cnt": i} for i in range(n)]


def test_envelope_has_8_required_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    from mj_agent.tools.sql.execute import execute_sql

    _install_fake_cursor(monkeypatch, _make_rows(2))
    envelope = execute_sql(_COMPLIANT_SQL)
    assert set(envelope) == set(_ENVELOPE_KEYS)
    assert len(envelope) == 8


def test_envelope_types(monkeypatch: pytest.MonkeyPatch) -> None:
    from mj_agent.tools.sql.execute import execute_sql

    _install_fake_cursor(monkeypatch, _make_rows(2))
    envelope = execute_sql(_COMPLIANT_SQL)

    assert envelope["executed_sql"] == _COMPLIANT_SQL
    assert envelope["columns"] == ["data_date", "qry_cnt"]
    assert isinstance(envelope["rows"], list)
    assert all(isinstance(row, dict) for row in envelope["rows"])
    assert envelope["row_count"] == 2
    assert envelope["truncated"] is False
    assert envelope["statement_timeout_hit"] is False
    assert isinstance(envelope["business_summary"], str)
    assert envelope["business_summary"]
    assert isinstance(envelope["precheck_warnings"], list)
    assert envelope["precheck_warnings"] == []


def test_envelope_truncated_when_rows_exceed_max(monkeypatch: pytest.MonkeyPatch) -> None:
    """rows are capped at SQL_MAX_ROWS and truncated flips True (fetch is max+1)."""
    from mj_agent.tools.sql.execute import execute_sql

    _install_fake_cursor(monkeypatch, _make_rows(5), sql_max_rows=3)
    envelope = execute_sql(_COMPLIANT_SQL)

    assert envelope["truncated"] is True
    assert envelope["row_count"] == 3
    assert len(envelope["rows"]) == 3
    assert "3" in envelope["business_summary"]


def test_envelope_rejected_sql_never_reaches_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guardrail rejection raises ValueError before the cursor opens (L1-first order)."""
    from mj_agent.tools.sql.execute import execute_sql

    fake = _install_fake_cursor(monkeypatch, _make_rows(1))
    with pytest.raises(ValueError, match="guardrail"):
        execute_sql("DELETE FROM biz_dws.dws_qcm_qrynum_daily_total")
    assert fake.executed == []
