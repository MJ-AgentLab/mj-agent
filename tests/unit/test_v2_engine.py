"""v1/v2 differential + compatibility matrix tests — Epic #499 PR-B layer B6.

Covers (plan §2.6 / §5.6): full v2 converge on a fixture tree (byte-copy +
translated + README + config + canonical v2 envelope), idempotence, the four
off-diagonal compatibility rows (cutover / rollback / both check mismatches),
unknown-malformed-mixed exit 2 with zero writes, the §2.7 adopt CAS table
under a verified v2 lock, partial-apply retry convergence, scoped-surface
member isolation, and the fidelity coverage closure (independent checker goes
red even when the renderer and its own report omit the same item).
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.sdd._common.projection_loader import parse_lock_json, verify_lock_v2
from scripts.sdd._common.skill_renderer import (
    generate_coverage,
    load_translation_map,
    load_workflow_registry,
    render_translated,
)
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_agents_projection import main as v9_main
from scripts.sdd.check_fidelity_attestations import main as fidelity_main

REPO_ROOT = Path(__file__).resolve().parents[2]

ALPHA_SOURCE = """\
---
name: mj-agent-alpha
description: Alpha byte-copy fixture.
---

# Alpha

Byte-copy body, kept verbatim.
"""

TBETA_SOURCE = """\
---
name: mj-agent-tbeta
description: Beta translated fixture for beta work.
---

# Beta

## Handoff

- next /mj-agent-alpha step
"""

FIXTURE_MAP = """\
schema_version: 1
preface_template_version: 1
lexicon:
  - category: slash-skill-token
    patterns: ['/mj-agent-[a-z0-9-]+']
    disposition: region-edge-or-noop
  - category: ask-user-question
    patterns: ['AskUserQuestion']
    disposition: site-classified
sites: []
templates:
  t1a: |
    > [codex-owner-gate:{site_id}] OWNER_APPROVAL_REQUIRED({reason}) — ask the Owner, stop, and wait.
  t1b: |
    > [codex-interaction:{site_id}] Ask the user and wait before continuing.
  t2a-route: |
    <!-- codex-route:{edge_id} -->
    > Codex route: {route}
  t2b-route: |
    <!-- codex-route:{edge_id} -->
    > Codex dependency route: {route}
"""

FIXTURE_REGISTRY = """\
schema_version: 1
workflows:
  - workflow_id: tbeta
    capability_id: mj-agent-tbeta
    codex_discovery_summary: "Beta translated fixture workflow for beta work."
    required_trigger_terms: ["beta work"]
edges:
  - {id: edge-tbeta-alpha, from: mj-agent-tbeta, to: mj-agent-alpha, relation: handoff, activation: conditional, closure: advisory}
routes: []
"""

FIXTURE_PREFACE = """\
# Codex carrier preface

> Generated artifact; harness references read as self-enforced duties.
"""

FIXTURE_README_TEMPLATE = """\
# GENERATED fixture readme

{{strategy_summary}}
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _cap(cap_id: str, carrier: str, projection: str, *,
         workflow_id: str | None = None, required: bool = True) -> dict[str, Any]:
    node: dict[str, Any] = {
        "id": cap_id,
        "group": "flow",
        "required": required,
        "projection": projection,
        "codex_carrier": carrier,
        "claude": {"support_mode": "native",
                   "approval": {"mode": "none", "gates": []},
                   "enforcement": ["manual"]},
        "codex": {"support_mode": "native",
                  "approval": {"mode": "none", "gates": []},
                  "enforcement": ["manual"]},
        "evidence": [f".claude/skills/{cap_id}/SKILL.md"],
    }
    if workflow_id is not None:
        node["carrier_binding"] = {"workflow_id": workflow_id}
    return node


def _manifest(schema_version: int) -> dict[str, Any]:
    if schema_version == 2:
        caps = [
            _cap("mj-agent-alpha", "byte-copy", "project"),
            _cap("mj-agent-tbeta", "translated", "project", workflow_id="tbeta"),
        ]
    else:
        caps = []
        for cap_id, projection in (("mj-agent-alpha", "project"),
                                   ("mj-agent-tbeta", "never")):
            node = _cap(cap_id, "none", projection)
            del node["codex_carrier"]
            caps.append(node)
    manifest: dict[str, Any] = {
        "schema_version": schema_version,
        "snapshot": "2026-08-25",
        "owners": ["fixture-owner"],
        "capabilities": caps,
        "mcp": {
            "default_projection_policy": "never",
            "servers": {"github": {"projection_policy": "project"}},
        },
        "codex": {"posture": {"approval_policy": "on-request",
                              "sandbox_mode": "workspace-write",
                              "project_doc_max_bytes": 65536}},
    }
    if schema_version == 2:
        manifest["codex_readme_template_version"] = 1
    return manifest


