"""Run pytest in a hardened, offline child process for Agents and CI.

Human and IDE callers may invoke pytest directly; ``tests/conftest.py`` makes
that path offline. Automation uses this stricter carrier so parent plugins,
profiles, Python-path state, credentials, and untracked collection inputs
cannot enter the child.
"""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Final

if __package__:
    from scripts.sdd.check_test_offline_boundary import check as check_offline_boundary
else:  # pragma: no cover - exercised by every script/CI invocation
    from check_test_offline_boundary import (  # type: ignore[no-redef]
        check as check_offline_boundary,
    )

_REPO_ROOT = Path(__file__).absolute().parent.parent.parent
_TESTS_ROOT = Path("tests")
_REPARSE_POINT: Final = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_OFFLINE_ENV_NAME = "MJ_AGENT_OFFLINE_TEST"
_RESERVED_EXTERNAL_FIXTURES = frozenset(
    {"live_db", "memory_db", "agent", "docker_available"}
)
_CANONICAL_FIXTURES = {
    "tests/conftest.py": frozenset({"live_db", "memory_db", "agent"}),
    "tests/bdd/conftest.py": frozenset({"docker_available"}),
}

# Closed, non-secret carrier list. Everything else is absent from subprocess
# environments; in particular no parent enumeration/copy operation is used.
SAFE_PARENT_ENV_NAMES = (
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
)

_FORBIDDEN_PARENT_NAMES = ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH")
_EXTERNAL_POLICY = "SKIP_POLICY_EXTERNAL_DEPENDENCY"
_PLUGIN_ENTRYPOINTS = {
    "pytest-asyncio": ("asyncio", "pytest_asyncio.plugin", "pytest_asyncio/plugin.py"),
    "pytest-bdd": ("pytest-bdd", "pytest_bdd.plugin", "pytest_bdd/plugin.py"),
}
_LOCK_VERIFIED_DISTRIBUTIONS = ("pytest", *_PLUGIN_ENTRYPOINTS)
_REQUIREMENT = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)(?:\[(?P<extras>[A-Za-z0-9_.,-]+)\])?(?P<specifier>[^;]*)$"
)
_EXPECTED_ADDOPTS = ("-ra", "--strict-markers", "-m", "not smoke and not contract")


class RunnerError(RuntimeError):
    """Fail-closed runner contract violation safe to show without values."""


def _dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


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


