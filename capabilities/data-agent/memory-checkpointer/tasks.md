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

> Build plan. **Complete** — the capability is at `lifecycle_state: active`. Mechanism B
> (#365 AC3-6): T-001..T-003 landed in the build-core PR (#368); T-004 (both-paths canary + smoke
> round-trip) + T-005 (behavior.feature + trace.yml + evidence + active-flip) in the AC4-6 slice.
> Mechanism C (#386): T-006 (retention.py + config + `mj-agent memory-evict` CLI + unit tests) +
> T-007 (REQ-005 + retention contract + behavior.feature + trace + design §6 + runbook §6 + evidence
> + ADR-038 addendum + real-DB smoke).

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

### T-006 — memory/retention.py + config + CLI (mechanism C code; #386)

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-005
- **Contract changed?**：yes (checkpoint-retention.contract.yml INV-R1..INV-R4 become live)
- **HITL trigger**：N (memory/ non-必停; opt-in + dry-run guard the destructive DELETE; commit/PR gates per ADR-034 still apply)
- **Status**：done
- Pure uuid6->epoch extraction (verified vs langgraph 1.1.8 UUID.time) + stale-thread selection
  (MAX(checkpoint_id) per thread, strict age boundary) + `evict_stale_threads` via `adelete_thread`
  (all 3 tables). `MJ_AGENT_MEMORY_TTL_DAYS` config (default 0 = disabled) + `.env.example` (commented
  so no `check` drift). `mj-agent memory-evict [--older-than] [--dry-run]` CLI: opt-in gate + SKIP on
  absent creds, both exit 0.
- **TDD test_list**：
  - `tests/unit/test_memory_retention.py::test_epoch_matches_langgraph_uuid6_time`
  - `tests/unit/test_memory_retention.py::test_evict_deletes_only_stale_threads`
  - `tests/unit/test_memory_retention.py::test_dry_run_deletes_nothing`
  - `tests/unit/test_memory_retention.py::test_stale_boundary_is_strict`

### T-007 — capability evolution + real-DB smoke (mechanism C docs; #386)

- **Phase**：build / **Priority**：medium / **Linked REQ**：REQ-005
- **Contract changed?**：yes (new contracts/checkpoint-retention.contract.yml)
- **HITL trigger**：N
- **Status**：done
- REQ-005 in spec.yml + requirements.md; design.md §6 (Owner rulings + engineering calls); new
  retention contract; behavior.feature REQ-005 scenarios (@risk:medium, container-gated → unautomated);
  trace.yml REQ-005 link; runbook §6 (memory-evict usage + external-cron wiring + troubleshooting);
  evidence/verification/2026-07-23_ttl_eviction.md; ADR-038 §Relationship addendum.
- **TDD test_list**（smoke, container-gated; skip-clean without creds）：
  - `tests/smoke/test_memory_retention_smoke.py::test_evict_removes_only_stale_threads`
  - `tests/smoke/test_memory_retention_smoke.py::test_dry_run_reports_but_deletes_nothing`

## In-Progress

- (none)

## Done

- Spec slice (#365 AC2): spec.yml + requirements.md + design.md + contracts/checkpoint-redaction.contract.yml
  + tasks.md authored at `lifecycle_state: planned` (PR #367).
- Build-core slice (#365 AC3): T-001 (langgraph 4.0.2 wheel verify) + T-002 (memory/digest.py + unit
  tests) + T-003 (RedactingAsyncPostgresSaver override aput + aput_writes; feature-flag) (PR #368).
- Activation slice (#365 AC4-6): T-004 (both-paths on-disk canary + smoke round-trip against
  mj-agent-postgres; negative control) + T-005 (contracts/behavior.feature 4 @risk:medium scenarios +
  trace.yml v1.2 + evidence/verification/ + runbook.md + lifecycle_state → active + default-on flip).
- Mechanism C slice (#386): T-006 (memory/retention.py + MJ_AGENT_MEMORY_TTL_DAYS config + `mj-agent
  memory-evict` CLI + unit tests) + T-007 (REQ-005 + checkpoint-retention.contract.yml + behavior.feature
  scenarios + trace.yml + design.md §6 + runbook §6 + evidence + ADR-038 addendum + real-DB smoke).

## Anti-Backlog (explicitly not doing here)

- Mechanism D (encrypt-at-rest) — rejected in ADR-038 (confidentiality not minimization; opaque to
  Codex; key mgmt).
- Answer-side (AIMessage NL) *content* redaction — egress/answer-side control, out of scope (mechanism
  C bounds its at-rest lifetime via TTL, but does not redact the content).
- One-time backfill of pre-deploy / pre-B checkpoints — forward-only accepted unless separately funded.
- In-app scheduler / pg_cron for eviction — external cron only (mechanism C decision, design.md §6).
