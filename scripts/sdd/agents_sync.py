"""agents_sync.py — scoped projection generator, emitter A: skills (dual-agent-compat v5 S1).

Contract: plans/[PLAN]_dual-agent-compat.md §8 (generator terms) + D-011 (scoped, two
surfaces only — this module covers `.agents/skills/`; the `.codex/config.toml` emitter B
is S2, spike-gated) + D-012 (artifacts committed, generator-owned, never hand-edited)
+ D-014 (whitelist SoT = manifest `projection: project` entries).
Drift gate: CI mounts `--check` warning-first (V10 in sdd/gates.md §2, per D-016).

Modes (exactly one; `doctor` is S3 — not implemented here):
  sync            Regenerate `.agents/skills/<name>/SKILL.md` (raw-byte copy of the
                  whitelisted `.claude/skills/<name>/SKILL.md` sources), the directory
                  README (`.agents/README.md`, fixed template), and `.agents.lock.json`
                  (name -> `sha256:<body_sha256>` over LF-normalized artifact text —
                  byte-compatible with V9 `check_agents_projection.check_lock`).
                  Full reconcile: anything under `.agents/` outside the expected file
                  set is deleted (orphan projections, stray files). Idempotent.
  --check         Read-only drift check. All content comparisons are LF-normalized
                  (F10: `.md` is not eol-pinned in .gitattributes, so Windows checkouts
                  are CRLF while ubuntu CI checkouts are LF). Exit 1 on any drift, with
                  the prescribed action printed once.
  --adopt NAME    Explicit reverse-feed (D-012): copy the artifact bytes back over the
                  source SKILL.md (the source's own gates / Owner HITL apply to that
                  write), then run the sync routine so lock + README realign.

Generation is a pure syntactic transformation: zero env parsing, zero network, zero
secrets — safe on forks and clean clones (plan §8).
Exit codes: 0 clean/success; 1 drift; 2 usage error / manifest or source unreadable.
`main(argv=None, repo_root=None)` — repo_root injectable for tests (#217 pattern).
ASCII-only output (#318 lesson: Windows consoles may not be UTF-8).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

_SCRIPT_NAME = "agents_sync.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.frontmatter import body_sha256  # noqa: E402
from scripts.sdd.check_agents_projection import (  # noqa: E402
    FatalCheckError,
    load_project_set,
)

SOURCE_DIR = Path(".claude/skills")
AGENTS_DIR = Path(".agents")
SKILLS_DIR = AGENTS_DIR / "skills"
LOCK_RELPATH = Path(".agents.lock.json")

README_TEMPLATE = """\
# GENERATED — do not edit anything under `.agents/`

Every file in this tree plus the repo-root `.agents.lock.json` is a **generated
artifact** owned 100% by `scripts/sdd/agents_sync.py` (dual-agent-compat v5,
ADR-036 D-011/D-012/D-014). `.agents/skills/<name>/SKILL.md` is a byte-identical
projection of `.claude/skills/<name>/SKILL.md` for every manifest capability with
`projection: project` (`sdd/development-agent.yml` is the whitelist SoT). Codex
discovers these skills natively under `.agents/skills`; projected copies do NOT
count toward the 37-skill SoT.

How to change a projected skill:

1. Edit the SOURCE: `.claude/skills/<name>/SKILL.md` (its own gates apply).
2. Run `python scripts/sdd/agents_sync.py sync`.
3. Commit source + artifacts + `.agents.lock.json` together.

Never hand-edit these files — CI runs `agents_sync.py --check` (drift gate V10)
and `check_agents_projection.py` (V9) against them. To reverse-feed an artifact
edit into the source use `python scripts/sdd/agents_sync.py --adopt <name>`
(Owner HITL applies). On merge conflicts in generated files: merge the source,
re-run `sync` to overwrite the artifacts — do not 3-way-merge artifacts.

