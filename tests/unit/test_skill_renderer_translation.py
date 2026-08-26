"""Translated-render engine tests — Epic #499 PR-B layer B5 (plan §2.4).

Synthetic golden: one source exercising every construct class (paragraph /
list-item / table / generic fence / dot fence / frontmatter description / T3
link destination / T1a / T1b / no-op passthroughs / Unicode) rendered against
a precommitted golden; the CRLF, BOM, quoted-description and
folded-description input variants must all render BYTE-IDENTICAL to it
(input form never influences the output).

Real 13: every translated source renders deterministically with the real
registry/map/preface; each edge identity appears exactly once; prohibition
lines pass through verbatim with no substitute route (the layer-A fixture
duty (a)+(b)); output wire shape is frontmatter -> preface -> body, LF, one
final newline.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.sdd._common.skill_renderer import (
    InteractionSite,
    TranslationError,
    TranslationMap,
    load_translation_map,
    load_workflow_registry,
    parse_source_document,
    render_translated,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = Path(__file__).resolve().parent / "golden" / "codex_translation"
REGISTRY_PATH = REPO_ROOT / "sdd" / "workflows" / "development-agent-workflows.yml"
MAP_PATH = REPO_ROOT / "sdd" / "adapters" / "codex-skill-translation.yml"
PREFACE_PATH = REPO_ROOT / "sdd" / "adapters" / "codex-skill-preface.md"

SYNTH_REGISTRY = """\
schema_version: 1
workflows:
  - workflow_id: alpha
    capability_id: mj-agent-alpha
    codex_discovery_summary: "Alpha test workflow for alpha work and 触发 paths."
    required_trigger_terms: ["alpha work"]
edges:
  - {id: edge-alpha-beta, from: mj-agent-alpha, to: mj-agent-beta, relation: call, activation: always, closure: carrier-required}
  - id: edge-alpha-gamma
    from: mj-agent-alpha
    to: mj-agent-gamma
    relation: handoff
    activation: conditional
    closure: advisory
    codex_substitute: {kind: inline-procedure, route_ref: route-gamma}
routes:
  - route_id: route-gamma
    text: "perform the gamma procedure manually and record the result."
"""

SYNTH_SOURCE = """\
---
name: mj-agent-alpha
description: Test skill for alpha work（触发）.
---

# mj-agent Alpha

Use `AskUserQuestion` to pick the mode before starting.

## Decide gate

The Owner gate uses AskUserQuestion for the final call.

## Graph

```dot
digraph g { a [label="/mj-agent-beta"]; }
```

## Steps

See [beta source](.claude/skills/mj-agent-beta/SKILL.md), superpowers:brainstorming,
PreToolUse hooks in .claude/settings.json, and Claude tools like Edit.

The prose token /mj-agent-beta here is not an edge.

## Sub-skill Calls

| Sub-skill | when |
|---|---|
| `/mj-agent-beta` | always |

## Handoff

Delegating this to /mj-agent-gamma when needed.

- item /mj-agent-beta call