def make_v2_repo(tmp_path: Path, *, schema_version: int = 2) -> Path:
    _write(tmp_path / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md",
           ALPHA_SOURCE)
    _write(tmp_path / ".claude" / "skills" / "mj-agent-tbeta" / "SKILL.md",
           TBETA_SOURCE)
    _write(tmp_path / "sdd" / "development-agent.yml",
           yaml.safe_dump(_manifest(schema_version), sort_keys=False))
    _write(tmp_path / "sdd" / "workflows" / "development-agent-workflows.yml",
           FIXTURE_REGISTRY)
    _write(tmp_path / "sdd" / "adapters" / "codex-skill-translation.yml",
           FIXTURE_MAP)
    _write(tmp_path / "sdd" / "adapters" / "codex-skill-preface.md",
           FIXTURE_PREFACE)
    _write(tmp_path / "sdd" / "adapters" / "codex-skills-readme.md",
           FIXTURE_README_TEMPLATE)
    _write(tmp_path / ".mcp.json",
           json.dumps({"mcpServers": {"github": {"command": "gh-mcp"}}}))
    return tmp_path


def _switch_manifest(root: Path, schema_version: int) -> None:
    _write(root / "sdd" / "development-agent.yml",
           yaml.safe_dump(_manifest(schema_version), sort_keys=False))


# --------------------------------------------------------------- v2 converge


