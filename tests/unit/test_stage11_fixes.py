"""Stage 11 fix-round regression tests — Epic #499 PR-B.

One pinned negative per adversarial-review fix (finding numbers refer to the
Stage 11 disposition table in the PR body): F1 T2a path corruption, F2 adopt
source hazard battery, F3 frontmatter blank-line desync, #4/#31 scoped v2
lock validation, #6 strict coverage anchor, #7 wrapped list construct, #8
numeric type tightening, #9/#11/#27 malformed-lock exit 2, #10/#29 scoped
dup-key drift, #14 T2b construct closure + frontmatter-description route,
#15 engine edge closure, #16 v1 ledger mappability, #20 canonical T1a
reason, #24 hook lexicon category, #30 v1 message path context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.sdd._common.projection_loader import (
    LockVerificationError,
    verify_lock_v2,
)
from scripts.sdd._common.skill_renderer import (
    CANONICAL_OWNER_GATE_REASONS,
    TranslationError,
    generate_coverage,
    load_translation_map,
    load_workflow_registry,
    parse_source_document,
    render_translated,
    scan_layer_a,
)
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_development_agent import VALID_POLICY_REFS

from tests.unit.test_lock_v2 import make_envelope
from tests.unit.test_skill_renderer_translation import (
    SYNTH_REGISTRY,
    SYNTH_SOURCE,
    _render_synth,
    _synth_map,
)
from tests.unit.test_v2_engine import make_v2_repo

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFACE = (REPO_ROOT / "sdd" / "adapters" / "codex-skill-preface.md").read_text(
    encoding="utf-8"
)


# F1 — T2a must not corrupt a T3-rewritten path on the same region line


def test_t2a_does_not_consume_path_embedded_tokens() -> None:
    source = SYNTH_SOURCE.replace(
        "- item /mj-agent-beta call",
        "- item /mj-agent-beta（见 .claude/skills/mj-agent-beta/SKILL.md）",
    )
    rendered = _render_synth(source.encode("utf-8"))
    assert "- item $mj-agent-beta（见 .agents/skills/mj-agent-beta/SKILL.md）" in rendered
    assert ".agents/skills$mj-agent-beta" not in rendered


# F3 — blank frontmatter lines keep the line-number base aligned


def test_blank_frontmatter_line_keeps_transforms_aligned() -> None:
    source = SYNTH_SOURCE.replace(
        "description: Test skill for alpha work（触发）.",
        "description: >-\n  Test skill for alpha work（触发）.\n\n  Second folded block.",
    )
    rendered = _render_synth(source.encode("utf-8"))
    # all transforms still land: routes once each, table/list rewritten
    assert rendered.count("<!-- codex-route:edge-alpha-beta -->") == 1
    assert rendered.count("<!-- codex-route:edge-alpha-gamma -->") == 1
    assert "| `$mj-agent-beta` | always |" in rendered
    assert rendered.count("[codex-interaction:site-alpha-mode]") == 1


# #7 — wrapped list items keep the route AFTER the whole item


def test_route_lands_after_wrapped_list_item() -> None:
    source = SYNTH_SOURCE.replace(
        "- item /mj-agent-beta call",
        "- item /mj-agent-beta call\n  continuation line of the same item",
    )
    rendered = _render_synth(source.encode("utf-8"))
    lines = rendered.split("\n")
    idx = next(i for i, line_ in enumerate(lines) if "item $mj-agent-beta call" in line_)
    assert "continuation line of the same item" in lines[idx + 1]


# #8 — numeric type tightening


def test_lock_versions_reject_floats_and_bools() -> None:
    env = make_envelope("skill-byte-copy")
    env["schema_version"] = 2.0
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)
    env2 = make_envelope("skill-byte-copy")
    env2["generator_protocol_version"] = 1.0
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env2)


def test_registry_schema_version_rejects_bool() -> None:
    text = SYNTH_REGISTRY.replace("schema_version: 1", "schema_version: true")
    with pytest.raises(TranslationError, match="integers only"):
        load_workflow_registry(text)


# #9/#11/#27 — malformed v2-schema lock is exit 2, never a traceback


def test_malformed_v2_lock_exits_2_in_sync_and_adopt(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    lock = root / ".agents.lock.json"
    envelope = json.loads(lock.read_text(encoding="utf-8"))
    del envelope["entries"][next(iter(envelope["entries"]))]["owner"]
    lock.write_text(json.dumps(envelope), encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 2
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err


# #10/#29 — duplicate-key lock reddens the scoped gates like sync


def test_duplicate_key_lock_scoped_check_drifts(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path, schema_version=1)
    assert sync_main(["sync"], repo_root=root) == 0
    lock = root / ".agents.lock.json"
    body = lock.read_text(encoding="utf-8").rstrip("\n}")
    dup = body + ',\n  "mj-agent-alpha": "sha256:' + "a" * 64 + '"\n}'
    lock.write_text(dup, encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 2
    capsys.readouterr()
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 1
    assert "unreadable" in capsys.readouterr().out


# #30 — v1 unreadable-lock diagnosis keeps the file path


def test_v1_lock_json_error_message_keeps_path(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path, schema_version=1)
    (root / ".agents.lock.json").write_text("not json", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 2
    assert ".agents.lock.json unreadable" in capsys.readouterr().err


# #4/#31 — scoped v2 check validates its lock entries


def test_scoped_v2_check_catches_stale_lock_entry(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    lock = root / ".agents.lock.json"
    envelope = json.loads(lock.read_text(encoding="utf-8"))
    key = ".agents/skills/mj-agent-tbeta/SKILL.md"
    envelope["entries"][key]["inputs"]["source_sha256"] = "0" * 64
    lock.write_text(
        json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    capsys.readouterr()
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 1
    assert "lock entry out of date" in capsys.readouterr().out
    # the stale skills entry never reddens the mcp surface
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 0


# #15 — engine-level edge closure (carrier-required -> carrier)


def test_carrier_required_edge_to_no_carrier_refuses(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    registry = root / "sdd" / "workflows" / "development-agent-workflows.yml"
    text = registry.read_text(encoding="utf-8").replace(
        "closure: advisory", "closure: carrier-required"
    )
    # edge target mj-agent-alpha HAS a carrier; retarget it to a ghost id
    text = text.replace("to: mj-agent-alpha", "to: mj-agent-ghost")
    registry.write_text(text, encoding="utf-8")
    (root / ".claude" / "skills" / "mj-agent-ghost").mkdir(parents=True)
    (root / ".claude" / "skills" / "mj-agent-ghost" / "SKILL.md").write_text(
        "---\nname: mj-agent-ghost\ndescription: g\n---\n\n# g\n", encoding="utf-8"
    )
    assert sync_main(["sync"], repo_root=root) == 2
    assert "carrier" in capsys.readouterr().err


# #16 — v1 ledger keys must be manifest-rebuildable at cutover


def test_cutover_rejects_unmappable_v1_lock_key(tmp_path: Path, capsys: Any) -> None:
    from tests.unit.test_v2_engine import _switch_manifest

    root = make_v2_repo(tmp_path, schema_version=1)
    assert sync_main(["sync"], repo_root=root) == 0
    lock = root / ".agents.lock.json"
    data = json.loads(lock.read_text(encoding="utf-8"))
    data["mj-agent-squatter"] = "sha256:" + "a" * 64
    lock.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _switch_manifest(root, 2)
    assert sync_main(["sync"], repo_root=root) == 2
    assert "cannot be rebuilt" in capsys.readouterr().err


# #14 — T2b construct closure + frontmatter-description route


def test_t2b_construct_mismatch_refuses() -> None:
    registry_text = SYNTH_REGISTRY + (
        "  # appended by test\n"
    )
    data = yaml.safe_load(registry_text)
    data["edges"].append({
        "id": "edge-alpha-declared",
        "from": "mj-agent-alpha",
        "to": "mj-agent-delta",
        "relation": "reference",
        "activation": "conditional",
        "closure": "advisory",
        "codex_substitute": {"kind": "inline-procedure", "route_ref": "route-gamma"},
        "source_evidence": {
            "marker_id": "alpha-declared",
            "path": ".claude/skills/mj-agent-alpha/SKILL.md",
            "marker": "prose token /mj-agent-beta here",
            "construct": "table",  # actually a paragraph line
            "placement": "after-table",
        },
    })
    registry = load_workflow_registry(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    with pytest.raises(TranslationError, match="construct"):
        render_translated(
            SYNTH_SOURCE.encode("utf-8"), "mj-agent-alpha", registry,
            _synth_map(),
            PREFACE, {"mj-agent-alpha", "mj-agent-beta"},
        )


def test_t2b_frontmatter_description_route() -> None:
    data = yaml.safe_load(SYNTH_REGISTRY)
    data["edges"].append({
        "id": "edge-alpha-fmroute",
        "from": "mj-agent-alpha",
        "to": "mj-agent-delta",
        "relation": "reference",
        "activation": "conditional",
        "closure": "advisory",
        "codex_substitute": {"kind": "inline-procedure", "route_ref": "route-gamma"},
        "source_evidence": {
            "marker_id": "alpha-fm",
            "path": ".claude/skills/mj-agent-alpha/SKILL.md",
            "marker": "alpha work（触发）",
            "construct": "frontmatter-description",
            "placement": "replace-description-scalar",
        },
    })
    registry = load_workflow_registry(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    rendered = render_translated(
        SYNTH_SOURCE.encode("utf-8"), "mj-agent-alpha", registry,
        _synth_map(), PREFACE, {"mj-agent-alpha", "mj-agent-beta"},
    )
    desc_line = rendered.split("\n")[2]
    assert desc_line.startswith("description: ")
    assert "[codex-route:edge-alpha-fmroute]" in desc_line


def test_registry_construct_enum_closed() -> None:
    data = yaml.safe_load(
        (REPO_ROOT / "sdd" / "workflows" / "development-agent-workflows.yml"
         ).read_text(encoding="utf-8")
    )
    for edge in data["edges"]:
        ev = edge.get("source_evidence")
        if ev is not None:
            assert ev["construct"] in {
                "paragraph", "list-item", "table", "fenced-block",
                "frontmatter-description",
            }


# #20 — T1a canonical reason vocabulary cross-check


def test_owner_gate_reasons_match_checker_vocabulary() -> None:
    assert CANONICAL_OWNER_GATE_REASONS == frozenset(VALID_POLICY_REFS)


def test_t1a_site_with_unknown_reason_refuses() -> None:
    tmap = load_translation_map(
        (REPO_ROOT / "sdd" / "adapters" / "codex-skill-translation.yml"
         ).read_text(encoding="utf-8")
    )
    del tmap  # loading real map is enough for shape; unknown-reason negative:
    bad = """\
