"""Offline safety assertions extracted unchanged from projection tests (Codex P1)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from scripts.sdd import run_offline_pytest as offline_runner
from scripts.sdd.check_test_offline_boundary import Violation as OfflineViolation
from scripts.sdd.check_test_offline_boundary import _read as offline_boundary_read
from scripts.sdd.check_test_offline_boundary import check as offline_boundary_check
from scripts.sdd.check_test_offline_boundary import main as offline_boundary_main

REPO_ROOT = Path(__file__).resolve().parents[2]

# -------------------------------------------------------- offline pytest boundary (Epic #499)


_OFFLINE_BOUNDARY_FILES = (
    Path("AGENTS.md"),
    Path("capabilities/AGENTS.md"),
    Path("docker/AGENTS.md"),
    Path("src/mj_agent/AGENTS.md"),
    Path("src/mj_agent/config.py"),
    Path("tests/AGENTS.md"),
    Path("tests/conftest.py"),
    Path("tests/bdd/conftest.py"),
    Path("sdd/workflows/execution-loop.md"),
    Path(".github/PULL_REQUEST_TEMPLATE.md"),
    Path(".github/workflows/ci.yml"),
    Path("scripts/sdd/run_offline_pytest.py"),
)


def _make_offline_boundary_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for relative in _OFFLINE_BOUNDARY_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, destination)
    return root


def test_offline_boundary_checker_real_tree_green_and_human_readme_excluded() -> None:
    assert offline_boundary_check(REPO_ROOT) == []
    assert "uv run pytest tests/unit" in (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def test_offline_boundary_checker_catches_source_ci_and_instruction_regressions(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\nfrom dotenv import load_dotenv\nload_dotenv()\n",
        encoding="utf-8",
    )
    config = root / "src" / "mj_agent" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            'values["_secrets_dir"] = None', 'values["not_a_source_disabler"] = None'
        ),
        encoding="utf-8",
    )
    instructions = root / "AGENTS.md"
    instructions.write_text(
        instructions.read_text(encoding="utf-8") + "\nuv run pytest tests/unit\n",
        encoding="utf-8",
    )
    workflow = root / ".github" / "workflows" / "ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/bdd -q",
            "uv run pytest tests/bdd -q",
        ),
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("dotenv" in message for message in messages)
    assert any("filesystem-source None writes" in message for message in messages)
    assert any("Agent-facing direct pytest" in message for message in messages)
    assert any("CI step is not bound" in message for message in messages)


def test_offline_boundary_checker_rejects_pre_skip_effect_and_fixture_override(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8").replace(
            '    pytest.skip(\n        "SKIP_POLICY_EXTERNAL_DEPENDENCY: biz live legs are permanently unavailable to pytest"\n    )',
            '    external_call()\n    pytest.skip(\n        "SKIP_POLICY_EXTERNAL_DEPENDENCY: biz live legs are permanently unavailable to pytest"\n    )',
        ),
        encoding="utf-8",
    )
    nested = root / "tests" / "unit" / "conftest.py"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def docker_available():\n"
        "    return object()\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("live_db must unconditionally" in message for message in messages)
    assert any("reserved external fixture override: docker_available" in message for message in messages)


@pytest.mark.parametrize(
    "replacement",
    (
        '@external_call()\n@pytest.fixture(scope="session")\ndef live_db() -> None:',
        '@pytest.fixture(scope="session")\ndef live_db(value=external_call()) -> None:',
    ),
)
def test_offline_boundary_checker_rejects_policy_fixture_definition_time_effects(
    tmp_path: Path, replacement: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8").replace(
            '@pytest.fixture(scope="session")\ndef live_db() -> None:',
            replacement,
        ),
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("live_db must remain the exact static session-skip fixture" in item for item in messages)


def test_offline_boundary_checker_rejects_marker_reset_and_renamed_fixture(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + '\nos.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    nested = root / "tests" / "unit" / "conftest.py"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        "import pytest\n\n"
        '@pytest.fixture(name="live_db")\n'
        "def enabled_external_route():\n"
        "    return object()\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("offline marker" in message or "process environment" in message for message in messages)
    assert any("reserved external fixture override: live_db" in message for message in messages)

    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\nfrom os import environ\nenviron.clear()\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("environment APIs directly" in message for message in messages)


def test_offline_boundary_checker_rejects_canonical_alias_and_functional_fixture(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\n@pytest.fixture(name=\"live_db\")\n"
        "def replacement_live_db():\n"
        "    return object()\n",
        encoding="utf-8",
    )
    test_module = root / "tests" / "unit" / "test_override.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "import pytest\n\n"
        "def enabled_external_route():\n"
        "    return object()\n\n"
        'pytest.fixture(name="memory_db")(enabled_external_route)\n',
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("reserved external fixture override: live_db" in message for message in messages)
    assert any("reserved external fixture override: memory_db" in message for message in messages)


def test_offline_boundary_checker_rejects_nested_canonical_fixture_duplicate(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8")
        + "\nif True:\n"
        "    @pytest.fixture\n"
        "    def live_db():\n"
        "        return object()\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("reserved external fixture override: live_db" in message for message in messages)


def test_offline_boundary_checker_rejects_dynamic_tuple_and_parametrize_shadows(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    test_module = root / "tests" / "unit" / "test_override.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "import pytest\n\n"
        "def enabled_external_route(): return object()\n"
        '@pytest.fixture(**{"name": "live_db"})\n'
        "def dynamic_live(): return object()\n"
        "memory_db, unused = pytest.fixture(enabled_external_route), None\n"
        '@pytest.mark.parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("static reviewed string" in message for message in messages)
    assert any("memory_db" in message for message in messages)
    assert any("docker_available" in message for message in messages)


def test_offline_boundary_checker_allows_plain_reserved_named_helpers(tmp_path: Path) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    test_module = root / "tests" / "unit" / "test_helpers.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "def agent(): return object()\n"
        "live_db = object()\n"
        "def test_helpers(): assert agent() is not live_db\n",
        encoding="utf-8",
    )
    assert offline_boundary_check(root) == []


def test_offline_boundary_checker_rejects_all_automatic_input_routes(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "conftest.py").write_text(
        "from dotenv import load_dotenv\nload_dotenv()\n",
        encoding="utf-8",
    )
    (unit / "__init__.py").write_text(
        'import os\nos.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    (unit / "test_plugins.py").write_text(
        "from helper import plugins as pytest_plugins\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("import dotenv" in message for message in messages)
    assert any("empty or docstring-only" in message for message in messages)
    assert any("pytest_plugins binding/import" in message for message in messages)


def test_offline_boundary_checker_rejects_runtime_plugin_registration(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    plugin_route = root / "tests" / "unit" / "conftest.py"
    plugin_route.parent.mkdir(parents=True)
    plugin_route.write_text(
        "def pytest_configure(config):\n"
        "    pm = config.pluginmanager\n"
        "    pm.register(object())\n",
        encoding="utf-8",
    )
    violations = offline_boundary_check(root)
    assert any(
        item.path == plugin_route and "dynamic pytest plugin loading" in item.message
        for item in violations
    )


def test_offline_boundary_checker_rejects_top_level_test_inputs_and_path_aliases(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "test_marker_reset.py").write_text(
        "import os as operating_system\n"
        'operating_system.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    (unit / "test_dotenv.py").write_text(
        "from dotenv import load_dotenv\nload_dotenv()\ndef test_ok(): pass\n",
        encoding="utf-8",
    )
    (unit / "test_manual_env.py").write_text(
        'from pathlib import Path\nPath(".env").read_text()\ndef test_ok(): pass\n',
        encoding="utf-8",
    )
    (unit / "test_local_reset.py").write_text(
        "import os\n"
        "def reset():\n"
        '    os.environ.pop("MJ_AGENT_" + "OFFLINE_TEST", None)\n'
        "reset()\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    (unit / "conftest.py").write_text(
        "import pathlib\npathlib.Path.home()\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert sum("process environment" in message for message in messages) >= 2
    assert any("import dotenv" in message for message in messages)
    assert any("read a .env file" in message for message in messages)
    assert any("repo/home paths" in message for message in messages)


def test_offline_boundary_checker_rejects_fixture_and_parametrize_factory_aliases(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    test_module = root / "tests" / "unit" / "test_alias_override.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "import pytest\n"
        "fixture_factory, unused = pytest.fixture, None\n"
        "parametrize = pytest.mark.parametrize\n"
        "def enabled_external_route(): return object()\n"
        "memory_db = fixture_factory(enabled_external_route)\n"
        '@parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )

    messages = [item.message for item in offline_boundary_check(root)]
    assert any("memory_db" in message for message in messages)
    assert any("docker_available" in message for message in messages)

    dynamic_module = root / "tests" / "unit" / "test_dynamic_alias.py"
    dynamic_module.write_text(
        "import pytest\n"
        "class Namespace: pass\n"
        "if True:\n"
        "    Namespace.fixture = pytest.fixture\n"
        '@Namespace.fixture(name="live_db")\n'
        "def enabled(): return object()\n"
        'factory = getattr(pytest, "fixture")\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    violations = offline_boundary_check(root)
    assert any(
        item.path == dynamic_module and "live_db" in item.message for item in violations
    )
    assert any(
        item.path == dynamic_module and "static reviewed string" in item.message
        for item in violations
    )


@pytest.mark.parametrize(
    ("addition", "expected"),
    (
        ('\nos.environb.pop(b"MJ_AGENT_OFFLINE_TEST", None)\n', "process environment"),
        ("\npytest.skip = external_call\n", "rebind os/pytest"),
        ("\npolicy = pytest\npolicy.skip = external_call\n", "rebind os/pytest"),
    ),
)
def test_offline_boundary_checker_rejects_bytes_marker_and_policy_api_mutation(
    tmp_path: Path, addition: str, expected: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        conftest.read_text(encoding="utf-8") + addition,
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any(expected in message for message in messages)


def test_offline_boundary_checker_rejects_repo_root_conftest(tmp_path: Path) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    (root / "conftest.py").write_text("raise RuntimeError\n", encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("repo-root conftest.py is forbidden" in message for message in messages)


def test_offline_boundary_read_rejects_reparse_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    target = root / "tests" / "conftest.py"
    target.parent.mkdir(parents=True)
    target.write_text("safe = True\n", encoding="utf-8")
    real_lstat = Path.lstat
    real_read_text = Path.read_text
    read_attempted = False

    def fake_lstat(path: Path) -> Any:
        info = real_lstat(path)
        if path == target:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=offline_runner._REPARSE_POINT,
            )
        return info

    def guarded_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        nonlocal read_attempted
        if path == target:
            read_attempted = True
            raise AssertionError("reparse target was read")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    violations: list[OfflineViolation] = []
    assert offline_boundary_read(target, root, violations) is None
    assert not read_attempted
    assert any("regular/non-reparse" in item.message for item in violations)


def test_offline_boundary_checker_reports_reparse_test_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    (unit / "test_safe.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    real_lstat = Path.lstat

    def fake_lstat(path: Path) -> Any:
        info = real_lstat(path)
        if path == unit:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=offline_runner._REPARSE_POINT,
            )
        return info

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("test directory must be regular/non-reparse" in message for message in messages)


@pytest.mark.parametrize(
    "command",
    (
        "pytest",
        "pytest tests/unit -q",
        "pytest --collect-only tests/unit",
        "pytest -s tests/unit",
        "pytest ./tests/unit",
        "pytest .\\tests\\unit",
        "pytest -- tests/unit",
        "pytest -- ./tests/unit",
        "pytest -- .\\tests\\unit",
        "'pytest' tests/unit",
        'uv run "pytest" tests/unit',
        "pytest \\\n  ./tests/unit",
        "uv run python -m pytest tests/unit -q",
        "uv run -q pytest tests/unit -q",
        "uv run -- pytest tests/unit -q",
        "python -I -m pytest tests/unit -q",
        "python3 -m pytest tests/unit -q",
        "py -3.12 -m pytest tests/unit -q",
    ),
)
def test_offline_boundary_checker_rejects_direct_pytest_variants(
    tmp_path: Path, command: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    instructions = root / "AGENTS.md"
    instructions.write_text(
        instructions.read_text(encoding="utf-8") + f"\n{command}\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("Agent-facing direct pytest" in message for message in messages)


@pytest.mark.parametrize("block_header", ("|", "| # retained comment", "|2-"))
def test_offline_boundary_checker_rejects_multiline_ci_direct_pytest(
    tmp_path: Path, block_header: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    workflow = root / ".github" / "workflows" / "ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8")
        + "\n  direct-regression:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - run: {block_header}\n"
        "          pytest \\\n"
        "            --collect-only ./tests/unit\n",
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("CI still contains a direct pytest entry" in message for message in messages)


def test_offline_boundary_checker_scans_all_workflows_and_agent_markdown(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    workflow = root / ".github" / "workflows" / "extra.yml"
    workflow.write_text(
        "name: extra\non: workflow_dispatch\njobs:\n"
        "  direct:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: pytest ./tests/unit\n",
        encoding="utf-8",
    )
    instructions = root / ".agents" / "commands" / "extra.md"
    instructions.parent.mkdir(parents=True)
    instructions.write_text("pytest ./tests/unit\n", encoding="utf-8")

    violations = offline_boundary_check(root)
    assert any(item.path == workflow and "direct pytest" in item.message for item in violations)
    assert any(
        item.path == instructions and "Agent-facing direct pytest" in item.message
        for item in violations
    )


def test_offline_boundary_checker_requires_runner_in_the_named_ci_step(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    workflow = root / ".github" / "workflows" / "ci.yml"
    expected = (
        "uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py "
        "tests --ignore tests/bdd"
    )
    source = workflow.read_text(encoding="utf-8")
    source = source.replace(f"        run: {expected}", "        run: echo wrong", 1)
    source += (
        "\n      - name: unrelated runner carrier\n"
        f"        run: {expected}\n"
    )
    workflow.write_text(source, encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("CI step is not bound" in message for message in messages)


def test_offline_boundary_checker_rejects_inverted_settings_condition(tmp_path: Path) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    config = root / "src" / "mj_agent" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "os.environ.get(OFFLINE_TEST_ENV) == \"1\"",
            "os.environ.get(OFFLINE_TEST_ENV) != \"1\"",
        ),
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("offline branch" in message for message in messages)


def test_offline_boundary_checker_rejects_source_reset_and_constant_rebind(
    tmp_path: Path,
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    config = root / "src" / "mj_agent" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8")
        .replace(
            '            values["_secrets_dir"] = None',
            '            values["_secrets_dir"] = None\n'
            '            values["_env_file"] = ".env"',
        )
        .replace(
            'OFFLINE_TEST_ENV = "MJ_AGENT_OFFLINE_TEST"',
            'OFFLINE_TEST_ENV = "MJ_AGENT_OFFLINE_TEST"\n'
            'OFFLINE_TEST_ENV = "MJ_AGENT_OFFLINE_TEST"',
        ),
        encoding="utf-8",
    )
    messages = [item.message for item in offline_boundary_check(root)]
    assert any("two filesystem-source None writes" in message for message in messages)
    assert any("uniquely bound" in message for message in messages)


@pytest.mark.parametrize(
    ("needle", "replacement", "expected"),
    (
        (
            "        super().__init__(**values)",
            "        super().__init__(**values)\n\n"
            "    def __init__(self, **values: Any) -> None:\n"
            "        super().__init__(**values)",
            "unique construction seam",
        ),
        (
            "    # ── 0. Application",
            "    @classmethod\n"
            "    def settings_customise_sources(cls, *sources: Any) -> tuple[Any, ...]:\n"
            "        return sources\n\n"
            "    # ── 0. Application",
            "source hooks bypass",
        ),
        (
            "settings = Settings()",
            "settings = Settings()\nsettings = Settings()",
            "must not be rebound or reconstructed",
        ),
        (
            "settings = Settings()",
            "from dotenv import load_dotenv\nload_dotenv()\nsettings = Settings()",
            "may not execute dotenv",
        ),
        (
            "settings = Settings()",
            "if True:\n"
            "    class Settings(BaseSettings):\n"
            "        pass\n\n"
            "settings = Settings()",
            "one unique top-level class",
        ),
    ),
)
def test_offline_boundary_checker_rejects_alternate_settings_construction_paths(
    tmp_path: Path, needle: str, replacement: str, expected: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    config = root / "src" / "mj_agent" / "config.py"
    source = config.read_text(encoding="utf-8")
    assert needle in source
    config.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any(expected in message for message in messages)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (
            lambda source: source + '\nSAFE_PARENT_ENV_NAMES += ("EXAMPLE_API_KEY",)\n',
            "literal closed collection",
        ),
        (
            lambda source: source.replace(
                "    env = _safe_parent_environment()",
                "    env = _safe_parent_environment()\n    env.update(os.environ)",
                1,
            ),
            "reviewed closed environment builder",
        ),
        (
            lambda source: source.replace(
                "def _load_toml(path: Path)",
                "if True:\n"
                "    def _safe_parent_environment() -> dict[str, str]:\n"
                "        return {}\n\n"
                "def _load_toml(path: Path)",
                1,
            ),
            "reviewed closed environment builder",
        ),
        (
            # #546: moving the persistent tiktoken cache back under the per-run
            # profile silently re-introduces the download-per-run network dependency.
            lambda source: source.replace(
                '    tiktoken_cache = repo_root / ".mj-agent-local" / "tiktoken-cache"',
                '    tiktoken_cache = profile_root / "tiktoken-cache"',
                1,
            ),
            "reviewed closed environment builder",
        ),
    ),
)
def test_offline_boundary_checker_rejects_runner_environment_expansion(
    tmp_path: Path, mutation: Any, expected: str
) -> None:
    root = _make_offline_boundary_repo(tmp_path)
    runner = root / "scripts" / "sdd" / "run_offline_pytest.py"
    runner.write_text(mutation(runner.read_text(encoding="utf-8")), encoding="utf-8")
    messages = [item.message for item in offline_boundary_check(root)]
    assert any(expected in message for message in messages)


def test_offline_boundary_checker_cli_rejects_arguments(capsys: Any) -> None:
    assert offline_boundary_main(["unexpected"], repo_root=REPO_ROOT) == 2
    assert "no command-line arguments" in capsys.readouterr().err


def test_offline_runner_child_environment_is_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    forbidden = (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONPATH",
        "EXAMPLE_CREDENTIAL",
        "EXAMPLE_TOKEN",
        "EXAMPLE_SECRET",
        "EXAMPLE_PASSWORD",
        "EXAMPLE_API_KEY",
        "EXAMPLE_URL",
    )
    for name in forbidden:
        monkeypatch.setenv(name, "synthetic-never-print")

    profile = tmp_path / "profile"
    repo = tmp_path / "repo"
    child = offline_runner._child_environment(profile, repo)

    assert not set(forbidden) & child.keys()
    assert child["MJ_AGENT_OFFLINE_TEST"] == "1"
    assert child["PYTHONNOUSERSITE"] == "1"
    assert child["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    for name in (
        "HOME",
        "USERPROFILE",
        "XDG_CONFIG_HOME",
        "APPDATA",
        "TEMP",
        "PYTHONPYCACHEPREFIX",
    ):
        assert Path(child[name]).is_relative_to(profile)

    # #546: the single deliberately persistent path lives under the repo root, not the
    # per-run profile, so tiktoken's BPE blobs survive between runs and re-runs stay offline.
    tiktoken_cache = Path(child["TIKTOKEN_CACHE_DIR"])
    assert tiktoken_cache == repo / ".mj-agent-local" / "tiktoken-cache"
    assert not tiktoken_cache.is_relative_to(profile)
    assert tiktoken_cache.is_dir()


def test_offline_runner_tiktoken_cache_is_gitignored() -> None:
    """#546: the persistent BPE cache must never surface as an untracked repo blob."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".mj-agent-local/tiktoken-cache/blob"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_offline_runner_expands_only_tracked_test_files_and_rejects_untracked_conftest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    tracked_file = unit / "test_tracked.py"
    tracked_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    (unit / "test_untracked.py").write_text("raise RuntimeError\n", encoding="utf-8")
    tracked = {"tests/unit/test_tracked.py"}

    assert offline_runner._expanded_target("tests/unit", root, tracked) == [
        "tests/unit/test_tracked.py"
    ]
    with pytest.raises(offline_runner.RunnerError, match="not Git-tracked"):
        offline_runner._expanded_target("tests/unit/test_untracked.py", root, tracked)

    root_conftest = root / "tests" / "conftest.py"
    root_conftest.write_text("pytest_plugins = ['rogue']\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="not Git-tracked"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    tracked.add("tests/conftest.py")
    with pytest.raises(offline_runner.RunnerError, match="declares pytest_plugins"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    root_conftest.unlink()
    tracked.remove("tests/conftest.py")
    root_init = root / "tests" / "__init__.py"
    root_init.write_text("# package marker\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="not Git-tracked"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    tracked.add("tests/__init__.py")
    root_init.write_text("pytest_plugins = ['rogue']\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="empty/docstring-only"):
        offline_runner._expanded_target("tests/unit", root, tracked)

    root_init.unlink()
    tracked.remove("tests/__init__.py")
    tracked_file.write_text(
        "pytest_plugins = ['rogue']\ndef test_ok(): pass\n", encoding="utf-8"
    )
    with pytest.raises(offline_runner.RunnerError, match="declares pytest_plugins"):
        offline_runner._expanded_target("tests/unit", root, tracked)


def test_offline_runner_rejects_reparse_and_malformed_node_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    tracked = {"tests/unit/test_boundary.py"}

    with pytest.raises(offline_runner.RunnerError, match="node id is malformed"):
        offline_runner._expanded_target("tests/unit/test_boundary.py::", root, tracked)

    real_lstat = Path.lstat

    def fake_lstat(path: Path) -> Any:
        info = real_lstat(path)
        if path == root / "tests" / "unit":
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=offline_runner._REPARSE_POINT,
            )
        return info

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(offline_runner.RunnerError, match="symlink/reparse"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_rejects_marker_reset_and_renamed_fixture(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    conftest = root / "tests" / "conftest.py"
    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        'os.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    tracked = {"tests/unit/test_boundary.py", "tests/conftest.py"}

    with pytest.raises(offline_runner.RunnerError, match="offline mode|environment"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        "from os import environ\nenviron.clear()\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="environment APIs directly"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        'os.environb.pop(b"MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="process environment"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n',
        encoding="utf-8",
    )
    test_file.write_text(
        "import pytest\n"
        '@pytest.fixture(name="live_db")\n'
        "def enabled_external_route(): return object()\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        (REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
        + "\nif True:\n"
        "    @pytest.fixture\n"
        "    def live_db(): return object()\n",
        encoding="utf-8",
    )
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text(
        "import pytest\n"
        "def enabled_external_route(): return object()\n"
        "live_db, unused = pytest.fixture(enabled_external_route), None\n"
        '@pytest.mark.parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text(
        "import pytest\n"
        '@pytest.fixture(**{"name": "live_db"})\n'
        "def dynamic_live(): return object()\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="dynamic name"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    conftest.write_text(
        'import os\nimport pytest\n'
        'os.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n'
        '@pytest.fixture(name="live_db")\n'
        "def replacement_live_db(): return object()\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n',
        encoding="utf-8",
    )
    test_file.write_text(
        "import pytest\n"
        "def enabled_external_route(): return object()\n"
        'pytest.fixture(name="memory_db")(enabled_external_route)\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_rejects_fixture_and_parametrize_factory_aliases(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "import pytest\n"
        "fixture_factory, unused = pytest.fixture, None\n"
        "parametrize = pytest.mark.parametrize\n"
        "def enabled_external_route(): return object()\n"
        "memory_db = fixture_factory(enabled_external_route)\n"
        '@parametrize("docker_available", [object()])\n'
        "def test_shadow(docker_available): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="reserved external fixture"):
        offline_runner._expanded_target(
            "tests/unit/test_boundary.py", root, {"tests/unit/test_boundary.py"}
        )

    test_file.write_text(
        "import pytest\n"
        "class Namespace: pass\n"
        "if True:\n"
        "    Namespace.fixture = pytest.fixture\n"
        '@Namespace.fixture(name="live_db")\n'
        "def enabled(): return object()\n"
        'factory = getattr(pytest, "fixture")\n'
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="dynamically|reserved external fixture"):
        offline_runner._expanded_target(
            "tests/unit/test_boundary.py", root, {"tests/unit/test_boundary.py"}
        )


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        (
            "import os as operating_system\n"
            'operating_system.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n'
            "def test_ok(): pass\n",
            "process environment",
        ),
        (
            "from dotenv import load_dotenv\nload_dotenv()\ndef test_ok(): pass\n",
            "imports dotenv",
        ),
        (
            'from pathlib import Path\nPath(".env").read_text()\ndef test_ok(): pass\n',
            "reads a .env file",
        ),
        (
            "import os\n"
            "def reset():\n"
            '    os.environ.pop("MJ_AGENT_" + "OFFLINE_TEST", None)\n'
            "reset()\n"
            "def test_ok(): pass\n",
            "process environment",
        ),
    ),
)
def test_offline_runner_rejects_test_module_top_level_automatic_inputs(
    tmp_path: Path, source: str, expected: str
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(source, encoding="utf-8")
    with pytest.raises(offline_runner.RunnerError, match=expected):
        offline_runner._expanded_target(
            "tests/unit/test_boundary.py", root, {"tests/unit/test_boundary.py"}
        )


def test_offline_runner_rejects_aliased_home_discovery_in_nested_conftest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_boundary.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    nested = root / "tests" / "unit" / "conftest.py"
    nested.write_text("import pathlib\npathlib.Path.home()\n", encoding="utf-8")
    tracked = {"tests/unit/test_boundary.py", "tests/unit/conftest.py"}
    with pytest.raises(offline_runner.RunnerError, match="repo/home paths"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_rejects_nested_discovery_package_code_and_plugin_import(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    unit = root / "tests" / "unit"
    unit.mkdir(parents=True)
    test_file = unit / "test_boundary.py"
    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    root_conftest = root / "tests" / "conftest.py"
    root_conftest.write_text(
        'import os\nos.environ["MJ_AGENT_OFFLINE_TEST"] = "1"\n',
        encoding="utf-8",
    )
    nested = unit / "conftest.py"
    nested.write_text("from dotenv import load_dotenv\nload_dotenv()\n", encoding="utf-8")
    tracked = {
        "tests/unit/test_boundary.py",
        "tests/conftest.py",
        "tests/unit/conftest.py",
    }
    with pytest.raises(offline_runner.RunnerError, match="imports dotenv"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    nested.unlink()
    tracked.remove("tests/unit/conftest.py")
    package = unit / "__init__.py"
    package.write_text(
        'import os\nos.environ.pop("MJ_AGENT_OFFLINE_TEST", None)\n',
        encoding="utf-8",
    )
    tracked.add("tests/unit/__init__.py")
    with pytest.raises(offline_runner.RunnerError, match="empty/docstring-only"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    package.unlink()
    tracked.remove("tests/unit/__init__.py")
    test_file.write_text(
        "from helper import plugins as pytest_plugins\n"
        "def test_ok(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(offline_runner.RunnerError, match="imports pytest_plugins"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)

    test_file.write_text("def test_ok(): pass\n", encoding="utf-8")
    dynamic_plugin = unit / "conftest.py"
    dynamic_plugin.write_text(
        "def pytest_configure(config):\n"
        "    pm = config.pluginmanager\n"
        "    pm.register(object())\n",
        encoding="utf-8",
    )
    tracked.add("tests/unit/conftest.py")
    with pytest.raises(offline_runner.RunnerError, match="loads plugins dynamically"):
        offline_runner._expanded_target("tests/unit/test_boundary.py", root, tracked)


def test_offline_runner_allows_plain_reserved_named_helpers(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    test_file = root / "tests" / "unit" / "test_helpers.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def agent(): return object()\n"
        "live_db = object()\n"
        "def test_helpers(): assert agent() is not live_db\n",
        encoding="utf-8",
    )
    assert offline_runner._expanded_target(
        "tests/unit/test_helpers.py", root, {"tests/unit/test_helpers.py"}
    ) == ["tests/unit/test_helpers.py"]


def test_offline_runner_cannot_ignore_boundary_conftest(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    conftest = root / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True)
    conftest.write_text("# boundary\n", encoding="utf-8")
    tracked = {"tests/conftest.py"}

    with pytest.raises(offline_runner.RunnerError, match="not a test module"):
        offline_runner._validated_ignore("tests/conftest.py", root, tracked)


def test_offline_runner_command_is_isolated_and_plugins_are_exact(tmp_path: Path) -> None:
    plugins = ("pytest_asyncio.plugin", "pytest_bdd.plugin")
    pycache = tmp_path / "pycache"
    command = offline_runner._pytest_command(
        plugins, ["tests/unit/test_agents_sync.py"], pycache
    )
    assert command[:6] == [
        offline_runner.sys.executable,
        "-I",
        "-X",
        f"pycache_prefix={pycache}",
        "-m",
        "pytest",
    ]
    assert command[command.index("-c") + 1] == "pyproject.toml"
    assert command.count("-p") == len(plugins)
    assert [command[index + 1] for index, item in enumerate(command) if item == "-p"] == list(
        plugins
    )


def test_offline_runner_rejects_unreviewed_addopts() -> None:
    project = offline_runner._load_toml(REPO_ROOT / "pyproject.toml")
    tool = project["tool"]
    assert isinstance(tool, dict)
    pytest_section = tool["pytest"]
    assert isinstance(pytest_section, dict)
    options = pytest_section["ini_options"]
    assert isinstance(options, dict)
    options["addopts"] = "-ra --strict-markers -m 'not smoke and not contract' ../outside"

    with pytest.raises(offline_runner.RunnerError, match="differs from the reviewed"):
        offline_runner._pytest_config(project)


def test_offline_runner_rejects_stale_project_lock_metadata() -> None:
    project = offline_runner._load_toml(REPO_ROOT / "pyproject.toml")
    lock = offline_runner._load_toml(REPO_ROOT / "uv.lock")
    packages = lock["package"]
    assert isinstance(packages, list)
    project_record = next(
        item
        for item in packages
        if isinstance(item, dict) and item.get("name") == "mj-agent"
    )
    metadata = project_record["metadata"]
    assert isinstance(metadata, dict)
    requires_dev = metadata["requires-dev"]
    assert isinstance(requires_dev, dict)
    dev = requires_dev["dev"]
    assert isinstance(dev, list)
    pytest_record = next(
        item for item in dev if isinstance(item, dict) and item.get("name") == "pytest"
    )
    pytest_record["specifier"] = ">=999"

    with pytest.raises(offline_runner.RunnerError, match="does not match uv.lock metadata"):
        offline_runner._locked_versions(project, lock)


def test_offline_runner_plugins_match_project_lock_and_active_environment() -> None:
    assert offline_runner._verified_plugin_modules(REPO_ROOT) == (
        "pytest_asyncio.plugin",
        "pytest_bdd.plugin",
    )


def test_offline_runner_error_never_prints_parent_value(
    monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    sentinel = "synthetic-parent-secret-must-not-appear"
    monkeypatch.setenv("EXAMPLE_SECRET", sentinel)
    assert offline_runner.main(["../outside"], repo_root=REPO_ROOT) == 2
    captured = capsys.readouterr()
    assert sentinel not in captured.out
    assert sentinel not in captured.err
