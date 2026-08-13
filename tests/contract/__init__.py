"""Contract tests — keep canonical declarations and live DB schema in sync.

Phase 1 sub 1.G — verifies that:
  - ``src/mj_agent/biz_catalog/qcm_catalog.yaml`` enumerations
    (signal_tables / dimension_tables / period.time_column) actually
    exist in the live biz DB
  - ``src/mj_agent/skills/mj-ddd-semantics/SKILL.md`` references only
    tables/columns that the catalog declares (transitive — if catalog
    aligns with DB, SKILL aligns transitively)

Tests are gated by the ``contract`` pytest marker AND the ``live_db``
session fixture. The fixture is an unconditional
``SKIP_POLICY_EXTERNAL_DEPENDENCY`` boundary: pytest never opens a biz-live
route, regardless of credential presence. Agent/CI invokes the hardened
offline runner and records the structured skips.

Out of scope for 1.G (Phase 2):
  - existing 4 MVP skills' SKILL.md contract coverage
  - cross-repo skill drift (SKILL referring to mj-system table that no
    longer exists in mj-system)
  - column-level contract (currently only table + time-column level)

**Note on schema sync intent (Phase 1)**:
  Contract tests here are a **defensive fail-then-manual-fix** mechanism —
  when biz schema drifts, the relevant test fails on the analyst's local
  run, signalling the maintainer to update ``qcm_catalog.yaml`` /
  ``mj-ddd-semantics/SKILL.md`` by hand. mj-agent does **not** actively
  pull mj-system schema changes; the automated sync mechanism is planned
  for Phase 2 (see ``plans/mj-agent-roadmap-v1.6.md`` §4.4 "schema
  自动同步"). These legacy live contracts remain collected but policy-skipped;
  they are not current-schema evidence. PR-0c supplies the sanctioned
  snapshot-only replacement path.
"""
