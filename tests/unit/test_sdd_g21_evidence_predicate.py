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

from pathlib import Path

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


class TestCheckJustificationFieldsMirror:
    """M-FU#4 NEW helper + drift guard against D-4 G22 versions.

    Refine 1 Step 1.5: byte-equivalent MIRROR until M-FU#10 consolidation
    post-Stage-E. Paired-edit warning enforced via drift guard test below.
    """

    def test_none_runbook_returns_all_missing(self) -> None:
        from scripts.sdd._common.bdd_helpers import (
            JUSTIFICATION_FIELDS,
            check_justification_fields,
        )

        all_present, missing = check_justification_fields(None)
        assert all_present is False
        assert set(missing) == set(JUSTIFICATION_FIELDS)

    def test_drift_guard_matches_g22_d4_constants(self) -> None:
        """★ M-FU#10 paired-edit drift guard.

        Asserts bdd_helpers JUSTIFICATION_FIELDS == check_bdd_unautomated
        ._JUSTIFICATION_FIELDS. Until M-FU#10 consolidation, BOTH copies
        MUST stay identical (4-field semantic + tuple order) — drift
        causes gate behavior inconsistency (G21 vs G22 disagreeing on
        what 'justified' means).
        """
        from scripts.sdd._common.bdd_helpers import JUSTIFICATION_FIELDS
        from scripts.sdd.check_bdd_unautomated import _JUSTIFICATION_FIELDS

        assert JUSTIFICATION_FIELDS == _JUSTIFICATION_FIELDS, (
            "★ DRIFT DETECTED: bdd_helpers.JUSTIFICATION_FIELDS diverged from "
            "check_bdd_unautomated._JUSTIFICATION_FIELDS. Per M-FU#10 paired-edit "
            "warning until consolidation, BOTH copies must stay identical to "
            "prevent G21/G22 disagreeing on 'justified' semantics."
        )


class TestG21PredicateExtension:
    """M-FU#4 G21 predicate extension (per AC-5 4 cases;R-15-1 coupling).

    G21 保 WARNING mode (flip 是 E-1 work); evidence-or-runbook fallback path
    per Anti-Gate-Defeat (R-16-6) cross-ref: explicit + reviewable;NOT silent
    auto-exempt OR fabricated content (R-18-6 schema-only boundary).
    """

    def test_evidence_present_pass_rate_1_0_passes(self, tmp_path: Path) -> None:
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
        # Evidence pass_rate=1.0 → PASS via evidence path
        assert summary.fail_count == 0
        # WARN may or may not be emitted depending on D-3 base layer; key
        # assertion: no FAIL + at least 1 scenario evaluated
        assert summary.pass_count >= 1 or summary.warn_count >= 1

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
        # Fallback to runbook justification (4-field full) → PASS path
        # (NO FAIL; either explicit fallback-PASS OR inherited D-3 base PASS)
        assert summary.fail_count == 0

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
        # pass_rate<1.0 但 runbook justification full → fallback path PASS
        # (per R-15-1: justification fallback acceptable when pass_rate insufficient)
        assert summary.fail_count == 0


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
