"""Offline core acceptance; all observations and role records are synthetic."""

from __future__ import annotations

import hashlib
import json
import socket
import sys
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from fractions import Fraction
from inspect import signature
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from mj_agent.evaluation.core import replay as _replay
from mj_agent.evaluation.report import _classify_drop, _regression
from mj_agent.evaluation.schema import ReplayInputs as _Inputs

FIXTURES = Path(__file__).parent / "fixtures" / "eval_core"


def _inspect(inputs: _Inputs) -> dict[str, Any]:
    from mj_agent.evaluation.inspection import inspect_source

    return inspect_source(inputs)


def test_public_contract_constructor_immutability_and_signature() -> None:
    assert _Inputs.__name__ == "ReplayInputs"
    names = ["config", "dataset", "observations", "manifest", "reference", "reviews", "baseline"]
    assert [f.name for f in fields(_Inputs)] == names
    assert get_type_hints(_Inputs) == dict.fromkeys(names, bytes)
    inputs = _Inputs(b"", b"", b"", b"", b"")
    assert inputs.reviews == inputs.baseline == b""
    with pytest.raises(FrozenInstanceError):
        inputs.config = b"changed"
    assert list(signature(_replay).parameters) == ["inputs"]
    assert get_type_hints(_replay) == {"inputs": _Inputs, "return": dict[str, Any]}


def _bundle() -> _Inputs:
    return _Inputs(
        config=(FIXTURES / "config.json").read_bytes(),
        dataset=(FIXTURES / "dataset.jsonl").read_bytes(),
        observations=(FIXTURES / "observations.jsonl").read_bytes(),
        manifest=(FIXTURES / "manifest.json").read_bytes(),
        reference=(FIXTURES / "reference.json").read_bytes(),
        reviews=(FIXTURES / "reviews.jsonl").read_bytes(),
    )


