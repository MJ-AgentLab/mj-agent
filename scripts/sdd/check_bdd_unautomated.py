"""scripts/sdd/check_bdd_unautomated.py — G22 validator (Stage D D-4).

Phase M4 WARNING gate (R-N v10 R-10-1 phased rollout per outline §4 R-1'';
NOT spec deviation per R-N v10 R-10-8 documented framing):

> sdd/gates.md L61:
> G22 | check_bdd_unautomated.py | 未自动化 scenario 在 runbook 说明原因 | M4

> sdd/adapters/bdd-tdd.md L120-122 (G22 authoritative strict spec):
> 任何 @risk:critical / @risk:high 未自动化 scenario → runbook.md 必含
> justification 段落（原因 / 替代验证手段 / 升级触发条件 / 预计时间）；
> M3 warning / M4 blocking.

R-N v10 R-10-8 spec phased-rollout interpretation: L121 "M4 blocking" =
BLOCKING by M4 END (Stage E α' flip per outline §4 R-1''); Stage D
WARNING is designed phased step; NOT spec deviation. M-FU#6 tracks the
Stage E α' BLOCKING flip; M-FU#7 tracks runbook.md curation across all
5 pilots (currently 0/5 have justification — honest WARN signal).

R-N v10 R-10-2 predicate (2-layer policy):
- (a) Filter: trace.yml ``automation_status: unautomated`` × @risk:critical|high
- (b) Check: runbook.md justification 4-field MVP keyword presence
  (原因 / 替代验证手段 / 升级触发条件 / 预计时间); WARN-only on missing.

R-N v10 R-10-6 FAIL/WARN/PASS policy (adapted from R-N v8 R-1 dichotomy):
- STRUCTURAL: filtered scenario but missing automation_status field → FAIL
  (expected NOT triggered per §0 #3 — 5/5 pilots have field universally;
  remains defensive backstop)
- CURATION: unautomated + runbook missing/partial justification → WARN
- Healthy: unautomated + 4-field justification full → PASS

bdd_helpers 4-of-5 SUBSET reuse (R-N v10 R-10-5; Section 5 stability 守 —
NO extension): parse_feature_file + Feature.scenarios (via attribute,
not separate extract_scenarios) + extract_tags + load_trace_yml +
FeatureParseError. NO trace_req_ctr (G22 trace.yml structure differs;
validator-local automation_status traversal).

M-FU registry (Action-N batch propagate post-Stage-E):

- M-FU#6 NEW ``M4-FU-G22-MODE-WARN-TO-BLOCKING-FLIP``: Stage E α' BLOCKING
  flip + WARN-to-FAIL reclassification per L121 end-state.
- M-FU#7 NEW ``M4-FU-RUNBOOK-JUSTIFICATION-CURATE-ALL-PILOTS``: 15
  critical|high × unautomated scenarios × 5 pilots × 0 justifications;
  capability content maintenance scope; defer Action-N batch post-Stage-E.
- M-FU PHASE-MAP-RECONCILE (existing) AMEND: G22 L96 "启用" vs L121
  "M4 blocking" added as concrete example of phase-map reconciliation.
- M-FU#3 (existing) AMEND: Complex Solo data point #2 (n=2 with D-3).
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
)
from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import (  # noqa: E402
    discover_capabilities,
    resolve_display_path,
)

_SCRIPT_NAME = "check_bdd_unautomated"
_TARGET_RISK_LEVELS = frozenset({"critical", "high"})
_JUSTIFICATION_FIELDS: tuple[str, ...] = (
    "原因",
    "替代验证手段",
    "升级触发条件",
    "预计时间",
)


def _filter_unautomated_critical_high(
    scenarios: list[Scenario], trace_data: dict
) -> list[Scenario]:
    """Filter scenarios per R-10-2 layer (a): @risk:critical|high × automation_status:unautomated.

    Cross-references each scenario's risk tags (via extract_tags) against
    trace.yml ``links[].bdd.automation_status``. Only scenarios whose name
    appears in a link's ``bdd.scenarios`` list AND that link has
    ``automation_status: unautomated`` AND the scenario carries
    ``@risk:critical`` OR ``@risk:high`` are returned.
    """
    unautomated_names: set[str] = set()
    links = trace_data.get("links") if isinstance(trace_data, dict) else None
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            bdd = link.get("bdd")
            if not isinstance(bdd, dict):
                continue
            if bdd.get("automation_status") != "unautomated":
                continue
            link_scenarios = bdd.get("scenarios", [])
            if isinstance(link_scenarios, list):
                unautomated_names.update(s for s in link_scenarios if isinstance(s, str))

    return [
        s
        for s in scenarios
        if s.name in unautomated_names
        and any(level in _TARGET_RISK_LEVELS for level in extract_tags(s).risk)
    ]


def _load_runbook(capability_dir: Path) -> str | None:
    """Load runbook.md as plain text; return None on missing.

    Validator-local helper per R-N v10 R-10-5 + N-3 inline:
    NOT promoted to bdd_helpers (YAGNI; Section 5 stability 守; M-FU#6
    Stage E α' may promote if strict mode needs richer parsing).
    """
    runbook_path = capability_dir / "runbook.md"
    if not runbook_path.exists():
        return None
    try:
        return runbook_path.read_text(encoding="utf-8")
    except OSError:
        return None


def _check_justification_fields(runbook_text: str | None) -> tuple[bool, list[str]]:
    """Check runbook.md for justification 4 fields per R-10-2 layer (b).

    MVP keyword presence (N-1 inline): simple substring matching for the
    4 canonical Chinese field names. M-FU#7 Stage E α' will standardize
    runbook sectioning (per-scenario sections + structured YAML sidecar)
    at which point strict mode (M-FU#6 BLOCKING flip) may use richer
    per-scenario parsing.

    Returns (all_present, missing_fields).
    """
    if runbook_text is None:
        return False, list(_JUSTIFICATION_FIELDS)

    missing = [f for f in _JUSTIFICATION_FIELDS if f not in runbook_text]
    return len(missing) == 0, missing


def _validate_capability(capability_dir: Path, repo_root: Path) -> Summary:
    """Validate G22 for one capability per R-N v10 R-10-6 2-layer policy.

    SKIP: behavior.feature missing OR no filtered scenarios (no
    critical|high × unautomated in this capability).
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

    trace_data = load_trace_yml(capability_dir)
    if trace_data is None:
        summary.add(
            Severity.WARN,
            f"{display}: trace.yml missing OR invalid "
            "(G22 cannot verify automation_status; R-N v7 R-1 graceful)",
        )
        return summary

    filtered = _filter_unautomated_critical_high(feature.scenarios, trace_data)
    if not filtered:
        return summary  # SKIP: no critical|high × unautomated scenarios

    runbook_text = _load_runbook(capability_dir)

    for scenario in filtered:
        tags = extract_tags(scenario)
        risk_label = ",".join(tags.risk)
        all_present, missing_fields = _check_justification_fields(runbook_text)

        if all_present:
            summary.add(
                Severity.PASS,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                "unautomated + runbook.md 4-field justification full",
            )
        else:
            missing_str = " / ".join(missing_fields)
            runbook_note = "runbook.md missing" if runbook_text is None else "runbook.md partial"
            summary.add(
                Severity.WARN,
                f"{display}: scenario '{scenario.name}' (@risk:{risk_label}) "
                f"unautomated + {runbook_note}; missing fields: {missing_str} "
                "(R-10-2 CURATION WARN; M-FU#7 maintenance)",
            )

    return summary


def main(argv: list[str] | None = None) -> int:
    """G22 validator entry point."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G22 BDD unautomated justification validator (per gates.md L61 + L96; "
        "bdd-tdd.md L120-122 strict spec; R-N v10 R-10-1 phased per outline §4 R-1'')",
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
        "@risk:critical|high × automation_status:unautomated subset per R-10-2;"
        " M-FU#7 runbook curation defer)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
