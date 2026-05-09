#!/usr/bin/env python3
"""Corpus-wide guard: no living references to archived framework files.

After Phase B promote and Phase C-1a active path stabilization, the
archived framework files at ``docs/archive/rule/`` must be referenced
via the archive prefix path (e.g.,
``[[archive/rule/[STANDARD]_..._v2.1|...]]``). A bare mention of an
archived basename outside ``docs/archive/`` is a *living* reference
that should have been migrated to the active stable path
(``rule/[STANDARD]_..._Meta_Framework`` etc.).

This is the ADR-011 §5.6.4 living/frozen contract, refined by ADR-018
§Decision (active path stability) and ADR-017 §5.9 (archive trigger
quantification). Phase C-3 will refactor this to auto-discover NEEDLES
from ``docs/archive/`` directory; Phase C-1a is the transitional list.

Walks ``docs/``, ``plans/``, ``src/``, plus ``CLAUDE.md`` at the repo
root. Skips files under ``docs/archive/`` (those are allowed to
reference archived files since the archive lives there). Prints any
violation as ``<file>:<line>:<text>`` and exits 1; on success prints
``OK: 0 violations`` and exits 0.

Standard library only. Cross-platform via ``pathlib``.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Each archived framework full filename (with ``[STANDARD]_MJ_Agent_``
# prefix). Using the full filename — not just the basename — avoids
# false-positives on narrative placeholders like
# ``[STANDARD]_..._Documentation_Meta_Framework_v2.0`` (which appears
# in ADR-012's directory tree code block describing the v1.1 → v2.0
# transition; the ``...`` placeholder breaks the prefix match). Extending
# this list (Phase C-1b / C-3) requires syncing ``ARCHIVE_PREFIXES``.
NEEDLES: tuple[str, ...] = (
    "[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.0",
    "[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1",
    "[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0",
    "[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1",  # archived in Phase C-1a (ADR-018)
    "[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0",
    "[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0",
)

# A line containing any NEEDLE is permitted only if it also contains
# the corresponding ARCHIVE_PREFIX on the same line — that marks the
# reference as a frozen archive pin (e.g.
# ``[[archive/rule/[STANDARD]_..._v2.1|...]]`` or
# ``docs/archive/rule/[STANDARD]_..._v2.1.md``). Each entry pairs with
# the ``NEEDLES`` entry of the same index.
ARCHIVE_PREFIXES: tuple[str, ...] = tuple(f"archive/rule/{n}" for n in NEEDLES)

# Directory entries are walked recursively; the lone file entry is
# read verbatim. Paths are project-relative; the repo root is
# auto-detected as the parent of this script's directory.
WALK_DIRS = ("docs", "src")  # plans/ excluded — working docs naturally describe migrations using NEEDLE literals
WALK_FILES = ("CLAUDE.md",)
SKIP_PATH_PARTS = (("docs", "archive"),)
TEXT_SUFFIXES = {".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".json", ".cfg", ".ini"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


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


def scan_file(path: Path, rel: Path) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return violations
    for lineno, line in enumerate(text.splitlines(), start=1):
        for needle, archive_prefix in zip(NEEDLES, ARCHIVE_PREFIXES, strict=True):
            if needle not in line:
                continue
            if archive_prefix in line:
                # Frozen archive-pinned reference — allowed.
                continue
            violations.append((rel, lineno, line.rstrip()))
            break  # one violation per line per needle is enough
    return violations


def main() -> int:
    root = repo_root()
    self_rel = Path(__file__).resolve().relative_to(root)
    all_violations: list[tuple[Path, int, str]] = []
    for path, rel in iter_target_files(root):
        # Don't flag this script's own description of needles.
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