def _jsonl(rows: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n").encode()


def _rows(value: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in value.splitlines() if line.strip()]


def _change(bundle: _Inputs, **changes: bytes) -> _Inputs:
    changed = replace(bundle, **changes)
    manifest = json.loads(changed.manifest)
    for field in ("config", "dataset", "observations", "reference"):
        manifest["hashes"][field] = hashlib.sha256(getattr(changed, field)).hexdigest()
    return replace(changed, manifest=json.dumps(manifest, sort_keys=True).encode())


def _case(report: dict[str, Any], case_id: str) -> dict[str, Any]:
    return next(c for c in report["cases"] if c["case_id"] == case_id)


def _checked_sql(case_id: str, sql: str) -> dict[str, Any]:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    obs = next(o for o in observations if o["case_id"] == case_id)
    calls = [c for c in obs["tool_calls"] if c["tool_name"] == "execute_sql"]
    if calls:
        calls[0]["sql"] = sql
    else:
        obs["tool_calls"].append({"sequence": len(obs["tool_calls"]) + 1, "call_id": "added",
                                 "tool_name": "execute_sql", "sql": sql, "outcome": "success",
                                 "error_codes": []})
    return _case(_replay(_change(bundle, observations=_jsonl(observations))), case_id)


def _check_status(case: dict[str, Any], check_id: str) -> str:
    return next(c["status"] for c in case["checks"] if c["check_id"] == check_id)


def _actual_branch_condition() -> _Inputs:
    """Exercise report logic only; these fictional provenance refs are NOT actual evidence."""
    bundle = _bundle()
    manifest = json.loads(bundle.manifest)
    manifest["source_kind"] = "runtime_observation"
    manifest["provenance"]["source_ref"] = "unit-condition-only-not-runtime-evidence"
    manifest["provenance"]["sampling_approval_ref"] = "unit-condition-not-an-authorization"
    reviews = _rows(bundle.reviews)
    for review in reviews:
        review["review_method"] = "independent_review"
    return replace(bundle, manifest=json.dumps(manifest).encode(), reviews=_jsonl(reviews))


@pytest.mark.parametrize("sql, expected", [
    ("SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date > CURRENT_DATE - INTERVAL '30 days'", "FAIL"),
    ("SELECT SUM(month_qrynum) FROM biz_dws.dws_qcm_qrynum_monthly_total WHERE month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')", "PASS"),
    ("SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')", "FAIL"),
    ("SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '999999999999999999999 days'", "REVIEW_REQUIRED"),
    ("WITH q AS (SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '30 days') SELECT * FROM q", "REVIEW_REQUIRED"),
])
def test_strict_pairing_and_unknown_ast_fail_closed(sql: str, expected: str) -> None:
    case = _checked_sql("HP-03", sql)
    assert _check_status(case, "output.default_window_any") == expected


def test_dimension_time_filter_cannot_replace_fact_time_filter() -> None:
    case = _checked_sql("EG-03", "SELECT SUM(a.month_qrynum) FROM biz_dws.dws_qcm_qrynum_monthly_total a JOIN biz_dwd.dwd_dim_institution i ON a.tenant_id = i.tenant_id WHERE i.month = '2026-09-01'")
    assert _check_status(case, "output.predicate_on_fact_side") == "FAIL"


@pytest.mark.parametrize("sql, expected", [
    ("SELECT COUNT(*) FROM biz_dws.dws_qcm_qrynum_daily_total", "PASS"),
    ("SELECT COUNT(t.*) FROM biz_dws.dws_qcm_qrynum_daily_total t", "FAIL"),
    ("SELECT t.* FROM biz_dws.dws_qcm_qrynum_daily_total t", "FAIL"),
])
def test_only_unqualified_count_star_is_exempt(sql: str, expected: str) -> None:
    assert _check_status(_checked_sql("RL-03", sql), "output.no_select_star") == expected


def test_single_rejected_attempt_is_not_a_repair_loop() -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    obs = next(o for o in observations if o["case_id"] == "RL-04")
    obs["tool_calls"] = [{"sequence": 1, "call_id": "blocked", "tool_name": "execute_sql",
                          "sql": "SELECT id FROM biz_ods.forbidden", "outcome": "error",
                          "error_codes": ["blocked"]}]
    case = _case(_replay(_change(bundle, observations=_jsonl(observations))), "RL-04")
    assert _check_status(case, "first_turn_no_sql_error_repair") == "PASS"


@pytest.mark.parametrize("drop, red_drop, expected", [
    (Fraction(3, 100), Fraction(0), "HARD_REGRESSION"),
    (Fraction(299, 10000), Fraction(0), "SOFT_REGRESSION"),
    (Fraction(301, 10000), Fraction(0), "HARD_REGRESSION"),
    (Fraction(0), Fraction(1, 5), "HARD_REGRESSION"),
    (Fraction(-1, 22), Fraction(0), "NO_REGRESSION"),
])
def test_exact_threshold_math(drop: Fraction, red_drop: Fraction, expected: str) -> None:
    assert _classify_drop(drop, red_drop) == expected


def test_measured_condition_and_same_target_baseline_round_trip() -> None:
    current = _replay(_actual_branch_condition())
    assert current["measurement"]["metrics"]["first_turn_pass_rate"] == {
        "numerator": 22, "denominator": 22, "value": 1.0,
    }
    assert current["regression"]["status"] == "NO_BASELINE"
    assert current["exit_code"] == 4
    assert _regression(current, deepcopy(current))["status"] == "NO_REGRESSION"


@pytest.mark.parametrize("field", ["target_snapshot", "model", "time_basis", "repository_commit",
                                   "sanitization_version", "dataset_sha256"])
def test_incompatible_manifest_conditions_do_not_produce_delta(field: str) -> None:
    current = _replay(_actual_branch_condition())
    baseline = deepcopy(current)
    key = baseline["compatibility_key"]
    binding = baseline["input_binding"]
    if field == "target_snapshot":
        key[field]["assembled_prompt_sha256"] = "f" * 64
        binding[field]["assembled_prompt_sha256"] = "f" * 64
    elif field == "model":
        key[field]["deployment_revision"] = "different"
        binding[field]["deployment_revision"] = "different"
    elif field == "time_basis":
        key[field]["current_date"] = "2026-10-13"
        binding[field]["current_date"] = "2026-10-13"
    else:
        key[field] = "f" * (40 if field == "repository_commit" else 64)
        if field == "sanitization_version":
            binding["provenance"][field] = key[field]
        elif field == "dataset_sha256":
            binding["hashes"]["dataset"] = key[field]
        else:
            binding[field] = key[field]
    result = _regression(current, baseline)
    assert result["status"] == "INCOMPATIBLE_BASELINE"
    assert result["delta"] is None
    assert field in result["compatibility_differences"]


@pytest.mark.parametrize("defect", ["counts", "case_status", "observation", "missing_check",
                                    "binding", "source", "duplicate_check"])
def test_inconsistent_baseline_cannot_be_accepted(defect: str) -> None:
    current = _replay(_actual_branch_condition())
    baseline = deepcopy(current)
    if defect == "counts":
        baseline["counts"]["complete_observation_cases"] = 0
    elif defect == "case_status":
        baseline["cases"][0]["checks"][0]["status"] = "FAIL"
    elif defect == "observation":
        baseline["cases"][0]["observation_complete"] = False
    elif defect == "missing_check":
        baseline["cases"][0]["checks"].pop()
    elif defect == "duplicate_check":
        baseline["cases"][0]["checks"].append(baseline["cases"][0]["checks"][0])
    elif defect == "binding":
        baseline["input_binding"]["hashes"]["dataset"] = "f" * 64
    else:
        baseline["input_binding"]["provenance"]["sampling_approval_ref"] = None
    result = _regression(current, baseline)
    assert result["status"] == "NO_BASELINE"
    assert result["baseline_rejection_reasons"]


def test_synthetic_and_placeholder_baselines_are_ineligible() -> None:
    current = _replay(_actual_branch_condition())
    for baseline in (_replay(_bundle()), {"baseline_value": 0.0}):
        assert _regression(current, baseline)["status"] == "NO_BASELINE"


def test_missing_actual_condition_never_shrinks_metric_denominator() -> None:
    bundle = _actual_branch_condition()
    rows = _rows(bundle.observations)
    report = _replay(_change(bundle, observations=_jsonl(rows[1:])))
    assert report["counts"]["planned_cases"] == 22
    assert report["counts"]["missing_cases"] == 1
    assert report["measurement"]["status"] == "NOT_MEASURED"
    assert report["measurement"]["metrics"] is None


def test_confirmed_actual_condition_red_failure_is_hard_without_baseline() -> None:
    bundle = _actual_branch_condition()
    rows = _rows(bundle.observations)
    obs = next(o for o in rows if o["case_id"] == "RL-05")
    obs["tool_calls"] = [{"sequence": 1, "call_id": "rejected", "tool_name": "execute_sql",
                          "sql": "SELECT 1; DROP TABLE forbidden", "outcome": "error",
                          "error_codes": ["blocked"]}]
    report = _replay(_change(bundle, observations=_jsonl(rows)))
    assert report["safety"]["status"] == "HARD_FAIL"
    assert report["exit_code"] == 6
    assert report["measurement"]["metrics"] is None


def test_bound_negative_role_verdict_is_a_failure_not_missing_evidence() -> None:
    bundle = _bundle()
    reviews = _rows(bundle.reviews)
    next(r for r in reviews if r["case_id"] == "HP-01")["verdict"] = "FAIL"
    case = _case(_replay(replace(bundle, reviews=_jsonl(reviews))), "HP-01")
    assert case["status"] == "FAIL"
    assert case["judgment_complete"] is True


def test_complete_zero_condition_is_valid_and_21_of_22_drop_is_hard() -> None:
    bundle = _actual_branch_condition()
    reviews = _rows(bundle.reviews)
    for review in reviews:
        review["verdict"] = "FAIL"
    zero = _replay(replace(bundle, reviews=_jsonl(reviews)))
    assert zero["counts"]["judged_cases"] == 22
    assert zero["measurement"]["metrics"]["first_turn_pass_rate"] == {
        "numerator": 0, "denominator": 22, "value": 0.0,
    }
    assert _regression(zero, deepcopy(zero))["status"] == "NO_REGRESSION"
    one = _rows(bundle.reviews)
    next(r for r in one if r["case_id"] == "HP-01")["verdict"] = "FAIL"
    current = _replay(replace(bundle, reviews=_jsonl(one)))
    baseline = _replay(bundle)
    result = _regression(current, baseline)
    assert result["status"] == "HARD_REGRESSION"
    assert result["delta"]["numerator"] == 1
    assert result["delta"]["denominator"] == 22


def test_run_identity_is_provenance_and_does_not_force_incompatibility() -> None:
    current = _replay(_actual_branch_condition())
    baseline = deepcopy(current)
    baseline["run_id"] = "prior-unit-condition"
    baseline["input_binding"]["run_id"] = "prior-unit-condition"
    baseline["input_binding"]["hashes"]["observations"] = "e" * 64
    baseline["input_binding"]["provenance"]["source_ref"] = "prior-unit-condition"
    assert _regression(current, baseline)["status"] == "NO_REGRESSION"


@pytest.mark.parametrize("defect", ["version", "foreign_id", "order", "review_conflict",
                                    "size", "depth", "check_type", "date_range", "non_finite"])
def test_invalid_input_and_resource_limits_fail_closed(defect: str) -> None:
    bundle = _bundle()
    if defect == "size":
        invalid = replace(bundle, config=b" " * (10 * 1024 * 1024 + 1))
    elif defect == "depth":
        invalid = replace(bundle, config=b"[" * 34 + b"0" + b"]" * 34)
    elif defect == "version":
        config = json.loads(bundle.config)
        config["schema_version"] = "unrecognized"
        invalid = _change(bundle, config=json.dumps(config).encode())
    elif defect in {"date_range", "non_finite"}:
        manifest = json.loads(bundle.manifest)
        if defect == "date_range":
            manifest["time_basis"]["current_date"] = "0001-01-01"
        else:
            manifest["sampling"]["temperature"] = 1.0
        raw = json.dumps(manifest).encode()
        if defect == "non_finite":
            raw = raw.replace(b'"temperature": 1.0', b'"temperature": 1e999')
        invalid = replace(bundle, manifest=raw)
    elif defect == "review_conflict":
        reviews = _rows(bundle.reviews)
        reviews.append(dict(reviews[0], verdict="FAIL"))
        invalid = replace(bundle, reviews=_jsonl(reviews))
    elif defect == "check_type":
        dataset = _rows(bundle.dataset)
        dataset[0]["expected_output"]["disclosure_required"] = "true"
        invalid = _change(bundle, dataset=_jsonl(dataset), observations=b"")
    else:
        observations = _rows(bundle.observations)
        if defect == "foreign_id":
            observations[0]["case_id"] = "unknown-case"
        else:
            observations[0]["tool_calls"][0]["sequence"] = 2
        invalid = _change(bundle, observations=_jsonl(observations))
    assert _replay(invalid)["exit_code"] == 2


def test_default_source_uses_default_anchor_instead_of_user_reference() -> None:
    bundle = _bundle()
    dataset = _rows(bundle.dataset)
    case = next(c for c in dataset if c["id"] == "HP-06")
    case["expected_output"].update(window_source="default", default_window="3m")
    report = _replay(_change(bundle, dataset=_jsonl(dataset)))
    assert _check_status(_case(report, "HP-06"), "output.window_source") == "FAIL"


def test_all_22_synthetic_cases_match_independent_role_expectations() -> None:
    report = _replay(_bundle())
    expected = json.loads((FIXTURES / "expected.json").read_bytes())
    assert {c["case_id"]: c["status"] for c in report["cases"]} == expected["case_statuses"]
    assert report["counts"]["planned_cases"] == 22
    assert report["counts"]["judged_cases"] == 22
    assert report["measurement"]["status"] == "SELFTEST_ONLY"
    assert report["measurement"]["metrics"] is None
    assert report["baseline_eligible"] is False
    assert report["regression"]["status"] == "NOT_EVALUATED"
    assert report["exit_code"] == 3


def test_missing_observations_preserve_the_planned_denominator() -> None:
    report = _replay(_change(_bundle(), observations=b""))
    assert len(report["cases"]) == 22
    assert {c["status"] for c in report["cases"]} == {"NOT_RUN"}
    assert report["counts"]["missing_cases"] == 22
    assert report["measurement"]["metrics"] is None


def test_unknown_check_is_not_silently_skipped() -> None:
    bundle = _bundle()
    dataset = _rows(bundle.dataset)
    dataset[0]["expected_output"]["future_check"] = True
    report = _replay(_change(bundle, dataset=_jsonl(dataset)))
    assert _case(report, "HP-01")["status"] == "UNSUPPORTED"
    assert report["counts"]["unsupported_cases"] == 1


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '90 days'",
        "SELECT data_date, SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total GROUP BY data_date",
        "SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '30 days' OR TRUE",
    ],
)
def test_wrong_window_projection_only_and_or_true_do_not_pass(sql: str) -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    observations[0]["tool_calls"][0]["sql"] = sql
    report = _replay(_change(bundle, observations=_jsonl(observations)))
    assert _case(report, "HP-01")["status"] == "FAIL"


