"""Unit tests for ``detect_anomaly`` post-processor."""

from __future__ import annotations

import pytest

from mj_agent.tools.analysis import detect_anomaly


def test_iqr_flags_outliers() -> None:
    rows = [
        {"data_date": f"2026-04-{i:02d}", "qrynum": v}
        for i, v in enumerate([100, 110, 105, 120, 95, 115, 5000, 100], start=1)
    ]
    r = detect_anomaly(rows, metric_column="qrynum", method="iqr", threshold=1.5)
    flagged = [row for row in r["rows"] if row["is_anomaly"]]
    assert any(row["qrynum"] == 5000 for row in flagged)
    assert r["anomaly_count"] >= 1
    assert r["method"] == "iqr"
    assert "iqr" in r["stats"]


def test_zscore_flags_outliers() -> None:
    rows = [
        {"data_date": f"2026-04-{i:02d}", "qrynum": v}
        for i, v in enumerate([100, 110, 105, 120, 95, 115, 500, 100], start=1)
    ]
    r = detect_anomaly(
        rows, metric_column="qrynum", method="zscore", threshold=2.0
    )
    assert r["method"] == "zscore"
    assert "stdev" in r["stats"]
    flagged = [row for row in r["rows"] if row["is_anomaly"]]
    assert any(row["qrynum"] == 500 for row in flagged)


def test_unknown_method_rejected() -> None:
    rows = [{"qrynum": 100}, {"qrynum": 200}, {"qrynum": 150}, {"qrynum": 175}]
    with pytest.raises(ValueError, match="unknown method"):
        detect_anomaly(rows, metric_column="qrynum", method="madness")  # type: ignore[arg-type]


def test_too_few_values_rejected() -> None:
    rows = [{"qrynum": 100}, {"qrynum": 200}]
    with pytest.raises(ValueError, match="need ≥ 4"):
        detect_anomaly(rows, metric_column="qrynum")


def test_missing_column_rejected() -> None:
    rows = [{"qrynum": v} for v in (100, 200, 150, 175)]
    with pytest.raises(ValueError, match="metric_column 'missing' not in rows"):
        detect_anomaly(rows, metric_column="missing")


def test_anomalies_indices_match() -> None:
    rows = [{"qrynum": v} for v in (100, 110, 105, 120, 95, 115, 5000, 100)]
    r = detect_anomaly(rows, metric_column="qrynum", method="iqr")
    assert 6 in r["anomalies"]  # index of 5000
    assert all(0 <= i < len(rows) for i in r["anomalies"])


def test_empty_rows() -> None:
    r = detect_anomaly([], metric_column="qrynum")
    assert r["row_count"] == 0
    assert r["anomaly_count"] == 0