schema_version: 1
preface_template_version: 1
lexicon:
  - {category: c, patterns: ['x'], disposition: noop-preface}
sites:
  - site_id: s1
    capability_id: mj-agent-a
    path: .claude/skills/mj-agent-a/SKILL.md
    marker: m
    disposition: t1a
    owner_gate_reason: not-a-canonical-reason
templates:
  t1a: "a"
  t1b: "b"
  t2a-route: "c"
  t2b-route: "d"
"""
    with pytest.raises(TranslationError, match="canonical"):
        load_translation_map(bad)


# #24 — bare hook census category present and disposed


def test_hook_category_in_lexicon_census() -> None:
    tmap = load_translation_map(
        (REPO_ROOT / "sdd" / "adapters" / "codex-skill-translation.yml"
         ).read_text(encoding="utf-8")
    )
    harness = tmap.lexicon["harness-enforcement"]
    assert any("hook" in p for p in harness.patterns)


# #6 — coverage anchors are exact transforms, never arbitrary lines


def test_coverage_transform_anchor_is_exact_never_arbitrary() -> None:
    # An INVENTORIED line inside a scan region gets transformed; coverage must
    # anchor to its EXACT transform and refuse when that line disappears —
    # even while other transformed lines still exist (the old fallback would
    # have anchored to any of them).
    source = SYNTH_SOURCE.replace(
        "- item /mj-agent-beta call",
        "- ❌ 不要 skip /mj-agent-beta call",
    )
    registry = load_workflow_registry(SYNTH_REGISTRY)
    carrier = {"mj-agent-alpha", "mj-agent-beta"}
    rendered = render_translated(
        source.encode("utf-8"), "mj-agent-alpha", registry, _synth_map(),
        PREFACE, carrier,
    )
    # positive: the transformed prohibition line anchors COVERED via T2a
    report = generate_coverage(
        "mj-agent-alpha", source.encode("utf-8"), rendered, registry, carrier
    )
    assert any(
        i["item_kind"] == "prohibition" and i["transform_class"] == "T2a"
        for i in report["items"]
    )
    # negative: drop that one line; other transformed lines remain, closure red
    forged = "\n".join(
        line for line in rendered.split("\n")
        if "❌ 不要 skip $mj-agent-beta call" not in line
    )
    with pytest.raises(TranslationError, match="coverage closure"):
        generate_coverage(
            "mj-agent-alpha", source.encode("utf-8"), forged, registry, carrier
        )


# F2 — adopt source path hazard battery (non-regular squat)


def test_adopt_refuses_non_regular_source_squat(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    # missing-source RECOVERY row (artifact stays at base) — but the source
    # path is squatted by a non-regular entry, so the hazard battery must
    # refuse before any write
    src.unlink()
    src.mkdir()  # a directory squatting the source path
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 2
    assert "hazard" in capsys.readouterr().err
    assert src.is_dir()  # untouched


# sanity: fence-blind census stays A1-pinned (C-group follow-up, not a fix)


def test_scan_layer_a_semantics_unchanged_for_real_sources() -> None:
    text = (
        REPO_ROOT / ".claude" / "skills" / "mj-agent-flow-intake" / "SKILL.md"
    ).read_text(encoding="utf-8")
    tokens = {(t.token, t.region) for t in scan_layer_a(text)}
    assert ("mj-agent-git-issue", "handoff") in tokens


def test_parse_source_document_blank_line_roundtrip() -> None:
    doc = parse_source_document(
        b"---\nname: x\ndescription: >-\n  a\n\n  b\n---\n\nbody\n"
    )
    assert doc.description_raw.count("\n") == 3  # continuation + blank + continuation