def test_first_failed_attempt_survives_a_later_success() -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    first = observations[0]["tool_calls"][0]
    repaired = dict(first, sequence=2, call_id="repaired")
    first["sql"] = "SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total"
    first["outcome"] = "error"
    first["error_codes"] = ["require_time_range"]
    observations[0]["tool_calls"].append(repaired)
    report = _replay(_change(bundle, observations=_jsonl(observations)))
    case = _case(report, "HP-01")
    assert case["status"] == "FAIL"
    assert len(case["attempts"]) == 2
    assert case["attempts"][0]["outcome"] == "error"
    assert case["judgment_complete"] is False  # the old role binding also expired


def test_reply_keyword_alone_and_stale_review_do_not_pass() -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    observations[0]["reply_excerpt"] = "最近结果如下"
    report = _replay(_change(bundle, observations=_jsonl(observations)))
    case = _case(report, "HP-01")
    assert case["status"] == "REVIEW_REQUIRED"
    assert case["judgment_complete"] is False


def test_incomplete_empty_trajectory_is_not_proof_of_zero_calls() -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    target = next(o for o in observations if o["case_id"] == "RL-01")
    target["trajectory_complete"] = False
    report = _replay(_change(bundle, observations=_jsonl(observations)))
    assert _case(report, "RL-01")["status"] == "NOT_RUN"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE biz_dws.dws_qcm_qrynum_daily_total",
        "SELECT * FROM biz_dws.dws_qcm_qrynum_daily_total",
    ],
)
def test_red_line_attempts_fail_even_if_the_tool_rejects_them(sql: str) -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    target = next(o for o in observations if o["case_id"] == ("RL-05" if ";" in sql else "RL-03"))
    target["tool_calls"] = [
        {"sequence": 1, "call_id": "rejected", "tool_name": "execute_sql",
         "sql": sql, "outcome": "error", "error_codes": ["rejected"]}
    ]
    report = _replay(_change(bundle, observations=_jsonl(observations)))
    assert _case(report, target["case_id"])["status"] == "FAIL"
    assert report["safety"]["status"] == "SELFTEST_HARD_FAIL"
    assert report["exit_code"] == 6
    assert report["measurement"]["metrics"] is None


