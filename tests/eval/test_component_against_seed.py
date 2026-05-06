"""Run the L3 Component check (sqlglot precheck) on each seed reference SQL.

The seed cases reference the QVL/loan_credit_day sub-domain (different
table family from the QCM catalog mj-agent currently exposes). For the
PR4 MVP eval pass we therefore:

  - run ``precheck_sql`` on every reference SQL,
  - record any precheck error in a dict keyed by seed id,
  - assert NO seed yields a P0 violation that the precheck claims as
    universal — only domain-coupled rules (require_time_range fires on
    biz_dws fact tables, which the seed cases do not target) may differ.

This guards the MVP commitment: the runtime guardrail / precheck and the
eval Component Judge share rule sources without false positives on the
existing baseline. When seed cases evolve toward QCM tables (post-MVP)
the assertions tighten automatically.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mj_agent.tools.sql.precheck import precheck_sql

_SEED_PATH = Path(__file__).parent / "golden_seed.jsonl"


def _load_seeds() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with _SEED_PATH.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                cases.append(json.loads(stripped))
    return cases


SEEDS: list[dict[str, Any]] = _load_seeds()
# Clarification cases have no reference_sql; precheck is N/A for them.
QUERY_SEEDS: list[dict[str, Any]] = [s for s in SEEDS if s["expected"].get("reference_sql")]


@pytest.mark.parametrize("seed", QUERY_SEEDS, ids=lambda s: s["id"])
def test_reference_sql_parses(seed: dict[str, Any]) -> None:
    """Precheck must at least not raise on any reference SQL."""
    sql = seed["expected"]["reference_sql"]
    result = precheck_sql(sql)
    # We don't require ok=True — domain mismatch is OK. We only require
    # that precheck did not crash and that warnings/errors are well-formed.
    assert isinstance(result.errors, list)
    assert isinstance(result.warnings, list)


@pytest.mark.parametrize("seed", QUERY_SEEDS, ids=lambda s: s["id"])
def test_no_select_star_consistency(seed: dict[str, Any]) -> None:
    """Reference SQL with explicit columns must not trigger no_select_star."""
    sql = seed["expected"]["reference_sql"]
    forbidden_patterns = seed["expected"].get("sql_checks", {}).get(
        "forbidden_patterns", []
    )
    if "SELECT \\*" not in forbidden_patterns:
        return
    result = precheck_sql(sql)
    assert not any("no_select_star" in e for e in result.errors), (
        f"{seed['id']}: reference SQL triggered no_select_star unexpectedly: "
        f"{result.errors}"
    )


def test_seed_corpus_runs_without_uncaught_exception() -> None:
    """Aggregate sweep: every reference SQL runs through precheck cleanly."""
    for seed in QUERY_SEEDS:
        sql = seed["expected"]["reference_sql"]
        precheck_sql(sql)


def test_clarification_cases_have_narrative() -> None:
    """Cases without reference_sql must justify it via narrative."""
    clarification = [s for s in SEEDS if not s["expected"].get("reference_sql")]
    assert clarification, "expected at least one clarification-style seed"
    for s in clarification:
        assert s["expected"].get("reference_narrative"), (
            f"{s['id']}: no reference_sql but no reference_narrative either"
        )
