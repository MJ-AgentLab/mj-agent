"""scripts/sdd/check_capability_evidence_required.py — G8 validator (Stage D D-1).

Phase M4 BLOCKING gate (per sdd/gates.md L30 + L96):

> G8 | (evidence required) | capability state: active 后 evidence/ 至少
> 1 文件 | M4 blocking

G8 trigger semantic (per most-specific-SoT sdd/lifecycle.md L69):

> verifying → active | evidence 写入 + trace.yml 链路完整 |
> G8 evidence required (Phase M4 起 blocking)

The L69 state-machine entry pins the trigger field to `lifecycle_state`
(the 9-state enum's ``active`` state), NOT ``archive_state`` (5-state).
Capabilities with ``lifecycle_state != active`` SKIP entirely — the
validator stays dormant until the capability matures (per
M3-FU-G1G2G9-IMPL note: "M4 will formalise vocabulary"; full pilot
state evolution tracked by M4-FU-CAPABILITY-STATE-EVOLVE-PILOTS).

What this validator does:

1. Discover all capabilities under ``capabilities/*/*/`` (via
   ``_common.discovery.discover_capabilities`` additive helper).
2. Read each ``spec.yml`` YAML frontmatter.
3. If ``lifecycle_state == "active"`` → require ``evidence/`` subdir to
   contain at least one file that is NOT named ``.gitkeep``.
4. PASS / FAIL per-capability; SKIP capabilities that have not reached
   ``active`` state yet.

Phase M4 baseline (post-D-1 land; all 5 pilots are
``lifecycle_state: drafting``): expected ``0P / 0W / 0F / 5SKIP``.
Enforcement activates as capabilities transition through the lifecycle
state machine.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import (  # noqa: E402
    discover_capabilities,
    resolve_display_path,
)

_SCRIPT_NAME = "check_capability_evidence_required"
_TARGET_STATE = "active"
_GITKEEP = ".gitkeep"


def _has_evidence(capability_dir: Path) -> bool:
    """Return True iff ``capability_dir/evidence/`` contains ≥1 non-.gitkeep file."""
    evidence_dir = capability_dir / "evidence"
    if not evidence_dir.exists():
        return False
    for path in evidence_dir.rglob("*"):
        if path.is_file() and path.name != _GITKEEP:
            return True
    return False


def _validate_capability(capability_dir: Path, repo_root: Path) -> Summary:
    """Validate G8 evidence-required for one capability.

    SKIP path: ``lifecycle_state != active`` → no count.
    PASS path: ``lifecycle_state == active`` + evidence/ ≥1 non-.gitkeep.
    FAIL path: ``lifecycle_state == active`` + evidence/ empty.
    """
    summary = Summary()
    spec_path = capability_dir / "spec.yml"
    display = resolve_display_path(capability_dir, repo_root)

    if not spec_path.exists():
        summary.add(Severity.WARN, f"{display}: spec.yml missing (G8 cannot evaluate)")
        return summary

    try:
        with spec_path.open("r", encoding="utf-8") as handle:
            spec_data = yaml.safe_load(handle)
    except (yaml.YAMLError, OSError) as exc:
        summary.add(Severity.WARN, f"{display}: spec.yml parse failed ({exc})")
        return summary

    if not isinstance(spec_data, dict):
        summary.add(
            Severity.WARN,
            f"{display}: spec.yml root is {type(spec_data).__name__}, not a mapping",
        )
        return summary

    lifecycle_state = spec_data.get("lifecycle_state")
    if lifecycle_state != _TARGET_STATE:
        # SKIP: validator dormant until capability reaches lifecycle_state: active
        return summary

    if _has_evidence(capability_dir):
        summary.add(
            Severity.PASS,
            f"{display}: lifecycle_state=active + evidence/ ≥1 non-.gitkeep file",
        )
    else:
        summary.add(
            Severity.FAIL,
            f"{display}: lifecycle_state=active but evidence/ is empty (only .gitkeep)",
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    """G8 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G8 evidence-required validator (lifecycle_state: active → evidence/ ≥1 file)",
        "spec.yml",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent
    capabilities = discover_capabilities(repo_root, args.capability)

    if not capabilities:
        print(f"{_SCRIPT_NAME}: no capabilities discovered under {repo_root}/capabilities")
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

    skip_count = len(capabilities) - (
        aggregate.pass_count + aggregate.warn_count + aggregate.fail_count
    )
    print(
        f"{_SCRIPT_NAME}: "
        f"{aggregate.pass_count}P / {aggregate.warn_count}W / "
        f"{aggregate.fail_count}F / {skip_count}SKIP "
        f"(over {len(capabilities)} capabilities)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
