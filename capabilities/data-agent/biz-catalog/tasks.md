---
type: capability-tasks
capability: data-agent.biz-catalog
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Tasks: QCM Catalog Mirror

> Phase M1 baseline. critical/high REQ tasks include `tdd.test_list[]`.

## Backlog

### T-001 — Phase M1 capability artifact suite
- **Phase**：M1 / **Priority**：critical (capability meta) / **Linked REQ**：N/A
- **Status**：in-progress (this PR)
- **HITL trigger**：M1 baseline HITL Gate (4 pilot batch)

### T-002 — REQ-001 catalog schema completeness
- **Phase**：M1 / **Priority**：high / **Linked REQ**：REQ-001
- **Contract changed?**：no (frozen anchor)
- **HITL trigger**：biz-catalog-sync (any modification to qcm_catalog.yaml → HITL)
- **Status**：done (M1 contract reverse-engineering)
- **TDD test_list**：
  - `tests/unit/test_biz_catalog.py::test_catalog_top_level_keys` (existing)
  - `tests/unit/test_biz_catalog.py::test_catalog_metric_families` (existing)
  - `tests/unit/test_biz_catalog.py::test_catalog_periods` (existing)
  - **TBD-M3** `tests/unit/test_loader_yaml_validation.py::test_load_catalog_rejects_non_mapping_root` (REQ-001 ValueError path)

### T-003 — REQ-002 catalog ↔ DB alignment
- **Phase**：M1 (contract) / M3 (BDD step defs) / M4 (evidence/runtime/ auto-collect)
- **Priority**：high / **Linked REQ**：REQ-002
- **Contract changed?**：no
- **HITL trigger**：biz-catalog-sync
- **Status**：done (M1 contract; existing live_db tests cover)
- **TDD test_list**：
  - `tests/contract/test_qcm_catalog_alignment.py::TestSignalTables` (existing; live_db gated)
  - `tests/contract/test_qcm_catalog_alignment.py::TestDimensionTables` (existing)
  - `tests/contract/test_qcm_catalog_alignment.py::TestPeriodTimeColumns` (existing)
  - `tests/contract/test_qcm_catalog_alignment.py::TestForbiddenSchemas` (existing)

### T-004 — REQ-003 SKILL ↔ catalog coherence
- **Phase**：M1 (contract) / M3 (clean stale test refs)
- **Priority**：high / **Linked REQ**：REQ-003
- **Contract changed?**：no
- **HITL trigger**：runtime-skill-content-change (modifying SKILL body would break this)
- **Status**：done (M1 contract); TBD-M3 stale skill name cleanup (T-005)
- **TDD test_list**：
  - `tests/contract/test_biz_schema_alignment.py::TestSkillTableRefs` (existing; references stale `mj-ddd-semantics`)
  - `tests/contract/test_biz_schema_alignment.py::TestMetricColumnPatterns` (existing)
  - **TBD-M3** rewrite test_biz_schema_alignment.py to use 3 current `_ACTIVE_SKILLS`

### T-005 — Clean stale `mj-ddd-semantics` skill reference (TBD-M3)
- **Phase**：M3
- **Priority**：low (test hygiene; not blocking REQ-003 contract)
- **Linked REQ**：REQ-003
- **HITL trigger**：none (test-only change; no SKILL body modification)
- **Status**：TBD-M3
- **Description**：`tests/contract/test_biz_schema_alignment.py` loads skill `mj-ddd-semantics` which is not in `_ACTIVE_SKILLS`. Update to use `biz-domain-context` + `qcm-analysis` + `safe-sql-analysis`. Verify no behavior change (test should still pass against live DB).

### T-006 — Catalog drift policy formalization (open question)
- **Phase**：TBD (Phase M2 design discussion; depends on §5 Q1)
- **Priority**：medium
- **Linked REQ**：REQ-002 (drift detector)
- **HITL trigger**：none (process design only)
- **Status**：TBD
- **Description**：Decide whether to add REQ-004 covering drift-tolerance policy explicitly (catalog mirrors actual DB until upstream PR1/PR2 lands). Discussed in design.md §5 Q1.

## In-Progress
(none beyond T-001)

## Done
(populated as M1 PR progresses)

## Anti-Backlog
- **Modify `qcm_catalog.yaml` to match staged STANDARD**：rejected — would break generated SQL until upstream mj-system PR1/PR2 lands. Re-sync triggered by upstream, not by M1.
- **Add unit tests for `find_biz_context()` fallback behavior at M1**：deferred to M3 — existing `tests/unit/test_find_biz_context.py` already has 5+ behavioral cases.

---

> Phase M1 baseline. 4 active tasks + 2 TBD tasks. tdd.test_list[] uses existing tests
> for REQ-001/002/003.
