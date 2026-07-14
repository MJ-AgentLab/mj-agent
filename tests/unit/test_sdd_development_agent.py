"""Unit tests for V8 (check_development_agent) + V9 (check_agents_projection).

Covers plan §10 interface (scope XOR / --json / --fail-on / exit codes 0-1-2), §9 schema
negatives (unknown schema / enum / required-unsupported / gates / policy_ref / evidence),
entry-file relations (AGENTS.md x5 + @AGENTS.md imports), canonical-10 drift guard,
stats-from-manifest rule, D-013 forced-never, projection closure / reconcile / lock, and
the S0 dual-discovery canary (on-disk skills ≟ manifest count).

Fixtures build a synthetic repo under tmp_path and inject it via
`main(argv, repo_root=...)` (#217 isolation pattern) — never mutate the live tree.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from scripts.sdd._common.frontmatter import body_sha256
from scripts.sdd.check_agents_projection import main as v9_main
from scripts.sdd.check_development_agent import CANONICAL_HITL_10
from scripts.sdd.check_development_agent import main as v8_main

REPO_ROOT = Path(__file__).resolve().parents[2]

POSTURE = {
    "approval_policy": "on-request",
    "sandbox_mode": "workspace-write",
    "project_doc_max_bytes": 65536,
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cap(
    cap_id: str,
    *,
    group: str = "flow",
    required: bool = False,
    projection: str = "never",
    claude: dict[str, Any] | None = None,
    codex: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    def side(mode: str) -> dict[str, Any]:
        return {
            "support_mode": mode,
            "approval": {"mode": "none", "gates": []},
            "enforcement": [] if mode == "unsupported" else ["manual"],
        }

    return {
        "id": cap_id,
        "group": group,
        "required": required,
        "projection": projection,
        "claude": claude or side("native"),
        "codex": codex or side("manual"),
        "evidence": evidence or [f".claude/skills/{cap_id}/SKILL.md"],
    }


def make_repo(
    tmp_path: Path,
    caps: list[dict[str, Any]],
    *,
    schema_version: int = 1,
    extra_skills: tuple[str, ...] = (),
    skill_index_count: int | None = None,
    mcp_servers: dict[str, Any] | None = None,
    posture: dict[str, Any] | None = None,
    skill_bodies: dict[str, str] | None = None,
) -> Path:
    ids = [c["id"] for c in caps] + list(extra_skills)
    bodies = skill_bodies or {}
    for cid in ids:
        body = bodies.get(cid, f"# {cid}\n\nbody\n")
        _write(
            tmp_path / ".claude" / "skills" / cid / "SKILL.md",
            f"---\nname: {cid}\ndescription: fixture\n---\n\n{body}",
        )
    count = skill_index_count if skill_index_count is not None else len(ids)
    _write(tmp_path / ".claude" / "skills" / "SKILL_INDEX.md", f"> count **{count}**\n")

    _write(tmp_path / "AGENTS.md", "# AGENTS.md\n")
    _write(tmp_path / "CLAUDE.md", "# CLAUDE.md\n\n@AGENTS.md\n")
    for d in ("capabilities", "docker", "src/mj_agent", "tests"):
        _write(tmp_path / d / "AGENTS.md", f"# {d}/AGENTS.md\n")
        _write(tmp_path / d / "CLAUDE.md", f"# {d}/CLAUDE.md\n\n@AGENTS.md\n")

    rows = "\n".join(f"| `{name}` | anchor | carrier |" for name in CANONICAL_HITL_10)
    _write(
        tmp_path / "policies" / "ai-agent.md",
        f"# ai-agent\n\n## §4 HITL Canonical\n\n| enum | a | c |\n|---|---|---|\n{rows}\n"
        f"\n## §5 next\n",
    )
    boxes = "\n".join(f"- [ ] {name}（fixture）" for name in CANONICAL_HITL_10)
    _write(
        tmp_path / ".github" / "PULL_REQUEST_TEMPLATE.md",
        f"# PR\n\n## HITL Trigger Inventory\n\n{boxes}\n\n## Verification Plan\n",
    )

    servers = mcp_servers if mcp_servers is not None else {"github": {"projection_policy": "project"}}
    _write(
        tmp_path / ".mcp.json",
        json.dumps({"mcpServers": {name: {"command": "x"} for name in servers}}),
    )

    manifest: dict[str, Any] = {
        "schema_version": schema_version,
        "snapshot": "2026-07-13",
        "owners": ["fixture-owner"],
        "capabilities": caps,
        "mcp": {"default_projection_policy": "never", "servers": servers},
        "codex": {"posture": posture or POSTURE},
    }
    _write(tmp_path / "sdd" / "development-agent.yml", yaml.safe_dump(manifest, sort_keys=False))
    return tmp_path


# ------------------------------------------------------------------ real-tree pins


def test_real_tree_v8_all_passes() -> None:
    assert v8_main(["--all"], repo_root=REPO_ROOT) == 0


def test_real_tree_v9_no_false_red() -> None:
    """Real tree exits 0 at --fail-on error (S0: empty state; S1+ #326: committed
    artifacts + closed closure — PJ011 runs at error severity once .agents/ exists)."""
    assert v9_main(["--all"], repo_root=REPO_ROOT) == 0


def test_dual_discovery_canary_on_disk_matches_manifest() -> None:
    """Canary (Owner 拍板 #3): on-disk .claude/skills count ≟ manifest capability count."""
    manifest = yaml.safe_load(
        (REPO_ROOT / "sdd" / "development-agent.yml").read_text(encoding="utf-8")
    )
    manifest_ids = {c["id"] for c in manifest["capabilities"]}
    on_disk = {p.parent.name for p in (REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md")}
    assert manifest_ids == on_disk
    assert len(manifest_ids) == len(manifest["capabilities"])  # no duplicate ids


# ------------------------------------------------------------------ CLI contract


def test_scope_parameters_are_exclusive_and_required(tmp_path: Path) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")])
    assert v8_main([], repo_root=root) == 2
    assert v8_main(["--all", "--changed-from", "HEAD"], repo_root=root) == 2
    assert v9_main([], repo_root=root) == 2
    assert v9_main(["--all", "--changed-from", "HEAD"], repo_root=root) == 2


def test_changed_from_bad_ref_exits_2() -> None:
    assert v8_main(["--changed-from", "no-such-ref-p1s0"], repo_root=REPO_ROOT) == 2
    assert v9_main(["--changed-from", "no-such-ref-p1s0"], repo_root=REPO_ROOT) == 2


def test_json_output_schema(capsys: Any) -> None:
    assert v8_main(["--all", "--json"], repo_root=REPO_ROOT) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"schema_version", "mode", "base", "violations", "summary"}
    assert payload["mode"] == "all"
    assert payload["base"] is None
    assert set(payload["summary"]) == {"error", "warning", "info"}


def test_unknown_manifest_schema_version_exits_2(tmp_path: Path) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")], schema_version=99)
    assert v8_main(["--all"], repo_root=root) == 2
    assert v9_main(["--all"], repo_root=root) == 2


# ------------------------------------------------------------------ §9 schema negatives


def _errors(capsys: Any) -> str:
    return capsys.readouterr().out


def test_unknown_support_mode_is_error(tmp_path: Path, capsys: Any) -> None:
    bad = cap("mj-agent-a")
    bad["claude"]["support_mode"] = "telepathy"
    root = make_repo(tmp_path, [bad])
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA021" in _errors(capsys)


def test_required_capability_unsupported_side_is_error(tmp_path: Path, capsys: Any) -> None:
    bad = cap("mj-agent-a", required=True)
    bad["codex"] = {
        "support_mode": "unsupported",
        "approval": {"mode": "none", "gates": []},
        "enforcement": [],
    }
    root = make_repo(tmp_path, [bad])
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA023" in _errors(capsys)


def test_owner_hitl_without_gates_is_error(tmp_path: Path, capsys: Any) -> None:
    bad = cap("mj-agent-a")
    bad["claude"]["approval"] = {"mode": "owner-hitl", "gates": []}
    root = make_repo(tmp_path, [bad])
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA013" in _errors(capsys)


def test_gate_policy_ref_must_resolve(tmp_path: Path, capsys: Any) -> None:
    bad = cap("mj-agent-a")
    bad["claude"]["approval"] = {
        "mode": "owner-hitl",
        "gates": [
            {
                "policy_ref": "made-up-eleventh-enum",
                "trigger": "x",
                "stop_before": "write",
                "evidence_required": "explicit-owner-message",
            }
        ],
    }
    root = make_repo(tmp_path, [bad])
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA015" in _errors(capsys)


def test_duplicate_ids_and_forbidden_owner_agent(tmp_path: Path, capsys: Any) -> None:
    a1, a2 = cap("mj-agent-a"), cap("mj-agent-a")
    a2["owner_agent"] = "claude"
    root = make_repo(tmp_path, [a1, a2])
    assert v8_main(["--all"], repo_root=root) == 1
    out = _errors(capsys)
    assert "DA005" in out and "DA002" in out


def test_missing_evidence_severity_follows_required(tmp_path: Path, capsys: Any) -> None:
    """Missing evidence: required cap == error; optional cap == warning (§10 semantics)."""
    optional = cap("mj-agent-a", evidence=["does/not/exist.md"])
    root = make_repo(tmp_path, [optional])
    assert v8_main(["--all"], repo_root=root) == 0  # warning below default threshold
    assert v8_main(["--all", "--fail-on", "warning"], repo_root=root) == 1
    capsys.readouterr()

    required = cap("mj-agent-b", required=True, evidence=["does/not/exist.md"])
    root2 = make_repo(tmp_path / "r2", [required])
    assert v8_main(["--all"], repo_root=root2) == 1
    assert "DA032" in _errors(capsys)


def test_on_disk_skill_missing_from_manifest_is_error(tmp_path: Path, capsys: Any) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")], extra_skills=("mj-agent-orphan",))
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA060" in _errors(capsys)


def test_skill_index_count_drift_is_warning_only(tmp_path: Path, capsys: Any) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")], skill_index_count=35)
    assert v8_main(["--all"], repo_root=root) == 0
    assert "DA061" in _errors(capsys)
    assert v8_main(["--all", "--fail-on", "warning"], repo_root=root) == 1


def test_missing_agents_import_is_error(tmp_path: Path, capsys: Any) -> None:
    root = make_repo(tmp_path, [cap("mj-agent-a")])
    (root / "tests" / "CLAUDE.md").write_text("# no import\n", encoding="utf-8")
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA042" in _errors(capsys)


def test_pr_template_enum_drift_is_error(tmp_path: Path, capsys: Any) -> None:
    """The 12-vs-10 incident guard: an extra checkbox row must fail."""
    root = make_repo(tmp_path, [cap("mj-agent-a")])
    template = root / ".github" / "PULL_REQUEST_TEMPLATE.md"
    text = template.read_text(encoding="utf-8")
    template.write_text(
        text.replace("## Verification Plan", "- [ ] extra-invented-enum（x）\n\n## Verification Plan"),
        encoding="utf-8",
    )
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA053" in _errors(capsys)


def test_mcp_forced_never_tier_is_enforced(tmp_path: Path, capsys: Any) -> None:
    """D-013: biz / ssh-manager servers can never be projected."""
    servers = {
        "github": {"projection_policy": "project"},
        "pg-mj-system-biz-dev": {"projection_policy": "project"},
    }
    root = make_repo(tmp_path, [cap("mj-agent-a")], mcp_servers=servers)
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA073" in _errors(capsys)


def test_codex_posture_required(tmp_path: Path, capsys: Any) -> None:
    root = make_repo(
        tmp_path, [cap("mj-agent-a")], posture={"approval_policy": "on-request"}
    )
    assert v8_main(["--all"], repo_root=root) == 1
    assert "DA081" in _errors(capsys)


# ------------------------------------------------------------------ V9 projection domain


HANDOFF_BODY = (
    "# skill\n\n## Overview\n\nmention /mj-agent-ignored-elsewhere here\n\n"
    "## Handoff to next\n\n- call /mj-agent-b\n\n## After Handoff\n\ntail\n"
)


def _projection_repo(tmp_path: Path, *, b_projected: bool) -> Path:
    caps = [
        cap("mj-agent-a", projection="project"),
        cap("mj-agent-b", projection="project" if b_projected else "never"),
        cap("mj-agent-ignored-elsewhere"),
    ]
    return make_repo(tmp_path, caps, skill_bodies={"mj-agent-a": HANDOFF_BODY})


def test_closure_only_counts_handoff_sections(tmp_path: Path, capsys: Any) -> None:
    """/mj-agent-ignored-elsewhere sits outside `## Handoff*` — must not be flagged."""
    root = _projection_repo(tmp_path, b_projected=True)
    assert v9_main(["--all", "--fail-on", "warning"], repo_root=root) == 0
    assert "PJ011" not in capsys.readouterr().out


def test_closure_violation_is_warning_at_s0_error_after_artifacts(
    tmp_path: Path, capsys: Any
) -> None:
    root = _projection_repo(tmp_path, b_projected=False)
    assert v9_main(["--all"], repo_root=root) == 0  # warning at S0 empty state
    assert "PJ011" in capsys.readouterr().out
    assert v9_main(["--all", "--fail-on", "warning"], repo_root=root) == 1

    # once .agents/ exists the same violation escalates to error
    _write(root / ".agents" / "skills" / "mj-agent-a" / "SKILL.md", "# a\n")
    lock = {"mj-agent-a": body_sha256("# a\n")}
    _write(root / ".agents.lock.json", json.dumps(lock))
    assert v9_main(["--all"], repo_root=root) == 1


def test_reconcile_extra_and_missing_artifacts_fail(tmp_path: Path, capsys: Any) -> None:
    root = _projection_repo(tmp_path, b_projected=True)
    a_body = (root / ".claude" / "skills" / "mj-agent-a" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    b_body = (root / ".claude" / "skills" / "mj-agent-b" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    _write(root / ".agents" / "skills" / "mj-agent-a" / "SKILL.md", a_body)
    _write(root / ".agents" / "skills" / "mj-agent-b" / "SKILL.md", b_body)
    _write(root / ".agents" / "skills" / "mj-agent-extra" / "SKILL.md", "# extra\n")
    lock = {
        "mj-agent-a": body_sha256(a_body),
        "mj-agent-b": body_sha256(b_body),
    }
    _write(root / ".agents.lock.json", json.dumps(lock))
    assert v9_main(["--all"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "PJ020" in out  # extra artifact
    assert "PJ021" not in out

    (root / ".agents" / "skills" / "mj-agent-extra" / "SKILL.md").unlink()
    (root / ".agents" / "skills" / "mj-agent-extra").rmdir()
    (root / ".agents" / "skills" / "mj-agent-b" / "SKILL.md").unlink()
    (root / ".agents" / "skills" / "mj-agent-b").rmdir()
    assert v9_main(["--all"], repo_root=root) == 1
    assert "PJ021" in capsys.readouterr().out  # missing artifact


def test_lock_and_artifacts_must_land_together(tmp_path: Path, capsys: Any) -> None:
    root = _projection_repo(tmp_path, b_projected=True)
    _write(root / ".agents.lock.json", json.dumps({}))  # lock without .agents/
    assert v9_main(["--all"], repo_root=root) == 1
    assert "PJ030" in capsys.readouterr().out


def test_lock_hash_mismatch_fails(tmp_path: Path, capsys: Any) -> None:
    root = _projection_repo(tmp_path, b_projected=True)
    a_body = (root / ".claude" / "skills" / "mj-agent-a" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    b_body = (root / ".claude" / "skills" / "mj-agent-b" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    _write(root / ".agents" / "skills" / "mj-agent-a" / "SKILL.md", a_body)
    _write(root / ".agents" / "skills" / "mj-agent-b" / "SKILL.md", b_body)
    lock = {
        "mj-agent-a": "sha256:" + "0" * 64,  # tampered
        "mj-agent-b": body_sha256(b_body),
        "mj-agent-ghost": body_sha256("x"),  # lock entry without projection
    }
    _write(root / ".agents.lock.json", json.dumps(lock))
    assert v9_main(["--all"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "PJ033" in out and "PJ034" in out
