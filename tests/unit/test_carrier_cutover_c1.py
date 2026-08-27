"""PR-C1 carrier-cutover invariants — Epic #499 (plan §2.3/§2.5/§2.6, F9).

Two things this PR established that nothing else pins:

1. **PJ011 dispatches on manifest schema_version.** Under v1, D-014's "every
   Handoff target must itself be projected" predicate stands unchanged. Under
   v2 it is replaced by plan §2.3/§2.5 semantics — a no-carrier target is closed
   iff the dependency registry declares an executable `codex_substitute` — which
   is exactly what the v2 sync engine already enforces. Without the dispatch the
   18-carrier manifest reddens blocking V9 with 10 PJ011 errors.

2. **v2 byte-copy digests are EOL-sensitive, deliberately** (`raw-bytes-v1` is
   the identity, plan §2.4 forbids normalizing it). That is the exact INVERSE of
   the v1 invariant pinned by `test_agents_sync.test_cross_eol_lock_hash_and_
   check_stable`, so it needs its own regression guard — plus a real-tree guard
   that the `.gitattributes` pin is actually in force, since git applies `eol`
   only on checkout and a stale worktree stays silently CRLF.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_agents_projection import check_closure, substituted_targets

from tests.unit.test_v2_engine import _write, make_v2_repo

REPO_ROOT = Path(__file__).resolve().parents[2]

HANDOFF_SOURCE = """\
---
name: mj-agent-alpha
description: Alpha fixture with an out-of-set handoff.
---

# Alpha

## Handoff

- next /mj-agent-gamma step
"""

REGISTRY_TEMPLATE = """\
schema_version: 1
workflows:
  - workflow_id: gamma-flow
    capability_id: mj-agent-gamma
    codex_discovery_summary: "Gamma fixture workflow for gamma work."
    required_trigger_terms: ["gamma work"]
edges:
  - {{id: edge-alpha-gamma, from: mj-agent-alpha, to: mj-agent-gamma, relation: handoff, activation: conditional, closure: advisory{substitute}}}
