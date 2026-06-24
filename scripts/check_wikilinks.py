#!/usr/bin/env python3
"""Corpus-wide guard: archived-reference forward-guard + root-file link resolution.

Two checks live here:

1. **Archive forward-guard (blocking).** Auto-discovers archived files from
   the ``rule/`` archive directory by globbing ``[DEPRECATED]_*.md``. The
   ``[DEPRECATED]_`` filename prefix is mandated by ADR-019 (Phase C-1b).
   Each archived file's stem becomes a NEEDLE; a line containing any NEEDLE
   outside ``docs/archive/`` is a *living* reference, permitted only if the
   same line also contains the corresponding ``archive/rule/{stem}`` pin.
   NEEDLES are auto-discovered (ADR-020) — new archived files need no script
   change. WALK_FILES now covers all 5 project-root files (was CLAUDE.md
   only), closing the M6 sweep gap that left ``GLOSSARY.md`` unguarded
   (#266 / #267 item 1).

2. **A4 root-file link resolution (warning mode).** Resolves Markdown
   ``[text](target)`` and Obsidian ``[[target]]`` link targets in the 5
   project-root files and warns on any that do not resolve to an existing
   path. This is the partial-A4 gate registered in #267 item 2 — it catches
   *moved/renamed/deleted* link targets (e.g. a root file still pointing at
   a STANDARD that was archived) that the NEEDLE-substring archive guard
   cannot see. Warning mode by default (does not affect exit code); set
   ``MJ_AGENT_A4_STRICT=1`` to make it blocking (a deliberate
   ``ci-blocking-gate-toggle`` decision, not yet flipped).

Standard library only. Cross-platform via ``pathlib``.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# The 5 project-root markdown files (gate-light per documentation.md §2.6).
ROOT_FILES = ("README.md", "CONTRIBUTING.md", "CHANGELOG.md", "GLOSSARY.md", "CLAUDE.md")

# Walk roots and per-file targets for the archive forward-guard. ``plans/``
# is excluded — working documents naturally describe past migrations using
# NEEDLE literals (e.g., ``[DEPRECATED]_...`` in plan body code blocks).
#
# WALK_DIRS extended for the M5 Spec-Anchored Refactor: capabilities/,
# decisions/, policies/, sdd/, docker/ are where living refs to archived
# STANDARDs may sit post-move. docker/ doesn't exist yet — the
# ``if not base.exists(): continue`` guard in iter_target_files handles that.
WALK_DIRS = ("docs", "src", "capabilities", "decisions", "policies", "sdd", "docker")
# #267 item 1: extend the archive forward-guard from CLAUDE.md-only to all
# 5 root files. GLOSSARY.md's dangling ``docs/rule/`` links (the M6 sweep
# gap) are now in-scope for the guard.
WALK_FILES = ROOT_FILES
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

# --- A4 link-resolution config (#267 item 2) ---
# Match the ``](target)`` closing of a Markdown link and capture only the
# target. Matching the target-only form (not ``[text](target)``) is
# deliberate: mj-agent filenames embed ``[STANDARD]`` / ``[ADR]`` brackets,
# so the link *text* routinely contains ``]`` and would break a
# text-inclusive pattern.
_MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")
# Obsidian wikilink: ``[[target|display]]`` / ``[[target#anchor]]``.
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
# Inline code spans (single backtick) are stripped before link extraction so
# example links inside `code` are not resolved.
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
# A target is "external" (skip) if it carries a URL scheme, is
# protocol-relative (``//``), or is a same-document anchor (``#``).
_EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.\-]*:|//|#)", re.IGNORECASE)


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


# --- A4 link resolution (#267 item 2) ---


def iter_content_lines(text: str):
    """Yield ``(lineno, line)`` for lines outside fenced code blocks.

    Tracks ```` ``` ```` / ``~~~`` fences so link-shaped example text inside
    code blocks is not resolved. The fence lines themselves are skipped.
    """
    in_fence = False
    fence_marker = ""
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif stripped.startswith(fence_marker):
                in_fence, fence_marker = False, ""
            continue
        if in_fence:
            continue
        yield lineno, line


def clean_target(raw: str, kind: str) -> str | None:
    """Normalize a captured link target; return None if it should be skipped.

    Skips external (scheme / protocol-relative), same-document anchors, and
    absolute (``/...``) targets. Strips Markdown link titles, angle brackets,
    wikilink display text (``|``), and ``#anchor`` fragments.
    """
    t = raw.strip()
    if kind == "md":
        if t.startswith("<"):
            t = t[1:].split(">", 1)[0]
        else:
            # drop an optional ``"title"`` / ``'title'`` after the path
            t = t.split(None, 1)[0] if t.split() else ""
    else:  # wiki — split on the display pipe, escaped (``\|`` in GFM table
        # cells) or bare; drop any trailing escape backslash.
        t = re.split(r"\\?\|", t, maxsplit=1)[0].strip()
    t = t.split("#", 1)[0].strip()
    if not t or t.startswith("/"):
        return None
    if _EXTERNAL_RE.match(t):
        return None
    return t


def target_resolves(root: Path, target: str) -> bool:
    """True if ``target`` (repo-root-relative) resolves to an existing path.

    Root files live at the repo root, so relative targets resolve from there.
    Extensionless targets (typical of wikilinks) also try a ``.md`` suffix.
    Bracketed mj-agent filenames resolve literally (pathlib, not glob).
    """
    if (root / target).exists():
        return True
    return not target.endswith(".md") and (root / f"{target}.md").exists()


def scan_links(root: Path, rel: Path, text: str) -> list[tuple[Path, int, str, str]]:
    """Return ``(rel, lineno, kind, target)`` for each unresolved link target."""
    unresolved: list[tuple[Path, int, str, str]] = []
    for lineno, line in iter_content_lines(text):
        clean_line = _INLINE_CODE_RE.sub("", line)
        for pattern, kind in ((_MD_LINK_RE, "md"), (_WIKILINK_RE, "wiki")):
            for match in pattern.finditer(clean_line):
                target = clean_target(match.group(1), kind)
                if target and not target_resolves(root, target):
                    unresolved.append((rel, lineno, kind, target))
    return unresolved


def scan_root_file_links(
    root: Path, target_files: tuple[str, ...] = ROOT_FILES
) -> list[tuple[Path, int, str, str]]:
    """Aggregate unresolved link targets across the given root files."""
    warnings: list[tuple[Path, int, str, str]] = []
    for name in target_files:
        path = root / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        warnings.extend(scan_links(root, Path(name), text))
    return warnings


def main() -> int:
    root = repo_root()
    self_rel = Path(__file__).resolve().relative_to(root)
    exit_code = 0

    # --- Check 1: archive forward-guard (blocking) ---
    needles, archive_prefixes = discover_needles(root)
    if not needles:
        scanned = ", ".join(d.as_posix() for d in ARCHIVE_DIRS)
        print(f"OK: no archived files discovered (scanned {scanned})")
    else:
        all_violations: list[tuple[Path, int, str]] = []
        for path, rel in iter_target_files(root):
            if rel == self_rel:  # don't flag this script's own NEEDLE prose
                continue
            all_violations.extend(scan_file(path, rel, needles, archive_prefixes))
        if all_violations:
            for rel, lineno, line in all_violations:
                print(f"{rel.as_posix()}:{lineno}:{line}")
            print(f"FAIL: {len(all_violations)} archive-ref violations", file=sys.stderr)
            exit_code = 1
        else:
            print(f"OK: 0 archive-ref violations ({len(needles)} archived files auto-discovered)")

    # --- Check 2: A4 root-file link resolution (warning mode) ---
    a4_strict = os.environ.get("MJ_AGENT_A4_STRICT") == "1"
    unresolved = scan_root_file_links(root, ROOT_FILES)
    if unresolved:
        for rel, lineno, kind, target in unresolved:
            print(f"{rel.as_posix()}:{lineno}: [A4-{kind}] unresolved link target -> {target}")
        mode = "blocking" if a4_strict else "warning-mode; set MJ_AGENT_A4_STRICT=1 to block"
        label = "FAIL" if a4_strict else "WARN"
        print(
            f"{label}: {len(unresolved)} unresolved root-file link target(s) ({mode})",
            file=sys.stderr,
        )
        if a4_strict:
            exit_code = 1
    else:
        print(f"OK: A4 link resolution — 0 unresolved targets in {len(ROOT_FILES)} root files")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
