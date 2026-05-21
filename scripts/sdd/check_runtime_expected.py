"""scripts/sdd/check_runtime_expected.py — Phase M2 skeleton + interface only.

Validates `capabilities/*/contracts/runtime.expected.yaml` (NOTE: `.yaml`
suffix per subagent C survey; other contracts use `.yml`) against actual
runtime state.

**Phase M2 scope (per blueprint §6 Phase M2 §3 + M2 §3.5)**: skeleton + function
signatures + docstring ONLY. Does NOT connect docker daemon / read docker ps
/ run any runtime probe. Phase M4 implements the full probe per blueprint §6
Phase M4 §3.

Per blueprint §6 Phase M2 §3 + ADR-031 §5 docker-container adapter. Phase M4
will lift this to actual runtime contract test (subprocess `docker compose ps`
+ healthcheck probe + log assertion).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common import (  # noqa: E402
    Severity,
    Summary,
    build_argparser,
    load_contract,
    resolve_display_path,
)


def _discover_runtime_expected(repo_root: Path, capability_arg: Path | None) -> list[Path]:
    """Discover runtime.expected.yaml (note: .yaml suffix, NOT .yml)."""
    if capability_arg is not None:
        candidate = (capability_arg / "contracts" / "runtime.expected.yaml").resolve()
        return [candidate] if candidate.exists() else []
    capabilities_dir = repo_root / "capabilities"
    if not capabilities_dir.exists():
        return []
    return sorted(capabilities_dir.glob("*/*/contracts/runtime.expected.yaml"))


def _validate_skeleton(contract_path: Path, repo_root: Path) -> Summary:
    """Phase M2 skeleton: schema-load only; no runtime probe.

    Phase M4 will replace this with actual implementation that:
    - Subprocess `docker compose ps --format json` and compare to `containers[]`.
    - Subprocess `docker inspect --format` for healthcheck status.
    - Compare network reachability against `network_reachability[]`.
    - Compare volume labels against `volumes[]`.
    """
    summary = Summary()
    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary

    containers = contract.get("containers", [])
    if not isinstance(containers, list):
        summary.add(Severity.WARN, f"{contract_path}: 'containers' field is not a list (M4 will require list)")
    elif not containers:
        summary.add(Severity.WARN, f"{contract_path}: 'containers' list is empty (M4 will require ≥1)")

    summary.add(
        Severity.WARN,
        f"{contract_path}: runtime probe deferred to Phase M4 (M2 skeleton only; per blueprint §6 Phase M4 §3)",
    )

    if summary.fail_count == 0:
        summary.add_aggregate_pass(
            n=1,
            message=f"runtime.expected.yaml structure load OK ({len(containers) if isinstance(containers, list) else 0} containers declared; M4 will runtime-verify)",
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_runtime_expected.py",
        description=(
            "Validate runtime.expected.yaml against actual runtime state. "
            "Phase M2: SKELETON + interface only (load YAML structure; emit "
            "informational WARN about M4 deferral). Phase M4 will implement "
            "actual `docker compose ps` + healthcheck probe + network reach test."
        ),
        contract_filename="runtime.expected.yaml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    if args.capability:
        contract_files = _discover_runtime_expected(repo_root, args.capability)
    else:
        contract_files = _discover_runtime_expected(repo_root, None)

    if args.dry_run:
        print(f"[dry-run] check_runtime_expected.py — Phase M2 skeleton; found {len(contract_files)} runtime.expected.yaml")
        print("[dry-run] full implementation deferred to Phase M4 (M2 §3.5 forbids docker daemon contact)")
        return 0

    if not contract_files:
        print("no runtime.expected.yaml found")
        return 0

    print(f"check_runtime_expected.py — M2 skeleton (no runtime probe); structure-loading {len(contract_files)} runtime.expected.yaml")
    total = Summary()
    for contract_path in contract_files:
        display = resolve_display_path(contract_path, repo_root)
        print(f"\n{display}")
        sub = _validate_skeleton(contract_path, repo_root)
        sub.print_messages()
        total.merge(sub)

    print("\n=== Summary ===")
    print(f"PASS: {total.pass_count} / WARN: {total.warn_count} / FAIL: {total.fail_count}")
    return total.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
