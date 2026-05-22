"""Unit tests for G1 / G2 / G9 SDD validators.

Covers M3-FU-G1G2G9-IMPL AC §4: 3 validators × ≥ 3 cases each (happy path
+ missing field + invalid schema + drift detection). Uses tmp_path fixtures
with synthetic spec.yml / trace.yml so tests run without touching the
real `capabilities/` tree.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd.check_capability_schema import _validate_spec
from scripts.sdd.check_traceability import _validate_trace
from scripts.sdd.generate_index import _build_index_content


def _baseline_spec() -> dict:
    return {
        "id": "data-agent.x",
        "name": "X",
        "domain": "data-agent",
        "lifecycle_state": "drafting",
        "archive_state": "active",
        "adapter_coverage": ["python", "tdd-bdd"],
        "last_verified": "2026-05-21",
        "owner": "ranzuozhou",
        "created": "2026-05-21",
        "updated": "2026-05-21",
        "summary": "test",
        "requirements": [
            {"id": "REQ-001", "statement": "s", "rationale": "r", "priority": "critical"},
        ],
    }


def _write_spec(tmp_path: Path, spec: dict, *, name: str = "x") -> Path:
    p = tmp_path / "capabilities" / "data-agent" / name / "spec.yml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(spec), encoding="utf-8")
    return p


def _baseline_trace() -> dict:
    return {
        "capability": "data-agent.x",
        "schema_version": "1.2",
        "links": [
            {"req": "REQ-001"},
        ],
    }


def _write_trace(tmp_path: Path, trace: dict, *, name: str = "x") -> Path:
    p = tmp_path / "capabilities" / "data-agent" / name / "trace.yml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(trace), encoding="utf-8")
    return p


# -------- G1: check_capability_schema --------


def test_g1_happy_path(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _baseline_spec())
    summary = _validate_spec(spec_path, tmp_path)
    assert summary.fail_count == 0
    assert summary.warn_count == 0
    assert summary.pass_count == 1


def test_g1_missing_required_field_warns(tmp_path: Path) -> None:
    spec = _baseline_spec()
    del spec["summary"]
    spec_path = _write_spec(tmp_path, spec)
    summary = _validate_spec(spec_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("missing required top-level field 'summary'" in m for m in summary.messages)


def test_g1_invalid_lifecycle_warns(tmp_path: Path) -> None:
    spec = _baseline_spec()
    spec["lifecycle_state"] = "bogus-state"
    spec_path = _write_spec(tmp_path, spec)
    summary = _validate_spec(spec_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("lifecycle_state 'bogus-state' not in 9-state enum" in m for m in summary.messages)


def test_g1_invalid_req_id_pattern_warns(tmp_path: Path) -> None:
    spec = _baseline_spec()
    spec["requirements"][0]["id"] = "REQ-1"  # too few digits
    spec_path = _write_spec(tmp_path, spec)
    summary = _validate_spec(spec_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("does not match REQ-NNN pattern" in m for m in summary.messages)


def test_g1_bdd_tdd_alias_accepted(tmp_path: Path) -> None:
    """`bdd-tdd` and `tdd-bdd` both accepted (M3 dual-name compat)."""
    spec = _baseline_spec()
    spec["adapter_coverage"] = ["python", "bdd-tdd"]
    spec_path = _write_spec(tmp_path, spec)
    summary = _validate_spec(spec_path, tmp_path)
    assert summary.warn_count == 0
    assert summary.pass_count == 1


# -------- G2: check_traceability --------


def test_g2_happy_path(tmp_path: Path) -> None:
    trace_path = _write_trace(tmp_path, _baseline_trace())
    summary = _validate_trace(trace_path, tmp_path)
    assert summary.fail_count == 0
    assert summary.warn_count == 0
    assert summary.pass_count == 1


def test_g2_missing_schema_version_warns(tmp_path: Path) -> None:
    trace = _baseline_trace()
    del trace["schema_version"]
    trace_path = _write_trace(tmp_path, trace)
    summary = _validate_trace(trace_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("missing required top-level field 'schema_version'" in m for m in summary.messages)


def test_g2_wrong_schema_version_warns(tmp_path: Path) -> None:
    trace = _baseline_trace()
    trace["schema_version"] = "1.0"  # only 1.2 is current
    trace_path = _write_trace(tmp_path, trace)
    summary = _validate_trace(trace_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("schema_version '1.0' !=" in m for m in summary.messages)


def test_g2_invalid_req_pattern_warns(tmp_path: Path) -> None:
    trace = _baseline_trace()
    trace["links"][0]["req"] = "REQ-1"  # too few digits
    trace_path = _write_trace(tmp_path, trace)
    summary = _validate_trace(trace_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("does not match REQ-NNN pattern" in m for m in summary.messages)


def test_g2_bdd_invalid_automation_status_warns(tmp_path: Path) -> None:
    trace = _baseline_trace()
    trace["links"][0]["bdd"] = {
        "feature": "f.feature",
        "scenarios": ["s"],
        "automation_status": "bogus",
    }
    trace_path = _write_trace(tmp_path, trace)
    summary = _validate_trace(trace_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("automation_status 'bogus' not in" in m for m in summary.messages)


def test_g2_cross_capability_ref_missing_direction(tmp_path: Path) -> None:
    trace = _baseline_trace()
    trace["cross_capability_refs"] = [
        {"target": "data-agent.y", "surface": "s", "rationale": "r"}  # missing direction
    ]
    trace_path = _write_trace(tmp_path, trace)
    summary = _validate_trace(trace_path, tmp_path)
    assert summary.warn_count >= 1
    assert any("missing required field 'direction'" in m for m in summary.messages)


# -------- G9: generate_index --------


def test_g9_emits_active_capabilities_row(tmp_path: Path) -> None:
    _write_spec(tmp_path, _baseline_spec())
    _write_trace(tmp_path, _baseline_trace())
    content = _build_index_content(tmp_path)
    assert "## Active Capabilities" in content
    assert "data-agent.x" in content
    assert "drafting" in content


def test_g9_emits_cross_capability_refs(tmp_path: Path) -> None:
    _write_spec(tmp_path, _baseline_spec())
    trace = _baseline_trace()
    trace["cross_capability_refs"] = [
        {
            "target": "data-agent.y",
            "direction": "outbound",
            "surface": "src/foo.py:1",
            "rationale": "test reason",
        }
    ]
    _write_trace(tmp_path, trace)
    content = _build_index_content(tmp_path)
    assert "## Cross-Capability References" in content
    assert "outbound" in content
    assert "data-agent.y" in content
    assert "test reason" in content


def test_g9_skips_archived(tmp_path: Path) -> None:
    spec = _baseline_spec()
    spec["archive_state"] = "archived"
    _write_spec(tmp_path, spec)
    _write_trace(tmp_path, _baseline_trace())
    content = _build_index_content(tmp_path)
    # archive_state=archived → row excluded
    assert "data-agent.x" not in content
    # the table header still exists even if no rows
    assert "## Active Capabilities" in content


def test_g9_no_cross_refs_emits_placeholder(tmp_path: Path) -> None:
    _write_spec(tmp_path, _baseline_spec())
    _write_trace(tmp_path, _baseline_trace())  # no cross_capability_refs
    content = _build_index_content(tmp_path)
    assert "_(none)_" in content


def test_g9_idempotent_regeneration(tmp_path: Path) -> None:
    """Regenerating twice produces byte-identical output (--check idempotency)."""
    _write_spec(tmp_path, _baseline_spec())
    _write_trace(tmp_path, _baseline_trace())
    first = _build_index_content(tmp_path)
    second = _build_index_content(tmp_path)
    assert first == second
