"""Top-N drill-down post-processor.

Given a set of rows that's too big to read whole, pick the top-N by a
metric — either globally or per-dimension (which gives the LLM a tidy
"top 5 per industry" view).
"""

from __future__ import annotations

from typing import Any


def drill_down(
    rows: list[dict[str, Any]],
    metric_column: str,
    top_n: int,
    dimension_column: str | None = None,
    descending: bool = True,
) -> dict[str, Any]:
    """Pick top-N rows by metric, optionally per dimension.

    Args:
        rows: input row set (typically from ``execute_sql``).
        metric_column: numeric column to rank by.
        top_n: how many rows to keep (per group when ``dimension_column``
            is set, otherwise global top-N). Must be > 0.
        dimension_column: optional column to partition by; when provided
            you get top-N within each distinct value of this column.
        descending: True → highest first (default); False → lowest first.

    Returns:
        Envelope dict:
          - ``rows`` — selected rows, sorted (per partition if applicable)
          - ``row_count``
          - ``input_row_count``
          - ``metric_column`` / ``top_n`` / ``dimension_column`` echoed
          - ``descending``

    Raises:
        ValueError: ``top_n <= 0``, missing metric/dimension columns,
            or non-numeric metric values.
    """
    if top_n <= 0:
        raise ValueError(f"top_n must be > 0, got {top_n}")
    if not rows:
        return {
            "rows": [],
            "row_count": 0,
            "input_row_count": 0,
            "metric_column": metric_column,
            "top_n": top_n,
            "dimension_column": dimension_column,
            "descending": descending,
        }

    sample = rows[0]
    if metric_column not in sample:
        raise ValueError(f"metric_column '{metric_column}' not in rows")
    if dimension_column is not None and dimension_column not in sample:
        raise ValueError(f"dimension_column '{dimension_column}' not in rows")

    def _sorted(part: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort a partition putting None metrics last regardless of direction."""
        valued = [r for r in part if r.get(metric_column) is not None]
        nulls = [r for r in part if r.get(metric_column) is None]
        valued.sort(key=lambda r: r[metric_column], reverse=descending)
        return valued + nulls

    if dimension_column is None:
        out = _sorted(rows)[:top_n]
    else:
        partitions: dict[Any, list[dict[str, Any]]] = {}
        for r in rows:
            partitions.setdefault(r.get(dimension_column), []).append(r)
        out = []
        for _, part in partitions.items():
            out.extend(_sorted(part)[:top_n])

    return {
        "rows": out,
        "row_count": len(out),
        "input_row_count": len(rows),
        "metric_column": metric_column,
        "top_n": top_n,
        "dimension_column": dimension_column,
        "descending": descending,
    }
