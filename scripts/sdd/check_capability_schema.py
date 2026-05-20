"""scripts/sdd/check_capability_schema.py — Phase M0 skeleton.

Phase M0: print skeleton notice; Phase M2 实现 spec.yml JSON Schema 合规校验
(含 adapter_coverage 含 tdd-bdd 校验) — 对应 sdd/gates.md G1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase M0 skeleton — validates capabilities/*/spec.yml against "
            "sdd/traceability.schema.json (G1). Full implementation in Phase M2."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run without filesystem checks; print skeleton notice.",
    )
    args = parser.parse_args(argv)

    print("[skeleton] scripts/sdd/check_capability_schema.py — Phase M0 placeholder (G1)")

    capabilities_dir = Path("capabilities")
    spec_files = (
        list(capabilities_dir.glob("*/*/spec.yml")) if capabilities_dir.exists() else []
    )
    if not spec_files:
        print("no capabilities/ yet (Phase M0 expected)")
        return 0

    if args.dry_run:
        print(
            f"[dry-run] found {len(spec_files)} spec.yml; "
            "Phase M2 will validate against sdd/traceability.schema.json"
        )
        return 0

    print(
        "[skeleton] capabilities/ contains spec.yml files but validation not implemented yet — "
        "blocked on Phase M2 sdd/templates/spec.yml.template schema lock-down."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
