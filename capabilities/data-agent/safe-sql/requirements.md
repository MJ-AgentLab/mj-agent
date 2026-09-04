---
type: capability-requirements
capability: data-agent.safe-sql
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Requirements: Safe SQL 4-Layer Guardrails

> Phase M1 baseline. 6 REQs: REQ-001..004 (critical; 4-layer defense per ADR-006) +
> REQ-005 (high; execute_sql envelope) + REQ-006 (high; middleware per ADR-029).
> All critical / high REQs have `bdd.examples[]` per Agent_Side §7.1 A8.

## REQ-001 — L1 hybrid guardrail

**Priority**：critical

**Statement**：L1 hybrid guardrail (regex keyword scan + AST allowlist) enforces SELECT-only + schema/table allowlist + blocks 16 dangerous keywords + SET SESSION.

**Rationale**：Defense layer 1 of 4 (per ADR-006). Prevents SQL injection and write operations at the agent boundary before any DB contact.

**Acceptance**：

- `is_safe_select(sql, allowed_schemas, allowed_tables_per_schema)` returns `(False, reason)` for any SQL containing blocked keywords (INSERT / UPDATE / DELETE / DROP / TRUNCATE / ALTER / GRANT / REVOKE / CREATE / COPY / VACUUM / REINDEX / CLUSTER / ANALYZE / LOCK / CALL / SET SESSION) — 16 keywords + SET SESSION
- Multi-statement (internal `;`) rejected after trailing-semicolon strip
- Empty SQL rejected
- Non-SELECT / non-WITH...SELECT start rejected
- Schema not in `allowed_schemas` rejected (case-insensitive)
- Table not in per-schema allowlist (when map present) rejected

**BDD Examples**：

- **Given** user request triggers `DROP TABLE biz_dws.dws_qcm_qrynum_daily_total`
- **When** agent invokes `execute_sql` (which calls `is_safe_select`)
- **Then** `ValueError` raised with message starting `"SQL rejected by guardrail: blocked keyword"` and DB is never contacted

- **Given** SQL is `SELECT * FROM biz_dwd.dwd_dim_product_interface LIMIT 10`
- **When** `is_safe_select` evaluates with PER_SCHEMA `{"biz_dwd": ["dwd_dim_product_interface", "dwd_dim_institution"]}`
- **Then** returns `(True, "")` (accepted via per-schema allowlist)

**Trace**：`trace.yml` REQ-001 row → `contracts/sql-guardrail.contract.yml` + `contracts/behavior.feature` Scenario 1 + `tests/unit/test_guardrail.py`

**Related ADR**：[ADR-006 Fail-Safe Reads](decisions/ADR-006_Fail_Safe_Reads.md)

---

## REQ-002 — L1b sqlglot AST precheck

**Priority**：critical

**Statement**：L1b sqlglot AST precheck enforces 5 stable rule IDs.

**Rationale**：Defense sub-layer L1b — catches semantic anti-patterns (full-table scans / missing time predicates on biz_dws fact tables) before DB execution. Rule IDs are stable contract strings asserted in middleware tests.

**Acceptance**：

- 5 rule IDs (prefix-encoded; stable contract):
  - `no_select_star:` — error (P0); `exp.Star` not child of `exp.Count`
  - `require_time_range:` — error (P0); biz_dws fact table referenced AND no column from `qcm_catalog.yaml periods.*.time_column` appears
  - `require_limit:` — warning (P1); non-aggregate outer SELECT without LIMIT
  - `limit_too_large:` — warning (P1); LIMIT literal > 1000
  - `sqlglot_parse_failed:` — warning, `ok=True` graceful degrade (DB is ultimate validator)
- `PrecheckResult.errors` populated by P0 rules → `execute_sql` raises `ValueError("SQL rejected by precheck: ...")`
- `PrecheckResult.warnings` populated by P1 rules → surfaced via envelope `precheck_warnings`
- Signal tables (`dws_qcm_preprocessed_data` / `dws_qcm_etl_metrics` / `dws_qcm_ready_signal`) exempt from `require_time_range`
- `qcm_catalog.yaml periods.*.time_column` is the time-column SOR (cross-cap dep on `data-agent.biz-catalog`)

**BDD Examples**：

