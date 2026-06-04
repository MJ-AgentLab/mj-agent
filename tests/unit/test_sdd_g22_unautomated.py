"""Unit tests for G22 check_bdd_unautomated validator (R-N v10 R-10-1..R-10-8).

Per Stage D D-4 + sdd/gates.md L61 + L96 + sdd/adapters/bdd-tdd.md L120-122
(G22 strict spec: @risk:critical|high 未自动化 scenario → runbook.md 必含
justification 4-field 段落).

R-10-1 mode = WARNING (phased per outline §4 R-1''; R-10-8 NOT deviation).
R-10-2 predicate: automation_status filter (a) + runbook 4-field check (b).
R-10-6 policy: STRUCTURAL FAIL + CURATION WARN + 4-field full PASS.

Test coverage (6 cases post R-N v11 R-11-1 trim):
- TestFilterByUnautomatedAndRisk (3): critical|unautomated / high|unautomated /
  high|automated (excluded);DRY via _make_link helper.
- TestCheckJustification (1): runbook None → all 4 missing (edge case
  test_runbook_partial dropped per R-11-1 redundancy trim).
- TestValidateCapability (2): full 4-field PASS / missing runbook WARN.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd._common.bdd_helpers import Scenario
from scripts.sdd.check_bdd_unautomated import (
    _filter_unautomated_critical_high,
    _validate_capability,
)


def _make_scenario(name: str, tags: list[str]) -> Scenario:
    return Scenario(name=name, tags=tags, line=1)


def _make_link(req: str, scenario: str, status: str = "unautomated") -> dict:
    """DRY helper (R-11-1 trim): trace.yml link dict for one REQ + 1 scenario."""
    return {
        "req": req,
        "bdd": {
            "feature": "contracts/behavior.feature",
            "scenarios": [scenario],
            "automation_status": status,
        },
    }


def _write_capability(
    tmp_path: Path,
    feature_content: str,
    trace_links: list[dict],
    runbook_content: str | None = None,
) -> Path:
    """Scaffold capability dir with behavior.feature + trace.yml + optional runbook.md."""
    cap_dir = tmp_path / "cap1"
    contracts_dir = cap_dir / "contracts"
    contracts_dir.mkdir(parents=True)
    (contracts_dir / "behavior.feature").write_text(feature_content, encoding="utf-8")
    (cap_dir / "trace.yml").write_text(
        yaml.safe_dump(
            {"capability": "test.cap", "schema_version": "1.2", "links": trace_links},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    if runbook_content is not None:
        (cap_dir / "runbook.md").write_text(runbook_content, encoding="utf-8")
    return cap_dir


class TestFilterByUnautomatedAndRisk:
    """R-10-2 layer (a) filter: @risk:critical|high × automation_status:unautomated."""

    def test_critical_unautomated_included(self) -> None:
        scenarios = [_make_scenario("S1", ["@REQ-001", "@CTR-test", "@risk:critical"])]
        trace_data = {"links": [_make_link("REQ-001", "S1")]}
        result = _filter_unautomated_critical_high(scenarios, trace_data)
        assert [s.name for s in result] == ["S1"]

    def test_high_unautomated_included(self) -> None:
        scenarios = [_make_scenario("S2", ["@REQ-002", "@CTR-test", "@risk:high"])]
        trace_data = {"links": [_make_link("REQ-002", "S2")]}
        result = _filter_unautomated_critical_high(scenarios, trace_data)
        assert [s.name for s in result] == ["S2"]

    def test_high_automated_excluded(self) -> None:
        scenarios = [_make_scenario("S3", ["@REQ-003", "@CTR-test", "@risk:high"])]
        trace_data = {"links": [_make_link("REQ-003", "S3", status="automated")]}
        result = _filter_unautomated_critical_high(scenarios, trace_data)
        assert result == []


class TestCheckJustification:
    """R-10-2 layer (b) MVP keyword presence check."""

    def test_runbook_none_all_missing(self) -> None:
        from scripts.sdd._common.bdd_helpers import (
            JUSTIFICATION_FIELDS,
            check_justification_fields,
        )

        all_present, missing = check_justification_fields(None)
        assert all_present is False
        assert set(missing) == set(JUSTIFICATION_FIELDS)


class TestValidateCapability:
    """R-10-6 2-layer policy integration."""

    def test_full_justification_passes(self, tmp_path: Path) -> None:
        feature_content = (
            "Feature: T\n\n"
            "  @REQ-001 @CTR-test @risk:critical @adapter:python\n"
            "  Scenario: Healthy critical\n"
            "    Given a precondition\n"
        )
        runbook = (
            "# Runbook\n\n"
            "原因: pre-Phase-M3 step defs land\n"
            "替代验证手段: manual verification\n"
            "升级触发条件: blocking on Phase M4\n"
            "预计时间: M3 EOL\n"
        )
        cap_dir = _write_capability(
            tmp_path, feature_content, [_make_link("REQ-001", "Healthy critical")], runbook
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (1, 0, 0)

    def test_missing_runbook_warns(self, tmp_path: Path) -> None:
        feature_content = (
            "Feature: T\n\n"
            "  @REQ-001 @CTR-test @risk:high @adapter:python\n"
            "  Scenario: Unjustified scenario\n"
            "    Given a precondition\n"
        )
        cap_dir = _write_capability(
            tmp_path, feature_content, [_make_link("REQ-001", "Unjustified scenario")]
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert summary.warn_count >= 1
        assert summary.fail_count == 0
        assert any(
            "runbook" in m.lower() or "justification" in m.lower() for m in summary.messages
        )


class TestStrictModeBlockingFlip:
    """Stage E α' E-2: --strict is the BLOCKING mechanism (severity NOT reclassified).

    Per ci.yml E-2 flip (continue-on-error:false + --strict): a CURATION WARN
    (missing runbook justification) → exit 1 under --strict (per
    _common/cli.py Summary.exit_code). Proves the gate blocks on a removed §7
    justification block and passes when fully justified.
    """

    _FEATURE = (
        "Feature: T\n\n"
        "  @REQ-001 @CTR-test @risk:critical @adapter:python\n"
        "  Scenario: Strict-mode scenario\n"
        "    Given a precondition\n"
    )

    def test_full_justification_strict_exit_0(self, tmp_path: Path) -> None:
        runbook = (
            "# Runbook\n\n"
            "原因: pre-Phase-M3 step defs land\n"
            "替代验证手段: manual verification\n"
            "升级触发条件: blocking on Phase M4\n"
            "预计时间: M3 EOL\n"
        )
        cap_dir = _write_capability(
            tmp_path, self._FEATURE, [_make_link("REQ-001", "Strict-mode scenario")], runbook
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert summary.warn_count == 0
        assert summary.exit_code(strict=True) == 0

    def test_missing_justification_strict_exit_1(self, tmp_path: Path) -> None:
        # §7 justification block removed (no runbook) → CURATION WARN → --strict blocks
        cap_dir = _write_capability(
            tmp_path, self._FEATURE, [_make_link("REQ-001", "Strict-mode scenario")]
        )
        summary = _validate_capability(cap_dir, tmp_path)
        assert summary.warn_count >= 1
        assert summary.exit_code(strict=True) == 1
        # Pre-flip (WARNING mode, no --strict) the same gap did NOT block:
        assert summary.exit_code(strict=False) == 0
