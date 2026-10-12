---
type: evidence
subtype: bdd
capability: data-agent.evaluation
covered_reqs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006]
covered_scenarios:
  - Dataset identity and every planned case are preserved
  - Semantic checks require a bound role-review verdict
  - A repaired final SQL does not hide the first failed attempt
  - A confirmed red-line failure remains hard without a baseline
  - Synthetic success cannot become a runtime baseline
  - Replay cannot load application credentials or connect to services
  - Local CLI emits deterministic synthetic reports with a real classification
  - CLI rejects a secret path before opening any file
  - CLI preserves a pre-existing output artifact
created: 2026-10-12
date: 2026-10-12
owner: ranzuozhou
commit_sha: 5b8833c523f4401de7b70deb5a82b908f3a9c763
source_artifact_digest: 2db977bbfe6ae39399106e323354129fc6434e66c27b3b68f781f928803cbfe0
scenario_count: 9
pass_rate: 1.0
hitl_triggered: true
risk_breakdown: {critical: 6, high: 3, medium: 0, low: 0}
adapter_coverage: [python, tdd-bdd]
source_kind: synthetic_fixture
---

# Evidence: Nine offline core and local CLI BDD scenarios

All nine bound [scenarios](../../contracts/behavior.feature) passed through the
existing hardened offline runner in the current candidate worktree. The full
[actual verbose console](2026-10-12_cli_windows_alias_pytest.txt) contains each
BDD node result and 145 total passing tests, including 136 units. pass_rate=9/9
is BDD software test evidence; it is not a runtime EVAL metric.

The commit_sha field records the checkout base, not a commit containing the
uncommitted candidate. The source_artifact_digest binds six evaluation sources,
three test modules, seven fixed JSON/JSONL fixtures and three contract files by
the algorithm in the [CLI acceptance record](../reports/2026-10-12_offline_cli_acceptance.md).
No new PR or published candidate SHA is claimed.

The existing six scenarios preserve identity, role-review binding, first SQL
failure, red-line precedence, synthetic isolation and no-service behavior. Three
new CLI scenarios demonstrate stable reports, secret rejection before file reads
and preservation of existing report artifacts. Independent review identified a
Windows trailing-dot/space alias issue; the corrected candidate additionally
passed fourteen before-metadata alias regressions and the normal-parent-syntax
positive test. The earlier [130-test log](2026-10-12_cli_pytest.txt) is retained
as pre-fix history and is not the final evidence binding.

Actual-source conditions are fictional, explicitly named software-test inputs.
No actual observation, secret, SQL, model, database or external dependency was
used. SELFTEST_ONLY outputs retain null metrics and baseline_eligible=false.
Actual sampling/provenance/runtime acceptance, Owner acceptance, repository
approval and publication remain separate states.

The implementation delegate recorded this fresh run; the coordinator's
independent verification is recorded separately, not impersonated here.
