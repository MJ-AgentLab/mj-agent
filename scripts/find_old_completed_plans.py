#!/usr/bin/env python3
"""Detect plans/ candidates for archived state (ADR-021 follow-up; ADR-023).

Scans ``plans/[PLAN]_*.md`` and ``plans/[INTAKE]_*.md`` for files where:

1. ``state: completed`` (per Meta v2.2 §5.11 working doc 4-state)
2. ``updated:`` is older than ``THRESHOLD_DAYS`` (default 180 = ~6 months)
3. (out of scope for MVP) Zero references elsewhere in repo

Outputs a candidate list. Does **not** actually move files or update
state; manual review + GC trigger by maintainer (Phase D follow-up).

Usage::

    python scripts/find_old_completed_plans.py [threshold_days]

Default threshold: 180 days. Custom via positional arg.

Output: candidate list to stdout. Always exits 0.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_THRESHOLD_DAYS = 180


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_frontmatter_field(text: str, field: str) -> str | None:
    """Quick frontmatter field parser (without YAML lib dep).

    Looks for ``^<field>:`` line within first 50 lines (frontmatter ends
    at second ``---`` typically within first ~30 lines).
    """
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.*)$", re.MULTILINE)
    head = "\n".join(text.splitlines()[:50])
    match = pattern.search(head)
    if not match:
        return None
    return match.group(1).strip()


def main() -> int:
    threshold_days = (
        int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_THRESHOLD_DAYS
    )
    root = repo_root()
    plans_dir = root / "plans"
    if not plans_dir.exists():
        print(f"OK: no plans/ dir at {plans_dir}")
        return 0

    threshold = datetime.now() - timedelta(days=threshold_days)
    candidates: list[tuple[str, str, int]] = []  # (filename, updated, age_days)

    for plan in plans_dir.glob("*.md"):
        try:
            text = plan.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        state = parse_frontmatter_field(text, "state")
        if state != "completed":
            continue

        updated_str = parse_frontmatter_field(text, "updated")
        if not updated_str:
            continue

        # Strip surrounding quotes and time component.
        updated_clean = updated_str.strip("'\" ").split()[0].split("T")[0]
        try:
            updated = datetime.strptime(updated_clean, "%Y-%m-%d")
        except ValueError:
            continue

        if updated < threshold:
            age_days = (datetime.now() - updated).days
            candidates.append((plan.name, updated_clean, age_days))

    if not candidates:
        print(
            f"OK: no archive candidates "
            f"(state: completed AND updated >= {threshold_days}d ago)"
        )
        return 0

    candidates.sort(key=lambda x: x[2], reverse=True)  # oldest first

    print(
        f"=== Archive candidates ({len(candidates)} file(s); "
        f"state: completed AND age >= {threshold_days}d) ==="
    )
    print()
    print(f"{'filename':<70}  {'updated':<12}  age (days)")
    print(f"{'-' * 70}  {'-' * 12}  ----------")
    for name, updated, age in candidates:
        print(f"{name:<70}  {updated:<12}  {age}")
    print()
    print(
        "Next: manually move candidates to plans/archive/ subdir; update "
        "state to 'archived'; verify zero refs (Meta v2.2 §5.11.5; ADR-023)."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
