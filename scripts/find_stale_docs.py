#!/usr/bin/env python3
"""mj-system v5.2 §7.1.1 派生：path-level stale doc reference detection.

Detects backtick-quoted file paths that were renamed / moved / deleted
in the current PR's git diff. For each rename / delete, greps:

- ``docs/**/*.md``
- ``plans/**/*.md``
- ``CLAUDE.md``, ``CHANGELOG.md``, ``README.md``

for backtick-bounded references to the old path (e.g. ``\\`docs/old/file.md\\```).
Reports remaining references as warnings. **Always exits 0 (warning mode)**;
4-week observation window planned before upgrading to blocking
(ADR-023 §Decision).

Usage::

    python scripts/find_stale_docs.py [base_ref [head_ref]]

- ``base_ref`` defaults to ``origin/develop``
- ``head_ref`` defaults to ``HEAD``

Output: human-readable findings to stdout; JSON summary to stderr
(parseable by CI annotations).

Standard library only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

WALK_DIRS = ("docs", "plans")
WALK_FILES = ("CLAUDE.md", "CHANGELOG.md", "README.md")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def git_diff_renames(base_ref: str, head_ref: str) -> list[tuple[str, str | None]]:
    """Return list of (old_path, new_path or None for delete)."""
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--find-renames",
                f"{base_ref}...{head_ref}",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo_root()),
            check=False,
        )
    except (OSError, FileNotFoundError):
        return []
    renames: list[tuple[str, str | None]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            # rename: status, old, new
            renames.append((parts[1], parts[2]))
        elif status == "D" and len(parts) >= 2:
            # delete: status, old
            renames.append((parts[1], None))
    return renames


def iter_target_files(root: Path) -> Iterable[Path]:
    for d in WALK_DIRS:
        base = root / d
        if base.exists():
            for p in base.rglob("*.md"):
                yield p
    for f in WALK_FILES:
        p = root / f
        if p.is_file():
            yield p


def grep_backtick_refs(target: Path, old_path: str) -> list[tuple[int, str]]:
    """Find lines containing backtick-bounded references to old_path."""
    pattern = f"`{old_path}`"
    out: list[tuple[int, str]] = []
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for lineno, line in enumerate(text.splitlines(), start=1):
        if pattern in line:
            out.append((lineno, line.rstrip()))
    return out


def main() -> int:
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/develop"
    head_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    root = repo_root()
    renames = git_diff_renames(base_ref, head_ref)
    if not renames:
        print(f"OK: no rename/move/delete in {base_ref}...{head_ref}")
        return 0

    findings: list[dict[str, object]] = []
    for old, new in renames:
        for target in iter_target_files(root):
            for lineno, line in grep_backtick_refs(target, old):
                findings.append(
                    {
                        "old_path": old,
                        "new_path": new,
                        "ref_file": target.relative_to(root).as_posix(),
                        "line": lineno,
                        "text": line,
                    }
                )

    print(
        f"=== Stale ref scan: {len(renames)} rename/delete(s); "
        f"{len(findings)} stale backtick-quoted ref(s) ==="
    )
    print()
    for f in findings:
        action = f"renamed to `{f['new_path']}`" if f["new_path"] else "deleted"
        print(f"{f['ref_file']}:{f['line']}: `{f['old_path']}` ({action})")
        print(f"    {f['text']}")
        print()

    if findings:
        # GitHub Actions warning annotation (rendered in PR Files / step summary)
        print(
            f"::warning::find_stale_docs.py: {len(findings)} stale backtick "
            "references found (warning mode; not blocking)"
        )

    # JSON summary to stderr for CI consumers.
    summary = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "renames": [
            {"old": old, "new": new} for old, new in renames
        ],
        "findings": findings,
    }
    sys.stderr.write(json.dumps(summary, ensure_ascii=False) + "\n")

    # Always exit 0: warning mode. Upgrade to blocking after 4-week
    # observation period evaluates false-positive rate (ADR-023 §Decision).
    return 0


if __name__ == "__main__":
    sys.exit(main())
