"""Static guard for the pytest offline boundary (Epic #499 PR-0b).

This checker is intentionally standalone: it uses only the Python standard
library, parses Python with :mod:`ast`, and reads tracked source text.  It must
not import pytest or any ``mj_agent`` module, inspect environment values, or
execute the test runner.
"""

from __future__ import annotations

import ast
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_OFFLINE_ENV_NAME = "MJ_AGENT_OFFLINE_TEST"
_RUNNER_COMMAND = "uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py"
_RESERVED_EXTERNAL_FIXTURES = frozenset(
    {"live_db", "memory_db", "agent", "docker_available"}
)
_CANONICAL_FIXTURES = {
    "tests/conftest.py": frozenset({"live_db", "memory_db", "agent"}),
    "tests/bdd/conftest.py": frozenset({"docker_available"}),
}

_AGENT_INSTRUCTION_FILES = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("capabilities/AGENTS.md"),
    Path("capabilities/CLAUDE.md"),
    Path("docker/AGENTS.md"),
    Path("docker/CLAUDE.md"),
    Path("src/mj_agent/AGENTS.md"),
    Path("src/mj_agent/CLAUDE.md"),
    Path("tests/AGENTS.md"),
    Path("tests/CLAUDE.md"),
    Path("sdd/workflows/execution-loop.md"),
    Path(".github/PULL_REQUEST_TEMPLATE.md"),
)

_EXPECTED_SAFE_PARENT_ENV_NAMES = {
    "CI",
    "COLORTERM",
    "COMSPEC",
    "GITHUB_ACTIONS",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TERM",
    "TZ",
    "WINDIR",
}
_EXPECTED_RUNNER_FUNCTIONS = {
    "_safe_parent_environment": """
def _safe_parent_environment() -> dict[str, str]:
    env: dict[str, str] = {}
    for name in SAFE_PARENT_ENV_NAMES:
        value = os.environ.get(name)
        if value is not None:
            env[name] = value
    return env
""",
    "_child_environment": """
def _child_environment(profile_root: Path) -> dict[str, str]:
    env = _safe_parent_environment()
    for forbidden in _FORBIDDEN_PARENT_NAMES:
        env.pop(forbidden, None)
    directories = {
        "HOME": profile_root / "home",
        "USERPROFILE": profile_root / "home",
        "XDG_CONFIG_HOME": profile_root / "xdg-config",
        "XDG_CACHE_HOME": profile_root / "xdg-cache",
        "XDG_DATA_HOME": profile_root / "xdg-data",
        "APPDATA": profile_root / "appdata",
        "LOCALAPPDATA": profile_root / "localappdata",
        "MPLCONFIGDIR": profile_root / "matplotlib",
        "TEMP": profile_root / "tmp",
        "TMP": profile_root / "tmp",
        "TMPDIR": profile_root / "tmp",
        "PYTHONPYCACHEPREFIX": profile_root / "pycache",
    }
    for name, directory in directories.items():
        directory.mkdir(parents=True, exist_ok=True)
        env[name] = str(directory)
    env.update(
        {
            "MJ_AGENT_OFFLINE_TEST": "1",
            "MJ_AGENT_EXTERNAL_TEST_POLICY": _EXTERNAL_POLICY,
            "NO_COLOR": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    return env
""",
}

_RUNNER_REQUIRED_TEXT = (
    "SAFE_PARENT_ENV_NAMES",
    "PYTHONNOUSERSITE",
    "PYTHONPYCACHEPREFIX",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTHONPATH",
    "SKIP_POLICY_EXTERNAL_DEPENDENCY",
    "pyproject.toml",
    "uv.lock",
    "importlib.metadata",
    "pytest_asyncio.plugin",
    "pytest_bdd.plugin",
    "git",
    "ls-files",
    "FILE_ATTRIBUTE_REPARSE_POINT",
    "check_offline_boundary",
    '"-I"',
    '"-c"',
    "metadata.requires-dev.dev",
    "_EXPECTED_ADDOPTS",
    "_validate_no_reserved_fixture_override",
    "_validate_conftest_marker",
    "_validate_automatic_input_discovery",
    "_validate_test_module_automatic_inputs",
    "_validate_package_init",
    "pycache_prefix=",
)

_SENSITIVE_ENV_NAME = re.compile(
    r"(?:CREDENTIAL|TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|(?:^|_)KEY(?:_|$)|URL|URI|DSN)",
    re.IGNORECASE,
)
_PYTHON_LAUNCHER = r"(?:python(?:3(?:\.\d+)*)?(?:\.exe)?|py(?:\.exe)?)"
_DIRECT_PYTEST = re.compile(
    r"(?:"
    r"\buv\s+run(?:\s+-{1,2}[\w-]+(?:=[^\s]+)?)*(?:\s+--)?\s+"
    rf"(?:{_PYTHON_LAUNCHER}\s+(?:-[^\s]+\s+)*-m\s+)?pytest(?:\.exe)?(?![\w.-])"
    rf"|\b{_PYTHON_LAUNCHER}\s+(?:-[^\s]+\s+)*-m\s+pytest\b"
    r"|(?<![\w.-])pytest(?:\.exe)?(?![\w.-])"
    r"(?=\s+(?:(?:\.[/\\])?tests(?:[/\\\s]|$)|--\s+(?:\.[/\\])?tests|--?[A-Za-z]))"
    r")",
    re.IGNORECASE,
)
_BARE_PYTEST_COMMAND = re.compile(
    r"^\s*(?:[$>]\s*)?pytest(?:\.exe)?\s*(?:[#;].*)?$", re.IGNORECASE
)


@dataclass(frozen=True)
class Violation:
    path: Path
    message: str


