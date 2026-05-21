"""scripts/sdd/check_capability_schema.py — Phase M3 implementation.

Validates `capabilities/*/spec.yml` against the documented schema (per
ADR-031 §4 RD5 + ADR-031 §4 RD9). Phase M0 skeleton replaced under
M3-FU-G1G2G9-IMPL. M3 warning mode; M4 strict.

Validated fields:
- Required top-level: id / name / domain / lifecycle_state / archive_state /
  adapter_coverage / last_verified / owner / created / updated / summary /
  requirements.
- `id` matches `<domain>.<slug>` pattern (`^[a-z][a-z0-9-]*\\.[a-z][a-z0-9-]*$`).
- `lifecycle_state` ∈ 9-state enum (idea / specified / contracted / planned /
  implementing / verifying / active / evolving / deprecated).
- `archive_state` ∈ 5-state enum (active / deprecated / frozen / archived /
  purge-eligible).
- `adapter_coverage` ⊆ 7 adapter slugs (python / langchain-agent / prompt /
  runtime-skill / claude-code-skill / docker-container / tdd-bdd) plus
  bdd-tdd alias accepted (sdd/adapters/bdd-tdd.md uses the bdd-tdd form;
  spec.yml files use tdd-bdd — dual-name accepted at M3 per drift compat).
- `requirements[]` non-empty; each entry has id matching `^REQ-[0-9]{3}$` +
  statement (string) + rationale (string) + priority ∈ {critical / high /
  medium / low}.

Schema deviations are WARN at M3 (per M3-FU-G1G2G9-IMPL §6 严格守约:
no blocking toggle); M4 will flip to FAIL.
"""

from __future__ import annotations

import re
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

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*$")
_REQ_PATTERN = re.compile(r"^REQ-[0-9]{3}$")

_LIFECYCLE_STATES = frozenset({
    "idea", "specified", "contracted", "planned", "implementing",
    "verifying", "active", "evolving", "deprecated",
    # `drafting` is the M1 transitional state used by all 5 pilot specs
    # (safe-sql/spec.yml:96 "TBD Phase M3: drafting → contracted"); the 9-state
    # enum in spec.yml header comments omits it but actual usage is canonical.
    # Accepted at M3; M4 will formalise the vocabulary (see follow-up).
    "drafting",
})
_ARCHIVE_STATES = frozenset({
    "active", "deprecated", "frozen", "archived", "purge-eligible",
})
_ADAPTER_COVERAGE_SLUGS = frozenset({
    "python", "langchain-agent", "prompt", "runtime-skill",
    "claude-code-skill", "docker-container",
    "tdd-bdd", "bdd-tdd",  # dual-name accepted (M3 drift compat)
})
_REQUIREMENT_PRIORITIES = frozenset({"critical", "high", "medium", "low"})
_REQUIRED_TOP_FIELDS = (
    "id", "name", "domain", "lifecycle_state", "archive_state",
    "adapter_coverage", "last_verified", "owner", "created", "updated",
    "summary", "requirements",
)


def _validate_requirement(req: dict, idx: int, summary: Summary, display: str) -> None:
    """Validate one requirements[] entry."""
    if not isinstance(req, dict):
        summary.add(Severity.WARN, f"{display}: requirements[{idx}] is not a mapping")
        return
    req_id = req.get("id")
    if not isinstance(req_id, str) or not _REQ_PATTERN.match(req_id):
        summary.add(
            Severity.WARN,
            f"{display}: requirements[{idx}].id {req_id!r} does not match REQ-NNN pattern",
        )
    for field in ("statement", "rationale"):
        value = req.get(field)
        if not isinstance(value, str) or not value.strip():
            summary.add(
                Severity.WARN,
                f"{display}: requirements[{idx}] ({req_id}) missing or non-string '{field}'",
            )
    priority = req.get("priority")
    if priority not in _REQUIREMENT_PRIORITIES:
        summary.add(
            Severity.WARN,
            f"{display}: requirements[{idx}] ({req_id}) priority {priority!r} not in "
            f"{{critical, high, medium, low}}",
        )


