"""Integration tests against the real DEV biz domain.

Gated by the ``live_db`` fixture, which permanently returns the structured
biz-live pytest policy skip. Credential presence never enables this module.
"""

from __future__ import annotations

import pytest

from mj_agent.tools.sql.execute import execute_sql
from mj_agent.tools.sql.introspect import describe_biz_table, list_biz_tables

pytestmark = pytest.mark.usefixtures("live_db")


def test_list_biz_tables_returns_expected_schemas() -> None:
    tables = list_biz_tables()
    assert tables, "no tables visible to analyst — check GRANTs"
    schemas = {t["schema"] for t in tables}
    assert schemas.issubset({"biz_dws", "biz_dwd"})
    assert "biz_dws" in schemas


def test_describe_table_has_columns() -> None:
    # Any known daily-total table: the name is part of the mj-system contract.
    result = describe_biz_table("biz_dws.dws_qcm_qrynum_daily_total")
    names = [c["name"] for c in result["columns"]]
    assert "data_date" in names


def test_execute_sql_returns_dict_rows() -> None:
    # precheck requires a time-column predicate on biz_dws fact tables.
    # data_date is the actual time column for daily-period tables (drift
    # from STANDARD §2.1 — see qcm_catalog.yaml source.drift_notes).
    result = execute_sql(
        "SELECT data_date FROM biz_dws.dws_qcm_qrynum_daily_total "
        "WHERE data_date >= CURRENT_DATE - INTERVAL '60 days' "
        "ORDER BY data_date DESC LIMIT 3"
    )
    assert "rows" in result and "columns" in result
    assert "executed_sql" in result
    assert "precheck_warnings" in result
    assert result["truncated"] is False


def test_execute_sql_rejects_ods() -> None:
    with pytest.raises(ValueError, match="allowlist"):
        execute_sql("SELECT 1 FROM biz_ods.ods_query_volume_daily")


def test_execute_sql_rejects_drop() -> None:
    # DROP fails L1 _STMT_START before _BLOCKED, so message is
    # "only SELECT or WITH ... SELECT is allowed"; either reason is fine.
    with pytest.raises(ValueError, match="blocked|only SELECT"):
        execute_sql("DROP TABLE biz_dws.dws_qcm_qrynum_daily_total")
