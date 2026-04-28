#!/usr/bin/env python3
"""Corpus-wide guard: no living references to the archived v1.1 Framework.

After Phase 0.5 promote, ``[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1``
lives at ``docs/archive/rule/`` with ``state: deprecated``. Any reference to
that filename outside ``docs/archive/`` must be **frozen** — i.e., must point
explicitly at the archive path (``archive/rule/[STANDARD]_..._v1.1``). A bare
mention of the v1.1 filename (or a path beginning with ``docs/rule/`` or
``rule/[STANDARD]_..._v1.1``) is a *living* reference that should have been
migrated to the v2.0 trio (Meta_Framework_v2.0 + Code_Side_v1.0 +
Agent_Side_v1.0). This is the ADR-011 §5.6.2 living/frozen contract.

Walks ``docs/``, ``plans/``, ``src/``, plus the file ``CLAUDE.md`` at the repo
root. Skips files under ``docs/archive/`` (those are allowed to reference v1.1
since v1.1 lives there). Prints any violation as ``<file>:<line>:<text>`` and
exits 1; on success prints ``OK: 0 violations`` and exits 0.

Standard library only. Cross-platform via ``pathlib``.
"""
from __future__ import annotations

import sys
from pathlib import Path

NEEDLE = "Documentation_Management_Framework_v1.1"
# A line containing the needle is permitted if it also contains the archive
# prefix on the same line — that marks the reference as a frozen archive pin
# (e.g. ``[[archive/rule/[STANDARD]_..._v1.1|...]]`` or
# ``docs/archive/rule/[STANDARD]_..._v1.1.md``).
ARCHIVE_PREFIX = "archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1"

# Directory entries are walked recursively; the lone file entry is read
# verbatim. Paths are project-relative; the repo root is auto-detected as the
# parent of this script's directory.
WALK_DIRS = ("docs", "plans", "src")
WALK_FILES = ("CLAUDE.md",)
SKIP_PATH_PARTS = (("docs", "archive"),)
TEXT_SUFFIXES = {".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".json", ".cfg", ".ini"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_skipped(rel: Path) -> bool:
    parts = rel.parts
    for skip in SKIP_PATH_PARTS:
        if len(parts) >= len(skip) and parts[: len(skip)] == skip:
            return True
    return False


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


def scan_file(path: Path, rel: Path) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return violations
    for lineno, line in enumerate(text.splitlines(), start=1):
        if NEEDLE not in line:
            continue
        if ARCHIVE_PREFIX in line:
            # Frozen archive-pinned reference — allowed.
            continue
        violations.append((rel, lineno, line.rstrip()))
    return violations


def main() -> int:
    root = repo_root()
    self_rel = Path(__file__).resolve().relative_to(root)
    all_violations: list[tuple[Path, int, str]] = []
    for path, rel in iter_target_files(root):
        # Don't flag this script's own description of the needle.
        if rel == self_rel:
            continue
        all_violations.extend(scan_file(path, rel))
    if all_violations:
        for rel, lineno, line in all_violations:
            # Use POSIX-style separators for portable output.
            print(f"{rel.as_posix()}:{lineno}:{line}")
        print(f"FAIL: {len(all_violations)} violations", file=sys.stderr)
        return 1
    print("OK: 0 violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
