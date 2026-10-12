"""BDD core bindings. Every input is synthetic, including actual-branch conditions."""

from __future__ import annotations

import builtins
import hashlib
import json
import socket
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from mj_agent.evaluation.core import replay as _replay
from mj_agent.evaluation.schema import ReplayInputs as _Inputs

_FIXTURES = Path(__file__).resolve().parents[3] / "unit/fixtures/eval_core"


def _rows(raw: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _jsonl(rows: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n").encode()


@pytest.fixture
def replay_inputs() -> dict[str, Any]:
    inputs = _Inputs(**{name: (_FIXTURES / filename).read_bytes() for name, filename in {
        "config": "config.json", "dataset": "dataset.jsonl", "observations": "observations.jsonl",
        "manifest": "manifest.json", "reference": "reference.json", "reviews": "reviews.jsonl",
    }.items()})
    return {"inputs": inputs}


def _observations(context: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    inputs = context["inputs"]
    raw = _jsonl(rows)
    manifest = json.loads(inputs.manifest)
    manifest["hashes"]["observations"] = hashlib.sha256(raw).hexdigest()
    context["inputs"] = replace(inputs, observations=raw, manifest=json.dumps(manifest).encode())


@given("a valid 22-case dataset and observations missing HP-01")
def missing(replay_inputs: dict[str, Any]) -> None:
    rows = _rows(replay_inputs["inputs"].observations)
    _observations(replay_inputs, [r for r in rows if r["case_id"] != "HP-01"])


@given("valid synthetic SQL and disclosure text without a bound Agent role review")
def no_review(replay_inputs: dict[str, Any]) -> None:
    replay_inputs["inputs"] = replace(replay_inputs["inputs"], reviews=b"")


@given("a first SQL attempt returning require_time_range and a later successful repair")
def repair(replay_inputs: dict[str, Any]) -> None:
    rows = _rows(replay_inputs["inputs"].observations)
    obs = next(r for r in rows if r["case_id"] == "HP-01")
    first = obs["tool_calls"][0]
    second = dict(first, sequence=2, call_id="repaired")
    first.update(sql="SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total",
                 outcome="error", error_codes=["require_time_range"])
    obs["tool_calls"].append(second)
    _observations(replay_inputs, rows)


@given("a confirmed actual red-line failure and no baseline")
def actual_condition(replay_inputs: dict[str, Any]) -> None:
    # A fictional unit condition exercises the branch; no actual observation is collected.
    inputs = replay_inputs["inputs"]
    manifest = json.loads(inputs.manifest)
    manifest["source_kind"] = "runtime_observation"
    manifest["provenance"].update(source_ref="bdd-unit-condition-not-runtime-evidence",
                                  sampling_approval_ref="unit-condition-not-authorization")
    reviews = _rows(inputs.reviews)
    for review in reviews:
        review["review_method"] = "independent_review"
    replay_inputs["inputs"] = replace(inputs, manifest=json.dumps(manifest).encode(),
                                       reviews=_jsonl(reviews))
    rows = _rows(inputs.observations)
    target = next(r for r in rows if r["case_id"] == "RL-05")
    target["tool_calls"] = [{"sequence": 1, "call_id": "blocked", "tool_name": "execute_sql",
                             "sql": "SELECT 1; DROP TABLE forbidden", "outcome": "error",
                             "error_codes": ["blocked"]}]
    _observations(replay_inputs, rows)


@given("a complete synthetic fixture whose checks all pass")
def synthetic(replay_inputs: dict[str, Any]) -> None:
    assert json.loads(replay_inputs["inputs"].manifest)["source_kind"] == "synthetic_fixture"


@given("sentinels rejecting application config imports secret-file reads and network connections")
def sentinels(replay_inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    original = builtins.__import__

    def import_guard(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "mj_agent.config" or name.startswith(("dotenv", "psycopg", "openai")):
            raise AssertionError("application import forbidden")
        return original(name, *args, **kwargs)

    def reject(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("IO forbidden in memory-only core")

    replay_inputs["modules_before"] = set(sys.modules)
    monkeypatch.setattr(builtins, "__import__", import_guard)
    monkeypatch.setattr(builtins, "open", reject)
    monkeypatch.setattr(Path, "open", reject)
    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket, "create_connection", reject)


@when("the offline runner replays the explicit inputs")
@when("the offline runner judges the case")
@when("the offline runner replays the ordered calls")
@when("the offline runner reports the run")
@when("the offline runner replays approved local fixtures")
def replay(replay_inputs: dict[str, Any]) -> None:
    replay_inputs["report"] = _replay(replay_inputs["inputs"])


@then("all 22 case results exist and HP-01 is NOT_RUN")
def preserved(replay_inputs: dict[str, Any]) -> None:
    cases = replay_inputs["report"]["cases"]
    assert len(cases) == 22
    assert next(c for c in cases if c["case_id"] == "HP-01")["status"] == "NOT_RUN"


@then("disclosure_required is REVIEW_REQUIRED")
def pending(replay_inputs: dict[str, Any]) -> None:
    case = next(c for c in replay_inputs["report"]["cases"] if c["case_id"] == "HP-01")
    assert next(c for c in case["checks"] if c["check_id"] == "output.disclosure_required")["status"] == "REVIEW_REQUIRED"


@then("the first-turn check is FAIL and both attempts remain referenced")
def first_preserved(replay_inputs: dict[str, Any]) -> None:
    case = next(c for c in replay_inputs["report"]["cases"] if c["case_id"] == "HP-01")
    assert case["status"] == "FAIL"
    assert len(case["attempts"]) == 2
    assert case["attempts"][0]["error_codes"] == ["require_time_range"]


@then("safety is HARD_FAIL and the exit code is 6")
def hard(replay_inputs: dict[str, Any]) -> None:
    assert replay_inputs["report"]["safety"]["status"] == "HARD_FAIL"
    assert replay_inputs["report"]["exit_code"] == 6


@then("runtime metrics are null and baseline_eligible is false")
def ineligible(replay_inputs: dict[str, Any]) -> None:
    report = replay_inputs["report"]
    assert report["measurement"]["metrics"] is None
    assert report["baseline_eligible"] is False
    assert report["counts"]["judged_cases"] == 22


@then("none of those forbidden accesses occurs")
def isolated(replay_inputs: dict[str, Any]) -> None:
    assert replay_inputs["report"]["counts"]["judged_cases"] == 22
    assert not any(name.startswith(("mj_agent.config", "dotenv", "psycopg", "openai"))
                   for name in set(sys.modules) - replay_inputs["modules_before"])



@given("explicit approved synthetic files with a valid complete 22-case fixture and bound Agent role reviews")
def cli_files(replay_inputs: dict[str, Any], tmp_path: Path) -> None:
    if sys.platform != "win32":
        pytest.skip("SKIP_FS_CAPABILITY_UNAVAILABLE: native CLI deferred")
    directory = tmp_path / "cli-inputs"
    directory.mkdir()
    args = ["--synthetic-fixture"]
    for field, option in {"config": "--eval-config", "dataset": "--dataset", "observations": "--observations",
                          "manifest": "--manifest", "reference": "--reference", "reviews": "--reviews"}.items():
        path = directory / f"{field}.json"
        path.write_bytes(getattr(replay_inputs["inputs"], field))
        args.extend([option, str(path)])
    replay_inputs.update(cli_root=tmp_path, cli_directory=directory, cli_args=args)


@when("the module CLI replays those bytes into two different new local output directories")
def cli_processes(replay_inputs: dict[str, Any]) -> None:
    import os
    import subprocess

    root = replay_inputs["cli_root"]
    env = {name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "WINDIR", "PATHEXT")
           if name in os.environ}
    env.update(PYTHONPATH=str(Path(__file__).parents[4] / "src"), PYTHONNOUSERSITE="1",
               PYTHONDONTWRITEBYTECODE="1", TEMP=str(root), TMP=str(root))
    results = []
    for name in ("first", "second"):
        output = root / name
        completed = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-m", "mj_agent.evaluation.runner",
             *replay_inputs["cli_args"], "--output-dir", str(output)],
            cwd=root, env=env, capture_output=True, check=False, timeout=30,
        )
        results.append((completed.returncode, (output / "report.json").read_bytes(),
                        (output / "report.md").read_bytes()))
    replay_inputs["cli_results"] = results
    replay_inputs["report"] = json.loads(results[0][1])


@then("both report pairs have identical bytes and the process exit code is 3")
def cli_deterministic(replay_inputs: dict[str, Any]) -> None:
    first, second = replay_inputs["cli_results"]
    assert first == second
    assert first[0] == replay_inputs["report"]["exit_code"] == 3
    assert b"\r" not in first[1] + first[2]
    fixed = json.loads((_FIXTURES / "expected.json").read_bytes())["case_statuses"]
    assert {c["case_id"]: c["status"] for c in replay_inputs["report"]["cases"]} == fixed


@given("a manifest declaring runtime_observation and sentinels rejecting every other input read")
def cli_actual(replay_inputs: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from mj_agent.evaluation import _file_io, runner

    cli_files(replay_inputs, tmp_path)
    manifest_path = replay_inputs["cli_directory"] / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["source_kind"] = "runtime_observation"
    manifest_path.write_bytes(json.dumps(manifest).encode())
    backend = _file_io._WindowsIO
    original = backend.read
    replay_inputs["reads"] = []

    def manifest_only(self: Any, parts: tuple[str, ...]) -> bytes:
        assert parts == ("cli-inputs", "manifest.json")
        replay_inputs["reads"].append(parts)
        return original(self, parts)

    def reject(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("actual cannot enter replay")

    monkeypatch.setattr(backend, "read", manifest_only)
    monkeypatch.setattr(runner, "replay", reject)


@when("the synthetic-only CLI is invoked")
def cli_actual_run(replay_inputs: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    from mj_agent.evaluation.runner import main

    output = replay_inputs["cli_root"] / "actual-refused"
    replay_inputs["cli_output"] = output
    replay_inputs["cli_exit"] = main([*replay_inputs["cli_args"], "--output-dir", str(output)],
                                     repo_root=replay_inputs["cli_root"])
    replay_inputs["diagnostic"] = json.loads(capsys.readouterr().err)


@then("the exit code is 2 with ACTUAL_ENTRY_DEFERRED")
def cli_deferred(replay_inputs: dict[str, Any]) -> None:
    assert replay_inputs["cli_exit"] == 2
    assert replay_inputs["diagnostic"]["reason_code"] == "ACTUAL_ENTRY_DEFERRED"


@then("replay is not called and no output directory is created")
def cli_not_replayed(replay_inputs: dict[str, Any]) -> None:
    assert replay_inputs["reads"] == [("cli-inputs", "manifest.json")]
    assert not replay_inputs["cli_output"].exists()


@given("a secret network device out-of-bound link or concurrently replaced input path")
def cli_unsafe_files(replay_inputs: dict[str, Any], tmp_path: Path) -> None:
    import os

    cli_files(replay_inputs, tmp_path)
    alias = replay_inputs["cli_directory"] / "hard-link.json"
    os.link(replay_inputs["cli_directory"] / "config.json", alias)
    replay_inputs["unsafe"] = [".env.production", "//server/share/input.json", "NUL",
                               str(tmp_path.parent / "outside.json"), str(alias)]


@when("the CLI validates and opens its explicitly named inputs")
def cli_unsafe_run(replay_inputs: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    from mj_agent.evaluation.runner import main

    results = []
    for index, path in enumerate(replay_inputs["unsafe"]):
        args = list(replay_inputs["cli_args"])
        args[args.index("--eval-config") + 1] = path
        output = replay_inputs["cli_root"] / f"refused-{index}"
        result = main([*args, "--output-dir", str(output)], repo_root=replay_inputs["cli_root"])
        results.append((result, capsys.readouterr().err, output))
    replay_inputs["unsafe_results"] = results


@then("the CLI refuses before reading protected content")
def cli_protected(replay_inputs: dict[str, Any]) -> None:
    assert all(result == 2 and not output.exists() for result, _, output in replay_inputs["unsafe_results"])


@then("the exit code is 2 without raw argv paths payloads or exception text")
def cli_diagnostics(replay_inputs: dict[str, Any]) -> None:
    for path, (result, error, _) in zip(replay_inputs["unsafe"], replay_inputs["unsafe_results"], strict=True):
        assert result == 2
        assert path not in error
        assert json.loads(error)["input_status"] == "INPUT_INVALID"


@given("a preexisting output target or a failure while writing the second report")
def cli_write_cases(replay_inputs: dict[str, Any], tmp_path: Path) -> None:
    cli_files(replay_inputs, tmp_path)
    output = tmp_path / "existing"
    output.mkdir()
    (output / "report.md").write_bytes(b"preserve prior evidence")
    replay_inputs["existing"] = output


@when("the CLI publishes a synthetic report pair")
def cli_failed_delivery(replay_inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
                        capsys: pytest.CaptureFixture[str]) -> None:
    from mj_agent.evaluation import _file_io, runner

    root = replay_inputs["cli_root"]
    args = replay_inputs["cli_args"]
    replay_inputs["existing_exit"] = runner.main([*args, "--output-dir", str(replay_inputs["existing"])],
                                                 repo_root=root)
    capsys.readouterr()
    backend = _file_io._WindowsIO
    original = backend.write

    def fail_second(self: Any, parts: tuple[str, ...], files: tuple[tuple[str, bytes], ...]) -> None:
        original(self, parts, files[:1])
        raise OSError("do-not-echo")

    monkeypatch.setattr(backend, "write", fail_second)
    partial = root / "partial"
    replay_inputs["partial"] = partial
    replay_inputs["partial_exit"] = runner.main([*args, "--output-dir", str(partial)], repo_root=root)
    replay_inputs["partial_diagnostic"] = json.loads(capsys.readouterr().err)


@then("the process exit code is 2 and existing inputs and reports remain unchanged")
def cli_old_preserved(replay_inputs: dict[str, Any]) -> None:
    assert replay_inputs["existing_exit"] == replay_inputs["partial_exit"] == 2
    assert (replay_inputs["existing"] / "report.md").read_bytes() == b"preserve prior evidence"
    assert not (replay_inputs["existing"] / "report.json").exists()
    for field in ("config", "dataset", "observations", "manifest", "reference", "reviews"):
        assert (replay_inputs["cli_directory"] / f"{field}.json").read_bytes() == getattr(replay_inputs["inputs"], field)


@then("partial newly created output is preserved without automatic cleanup")
def cli_partial_preserved(replay_inputs: dict[str, Any]) -> None:
    assert (replay_inputs["partial"] / "report.json").is_file()
    assert not (replay_inputs["partial"] / "report.md").exists()
    assert replay_inputs["partial_diagnostic"]["core_exit_code"] == 3


scenarios("../../../../capabilities/data-agent/evaluation/contracts/behavior.feature")
