"""Unit tests for ``precheck_sql`` (sqlglot AST static rules).

SQL examples use the **actual DB column names** (data_date / month /
day_qrynum / month_qrynum_sum etc) — not the STANDARD-draft names —
because that is what the catalog now mirrors after the 2026-05-06
drift correction. See ``qcm_catalog.yaml`` source.drift_notes.
"""

from __future__ import annotations

from mj_agent.biz_catalog import load_catalog
from mj_agent.tools.sql.precheck import precheck_sql


def setup_function() -> None:
    load_catalog.cache_clear()


class TestNoSelectStar:
    def test_select_star_rejected(self) -> None:
        r = precheck_sql(
            "SELECT * FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date = '2026-04-30'"
        )
        assert not r.ok
        assert any("no_select_star" in e for e in r.errors)

    def test_count_star_allowed(self) -> None:
        r = precheck_sql(
            "SELECT COUNT(*) FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date = '2026-04-30'"
        )
        assert r.ok, r.errors

    def test_explicit_columns_allowed(self) -> None:
        r = precheck_sql(
            "SELECT data_date, day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date >= '2026-04-01' LIMIT 31"
        )
        assert r.ok, r.errors


class TestRequireTimeRange:
    def test_fact_table_without_time_predicate_rejected(self) -> None:
        r = precheck_sql(
            "SELECT day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total LIMIT 10"
        )
        assert not r.ok
        assert any("require_time_range" in e for e in r.errors)

    def test_fact_table_with_data_date_passes(self) -> None:
        r = precheck_sql(
            "SELECT day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date >= '2026-04-01'"
        )
        # may warn about LIMIT but no errors
        assert r.ok, r.errors

    def test_fact_table_with_month_passes(self) -> None:
        r = precheck_sql(
            "SELECT month_tntcnt_sum FROM biz_dws.dws_qcm_tntcnt_monthly_total "
            "WHERE month >= '2026-01-01'"
        )
        assert r.ok, r.errors

    def test_signal_table_no_time_required(self) -> None:
        """Signal tables are small; time predicate not required."""
        r = precheck_sql(
            "SELECT * FROM biz_dws.dws_qcm_ready_signal LIMIT 10"
        )
        # SELECT * still rejected, but require_time_range should not fire.
        assert any("no_select_star" in e for e in r.errors)
        assert not any("require_time_range" in e for e in r.errors)

    def test_dimension_table_no_time_required(self) -> None:
        r = precheck_sql(
            "SELECT tenant_id FROM biz_dwd.dwd_dim_institution LIMIT 100"
        )
        assert r.ok, r.errors


class TestRequireLimit:
    def test_detail_select_without_limit_warns(self) -> None:
        r = precheck_sql(
            "SELECT data_date, day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date >= '2026-04-01'"
        )
        assert r.ok, r.errors
        assert any("require_limit" in w for w in r.warnings)

    def test_aggregate_without_limit_clean(self) -> None:
        r = precheck_sql(
            "SELECT ana_ind_name, SUM(month_qrynum_sum) "
            "FROM biz_dws.dws_qcm_qrynum_monthly_by_industry "
            "WHERE month = '2026-04-01' GROUP BY ana_ind_name"
        )
        assert r.ok, r.errors
        assert not any("require_limit" in w for w in r.warnings)

    def test_count_aggregate_without_limit_clean(self) -> None:
        r = precheck_sql(
            "SELECT COUNT(*) FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date >= '2026-04-01'"
        )
        assert r.ok, r.errors
        assert not any("require_limit" in w for w in r.warnings)

    def test_limit_too_large_warns(self) -> None:
        r = precheck_sql(
            "SELECT data_date, day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total "
            "WHERE data_date >= '2026-01-01' LIMIT 5000"
        )
        assert r.ok, r.errors
        assert any("limit_too_large" in w for w in r.warnings)


class TestParseFailureGracefulFallback:
    def test_unparseable_sql_does_not_block(self) -> None:
        # Garbage that L1 already rejected; precheck should degrade.
        r = precheck_sql("not valid sql at all here")
        # No errors means precheck did not block; warnings may carry
        # the parse-failure note.
        assert r.ok
