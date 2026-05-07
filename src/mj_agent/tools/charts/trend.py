"""Trend chart — alias of ``chart_line`` with time-axis defaults.

Shape matches ``chart_line`` but advertises "time-series intent" so the
LLM picks this when the user asks for a "趋势 / trend" rather than a
generic "line chart". Internally delegates to ``chart_line``.
"""

from __future__ import annotations

from typing import Any

from mj_agent.tools.charts.line import chart_line


def chart_trend(
    rows: list[dict[str, Any]],
    time_column: str,
    metric_columns: list[str],
    title: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render a time-series trend chart (alias of ``chart_line``).

    Args:
        rows: time-ordered row set (caller must sort by time_column).
        time_column: x-axis time column name.
        metric_columns: 1+ metric column names (each → one trend line).
        title: optional title.
        output_path: optional PNG path.

    Returns:
        Same envelope as ``chart_line``.
    """
    if not metric_columns:
        raise ValueError("chart_trend: metric_columns is empty")
    return chart_line(
        rows=rows,
        x_column=time_column,
        y_columns=list(metric_columns),
        title=title or f"{' / '.join(metric_columns)} 趋势",
        output_path=output_path,
    )
