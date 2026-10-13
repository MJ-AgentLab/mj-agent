"""Unit tests for G21 evidence predicate extension (Stage E α' E-0a M-FU#4).

Per R-15-1 G21/G22 share runbook.md justification source (bdd-tdd.md L160 →
L121 + L161 parsimony resolved post §0). M-FU#4 reduced scope per R-15-2:
load_bdd_evidence helper + harness + fallback to runbook reuse (NO independent
justification mechanism). M-FU#1 trace.yml L67 quote fix mechanical (HITL
confirmed).

R-N v18 increments locked at Gate-1:
- R-18-1: E-0a Compound-Reduced classification
- R-18-2: M-FU#4 additive bdd_helpers extension (4 NEW helpers + const)
- R-18-3: M-FU#5 deliberate read-only-spec lift (HITL wording gate Step 5.5)
- R-18-4: G21 WARN-raise intended gap exposure (NOT regression)
- R-18-6: Anti-Gate-Defeat (R-16-6) cross-ref — evidence schema-only NOT
  populated (anti-fabrication; schema deploy is infra, real pass_rate comes
  from automated scenario runs OR fallback runbook owner authorship)

Refine 1 (Step 1.5 mini-review approved): load_runbook + check_justification_fields
+ JUSTIFICATION_FIELDS in bdd_helpers are byte-equivalent MIRROR of D-4 G22
validator-local versions (check_bdd_unautomated.py D-4 merged code UNTOUCHED
per §7 batch boundary). Drift guard test asserts identical semantics until
M-FU#10 consolidation post-Stage-E.

Refine 2 (M-FU#10 register): paired-edit warning — until consolidation, any
change to 4-field semantic / check logic in EITHER source MUST be applied to
BOTH (G22 local OR bdd_helpers shared) to prevent gate behavior drift.

Test coverage (per brief §4 + §6 AC-5):
- TestLoadBddEvidence (3): valid frontmatter → dict / missing file → None /
  invalid → None
- TestLoadRunbookMirror (1): mirrors D-4 G22 _load_runbook behavior
- TestCheckJustificationFieldsMirror (2): all-missing on None runbook +
  drift guard with G22's _JUSTIFICATION_FIELDS
- TestG21PredicateExtension (4): evidence-present-pass / evidence-fallback-
  runbook-pass / runbook-only-fallback-pass / neither-WARN
- TestTraceYmlMfu1Fix (1): llm-provider trace.yml L67 scenario name match
  behavior.feature post quote fix
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml


def _write_evidence(
    cap_dir: Path, scenario_keyword: str, pass_rate: float = 1.0
) -> Path:
    """Helper: scaffold an evidence/bdd/*.md file with frontmatter."""
    bdd_dir = cap_dir / "evidence" / "bdd"
    bdd_dir.mkdir(parents=True, exist_ok=True)
    filename = f"2026-05-29_{scenario_keyword}_pass.md"
    content = (
        "---\n"
        "type: evidence\n"
        "subtype: bdd\n"
        "date: 2026-05-29\n"
        "commit_sha: 0000000000000000000000000000000000000000\n"
        "scenario_count: 1\n"
        f"pass_rate: {pass_rate}\n"
        "hitl_triggered: false\n"
        "risk_breakdown: { critical: 0, high: 1, medium: 0, low: 0 }\n"
        "adapter_coverage: [python]\n"
        "---\n\n"
        f"# Evidence: {scenario_keyword}\n\n"
        "Test evidence body.\n"
    )
    path = bdd_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def _write_runbook(cap_dir: Path, content: str) -> Path:
    """Helper: scaffold a runbook.md."""
    path = cap_dir / "runbook.md"
    path.write_text(content, encoding="utf-8")
    return path


def _make_capability_dir(tmp_path: Path) -> Path:
    """Helper: capability dir scaffold."""
    cap_dir = tmp_path / "cap1"
    cap_dir.mkdir()
    return cap_dir


class TestLoadBddEvidence:
    """M-FU#4 NEW helper: load_bdd_evidence(capability_dir, scenario_name=None)."""

    def test_valid_evidence_returns_dict(self, tmp_path: Path) -> None:
        from scripts.sdd._common.bdd_helpers import load_bdd_evidence

        cap_dir = _make_capability_dir(tmp_path)
        _write_evidence(cap_dir, "test_scenario", pass_rate=1.0)
        result = load_bdd_evidence(cap_dir)
        assert isinstance(result, dict)
        assert result.get("pass_rate") == 1.0

    def test_missing_evidence_dir_returns_none(self, tmp_path: Path) -> None:
        from scripts.sdd._common.bdd_helpers import load_bdd_evidence

        cap_dir = _make_capability_dir(tmp_path)
        # No evidence/bdd/ dir created
        result = load_bdd_evidence(cap_dir)
        assert result is None

    def test_unrelated_file_cannot_supply_scenario_evidence(self, tmp_path: Path) -> None:
        from scripts.sdd._common.bdd_helpers import load_bdd_evidence

        cap_dir = _make_capability_dir(tmp_path)
        path = _write_evidence(cap_dir, "unrelated", pass_rate=1.0)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("subtype: bdd", "subtype: bdd\ncovered_scenarios: [Different]"), encoding="utf-8")
        assert load_bdd_evidence(cap_dir, "Wanted") is None

    def test_no_pass_rate_field_returns_none(self, tmp_path: Path) -> None:
        from scripts.sdd._common.bdd_helpers import load_bdd_evidence

        cap_dir = _make_capability_dir(tmp_path)
        bdd_dir = cap_dir / "evidence" / "bdd"
        bdd_dir.mkdir(parents=True)
        # Evidence file without pass_rate frontmatter field
        (bdd_dir / "2026-05-29_bad_pass.md").write_text(
            "---\ntype: evidence\n---\n\nNo pass_rate.\n",
            encoding="utf-8",
        )
        result = load_bdd_evidence(cap_dir)
        assert result is None


class TestLoadRunbookMirror:
    """M-FU#4 NEW helper: load_runbook(capability_dir).

    Byte-equivalent MIRROR of D-4 G22 check_bdd_unautomated._load_runbook
    (Refine 1 Step 1.5;G22 D-4 merged code UNTOUCHED per §7 batch boundary).
    """

    def test_missing_runbook_returns_none(self, tmp_path: Path) -> None:
        from scripts.sdd._common.bdd_helpers import load_runbook

        cap_dir = _make_capability_dir(tmp_path)
        result = load_runbook(cap_dir)
        assert result is None


class TestCheckJustificationFields:
    """M-FU#4 shared justification helper in bdd_helpers (used by G21 + G22).

    Post M5-PR6 consolidation (M4-FU-G22-BDD-HELPERS-CONSOLIDATE): G22 imports
    JUSTIFICATION_FIELDS + check_justification_fields from bdd_helpers directly,
    so the byte-equivalent D-4 duplicate + its paired-edit drift-guard are retired.
    """

    def test_none_runbook_returns_all_missing(self) -> None:
        from scripts.sdd._common.bdd_helpers import (
            JUSTIFICATION_FIELDS,
            check_justification_fields,
        )

        all_present, missing = check_justification_fields(None)
        assert all_present is False
        assert set(missing) == set(JUSTIFICATION_FIELDS)


class TestG21PredicateExtension:
    """M-FU#4 G21 predicate extension (per AC-5 4 cases;R-15-1 coupling).

    G21 保 WARNING mode (flip 是 E-1 work); evidence-or-runbook fallback path
    per Anti-Gate-Defeat (R-16-6) cross-ref: explicit + reviewable;NOT silent
    auto-exempt OR fabricated content (R-18-6 schema-only boundary).
    """

    def test_bare_pass_rate_is_not_behavior_evidence(self, tmp_path: Path) -> None:
        from scripts.sdd.check_bdd_acceptance import _validate_capability_with_evidence

        cap_dir = _make_capability_dir(tmp_path)
        (cap_dir / "contracts").mkdir()
        (cap_dir / "contracts" / "behavior.feature").write_text(
            "Feature: T\n\n"
            "  @REQ-001 @CTR-test @risk:critical @adapter:python\n"
            "  Scenario: Healthy critical\n"
            "    Given a precondition\n",
            encoding="utf-8",
        )
        (cap_dir / "trace.yml").write_text(
            yaml.safe_dump(
                {
                    "capability": "test.cap",
                    "schema_version": "1.2",
                    "links": [
                        {
                            "req": "REQ-001",
                            "bdd": {
                                "feature": "contracts/behavior.feature",
                                "scenarios": ["Healthy critical"],
                            },
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        _write_evidence(cap_dir, "healthy_critical", pass_rate=1.0)

        summary = _validate_capability_with_evidence(cap_dir, tmp_path)
        # A number or filename does not establish executed scenario evidence.
        assert summary.fail_count == 0
        assert summary.pass_count == 0
        assert summary.warn_count == 1

    def test_evidence_absent_runbook_justification_fallback_passes(
        self, tmp_path: Path
    ) -> None:
        from scripts.sdd.check_bdd_acceptance import _validate_capability_with_evidence

        cap_dir = _make_capability_dir(tmp_path)
        (cap_dir / "contracts").mkdir()
        (cap_dir / "contracts" / "behavior.feature").write_text(
            "Feature: T\n\n"
            "  @REQ-001 @CTR-test @risk:high @adapter:python\n"
            "  Scenario: Fallback runbook scenario\n"
            "    Given a precondition\n",
            encoding="utf-8",
        )
        (cap_dir / "trace.yml").write_text(
            yaml.safe_dump(
                {
                    "capability": "test.cap",
                    "schema_version": "1.2",
                    "links": [
                        {
                            "req": "REQ-001",
                            "bdd": {
                                "feature": "contracts/behavior.feature",
                                "scenarios": ["Fallback runbook scenario"],
                            },
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        # NO evidence/bdd/ deployed
        _write_runbook(
            cap_dir,
            "# Runbook\n\n"
            "原因: pre-Phase-M3 step defs land\n"
            "替代验证手段: manual verification\n"
            "升级触发条件: blocking on Phase M4\n"
            "预计时间: M3 EOL\n",
        )

        summary = _validate_capability_with_evidence(cap_dir, tmp_path)
        # A complete justification is a legal deferral, not behavior PASS.
        assert summary.fail_count == 0
        assert summary.pass_count == 0
        assert any("DEFERRED" in message for message in summary.messages)

    def test_evidence_absent_runbook_absent_warns(self, tmp_path: Path) -> None:
        from scripts.sdd.check_bdd_acceptance import _validate_capability_with_evidence

        cap_dir = _make_capability_dir(tmp_path)
        (cap_dir / "contracts").mkdir()
        (cap_dir / "contracts" / "behavior.feature").write_text(
            "Feature: T\n\n"
            "  @REQ-001 @CTR-test @risk:high @adapter:python\n"
            "  Scenario: Gap scenario\n"
            "    Given a precondition\n",
            encoding="utf-8",
        )
        (cap_dir / "trace.yml").write_text(
            yaml.safe_dump(
                {
                    "capability": "test.cap",
                    "schema_version": "1.2",
                    "links": [
                        {
                            "req": "REQ-001",
                            "bdd": {
                                "feature": "contracts/behavior.feature",
                                "scenarios": ["Gap scenario"],
                            },
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        # NO evidence + NO runbook → gap exposure (R-18-4 intended WARN-raise)

        summary = _validate_capability_with_evidence(cap_dir, tmp_path)
        # WARN emitted (保 WARNING mode per R-15-* E-0a; NOT FAIL)
        assert summary.warn_count >= 1
        assert summary.fail_count == 0

    def test_evidence_present_pass_rate_below_1_0_falls_back_to_runbook(
        self, tmp_path: Path
    ) -> None:
        from scripts.sdd.check_bdd_acceptance import _validate_capability_with_evidence

        cap_dir = _make_capability_dir(tmp_path)
        (cap_dir / "contracts").mkdir()
        (cap_dir / "contracts" / "behavior.feature").write_text(
            "Feature: T\n\n"
            "  @REQ-001 @CTR-test @risk:high @adapter:python\n"
            "  Scenario: Partial pass scenario\n"
            "    Given a precondition\n",
            encoding="utf-8",
        )
        (cap_dir / "trace.yml").write_text(
            yaml.safe_dump(
                {
                    "capability": "test.cap",
                    "schema_version": "1.2",
                    "links": [
                        {
                            "req": "REQ-001",
                            "bdd": {
                                "feature": "contracts/behavior.feature",
                                "scenarios": ["Partial pass scenario"],
                            },
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        # Evidence partial (pass_rate=0.7);runbook present 4-field
        _write_evidence(cap_dir, "partial_pass", pass_rate=0.7)
        _write_runbook(
            cap_dir,
            "# Runbook\n\n"
            "原因: partial automation\n"
            "替代验证手段: 70% pass adequate per L109 baseline\n"
            "升级触发条件: 100% target by Phase M4\n"
            "预计时间: Phase M4 EOL\n",
        )

        summary = _validate_capability_with_evidence(cap_dir, tmp_path)
        # Partial historical evidence can be explicitly deferred, not passed.
        assert summary.fail_count == 0
        assert summary.pass_count == 0
        assert any("DEFERRED" in message for message in summary.messages)


class TestTraceYmlMfu1Fix:
    """M-FU#1 trace.yml L67 quote fix verification (post-fix state)."""

    def test_llm_provider_trace_scenario_matches_behavior_feature(self) -> None:
        """Post M-FU#1 fix: llm-provider trace.yml scenario name MUST match
        behavior.feature scenario name char-level (double quotes around EMPTY).
        """
        repo_root = Path(__file__).resolve().parent.parent.parent
        trace_path = (
            repo_root / "capabilities" / "data-agent" / "llm-provider" / "trace.yml"
        )
        feature_path = (
            repo_root
            / "capabilities"
            / "data-agent"
            / "llm-provider"
            / "contracts"
            / "behavior.feature"
        )

        # Read trace.yml scenarios under REQ-003 link
        trace_data = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        req_003_link = next(
            link for link in trace_data["links"] if link["req"] == "REQ-003"
        )
        trace_scenarios: list[str] = req_003_link["bdd"]["scenarios"]
        assert len(trace_scenarios) == 1
        trace_scenario_name = trace_scenarios[0]

        # Extract behavior.feature REQ-003 scenario name
        feature_text = feature_path.read_text(encoding="utf-8")
        scenario_lines = [
            line.strip().removeprefix("Scenario:").strip()
            for line in feature_text.splitlines()
            if line.strip().startswith("Scenario:")
            and "effective_llm_api_key" in line
        ]
        assert len(scenario_lines) == 1
        feature_scenario_name = scenario_lines[0]

        # Post-fix: names MUST match char-level (EMPTY in double quotes both)
        assert trace_scenario_name == feature_scenario_name, (
            f"M-FU#1 quote fix not applied:\n"
            f"  trace.yml:    {trace_scenario_name!r}\n"
            f"  behavior.feature: {feature_scenario_name!r}"
        )


class TestStrictModeBlockingFlip:
    """Stage E α' E-1: --strict is the BLOCKING mechanism for G21 (severity NOT
    reclassified). main() uses _validate_capability_with_evidence; under --strict
    a WARN (no evidence pass_rate=1.0 AND no runbook 4-field justification) →
    exit 1. Proves the E-1 flip blocks on a gap and passes when justified.
    """

    _FEATURE = (
        "Feature: T\n\n"
        "  @REQ-001 @CTR-test @risk:critical @adapter:python\n"
        "  Scenario: Strict-mode scenario\n"
        "    Given a precondition\n"
    )

    def _scaffold(self, tmp_path: Path) -> Path:
        cap_dir = _make_capability_dir(tmp_path)
        (cap_dir / "contracts").mkdir()
        (cap_dir / "contracts" / "behavior.feature").write_text(
            self._FEATURE, encoding="utf-8"
        )
        (cap_dir / "trace.yml").write_text(
            yaml.safe_dump(
                {
                    "capability": "test.cap",
                    "schema_version": "1.2",
                    "links": [
                        {
                            "req": "REQ-001",
                            "bdd": {
                                "feature": "contracts/behavior.feature",
                                "scenarios": ["Strict-mode scenario"],
                            },
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return cap_dir

    def test_runbook_justified_strict_exit_0(self, tmp_path: Path) -> None:
        from scripts.sdd.check_bdd_acceptance import _validate_capability_with_evidence

        cap_dir = self._scaffold(tmp_path)
        _write_runbook(
            cap_dir,
            "# Runbook\n\n"
            "原因: pre-Phase-M3 step defs land\n"
            "替代验证手段: manual verification\n"
            "升级触发条件: blocking on Phase M4\n"
            "预计时间: M3 EOL\n",
        )
        summary = _validate_capability_with_evidence(cap_dir, tmp_path)
        assert summary.warn_count == 0
        assert summary.pass_count == 0
        assert any("DEFERRED" in message for message in summary.messages)
        assert summary.exit_code(strict=True) == 0

    def test_no_evidence_no_runbook_strict_exit_1(self, tmp_path: Path) -> None:
        from scripts.sdd.check_bdd_acceptance import _validate_capability_with_evidence

        # §7 justification removed + no evidence → WARN → --strict blocks
        cap_dir = self._scaffold(tmp_path)
        summary = _validate_capability_with_evidence(cap_dir, tmp_path)
        assert summary.warn_count >= 1
        assert summary.exit_code(strict=True) == 1
        # Pre-flip (WARNING mode, no --strict) did NOT block:
        assert summary.exit_code(strict=False) == 0


def _executed_metadata() -> dict:
    return {
        "covered_scenarios": ["Observed"], "pass_rate": 1.0,
        "status": "PASS", "source_kind": "actual_observation",
        "execution": {"command": "offline-check", "output_ref": "original.log", "exit_code": 0,
                      "test_counts": {"tests": 1, "passed": 1, "failed": 0, "skipped": 0}},
    }


def test_declared_result_without_original_outputs_cannot_pass(tmp_path: Path) -> None:
    from scripts.sdd._common.bdd_helpers import bdd_evidence_status

    assert bdd_evidence_status(_executed_metadata(), "Observed") == "UNVERIFIED"


@pytest.mark.parametrize("status", ["NOT_RUN", "NOT_TESTED", "UNSUPPORTED", "REVIEW_REQUIRED"])
def test_unexecuted_status_is_never_behavior_pass(tmp_path: Path, status: str) -> None:
    from scripts.sdd._common.bdd_helpers import bdd_evidence_status

    payload = _original_outputs(tmp_path)
    payload["status"] = status
    assert bdd_evidence_status(payload, "Observed", tmp_path) == "UNVERIFIED"


def _original_outputs(tmp_path: Path) -> dict:
    payload = _executed_metadata()
    log = b"Fixed fixture original execution output\n"
    xml = b'<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="probe" name="test_observed"/></testsuite>'
    (tmp_path / "original.log").write_bytes(log)
    (tmp_path / "original.xml").write_bytes(xml)
    payload["execution"].update({
        "output_sha256": hashlib.sha256(log).hexdigest(),
        "junit_ref": "original.xml", "junit_sha256": hashlib.sha256(xml).hexdigest(),
        "scenario_test_ids": {"Observed": ["probe::test_observed"]},
    })
    return payload


@pytest.mark.parametrize(("source", "expected"), [
    ("actual_observation", "PASS"), ("synthetic_fixture", "SELFTEST"),
    ("software_test", "SELFTEST"), ("unknown", "UNVERIFIED"),
])
def test_original_bound_test_outcomes_keep_source_claims_separate(
    tmp_path: Path, source: str, expected: str,
) -> None:
    from scripts.sdd._common.bdd_helpers import bdd_evidence_status

    # Fictional actual-source conditions exercise classification, not runtime sampling.
    payload = _original_outputs(tmp_path)
    payload["source_kind"] = source
    assert bdd_evidence_status(payload, "Observed", tmp_path) == expected


@pytest.mark.parametrize("mutation", ["missing_log", "changed_log", "wrong_scenario", "secret_ref", "skipped", "nonfinite_rate"])
def test_incomplete_or_modified_original_evidence_is_not_pass(tmp_path: Path, mutation: str) -> None:
    from scripts.sdd._common.bdd_helpers import bdd_evidence_status

    payload = _original_outputs(tmp_path)
    if mutation == "missing_log":
        (tmp_path / "original.log").unlink()
    elif mutation == "changed_log":
        (tmp_path / "original.log").write_text("changed", encoding="utf-8")
    elif mutation == "wrong_scenario":
        payload["execution"]["scenario_test_ids"] = {"Different": ["probe::test_observed"]}
    elif mutation == "secret_ref":
        payload["execution"]["output_ref"] = ".env"
    elif mutation == "skipped":
        payload["execution"]["test_counts"] = {"tests": 1, "passed": 0, "failed": 0, "skipped": 1}
    else:
        payload["pass_rate"] = float("nan")
    assert bdd_evidence_status(payload, "Observed", tmp_path) == "UNVERIFIED"
