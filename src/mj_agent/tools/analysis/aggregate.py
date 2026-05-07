"""Group-by aggregation post-processor.

Use **after** ``execute_sql`` when the returned row set is too large for
direct LLM consumption (per ``estimate_tokens`` budget). The preferred
path is still to write aggregating SQL up front; this tool is the fallback.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Sequence
from typing import Any

_AGG_FUNCS: dict[str, Callable[[Sequence[Any]], Any]] = {
    "sum": lambda xs: sum(xs),
    "avg": lambda xs: statistics.mean(xs) if xs else 0,
    "mean": lambda xs: statistics.mean(xs) if xs else 0,
    "min": lambda xs: min(xs),
    "max": lambda xs: max(xs),
    "count": lambda xs: len(xs),
}


def aggregate(
    rows: list[dict[str, Any]],
    group_by: list[str],
    aggregations: dict[str, str],
) -> dict[str, Any]:
    """Group rows by ``group_by`` columns and aggregate metric columns.

    Args:
        rows: list of rows (typically the ``rows`` field from
            ``execute_sql`` envelope). Each row is a dict
            ``{column_name: value}``.
        group_by: column names to group on. Rows with identical values
            in these columns collapse to one output row.
        aggregations: mapping of metric column → function name.
            Supported: ``sum`` / ``avg`` (alias ``mean``) / ``min`` /
            ``max`` / ``count``.

    Returns:
        A dict envelope:
          - ``rows``: aggregated rows (one per unique group_by tuple)
          - ``row_count``: len(rows after aggregation)
          - ``input_row_count``: len(rows in)
          - ``compression_ratio``: input/output ratio (>=1.0)
          - ``group_by``: echoed input
          - ``aggregations``: echoed input

    Raises:
        ValueError: unknown aggregation function or missing column.
    """
    for col, fn in aggregations.items():
        if fn not in _AGG_FUNCS:
            raise ValueError(
                f"unknown aggregation '{fn}' for column '{col}'; "
                f"supported: {sorted(_AGG_FUNCS)}"
            )

    if not rows:
        return {
            "rows": [],
            "row_count": 0,
            "input_row_count": 0,
            "compression_ratio": 1.0,
            "group_by": list(group_by),
            "aggregations": dict(aggregations),
        }

    # Validate columns exist in at least one row (cheap probe of first row).
    sample = rows[0]
    for col in (*group_by, *aggregations):
        if col not in sample:
            raise ValueError(
                f"column '{col}' missing in input rows (first row keys: "
                f"{sorted(sample)})"
            )

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row.get(g) for g in group_by)
        buckets.setdefault(key, []).append(row)

    out: list[dict[str, Any]] = []
    for key, group_rows in buckets.items():
        agg_row: dict[str, Any] = dict(zip(group_by, key, strict=True))
        for col, fn in aggregations.items():
            values = [r[col] for r in group_rows if r[col] is not None]
            agg_row[f"{fn}_{col}"] = _AGG_FUNCS[fn](values) if values else None
        out.append(agg_row)

    return {
        "rows": out,
        "row_count": len(out),
        "input_row_count": len(rows),
        "compression_ratio": len(rows) / max(len(out), 1),
        "group_by": list(group_by),
        "aggregations": dict(aggregations),
    }
