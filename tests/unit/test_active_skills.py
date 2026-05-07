"""Sanity tests for the active skill load (MVP PR3 + Phase 1 sub 1.D)."""

from __future__ import annotations

import pytest

from mj_agent.agent import _ACTIVE_SKILLS, _build_system_prompt
from mj_agent.skills import load_skill, load_skill_meta


def test_active_skills_phase1() -> None:
    """Phase 1 sub 1.D inserts mj-ddd-semantics between context and templates."""
    assert _ACTIVE_SKILLS == (
        "biz-domain-context",
        "mj-ddd-semantics",
        "qcm-analysis",
        "safe-sql-analysis",
    )


@pytest.mark.parametrize(
    "name",
    [
        "biz-domain-context",
        "mj-ddd-semantics",
        "qcm-analysis",
        "safe-sql-analysis",
    ],
)
def test_active_skills_loadable(name: str) -> None:
    body = load_skill(name)
    # Must include the canonical heading
    assert f"# Skill: {name}" in body
    # Frontmatter must declare active state
    meta = load_skill_meta(name)
    assert meta.get("state") == "active"
    assert meta.get("track") == "agent"


def test_query_writing_deprecated() -> None:
    meta = load_skill_meta("query-writing")
    assert meta.get("state") == "deprecated"
    # And it should NOT be in the active list.
    assert "query-writing" not in _ACTIVE_SKILLS


def test_system_prompt_concatenates_active_skills() -> None:
    prompt = _build_system_prompt()
    # Each active skill heading appears once
    assert prompt.count("# Skill: biz-domain-context") == 1
    assert prompt.count("# Skill: mj-ddd-semantics") == 1
    assert prompt.count("# Skill: qcm-analysis") == 1
    assert prompt.count("# Skill: safe-sql-analysis") == 1
    # query-writing must NOT be loaded into the active prompt
    assert "# Skill: query-writing" not in prompt
