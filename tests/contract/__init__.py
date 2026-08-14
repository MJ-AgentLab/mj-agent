"""Contract tests — keep canonical declarations and the sanitized biz snapshot in sync.

Phase 1 sub 1.G, rebased onto the offline boundary at Epic #499 PR-0c. Verifies that:
  - ``src/mj_agent/biz_catalog/qcm_catalog.yaml`` enumerations
    (signal_tables / dimension_tables / period.time_column) resolve in the
    snapshot payload
  - ``src/mj_agent/skills/mj-ddd-semantics/SKILL.md`` references only
    tables/columns that the catalog declares (transitive — if catalog
    aligns with the snapshot, SKILL aligns transitively)
  - ``scripts/fetch_biz_schema.py`` / ``scripts/diff_biz_schema.py`` and this whole
    package stay free of any dotenv / DB client / introspection import (AC-08)
  - the snapshot validator itself: closed ``schema-v1`` envelope, sanctioned-root path
    confinement, the 7-day injectable clock, and SKIP-is-not-PASS semantics

Selection is by the ``contract`` pytest marker only. **There is no credential gate.**
Before PR-0c these tests hung off the ``live_db`` session fixture and therefore skipped in
full, verifying nothing; they now run for real against hand-authored synthetic fixtures in
``fixtures/biz_snapshots/`` and are green in CI. Pytest still never opens a biz-live route:
nothing under test imports a database client.

Because the fixtures are synthetic, a green run proves the *assertion logic* and the
*boundary*, not that the live warehouse currently agrees. Real-data drift detection is a
separate motion — ``scripts/diff_biz_schema.py`` against an Owner-attested sanitized
snapshot under ``.mj-agent-local/biz-schema-snapshots/``, which reports
``SKIP_NO_SNAPSHOT`` / ``SKIP_STALE_SNAPSHOT`` rather than implying freshness it cannot see.

Out of scope for 1.G (Phase 2):
  - existing 4 MVP skills' SKILL.md contract coverage
  - cross-repo skill drift (SKILL referring to mj-system table that no
    longer exists in mj-system)
  - column-level contract (currently only table + time-column level)

**Note on schema sync intent (Phase 1)**:
  Drift reconciliation remains **fail-then-manual-fix**: ``diff_biz_schema.py`` reports
  ``DRIFT_DETECTED`` and the maintainer updates ``qcm_catalog.yaml`` /
  ``mj-ddd-semantics/SKILL.md`` by hand. mj-agent does **not** actively pull mj-system
  schema changes; the automated sync mechanism is planned for Phase 2 (see
  ``plans/mj-agent-roadmap-v1.6.md`` §4.4 "schema 自动同步").
"""
