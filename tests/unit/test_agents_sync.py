"""Unit tests for agents_sync.py (scoped projection generator, emitter A — S1 #326).

Covers: sync artifact/README/lock generation + idempotency, --check drift tri-state
(clean / hand-edited artifact / source edited without sync) with prescribed-action
text, full-reconcile negatives (orphan projection dirs, stray files), cross-EOL
stability (F10: Windows CRLF checkout vs ubuntu LF checkout must agree on lock
hashes and --check verdicts), --adopt reverse-feed, mode exclusivity / exit codes,
V9 (check_agents_projection) integration on generated artifacts, and a real-tree
pin (committed artifacts stay in sync).

Fixtures reuse `make_repo` / `cap` from test_sdd_development_agent and inject
tmp_path via `main(argv, repo_root=...)` (#217 pattern) — never mutate the live tree.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from scripts.sdd.agents_sync import PRESCRIBED_ACTION
from scripts.sdd.agents_sync import main as sync_main
from scripts.sdd.check_agents_projection import main as v9_main

from tests.unit.test_sdd_development_agent import cap, make_repo

REPO_ROOT = Path(__file__).resolve().parents[2]

PROJECT_SKILLS = ("mj-agent-alpha", "mj-agent-beta")


def make_projection_repo(tmp_path: Path, *, bodies: dict[str, str] | None = None) -> Path:
    caps = [cap(name, projection="project") for name in PROJECT_SKILLS]
    caps.append(cap("mj-agent-gamma", projection="never"))
    return make_repo(tmp_path, caps, skill_bodies=bodies)


def _snapshot(root: Path) -> dict[str, bytes]:
    files = [root / ".agents.lock.json", *sorted((root / ".agents").rglob("*"))]
    return {str(p): p.read_bytes() for p in files if p.is_file()}


# ------------------------------------------------------------------ sync


def test_sync_creates_artifacts_readme_lock(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    for name in PROJECT_SKILLS:
        src = root / ".claude" / "skills" / name / "SKILL.md"
        dst = root / ".agents" / "skills" / name / "SKILL.md"
        assert dst.read_bytes() == src.read_bytes()  # byte-identical projection
    assert not (root / ".agents" / "skills" / "mj-agent-gamma").exists()  # never tier
    assert "GENERATED" in (root / ".agents" / "README.md").read_text(encoding="utf-8")
    lock = json.loads((root / ".agents.lock.json").read_text(encoding="utf-8"))
    assert set(lock) == set(PROJECT_SKILLS)
    assert all(v.startswith("sha256:") for v in lock.values())
    # one sorted entry per line localizes merge conflicts (plan §8) — pin BOTH
    # properties: per-line entries (a compact-JSON regression collapses them to
    # one line) AND sortedness
    lines = (root / ".agents.lock.json").read_text(encoding="utf-8").splitlines()
    entry_lines = [ln for ln in lines if '"mj-agent-' in ln]
    assert len(entry_lines) == len(PROJECT_SKILLS)
    assert entry_lines == sorted(entry_lines)


def test_sync_is_idempotent(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    before = _snapshot(root)
    assert sync_main(["sync"], repo_root=root) == 0
    assert "up to date" in capsys.readouterr().out
    assert _snapshot(root) == before


def test_sync_reconciles_orphans_and_strays(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    orphan = root / ".agents" / "skills" / "mj-agent-orphan" / "SKILL.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("rogue\n", encoding="utf-8")
    (root / ".agents" / "stray.txt").write_text("stray\n", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 0
    assert not orphan.parent.exists()
    assert not (root / ".agents" / "stray.txt").exists()
    assert sync_main(["--check"], repo_root=root) == 0


def test_sync_missing_source_exits_2(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    (root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md").unlink()
    assert sync_main(["sync"], repo_root=root) == 2
    assert "source missing" in capsys.readouterr().err


# ------------------------------------------------------------------ --check tri-state


def test_check_clean_after_sync(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert sync_main(["--check"], repo_root=root) == 0
    assert "OK: projection in sync" in capsys.readouterr().out


def test_check_hand_edited_artifact_red_with_prescribed_action(
    tmp_path: Path, capsys: Any
) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    artifact.write_text(
        artifact.read_text(encoding="utf-8") + "\nrogue edit\n", encoding="utf-8"
    )
    assert sync_main(["--check"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "artifact != source" in out
    assert PRESCRIBED_ACTION in out
    # independently pin the plan §12 content elements (NOT via the constant, so a
    # trimmed/reworded PRESCRIBED_ACTION cannot silently drop them):
    assert "edit the SOURCE" in out
    assert "agents_sync.py sync" in out
    assert "--adopt" in out  # reverse-feed path
    assert "merge the source" in out and "3-way-merge" in out  # merge-conflict rule


def test_check_source_edited_without_sync_red(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-beta" / "SKILL.md"
    src.write_text(src.read_text(encoding="utf-8") + "\nnew source line\n", encoding="utf-8")
    assert sync_main(["--check"], repo_root=root) == 1
    assert "artifact != source" in capsys.readouterr().out


def test_check_extra_file_and_missing_lock_red(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    (root / ".agents" / "skills" / "mj-agent-alpha" / "extra.txt").write_text(
        "x\n", encoding="utf-8"
    )
    (root / ".agents.lock.json").unlink()
    assert sync_main(["--check"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "unexpected file" in out
    assert "missing .agents.lock.json" in out


def test_check_red_when_agents_tree_absent(tmp_path: Path, capsys: Any) -> None:
    """Fresh pre-sync tree (non-empty project set, no .agents/) must be drift, not
    a vacuous pass — unlike V9's S0 empty-state rule, V10 requires artifacts."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["--check"], repo_root=root) == 1
    out = capsys.readouterr().out
    assert "missing artifact" in out
    assert "missing .agents/README.md" in out
    assert "missing .agents.lock.json" in out


