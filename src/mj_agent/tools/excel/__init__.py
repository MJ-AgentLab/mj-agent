"""Excel export (openpyxl) — Phase 1 sub 1.F.

Single tool: ``excel_export(rows, sheet_name?, output_path?)`` writes
a row set to an .xlsx file. The Chainlit UI surfaces the file via
``cl.File`` so the analyst can download.
"""

from mj_agent.tools.excel.export import excel_export

__all__ = ["excel_export"]
