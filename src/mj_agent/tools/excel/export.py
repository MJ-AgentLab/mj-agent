"""Excel export — `excel_export(rows, sheet_name?, output_path?)`."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook


def _output_dir() -> Path:
    """Resolve the export directory (env override or system tmp)."""
    override = os.environ.get("MJ_AGENT_CHART_TMPDIR")  # reuse same dir
    base = Path(override) if override else Path(tempfile.gettempdir()) / "mj-agent-charts"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _make_output_path(output_path: str | None) -> Path:
    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return _output_dir() / f"export-{ts}.xlsx"


def excel_export(
    rows: list[dict[str, Any]],
    sheet_name: str = "data",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Write a row set to an .xlsx file.

    Args:
        rows: row set; first-row keys become headers (caller is expected
            to keep keys consistent across rows).
        sheet_name: worksheet name (≤ 31 chars per Excel spec; truncated
            and slash characters replaced if violating).
        output_path: optional explicit .xlsx path; auto-generated under
            ``MJ_AGENT_CHART_TMPDIR`` (or system temp) when ``None``.

    Returns:
        Envelope dict:
          - ``file_path`` (str): absolute path to the .xlsx written
          - ``kind`` (str): always
            ``"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"``
          - ``sheet_name`` (str)
          - ``row_count`` (int)
          - ``column_count`` (int)
          - ``columns`` (list[str])

    Raises:
        ValueError: empty rows.
    """
    if not rows:
        raise ValueError("excel_export: rows is empty")

    safe_sheet = "".join(c for c in sheet_name if c not in r"\/?*[]:")[:31] or "data"

    wb = Workbook()
    ws = wb.active
    if ws is None:  # never None for fresh workbook but mypy wants the guard
        raise RuntimeError("openpyxl returned no active sheet")
    ws.title = safe_sheet

    columns = list(rows[0].keys())
    ws.append(columns)
    for r in rows:
        ws.append([r.get(c) for c in columns])

    out = _make_output_path(output_path)
    wb.save(out)

    return {
        "file_path": str(out),
        "kind": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        "sheet_name": safe_sheet,
        "row_count": len(rows),
        "column_count": len(columns),
        "columns": columns,
    }
