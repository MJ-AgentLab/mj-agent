"""Contract: ``mj-ddd-semantics/SKILL.md`` claims vs a sanitized biz-schema snapshot.

Light-touch — extracts table names referenced in the SKILL body and asserts each one
resolves in the snapshot payload, then checks that the metric-column families the SKILL
declares in §模式 1 are present on the corresponding ``_total`` tables.

**Offline by construction (Epic #499 PR-0c).** This used to introspect the live business
warehouse behind a ``live_db`` credential gate, which meant it always skipped. It now reads
a hand-authored synthetic snapshot fixture, so it runs for real in CI, and it imports no
introspection wrapper, no database client and no dotenv (AC-08).

Real-data drift detection is a separate concern and lives in ``scripts/diff_biz_schema.py``,
which consumes an Owner-attested sanitized snapshot from ``.mj-agent-local/`` and reports
``SKIP_NO_SNAPSHOT`` / ``SKIP_STALE_SNAPSHOT`` rather than pretending to be current.
"""

from __future__ import annotations

import re

import pytest

from mj_agent.skills import load_skill
from tests.contract.snapshot_fixtures import columns_of, load_valid_payload, tables_of

pytestmark = pytest.mark.contract

_TABLE_REF = re.compile(r"\bbiz_(?:dws|dwd)\.[a-z_]+\b")


@pytest.fixture(scope="module")
def snapshot_tables() -> dict[str, set[str]]:
    return tables_of(load_valid_payload())


@pytest.fixture(scope="module")
def skill_body() -> str:
    body = load_skill("mj-ddd-semantics")
    assert body.strip(), "mj-ddd-semantics SKILL body is empty"
    return body


class TestSkillTableReferences:
    """Every ``biz_(dws|dwd).<table>`` referenced in SKILL must resolve in the snapshot."""

    def test_table_references_resolve(
        self, skill_body: str, snapshot_tables: dict[str, set[str]]
    ) -> None:
        # Note there is deliberately no placeholder filter here. The previous
        # `"<" not in ref` guard was dead code: `_TABLE_REF`'s `[a-z_]+` class cannot match
        # `<` or `>`, so it removed 0 of 0 items and merely implied a protection that did
        # not exist. Angle-bracket patterns simply never reach this set.
        concrete = set(_TABLE_REF.findall(skill_body))
        assert concrete, "no concrete biz_dws/biz_dwd table refs found in SKILL"

        unknown: list[str] = []
        for full in concrete:
            schema, name = full.split(".", 1)
            if name not in snapshot_tables.get(schema, set()):
                unknown.append(full)
        assert not unknown, (
            f"mj-ddd-semantics references tables absent from the synthetic snapshot: "
            f"{sorted(unknown)}; either the SKILL changed or "
            f"tests/contract/fixtures/biz_snapshots/valid_fresh.yaml needs the new table"
        )


class TestSkillMetricColumnsResolve:
    """Sample the ``daily`` / ``monthly`` ``_total`` tables and verify the metric column
    families declared in the SKILL §模式 1 are present."""

    def test_daily_total_metric_columns(self, snapshot_tables: dict[str, set[str]]) -> None:
        payload = load_valid_payload()
        biz_dws = snapshot_tables.get("biz_dws", set())
        candidates = sorted(
            t for t in biz_dws if t.startswith("dws_qcm_qrynum_daily") and t.endswith("_total")
        )
        assert candidates, (
            "synthetic snapshot has no daily qrynum _total table; the fixture must keep one "
            "so this contract cannot pass vacuously"
        )
        cols = {c.lower() for c in columns_of(payload, f"biz_dws.{candidates[0]}")}
        for required in (
            "data_date",
            "day_qrynum",
            "prev_day_qrynum",
            "dod_qrynum_diff",
            "dod_qrynum_rate",
        ):
            assert required in cols, (
                f"SKILL §模式 1 expects '{required}' in {candidates[0]} "
                f"but col not found (cols: {sorted(cols)[:8]}...)"
            )

    def test_monthly_total_quantile_family(self, snapshot_tables: dict[str, set[str]]) -> None:
        """SKILL §模式 1 weekly+ table claim: daily_<metric>_{avg,max,min,...} 分位数族."""
        payload = load_valid_payload()
        biz_dws = snapshot_tables.get("biz_dws", set())
        candidates = sorted(
            t for t in biz_dws if t.startswith("dws_qcm_qrynum_monthly") and t.endswith("_total")
        )
        assert candidates, (
            "synthetic snapshot has no monthly qrynum _total table; the fixture must keep "
            "one so this contract cannot pass vacuously"
        )
        cols = {c.lower() for c in columns_of(payload, f"biz_dws.{candidates[0]}")}
        for q in ("daily_qrynum_avg", "daily_qrynum_max", "daily_qrynum_min"):
            assert q in cols, (
                f"SKILL/catalog claims monthly _total has '{q}' but missing in "
                f"{candidates[0]} (cols sample: {sorted(cols)[:8]}...)"
            )
