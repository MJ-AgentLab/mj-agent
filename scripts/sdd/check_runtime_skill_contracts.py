"""scripts/sdd/check_runtime_skill_contracts.py — Phase M3 implementation.

Validates `capabilities/*/contracts/runtime-skill.contract.yml` against
actual in-source SKILL.md files (`src/mj_agent/skills/<name>/SKILL.md`).

Per blueprint §6 + ADR-031 §5 runtime-skill adapter +
M3-FU-RUNTIME-SKILL-VALIDATOR. Distinct from `check_runtime_expected.py`
which validates docker `runtime.expected.yaml` (containers + healthchecks).

Validates per skills[] entry:
- `file` exists on disk.
- `version` string-exact match against SKILL.md frontmatter version
  (per accumulated AC: NO v-prefix strip / NO normalize; cosmetic-looking
  change like `v0.2` → `0.2` is treated as explicit semantic change → FAIL).
- `state` string-exact match against frontmatter state.
- `body_section_heads` (level-2 headings; Stage B canonical stores with
  `## ` marker) match `extract_headings(body, level=2)`.
- `content_hash` matches `body_sha256(text)` per canonical algorithm
  (strip frontmatter; LF-normalised body bytes; SHA-256 hex lowercase).
  Accepts `sha256:<hex>` or bare `<hex>` via `content_hash_matches`.

content_hash drift is FAIL (runtime-skill-content-change HITL gate);
section heading mismatch is WARN (advisory only); other fields informational.

9-field prose-like exclude list (per accumulated AC from Stage C closure):
type / domain / summary / owner / created / updated / track / eval_references /
supersedes are NOT validated as frozen fields here — they are prose, indirectly
covered by body content_hash via the freeze_anchor.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common import (  # noqa: E402
    Severity,
    Summary,
    body_sha256,
    build_argparser,
    content_hash_matches,
    discover_contracts,
    extract_headings,
    load_contract,
    parse_frontmatter,
    resolve_display_path,
    validate_contract_id,
)

_REQUIRED_TOP_FIELDS = (
    "contract_id",
    "adapter",
    "frontmatter_strip_contract",
    "loader",
    "skills",
)
_REQUIRED_SKILL_FIELDS = (
    "file",
    "version",
    "state",
    "body_section_heads",
    "content_hash",
)
_HEADING_MARKER_LEVEL_2 = "## "


def _validate_skill_entry(
    skill_entry: dict[str, Any],
    repo_root: Path,
    summary: Summary,
) -> None:
    """Validate one entry of skills[]; add findings directly to `summary`.

    Modifies the shared contract-level summary in place so messages survive
    aggregation (Summary.merge merges counts only, per its docstring).
    """
    fail_before = summary.fail_count

    for field in _REQUIRED_SKILL_FIELDS:
        if field not in skill_entry:
            summary.add(Severity.FAIL, f"skills[] entry missing required field '{field}'")
            return

    file_str = skill_entry["file"]
    skill_path = repo_root / file_str
    if not skill_path.exists():
        summary.add(Severity.FAIL, f"{file_str}: skill file does not exist on disk")
        return

    text = skill_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if fm is None:
        summary.add(
            Severity.FAIL,
            f"{file_str}: no frontmatter block found (frontmatter strip contract requires one)",
        )
        return

    expected_version = skill_entry["version"]
    actual_version = fm.get("version")
    if actual_version != expected_version:
        summary.add(
            Severity.FAIL,
            f"{file_str}: version mismatch — contract: {expected_version!r}, "
            f"frontmatter: {actual_version!r} (string-exact required; no v-prefix strip / normalize)",
        )

    expected_state = skill_entry["state"]
    actual_state = fm.get("state")
    if actual_state != expected_state:
        summary.add(
            Severity.FAIL,
            f"{file_str}: state mismatch — contract: {expected_state!r}, frontmatter: {actual_state!r}",
        )

    expected_hash = skill_entry["content_hash"]
    actual_hash = body_sha256(text)
    if not content_hash_matches(expected_hash, actual_hash):
        summary.add(
            Severity.FAIL,
            f"{file_str}: BODY CONTENT HASH DRIFT — contract anchored '{expected_hash[:24]}...' "
            f"but actual is '{actual_hash[:16]}...' (runtime-skill-content-change HITL gate; "
            f"STOP + HITL; investigate)",
        )

    expected_heads = skill_entry.get("body_section_heads") or []
    actual_heads = extract_headings(body, level=2, skip_fenced=True)
    for required_head in expected_heads:
        compare_name = required_head
        if compare_name.startswith(_HEADING_MARKER_LEVEL_2):
            compare_name = compare_name[len(_HEADING_MARKER_LEVEL_2):]
        if compare_name not in actual_heads:
            summary.add(
                Severity.WARN,
                f"{file_str}: contract-required body section {required_head!r} "
                f"not found in actual level-2 headings",
            )

    if summary.fail_count == fail_before:
        summary.add_aggregate_pass(
            n=1,
            message=f"{file_str}: version + state + content_hash + body_section_heads all PASS",
        )


def _validate_contract(contract_path: Path, repo_root: Path) -> Summary:
    """Validate one runtime-skill.contract.yml file."""
    summary = Summary()

    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary

    if not validate_contract_id(contract, "runtime-skill"):
        summary.add(
            Severity.FAIL,
            f"contract_id is not 'runtime-skill' (got {contract.get('contract_id')!r})",
        )
        return summary

    for field in _REQUIRED_TOP_FIELDS:
        if field not in contract:
            summary.add(Severity.FAIL, f"missing required top-level field '{field}'")

    if contract.get("frontmatter_strip_contract") is not True:
        summary.add(
            Severity.FAIL,
            "frontmatter_strip_contract MUST be true (Agent_Side §7.5 strip contract)",
        )

    loader = contract.get("loader")
    if not isinstance(loader, str):
        summary.add(
            Severity.FAIL,
            f"loader MUST be a string (got {type(loader).__name__})",
        )

    skills = contract.get("skills")
    if not isinstance(skills, list):
        summary.add(
            Severity.FAIL,
            f"skills MUST be a list (got {type(skills).__name__})",
        )
    elif not skills:
        summary.add(Severity.FAIL, "skills list is empty (must have ≥1 entry)")

    # Short-circuit: contract-level FAILs make per-skill validation unreliable.
    if summary.fail_count > 0:
        return summary

    for i, skill_entry in enumerate(skills):
        if not isinstance(skill_entry, dict):
            summary.add(Severity.FAIL, f"skills[{i}] is not a mapping")
            continue
        _validate_skill_entry(skill_entry, repo_root, summary)

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_runtime_skill_contracts.py",
        description=(
            "Validate capabilities/*/contracts/runtime-skill.contract.yml against "
            "actual src/mj_agent/skills/<name>/SKILL.md files. Phase M3 warning mode "
            "(per blueprint §6 gate matrix); M4 strict. CRITICAL: content_hash drift "
            "is FAIL — drift indicates runtime-skill-content-change HITL gate breach."
        ),
        contract_filename="runtime-skill.contract.yml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    contract_files = discover_contracts(repo_root, "runtime-skill.contract.yml", args.capability)

    if args.dry_run:
        print(
            f"[dry-run] check_runtime_skill_contracts.py — Phase M3 impl; "
            f"found {len(contract_files)} runtime-skill.contract.yml"
        )
        return 0

    if not contract_files:
        print("no runtime-skill.contract.yml found")
        return 0

    print(
        f"check_runtime_skill_contracts.py — validating "
        f"{len(contract_files)} runtime-skill.contract.yml"
    )
    total = Summary()
    for contract_path in contract_files:
        display = resolve_display_path(contract_path, repo_root)
        print(f"\n{display}")
        sub = _validate_contract(contract_path, repo_root)
        sub.print_messages()
        total.merge(sub)

    print("\n=== Summary ===")
    print(f"PASS: {total.pass_count} / WARN: {total.warn_count} / FAIL: {total.fail_count}")
    return total.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