```
next → /mj-agent-gamma
```
"""


def _synth_map() -> TranslationMap:
    real = load_translation_map(MAP_PATH.read_text(encoding="utf-8"))
    sites = {
        "site-alpha-mode": InteractionSite(
            site_id="site-alpha-mode",
            capability_id="mj-agent-alpha",
            path=".claude/skills/mj-agent-alpha/SKILL.md",
            marker="pick the mode before starting",
            disposition="t1b",
            owner_gate_reason=None,
        ),
        "site-alpha-gate": InteractionSite(
            site_id="site-alpha-gate",
            capability_id="mj-agent-alpha",
            path=".claude/skills/mj-agent-alpha/SKILL.md",
            marker="Owner gate uses AskUserQuestion",
            disposition="t1a",
            owner_gate_reason="declared-contract-change",
        ),
    }
    return TranslationMap(
        lexicon=real.lexicon,
        sites=sites,
        templates=real.templates,
        preface_template_version=real.preface_template_version,
    )


def _render_synth(source: bytes) -> str:
    return render_translated(
        source,
        "mj-agent-alpha",
        load_workflow_registry(SYNTH_REGISTRY),
        _synth_map(),
        PREFACE_PATH.read_text(encoding="utf-8"),
        carrier_ids={"mj-agent-alpha", "mj-agent-beta"},
    )


# ------------------------------------------------------------------- golden


def test_synthetic_golden_all_constructs() -> None:
    rendered = _render_synth(SYNTH_SOURCE.encode("utf-8"))
    golden = (GOLDEN_DIR / "alpha.out.md").read_text(encoding="utf-8")
    assert rendered == golden.replace("\r\n", "\n")


@pytest.mark.parametrize(
    "variant",
    ["crlf", "bom", "quoted", "folded"],
)
def test_input_form_never_changes_output(variant: str) -> None:
    if variant == "crlf":
        source = SYNTH_SOURCE.replace("\n", "\r\n").encode("utf-8")
    elif variant == "bom":
        source = b"\xef\xbb\xbf" + SYNTH_SOURCE.encode("utf-8")
    elif variant == "quoted":
        source = SYNTH_SOURCE.replace(
            "description: Test skill for alpha work（触发）.",
            'description: "Test skill for alpha work（触发）."',
        ).encode("utf-8")
    else:  # folded
        source = SYNTH_SOURCE.replace(
            "description: Test skill for alpha work（触发）.",
            "description: >-\n  Test skill for alpha work（触发）.",
        ).encode("utf-8")
    golden = (GOLDEN_DIR / "alpha.out.md").read_text(encoding="utf-8")
    assert _render_synth(source) == golden.replace("\r\n", "\n")


def test_golden_structure_assertions() -> None:
    rendered = _render_synth(SYNTH_SOURCE.encode("utf-8"))
    # wire shape
    assert rendered.startswith("---\nname: mj-agent-alpha\ndescription: \"")
    assert rendered.endswith("\n") and not rendered.endswith("\n\n")
    assert "\r" not in rendered and "﻿" not in rendered
    # description swapped to the registry summary (JSON-style scalar)
    assert '"Alpha test workflow for alpha work and 触发 paths."' in rendered
    assert "Test skill for alpha work（触发）." not in rendered
    # preface prepended once
    assert rendered.count("Semantic difference declaration") == 1
    # T2a: carrier target rewritten in dot label / table / list; identity once
    assert '[label="$mj-agent-beta"]' in rendered
    assert "| `$mj-agent-beta` | always |" in rendered
    assert "- item $mj-agent-beta call" in rendered
    assert rendered.count("<!-- codex-route:edge-alpha-beta -->") == 1
    # T2a: no-carrier target uses the substitute short form + route text
    assert "Codex substitute edge-alpha-gamma" in rendered
    assert rendered.count("<!-- codex-route:edge-alpha-gamma -->") == 1
    assert "perform the gamma procedure manually" in rendered
    # prose token outside the regions passes through verbatim
    assert "The prose token /mj-agent-beta here is not an edge." in rendered
    # T3 link destination rewritten
    assert "(.agents/skills/mj-agent-beta/SKILL.md)" in rendered
    # no-op passthroughs preserved
    assert "superpowers:brainstorming" in rendered
    assert ".claude/settings.json" in rendered
    # T1b + T1a blocks, each exactly once, with their site ids
    assert rendered.count("[codex-interaction:site-alpha-mode]") == 1
    assert rendered.count("[codex-owner-gate:site-alpha-gate]") == 1
    assert "OWNER_APPROVAL_REQUIRED(declared-contract-change)" in rendered


# ------------------------------------------------------------------ real 13


def _real_setup() -> tuple:
    registry = load_workflow_registry(REGISTRY_PATH.read_text(encoding="utf-8"))
    tmap = load_translation_map(MAP_PATH.read_text(encoding="utf-8"))
    preface = PREFACE_PATH.read_text(encoding="utf-8")
    import yaml

    manifest = yaml.safe_load(
        (REPO_ROOT / "sdd" / "development-agent.yml").read_text(encoding="utf-8")
    )
    required = {
        c["id"] for c in manifest["capabilities"] if c.get("required") is True
    }
    return registry, tmap, preface, required


def test_all_13_translated_sources_render_deterministically() -> None:
    registry, tmap, preface, required = _real_setup()
    for wf in sorted(registry.workflows.values(), key=lambda w: w.workflow_id):
        cap = wf.capability_id
        source = (
            REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md"
        ).read_bytes()
        first = render_translated(source, cap, registry, tmap, preface, required)
        second = render_translated(source, cap, registry, tmap, preface, required)
        assert first == second, cap
        assert first.startswith(f"---\nname: {cap}\n"), cap
        assert first.endswith("\n") and not first.endswith("\n\n"), cap
        assert "\r" not in first, cap
        assert wf.codex_discovery_summary in first, cap
        for edge in registry.edges_from(cap):
            assert first.count(f"<!-- codex-route:{edge.edge_id} -->") == 1, (
                cap, edge.edge_id,
            )


def test_prohibition_lines_pass_through_with_no_route() -> None:
    registry, tmap, preface, required = _real_setup()
    cases = [
        ("mj-agent-flow-intake", "**不要** 自动调用 /mj-agent-git-issue"),
        ("mj-agent-flow-scope-drift", "❌ 不调 /mj-agent-flow-self-review"),
        ("mj-agent-flow-self-review", "❌ 不调 /mj-agent-flow-post-merge"),
    ]
    for cap, needle in cases:
        source = (
            REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md"
        ).read_bytes()
        rendered = render_translated(source, cap, registry, tmap, preface, required)
        matches = [
            line for line in rendered.split("\n") if needle in line
        ]
        assert len(matches) == 1, (cap, needle)
        # the prohibition token is untouched and no substitute follows it
        assert "/mj-agent-" in matches[0]
        idx = rendered.split("\n").index(matches[0])
        following = rendered.split("\n")[idx + 1]
        assert "codex-route" not in following, (cap, needle)


def test_git_issue_renders_four_t1b_interactions() -> None:
    registry, tmap, preface, required = _real_setup()
    source = (
        REPO_ROOT / ".claude" / "skills" / "mj-agent-git-issue" / "SKILL.md"
    ).read_bytes()
    rendered = render_translated(
        source, "mj-agent-git-issue", registry, tmap, preface, required
    )
    assert rendered.count("[codex-interaction:") == 4
    assert "[codex-owner-gate:" not in rendered  # no t1a sites registered today
    # the noop-mention site inserts nothing
    assert "site-git-issue-branch-type-table-pointer]" not in rendered


# ----------------------------------------------------------------- negatives


def test_unclassified_interaction_token_refuses_with_diagnostics() -> None:
    source = SYNTH_SOURCE.replace(
        "## Steps", "## Steps\n\nAnother AskUserQuestion appears here.\n"
    )
    with pytest.raises(TranslationError) as err:
        _render_synth(source.encode("utf-8"))
    message = str(err.value)
    assert "mj-agent-alpha" in message
    assert "ask-user-question" in message
    assert "codex-skill-translation.yml" in message
    assert "remediation" in message


def test_region_token_without_edge_refuses() -> None:
    source = SYNTH_SOURCE.replace(
        "- item /mj-agent-beta call", "- item /mj-agent-unknown call"
    )
    with pytest.raises(TranslationError):
        _render_synth(source.encode("utf-8"))


def test_frontmatter_extra_key_refuses() -> None:
    source = SYNTH_SOURCE.replace(
        "description: Test skill for alpha work（触发）.",
        "description: Test skill for alpha work（触发）.\nlicense: MIT",
    )
    with pytest.raises(TranslationError, match="allowlist"):
        _render_synth(source.encode("utf-8"))


def test_missing_closing_fence_refuses() -> None:
    with pytest.raises(TranslationError, match="closing"):
        parse_source_document(b"---\nname: x\ndescription: y\nno end")


def test_name_scalar_is_verbatim() -> None:
    doc = parse_source_document(SYNTH_SOURCE.encode("utf-8"))
    assert doc.name == "mj-agent-alpha"
    assert doc.description_raw == "Test skill for alpha work（触发）."
