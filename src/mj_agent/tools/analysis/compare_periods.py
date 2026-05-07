"""Period-over-period comparison post-processor.

QCM fact tables already carry ``prev_<period>_<metric>`` /
``<period_abbrev>_<metric>_diff`` / ``<period_abbrev>_<metric>_rate``
columns (per ``[STANDARD]_Biz_DWS_Naming_Stability.md`` §3.1, drift
notes in ``biz_catalog/qcm_catalog.yaml``). The preferred path is to
SELECT those columns directly. This tool is the **fallback** for when
the SQL didn't pull them — typically because the user asked an ad-hoc
trend question that doesn't sit on a `_total` table.
"""

from __future__ import annotations

from typing import Any


def compare_periods(
    rows: list[dict[str, Any]],
    time_column: str,
    metric_columns: list[str],
) -> dict[str, Any]:
    """Append previous-period columns to a time-ordered row set.

    Walks rows in input order (caller is expected to ``ORDER BY
    <time_column>`` before invoking) and adds three derived columns
    per metric:

      - ``prev_<metric>``     — value from the row immediately before
      - ``<metric>_diff``     — current - prev (None on first row)
      - ``<metric>_rate``     — (current - prev) / prev (None on first row
                                 or when prev is 0/None)

    Args:
        rows: time-ordered list of row dicts (oldest → newest).
        time_column: name of the time column (used to verify presence
            and to echo in the envelope; not re-sorted here).
        metric_columns: numeric columns to compute period-over-period on.

    Returns:
        Envelope dict:
          - ``rows``: original rows + per-metric prev/diff/rate columns
          - ``row_count``
          - ``time_column`` / ``metric_columns`` echoed
          - ``warnings``: list[str] for any column issues found

    Raises:
        ValueError: ``time_column`` or any ``metric_columns`` missing
            from input rows.
    """
    warnings: list[str] = []
    if not rows:
        return {
            "rows": [],
            "row_count": 0,
            "time_column": time_column,
            "metric_columns": list(metric_columns),
            "warnings": warnings,
        }

    sample = rows[0]
    if time_column not in sample:
        raise ValueError(f"time_column '{time_column}' not in rows")
    for m in metric_columns:
        if m not in sample:
            raise ValueError(f"metric '{m}' not in rows")

    out: list[dict[str, Any]] = []
    prev_row: dict[str, Any] | None = None
    for row in rows:
        new = dict(row)
        for metric in metric_columns:
            curr = row.get(metric)
            prev = prev_row.get(metric) if prev_row else None
            new[f"prev_{metric}"] = prev
            if curr is None or prev is None:
                new[f"{metric}_diff"] = None
                new[f"{metric}_rate"] = None
            else:
                new[f"{metric}_diff"] = curr - prev
                new[f"{metric}_rate"] = (curr - prev) / prev if prev else None
        out.append(new)
        prev_row = row

    if any(r.get(f"{metric_columns[0]}_diff") is None for r in out[1:]):
        warnings.append(
            "some intermediate rows had None metrics; check input data quality"
        )

    return {
        "rows": out,
        "row_count": len(out),
        "time_column": time_column,
        "metric_columns": list(metric_columns),
        "warnings": warnings,
    }
