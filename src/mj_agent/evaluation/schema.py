"""Strict in-memory inputs. This module never reads application files or settings."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

_REVISION = "offline-core-v1"


class _Invalid(ValueError):
    pass


@dataclass(frozen=True)
class ReplayInputs:
    """Explicit byte inputs to the public replay API; no file or service access."""

    config: bytes
    dataset: bytes
    observations: bytes
    manifest: bytes
    reference: bytes
    reviews: bytes = b""
    baseline: bytes = b""


_Inputs = ReplayInputs


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _Invalid("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise _Invalid("NON_FINITE_JSON")


def _depth(value: object, level: int = 0) -> None:
    if level > 32:
        raise _Invalid("JSON_DEPTH_LIMIT")
    if isinstance(value, float) and not math.isfinite(value):
        raise _Invalid("NON_FINITE_JSON")
    if isinstance(value, dict):
        for child in value.values():
            _depth(child, level + 1)
    elif isinstance(value, list):
        for child in value:
            _depth(child, level + 1)


def _json(raw: bytes) -> Any:
    if len(raw) > 10 * 1024 * 1024:
        raise _Invalid("INPUT_SIZE_LIMIT")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    _depth(value)
    return value


def _jsonl(raw: bytes) -> list[dict[str, Any]]:
    if len(raw) > 10 * 1024 * 1024:
        raise _Invalid("INPUT_SIZE_LIMIT")
    records = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        if len(line) > 256 * 1024:
            raise _Invalid("RECORD_SIZE_LIMIT")
        record = _json(line)
        if not isinstance(record, dict):
            raise _Invalid("RECORD_NOT_OBJECT")
        records.append(record)
    return records


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Config(_Model):
    schema_version: Literal["offline-eval-v1"]
    eval_id: str
    eval_kind: Literal["outcome"]
    judge_profile: Literal["first-turn-time-predicate-v1"]
    judge_revision: Literal["offline-core-v1"]
    planned_case_count: Literal[22]
    red_line_ids: list[str]
    baseline_metric: Literal["first_turn_pass_rate"]
    threshold: float
    manual_audit_fraction: float
    comparison_mode: Literal["same_target_replay"]

    @model_validator(mode="after")
    def _fixed_policy(self) -> _Config:
        if self.threshold != 0.03 or self.manual_audit_fraction != 0.10:
            raise _Invalid("PROFILE_POLICY_MISMATCH")
        if self.red_line_ids != [f"RL-{i:02}" for i in range(1, 6)]:
            raise _Invalid("RED_LINE_PROFILE_MISMATCH")
        return self


class _Case(_Model):
    id: str
    user_query: str
    expected_output: dict[str, Any]
    expected_trajectory: list[dict[str, Any]]
    context: dict[str, str]
    tags: list[str]


class _Call(_Model):
    sequence: int = Field(ge=1)
    call_id: str
    tool_name: str
    sql: str | None = None
    outcome: Literal["success", "error", "unknown"] = "unknown"
    error_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sql_arguments(self) -> _Call:
        if self.tool_name != "execute_sql" and self.sql is not None:
            raise _Invalid("UNAPPROVED_TOOL_ARGUMENT")
        return self


class _Observation(_Model):
    schema_version: Literal["offline-observation-v1"]
    case_id: str
    run_id: str
    turn_complete: bool = False
    trajectory_complete: bool = False
    reply_complete: bool = False
    reply_excerpt: str = ""
    tool_calls: list[_Call] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def _order(self) -> _Observation:
        if [c.sequence for c in self.tool_calls] != list(range(1, len(self.tool_calls) + 1)):
            raise _Invalid("CALL_SEQUENCE_INVALID")
        if len({c.call_id for c in self.tool_calls}) != len(self.tool_calls):
            raise _Invalid("DUPLICATE_CALL_ID")
        return self


class _Component(_Model):
    path: str
    version: str
    body_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class _Snapshot(_Model):
    prompt: _Component
    skills: list[_Component] = Field(min_length=1)
    assembled_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _unique(self) -> _Snapshot:
        if len({c.path for c in self.skills}) != len(self.skills):
            raise _Invalid("DUPLICATE_TARGET_COMPONENT")
        return self


class _Hashes(_Model):
    config: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset: str = Field(pattern=r"^[0-9a-f]{64}$")
    observations: str = Field(pattern=r"^[0-9a-f]{64}$")
    reference: str = Field(pattern=r"^[0-9a-f]{64}$")


class _ModelIdentity(_Model):
    provider_kind: str = Field(min_length=1)
    deployment_label: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    deployment_revision: str = Field(min_length=1)


class _Sampling(_Model):
    temperature: float = Field(ge=0)
    top_p: float = Field(gt=0, le=1)
    max_tokens: int = Field(ge=1)
    seed: int | None


class _Time(_Model):
    current_date: str
    timezone: str = Field(min_length=1)
    data_as_of: str
    interpretation_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _dates(self) -> _Time:
        date.fromisoformat(self.current_date)
        date.fromisoformat(self.data_as_of)
        return self


class _Provenance(_Model):
    source_ref: str = Field(min_length=1)
    sampled_at: str = Field(min_length=1)
    sanitization_version: str = Field(min_length=1)
    sanitization_review_ref: str = Field(min_length=1)
    sampling_approval_ref: str | None


class _Manifest(_Model):
    schema_version: Literal["offline-manifest-v1"]
    run_id: str
    eval_id: str
    repository_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    hashes: _Hashes
    source_kind: Literal["runtime_observation", "synthetic_fixture"]
    target_snapshot: _Snapshot
    model: _ModelIdentity
    sampling: _Sampling
    time_basis: _Time
    provenance: _Provenance

    @model_validator(mode="after")
    def _actual_source(self) -> _Manifest:
        if self.source_kind == "runtime_observation" and not self.provenance.sampling_approval_ref:
            raise _Invalid("ACTUAL_SOURCE_APPROVAL_REFERENCE_MISSING")
        return self


class _Table(_Model):
    period: str | None
    time_column: str | None
    kind: Literal["fact", "signal", "dimension"]


class _Window(_Model):
    lower: str
    upper: str | None
    lower_inclusive: bool
    upper_inclusive: bool

    @model_validator(mode="after")
    def _range(self) -> _Window:
        lower = date.fromisoformat(self.lower)
        if self.upper is not None and date.fromisoformat(self.upper) < lower:
            raise _Invalid("REFERENCE_WINDOW_INVALID")
        return self


class _Reference(_Model):
    schema_version: Literal["offline-reference-v1"]
    source_ref: str
    tables: dict[str, _Table]
    windows: dict[str, _Window]


class _Review(_Model):
    schema_version: Literal["offline-review-v1"]
    run_id: str
    case_id: str
    check_id: str
    case_observation_sha256: str
    config_sha256: str
    reference_sha256: str
    judge_profile: str
    judge_revision: str
    reviewer_role: Literal["domain", "prompt", "swe"]
    sanitized_review_ref: str
    verdict: Literal["PASS", "FAIL"]
    reason_code: str = Field(pattern=r"^[A-Z0-9_]+$")
    review_method: Literal["agent_simulated", "independent_review"]
    initial_label_ref: str | None = None
    independent_check_ref: str | None = None


@dataclass(frozen=True)
class _Bundle:
    config: _Config
    cases: list[_Case]
    observations: dict[str, _Observation]
    observation_hashes: dict[str, str]
    manifest: _Manifest
    reference: _Reference
    reviews: dict[tuple[str, str], _Review]
    baseline: dict[str, Any] | None


def _load(inputs: _Inputs) -> _Bundle:
    config = _Config.model_validate(_json(inputs.config))
    manifest = _Manifest.model_validate(_json(inputs.manifest))
    reference = _Reference.model_validate(_json(inputs.reference))
    cases = [_Case.model_validate(c) for c in _jsonl(inputs.dataset)]
    raw_observations = _jsonl(inputs.observations)
    observations = [_Observation.model_validate(o) for o in raw_observations]
    reviews = [_Review.model_validate(r) for r in _jsonl(inputs.reviews)]
    if config.eval_id != manifest.eval_id:
        raise _Invalid("EVAL_ID_MISMATCH")
    for field in ("config", "dataset", "observations", "reference"):
        if _digest(getattr(inputs, field)) != getattr(manifest.hashes, field):
            raise _Invalid("INPUT_HASH_MISMATCH")
    case_ids = {c.id for c in cases}
    if len(cases) != 22 or len(case_ids) != len(cases):
        raise _Invalid("DATASET_CARDINALITY_INVALID")
    if {c.id for c in cases if "red-line" in c.tags} != set(config.red_line_ids):
        raise _Invalid("RED_LINE_DATASET_MISMATCH")
    if len({o.case_id for o in observations}) != len(observations):
        raise _Invalid("DUPLICATE_OBSERVATION_ID")
    if any(o.case_id not in case_ids or o.run_id != manifest.run_id for o in observations):
        raise _Invalid("OBSERVATION_ID_MISMATCH")
    review_keys = {(r.case_id, r.check_id) for r in reviews}
    if len(review_keys) != len(reviews) or any(r.case_id not in case_ids for r in reviews):
        raise _Invalid("REVIEW_ID_INVALID")
    baseline = _json(inputs.baseline) if inputs.baseline else None
    if baseline is not None and not isinstance(baseline, dict):
        raise _Invalid("BASELINE_NOT_OBJECT")
    return _Bundle(config, cases, {o.case_id: o for o in observations},
                   {o["case_id"]: _digest(_canonical(o)) for o in raw_observations},
                   manifest, reference, {(r.case_id, r.check_id): r for r in reviews}, baseline)


_INPUT_ERRORS = (
    _Invalid, ValidationError, UnicodeError, ValueError, TypeError, RecursionError, OverflowError,
)