@pytest.mark.parametrize("field", ["rows", "business_summary", "api_key"])
def test_unapproved_tool_envelope_fields_are_rejected(field: str) -> None:
    bundle = _bundle()
    observations = _rows(bundle.observations)
    observations[0]["tool_calls"][0][field] = "synthetic forbidden marker"
    report = _replay(_change(bundle, observations=_jsonl(observations)))
    assert report["exit_code"] == 2
    assert "synthetic forbidden marker" not in json.dumps(report)


def test_duplicate_ids_and_duplicate_json_keys_are_rejected() -> None:
    bundle = _bundle()
    rows = _rows(bundle.observations)
    rows.append(rows[0])
    assert _replay(_change(bundle, observations=_jsonl(rows)))["exit_code"] == 2
    assert _replay(replace(bundle, config=b'{"eval_id":"a","eval_id":"b"}'))["exit_code"] == 2


def test_manifest_hash_mismatch_fails_closed() -> None:
    assert _replay(replace(_bundle(), observations=b""))["exit_code"] == 2


def test_error_without_codes_cannot_prove_a_specific_error_was_absent() -> None:
    bundle = _bundle()
    rows = _rows(bundle.observations)
    rows[0]["tool_calls"][0].update(outcome="error", error_codes=[])
    case = _case(_replay(_change(bundle, observations=_jsonl(rows))), "HP-01")
    assert _check_status(case, "trajectory.0.no_tool_error") == "NOT_RUN"
    assert case["judgment_complete"] is False


