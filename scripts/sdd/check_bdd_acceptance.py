"""scripts/sdd/check_bdd_acceptance.py — G21 validator (Stage D D-3).

Phase M4 WARNING gate (per sdd/gates.md L60 + L96 "G21/G22 启用" mode-unqualified
→ WARNING per outline §3 v2 + Phase M3 L95 "G19/G20 warning" precedent):

> G21 | check_bdd_acceptance.py | 关键验收场景通过率 | M4

Authoritative scope spec (sdd/adapters/bdd-tdd.md L161):

> @risk:high / @risk:critical scenario 必含 pass_rate: 1.0 或 justification

R-N v9 R-9-1 filter scope: scenarios with ``@risk:critical`` OR ``@risk:high``
tag (15 scenarios across 4 pilots per §0 #3 inventory; mcp-server-governance
excluded medium-only).

R-N v9 R-9-2 4-layer policy (Stage D D-3 MVP):

- (a) Risk filter precondition: SKIP scenarios not @risk:critical|high
- (b) TAG layer (R-N v8 R-1 inherit): missing @REQ or @CTR → **FAIL**
- (c) TRACE layer (R-N v8 R-1 inherit): trace.yml bdd 层 mapping gap → **WARN**
- (d) EVIDENCE layer (pass_rate strict): **DEFERRED** to M-FU#4 Stage E α'

Graceful trace.yml handling preserved (R-N v7 R-1 carryover):

- ``trace.yml`` missing OR YAML invalid → capability-level WARN + per-scenario
  PASS at tag layer (TRACE layer dormant; tag-only check).
- ``behavior.feature`` missing → SKIP (capability not yet contracted state).
- No @risk:critical|high scenarios in capability → SKIP whole capability
  (e.g. mcp-server-governance medium-only per §0 #3).

bdd_helpers FULL 5-func reuse (R-N v2 R-4 first bundle decision validation;
Section 5 stability commitment 守 — NO extension): parse_feature_file +
extract_tags + load_trace_yml + trace_req_ctr + FeatureParseError.

M-FU registry (Action-N batch propagate post-Stage-E):

- M-FU#4 ``M4-FU-G21-EVIDENCE-PASS-RATE-STRICT``: layer (d) tightening before
  G21 BLOCKING flip; add ``load_bdd_evidence`` helper + evidence/*.md
  pass_rate field check + justification fallback semantic.
- M-FU#5 ``M4-FU-G21-RISK-CRITICAL-HIGH-FILTER-SCOPE-CLARIFY``: spec wording
  ambiguity between gates.md "关键 (key)" vs bdd-tdd.md "critical|high"
  explicit clarification before BLOCKING flip.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.bdd_helpers import (  # noqa: E402
    FeatureParseError,
    Scenario,
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

_SCRIPT_NAME = "check_bdd_acceptance"
_TARGET_RISK_LEVELS = frozenset({"critical", "high"})


def _filter_by_risk(scenarios: list[Scenario]) -> list[Scenario]:
    """Filter scenarios with @risk:critical OR @risk:high (R-N v9 R-9-1)."""
    return [
        s for s in scenarios
        if any(level in _TARGET_RISK_LEVELS for level in extract_tags(s).risk)
    ]


def _validate_capability(capability_dir: Path, repo_root: Path) -> Summary:
    """Validate G21 acceptance for one capability (R-N v9 R-9-2 4-layer policy).

    SKIP conditions:
    - behavior.feature missing (capability not yet contracted state)
    - no @risk:critical|high scenarios in capability (layer a precondition)

    Capability-level WARN: feature parse error OR trace.yml missing/invalid
    (R-N v7 R-1 graceful carryover).
    """
    summary = Summary()
    feature_path = capability_dir / "contracts" / "behavior.feature"
    display = resolve_display_path(capability_dir, repo_root)

    if not feature_path.exists():
        return summary

    try:
        feature = parse_feature_file(feature_path)
    except FeatureParseError as exc:
        summary.add(Severity.WARN, f"{display}: feature parse error ({exc})")
        return summary

    # Layer (a): risk filter precondition (R-N v9 R-9-1)
    filtered = _filter_by_risk(feature.scenarios)
    if not filtered:
        return summary

    trace_data = load_trace_yml(capability_dir)
    trace_missing = trace_data is None

    if trace_missing:
        summary.add(
            Severity.WARN,
            f"{display}: trace.yml missing OR invalid "
            "(G21 cannot verify bdd 层 binding; R-N v7 R-1 graceful)",
        )
        trace_data_for_check: dict = {"links": []}
    else:
        trace_data_for_check = trace_data

    for scenario in filtered:
        tags = extract_tags(scenario)
        risk_label = ",".join(tags.risk)
        result = trace_req_ctr(scenario, trace_data_for_check)

        # Layer (b): TAG (R-N v8 R-1 TAG inherit; FAIL always)
        if not result.has_req_tag:
            summary.add(
                Severity.FAIL,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                "missing @REQ-NNN tag binding",
            )
            continue
        if not result.has_ctr_tag:
            summary.add(
                Severity.FAIL,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                "missing @CTR-<slug> tag binding",
            )
            continue

        # Layer (c): TRACE (R-N v8 R-1 TRACE inherit; WARN on mapping gap)
        if trace_missing:
            summary.add(
                Severity.PASS,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                "REQ+CTR tags bound (trace.yml missing; tag-only check)",
            )
        elif not result.req_bound_in_trace:
            summary.add(
                Severity.WARN,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                f"has @REQ tags {tags.req} but not bound in trace.yml bdd 层 "
                "(R-N v8 R-1 trace curation gap; M-FU#1 maintenance)",
            )
        else:
            summary.add(
                Severity.PASS,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                "REQ+CTR tags bound + trace cross-ref OK",
            )

        # Layer (d): EVIDENCE pass_rate DEFERRED per M-FU#4 Stage E α'

    return summary


def main(argv: list[str] | None = None) -> int:
    """G21 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G21 BDD acceptance validator (per gates.md L60 + L96; "
        "@risk:critical|high subset per bdd-tdd.md L161 + R-N v9 R-9-1)",
        "behavior.feature",
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
        f"(over {len(capabilities)} capabilities; "
        "@risk:critical|high subset per R-N v9 R-9-1)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
