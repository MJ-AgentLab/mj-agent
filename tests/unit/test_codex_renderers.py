"""Focused output-class renderer tests — Epic #499 PR-B layer B3 (plan §2.6).

codex_config_renderer: extraction byte-identity (the rendered config equals the
committed real-tree `.codex/config.toml` byte for byte — zero real-tree diff),
plus fail-closed refusals surfacing as ConfigRenderError.

codex_readme_renderer: template + manifest-derived strategy statistics with a
closed placeholder vocabulary; counts derived, never hardcoded (AC-04); output
normalized to LF with exactly one final newline (generated-utf8-lf-v1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from scripts.sdd._common.codex_config_renderer import (
    ConfigRenderError,
    render_codex_config,
)
from scripts.sdd._common.codex_readme_renderer import (
    KNOWN_PLACEHOLDERS,
    ReadmeRenderError,
    render_skills_readme,
    strategy_summary,
)
from scripts.sdd.agents_sync import _load_mcp_json
from scripts.sdd.check_agents_projection import load_mcp_projection

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPO_ROOT / "sdd" / "adapters" / "codex-skills-readme.md"

POSTURE = {
    "approval_policy": "on-request",
    "sandbox_mode": "workspace-write",
    "project_doc_max_bytes": 65536,
}


# ------------------------------------------------------------ config renderer


def test_extraction_is_byte_identical_on_real_tree() -> None:
    """The focused module renders EXACTLY the committed real-tree config —
    the extraction may not change a single byte (zero real-tree diff)."""
    mcp_project, posture, _never = load_mcp_projection(REPO_ROOT)
    rendered = render_codex_config(mcp_project, posture, _load_mcp_json(REPO_ROOT))
    on_disk = (REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert rendered == on_disk.replace("\r\n", "\n")


def test_missing_posture_refuses() -> None:
    with pytest.raises(ConfigRenderError, match="codex.posture"):
        render_codex_config({"github": {}}, None, {"github": {"command": "x"}})


def test_env_literal_refuses() -> None:
    servers = {"github": {"command": "x", "env": {"TOKEN": "literal-secret"}}}
    with pytest.raises(ConfigRenderError, match="pure"):
        render_codex_config({"github": {}}, POSTURE, servers)


def test_non_stdio_type_refuses() -> None:
    servers = {"github": {"command": "x", "type": "sse"}}
    with pytest.raises(ConfigRenderError, match="stdio"):
        render_codex_config({"github": {}}, POSTURE, servers)


# ------------------------------------------------------------ readme renderer


def _caps(byte_copy: int, translated: int, none: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in range(byte_copy):
        rows.append({"id": f"mj-agent-b{i}", "codex_carrier": "byte-copy"})
    for i in range(translated):
        rows.append({"id": f"mj-agent-t{i}", "codex_carrier": "translated"})
    for i in range(none):
        rows.append({"id": f"mj-agent-n{i}", "codex_carrier": "none"})
    return rows


def test_strategy_summary_is_derived_not_hardcoded() -> None:
    assert "5 byte-copy + 13 translated" in strategy_summary(_caps(5, 13, 19))
    assert "2 byte-copy + 3 translated" in strategy_summary(_caps(2, 3, 0))
    with pytest.raises(ReadmeRenderError, match="codex_carrier"):
        strategy_summary([{"id": "mj-agent-x", "codex_carrier": "hand-authored"}])
    with pytest.raises(ReadmeRenderError):
        strategy_summary([{"id": "mj-agent-x"}])  # v1 row without a carrier


def test_render_readme_from_real_template_is_deterministic() -> None:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    first = render_skills_readme(template, _caps(5, 13, 19))
    second = render_skills_readme(template, _caps(5, 13, 19))
    assert first == second
    assert "{{" not in first
    assert first.endswith("\n") and not first.endswith("\n\n")
    assert "\r" not in first
    assert "18 skills carry a Codex projection" in first


def test_unknown_placeholder_fails_closed() -> None:
    with pytest.raises(ReadmeRenderError, match="closed"):
        render_skills_readme("# x\n\n{{surprise_token}}\n", _caps(1, 0, 0))


def test_missing_required_placeholder_fails_closed() -> None:
    with pytest.raises(ReadmeRenderError, match="missing"):
        render_skills_readme("# x\n\nno placeholders here\n", _caps(1, 0, 0))


def test_real_template_uses_only_known_placeholders() -> None:
    import re

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    tokens = set(re.findall(r"\{\{([a-z0-9_]*)\}\}", template))
    assert tokens == set(KNOWN_PLACEHOLDERS)
