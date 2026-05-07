"""Contract tests — keep canonical declarations and live DB schema in sync.

Phase 1 sub 1.G — verifies that:
  - ``src/mj_agent/biz_catalog/qcm_catalog.yaml`` enumerations
    (signal_tables / dimension_tables / period.time_column) actually
    exist in the live biz DB
  - ``src/mj_agent/skills/mj-ddd-semantics/SKILL.md`` references only
    tables/columns that the catalog declares (transitive — if catalog
    aligns with DB, SKILL aligns transitively)

Tests are gated by the ``contract`` pytest marker AND the ``live_db``
session fixture (skip when ``POSTGRES_ANALYST_USER`` absent). CI runs
``uv run pytest tests/contract -m contract`` after unit/eval — green
when no env, real check when env present.

Out of scope for 1.G (Phase 2):
  - existing 4 MVP skills' SKILL.md contract coverage
  - cross-repo skill drift (SKILL referring to mj-system table that no
    longer exists in mj-system)
  - column-level contract (currently only table + time-column level)
"""
