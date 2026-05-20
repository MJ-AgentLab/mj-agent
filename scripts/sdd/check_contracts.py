"""scripts/sdd/check_contracts.py — Phase M0 skeleton.

Phase M0: print skeleton notice; Phase M2-M3 实现 contracts/ 目录非空 + contract 文件格式
(含 behavior.feature 存在性校验，高风险 REQ 必填) — 对应 sdd/gates.md G3.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase M0 skeleton — validates capabilities/*/contracts/ directory "
            "non-empty + contract file format + behavior.feature for high-risk REQ (G3)."
        )
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("[skeleton] scripts/sdd/check_contracts.py — Phase M0 placeholder (G3)")

    capabilities_dir = Path("capabilities")
    contracts_dirs = (
        list(capabilities_dir.glob("*/*/contracts"))
        if capabilities_dir.exists()
        else []
    )
    if not contracts_dirs:
        print("no capabilities/ yet (Phase M0 expected)")
        return 0

    if args.dry_run:
        print(
            f"[dry-run] found {len(contracts_dirs)} contracts/ dirs; "
            "Phase M2/M3 will validate non-empty + format + behavior.feature"
        )
        return 0

    print("[skeleton] capabilities/ exists but contracts/ validation not implemented yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