def _validate_spec(spec_path: Path, repo_root: Path) -> Summary:
    """Validate one capabilities/*/spec.yml file."""
    summary = Summary()
    display = resolve_display_path(spec_path, repo_root)
    spec = load_contract(spec_path)
    if spec is None:
        summary.add(Severity.WARN, f"{display}: YAML parse error or non-mapping root")
        return summary

    for field in _REQUIRED_TOP_FIELDS:
        if field not in spec:
            summary.add(Severity.WARN, f"{display}: missing required top-level field '{field}'")

    spec_id = spec.get("id")
    if isinstance(spec_id, str) and not _ID_PATTERN.match(spec_id):
        summary.add(
            Severity.WARN,
            f"{display}: id {spec_id!r} does not match <domain>.<slug> pattern",
        )

    lifecycle = spec.get("lifecycle_state")
    if lifecycle is not None and lifecycle not in _LIFECYCLE_STATES:
        summary.add(
            Severity.WARN,
            f"{display}: lifecycle_state {lifecycle!r} not in 9-state enum",
        )

    archive = spec.get("archive_state")
    if archive is not None and archive not in _ARCHIVE_STATES:
        summary.add(
            Severity.WARN,
            f"{display}: archive_state {archive!r} not in 5-state enum",
        )

    coverage = spec.get("adapter_coverage")
    if isinstance(coverage, list):
        for slug in coverage:
            if slug not in _ADAPTER_COVERAGE_SLUGS:
                summary.add(
                    Severity.WARN,
                    f"{display}: adapter_coverage entry {slug!r} not in adapter slug set",
                )
    elif coverage is not None:
        summary.add(
            Severity.WARN,
            f"{display}: adapter_coverage must be a list (got {type(coverage).__name__})",
        )

    requirements = spec.get("requirements")
    if isinstance(requirements, list):
        if not requirements:
            summary.add(Severity.WARN, f"{display}: requirements list is empty")
        for idx, req in enumerate(requirements):
            _validate_requirement(req, idx, summary, display)
    elif requirements is not None:
        summary.add(
            Severity.WARN,
            f"{display}: requirements must be a list (got {type(requirements).__name__})",
        )

    if summary.warn_count == 0 and summary.fail_count == 0:
        n_reqs = len(requirements) if isinstance(requirements, list) else 0
        summary.add_aggregate_pass(
            n=1,
            message=f"{display}: schema valid ({n_reqs} requirements; "
                    f"lifecycle={lifecycle}, archive={archive})",
        )
    return summary


def _discover_specs(repo_root: Path, capability_arg: Path | None) -> list[Path]:
    if capability_arg is not None:
        candidate = (capability_arg / "spec.yml").resolve()
        return [candidate] if candidate.exists() else []
    capabilities_dir = repo_root / "capabilities"
    if not capabilities_dir.exists():
        return []
    return sorted(capabilities_dir.glob("*/*/spec.yml"))


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_capability_schema.py",
        description=(
            "Validate capabilities/*/spec.yml schema (G1). Phase M3 warning mode; "
            "M4 strict per blueprint §6 gate matrix. Replaces M0 skeleton under "
            "M3-FU-G1G2G9-IMPL."
        ),
        contract_filename="spec.yml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    spec_files = _discover_specs(repo_root, args.capability)

    if args.dry_run:
        print(f"[dry-run] check_capability_schema.py — Phase M3 impl; found {len(spec_files)} spec.yml")
        return 0

    if not spec_files:
        print("no capabilities/*/spec.yml found")
        return 0

    print(f"check_capability_schema.py — validating {len(spec_files)} spec.yml (G1)")
    total = Summary()
    for spec_path in spec_files:
        sub = _validate_spec(spec_path, repo_root)
        sub.print_messages()
        total.merge(sub)

    print("\n=== Summary ===")
    print(f"PASS: {total.pass_count} / WARN: {total.warn_count} / FAIL: {total.fail_count}")
    return total.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
