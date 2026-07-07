---
type: capability-tasks
capability: data-agent.safe-sql
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Tasks: Safe SQL 4-Layer Guardrails

> Phase M1 baseline. critical / high REQ tasks include `tdd.test_list[]` per R-G19
> mitigation: existing test refs OR TBD-M3 markers (no red-green-refactor evidence
> required at M1; M4+ for blocking).

## Backlog

### T-001 — Phase M1 capability artifact suite

- **Phase**：M1
- **Priority**：critical (capability foundation)
- **Linked REQ**：N/A (meta-task)
- **HITL trigger**：M1 baseline checkpoint (HITL Gate-1; safe-sql is pilot 1)
- **Status**：in-progress (this PR)
- **Acceptance**：
  - 9-artifact suite created (spec / requirements / design / 4 contracts / tasks / runbook / trace / evidence skeleton)
  - All YAML files valid via `python -c "import yaml; yaml.safe_load(...)"`
  - 6 REQs in requirements.md with bdd.examples[]
  - 6 scenarios in behavior.feature (4 critical + 2 high)
  - design.md ≤ 200 lines
  - contracts ≤ 5 files
  - cross_capability_refs ≤ 5

### T-002 — REQ-001 L1 regex guardrail (contract reverse-engineering)

- **Phase**：M1
- **Priority**：critical
- **Linked REQ**：REQ-001
- **Contract changed?**：no (frozen anchor; existing impl)
- **HITL trigger**：sql-guardrail-relax (any modification to `guardrail.py` → HITL)
- **Status**：done (M1; contract describes existing behavior)
- **TDD test_list**：
  - `tests/unit/test_guardrail.py::TestAccepted::test_simple_select` (status: existing; verifies SELECT pass)
  - `tests/unit/test_guardrail.py::TestAccepted::test_with_clause` (existing; WITH...SELECT pass)
  - `tests/unit/test_guardrail.py::TestAccepted::test_join_across_allowed_schemas` (existing)
  - `tests/unit/test_guardrail.py::TestAccepted::test_trailing_semicolon_allowed` (existing)
  - `tests/unit/test_guardrail.py::TestRejected::test_blocked_keywords` (existing; parametrized × 9 keywords)
  - `tests/unit/test_guardrail.py::TestRejected::test_multi_statement` (existing)
  - `tests/unit/test_guardrail.py::TestRejected::test_non_select` (existing; EXPLAIN rejected)
  - `tests/unit/test_guardrail.py::TestRejected::test_disallowed_schema` (existing; biz_ods rejected)
  - `tests/unit/test_guardrail.py::TestRejected::test_empty_sql` (existing)
  - `tests/unit/test_guardrail.py::TestTableLevelAllowlist::*` (existing; 6 cases on per-schema allowlist)

### T-003 — REQ-002 L1b sqlglot AST precheck (contract reverse-engineering)

- **Phase**：M1
- **Priority**：critical
- **Linked REQ**：REQ-002
- **Contract changed?**：no (frozen anchor)
- **HITL trigger**：sql-guardrail-relax (any modification to `precheck.py` → HITL)
- **Status**：done (M1)
- **TDD test_list**：
  - `tests/unit/test_precheck.py::TestNoSelectStar::*` (existing; rejected / COUNT(*) exempt / explicit columns pass)
  - `tests/unit/test_precheck.py::TestRequireTimeRange::*` (existing; fact w/o time reject / data_date pass / month pass / signal exempt / dimension exempt)
  - `tests/unit/test_precheck.py::TestRequireLimit::*` (existing; detail w/o LIMIT warn / aggregate clean / limit_too_large warn)
  - `tests/unit/test_precheck.py::TestParseFailureGracefulFallback::*` (existing; unparseable → ok=True)

### T-004 — REQ-003 L3 read-only connection (contract reverse-engineering)

- **Phase**：M1
- **Priority**：critical
- **Linked REQ**：REQ-003
- **Contract changed?**：no (frozen anchor)
- **HITL trigger**：none for documentation; modification to `mj_system_db.py` would require HITL (data-LLM boundary 通道隔离 per `policies/data-boundary.md`)
- **Status**：done (M1 contract); TBD-M3 (unit test for DSN string)
- **TDD test_list**：
  - **TBD-M3** `tests/unit/test_dsn_options.py::test_dsn_contains_default_transaction_read_only` — assert DSN string contains `-c default_transaction_read_only=on` (no live DB; parse return of `_dsn()`)
  - **TBD-M3** `tests/unit/test_dsn_options.py::test_dsn_contains_lock_timeout` — assert `-c lock_timeout=5000`
  - **TBD-M3** `tests/unit/test_dsn_options.py::test_dsn_contains_idle_in_transaction_session_timeout` — assert `-c idle_in_transaction_session_timeout=10000`
  - **TBD-M3** `tests/unit/test_readonly_cursor.py::test_rollback_on_exit` — monkeypatch cursor / connection, assert `conn.rollback()` called in finally

### T-005 — REQ-004 L4 statement_timeout catch + GRANT reference

