"""Unit tests for G19 check_bdd_scenario_trace validator + _common.bdd_helpers.

Per Stage D D-2 + sdd/gates.md L58 (G19) + L51 (docker-bdd-scenario-check
subset; same script via `--scope` flag per #D2-A3 design insight) + L96
(Phase M4 BLOCKING per L58 specific row authoritative).

Test coverage (7 cases per brief guidance + R-N v7 R-2 scope path split via
Step 5 quintuple dry-run):

- TestParseFeatureFile: valid parse + invalid raises FeatureParseError
- TestExtractTags: 5-bucket coverage (REQ/CTR/risk/adapter/other) + unknown → other
- TestLoadTraceYml: missing file → None (graceful per Stage A `_common.frontmatter` precedent)
- TestTraceReqCtr: full binding pass + missing REQ tag fail

Stage A test_sdd_g1g2g9_validators.py + Stage D test_sdd_g8_evidence_required.py
precedent: synthetic feature/trace + tmp_path fixture for branch coverage.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from scripts.sdd._common.bdd_helpers import (
    Feature,
    FeatureParseError,
    Scenario,
    ScenarioTags,
    extract_tags,
    load_trace_yml,
    parse_feature_file,
    trace_req_ctr,
)


def _write_feature(tmp_path: Path, content: str, name: str = "test.feature") -> Path:
    """Helper: write content to tmp_path/<name>.feature; return path."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def _baseline_feature_content() -> str:
    """Minimal valid gherkin feature with 1 scenario + canonical tags."""
    return """\
@adapter:python
Feature: Test feature

  @REQ-001 @CTR-test-slug @risk:critical @adapter:python
  Scenario: First scenario
    Given a precondition
    When an action
    Then an outcome
"""


def _write_trace(tmp_path: Path, scenarios: list[str]) -> Path:
    """Helper: write trace.yml at tmp_path/trace.yml with bdd 层 scenarios."""
    trace = {
        "capability": "test.cap",
        "schema_version": "1.2",
        "links": [
            {
                "req": "REQ-001",
                "bdd": {
                    "feature": "contracts/behavior.feature",
                    "scenarios": scenarios,
                },
            }
        ],
    }
    path = tmp_path / "trace.yml"
    path.write_text(yaml.safe_dump(trace), encoding="utf-8")
    return path


class TestParseFeatureFile:
    """parse_feature_file: gherkin parse → Feature dataclass; raise on invalid."""

    def test_valid_feature_parses(self, tmp_path: Path) -> None:
        feature_path = _write_feature(tmp_path, _baseline_feature_content())
        feature = parse_feature_file(feature_path)
        assert isinstance(feature, Feature)
        assert feature.name == "Test feature"
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "First scenario"
        assert "@adapter:python" in feature.feature_tags

    def test_invalid_gherkin_raises_FeatureParseError(self, tmp_path: Path) -> None:
        invalid = "this is not valid gherkin syntax at all\n"
        feature_path = _write_feature(tmp_path, invalid)
        with pytest.raises(FeatureParseError):
            parse_feature_file(feature_path)


class TestExtractTags:
    """extract_tags: bucket tags per canonical @REQ/@CTR/@risk/@adapter + other."""

    def test_5_buckets_canonical_pattern(self) -> None:
        scenario = Scenario(
            name="x",
            tags=[
                "@REQ-001",
                "@REQ-002",
                "@CTR-sql-guardrail",
                "@risk:critical",
                "@adapter:python",
                "@adapter:langchain-agent",
            ],
            line=1,
        )
        tags = extract_tags(scenario)
        assert isinstance(tags, ScenarioTags)
        assert tags.req == ["REQ-001", "REQ-002"]
        assert tags.ctr == ["sql-guardrail"]
        assert tags.risk == ["critical"]
        assert tags.adapter == ["python", "langchain-agent"]
        assert tags.other == []

    def test_unknown_tag_to_other(self) -> None:
        scenario = Scenario(
            name="x",
            tags=["@meta-gate:A14", "@reference-contract", "@adr:ADR-029"],
            line=1,
        )
        tags = extract_tags(scenario)
        assert tags.req == []
        assert tags.ctr == []
        assert "@meta-gate:A14" in tags.other
        assert "@reference-contract" in tags.other
        assert "@adr:ADR-029" in tags.other


class TestLoadTraceYml:
    """load_trace_yml: file missing → None (graceful per Stage A precedent)."""

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        cap_dir = tmp_path / "cap1"
        cap_dir.mkdir()
        # trace.yml NOT created
        result = load_trace_yml(cap_dir)
        assert result is None


class TestTraceReqCtr:
    """trace_req_ctr: REQ/CTR tag binding cross-ref to trace.yml bdd 层."""

    def test_full_binding_passes(self, tmp_path: Path) -> None:
        scenario = Scenario(
            name="First scenario",
            tags=["@REQ-001", "@CTR-test-slug"],
            line=5,
        )
        _write_trace(tmp_path, scenarios=["First scenario"])
        trace_data = load_trace_yml(tmp_path)
        assert trace_data is not None
        result = trace_req_ctr(scenario, trace_data)
        assert result.has_req_tag is True
        assert result.has_ctr_tag is True
        assert result.req_bound_in_trace is True

    def test_missing_req_tag_fails(self) -> None:
        scenario = Scenario(
            name="x",
            tags=["@CTR-only", "@risk:critical"],  # NO @REQ-NNN
            line=1,
        )
        # trace_data minimal (real cross-ref not exercised since has_req_tag fails first)
        result = trace_req_ctr(scenario, {"links": []})
        assert result.has_req_tag is False
        assert result.has_ctr_tag is True
        assert any("REQ" in m for m in result.messages)
