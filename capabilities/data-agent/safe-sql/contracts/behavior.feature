# capabilities/data-agent/safe-sql/contracts/behavior.feature
#
# Gherkin BDD scenarios for safe-sql capability (Phase M1 baseline).
# 5 @risk:critical (REQ-001 ×2 + REQ-002..004) + 2 @risk:high (REQ-005 / REQ-006) = 7 scenarios.
# critical_count = 5 (R-G17 ceiling reached; ≤ 5 still satisfied — last critical slot).
# step definitions: Phase M3 will land in tests/bdd/data_agent/safe_sql/steps/.

@adapter:python @adapter:langchain-agent
Feature: Safe SQL 4-Layer Guardrails
  As an analyst using mj-agent
  I want destructive / write SQL operations and semantic anti-patterns to be
  blocked at the agent layer
  So that the upstream business warehouse stays read-only from mj-agent and
  resource-bounded under LLM-generated SQL

  Background:
    Given the analyst has read-only PostgreSQL grants on biz_dws.* + biz_dwd.{dwd_dim_product_interface, dwd_dim_institution}
    And mj-agent is configured with biz_allowed_schemas = ["biz_dws", "biz_dwd"]
    And mj-agent is configured with biz_allowed_dwd_tables = ["dwd_dim_product_interface", "dwd_dim_institution"]
    And qcm_catalog.yaml periods.*.time_column includes "data_date" and "month"
    # ↑ pinned time columns per HITL Q5: pin in feature Background to avoid catalog drift breaking scenarios

  # ---------- REQ-001 — L1 hybrid guardrail: blocked-keyword path (critical) ----------

  @REQ-001 @CTR-sql-guardrail @risk:critical @adapter:python
  Scenario: L1 regex guardrail rejects blocked-keyword statement before DB contact
    Given the user-generated SQL is "DROP TABLE biz_dws.dws_qcm_qrynum_daily_total"
    When the agent invokes execute_sql with that statement
    Then execute_sql raises ValueError whose message starts with "SQL rejected by guardrail:"
    And the message contains the blocked keyword name "DROP"
    And the database is not contacted (readonly_cursor never opens)

  # ---------- REQ-001 — L1 hybrid guardrail: AST allowlist path (critical) ----------

  @REQ-001 @CTR-sql-guardrail @risk:critical @adapter:python
  Scenario: L1 guardrail rejects an out-of-allowlist schema reference regardless of identifier quoting before DB contact
    Given the user-generated SQL references an out-of-allowlist schema with quoted identifiers
    When the agent invokes execute_sql with that statement
    Then execute_sql raises ValueError whose message starts with "SQL rejected by guardrail:"
    And the message contains "biz_ods"
    And the database is not contacted (readonly_cursor never opens)

  # ---------- REQ-002 — L1b sqlglot AST precheck (critical) ----------

  @REQ-002 @CTR-sql-guardrail @risk:critical @adapter:python
  Scenario: L1b precheck rejects biz_dws fact-table query missing time-column predicate
    Given the user-generated SQL is "SELECT day_qrynum FROM biz_dws.dws_qcm_qrynum_daily_total LIMIT 10"
    And the SQL passes the L1 hybrid guardrail (SELECT-only, allowlisted schema)
    When precheck_sql parses the SQL via sqlglot
    Then PrecheckResult.errors contains a string starting with "require_time_range:"
    And execute_sql raises ValueError whose message starts with "SQL rejected by precheck:"
    And the message contains "require_time_range"

  # ---------- REQ-003 — L3 read-only connection (critical) ----------

  @REQ-003 @CTR-execute-sql @risk:critical @adapter:python
  Scenario: L3 connection enforces read-only transaction + bounded timeouts via DSN options
    Given the analyst credentials are configured (POSTGRES_ANALYST_USER set)
    When readonly_cursor() opens a new psycopg session
    Then the session's DSN options string contains "-c default_transaction_read_only=on"
    And the DSN options contains "-c lock_timeout=5000"
    And the DSN options contains "-c idle_in_transaction_session_timeout=10000"
    And on context exit the cursor's connection rolls back any open transaction
    And the pool is configured with min_size=1, max_size=4, autocommit=False, row_factory=dict_row

  # ---------- REQ-004 — L4 statement_timeout + GRANT reference (critical) ----------

  @REQ-004 @CTR-execute-sql @risk:critical @adapter:python @reference-contract
  Scenario: L4 statement_timeout cancellation translates to Chinese self-correction hint
    Given the upstream analyst role has statement_timeout='60s' set via R__analyst_permissions.sql
    And an in-flight SQL query exceeds 60s
    When the PostgreSQL backend raises psycopg.errors.QueryCanceled inside execute_sql
    Then execute_sql raises RuntimeError
    And the message contains "statement_timeout=60s"
    And the message includes a Chinese self-correction hint suggesting GROUP BY / narrower time range / fewer JOINs

  # ---------- REQ-005 — execute_sql envelope schema (high) ----------

  @REQ-005 @CTR-execute-sql @risk:high @adapter:python
  Scenario: execute_sql return envelope contains 8 required keys with documented types
    Given execute_sql is invoked with a valid SELECT statement that returns 5 rows
    When the call succeeds and the envelope is returned
    Then the envelope dict has exactly 8 keys
    And key "executed_sql" is a string equal to the input SQL verbatim
    And key "columns" is a list of strings
    And key "rows" is a list of dicts (each row mapping column-name to value)
    And key "row_count" is an integer equal to 5
    And key "truncated" is a boolean equal to False
    And key "statement_timeout_hit" is a boolean equal to False
    And key "business_summary" is a string (heuristic Chinese summary)
    And key "precheck_warnings" is a list of strings (empty if no precheck warnings fired)

  # ---------- REQ-006 — handle_sql_tool_errors middleware (high; ADR-029) ----------

  @REQ-006 @CTR-python @risk:high @adapter:langchain-agent @adr:ADR-029
  Scenario: handle_sql_tool_errors middleware converts tool ValueError into ToolMessage
    Given a ToolCallRequest whose handler raises ValueError("SQL rejected by guardrail: blocked keyword DROP") with tool_call_id="abc123"
    When handle_sql_tool_errors wraps the handler invocation
    Then the middleware returns a ToolMessage (does NOT re-raise)
    And the ToolMessage.content starts with "工具调用未通过校验"
    And the ToolMessage.content contains "SQL rejected by guardrail: blocked keyword DROP"
    And the ToolMessage.content ends with the retry hint "请根据错误信息调整 SQL 或工具参数后重试。"
    And the ToolMessage.tool_call_id equals "abc123"

# Gherkin tag convention (per sdd/adapters/bdd-tdd.md):
#   @REQ-NNN              — binds capability/requirements.md REQ id (required)
#   @CTR-<contract-slug>  — binds capability/contracts/<slug>.contract.yml (required)
#   @risk:<level>         — critical / high / medium / low (Feature or Scenario level)
#   @adapter:<name>       — binds sdd/adapters/ one or more (Feature or Scenario level)
#   @reference-contract   — marks a scenario whose actual SUT lives in a different repo
#   @adr:ADR-NNN          — links to a specific ADR for traceability
#
# Step definitions: Phase M3 will create tests/bdd/data_agent/safe_sql/steps/.
# Phase M1 only defines the .feature file; no automation yet (R-G18 mitigation).