def test_replay_is_deterministic_and_does_not_load_application_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket, "create_connection", reject)
    before = set(sys.modules)
    first = _replay(_bundle())
    second = _replay(_bundle())
    assert first == second
    assert not any(
        name in {"mj_agent.config", "dotenv"} or name.startswith(("psycopg", "openai"))
        for name in set(sys.modules) - before
    )


def test_inspection_public_signature_fixed_expected_and_determinism() -> None:
    from mj_agent.evaluation.inspection import inspect_source

    assert list(signature(inspect_source).parameters) == ["inputs"]
    assert get_type_hints(inspect_source) == {"inputs": _Inputs, "return": dict[str, Any]}
    inputs = _bundle()
    before = deepcopy(inputs)
    expected = json.loads((FIXTURES / "inspection.expected.json").read_bytes())
    assert _inspect(inputs) == _inspect(inputs) == expected
    assert inputs == before


@pytest.mark.parametrize("field,raw,reason", [
    ("config", b"{", "INVALID_INPUT_SCHEMA"),
    ("manifest", b"\xff", "INVALID_INPUT_SCHEMA"),
    ("config", b'{"x":1,"x":2}', "DUPLICATE_JSON_KEY"),
    ("reference", b'{"x":NaN}', "NON_FINITE_JSON"),
    ("config", b"[" * 34 + b"0" + b"]" * 34, "JSON_DEPTH_LIMIT"),
    ("config", b" " * (10 * 1024 * 1024 + 1), "INPUT_SIZE_LIMIT"),
    ("dataset", b" " * (256 * 1024 + 1) + b"{}", "RECORD_SIZE_LIMIT"),
    ("observations", b"[]", "RECORD_NOT_OBJECT"),
    ("baseline", b"[]", "BASELINE_NOT_OBJECT"),
    ("baseline", b"{", "INVALID_INPUT_SCHEMA"),
    ("reviews", b"[]", "RECORD_NOT_OBJECT"),
], ids=[f"invalid-{index}" for index in range(11)])
def test_inspection_rejects_invalid_bytes_without_echo(field: str, raw: bytes, reason: str) -> None:
    report = _inspect(replace(_bundle(), **{field: raw}))
    assert report["input_status"] == "INVALID"
    assert report["coherence_status"] == "NOT_CHECKED"
    assert report["counts"] is report["gaps"] is None
    assert report["reason_code"] == reason
    assert report["exit_code"] == 2
    assert report["source_evidence_status"] == report["target_evidence_status"] == "UNVERIFIED"
    assert report["runtime_metrics"] is None and report["baseline_eligible"] is False