def test_v2_sync_converges_and_is_idempotent(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    alpha = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    tbeta = root / ".agents" / "skills" / "mj-agent-tbeta" / "SKILL.md"
    readme = root / ".agents" / "README.md"
    config = root / ".codex" / "config.toml"
    lock = root / ".agents.lock.json"
    assert alpha.read_bytes() == ALPHA_SOURCE.encode("utf-8")  # raw byte copy
    rendered = tbeta.read_text(encoding="utf-8")
    assert rendered.startswith("---\nname: mj-agent-tbeta\n")
    assert "Beta translated fixture workflow for beta work." in rendered
    assert "Codex carrier preface" in rendered
    assert rendered.count("<!-- codex-route:edge-tbeta-alpha -->") == 1
    assert "- next $mj-agent-alpha step" in rendered
    assert "1 byte-copy + 1 translated" in readme.read_text(encoding="utf-8")
    assert "[mcp_servers.github]" in config.read_text(encoding="utf-8")
    verified = verify_lock_v2(parse_lock_json(lock.read_text(encoding="utf-8")))
    assert set(verified.entries) == {
        ".agents/skills/mj-agent-alpha/SKILL.md",
        ".agents/skills/mj-agent-tbeta/SKILL.md",
        ".agents/README.md",
        ".codex/config.toml",
    }
    capsys.readouterr()
    assert sync_main(["sync"], repo_root=root) == 0
    assert "up to date" in capsys.readouterr().out
    assert sync_main(["--check"], repo_root=root) == 0
    assert v9_main(["--all"], repo_root=root) == 0


def test_v2_unowned_neighbors_survive_and_are_reported(
    tmp_path: Path, capsys: Any
) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    neighbor = root / ".agents" / "skills" / "user-note.md"
    _write(neighbor, "mine\n")
    hook = root / ".codex" / "hooks.json"
    _write(hook, "{}\n")
    assert sync_main(["sync"], repo_root=root) == 0
    assert neighbor.is_file() and hook.is_file()
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 1
    assert "unowned neighbor" in capsys.readouterr().out


# ------------------------------------------------------- compatibility rows


def test_cutover_v1_lock_is_read_only_ledger(tmp_path: Path) -> None:
    root = make_v2_repo(tmp_path, schema_version=1)
    assert sync_main(["sync"], repo_root=root) == 0  # legacy v1 sync
    v1_lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    assert all(isinstance(v, str) for v in v1_lock.values())  # flat map
    _write(root / ".agents" / "keepme.txt", "unowned\n")
    _switch_manifest(root, 2)
    assert sync_main(["sync"], repo_root=root) == 0  # cutover
    verified = verify_lock_v2(
        parse_lock_json((root / ".agents.lock.json").read_text(encoding="utf-8"))
    )
    assert ".agents/skills/mj-agent-tbeta/SKILL.md" in verified.entries
    assert (root / ".agents" / "keepme.txt").is_file()
    # checker strict / generator non-destructive split: the surviving unowned
    # neighbor IS check-drift (remove manually) while sync never deletes it
    assert sync_main(["--check"], repo_root=root) == 1
    (root / ".agents" / "keepme.txt").unlink()
    assert sync_main(["--check"], repo_root=root) == 0


def test_rollback_v2_lock_is_read_only_ledger(tmp_path: Path) -> None:
    """Golden §2.6 scenario: old-owned translated outputs are deleted, the
    byte-copy artifact and every unowned neighbor survive, a v1 lock lands."""
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0  # v2 tree
    _write(root / ".agents" / "skills" / "user-note.md", "mine\n")
    _switch_manifest(root, 1)
    assert sync_main(["sync"], repo_root=root) == 0  # rollback
    assert not (root / ".agents" / "skills" / "mj-agent-tbeta").exists()
    assert (root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md").is_file()
    assert (root / ".agents" / "skills" / "user-note.md").is_file()
    v1_lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    assert "schema_version" not in v1_lock
    assert "mj-agent-alpha" in v1_lock
    # unowned neighbor: check-drift by design, never deleted by sync
    assert sync_main(["--check"], repo_root=root) == 1
    (root / ".agents" / "skills" / "user-note.md").unlink()
    assert sync_main(["--check"], repo_root=root) == 0


def test_check_mismatch_rows_are_nonzero(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    _switch_manifest(root, 1)  # v1 manifest + v2 lock
    assert sync_main(["--check"], repo_root=root) == 1
    assert "rollback pending" in capsys.readouterr().out

    root2 = make_v2_repo(tmp_path / "two", schema_version=1)
    assert sync_main(["sync"], repo_root=root2) == 0
    _switch_manifest(root2, 2)  # v2 manifest + v1 lock
    assert sync_main(["--check"], repo_root=root2) == 1
    assert "cutover pending" in capsys.readouterr().out


@pytest.mark.parametrize(
    "lock_text",
    [
        '{"schema_version": 3, "generator_protocol_version": 1, "entries": {}}',
        '{"mj-agent-alpha": "sha256:' + "a" * 64 + '", "entries": {}}',
        '{"mj-agent-alpha": "' + "a" * 64 + '"}',
        '{"a": 1, "a": 2}',
    ],
)
def test_malformed_mixed_lock_exits_2_with_zero_writes(
    tmp_path: Path, lock_text: str
) -> None:
    root = make_v2_repo(tmp_path)
    _write(root / ".agents.lock.json", lock_text)
    before = sorted(p.as_posix() for p in root.rglob("*") if p.is_file())
    assert sync_main(["sync"], repo_root=root) == 2
    after = sorted(p.as_posix() for p in root.rglob("*") if p.is_file())
    assert before == after  # zero writes, zero deletes


# ------------------------------------------------------------- adopt (CAS)


def test_adopt_cas_success_and_noop(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    capsys.readouterr()
    # no-op row: source base + artifact base -> exit 0, zero writes
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    assert "<- artifact" not in capsys.readouterr().out
    # success row: artifact edited, source base -> artifact becomes the source
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    edited = artifact.read_bytes() + b"adopted line\n"
    artifact.write_bytes(edited)
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    assert src.read_bytes() == edited
    assert sync_main(["--check"], repo_root=root) == 0  # realigned


def test_adopt_cas_ambiguous_rows_exit_2(tmp_path: Path, capsys: Any) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    # both changed (even to identical bytes) -> exit 2, zero writes
    src.write_bytes(src.read_bytes() + b"x\n")
    artifact.write_bytes(src.read_bytes())
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 2
    assert "CAS" in capsys.readouterr().err
    # artifact missing -> exit 2
    root2 = make_v2_repo(tmp_path / "two")
    assert sync_main(["sync"], repo_root=root2) == 0
    (root2 / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md").unlink()
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root2) == 2


def test_adopt_missing_source_recovery(tmp_path: Path) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    expected = src.read_bytes()
    src.unlink()
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    assert src.read_bytes() == expected


def test_adopt_translated_and_none_never_eligible(
    tmp_path: Path, capsys: Any
) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    before = (root / ".agents.lock.json").read_bytes()
    assert sync_main(["--adopt", "mj-agent-tbeta"], repo_root=root) == 2
    assert "byte-copy only" in capsys.readouterr().err
    assert (root / ".agents.lock.json").read_bytes() == before


# ------------------------------------------------------ partial apply retry


def test_partial_apply_reports_and_next_sync_converges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    root = make_v2_repo(tmp_path)
    real_replace = os.replace
    calls = {"n": 0}

    def flaky_replace(src: Any, dst: Any) -> None:
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("disk hiccup")
        real_replace(src, dst)

    monkeypatch.setattr("scripts.sdd.agents_sync.os.replace", flaky_replace)
    assert sync_main(["sync"], repo_root=root) == 2
    err = capsys.readouterr().err
    assert "partial apply" in err and "rerun sync" in err
    monkeypatch.setattr("scripts.sdd.agents_sync.os.replace", real_replace)
    assert sync_main(["sync"], repo_root=root) == 0
    assert sync_main(["--check"], repo_root=root) == 0


# --------------------------------------------------------- member isolation


def test_scoped_surfaces_stay_isolated_under_v2(tmp_path: Path) -> None:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    config = root / ".codex" / "config.toml"
    config.write_bytes(config.read_bytes() + b"# rogue\n")
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 0
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 1
    assert sync_main(["sync"], repo_root=root) == 0
    tbeta = root / ".agents" / "skills" / "mj-agent-tbeta" / "SKILL.md"
    tbeta.write_bytes(tbeta.read_bytes() + b"rogue\n")
    assert sync_main(["--check", "--surface", "mcp"], repo_root=root) == 0
    assert sync_main(["--check", "--surface", "skills"], repo_root=root) == 1


# ------------------------------------------------------------- fidelity gate


def _fidelity_fixture(tmp_path: Path) -> Path:
    """Fixture tree carrying the REAL 13 sources + registry + a synthetic
    index + renderer-generated coverage reports."""
    registry_text = (
        REPO_ROOT / "sdd" / "workflows" / "development-agent-workflows.yml"
    ).read_text(encoding="utf-8")
    registry = load_workflow_registry(registry_text)
    tmap = load_translation_map(
        (REPO_ROOT / "sdd" / "adapters" / "codex-skill-translation.yml"
         ).read_text(encoding="utf-8")
    )
    preface = (
        REPO_ROOT / "sdd" / "adapters" / "codex-skill-preface.md"
    ).read_text(encoding="utf-8")
    manifest = yaml.safe_load(
        (REPO_ROOT / "sdd" / "development-agent.yml").read_text(encoding="utf-8")
    )
    required = {
        c["id"] for c in manifest["capabilities"] if c.get("required") is True
    }
    caps = sorted(w.capability_id for w in registry.workflows.values())
    root = tmp_path / "fidelity"
    for cap in caps:
        shutil.copy(
            REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md",
            _mk(root / ".claude" / "skills" / cap / "SKILL.md"),
        )
    _write(root / "sdd" / "workflows" / "development-agent-workflows.yml",
           registry_text)
    coverage_dir = root / "evidence" / "development-agent-v8" / "fidelity" / "coverage"
    for cap in caps:
        source = (REPO_ROOT / ".claude" / "skills" / cap / "SKILL.md").read_bytes()
        artifact = render_translated(source, cap, registry, tmap, preface, required)
        report = generate_coverage(cap, source, artifact, registry, required)
        _write(coverage_dir / f"{cap}.json",
               json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    tranches = [caps[0:5], caps[5:10], caps[10:13]]
    index = {
        "schema_version": 1,
        "translated_capabilities": caps,
        "coverage_reports": [
            f"evidence/development-agent-v8/fidelity/coverage/{c}.json"
            for c in caps
        ],
        "tranches": [
            {
                "tranche_id": f"tranche-{i + 1}",
                "capability_ids": group,
                "candidate_commit_sha": "a" * 40,
                "manifest_set_sha256": "b" * 64,
                "source_set_sha256": "c" * 64,
                "artifact_set_sha256": "d" * 64,
                "translation_set_sha256": "e" * 64,
                "workflow_set_sha256": "f" * 64,
                "preface_sha256": "0" * 64,
                "renderer_set_sha256": "1" * 64,
                "coverage_set_sha256": "2" * 64,
                "approval_binding": {
                    "record_system": "github-pr-review",
                    "immutable_record_id": f"record-{i + 1}",
                    "reviewer_identity": "fixture-reviewer",
                    "verdict": "approved",
                    "reviewed_candidate_commit_sha": "a" * 40,
                    "reviewed_source_set_sha256": "c" * 64,
                    "reviewed_artifact_set_sha256": "d" * 64,
                    "recorded_at": "2026-08-25T00:00:00Z",
                },
            }
            for i, group in enumerate(tranches)
        ],
    }
    _write(root / "sdd" / "adapters" / "codex-skill-fidelity.yml",
           yaml.safe_dump(index, sort_keys=False, allow_unicode=True))
    return root


def _mk(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_fidelity_closure_green_on_generated_reports(tmp_path: Path) -> None:
    root = _fidelity_fixture(tmp_path)
    assert fidelity_main(["--all"], repo_root=root) == 0


def test_fidelity_red_when_renderer_and_report_both_omit_an_item(
    tmp_path: Path, capsys: Any
) -> None:
    """The mandated negative: drop one heading item from a report AND keep its
    inventory_sha256 self-consistent — the independent checker still reds."""
    root = _fidelity_fixture(tmp_path)
    report_path = (
        root / "evidence" / "development-agent-v8" / "fidelity" / "coverage"
        / "mj-agent-flow-plan.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["items"] = [
        i for i in report["items"] if i["item_kind"] != "heading"
    ][:-0] or report["items"]
    report["items"] = [i for i in report["items"] if i["item_kind"] != "heading"]
    from scripts.sdd.check_fidelity_attestations import _canonical_sha256

    report["inventory_sha256"] = _canonical_sha256(report["items"])
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert fidelity_main(["--all"], repo_root=root) == 1
    assert "independent inventory expects" in capsys.readouterr().out


def test_fidelity_index_negatives(tmp_path: Path, capsys: Any) -> None:
    root = _fidelity_fixture(tmp_path)
    index_path = root / "sdd" / "adapters" / "codex-skill-fidelity.yml"
    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    # partition overlap
    index["tranches"][1]["capability_ids"].append(
        index["tranches"][0]["capability_ids"][0]
    )
    _write(index_path, yaml.safe_dump(index, sort_keys=False, allow_unicode=True))
    assert fidelity_main(["--all"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "overlap" in out or "partition" in out

    # duplicate immutable record id
    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    index["tranches"][1]["capability_ids"] = index["tranches"][1]["capability_ids"][:-1]
    index["tranches"][1]["approval_binding"]["immutable_record_id"] = "record-1"
    _write(index_path, yaml.safe_dump(index, sort_keys=False, allow_unicode=True))
    assert fidelity_main(["--all"], repo_root=root) == 1
    assert "record" in capsys.readouterr().out


# ----------------------------------------------------------- real-tree guard


def test_real_tree_now_takes_the_v2_paths() -> None:
    """Post-PR-C1-cutover pin (was `..._still_takes_the_legacy_v1_paths`).

    The live repo is manifest v2 + a v2 lock envelope, so sync/--check dispatch
    to the v2 engine. The BARE `--check` (surface=all) is the load-bearing call:
    it is the only caller that compares the WHOLE canonical lock text, which no
    CI gate does (V10 is skills-scoped, V11 mcp-scoped).
    """
    raw = json.loads((REPO_ROOT / ".agents.lock.json").read_text(encoding="utf-8"))
    assert raw["schema_version"] == 2
    assert verify_lock_v2(raw).entries, "an empty ledger would make this vacuous"
    assert sync_main(["--check"], repo_root=REPO_ROOT) == 0
    assert sync_main(["--check", "--surface", "skills"], repo_root=REPO_ROOT) == 0
    assert sync_main(["--check", "--surface", "mcp"], repo_root=REPO_ROOT) == 0
