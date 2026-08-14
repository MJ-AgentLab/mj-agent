---
type: capability-runbook
capability: data-agent.biz-catalog
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-23
last_verified: 2026-05-20
---

# Runbook: QCM Catalog Mirror

> Phase M1 baseline. ≥ 3 sections. Cross-refs `docs/guide/[GUIDE]_Developer_Onboarding.md` §7 (M6 X4 dissolved dev_studio_walkthrough into it).

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

# Catalog ↔ snapshot alignment (offline; synthetic fixtures, NO credentials needed)
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/contract -m contract
```

Expected — **no credential axis any more** (Epic #499 PR-0c made these contract tests
fixture-only; they used to session-skip unconditionally and verify nothing):

| Command | Result |
|---|---|
| `pytest tests/unit/test_biz_catalog.py` | all pass (no DB) |
| `pytest tests/unit/test_find_biz_context.py` | all pass (no DB) |
| `run_offline_pytest.py tests/contract -m contract` | all pass (synthetic snapshot fixtures) |

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
- Run `/mj-agent-runtime-biz-catalog-sync` skill — read-only diff between catalog and an Owner-attested sanitized snapshot (offline; never a live DB); surfaces drift list
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

**Cadence reference**: 主动检查 cadence per §6.1 Catalog Freshness Check Cadence SOP; reactive symptom (this block) 是 when 检查命中 drift; proactive cadence (§6.1) 是 when to run the check。

## §4 Related Artifacts

- `contracts/catalog.contract.yml` — REQ-001 schema completeness
- `contracts/catalog-db-alignment.contract.yml` — REQ-002 + REQ-003 alignment
- `contracts/behavior.feature` — 3 Gherkin scenarios
- `/mj-agent-runtime-biz-catalog-sync` skill — read-only diff between catalog and an Owner-attested sanitized snapshot (offline; never a live DB)
- `policies/data-boundary.md` §3 — biz-catalog-sync 4 项必停 governance
- `docs/guide/[GUIDE]_Developer_Onboarding.md` §7 — broader Studio walkthrough (M6 X4 absorbed dev_studio_walkthrough)
- `§6.1 Catalog Freshness Check Cadence SOP` — cross-ref `qcm_catalog.yaml source.status` + `scripts/diff_biz_schema.py` reference
- `§6.2 Catalog-Sync Skill Walkthrough SOP` — wraps `/mj-agent-runtime-biz-catalog-sync` skill (black-box workflow reference; `biz-catalog-sync` canonical 10-enum HITL per `policies/ai-agent.md §4`)
- `§6.3 Upstream PR Linkage SOP` — cross-repo coordination with mj-system PR1/PR2 tracking (generic wording; specific PRs evolve)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` when:

- REQ-001 schema completeness violation in production (LLM hits KeyError during user query)
- REQ-002 drift not caught by contract tests (live DB silently diverged for ≥ 30 days)
- REQ-003 SKILL incoherence causes LLM to generate sustained hallucinations (multiple sessions affected)

Path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per `policies/archive.md` retention class permanent.

## §6 Standard Operating Procedures (SOPs)

