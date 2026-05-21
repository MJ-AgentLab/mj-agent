"""scripts/sdd/check_agent_contracts.py — Phase M2 implementation.

Validates `capabilities/*/contracts/agent.contract.yml` against the actual
LangChain Agent wiring in `src/mj_agent/agent.py` + `tools/__init__.py`.

Per blueprint §6 Phase M2 §3 + ADR-031 §5 langchain-agent adapter + ADR-029
middleware wiring contract. Phase M2 warning mode; M3 strict.

NOTE: At Phase M1 end, **NO capability instantiates agent.contract.yml**. The
schema is documented in `sdd/templates/contracts/agent.contract.yml.template`
but no capability has elected to author one yet (future `data-agent.tool-chain`
in Phase 2+ will own it). This validator is delivered ready; M1 smoke verifies
only `discover` + `--dry-run` + early-return paths.

Validates:
  - `graph_symbol` (default `make_graph`) is a top-level definition in `agent.py`.
  - Each `tools[]` entry appears in `ALL_TOOLS` list inside `tools/__init__.py`.
  - `middleware[]` functions can be referenced (descriptive; M3 will verify
    `make_graph(middleware=[...])` kwargs match).
  - `hitl_required[]` enum normalization (hyphen canonical; underscore → WARN).

WARN sources (informational, M3 will tighten):
  - `tool_call_order_hint:` text documented but tied to system prompt content.
  - `checkpointer:` config documented but validation requires make_graph parse.
  - `middleware[]` items not found in agent.py top-level (likely imported).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Bootstrap: enable `python scripts/sdd/<name>.py` invocation by putting
# worktree root on sys.path (chicken-and-egg with _common; see V1 docstring).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common import (  # noqa: E402
    Severity,
    Summary,
    build_argparser,
    discover_contracts,
    extract_top_level_names,
    load_contract,
    module_path_to_file,
    parse_module_safe,
    resolve_display_path,
    validate_contract_id,
    validate_hitl_enum,
)


def _extract_assign_value(tree: ast.AST, name: str) -> ast.AST | None:
    """Return the RHS AST of `name = <expr>` top-level assignment, or None."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
    return None


def _extract_list_items(value_ast: ast.AST) -> list[str]:
    """Extract item strings or bare-name references from a list AST."""
    if not isinstance(value_ast, ast.List):
        return []
    items: list[str] = []
    for el in value_ast.elts:
        if isinstance(el, ast.Constant) and isinstance(el.value, str):
            items.append(el.value)
        elif isinstance(el, ast.Name):
            items.append(el.id)
    return items


def _validate_contract(contract_path: Path, repo_root: Path) -> Summary:
    """Validate one agent.contract.yml file."""
    summary = Summary()

    contract = load_contract(contract_path)
    if contract is None:
        summary.add(Severity.FAIL, f"{contract_path}: YAML parse error or non-mapping root")
        return summary

    if not validate_contract_id(contract, "agent"):
        summary.add(Severity.FAIL, f"{contract_path}: contract_id is not 'agent' (got {contract.get('contract_id')!r})")
        return summary

    graph_symbol = contract.get("graph_symbol")
    if not graph_symbol:
        summary.add(Severity.FAIL, "contract missing required field 'graph_symbol'")
        return summary

    agent_py = module_path_to_file("src.mj_agent.agent", repo_root)
    if agent_py is None:
        summary.add(Severity.FAIL, "src/mj_agent/agent.py not found in repo")
        return summary

    tree = parse_module_safe(agent_py)
    if tree is None:
        summary.add(Severity.FAIL, f"{agent_py}: SyntaxError during ast.parse")
        return summary

    agent_names = extract_top_level_names(tree)
    if graph_symbol not in agent_names:
        summary.add(Severity.FAIL, f"{agent_py}: graph_symbol '{graph_symbol}' not found at module level")

    tools_contract = contract.get("tools", [])
    if tools_contract:
        tools_init = repo_root / "src" / "mj_agent" / "tools" / "__init__.py"
        if not tools_init.exists():
            summary.add(Severity.FAIL, "src/mj_agent/tools/__init__.py not found")
        else:
            tools_tree = parse_module_safe(tools_init)
            if tools_tree is not None:
                all_tools_value = _extract_assign_value(tools_tree, "ALL_TOOLS")
                if all_tools_value is None:
                    summary.add(Severity.WARN, "tools/__init__.py: ALL_TOOLS list not found at module level (informational; may be conditional)")
                else:
                    all_tools_items = _extract_list_items(all_tools_value)
                    for tool_name in tools_contract:
                        if tool_name not in all_tools_items:
                            summary.add(Severity.FAIL, f"tool '{tool_name}' not in tools/__init__.py:ALL_TOOLS")

    middleware = contract.get("middleware", [])
    for mw_name in middleware:
        if mw_name not in agent_names:
            summary.add(Severity.WARN, f"middleware '{mw_name}': not at agent.py top-level (likely imported; M3 will verify make_graph kwargs)")

    hitl = contract.get("hitl_required", [])
    if isinstance(hitl, list):
        for sev_str, msg in validate_hitl_enum(hitl):
            summary.add(Severity(sev_str), msg)

    if contract.get("tool_call_order_hint"):
        summary.add(Severity.WARN, "tool_call_order_hint documented (informational; M3 will validate system prompt content)")
    if contract.get("checkpointer"):
        summary.add(Severity.WARN, "checkpointer config documented (informational; M3 will validate make_graph kwargs)")

    if summary.fail_count == 0:
        summary.add_aggregate_pass(
            n=1,
            message=f"agent.contract.yml verified (graph_symbol={graph_symbol!r}, tools={len(tools_contract)}, middleware={len(middleware)})",
        )

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_agent_contracts.py",
        description=(
            "Validate capabilities/*/contracts/agent.contract.yml against actual "
            "src/mj_agent/agent.py + tools/__init__.py wiring. Phase M2 warning "
            "mode; --strict flips to exit 1 on WARN (M3 blocking)."
        ),
        contract_filename="agent.contract.yml",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    contract_files = discover_contracts(repo_root, "agent.contract.yml", args.capability)

    if args.dry_run:
        print(f"[dry-run] check_agent_contracts.py — Phase M2 impl; found {len(contract_files)} agent.contract.yml")
        return 0

    if not contract_files:
        print("no agent.contract.yml found (Phase M1 has none; future data-agent.tool-chain Phase 2+ will add)")
        return 0

    print(f"check_agent_contracts.py — validating {len(contract_files)} agent.contract.yml")
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