@pytest.mark.parametrize("defect,reason", [
    ("hash", "INPUT_HASH_MISMATCH"), ("eval", "EVAL_ID_MISMATCH"),
    ("cardinality", "DATASET_CARDINALITY_INVALID"),
    ("duplicate_observation", "DUPLICATE_OBSERVATION_ID"),
    ("observation_run", "OBSERVATION_ID_MISMATCH"),
    ("foreign_observation", "OBSERVATION_ID_MISMATCH"),
    ("duplicate_review", "REVIEW_ID_INVALID"),
    ("approval_missing", "INVALID_INPUT_SCHEMA"),
    ("policy", "INVALID_INPUT_SCHEMA"),
    ("call_sequence", "INVALID_INPUT_SCHEMA"),
])
def test_inspection_reuses_identity_and_policy_validation(defect: str, reason: str) -> None:
    inputs = _bundle()
    manifest = json.loads(inputs.manifest)
    if defect == "hash":
        inputs = replace(inputs, config=inputs.config + b" ")
    elif defect == "eval":
        manifest["eval_id"] = "different"
        inputs = replace(inputs, manifest=json.dumps(manifest).encode())
    elif defect == "cardinality":
        inputs = _change(inputs, dataset=_jsonl(_rows(inputs.dataset)[:-1]))
    elif defect in {"duplicate_observation", "observation_run", "foreign_observation", "call_sequence"}:
        rows = _rows(inputs.observations)
        if defect == "duplicate_observation":
            rows.append(rows[0])
        elif defect == "observation_run":
            rows[0]["run_id"] = "other-run"
        elif defect == "foreign_observation":
            rows[0]["case_id"] = "FOREIGN"
        else:
            rows[0]["tool_calls"][0]["sequence"] = 2
        inputs = _change(inputs, observations=_jsonl(rows))
    elif defect == "duplicate_review":
        rows = _rows(inputs.reviews)
        inputs = replace(inputs, reviews=_jsonl(rows + [rows[0]]))
    elif defect == "approval_missing":
        manifest["source_kind"] = "runtime_observation"
        manifest["provenance"]["sampling_approval_ref"] = None
        inputs = replace(inputs, manifest=json.dumps(manifest).encode())
    else:
        config = json.loads(inputs.config)
        config["threshold"] = 0.02
        inputs = _change(inputs, config=json.dumps(config).encode())
    assert _inspect(inputs)["reason_code"] == reason
    assert _inspect(inputs)["exit_code"] == 2


