#!/usr/bin/env python3
"""Corpus-wide guard: no living references to archived framework files.

Auto-discovers archived files from the ``rule/`` archive directory by
globbing ``[DEPRECATED]_*.md``. The ``[DEPRECATED]_`` filename prefix is
mandated by ADR-019 (Phase C-1b). Each archived file's stem (without
``.md``) becomes a NEEDLE; the corresponding ARCHIVE_PREFIX is
``archive/rule/{stem}``.

NEEDLES are unioned from BOTH the legacy ``docs/archive/rule`` location
AND the future top-level ``archive/rule`` location (M5 Spec-Anchored
Refactor move target), so the guard is correct pre-move (docs/archive/rule
exists today) and post-move (archive/rule is born in the M5 move PRs).
The ARCHIVE_PREFIX (``archive/rule/{stem}``) is already the future form.

A line containing any NEEDLE outside ``docs/archive/`` is a *living*
reference; it is permitted only if the same line also contains the
corresponding ARCHIVE_PREFIX (frozen archive pin).

This generalizes the Phase C-1b transitional hardcoded NEEDLES list
(ADR-020; eliminates per-archive manual sync). New archived files
auto-discovered without script changes.

Standard library only. Cross-platform via ``pathlib``.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Walk roots and per-file targets. ``plans/`` is excluded — working
# documents naturally describe past migrations using NEEDLE literals
# (e.g., ``[DEPRECATED]_...`` in plan body code blocks).
#
# WALK_DIRS extended for the M5 Spec-Anchored Refactor: capabilities/,
# decisions/, policies/, sdd/, docker/ are where living refs to archived
# STANDARDs may sit post-move. docker/ doesn't exist yet — the
# ``if not base.exists(): continue`` guard in iter_target_files handles
# that absence.
WALK_DIRS = ("docs", "src", "capabilities", "decisions", "policies", "sdd", "docker")
WALK_FILES = ("CLAUDE.md",)
# Skip the legacy ``docs/archive`` tree AND the future top-level ``archive``
# tree (M5 move target) so archived files themselves are never flagged.
SKIP_PATH_PARTS = (("docs", "archive"), ("archive",))
TEXT_SUFFIXES = {".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".json", ".cfg", ".ini"}

# Auto-discovery configuration. NEEDLES are unioned across both archive
# locations (legacy docs/archive/rule + future top-level archive/rule).
ARCHIVE_DIRS = (Path("docs/archive/rule"), Path("archive/rule"))
# Glob: ``[DEPRECATED]_*.md``. Pathlib glob char-class escaping —
# literal ``[`` and ``]`` must each be wrapped in their own char class.
ARCHIVE_FILE_GLOB = "[[]DEPRECATED[]]_*.md"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def discover_needles(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Auto-discover NEEDLES + ARCHIVE_PREFIXES from archive directories.

    Unions stems across both ARCHIVE_DIRS (legacy ``docs/archive/rule`` +
    future top-level ``archive/rule``); whichever exist contribute. Returns
    sorted, de-duplicated tuples (filename stems and corresponding archive
    paths) so script behavior is deterministic across platforms.
    """
    stems: set[str] = set()
    for archive_dir in ARCHIVE_DIRS:
        base = root / archive_dir
        if not base.exists():
            continue
        stems.update(p.stem for p in base.glob(ARCHIVE_FILE_GLOB))
    needles = tuple(sorted(stems))
    archive_prefixes = tuple(f"archive/rule/{n}" for n in needles)
    return needles, archive_prefixes


def is_skipped(rel: Path) -> bool:
    parts = rel.parts
    return any(
        len(parts) >= len(skip) and parts[: len(skip)] == skip
        for skip in SKIP_PATH_PARTS
    )


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in WALK_FILES


def iter_target_files(root: Path):
    for d in WALK_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(root)
            if is_skipped(rel):
                continue
            if not is_text_file(p):
                continue
            yield p, rel
    for f in WALK_FILES:
        p = root / f
        if p.is_file():
            yield p, p.relative_to(root)


def scan_file(
    path: Path,
    rel: Path,
    needles: tuple[str, ...],
    archive_prefixes: tuple[str, ...],
) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return violations
    for lineno, line in enumerate(text.splitlines(), start=1):
        for needle, archive_prefix in zip(needles, archive_prefixes, strict=True):
            if needle not in line:
                continue
            if archive_prefix in line:
                # Frozen archive-pinned reference — allowed.
                continue
            violations.append((rel, lineno, line.rstrip()))
            break  # one violation per line is enough
    return violations


def main() -> int:
    root = repo_root()
    self_rel = Path(__file__).resolve().relative_to(root)
    needles, archive_prefixes = discover_needles(root)
    if not needles:
        scanned = ", ".join(d.as_posix() for d in ARCHIVE_DIRS)
        print(f"OK: no archived files discovered (scanned {scanned})")
        return 0
    all_violations: list[tuple[Path, int, str]] = []
    for path, rel in iter_target_files(root):
        # Don't flag this script's own description of needles.
        if rel == self_rel:
            continue
        all_violations.extend(scan_file(path, rel, needles, archive_prefixes))
    if all_violations:
        for rel, lineno, line in all_violations:
            # Use POSIX-style separators for portable output.
            print(f"{rel.as_posix()}:{lineno}:{line}")
        print(f"FAIL: {len(all_violations)} violations", file=sys.stderr)
        return 1
    print(f"OK: 0 violations ({len(needles)} archived files auto-discovered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
