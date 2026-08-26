"""Manifest v2 carrier schema tests — Epic #499 PR-B (dormant v2 engine), plan §2.1.

V8/V9 accept BOTH manifest schema versions since PR-B while the real tree stays
v1 byte-identical until the PR-C1 cutover; unknown versions keep exiting 2.
Covers the DA09x family: v1 closed-schema rejection of v2-only fields (DA090),
explicit `codex_carrier` requirement (DA091), `carrier_binding` shape (DA092/
DA093), invariants 1-2 (DA094/DA095) and derived-path id safety (DA096).

Fixtures reuse the synthetic-repo builders from test_sdd_development_agent
(#217 isolation pattern) — never mutate the live tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.sdd.check_agents_projection import main as v9_main
from scripts.sdd.check_development_agent import main as v8_main

from tests.unit.test_sdd_development_agent import cap, make_repo

REPO_ROOT = Path(__file__).resolve().parents[2]


def _out(capsys: Any) -> str:
    return capsys.readouterr().out


def _v2_cap(
    cap_id: str,
    *,
    carrier: str,
    projection: str,
    required: bool = False,
    workflow_id: str | None = None,
) -> dict[str, Any]:
    entry = cap(cap_id, required=required, projection=projection)
    entry["codex_carrier"] = carrier
    if workflow_id is not None:
        entry["carrier_binding"] = {"workflow_id": workflow_id}
    return entry


def test_v2_manifest_well_formed_is_green(tmp_path: Path) -> None:
    root = make_repo(
        tmp_path,
        [
            _v2_cap("mj-agent-a", carrier="byte-copy", projection="project", required=True),
            _v2_cap(
                "mj-agent-b",
                carrier="translated",
                projection="project",
                required=True,
                workflow_id="b",
            ),
            _v2_cap("mj-agent-c", carrier="none", projection="never"),
        ],
        schema_version=2,
    )
    # V9 carrier-binding closure (PJ05x) needs the workflow registry typed
    # source once the manifest is v2.
    registry = root / "sdd" / "workflows" / "development-agent-workflows.yml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        'schema_version: 1\n'
        'workflows:\n'
        '  - workflow_id: b\n'
        '    capability_id: mj-agent-b\n'
        '    codex_discovery_summary: "Fixture workflow for b work."\n'
        '    required_trigger_terms: ["b work"]\n'
        'edges:\n'
        '  - {id: edge-b-a, from: mj-agent-b, to: mj-agent-a,'
        ' relation: handoff, activation: conditional, closure: advisory}\n'
        'routes: []\n',
        encoding="utf-8",
    )
    assert v8_main(["--all"], repo_root=root) == 0
    assert v9_main(["--all"], repo_root=root) == 0


def test_v2_manifest_without_registry_is_red(tmp_path: Path, capsys: Any) -> None:
    root = make_repo(
        tmp_path,
        [_v2_cap("mj-agent-a", carrier="byte-copy", projection="project", required=True)],
        schema_version=2,
    )
    assert v9_main(["--all"], repo_root=root) == 1
    assert "PJ050" in _out(capsys)


def test_unknown_schema_version_still_exits_2(tmp_path: Path) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")], schema_version=3)
    assert v8_main(["--all"], repo_root=root) == 2
    assert v9_main(["--all"], repo_root=root) == 2


def test_v1_rejects_v2_only_fields(tmp_path: Path, capsys: Any) -> None:
    bad = cap("mj-agent-a", projection="project")
    bad["codex_carrier"] = "byte-copy"
    root = make_repo(tmp_path, [bad], schema_version=1)
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA090" in _out(capsys)


def test_v2_requires_explicit_codex_carrier(tmp_path: Path, capsys: Any) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA091" in _out(capsys)


def test_translated_requires_exactly_workflow_id(tmp_path: Path, capsys: Any) -> None:
    missing = _v2_cap("mj-agent-a", carrier="translated", projection="project")
    extra = _v2_cap(
        "mj-agent-b", carrier="translated", projection="project", workflow_id="b"
    )
    extra["carrier_binding"]["output_path"] = "elsewhere"
    empty = _v2_cap(
        "mj-agent-c", carrier="translated", projection="project", workflow_id=""
    )
    root = make_repo(tmp_path, [missing, extra, empty], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    assert _out(capsys).count("DA092") == 3


def test_binding_forbidden_off_translated(tmp_path: Path, capsys: Any) -> None:
    bad = _v2_cap(
        "mj-agent-a", carrier="byte-copy", projection="project", workflow_id="a"
    )
    root = make_repo(tmp_path, [bad], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA093" in _out(capsys)


def test_invariant_1_carrier_iff_project(tmp_path: Path, capsys: Any) -> None:
    none_project = _v2_cap("mj-agent-a", carrier="none", projection="project")
    copy_never = _v2_cap("mj-agent-b", carrier="byte-copy", projection="never")
    root = make_repo(tmp_path, [none_project, copy_never], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    assert _out(capsys).count("DA094") == 2


def test_invariant_2_required_needs_carrier(tmp_path: Path, capsys: Any) -> None:
    bad = _v2_cap("mj-agent-a", carrier="none", projection="never", required=True)
    root = make_repo(tmp_path, [bad], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    out = _out(capsys)
    assert "DA095" in out
    assert "DA094" not in out  # none + never satisfies invariant 1 on its own


def test_id_syntax_guards_derived_path(tmp_path: Path, capsys: Any) -> None:
    bad = _v2_cap("MJ-Agent-A", carrier="none", projection="never")
    root = make_repo(tmp_path, [bad], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA096" in _out(capsys)


def test_duplicate_id_is_a_casefold_collision_too(tmp_path: Path, capsys: Any) -> None:
    a1 = _v2_cap("mj-agent-a", carrier="none", projection="never")
    a2 = _v2_cap("mj-agent-a", carrier="none", projection="never")
    root = make_repo(tmp_path, [a1, a2], schema_version=2)
    assert v8_main(["--all"], repo_root=root) == 1
    out = _out(capsys)
    assert "DA005" in out  # duplicate id
    assert "DA096" in out  # same physical derived path — one owner per path


def test_real_tree_stays_v1_and_green() -> None:
    """Zero real-tree diff guard: the live manifest is still schema_version 1 and
    both blocking gates stay green after the dormant widening."""
    import yaml

    manifest = yaml.safe_load(
        (REPO_ROOT / "sdd" / "development-agent.yml").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == 1
    assert v8_main(["--all"], repo_root=REPO_ROOT) == 0
    assert v9_main(["--all"], repo_root=REPO_ROOT) == 0
