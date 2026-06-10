---
type: capability-runbook
capability: data-agent.safe-sql
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-23
last_verified: 2026-05-20
---

# Runbook: Safe SQL 4-Layer Guardrails

> Phase M1 baseline. ≥ 3 sections per quality baseline. References
> `docs/guide/[GUIDE]_Developer_Onboarding.md` §7 for shared startup context
> (M6 X4 dissolved dev_studio_walkthrough into it; docs/runbook/ now empty).

## §1 Startup

### Local DEV

```bash
# 1. Install deps + decrypt secrets to .env
uv sync
.\scripts\setup-env.ps1

# 2. Verify L3 connection wiring (no DB call; just import-level check)
uv run python -c "from src.mj_agent.integrations.mj_system_db import get_pool; print('pool factory loaded')"

# 3. Verify L1 guardrail + L1b precheck modules importable
uv run python -c "from src.mj_agent.tools.sql import guardrail, precheck, execute; print('safe-sql modules loaded')"

# 4. Start LangGraph Studio (loads agent.py make_graph with middleware wiring)
uv run langgraph dev
```

### TEST / PROD profiles

Per `docker/CLAUDE.md`. 4-file
profile chain; `--env-file .env` explicit.

```bash
# DEV
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml up -d

# TEST (192.168.0.179)
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.test.yml up -d

# PROD (192.168.0.106)
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.prod.yml up -d
```

## §2 Health Check

```bash
# Lightweight smoke (no DB; checks LLM creds + module imports)
uv run mj-agent check

# Full pre-flight (requires POSTGRES_ANALYST_USER + biz pg reachable)
uv run pytest tests/unit/test_guardrail.py tests/unit/test_precheck.py tests/unit/test_tool_error_middleware.py -q
# Expected: ~30+ tests passed; ~25-30 seconds

# Integration test (skip-clean without DB creds)
uv run pytest tests/integration -q

# Contract tests for cross-cap deps (biz-catalog freshness; skip-clean without DB)
uv run pytest tests/contract -m contract -q
```

**Expected outcomes**：

| Command | DB creds present | DB creds absent |
|---|---|---|
| `mj-agent check` | LLM + DB OK | LLM OK + DB warning |
| `pytest tests/unit` (sql tests) | all pass | all pass (no DB needed) |
| `pytest tests/integration` | all pass | session-skip (clean) |
| `pytest tests/contract -m contract` | all pass | 12 skipped (clean) |

## §3 Troubleshooting

### Symptom: `ValueError: SQL rejected by guardrail: ...`

**Diagnostic**：L1 regex caught a write keyword / disallowed schema / multi-statement /
non-SELECT / empty SQL / out-of-allowlist biz_dwd table.

**Resolution**：

- If LLM generates write SQL → check `prompts/system.md` body (do NOT modify — `prompt-version-bump` 必停; instead file an `[AGENT]` issue with the prompt-vs-output drift evidence)
- If SQL targets `biz_ods` / `biz_ads` → these are not visible to mj-agent; ADR-009 constraint
- If targeting unlisted biz_dwd table → check `settings.biz_allowed_dwd_tables` (currently 2 dim tables); expansion requires sql-guardrail-relax HITL + cross-capability change

### Symptom: `ValueError: SQL rejected by precheck: <rule_id>: ...`

**Diagnostic**：L1b sqlglot AST rule fired. 5 rule IDs (per spec.yml REQ-002):

- `require_time_range: ...` — biz_dws fact table without time-column predicate (rule fires on schema=biz_dws + name starts_with dws_qcm_ + NOT in signal_tables)
- `no_select_star: ...` — `SELECT *` not allowed (use COUNT(*) if aggregation needed)
- `require_limit: ...` — non-aggregate detail query without LIMIT clause; **warning only** (surfaces in `envelope.precheck_warnings`; not blocking; REQ-005)
- `limit_too_large: ...` — LIMIT > threshold (currently 10000); **warning only**; tunable per query pattern
- `sqlglot_parse_failed: ...` — graceful fallback when sqlglot cannot parse; not blocking but surfaces

**Resolution**：

- Add a `WHERE` predicate on a column listed in `qcm_catalog.yaml periods.*.time_column` (currently `data_date`, `month`, etc.)
- Replace `*` with explicit columns
- For warnings (require_limit / limit_too_large): adjust query to match expected pattern OR accept warning (LLM sees them in envelope)

### Symptom: `RuntimeError: ... statement_timeout=60s ...`

**Diagnostic**：L4 — query took > 60s and DB cancelled per `R__analyst_permissions.sql`
upstream config.