- **Given** SQL is `SELECT day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total LIMIT 10`
- **When** `precheck_sql` runs
- **Then** `PrecheckResult.errors` contains a `"require_time_range:"` entry; `execute_sql` raises `ValueError("SQL rejected by precheck: require_time_range: ...")`

- **Given** SQL is `SELECT * FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date = '2026-05-01'`
- **When** `precheck_sql` runs
- **Then** `errors` contains `"no_select_star: ..."` (rejects star projection)

**Trace**：REQ-002 → `contracts/sql-guardrail.contract.yml` + `behavior.feature` Scenario 2 + `tests/unit/test_precheck.py`

---

## REQ-003 — L3 read-only connection

**Priority**：critical

**Statement**：L3 read-only psycopg connection pinned via DSN options.

**Rationale**：Defense layer 3 — DB-side enforcement of read-only intent and bounded resource consumption; pool guarantees tx-rollback on cursor exit (no dangling tx).

**Acceptance**：

- DSN `options` payload contains all 3 PGOPTIONS flags:
  - `-c default_transaction_read_only=on`
  - `-c lock_timeout=5000` (5s, ms units)
  - `-c idle_in_transaction_session_timeout=10000` (10s, ms units)
- Pool: `min_size=1, max_size=4, autocommit=False, row_factory=dict_row`
- `readonly_cursor()` ctx manager ALWAYS `conn.rollback()` in finally
- Does NOT set `search_path` (schema qualification enforced at L1)
- Does NOT set `statement_timeout` client-side (delegated to L4 role-level config)
- `atexit` pool close registered at module init

**BDD Examples**：

- **Given** analyst credentials configured in env
- **When** `readonly_cursor()` opens a new session
- **Then** the `_dsn()` string contains all 3 `-c` flags with documented values, and the connection rolls back any open transaction upon context exit

**Trace**：REQ-003 → `contracts/execute-sql.contract.yml` + `behavior.feature` Scenario 3 + **TBD-M3** unit test (`test_dsn_options.py` or similar — Phase M3 will assert DSN string content without live DB)

---

## REQ-004 — L4 statement_timeout + GRANT reference contract

**Priority**：critical (reference contract)

**Statement**：L4 statement_timeout 60s cancellation catch + upstream GRANT (cross-repo reference contract).

**Rationale**：Defense layer 4 — runaway query cancellation + GRANT-level read-only enforcement at DB role. The GRANT SQL is OWNED UPSTREAM in mj-system repo. mj-agent SUT side implements only timeout-catch + introspection sanity check.

**Acceptance**：

- **SUT-side (testable here)**：
  - `execute_sql` catches `psycopg.errors.QueryCanceled` and raises `RuntimeError` whose message contains `"statement_timeout=60s"` plus a Chinese self-correction hint (GROUP BY / narrower time range / fewer JOINs)
  - `introspect.list_biz_tables()` filters by `information_schema.table_privileges` on `CURRENT_USER` SELECT — sanity-checks the upstream GRANT visibility
- **Upstream (reference contract)**：
  - `ALTER ROLE analyst SET statement_timeout='60s'` in `mj-system:sql/migrations/repeatable/R__analyst_permissions.sql`
  - Table-level SELECT GRANTs to `analyst` role on `biz_dws.*` + `biz_dwd.{dwd_dim_product_interface, dwd_dim_institution}`
- Contract verification gates on `live_db` fixture (skip-clean when `POSTGRES_ANALYST_USER` unset)

**BDD Examples**：

- **Given** upstream `analyst` role has `statement_timeout='60s'` (via `R__analyst_permissions.sql` reference contract) and an in-flight query exceeds 60s
- **When** the DB raises `psycopg.errors.QueryCanceled` inside `execute_sql`
- **Then** `execute_sql` raises `RuntimeError` whose message contains `"statement_timeout=60s"` and the Chinese self-correction hint

**Trace**：REQ-004 → `contracts/execute-sql.contract.yml` (sut-side) + `behavior.feature` Scenario 4 + **TBD-M3** (a) unit test monkeypatching `readonly_cursor` to raise `QueryCanceled`; (b) contract test asserting `list_biz_tables()` GRANT visibility (gated on live_db)

---

## REQ-005 — execute_sql return envelope schema

**Priority**：high

**Statement**：execute_sql return envelope contains 8 required keys with documented types.

