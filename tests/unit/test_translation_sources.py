"""Typed-source + census closure tests — Epic #499 PR-B layer B4 (plan §2.4/§2.5).

Proves, against the REAL tree (frontmatter INCLUDED — the PR-B census re-test):

- both typed sources load through the strict loaders (tags/aliases/merge keys/
  duplicate keys/extra keys/unknown versions all refuse);
- the registry's translated capability set + the v1 projection whitelist
  exactly partition the v1 `required` 18 (fully DERIVED, nothing hardcoded);
- layer-A double closure: every scanned region token resolves to exactly one
  registry edge AND every layer-A edge is hit by at least one region token;
- layer-B markers hit their paths exactly once;
- the three prohibition lines (anchored by CONTENT, not line numbers — the
  review-period line anchors already drifted once) produce no scan token;
- the fail-closed lexicon census disposes of every hit in all 13 translated
  sources, with every AskUserQuestion hit line claimed by exactly one site;
- every discovery summary passes the lexicon and closes against the source
  description (each required trigger term appears in both).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from scripts.sdd._common.skill_renderer import (
    TranslationError,
    WorkflowRegistry,
    expand_wildcard,
    lexicon_scan,
    load_translation_map,
    load_workflow_registry,
    marker_hit_count,
    scan_layer_a,
    strict_yaml_load,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "sdd" / "workflows" / "development-agent-workflows.yml"
MAP_PATH = REPO_ROOT / "sdd" / "adapters" / "codex-skill-translation.yml"
PREFACE_PATH = REPO_ROOT / "sdd" / "adapters" / "codex-skill-preface.md"

PROHIBITION_LINES = [
    (
        "mj-agent-flow-scope-drift",
        "❌ 不调 /mj-agent-flow-self-review",
    ),
    (
        "mj-agent-flow-self-review",
        "❌ 不调 /mj-agent-flow-post-merge",
    ),
    (
        "mj-agent-flow-intake",
        "**不要** 自动调用 /mj-agent-git-issue",
    ),
]


def _registry() -> WorkflowRegistry:
    return load_workflow_registry(REGISTRY_PATH.read_text(encoding="utf-8"))


def _manifest() -> dict:
    return yaml.safe_load(
        (REPO_ROOT / "sdd" / "development-agent.yml").read_text(encoding="utf-8")
    )


def _source_text(cap: str) -> str:
    return (REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md").read_text(
        encoding="utf-8"
    )


def _required_ids() -> set[str]:
    return {
        c["id"] for c in _manifest()["capabilities"] if c.get("required") is True
    }


def _byte_copy_ids() -> set[str]:
    """Byte-copy carriers, derived from `codex_carrier`.

    Before the PR-C1 cutover this was `projection == "project"`, which happened
    to select exactly the byte-copy five. Under manifest v2 that selector means
    ALL 18 carriers (V8 DA094 forces every carrier to `projection: project`), so
    the strategy axis is the only correct discriminator.
    """
    return {
        c["id"]
        for c in _manifest()["capabilities"]
        if c.get("codex_carrier") == "byte-copy"
    }


# --------------------------------------------------------------- typed load


def test_real_typed_sources_load() -> None:
    registry = _registry()
    tmap = load_translation_map(MAP_PATH.read_text(encoding="utf-8"))
    assert registry.workflows and registry.edges
    assert tmap.lexicon and tmap.sites and tmap.preface_template_version == 1
    assert PREFACE_PATH.is_file()


def test_translated_set_partitions_required_with_byte_copy() -> None:
    """registry translated caps + byte-copy carriers == the required set —
    derived end to end from the two committed sources, no hardcoded count.

    This union is the only place that proves the two carrier strategies exactly
    partition the required 18 without naming either number.
    """
    registry = _registry()
    translated = {w.capability_id for w in registry.workflows.values()}
    byte_copy = _byte_copy_ids()
    required = _required_ids()
    assert translated and byte_copy, "an empty side would satisfy the union vacuously"
    assert translated.isdisjoint(byte_copy)
    assert translated | byte_copy == required
    for cap in translated | byte_copy:
        assert (REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md").is_file()


# ------------------------------------------------------------ layer-A gate


def test_layer_a_double_closure_on_real_sources() -> None:
    registry = _registry()
    by_pair = {(e.from_id, e.to_id): e for e in registry.edges.values()}
    assert len(by_pair) == len(registry.edges)  # one edge per (from, to)
    layer_a_edges = {
        (e.from_id, e.to_id)
        for e in registry.edges.values()
        if e.evidence is None
    }
    hit_pairs: set[tuple[str, str]] = set()
    for cap in sorted(_required_ids()):
        for token in scan_layer_a(_source_text(cap)):
            target = (
                f"mj-agent-{token.token[len('mj-agent-'):]}"
                if not token.token.endswith("*")
                else token.token
            )
            pair = (cap, target)
            assert pair in by_pair, (
                f"scanned token /{token.token} in {cap} [{token.region}]"
                f" line {token.line_no} has no registry edge (source->registry"
                " closure)"
            )
            assert by_pair[pair].evidence is None, (
                f"{pair} is declared layer-B but also hits a scan region"
            )
            hit_pairs.add(pair)
    missing = layer_a_edges - hit_pairs
    assert not missing, (
        f"registry layer-A edges with no region hit (registry->source closure):"
        f" {sorted(missing)}"
    )


def test_layer_b_markers_hit_exactly_once() -> None:
    registry = _registry()
    declared = [e for e in registry.edges.values() if e.evidence is not None]
    assert {e.edge_id for e in declared} == {
        "edge-flow-implement-flow-diagnose",
        "edge-flow-diagnose-infra-studio-probe",
    }
    for edge in declared:
        text = (REPO_ROOT / edge.evidence.path).read_text(encoding="utf-8")
        assert marker_hit_count(text, edge.evidence.marker) == 1, edge.edge_id


def test_prohibition_lines_produce_no_scan_token() -> None:
    """Content-anchored (the review-period line numbers 170/266/305 already
    drifted): the line CONTAINING the verbatim prohibition text must exist
    exactly once and must not be inside any scan region."""
    for cap, needle in PROHIBITION_LINES:
        text = _source_text(cap)
        lines = [
            i for i, line in enumerate(text.splitlines(), 1) if needle in line
        ]
        assert len(lines) == 1, (cap, needle)
        scan_lines = {t.line_no for t in scan_layer_a(text)}
        assert lines[0] not in scan_lines, (cap, needle)


def test_no_carrier_targets_all_carry_substitutes() -> None:
    registry = _registry()
    carrier_set = {
        w.capability_id for w in registry.workflows.values()
    } | _byte_copy_ids()
    for edge in registry.edges.values():
        if edge.to_id.endswith("*"):
            expanded = expand_wildcard(
                edge.to_id, {c["id"] for c in _manifest()["capabilities"]}
            )
            assert expanded == sorted(expanded)
            assert all(i.startswith("mj-agent-runtime-") for i in expanded)
            has_carrier = False
        else:
            has_carrier = edge.to_id in carrier_set
        if not has_carrier:
            assert edge.substitute is not None, edge.edge_id
            assert edge.closure in ("advisory", "substitute-required"), edge.edge_id
        else:
            assert edge.substitute is None, edge.edge_id
        if edge.closure == "carrier-required":
            assert has_carrier, edge.edge_id


# ------------------------------------------------------------ lexicon gate


def test_lexicon_census_disposes_every_hit_in_13_sources() -> None:
    registry = _registry()
    tmap = load_translation_map(MAP_PATH.read_text(encoding="utf-8"))
    for cap in sorted(w.capability_id for w in registry.workflows.values()):
        text = _source_text(cap)
        hits = lexicon_scan(text, tmap.lexicon)
        assert hits, f"{cap}: census expected at least one hit"
        site_markers = {
            s.site_id: s for s in tmap.sites.values() if s.capability_id == cap
        }
        # every site marker for this capability hits exactly once
        claimed_lines: set[int] = set()
        for site in site_markers.values():
            assert marker_hit_count(text, site.marker) == 1, site.site_id
            offset = text.index(site.marker)
            line_no = text[:offset].count("\n") + 1
            assert line_no not in claimed_lines, (
                f"{site.site_id}: two sites claim line {line_no}"
            )
            claimed_lines.add(line_no)
        for hit in hits:
            if hit.disposition == "site-classified":
                assert hit.line_no in claimed_lines, (
                    f"{cap}: unclassified {hit.category} hit at line"
                    f" {hit.line_no}: {hit.line_text[:60]!r}"
                )


def test_all_sites_point_at_translated_sources() -> None:
    registry = _registry()
    tmap = load_translation_map(MAP_PATH.read_text(encoding="utf-8"))
    translated = {w.capability_id for w in registry.workflows.values()}
    for site in tmap.sites.values():
        assert site.capability_id in translated, site.site_id
        assert site.path == f".claude/skills/{site.capability_id}/SKILL.md"


def test_summaries_pass_lexicon_and_close_with_descriptions() -> None:
    registry = _registry()
    tmap = load_translation_map(MAP_PATH.read_text(encoding="utf-8"))
    for wf in registry.workflows.values():
        assert not lexicon_scan(wf.codex_discovery_summary, tmap.lexicon), (
            f"{wf.workflow_id}: summary has lexicon hits"
        )
        source = _source_text(wf.capability_id)
        # The live frontmatter description is a plain scalar that is NOT
        # loadable YAML (it contains ": " sequences) — assert closure against
        # the verbatim frontmatter text instead of a parsed field.
        frontmatter = source.split("---", 2)[1]
        for term in wf.required_trigger_terms:
            assert term in wf.codex_discovery_summary, (wf.workflow_id, term)
            assert term in frontmatter, (
                f"{wf.workflow_id}: trigger term {term!r} not grounded in the"
                " source description (source/summary closure)"
            )


# ------------------------------------------------------- loader negatives


def _mutated_registry(**overrides: object) -> str:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    data.update(overrides)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def test_unknown_registry_schema_version_refuses() -> None:
    with pytest.raises(TranslationError, match="schema_version"):
        load_workflow_registry(_mutated_registry(schema_version=9))


def test_summary_missing_trigger_term_refuses() -> None:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    data["workflows"][0]["required_trigger_terms"].append("absent-term-zz")
    with pytest.raises(TranslationError, match="trigger"):
        load_workflow_registry(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def test_oversized_summary_refuses() -> None:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    wf = data["workflows"][0]
    wf["codex_discovery_summary"] += " x" * 600
    with pytest.raises(TranslationError, match="budget"):
        load_workflow_registry(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def test_dangling_route_ref_refuses() -> None:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    data["routes"] = [r for r in data["routes"] if r["route_id"] != "route-doc-family-adapter"]
    with pytest.raises(TranslationError, match="route"):
        load_workflow_registry(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


@pytest.mark.parametrize(
    "text,needle",
    [
        ("a: 1\na: 2\n", "duplicate"),
        ("a: &x 1\nb: *x\n", "alias"),
        ("a: !!python/object:os.system {}\n", "YAML"),
        ("base: {x: 1}\nchild:\n  <<: {y: 2}\n", "merge"),
        ("a: 2026-01-01\n", "tag"),
    ],
)
def test_strict_yaml_refusals(text: str, needle: str) -> None:
    with pytest.raises(TranslationError, match=needle):
        strict_yaml_load(text)


def test_wildcard_expansion_is_deterministic_and_nonempty() -> None:
    ids = {c["id"] for c in _manifest()["capabilities"]}
    expanded = expand_wildcard("mj-agent-runtime-*", ids)
    assert expanded == sorted(expanded) and len(expanded) >= 1
    with pytest.raises(TranslationError, match="wildcard"):
        expand_wildcard("mj-agent-nonexistent-*", ids)
    with pytest.raises(TranslationError):
        expand_wildcard("not-a-wildcard", ids)
