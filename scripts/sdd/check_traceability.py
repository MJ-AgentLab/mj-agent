"""scripts/sdd/check_traceability.py — Phase M0 skeleton.

Phase M0: print skeleton notice; Phase M2-M3 实现 trace.yml schema v1.2 合规校验
(REQ -> BDD -> CONTRACT -> TEST -> TASK -> PR -> EVIDENCE) — 对应 sdd/gates.md G2/G5.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase M0 skeleton — validates capabilities/*/trace.yml against "
            "sdd/traceability.schema.json (G2/G5; schema v1.2 含 BDD 层)."
        )
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("[skeleton] scripts/sdd/check_traceability.py — Phase M0 placeholder (G2/G5)")

    capabilities_dir = Path("capabilities")
    trace_files = (
        list(capabilities_dir.glob("*/*/trace.yml")) if capabilities_dir.exists() else []
    )
    if not trace_files:
        print("no capabilities/ yet (Phase M0 expected)")
        return 0

    if args.dry_run:
        print(
            f"[dry-run] found {len(trace_files)} trace.yml; "
            "Phase M2/M3 will validate REQ->BDD->CONTRACT->TEST chain"
        )
        return 0

    print("[skeleton] capabilities/ exists but validation not implemented yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
