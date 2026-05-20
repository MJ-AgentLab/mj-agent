"""scripts/sdd/generate_index.py — Phase M0 skeleton.

Phase M0: print skeleton notice; Phase M1 起实现 capabilities/INDEX.md 自动生成
(id / name / lifecycle_state / archive_state / last_verified / adapter_coverage)
— 对应 sdd/gates.md G9.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase M0 skeleton — auto-generates capabilities/INDEX.md from each "
            "capability's spec.yml (G9). Full implementation in Phase M1."
        )
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("[skeleton] scripts/sdd/generate_index.py — Phase M0 placeholder (G9)")

    capabilities_dir = Path("capabilities")
    spec_files = (
        list(capabilities_dir.glob("*/*/spec.yml")) if capabilities_dir.exists() else []
    )
    if not spec_files:
        print("no capabilities/ yet (Phase M0 expected; INDEX.md is the placeholder header)")
        return 0

    if args.dry_run:
        print(
            f"[dry-run] would walk {len(spec_files)} spec.yml files and emit Markdown table; "
            "Phase M1 will fill in"
        )
        return 0

    print("[skeleton] capabilities/ exists but INDEX generation not implemented yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