**Rationale**：Agent-facing data contract. Every key consumed by system prompt + LLM. Key absence or type drift breaks LLM behavior reliability — system prompt instructs LLM to read `business_summary` / `precheck_warnings` / `truncated` for self-correction.

**Acceptance**：

- Envelope contains exactly these 8 keys with these types:
  - `executed_sql: str` — verbatim echo of input SQL
  - `columns: list[str]` — column names from `cursor.description`
  - `rows: list[dict[str, Any]]` — `dict_row` mapping rows (≤ `sql_max_rows`)
  - `row_count: int` — `len(rows)` after truncation slice
  - `truncated: bool` — `True` if pre-slice row count exceeded `sql_max_rows`
  - `statement_timeout_hit: bool` — always `False` on success path; reserved for callers that catch
  - `business_summary: str` — heuristic Chinese summary (empty / truncated / timeout fallbacks)
  - `precheck_warnings: list[str]` — copy of `PrecheckResult.warnings`
- Key set is closed (no extra keys) — adding a 9th key requires `evolve-capability.md` workflow

**BDD Examples**：

- **Given** `execute_sql` succeeds with a 5-row result
- **When** the envelope is returned to the caller (LLM via tool message)
- **Then** all 8 keys are present with correct types; `truncated=False`, `statement_timeout_hit=False`, `precheck_warnings=[]` if no precheck warnings fired

**Trace**：REQ-005 → `contracts/execute-sql.contract.yml` (envelope schema section) + `behavior.feature` Scenario 5 + **TBD-M3** unit test (envelope key set + type assertions; can be done without live DB by stubbing `readonly_cursor`)

---

## REQ-006 — handle_sql_tool_errors middleware (ADR-029)

**Priority**：high

**Statement**：handle_sql_tool_errors middleware converts ValueError/RuntimeError from SQL tools to ToolMessage (sync + async).

**Rationale**：Per ADR-029. Graph step succeeds even when tool raises. LLM sees error as tool output and self-corrects rather than the graph crashing. Async variant required because Chainlit drives `graph.astream`.

**Acceptance**：

- `SQLToolErrorMiddleware(AgentMiddleware)` — ONE middleware overriding BOTH
  `wrap_tool_call` (sync) and `awrap_tool_call` (async); `handle_sql_tool_errors`
  is its module-level singleton. Must never be split back into two one-sided
  `@wrap_tool_call` functions: langchain's factory routes an either-hook
  middleware into both chains, so the missing side raises `NotImplementedError`
  (issue #288 — froze Chainlit on every tool call)
- Both hooks catch `(ValueError, RuntimeError)` from inner tool call
- Both hooks return `ToolMessage(content=<formatted>, tool_call_id=request.tool_call["id"])`
- Content prefixes (stable contract strings):
  - `ValueError` → `"工具调用未通过校验 ..."` + `_RETRY_HINT`
  - `RuntimeError` → `"工具执行失败 ..."` + `_RETRY_HINT`
  - Other exception types → `"工具执行失败（意外异常 <Type>）：..."` + `_RETRY_HINT`
- Direct callers (unit / smoke tests, internal code) still see raw exception — middleware only intercepts agent's tool-call path
- Wired in `agent.py:make_graph()` as `middleware=[handle_sql_tool_errors]` — the single
  instance serves both chains; async path pinned by `tests/unit/test_agent_async_tool_path.py` (#288)

**BDD Examples**：

- **Given** L1 guardrail raises `ValueError("SQL rejected by guardrail: blocked keyword")`
- **When** the SQL tool call is wrapped by `handle_sql_tool_errors` middleware
- **Then** middleware returns `ToolMessage` with content prefixed by `"工具调用未通过校验"`, suffixed with `_RETRY_HINT`, and `tool_call_id` preserved from the request

**Trace**：REQ-006 → `contracts/python.contract.yml` (middleware module + signatures section) + `behavior.feature` Scenario 6 + `tests/unit/test_tool_error_middleware.py`

---

> Phase M1 baseline — all 6 REQs sourced from `_refactor-scan/m1-safe-sql-survey.md`.
> TBD Phase M3: contract tests for REQ-003 / REQ-004 / REQ-005 (TBD-M3 markers per
> REQ Acceptance sections above).