def _normalized_distribution(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _safe_parent_environment() -> dict[str, str]:
    env: dict[str, str] = {}
    for name in SAFE_PARENT_ENV_NAMES:
        value = os.environ.get(name)
        if value is not None:
            env[name] = value
    return env


def _load_toml(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as stream:
            payload = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RunnerError(f"cannot read required lock metadata: {path.name}") from exc
    if not isinstance(payload, dict):
        raise RunnerError(f"invalid lock metadata root: {path.name}")
    return payload


def _requirement_record(requirement: str) -> tuple[str, tuple[str, ...], str]:
    match = _REQUIREMENT.fullmatch(requirement.strip())
    if match is None:
        raise RunnerError("dependency-groups.dev contains an unsupported requirement")
    extras = tuple(sorted(filter(None, (match.group("extras") or "").split(","))))
    return (
        _normalized_distribution(match.group("name")),
        extras,
        match.group("specifier").strip(),
    )


def _project_dev_requirements(project: dict[str, object]) -> dict[str, tuple[tuple[str, ...], str]]:
    groups = project.get("dependency-groups")
    if not isinstance(groups, dict) or not isinstance(groups.get("dev"), list):
        raise RunnerError("pyproject.toml does not declare dependency-groups.dev")
    declared: dict[str, tuple[tuple[str, ...], str]] = {}
    for requirement in groups["dev"]:
        if not isinstance(requirement, str):
            raise RunnerError("dependency-groups.dev contains a non-string requirement")
        name, extras, specifier = _requirement_record(requirement)
        if name in declared:
            raise RunnerError("dependency-groups.dev contains a duplicate distribution")
        declared[name] = (extras, specifier)
    return declared


def _lock_requirement_record(record: object) -> tuple[str, tuple[str, ...], str]:
    if not isinstance(record, dict) or not isinstance(record.get("name"), str):
        raise RunnerError("uv.lock project dev metadata is malformed")
    extras_value = record.get("extras", [])
    if not isinstance(extras_value, list) or not all(isinstance(item, str) for item in extras_value):
        raise RunnerError("uv.lock project dev extras are malformed")
    specifier = record.get("specifier", "")
    if not isinstance(specifier, str):
        raise RunnerError("uv.lock project dev specifier is malformed")
    return (
        _normalized_distribution(record["name"]),
        tuple(sorted(extras_value)),
        specifier,
    )


def _project_name(project: dict[str, object]) -> str:
    metadata = project.get("project")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
        raise RunnerError("pyproject.toml does not declare project.name")
    return _normalized_distribution(metadata["name"])


def _locked_versions(
    project: dict[str, object], lock: dict[str, object]
) -> dict[str, str]:
    packages = lock.get("package")
    if not isinstance(packages, list):
        raise RunnerError("uv.lock does not contain a package array")

    declared = _project_dev_requirements(project)
    project_records = [
        record
        for record in packages
        if isinstance(record, dict)
        and isinstance(record.get("name"), str)
        and _normalized_distribution(record["name"]) == _project_name(project)
        and record.get("source") == {"editable": "."}
    ]
    if len(project_records) != 1:
        raise RunnerError("uv.lock must contain one editable project record")
    root_metadata = project_records[0].get("metadata")
    requires_dev = root_metadata.get("requires-dev") if isinstance(root_metadata, dict) else None
    locked_dev = requires_dev.get("dev") if isinstance(requires_dev, dict) else None
    if not isinstance(locked_dev, list):
        raise RunnerError("uv.lock lacks project metadata.requires-dev.dev")
    locked_requirements: dict[str, tuple[tuple[str, ...], str]] = {}
    for record in locked_dev:
        name, extras, specifier = _lock_requirement_record(record)
        if name in locked_requirements:
            raise RunnerError("uv.lock project dev metadata has a duplicate distribution")
        locked_requirements[name] = (extras, specifier)
    if locked_requirements != declared:
        raise RunnerError("pyproject.toml dependency-groups.dev does not match uv.lock metadata")

    wanted = {_normalized_distribution(name) for name in _LOCK_VERIFIED_DISTRIBUTIONS}
    versions: dict[str, str] = {}
    for record in packages:
        if not isinstance(record, dict):
            continue
        package_name = record.get("name")
        version = record.get("version")
        if not isinstance(package_name, str) or not isinstance(version, str):
            continue
        normalized = _normalized_distribution(package_name)
        if normalized not in wanted:
            continue
        if normalized in versions:
            raise RunnerError("uv.lock has duplicate pytest distribution records")
        if record.get("source") != {"registry": "https://pypi.org/simple"}:
            raise RunnerError("a pytest distribution is not locked to the reviewed registry")
        versions[normalized] = version
    if wanted != versions.keys():
        raise RunnerError("uv.lock is missing a required pytest distribution")
    return versions


def _pytest_config(project: dict[str, object]) -> None:
    tool = project.get("tool")
    pytest_section = tool.get("pytest") if isinstance(tool, dict) else None
    options = pytest_section.get("ini_options") if isinstance(pytest_section, dict) else None
    if not isinstance(options, dict):
        raise RunnerError("pyproject.toml lacks tool.pytest.ini_options")
    if options.get("testpaths") != ["tests"] or options.get("pythonpath") != ["src"]:
        raise RunnerError("pytest testpaths/pythonpath differ from the reviewed project roots")
    addopts = options.get("addopts")
    if not isinstance(addopts, str):
        raise RunnerError("pytest addopts must be a string")
    try:
        tokens = shlex.split(addopts, posix=True)
    except ValueError as exc:
        raise RunnerError("pytest addopts cannot be parsed safely") from exc
    if tuple(tokens) != _EXPECTED_ADDOPTS:
        raise RunnerError("pytest addopts differs from the reviewed offline selection")


def _path_is_non_reparse_beneath(root: Path, path: Path) -> bool:
    root = root.absolute()
    path = path.absolute()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in (None, *relative.parts):
        if part is not None:
            current = current / part
        try:
            info = current.lstat()
        except OSError:
            return False
        attributes = getattr(info, "st_file_attributes", 0)
        if stat.S_ISLNK(info.st_mode) or attributes & _REPARSE_POINT:
            return False
    return True


def _distribution_file_is_valid(
    distribution: importlib.metadata.Distribution, relative: str
) -> bool:
    files = distribution.files or []
    matches = [item for item in files if item.as_posix() == relative]
    if len(matches) != 1:
        return False
    path = Path(str(distribution.locate_file(matches[0]))).absolute()
    prefix = Path(sys.prefix).absolute()
    if not _path_is_non_reparse_beneath(prefix, path):
        return False
    try:
        info = path.lstat()
    except OSError:
        return False
    attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not (
        attributes & _REPARSE_POINT
    )


def _verified_plugin_modules(repo_root: Path) -> tuple[str, ...]:
    tracked = _tracked_paths(repo_root)
    _validate_tracked_file(repo_root, Path("pyproject.toml"), tracked)
    _validate_tracked_file(repo_root, Path("uv.lock"), tracked)
    project = _load_toml(repo_root / "pyproject.toml")
    lock = _load_toml(repo_root / "uv.lock")
    _pytest_config(project)
    declared = _project_dev_requirements(project)
    locked = _locked_versions(project, lock)

    distributions: dict[str, importlib.metadata.Distribution] = {}
    for name in _LOCK_VERIFIED_DISTRIBUTIONS:
        normalized = _normalized_distribution(name)
        if normalized not in declared:
            raise RunnerError(f"required pytest distribution is not project-declared: {name}")
        try:
            distribution = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise RunnerError(f"required pytest distribution is not installed: {name}") from exc
        if distribution.version != locked[normalized]:
            raise RunnerError(f"installed pytest distribution does not match uv.lock: {name}")
        distribution_root = Path(str(distribution.locate_file(""))).absolute()
        if not _path_is_non_reparse_beneath(Path(sys.prefix), distribution_root):
            raise RunnerError(f"pytest distribution is outside the active environment: {name}")
        distributions[normalized] = distribution

    modules: list[str] = []
    for name, (entrypoint_name, module, module_file) in _PLUGIN_ENTRYPOINTS.items():
        distribution = distributions[_normalized_distribution(name)]
        matches = [
            entrypoint
            for entrypoint in distribution.entry_points
            if entrypoint.group == "pytest11" and entrypoint.name == entrypoint_name
        ]
        if len(matches) != 1 or matches[0].value != module:
            raise RunnerError(f"pytest plugin entry point does not match the lock policy: {name}")
        if not _distribution_file_is_valid(distribution, module_file):
            raise RunnerError(f"pytest plugin module is not a regular installed file: {name}")
        modules.append(module)
    return tuple(modules)


def _tracked_paths(repo_root: Path) -> set[str]:
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-files",
                "-z",
                "--",
                "pyproject.toml",
                "uv.lock",
                "conftest.py",
                "tests",
            ],
            check=False,
            capture_output=True,
            env=_safe_parent_environment(),
        )
    except OSError as exc:
        raise RunnerError("cannot execute git while validating pytest targets") from exc
    if proc.returncode != 0:
        raise RunnerError("git ls-files failed while validating pytest targets")
    try:
        decoded = proc.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RunnerError("git ls-files returned non-UTF-8 paths") from exc
    tracked = {item for item in decoded.split("\0") if item}
    if not {"pyproject.toml", "uv.lock"}.issubset(tracked) or not any(
        item.startswith("tests/") for item in tracked
    ):
        raise RunnerError("git reports an incomplete tracked pytest surface")
    root_conftest = repo_root / "conftest.py"
    if root_conftest.exists() or root_conftest.is_symlink():
        raise RunnerError("repository-root conftest.py is outside the reviewed pytest boundary")
    return tracked


