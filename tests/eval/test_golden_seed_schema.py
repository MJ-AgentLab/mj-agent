"""Validate the structural integrity of ``golden_seed.jsonl``.

This test runs without DB or LLM access — it only parses the seed file
and asserts the schema each case promises (per evals-design.md v1.1).
The actual outcome eval (rows match expected) requires a live DB and is
covered by the smoke layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_SEED_PATH = Path(__file__).parent / "golden_seed.jsonl"


def _load_seeds() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with _SEED_PATH.open(encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            cases.append(json.loads(line))
            del line_no
    return cases


SEEDS: list[dict[str, Any]] = _load_seeds()


def test_seed_file_present_and_nonempty() -> None:
    assert _SEED_PATH.exists(), "golden_seed.jsonl must ship in tests/eval/"
    assert SEEDS, "golden_seed.jsonl is empty"
    assert len(SEEDS) >= 15, f"expected ≥15 seed cases, got {len(SEEDS)}"


@pytest.mark.parametrize("seed", SEEDS, ids=lambda s: s["id"])
def test_seed_top_level_schema(seed: dict[str, Any]) -> None:
    """Each case must declare these keys (evals-design v1.1 §4.2)."""
    expected_keys = {
        "id", "source", "version", "tags", "difficulty",
        "biz_schema_version", "input", "expected", "meta",
    }
    missing = expected_keys - seed.keys()
    assert not missing, f"{seed.get('id', '<no-id>')}: missing {sorted(missing)}"


@pytest.mark.parametrize("seed", SEEDS, ids=lambda s: s["id"])
def test_seed_input_schema(seed: dict[str, Any]) -> None:
    inp = seed["input"]
    assert "question" in inp and inp["question"], f"{seed['id']}: empty question"
    assert "user_context" in inp


@pytest.mark.parametrize("seed", SEEDS, ids=lambda s: s["id"])
def test_seed_expected_schema(seed: dict[str, Any]) -> None:
    exp = seed["expected"]
    assert "result_checks" in exp and isinstance(exp["result_checks"], list)
    assert "trajectory" in exp
    assert "sql_checks" in exp
    # Query cases carry reference_sql; clarification-style cases (agent
    # should ask the user, not produce SQL) carry reference_narrative
    # only. At least one must be present.
    has_sql = bool(exp.get("reference_sql", "").strip()) if isinstance(
        exp.get("reference_sql"), str
    ) else False
    has_narrative = bool(exp.get("reference_narrative", "").strip()) if isinstance(
        exp.get("reference_narrative"), str
    ) else False
    assert has_sql or has_narrative, (
        f"{seed['id']}: must carry either reference_sql or reference_narrative"
    )


@pytest.mark.parametrize("seed", SEEDS, ids=lambda s: s["id"])
def test_seed_difficulty_in_set(seed: dict[str, Any]) -> None:
    assert seed["difficulty"] in {"easy", "medium", "hard"}


def test_seed_id_uniqueness() -> None:
    ids = [s["id"] for s in SEEDS]
    assert len(ids) == len(set(ids)), "duplicate seed ids"


def test_seed_difficulty_distribution() -> None:
    """Eval design implies a healthy mix; track the breakdown."""
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for s in SEEDS:
        counts[s["difficulty"]] += 1
    # baseline: at least one of each tier — looser than evals-design but
    # sufficient as a regression guard for seed evolution
    for tier, n in counts.items():
        assert n > 0, f"no {tier} cases in golden seed"
