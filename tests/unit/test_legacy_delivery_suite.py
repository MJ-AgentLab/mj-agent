"""Independent checks for the scoped historical-capability software refresh."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from scripts.sdd._common.bdd_helpers import (
    bdd_evidence_status,
    extract_tags,
    load_bdd_evidence,
    parse_feature_file,
)
from scripts.sdd.delivery_evidence import _acceptance_results, load_suite

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "evidence/delivery/legacy-capabilities.suite.json"
MIGRATION = ROOT / "evidence/delivery/legacy-capabilities-migration.json"
HISTORICAL_SHA = "fd045520c0123627e53d23c0ad58bf97a6b3552e"
EXPECTED_OFFLINE = {
    "data-agent.safe-sql": (
        "test_req_001_l1_guardrail",
        "test_req_001_l1_allowlist_quoting_agnostic",
        "test_req_002_l1b_precheck",
        "test_req_006_middleware_tool_message",
    ),
    "data-agent.biz-catalog": ("test_req_001_load_catalog_rejects_list_root",),
    "data-agent.llm-provider": (
        "test_req_001_ark_empty_creds",
        "test_req_002_local_no_thinking",
        "test_req_003_local_empty_sentinel",
    ),
    "data-agent.memory-checkpointer": (
        "test_req_001_rows_replaced_by_digest",
        "test_req_002_live_state_untouched",
        "test_req_003_retains_executed_sql",
    ),
    "infrastructure.mcp-server-governance": (
        "test_req_001_a14_gate_template_exists",
        "test_req_002_pg_wrapper_consistency",
    ),
    "infrastructure.docker-compose": (),
}
EXPECTED_HISTORY_COUNTS = {
    "data-agent.safe-sql": 10,
    "data-agent.biz-catalog": 1,
    "data-agent.llm-provider": 3,
    "data-agent.memory-checkpointer": 2,
    "infrastructure.docker-compose": 2,
    "infrastructure.mcp-server-governance": 2,
}
EXPECTED_CONTROLS = (
    "tests/unit/test_guardrail.py::TestParseFailureFailClosed::test_unparseable_on_allowed_table_also_rejected",
    "tests/unit/test_guardrail.py::TestQuotedIdentifierAllowlist::test_forbidden_ref_in_where_subquery_rejected",
    "tests/unit/test_guardrail.py::TestTableLevelAllowlist::test_disallowed_dwd_fact_table_rejected",
    "tests/unit/test_precheck.py::TestNoSelectStar::test_select_star_rejected",
    "tests/unit/test_precheck.py::TestParseFailureGracefulFallback::test_unparseable_sql_does_not_block",
    "tests/unit/test_memory_redaction.py::test_redact_checkpoint_live_state_untouched",
    "tests/unit/test_memory_redaction.py::test_redaction_is_idempotent",
    "tests/unit/test_memory_digest.py::test_digest_is_deterministic",
    "tests/unit/test_memory_digest.py::test_digest_contains_no_verbatim_cell_value",
    "tests/unit/test_memory_retention.py::test_uuid6_at_builder_round_trips",
    "tests/unit/test_memory_retention.py::test_epoch_rejects_non_uuid6",
)


def _documents() -> tuple[dict, dict]:
    return json.loads(SUITE.read_text("utf-8")), json.loads(MIGRATION.read_text("utf-8"))


def _scenario_bindings(path: Path) -> dict[str, tuple[str, list[str]]]:
    result = {}
    for node in ast.parse(path.read_text("utf-8")).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "scenario"):
                result[node.name] = (
                    ast.literal_eval(decorator.args[1]), [argument.arg for argument in node.args.args],
                )
    return result


def test_exact_thirteen_bdd_selections_are_real_and_have_no_external_fixture() -> None:
    suite, migration = _documents()
    assert {item["capability"] for item in migration["capabilities"]} == set(EXPECTED_OFFLINE)
    commands = {item["id"]: item for item in suite["commands"]}
    selected = []
    for capability in migration["capabilities"]:
        expected = EXPECTED_OFFLINE[capability["capability"]]
        nodes = capability["offline_bdd_nodes"]
        assert tuple(node.split("::")[-1] for node in nodes) == expected
        if not nodes:
            assert capability["software_command_id"] is None
            continue
        command = commands[capability["software_command_id"]]
        assert command["argv"][4:6] == ["python", "scripts/sdd/run_offline_pytest.py"]
        assert [arg for arg in command["argv"] if arg.startswith("tests/")] == list(
            dict.fromkeys(node.split("::", 1)[0] for node in nodes))
        assert command["argv"][command["argv"].index("-k") + 1] == " or ".join(expected)
        for identity in nodes:
            filename, name = identity.split("::")
            scenario, fixtures = _scenario_bindings(ROOT / filename)[name]
            assert fixtures == []
            assert scenario in {item["name"] for item in capability["scenarios"]}
            selected.append(identity)
    assert len(selected) == len(set(selected)) == 13


def test_collector_arguments_use_portable_file_paths_and_exact_selectors() -> None:
    suite, _ = _documents()
    for command in suite["commands"]:
        files = [arg for arg in command["argv"] if arg.startswith("tests/")]
        assert files and all("::" not in arg and (ROOT / arg).is_file() for arg in files)


def test_every_feature_scenario_has_an_honest_migration_status() -> None:
    _, migration = _documents()
    high_count = 0
    for capability in migration["capabilities"]:
        directory = ROOT / capability["path"]
        feature = parse_feature_file(directory / "contracts/behavior.feature")
        declared = {item["name"]: item for item in capability["scenarios"]}
        assert len(declared) == len(feature.scenarios)
        assert set(declared) == {scenario.name for scenario in feature.scenarios}
        for scenario in feature.scenarios:
            item = declared[scenario.name]
            high = bool(set(extract_tags(scenario).risk) & {"critical", "high"})
            high_count += int(high)
            assert item["historical_integrity"] == bdd_evidence_status(
                load_bdd_evidence(directory, scenario.name), scenario.name, directory,
            )
            assert item["g21_status"] == ("DEFERRED" if high else "NOT_APPLICABLE")
            assert item["software_status"] == "NOT_RUN_VERSION_BOUND_COLLECTOR"
            assert item["actual_runtime_status"] == "NOT_RUN"
            if item["offline_bdd_node"] is not None:
                filename, name = item["offline_bdd_node"].split("::")
                assert _scenario_bindings(ROOT / filename)[name][0] == scenario.name
                assert item["planned_evidence_kind"] == "SELFTEST"
            else:
                assert item["planned_evidence_kind"] in {"POLICY_SKIP", "NOT_RUN"}
    assert high_count == 16
    assert migration["g21_interface_migration"] == "NOT_MIGRATED"
    assert migration["claims"] == {
        "owner_accepted": False,
        "runtime_baseline_eligible": False,
        "independent_source_authenticated": False,
        "actual_runtime_verified": False,
    }


def test_original_twenty_files_equal_their_original_git_blobs() -> None:
    _, migration = _documents()
    assert migration["historical_baseline_sha"] == HISTORICAL_SHA
    recorded = {}
    env = {name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "WINDIR", "PATHEXT")
           if name in os.environ}
    for capability in migration["capabilities"]:
        directory = ROOT / capability["path"] / "evidence"
        current = {path.relative_to(ROOT).as_posix() for path in directory.rglob("*")
                   if path.is_file() and path.name != ".gitkeep"}
        files = capability["historical_files"]
        assert len(files) == EXPECTED_HISTORY_COUNTS[capability["capability"]]
        assert {item["path"] for item in files} == current
        for item in files:
            assert item["path"] not in recorded
            original = subprocess.run(
                ["git", "--no-replace-objects", "-C", str(ROOT), "cat-file", "blob",
                 f"{HISTORICAL_SHA}:{item['path']}"],
                capture_output=True, check=True, timeout=30, env=env,
            ).stdout
            assert hashlib.sha256(original).hexdigest() == item["sha256"]
            assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
            recorded[item["path"]] = item["sha256"]
    assert len(recorded) == 20


def test_suite_binds_baselines_sut_and_dependency_inputs_without_claiming_actual() -> None:
    suite, migration = _documents()
    _, digests = load_suite(SUITE, ROOT)
    assert {"pyproject.toml", "uv.lock", ".python-version"} <= set(digests["dependencies"])
    assert {"scripts/sdd/delivery_evidence.py", "scripts/sdd/run_offline_pytest.py",
            "scripts/sdd/check_test_offline_boundary.py"} <= set(digests["harness"])
    assert all(ac["mode"] == "SELFTEST_SOFTWARE" and ac["source_kind"] == "software_test"
               for unit in suite["units"] for ac in unit["acceptance"])
    bound = {path for unit in digests["units"].values()
             for field in ("baseline", "inputs") for path in unit[field]}
    for capability in migration["capabilities"]:
        if capability["offline_bdd_nodes"]:
            assert {f"{capability['path']}/requirements.md",
                    f"{capability['path']}/contracts/behavior.feature"} <= bound
            assert set(capability["sut_inputs"]) <= bound
    assert "evidence/delivery/legacy-capabilities-migration.json" in bound
    assert not any("evaluation" in path or path.endswith(".env") for path in bound)


def test_pure_controls_have_real_nodes_and_correct_junit_class_identities() -> None:
    suite, _ = _documents()
    command = next(item for item in suite["commands"] if item["id"] == "pure-regression")
    nodes = list(EXPECTED_CONTROLS)
    assert [value for value in command["argv"] if value.startswith("tests/")] == list(
        dict.fromkeys(node.split("::", 1)[0] for node in nodes))
    assert command["argv"][command["argv"].index("-k") + 1] == " or ".join(
        node.rsplit("::", 1)[-1] for node in nodes)
    expected = []
    assert len(nodes) == len(set(nodes)) == 11
    for node in nodes:
        filename, *names = node.split("::")
        tree = ast.parse((ROOT / filename).read_text("utf-8"))
        children = tree.body
        for name in names:
            definition = next(child for child in children
                              if isinstance(child, (ast.ClassDef, ast.FunctionDef))
                              and child.name == name)
            children = definition.body
        assert isinstance(definition, ast.FunctionDef)
        assert {argument.arg for argument in definition.args.args} <= {"self"}
        module = filename.removesuffix(".py").replace("/", ".")
        classname = ".".join([module, *names[:-1]])
        expected.append(f"{classname}::{names[-1]}")
    unit = next(item for item in suite["units"] if item["id"] == "pure-regression")
    assert unit["acceptance"][0]["tests"][0]["ids"] == expected


@pytest.mark.parametrize("mutation", ["missing", "skipped", "failed", "wrong_mapping"])
def test_missing_skipped_failed_or_wrong_named_case_cannot_be_selftest(mutation: str) -> None:
    suite, _ = _documents()
    unit = copy.deepcopy(next(item for item in suite["units"] if item["id"] == "safe-sql"))
    command = next(item for item in suite["commands"] if item["id"] == "safe-sql-bdd")
    prefix = "tests.bdd.data_agent.safe_sql.test_safe_sql_bdd::"
    cases = {prefix + name: "PASS" for name in EXPECTED_OFFLINE["data-agent.safe-sql"]}
    if mutation == "missing":
        cases.pop(prefix + "test_req_001_l1_guardrail")
    elif mutation in {"skipped", "failed"}:
        cases[prefix + "test_req_001_l1_guardrail"] = "SKIP" if mutation == "skipped" else "FAIL"
    else:
        unit["acceptance"][0]["tests"][0]["ids"] = [prefix + "unrelated_green_case"]
    record = {
        "id": command["id"], "exit_code": 0, "execution_error": None,
        "output_ref": "safe-sql-bdd.log",
        "test_integrity": {"tests": 4, "failed": int(mutation == "failed"),
                           "skipped": int(mutation == "skipped"), "cases": cases},
    }
    result = _acceptance_results({"commands": [command], "units": [unit]}, [record])
    assert any(ac["status"] != "SELFTEST" for ac in result[0]["acceptance"])
