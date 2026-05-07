"""Contract: ``mj-ddd-semantics/SKILL.md`` claims vs live DB schema.

Light-touch — extracts table names referenced in the SKILL body and
asserts each one is either:
  - the analyst's biz_dws / biz_dwd allowlist, OR
  - explicitly enumerated in qcm_catalog.yaml (catalog test below
    re-checks catalog against live DB)

Goes one level past the SKILL body too: any column name in the SKILL
that matches a metric pattern (e.g. ``day_qrynum``, ``daily_qrynum_avg``)
should resolve in the corresponding live table. Phase 1 sub 1.G keeps
this loose by sampling representative ``_total`` tables only; full
column-coverage matrix lands in Phase 2.
"""

from __future__ import annotations

import re

import pytest

from mj_agent.biz_catalog import load_catalog
from mj_agent.skills import load_skill
from mj_agent.tools.sql.introspect import describe_biz_table, list_biz_tables

pytestmark = [pytest.mark.contract, pytest.mark.usefixtures("live_db")]

_TABLE_REF = re.compile(r"\bbiz_(?:dws|dwd)\.[a-z_]+\b")


@pytest.fixture(scope="session")
def live_tables() -> dict[str, set[str]]:
    by_schema: dict[str, set[str]] = {}
    for t in list_biz_tables():
        by_schema.setdefault(t["schema"], set()).add(t["table"])
    return by_schema


@pytest.fixture(scope="session")
def catalog() -> dict:
    load_catalog.cache_clear()
    return load_catalog()


@pytest.fixture(scope="session")
def skill_body() -> str:
    return load_skill("mj-ddd-semantics")


class TestSkillTableReferences:
    """Every ``biz_(dws|dwd).<table>`` referenced in SKILL must resolve in DB."""

    def test_table_references_resolve(
        self, skill_body: str, live_tables: dict[str, set[str]]
    ) -> None:
        refs = set(_TABLE_REF.findall(skill_body))
        # Pattern-only references (with placeholders) are skipped by allowing
        # `<` / `>` characters to neutralise; refine here if false positives appear.
        concrete = {ref for ref in refs if "<" not in ref and ">" not in ref}
        assert concrete, "no concrete biz_dws/biz_dwd table refs found in SKILL"

        unknown: list[str] = []
        for full in concrete:
            schema, name = full.split(".", 1)
            if name not in live_tables.get(schema, set()):
                unknown.append(full)
        assert not unknown, (
            f"mj-ddd-semantics references unknown tables: {sorted(unknown)}; "
            f"either the SKILL is stale or DB schema drifted"
        )


class TestSkillMetricColumnsResolve:
    """Sample the ``daily _total`` table and verify metric column patterns
    declared in the SKILL §模式 1 actually exist."""

    def test_daily_total_metric_columns(
        self, catalog: dict, live_tables: dict[str, set[str]]
    ) -> None:
        biz_dws = live_tables.get("biz_dws", set())
        # Pick the first qrynum daily _total table (catalog says these exist)
        candidates = sorted(
            t for t in biz_dws if t.startswith("dws_qcm_qrynum_daily") and t.endswith("_total")
        )
        if not candidates:
            pytest.skip(
                "no daily qrynum _total table in DB; covered by qcm_catalog test"
            )
        desc = describe_biz_table(f"biz_dws.{candidates[0]}")
        cols = {c["name"].lower() for c in desc["columns"]}
        # SKILL §模式 1 declares: day_<metric> + same prev/diff/rate columns
        for required in ("data_date", "day_qrynum", "prev_day_qrynum", "dod_qrynum_diff", "dod_qrynum_rate"):
            assert required in cols, (
                f"SKILL §模式 1 expects '{required}' in {candidates[0]} "
                f"but col not found (cols: {sorted(cols)[:8]}...)"
            )

    def test_monthly_total_quantile_family(
        self, live_tables: dict[str, set[str]]
    ) -> None:
        """SKILL §模式 1 weekly+ table claim: daily_<metric>_{avg,max,min,...} 分位数族."""
        biz_dws = live_tables.get("biz_dws", set())
        candidates = sorted(
            t for t in biz_dws if t.startswith("dws_qcm_qrynum_monthly") and t.endswith("_total")
        )
        if not candidates:
            pytest.skip("no monthly qrynum _total in DB")
        desc = describe_biz_table(f"biz_dws.{candidates[0]}")
        cols = {c["name"].lower() for c in desc["columns"]}
        # Catalog metric_column_shapes.monthly.quantile_family
        for q in ("daily_qrynum_avg", "daily_qrynum_max", "daily_qrynum_min"):
            assert q in cols, (
                f"SKILL/catalog claims monthly _total has '{q}' but missing in "
                f"{candidates[0]} (cols sample: {sorted(cols)[:8]}...)"
            )
