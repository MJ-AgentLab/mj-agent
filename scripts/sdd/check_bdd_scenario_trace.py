"""scripts/sdd/check_bdd_scenario_trace.py — G19 validator (Stage D D-2).

Phase M4 BLOCKING gate (per sdd/gates.md L58 specific row authoritative + L96
Phase M4 schedule; L96 omits G19 row but L58 specific row most-specific-SoT-wins
per D-2 §0 #D2-A1):

> G19 | check_bdd_scenario_trace.py | 关键 scenario 绑定 REQ/CTR | M3 warning / M4 blocking

Per L51 docker-bdd-scenario-check (same script via ``--scope`` flag per D-2 §0
#D2-A3 design insight; V5 sub-flags M3-FU-V5-SUBFLAGS precedent):

> docker-bdd-scenario-check | check_bdd_scenario_trace.py（Docker 子集）|
> docker behavior.feature | M3 warning / M4 blocking

What this validator does:

1. Discover all capabilities under ``capabilities/*/*/`` (via
   ``_common.discovery.discover_capabilities``).
2. Filter per ``--scope`` flag (full=all 5 pilots / docker=docker-compose only).
3. Per capability: parse ``contracts/behavior.feature`` → list[Scenario]
   (via ``_common.bdd_helpers.parse_feature_file``).
4. Per scenario: extract tags + cross-ref ``trace.yml`` bdd 层 via
   ``trace_req_ctr`` helper (returns binding FACTS).
5. Apply R-N v8 R-1 Decision Matrix policy → PASS / WARN / FAIL per scenario.

R-N v8 R-1 Decision Matrix (supersedes R-N v7 R-1; Stage D D-2 Step 5
escalation lock-in):

- TAG layer (validator concern): missing ``@REQ-NNN`` OR ``@CTR-<slug>`` tag
  on scenario → **FAIL** (.feature schema concern; gates.md L58 真义).
- TRACE layer (maintenance concern): tags present + trace.yml bdd 层 mapping
  gap (REQ entry absent OR scenario name not in REQ entry's scenarios list)
  → **WARN** (trace.yml curation gap; M-FU maintenance task).
- Healthy: tags present + trace mapping found → **PASS**.

Graceful trace.yml handling preserved (R-N v7 R-1 carryover):

- ``trace.yml`` missing OR YAML invalid → capability-level WARN (R-N v7 R-1)
  + per-scenario PASS at tag layer (TRACE layer dormant; tag-only check).
- ``behavior.feature`` missing → SKIP (capability not yet contracted state).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.bdd_helpers import (  # noqa: E402
    FeatureParseError,
    extract_tags,
    load_trace_yml,
    parse_feature_file,
    trace_req_ctr,
)
from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import (  # noqa: E402
    discover_capabilities,
    resolve_display_path,
)

_SCRIPT_NAME = "check_bdd_scenario_trace"
_DOCKER_CAPABILITY_NAME = "docker-compose"


def _validate_capability(capability_dir: Path, repo_root: Path) -> Summary:
    """Validate G19 scenario trace for one capability (R-N v8 R-1 policy).

    Per R-N v8 R-1 Decision Matrix (supersedes R-N v7 R-1):

    - TAG layer (validator concern): missing @REQ or @CTR → **FAIL**.
    - TRACE layer (maintenance concern): tags present + trace.yml bdd 层
      mapping gap → **WARN**.
    - Healthy: tags present + trace mapping found → **PASS**.

    SKIP: behavior.feature missing (capability not yet contracted state).
    Capability-level WARN: feature parse error OR trace.yml missing/invalid
    (R-N v7 R-1 graceful carryover).
    """
    summary = Summary()
    feature_path = capability_dir / "contracts" / "behavior.feature"
    display = resolve_display_path(capability_dir, repo_root)

    if not feature_path.exists():
        return summary  # SKIP: capability has no behavior.feature

    try:
        feature = parse_feature_file(feature_path)
    except FeatureParseError as exc:
        summary.add(Severity.WARN, f"{display}: feature parse error ({exc})")
        return summary

    trace_data = load_trace_yml(capability_dir)
    trace_missing = trace_data is None

    if trace_missing:
        summary.add(
            Severity.WARN,
            f"{display}: trace.yml missing OR invalid "
            "(G19 cannot verify bdd 层 binding; per R-N v7 R-1 graceful)",
        )
        trace_data_for_check: dict = {"links": []}
    else:
        trace_data_for_check = trace_data

    for scenario in feature.scenarios:
        tags = extract_tags(scenario)
        result = trace_req_ctr(scenario, trace_data_for_check)

        # TAG layer (R-N v8 R-1 row 1; FAIL always — even when trace_missing).
        if not result.has_req_tag:
            summary.add(
                Severity.FAIL,
                f"{display}: scenario '{scenario.name}' missing @REQ-NNN tag binding",
            )
            continue
        if not result.has_ctr_tag:
            summary.add(
                Severity.FAIL,
                f"{display}: scenario '{scenario.name}' missing @CTR-<slug> tag binding",
            )
            continue

        # TRACE layer (R-N v8 R-1 rows 2-3; WARN on trace.yml curation gap).
        if trace_missing:
            summary.add(
                Severity.PASS,
                f"{display}: scenario '{scenario.name}' REQ+CTR tags bound "
                "(trace.yml missing; tag-only check)",
            )
        elif not result.req_bound_in_trace:
            summary.add(
                Severity.WARN,
                f"{display}: scenario '{scenario.name}' has @REQ tags {tags.req} "
                "but not bound in trace.yml bdd 层 "
                "(R-N v8 R-1 trace curation gap; M-FU maintenance)",
            )
        else:
            summary.add(
                Severity.PASS,
                f"{display}: scenario '{scenario.name}' REQ+CTR tags bound + trace cross-ref OK",
            )

    return summary


def _filter_by_scope(capabilities: list[Path], scope: str) -> list[Path]:
    """Filter capabilities per ``--scope`` flag.

    - full (default): all discovered capabilities (G19 main scope)
    - docker: only docker-compose capability (L51 docker-bdd-scenario-check subset)
    """
    if scope == "full":
        return capabilities
    if scope == "docker":
        return [cap for cap in capabilities if cap.name == _DOCKER_CAPABILITY_NAME]
    raise ValueError(f"unknown --scope value: {scope}")


def main(argv: list[str] | None = None) -> int:
    """G19 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G19 BDD scenario trace validator (per gates.md L58; --scope full|docker per L51)",
        "behavior.feature",
    )
    parser.add_argument(
        "--scope",
        choices=["full", "docker"],
        default="full",
        help="full (all pilots; G19) OR docker (L51 docker-bdd-scenario-check subset)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent
    all_caps = discover_capabilities(repo_root, args.capability)
    capabilities = _filter_by_scope(all_caps, args.scope)

    if not capabilities:
        print(f"{_SCRIPT_NAME}: no capabilities discovered (scope={args.scope})")
        return 0

    if args.dry_run:
        print(
            f"{_SCRIPT_NAME}: {len(capabilities)} capability(ies) discovered "
            f"(scope={args.scope}; no validation in dry-run mode)"
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
        f"(scope={args.scope}; over {len(capabilities)} capabilities)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
