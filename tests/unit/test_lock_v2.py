"""Lock v2 envelope tests — Epic #499 PR-B (plan §2.6 / §2.8.1 / §2.8.3).

Covers the 7-kind closed entry union with the mandated negative classes per
kind (missing / extra / wrong-type / wrong-owner / wrong-surface /
wrong-strategy / wrong-normalization / invalid-digest), the canonical-JSON
wire (code-point key order, ensure_ascii=false, one final newline, duplicate
keys rejected before canonicalization), the §2.8.3 wildcard expansion wire,
composite member closure with RECOMPUTED member digests, and the version
dispatch (strict legacy v1 / v2 envelope / everything else malformed-mixed).

All digests are computed from distinct real inputs — a constant digest can
never satisfy the recomputed member/wildcard checks (plan §2.6).
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from scripts.sdd._common.projection_loader import (
    CODEX_LOCK_KEY,
    KIND_SPECS,
    LockVerificationError,
    canonical_json_text,
    classify_lock,
    lock_v2_canonical_text,
    parse_lock_json,
    sha256_of_canonical,
    verify_lock,
    verify_lock_v2,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def hex64(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _renderer(module: str, seed: str) -> dict[str, Any]:
    return {
        "renderer_module": module,
        "renderer_module_sha256": hex64(seed),
        "renderer_version": 1,
    }


def make_entry(kind: str) -> tuple[str, dict[str, Any]]:
    """(entry key, valid raw entry) for each closed-union member."""
    if kind == "skill-byte-copy":
        return ".agents/skills/mj-agent-git-sync/SKILL.md", {
            "entry_kind": kind,
            "owner": "capability:mj-agent-git-sync",
            "surface_members": ["skills"],
            "strategy": "byte-copy",
            "normalization_policy": "raw-bytes-v1",
            "output_sha256": hex64("byte-copy-output"),
            "inputs": {
                "source_path": ".claude/skills/mj-agent-git-sync/SKILL.md",
                "source_sha256": hex64("byte-copy-source"),
                "manifest_slice_sha256": hex64("byte-copy-slice"),
                **_renderer("scripts.sdd._common.skill_renderer", "skill-renderer"),
            },
        }
    if kind == "skill-translated":
        expansions = [
            {
                "pattern": "/mj-agent-git-*",
                "resolved_ids": ["mj-agent-git-branch", "mj-agent-git-commit"],
            }
        ]
        return ".agents/skills/mj-agent-flow-plan/SKILL.md", {
            "entry_kind": kind,
            "owner": "capability:mj-agent-flow-plan",
            "surface_members": ["skills"],
            "strategy": "translated",
            "normalization_policy": "translated-utf8-lf-v1",
            "output_sha256": hex64("translated-output"),
            "inputs": {
                "source_path": ".claude/skills/mj-agent-flow-plan/SKILL.md",
                "source_sha256": hex64("translated-source"),
                "manifest_slice_sha256": hex64("translated-manifest-slice"),
                "workflow_slice_sha256": hex64("translated-workflow-slice"),
                "translation_map_sha256": hex64("translation-map"),
                "preface_sha256": hex64("preface"),
                **_renderer("scripts.sdd._common.skill_renderer", "skill-renderer"),
                "wildcard_expansions": expansions,
                "wildcard_expansions_sha256": sha256_of_canonical(expansions),
            },
        }
    if kind == "skills-readme":
        return ".agents/README.md", {
            "entry_kind": kind,
            "owner": "system:skills-readme",
            "surface_members": ["skills"],
            "strategy": "rendered",
            "normalization_policy": "generated-utf8-lf-v1",
            "output_sha256": hex64("readme-output"),
            "inputs": {
                "manifest_slice_sha256": hex64("readme-slice"),
                "template_path": "sdd/adapters/codex-skills-readme.md",
                "template_sha256": hex64("readme-template"),
                "template_version": 1,
                **_renderer("scripts.sdd._common.codex_readme_renderer", "readme-renderer"),
            },
        }
    if kind == "codex-config-mcp":
        return CODEX_LOCK_KEY, {
            "entry_kind": kind,
            "owner": "system:codex-config",
            "surface_members": ["mcp"],
            "strategy": "rendered",
            "normalization_policy": "canonical-toml-v1",
            "output_sha256": hex64("config-output"),
            "inputs": {
                "mcp_source_path": ".mcp.json",
                "mcp_source_sha256": hex64("mcp-json"),
                "manifest_mcp_slice_sha256": hex64("mcp-slice"),
                "codex_posture_slice_sha256": hex64("posture-slice"),
                **_renderer("scripts.sdd._common.codex_config_renderer", "config-renderer"),
            },
        }
    if kind == "codex-config-composite":
        member_inputs = {
            "enforcement": {
                "binding_slice_sha256": hex64("binding-slice"),
                "enforcement_source_sha256": hex64("enforcement-source"),
            },
            "mcp": {
                "codex_posture_slice_sha256": hex64("posture-slice"),
                "manifest_mcp_slice_sha256": hex64("mcp-slice"),
                "mcp_source_path": ".mcp.json",
                "mcp_source_sha256": hex64("mcp-json"),
            },
            "shared": _renderer(
                "scripts.sdd._common.codex_config_renderer", "config-renderer"
            ),
        }
        return CODEX_LOCK_KEY, {
            "entry_kind": kind,
            "owner": "system:codex-config",
            "surface_members": ["enforcement", "mcp"],
            "strategy": "rendered",
            "normalization_policy": "canonical-toml-v1",
            "output_sha256": hex64("composite-output"),
            "member_inputs": member_inputs,
            "member_input_sha256": {
                m: sha256_of_canonical(member_inputs[m]) for m in member_inputs
            },
            "member_output_sha256": {
                "enforcement": hex64("composite-enforcement-out"),
                "mcp": hex64("composite-mcp-out"),
            },
        }
    if kind == "codex-hook":
        return ".codex/hooks.json", {
            "entry_kind": kind,
            "owner": "system:codex-hooks",
            "surface_members": ["enforcement"],
            "strategy": "rendered",
            "normalization_policy": "canonical-json-v1",
            "output_sha256": hex64("hook-output"),
            "inputs": {
                "enforcement_source_sha256": hex64("enforcement-source"),
                "policy_refs_sha256": hex64("policy-refs"),
                **_renderer("scripts.sdd._common.codex_hook_renderer", "hook-renderer"),
            },
        }
    if kind == "codex-rule":
        key = ".codex/rules/data-boundary.rules"
        return key, {
            "entry_kind": kind,
            "owner": f"system:codex-rules:{key}",
            "surface_members": ["enforcement"],
            "strategy": "rendered",
            "normalization_policy": "generated-utf8-lf-v1",
            "output_sha256": hex64("rule-output"),
            "inputs": {
                "enforcement_source_sha256": hex64("enforcement-source"),
                "policy_refs_sha256": hex64("policy-refs"),
                **_renderer("scripts.sdd._common.codex_rule_renderer", "rule-renderer"),
            },
        }
    raise AssertionError(f"unknown kind {kind}")


def make_envelope(*kinds: str) -> dict[str, Any]:
    entries: dict[str, Any] = {}
    for kind in kinds:
        key, entry = make_entry(kind)
        entries[key] = entry
    return {
        "schema_version": 2,
        "generator_protocol_version": 1,
        "entries": entries,
    }


ALL_KINDS = sorted(KIND_SPECS)


# ----------------------------------------------------------------- happy path


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_each_kind_verifies(kind: str) -> None:
    verified = verify_lock_v2(make_envelope(kind))
    key, _ = make_entry(kind)
    assert verified.entries[key].entry_kind == kind
    assert verified.generator_protocol_version == 1


def test_multi_entry_envelope_and_surface_mapping() -> None:
    env = make_envelope("skill-byte-copy", "skill-translated", "skills-readme")
    key, hook = make_entry("codex-hook")
    env["entries"][key] = hook
    verified = verify_lock_v2(env)
    assert verified.surface_owned_keys("skills") == (
        ".agents/README.md",
        ".agents/skills/mj-agent-flow-plan/SKILL.md",
        ".agents/skills/mj-agent-git-sync/SKILL.md",
    )
    assert verified.surface_owned_keys("enforcement") == (".codex/hooks.json",)
    assert verified.surface_owned_keys("mcp") == ()


# ------------------------------------------------- per-kind negative classes


def _mutations(kind: str) -> dict[str, dict[str, Any]]:
    """The 8 mandated negative classes applied to a valid entry (plan §2.6)."""
    _, entry = make_entry(kind)
    out: dict[str, dict[str, Any]] = {}

    m = copy.deepcopy(entry)
    if kind == "codex-config-composite":
        del m["member_inputs"]["shared"]["renderer_version"]
    else:
        del m["inputs"][next(iter(m["inputs"]))]
    out["missing"] = m

    m = copy.deepcopy(entry)
    m["surplus_field"] = "x"
    out["extra"] = m

    m = copy.deepcopy(entry)
    if kind == "codex-config-composite":
        m["member_inputs"]["shared"]["renderer_version"] = "1"
        m["member_input_sha256"]["shared"] = sha256_of_canonical(
            m["member_inputs"]["shared"]
        )
    else:
        version_key = "renderer_version"
        m["inputs"][version_key] = "1"
    out["wrong-type"] = m

    m = copy.deepcopy(entry)
    m["owner"] = "capability:someone-else" if kind.startswith("skill") else "system:other"
    out["wrong-owner"] = m

    m = copy.deepcopy(entry)
    m["surface_members"] = ["mcp", "enforcement"]  # wrong (or unsorted) for every kind
    out["wrong-surface"] = m

    m = copy.deepcopy(entry)
    m["strategy"] = "hand-authored"
    out["wrong-strategy"] = m

    m = copy.deepcopy(entry)
    m["normalization_policy"] = "raw-bytes-v9"
    out["wrong-normalization"] = m

    m = copy.deepcopy(entry)
    m["output_sha256"] = "sha256:" + hex64("prefixed")  # legacy prefix is v1-only
    out["invalid-digest"] = m
    return out


@pytest.mark.parametrize("kind", ALL_KINDS)
@pytest.mark.parametrize(
    "mutation",
    [
        "missing", "extra", "wrong-type", "wrong-owner",
        "wrong-surface", "wrong-strategy", "wrong-normalization", "invalid-digest",
    ],
)
def test_negative_matrix(kind: str, mutation: str) -> None:
    key, _ = make_entry(kind)
    env = make_envelope()
    env["entries"][key] = _mutations(kind)[mutation]
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)


def test_cross_kind_combination_fails() -> None:
    """composite member fields on an inputs kind (and vice versa) must fail."""
    key, entry = make_entry("codex-config-mcp")
    _, composite = make_entry("codex-config-composite")
    entry["member_inputs"] = composite["member_inputs"]
    env = make_envelope()
    env["entries"][key] = entry
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)

    key2, composite2 = make_entry("codex-config-composite")
    composite2["inputs"] = {"anything": "x"}
    env2 = make_envelope()
    env2["entries"][key2] = composite2
    with pytest.raises(LockVerificationError, match="closed union|exact"):
        verify_lock_v2(env2)


def test_composite_member_hash_is_recomputed_not_trusted() -> None:
    key, entry = make_entry("codex-config-composite")
    entry["member_inputs"]["mcp"]["mcp_source_sha256"] = hex64("a-different-mcp-json")
    env = make_envelope()
    env["entries"][key] = entry
    with pytest.raises(LockVerificationError, match="member_input_sha256"):
        verify_lock_v2(env)


# ------------------------------------------------------------- wildcard wire


def test_wildcard_empty_list_still_requires_digest() -> None:
    key, entry = make_entry("skill-translated")
    entry["inputs"]["wildcard_expansions"] = []
    entry["inputs"]["wildcard_expansions_sha256"] = sha256_of_canonical([])
    env = make_envelope()
    env["entries"][key] = entry
    assert verify_lock_v2(env).entries[key].inputs is not None

    del entry["inputs"]["wildcard_expansions_sha256"]
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)


@pytest.mark.parametrize(
    "ids",
    [
        [],  # empty resolution
        ["mj-agent-git-commit", "mj-agent-git-branch"],  # unsorted
        ["mj-agent-git-branch", "mj-agent-git-branch"],  # duplicate
    ],
)
def test_wildcard_resolved_ids_shape(ids: list[str]) -> None:
    key, entry = make_entry("skill-translated")
    expansions = [{"pattern": "/mj-agent-git-*", "resolved_ids": ids}]
    entry["inputs"]["wildcard_expansions"] = expansions
    entry["inputs"]["wildcard_expansions_sha256"] = sha256_of_canonical(expansions)
    env = make_envelope()
    env["entries"][key] = entry
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)


def test_wildcard_digest_mismatch_fails() -> None:
    key, entry = make_entry("skill-translated")
    entry["inputs"]["wildcard_expansions_sha256"] = hex64("stale-expansion-set")
    env = make_envelope()
    env["entries"][key] = entry
    with pytest.raises(LockVerificationError, match="wildcard_expansions_sha256"):
        verify_lock_v2(env)


# ------------------------------------------------------------ envelope level


def test_envelope_top_level_is_closed() -> None:
    env = make_envelope("skill-byte-copy")
    env["extra_top"] = 1
    with pytest.raises(LockVerificationError, match="top level"):
        verify_lock_v2(env)


def test_unknown_generator_protocol_fails() -> None:
    env = make_envelope("skill-byte-copy")
    env["generator_protocol_version"] = 2
    with pytest.raises(LockVerificationError, match="generator_protocol_version"):
        verify_lock_v2(env)


def test_entry_key_casefold_collision_fails() -> None:
    env = make_envelope("skill-byte-copy")
    key, entry = make_entry("skill-byte-copy")
    upper = key.replace("mj-agent-git-sync", "MJ-agent-git-sync")
    env["entries"][upper] = copy.deepcopy(entry)
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)


@pytest.mark.parametrize(
    "key",
    [
        "/absolute/path.md",
        "C:/drive/path.md",
        "//unc/share/path.md",
        ".agents/../escape.md",
        ".agents//double.md",
        ".agents\\skills\\x\\SKILL.md",
        ".agents/./skills/SKILL.md",
    ],
)
def test_unsafe_entry_keys_fail(key: str) -> None:
    _, entry = make_entry("skill-byte-copy")
    env = make_envelope()
    env["entries"][key] = entry
    with pytest.raises(LockVerificationError):
        verify_lock_v2(env)


# --------------------------------------------------------- version dispatch


def test_classify_strict_v1_and_v2() -> None:
    assert classify_lock({"mj-agent-git-sync": "sha256:" + hex64("x")}) == "v1"
    assert classify_lock({CODEX_LOCK_KEY: "sha256:" + hex64("y")}) == "v1"
    assert classify_lock(make_envelope("skill-byte-copy")) == "v2"


@pytest.mark.parametrize(
    "raw",
    [
        {"mj-agent-a": "sha256:" + "a" * 64, "entries": {}},  # hybrid flat + envelope
        {"mj-agent-a": "a" * 64},  # bare 64-hex (missing prefix)
        {"mj-agent-a": "SHA256:" + "a" * 64},  # wrong prefix case
        {".agents/skills/mj-agent-a/SKILL.md": "sha256:" + "a" * 64},  # path-style key
        {"schema_version": 1, "entries": {}},  # explicit v1 envelope does not exist
        {"schema_version": 3, "generator_protocol_version": 1, "entries": {}},
    ],
)
def test_classify_malformed_and_mixed(raw: dict[str, Any]) -> None:
    with pytest.raises(LockVerificationError):
        classify_lock(raw)


def test_real_tree_lock_is_strict_v1() -> None:
    raw = json.loads((REPO_ROOT / ".agents.lock.json").read_text(encoding="utf-8"))
    assert classify_lock(raw) == "v1"
    assert set(verify_lock(raw).entries) == set(raw)


# ------------------------------------------------------------ canonical wire


def test_canonical_json_wire_shape() -> None:
    text = canonical_json_text({"b": 1, "a": {"d": 2, "c": "\u4e2d\u6587"}})
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert text.index('"a"') < text.index('"b"')
    assert "\u4e2d\u6587" in text  # ensure_ascii=false
    assert "\\u" not in text


def test_duplicate_json_keys_rejected_before_canonicalization() -> None:
    with pytest.raises(LockVerificationError, match="duplicate"):
        parse_lock_json('{"a": 1, "a": 2}')
    with pytest.raises(LockVerificationError, match="duplicate"):
        parse_lock_json('{"entries": {"k": {"x": 1, "x": 2}}}')


def test_lock_v2_canonical_text_round_trips() -> None:
    env = make_envelope("skill-byte-copy", "codex-hook")
    text = lock_v2_canonical_text(env)
    assert parse_lock_json(text) == env
    assert lock_v2_canonical_text(parse_lock_json(text)) == text


def test_different_inputs_produce_different_digests() -> None:
    assert sha256_of_canonical({"a": 1}) != sha256_of_canonical({"a": 2})
    assert hex64("byte-copy-source") != hex64("translated-source")
