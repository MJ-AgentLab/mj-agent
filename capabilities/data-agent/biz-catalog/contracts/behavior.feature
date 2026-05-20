# capabilities/data-agent/biz-catalog/contracts/behavior.feature
#
# Gherkin BDD scenarios for biz-catalog capability (Phase M1 baseline).
# 3 @risk:high scenarios (REQ-001 / REQ-002 / REQ-003).
# critical_count: 0 (no critical REQs in biz-catalog).

@adapter:python @adapter:runtime-skill
Feature: QCM Catalog Mirror — schema completeness + live DB alignment + SKILL coherence
  As an mj-agent maintainer
  I want the QCM catalog to (a) declare a stable 10-key schema, (b) match the
  live biz DB structure, (c) stay coherent with active in-source SKILLs
  So that generated SQL targets real tables and the LLM doesn't hallucinate
  non-existent metric / period / dimension combinations

  Background:
    Given mj-agent is configured with biz_allowed_schemas = ["biz_dws", "biz_dwd"]
    And the analyst role has read-only GRANTs per mj-system R__analyst_permissions.sql
    And qcm_catalog.yaml is bundled at src/mj_agent/biz_catalog/qcm_catalog.yaml

  # ---------- REQ-001 — Schema completeness ----------

  @REQ-001 @CTR-catalog @risk:high @adapter:python
  Scenario: load_catalog rejects YAML whose root parses to a list (not a mapping)
    Given a malformed qcm_catalog.yaml whose top-level YAML parses to a list (e.g. starts with "- foo")
    When load_catalog() is invoked
    Then it raises ValueError
    And the message mentions the actual top-level type ("list" or similar)
    And find_biz_context() also fails (load_catalog raise propagates)

  # ---------- REQ-002 — Catalog ↔ DB alignment ----------

  @REQ-002 @CTR-catalog-db-alignment @risk:high @adapter:python @gated:live_db
  Scenario: Catalog signal_tables must resolve in live biz_dws
    Given a freshly loaded catalog with 3 signal_tables entries (dws_qcm_preprocessed_data / dws_qcm_etl_metrics / dws_qcm_ready_signal)
    And the analyst role can SELECT from information_schema.tables
    When the contract test queries information_schema for table_schema='biz_dws' AND table_name IN signal_tables
    Then all 3 names appear in the result set
    And drift (missing table or renamed table) surfaces a clear error naming the missing entry

  # ---------- REQ-003 — SKILL ↔ catalog coherence ----------

  @REQ-003 @CTR-catalog-db-alignment @risk:high @adapter:runtime-skill @gated:live_db
  Scenario: Active SKILL bodies reference only resolvable catalog symbols and DB tables
    Given the 3 active in-source SKILLs (biz-domain-context / qcm-analysis / safe-sql-analysis)
    And each SKILL body is loaded via load_skill() (strip frontmatter per A11 contract)
    When the contract test regex-extracts "biz_dws.*" / "biz_dwd.*" table refs from each SKILL body
    And queries information_schema.tables for each extracted ref
    Then every extracted table ref resolves in live DB (visible to analyst role)
    And every metric / period / dimension keyword referenced in SKILL body exists in catalog.metrics / catalog.periods / catalog.dimensions

# Gherkin tag convention:
#   @REQ-NNN              — binds requirements.md REQ id
#   @CTR-<contract-slug>  — binds contracts/<slug>.contract.yml
#   @risk:high            — Phase M3/M4 BDD gates fire for high+
#   @adapter:<name>       — binds sdd/adapters/ (python + runtime-skill here)
#   @gated:live_db        — scenario requires POSTGRES_ANALYST_USER live DB fixture; skip-clean otherwise
#
# Step definitions: Phase M3 lands in tests/bdd/data_agent/biz_catalog/steps/.
# Existing automation: tests/contract/test_qcm_catalog_alignment.py + test_biz_schema_alignment.py
# cover REQ-002 + REQ-003 via direct contract tests (gated on live_db).
