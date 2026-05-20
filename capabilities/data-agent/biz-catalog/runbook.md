---
type: capability-runbook
capability: data-agent.biz-catalog
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
last_verified: 2026-05-20
---

# Runbook: QCM Catalog Mirror

> Phase M1 baseline. ≥ 3 sections. Cross-refs `docs/runbook/dev_studio_walkthrough.md` (Phase M5 will dissolve).

## §1 Startup

`qcm_catalog.yaml` is loaded automatically by `load_catalog()` on first call to `find_biz_context`. No explicit startup step needed; pool is `@cache`-lazy.

Verify catalog loadable + finder operational:

```bash
uv run python -c "from src.mj_agent.biz_catalog.finder import find_biz_context; r = find_biz_context('上月 product interface 调用量'); print('metrics:', r['metrics'], 'periods:', r['periods'])"
```

Expected output: `metrics: ['qrynum']` (resolved from "调用量") + `periods: ['monthly']` (resolved from "上月").

## §2 Health Check

```bash
# Schema sanity (no DB needed)
uv run pytest tests/unit/test_biz_catalog.py -q

# Finder behavior (no DB needed)
uv run pytest tests/unit/test_find_biz_context.py -q

# Live DB alignment (requires POSTGRES_ANALYST_USER + biz pg reachable)
uv run pytest tests/contract/test_qcm_catalog_alignment.py -m contract -q
uv run pytest tests/contract/test_biz_schema_alignment.py -m contract -q
```

Expected:

| Command | DB creds present | DB creds absent |
|---|---|---|
| `pytest tests/unit/test_biz_catalog.py` | all pass (no DB) | all pass (no DB) |
| `pytest tests/unit/test_find_biz_context.py` | all pass | all pass |
| `pytest tests/contract/test_qcm_catalog_alignment.py -m contract` | all pass | session-skip clean |
| `pytest tests/contract/test_biz_schema_alignment.py -m contract` | all pass | session-skip clean |

## §3 Troubleshooting

### Symptom: `KeyError: 'signal_tables'` (or similar key) when LLM calls find_biz_context

**Diagnostic**：REQ-001 schema completeness violated — `qcm_catalog.yaml` missing a contract-required top-level key.

**Resolution**：

- Verify YAML structure: `python -c "import yaml; d=yaml.safe_load(open('src/mj_agent/biz_catalog/qcm_catalog.yaml')); print(list(d.keys()))"`
- Expected keys: 10 required (version / catalog_kind / metrics / periods / metric_column_shapes / dimensions / signal_tables / dimension_tables / fact_table_pattern / forbidden_access) + 3 informational (source / period_over_period_columns / runtime_constraints)
- If missing key — biz-catalog-sync HITL required; do NOT edit YAML directly. Use `/mj-agent-runtime-biz-catalog-sync` skill (read-only diff).

### Symptom: `tests/contract/test_qcm_catalog_alignment.py` fails

**Diagnostic**：REQ-002 catalog ↔ DB drift detected — catalog references a table or column that no longer exists in upstream biz DB.

**Resolution**：

- Identify drift: look at failing assertion (signal_tables / dimension_tables / time_columns / forbidden_schemas)
- Run `/mj-agent-runtime-biz-catalog-sync` skill — read-only diff between catalog and live DB schema; surfaces drift list
- Decide policy:
  - **Upstream renamed column** (e.g. `stat_date` → `data_date`): file `[AGENT]` issue; update `qcm_catalog.yaml` via biz-catalog-sync HITL (4 项必停)
  - **Catalog has stale extra entry** (DB dropped it): update catalog accordingly
- Run alignment tests again after sync

### Symptom: `tests/contract/test_biz_schema_alignment.py` fails

**Diagnostic**：REQ-003 SKILL ↔ catalog coherence violated — SKILL.md body references a metric/period/dimension/table that doesn't exist.

**Resolution**：

- Check if failure is due to known stale `mj-ddd-semantics` skill reference in test (per T-005 cleanup task): file `[BUG]` issue if so
- Otherwise: identify which SKILL body has a stale reference (test output names the SKILL + table); SKILL body change requires runtime-skill-content-change HITL (4 项必停)
- Use `/mj-agent-runtime-skill-doc-improve` skill (read-only diff) to propose SKILL body update

### Symptom: `find_biz_context` returns unexpected `candidate_table_names`

**Diagnostic**：finder.py's keyword dicts (`_METRIC_KEYWORDS` / `_PERIOD_KEYWORDS` / `_DIMENSION_KEYWORDS` / `_COMPARISON_KEYWORDS`) may not cover the question's vocabulary.

**Resolution**：

- Add NL keyword variants to finder.py keyword dicts (not a 4 项必停 file — modifying finder.py is allowed without HITL, but cross-cap impact on safe-sql REQ-002 should be evaluated)
- Add `notes` field to finder.py result explaining fallback behavior

### Symptom: catalog drift in `source.status: drift_detected` field — when does this re-sync?

**Diagnostic**：Catalog mirrors actual DB, not staged STANDARD. `source.status: drift_detected` is informational; re-sync triggered when upstream mj-system PR1/PR2 lands the new column names.

**Resolution**：no action required at agent side. When upstream lands:

1. Track upstream PR1/PR2 in `[AGENT]` issue
2. After upstream PR merged, run `/mj-agent-runtime-biz-catalog-sync` skill against new DB
3. Update `qcm_catalog.yaml` via biz-catalog-sync HITL
4. Update header `source.status: synced`
5. Re-run alignment tests; should pass

## §4 Related Artifacts

- `contracts/catalog.contract.yml` — REQ-001 schema completeness
- `contracts/catalog-db-alignment.contract.yml` — REQ-002 + REQ-003 alignment
- `contracts/behavior.feature` — 3 Gherkin scenarios
- `/mj-agent-runtime-biz-catalog-sync` skill — read-only diff between catalog and live DB
- `policies/data-boundary.md` §3 — biz-catalog-sync 4 项必停 governance
- `docs/runbook/dev_studio_walkthrough.md` — broader Studio walkthrough (Phase M5 dissolves)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` when:

- REQ-001 schema completeness violation in production (LLM hits KeyError during user query)
- REQ-002 drift not caught by contract tests (live DB silently diverged for ≥ 30 days)
- REQ-003 SKILL incoherence causes LLM to generate sustained hallucinations (multiple sessions affected)

Path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per `policies/archive.md` retention class permanent.

---

> Phase M1 baseline. M2 will refine §3 troubleshooting with M3 BDD findings.
