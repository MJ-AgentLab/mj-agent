---
type: capability-design
capability: data-agent.biz-catalog
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Design: QCM Catalog Mirror

> Phase M1 baseline (≤ 200 lines per R-G3).

## §1 Context

mj-agent generates SQL against the upstream business warehouse (biz domain).
The agent's LLM doesn't know the warehouse schema — it relies on a **local
data dictionary mirror** to translate natural language questions into specific
table + column references. That mirror is `qcm_catalog.yaml`.

**Why mirror, not query?** Live DB schema introspection would:

1. Add a DB roundtrip to every NL → SQL turn (latency cost)
2. Reveal cardinality / list of tables to the LLM (information leak)
3. Couple the agent's startup to DB availability (booting offline-first preferred)

A **static YAML mirror** trades freshness for determinism. Drift between mirror
and live DB is the cost; existing contract tests in `tests/contract/` catch it.

**Threats**：

1. Catalog YAML malformed (parse failure) → loader raises → graph fails to build
2. Top-level key missing → `find_biz_context()` raises `KeyError` per REQ-001
3. Table name in catalog doesn't exist in live DB → generated SQL fails
4. SKILL.md body references a metric / period / dimension that doesn't exist
   in catalog → LLM hallucinates SQL that gets rejected by L1 guardrail
5. Upstream renames column (e.g. `stat_date` → `data_date`) → catalog goes
   stale → REQ-002 contract test fails (intentional drift detector)

## §2 Decision

**Single static YAML + cached loader + pure-function finder + 4 contract tests**.

| Component | File | Purpose |
|---|---|---|
| YAML data | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | 13 top-level keys (10 required + 3 informational) |
| Loader | `src/mj_agent/biz_catalog/loader.py` | `@cache` `load_catalog()` + `catalog_path()` |
| Finder | `src/mj_agent/biz_catalog/finder.py` | `find_biz_context(question: str)` — NL → 14-field dict via 4 keyword dicts |
| Schema test | `tests/unit/test_biz_catalog.py` | top-level key set + metric family enumeration |
| Behavior test | `tests/unit/test_find_biz_context.py` | 5+ keyword cases incl. fallback |
| Alignment test | `tests/contract/test_qcm_catalog_alignment.py` | signal_tables + dimension_tables + periods.time_column resolve in live DB |
| SKILL alignment | `tests/contract/test_biz_schema_alignment.py` | SKILL body table refs resolve in live DB + metric column patterns |

**Catalog drift policy**：catalog mirrors **actual DEV DB**, not staged STANDARD.
Re-sync triggered only by mj-system upstream PR1/PR2 landing (renaming
`stat_date → data_date` etc. in staged STANDARD). Current YAML header comment
documents this with `source.status: drift_detected`.

**Why catalog ↔ STANDARD drift is tolerated**：generated SQL must execute now.
The STANDARD is a future-state target. Mirroring STANDARD before upstream PRs
would break agent. Drift visibility maintained via `source.status` field +
contract test detection.

## §3 Architecture

```
User NL question
      │
      ▼
[find_biz_context(question)]      ──── finder.py
      │
      ├──► load_catalog()         ──── loader.py (@cache)
      │        └─► qcm_catalog.yaml  (4 项必停: biz-catalog-sync hard stop)
      │
      ├──► 4 keyword dicts:
      │     - _METRIC_KEYWORDS   (qrynum / tntcnt aliases EN+ZH)
      │     - _PERIOD_KEYWORDS   (daily/weekly/monthly/... aliases)
      │     - _DIMENSION_KEYWORDS (per dim suffix aliases)
      │     - _COMPARISON_KEYWORDS (period_over_period triggers)
      │
      └──► returns 14-field dict:
             - metrics / periods / dimensions / comparisons (resolved)
             - candidate_table_names (cross-product biz_dws.dws_qcm_<m>_<p>_<d>)
             - signal_tables, dimension_tables, fact_table_pattern (verbatim)
             - forbidden_access, runtime_constraints (verbatim)
             - notes (fallback explanation)

LLM consumes:
- 3 active SKILL.md bodies (biz-domain-context / qcm-analysis / safe-sql-analysis)
  reference catalog symbols (qrynum / daily / _total / ...)
- find_biz_context output → narrow LLM's candidate table set
```

**Cross-capability dependencies (2 refs)**：

- **safe-sql** (inbound)：safe-sql REQ-002 `require_time_range` reads
  `periods.*.time_column` via `_all_time_columns()` in `precheck.py:58-59`
- **tool-chain** (outbound; Phase 2+)：`find_biz_context` is registered in
  `ALL_TOOLS` (`tools/__init__.py`); tool schema contract owned by future
  tool-chain capability

## §4 Tradeoffs

| Choice | Pros | Cons | Rationale |
|---|---|---|---|
| **A. Static YAML mirror (chosen)** | Deterministic, fast, offline-first, version-controlled | Drift cost | Latency + info-leak concerns weigh against live introspection |
| B. Live DB introspection on boot | Always fresh | Boots fail if DB unreachable; DB churn impacts agent | Rejected — fragile |
| C. YAML + periodic sync job | Fresh + offline-first | Job needs maintenance + GRANT scope expansion | Considered Phase 3+; for now manual sync via `/mj-agent-runtime-biz-catalog-sync` skill |
| **D. `@cache` decorator (chosen)** | Single load per process | Tests must clear cache | Standard Python pattern; `cache_clear()` documented |
| E. Module-level constant | Even cheaper | No reload without restart | Equivalent in practice; `@cache` is more explicit |
| **F. Keyword dict NL matching (chosen)** | No LLM dependency in finder | Coverage gaps need manual curation | Critical — finder must be deterministic so LLM has stable context |
| G. LLM-driven NL parsing | Better coverage | Adds LLM call before LLM call | Rejected — defeats finder's purpose |

## §5 Open Questions

1. **Catalog drift re-sync trigger** — currently informal (mj-system PR1/PR2
   landing). Should there be a periodic check (e.g. quarterly contract test on
   live DB) that emits warning when STANDARD ↔ actual DB drift narrows? Phase M4
   evidence/runtime/ tracking could surface this.

2. **SKILL ↔ catalog coherence enforcement** — REQ-003 relies on
   `test_biz_schema_alignment.py` which references stale skill name
   `mj-ddd-semantics`. Update needed to use 3 current `_ACTIVE_SKILLS`. TBD-M3.

3. **`forbidden_access.schemas` vs `is_table_allowed()` SOT split** — catalog
   has its own `forbidden_access.schemas` list (5 schemas); `config.py:Settings`
   has `biz_allowed_schemas`. Should they be unified? Likely Phase 2+
   capability-boundary refactor.

4. **`find_biz_context` cross-product explosion** — `candidate_table_names` is
   the Cartesian product of metric × period × dimension; with 2 metrics × 5
   periods × 8 dimensions = 80 candidates per call. Most are pruned downstream
   by L1 guardrail allowlist. Consider trimming earlier? Phase 3+ optimization.

> Phase M2 will fill in adapter §BDD Rules + §TDD Rules per
> `sdd/adapters/{python,runtime-skill,bdd-tdd}.md`.
