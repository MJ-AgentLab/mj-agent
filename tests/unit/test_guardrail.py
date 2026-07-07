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


class TestQuotedIdentifierAllowlist:
    """#280 — quoted / mixed-quoted identifiers must not bypass the L1 allowlist.

    Regression guard: the original regex extraction (``FROM|JOIN`` + a bare
    ``[a-zA-Z_]\\w*`` capture) could not see double-quoted schema refs, so
    ``FROM "biz_ods"."t"`` slipped past L1 and was stopped only by the L4 DB
    GRANT. Extraction is now AST-based (sqlglot), so out-of-allowlist refs are
    rejected at L1 regardless of quoting or JOIN shape.
    """

    PER_SCHEMA = {"biz_dwd": ["dwd_dim_product_interface", "dwd_dim_institution"]}

    @pytest.mark.parametrize(
        "sql",
        [
            'SELECT 1 FROM "biz_ods"."ods_qvl_ready_signal"',  # fully quoted
            'SELECT 1 FROM "biz_ods".ods_raw',  # schema quoted only
            'SELECT 1 FROM biz_ods."ods_raw"',  # table quoted only
            'SELECT 1 FROM "BiZ_oDs"."x"',  # quoted + case-mixed
        ],
    )
    def test_quoted_disallowed_schema_rejected_at_l1(self, sql: str) -> None:
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "biz_ods" in reason.lower()
        assert "allowlist" in reason

    @pytest.mark.parametrize("schema", ["biz_ads", "ops_meta"])
    def test_quoted_other_forbidden_schemas_rejected(self, schema: str) -> None:
        sql = f'SELECT 1 FROM "{schema}"."some_table"'
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "allowlist" in reason

    def test_quoted_union_leg_rejected(self) -> None:
        sql = (
            "SELECT 1 FROM biz_dwd.dwd_dim_institution "
            'UNION SELECT 1 FROM "biz_ods"."ods_raw"'
        )
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "biz_ods" in reason.lower()

    def test_quoted_comma_join_leg_rejected(self) -> None:
        # Comma (cross) join — the forbidden ref is NOT immediately after
        # FROM/JOIN, so the old regex could never catch it, even unquoted.
        sql = (
            "SELECT 1 FROM biz_dwd.dwd_dim_institution a, "
            '"biz_ods"."ods_raw" b LIMIT 10'
        )
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "biz_ods" in reason.lower()

    def test_forbidden_ref_in_where_subquery_rejected(self) -> None:
        # Nested sub-query in WHERE — the AST walk traverses the whole tree,
        # whereas the old regex only scanned FROM/JOIN-adjacent text.
        sql = (
            "SELECT 1 FROM biz_dwd.dwd_dim_institution "
            'WHERE tenant_code IN (SELECT code FROM "biz_ods"."ods_raw")'
        )
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "biz_ods" in reason.lower()

    def test_quoted_disallowed_dwd_table_rejected(self) -> None:
        sql = 'SELECT 1 FROM "biz_dwd"."dwd_qvl_downstream_query"'
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "dwd_qvl_downstream_query" in reason
        assert "allowlist" in reason

    @pytest.mark.parametrize(
        "sql",
        [
            'SELECT 1 FROM "biz_dwd"."dwd_dim_institution"',
            'SELECT institution_name FROM biz_dwd."dwd_dim_institution"',
            'SELECT 1 FROM "biz_dws"."dws_qcm_qrynum_daily_total"',
        ],
    )
    def test_quoted_allowlisted_refs_still_pass(self, sql: str) -> None:
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert ok, reason

    def test_string_literal_lookalike_not_treated_as_table(self) -> None:
        # A 'FROM biz_ods.x' substring inside a string literal is data, not a
        # table reference; the AST extraction correctly ignores it (the old
        # regex would false-positive reject this).
        sql = "SELECT 'FROM biz_ods.x' AS note FROM biz_dwd.dwd_dim_institution"
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert ok, reason


class TestParseFailureFailClosed:
    """#280 tail — SQL that sqlglot cannot parse is rejected (fail-closed).

    The schema/table allowlist is a security boundary: when static analysis
    cannot read the statement we reject rather than degrade to a weaker check.
    (Contrast the L1b precheck *quality* rules, which fail open because the DB
    is their ultimate validator.) Without this, valid-but-unparseable
    PostgreSQL — jsonb ``@?``, ``ORDER BY ... USING <`` — forced the old regex
    fallback, through which a quoted or comma-joined forbidden ref slipped
    past L1 again.
    """

    PER_SCHEMA = {"biz_dwd": ["dwd_dim_product_interface", "dwd_dim_institution"]}

    @pytest.mark.parametrize(
        "sql",
        [
            # jsonb path operator @? — valid PG, unparseable by sqlglot; would
            # otherwise let the quoted biz_ods ref slip via the regex fallback.
            "SELECT id FROM \"biz_ods\".\"customers\" WHERE profile @? '$.email'",
            # comma cross-join hiding an unquoted forbidden ref behind a parse
            # failure (@?) — the old regex only matched the first FROM table.
            "SELECT x @? '$.a' FROM biz_dws.dws_qcm_x t1, biz_ods.b t2",
            # custom sort operator on a quoted forbidden ref — valid PG.
            'SELECT c FROM "biz_ods"."secret" ORDER BY c USING <',
        ],
    )
    def test_unparseable_sql_rejected(self, sql: str) -> None:
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "could not parse" in reason.lower()

    def test_unparseable_on_allowed_table_also_rejected(self) -> None:
        # Accepted UX cost of fail-closed: even an allowed-table query is
        # rejected when it cannot be parsed for validation.
        sql = "SELECT c FROM biz_dws.dws_qcm_x ORDER BY c USING <"
        ok, reason = is_safe_select(
            sql, ALLOWED, allowed_tables_per_schema=self.PER_SCHEMA
        )
        assert not ok
        assert "could not parse" in reason.lower()

    def test_pathological_nesting_never_raises(self) -> None:
        # Deeply nested parens make sqlglot raise RecursionError; is_safe_select
        # must catch it and fail closed, not propagate.
        sql = "SELECT " + "(" * 200 + "1" + ")" * 200 + " FROM biz_dws.t"
        ok, reason = is_safe_select(sql, ALLOWED)
        assert not ok
        assert "could not parse" in reason.lower()
