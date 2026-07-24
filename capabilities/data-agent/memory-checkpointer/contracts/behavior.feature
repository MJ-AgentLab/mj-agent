# capabilities/data-agent/memory-checkpointer/contracts/behavior.feature
#
# Gherkin BDD scenarios for the memory checkpointer capability — mechanism B (at-rest redaction,
# REQ-001..004) + mechanism C (opt-in TTL eviction, REQ-005; #386).
# 6 @risk:medium scenarios — all medium because the residual being hardened is an Owner-accepted,
# reversible copy of already-guardrail-approved biz rows (not a new exposure), and TTL eviction is
# opt-in + dry-run-guarded; see spec.yml rationale. Medium keeps G21/G22 in skip (they filter
# @risk:critical|high); G19 still requires @REQ + @CTR tags on every scenario.
#
# REQ-001/002/003 are automated offline (pure transform; no container) in
# tests/bdd/data_agent/memory_checkpointer/test_memory_checkpointer_bdd.py.
# REQ-004 (both on-disk write paths) + REQ-005 (TTL eviction) are unautomated here — they need the
# mj-agent-postgres container, so they are covered by the -m smoke tests
# (test_memory_redaction_canary.py + test_memory_retention_smoke.py); REQ-005's offline age / dry-run
# logic is additionally unit-tested (test_memory_retention.py). Medium ⇒ no runbook justification required.

@adapter:python @risk:medium
Feature: Memory Checkpoint At-Rest Desensitization
  As the operator of mj-agent
  I want execute_sql biz rows replaced by a deterministic per-column digest when a
  checkpoint is persisted
  So that the memory database (a second at-rest copy, now Codex-readable post-ADR-037) holds
  column statistics + the SQL rather than verbatim customer / institution cell values, while
  the live conversation stays untouched

  Background:
    Given the RedactingAsyncPostgresSaver is installed as the memory checkpointer

  # ---------- REQ-001 — at-rest minimization (medium) ----------

  @REQ-001 @CTR-checkpoint-redaction @risk:medium @adapter:python
  Scenario: Persisting an execute_sql ToolMessage replaces biz rows with a per-column digest
    Given an execute_sql ToolMessage whose rows contain the verbatim value "CANARY-ACME-9973"
    When the redacting saver prepares the message for persistence
    Then the persisted content contains no verbatim value from the original rows
    And the persisted envelope carries rows_redacted true and a per-column row_digest

  # ---------- REQ-002 — persist-time only; live untouched (medium) ----------

  @REQ-002 @CTR-checkpoint-redaction @risk:medium @adapter:python
  Scenario: Redaction clones the message so the live in-process state is untouched
    Given an execute_sql ToolMessage whose rows contain the verbatim value "CANARY-ACME-9973"
    When the redacting saver prepares the message for persistence
    Then the redacted message is a different object from the live message
    And the live message still contains the verbatim value "CANARY-ACME-9973"

  # ---------- REQ-003 — recoverable-by-refetch (medium) ----------

  @REQ-003 @CTR-checkpoint-redaction @risk:medium @adapter:python
  Scenario: The digested envelope retains executed_sql for recoverable-by-refetch
    Given an execute_sql ToolMessage whose rows contain the verbatim value "CANARY-ACME-9973"
    When the redacting saver prepares the message for persistence
    Then the persisted envelope retains executed_sql verbatim

  # ---------- REQ-004 — both write paths covered (medium; container canary) ----------

  @REQ-004 @CTR-checkpoint-redaction @risk:medium @adapter:python
  Scenario: Both on-disk write paths carry no verbatim biz cell value
    Given the redacting saver is installed against the memory database
    When a checkpoint is written via aput and pending writes are flushed via aput_writes
    Then neither checkpoint_blobs nor checkpoint_writes contains a verbatim biz cell value

  # ---------- REQ-005 — opt-in TTL eviction (mechanism C; medium; container-gated) ----------

  @REQ-005 @CTR-checkpoint-retention @risk:medium @adapter:python
  Scenario: Evicting stale threads removes only threads older than the TTL
    Given a thread whose newest checkpoint is older than the TTL
    And a thread whose newest checkpoint is newer than the TTL
    When mj-agent memory-evict runs with that TTL
    Then the older thread is removed from checkpoints, checkpoint_blobs and checkpoint_writes
    And the newer thread remains

  @REQ-005 @CTR-checkpoint-retention @risk:medium @adapter:python
  Scenario: A dry run reports stale threads without deleting
    Given a thread whose newest checkpoint is older than the TTL
    When mj-agent memory-evict runs with the dry-run flag
    Then the stale thread is reported
    And nothing is deleted from the checkpoint tables

# Gherkin tag convention (per sdd/adapters/bdd-tdd.md):
#   @REQ-NNN              — binds capability/requirements.md REQ id (required; G19)
#   @CTR-<contract-slug>  — binds capability/contracts/<slug>.contract.yml (required; G19)
#   @risk:<level>         — critical / high / medium / low (Feature or Scenario level)
#   @adapter:<name>       — binds sdd/adapters/ one or more (Feature or Scenario level)
#
# Automation: REQ-001/002/003 bound via pytest-bdd (offline pure transform); REQ-004 + REQ-005 are
# @scenario-unbound (container tests in tests/smoke/) — see trace.yml automation_status.
