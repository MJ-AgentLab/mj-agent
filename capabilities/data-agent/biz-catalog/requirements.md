---
type: capability-requirements
capability: data-agent.biz-catalog
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Requirements: QCM Catalog Mirror

> Phase M1 baseline. 3 REQs (all @risk:high). Survey: `_refactor-scan/m1-other-pilots-survey.md` §A.

## REQ-001 — Catalog schema completeness

**Priority**：high

**Statement**：qcm_catalog.yaml SHALL declare the 10 contract-required top-level keys; `find_biz_context()` SHALL fail loudly if any required key is missing.

**Rationale**：`finder.py` hard-codes references to specific catalog keys via `_METRIC_KEYWORDS`, `_PERIOD_KEYWORDS`, `_DIMENSION_KEYWORDS`, `_COMPARISON_KEYWORDS`. Missing top-level key → `KeyError` at `find_biz_context()` call time. Existing test `tests/unit/test_biz_catalog.py::test_catalog_top_level_keys` asserts the contract set.

**Acceptance**：

- 10 contract-required top-level keys present (current YAML has 13 keys total; 10 required for `find_biz_context()` to operate):
  - `version` (str, semver)
  - `catalog_kind` (str, discriminator; currently `qcm`)
  - `metrics` (mapping<str, mapping> — per-family description + column_root)
  - `periods` (mapping<str, mapping> — per-period suffix + time_column + time_column_type + abbreviation)
  - `metric_column_shapes` (mapping<str, mapping> — per-period primary/examples + quantile_family for weekly+)
  - `dimensions` (list<mapping> — 8 entries with suffix/description/has_dim_column/dim_column/join_*)
  - `signal_tables` (list<mapping> — 3 entries; role=signal; excluded from biz_dws fact table predicate)
  - `dimension_tables` (list<mapping> — 2 entries; primary_key/join_key/stable)
  - `fact_table_pattern` (mapping — template/example/total_count)
  - `forbidden_access` (mapping — schemas list + notes)
- 3 additional informational keys present in current YAML:
  - `source` (mapping — provenance: guide/standard/adr/bundle_path/status/drift_notes)
  - `period_over_period_columns` (mapping — pattern definitions)
  - `runtime_constraints` (mapping — statement_timeout_sec + recommended_client)
- `load_catalog()` is `@cache`-decorated; cache cleared via `load_catalog.cache_clear()` in test fixtures
- `load_catalog()` raises `ValueError` if top-level YAML root is not a mapping (e.g. list / scalar)

**BDD Examples**：

- **Given** a fresh process boot
- **When** `load_catalog()` is called
- **Then** the returned dict contains all 10 required top-level keys; if `signal_tables` (or any required key) is absent, `find_biz_context()` raises `KeyError("signal_tables")` mentioning the missing key

**Trace**：REQ-001 → `contracts/catalog.contract.yml` (schema STRUCTURE block) + `contracts/behavior.feature` Scenario 1 + `tests/unit/test_biz_catalog.py::test_catalog_top_level_keys`

---

## REQ-002 — Catalog ↔ DB alignment (drift detector)

**Priority**：high

**Statement**：Every `signal_tables[].name` / `dimension_tables[].name` SHALL resolve to a live analyst-visible biz_dws/biz_dwd table; per-period `time_column` SHALL exist on at least one matching `_total` fact table.

**Rationale**：Catalog is a mirror of the live upstream DB. Drift (upstream rename / drop / new table) → catalog becomes stale → generated SQL fails or returns wrong data. Contract test `tests/contract/test_qcm_catalog_alignment.py` encodes the alignment assertions; offline against a sanitized snapshot fixture since #499 PR-0c (no credential gate). Real-data drift is detected separately by `scripts/diff_biz_schema.py`.

**Acceptance**：

- 3 signal_tables names resolve to live tables visible to analyst role:
  - `dws_qcm_preprocessed_data` (biz_dws)
  - `dws_qcm_etl_metrics` (biz_dws)
  - `dws_qcm_ready_signal` (biz_dws)
- 2 dimension_tables names resolve:
  - `dwd_dim_product_interface` (biz_dwd)
  - `dwd_dim_institution` (biz_dwd)