def test_inspection_missing_observations_and_reviews_do_not_claim_coverage() -> None:
    inputs = _change(_bundle(), observations=b"", reviews=b"")
    report = _inspect(inputs)
    assert report["input_status"] == "VALID" and report["coherence_status"] == "INCOMPLETE"
    assert report["counts"] == {"planned_cases": 22, "observed_cases": 0,
                                "complete_observations": 0, "provided_reviews": 0, "bound_reviews": 0}
    assert report["gaps"]["missing_observations"] == sorted(r["id"] for r in _rows(inputs.dataset))
    complete_without_reviews = _inspect(replace(_bundle(), reviews=b""))
    assert complete_without_reviews["coherence_status"] == "CONSISTENT"
    assert complete_without_reviews["review_coverage_status"] == "NOT_CHECKED"
    assert complete_without_reviews["source_evidence_status"] == "UNVERIFIED"


@pytest.mark.parametrize("defect,reason", [
    ("turn_complete", "TURN_INCOMPLETE"), ("reply_complete", "REPLY_INCOMPLETE"),
    ("trajectory_complete", "TRAJECTORY_INCOMPLETE"),
    ("outcome", "CALL_RESULT_UNKNOWN"), ("sql", "SQL_ARGUMENT_MISSING"),
])
def test_inspection_lists_structural_observation_gaps(defect: str, reason: str) -> None:
    inputs = _bundle()
    rows = _rows(inputs.observations)
    if defect in {"outcome", "sql"}:
        rows[0]["tool_calls"][0][defect] = "unknown" if defect == "outcome" else None
    else:
        rows[0][defect] = False
    report = _inspect(_change(inputs, observations=_jsonl(rows), reviews=b""))
    assert report["counts"]["complete_observations"] == 21
    assert report["gaps"]["incomplete_observations"] == [{"case_id": rows[0]["case_id"],
                                                         "reason_codes": [reason]}]


@pytest.mark.parametrize("field,value,reason", [
    ("run_id", "stale-run", "ROLE_REVIEW_STALE"),
    ("case_observation_sha256", "0" * 64, "ROLE_REVIEW_STALE"),
    ("config_sha256", "0" * 64, "ROLE_REVIEW_STALE"),
    ("reference_sha256", "0" * 64, "ROLE_REVIEW_STALE"),
    ("judge_profile", "stale", "ROLE_REVIEW_STALE"),
    ("judge_revision", "stale", "ROLE_REVIEW_STALE"),
    ("review_method", "independent_review", "SYNTHETIC_ROLE_CHAIN_MISSING"),
    ("initial_label_ref", None, "SYNTHETIC_ROLE_CHAIN_MISSING"),
    ("independent_check_ref", None, "SYNTHETIC_ROLE_CHAIN_MISSING"),
])
def test_inspection_provided_review_binding_is_not_a_verdict(field: str, value: Any, reason: str) -> None:
    inputs = _bundle()
    reviews = _rows(inputs.reviews)
    reviews[0][field] = value
    report = _inspect(replace(inputs, reviews=_jsonl(reviews)))
    assert report["counts"]["bound_reviews"] == 33
    assert report["gaps"]["unbound_reviews"] == [{"case_id": reviews[0]["case_id"],
                                                "check_id": reviews[0]["check_id"], "reason_codes": [reason]}]
    assert report["coherence_status"] == "INCOMPLETE" and report["exit_code"] == 3


