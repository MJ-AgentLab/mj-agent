"""Unit tests for ``estimate_tokens`` (ADR-012 budget gate)."""

from __future__ import annotations

import pytest

from mj_agent.config import Settings
from mj_agent.tools.analysis import estimate_tokens
from mj_agent.tools.analysis.token_estimator import DEFAULT_TOKEN_BUDGET


def test_small_set_within_budget() -> None:
    rows = [{"a": i, "b": f"row-{i}"} for i in range(5)]
    r = estimate_tokens(rows)
    assert r["within_budget"] is True
    assert r["row_count"] == 5
    assert r["budget"] == DEFAULT_TOKEN_BUDGET
    assert r["suggestion"] is None
    assert r["token_count"] > 0


def test_huge_set_exceeds_budget() -> None:
    rows = [{"col": "x" * 200} for _ in range(500)]
    r = estimate_tokens(rows, budget=100)
    assert r["within_budget"] is False
    assert r["token_count"] > 100
    assert r["suggestion"] is not None
    assert "aggregate" in r["suggestion"]
    assert "drill_down" in r["suggestion"]


def test_unknown_model_falls_back_to_cl100k() -> None:
    rows = [{"a": 1, "b": 2}]
    r = estimate_tokens(rows, model_id="not-a-real-model")
    # Should not raise; just use the cl100k_base fallback.
    assert r["token_count"] > 0


def test_budget_zero_rejected() -> None:
    with pytest.raises(ValueError, match="budget must be > 0"):
        estimate_tokens([{"a": 1}], budget=0)


def test_empty_rows() -> None:
    r = estimate_tokens([])
    assert r["row_count"] == 0
    # JSON empty list is "[]" → small but non-zero tokens
    assert r["token_count"] >= 1
    assert r["within_budget"] is True


def test_default_budget_matches_adr012() -> None:
    """ADR-012 says 5000 tokens default budget."""
    assert DEFAULT_TOKEN_BUDGET == 5000


def test_compact_serialization() -> None:
    """Compact JSON keeps token count realistic for budgeting."""
    rows = [{"k": "v"}]
    r = estimate_tokens(rows)
    # Single small row should be << 50 tokens; verifies separators=(',',':')
    assert r["token_count"] < 50


def test_default_model_id_resolves_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bugfix #285: omitting model_id resolves to the deployment model.

    A hardcoded vendor default would leak into the LLM tool schema and get
    misread as the agent's own identity.
    """
    import mj_agent.tools.analysis.token_estimator as te_mod

    monkeypatch.setattr(
        te_mod, "settings", Settings(_env_file=None, llm_model_id="test-model-xyz")
    )
    r = estimate_tokens([{"a": 1}])
    assert r["model_id"] == "test-model-xyz"


def test_none_model_id_resolves_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit None (e.g. the LLM passes null) also resolves to settings."""
    import mj_agent.tools.analysis.token_estimator as te_mod

    monkeypatch.setattr(
        te_mod, "settings", Settings(_env_file=None, llm_model_id="test-model-xyz")
    )
    r = estimate_tokens([{"a": 1}], model_id=None)
    assert r["model_id"] == "test-model-xyz"


def test_explicit_model_id_still_honored() -> None:
    """An explicit model_id argument is used and echoed as-is."""
    r = estimate_tokens([{"a": 1}], model_id="gpt-4o")
    assert r["model_id"] == "gpt-4o"
