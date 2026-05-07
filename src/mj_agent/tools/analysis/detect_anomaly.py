"""IQR / z-score outlier flagging.

Phase 1 starter — runs cheap statistical anomaly detection on a numeric
column. Phase 2 may layer in domain-specific signals (week-over-week
ratios, seasonal decomposition, etc).
"""

from __future__ import annotations

import statistics
from typing import Any, Literal


def detect_anomaly(
    rows: list[dict[str, Any]],
    metric_column: str,
    method: Literal["iqr", "zscore"] = "iqr",
    threshold: float = 1.5,
) -> dict[str, Any]:
    """Flag rows where ``metric_column`` is statistically anomalous.

    Args:
        rows: input row set.
        metric_column: numeric column to inspect.
        method: ``iqr`` (Tukey fences at threshold × IQR; default 1.5)
            or ``zscore`` (|value − mean| / stdev > threshold; default
            1.5 → ~13.4% expected on normal data; raise to 3.0 for
            strict outliers).
        threshold: scale factor — interpretation depends on ``method``.

    Returns:
        Envelope dict:
          - ``rows`` — same rows with ``is_anomaly`` (bool) field added;
            method-specific fields too (`zscore` gets a ``zscore`` value;
            ``iqr`` gets ``below_lower`` / ``above_upper`` flags)
          - ``row_count``
          - ``anomaly_count``
          - ``method`` / ``threshold`` echoed
          - ``stats`` — per-method summary (mean/stdev or q1/q3/iqr)
          - ``anomalies`` — convenience: indices of flagged rows

    Raises:
        ValueError: missing column, fewer than 4 numeric values (insufficient
            sample for IQR), or unknown method.
    """
    if method not in ("iqr", "zscore"):
        raise ValueError(f"unknown method '{method}'; supported: iqr / zscore")
    if not rows:
        return {
            "rows": [],
            "row_count": 0,
            "anomaly_count": 0,
            "method": method,
            "threshold": threshold,
            "stats": {},
            "anomalies": [],
        }

    sample = rows[0]
    if metric_column not in sample:
        raise ValueError(f"metric_column '{metric_column}' not in rows")

    values: list[float] = [
        float(r[metric_column]) for r in rows if r[metric_column] is not None
    ]
    if len(values) < 4:
        raise ValueError(
            f"need ≥ 4 non-null values for stable {method}; "
            f"got {len(values)}"
        )

    out_rows = [dict(r) for r in rows]
    anomalies: list[int] = []
    stats: dict[str, float] = {}

    if method == "iqr":
        q1 = statistics.quantiles(values, n=4)[0]
        q3 = statistics.quantiles(values, n=4)[2]
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        stats = {"q1": q1, "q3": q3, "iqr": iqr, "lower": lower, "upper": upper}
        for i, r in enumerate(out_rows):
            v = r[metric_column]
            below = v is not None and v < lower
            above = v is not None and v > upper
            r["below_lower"] = bool(below)
            r["above_upper"] = bool(above)
            r["is_anomaly"] = bool(below or above)
            if r["is_anomaly"]:
                anomalies.append(i)
    else:  # zscore
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) >= 2 else 0.0
        stats = {"mean": mean, "stdev": stdev}
        for i, r in enumerate(out_rows):
            v = r[metric_column]
            if v is None or stdev == 0:
                r["zscore"] = None
                r["is_anomaly"] = False
            else:
                z = (float(v) - mean) / stdev
                r["zscore"] = z
                r["is_anomaly"] = abs(z) > threshold
                if r["is_anomaly"]:
                    anomalies.append(i)

    return {
        "rows": out_rows,
        "row_count": len(out_rows),
        "anomaly_count": len(anomalies),
        "method": method,
        "threshold": threshold,
        "stats": stats,
        "anomalies": anomalies,
    }
