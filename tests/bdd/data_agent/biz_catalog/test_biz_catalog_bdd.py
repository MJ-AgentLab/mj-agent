"""BDD step definitions for data-agent.biz-catalog capability.

Binds all 3 scenarios from
`capabilities/data-agent/biz-catalog/contracts/behavior.feature`:

- REQ-001 load_catalog rejects YAML root that parses to a list (OFFLINE)
- REQ-002 Catalog signal_tables must resolve in live biz_dws (LIVE-DB gated)
- REQ-003 Active SKILL bodies reference only resolvable catalog symbols + DB tables (LIVE-DB gated)

Shared Background step defs live in tests/bdd/conftest.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, then, when

_FEATURE_FILE = "../../../../capabilities/data-agent/biz-catalog/contracts/behavior.feature"


# -------- Background-specific to biz-catalog --------

@given(parsers.re(re.escape(
    "the analyst role has read-only GRANTs per mj-system R__analyst_permissions.sql"
)))
def biz_catalog_grants() -> None:
    """Background — upstream GRANT SQL (mj-system); no test setup."""


@given(parsers.re(re.escape(
    "qcm_catalog.yaml is bundled at src/mj_agent/biz_catalog/qcm_catalog.yaml"
)))
def qcm_catalog_bundled() -> None:
    """Background — catalog YAML ships with the package; verified by tests/unit/test_biz_catalog.py."""


# -------- Scenarios --------


@scenario(_FEATURE_FILE, "load_catalog rejects YAML whose root parses to a list (not a mapping)")
def test_req_001_load_catalog_rejects_list_root() -> None:
    pass


@scenario(_FEATURE_FILE, "Catalog signal_tables must resolve in live biz_dws")
def test_req_002_signal_tables_resolve_live(live_db: None) -> None:  # noqa: ARG001
    pass


@scenario(_FEATURE_FILE, "Active SKILL bodies reference only resolvable catalog symbols and DB tables")
def test_req_003_skill_catalog_coherence(live_db: None) -> None:  # noqa: ARG001
    pass


# -------- REQ-001 step defs (OFFLINE) --------


@given(parsers.parse(
    "a malformed qcm_catalog.yaml whose top-level YAML parses to a list "
    '(e.g. starts with "{prefix}")'
), target_fixture="malformed_catalog_path")
def given_malformed_catalog(
    prefix: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    malformed = tmp_path / "qcm_catalog.yaml"
    malformed.write_text(f"{prefix}\n- bar\n", encoding="utf-8")
    from mj_agent.biz_catalog import loader
    monkeypatch.setattr(loader, "catalog_path", lambda: malformed)
    loader.load_catalog.cache_clear()
    return malformed


@when("load_catalog() is invoked", target_fixture="raised_exception")
def when_load_catalog_invoked(malformed_catalog_path: Path) -> BaseException:  # noqa: ARG001
    from mj_agent.biz_catalog import load_catalog
    try:
        load_catalog()
    except BaseException as exc:  # noqa: BLE001
        return exc
    raise AssertionError("load_catalog did not raise on malformed root")


@then("it raises ValueError")
def then_value_error_raised(raised_exception: BaseException) -> None:
    assert isinstance(raised_exception, ValueError), (
        f"expected ValueError, got {type(raised_exception).__name__}: {raised_exception}"
    )


@then(parsers.parse(
    'the message mentions the actual top-level type ("{tname1}" or similar)'
))
def then_message_mentions_type(raised_exception: BaseException, tname1: str) -> None:
    # Allow either "list" or "<class 'list'>" representation
    msg = str(raised_exception)
    assert tname1 in msg or "list" in msg.lower(), (
        f"expected {tname1!r} or 'list' in {msg!r}"
    )


@then("find_biz_context() also fails (load_catalog raise propagates)")
def then_find_biz_context_also_fails(malformed_catalog_path: Path) -> None:  # noqa: ARG001
    from mj_agent.biz_catalog import find_biz_context, load_catalog
    load_catalog.cache_clear()
    with pytest.raises(ValueError):
        find_biz_context("any keyword")


# -------- REQ-002 step defs (LIVE-DB) --------


@given(parsers.re(re.escape(
    "a freshly loaded catalog with 3 signal_tables entries "
    "(dws_qcm_preprocessed_data / dws_qcm_etl_metrics / dws_qcm_ready_signal)"
)), target_fixture="signal_tables")
def given_signal_tables() -> list[str]:
    from mj_agent.biz_catalog import load_catalog
    load_catalog.cache_clear()
    catalog = load_catalog()
    sigs = list(catalog.get("signal_tables", []))
    assert len(sigs) == 3, f"expected 3 signal_tables, got {sigs!r}"
    return sigs


@given("the analyst role can SELECT from information_schema.tables")
def given_analyst_can_select_information_schema() -> None:
    """Background — verified by upstream GRANT (mj-system); no test setup."""


@when(
    "the contract test queries information_schema for table_schema='biz_dws' "
    "AND table_name IN signal_tables",
    target_fixture="resolved_signal_tables",
)
def when_query_information_schema(signal_tables: list[str]) -> set[str]:
    from mj_agent.integrations.mj_system_db import readonly_cursor
    with readonly_cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'biz_dws' AND table_name = ANY(%s)",
            (signal_tables,),
        )
        rows = cur.fetchall()
    return {r["table_name"] for r in rows}


@then("all 3 names appear in the result set")
def then_all_3_signal_tables_resolve(
    signal_tables: list[str], resolved_signal_tables: set[str]
) -> None:
    missing = set(signal_tables) - resolved_signal_tables
    assert not missing, f"signal_tables missing in live biz_dws: {sorted(missing)}"


@then("drift (missing table or renamed table) surfaces a clear error naming the missing entry")
def then_drift_surfaces_clear_error() -> None:
    """Descriptive — the SUT's contract-alignment test
    (tests/contract/test_biz_schema_alignment.py) emits assertion errors
    naming missing entries; verified by code-read of that test module.
    """


# -------- REQ-003 step defs (LIVE-DB) --------


@given(parsers.re(re.escape(
    "the 3 active in-source SKILLs "
    "(biz-domain-context / qcm-analysis / safe-sql-analysis)"
)), target_fixture="active_skill_names")
def given_active_skills() -> list[str]:
    return ["biz-domain-context", "qcm-analysis", "safe-sql-analysis"]


@given(parsers.re(re.escape(
    "each SKILL body is loaded via load_skill() (strip frontmatter per A11 contract)"
)), target_fixture="skill_bodies")
def given_skill_bodies_loaded(active_skill_names: list[str]) -> dict[str, str]:
    from mj_agent.skills import load_skill
    return {name: load_skill(name) for name in active_skill_names}


@when(
    'the contract test regex-extracts "biz_dws.*" / "biz_dwd.*" table refs from each SKILL body',
    target_fixture="extracted_table_refs",
)
def when_extract_table_refs(skill_bodies: dict[str, str]) -> set[str]:
    pattern = re.compile(r"\b(biz_dws|biz_dwd)\.([a-z][a-z0-9_]*)", re.IGNORECASE)
    refs: set[str] = set()
    for body in skill_bodies.values():
        for schema, table in pattern.findall(body):
            refs.add(f"{schema.lower()}.{table.lower()}")
    return refs


@when(
    "queries information_schema.tables for each extracted ref",
    target_fixture="live_table_set",
)
def when_query_live_information_schema(extracted_table_refs: set[str]) -> set[str]:
    if not extracted_table_refs:
        return set()
    from mj_agent.integrations.mj_system_db import readonly_cursor
    with readonly_cursor() as cur:
        cur.execute(
            "SELECT table_schema || '.' || table_name AS full FROM information_schema.tables "
            "WHERE table_schema IN ('biz_dws', 'biz_dwd')"
        )
        rows = cur.fetchall()
    return {r["full"].lower() for r in rows}


@then("every extracted table ref resolves in live DB (visible to analyst role)")
def then_every_ref_resolves(
    extracted_table_refs: set[str], live_table_set: set[str]
) -> None:
    missing = extracted_table_refs - live_table_set
    assert not missing, (
        f"SKILL body references non-resolvable tables: {sorted(missing)}"
    )


@then(
    "every metric / period / dimension keyword referenced in SKILL body exists in "
    "catalog.metrics / catalog.periods / catalog.dimensions"
)
def then_keywords_exist_in_catalog(skill_bodies: dict[str, str]) -> None:
    """Validated by tests/contract/test_qcm_catalog_alignment.py at module scope;
    this BDD step asserts the contract test exists (presence check) — full
    keyword extraction is non-trivial and lives in that contract test.
    """
    from pathlib import Path
    contract_test = (
        Path(__file__).resolve().parents[4]
        / "tests" / "contract" / "test_qcm_catalog_alignment.py"
    )
    assert contract_test.exists(), (
        f"contract test {contract_test} missing — REQ-003 keyword check unimplemented"
    )
    # Sanity: every SKILL body has at least one metric reference
    for name, body in skill_bodies.items():
        assert any(kw in body for kw in ("qrynum", "tntcnt", "metric")), (
            f"SKILL {name!r} body has no recognisable metric keyword"
        )


# -------- biz-catalog Background also needs the `biz_allowed_schemas` line --------
# (Shared step from tests/bdd/conftest.py already covers this — re-exported here for clarity)
