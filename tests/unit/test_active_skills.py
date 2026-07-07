"""Sanity tests for the active skill load (MVP PR3 → Phase 1 sub 1.D → 1.E)."""

from __future__ import annotations

import pytest

from mj_agent.agent import _ACTIVE_SKILLS, _build_system_prompt
from mj_agent.config import Settings
from mj_agent.skills import load_skill, load_skill_meta

_PHASE1_SUB_E_SKILLS = (
    "biz-schema-exploration",
    "biz-domain-context",
    "mj-ddd-semantics",
    "qcm-analysis",
    "query-writing",
    "monthly-report",
    "safe-sql-analysis",
    "query-optimization",
)


def test_active_skills_phase1_sub_e() -> None:
    """Phase 1 sub 1.E expands to 8 active skills (3 bands)."""
    assert _ACTIVE_SKILLS == _PHASE1_SUB_E_SKILLS


@pytest.mark.parametrize("name", _PHASE1_SUB_E_SKILLS)
def test_active_skills_loadable(name: str) -> None:
    body = load_skill(name)
    # Must include the canonical heading
    assert f"# Skill: {name}" in body
    # Frontmatter must declare active state
    meta = load_skill_meta(name)
    assert meta.get("state") == "active"
    assert meta.get("track") == "agent"


def test_query_writing_revived_v10() -> None:
    """1.E revives query-writing from deprecated → active v1.0 with narrowed scope."""
    meta = load_skill_meta("query-writing")
    assert meta.get("state") == "active"
    assert meta.get("version") == "v1.0"
    assert "query-writing" in _ACTIVE_SKILLS


def test_system_prompt_concatenates_eight_skills() -> None:
    prompt = _build_system_prompt()
    for name in _PHASE1_SUB_E_SKILLS:
        assert prompt.count(f"# Skill: {name}") == 1, f"missing or duplicate: {name}"


def test_system_prompt_band_ordering() -> None:
    """3-band ordering: recall & entity → authoring → execute & optimize."""
    prompt = _build_system_prompt()
    idx = {name: prompt.index(f"# Skill: {name}") for name in _PHASE1_SUB_E_SKILLS}
    # Recall & entity 前
    assert idx["biz-schema-exploration"] < idx["mj-ddd-semantics"]
    assert idx["biz-domain-context"] < idx["mj-ddd-semantics"]
    # Authoring 中段
    assert idx["mj-ddd-semantics"] < idx["safe-sql-analysis"]
    assert idx["qcm-analysis"] < idx["safe-sql-analysis"]
    assert idx["query-writing"] < idx["safe-sql-analysis"]
    assert idx["monthly-report"] < idx["safe-sql-analysis"]
    # Execute / optimize 后段
    assert idx["safe-sql-analysis"] < idx["query-optimization"]


def test_system_prompt_contains_runtime_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bugfix #285: the agent must know its deployment provider + model id.

    Without this the only model-name string in LLM context is whatever leaks
    through tool schemas, and the agent misreports its own identity.
    """
    import mj_agent.agent as agent_mod

    monkeypatch.setattr(
        agent_mod,
        "settings",
        Settings(
            _env_file=None,
            llm_provider="local-openai-compat",
            llm_model_id="test-model-xyz",
        ),
    )
    prompt = _build_system_prompt()
    assert "# Runtime" in prompt
    assert "local-openai-compat" in prompt
    assert "test-model-xyz" in prompt


def test_runtime_identity_placement() -> None:
    """Runtime section sits between base identity and the skill block."""
    prompt = _build_system_prompt()
    assert prompt.index("# Identity") < prompt.index("# Runtime")
    assert prompt.index("# Runtime") < prompt.index("# Skill: biz-schema-exploration")
