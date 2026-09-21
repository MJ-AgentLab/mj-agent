"""Native entry/consumer checks. Public files only; never loads a Codex host.

Consumer inventory is reviewed with policy and CI, not a discovery exemption.
Python comments/docstrings are historical context; imports and string constants
are checked. Markdown history remains a manual review responsibility.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

CANONICAL = (
    'sql-guardrail-relax', 'runtime-skill-content-change', 'prompt-version-or-body-change',
    'biz-catalog-sync', 'mcp-server-trust-posture-change', 'declared-contract-change',
    'database-migration', 'secrets-grants-or-prod-config', 'ci-blocking-gate-toggle',
    'bulk-content-purge-or-migration',
)
ENTRIES = ('AGENTS.md', 'capabilities/AGENTS.md', 'docker/AGENTS.md',
           'src/mj_agent/AGENTS.md', 'tests/AGENTS.md')
OLD = re.compile(r'\.claude[/\\]|CLAUDE\.md|\.mcp\.json|\.migration[/\\]|\.agents\.lock\.json|'
                 r'\b(?:agents_sync|check_agents_projection|check_development_agent|check_cross_carrier|'
                 r'check_claude_skill_contracts|codex_renderers|skill_renderer)\b')


def read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError('indirect consumer')
    return path.read_text('utf-8')


def entries(root: Path) -> list[str]:
    errors = []
    for rel in ENTRIES:
        try:
            text = read(root, rel)
            if not text.strip():
                raise ValueError('empty')
            if rel == 'AGENTS.md' and not all(x in text for x in
                    ('policies/ai-agent.md', 'OWNER_APPROVAL_REQUIRED', 'BLOCKED_EXECUTION_ROUTE')):
                raise ValueError('boundary')
        except (OSError, ValueError):
            errors.append('missing native entry or boundary: ' + rel)
    for rel, heading, row in (
        ('policies/ai-agent.md', r'## §4 .*?(?=\n## |\Z)', r'^\|\s*`([a-z0-9-]+)`'),
        ('.github/PULL_REQUEST_TEMPLATE.md', r'## HITL Trigger Inventory.*?(?=\n## |\Z)', r'^- \[ \] ([a-z0-9-]+)'),
    ):
        try:
            section = re.search(heading, read(root, rel), re.S)
            names = re.findall(row, section[0], re.M) if section else []
            if len(names) != len(CANONICAL) or set(names) != set(CANONICAL):
                raise ValueError('enum')
        except (OSError, ValueError):
            errors.append('canonical approval vocabulary mismatch: ' + rel)
    return errors


def dependencies(root: Path, paths: list[str]) -> list[str]:
    errors = []
    pending = list(paths)
    visited = set()
    vocabulary_only = {'scripts/sdd/_common/native_assets.py', 'scripts/sdd/codex_hook_guard.py'}
    while pending:
        rel = pending.pop()
        if rel in visited:
            continue
        visited.add(rel)
        try:
            text = read(root, rel)
            if rel.endswith('.py'):
                tree = ast.parse(text)
                docstrings = {id(node.value) for parent in ast.walk(tree)
                              if isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                              for node in parent.body[:1] if isinstance(node, ast.Expr)
                              and isinstance(node.value, ast.Constant)}
                patterns = {id(arg) for node in ast.walk(tree) if isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == 're' and node.func.attr == 'compile'
                            for arg in node.args[:1]}
                parts = []
                for node in ast.walk(tree):
                    if rel in vocabulary_only and isinstance(node, ast.Call):
                        name = node.func.id if isinstance(node.func, ast.Name) else (
                            node.func.attr if isinstance(node.func, ast.Attribute) else '')
                        if name in {'open', 'read_text', 'read_bytes', 'readlink'}:
                            errors.append('protection vocabulary must not read files: ' + rel)
                    if isinstance(node, ast.Import):
                        parts.extend(x.name for x in node.names)
                        for name in (x.name for x in node.names):
                            candidate = name.replace('.', '/') + '.py'
                            if name.startswith('scripts.') and (root / candidate).is_file():
                                pending.append(candidate)
                    elif isinstance(node, ast.ImportFrom):
                        parts.append(node.module or '')
                        parts.extend(x.name for x in node.names)
                        module = node.module or ''
                        if module == 'scripts' or module.startswith('scripts.'):
                            for name in [module, *(module + '.' + x.name for x in node.names)]:
                                candidate = name.replace('.', '/') + '.py'
                                if (root / candidate).is_file():
                                    pending.append(candidate)
                    elif (isinstance(node, ast.Constant) and isinstance(node.value, str)
                          and id(node) not in docstrings | patterns and rel not in vocabulary_only):
                        parts.append(node.value)
                text = '\n'.join(parts)
            if OLD.search(text):
                errors.append('legacy activity reference: ' + rel)
        except (OSError, ValueError, SyntaxError):
            errors.append('invalid or absent active consumer: ' + rel)
    return errors


def inventory_errors(root: Path, paths: list[str]) -> list[str]:
    """A new workflow/script call cannot silently fall outside the reviewed list."""
    errors = []
    if len(paths) != len(set(paths)):
        errors.append('duplicate active consumer')
    for workflow in (root / '.github/workflows').glob('*.yml'):
        rel = workflow.relative_to(root).as_posix()
        if rel not in paths:
            errors.append('unregistered workflow: ' + rel)
        text = '\n'.join(line for line in read(root, rel).splitlines() if not line.lstrip().startswith('#'))
        for script in re.findall(r'scripts/[A-Za-z0-9_/.-]+\.(?:py|ps1|mjs)', text):
            if script not in paths:
                errors.append('unregistered workflow script in: ' + rel)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--surface', choices=('entries', 'consumers'), required=True)
    args = parser.parse_args()
    if args.surface == 'entries':
        errors = entries(args.root)
    else:
        try:
            inventory = json.loads(read(args.root, 'sdd/native-consumers.json'))
            paths = inventory['executable_consumers']
            if not isinstance(paths, list) or not paths or not all(isinstance(x, str) for x in paths):
                raise ValueError('inventory')
            errors = inventory_errors(args.root, paths) + dependencies(args.root, paths)
        except (OSError, ValueError, KeyError, TypeError):
            errors = ['native consumer inventory missing or invalid']
    print(json.dumps({'result': 'FAIL' if errors else 'STATIC_PASS', 'errors': errors,
                      'scope': args.surface, 'host': 'NOT_TESTED'}, ensure_ascii=False))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
