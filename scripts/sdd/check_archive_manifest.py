"""scripts/sdd/check_archive_manifest.py — Phase M0 skeleton.

Phase M0: print skeleton notice; Phase M5 实现 archive.yml 存在 + ai_visibility
字段已设置校验 — 对应 sdd/gates.md G11/G12.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase M0 skeleton — validates archive/*/archive.yml existence + "
            "ai_visibility / retention_class fields set (G11/G12). Full implementation in Phase M5."
        )
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("[skeleton] scripts/sdd/check_archive_manifest.py — Phase M0 placeholder (G11/G12)")

    archive_dir = Path("archive")
    if not archive_dir.exists():
        print("no archive/ yet (Phase M5 expected to create)")
        return 0

    if args.dry_run:
        print("[dry-run] skipping archive.yml validation; Phase M5 will fill in")
        return 0

    print("[skeleton] archive/ exists but manifest validation not implemented yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
