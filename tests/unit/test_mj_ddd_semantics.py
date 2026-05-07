"""Phase 1 sub 1.D — mj-ddd-semantics skill loaded + active.

Contract test fixture lives here too (Phase 1 sub 1.G activates it
under tests/contract/; for now just unit-level shape checks).
"""

from __future__ import annotations

import pytest

from mj_agent.agent import _ACTIVE_SKILLS, _build_system_prompt
from mj_agent.skills import load_skill, load_skill_meta


def test_mj_ddd_semantics_in_active_skills() -> None:
    assert "mj-ddd-semantics" in _ACTIVE_SKILLS


def test_mj_ddd_semantics_loadable_and_active() -> None:
    body = load_skill("mj-ddd-semantics")
    assert "# Skill: mj-ddd-semantics" in body
    meta = load_skill_meta("mj-ddd-semantics")
    assert meta["state"] == "active"
    assert meta["track"] == "agent"
    assert meta["version"] == "v0.1"


def test_mj_ddd_semantics_in_system_prompt() -> None:
    """system prompt embeds mj-ddd-semantics between recall and templates."""
    prompt = _build_system_prompt()
    assert prompt.count("# Skill: biz-domain-context") == 1
    assert prompt.count("# Skill: mj-ddd-semantics") == 1
    assert prompt.count("# Skill: qcm-analysis") == 1
    assert prompt.count("# Skill: safe-sql-analysis") == 1
    # Order: catalog recall → DDD → templates → discipline
    idx = {
        name: prompt.index(f"# Skill: {name}")
        for name in (
            "biz-domain-context",
            "mj-ddd-semantics",
            "qcm-analysis",
            "safe-sql-analysis",
        )
    }
    assert (
        idx["biz-domain-context"]
        < idx["mj-ddd-semantics"]
        < idx["qcm-analysis"]
        < idx["safe-sql-analysis"]
    )


def test_active_skills_count() -> None:
    """Skill count: 4 after 1.D, 8 after 1.E (Phase 1 sub 1.E expansion)."""
    assert len(_ACTIVE_SKILLS) == 8


@pytest.mark.parametrize(
    "concept,expected_excerpt",
    [
        # 业务概念 → 物理列映射（核心契约）
        ("metric 列形态", "day_<metric>"),
        ("分位数族", "daily_<metric>_{avg,max,min,std,q25,median,q75}"),
        ("同环比", "prev_<period>_<metric_column>"),
        ("机构生命周期", "hist_active_<period>s_count"),
        ("ready_signal", "dws_qcm_ready_signal"),
        # 维表 JOIN
        ("tenant_id", "biz_dwd.dwd_dim_institution"),
        # 反模式
        ("不要在 daily 周期用", "_sum"),
        ("不要用 LAG", "prev/diff/rate"),
    ],
)
def test_skill_body_codifies_key_mappings(concept: str, expected_excerpt: str) -> None:
    """The SKILL body must surface the named DDD mappings verbatim."""
    body = load_skill("mj-ddd-semantics")
    assert expected_excerpt in body, f"missing for concept '{concept}': {expected_excerpt}"