def test_check_red_when_artifacts_deleted_but_lock_remains(
    tmp_path: Path, capsys: Any
) -> None:
    """PJ030 analog: lock present while the .agents/ tree is gone must go red."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    shutil.rmtree(root / ".agents")
    assert sync_main(["--check"], repo_root=root) == 1
    assert "missing artifact" in capsys.readouterr().out


def test_sync_replaces_stray_file_squatting_on_skill_dir_path(tmp_path: Path) -> None:
    """--check prescribes 'run sync' for a mangled tree; sync must reconcile a stray
    FILE at .agents/skills/<name> instead of crashing on mkdir (review finding #2)."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    skill_dir = root / ".agents" / "skills" / "mj-agent-alpha"
    shutil.rmtree(skill_dir)
    skill_dir.write_text("stray\n", encoding="utf-8")
    assert sync_main(["sync"], repo_root=root) == 0
    assert (skill_dir / "SKILL.md").is_file()
    assert sync_main(["--check"], repo_root=root) == 0


# ------------------------------------------------------------------ F10 cross-EOL


def test_cross_eol_lock_hash_and_check_stable(tmp_path: Path) -> None:
    """Same logical content as CRLF (Windows checkout) vs LF (ubuntu checkout):
    lock hashes must be identical and --check must stay green either way."""
    body = "# mj-agent-alpha\n\nbody line\n"
    fm = "---\nname: mj-agent-alpha\ndescription: fixture\n---\n\n"
    root_lf = make_projection_repo(tmp_path / "lf")
    root_crlf = make_projection_repo(tmp_path / "crlf")
    (root_lf / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md").write_bytes(
        (fm + body).encode("utf-8")
    )
    (root_crlf / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md").write_bytes(
        (fm + body).replace("\n", "\r\n").encode("utf-8")
    )
    assert sync_main(["sync"], repo_root=root_lf) == 0
    assert sync_main(["sync"], repo_root=root_crlf) == 0
    lock_lf = json.loads((root_lf / ".agents.lock.json").read_text(encoding="utf-8"))
    lock_crlf = json.loads((root_crlf / ".agents.lock.json").read_text(encoding="utf-8"))
    assert lock_lf["mj-agent-alpha"] == lock_crlf["mj-agent-alpha"]
    # simulate git flipping the artifact's checkout EOL under an unchanged source
    artifact = root_lf / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    artifact.write_bytes(artifact.read_bytes().replace(b"\n", b"\r\n"))
    assert sync_main(["--check"], repo_root=root_lf) == 0


# ------------------------------------------------------------------ --adopt


def test_adopt_reverse_feeds_source_and_realigns(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    artifact = root / ".agents" / "skills" / "mj-agent-alpha" / "SKILL.md"
    edited = artifact.read_text(encoding="utf-8") + "\nadopted line\n"
    artifact.write_text(edited, encoding="utf-8")
    assert sync_main(["--check"], repo_root=root) == 1
    capsys.readouterr()
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    out = capsys.readouterr().out
    assert "adopt .claude/skills/mj-agent-alpha/SKILL.md <- artifact" in out
    assert "Owner" in out  # HITL reminder
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    assert src.read_text(encoding="utf-8") == edited
    assert sync_main(["--check"], repo_root=root) == 0  # lock realigned by adopt's sync


def test_adopt_unknown_or_non_project_target_exits_2(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert sync_main(["--adopt", "mj-agent-gamma"], repo_root=root) == 2  # never tier
    assert "not a manifest" in capsys.readouterr().err


def test_adopt_missing_artifact_exits_2(tmp_path: Path, capsys: Any) -> None:
    root = make_projection_repo(tmp_path)  # pre-sync: no artifacts yet
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 2
    assert "artifact missing" in capsys.readouterr().err


def test_adopt_restores_deleted_source(tmp_path: Path) -> None:
    """Recovery path (review finding #1): a deleted source is restored from its
    committed artifact instead of crashing with FileNotFoundError."""
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    src = root / ".claude" / "skills" / "mj-agent-alpha" / "SKILL.md"
    expected = src.read_bytes()
    src.unlink()
    assert sync_main(["--adopt", "mj-agent-alpha"], repo_root=root) == 0
    assert src.read_bytes() == expected
    assert sync_main(["--check"], repo_root=root) == 0


# ------------------------------------------------------------------ CLI contract


def test_mode_exclusivity_exits_2(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main([], repo_root=root) == 2
    assert sync_main(["sync", "--check"], repo_root=root) == 2
    assert sync_main(["sync", "--adopt", "mj-agent-alpha"], repo_root=root) == 2


# ------------------------------------------------------------------ V9 integration


def test_v9_accepts_generated_artifacts_and_flags_hand_edits(tmp_path: Path) -> None:
    root = make_projection_repo(tmp_path)
    assert sync_main(["sync"], repo_root=root) == 0
    assert v9_main(["--all"], repo_root=root) == 0  # closure/reconcile/lock all green
    artifact = root / ".agents" / "skills" / "mj-agent-beta" / "SKILL.md"
    artifact.write_text(
        artifact.read_text(encoding="utf-8") + "\nrogue\n", encoding="utf-8"
    )
    assert v9_main(["--all"], repo_root=root) == 1  # PJ033 lock hash mismatch


# ------------------------------------------------------------------ real-tree pin


def test_real_tree_projection_in_sync() -> None:
    """Committed artifacts + lock must match sources (D-012: regenerate, never edit)."""
    assert sync_main(["--check"], repo_root=REPO_ROOT) == 0
