"""Unit tests for ``aggregate`` post-processor."""

from __future__ import annotations

import pytest

from mj_agent.tools.analysis import aggregate

ROWS = [
    {"industry": "bank", "tenant_id": "t1", "qrynum": 100},
    {"industry": "bank", "tenant_id": "t2", "qrynum": 200},
    {"industry": "fintech", "tenant_id": "t3", "qrynum": 50},
    {"industry": "fintech", "tenant_id": "t4", "qrynum": 150},
    {"industry": "fintech", "tenant_id": "t5", "qrynum": None},
]


def test_aggregate_sum_by_industry() -> None:
    r = aggregate(ROWS, group_by=["industry"], aggregations={"qrynum": "sum"})
    assert r["row_count"] == 2
    assert r["input_row_count"] == 5
    assert r["compression_ratio"] == 2.5
    by_ind = {row["industry"]: row["sum_qrynum"] for row in r["rows"]}
    assert by_ind == {"bank": 300, "fintech": 200}


def test_aggregate_avg_handles_nulls() -> None:
    r = aggregate(ROWS, group_by=["industry"], aggregations={"qrynum": "avg"})
    by_ind = {row["industry"]: row["avg_qrynum"] for row in r["rows"]}
    # bank: (100+200)/2 = 150 ; fintech: (50+150)/2 = 100 (None ignored)
    assert by_ind == {"bank": 150, "fintech": 100}


def test_aggregate_count_min_max() -> None:
    r = aggregate(
        ROWS,
        group_by=["industry"],
        aggregations={"qrynum": "count", "tenant_id": "count"},
    )
    by_ind = {row["industry"]: row for row in r["rows"]}
    assert by_ind["bank"]["count_qrynum"] == 2
    assert by_ind["fintech"]["count_qrynum"] == 2  # None filtered


def test_aggregate_unknown_function_rejected() -> None:
    with pytest.raises(ValueError, match="unknown aggregation"):
        aggregate(ROWS, group_by=["industry"], aggregations={"qrynum": "median"})


def test_aggregate_missing_column_rejected() -> None:
    with pytest.raises(ValueError, match="column 'noexist' missing"):
        aggregate(ROWS, group_by=["noexist"], aggregations={"qrynum": "sum"})


def test_aggregate_empty_rows() -> None:
    r = aggregate([], group_by=["industry"], aggregations={"qrynum": "sum"})
    assert r["row_count"] == 0
    assert r["compression_ratio"] == 1.0