**Resolution** (Chinese self-correction hint already in error message; LLM will
attempt these on retry)：

- Add GROUP BY (aggregate instead of detail)
- Narrow the time range in WHERE
- Reduce JOIN count
- If query is intrinsically slow → file `[RUNTIME]` issue; investigate upstream
  biz_dws index strategy (cross-repo to mj-system)

**Tuning parameters detail** (for §6.2 SOP reference):

- `statement_timeout` default `60s` set via upstream `R__analyst_permissions.sql` `ALTER ROLE analyst SET statement_timeout='60s'`; ANY adjustment 是 cross-repo change to mj-system + triggers canonical 10-enum `secrets-grants-or-prod-config` HITL (per `policies/ai-agent.md §4`)
- `lock_timeout` `5000ms` (5s) via DSN options in `mj_system_db.py`; pool factory-level config; adjustment requires `database-migration` enum (data-LLM boundary; ADR-006/009)
- `idle_in_transaction_session_timeout` `10000ms` (10s) via DSN options; rarely adjusted; preserves bounded resource consumption (REQ-003)
- See `§6.2 L3 Statement Timeout & Lock Timeout Tuning SOP` for the full workflow

### Symptom: `RuntimeError: database error: ...`

**Diagnostic**：Generic catch (non-`QueryCanceled` DB exception).

**Resolution**：

- Check `mj-agent-postgres` container health (for memory checkpointer) — `docker compose ps`
- Check biz pg reachability — `uv run mj-agent check` (provider-aware)
- Check `analyst` role auth — `POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD` in `.env`
- Check `mj-system-backend-network` external network exists — `docker network ls | grep mj-system`

### Symptom: graph hangs / Chainlit frontend hangs after tool call

**Diagnostic**：potential middleware regression (ADR-029). REQ-006 contract says
`handle_sql_tool_errors` (sync) and `ahandle_sql_tool_errors` (async) catch
ValueError/RuntimeError and return ToolMessage instead of re-raising.

**Resolution**：

- Verify `make_graph()` in `agent.py` has `middleware=[handle_sql_tool_errors]`
- If using Chainlit (`graph.astream` path) → verify async variant wiring (TBD-M3
  per design.md §5 Q4)
- Check `tests/unit/test_tool_error_middleware.py` passes locally

### Symptom: catalog drift breaking REQ-002 `require_time_range`

**Diagnostic**：upstream biz_dws renamed a time column (e.g. `data_date` → `stat_date`)
but `qcm_catalog.yaml periods.*.time_column` still references the old name.

**Resolution**：

- This is the **intended drift detector** — the L1b precheck rule fails loudly
- Run `/mj-agent-runtime-biz-catalog-sync` skill (read-only diff) to compare
  `qcm_catalog.yaml` vs upstream DB
- File `[AGENT]` issue with biz-catalog-sync 必停 trigger
- Resolution touches `qcm_catalog.yaml` → HITL required

## §4 Related artifacts