Semantic difference declaration: the Claude Code harness `ask`-gates, protected-path
prompts and PreToolUse hooks referenced inside projected skill bodies are NOT present
under Codex. Under Codex those stop points are AGENTS.md self-enforced duties
(see the repo-root `AGENTS.md`, sections "Self-enforced boundaries" and
"Generated projections").
"""

PRESCRIBED_ACTION = (
    "Prescribed action (D-012): edit the SOURCE (.claude/skills/<name>/SKILL.md),"
    " then run `python scripts/sdd/agents_sync.py sync` and commit source + artifacts"
    " + .agents.lock.json together. Never hand-edit .agents/** or .agents.lock.json."
    " To reverse-feed an artifact edit into the source, run"
    " `python scripts/sdd/agents_sync.py --adopt <name>` (Owner HITL applies)."
    " On merge conflicts in generated files: merge the source, re-run `sync` to"
    " overwrite the artifacts - do not 3-way-merge artifacts."
)


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def _read_lf(path: Path) -> str:
    return _lf(path.read_text(encoding="utf-8"))


def _lock_hash(artifact_text: str) -> str:
    """LF-normalized body hash, byte-compatible with V9 `_normalized_body_hash`."""
    return "sha256:" + body_sha256(_lf(artifact_text))


def _expected_lock(repo_root: Path, project: set[str]) -> dict[str, str]:
    lock: dict[str, str] = {}
    for name in sorted(project):
        artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
        if artifact.is_file():
            lock[name] = _lock_hash(artifact.read_text(encoding="utf-8"))
    return lock


def _lock_text(lock: dict[str, str]) -> str:
    return json.dumps(lock, indent=2, sort_keys=True) + "\n"


def _source_path(repo_root: Path, name: str) -> Path:
    return repo_root / SOURCE_DIR / name / "SKILL.md"


def _require_sources(repo_root: Path, project: set[str]) -> None:
    missing = [n for n in sorted(project) if not _source_path(repo_root, n).is_file()]
    if missing:
        raise FatalCheckError(
            "projection source missing for: " + ", ".join(missing)
            + " (manifest `projection: project` entries need on-disk SKILL.md)"
        )


def _expected_files(project: set[str]) -> set[Path]:
    """Relative paths (under repo root) that may exist inside `.agents/`."""
    expected = {AGENTS_DIR / "README.md"}
    for name in project:
        expected.add(SKILLS_DIR / name / "SKILL.md")
    return expected


def do_sync(repo_root: Path, project: set[str]) -> list[str]:
    """Regenerate artifacts + README + lock; full reconcile. Returns change log."""
    _require_sources(repo_root, project)
    changes: list[str] = []

    # Full reconcile FIRST: delete anything under .agents/ outside the expected set,
    # so a stray file/dir squatting on an expected path never crashes the copy pass.
    expected = _expected_files(project)
    expected_dirs = {p.parent for p in expected} | {AGENTS_DIR, SKILLS_DIR}
    agents_root = repo_root / AGENTS_DIR
    if agents_root.is_dir():
        for path in sorted(agents_root.rglob("*"), reverse=True):
            if not path.exists():
                continue  # parent already removed earlier in the walk
            rel = path.relative_to(repo_root)
            if path.is_file() and rel not in expected:
                path.unlink()
                changes.append(f"remove {rel.as_posix()}")
            elif path.is_dir() and rel not in expected_dirs:
                shutil.rmtree(path)
                changes.append(f"remove {rel.as_posix()}/")

    for name in sorted(project):
        src = _source_path(repo_root, name)
        dst = repo_root / SKILLS_DIR / name / "SKILL.md"
        data = src.read_bytes()
        if not dst.is_file() or dst.read_bytes() != data:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            changes.append(f"write {SKILLS_DIR.as_posix()}/{name}/SKILL.md")

    readme = repo_root / AGENTS_DIR / "README.md"
    if not readme.is_file() or _read_lf(readme) != README_TEMPLATE:
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(README_TEMPLATE, encoding="utf-8", newline="\n")
        changes.append(f"write {AGENTS_DIR.as_posix()}/README.md")

    lock_path = repo_root / LOCK_RELPATH
    lock_text = _lock_text(_expected_lock(repo_root, project))
    if not lock_path.is_file() or _read_lf(lock_path) != lock_text:
        lock_path.write_text(lock_text, encoding="utf-8", newline="\n")
        changes.append(f"write {LOCK_RELPATH.as_posix()}")

    return changes


def do_check(repo_root: Path, project: set[str]) -> list[str]:
    """Read-only drift check (LF-normalized). Returns drift messages."""
    _require_sources(repo_root, project)
    drift: list[str] = []

    for name in sorted(project):
        artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
        if not artifact.is_file():
            drift.append(f"missing artifact: {SKILLS_DIR.as_posix()}/{name}/SKILL.md")
            continue
        if _read_lf(artifact) != _read_lf(_source_path(repo_root, name)):
            drift.append(
                f"artifact != source for '{name}' (hand-edited artifact OR source"
                " edited without re-running sync)"
            )

    readme = repo_root / AGENTS_DIR / "README.md"
    if not readme.is_file():
        drift.append(f"missing {AGENTS_DIR.as_posix()}/README.md")
    elif _read_lf(readme) != README_TEMPLATE:
        drift.append(f"{AGENTS_DIR.as_posix()}/README.md differs from the fixed template")

    expected = _expected_files(project)
    expected_dirs = {p.parent for p in expected} | {AGENTS_DIR, SKILLS_DIR}
    agents_root = repo_root / AGENTS_DIR
    if agents_root.is_dir():
        for path in sorted(agents_root.rglob("*")):
            rel = path.relative_to(repo_root)
            if path.is_file() and rel not in expected:
                drift.append(f"unexpected file: {rel.as_posix()} (full reconcile)")
            elif path.is_dir() and rel not in expected_dirs:
                drift.append(f"unexpected directory: {rel.as_posix()}/ (full reconcile)")

    lock_path = repo_root / LOCK_RELPATH
    if not lock_path.is_file():
        drift.append(f"missing {LOCK_RELPATH.as_posix()}")
    elif _read_lf(lock_path) != _lock_text(_expected_lock(repo_root, project)):
        drift.append(
            f"{LOCK_RELPATH.as_posix()} out of date (lock is regenerated by sync,"
            " one sorted entry per line)"
        )

    return drift


def do_adopt(repo_root: Path, project: set[str], name: str) -> list[str]:
    """Copy artifact bytes back over the source, then realign via sync."""
    if name not in project:
        raise FatalCheckError(
            f"--adopt target '{name}' is not a manifest `projection: project` capability"
        )
    artifact = repo_root / SKILLS_DIR / name / "SKILL.md"
    if not artifact.is_file():
        raise FatalCheckError(f"--adopt target artifact missing: {artifact}")
    src = _source_path(repo_root, name)
    changes: list[str] = []
    data = artifact.read_bytes()
    # A missing source is a legitimate recovery state (restore a deleted source
    # from its committed artifact) — recreate it instead of crashing.
    if not src.is_file() or src.read_bytes() != data:
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(data)
        changes.append(f"adopt {SOURCE_DIR.as_posix()}/{name}/SKILL.md <- artifact")
    changes += do_sync(repo_root, project)
    return changes


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description=(
            "Scoped projection generator, emitter A: .claude/skills whitelist ->"
            " .agents/skills byte-identical artifacts + .agents.lock.json"
            " (plan §8, D-011/D-012/D-014; `doctor` lands at S3)"
        ),
    )
    parser.add_argument(
        "command", nargs="?", choices=["sync"],
        help="regenerate artifacts + README + lock (full reconcile; idempotent)",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="read-only drift check (LF-normalized); exit 1 on drift",
    )
    parser.add_argument(
        "--adopt", metavar="SKILL",
        help="explicit reverse-feed: artifact -> source, then realign (Owner HITL applies)",
    )
    args = parser.parse_args(argv)
    root = repo_root if repo_root is not None else _REPO_ROOT

    modes = [args.command == "sync", args.check, args.adopt is not None]
    if sum(modes) != 1:
        parser.print_usage(sys.stderr)
        print(
            f"{_SCRIPT_NAME}: exactly one mode required: `sync` XOR --check XOR --adopt",
            file=sys.stderr,
        )
        return 2

    try:
        project, _ = load_project_set(root)
        if args.check:
            drift = do_check(root, project)
            for line in drift:
                print(f"[DRIFT] {line}")
            if drift:
                print(PRESCRIBED_ACTION)
                return 1
            print(f"OK: projection in sync ({len(project)} skills, lock consistent)")
            return 0
        if args.adopt is not None:
            changes = do_adopt(root, project, args.adopt)
            for line in changes:
                print(line)
            print(
                "NOTE: --adopt wrote the SOURCE skill; the source's own gates / Owner"
                " HITL apply to that change. Review and commit source + artifacts +"
                " lock together."
            )
            return 0
        changes = do_sync(root, project)
        for line in changes:
            print(line)
        print(
            f"OK: {len(changes)} change(s)" if changes
            else f"OK: up to date ({len(project)} skills)"
        )
        return 0
    except FatalCheckError as exc:
        print(f"{_SCRIPT_NAME}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