- Each dimension_table's `join_key` exists as a column in the resolved table
- For each period (daily / weekly / monthly / quarterly / yearly), the `time_column` exists on at least one matching `_total` fact table (e.g. `biz_dws.dws_qcm_qrynum_daily_total` has `data_date`)
- `forbidden_access.schemas` (5 schemas) NOT visible to analyst role
- Catalog `version` field is semver; bumped when schema structure changes (informational; not enforced)

**Documented drift (informational; not REQ-mandated)**：

- Catalog `header_comments.source.status: drift_detected` — staged STANDARD specifies `stat_date / stat_week / ...` + `qrynum / tntcnt` + `tenant_code`; actual DEV DB uses `data_date / week / month / quarter / year` + `<period>_<metric>` + `tenant_id`. Catalog mirrors **actual DB** so generated SQL runs; re-sync deferred until upstream mj-system PR1/PR2 lands.

**BDD Examples**：

- **Given** a freshly loaded catalog with 3 `signal_tables` entries
- **When** analyst lists biz_dws tables from the sanctioned snapshot of the warehouse
- **Then** each entry's `name` exists in the returned set; mismatch surfaces a catalog-vs-DB drift error naming the missing table

**Trace**：REQ-002 → `contracts/catalog-db-alignment.contract.yml` + `behavior.feature` Scenario 2 + `tests/contract/test_qcm_catalog_alignment.py` (offline snapshot fixtures since #499 PR-0c)

---

## REQ-003 — SKILL ↔ catalog coherence

**Priority**：high

**Statement**：Active in-source SKILLs (`biz-domain-context` / `qcm-analysis` / `safe-sql-analysis`) SHALL reference only metric / period / dimension keys that exist in `qcm_catalog.yaml`; biz table names referenced in SKILL.md body SHALL resolve in the sanctioned snapshot of the warehouse.

**Rationale**：SKILL bodies are LLM-facing prompt content (concatenated by `_build_system_prompt()` in `agent.py`). Stale references → LLM hallucinates non-existent tables / columns → guardrail rejects or DB errors. Existing test `tests/contract/test_biz_schema_alignment.py` regex-extracts table refs from SKILL bodies and asserts DB resolution.

**Acceptance**：

- 3 active SKILLs (per `agent.py:_ACTIVE_SKILLS`):
  - `biz-domain-context` (v0.1; active; domain:SKILL; track:agent)
  - `qcm-analysis` (v0.1; active)
  - `safe-sql-analysis` (v0.2; active; updated 2026-05-12)
- All metric families referenced in SKILL bodies exist in catalog `metrics` (e.g. `qrynum`, `tntcnt`)
- All period names referenced exist in catalog `periods` (e.g. `daily`, `monthly`)
- All dimension suffixes referenced exist in catalog `dimensions[].suffix` (e.g. `_total`, `_by_tenant`)
- All biz_dws.*/biz_dwd.* table names referenced resolve in the snapshot payload (analyst-visible scope)
- Daily / monthly metric column patterns documented in catalog `metric_column_shapes` resolve to actual column names

**Documented stale test reference (informational)**：

- `tests/contract/test_biz_schema_alignment.py` loads a skill named `mj-ddd-semantics` which appears stale (not in current `_ACTIVE_SKILLS`); 3 active skills are `biz-domain-context` / `qcm-analysis` / `safe-sql-analysis`. Test update tracked as TBD-M3 cleanup task (T-003).

**BDD Examples**：

- **Given** catalog `metrics` has families `{qrynum, tntcnt}` and `periods` has `{daily, weekly, monthly, quarterly, yearly}`
- **When** an active SKILL body references metric family `daily_qrynum_total`
- **Then** family `qrynum` resolves in catalog `metrics`; period `daily` resolves in catalog `periods`; table `biz_dws.dws_qcm_qrynum_daily_total` resolves in the snapshot payload

**Trace**：REQ-003 → `contracts/catalog-db-alignment.contract.yml` (SKILL alignment section) + `behavior.feature` Scenario 3 + `tests/contract/test_biz_schema_alignment.py` (offline snapshot fixtures since #499 PR-0c)

---

> Phase M1 baseline. All 3 REQs sourced from `_refactor-scan/m1-other-pilots-survey.md` §A.
> TBD Phase M3: contract test for stale `mj-ddd-semantics` reference fix; no new tests added in M1.
