"""Unit tests for G3 contracts validator (completion-audit PR2 real impl).

Modeled on test_sdd_g1g2g9_validators.py: private `_validate_capability`
against tmp_path scaffolds (no real-tree main() runs per the #217 lesson —
tests stay isolated from working-tree drift).
"""

from __future__ import annotations

from pathlib import Path

from scripts.sdd.check_contracts import _spec_has_high_risk_req, _validate_capability

_SPEC_CRITICAL = (
    "id: data-agent.demo\n"
    "requirements:\n"
    "  - id: REQ-001\n"
    "    priority: critical\n"
)
_SPEC_MEDIUM = (
    "id: data-agent.demo\n"
    "requirements:\n"
    "  - id: REQ-001\n"
    "    priority: medium\n"
)


def _scaffold(
    tmp_path: Path,
    *,
    spec: str = _SPEC_CRITICAL,
    contract_yml: str | None = "contract_id: demo\nsections: {}\n",
    behavior_feature: bool = True,
) -> Path:
    cap_dir = tmp_path / "data-agent" / "demo"
    contracts = cap_dir / "contracts"
    contracts.mkdir(parents=True)
    (cap_dir / "spec.yml").write_text(spec, encoding="utf-8")
    if contract_yml is not None:
        (contracts / "demo.contract.yml").write_text(contract_yml, encoding="utf-8")
    if behavior_feature:
        (contracts / "behavior.feature").write_text("Feature: demo\n", encoding="utf-8")
    return cap_dir


def test_g3_happy_path_passes(tmp_path: Path) -> None:
    cap_dir = _scaffold(tmp_path)
    summary = _validate_capability(cap_dir, tmp_path)
    assert summary.fail_count == 0
    assert summary.warn_count == 0
    assert summary.pass_count == 1


def test_g3_missing_behavior_feature_with_critical_req_fails(tmp_path: Path) -> None:
    cap_dir = _scaffold(tmp_path, behavior_feature=False)
    summary = _validate_capability(cap_dir, tmp_path)
    assert summary.fail_count == 1
    assert any("behavior.feature" in m for m in summary.messages)


def test_g3_empty_contracts_dir_fails(tmp_path: Path) -> None:
    cap_dir = tmp_path / "data-agent" / "demo"
    (cap_dir / "contracts").mkdir(parents=True)
    (cap_dir / "spec.yml").write_text(_SPEC_CRITICAL, encoding="utf-8")
    summary = _validate_capability(cap_dir, tmp_path)
    assert summary.fail_count == 1
    assert any("empty" in m for m in summary.messages)


def test_g3_malformed_contract_yml_fails(tmp_path: Path) -> None:
    cap_dir = _scaffold(tmp_path, contract_yml="- just\n- a\n- list\n")
    summary = _validate_capability(cap_dir, tmp_path)
    assert summary.fail_count == 1
    assert any("parse error or non-mapping" in m for m in summary.messages)


def test_g3_medium_only_spec_needs_no_behavior_feature(tmp_path: Path) -> None:
    cap_dir = _scaffold(tmp_path, spec=_SPEC_MEDIUM, behavior_feature=False)
    assert _spec_has_high_risk_req(cap_dir) is False
    summary = _validate_capability(cap_dir, tmp_path)
    assert summary.fail_count == 0
    assert summary.pass_count == 1
