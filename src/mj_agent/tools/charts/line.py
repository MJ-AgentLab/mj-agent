"""Line chart — `chart_line(rows, x_column, y_columns, ...)`."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

from mj_agent.tools.charts._common import configure_style, make_output_path


def chart_line(
    rows: list[dict[str, Any]],
    x_column: str,
    y_columns: list[str],
    title: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render a line chart and write PNG.

    Args:
        rows: row set (typically from ``execute_sql``); must be ordered
            by ``x_column`` for a meaningful line.
        x_column: column name for the x-axis (categorical or temporal).
        y_columns: list of metric column names to plot as separate lines.
        title: optional chart title (defaults to ``y_columns`` joined).
        output_path: optional explicit PNG path; auto-generated under
            ``MJ_AGENT_CHART_TMPDIR`` (or system temp) when ``None``.

    Returns:
        Envelope dict:
          - ``file_path`` (str): absolute path to the PNG written
          - ``kind`` (str): always ``"image/png"``
          - ``title`` (str)
          - ``x_column`` (str)
          - ``y_columns`` (list[str])
          - ``point_count`` (int): number of x values plotted

    Raises:
        ValueError: empty ``y_columns``, missing column, or empty rows.
    """
    if not rows:
        raise ValueError("chart_line: rows is empty")
    if not y_columns:
        raise ValueError("chart_line: y_columns is empty")

    sample = rows[0]
    for col in (x_column, *y_columns):
        if col not in sample:
            raise ValueError(f"chart_line: column '{col}' missing in rows")

    configure_style()
    xs = [r[x_column] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 5))
    for y in y_columns:
        ys = [r[y] for r in rows]
        ax.plot(xs, ys, marker="o", label=y)
    ax.set_xlabel(x_column)
    ax.set_ylabel(" / ".join(y_columns) if len(y_columns) > 1 else y_columns[0])
    ax.set_title(title or " vs ".join(y_columns))
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()

    out = make_output_path("line", output_path)
    fig.savefig(out)
    plt.close(fig)

    return {
        "file_path": str(out),
        "kind": "image/png",
        "title": title or " vs ".join(y_columns),
        "x_column": x_column,
        "y_columns": list(y_columns),
        "point_count": len(rows),
    }
