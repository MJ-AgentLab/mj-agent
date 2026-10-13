---
type: evidence
subtype: bdd
capability: data-agent.evaluation
covered_reqs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006]
date: 2026-10-12
created: 2026-10-12
owner: ranzuozhou
commit_sha: a96d759c080f4568e6810084f90fadce7b2c75cf
scenario_count: 14
pass_rate: 1.0
hitl_triggered: true
risk_breakdown: {critical: 9, high: 5, medium: 0, low: 0}
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
  - Coherent source references never authenticate runtime evidence
  - Source inspection lists missing observations without judging cases
  - Source inspection cannot access files services or application configuration
---

# #582 T-007b BDD PASS record

Codex implemented and performed same-Agent independent SWE review; delegation NONE.
Base a96d759; feature/582-baseline-cli, candidate UNCOMMITTED. Owner independently authorized T-007b A on 2026-10-12; no Git publication or live/source acceptance.

Hardened runner: 108 core/inspection unit + 156 CLI unit + 14 BDD = 278 passed, 28 third-party gherkin DeprecationWarning. [Raw transcript](2026-10-12_source_inspection_pytest.txt) is the fresh final run; 6 core + 5 CLI + 3 inspection scenarios automated.

New scenarios prove fictional coherent references remain UNVERIFIED; missing HP-01 appears as a structural gap; sentinels and repeat results verify explicit-memory isolation. Runtime metrics null, baseline_eligible=false, review coverage NOT_CHECKED. API classification3 is returned data, not process EVAL success.

Existing CLI actual early refusal/baseline paths/output guards remain. Memory platform models for win32/linux/darwin do not prove native Linux/macOS IO. Actual-branch metadata in tests is fictional, never a real observation pack; source authenticity and target acceptance NOT_RUN.

[Acceptance](../reports/2026-10-12_source_inspection_acceptance.md) and new raw-byte binding accompany this record. Historical T-007a evidence is preserved.
