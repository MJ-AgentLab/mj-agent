---
type: evidence
subtype: bdd
capability: data-agent.evaluation
covered_reqs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006]
date: 2026-10-12
created: 2026-10-12
owner: ranzuozhou
commit_sha: a96d759c080f4568e6810084f90fadce7b2c75cf
scenario_count: 11
pass_rate: 1.0
hitl_triggered: true
risk_breakdown: {critical: 7, high: 4, medium: 0, low: 0}
adapter_coverage: [python, tdd-bdd]
covered_scenarios:
  - Dataset identity and every planned case are preserved
  - Semantic checks require a bound role-review verdict
  - A repaired final SQL does not hide the first failed attempt
  - A confirmed red-line failure remains hard without a baseline
  - Synthetic success cannot become a runtime baseline
  - Replay cannot load application credentials or connect to services
  - Synthetic CLI writes deterministic reports without a runtime baseline
  - Actual source is refused before observation access
  - Unsafe input paths cannot expose protected content
  - Output collision or partial write is never a completed report delivery
  - A baseline file cannot turn a synthetic run into runtime comparison
---

# #582 T-007a BDD PASS record

- Date: 2026-10-12, Asia/Taipei; implementer and same-Agent SWE round: Codex; delegation: NONE.
- Base: a96d759c080f4568e6810084f90fadce7b2c75cf; feature/582-baseline-cli; candidate UNCOMMITTED.
- Contracts: contracts/behavior.feature; steps: tests/bdd/data_agent/evaluation/test_evaluation_bdd.py.
- Six core plus five CLI scenarios = 11 automated scenarios, all high/critical, seven critical.
- Hardened execution: 64 core + 156 CLI unit + 11 BDD = 231 passed, 22 third-party DeprecationWarning; [transcript](2026-10-12_baseline_cli_pytest.txt).
- New scenario: fixed synthetic baseline bytes unchanged; two native process reports identical, exit3, SELFTEST_ONLY/NOT_EVALUATED, metrics=null, baseline_eligible=false.
- Existing actual refusal now includes an explicit unread baseline; only manifest read, no replay or output.
- Unsafe-path BDD now probes baseline; unit suite retains config/output coverage and adds baseline guards.
- Root/platform guard and output collision/partial failure remain. Linux/macOS native CLI success NOT_RUN/DEFERRED_FS_CAPABILITY; software mocks/static checks do not replace native evidence.
- Actual-branch core scenarios remain fictional unit conditions; no actual file replay, sampling, source acceptance or service access.
- This software evidence does not replace target acceptance or Owner final acceptance; no Git publication.
