"""Inspect explicit bytes for structural coherence, never source authenticity or EVAL."""

from __future__ import annotations

from typing import Any

from .schema import _INPUT_ERRORS, ReplayInputs, _Bundle, _Invalid, _load, _Observation, _Review


def _observation_gaps(observation: _Observation) -> list[str]:
    reasons = [reason for complete, reason in (
        (observation.turn_complete, "TURN_INCOMPLETE"),
        (observation.reply_complete, "REPLY_INCOMPLETE"),
        (observation.trajectory_complete, "TRAJECTORY_INCOMPLETE"),
    ) if not complete]
    if any(call.outcome == "unknown" for call in observation.tool_calls):
        reasons.append("CALL_RESULT_UNKNOWN")
    if any(call.tool_name == "execute_sql" and call.sql is None for call in observation.tool_calls):
        reasons.append("SQL_ARGUMENT_MISSING")
    return reasons


def _review_gaps(bundle: _Bundle, review: _Review) -> list[str]:
    if review.case_id not in bundle.observations:
        return ["REVIEW_OBSERVATION_MISSING"]
    if not (
        review.run_id == bundle.manifest.run_id
        and review.case_observation_sha256 == bundle.observation_hashes[review.case_id]
        and review.config_sha256 == bundle.manifest.hashes.config
        and review.reference_sha256 == bundle.manifest.hashes.reference
        and review.judge_profile == bundle.config.judge_profile
        and review.judge_revision == bundle.config.judge_revision
    ):
        return ["ROLE_REVIEW_STALE"]
    if bundle.manifest.source_kind == "synthetic_fixture":
        if (review.review_method != "agent_simulated" or not review.initial_label_ref
                or not review.independent_check_ref):
            return ["SYNTHETIC_ROLE_CHAIN_MISSING"]
    elif review.review_method != "independent_review":
        return ["ACTUAL_REVIEW_SOURCE_INELIGIBLE"]
    return []


def inspect_source(inputs: ReplayInputs) -> dict[str, Any]:
    """Check schema, identity, completeness and provided bindings without IO or judging.

    VALID/CONSISTENT describe only the supplied records. References, target hashes,
    review coverage and authority are never authenticated. The returned classification
    (2 invalid, 3 inspection only) is data, not a CLI exit or runtime acceptance.
    """
    result: dict[str, Any] = {
        "schema_version": "offline-source-inspection-v1",
        "input_status": "INVALID", "coherence_status": "NOT_CHECKED",
        "reason_code": "INVALID_INPUT_SCHEMA", "source_kind": None,
        "counts": None, "gaps": None,
        "source_evidence_status": "UNVERIFIED", "target_evidence_status": "UNVERIFIED",
        "review_coverage_status": "NOT_CHECKED", "runtime_metrics": None,
        "baseline_eligible": False, "exit_code": 2,
    }
    try:
        bundle = _load(inputs)
    except _INPUT_ERRORS as exc:
        result["reason_code"] = str(exc) if isinstance(exc, _Invalid) else "INVALID_INPUT_SCHEMA"
        return result

    missing = sorted(case.id for case in bundle.cases if case.id not in bundle.observations)
    incomplete = []
    for case_id, observation in sorted(bundle.observations.items()):
        reasons = _observation_gaps(observation)
        if reasons:
            incomplete.append({"case_id": case_id, "reason_codes": reasons})
    unbound = []
    for (case_id, check_id), review in sorted(bundle.reviews.items()):
        reasons = _review_gaps(bundle, review)
        if reasons:
            unbound.append({"case_id": case_id, "check_id": check_id, "reason_codes": reasons})
    result.update(
        input_status="VALID", reason_code="SOURCE_INSPECTION_ONLY", exit_code=3,
        coherence_status="INCOMPLETE" if missing or incomplete or unbound else "CONSISTENT",
        source_kind=bundle.manifest.source_kind,
        counts={"planned_cases": len(bundle.cases), "observed_cases": len(bundle.observations),
                "complete_observations": len(bundle.observations) - len(incomplete),
                "provided_reviews": len(bundle.reviews),
                "bound_reviews": len(bundle.reviews) - len(unbound)},
        gaps={"missing_observations": missing, "incomplete_observations": incomplete,
              "unbound_reviews": unbound},
    )
    return result
