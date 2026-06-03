"""scripts/sdd/check_archive_manifest.py — G11/G12 validator (M5-PR0 gate-prep).

Replaces the Phase M0 skeleton with a REAL validator per sdd/gates.md
G11/G12:

> G11 | check_archive_manifest.py | archive.yml + ai_visibility 必填 | M5 blocking
> G12 | check_archive_manifest.py | 同上 | M5 blocking

This PR (M5-PR0) wires the gate in **WARNING mode only** (no blocking flip —
that is a HITL action deferred to the M5 move PRs). The validator must:

1. No-op cleanly on the CURRENT tree (no top-level ``archive/`` dir exists
   yet) — return 0 with a clean "no archive/ yet" line.
2. Be correct once ``archive/`` populates — proven by synthetic-fixture tests.

What this validator does (when ``archive/`` exists):

- Discover "archive units" = every leaf-ish directory under ``archive/``
  that carries archived content. Pragmatic rule:
  - every ``archive.yml`` found under ``archive/**`` is an archive unit;
  - additionally, any subdir under ``archive/`` that contains ``.md`` /
    content files but has NO sibling ``archive.yml`` is flagged as a
    missing-manifest unit (FAIL).
- For each ``archive.yml``: validate the 5 required fields are present +
  enum values for ``ai_visibility`` / ``retention_class`` / ``original_state``
  (manual PyYAML validation — NO jsonschema dependency).
  - missing required field → FAIL
  - bad enum value → FAIL
  - missing ``archive.yml`` for a content dir → FAIL

Required fields + enums mirror ``sdd/archive.schema.json``:
- required: ``archived_at`` / ``reason`` / ``original_path`` /
  ``ai_visibility`` / ``retention_class``
- ``ai_visibility`` ∈ {hidden, reference}
- ``retention_class`` ∈ {permanent, 5-year, 1-year}
- ``original_state`` ∈ {draft, active, deprecated, frozen} (optional field;
  validated only when present)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import resolve_display_path  # noqa: E402

_SCRIPT_NAME = "check_archive_manifest"
_MANIFEST_NAME = "archive.yml"

# Mirror sdd/archive.schema.json (manual validation — no jsonschema dep).
_REQUIRED_FIELDS = (
    "archived_at",
    "reason",
    "original_path",
    "ai_visibility",
    "retention_class",
)
_AI_VISIBILITY_ENUM = {"hidden", "reference"}
_RETENTION_CLASS_ENUM = {"permanent", "5-year", "1-year"}
_ORIGINAL_STATE_ENUM = {"draft", "active", "deprecated", "frozen"}

# Content-file suffixes that, when present in an archive subdir lacking a
# sibling archive.yml, indicate a missing manifest (FAIL).
_CONTENT_SUFFIXES = {".md", ".markdown"}
# Never treated as "content" requiring a manifest.
_IGNORE_NAMES = {".gitkeep", "INDEX.md"}


def _validate_manifest(manifest_path: Path, repo_root: Path) -> Summary:
    """Validate one ``archive.yml`` against the 5 required fields + enums."""
    summary = Summary()
    display = resolve_display_path(manifest_path, repo_root)

    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (yaml.YAMLError, OSError) as exc:
        summary.add(Severity.FAIL, f"{display}: archive.yml parse failed ({exc})")
        return summary

    if not isinstance(data, dict):
        summary.add(
            Severity.FAIL,
            f"{display}: archive.yml root is {type(data).__name__}, not a mapping",
        )
        return summary

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        summary.add(
            Severity.FAIL,
            f"{display}: missing required field(s): {', '.join(missing)}",
        )

    ai_visibility = data.get("ai_visibility")
    if "ai_visibility" in data and ai_visibility not in _AI_VISIBILITY_ENUM:
        summary.add(
            Severity.FAIL,
            f"{display}: ai_visibility '{ai_visibility}' not in "
            f"{sorted(_AI_VISIBILITY_ENUM)}",
        )

    retention_class = data.get("retention_class")
    if "retention_class" in data and retention_class not in _RETENTION_CLASS_ENUM:
        summary.add(
            Severity.FAIL,
            f"{display}: retention_class '{retention_class}' not in "
            f"{sorted(_RETENTION_CLASS_ENUM)}",
        )

    original_state = data.get("original_state")
    if "original_state" in data and original_state not in _ORIGINAL_STATE_ENUM:
        summary.add(
            Severity.FAIL,
            f"{display}: original_state '{original_state}' not in "
            f"{sorted(_ORIGINAL_STATE_ENUM)}",
        )

    if summary.fail_count == 0:
        summary.add(Severity.PASS, f"{display}: 5 required fields present + enums valid")
    return summary


def _is_content_file(path: Path) -> bool:
    """True iff ``path`` is a content file that should be covered by a manifest."""
    if not path.is_file():
        return False
    if path.name in _IGNORE_NAMES or path.name == _MANIFEST_NAME:
        return False
    return path.suffix.lower() in _CONTENT_SUFFIXES


def _find_missing_manifest_dirs(archive_dir: Path, repo_root: Path) -> Summary:
    """Flag archive subdirs holding content files but NO sibling archive.yml.

    A directory is a missing-manifest unit when it (directly) contains a
    content file and has no ``archive.yml`` sibling in the same directory.
    Directories that are themselves covered by a parent ``archive.yml``
    are still flagged: an archive unit's manifest must sit beside its
    content (per the archive ceremony's leaf-dir rule).
    """
    summary = Summary()
    seen_dirs: set[Path] = set()
    for content_path in sorted(archive_dir.rglob("*")):
        if not _is_content_file(content_path):
            continue
        parent = content_path.parent
        if parent in seen_dirs:
            continue
        seen_dirs.add(parent)
        if (parent / _MANIFEST_NAME).exists():
            continue
        display = resolve_display_path(parent, repo_root)
        summary.add(
            Severity.FAIL,
            f"{display}/: contains content file(s) but no sibling "
            f"{_MANIFEST_NAME} (missing manifest)",
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    """G11/G12 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G11/G12 archive manifest validator (archive.yml required fields + enums). "
        "M5-PR0 gate-prep; WARNING mode in CI (blocking flip deferred to M5 move PRs).",
        _MANIFEST_NAME,
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent
    archive_dir = repo_root / "archive"

    if not archive_dir.exists():
        print(f"{_SCRIPT_NAME}: no archive/ yet (no-op; born in M5 move PRs)")
        return 0

    manifests = sorted(archive_dir.rglob(_MANIFEST_NAME))

    if args.dry_run:
        print(
            f"{_SCRIPT_NAME}: {len(manifests)} archive.yml discovered under "
            f"{resolve_display_path(archive_dir, repo_root)} (no validation in dry-run mode)"
        )
        return 0

    aggregate = Summary()
    for manifest_path in manifests:
        per = _validate_manifest(manifest_path, repo_root)
        aggregate.merge(per)
        per.print_messages()

    missing = _find_missing_manifest_dirs(archive_dir, repo_root)
    aggregate.merge(missing)
    missing.print_messages()

    print(
        f"{_SCRIPT_NAME}: "
        f"{aggregate.pass_count}P / {aggregate.warn_count}W / {aggregate.fail_count}F "
        f"(over {len(manifests)} archive.yml manifest(s))"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