- `contracts/sql-guardrail.contract.yml` — REQ-001 / REQ-002 details
- `contracts/execute-sql.contract.yml` — REQ-003 / REQ-004 / REQ-005 details
- `contracts/python.contract.yml` — module signatures + REQ-006 middleware
- `contracts/behavior.feature` — 6 Gherkin scenarios
- `docs/guide/[GUIDE]_Developer_Onboarding.md` §7 — broader Studio walkthrough (M6 X4 absorbed dev_studio_walkthrough)
- `policies/data-boundary.md` — 数据-LLM 三原则 + 4 项必停 governance
- `§6.1 L2 Schema/Table Whitelist Extension SOP` — cross-ref `src/mj_agent/tools/sql/guardrail.py` `allowed_tables_per_schema` + `sql-guardrail-relax` canonical 10-enum HITL (per `policies/ai-agent.md §4`)
- `§6.2 L3 Statement Timeout & Lock Timeout Tuning SOP` — cross-ref behavior.feature REQ-003/REQ-004 + `mj_system_db.py` DSN options + upstream `R__analyst_permissions.sql`
- `§6.3 L4 Upstream DB Connection & Index Tuning SOP` — cross-ref spec.yml REQ-004 `reference_contract` + mj-system biz_dws index strategy (cross-repo)

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` writeup when:

- REQ-001 rejects valid SQL (false positive at agent boundary) ≥ 3 times in same session
- REQ-002 `require_time_range` blocks query that has valid time predicate (false positive in fact-table detection)
- REQ-003 connection hangs > 30s (lock_timeout=5s should not allow this; investigate pool exhaustion)
- REQ-004 `statement_timeout` triggers on routine analyst query (DB-side timeout suggests slow upstream)
- REQ-005 envelope key missing or wrong type (LLM behavior break)
- REQ-006 middleware fails to catch (graph crashes) → highest priority; ADR-029 regression

Postmortem path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per
`policies/archive.md` retention class `permanent`.

## §6 Standard Operating Procedures (SOPs)

> Procedural how-to for the 3 most common safe-sql tuning / extension scenarios.
> Each SOP follows Trigger / Pre-conditions / Steps / Verify / Rollback structure.
> B-1 establishes this §6 SOPs pattern as **candidate precedent** for B-2..B-5 capability
> runbooks; **not mandated** per capability content needs.

### §6.1 L2 Schema/Table Whitelist Extension SOP

**Trigger**: New biz_dwd table (beyond current 2 dim tables) needs analyst exposure; OR new schema (beyond biz_dws + biz_dwd) needs allowlist.

**Pre-conditions**: Whitelist extension triggers canonical 10-enum **`sql-guardrail-relax`** HITL Gate-2 (per `policies/ai-agent.md §4`); Steps below MUST NOT execute before HITL Gate-2 ack obtained.

**Steps**:

1. **HITL Gate-2 question** — Open canonical 10-enum question; obtain user ack on enum trigger + scope + canonical surface impact
2. Edit `src/mj_agent/config.py` `biz_allowed_dwd_tables` (or `biz_allowed_schemas`) per requested expansion
3. Regression test: `uv run pytest tests/unit/test_guardrail.py::TestTableLevelAllowlist -q`; verify new table accepted, others still rejected
4. Update `runbook.md §3 L1 guardrail symptom block` if user-facing behavior changes

**Verify**: smoke test via `is_safe_select()` against new SQL referencing newly-allowlisted table → expect `(True, '')` accept tuple

**Rollback**: Revert `config.py` allowlist change; rerun regression test → expect old behavior restored

### §6.2 L3 Statement Timeout & Lock Timeout Tuning SOP

**Trigger**: `statement_timeout` cancellation 频繁 (§3 L4 symptom fires > 5 times in 1 day) OR query patterns systematically need > 60s; OR `lock_timeout` (5s) blocks legitimate longer-locked queries.

**Pre-conditions**: `statement_timeout` adjustment 是 **cross-repo change to mj-system `R__analyst_permissions.sql`** + triggers canonical 10-enum `secrets-grants-or-prod-config` HITL; `lock_timeout` adjustment via `mj_system_db.py` DSN options triggers `database-migration` enum (data-LLM boundary; ADR-006/009).

**Steps**:

1. HITL Gate-2 question per appropriate enum
2. For `statement_timeout`: file cross-repo PR to mj-system updating `R__analyst_permissions.sql` `ALTER ROLE analyst SET statement_timeout='<new>'`
3. For `lock_timeout`: edit `src/mj_agent/integrations/mj_system_db.py` `_dsn()` function DSN options
4. Coordinate deployment: upstream migration must precede mj-agent runtime restart for `statement_timeout`; for `lock_timeout`, mj-agent compose restart suffices
5. Regression: behavior.feature REQ-003/REQ-004 scenarios still pass with new values

**Verify**: `psql -c "SHOW statement_timeout" -U analyst` against biz pg → expect new value; mj-agent fixture test with adjusted lock_timeout

**Rollback**: Revert upstream R__ migration + mj-agent DSN edit; deploy in same coordinated order

### §6.3 L4 Upstream DB Connection & Index Tuning SOP

**Trigger**: `RuntimeError: database error` 频繁 (§3 generic DB error symptom > 3/day) OR specific biz_dws query routinely hits `statement_timeout=60s` despite tuning attempts (per §6.2).

**Pre-conditions**: Upstream tuning 是 **cross-repo coordination with mj-system team**; mj-agent SUT side cannot directly modify upstream biz_dws indexes / connection pool. File `[RUNTIME]` issue with reproducible query + impact scope; awaits upstream owner ack.

**Steps**:

1. Run `EXPLAIN ANALYZE <problem-query>` via analyst psql against biz pg → capture query plan + 实测 execution time
2. Identify missing index: cross-ref `biz_dws.dws_qcm_<table>` 与 typical WHERE predicate columns
3. File `[RUNTIME]` issue with evidence — propose specific index (e.g. `CREATE INDEX ON biz_dws.dws_qcm_qrynum_daily_total (data_date, institution_id)`)
4. mj-system team review + applies index migration via their migration mechanism
5. Post-deploy: rerun problem query; verify reduced execution time + no `statement_timeout` fires

**Verify**: mj-agent integration test re-run problem query under `uv run pytest tests/integration -q`; query envelope `row_count` returned without `statement_timeout_hit=true`

**Rollback**: If index causes write/maintenance regressions on biz_dws → mj-system team drops index; documenting drop rationale in issue

---

## §7 Unautomated Scenario Justifications (M-FU#7)

> Per `sdd/adapters/bdd-tdd.md` L121 + L160 + L161 (G21+G22 share runbook
> justification source per R-15-1 resolution); BDD scenarios that are not yet
> automated must include 4-field justification (原因 / 替代验证手段 / 升级触发
> 条件 / 预计时间).

### G22/G21 Justification: L1 regex guardrail rejects blocked-keyword statement before DB contact

> **Status (post-M6 truth-up 2026-06-10): automated** — pytest-bdd binding green in CI (tests/bdd blocking); justification below retained as historical record + G21 fallback source.

- **REQ**: REQ-001 / **Risk**: critical / **Adapter**: python
- **原因**: M1 baseline 只落 contract + scenario 文本；pytest-bdd 框架的 step
  definitions 集中到 M3 batch land。
- **替代验证手段**: `tests/unit/test_guardrail.py` 已覆盖等效语义 — `TestAccepted`
  4 cases + `TestRejected` 含 9 个 blocked_keywords + `TestTableLevelAllowlist`
  6 cases,共 ~24 unit tests。
- **升级触发条件**: M3 step defs 集中实装,`tests/bdd/data_agent/safe_sql/` step
  folder 建好。
- **预计时间**: M3 EOL（per `plans/mj-agent-roadmap-v1.6.md` § Phase M3 BDD
  集中实装节奏）。

### G22/G21 Justification: L1b precheck rejects biz_dws fact-table query missing time-column predicate

> **Status (post-M6 truth-up 2026-06-10): automated** — pytest-bdd binding green in CI (tests/bdd blocking); justification below retained as historical record + G21 fallback source.

- **REQ**: REQ-002 / **Risk**: critical / **Adapter**: python
- **原因**: M1 baseline 只落 contract + scenario 文本；pytest-bdd step definitions
  集中到 M3 batch land（与 S1 同节奏）。
- **替代验证手段**: `tests/unit/test_precheck.py` 已覆盖 sqlglot AST precheck
  等效语义 ~13 cases — `TestNoSelectStar` (3) + **`TestRequireTimeRange` (5;
  直接对应该 scenario 的 time-column predicate 规则)** + `TestRequireLimit`
  (4 advisory) + `TestParseFailureGracefulFallback` (1)。
- **升级触发条件**: M3 step defs 集中实装；`tests/bdd/data_agent/safe_sql/`
  step folder 落地后该 BDD scenario 走 pytest-bdd 自动跑。
- **预计时间**: M3 EOL（per roadmap-v1.6 § Phase M3 BDD 集中实装节奏；与 S1
  同 batch）。

### G22/G21 Justification: L3 connection enforces read-only transaction + bounded timeouts via DSN options ★ coverage 弱

> **Status (post-M6 truth-up 2026-06-10): automated (live_db env-gated)** — pytest-bdd binding real; skips in CI without POSTGRES_ANALYST_USER. New offline `tests/unit/test_dsn_options.py` closes the ★ coverage 弱 gap flagged below.

- **REQ**: REQ-003 / **Risk**: critical / **Adapter**: python
- **原因**: M1 baseline；connection-layer test 基础设施（`test_dsn_options.py` +
  `test_readonly_cursor.py`）尚未实装（per trace.yml L80-83 全 TBD-M3 标记）。
- **替代验证手段 + 为何暂可接受**: 该 scenario 验证 connection 配置正确性。
  双层硬保障:(a) `src/mj_agent/integrations/mj_system_db.py` 中 DSN options
  在 connection 建立时**硬编码注入**（`default_transaction_read_only=on` +
  `lock_timeout=5s` + `idle_in_transaction_session_timeout=10s`）— 配置漂移
  即 connection 失败而非 silent 失效；(b) `analyst` PostgreSQL 角色 GRANT
  仅 SELECT 权限（DB role 层强制）— form connection 层 + role 层 double-
  defense。M3 unit test 落地前,prod 风险由双层硬约束缓解,**owner affirm
  暂可接受**。
- **升级触发条件**: M3 unit test 基础设施实装（`test_dsn_options.py` 验 DSN
  options 字串 + `test_readonly_cursor.py` 验 rollback-on-exit 行为）。
- **预计时间**: M3（per TBD-M3 markers；具体里程碑 TBD per owner planning）。

### G22/G21 Justification: L4 statement_timeout cancellation translates to Chinese self-correction hint ★ 跨 repo + 弱

- **REQ**: REQ-004 / **Risk**: critical / **Adapter**: python / **@reference-contract**
- **原因**: M1 baseline；cross-repo reference contract（mj-system
  `R__analyst_permissions.sql`）verification + live_db contract test 推迟到
  M3/M4 分阶段（per trace.yml L110-111 TBD-M3 + TBD-M4 markers）。
- **替代验证手段 + 为何暂可接受**: 三层保障:(a) SUT 侧
  `contracts/execute-sql.contract.yml § l4_timeout_and_grant` 已 freeze；
  `execute.py` 中 statement_timeout 显式 catch + 友好 Chinese hint 已实装；
  (b) `analyst` role `statement_timeout=60s` 在上游 mj-system
  `R__analyst_permissions.sql` 配置（跨仓 freeze）；(c) 任何 mj-system 上游
  SQL migration 变更会触发其仓 PR review,被相关 reviewer 察觉。**owner
  affirm**:跨仓 freeze + PR review 流程在 M3 unit / M4 live_db contract
  test 落地前可接受。
- **升级触发条件**: (a) M3 unit `test_execute_sql_timeout.py` 验 timeout
  cancellation 转 Chinese hint；(b) M4 live_db contract
  `test_safe_sql_grant_visibility.py` 验跨仓 grant 配置（live_db fixture
  必须）。
- **预计时间**: 分阶段 — M3（unit 部分）+ M4（live_db contract 部分）（per
  TBD-M3 + TBD-M4 markers）。

### G22/G21 Justification: execute_sql return envelope contains 8 required keys with documented types

> **Status (post-M6 truth-up 2026-06-10): automated (live_db env-gated)** — pytest-bdd binding real; skips in CI without POSTGRES_ANALYST_USER. New offline `tests/unit/test_execute_sql_envelope.py` covers the 8-key schema + truncation without DB.

- **REQ**: REQ-005 / **Risk**: high / **Adapter**: python
- **原因**: M1 baseline；envelope schema-conformance tests 推迟 M3（per
  trace.yml L128-130 TBD-M3 markers）。
- **替代验证手段**: `contracts/execute-sql.contract.yml § envelope_schema`
  已 freeze 8 keys + types（`executed_sql / columns / rows / row_count /
  truncated / statement_timeout_hit / business_summary / precheck_warnings`）；
  `execute.py` 实现已落 envelope 装配代码。当前依靠 contract freeze + 代码
  review 维持 schema 稳定。
- **升级触发条件**: M3 envelope tests 实装（`test_execute_sql_envelope.py`
  验 8 keys 存在 + types 正确 + truncation 行为）。
- **预计时间**: M3 EOL（per TBD-M3 markers；与 S1/S2 同 batch）。

### G22/G21 Justification: handle_sql_tool_errors middleware converts tool ValueError into ToolMessage

> **Status (post-M6 truth-up 2026-06-10): automated** — pytest-bdd binding green in CI (tests/bdd blocking); justification below retained as historical record + G21 fallback source.

- **REQ**: REQ-006 / **Risk**: high / **Adapter**: langchain-agent / **ADR-029**
- **原因**: Unit 层已自动化 5 cases；BDD scenario + integration + smoke 层
  推迟 M3（per trace.yml L147-154 TBD-M3 markers）。
- **替代验证手段**: `tests/unit/test_tool_error_middleware.py` 已覆盖中间件
  转换语义（per ADR-029）— `TestValueErrorConversion` (precheck rejection
  → ToolMessage + guardrail rejection 保留 message) +
  `TestRuntimeErrorConversion` (timeout passthrough + generic DB error) +
  `TestUnexpectedExceptionFallback` (其他 exceptions 转 ToolMessage) = 5
  cases 覆盖核心转换路径。
- **升级触发条件**: M3 integration tests 实装
  (`test_middleware_wrap_integration.py` 验 sync + async wrap_tool_call) +
  smoke test 实装（`test_chainlit_astream_middleware.py` 验 astream 路径）。
- **预计时间**: M3 EOL（per TBD-M3 markers；与 S1/S2 同 batch）。

---

> Phase M1 baseline. Phase M2 will refine §3 troubleshooting with M3 contract test
> findings; M6 X4 dissolved docs/runbook/dev_studio_walkthrough.md into docs/guide/[GUIDE]_Developer_Onboarding.md §7 (owner-approved target; not this file).
