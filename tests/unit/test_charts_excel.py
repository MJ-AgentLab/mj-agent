"""Phase 1 sub 1.F — charts (matplotlib) + Excel (openpyxl)."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from mj_agent.tools import ALL_TOOLS
from mj_agent.tools.charts import chart_bar, chart_line, chart_trend
from mj_agent.tools.excel import excel_export


@pytest.fixture(autouse=True)
def _isolate_tmpdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MJ_AGENT_CHART_TMPDIR", str(tmp_path))


_LINE_ROWS = [
    {"date": "2026-04-01", "qrynum": 100},
    {"date": "2026-04-02", "qrynum": 120},
    {"date": "2026-04-03", "qrynum": 90},
]

_BAR_ROWS = [
    {"tenant": "上海银行", "qrynum": 200},
    {"tenant": "京东小贷", "qrynum": 180},
    {"tenant": "马上消金", "qrynum": 150},
]

_MULTI_LINE_ROWS = [
    {"date": "2026-04-01", "qrynum": 100, "tntcnt": 30},
    {"date": "2026-04-02", "qrynum": 120, "tntcnt": 32},
    {"date": "2026-04-03", "qrynum": 90, "tntcnt": 28},
]


class TestChartLine:
    def test_envelope_shape(self) -> None:
        r = chart_line(_LINE_ROWS, x_column="date", y_columns=["qrynum"])
        assert set(r) == {"file_path", "kind", "title", "x_column", "y_columns", "point_count"}
        assert r["kind"] == "image/png"
        assert r["point_count"] == 3
        assert Path(r["file_path"]).exists()
        assert os.path.getsize(r["file_path"]) > 0

    def test_multi_series(self) -> None:
        r = chart_line(_MULTI_LINE_ROWS, x_column="date", y_columns=["qrynum", "tntcnt"])
        assert r["y_columns"] == ["qrynum", "tntcnt"]
        assert Path(r["file_path"]).exists()

    def test_missing_column_raises(self) -> None:
        with pytest.raises(ValueError, match="missing in rows"):
            chart_line(_LINE_ROWS, x_column="missing", y_columns=["qrynum"])

    def test_empty_rows_raises(self) -> None:
        with pytest.raises(ValueError, match="rows is empty"):
            chart_line([], x_column="date", y_columns=["qrynum"])

    def test_explicit_output_path(self, tmp_path: Path) -> None:
        target = tmp_path / "custom.png"
        r = chart_line(_LINE_ROWS, x_column="date", y_columns=["qrynum"], output_path=str(target))
        assert Path(r["file_path"]) == target
        assert target.exists()


class TestChartBar:
    def test_vertical_bars(self) -> None:
        r = chart_bar(_BAR_ROWS, x_column="tenant", y_column="qrynum")
        assert r["horizontal"] is False
        assert r["point_count"] == 3
        assert Path(r["file_path"]).exists()

    def test_horizontal_bars(self) -> None:
        r = chart_bar(
            _BAR_ROWS, x_column="tenant", y_column="qrynum", horizontal=True
        )
        assert r["horizontal"] is True
        assert Path(r["file_path"]).exists()

    def test_missing_column_raises(self) -> None:
        with pytest.raises(ValueError, match="missing in rows"):
            chart_bar(_BAR_ROWS, x_column="tenant", y_column="missing")


class TestChartTrend:
    def test_delegates_to_chart_line(self) -> None:
        r = chart_trend(
            _MULTI_LINE_ROWS, time_column="date", metric_columns=["qrynum"]
        )
        assert r["kind"] == "image/png"
        assert r["point_count"] == 3
        # default title carries 趋势 suffix
        assert "趋势" in r["title"]

    def test_empty_metric_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="metric_columns is empty"):
            chart_trend(_MULTI_LINE_ROWS, time_column="date", metric_columns=[])


class TestExcelExport:
    def test_envelope_shape(self) -> None:
        r = excel_export(_LINE_ROWS)
        assert set(r) >= {
            "file_path",
            "kind",
            "sheet_name",
            "row_count",
            "column_count",
            "columns",
        }
        assert r["row_count"] == 3
        assert r["column_count"] == 2
        assert r["columns"] == ["date", "qrynum"]
        assert Path(r["file_path"]).exists()

    def test_xlsx_is_valid_zip(self) -> None:
        """An .xlsx is a zip archive; if openpyxl wrote it correctly,
        zipfile should be able to crack it open."""
        r = excel_export(_LINE_ROWS, sheet_name="qrynum")
        with zipfile.ZipFile(r["file_path"]) as z:
            assert "[Content_Types].xml" in z.namelist()
            assert any("sheet1.xml" in n for n in z.namelist())

    def test_sheet_name_sanitized(self) -> None:
        r = excel_export(_LINE_ROWS, sheet_name="bad/name?with*chars")
        assert "/" not in r["sheet_name"]
        assert "?" not in r["sheet_name"]
        assert "*" not in r["sheet_name"]

    def test_sheet_name_truncated_to_31(self) -> None:
        r = excel_export(_LINE_ROWS, sheet_name="x" * 50)
        assert len(r["sheet_name"]) <= 31

    def test_empty_rows_raises(self) -> None:
        with pytest.raises(ValueError, match="rows is empty"):
            excel_export([])


class TestRegistration:
    def test_chart_and_excel_in_all_tools(self) -> None:
        names = [t.__name__ for t in ALL_TOOLS]
        for expected in ("chart_line", "chart_bar", "chart_trend", "excel_export"):
            assert expected in names

    def test_presentation_tools_at_end(self) -> None:
        """chart_* and excel_export are last in ALL_TOOLS (they consume rows
        produced by SQL / analysis tools earlier)."""
        names = [t.__name__ for t in ALL_TOOLS]
        sql_idx = names.index("execute_sql")
        for tool_name in ("chart_line", "chart_bar", "chart_trend", "excel_export"):
            assert names.index(tool_name) > sql_idx
