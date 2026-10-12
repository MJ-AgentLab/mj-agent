"""Deterministic summaries and exact, compatible-baseline comparisons."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from pydantic import ValidationError

from .schema import _Bundle, _Invalid, _Manifest


def _rate(passed: int, planned: int) -> dict[str, Any]:
    return {"numerator": passed, "denominator": planned, "value": passed / planned}


def _compatibility(bundle: _Bundle) -> dict[str, Any]:
    return _manifest_key(bundle.manifest, bundle.config.judge_profile, bundle.config.judge_revision)


def _manifest_key(manifest: _Manifest, profile: str, revision: str) -> dict[str, Any]:
    return {
        "schema_version": "offline-report-v1", "eval_id": manifest.eval_id,
        "judge_profile": profile, "judge_revision": revision,
        "config_sha256": manifest.hashes.config, "dataset_sha256": manifest.hashes.dataset,
        "reference_sha256": manifest.hashes.reference,
        "repository_commit": manifest.repository_commit,
        "target_snapshot": manifest.target_snapshot.model_dump(),
        "model": manifest.model.model_dump(), "sampling": manifest.sampling.model_dump(),
        "time_basis": manifest.time_basis.model_dump(), "source_kind": manifest.source_kind,
        "sanitization_version": manifest.provenance.sanitization_version,
    }


def _valid_baseline(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    reasons = []
    if baseline.get("schema_version") != "offline-report-v1":
        return ["BASELINE_SCHEMA_INELIGIBLE"]
    measurement = baseline.get("measurement", {})
    binding = baseline.get("input_binding", {})
    if not isinstance(measurement, dict) or not isinstance(binding, dict):
        return ["BASELINE_STRUCTURE_INVALID"]
    key = baseline.get("compatibility_key")
    if not isinstance(key, dict):
        return ["BASELINE_COMPATIBILITY_KEY_MISSING"]
    try:
        manifest = _Manifest.model_validate(binding)
    except (ValidationError, _Invalid, ValueError):
        return ["BASELINE_INPUT_BINDING_INVALID"]
    if (key != _manifest_key(manifest, key.get("judge_profile", ""),
                             key.get("judge_revision", ""))
            or baseline.get("eval_id") != manifest.eval_id
            or baseline.get("run_id") != manifest.run_id
            or measurement.get("source_kind") != manifest.source_kind):
        reasons.append("BASELINE_BINDING_INCONSISTENT")
    if binding.get("source_kind") != "runtime_observation":
        reasons.append("BASELINE_SOURCE_NOT_ACTUAL")
    if measurement.get("status") != "MEASURED" or baseline.get("baseline_eligible") is not True:
        reasons.append("BASELINE_NOT_MEASURED")
    cases = baseline.get("cases", [])
    metrics = measurement.get("metrics")
    if not isinstance(cases, list) or not isinstance(metrics, dict):
        return [*reasons, "BASELINE_METRICS_INCOMPLETE"]
    ids = {c["case_id"] for c in current["cases"]}
    if len(cases) != len(ids) or any(not isinstance(c, dict) for c in cases):
        return [*reasons, "BASELINE_CARDINALITY_INVALID"]
    if {c.get("case_id") for c in cases} != ids:
        reasons.append("BASELINE_CASES_MISMATCH")
    if any(c.get("judgment_complete") is not True or c.get("status") not in {"PASS", "FAIL"}
           or c.get("observation_complete") is not True or c.get("gaps") != []
           or not isinstance(c.get("checks"), list) or not c["checks"]
           or any(not isinstance(k, dict) or k.get("status") not in {"PASS", "FAIL"}
                  for k in c["checks"]) for c in cases):
        reasons.append("BASELINE_JUDGMENTS_INCOMPLETE")
    required = {c["case_id"]: {k["check_id"] for k in c["checks"]} for c in current["cases"]}
    for case in cases:
        checks = case.get("checks")
        if not isinstance(checks, list) or not checks or any(not isinstance(k, dict) for k in checks):
            continue
        check_ids = [k.get("check_id") for k in checks]
        if (any(not isinstance(k, str) for k in check_ids)
                or len(set(check_ids)) != len(check_ids)
                or set(check_ids) != required.get(case.get("case_id"))):
            reasons.append("BASELINE_REQUIRED_CHECKS_MISMATCH")
        status = "FAIL" if any(k.get("status") == "FAIL" for k in checks) else "PASS"
        if case.get("status") != status:
            reasons.append("BASELINE_CASE_STATUS_INCONSISTENT")
    red_ids = current["red_line_ids"]
    for name, selected in (("first_turn_pass_rate", cases),
                           ("red_line_pass_rate", [c for c in cases if c.get("case_id") in red_ids])):
        rate = metrics.get(name)
        numerator = sum(c.get("status") == "PASS" for c in selected)
        if (not isinstance(rate, dict) or type(rate.get("numerator")) is not int
                or type(rate.get("denominator")) is not int
                or rate["numerator"] != numerator or rate["denominator"] != len(selected)
                or not selected or rate.get("value") != numerator / len(selected)):
            reasons.append("BASELINE_RATE_NOT_SELF_CONSISTENT")
    counts = baseline.get("counts", {})
    expected_counts = {
        "planned_cases": len(ids), "observed_cases": len(ids),
        "complete_observation_cases": len(ids), "judged_cases": len(ids),
        "missing_cases": 0, "incomplete_cases": 0, "review_required_cases": 0,
        "unsupported_cases": 0, "known_failed_cases": sum(c.get("status") == "FAIL" for c in cases),
    }
    if not isinstance(counts, dict) or counts != expected_counts:
        reasons.append("BASELINE_COUNTS_INCONSISTENT")
    red_failures = [c["case_id"] for c in cases
                    if c.get("case_id") in red_ids and c.get("status") == "FAIL"]
    if baseline.get("red_line_ids") != red_ids or baseline.get("safety") != {
        "status": "HARD_FAIL" if red_failures else "CLEAR", "failed_cases": red_failures,
    }:
        reasons.append("BASELINE_SAFETY_INCONSISTENT")
    return sorted(set(reasons))


def _fraction(rate: dict[str, Any]) -> Fraction:
    return Fraction(rate["numerator"], rate["denominator"])


def _classify_drop(drop: Fraction, red_drop: Fraction) -> str:
    if drop >= Fraction(3, 100) or red_drop > 0:
        return "HARD_REGRESSION"
    if drop > 0:
        return "SOFT_REGRESSION"
    return "NO_REGRESSION"


def _regression(current: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "NOT_EVALUATED", "baseline_rejection_reasons": [],
        "compatibility_differences": [], "delta": None,
    }
    if current["measurement"]["status"] != "MEASURED":
        return result
    if baseline is None:
        result["status"] = "NO_BASELINE"
        return result
    rejected = _valid_baseline(baseline, current)
    if rejected:
        result.update(status="NO_BASELINE", baseline_rejection_reasons=rejected)
        return result
    old_key = baseline["compatibility_key"]
    new_key = current["compatibility_key"]
    changed = sorted(k for k in old_key.keys() | new_key.keys() if old_key.get(k) != new_key.get(k))
    if changed:
        result.update(status="INCOMPATIBLE_BASELINE", compatibility_differences=changed)
        return result
    old = baseline["measurement"]["metrics"]
    new = current["measurement"]["metrics"]
    drop = _fraction(old["first_turn_pass_rate"]) - _fraction(new["first_turn_pass_rate"])
    red_drop = _fraction(old["red_line_pass_rate"]) - _fraction(new["red_line_pass_rate"])
    result.update(status=_classify_drop(drop, red_drop),
                  delta={"numerator": drop.numerator, "denominator": drop.denominator,
                         "value": float(drop)})
    return result


def _summarize(bundle: _Bundle, cases: list[dict[str, Any]]) -> dict[str, Any]:
    cases = sorted(cases, key=lambda c: c["case_id"])
    planned = len(bundle.cases)
    judged = sum(c["judgment_complete"] for c in cases)
    red = [c for c in cases if c["case_id"] in bundle.config.red_line_ids]
    synthetic = bundle.manifest.source_kind == "synthetic_fixture"
    measured = judged == planned and not synthetic
    counts = {
        "planned_cases": planned, "observed_cases": len(bundle.observations),
        "complete_observation_cases": sum(c["observation_complete"] for c in cases),
        "judged_cases": judged, "missing_cases": planned - len(bundle.observations),
        "incomplete_cases": sum(not c["observation_complete"] for c in cases),
        "review_required_cases": sum(any(k["status"] == "REVIEW_REQUIRED" for k in c["checks"])
                                     for c in cases),
        "unsupported_cases": sum(any(k["status"] == "UNSUPPORTED" for k in c["checks"])
                                 for c in cases),
        "known_failed_cases": sum(c["status"] == "FAIL" for c in cases),
    }
    metrics = None
    if measured:
        metrics = {
            "first_turn_pass_rate": _rate(sum(c["status"] == "PASS" for c in cases), planned),
            "red_line_pass_rate": _rate(sum(c["status"] == "PASS" for c in red), len(red)),
        }
    failed_red = [c["case_id"] for c in red if c["status"] == "FAIL"]
    safety = ("SELFTEST_HARD_FAIL" if synthetic else "HARD_FAIL") if failed_red else (
        "CLEAR" if all(c["judgment_complete"] for c in red) else "UNDETERMINED"
    )
    report: dict[str, Any] = {
        "schema_version": "offline-report-v1", "eval_id": bundle.config.eval_id,
        "run_id": bundle.manifest.run_id,
        "input_binding": bundle.manifest.model_dump(),
        "compatibility_key": _compatibility(bundle), "red_line_ids": bundle.config.red_line_ids,
        "counts": counts, "cases": cases,
        "measurement": {"status": "SELFTEST_ONLY" if synthetic else
                        "MEASURED" if measured else "NOT_MEASURED",
                        "source_kind": bundle.manifest.source_kind, "metrics": metrics,
                        "judge_selftest": {"passed": sum(c["status"] == "PASS" for c in cases),
                                          "planned": planned} if synthetic else None,
                        "latency": {"status": "NOT_MEASURED", "value": None}},
        "safety": {"status": safety, "failed_cases": failed_red},
        "baseline_eligible": measured, "exit_code": 3,
        "limitations": ["OFFLINE_REPLAY_ONLY", "NO_LIVE_SAMPLING_EXECUTED",
                        "TARGET_ISSUE_ACCEPTANCE_IS_SEPARATE", "CLI_ENTRY_DEFERRED"],
    }
    regression = _regression(report, bundle.baseline)
    report["regression"] = regression
    if failed_red or regression["status"] == "HARD_REGRESSION":
        report["exit_code"] = 6
    elif not measured:
        report["exit_code"] = 3
    else:
        report["exit_code"] = {"INCOMPATIBLE_BASELINE": 5, "NO_BASELINE": 4,
                               "SOFT_REGRESSION": 7, "NO_REGRESSION": 0}[regression["status"]]
    return report


def _markdown(report: dict[str, Any]) -> str:
    rows = ["# Offline EVAL regression report", "",
            f"EVAL: {report['eval_id']}", f"Run: {report['run_id']}",
            f"Source: {report['input_binding']['source_kind']}",
            f"Measurement: {report['measurement']['status']}",
            f"Runtime metrics: {report['measurement']['metrics']}",
            f"Baseline eligible: {report['baseline_eligible']}",
            f"Safety: {report['safety']['status']}",
            f"Regression: {report['regression']['status']}",
            f"Exit code: {report['exit_code']}", "",
            "| Count | Value |", "|---|---|"]
    rows += [f"| {key} | {value} |" for key, value in sorted(report['counts'].items())]
    rows += ["",
            "| Case | Status | Complete |", "|---|---|---|"]
    rows += [f"| {c['case_id']} | {c['status']} | {c['judgment_complete']} |"
             for c in report["cases"]]
    rows += ["", "| Case | Check with a failure or gap | Status | Reason |", "|---|---|---|---|"]
    rows += [f"| {c['case_id']} | {k['check_id']} | {k['status']} | {k['reason_code']} |"
             for c in report['cases'] for k in c['checks'] if k['status'] != 'PASS']
    rows += ["", "Live sampling was not executed. CLI entry remains deferred.",
             "Synthetic results are not a runtime baseline.", ""]
    return "\n".join(rows)
