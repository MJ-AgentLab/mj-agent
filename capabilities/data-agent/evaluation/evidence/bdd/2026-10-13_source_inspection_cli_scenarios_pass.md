---
type: evidence
subtype: bdd
capability: data-agent.evaluation
covered_reqs:
- REQ-001
- REQ-002
- REQ-003
- REQ-004
- REQ-005
- REQ-006
date: '2026-10-13'
created: '2026-10-13'
owner: ranzuozhou
commit_sha: fd045520c0123627e53d23c0ad58bf97a6b3552e
scenario_count: 18
pass_rate: 1.0
hitl_triggered: true
risk_breakdown:
  critical: 12
  high: 6
  medium: 0
  low: 0
adapter_coverage:
- python
- tdd-bdd
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
- Coherent source references never authenticate runtime evidence
- Source inspection lists missing observations without judging cases
- Source inspection cannot access files services or application configuration
- Synthetic source inspection CLI never authenticates evidence
- Source inspection CLI refuses actual before other input access
- Invalid source inspection input cannot create a report
- Source inspection CLI preserves missing observation gaps
source_kind: software_test
status: PASS
execution:
  command: python -X utf8 -B scripts/sdd/run_offline_pytest.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py
    -q --tb=short --junitxml C:\Users\Admin\AppData\Local\Temp\mj-agent-t007c-19f63e8688f44c388693119304e76b17\bdd.xml
  exit_code: 0
  test_counts:
    tests: 18
    passed: 18
    failed: 0
    skipped: 0
  output_ref: evidence/bdd/2026-10-13_source_inspection_cli_junit_pytest.txt
  output_sha256: 39fab7fc2185b58b252e110145d1b0deb748b15c5404227f0e9edaa5f3a1ba15
  junit_ref: evidence/bdd/2026-10-13_source_inspection_cli_junit.xml
  junit_sha256: e429cee5bcf66da4a44667321976be4d3cb2a728cf698e961954b6ef9885e341
  scenario_test_ids:
    Dataset identity and every planned case are preserved:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_dataset_identity_and_every_planned_case_are_preserved
    Semantic checks require a bound role-review verdict:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_semantic_checks_require_a_bound_rolereview_verdict
    A repaired final SQL does not hide the first failed attempt:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_a_repaired_final_sql_does_not_hide_the_first_failed_attempt
    A confirmed red-line failure remains hard without a baseline:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_a_confirmed_redline_failure_remains_hard_without_a_baseline
    Synthetic success cannot become a runtime baseline:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_synthetic_success_cannot_become_a_runtime_baseline
    Replay cannot load application credentials or connect to services:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_replay_cannot_load_application_credentials_or_connect_to_services
    Synthetic CLI writes deterministic reports without a runtime baseline:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_synthetic_cli_writes_deterministic_reports_without_a_runtime_baseline
    Actual source is refused before observation access:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_actual_source_is_refused_before_observation_access
    Unsafe input paths cannot expose protected content:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_unsafe_input_paths_cannot_expose_protected_content
    Output collision or partial write is never a completed report delivery:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_output_collision_or_partial_write_is_never_a_completed_report_delivery
    A baseline file cannot turn a synthetic run into runtime comparison:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_a_baseline_file_cannot_turn_a_synthetic_run_into_runtime_comparison
    Coherent source references never authenticate runtime evidence:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_coherent_source_references_never_authenticate_runtime_evidence
    Source inspection lists missing observations without judging cases:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_source_inspection_lists_missing_observations_without_judging_cases
    Source inspection cannot access files services or application configuration:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_source_inspection_cannot_access_files_services_or_application_configuration
    Synthetic source inspection CLI never authenticates evidence:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_synthetic_source_inspection_cli_never_authenticates_evidence
    Source inspection CLI refuses actual before other input access:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_source_inspection_cli_refuses_actual_before_other_input_access
    Invalid source inspection input cannot create a report:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_invalid_source_inspection_input_cannot_create_a_report
    Source inspection CLI preserves missing observation gaps:
    - tests.bdd.data_agent.evaluation.test_evaluation_bdd::test_source_inspection_cli_preserves_missing_observation_gaps
---

# T-007c BDD software evidence

Fresh hardened runner: 340 unit + 18 BDD = 358 passed, 36 existing third-party gherkin warnings, 11.29s. Base fd045520; feature/582-source-inspection-cli, candidate UNCOMMITTED, no Git publication. Owner authorized T-007c A on 2026-10-13; no actual/live or target acceptance.

[Raw transcript](2026-10-13_source_inspection_cli_pytest.txt) proves all 18 scenarios ran, including 4 new file-adapter scenarios. The fixed inspection.expected.json predates the wrapper; synthetic labels never authenticate source/target or coverage. Invalid input creates no output, valid incomplete structure writes a single JSON/3, fictional actual labels test refusal only. Native Windows fixed NTFS only; Linux/macOS native protection deferred. Independent Agent evidence is recorded separately in the [acceptance](../reports/2026-10-13_source_inspection_cli_acceptance.md).

Additional hardened BDD-only run: 18 passed / 36 warnings, 2.76s; original log and JUnit above are independently hash-bound and map every scenario to its actual test identity. source_kind=software_test only. Existing sorted legacy evidence remains historical; G21 does not upgrade it to executed runtime PASS.
