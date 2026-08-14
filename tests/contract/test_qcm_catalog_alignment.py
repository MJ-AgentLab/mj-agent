"""Contract: ``qcm_catalog.yaml`` claims vs a sanitized biz-schema snapshot.

Drift here means ``mj-ddd-semantics`` will mislead the LLM — fix the catalog (or update the
snapshot if the upstream STANDARD moved) before merging the offending change.

**Offline by construction (Epic #499 PR-0c).** This used to introspect the live business
warehouse behind a ``live_db`` credential gate, which meant it always skipped. It now reads
a hand-authored synthetic snapshot fixture, so it runs for real in CI, and it imports no
introspection wrapper, no database client and no dotenv (AC-08).

Real-data drift detection lives in ``scripts/diff_biz_schema.py``, which consumes an
Owner-attested sanitized snapshot from ``.mj-agent-local/`` and emits explicit SKIP codes
rather than pretending the catalog was verified against a current database.
"""

from __future__ import annotations

from typing import Any

import pytest

from mj_agent.biz_catalog import load_catalog
from tests.contract.snapshot_fixtures import columns_of, load_valid_payload, tables_of

pytestmark = pytest.mark.contract


@pytest.fixture(scope="module")
def snapshot_payload() -> dict[str, Any]:
    return load_valid_payload()


@pytest.fixture(scope="module")
def snapshot_tables(snapshot_payload: dict[str, Any]) -> dict[str, set[str]]:
    return tables_of(snapshot_payload)


@pytest.fixture(scope="module")
def catalog() -> dict[str, Any]:
    load_catalog.cache_clear()
    cat = load_catalog()
    assert cat.get("periods"), "qcm_catalog.yaml declares no periods"
    return cat


class TestSignalTables:
    """3 QCM signal tables must exist in biz_dws."""

    def test_signal_tables_exist(
        self, catalog: dict[str, Any], snapshot_tables: dict[str, set[str]]
    ) -> None:
        entries = catalog.get("signal_tables", [])
        assert entries, "qcm_catalog.yaml declares no signal_tables — nothing was checked"
        for entry in entries:
            full = entry["name"]
            schema, name = full.split(".", 1)
            tables = snapshot_tables.get(schema, set())
            assert name in tables, (
                f"signal table {full} declared in qcm_catalog.yaml but missing from the "
                f"snapshot ({schema} tables: {sorted(tables)[:5]}...)"
            )


class TestDimensionTables:
    """2 biz_dwd dim tables must exist + carry their declared join_key."""

    def test_dimension_tables_exist(
        self, catalog: dict[str, Any], snapshot_tables: dict[str, set[str]]
    ) -> None:
        entries = catalog.get("dimension_tables", [])
        assert entries, "qcm_catalog.yaml declares no dimension_tables — nothing was checked"
        for entry in entries:
            full = entry["name"]
            schema, name = full.split(".", 1)
            tables = snapshot_tables.get(schema, set())
            assert name in tables, (
                f"dim table {full} declared in qcm_catalog.yaml but missing from the "
                f"snapshot (allowlist enforced — see ADR-008)"
            )

    def test_dimension_join_keys_exist(
        self, catalog: dict[str, Any], snapshot_payload: dict[str, Any]
    ) -> None:
        entries = catalog.get("dimension_tables", [])
        assert entries, "qcm_catalog.yaml declares no dimension_tables — nothing was checked"
        for entry in entries:
            full = entry["name"]
            join_key = entry["join_key"]
            cols = columns_of(snapshot_payload, full)
            assert join_key in cols, (
                f"dim {full}: join_key '{join_key}' declared in catalog but not present "
                f"in the snapshot (cols sample: {sorted(cols)[:6]}...)"
            )


class TestPeriodTimeColumns:
    """Each period's time_column must exist on at least one ``_total`` fact table."""

    @pytest.mark.parametrize("period", ["daily", "weekly", "monthly", "quarterly", "yearly"])
    def test_period_time_column_present_on_total_table(
        self,
        catalog: dict[str, Any],
        snapshot_payload: dict[str, Any],
        snapshot_tables: dict[str, set[str]],
        period: str,
    ) -> None:
        period_cfg = catalog["periods"][period]
        time_column = period_cfg["time_column"]
        suffix = period_cfg["suffix"]  # e.g. "_daily"
        biz_dws = snapshot_tables.get("biz_dws", set())
        candidates = [
            t for t in biz_dws if t.startswith("dws_qcm_") and t.endswith(f"{suffix}_total")
        ]
        assert candidates, (
            f"no biz_dws.dws_qcm_*{suffix}_total table in the snapshot for period={period} "
            f"(catalog claims this period exists; either the catalog or the fixture is stale)"
        )
        sample = sorted(candidates)[0]
        cols = {c.lower() for c in columns_of(snapshot_payload, f"biz_dws.{sample}")}
        assert time_column.lower() in cols, (
            f"period={period} time_column='{time_column}' not in {sample} "
            f"(actual cols sample: {sorted(cols)[:8]}...)"
        )


class TestForbiddenAccess:
    """Schemas in catalog.forbidden_access must NOT appear in a sanitized snapshot.

    A sanctioned capture walks only analyst-visible schemas, so a forbidden schema showing
    up means either the GRANTs drifted from the contract or the snapshot was not produced
    through the sanctioned chain.
    """

    def test_forbidden_schemas_absent_from_snapshot(
        self, catalog: dict[str, Any], snapshot_tables: dict[str, set[str]]
    ) -> None:
        forbidden = set(catalog.get("forbidden_access", {}).get("schemas", []))
        assert forbidden, "qcm_catalog.yaml declares no forbidden schemas — nothing was checked"
        leaked = forbidden & set(snapshot_tables)
        assert not leaked, (
            f"snapshot exposes schemas the catalog declares forbidden: {sorted(leaked)} — "
            f"either mj-system permissions drifted or the capture bypassed the sanctioned chain"
        )
