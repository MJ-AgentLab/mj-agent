"""Contract tests for ``scripts/sdd/task0_freeze.py`` (Epic #499 Task-0 freeze carrier).

Every case runs against a synthetic git repository under ``tmp_path`` via the
injectable ``repo_root`` parameter — never against the live tree (per
``tests/AGENTS.md`` "no dev-machine coupling").

Expected digests are recomputed with ``hashlib`` inside the test rather than through
the module's own helpers, so a bug in ``surface_digest``/``blob_digests`` cannot make
its own output look correct.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from scripts.sdd import task0_freeze

OUT_DIR = "ev"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


def _write(repo: Path, rel: str, data: bytes) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _commit(repo: Path, message: str = "fixture") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


# Deliberately omits `.claudeignore`, `capabilities/`, `docker/` and `tests/CLAUDE.md`
# so the "pattern matched nothing" bookkeeping has something real to record.
FIXTURE_TREE: dict[str, bytes] = {
    "CLAUDE.md": b"# CLAUDE\n",
    "AGENTS.md": b"# AGENTS\n",
    ".mcp.json": b'{"mcpServers": {}}\n',
    ".claude/settings.json": b'{"permissions": {}}\n',
    ".claude/skills/demo/SKILL.md": b"---\nname: demo\n---\n\nbody\n",
    "src/mj_agent/AGENTS.md": b"# nested AGENTS\n",
    "src/mj_agent/agent.py": b"ACTIVE = ()\n",
    "tests/unit/test_guard_git_workflow_hook.py": b"def test_guard():\n    assert True\n",
    "tests/unit/test_other.py": b"def test_other():\n    assert True\n",
    "policies/ai-agent.md": b"# policy\n",
    "sdd/gates.md": b"# gates\n",
    ".agents.lock.json": b'{"entries": []}\n',
    ".agents/skills/demo/SKILL.md": b"projected\n",
    "docs/note.md": b"# note\n",
    "README.md": b"# readme\n",
}

EXPECTED_HARD_FROZEN = {
    "CLAUDE.md",
    ".mcp.json",
    ".claude/settings.json",
    ".claude/skills/demo/SKILL.md",
    "src/mj_agent/AGENTS.md",
    "tests/unit/test_guard_git_workflow_hook.py",
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed synthetic repository mirroring the real frozen surfaces."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "task0@example.invalid")
    _git(root, "config", "user.name", "Task0 Fixture")
    _git(root, "config", "commit.gpgsign", "false")
    for rel, data in FIXTURE_TREE.items():
        _write(root, rel, data)
    _commit(root, "initial")
    return root


def _emit(repo_root: Path) -> int:
    return task0_freeze.main(["--emit", "--out-dir", OUT_DIR], repo_root=repo_root)


def _check(repo_root: Path) -> int:
    return task0_freeze.main(["--check", "--out-dir", OUT_DIR], repo_root=repo_root)


def _load(repo_root: Path, name: str) -> dict:
    return json.loads((repo_root / OUT_DIR / name).read_text(encoding="utf-8"))


def _inventory(repo_root: Path) -> dict:
    return _load(repo_root, task0_freeze.INVENTORY_NAME)


def _identity(repo_root: Path) -> dict:
    return _load(repo_root, task0_freeze.IDENTITY_NAME)


# --------------------------------------------------------------------- emit ------


def test_emit_hashes_match_independently_computed_blob_digests(repo: Path) -> None:
    assert _emit(repo) == 0
    inventory = _inventory(repo)
    assert inventory["file_count"] == len(FIXTURE_TREE)
    assert inventory["content_basis"] == "git-blob"

    recorded = {entry["path"]: entry["sha256"] for entry in inventory["files"]}
    assert recorded, "inventory produced no files — a vacuous pass"
    assert set(recorded) == set(FIXTURE_TREE)
    for rel, data in FIXTURE_TREE.items():
        assert recorded[rel] == hashlib.sha256(data).hexdigest(), rel


def test_inventory_surface_counts_sum_to_file_count(repo: Path) -> None:
    assert _emit(repo) == 0
    inventory = _inventory(repo)
    assert inventory["surface_counts"], "no surfaces classified — a vacuous pass"
    assert sum(inventory["surface_counts"].values()) == inventory["file_count"]


def test_hard_frozen_shadows_the_generic_prefix_surfaces(repo: Path) -> None:
    """`src/mj_agent/AGENTS.md` must classify as hard-frozen, not runtime-src."""
    assert _emit(repo) == 0
    surfaces = {entry["path"]: entry["surface"] for entry in _inventory(repo)["files"]}
    assert surfaces["src/mj_agent/AGENTS.md"] == task0_freeze.SURFACE_HARD_FROZEN
    assert surfaces["src/mj_agent/agent.py"] == "runtime-src"
    assert surfaces["AGENTS.md"] == task0_freeze.SURFACE_CONTROLLED_FROZEN
    assert surfaces[".agents.lock.json"] == "generated-projection"
    assert surfaces["README.md"] == task0_freeze.SURFACE_REPO_ROOT


def test_identity_resolves_the_expected_hard_frozen_set(repo: Path) -> None:
    assert _emit(repo) == 0
    identity = _identity(repo)
    resolved = {entry["path"] for entry in identity["hard_frozen"]["files"]}
    assert resolved == EXPECTED_HARD_FROZEN
    assert identity["hard_frozen"]["count"] == len(EXPECTED_HARD_FROZEN) > 0
    assert identity["controlled_frozen"]["count"] == 1


def test_patterns_that_matched_nothing_are_recorded_explicitly(repo: Path) -> None:
    """An empty match must be visible in the artifact, not silently absent."""
    assert _emit(repo) == 0
    absent = _identity(repo)["hard_frozen"]["absent_exact_patterns"]
    assert ".claudeignore" in absent
    assert "capabilities/CLAUDE.md" in absent
    assert "CLAUDE.md" not in absent


def test_identity_digest_is_independently_reproducible(repo: Path) -> None:
    assert _emit(repo) == 0
    identity = _identity(repo)
    for block in ("hard_frozen", "controlled_frozen"):
        payload = "\n".join(
            f"{entry['path']}\0{entry['mode']}\0{entry['sha256']}"
            for entry in sorted(identity[block]["files"], key=lambda e: e["path"])
        )
        assert identity[block]["digest"] == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    combined = f"{identity['hard_frozen']['digest']}\0{identity['controlled_frozen']['digest']}"
    assert identity["identity_digest"] == hashlib.sha256(combined.encode("utf-8")).hexdigest()


def test_untracked_paths_never_enter_the_inventory(repo: Path) -> None:
    """Private/ignored harness state is excluded by construction (plan §1.1)."""
    _write(repo, ".claude/scheduled_tasks.lock", b"private harness state\n")
    _write(repo, ".gitignore", b".claude/scheduled_tasks.lock\n")
    _commit(repo, "add gitignore only")
    assert _emit(repo) == 0
    paths = {entry["path"] for entry in _inventory(repo)["files"]}
    assert ".gitignore" in paths
    assert ".claude/scheduled_tasks.lock" not in paths


def test_hash_follows_the_blob_not_the_worktree_bytes(repo: Path) -> None:
    """CRLF in the checked-out file must not change the recorded digest."""
    assert _emit(repo) == 0
    before = {e["path"]: e["sha256"] for e in _inventory(repo)["files"]}["CLAUDE.md"]

    (repo / "CLAUDE.md").write_bytes(FIXTURE_TREE["CLAUDE.md"].replace(b"\n", b"\r\n"))
    assert (repo / "CLAUDE.md").read_bytes() != FIXTURE_TREE["CLAUDE.md"]

    assert _emit(repo) == 0
    after = {e["path"]: e["sha256"] for e in _inventory(repo)["files"]}["CLAUDE.md"]
    assert after == before == hashlib.sha256(FIXTURE_TREE["CLAUDE.md"]).hexdigest()


# -------------------------------------------------------------------- check ------


def test_check_is_clean_immediately_after_emit(repo: Path, capsys: pytest.CaptureFixture) -> None:
    assert _emit(repo) == 0
    capsys.readouterr()
    assert _check(repo) == 0
    assert capsys.readouterr().out.strip().splitlines()[-1] == "TASK0_FREEZE_CLEAN"


def test_modified_hard_frozen_file_stops(repo: Path, capsys: pytest.CaptureFixture) -> None:
    assert _emit(repo) == 0
    _write(repo, ".claude/settings.json", b'{"permissions": {"allow": ["Edit"]}}\n')
    _commit(repo, "widen settings")
    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "STOP_FROZEN_SURFACE_DRIFT"
    assert "MODIFIED .claude/settings.json" in out


def test_added_hard_frozen_file_stops(repo: Path, capsys: pytest.CaptureFixture) -> None:
    assert _emit(repo) == 0
    _write(repo, ".claude/skills/new/SKILL.md", b"new skill\n")
    _commit(repo, "add skill")
    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "STOP_FROZEN_SURFACE_DRIFT"
    assert "ADDED    .claude/skills/new/SKILL.md" in out


def test_removed_hard_frozen_file_stops(repo: Path, capsys: pytest.CaptureFixture) -> None:
    assert _emit(repo) == 0
    _git(repo, "rm", "-q", ".claude/skills/demo/SKILL.md")
    _commit(repo, "drop skill")
    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "STOP_FROZEN_SURFACE_DRIFT"
    assert "REMOVED  .claude/skills/demo/SKILL.md" in out


def test_controlled_surface_change_is_reported_as_its_own_code(
    repo: Path, capsys: pytest.CaptureFixture
) -> None:
    assert _emit(repo) == 0
    _write(repo, "AGENTS.md", b"# AGENTS\n\ncarrier ownership hunk\n")
    _commit(repo, "controlled hunk")
    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "CONTROLLED_SURFACE_CHANGED"
    assert "STOP_FROZEN_SURFACE_DRIFT" not in out


def test_unfrozen_change_stays_clean(repo: Path, capsys: pytest.CaptureFixture) -> None:
    """The check is scoped to frozen surfaces, not a blanket whole-tree hash."""
    assert _emit(repo) == 0
    _write(repo, "docs/note.md", b"# note\n\nrewritten\n")
    _write(repo, "src/mj_agent/agent.py", b"ACTIVE = ('a',)\n")
    _commit(repo, "ordinary work")
    capsys.readouterr()
    assert _check(repo) == 0
    assert capsys.readouterr().out.strip().splitlines()[-1] == "TASK0_FREEZE_CLEAN"


def test_missing_baseline_exits_two_and_never_zero(
    repo: Path, capsys: pytest.CaptureFixture
) -> None:
    """An absent baseline is not a pass — the PR-0c `SKIP is never a PASS` rule."""
    rc = _check(repo)
    assert rc == 2
    captured = capsys.readouterr()
    assert captured.out.strip().splitlines()[-1] == "ERROR_NO_BASELINE"
    assert "nothing was verified" in captured.err


def test_malformed_baseline_exits_two(repo: Path, capsys: pytest.CaptureFixture) -> None:
    assert _emit(repo) == 0
    (repo / OUT_DIR / task0_freeze.IDENTITY_NAME).write_text("{not json", encoding="utf-8")
    capsys.readouterr()
    assert _check(repo) == 2
    assert capsys.readouterr().out.strip().splitlines()[-1] == "ERROR_MALFORMED_BASELINE"


def test_baseline_with_wrong_schema_version_exits_two(
    repo: Path, capsys: pytest.CaptureFixture
) -> None:
    assert _emit(repo) == 0
    path = repo / OUT_DIR / task0_freeze.IDENTITY_NAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = "task0-freeze-identity-v0"
    path.write_text(json.dumps(payload), encoding="utf-8")
    capsys.readouterr()
    assert _check(repo) == 2
    assert capsys.readouterr().out.strip().splitlines()[-1] == "ERROR_MALFORMED_BASELINE"


def test_mode_flip_on_a_hard_frozen_file_stops(
    repo: Path, capsys: pytest.CaptureFixture
) -> None:
    """An exec bit landing on a frozen hook script is drift even with identical content."""
    assert _emit(repo) == 0
    _git(repo, "update-index", "--chmod=+x", ".claude/settings.json")
    _commit(repo, "flip exec bit")

    raw = subprocess.run(
        ["git", "diff", "HEAD~1", "HEAD", "--raw"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "100644 100755" in raw, f"fixture did not actually flip the mode: {raw!r}"

    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "STOP_FROZEN_SURFACE_DRIFT"
    assert "MODE     .claude/settings.json" in out
    assert "baseline mode=100644" in out
    assert "current  mode=100755" in out


def test_gitlink_under_a_hard_frozen_prefix_is_visible_and_stops(
    repo: Path, capsys: pytest.CaptureFixture
) -> None:
    """A submodule grafted under `.claude/` must not be invisible to the identity."""
    assert _emit(repo) == 0
    before = _identity(repo)["identity_digest"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True, check=True
    ).stdout.strip()

    _git(repo, "update-index", "--add", "--cacheinfo", f"160000,{head},.claude/vendor")
    _write(repo, ".gitmodules", b'[submodule "vendor"]\n\tpath = .claude/vendor\n')
    _git(repo, "add", ".gitmodules")
    _git(repo, "commit", "-q", "-m", "graft gitlink")

    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "STOP_FROZEN_SURFACE_DRIFT"
    assert "ADDED    .claude/vendor" in out

    assert _emit(repo) == 0
    identity = _identity(repo)
    assert identity["identity_digest"] != before
    graft = [f for f in identity["hard_frozen"]["files"] if f["path"] == ".claude/vendor"]
    assert len(graft) == 1, "gitlink absent from the frozen block"
    assert graft[0]["mode"] == "160000"
    assert graft[0]["sha256"] == task0_freeze.gitlink_digest(head)


def test_identity_digest_mismatch_alone_is_treated_as_drift(
    repo: Path, capsys: pytest.CaptureFixture
) -> None:
    """The digest is the authority; an unlocatable difference must not read as clean."""
    assert _emit(repo) == 0
    path = repo / OUT_DIR / task0_freeze.IDENTITY_NAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["identity_digest"] = "0" * 64  # files[] left untouched and still matching
    path.write_text(json.dumps(payload), encoding="utf-8")

    capsys.readouterr()
    assert _check(repo) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "STOP_FROZEN_SURFACE_DRIFT"
    assert "IDENTITY digest differs with no per-file difference located" in out


def test_identity_digest_changes_when_a_frozen_file_changes(repo: Path) -> None:
    assert _emit(repo) == 0
    before = _identity(repo)["identity_digest"]
    _write(repo, "CLAUDE.md", b"# CLAUDE\n\nchanged\n")
    _commit(repo, "touch CLAUDE.md")
    assert _emit(repo) == 0
    assert _identity(repo)["identity_digest"] != before


def test_emit_outside_a_repo_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    assert task0_freeze.main(["--emit", "--out-dir", OUT_DIR], repo_root=empty) == 2
    captured = capsys.readouterr()
    assert captured.out.strip().splitlines()[-1] == "ERROR_NOT_A_REPO"
    assert "nothing was verified" in captured.err
    assert not (empty / OUT_DIR).exists(), "failed emit must not leave partial artifacts"


def test_check_outside_a_repo_reports_missing_baseline_first(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    empty = tmp_path / "also-not-a-repo"
    empty.mkdir()
    assert task0_freeze.main(["--check", "--out-dir", OUT_DIR], repo_root=empty) == 2
    assert capsys.readouterr().out.strip().splitlines()[-1] == "ERROR_NO_BASELINE"
