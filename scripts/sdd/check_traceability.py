"""scripts/sdd/check_traceability.py — Phase M3 implementation.

Validates `capabilities/*/trace.yml` against `sdd/traceability.schema.json`
(schema v1.2 — REQ -> BDD -> CONTRACT -> TEST -> TASK -> PR -> EVIDENCE).
Phase M0 skeleton replaced under M3-FU-G1G2G9-IMPL. M3 warning mode;
M4 strict per blueprint §6 gate matrix.

Validated fields:
- Required top-level: capability / schema_version / links.
- `capability` matches `<domain>.<slug>` pattern.
- `schema_version == "1.2"` (per current schema enum).
- `links[]` non-empty; each entry has `req` matching `^REQ-[0-9]{3}$`.
- Per-link optional `bdd` object: feature / scenarios (non-empty) /
  automation_status ∈ {automated / manual / unautomated}.
- `cross_capability_refs[]` (if present): target / direction (outbound /
  inbound / bidirectional) / surface / rationale required.

Standalone re-implementation of the relevant JSON Schema subset; no
external `jsonschema` dependency to keep `_common/` lean.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

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

_CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*$")
_REQ_PATTERN = re.compile(r"^REQ-[0-9]{3}$")
_SCHEMA_VERSION = "1.2"
_BDD_AUTOMATION_STATES = frozenset({"automated", "manual", "unautomated"})
_CROSS_REF_DIRECTIONS = frozenset({"outbound", "inbound", "bidirectional"})
_REQUIRED_TOP_FIELDS = ("capability", "schema_version", "links")
_REQUIRED_CROSS_REF_FIELDS = ("target", "direction", "surface", "rationale")


def _validate_bdd(bdd: Any, link_idx: int, req: str, summary: Summary, display: str) -> None:
    """Validate the bdd object inside one link entry."""
    if not isinstance(bdd, dict):
        summary.add(Severity.WARN, f"{display}: links[{link_idx}] ({req}) bdd is not a mapping")
        return
    if not isinstance(bdd.get("feature"), str):
        summary.add(Severity.WARN, f"{display}: links[{link_idx}] ({req}) bdd.feature missing or not string")
    scenarios = bdd.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        summary.add(
            Severity.WARN,
            f"{display}: links[{link_idx}] ({req}) bdd.scenarios must be a non-empty list",
        )
    automation = bdd.get("automation_status")
    if automation not in _BDD_AUTOMATION_STATES:
        summary.add(
            Severity.WARN,
            f"{display}: links[{link_idx}] ({req}) bdd.automation_status {automation!r} "
            f"not in {{automated, manual, unautomated}}",
        )


def _validate_cross_capability_ref(ref: Any, idx: int, summary: Summary, display: str) -> None:
    """Validate one entry of cross_capability_refs[]."""
    if not isinstance(ref, dict):
        summary.add(Severity.WARN, f"{display}: cross_capability_refs[{idx}] is not a mapping")
        return
    for field in _REQUIRED_CROSS_REF_FIELDS:
        if field not in ref:
            summary.add(
                Severity.WARN,
                f"{display}: cross_capability_refs[{idx}] missing required field '{field}'",
            )
    target = ref.get("target")
    if isinstance(target, str) and not _CAPABILITY_PATTERN.match(target):
        summary.add(
            Severity.WARN,
            f"{display}: cross_capability_refs[{idx}].target {target!r} not matching "
            f"<domain>.<slug> pattern",
        )
    direction = ref.get("direction")
    if direction not in _CROSS_REF_DIRECTIONS:
        summary.add(
            Severity.WARN,
            f"{display}: cross_capability_refs[{idx}].direction {direction!r} not in "
            f"{{outbound, inbound, bidirectional}}",
        )


def _validate_trace(trace_path: Path, repo_root: Path) -> Summary:
    """Validate one capabilities/*/trace.yml file."""
    summary = Summary()
    display = resolve_display_path(trace_path, repo_root)
    trace = load_contract(trace_path)
    if trace is None:
        summary.add(Severity.WARN, f"{display}: YAML parse error or non-mapping root")
        return summary

    for field in _REQUIRED_TOP_FIELDS:
        if field not in trace:
            summary.add(Severity.WARN, f"{display}: missing required top-level field '{field}'")

    capability = trace.get("capability")
    if isinstance(capability, str) and not _CAPABILITY_PATTERN.match(capability):
        summary.add(
            Severity.WARN,
            f"{display}: capability {capability!r} does not match <domain>.<slug> pattern",
        )

    schema_version = trace.get("schema_version")
    if schema_version != _SCHEMA_VERSION:
        summary.add(
            Severity.WARN,
            f"{display}: schema_version {schema_version!r} != {_SCHEMA_VERSION!r} (current enum)",
        )

    cross_refs = trace.get("cross_capability_refs")
    if isinstance(cross_refs, list):
        if len(cross_refs) > 5:
            summary.add(
                Severity.WARN,
                f"{display}: cross_capability_refs has {len(cross_refs)} entries (R-G7 budget ≤ 5)",
            )
        for idx, ref in enumerate(cross_refs):
            _validate_cross_capability_ref(ref, idx, summary, display)

    links = trace.get("links")
    if not isinstance(links, list):
        summary.add(
            Severity.WARN,
            f"{display}: links must be a list (got {type(links).__name__})",
        )
    elif not links:
        summary.add(Severity.WARN, f"{display}: links list is empty")
    else:
        for idx, link in enumerate(links):
            if not isinstance(link, dict):
                summary.add(Severity.WARN, f"{display}: links[{idx}] is not a mapping")
                continue
            req = link.get("req")
            if not isinstance(req, str) or not _REQ_PATTERN.match(req):
                summary.add(
                    Severity.WARN,
                    f"{display}: links[{idx}].req {req!r} does not match REQ-NNN pattern",
                )
                continue
            if "bdd" in link:
                _validate_bdd(link["bdd"], idx, req, summary, display)

    if summary.warn_count == 0 and summary.fail_count == 0:
        n_links = len(links) if isinstance(links, list) else 0
        n_refs = len(cross_refs) if isinstance(cross_refs, list) else 0
        summary.add_aggregate_pass(
            n=1,
            message=f"{display}: schema valid ({n_links} REQ links; {n_refs} cross_capability_refs)",
        )
    return summary


def _discover_traces(repo_root: Path, capability_arg: Path | None) -> list[Path]:
    if capability_arg is not None:
        candidate = (capability_arg / "trace.yml").resolve()
        return [candidate] if candidate.exists() else []
    capabilities_dir = repo_root / "capabilities"
    if not capabilities_dir.exists():
        return []
    return sorted(capabilities_dir.glob("*/*/trace.yml"))


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_traceability.py",
        description=(
            "Validate capabilities/*/trace.yml against schema v1.2 (G2/G5). "
            "Phase M3 warning mode; M4 strict per blueprint §6 gate matrix. "
            "Replaces M0 skeleton under M3-FU-G1G2G9-IMPL."
        ),
        contract_filename="trace.yml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    trace_files = _discover_traces(repo_root, args.capability)

    if args.dry_run:
        print(f"[dry-run] check_traceability.py — Phase M3 impl; found {len(trace_files)} trace.yml")
        return 0

    if not trace_files:
        print("no capabilities/*/trace.yml found")
        return 0

    print(f"check_traceability.py — validating {len(trace_files)} trace.yml (G2/G5; schema v{_SCHEMA_VERSION})")
    total = Summary()
    for trace_path in trace_files:
        sub = _validate_trace(trace_path, repo_root)
        sub.print_messages()
        total.merge(sub)

    print("\n=== Summary ===")
    print(f"PASS: {total.pass_count} / WARN: {total.warn_count} / FAIL: {total.fail_count}")
    return total.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
