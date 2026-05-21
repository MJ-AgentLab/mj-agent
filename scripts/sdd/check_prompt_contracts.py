"""scripts/sdd/check_prompt_contracts.py — Phase M2 implementation.

Validates `capabilities/*/contracts/prompt.contract.yml` against actual prompt
files (typically `src/mj_agent/prompts/system.md` + 9 in-source SKILL.md).

Per blueprint §6 Phase M2 §3 + ADR-031 §5 prompt adapter. Phase M2 warning
mode; M3 strict.

NOTE: At Phase M1 end, **NO capability instantiates prompt.contract.yml**;
Stage C will create one for llm-provider (`llm-provider/contracts/prompt.contract.yml`).
This validator is delivered ready; M1 smoke verifies discover + early-return.

Validates (per C4 augmentation — schema-invariant focus):
  - `prompt_path` field exists; the referenced file exists on disk.
  - Frontmatter has 3 required fields: `version` / `state` / `model_binding`.
    (Other fields like `eval_references` are A8 transitional waiver — not
    required at M2 per ADR-024 §A8 waiver延续 Phase E.)
  - Body section headings (single-hash for system.md style; fenced-block
    skipping per Subagent B finding — uses _common.frontmatter.extract_headings
    level=1 skip_fenced=True).
  - **CRITICAL FAIL**: `freeze_anchor.content_hash` MUST match
    `sha256(current body)`. Any drift indicates prompt-version-bump 必停
    surface was modified outside the contract evolution workflow → STOP +
    HITL (do not silent-fix; investigate why drift occurred).

Per C4 augmentation: this validator does NOT check behavior.feature for
`@adapter:prompt` tag (M1 17 scenarios have 0 by design — prompt is a
schema contract, not behavior contract).
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
    body_sha256,
    build_argparser,
    discover_contracts,
    extract_headings,
    load_contract,
    parse_frontmatter,
    resolve_display_path,
    validate_contract_id,
)

_REQUIRED_FRONTMATTER_FIELDS = ("version", "state", "model_binding")


def _validate_contract(contract_path: Path, repo_root: Path) -> Summary:
    """Validate one prompt.contract.yml file."""
    summary = Summary()

    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary

    if not validate_contract_id(contract, "prompt"):
        summary.add(Severity.FAIL, f"{contract_path}: contract_id is not 'prompt' (got {contract.get('contract_id')!r})")
        return summary

    prompt_path_str = contract.get("prompt_path")
    if not prompt_path_str:
        summary.add(Severity.FAIL, "contract missing required field 'prompt_path'")
        return summary

    prompt_path = repo_root / prompt_path_str
    if not prompt_path.exists():
        summary.add(Severity.FAIL, f"prompt_path '{prompt_path_str}' does not exist in repo")
        return summary

    prompt_text = prompt_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(prompt_text)

    if fm is None:
        summary.add(Severity.WARN, f"{prompt_path_str}: no frontmatter block found (frontmatter strip contract requires one)")
    else:
        for field in _REQUIRED_FRONTMATTER_FIELDS:
            if field not in fm:
                summary.add(Severity.FAIL, f"{prompt_path_str}: required frontmatter field '{field}' missing")
        contract_version = contract.get("version")
        actual_version = fm.get("version")
        if contract_version and actual_version and contract_version != actual_version:
            summary.add(Severity.FAIL, f"{prompt_path_str}: version drift — contract says {contract_version!r} but file says {actual_version!r}")

    freeze_anchor = contract.get("freeze_anchor", {})
    expected_hash = freeze_anchor.get("content_hash") if isinstance(freeze_anchor, dict) else None
    if expected_hash:
        actual_hash = body_sha256(prompt_text)
        if actual_hash != expected_hash:
            summary.add(
                Severity.FAIL,
                f"{prompt_path_str}: BODY CONTENT HASH DRIFT — contract anchored '{expected_hash[:16]}...' but actual is '{actual_hash[:16]}...' (prompt-version-bump 必停 surface drifted; STOP + HITL; investigate)"
            )

    body_headings = extract_headings(body, level=1, skip_fenced=True)
    if not body_headings:
        summary.add(Severity.WARN, f"{prompt_path_str}: no level-1 headings found in body (system.md uses '# ' style; verify or check fenced blocks)")
    contract_sections = freeze_anchor.get("body_section_names", []) if isinstance(freeze_anchor, dict) else []
    if contract_sections:
        for required_section in contract_sections:
            if required_section not in body_headings:
                summary.add(Severity.WARN, f"{prompt_path_str}: contract-required body section {required_section!r} not found in current body headings")

    if contract.get("allowed_state_transitions"):
        summary.add(Severity.WARN, "allowed_state_transitions documented (informational; M3 will track via PR / git log analysis)")
    if contract.get("eval_references"):
        summary.add(Severity.WARN, "eval_references documented (A8 transitional waiver延续 Phase E per ADR-024; informational at M2)")

    if summary.fail_count == 0:
        summary.add_aggregate_pass(
            n=1,
            message=f"prompt.contract.yml verified (prompt_path={prompt_path_str!r}, content_hash match)",
        )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_prompt_contracts.py",
        description=(
            "Validate capabilities/*/contracts/prompt.contract.yml against actual "
            "prompt files (typically src/mj_agent/prompts/system.md). Phase M2 "
            "warning mode; --strict for M3 blocking. CRITICAL: content_hash drift "
            "is FAIL not WARN — drift indicates prompt-version-bump 必停 surface "
            "was modified outside contract evolution workflow."
        ),
        contract_filename="prompt.contract.yml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    contract_files = discover_contracts(repo_root, "prompt.contract.yml", args.capability)

    if args.dry_run:
        print(f"[dry-run] check_prompt_contracts.py — Phase M2 impl; found {len(contract_files)} prompt.contract.yml")
        return 0

    if not contract_files:
        print("no prompt.contract.yml found (Phase M1 has none; Stage C will add llm-provider/contracts/prompt.contract.yml)")
        return 0

    print(f"check_prompt_contracts.py — validating {len(contract_files)} prompt.contract.yml")
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
