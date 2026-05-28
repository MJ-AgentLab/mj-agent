"""Unit tests for G21 check_bdd_acceptance validator (R-N v9 R-9-1/R-9-2).

Per Stage D D-3 + sdd/gates.md L60 (G21) + L96 (Phase M4 启用 mode-unqualified
→ WARNING per outline §3 v2 + Phase M3 G19/G20 warning precedent) +
sdd/adapters/bdd-tdd.md L161 (G21 spec authoritative wording:
``@risk:high`` / ``@risk:critical`` scenario 必含 ``pass_rate: 1.0`` 或 justification).

R-N v9 R-9-1: filter scope = ``@risk:critical`` OR ``@risk:high`` (15 scenarios
across 4 pilots per §0 #3 inventory; mcp-server-governance excluded medium-only).

R-N v9 R-9-2 4-layer policy (D-3 MVP):
- (a) risk filter precondition: SKIP scenarios not @risk:critical|high
- (b) TAG layer: missing @REQ or @CTR → FAIL (R-N v8 R-1 TAG inherit)
- (c) TRACE layer: trace.yml bdd 层 mapping gap → WARN (R-N v8 R-1 TRACE inherit)
- (d) EVIDENCE layer (pass_rate strict): DEFERRED to M-FU#4 Stage E α'

Test coverage (7 cases per brief §4 + §6 AC-2):

- TestFilterByRisk (4): critical included / high included / medium excluded /
  no-risk excluded
- TestValidateCapability (3): tag+trace healthy PASS / tag missing FAIL /
  trace gap WARN

Stage A test_sdd_g1g2g9_validators.py + Stage D test_sdd_g8_evidence_required.py
+ D-2 test_sdd_g19_scenario_trace.py precedent: synthetic feature/trace fixtures
+ tmp_path branch coverage.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd._common.bdd_helpers import Scenario
from scripts.sdd.check_bdd_acceptance import _filter_by_risk, _validate_capability


def _make_scenario(name: str, tags: list[str], line: int = 1) -> Scenario:
    """Helper: synthetic Scenario dataclass with explicit tags."""
    return Scenario(name=name, tags=tags, line=line)


def _write_capability(tmp_path: Path, feature_content: str,
                      trace_scenarios: list[str] | None = None) -> Path:
    """Helper: scaffold a capability dir with contracts/behavior.feature + trace.yml."""
    cap_dir = tmp_path / "cap1"
    contracts_dir = cap_dir / "contracts"
    contracts_dir.mkdir(parents=True)
    (contracts_dir / "behavior.feature").write_text(feature_content, encoding="utf-8")
    if trace_scenarios is not None:
        trace = {
            "capability": "test.cap",
            "schema_version": "1.2",
            "links": [
                {
                    "req": "REQ-001",
                    "bdd": {
                        "feature": "contracts/behavior.feature",
                        "scenarios": trace_scenarios,
                    },
                }
            ],
        }
        (cap_dir / "trace.yml").write_text(yaml.safe_dump(trace), encoding="utf-8")
    return cap_dir


class TestFilterByRisk:
    """_filter_by_risk: R-9-1 scope = @risk:critical | @risk:high."""

    def test_critical_included(self) -> None:
        scenarios = [_make_scenario("S1", ["@REQ-001", "@risk:critical"])]
        result = _filter_by_risk(scenarios)
        assert len(result) == 1
        assert result[0].name == "S1"

    def test_high_included(self) -> None:
        scenarios = [_make_scenario("S2", ["@REQ-002", "@risk:high"])]
        result = _filter_by_risk(scenarios)
        assert len(result) == 1
        assert result[0].name == "S2"

    def test_medium_excluded(self) -> None:
        scenarios = [_make_scenario("S3", ["@REQ-003", "@risk:medium"])]
        result = _filter_by_risk(scenarios)
        assert result == []

    def test_no_risk_excluded(self) -> None:
        scenarios = [_make_scenario("S4", ["@REQ-004"])]
        result = _filter_by_risk(scenarios)
        assert result == []


class TestValidateCapability:
    """_validate_capability: R-9-2 4-layer policy (a/b/c apply; d deferred)."""

    def test_full_binding_passes(self, tmp_path: Path) -> None:
        feature_content = (
            "Feature: T\n"
            "\n"
            "  @REQ-001 @CTR-test @risk:critical @adapter:python\n"
            "  Scenario: Healthy critical\n"
            "    Given a precondition\n"
        )
        cap_dir = _write_capability(
            tmp_path, feature_content, trace_scenarios=["Healthy critical"]
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert summary.fail_count == 0
        assert summary.warn_count == 0
        assert summary.pass_count == 1

    def test_tag_missing_fails(self, tmp_path: Path) -> None:
        # @risk:high present (matches filter); missing @CTR → FAIL per R-N v8 R-1 TAG layer
        feature_content = (
            "Feature: T\n"
            "\n"
            "  @REQ-001 @risk:high @adapter:python\n"
            "  Scenario: Missing CTR tag\n"
            "    Given a precondition\n"
        )
        cap_dir = _write_capability(
            tmp_path, feature_content, trace_scenarios=["Missing CTR tag"]
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert summary.fail_count >= 1
        assert any("[FAIL]" in m and "CTR" in m for m in summary.messages)

    def test_trace_gap_warns(self, tmp_path: Path) -> None:
        # @risk:critical + full tags; trace.yml exists but scenario name not bound → WARN per R-N v8 R-1 TRACE layer
        feature_content = (
            "Feature: T\n"
            "\n"
            "  @REQ-001 @CTR-test @risk:critical @adapter:python\n"
            "  Scenario: Trace gap scenario\n"
            "    Given a precondition\n"
        )
        cap_dir = _write_capability(
            tmp_path, feature_content, trace_scenarios=["Other scenario name"]
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert summary.warn_count >= 1
        assert any(
            "[WARN]" in m and ("trace.yml" in m or "trace curation" in m)
            for m in summary.messages
        )