def _assert_repo_root_non_reparse(repo_root: Path) -> None:
    try:
        info = repo_root.lstat()
    except OSError as exc:
        raise RunnerError("pytest repository root does not exist") from exc
    attributes = getattr(info, "st_file_attributes", 0)
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) or attributes & _REPARSE_POINT:
        raise RunnerError("pytest repository root is not a regular non-reparse directory")


def _assert_non_reparse(repo_root: Path, relative: Path) -> None:
    current = repo_root
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except OSError as exc:
            raise RunnerError(f"pytest input does not exist: {relative.as_posix()}") from exc
        attributes = getattr(info, "st_file_attributes", 0)
        if stat.S_ISLNK(info.st_mode) or attributes & _REPARSE_POINT:
            raise RunnerError(f"pytest input crosses a symlink/reparse point: {relative.as_posix()}")


def _validate_tracked_file(repo_root: Path, relative: Path, tracked: set[str]) -> None:
    posix = relative.as_posix()
    if posix not in tracked:
        raise RunnerError(f"pytest input is not Git-tracked: {posix}")
    _assert_non_reparse(repo_root, relative)
    try:
        info = (repo_root / relative).lstat()
    except OSError as exc:
        raise RunnerError(f"pytest input does not exist: {posix}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise RunnerError(f"pytest input is not a regular file: {posix}")


def _validate_no_pytest_plugins(path: Path, relative: Path) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative.as_posix())
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RunnerError(f"cannot validate tracked pytest module: {relative.as_posix()}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "pytest_plugins":
            raise RunnerError(f"tracked pytest module declares pytest_plugins: {relative.as_posix()}")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.rsplit(".", 1)[-1]
                if bound == "pytest_plugins" or alias.name == "*":
                    raise RunnerError(
                        f"tracked pytest module imports pytest_plugins dynamically: "
                        f"{relative.as_posix()}"
                    )
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
            raise RunnerError(
                f"tracked pytest module loads plugins dynamically: {relative.as_posix()}"
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
        names = [keyword for keyword in decorator.keywords if keyword.arg == "name"]
        if not names:
            return True, function.name
        if len(names) != 1:
            return True, None
        value = names[0].value
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


def _validate_no_reserved_fixture_override(
    path: Path,
    relative: Path,
    allowed: frozenset[str] = frozenset(),
) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative.as_posix())
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RunnerError(f"cannot validate tracked pytest module: {relative.as_posix()}") from exc
    references, parametrize_references = _pytest_callable_references(tree)
    top_level_functions = {
        id(node)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    overrides: set[str] = set()
    if _has_dynamic_pytest_factory_access(tree, references, parametrize_references):
        raise RunnerError(
            f"tracked pytest module resolves fixture factories dynamically: {relative.as_posix()}"
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
                raise RunnerError(
                    f"tracked pytest fixture has a dynamic name: {relative.as_posix()}"
                )
            if fixture_names:
                value = fixture_names[0].value
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    raise RunnerError(
                        f"tracked pytest fixture has a dynamic name: {relative.as_posix()}"
                    )
                if value.value in _RESERVED_EXTERNAL_FIXTURES:
                    overrides.add(value.value)
        if isinstance(candidate, ast.Call) and (
            _dotted_name(candidate.func) in parametrize_references
            or _dotted_name(candidate.func).endswith(".parametrize")
        ):
            parameter_names, dynamic = _parametrize_names(candidate)
            if dynamic:
                raise RunnerError(
                    f"tracked pytest parametrization has dynamic argnames: {relative.as_posix()}"
                )
            overrides.update(parameter_names & _RESERVED_EXTERNAL_FIXTURES)
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        is_fixture, exported = _fixture_export(candidate, references)
        if not is_fixture:
            continue
        if exported is None:
            raise RunnerError(
                f"tracked pytest fixture has a dynamic name: {relative.as_posix()}"
            )
        if exported in _RESERVED_EXTERNAL_FIXTURES and (
            exported not in allowed
            or candidate.name != exported
            or id(candidate) not in top_level_functions
        ):
            overrides.add(exported)
    if overrides:
        override_names = ", ".join(sorted(overrides))
        raise RunnerError(
            f"tracked pytest module overrides reserved external fixture ({override_names}): "
            f"{relative.as_posix()}"
        )


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


def _validate_environment_tree(
    tree: ast.Module,
    relative: Path,
    *,
    canonical_root: bool | None,
    top_level_only: bool = False,
) -> None:
    exact = [node for node in tree.body if _exact_offline_assignment(node)]
    if canonical_root is True and len(exact) != 1:
        raise RunnerError("root conftest does not set offline mode exactly once")
    if canonical_root is False and exact:
        raise RunnerError(f"nested conftest sets offline mode: {relative.as_posix()}")
    allowed_nodes: set[int] = set()
    if canonical_root is True and len(exact) == 1:
        allowed_nodes.update(id(node) for node in ast.walk(exact[0]))
    mappings, calls = _environment_references(tree)
    strict_imports = canonical_root is not None
    for node in _automatic_effect_nodes(tree, top_level_only=top_level_only):
        if id(node) in allowed_nodes:
            continue
        if strict_imports and isinstance(node, ast.Import) and any(
            alias.name == "os" and (canonical_root is not True or alias.asname is not None)
            for alias in node.names
        ):
            raise RunnerError(
                f"automatic pytest input imports/aliases environment APIs: {relative.as_posix()}"
            )
        if strict_imports and isinstance(node, ast.ImportFrom) and node.module == "os":
            raise RunnerError(
                f"conftest imports process environment APIs directly: {relative.as_posix()}"
            )
        if isinstance(node, (ast.Attribute, ast.Name)) and any(
            _dotted_name(node) == reference or _dotted_name(node).startswith(f"{reference}.")
            for reference in mappings
        ):
            raise RunnerError(
                f"automatic pytest input accesses process environment: {relative.as_posix()}"
            )
        if isinstance(node, ast.Call) and _dotted_name(node.func) in calls:
            raise RunnerError(
                f"automatic pytest input accesses process environment: {relative.as_posix()}"
            )
        if (
            isinstance(node, ast.Name) and node.id == "OFFLINE_TEST_ENV"
        ) or (
            isinstance(node, ast.Constant)
            and node.value in {_OFFLINE_ENV_NAME, _OFFLINE_ENV_NAME.encode()}
        ):
            raise RunnerError(f"automatic pytest input overrides offline mode: {relative.as_posix()}")


def _validate_conftest_marker(path: Path, relative: Path) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative.as_posix())
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RunnerError(f"cannot validate tracked pytest module: {relative.as_posix()}") from exc
    _validate_environment_tree(
        tree,
        relative,
        canonical_root=relative == Path("tests/conftest.py"),
    )


def _validate_automatic_input_discovery(
    path: Path,
    relative: Path,
    *,
    top_level_only: bool = False,
    include_path_discovery: bool = True,
) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative.as_posix())
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RunnerError(f"cannot validate tracked pytest module: {relative.as_posix()}") from exc
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
        if isinstance(node, ast.Import) and any(
            alias.name == "dotenv" or alias.name.startswith("dotenv.")
            for alias in node.names
        ):
            raise RunnerError(f"automatic pytest input imports dotenv: {relative.as_posix()}")
        if isinstance(node, ast.ImportFrom) and (
            node.module == "dotenv" or (node.module or "").startswith("dotenv.")
        ):
            raise RunnerError(f"automatic pytest input imports dotenv: {relative.as_posix()}")
        if include_path_discovery and isinstance(node, ast.Name) and node.id == "__file__":
            raise RunnerError(f"automatic pytest input discovers repo paths: {relative.as_posix()}")
        if isinstance(node, ast.Call) and (
            _dotted_name(node.func) in dynamic_calls
        ):
            raise RunnerError(f"automatic pytest input executes dynamic code: {relative.as_posix()}")
        if isinstance(node, ast.Call) and (
            _dotted_name(node.func) in forbidden_calls
            or (
                include_path_discovery
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in path_call_attributes
            )
        ):
            raise RunnerError(
                f"automatic pytest input discovers dotenv/repo/home paths: {relative.as_posix()}"
            )
        if isinstance(node, ast.Call) and any(is_env_path(item) for item in ast.walk(node)):
            raise RunnerError(f"automatic pytest input reads a .env file: {relative.as_posix()}")
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and node.value is not None
            and is_env_path(node.value)
        ):
            raise RunnerError(f"automatic pytest input binds a .env path: {relative.as_posix()}")
        if (
            include_path_discovery
            and isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and is_env_path(node)
        ):
            raise RunnerError(f"automatic pytest input names a .env file: {relative.as_posix()}")


