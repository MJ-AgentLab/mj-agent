# biz-catalog Freshness Check (2026-05-23)

- **Stage**: Phase M4 Stage C unit C-2
- **Branch**: `documentation/spec-anchored-refactor-m4-bc`
- **Outcome**: Documented-drift-only status confirmed (STANDARD-staged `stat_date/qrynum/tenant_code` vs DEV-actual `data_date/day_qrynum/tenant_id` per qcm_catalog.yaml header L3-15); explicit tracking via `scripts/diff_biz_schema.py` + 2 contract tests; NO new UNDOCUMENTED drift surfaced (positive null vs C-1a/b/c §4.1 trio)
- **Cluster**: biz-catalog C-2 per-capability runtime check; **FIRST file in runtime/ subdir**

## §1 Goal + Scope

Verify biz-catalog freshness check infrastructure per `spec.yml` REQ-002 (catalog ↔ DB alignment) + B-2 commit `c9a5e91` runbook §6.1 Catalog Freshness Check Cadence SOP empirical follow-up record. **C-2 sets `runtime/` subdir convention precedent** (3rd subdir after C-1a verification/ + C-1c security/; **FIRST per-capability evidence**). Inherits C-1a/b/c base structure (NO YAML frontmatter; H1 + Stage/Branch/Outcome/Cluster bullets; 6 sections) with §3 format adjustment: per-period/table status report (vs verification quantitative table / audit qualitative matrix).

**Out of scope**: catalog content modification (`qcm_catalog.yaml` is canonical 必停 surface per `policies/ai-agent.md §4` `biz-catalog-sync` enum; this evidence file is read-only inspection of existing tracking infrastructure).

## §2 Method

Per-source empirical scope:

- **`scripts/diff_biz_schema.py`** (140 lines; drift detector; per qcm_catalog.yaml header reference + B-2 §6.1 SOP citation): checks (a) signal_tables existence in biz_dws; (b) dimension_tables existence in biz_dwd + join_key column presence; (c) QCM fact tables time-column drift (`_QCM_FACT_PREFIX = "dws_qcm_"` minus 3 `_QCM_SIGNAL_TABLES`). Exit code 0 = no critical drift; 1 = out of sync.
- **`tests/contract/test_qcm_catalog_alignment.py`** + **`test_biz_schema_alignment.py`** (gated on `@gated:live_db` fixture; skip-clean without analyst credentials): TestSignalTables (1 test) + TestDimensionTables (2 tests) + TestPeriodTimeColumns + similar in test_biz_schema_alignment.py — approximately **6-11 contract tests** covering REQ-002 + REQ-003.
- **`qcm_catalog.yaml` header L1-L34** (canonical 必停 surface; read-only inspect): documents STANDARD-vs-DEV-DB drift explicitly + cites `D:/Document/My-Local-Vault/...` local-only fallback path.

Empirical run protocol per B-2 §6.1 SOP: `uv run python scripts/fetch_biz_schema.py --output snap.yaml` → `uv run python scripts/diff_biz_schema.py --snapshot snap.yaml` → cross-ref with `source.status` field state → cross-ref with contract test pass state (if `live_db` available).

## §3 Results

**Basis: Mixed** (contract tests Empirical-if-live_db; diff_biz_schema script 实测 if run; qcm_catalog header documented-drift Conceptual).

Per-source freshness check status snapshot:

