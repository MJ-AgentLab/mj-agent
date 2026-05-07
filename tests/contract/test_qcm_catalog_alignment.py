"""Contract: ``qcm_catalog.yaml`` claims vs live DB schema.

Skips if no analyst credentials. Drift here means ``mj-ddd-semantics``
will mislead the LLM — fix the catalog (or update DB if STANDARD
moved) before merging the offending change.
"""

from __future__ import annotations

import pytest

from mj_agent.biz_catalog import load_catalog
from mj_agent.tools.sql.introspect import describe_biz_table, list_biz_tables

pytestmark = [pytest.mark.contract, pytest.mark.usefixtures("live_db")]


def _live_tables() -> dict[str, set[str]]:
    """Return ``{schema: {table_name, ...}}`` from analyst-visible DB."""
    by_schema: dict[str, set[str]] = {}
    for t in list_biz_tables():
        by_schema.setdefault(t["schema"], set()).add(t["table"])
    return by_schema


@pytest.fixture(scope="session")
def live_tables() -> dict[str, set[str]]:
    return _live_tables()


@pytest.fixture(scope="session")
def catalog() -> dict:
    load_catalog.cache_clear()
    return load_catalog()


class TestSignalTables:
    """3 QCM signal tables must exist in biz_dws."""

    def test_signal_tables_exist(
        self, catalog: dict, live_tables: dict[str, set[str]]
    ) -> None:
        for entry in catalog.get("signal_tables", []):
            full = entry["name"]
            schema, name = full.split(".", 1)
            tables = live_tables.get(schema, set())
            assert name in tables, (
                f"signal table {full} declared in qcm_catalog.yaml but missing from "
                f"DB (analyst-visible {schema} tables: {sorted(tables)[:5]}...)"
            )


class TestDimensionTables:
    """2 biz_dwd dim tables must exist + carry their declared join_key."""

    def test_dimension_tables_exist(
        self, catalog: dict, live_tables: dict[str, set[str]]
    ) -> None:
        for entry in catalog.get("dimension_tables", []):
            full = entry["name"]
            schema, name = full.split(".", 1)
            tables = live_tables.get(schema, set())
            assert name in tables, (
                f"dim table {full} declared in qcm_catalog.yaml but missing from "
                f"analyst-visible DB (allowlist enforced — see ADR-008)"
            )

    def test_dimension_join_keys_exist(self, catalog: dict) -> None:
        for entry in catalog.get("dimension_tables", []):
            full = entry["name"]
            join_key = entry["join_key"]
            desc = describe_biz_table(full)
            cols = {c["name"] for c in desc["columns"]}
            assert join_key in cols, (
                f"dim {full}: join_key '{join_key}' declared in catalog "
                f"but not present in DB (cols sample: {sorted(cols)[:6]}...)"
            )


class TestPeriodTimeColumns:
    """Each period's time_column must exist on at least one ``_total`` fact table."""

    @pytest.mark.parametrize("period", ["daily", "weekly", "monthly", "quarterly", "yearly"])
    def test_period_time_column_present_on_total_table(
        self, catalog: dict, live_tables: dict[str, set[str]], period: str
    ) -> None:
        period_cfg = catalog["periods"][period]
        time_column = period_cfg["time_column"]
        suffix = period_cfg["suffix"]  # e.g. "_daily"
        biz_dws = live_tables.get("biz_dws", set())
        # First _total table for this period (probe one is enough for contract).
        candidates = [
            t for t in biz_dws if t.startswith("dws_qcm_") and t.endswith(f"{suffix}_total")
        ]
        assert candidates, (
            f"no biz_dws.dws_qcm_*{suffix}_total table found in DB for period={period} "
            f"(catalog claims this period exists; either the catalog or the DB is stale)"
        )
        # Sample the first one
        sample = sorted(candidates)[0]
        desc = describe_biz_table(f"biz_dws.{sample}")
        cols = {c["name"].lower() for c in desc["columns"]}
        assert time_column.lower() in cols, (
            f"period={period} time_column='{time_column}' not in {sample} "
            f"(actual cols sample: {sorted(cols)[:8]}...)"
        )


class TestForbiddenAccess:
    """Tables in catalog.forbidden_access must NOT show up in analyst-visible list.

    This is a sanity check that the analyst role's GRANTs match the catalog's
    deny list — drift means mj-system changed permissions without telling us.
    """

    def test_forbidden_schemas_not_visible(
        self, catalog: dict, live_tables: dict[str, set[str]]
    ) -> None:
        forbidden = set(catalog.get("forbidden_access", {}).get("schemas", []))
        leaked = forbidden & set(live_tables)
        assert not leaked, (
            f"analyst role can see schemas the catalog declares forbidden: "
            f"{sorted(leaked)} — mj-system permissions drifted from contract"
        )
