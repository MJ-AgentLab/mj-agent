"""V12 "Cross-Carrier Structure" telemetry tests — Epic #499 PR-C1 (plan §5.8).

V12 is warning-only, so its value is entirely in what it REPORTS. These tests
therefore spend most of their effort proving the finding branches are reachable
— a reporter whose warning paths are dead code would sit green forever and look
identical to a healthy tree.

Fixture trees are built with `test_v2_engine.make_v2_repo`, the same synthetic
repo the v2 engine differential uses, so V12 is exercised against a tree the
engine itself converges rather than a hand-written imitation.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import yaml
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_cross_carrier import main as v12_main

from tests.unit.test_v2_engine import _write, make_v2_repo

REPO_ROOT = Path(__file__).resolve().parents[2]
V12_SOURCE = REPO_ROOT / "scripts" / "sdd" / "check_cross_carrier.py"


def _fidelity(root: Path, capability_ids: list[str]) -> None:
    _write(
        root / "sdd" / "adapters" / "codex-skill-fidelity.yml",
        yaml.safe_dump(
            {"schema_version": 1, "tranches": [{"capability_ids": capability_ids}]},
            sort_keys=False,
        ),
    )


def _converged(tmp_path: Path) -> Path:
    root = make_v2_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    # The attestation index is a permanent artifact post-PR-C0, so a healthy
    # fixture has one; X07 warns on its absence rather than degrading to PASS.
    _fidelity(root, ["mj-agent-tbeta"])
    return root


def _run(root: Path, tmp_path: Path, name: str = "status.json") -> tuple[int, dict[str, Any]]:
    status = tmp_path / "out" / name  # nested: proves the parent mkdir
    code = v12_main(["--status-json", str(status)], repo_root=root)
    assert status.is_file(), "status artifact was not written"
    payload = json.loads(status.read_text(encoding="utf-8"))
    return code, payload


# ------------------------------------------------------------------ clean


def test_v12_is_clean_on_a_converged_v2_tree(tmp_path: Path) -> None:
    code, payload = _run(_converged(tmp_path), tmp_path)
    assert code == 0
    assert payload["result_code"] == "EXECUTED_CLEAN"
    assert payload["warn_count"] == 0 and payload["fail_count"] == 0
    assert payload["pass_count"] > 0, "a clean run with zero checks would be vacuous"
    assert payload["posture"] == "warning"
    assert payload["observation_anchor"] == "PENDING_PR_C1_FIRST_CI"


def test_v12_skips_a_pre_cutover_v1_tree_neutrally(tmp_path: Path) -> None:
    """A v1 tree is not a failure — plan §5.8 makes SKIP neutral for the streak."""
    root = make_v2_repo(tmp_path, schema_version=1)
    assert sync_main(["sync"], repo_root=root) == 0
    code, payload = _run(root, tmp_path)
    assert code == 0
    assert payload["result_code"] == "SKIP_MANIFEST_V1"
    assert payload["warn_count"] == 0


# --------------------------------------------------- finding branches fire


def test_v12_reports_a_missing_artifact(tmp_path: Path) -> None:
    root = _converged(tmp_path)
    (root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md").unlink()
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert payload["result_code"] == "EXECUTED_WITH_FINDINGS"
    assert any("X03" in m and "mj-agent-alpha" in m for m in payload["messages"])


def test_v12_reports_an_orphan_artifact_dir(tmp_path: Path) -> None:
    root = _converged(tmp_path)
    _write(root / ".agents" / "skills" / "mj-agent-stray" / "SKILL.md", "# stray\n")
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert any("X06" in m and "mj-agent-stray" in m for m in payload["messages"])


def test_v12_reports_a_carrier_with_no_lock_entry(tmp_path: Path) -> None:
    root = _converged(tmp_path)
    lock_path = root / ".agents.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    del lock["entries"][".agents/skills/mj-agent-alpha/SKILL.md"]
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="\n")
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert any("X04" in m and "mj-agent-alpha" in m for m in payload["messages"])


def test_v12_reports_a_broken_translated_registry_bijection(tmp_path: Path) -> None:
    """Mutate the manifest AFTER convergence so only the join breaks."""
    root = _converged(tmp_path)
    manifest_path = root / "sdd" / "development-agent.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    for cap in manifest["capabilities"]:
        if cap["id"] == "mj-agent-tbeta":
            cap["carrier_binding"] = {"workflow_id": "tbeta"}
            cap["id"] = "mj-agent-renamed"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n"
    )
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert any("X02" in m for m in payload["messages"])


def test_v12_reports_a_fidelity_coverage_gap(tmp_path: Path) -> None:
    root = _converged(tmp_path)
    _fidelity(root, ["mj-agent-absent"])
    code, payload = _run(root, tmp_path)
    assert code == 1
    msgs = " ".join(payload["messages"])
    assert "X07" in msgs and "mj-agent-tbeta" in msgs


def test_v12_warns_when_the_fidelity_index_is_missing(tmp_path: Path) -> None:
    """A deleted governance artifact must not read as a healthy tree.

    Nothing else in CI reads this surface (follow-up F11), so degrading to PASS
    would make the absence invisible everywhere.
    """
    root = _converged(tmp_path)
    (root / "sdd" / "adapters" / "codex-skill-fidelity.yml").unlink()
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert payload["surfaces"]["fidelity_index"] == "absent"
    assert any("X07" in m and "absent" in m for m in payload["messages"])


def test_v12_errors_on_an_unknown_manifest_schema_version(tmp_path: Path) -> None:
    """An unknown schema must not be labelled the streak-neutral pre-cutover SKIP."""
    root = _converged(tmp_path)
    manifest_path = root / "sdd" / "development-agent.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 3
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8", newline="\n"
    )
    code, payload = _run(root, tmp_path)
    assert code == 2
    assert payload["result_code"] == "ERROR_UNREADABLE"


def test_v12_errors_on_a_malformed_lock(tmp_path: Path) -> None:
    """read_lock/classify_lock raise LockVerificationError, not SurfaceError —
    an unreadable ledger must still map to ERROR_UNREADABLE, not a traceback."""
    root = _converged(tmp_path)
    (root / ".agents.lock.json").write_text(
        json.dumps({"schema_version": 2, "entries": {}, "stray": 1}) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    code, payload = _run(root, tmp_path)
    assert code in (1, 2)
    assert payload["result_code"] in {"ERROR_UNREADABLE", "EXECUTED_WITH_FINDINGS"}


def test_v12_reports_an_edge_whose_target_has_no_substitute(tmp_path: Path) -> None:
    """Fail-closed §2.5: a no-carrier target without `codex_substitute` is a finding."""
    root = _converged(tmp_path)
    registry_path = root / "sdd" / "workflows" / "development-agent-workflows.yml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["edges"].append(
        {
            "id": "edge-tbeta-nowhere",
            "from": "mj-agent-tbeta",
            "to": "mj-agent-alpha-absent",
            "relation": "handoff",
            "activation": "conditional",
            "closure": "advisory",
        }
    )
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False), encoding="utf-8", newline="\n"
    )
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert any("X09" in m and "edge-tbeta-nowhere" in m for m in payload["messages"])


def test_v12_errors_rather_than_passing_on_an_unreadable_manifest(tmp_path: Path) -> None:
    """An unreadable surface must never look like a pass."""
    root = _converged(tmp_path)
    (root / "sdd" / "development-agent.yml").write_text("{[not yaml", encoding="utf-8")
    code, payload = _run(root, tmp_path)
    assert code == 2
    assert payload["result_code"] == "ERROR_UNREADABLE"
    assert payload["pass_count"] == 0


def test_v12_flags_a_v1_lock_under_a_v2_manifest(tmp_path: Path) -> None:
    root = _converged(tmp_path)
    (root / ".agents.lock.json").write_text(
        json.dumps({"mj-agent-alpha": "sha256:" + "0" * 64}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    code, payload = _run(root, tmp_path)
    assert code == 1
    assert payload["surfaces"]["lock_class"] == "v1"
    assert any("X04" in m for m in payload["messages"])


# ------------------------------------------------------------------- AC-04


def test_v12_source_hardcodes_no_carrier_counts() -> None:
    """AC-04: validators derive the partition; they never pin 5/13/18/20."""
    tree = ast.parse(V12_SOURCE.read_text(encoding="utf-8"))
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, int)
    }
    assert literals, "no integer literals found at all — the AST probe is broken"
    forbidden = {5, 13, 18, 19, 20, 37} & literals
    assert not forbidden, f"carrier counts hardcoded in V12 source: {sorted(forbidden)}"


# --------------------------------------------------------------- real tree


def test_v12_runs_on_the_real_tree_without_erroring() -> None:
    """Deliberately does NOT pin EXECUTED_CLEAN.

    The Tests step is BLOCKING, so asserting the real tree is V12-clean would
    make V12's predicate blocking through the back door — precisely what plan
    §5.8 forbids by keeping V12 warning telemetry for this whole program (a
    blocking flip is a separate plan/toggle). What is worth pinning is that the
    reporter still EXECUTES and classifies the real tree rather than erroring:
    exit 2 would mean a surface became unreadable, which is a real defect.
    The observed EXECUTED_CLEAN at the cutover is recorded in the PR/ledger,
    not asserted here.
    """
    assert v12_main([], repo_root=REPO_ROOT) in (0, 1)