- **Phase**：M1 (sut-side contract); M3 (test); M4+ (live_db verification)
- **Priority**：critical (reference contract)
- **Linked REQ**：REQ-004
- **Contract changed?**：no
- **HITL trigger**：if upstream `R__analyst_permissions.sql` changes → cross-capability + cross-repo HITL
- **Status**：done (M1 sut-side); TBD-M3 (timeout catch test); TBD-M4 (live_db GRANT verification)
- **TDD test_list**：
  - **TBD-M3** `tests/unit/test_execute_sql_timeout.py::test_query_canceled_becomes_runtime_error` — monkeypatch `readonly_cursor` to raise `psycopg.errors.QueryCanceled` on `cur.execute()`; assert `execute_sql` raises `RuntimeError` containing `statement_timeout=60s` and Chinese hint
  - **TBD-M4** `tests/contract/test_safe_sql_grant_visibility.py::test_list_biz_tables_matches_documented_schemas` — gated on `live_db` fixture; assert `list_biz_tables()` returns exactly {all biz_dws.* tables + 2 biz_dwd dim tables}

### T-006 — REQ-005 execute_sql envelope schema

- **Phase**：M1 (contract); M3 (test)
- **Priority**：high
- **Linked REQ**：REQ-005
- **Contract changed?**：no
- **HITL trigger**：adding 9th envelope key → cross-capability (LLM behavior change per `policies/ai-agent.md` §HITL #7)
- **Status**：done (M1 contract); TBD-M3 (envelope key set + types)
- **TDD test_list**：
  - **TBD-M3** `tests/unit/test_execute_sql_envelope.py::test_envelope_has_8_required_keys` — stub `readonly_cursor` to return 5 rows; assert envelope `.keys()` == expected set
  - **TBD-M3** `tests/unit/test_execute_sql_envelope.py::test_envelope_types` — assert each key's type
  - **TBD-M3** `tests/unit/test_execute_sql_envelope.py::test_envelope_truncated_when_rows_exceed_max` — feed `sql_max_rows + 1` rows; assert `truncated=True` and slice applied

### T-007 — REQ-006 handle_sql_tool_errors middleware

- **Phase**：M1
- **Priority**：high
- **Linked REQ**：REQ-006
- **Contract changed?**：no (frozen anchor; ADR-029)
- **HITL trigger**：modification to `tool_errors.py` requires HITL (changes agent error surface; affects all SQL tools)
- **Status**：done (M1 contract + #288 wrap/graph 集成回归，2026-07-07)。原 TBD-M3 三项由
  issue #288 修复落地（sync-only middleware 使 Chainlit/Studio async 链每次工具调用炸
  `NotImplementedError`）；smoke 占位改为 unit 级 fake-model graph 测试（无需 creds，CI 默认跑）
- **TDD test_list**：
  - `tests/unit/test_tool_error_middleware.py::TestValueErrorConversion::test_precheck_rejection_becomes_tool_message` (existing)
  - `tests/unit/test_tool_error_middleware.py::TestValueErrorConversion::test_guardrail_rejection_preserves_message` (existing)
  - `tests/unit/test_tool_error_middleware.py::TestRuntimeErrorConversion::test_timeout_message_passed_through` (existing)
  - `tests/unit/test_tool_error_middleware.py::TestRuntimeErrorConversion::test_generic_db_error` (existing)
  - `tests/unit/test_tool_error_middleware.py::TestUnexpectedExceptionFallback::test_other_exceptions_become_messages` (existing; parametrized: TypeError, KeyError)
  - `tests/unit/test_tool_error_middleware.py::TestSyncWrapToolCall::{test_value_error_converted,test_runtime_error_converted,test_success_passthrough}` (#288 — wrap 层 sync 集成)
  - `tests/unit/test_tool_error_middleware.py::TestAsyncAwrapToolCall::{test_value_error_converted,test_runtime_error_converted,test_success_passthrough}` (#288 — wrap 层 async 集成；全仓首批 async 测试)
  - `tests/unit/test_tool_error_middleware.py::TestBothHooksOverridden::{test_sync_hook_overridden,test_async_hook_overridden}` (#288 — 注册实例双 hook pin)
  - `tests/unit/test_agent_async_tool_path.py::{test_ainvoke_tool_error_converted_not_raised,test_invoke_tool_error_converted_not_raised}` (#288 — graph 级 fake-model E2E，复现事故路径)

## In-Progress

(none beyond T-001)

## Done

(populated as M1 PR progresses)

## Anti-Backlog (decided NOT to do)

- **Phase M1 contract tests** — explicitly deferred to Phase M3 per [PLAN]_spec_anchored_refactor.md §2 and R-G19 mitigation; M1 only describes contracts.
- **Modify `guardrail.py` / `precheck.py` to fix doc-stated non-goals** (comment scan / string literal scan) — out of scope; would touch sql-guardrail-relax 4 项必停 and requires separate HITL + ADR.
- **REQ-002 severity split into REQ-002a (errors) + REQ-002b (warnings)** — rejected at HITL Q3; severity differentiation lives in contract not REQ.

---

> Phase M1 baseline. Total: 7 tasks (T-001 meta + T-002..T-007 per REQ).
> tdd.test_list[] coverage: REQ-001 + REQ-002 + REQ-006 use existing tests; REQ-003 + REQ-004 + REQ-005 have TBD-M3 markers.