> Procedural how-to for the 3 most common biz-catalog maintenance scenarios.
> Each SOP follows Trigger / Pre-conditions / Steps / Verify / Rollback structure
> per B-1 §6 SOPs precedent (safe-sql runbook §6; PR #M4-BC scope).

### §6.1 Catalog Freshness Check Cadence SOP

**Trigger**: Periodic catalog ↔ DB alignment check (cadence: weekly during active development phase OR after any mj-system upstream merge announcement); OR `source.status: drift_detected` field investigation per §3 catalog drift symptom block.

**Pre-conditions**: An Owner-attested sanitized `schema-v1` snapshot present under
`.mj-agent-local/biz-schema-snapshots/` (gitignored) and captured within the last 7 days.
**No credentials and no DB reachability are required or permitted** — `scripts/diff_biz_schema.py`
is offline-only since Epic #499 PR-0c, and `scripts/fetch_biz_schema.py` is a fail-closed
tombstone (exit 2). If no fresh snapshot exists, this SOP yields `SKIP_NO_SNAPSHOT` /
`SKIP_STALE_SNAPSHOT` and the correct outcome is to record **"not verified"**, not "no drift".

**Steps**:

1. Run `uv run python scripts/diff_biz_schema.py` against the sanitized snapshot → capture the
   result code (`PASS_NO_DRIFT` / `DRIFT_DETECTED` / `SKIP_*` / `REJECT_INVALID_SNAPSHOT`)
2. Cross-reference output with `qcm_catalog.yaml source.status` field state (current expected: `drift_detected` per header)
3. If diff matches expected drift (staged STANDARD `stat_date/qrynum` vs DEV `data_date/day_qrynum`) → log expected; no action
4. If new unexpected drift surfaced → trigger §6.2 Catalog-Sync Skill Walkthrough SOP

**Verify**: `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/contract -m contract`
→ expected all PASS. Note these assert catalog claims against the **synthetic fixture**, so a green
run does not by itself prove the live warehouse agrees — that is what step 1's snapshot diff is for.

**Rollback**: N/A (read-only check; no state change)

### §6.2 Catalog-Sync Skill Walkthrough SOP

**Trigger**: §6.1 surface unexpected drift OR scheduled re-sync after upstream mj-system PR1/PR2 lands per §6.3.

**Pre-conditions**: Catalog modification triggers canonical 10-enum **`biz-catalog-sync`** HITL Gate-2 (per `policies/ai-agent.md §4`); Steps below MUST NOT modify `qcm_catalog.yaml` before HITL Gate-2 ack obtained.

**Steps** (skill wraps; see `/mj-agent-runtime-biz-catalog-sync` for black-box workflow):

1. Invoke `/mj-agent-runtime-biz-catalog-sync` skill — skill performs read-only diff between catalog and an Owner-attested sanitized snapshot (offline; never a live DB), surfaces drift items as proposed changes
2. **HITL Gate-2 question** — Open `biz-catalog-sync` canonical enum question; obtain user ack on proposed `qcm_catalog.yaml` modifications
3. User applies proposed diff to `qcm_catalog.yaml` via Edit (skill outputs diff; does not auto-write)
4. Update `qcm_catalog.yaml source.status: synced` field
5. Regression: `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/contract -m contract`

**Verify**: tests/contract alignment tests PASS; `source.status: synced` field reflects new state

**Rollback**: Revert `qcm_catalog.yaml` changes; tests/contract should return to prior PASS state with drift accepted

### §6.3 Upstream PR Linkage SOP

**Trigger**: mj-system upstream PR (typically PR1 / PR2 per `qcm_catalog.yaml` header reference) announces or merges biz_dws schema changes (column renames / table additions / etc.).

**Pre-conditions**: Cross-repo coordination with mj-system team; mj-agent SUT side does not directly modify upstream biz_dws schema.

**Steps**:

1. File `[AGENT]` issue tracking upstream PR (use generic title format: "Track mj-system PR <ID> — <change summary>")
2. Monitor upstream PR status (open / merged / reverted)
3. After upstream PR merged + deployed to DEV biz DB → trigger §6.1 Catalog Freshness Check Cadence SOP
4. If §6.1 surfaces drift matching upstream PR scope → trigger §6.2 Catalog-Sync Skill Walkthrough SOP
5. Update `[AGENT]` issue with completion status + reference §6.2 sync result

**Verify**: tests/contract alignment tests PASS post-sync; `qcm_catalog.yaml source.status: synced`; `[AGENT]` issue closed

**Rollback**: If upstream PR reverted → revert §6.2 sync changes; re-verify tests with drift state restored

---

## §7 Unautomated Scenario Justifications (M-FU#7)

> Per `sdd/adapters/bdd-tdd.md` L121 + L160 + L161 (G21+G22 share runbook
> justification source per R-15-1 resolution); BDD scenarios that are not yet
> automated must include 4-field justification (原因 / 替代验证手段 / 升级触发
> 条件 / 预计时间).

### G22/G21 Justification: load_catalog rejects YAML whose root parses to a list (not a mapping)

> **Status (post-M6 truth-up 2026-06-10): automated** — pytest-bdd binding green in CI (tests/bdd blocking); justification below retained as historical record + G21 fallback source.

- **REQ**: REQ-001 / **Risk**: high / **Adapter**: python
- **原因**: M1 baseline；pytest-bdd 框架的 step definitions 集中到 M3 batch
  land（与 safe-sql 同节奏）。
- **替代验证手段**: catalog loader (`src/mj_agent/biz_catalog/loader.py`)
  schema validation 路径 unit-tested；★ 具体 test 文件路径 TBD per owner
  verify（worksheet 标 需 owner 核实）。
- **升级触发条件**: M3 pytest-bdd step defs 集中实装；
  `tests/bdd/data_agent/biz_catalog/` step folder 落地后该 BDD scenario 走
  pytest-bdd 自动跑。
- **预计时间**: M3 EOL（per Phase M3 BDD 集中实装节奏；与 safe-sql 同 batch）。

### G22/G21 Justification: Catalog signal_tables must resolve in live biz_dws

> **Status (post-M6 truth-up 2026-06-10): automated (live_db env-gated)** — pytest-bdd binding real; skips in CI without POSTGRES_ANALYST_USER; justification below retained as historical record + G21 fallback source.

- **REQ**: REQ-002 / **Risk**: high / **Adapter**: python / **@gated:live_db**
- **原因**: live_db 依赖 — automation 需 live test biz_dws postgres fixture
  (per `@gated:live_db` tag)；CI runner 当前无 live_db。
- **替代验证手段**: DEV 环境 manual verification（analyst 角色 SELECT 查询
  biz_dws 验 signal_tables 解析）；catalog YAML 中静态 mapping 已 freeze
  (`src/mj_agent/biz_catalog/qcm_catalog.yaml`)。
- **升级触发条件**: live_db test fixture 实装（CI runner 接 test biz_dws OR
  docker test postgres + seed data）。
- **预计时间**: M3+（live_db infra 准备后；具体里程碑 TBD per owner planning）。

### G22/G21 Justification: Active SKILL bodies reference only resolvable catalog symbols and DB tables

> **Status (post-M6 truth-up 2026-06-10): automated (live_db env-gated)** — pytest-bdd binding real; skips in CI without POSTGRES_ANALYST_USER; justification below retained as historical record + G21 fallback source.

- **REQ**: REQ-003 / **Risk**: high / **Adapter**: runtime-skill / **@gated:live_db**
- **原因**: 跨 artifact 验证（SKILL bodies × catalog × live DB）；automation
  需 live_db + runtime-skill loader integration（per `@gated:live_db` +
  `@adapter:runtime-skill`）。
- **替代验证手段**: SKILL body loader strip + frontmatter 一致性已 unit-tested
  (V4 claude-skill contracts validator BLOCKING per Stage C C-a 34P/0W/0F
  clean)；catalog symbol resolution × SKILL body cross-ref 当前 manual review。
- **升级触发条件**: (a) live_db test fixture；(b) runtime-skill loader test
  infrastructure（cross-ref validation harness 验 SKILL body 引用的 symbol
  + DB table 都可解析）。
- **预计时间**: M3+（live_db + runtime-skill infra；TBD per owner planning）。

---

> Phase M1 baseline. M2 will refine §3 troubleshooting with M3 BDD findings.
