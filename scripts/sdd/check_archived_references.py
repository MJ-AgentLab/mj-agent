"""scripts/sdd/check_archived_references.py — G14/G15 validator (M5-PR0 gate-prep).

Per sdd/gates.md G14/G15:

> G14 | check_archived_references.py | active 文件不引用 archived 路径 | M5 blocking
> G15 | 同 G14 | — | M5 blocking

This PR (M5-PR0) wires the gate in **WARNING mode only** (no blocking flip —
that is a HITL action deferred to the M5 move PRs).

Purpose: active (non-archive) files must NOT reference ``archive/`` paths
unless permitted. Permitted =

1. the referenced archive unit's ``archive.yml`` has
   ``ai_visibility: reference`` (AI may cite it for history), OR
2. the referencing file is on a small allowlist (``CHANGELOG.md``), OR
3. the referencing line carries an explicit ``ai_visibility=reference``
   marker (line-level override).

Behavior:

- Scan active text files across docs/, capabilities/, sdd/, policies/,
  decisions/, plans/, CLAUDE.md — SKIP the ``archive/`` tree itself.
- For each literal ``archive/`` path reference, resolve the target archive
  unit + its ``archive.yml`` ``ai_visibility``; ``reference`` → OK,
  otherwise WARN (G14/G15 are WARNING in this PR).
- No-op: if ``archive/`` does not exist, no archive paths can resolve →
  print a clean no-op line and return 0 (current tree state).

Same CLI/Summary pattern as the other sdd validators; honors ``--strict``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import resolve_display_path  # noqa: E402

_SCRIPT_NAME = "check_archived_references"
_MANIFEST_NAME = "archive.yml"

# Active trees scanned for archive/ references. The archive/ tree itself is
# deliberately excluded (we don't flag the archived files referencing siblings).
_WALK_DIRS = ("docs", "capabilities", "sdd", "policies", "decisions", "plans")
_WALK_FILES = ("CLAUDE.md",)
_TEXT_SUFFIXES = {
    ".md",
    ".markdown",
    ".py",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".cfg",
    ".ini",
}

# Files always permitted to reference archive/ paths (e.g. version history).
_FILE_ALLOWLIST = {"CHANGELOG.md"}
# Line-level override marker.
_LINE_REFERENCE_MARKER = "ai_visibility=reference"

# Match a literal ``archive/<path...>`` token. Path component characters:
# letters, digits, ``_ - . [ ]`` (archive filenames carry ``[DEPRECATED]``),
# and ``/`` for nesting. Capture the longest path-like run after ``archive/``.
_ARCHIVE_REF_RE = re.compile(r"(?<![\w./-])archive/([\w./\-\[\]]+)")


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in _TEXT_SUFFIXES or path.name in _WALK_FILES


def _iter_target_files(repo_root: Path):
    """Yield (path, rel) for every scanned active text file (archive/ excluded)."""
    for dir_name in _WALK_DIRS:
        base = repo_root / dir_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if not _is_text_file(path):
                continue
            yield path, path.relative_to(repo_root)
    for file_name in _WALK_FILES:
        path = repo_root / file_name
        if path.is_file():
            yield path, path.relative_to(repo_root)


def _resolve_unit_visibility(archive_dir: Path, ref_path: str) -> str | None:
    """Resolve the ai_visibility of the archive unit covering ``ref_path``.

    Walks up from the referenced ``archive/<ref_path>`` looking for the
    nearest ``archive.yml`` (the manifest sits beside its content). Returns
    the ``ai_visibility`` string, or None if no manifest / unreadable.
    """
    # Normalize the reference into a path under archive/.
    target = (archive_dir / ref_path).resolve()
    archive_root = archive_dir.resolve()

    # Walk up from the target (or its parent if it's a file path) until we
    # leave archive/ — find the nearest archive.yml.
    probe = target if target.is_dir() else target.parent
    while True:
        try:
            probe.relative_to(archive_root)
        except ValueError:
            return None
        manifest = probe / _MANIFEST_NAME
        if manifest.exists():
            try:
                with manifest.open("r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle)
            except (yaml.YAMLError, OSError):
                return None
            if isinstance(data, dict):
                value = data.get("ai_visibility")
                return value if isinstance(value, str) else None
            return None
        if probe == archive_root:
            return None
        probe = probe.parent


def _scan_file(
    path: Path,
    rel: Path,
    archive_dir: Path,
    repo_root: Path,
) -> Summary:
    """Scan one file for archive/ references; classify each as OK or WARN."""
    summary = Summary()
    display = resolve_display_path(path, repo_root)
    file_allowlisted = rel.name in _FILE_ALLOWLIST
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return summary

    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in _ARCHIVE_REF_RE.finditer(line):
            ref_path = match.group(1)
            if file_allowlisted:
                summary.add(
                    Severity.PASS,
                    f"{display}:{lineno}: archive/{ref_path} (allowlisted file)",
                )
                continue
            if _LINE_REFERENCE_MARKER in line:
                summary.add(
                    Severity.PASS,
                    f"{display}:{lineno}: archive/{ref_path} (line ai_visibility=reference marker)",
                )
                continue
            visibility = _resolve_unit_visibility(archive_dir, ref_path)
            if visibility == "reference":
                summary.add(
                    Severity.PASS,
                    f"{display}:{lineno}: archive/{ref_path} (unit ai_visibility=reference)",
                )
            else:
                detail = "no resolvable archive.yml" if visibility is None else visibility
                summary.add(
                    Severity.WARN,
                    f"{display}:{lineno}: references archive/{ref_path} "
                    f"(ai_visibility={detail}); not permitted",
                )
    return summary


def main(argv: list[str] | None = None) -> int:
    """G14/G15 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G14/G15 archived-reference validator (active files must not cite hidden "
        "archive/ paths). M5-PR0 gate-prep; WARNING mode in CI (blocking flip "
        "deferred to M5 move PRs).",
        _MANIFEST_NAME,
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent
    archive_dir = repo_root / "archive"

    if not archive_dir.exists():
        print(f"{_SCRIPT_NAME}: no archive/ yet (no-op; no archive paths can resolve)")
        return 0

    if args.dry_run:
        files = list(_iter_target_files(repo_root))
        print(
            f"{_SCRIPT_NAME}: {len(files)} active text file(s) would be scanned "
            "for archive/ references (no validation in dry-run mode)"
        )
        return 0

    aggregate = Summary()
    for path, rel in _iter_target_files(repo_root):
        per = _scan_file(path, rel, archive_dir, repo_root)
        aggregate.merge(per)
        per.print_messages()

    print(
        f"{_SCRIPT_NAME}: "
        f"{aggregate.pass_count}P / {aggregate.warn_count}W / {aggregate.fail_count}F "
        f"(archive/ reference scan)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
