"""Matplotlib-based chart rendering (Phase 1 sub 1.F).

LLM-callable chart tools that take a row set (typically from
``execute_sql``) and produce a PNG file. The Chainlit UI
(``src/mj_agent/ui.py``) surfaces the PNG via ``cl.Image`` so the
analyst sees the chart inline.

Tools:
  - ``chart_line(rows, x_column, y_columns, ...)`` — line chart
  - ``chart_bar(rows, x_column, y_column, ...)``  — bar chart
  - ``chart_trend(rows, time_column, metric_columns, ...)`` — alias for
    line chart with sane time-axis defaults

All tools return ``{"file_path": str, "kind": "image/png", ...}`` so
the agent's reply layer can pick up the file uniformly.
"""

from mj_agent.tools.charts.bar import chart_bar
from mj_agent.tools.charts.line import chart_line
from mj_agent.tools.charts.trend import chart_trend

__all__ = ["chart_bar", "chart_line", "chart_trend"]
