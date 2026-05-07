"""Unit tests for ``compare_periods`` post-processor."""

from __future__ import annotations

import pytest

from mj_agent.tools.analysis import compare_periods


def test_compare_periods_appends_prev_diff_rate() -> None:
    rows = [
        {"data_date": "2026-04-01", "qrynum": 100},
        {"data_date": "2026-04-02", "qrynum": 120},
        {"data_date": "2026-04-03", "qrynum": 90},
    ]
    r = compare_periods(rows, time_column="data_date", metric_columns=["qrynum"])
    assert r["row_count"] == 3
    out = r["rows"]
    assert out[0]["prev_qrynum"] is None
    assert out[0]["qrynum_diff"] is None
    assert out[1]["prev_qrynum"] == 100
    assert out[1]["qrynum_diff"] == 20
    assert out[1]["qrynum_rate"] == pytest.approx(0.2)
    assert out[2]["qrynum_diff"] == -30
    assert out[2]["qrynum_rate"] == pytest.approx(-0.25)


def test_compare_periods_handles_missing_metric_column() -> None:
    rows = [{"data_date": "2026-04-01", "qrynum": 100}]
    with pytest.raises(ValueError, match="metric 'noexist' not in rows"):
        compare_periods(rows, time_column="data_date", metric_columns=["noexist"])


def test_compare_periods_handles_missing_time_column() -> None:
    rows = [{"data_date": "2026-04-01", "qrynum": 100}]
    with pytest.raises(ValueError, match="time_column 'stat_date' not in rows"):
        compare_periods(rows, time_column="stat_date", metric_columns=["qrynum"])


def test_compare_periods_zero_prev_yields_none_rate() -> None:
    rows = [
        {"data_date": "2026-04-01", "qrynum": 0},
        {"data_date": "2026-04-02", "qrynum": 100},
    ]
    r = compare_periods(rows, time_column="data_date", metric_columns=["qrynum"])
    assert r["rows"][1]["qrynum_diff"] == 100
    assert r["rows"][1]["qrynum_rate"] is None  # divide-by-zero guard


def test_compare_periods_empty_rows() -> None:
    r = compare_periods([], time_column="data_date", metric_columns=["qrynum"])
    assert r["row_count"] == 0
    assert r["rows"] == []
