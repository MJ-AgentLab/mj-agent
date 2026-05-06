"""Unit tests for ``find_biz_context`` (semantic context retrieval)."""

from __future__ import annotations

from mj_agent.biz_catalog import find_biz_context, load_catalog


def setup_function() -> None:
    load_catalog.cache_clear()


def test_query_count_question_picks_qrynum() -> None:
    ctx = find_biz_context("最近 7 天查询量趋势")
    assert "qrynum" in ctx["candidate_metrics"]
    assert "daily" in ctx["candidate_periods"]


def test_tenant_question_picks_tntcnt_or_qrynum() -> None:
    ctx = find_biz_context("Top 10 机构查询量")
    # Both metrics may match: 机构 → tntcnt, 查询 → qrynum.
    # Keep it permissive: at least one matches.
    assert ctx["candidate_metrics"]
    assert "_by_tenant" in ctx["candidate_dimensions"]


def test_industry_question_picks_by_industry() -> None:
    ctx = find_biz_context("某行业月度同比变化")
    assert "_by_industry" in ctx["candidate_dimensions"]
    assert "monthly" in ctx["candidate_periods"]
    assert ctx["needs_period_over_period"] is True


def test_yoy_keyword_triggers_period_over_period() -> None:
    ctx = find_biz_context("查询量同比")
    assert ctx["needs_period_over_period"] is True
    pop = ctx["period_over_period_patterns"]
    assert pop["diff"]["pattern"] == "<period_abbrev>_<metric_part>_diff"


def test_no_keywords_returns_sensible_defaults() -> None:
    ctx = find_biz_context("看一下数据")
    # Defaults: all metrics, daily+monthly periods, _total dimension.
    assert set(ctx["candidate_metrics"]) == {"qrynum", "tntcnt"}
    assert "daily" in ctx["candidate_periods"]
    assert "monthly" in ctx["candidate_periods"]
    assert ctx["candidate_dimensions"] == ["_total"]
    # Notes should explain the defaulting.
    assert any("metric" in n for n in ctx["notes"])


def test_candidate_table_names_follow_pattern() -> None:
    ctx = find_biz_context("最近 7 天查询量")
    # Should include at least one biz_dws.dws_qcm_qrynum_daily_* table.
    has_daily_qrynum = any(
        name.startswith("biz_dws.dws_qcm_qrynum_daily")
        for name in ctx["candidate_table_names"]
    )
    assert has_daily_qrynum


def test_dimension_tables_always_returned() -> None:
    ctx = find_biz_context("anything")
    names = {t["name"] for t in ctx["dimension_tables"]}
    assert names == {
        "biz_dwd.dwd_dim_product_interface",
        "biz_dwd.dwd_dim_institution",
    }


def test_signal_tables_always_returned() -> None:
    ctx = find_biz_context("ETL 指标怎么样")
    names = {t["name"] for t in ctx["signal_tables"]}
    assert "biz_dws.dws_qcm_etl_metrics" in names
    assert "biz_dws.dws_qcm_ready_signal" in names


def test_time_columns_match_periods() -> None:
    ctx = find_biz_context("月度查询量")
    assert ctx["time_columns"]["monthly"] == "month"


def test_period_abbreviations_match_standard() -> None:
    ctx = find_biz_context("daily 查询量")
    assert ctx["period_abbreviations"]["daily"] == "dod"


def test_forbidden_access_surfaced() -> None:
    ctx = find_biz_context("anything")
    forbidden = ctx["forbidden_access"]
    assert "biz_ods" in forbidden["schemas"]
    assert "ops_ods" in forbidden["schemas"]