routes:
{routes}
"""

WITH_SUBSTITUTE = ", codex_substitute: {kind: inline-procedure, route_ref: route-gamma}"
ROUTE_BLOCK = "  - {route_id: route-gamma, text: 'Run the gamma procedure by hand.'}"


def _closure_tree(tmp_path: Path, *, schema_version: int, substitute: bool) -> Path:
    root = tmp_path
    _write(root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md", HANDOFF_SOURCE)
    _write(root / ".claude" / "skills" / "mj-agent-gamma" / "SKILL.md", "# gamma\n")
    _write(root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md", HANDOFF_SOURCE)
    manifest: dict[str, Any] = {
        "schema_version": schema_version,
        "snapshot": "2026-08-27",
        "owners": ["fixture-owner"],
        "capabilities": [
            {"id": "mj-agent-alpha", "required": True, "projection": "project"},
            {"id": "mj-agent-gamma", "required": False, "projection": "never"},
        ],
    }
    if schema_version == 2:
        manifest["capabilities"][0]["codex_carrier"] = "byte-copy"
        manifest["capabilities"][1]["codex_carrier"] = "none"
    _write(root / "sdd" / "development-agent.yml", yaml.safe_dump(manifest, sort_keys=False))
    _write(
        root / "sdd" / "workflows" / "development-agent-workflows.yml",
        REGISTRY_TEMPLATE.format(
            substitute=WITH_SUBSTITUTE if substitute else "",
            routes=ROUTE_BLOCK if substitute else " []",
        ),
    )
    return root


def _pj011(root: Path) -> list[Any]:
    project = {"mj-agent-alpha"}
    all_ids = {"mj-agent-alpha", "mj-agent-gamma"}
    return [v for v in check_closure(root, project, all_ids) if v.code == "PJ011"]


# ------------------------------------------------------- PJ011 v2 dispatch


def test_pj011_v1_predicate_is_unchanged(tmp_path: Path) -> None:
    """Under v1 a substitute does NOT satisfy closure — the historical rule stands."""
    root = _closure_tree(tmp_path, schema_version=1, substitute=True)
    assert _pj011(root), "v1 must still require the target itself to be projected"


def test_pj011_v2_accepts_a_declared_substitute(tmp_path: Path) -> None:
    root = _closure_tree(tmp_path, schema_version=2, substitute=True)
    assert _pj011(root) == []


def test_pj011_v2_still_red_without_a_substitute(tmp_path: Path) -> None:
    """Fail closed: v2 relaxes the predicate, it does not remove it."""
    root = _closure_tree(tmp_path, schema_version=2, substitute=False)
    violations = _pj011(root)
    assert violations, "a no-carrier target with no substitute must stay a violation"
    assert "mj-agent-gamma" in violations[0].message


def test_substituted_targets_is_empty_without_a_registry(tmp_path: Path) -> None:
    """An unreadable/absent registry must not silently widen the predicate."""
    root = _closure_tree(tmp_path, schema_version=2, substitute=True)
    (root / "sdd" / "workflows" / "development-agent-workflows.yml").unlink()
    assert substituted_targets(root, {"mj-agent-gamma"}) == {}
    assert _pj011(root), "absent registry must fall back to the strict predicate"


def test_substituted_targets_is_empty_on_a_malformed_registry(tmp_path: Path) -> None:
    root = _closure_tree(tmp_path, schema_version=2, substitute=True)
    _write(root / "sdd" / "workflows" / "development-agent-workflows.yml", "{[not yaml")
    assert substituted_targets(root, {"mj-agent-gamma"}) == {}


def test_pj011_substitute_is_per_referrer_not_global(tmp_path: Path) -> None:
    """A substitute closes the edge it was declared for — nobody else's.

    Otherwise one capability's inline-procedure route would silently close every
    other capability's dangling Handoff, which is strictly weaker than the D-014
    predicate the v2 dispatch replaces.
    """
    root = _closure_tree(tmp_path, schema_version=2, substitute=True)
    # A second projected carrier hands off to the same target, declaring no edge.
    _write(root / ".claude" / "skills" / "mj-agent-delta" / "SKILL.md",
           HANDOFF_SOURCE.replace("mj-agent-alpha", "mj-agent-delta"))
    manifest_path = root / "sdd" / "development-agent.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["capabilities"].append(
        {"id": "mj-agent-delta", "required": True, "projection": "project",
         "codex_carrier": "byte-copy"}
    )
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n"
    )
    covered = substituted_targets(root, {"mj-agent-alpha", "mj-agent-gamma", "mj-agent-delta"})
    assert covered.get("mj-agent-alpha") == {"mj-agent-gamma"}
    assert "mj-agent-delta" not in covered

    project = {"mj-agent-alpha", "mj-agent-delta"}
    all_ids = {"mj-agent-alpha", "mj-agent-gamma", "mj-agent-delta"}
    hits = [v for v in check_closure(root, project, all_ids) if v.code == "PJ011"]
    assert [v.capability_id for v in hits] == ["mj-agent-delta"], (
        "alpha is closed by its own edge; delta declared none and must stay red"
    )


# ------------------------------------------------- v2 byte-copy EOL (F9)


def _byte_copy_digest(root: Path) -> str:
    lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    return str(lock["entries"][".agents/skills/mj-agent-alpha/SKILL.md"]["output_sha256"])


def test_v2_byte_copy_digest_is_eol_sensitive(tmp_path: Path) -> None:
    """INVERSE of the v1 F10 invariant: `raw-bytes-v1` includes EOL by design,
    so the same logical content checked out CRLF vs LF yields DIFFERENT digests.

    This is why `.gitattributes` pins the carrier SKILL.md paths — the engine is
    behaving as specified; only the checkout can make it reproducible.
    """
    lf = make_v2_repo(tmp_path / "lf")
    crlf = make_v2_repo(tmp_path / "crlf")
    source = crlf / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))
    assert sync_main(["sync"], repo_root=lf) == 0
    assert sync_main(["sync"], repo_root=crlf) == 0
    assert _byte_copy_digest(lf) != _byte_copy_digest(crlf)


def test_v2_byte_copy_artifact_crlf_flip_is_drift(tmp_path: Path) -> None:
    """The v1 engine tolerated a checkout EOL flip on the artifact; v2 must not."""
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert sync_main(["--check"], repo_root=root) == 0
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    artifact.write_bytes(artifact.read_bytes().replace(b"\n", b"\r\n"))
    assert sync_main(["--check"], repo_root=root) != 0


def test_v2_translated_artifact_stays_eol_immune(tmp_path: Path) -> None:
    """Only byte-copy is EOL-sensitive; every generated class is LF-normalized."""
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    artifact = root / ".agents" / "skills" / "mj-agent-tbeta" / "SKILL.md"
    artifact.write_bytes(artifact.read_bytes().replace(b"\n", b"\r\n"))
    assert sync_main(["--check"], repo_root=root) == 0


# ---------------------------------------------------------- real-tree F9


def test_gitattributes_pins_both_carrier_sides_to_lf() -> None:
    """Assert the EFFECTIVE attribute, not the presence of a substring.

    A substring assertion passes even when the pin lines are commented out, and
    the surrounding explanatory comment block already contains those exact
    strings — so `git check-attr` is the only honest oracle here. A source-only
    pin manufactures drift on Windows, hence both sides are checked.
    """
    for rel in (".claude/skills/mj-agent-git-commit/SKILL.md",
                ".agents/skills/mj-agent-git-commit/SKILL.md"):
        out = subprocess.run(
            ["git", "check-attr", "text", "eol", "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert out.strip(), f"git check-attr returned nothing for {rel} — probe is broken"
        assert f"{rel}: eol: lf" in out, out
        assert f"{rel}: text: set" in out, out


def test_real_tree_byte_copy_carriers_are_lf_on_disk() -> None:
    """Cheap guard for the one hazard the pin cannot prevent.

    `eol=lf` is applied by git only when git writes the file; an editor that
    re-CRLFs a pinned source leaves `git status` clean (the clean filter
    normalizes it back) while a local `sync` would mint CRLF byte-copy digests
    that Linux CI cannot reproduce. This fails loudly in that case.
    """
    manifest = yaml.safe_load(
        (REPO_ROOT / "sdd" / "development-agent.yml").read_text(encoding="utf-8")
    )
    byte_copy = [
        str(c["id"]) for c in manifest["capabilities"] if c.get("codex_carrier") == "byte-copy"
    ]
    assert byte_copy, "no byte-copy carriers derived — this check would be vacuous"
    for cap_id in byte_copy:
        for rel in (f".claude/skills/{cap_id}/SKILL.md", f".agents/skills/{cap_id}/SKILL.md"):
            assert b"\r\n" not in (REPO_ROOT / rel).read_bytes(), rel
