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
created: 2026-10-12
date: 2026-10-12
owner: ranzuozhou
commit_sha: c91d3151d14388f3caab689e5045344c6a134196
scenario_count: 6
pass_rate: 1.0
hitl_triggered: true
risk_breakdown: {critical: 3, high: 3, medium: 0, low: 0}
adapter_coverage: [python, tdd-bdd]
source_kind: synthetic_fixture
---

# Evidence: Six offline core BDD scenarios

## §1 Context

Owner explicitly authorized the offline core and necessary synthetic acceptance.
Codex implemented and verified it in feature/582-offline-eval-core. commit_sha is
the checkout base, not a commit containing this uncommitted implementation.
This evidence concerns core conditions; CLI and actual runtime acceptance remain deferred.

## §2 Method

The frozen [feature](../../contracts/behavior.feature) is bound by
[capability test-module steps](../../../../../tests/bdd/data_agent/evaluation/test_evaluation_bdd.py).
All six scenarios ran through the existing hardened offline pytest runner together
with 63 unit tests. No service, runtime or model invocation occurred.

The actual-source safety scenario uses fictional, explicitly labelled unit conditions
to exercise HARD_FAIL logic. It does not assert that an actual red-line incident was
sampled. Domain/Prompt labels and the separate SWE check were simulated by the same
Agent; no human signatures or separate subagent review are claimed.

## §3 Result

Six scenarios passed; pass_rate=6/6=1.0 is BDD test acceptance, not an EVAL runtime
metric. The combined run passed 69 tests. No failing scenarios or policy skips.
Twelve deprecation warnings came from the existing gherkin dependency.

The delivered synthetic replay remains SELFTEST_ONLY, runtime metrics=null,
baseline_eligible=false and classification code 3. The public main anchor remains
absent. Its contract check is deferred and not made green by these tests.

The hardened runner accepts no JUnit/HTML output flag. It was left unchanged;
[actual verbose console output](2026-10-12_core_pytest.txt) is retained instead.
Remote CI was not executed. Complete capability and actual observation acceptance
remain pending; next work is the separately authorized CLI interface.

## §4 Related Artifacts

- bdd-feature: [contracts/behavior.feature](../../contracts/behavior.feature)
- contract: [python.contract.yml](../../contracts/python.contract.yml)
- tests: [unit tests](../../../../../tests/unit/test_eval_core.py)
- tdd-test-list: [tasks](../../tasks.md)
- report: [core acceptance](../reports/2026-10-12_offline_core_acceptance.md)
- PR: none; no commit, push or Issue-state change.

Publication preparation: console evidence retains actual test names/results and warnings, with only local worktree/venv paths redacted. Core/report input hashes and outputs are unchanged. Owner subsequently authorized commit, ordinary dual push and Draft PR; earlier no-PR statements describe the core-delivery phase.
