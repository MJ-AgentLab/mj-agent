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

from mj_agent.evaluation.core import _Inputs, _replay

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


scenarios("../../../../capabilities/data-agent/evaluation/contracts/behavior.feature")
