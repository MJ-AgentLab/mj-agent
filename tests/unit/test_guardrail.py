"""Guardrail unit tests — behavior contract for Phase 0."""

from __future__ import annotations

import pytest

from mj_agent.tools.sql.guardrail import is_safe_select

ALLOWED = ["biz_dws", "biz_dwd"]


class TestAccepted:
    def test_simple_select(self) -> None:
        ok, _ = is_safe_select("SELECT data_date FROM biz_dws.dws_qcm_qrynum_daily_total", ALLOWED)
        assert ok

    def test_with_clause(self) -> None:
        sql = (
            "WITH t AS (SELECT data_date FROM biz_dws.dws_qcm_qrynum_daily_total) "
            "SELECT * FROM t"
        )
        ok, _ = is_safe_select(sql, ALLOWED)
        assert ok

    def test_join_across_allowed_schemas(self) -> None:
        sql = (
            "SELECT a.data_date, i.tenant_code "
            "FROM biz_dws.dws_qcm_qrynum_daily_by_tenant a "
            "JOIN biz_dwd.dwd_dim_institution i ON a.tenant_code = i.tenant_code "
            "LIMIT 10"
        )
        ok, reason = is_safe_select(sql, ALLOWED)
        assert ok, reason

    def test_trailing_semicolon_allowed(self) -> None:
        ok, _ = is_safe_select("SELECT 1 FROM biz_dws.dws_qcm_qrynum_daily_total;", ALLOWED)
        assert ok


class TestRejected:
    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE biz_dws.dws_qcm_qrynum_daily_total",
            "INSERT INTO biz_dws.foo VALUES (1)",
            "UPDATE biz_dws.foo SET x = 1",
            "DELETE FROM biz_dws.foo",
            "TRUNCATE biz_dws.foo",
            "ALTER TABLE biz_dws.foo ADD COLUMN x int",
            "GRANT SELECT ON biz_dws.foo TO public",
            "VACUUM biz_dws.foo",
            "CALL some_proc()",
        ],
    )
    def test_blocked_keywords(self, sql: str) -> None:
        ok, reason = is_safe_select(sql, ALLOWED)
        assert not ok
        assert "blocked" in reason or "only SELECT" in reason

    def test_multi_statement(self) -> None:
        sql = "SELECT 1 FROM biz_dws.x; SELECT 2 FROM biz_dws.y"
        ok, reason = is_safe_select(sql, ALLOWED)
        assert not ok
        assert "multi-statement" in reason

    def test_non_select(self) -> None:
        ok, reason = is_safe_select("EXPLAIN SELECT 1", ALLOWED)
        assert not ok
        assert "only SELECT" in reason

    def test_disallowed_schema(self) -> None:
        ok, reason = is_safe_select("SELECT 1 FROM biz_ods.raw", ALLOWED)
        assert not ok
        assert "allowlist" in reason

    def test_empty_sql(self) -> None:
        ok, reason = is_safe_select("   ", ALLOWED)
        assert not ok
        assert "empty" in reason or "only SELECT" in reason


class TestTableLevelAllowlist:
    """biz_dwd is restricted to a per-table allowlist (mj-system contract)."""

    DWD_TABLES = ["dwd_dim_product_interface", "dwd_dim_institution"]
    PER_SCHEMA = {"biz_dwd": DWD_TABLES}

    def test_allowed_dwd_dimension_passes(self) -> None:
        sql = "SELECT 1 FROM biz_dwd.dwd_dim_institution"
        ok, reason = is_safe_select(sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA)
        assert ok, reason

    def test_disallowed_dwd_fact_table_rejected(self) -> None:
        sql = "SELECT 1 FROM biz_dwd.dwd_qvl_downstream_query"
        ok, reason = is_safe_select(sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA)
        assert not ok
        assert "biz_dwd.dwd_qvl_downstream_query" in reason
        assert "allowlist" in reason

    def test_join_with_allowed_dwd_passes(self) -> None:
        sql = (
            "SELECT a.stat_date, i.tenant_code "
            "FROM biz_dws.dws_qcm_qrynum_daily_by_tenant a "
            "JOIN biz_dwd.dwd_dim_institution i ON a.tenant_code = i.tenant_code "
            "LIMIT 10"
        )
        ok, reason = is_safe_select(sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA)
        assert ok, reason

    def test_join_with_disallowed_dwd_rejected(self) -> None:
        sql = (
            "SELECT * FROM biz_dws.dws_qcm_qrynum_daily_total a "
            "JOIN biz_dwd.dwd_fact_event e ON e.id = a.id"
        )
        ok, reason = is_safe_select(sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA)
        assert not ok
        assert "biz_dwd.dwd_fact_event" in reason

    def test_dws_unrestricted(self) -> None:
        """biz_dws has no per-table whitelist — all tables pass."""
        sql = "SELECT 1 FROM biz_dws.dws_qcm_anything_we_invent_total"
        ok, reason = is_safe_select(sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA)
        assert ok, reason

    def test_no_per_schema_map_defaults_to_wildcard(self) -> None:
        """Backward compatibility: absent map -> existing schema-level behavior."""
        sql = "SELECT 1 FROM biz_dwd.anything_at_all"
        ok, _ = is_safe_select(sql, ALLOWED)
        assert ok
