"""scripts/sdd/_common/ast_helpers.py — AST parsing helpers for python + agent validators.

Uses `ast.parse` (not `import`) because:
- Importing src/mj_agent may fail without LangChain/runtime deps installed.
- AST is safer (no side effects) + faster + mypy-strict friendly.
"""

from __future__ import annotations

import ast
from pathlib import Path


def module_path_to_file(dotted_path: str, repo_root: Path) -> Path | None:
    """Resolve dotted module path to .py file.

    Example: `src.mj_agent.tools.sql.guardrail` → `<repo_root>/src/mj_agent/tools/sql/guardrail.py`.
    Returns None if the file does not exist.
    """
    parts = dotted_path.split(".")
    candidate = repo_root.joinpath(*parts).with_suffix(".py")
    return candidate if candidate.exists() else None


def parse_module_safe(file_path: Path) -> ast.Module | None:
    """Parse Python source via ast.parse; return None on SyntaxError."""
    try:
        return ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except SyntaxError:
        return None


def extract_top_level_names(tree: ast.AST) -> set[str]:
    """Extract module-level function / class / assignment names from an AST tree."""
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def check_constant_literal(tree: ast.AST, name: str, expected_value: str) -> bool:
    """Check module has top-level `name = "expected_value"` literal string assignment."""
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == name
                and isinstance(node.value, ast.Constant)
                and node.value.value == expected_value
            ):
                return True
    return False


__all__ = [
    "module_path_to_file",
    "parse_module_safe",
    "extract_top_level_names",
    "check_constant_literal",
]
