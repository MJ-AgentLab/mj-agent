---
type: capability-tasks
capability: data-agent.memory-checkpointer
state: active
version: 1.0
owner: ranzuozhou
created: 2026-07-20
updated: 2026-07-22
---

# Tasks: Memory Checkpoint At-Rest Desensitization

> Build plan for the implementation slice (#365 AC3-6). **Complete** — the capability is now at
> `lifecycle_state: active`. T-001..T-003 landed in the #365 build-core PR (#368); T-004 (both-paths
> canary + smoke round-trip) and T-005 (behavior.feature + trace.yml + evidence + active-flip)
> landed in the #365 AC4-6 activation slice.

## Backlog

### T-001 — langgraph pinned-wheel verification (pre-code)

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-004
- **Contract changed?**：no
- **HITL trigger**：N
- **Status**：done
- Verify against the installed langgraph wheel: the `aput` / `aput_writes` write paths, the
  `_dump_blobs` / `_dump_writes` → serde contract, and that the default `JsonPlusSerializer`
  msgpack-encodes the `messages` channel. Confirm the two override points before writing code.

### T-002 — memory/digest.py pure aggregation + unit tests

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-001
- **Contract changed?**：no
- **HITL trigger**：N
- **Status**：done
- Pure deterministic per-column aggregation (`{non_null, distinct}`); no LLM call; handle
  Decimal/datetime/date cell types deterministically.
- **TDD test_list**：
  - `tests/unit/test_memory_digest.py::test_digest_per_column_aggregates`
  - `tests/unit/test_memory_digest.py::test_digest_is_deterministic`
  - `tests/unit/test_memory_digest.py::test_digest_carries_no_verbatim_cell_value`

### T-003 — RedactingAsyncPostgresSaver (override aput + aput_writes)

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-001, REQ-002, REQ-004
- **Contract changed?**：yes (checkpoint-redaction.contract.yml INV-1..INV-4 become live)
- **HITL trigger**：N (memory/ non-必停; commit/PR gates per ADR-034 still apply)
- **Status**：done
- Subclass `AsyncPostgresSaver`; override BOTH `aput` and `aput_writes`; select `execute_sql`
  ToolMessages by `name` + envelope-shape guard; emit `model_copy` clones (never mutate live);
  swap constructor at `checkpointer.py:88` behind a feature flag.
- **TDD test_list**：
  - `tests/unit/test_memory_redaction.py::test_execute_sql_message_selected`
  - `tests/unit/test_memory_redaction.py::test_error_and_chart_envelopes_skipped`
  - `tests/unit/test_memory_redaction.py::test_live_message_unmutated_after_aput`

### T-004 — both-paths canary + smoke round-trip

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-004
- **Contract changed?**：no
- **HITL trigger**：N
- **Status**：done
- Canary asserting the persisted bytes carry no verbatim cell value on BOTH `aput` (checkpoint_blobs)
  AND `aput_writes` (checkpoint_writes) — the both-hooks-or-it-leaks guard (ADR-029 #288 class). Plus a
  smoke round-trip against the `mj-agent-postgres` container (conftest-skipped without creds).
- **TDD test_list**：
  - `tests/unit/test_memory_redaction_canary.py::test_aput_path_no_verbatim_value`
  - `tests/unit/test_memory_redaction_canary.py::test_aput_writes_path_no_verbatim_value`

### T-005 — activate: behavior.feature + trace.yml + evidence + flip to active

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-001..REQ-004
- **Contract changed?**：no
- **HITL trigger**：N
- **Status**：done
- Add `contracts/behavior.feature` (scenarios tagged @REQ + @CTR-checkpoint-redaction), `trace.yml`
  (schema v1.2, `automation_status: automated` once tests are green), write `evidence/` (G8 activates
  at `active`), then flip `spec.yml lifecycle_state: planned → implementing → verifying → active`.
- Decide BDD @risk levels here (medium keeps G21/G22 skip; high needs trace + runbook justification).

## In-Progress

- (none)

## Done

- Spec slice (#365 AC2): spec.yml + requirements.md + design.md + contracts/checkpoint-redaction.contract.yml
  + tasks.md authored at `lifecycle_state: planned` (PR #367).
- Build-core slice (#365 AC3): T-001 (langgraph 4.0.2 wheel verify) + T-002 (memory/digest.py + unit
  tests) + T-003 (RedactingAsyncPostgresSaver override aput + aput_writes; feature-flag) (PR #368).
- Activation slice (#365 AC4-6, this PR): T-004 (both-paths on-disk canary + smoke round-trip against
  mj-agent-postgres; negative control) + T-005 (contracts/behavior.feature 4 @risk:medium scenarios +
  trace.yml v1.2 + evidence/verification/ + runbook.md + lifecycle_state → active + default-on flip).

## Anti-Backlog (explicitly not doing here)

- Mechanism D (encrypt-at-rest) — rejected in ADR-038 (confidentiality not minimization; opaque to
  Codex; key mgmt).
- Mechanism C (TTL/retention) — separate optional capability/complement, not this one.
- Answer-side (AIMessage NL) redaction — egress/answer-side control, out of scope.
- One-time backfill of pre-deploy checkpoints — forward-only accepted unless separately funded.
