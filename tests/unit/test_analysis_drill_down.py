"""Unit tests for ``drill_down`` post-processor."""

from __future__ import annotations

import pytest

from mj_agent.tools.analysis import drill_down

ROWS = [
    {"industry": "bank", "tenant_id": "t1", "qrynum": 100},
    {"industry": "bank", "tenant_id": "t2", "qrynum": 200},
    {"industry": "bank", "tenant_id": "t3", "qrynum": 50},
    {"industry": "fintech", "tenant_id": "t4", "qrynum": 300},
    {"industry": "fintech", "tenant_id": "t5", "qrynum": 250},
]


def test_drill_down_global_top_n_descending() -> None:
    r = drill_down(ROWS, metric_column="qrynum", top_n=3)
    assert r["row_count"] == 3
    assert [row["qrynum"] for row in r["rows"]] == [300, 250, 200]


def test_drill_down_ascending() -> None:
    r = drill_down(ROWS, metric_column="qrynum", top_n=2, descending=False)
    assert [row["qrynum"] for row in r["rows"]] == [50, 100]


def test_drill_down_per_dimension() -> None:
    r = drill_down(
        ROWS, metric_column="qrynum", top_n=2, dimension_column="industry"
    )
    by_ind: dict[str, list[int]] = {}
    for row in r["rows"]:
        by_ind.setdefault(row["industry"], []).append(row["qrynum"])
    assert sorted(by_ind["bank"], reverse=True) == [200, 100]
    assert sorted(by_ind["fintech"], reverse=True) == [300, 250]


def test_drill_down_top_n_zero_rejected() -> None:
    with pytest.raises(ValueError, match="top_n must be > 0"):
        drill_down(ROWS, metric_column="qrynum", top_n=0)


def test_drill_down_missing_metric() -> None:
    with pytest.raises(ValueError, match="metric_column 'noexist' not in rows"):
        drill_down(ROWS, metric_column="noexist", top_n=3)


def test_drill_down_handles_none_metric() -> None:
    rows = ROWS + [{"industry": "bank", "tenant_id": "t6", "qrynum": None}]
    r = drill_down(rows, metric_column="qrynum", top_n=3)
    # None should sort last regardless of direction
    assert [row["qrynum"] for row in r["rows"]] == [300, 250, 200]