def _validate_test_module_automatic_inputs(path: Path, relative: Path) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative.as_posix())
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RunnerError(f"cannot validate tracked pytest module: {relative.as_posix()}") from exc
    _validate_environment_tree(
        tree,
        relative,
        canonical_root=None,
        top_level_only=True,
    )
    _validate_automatic_input_discovery(
        path,
        relative,
        top_level_only=True,
        include_path_discovery=False,
    )


def _validate_package_init(path: Path, relative: Path) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative.as_posix())
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RunnerError(f"cannot validate tracked pytest module: {relative.as_posix()}") from exc
    if tree.body and not (
        len(tree.body) == 1
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        raise RunnerError(
            f"pytest package __init__.py is not empty/docstring-only: {relative.as_posix()}"
        )


def _validate_conftest_chain(repo_root: Path, test_file: Path, tracked: set[str]) -> None:
    parent = test_file.parent
    while True:
        relative = parent / "conftest.py"
        candidate = repo_root / relative
        if candidate.exists() or candidate.is_symlink():
            _validate_tracked_file(repo_root, relative, tracked)
            _validate_no_pytest_plugins(candidate, relative)
            _validate_no_reserved_fixture_override(
                candidate,
                relative,
                _CANONICAL_FIXTURES.get(relative.as_posix(), frozenset()),
            )
            _validate_conftest_marker(candidate, relative)
            _validate_automatic_input_discovery(candidate, relative)
        if parent == Path("."):
            break
        parent = parent.parent


def _validate_package_chain(repo_root: Path, test_file: Path, tracked: set[str]) -> None:
    parent = test_file.parent
    while parent != Path("."):
        relative = parent / "__init__.py"
        candidate = repo_root / relative
        if candidate.exists() or candidate.is_symlink():
            _validate_tracked_file(repo_root, relative, tracked)
            _validate_package_init(candidate, relative)
        if parent == _TESTS_ROOT:
            break
        parent = parent.parent


def _relative_test_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if (
        not raw_path
        or path.is_absolute()
        or path.drive
        or any(part in {"", ".."} for part in path.parts)
        or not path.parts
        or path.parts[0] != _TESTS_ROOT.as_posix()
    ):
        raise RunnerError(f"pytest target must be repo-relative under tests/: {raw_path or '<empty>'}")
    return Path(*path.parts)


def _is_test_file(relative: Path) -> bool:
    return relative.suffix == ".py" and (
        relative.name.startswith("test_") or relative.name.endswith("_test.py")
    )


def _expanded_target(raw: str, repo_root: Path, tracked: set[str]) -> list[str]:
    path_text, separator, node_suffix = raw.partition("::")
    relative = _relative_test_path(path_text)
    _assert_non_reparse(repo_root, relative)
    candidate = repo_root / relative

    if candidate.is_file():
        if not _is_test_file(relative):
            raise RunnerError(f"pytest file target is not a test module: {relative.as_posix()}")
        _validate_tracked_file(repo_root, relative, tracked)
        _validate_no_pytest_plugins(candidate, relative)
        _validate_no_reserved_fixture_override(candidate, relative)
        _validate_test_module_automatic_inputs(candidate, relative)
        _validate_conftest_chain(repo_root, relative, tracked)
        _validate_package_chain(repo_root, relative, tracked)
        if separator and (not node_suffix or any(char in node_suffix for char in "\0\r\n")):
            raise RunnerError(f"pytest node id is malformed: {relative.as_posix()}")
        return [relative.as_posix() + (separator + node_suffix if separator else "")]

    if not candidate.is_dir():
        raise RunnerError(f"pytest target is not a regular file/directory: {relative.as_posix()}")
    if separator:
        raise RunnerError(f"pytest node id must name a tracked file: {relative.as_posix()}")
    prefix = relative.as_posix().rstrip("/") + "/"
    files = [
        Path(item)
        for item in sorted(tracked)
        if item.startswith(prefix) and _is_test_file(Path(item))
    ]
    if not files:
        raise RunnerError(f"pytest directory target contains no Git-tracked tests: {relative.as_posix()}")
    for test_file in files:
        _validate_tracked_file(repo_root, test_file, tracked)
        _validate_no_pytest_plugins(repo_root / test_file, test_file)
        _validate_no_reserved_fixture_override(repo_root / test_file, test_file)
        _validate_test_module_automatic_inputs(repo_root / test_file, test_file)
        _validate_conftest_chain(repo_root, test_file, tracked)
        _validate_package_chain(repo_root, test_file, tracked)
    return [item.as_posix() for item in files]


def _validated_ignore(raw: str, repo_root: Path, tracked: set[str]) -> str:
    relative = _relative_test_path(raw)
    _assert_non_reparse(repo_root, relative)
    candidate = repo_root / relative
    if candidate.is_file():
        if not _is_test_file(relative):
            raise RunnerError(
                f"ignored pytest file is not a test module: {relative.as_posix()}"
            )
        _validate_tracked_file(repo_root, relative, tracked)
    elif candidate.is_dir():
        prefix = relative.as_posix().rstrip("/") + "/"
        if not any(item.startswith(prefix) for item in tracked):
            raise RunnerError(f"ignored directory contains no Git-tracked tests: {relative.as_posix()}")
    else:
        raise RunnerError(f"ignored pytest path is not a regular file/directory: {relative.as_posix()}")
    return relative.as_posix()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+", help="tracked tests/** path or file node id")
    parser.add_argument("-q", "--quiet", action="count", default=0)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-k", dest="keyword")
    parser.add_argument("-m", dest="markers")
    parser.add_argument("--ignore", action="append", default=[])
    parser.add_argument("--maxfail", type=int)
    parser.add_argument("-x", "--exitfirst", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--tb", choices=("auto", "long", "short", "line", "native", "no"))
    parser.add_argument("-r", dest="report_chars")
    return parser


def _is_ignored(path: str, ignores: list[str]) -> bool:
    file_path = path.partition("::")[0]
    return any(file_path == item or file_path.startswith(item.rstrip("/") + "/") for item in ignores)


def _pytest_arguments(args: argparse.Namespace, repo_root: Path) -> list[str]:
    tracked = _tracked_paths(repo_root)
    _validate_tracked_file(repo_root, Path("pyproject.toml"), tracked)
    ignored = [_validated_ignore(raw, repo_root, tracked) for raw in args.ignore]
    targets: list[str] = []
    for raw in args.targets:
        targets.extend(_expanded_target(raw, repo_root, tracked))
    targets = list(dict.fromkeys(path for path in targets if not _is_ignored(path, ignored)))
    if not targets:
        raise RunnerError("pytest target set is empty after applying ignores")
    if args.maxfail is not None and args.maxfail < 1:
        raise RunnerError("--maxfail must be at least 1")
    if args.report_chars is not None and not re.fullmatch(r"[A-Za-z]+", args.report_chars):
        raise RunnerError("-r accepts alphabetic pytest report characters only")

    forwarded: list[str] = []
    forwarded.extend(["-q"] * args.quiet)
    forwarded.extend(["-v"] * args.verbose)
    if args.keyword is not None:
        forwarded.extend(["-k", args.keyword])
    if args.markers is not None:
        forwarded.extend(["-m", args.markers])
    for path in ignored:
        forwarded.extend(["--ignore", path])
    if args.maxfail is not None:
        forwarded.extend(["--maxfail", str(args.maxfail)])
    if args.exitfirst:
        forwarded.append("-x")
    if args.collect_only:
        forwarded.append("--collect-only")
    if args.tb is not None:
        forwarded.extend(["--tb", args.tb])
    if args.report_chars is not None:
        forwarded.extend(["-r", args.report_chars])
    return [*targets, *forwarded]


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


def _pytest_command(
    plugins: tuple[str, ...], pytest_args: list[str], pycache_root: Path
) -> list[str]:
    command = [
        sys.executable,
        "-I",
        "-X",
        f"pycache_prefix={pycache_root}",
        "-m",
        "pytest",
        "-c",
        "pyproject.toml",
        "--rootdir=.",
        "--confcutdir=.",
    ]
    for module in plugins:
        command.extend(["-p", module])
    return [*command, *pytest_args]


def _assert_boundary_green(repo_root: Path) -> None:
    violations = check_offline_boundary(repo_root)
    if violations:
        raise RunnerError(
            f"offline boundary checker reported {len(violations)} violation(s); run the checker"
        )


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    root = (repo_root or _REPO_ROOT).absolute()
    args = _parser().parse_args(argv)
    try:
        _assert_repo_root_non_reparse(root)
        _assert_boundary_green(root)
        plugins = _verified_plugin_modules(root)
        pytest_args = _pytest_arguments(args, root)
        with tempfile.TemporaryDirectory(prefix="mj-agent-offline-pytest-") as temp_dir:
            profile_root = Path(temp_dir)
            env = _child_environment(profile_root)
            proc = subprocess.run(
                _pytest_command(plugins, pytest_args, profile_root / "pycache"),
                cwd=root,
                env=env,
                check=False,
            )
    except RunnerError as exc:
        print(f"OFFLINE_PYTEST_RUNNER: ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("OFFLINE_PYTEST_RUNNER: ERROR: local process/filesystem operation failed", file=sys.stderr)
        return 2
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