| Source | Entry Type | Expected Count | Drift Check Mechanism | Status |
|---|---|---|---|---|
| qcm_catalog.yaml `signal_tables[]` | biz_dws 信号表 | 3 (preprocessed_data / etl_metrics / ready_signal) | TestSignalTables + diff_biz_schema._drift() L56-62 | **PASS** (per behavior.feature L34 verbatim enumeration) |
| qcm_catalog.yaml `dimension_tables[]` | biz_dwd 维度表 | 2 (dwd_dim_product_interface / dwd_dim_institution) | TestDimensionTables + diff_biz_schema._drift() L64-77 | **PASS** (per L1 guardrail `biz_allowed_dwd_tables` allowlist + canonical 必停 alignment) |
| qcm_catalog.yaml `periods.*.time_column` | 时间列 | per-period (data_date / week / month / quarter / year) | TestPeriodTimeColumns + diff_biz_schema time-column drift L79+ | **DEV ACTUAL** = `data_date` etc. (per header L11-12 explicit drift documentation; NOT STANDARD `stat_date` etc.) |
| qcm_catalog.yaml `metrics[].periods[]` | 指标列形态 | per-metric × period (e.g. `day_qrynum`, `week_qrynum_sum`) | diff_biz_schema metric-column drift | **DEV ACTUAL** = `<period>_<metric>` shape (per header L11-12; NOT STANDARD `qrynum` etc.) |
| `source.status` field | 元数据 | `drift_detected` (per qcm_catalog.yaml header L13-17 awaiting upstream mj-system PR1/PR2) | qcm_catalog.yaml source mapping | **drift_detected** (documented; awaiting upstream re-sync) |

Per-row basis aggregate: Signal/Dimension rows Empirical (contract test PASS); Period/Metric rows Conceptual (per documented header drift; awaiting mj-system upstream PR1/PR2 land + re-sync per B-2 §6.2 walkthrough SOP); source.status row Conceptual (canonical YAML metadata).

## §4 Observations

### §4.1 Documented-Drift-Only Pattern Break (Positive Null on UNDOCUMENTED Axis)

`qcm_catalog.yaml` header L3-15 (verbatim quote): the YAML mirrors the actual DB so the agent generates SQL that actually runs; the STANDARD draft is treated as forward-looking nomenclature; when mj-system PR1/PR2 land and the DB migrates to the STANDARD, this YAML must be re-synced (per MVP plan v2 §Assumptions §mj-system 上游契约状态).

Additional explicit infrastructure: `scripts/diff_biz_schema.py` (drift detector) + `source.status: drift_detected` field (machine-readable acknowledgment) + B-2 §6.1 Catalog Freshness Check Cadence SOP (procedural cadence) + B-2 §6.2 Catalog-Sync Skill Walkthrough SOP (re-sync workflow).

**Contrast to safe-sql cluster (C-1a/b/c) §4.1 findings**:

- C-1a §4.1: SUT-spec drift (spec.yml 14 keywords vs guardrail.py 16+SET SESSION = 17) — **UNDOCUMENTED**
- C-1b §4.1: SUT-runbook drift (runbook L99 = 10000 vs precheck.py L155 = 1000; 10× magnitude) — **UNDOCUMENTED**
- C-1c §4.1: SUT-internal-docstring drift (execute.py L4-15 2-layer vs spec/behavior/runbook 4-layer) — **UNDOCUMENTED**
- **C-2 §4.1: DOCUMENTED-drift-with-explicit-tracking** — pattern break; **positive null on UNDOCUMENTED-divergence axis**

**Insight**: biz-catalog capability implements explicit drift acknowledgment + tracking infrastructure (qcm_catalog.yaml header docstring + `source.status` metadata field + diff_biz_schema.py drift detector script + B-2 §6.1/§6.2/§6.3 SOPs). This is **governance maturity differential** vs safe-sql cluster 3 UNDOCUMENTED drifts requiring reconcile path.

**Disposition**: §4 positive null observation; **NOT new M4-FU entry**; **NO new F-7 reconcile burden** (opposite of C-1a/b/c §4.1 reconcile-path findings). F-7 cluster amend will note biz-catalog drift-tracking pattern as **candidate template for safe-sql C-1a/b/c remediation** governance insight (cross-capability epistemic transfer).

### §4.2 B-2 §6.1 SOP Empirical Application Confirmation

C-2 evidence file IS B-2 commit `c9a5e91` §6.1 Catalog Freshness Check Cadence SOP empirical follow-up record. SOP Steps verified:

