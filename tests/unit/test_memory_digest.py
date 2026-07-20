"""Unit tests for the at-rest checkpoint digest (capability data-agent.memory-checkpointer, REQ-001)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from mj_agent.memory.digest import digest_rows


def test_digest_per_column_counts() -> None:
    rows = [
        {"tenant_id": 1, "amount": Decimal("10.5")},
        {"tenant_id": 1, "amount": Decimal("20.0")},
        {"tenant_id": 2, "amount": None},
    ]
    d = digest_rows(rows, ["tenant_id", "amount"])
    assert d["tenant_id"] == {"non_null": 3, "distinct": 2}
    assert d["amount"] == {"non_null": 2, "distinct": 2}


def test_digest_is_deterministic() -> None:
    rows = [{"a": 1}, {"a": 2}, {"a": 1}]
    assert digest_rows(rows, ["a"]) == digest_rows(rows, ["a"])


def test_digest_contains_no_verbatim_cell_value() -> None:
    # REQ-001: no verbatim value survives. min/max would be verbatim → excluded; counts only.
    rows = [{"secret": "customer-alpha"}, {"secret": "customer-beta"}]
    d = digest_rows(rows, ["secret"])
    blob = json.dumps(d)
    assert "customer-alpha" not in blob
    assert "customer-beta" not in blob
    assert d["secret"] == {"non_null": 2, "distinct": 2}


def test_digest_counts_columns_absent_from_arg() -> None:
    rows = [{"x": 1, "y": 2}]
    d = digest_rows(rows, ["x"])  # y not in the columns arg but present in a row
    assert "y" in d
    assert d["y"] == {"non_null": 1, "distinct": 1}


def test_digest_empty_rows() -> None:
    assert digest_rows([], ["a"]) == {"a": {"non_null": 0, "distinct": 0}}


def test_digest_handles_date_and_decimal_types() -> None:
    rows = [
        {"d": date(2026, 7, 20)},
        {"d": date(2026, 7, 20)},
        {"d": date(2026, 7, 21)},
    ]
    assert digest_rows(rows, ["d"])["d"] == {"non_null": 3, "distinct": 2}
