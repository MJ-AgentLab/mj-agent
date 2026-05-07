"""Bar chart — `chart_bar(rows, x_column, y_column, ...)`."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

from mj_agent.tools.charts._common import configure_style, make_output_path


def chart_bar(
    rows: list[dict[str, Any]],
    x_column: str,
    y_column: str,
    title: str | None = None,
    horizontal: bool = False,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render a bar chart and write PNG.

    Args:
        rows: row set; row order = bar order (caller may pre-sort).
        x_column: categorical column for bar labels.
        y_column: numeric column for bar height.
        title: optional chart title.
        horizontal: True → horizontal bars (good for long labels);
            False (default) → vertical bars.
        output_path: optional explicit PNG path; auto-generated when None.

    Returns:
        Envelope dict; same shape as ``chart_line`` plus ``horizontal``.

    Raises:
        ValueError: empty rows or missing column.
    """
    if not rows:
        raise ValueError("chart_bar: rows is empty")
    sample = rows[0]
    for col in (x_column, y_column):
        if col not in sample:
            raise ValueError(f"chart_bar: column '{col}' missing in rows")

    configure_style()
    labels = [str(r[x_column]) for r in rows]
    values = [r[y_column] for r in rows]
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.35)) if horizontal else (10, 5))
    if horizontal:
        ax.barh(labels, values)
        ax.set_xlabel(y_column)
        ax.invert_yaxis()
    else:
        ax.bar(labels, values)
        ax.set_ylabel(y_column)
        if any(len(label) > 8 for label in labels):
            fig.autofmt_xdate()
    ax.set_title(title or f"{y_column} by {x_column}")
    ax.grid(alpha=0.3, axis="x" if horizontal else "y")

    out = make_output_path("bar", output_path)
    fig.savefig(out)
    plt.close(fig)

    return {
        "file_path": str(out),
        "kind": "image/png",
        "title": title or f"{y_column} by {x_column}",
        "x_column": x_column,
        "y_column": y_column,
        "horizontal": horizontal,
        "point_count": len(rows),
    }