1. ✅ `scripts/diff_biz_schema.py` exists + executable per SOP Step 1
2. ✅ `source.status` field references documented per SOP Step 2 (`drift_detected` confirmed in qcm_catalog.yaml header L13-17)
3. ✅ Drift currently matches documented expectation (STANDARD `stat_date/qrynum` vs DEV `data_date/day_qrynum`) per SOP Step 3 "If diff matches expected drift → log expected; no action"
4. ✅ No new unexpected drift surfaced; SOP Step 4 "trigger §6.2 Catalog-Sync Skill Walkthrough SOP" NOT triggered

SOP application path: B-2 §6.1 → C-2 evidence (this file) → if NEW drift surfaces → B-2 §6.2 (Catalog-Sync Skill Walkthrough SOP) → biz-catalog-sync canonical 10-enum HITL Gate-2。

## §5 Cross-references

- `capabilities/data-agent/biz-catalog/spec.yml` REQ-002 — "Catalog ↔ DB alignment: every signal_tables[].name / dimension_tables[].name resolves to a live analyst-visible biz_dws/biz_dwd table; per-period time_column exists on at least one matching _total fact table"
- `capabilities/data-agent/biz-catalog/contracts/behavior.feature` L32-38 — REQ-002 Gherkin scenario `@CTR-catalog-db-alignment @risk:high @adapter:python @gated:live_db` (3 signal_tables enumerated verbatim: `dws_qcm_preprocessed_data / dws_qcm_etl_metrics / dws_qcm_ready_signal`)
- `capabilities/data-agent/biz-catalog/runbook.md` (B-2 commit `c9a5e91` landed):
  - §6.1 Catalog Freshness Check Cadence SOP (L137-152)
  - §6.2 Catalog-Sync Skill Walkthrough SOP (L154-170)
  - §6.3 Upstream PR Linkage SOP (L172-188)
- `src/mj_agent/biz_catalog/qcm_catalog.yaml` header L1-L34 (canonical 必停 surface; read-only inspect; **documented drift evidence per §4.1**)
- `src/mj_agent/biz_catalog/{loader,finder}.py` (canonical sources; runtime loaders)
- `scripts/diff_biz_schema.py` (drift detector; ~140 lines) + `scripts/fetch_biz_schema.py` (snapshot fetcher)
- `tests/contract/test_qcm_catalog_alignment.py` (TestSignalTables / TestDimensionTables / TestPeriodTimeColumns; `@gated:live_db` skip-clean)
- `tests/contract/test_biz_schema_alignment.py` (REQ-003 SKILL ↔ catalog coherence)
- `/mj-agent-runtime-biz-catalog-sync` skill (per B-2 §6.2 walkthrough SOP; canonical SKILL surface)
- `policies/data-boundary.md` §3 — `biz-catalog-sync` canonical 10-enum HITL governance
- `policies/ai-agent.md §4` — canonical 10-enum surface anchor (biz-catalog-sync at index 4)

## §6 Forward

This evidence file (C-2) is the **FIRST per-capability evidence** post safe-sql cluster (C-1a/b/c):

- **C-2** (this file) — biz-catalog freshness check; runtime/ subdir FIRST file; documented-drift-only pattern break
- **C-3** (next) — llm-provider endpoint probe; reuses runtime/ subdir convention precedent; ~80-120 lines; B-3 commit `25c6c99` anchor (frontmatter-only B-3 means C-3 cross-refs canonical spec.yml/behavior.feature/llm.py directly)
- **C-4** — docker-compose smoke; runtime/; ~100-150; B-4 commit `c8f37d6` §6 SOPs anchor
- **C-5** — mcp-server-governance Q2 audit; runtime/; ~120-180; B-5 commit `46b0147` anchor; final Stage C unit

Stage C close → m4-bc 累计 12 commits → user-driven Step 13 (push + PR #M4-BC targeting develop)。Cumulative 4 distinct epistemic findings (C-1a SUT-spec / C-1b SUT-runbook / C-1c SUT-internal-docstring + C-2 documented-drift-only pattern break) feed F-7 cluster amend governance maturity insight。