def _display(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _path_is_regular_non_reparse(path: Path, repo_root: Path) -> bool:
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        return False
    current = repo_root
    try:
        root_info = current.lstat()
    except OSError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if (
        not stat.S_ISDIR(root_info.st_mode)
        or stat.S_ISLNK(root_info.st_mode)
        or getattr(root_info, "st_file_attributes", 0) & reparse
    ):
        return False
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & reparse:
            return False
    return stat.S_ISREG(info.st_mode) if relative.parts else False


def _read(path: Path, repo_root: Path, violations: list[Violation]) -> str | None:
    if not _path_is_regular_non_reparse(path, repo_root):
        violations.append(Violation(path, "required file must be regular/non-reparse inside repo"))
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        violations.append(Violation(path, f"cannot read UTF-8 source: {type(exc).__name__}"))
        return None


def _has_direct_pytest(line: str) -> bool:
    unquoted = re.sub(
        rf"(?<![\w.-])(['\"])(uv|pytest(?:\.exe)?|{_PYTHON_LAUNCHER})\1(?![\w.-])",
        lambda match: match.group(2),
        line,
        flags=re.IGNORECASE,
    )
    scrubbed = unquoted.replace(_RUNNER_COMMAND, "")
    return (
        _DIRECT_PYTEST.search(scrubbed) is not None
        or _BARE_PYTEST_COMMAND.fullmatch(scrubbed) is not None
    )


def _logical_shell_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Join shell backslash continuations while retaining the first line number."""

    logical: list[tuple[int, str]] = []
    start = 0
    pending = ""
    for line_no, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not pending and not stripped:
            continue
        if not pending:
            start = line_no
        continued = stripped.endswith("\\")
        piece = stripped[:-1].rstrip() if continued else stripped
        pending = f"{pending} {piece}".strip()
        if not continued:
            logical.append((start, pending))
            pending = ""
    if pending:
        logical.append((start, pending))
    return logical


def _parse_python(
    path: Path, source: str, violations: list[Violation]
) -> ast.Module | None:
    try:
        return ast.parse(source, filename=path.as_posix())
    except SyntaxError as exc:
        violations.append(Violation(path, f"cannot parse Python AST: {exc.msg}"))
        return None


def _dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _literal_string_collection(node: ast.AST) -> set[str] | None:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    values: set[str] = set()
    for item in node.elts:
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            return None
        values.add(item.value)
    return values


def _assignment_pairs(target: ast.AST, value: ast.AST) -> list[tuple[str, ast.AST]]:
    if isinstance(target, ast.Name):
        return [(target.id, value)]
    if isinstance(target, ast.Attribute) and (name := _dotted_name(target)):
        return [(name, value)]
    if (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and len(target.elts) == len(value.elts)
    ):
        pairs: list[tuple[str, ast.AST]] = []
        for target_item, value_item in zip(target.elts, value.elts, strict=True):
            pairs.extend(_assignment_pairs(target_item, value_item))
        return pairs
    return []


class _TopLevelEffectVisitor(ast.NodeVisitor):
    """Collect import-time nodes without descending into deferred function bodies."""

    def __init__(self) -> None:
        self.nodes: list[ast.AST] = []

    def generic_visit(self, node: ast.AST) -> None:
        self.nodes.append(node)
        super().generic_visit(node)

    def _visit_definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.nodes.append(node)
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.visit(node.args)
        if node.returns is not None:
            self.visit(node.returns)
        for parameter in getattr(node, "type_params", ()):
            self.visit(parameter)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_definition(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        self.nodes.append(node)
        self.visit(node.args)


def _automatic_effect_nodes(tree: ast.Module, *, top_level_only: bool) -> list[ast.AST]:
    if not top_level_only:
        return list(ast.walk(tree))
    visitor = _TopLevelEffectVisitor()
    visitor.visit(tree)
    nodes = list(visitor.nodes)
    definitions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda] = {
        node.name: node
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if isinstance(node.value, ast.Lambda):
                for target in targets:
                    for name in _bound_names(target):
                        definitions[name] = node.value

    aliases = set(definitions)
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for name, value in _assignment_pairs(target, node.value):
                    source = _dotted_name(value)
                    if source in aliases and name not in aliases:
                        aliases.add(name)
                        definitions[name] = definitions[source]
                        changed = True

    expanded: set[int] = set()
    while True:
        calls = [
            node
            for node in nodes
            if isinstance(node, ast.Call) and _dotted_name(node.func) in aliases
        ]
        pending = [call for call in calls if id(definitions[_dotted_name(call.func)]) not in expanded]
        if not pending:
            break
        for call in pending:
            function = definitions[_dotted_name(call.func)]
            expanded.add(id(function))
            body = [function.body] if isinstance(function, ast.Lambda) else function.body
            for statement in body:
                nodes.extend(ast.walk(statement))
    return nodes


def _has_top_level_policy_skip(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    executable = list(function.body)
    if (
        executable
        and isinstance(executable[0], ast.Expr)
        and isinstance(executable[0].value, ast.Constant)
        and isinstance(executable[0].value.value, str)
    ):
        executable = executable[1:]
    if len(executable) != 1:
        return False
    statement = executable[0]
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return False
    call = statement.value
    if _dotted_name(call.func) != "pytest.skip" or len(call.args) != 1 or call.keywords:
        return False
    reason = call.args[0]
    return (
        isinstance(reason, ast.Constant)
        and isinstance(reason.value, str)
        and reason.value.startswith("SKIP_POLICY_EXTERNAL_DEPENDENCY:")
    )


def _pytest_callable_references(tree: ast.Module) -> tuple[set[str], set[str]]:
    fixture_references = {"pytest.fixture"}
    mark_references = {"pytest.mark"}
    effect_nodes = _automatic_effect_nodes(tree, top_level_only=True)
    for node in effect_nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest":
                    pytest_name = alias.asname or alias.name
                    fixture_references.add(f"{pytest_name}.fixture")
                    mark_references.add(f"{pytest_name}.mark")
        elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
            for alias in node.names:
                if alias.name == "fixture":
                    fixture_references.add(alias.asname or alias.name)
                elif alias.name == "mark":
                    mark_references.add(alias.asname or alias.name)

    parametrize_references = {
        f"{reference}.parametrize" for reference in mark_references
    }
    changed = True
    while changed:
        changed = False
        for node in effect_nodes:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for name, value in _assignment_pairs(target, node.value):
                    dotted = _dotted_name(value)
                    before = (
                        len(fixture_references),
                        len(mark_references),
                        len(parametrize_references),
                    )
                    if dotted in fixture_references:
                        fixture_references.add(name)
                    if dotted in mark_references:
                        mark_references.add(name)
                        parametrize_references.add(f"{name}.parametrize")
                    if dotted in parametrize_references:
                        parametrize_references.add(name)
                    after = (
                        len(fixture_references),
                        len(mark_references),
                        len(parametrize_references),
                    )
                    changed = changed or before != after
    return fixture_references, parametrize_references


def _has_dynamic_pytest_factory_access(
    tree: ast.Module,
    fixture_references: set[str],
    parametrize_references: set[str],
) -> bool:
    pytest_roots = {
        reference.removesuffix(".fixture")
        for reference in fixture_references
        if reference.endswith(".fixture")
    }
    mark_roots = {
        reference.removesuffix(".parametrize")
        for reference in parametrize_references
        if reference.endswith(".parametrize")
    }
    for node in _automatic_effect_nodes(tree, top_level_only=True):
        if not isinstance(node, ast.Call) or _dotted_name(node.func) != "getattr":
            continue
        if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant):
            continue
        attribute = node.args[1].value
        base = _dotted_name(node.args[0])
        if (attribute in {"fixture", "mark"} and base in pytest_roots) or (
            attribute == "parametrize" and base in mark_roots
        ):
            return True
    return False


def _fixture_export(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    references: set[str],
) -> tuple[bool, str | None]:
    for decorator in function.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if _dotted_name(target) not in references:
            continue
        if not isinstance(decorator, ast.Call):
            return True, function.name
        name_keywords = [keyword for keyword in decorator.keywords if keyword.arg == "name"]
        if not name_keywords:
            return True, function.name
        if len(name_keywords) != 1:
            return True, None
        value = name_keywords[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return True, value.value
        return True, None
    return False, None


def _bound_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Starred):
        return _bound_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_bound_names(item) for item in target.elts))
    return set()


def _contains_fixture_call(node: ast.AST, references: set[str]) -> bool:
    return any(
        isinstance(candidate, ast.Call) and _dotted_name(candidate.func) in references
        for candidate in ast.walk(node)
    )


def _parametrize_names(call: ast.Call) -> tuple[set[str], bool]:
    values = list(call.args[:1])
    values.extend(
        keyword.value for keyword in call.keywords if keyword.arg == "argnames"
    )
    if len(values) != 1 or any(keyword.arg is None for keyword in call.keywords):
        return set(), True
    value = values[0]
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        names = {item.strip() for item in value.value.split(",") if item.strip()}
        return names, not bool(names)
    if isinstance(value, (ast.List, ast.Tuple)) and all(
        isinstance(item, ast.Constant) and isinstance(item.value, str)
        for item in value.elts
    ):
        names = {
            item.value
            for item in value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }
        return names, not bool(names)
    return set(), True


def _has_pytest_plugins_binding(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "pytest_plugins":
            return True
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.rsplit(".", 1)[-1]
                if bound == "pytest_plugins" or alias.name == "*":
                    return True
    return False


def _has_dynamic_pytest_plugin_loading(tree: ast.Module) -> bool:
    forbidden_attributes = {
        "consider_conftest",
        "consider_module",
        "get_plugin_manager",
        "import_plugin",
        "load_setuptools_entrypoints",
        "register",
    }
    forbidden_names = {
        "pluggy.PluginManager",
        "pytest.PytestPluginManager",
        "pytest.PytestPluginManager.parse_hookimpl_opts",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted_name(node.func)
        if dotted in forbidden_names or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden_attributes
        ):
            return True
    return False


def _fixture_override_details(
    tree: ast.Module,
    allowed: frozenset[str],
) -> tuple[list[str], bool]:
    references, parametrize_references = _pytest_callable_references(tree)
    top_level_functions = {
        id(node)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    overrides: set[str] = set()
    dynamic = _has_dynamic_pytest_factory_access(
        tree, references, parametrize_references
    )
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is not None and _contains_fixture_call(node.value, references):
                bound = set().union(*(_bound_names(target) for target in targets))
                overrides.update(bound & _RESERVED_EXTERNAL_FIXTURES)
    for candidate in ast.walk(tree):
        if isinstance(candidate, ast.Call) and _dotted_name(candidate.func) in references:
            fixture_names = [
                keyword for keyword in candidate.keywords if keyword.arg == "name"
            ]
            if len(fixture_names) > 1 or any(
                keyword.arg is None for keyword in candidate.keywords
            ):
                dynamic = True
            elif fixture_names:
                value = fixture_names[0].value
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    dynamic = True
                elif value.value in _RESERVED_EXTERNAL_FIXTURES:
                    overrides.add(value.value)
        if isinstance(candidate, ast.Call) and (
            _dotted_name(candidate.func) in parametrize_references
            or _dotted_name(candidate.func).endswith(".parametrize")
        ):
            parameter_names, names_dynamic = _parametrize_names(candidate)
            overrides.update(parameter_names & _RESERVED_EXTERNAL_FIXTURES)
            dynamic = dynamic or names_dynamic
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        is_fixture, exported = _fixture_export(candidate, references)
        if not is_fixture:
            continue
        if exported is None:
            dynamic = True
        elif exported in _RESERVED_EXTERNAL_FIXTURES and (
            exported not in allowed
            or candidate.name != exported
            or id(candidate) not in top_level_functions
        ):
            overrides.add(exported)
    return sorted(overrides), dynamic


def _exact_offline_assignment(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return False
    target = node.targets[0]
    return (
        isinstance(target, ast.Subscript)
        and _dotted_name(target.value) == "os.environ"
        and isinstance(target.slice, ast.Constant)
        and target.slice.value == _OFFLINE_ENV_NAME
        and isinstance(node.value, ast.Constant)
        and node.value.value == "1"
    )


def _environment_references(tree: ast.Module) -> tuple[set[str], set[str]]:
    mappings = {"os.environ", "os.environb"}
    calls = {"os.getenv", "os.getenvb", "os.putenv", "os.unsetenv"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    name = alias.asname or alias.name
                    mappings.update({f"{name}.environ", f"{name}.environb"})
                    calls.update(
                        {f"{name}.getenv", f"{name}.getenvb", f"{name}.putenv", f"{name}.unsetenv"}
                    )
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                name = alias.asname or alias.name
                if alias.name in {"environ", "environb"}:
                    mappings.add(name)
                elif alias.name in {"getenv", "getenvb", "putenv", "unsetenv"}:
                    calls.add(name)

    changed = True
    while changed:
        changed = False
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for name, value in _assignment_pairs(target, node.value):
                    dotted = _dotted_name(value)
                    before = (len(mappings), len(calls))
                    if dotted in mappings:
                        mappings.add(name)
                    if dotted in calls:
                        calls.add(name)
                    changed = changed or before != (len(mappings), len(calls))
    return mappings, calls


def _check_conftest_environment(
    path: Path,
    tree: ast.Module,
    *,
    canonical_root: bool | None,
    violations: list[Violation],
    top_level_only: bool = False,
    strict_imports: bool = True,
) -> int | None:
    exact = [node for node in tree.body if _exact_offline_assignment(node)]
    if canonical_root is True and len(exact) != 1:
        violations.append(
            Violation(path, f'must set os.environ["{_OFFLINE_ENV_NAME}"] = "1" exactly once')
        )
    if canonical_root is False and exact:
        violations.append(Violation(path, "only the root conftest may set offline mode"))

    allowed_nodes: set[int] = set()
    if canonical_root is True and len(exact) == 1:
        allowed_nodes.update(id(node) for node in ast.walk(exact[0]))
    mappings, calls = _environment_references(tree)
    for node in _automatic_effect_nodes(tree, top_level_only=top_level_only):
        if id(node) in allowed_nodes:
            continue
        if strict_imports and isinstance(node, ast.Import) and any(
            alias.name == "os" and (canonical_root is not True or alias.asname is not None)
            for alias in node.names
        ):
            violations.append(
                Violation(path, "automatic pytest input may not import/alias environment APIs")
            )
        elif strict_imports and isinstance(node, ast.ImportFrom) and node.module == "os":
            violations.append(
                Violation(path, "automatic pytest input may not import environment APIs directly")
            )
        elif isinstance(node, (ast.Attribute, ast.Name)) and any(
            _dotted_name(node) == reference or _dotted_name(node).startswith(f"{reference}.")
            for reference in mappings
        ):
            violations.append(
                Violation(path, "automatic pytest input may not read or mutate process environment")
            )
        elif isinstance(node, ast.Call) and _dotted_name(node.func) in calls:
            violations.append(
                Violation(path, "automatic pytest input may not read environment values")
            )
        elif (
            isinstance(node, ast.Name) and node.id == "OFFLINE_TEST_ENV"
        ) or (
            isinstance(node, ast.Constant)
            and node.value in {_OFFLINE_ENV_NAME, _OFFLINE_ENV_NAME.encode()}
        ):
            violations.append(Violation(path, "automatic pytest input may not override offline mode"))
    return exact[0].lineno if canonical_root is True and len(exact) == 1 else None


def _check_automatic_input_discovery(
    path: Path,
    tree: ast.Module,
    violations: list[Violation],
    *,
    top_level_only: bool = False,
    include_path_discovery: bool = True,
) -> None:
    def is_env_path(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and (
                (normalized := node.value.replace("\\", "/").rstrip("/")) == ".env"
                or normalized.endswith("/.env")
            )
        )

    forbidden_calls = {
        "dotenv.find_dotenv",
        "dotenv.load_dotenv",
        "find_dotenv",
        "load_dotenv",
    }
    path_call_attributes = {"absolute", "cwd", "expanduser", "getcwd", "home", "resolve"}
    dynamic_calls = {
        "__import__",
        "compile",
        "eval",
        "exec",
        "importlib.import_module",
        "runpy.run_module",
    }
    for node in _automatic_effect_nodes(tree, top_level_only=top_level_only):
        if (
            isinstance(node, ast.Import)
            and any(
                alias.name == "dotenv" or alias.name.startswith("dotenv.")
                for alias in node.names
            )
        ) or (
            isinstance(node, ast.ImportFrom)
            and (node.module == "dotenv" or (node.module or "").startswith("dotenv."))
        ):
            violations.append(Violation(path, "automatic pytest input may not import dotenv"))
        elif include_path_discovery and isinstance(node, ast.Name) and node.id == "__file__":
            violations.append(Violation(path, "automatic pytest input may not discover repo paths"))
        elif isinstance(node, ast.Call) and (
            _dotted_name(node.func) in dynamic_calls
        ):
            violations.append(Violation(path, "automatic pytest input may not execute dynamic code"))
        elif isinstance(node, ast.Call) and (
            _dotted_name(node.func) in forbidden_calls
            or (
                include_path_discovery
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in path_call_attributes
            )
        ):
            violations.append(
                Violation(path, "automatic pytest input may not discover dotenv/repo/home paths")
            )
        elif isinstance(node, ast.Call) and any(is_env_path(item) for item in ast.walk(node)):
            violations.append(Violation(path, "automatic pytest input may not read a .env file"))
        elif (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and node.value is not None
            and is_env_path(node.value)
        ):
            violations.append(Violation(path, "automatic pytest input may not bind a .env path"))
        elif (
            include_path_discovery
            and isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and is_env_path(node)
        ):
            violations.append(Violation(path, "automatic pytest input may not name a .env file"))


def _module_is_docstring_only(tree: ast.Module) -> bool:
    return not tree.body or (
        len(tree.body) == 1
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    )


def _check_canonical_conftest_bindings(
    path: Path,
    tree: ast.Module,
    *,
    require_os: bool,
    violations: list[Violation],
) -> None:
    bindings: dict[str, list[tuple[str, str | None]]] = {"os": [], "pytest": []}
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                if bound in bindings:
                    bindings[bound].append((alias.name, alias.asname))
        elif isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                bound = alias.asname or alias.name
                if bound in bindings:
                    bindings[bound].append((f"{statement.module}.{alias.name}", alias.asname))
        elif (
            isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and statement.name in bindings
        ):
            bindings[statement.name].append((type(statement).__name__, None))

    expected_os = [("os", None)] if require_os else []
    if bindings["os"] != expected_os or bindings["pytest"] != [("pytest", None)]:
        violations.append(
            Violation(path, "canonical conftest must keep exact unaliased os/pytest bindings")
        )

    policy_roots = set(bindings)
    effect_nodes = _automatic_effect_nodes(tree, top_level_only=True)
    changed = True
    while changed:
        changed = False
        for node in effect_nodes:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for name, value in _assignment_pairs(target, node.value):
                    if _dotted_name(value) in policy_roots and name not in policy_roots:
                        policy_roots.add(name)
                        changed = True

    mutated = False
    for node in ast.walk(tree):
        if (
            (
                isinstance(node, ast.Name)
                and node.id in policy_roots
                and isinstance(node.ctx, (ast.Store, ast.Del))
            )
            or (
                isinstance(node, ast.Attribute)
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and _dotted_name(node).split(".", 1)[0] in policy_roots
            )
            or (
                isinstance(node, ast.Call)
                and _dotted_name(node.func) in {"setattr", "delattr"}
                and node.args
                and _dotted_name(node.args[0]) in policy_roots
            )
        ):
            mutated = True
    if mutated:
        violations.append(Violation(path, "canonical conftest may not rebind os/pytest policy APIs"))


def _check_unconditional_fixture_skips(
    path: Path,
    tree: ast.Module,
    required: set[str],
    violations: list[Violation],
) -> None:
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for name in sorted(required):
        matches = [function for function in functions if function.name == name]
        rebound = False
        for statement in tree.body:
            if isinstance(statement, ast.Assign):
                rebound = rebound or any(
                    name in _bound_names(target) for target in statement.targets
                )
            elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
                rebound = rebound or name in _bound_names(statement.target)
            elif isinstance(statement, (ast.ClassDef,)):
                rebound = rebound or statement.name == name
            elif isinstance(statement, (ast.Import, ast.ImportFrom)):
                rebound = rebound or any(
                    (alias.asname or alias.name.rsplit(".", 1)[-1]) == name
                    for alias in statement.names
                )
        if len(matches) != 1 or rebound:
            violations.append(Violation(path, f"missing policy-gated fixture: {name}"))
            continue
        function = matches[0]
        args = function.args
        signature_is_empty = (
            not args.posonlyargs
            and not args.args
            and args.vararg is None
            and not args.kwonlyargs
            and args.kwarg is None
            and not args.defaults
            and not args.kw_defaults
        )
        decorator_is_exact = False
        if len(function.decorator_list) == 1:
            decorator = function.decorator_list[0]
            decorator_is_exact = (
                isinstance(decorator, ast.Call)
                and _dotted_name(decorator.func) == "pytest.fixture"
                and not decorator.args
                and len(decorator.keywords) == 1
                and decorator.keywords[0].arg == "scope"
                and isinstance(decorator.keywords[0].value, ast.Constant)
                and decorator.keywords[0].value.value == "session"
            )
        return_is_none = (
            isinstance(function.returns, ast.Constant) and function.returns.value is None
        )
        if (
            isinstance(function, ast.AsyncFunctionDef)
            or not signature_is_empty
            or not decorator_is_exact
            or not return_is_none
        ):
            violations.append(
                Violation(path, f"{name} must remain the exact static session-skip fixture")
            )
        elif not _has_top_level_policy_skip(function):
            violations.append(
                Violation(
                    path,
                    f"{name} must unconditionally use SKIP_POLICY_EXTERNAL_DEPENDENCY",
                )
            )


def _check_conftest(repo_root: Path, violations: list[Violation]) -> None:
    path = repo_root / "tests" / "conftest.py"
    source = _read(path, repo_root, violations)
    if source is None:
        return
    tree = _parse_python(path, source, violations)
    if tree is None:
        return

    _check_automatic_input_discovery(path, tree, violations)
    _check_canonical_conftest_bindings(
        path, tree, require_os=True, violations=violations
    )

    first_mj_agent_import: int | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            if any(name == "mj_agent" or name.startswith("mj_agent.") for name in modules):
                first_mj_agent_import = min(first_mj_agent_import or node.lineno, node.lineno)
    offline_line = _check_conftest_environment(
        path, tree, canonical_root=True, violations=violations
    )
    if (
        offline_line is not None
        and first_mj_agent_import is not None
        and offline_line >= first_mj_agent_import
    ):
        violations.append(Violation(path, "offline mode must be set before every mj_agent import"))

    _check_unconditional_fixture_skips(
        path, tree, {"live_db", "memory_db", "agent"}, violations
    )


def _check_bdd_conftest(repo_root: Path, violations: list[Violation]) -> None:
    path = repo_root / "tests" / "bdd" / "conftest.py"
    source = _read(path, repo_root, violations)
    if source is None:
        return
    tree = _parse_python(path, source, violations)
    if tree is not None:
        _check_automatic_input_discovery(path, tree, violations)
        _check_canonical_conftest_bindings(
            path, tree, require_os=False, violations=violations
        )
        _check_conftest_environment(
            path, tree, canonical_root=False, violations=violations
        )
        _check_unconditional_fixture_skips(path, tree, {"docker_available"}, violations)


def _check_test_python_boundaries(repo_root: Path, violations: list[Violation]) -> None:
    tests_root = repo_root / "tests"
    def record_walk_error(error: OSError) -> None:
        path = Path(error.filename) if error.filename else tests_root
        violations.append(Violation(path, "cannot inspect test directory"))

    for current, directories, files in os.walk(
        tests_root, followlinks=False, onerror=record_walk_error
    ):
        safe_directories: list[str] = []
        for name in sorted(directories):
            candidate = Path(current) / name
            try:
                info = candidate.lstat()
            except OSError:
                violations.append(Violation(candidate, "cannot inspect test directory"))
                continue
            attributes = getattr(info, "st_file_attributes", 0)
            if (
                stat.S_ISDIR(info.st_mode)
                and not stat.S_ISLNK(info.st_mode)
                and not attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                safe_directories.append(name)
            else:
                violations.append(
                    Violation(candidate, "test directory must be regular/non-reparse")
                )
        directories[:] = safe_directories
        for name in sorted(item for item in files if item.endswith(".py")):
            path = Path(current) / name
            try:
                info = path.lstat()
            except OSError:
                violations.append(Violation(path, "cannot inspect test Python path"))
                continue
            attributes = getattr(info, "st_file_attributes", 0)
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                violations.append(Violation(path, "test Python path must be regular/non-reparse"))
                continue
            source = _read(path, repo_root, violations)
            if source is None:
                continue
            tree = _parse_python(path, source, violations)
            if tree is None:
                continue
            relative = path.relative_to(repo_root).as_posix()
            if _has_pytest_plugins_binding(tree):
                violations.append(Violation(path, "pytest_plugins binding/import is forbidden"))
            if _has_dynamic_pytest_plugin_loading(tree):
                violations.append(Violation(path, "dynamic pytest plugin loading is forbidden"))
            allowed = _CANONICAL_FIXTURES.get(relative, frozenset())
            overrides, dynamic = _fixture_override_details(tree, allowed)
            if overrides:
                violations.append(
                    Violation(path, f"reserved external fixture override: {', '.join(overrides)}")
                )
            if dynamic:
                violations.append(
                    Violation(path, "pytest fixture name must be a static reviewed string")
                )
            if name == "conftest.py" and relative not in _CANONICAL_FIXTURES:
                _check_automatic_input_discovery(path, tree, violations)
                _check_conftest_environment(path, tree, canonical_root=False, violations=violations)
            elif name == "__init__.py" and not _module_is_docstring_only(tree):
                violations.append(
                    Violation(path, "pytest package __init__.py must be empty or docstring-only")
                )
            elif name not in {"conftest.py", "__init__.py"}:
                _check_automatic_input_discovery(
                    path,
                    tree,
                    violations,
                    top_level_only=True,
                    include_path_discovery=False,
                )
                _check_conftest_environment(
                    path,
                    tree,
                    canonical_root=None,
                    violations=violations,
                    top_level_only=True,
                    strict_imports=False,
                )


def _assigns_none_to_values_key(statement: ast.stmt, key: str) -> bool:
    if not isinstance(statement, ast.Assign) or not isinstance(statement.value, ast.Constant):
        return False
    if statement.value.value is not None or len(statement.targets) != 1:
        return False
    target = statement.targets[0]
    return (
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and target.value.id == "values"
        and isinstance(target.slice, ast.Constant)
        and target.slice.value == key
    )


def _is_super_init_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    parent = node.func.value
    return (
        node.func.attr == "__init__"
        and isinstance(parent, ast.Call)
        and isinstance(parent.func, ast.Name)
        and parent.func.id == "super"
    )


def _is_exact_super_init_statement(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.Expr) or not _is_super_init_call(statement.value):
        return False
    call = statement.value
    return (
        isinstance(call, ast.Call)
        and not call.args
        and len(call.keywords) == 1
        and call.keywords[0].arg is None
        and isinstance(call.keywords[0].value, ast.Name)
        and call.keywords[0].value.id == "values"
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Call)
        and not call.func.value.args
        and not call.func.value.keywords
    )


def _is_exact_offline_condition(node: ast.AST) -> bool:
    if (
        not isinstance(node, ast.Compare)
        or len(node.ops) != 1
        or not isinstance(node.ops[0], ast.Eq)
        or len(node.comparators) != 1
    ):
        return False
    left = node.left
    right = node.comparators[0]
    return (
        isinstance(left, ast.Call)
        and _dotted_name(left.func) == "os.environ.get"
        and len(left.args) == 1
        and not left.keywords
        and isinstance(left.args[0], ast.Name)
        and left.args[0].id == "OFFLINE_TEST_ENV"
        and isinstance(right, ast.Constant)
        and right.value == "1"
    )


def _check_config(repo_root: Path, violations: list[Violation]) -> None:
    path = repo_root / "src" / "mj_agent" / "config.py"
    source = _read(path, repo_root, violations)
    if source is None:
        return
    tree = _parse_python(path, source, violations)
    if tree is None:
        return

    offline_constant_assignments: list[ast.Assign] = []
    settings_classes = [
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Settings"
    ]
    all_settings_definitions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "Settings"
    ]
    singleton_assignments: list[ast.Assign] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "OFFLINE_TEST_ENV"
                and isinstance(node.value, ast.Constant)
                and node.value.value == _OFFLINE_ENV_NAME
            ):
                offline_constant_assignments.append(node)
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "settings"
                and isinstance(node.value, ast.Call)
                and _dotted_name(node.value.func) == "Settings"
                and not node.value.args
                and not node.value.keywords
            ):
                singleton_assignments.append(node)

    offline_stores = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "OFFLINE_TEST_ENV"
        and isinstance(node.ctx, (ast.Store, ast.Del))
    ]
    if len(offline_constant_assignments) != 1 or len(offline_stores) != 1:
        violations.append(
            Violation(
                path,
                f'OFFLINE_TEST_ENV must be uniquely bound to literal "{_OFFLINE_ENV_NAME}"',
            )
        )
    if (
        len(settings_classes) != 1
        or len(all_settings_definitions) != 1
        or (settings_classes and id(settings_classes[0]) != id(all_settings_definitions[0]))
    ):
        violations.append(Violation(path, "Settings must be one unique top-level class"))
    if not settings_classes:
        return
    settings_class = settings_classes[-1]
    if settings_class.decorator_list:
        violations.append(Violation(path, "Settings class may not have runtime decorators"))

    dotenv_import = any(
        (
            isinstance(node, ast.Import)
            and any(alias.name == "dotenv" or alias.name.startswith("dotenv.") for alias in node.names)
        )
        or (
            isinstance(node, ast.ImportFrom)
            and (node.module == "dotenv" or (node.module or "").startswith("dotenv."))
        )
        for node in ast.walk(tree)
    )
    dotenv_call = any(
        isinstance(node, ast.Call)
        and (
            _dotted_name(node.func) in {
                "dotenv.find_dotenv",
                "dotenv.load_dotenv",
                "find_dotenv",
                "load_dotenv",
            }
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"find_dotenv", "load_dotenv"}
            )
        )
        for node in ast.walk(tree)
    )
    if dotenv_import or dotenv_call:
        violations.append(Violation(path, "config may not execute dotenv outside Settings sources"))

    source_hooks = [
        node
        for node in ast.walk(settings_class)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {"settings_customise_sources", "customise_sources"}
    ]
    if source_hooks:
        violations.append(Violation(path, "Settings source hooks bypass the unique construction seam"))

    settings_name_stores = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "settings"
        and isinstance(node.ctx, (ast.Store, ast.Del))
    ]
    settings_class_stores = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Name)
            and node.id == "Settings"
            and isinstance(node.ctx, (ast.Store, ast.Del))
        )
        or (
            isinstance(node, ast.Attribute)
            and _dotted_name(node).startswith("Settings.")
            and isinstance(node.ctx, (ast.Store, ast.Del))
        )
    ]
    named_rebindings = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {"Settings", "settings"}
    ]
    settings_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _dotted_name(node.func) == "Settings"
    ]
    singleton_call_ids = {id(node.value) for node in singleton_assignments}
    if (
        len(singleton_assignments) != 1
        or len(settings_name_stores) != 1
        or settings_class_stores
        or named_rebindings
        or len(settings_calls) != 1
        or id(settings_calls[0]) not in singleton_call_ids
    ):
        violations.append(
            Violation(path, "module singleton and Settings class must not be rebound or reconstructed")
        )

    init_methods = [
        node
        for node in settings_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__init__"
    ]
    all_init_methods = [
        node
        for node in ast.walk(settings_class)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__init__"
    ]
    init_rebindings = [
        node
        for node in ast.walk(settings_class)
        if isinstance(node, ast.Name)
        and node.id == "__init__"
        and isinstance(node.ctx, (ast.Store, ast.Del))
    ]
    if (
        len(init_methods) != 1
        or len(all_init_methods) != 1
        or init_rebindings
        or not isinstance(init_methods[0], ast.FunctionDef)
        or init_methods[0].decorator_list
    ):
        violations.append(Violation(path, "Settings.__init__ must be the unique construction seam"))
    else:
        init = init_methods[0]
        args = init.args
        signature_is_exact = (
            not args.posonlyargs
            and len(args.args) == 1
            and args.args[0].arg == "self"
            and args.vararg is None
            and not args.kwonlyargs
            and args.kwarg is not None
            and args.kwarg.arg == "values"
            and not args.defaults
            and not args.kw_defaults
        )
        if not signature_is_exact:
            violations.append(Violation(path, "Settings.__init__ seam must receive **values"))
        executable = list(init.body)
        if (
            executable
            and isinstance(executable[0], ast.Expr)
            and isinstance(executable[0].value, ast.Constant)
            and isinstance(executable[0].value.value, str)
        ):
            executable = executable[1:]
        if len(executable) != 2 or not isinstance(executable[0], ast.If):
            violations.append(
                Violation(
                    path,
                    "Settings.__init__ must contain only the offline source branch and exact super call",
                )
            )
        else:
            branch = executable[0]
            branch_is_exact = (
                _is_exact_offline_condition(branch.test)
                and not branch.orelse
                and len(branch.body) == 2
                and all(
                    sum(
                        _assigns_none_to_values_key(statement, key)
                        for statement in branch.body
                    )
                    == 1
                    for key in ("_env_file", "_secrets_dir")
                )
                and all(
                    any(
                        _assigns_none_to_values_key(statement, key)
                        for key in ("_env_file", "_secrets_dir")
                    )
                    for statement in branch.body
                )
            )
            if not branch_is_exact:
                violations.append(
                    Violation(path, "offline branch must be exactly the two filesystem-source None writes")
                )
            if not _is_exact_super_init_statement(executable[1]):
                violations.append(
                    Violation(path, "Settings.__init__ must end with exact super().__init__(**values)")
                )


def _check_runner(repo_root: Path, violations: list[Violation]) -> None:
    path = repo_root / "scripts" / "sdd" / "run_offline_pytest.py"
    source = _read(path, repo_root, violations)
    if source is None:
        return
    tree = _parse_python(path, source, violations)
    if tree is None:
        return

    for token in _RUNNER_REQUIRED_TEXT:
        if token not in source:
            violations.append(Violation(path, f"runner contract token is missing: {token}"))

    banned_fragments = (
        "os.environ.copy(",
        "dict(os.environ",
        "os.environ.items(",
        "os.environ.values(",
    )
    for fragment in banned_fragments:
        if fragment in source:
            violations.append(Violation(path, f"runner may inherit/read unbounded environment: {fragment}"))

    allowlist_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "SAFE_PARENT_ENV_NAMES"
    ]
    allowlist_stores = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "SAFE_PARENT_ENV_NAMES"
        and isinstance(node.ctx, (ast.Store, ast.Del))
    ]
    allowlist = (
        _literal_string_collection(allowlist_assignments[0].value)
        if len(allowlist_assignments) == 1 and len(allowlist_stores) == 1
        else None
    )
    if allowlist is None:
        violations.append(Violation(path, "SAFE_PARENT_ENV_NAMES must be a literal closed collection"))
    else:
        if allowlist != _EXPECTED_SAFE_PARENT_ENV_NAMES:
            violations.append(
                Violation(path, "SAFE_PARENT_ENV_NAMES differs from the reviewed OS carrier set")
            )
        unsafe = sorted(name for name in allowlist if _SENSITIVE_ENV_NAME.search(name))
        if unsafe:
            violations.append(
                Violation(path, f"sensitive-looking names in parent allowlist: {', '.join(unsafe)}")
            )

    function_nodes: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_nodes.setdefault(node.name, []).append(node)
    for function_name, expected_source in _EXPECTED_RUNNER_FUNCTIONS.items():
        candidates = function_nodes.get(function_name, [])
        all_candidates = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        ]
        rebindings = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and node.id == function_name
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ]
        expected = ast.parse(expected_source).body[0]
        if (
            len(candidates) != 1
            or len(all_candidates) != 1
            or rebindings
            or ast.dump(candidates[0], include_attributes=False)
            != ast.dump(expected, include_attributes=False)
        ):
            violations.append(
                Violation(path, f"{function_name} differs from the reviewed closed environment builder")
            )

    environment_attributes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and _dotted_name(node) in {"os.environ", "os.environb"}
    ]
    if len(environment_attributes) != 1 or _dotted_name(environment_attributes[0]) != "os.environ":
        violations.append(
            Violation(path, "runner may access parent environment only at the reviewed allowlist lookup")
        )
    unreviewed_environment_api = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and _dotted_name(node)
        in {"os.getenv", "os.getenvb", "os.putenv", "os.unsetenv", "os.environb"}
    ]
    if unreviewed_environment_api:
        violations.append(
            Violation(path, "runner may not reference unreviewed parent-environment APIs")
        )

    os_bindings: list[tuple[str, str | None]] = []
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if (alias.asname or alias.name.split(".", 1)[0]) == "os":
                    os_bindings.append((alias.name, alias.asname))
        elif isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                if (alias.asname or alias.name) == "os":
                    os_bindings.append((f"{statement.module}.{alias.name}", alias.asname))
    os_mutations = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Name)
            and node.id == "os"
            and isinstance(node.ctx, (ast.Store, ast.Del))
        )
        or (
            isinstance(node, ast.Attribute)
            and _dotted_name(node).startswith("os.")
            and isinstance(node.ctx, (ast.Store, ast.Del))
        )
        or (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == "os"
        )
    ]
    if os_bindings != [("os", None)] or os_mutations:
        violations.append(Violation(path, "runner must keep the reviewed os module binding immutable"))

    for candidate in ast.walk(tree):
        if isinstance(candidate, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in candidate.names]
                if isinstance(candidate, ast.Import)
                else [candidate.module or ""]
            )
            if any(
                name == "pytest"
                or name.startswith("mj_agent")
                or name == "dotenv"
                or name.startswith("dotenv.")
                for name in names
            ):
                violations.append(
                    Violation(path, "runner must launch pytest as a child, never import pytest/application")
                )
        if isinstance(candidate, ast.Call) and _dotted_name(candidate.func) in {
            "find_dotenv",
            "load_dotenv",
            "dotenv.find_dotenv",
            "dotenv.load_dotenv",
            "os.getenv",
            "os.getenvb",
            "os.putenv",
            "os.unsetenv",
        }:
            violations.append(Violation(path, "runner may not execute unreviewed environment discovery"))

    functions = {
        node.name: ast.get_source_segment(source, node) or ""
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    function_tokens = {
        "_pytest_arguments": ("_tracked_paths", "_expanded_target", "_validated_ignore"),
        "_expanded_target": (
            "_validate_tracked_file",
            "_validate_no_pytest_plugins",
            "_validate_no_reserved_fixture_override",
            "_validate_test_module_automatic_inputs",
            "_validate_conftest_chain",
            "_validate_package_chain",
        ),
        "_validate_conftest_chain": (
            "_validate_no_reserved_fixture_override",
            "_validate_conftest_marker",
            "_validate_automatic_input_discovery",
        ),
        "_validate_package_chain": (
            "_validate_package_init",
        ),
        "_pytest_command": (
            '"-I"',
            '"-X"',
            "pycache_prefix=",
            '"-m"',
            '"pytest"',
            '"-c"',
            '"pyproject.toml"',
        ),
        "main": (
            "_assert_repo_root_non_reparse",
            "_assert_boundary_green",
            "_verified_plugin_modules",
            "_pytest_arguments",
            "_child_environment",
            "_pytest_command",
            "env=env",
        ),
    }
    for function_name, tokens in function_tokens.items():
        body = functions.get(function_name)
        if body is None:
            violations.append(Violation(path, f"runner function is missing: {function_name}"))
            continue
        for token in tokens:
            if token not in body:
                violations.append(
                    Violation(path, f"{function_name} does not enforce runner token: {token}")
                )


def _check_ci_direct_entries(
    path: Path, source: str, violations: list[Violation]
) -> None:
    lines = source.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*?)\s*$", line)
        if match is None:
            continue
        commands: list[str] = []
        value = match.group(2)
        if re.fullmatch(r"[|>](?:[1-9][-+]?|[-+]?[1-9]?)(?:\s+#.*)?", value):
            base_indent = len(match.group(1))
            for continuation in lines[index + 1 :]:
                if (
                    continuation.strip()
                    and len(continuation) - len(continuation.lstrip()) <= base_indent
                ):
                    break
                if continuation.strip() and not continuation.lstrip().startswith("#"):
                    commands.append(continuation.strip())
        else:
            commands.append(value)
        logical_commands = _logical_shell_lines(commands)
        if any(_has_direct_pytest(command) for _, command in logical_commands):
            violations.append(Violation(path, "CI still contains a direct pytest entry"))


def _check_ci(repo_root: Path, violations: list[Violation]) -> None:
    path = repo_root / ".github" / "workflows" / "ci.yml"
    source = _read(path, repo_root, violations)
    if source is None:
        return
    expected_steps = {
        "Tests (unit + eval + integration; smoke + contract + bdd excluded by default)": (
            f"{_RUNNER_COMMAND} tests --ignore tests/bdd"
        ),
        "'BDD scenarios (BLOCKING per Stage C C-a; hardened offline runner)'": (
            f"{_RUNNER_COMMAND} tests/bdd -q"
        ),
        # Renamed at #499 PR-0c: the band stopped being a policy skip and became real
        # offline assertions over synthetic snapshot fixtures. The binding this gate
        # enforces — that the step runs through the hardened runner — is unchanged.
        "Contract tests (offline; synthetic snapshot fixtures)": (
            f"{_RUNNER_COMMAND} tests/contract -m contract"
        ),
    }
    lines = source.splitlines()
    step_runs: dict[str, list[str]] = {}
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)-\s+name:\s*(.*?)\s*$", line)
        if match is None:
            continue
        indent = len(match.group(1))
        name = match.group(2)
        runs: list[str] = []
        for continuation in lines[index + 1 :]:
            stripped = continuation.strip()
            continuation_indent = len(continuation) - len(continuation.lstrip())
            if stripped and continuation_indent <= indent:
                break
            run_match = re.match(r"^\s*run:\s*(.*?)\s*$", continuation)
            if run_match is not None:
                runs.append(run_match.group(1))
        step_runs.setdefault(name, []).extend(runs)

    for name, command in expected_steps.items():
        if step_runs.get(name) != [command]:
            violations.append(Violation(path, f"CI step is not bound to the runner: {name}"))
    runner_steps = re.findall(rf"(?m)^\s*run:\s*{re.escape(_RUNNER_COMMAND)}(?:\s|$)", source)
    if len(runner_steps) != len(expected_steps):
        violations.append(Violation(path, "CI must contain exactly three offline pytest runner steps"))
    workflow_root = repo_root / ".github" / "workflows"
    workflow_paths = sorted(
        set(workflow_root.glob("*.yml")) | set(workflow_root.glob("*.yaml"))
    )
    for workflow_path in workflow_paths:
        workflow_source = source if workflow_path == path else _read(
            workflow_path, repo_root, violations
        )
        if workflow_source is not None:
            _check_ci_direct_entries(workflow_path, workflow_source, violations)


def _agent_instruction_paths(repo_root: Path) -> list[Path]:
    paths = {repo_root / rel for rel in _AGENT_INSTRUCTION_FILES}
    for root in (repo_root / ".claude", repo_root / ".agents"):
        if root.is_dir():
            paths.update(root.rglob("*.md"))
    return sorted(paths)


def _check_agent_instructions(repo_root: Path, violations: list[Violation]) -> None:
    for path in _agent_instruction_paths(repo_root):
        source = _read(path, repo_root, violations)
        if source is None:
            continue
        for line_no, line in _logical_shell_lines(source.splitlines()):
            if _has_direct_pytest(line):
                violations.append(
                    Violation(path, f"line {line_no}: Agent-facing direct pytest must use the offline runner")
                )


def _check_repo_root_conftest_absent(
    repo_root: Path, violations: list[Violation]
) -> None:
    path = repo_root / "conftest.py"
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError:
        violations.append(Violation(path, "cannot prove repo-root conftest.py is absent"))
        return
    violations.append(
        Violation(path, "repo-root conftest.py is forbidden; tests/conftest.py owns offline mode")
    )


def check(repo_root: Path) -> list[Violation]:
    """Return deterministic static violations for *repo_root*."""

    violations: list[Violation] = []
    _check_repo_root_conftest_absent(repo_root, violations)
    _check_conftest(repo_root, violations)
    _check_bdd_conftest(repo_root, violations)
    _check_test_python_boundaries(repo_root, violations)
    _check_config(repo_root, violations)
    _check_runner(repo_root, violations)
    _check_ci(repo_root, violations)
    _check_agent_instructions(repo_root, violations)
    return violations


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments:
        print("check_test_offline_boundary.py: no command-line arguments are accepted", file=sys.stderr)
        return 2
    root = (repo_root or _REPO_ROOT).resolve()
    violations = check(root)
    if violations:
        print(f"OFFLINE_BOUNDARY: RED ({len(violations)} violation(s))")
        for item in violations:
            print(f"  - {_display(item.path, root)}: {item.message}")
        return 1
    print("OFFLINE_BOUNDARY: GREEN (static/AST boundary closed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
