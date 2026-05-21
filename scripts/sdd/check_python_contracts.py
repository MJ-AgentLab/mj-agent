"""scripts/sdd/check_python_contracts.py — Phase M2 implementation (refactored).

Validates `capabilities/*/contracts/python.contract.yml` against the actual
`src/mj_agent/` Python codebase using `ast` parsing (via `_common.ast_helpers`).

Per blueprint §6 Phase M2 §3 + ADR-031 §5 python adapter. Phase M2 warning
mode (default exit 0 on WARN). Phase M3 will enable `--strict` in CI to flip
WARN → blocking.

Validates:
  - `modules:` is a LIST (per subagent C survey §D; multi-module schema).
  - Each module `path` (dotted) resolves to an existing `.py` file.
  - Each module's `exports[].name` is a top-level definition in source AST.
  - Each module's `constants[]` (when present) has literal-value match
    (e.g. ADR-029 stable strings in `tool_errors.py`).
  - `hitl_required[]` enum uses hyphen canonical (`sql-guardrail-relax`);
    underscore variants → WARN (M3 cleanup planned; per C5 augmentation).

WARN sources (informational, by design at M2):
  - `public_invariants:` text documented but not machine-verifiable here.
  - `adr:` cross-ref not yet linked to actual ADR file existence.
  - `wiring:` middleware/agent wiring not yet machine-validated.
  - All flagged as TBD-M3 (when contract test infrastructure lands).

Refactor (Stage A X.2): shared helpers moved to `_common/`; this file now holds
only python-validator-specific logic. Regression check verified: counts +
trigger categories identical to pre-refactor 265-line version.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Bootstrap: enable direct `python scripts/sdd/<name>.py` invocation by
# putting the worktree root (3 levels up) on sys.path so `scripts.sdd._common`
# resolves. uv run / python -m / pytest -friendly.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common import (  # noqa: E402  (after sys.path manipulation)
    Severity,
    Summary,
    build_argparser,
    check_constant_literal,
    discover_contracts,
    extract_top_level_names,
    load_contract,
    module_path_to_file,
    parse_module_safe,
    resolve_display_path,
    validate_contract_id,
    validate_hitl_enum,
)


def _validate_module(
    module_entry: dict[str, Any], repo_root: Path
) -> list[tuple[Severity, str]]:
    """Validate one entry in `modules:` list."""
    findings: list[tuple[Severity, str]] = []
    module_path_dotted = module_entry.get("path")
    if not module_path_dotted:
        findings.append((Severity.FAIL, "module entry missing required field 'path'"))
        return findings

    file_path = module_path_to_file(module_path_dotted, repo_root)
    if file_path is None:
        findings.append((Severity.FAIL, f"module {module_path_dotted!r} → file not found in repo"))
        return findings

    tree = parse_module_safe(file_path)
    if tree is None:
        findings.append((Severity.FAIL, f"{file_path}: SyntaxError during ast.parse"))
        return findings

    top_level_names = extract_top_level_names(tree)
    for export in module_entry.get("exports", []):
        name = export.get("name")
        if name and name not in top_level_names:
            findings.append((Severity.FAIL, f"{file_path}: export '{name}' not found at module level"))

    for constant in module_entry.get("constants", []):
        name = constant.get("name")
        value = constant.get("value")
        if (
            name
            and isinstance(value, str)
            and not check_constant_literal(tree, name, value)
        ):
            findings.append((Severity.WARN, f"{file_path}: constant '{name}' literal drift or non-literal expression (contract: {value!r})"))

    if module_entry.get("public_invariants"):
        findings.append((Severity.WARN, f"{module_path_dotted}: public_invariants documented (informational; M3 will add machine-verifiable test)"))
    if module_entry.get("adr"):
        findings.append((Severity.WARN, f"{module_path_dotted}: adr cross-ref '{module_entry['adr']}' not yet linked to docs/adr/ existence check (TBD-M3)"))
    if module_entry.get("wiring"):
        findings.append((Severity.WARN, f"{module_path_dotted}: wiring spec documented (informational; M3 will validate make_graph middleware=[...] match)"))

    return findings


def _validate_contract(contract_path: Path, repo_root: Path) -> Summary:
    """Validate one python.contract.yml file."""
    summary = Summary()

    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary

    if not validate_contract_id(contract, "python"):
        summary.add(Severity.FAIL, f"{contract_path}: contract_id is not 'python' (got {contract.get('contract_id')!r})")
        return summary

    modules = contract.get("modules", [])
    if not isinstance(modules, list):
        summary.add(Severity.FAIL, f"{contract_path}: 'modules' must be a list (per multi-module schema; subagent C §D)")
        return summary

    for module_entry in modules:
        for severity, msg in _validate_module(module_entry, repo_root):
            summary.add(severity, msg)

    hitl = contract.get("hitl_required", [])
    if isinstance(hitl, list):
        for sev_str, msg in validate_hitl_enum(hitl):
            summary.add(Severity(sev_str), msg)

    if summary.fail_count == 0:
        summary.add_aggregate_pass(
            n=len(modules),
            message=f"{len(modules)} modules verified (exports + constants where present)",
        )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_python_contracts.py",
        description=(
            "Validate capabilities/*/contracts/python.contract.yml against actual "
            "src/mj_agent/ Python codebase. Phase M2 warning mode; --strict flips to "
            "exit 1 on WARN (M3 blocking)."
        ),
        contract_filename="python.contract.yml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    contract_files = discover_contracts(repo_root, "python.contract.yml", args.capability)

    if args.dry_run:
        print(f"[dry-run] check_python_contracts.py — Phase M2 impl; found {len(contract_files)} python.contract.yml")
        return 0

    if not contract_files:
        print("no python.contract.yml found")
        return 0

    print(f"check_python_contracts.py — validating {len(contract_files)} python.contract.yml")

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
