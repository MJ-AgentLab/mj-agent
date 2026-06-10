"""scripts/sdd/check_contracts.py — G3 validator (real implementation).

Replaces the Phase M0 skeleton (post-M6 completion-audit PR2;
M6-FU-GATES-TRUTH-UP). Per sdd/gates.md §1 G3 row + capabilities/CLAUDE.md
"behavior.feature 高风险必填规则":

1. `contracts/` directory exists and is non-empty per discovered capability.
2. Every `contracts/*.contract.yml` parses to a YAML mapping
   (via `_common.yaml_io.load_contract`).
3. When `spec.yml` declares ≥1 requirement with priority critical|high,
   `contracts/behavior.feature` MUST exist — same priority scope as G23's
   `_TARGET_PRIORITIES` (check_tdd_test_list.py).

Severity policy (R-N v8 R-1 dichotomy applied):
- STRUCTURAL: contracts/ missing/empty, unparseable *.contract.yml, or
  missing behavior.feature with critical|high REQs → FAIL.
- Healthy: all three checks green → 1 aggregate PASS per capability.

WARNING mode at landing (`continue-on-error: true` in ci.yml); empirical
baseline 5P/0W/0F over the 5 pilots. Blocking flip is a separate
`ci-blocking-gate-toggle` HITL action (policies/ai-agent.md §4).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import (  # noqa: E402
    discover_capabilities,
    resolve_display_path,
)
from scripts.sdd._common.yaml_io import load_contract  # noqa: E402

_SCRIPT_NAME = "check_contracts"
# Same scope as check_tdd_test_list._TARGET_PRIORITIES (G23) — critical|high
# requirements demand a behavior.feature per capabilities/CLAUDE.md rule.
_TARGET_PRIORITIES = frozenset({"critical", "high"})


def _spec_has_high_risk_req(capability_dir: Path) -> bool:
    """True if spec.yml declares ≥1 requirement with priority critical|high.

    Graceful on schema gaps (missing/odd `requirements`): G1
    (check_capability_schema) owns spec.yml schema validation; G3 only
    consumes the priority field.
    """
    spec = load_contract(capability_dir / "spec.yml")
    if spec is None:
        return False
    requirements = spec.get("requirements")
    if not isinstance(requirements, list):
        return False
    return any(
        isinstance(req, dict) and str(req.get("priority", "")).lower() in _TARGET_PRIORITIES
        for req in requirements
    )


def _validate_capability(capability_dir: Path, repo_root: Path) -> Summary:
    """Validate G3 for one capability (contracts/ non-empty + parse + feature)."""
    summary = Summary()
    display = resolve_display_path(capability_dir, repo_root)
    contracts_dir = capability_dir / "contracts"

    if not contracts_dir.is_dir():
        summary.add(Severity.FAIL, f"{display}: contracts/ directory missing")
        return summary

    contract_files = sorted(p for p in contracts_dir.iterdir() if p.is_file())
    if not contract_files:
        summary.add(Severity.FAIL, f"{display}: contracts/ directory is empty")
        return summary

    yml_files = [p for p in contract_files if p.name.endswith(".contract.yml")]
    for yml_path in yml_files:
        if load_contract(yml_path) is None:
            summary.add(
                Severity.FAIL,
                f"{display}: contracts/{yml_path.name} YAML parse error or non-mapping root",
            )

    feature_path = contracts_dir / "behavior.feature"
    needs_feature = _spec_has_high_risk_req(capability_dir)
    if needs_feature and not feature_path.exists():
        summary.add(
            Severity.FAIL,
            f"{display}: spec.yml has critical|high REQ but contracts/behavior.feature "
            "missing (capabilities/CLAUDE.md 高风险必填规则)",
        )

    if summary.fail_count == 0:
        feature_note = (
            "behavior.feature present (critical|high REQs)"
            if needs_feature
            else "behavior.feature not required (no critical|high REQ)"
        )
        summary.add(
            Severity.PASS,
            f"{display}: contracts/ non-empty ({len(contract_files)} files; "
            f"{len(yml_files)} *.contract.yml parse OK); {feature_note}",
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    """G3 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G3 contracts validator (contracts/ non-empty + *.contract.yml parse + "
        "behavior.feature for critical|high REQs; real impl per completion-audit PR2)",
        "contracts/",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent
    capabilities = discover_capabilities(repo_root, args.capability)

    if not capabilities:
        print(f"{_SCRIPT_NAME}: no capabilities discovered")
        return 0

    if args.dry_run:
        print(
            f"{_SCRIPT_NAME}: {len(capabilities)} capability(ies) discovered "
            "(no validation in dry-run mode)"
        )
        return 0

    aggregate = Summary()
    for cap_dir in capabilities:
        per_cap = _validate_capability(cap_dir, repo_root)
        aggregate.merge(per_cap)
        per_cap.print_messages()

    print(
        f"{_SCRIPT_NAME}: "
        f"{aggregate.pass_count}P / {aggregate.warn_count}W / {aggregate.fail_count}F "
        f"(over {len(capabilities)} capabilities; contracts non-empty + parse + "
        "behavior.feature critical|high rule)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