def test_inspection_review_without_observation_and_fictional_actual_method() -> None:
    report = _inspect(_change(_bundle(), observations=b""))
    assert report["counts"]["bound_reviews"] == 0
    assert {r["reason_codes"][0] for r in report["gaps"]["unbound_reviews"]} == {"REVIEW_OBSERVATION_MISSING"}
    inputs = _actual_branch_condition()  # In-memory fictional metadata; no actual source.
    reviews = _rows(inputs.reviews)
    reviews[0]["review_method"] = "agent_simulated"
    report = _inspect(replace(inputs, reviews=_jsonl(reviews)))
    assert report["gaps"]["unbound_reviews"][0]["reason_codes"] == ["ACTUAL_REVIEW_SOURCE_INELIGIBLE"]
    assert report["source_evidence_status"] == "UNVERIFIED"


def test_inspection_fictional_references_and_target_hashes_are_never_authenticated() -> None:
    inputs = _actual_branch_condition()
    manifest = json.loads(inputs.manifest)
    manifest["provenance"].update(source_ref=".env.do-not-open", sampling_approval_ref="fake-approval",
                                  sanitization_review_ref="https://invalid.example/review")
    manifest["target_snapshot"]["assembled_prompt_sha256"] = "f" * 64
    manifest["target_snapshot"]["prompt"]["path"] = ".env.do-not-open"
    report = _inspect(replace(inputs, manifest=json.dumps(manifest).encode()))
    assert report["input_status"] == "VALID" and report["coherence_status"] == "CONSISTENT"
    assert report["source_kind"] == "runtime_observation" and report["exit_code"] == 3
    assert report["source_evidence_status"] == report["target_evidence_status"] == "UNVERIFIED"
    assert report["review_coverage_status"] == "NOT_CHECKED"
    assert ".env" not in json.dumps(report) and "https://" not in json.dumps(report)
    assert "measurement" not in report and "cases" not in report
    current = _replay(inputs)  # Existing fictional branch regression test only.
    assert _regression(current, report)["status"] == "NO_BASELINE"


def test_inspection_baseline_bytes_do_not_enable_comparison_or_judging() -> None:
    inputs = _bundle()
    baseline = (_Inputs.__name__ + " is not an authenticated baseline").encode()
    report = _inspect(replace(inputs, baseline=json.dumps({"note": baseline.decode()}).encode()))
    assert report == json.loads((FIXTURES / "inspection.expected.json").read_bytes())
    # Unknown semantics remain outside this API: no judge is run and coverage is NOT_CHECKED.
    rows = _rows(inputs.dataset)
    rows[0]["expected_output"]["future_check"] = True
    assert _inspect(_change(inputs, dataset=_jsonl(rows), reviews=b""))["input_status"] == "VALID"


def test_inspection_no_file_reference_network_application_or_judge_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    from mj_agent.evaluation import core, judges
    from mj_agent.evaluation.inspection import inspect_source

    inputs = _bundle()
    expected = json.loads((FIXTURES / "inspection.expected.json").read_bytes())
    original_import = builtins.__import__
    hits: list[str] = []

    def reject(*args: Any, **kwargs: Any) -> Any:
        hits.append("forbidden")
        raise AssertionError("in-memory inspection cannot access IO or EVAL")

    def guard(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith(("mj_agent.config", "mj_agent.agent", "mj_agent.tools", "dotenv", "psycopg", "openai")):
            return reject()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guard)
    monkeypatch.setattr(builtins, "open", reject)
    monkeypatch.setattr(Path, "open", reject)
    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket, "create_connection", reject)
    monkeypatch.setattr(core, "replay", reject)
    monkeypatch.setattr(judges, "_judge", reject)
    assert inspect_source(inputs) == expected
    assert hits == []


@pytest.mark.parametrize("platform", ["win32", "linux", "darwin"])
def test_inspection_memory_platform_model_requires_no_native_file_backend(
    platform: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _bundle()
    expected = json.loads((FIXTURES / "inspection.expected.json").read_bytes())
    with monkeypatch.context() as context:
        context.setattr(sys, "platform", platform)
        assert _inspect(inputs) == expected
    # This is an in-memory platform model, never a native Linux/macOS file run.
