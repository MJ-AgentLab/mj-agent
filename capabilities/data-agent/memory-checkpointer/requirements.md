---
type: capability-requirements
capability: data-agent.memory-checkpointer
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-07-20
updated: 2026-07-20
---

# Requirements: Memory Checkpoint At-Rest Desensitization

> Machine-authoritative REQ source is `spec.yml requirements[]`; this file is the prose mirror.
> Direction fixed by [ADR-038](../../../decisions/ADR-038_Memory_Checkpoint_At_Rest_Desensitization.md)
> (Ruling 1 store-at-rest minimization / Ruling 2 mechanism B). Owning issue #365.

## REQ-001 — At-rest minimization of execute_sql rows

**Priority**：medium

**Statement**：Persisted checkpoints SHALL NOT contain verbatim biz cell values from
`execute_sql` results. At persist time the ToolMessage `rows` payload is replaced by a
deterministic per-column digest (e.g. per column `{non_null, distinct}`), and the
envelope is marked `rows_redacted: true`, while `columns` / `row_count` / `business_summary` /
`executed_sql` are retained.

**Rationale**：The `mj_agent_memory` DB otherwise holds a second copy of already-guardrail-approved
biz rows — now also readable by Codex post-[ADR-037](../../../decisions/ADR-037_Memory_PG_MCP_Projection_To_Codex.md).
The digest removes verbatim cell values while preserving analytic shape. **Medium** because a
regression leaves the ADR-037-accepted, reversible residual in place — not a new exposure.

**Acceptance**：Stored `execute_sql` ToolMessage content carries a per-column digest + `rows_redacted:true`;
no verbatim value from the original `rows` survives in `checkpoint_blobs` / `checkpoint_writes`.

**Trace**：REQ-001 → `contracts/checkpoint-redaction.contract.yml` (INV-1/INV-2) →
`contracts/behavior.feature` (scenario "Persisting an execute_sql ToolMessage replaces biz rows…") →
`tests/bdd/data_agent/memory_checkpointer/test_memory_checkpointer_bdd.py::test_req_001_rows_replaced_by_digest`
+ `tests/unit/test_memory_digest.py` + `tests/unit/test_memory_redaction.py::test_execute_sql_rows_replaced_by_digest`.

## REQ-002 — Persist-time only; live conversation untouched

**Priority**：medium

**Statement**：Redaction SHALL occur only on the persistence path (checkpoint write). The live
in-process message state SHALL remain byte-identical; what the LLM reads within an active turn is
unchanged. The saver passes redacted **clones** to `super()` and never mutates live message objects.

**Rationale**：Mechanism B is at-persist, not at-tool-emission (ADR-038 Ruling 2) — this is what
lets the store be minimized without degrading same-session multi-turn analysis. **Medium**.

**Acceptance**：After a persist superstep, the in-memory `messages` channel still carries the
original verbatim `rows`; only the bytes written to Postgres differ.

**Trace**：REQ-002 → `contracts/checkpoint-redaction.contract.yml` (INV-3) →
`contracts/behavior.feature` (scenario "Redaction clones the message…") →
`tests/bdd/data_agent/memory_checkpointer/test_memory_checkpointer_bdd.py::test_req_002_live_state_untouched`
+ `tests/unit/test_memory_redaction.py::{test_redact_value_list_clones_only_execute_sql, test_redact_checkpoint_live_state_untouched}`.

## REQ-003 — Recoverable-by-refetch (retain executed_sql)

**Priority**：medium

**Statement**：The persisted digest SHALL retain `executed_sql` verbatim so a cold cross-process
resume can re-fetch full rows by re-running the guardrail-approved query.

**Rationale**：Makes the resume-fidelity loss recoverable rather than permanent (ADR-038). Caveat:
relative-time / "latest" queries may drift on re-fetch — documented, not a defect. **Medium**.

**Acceptance**：A digested `execute_sql` envelope still contains `executed_sql`; re-running it
through the tool-chain yields rows (subject to the drift caveat).

**Trace**：REQ-003 → `contracts/checkpoint-redaction.contract.yml` (INV-2) →
`contracts/behavior.feature` (scenario "The digested envelope retains executed_sql…") →
`tests/bdd/data_agent/memory_checkpointer/test_memory_checkpointer_bdd.py::test_req_003_retains_executed_sql`
+ `tests/smoke/test_memory_redaction_canary.py::test_smoke_round_trip_digested_on_resume`.

## REQ-004 — All write paths covered (both-hooks-or-it-leaks)

**Priority**：medium

**Statement**：Redaction SHALL be applied on ALL checkpoint write paths (both `aput` and
`aput_writes`) so no path leaks verbatim biz rows. A canary test SHALL assert the persisted bytes
carry no cell value on either path.

**Rationale**：Overriding only one path leaks rows through the other — the same class of footgun as
[ADR-029](../../../decisions/ADR-029_Tool_Error_Surfacing_To_LLM.md) #288 (sync/async middleware).
**Medium** for the residual, but the canary is mandatory to prevent silent regression on a
langgraph upgrade that moves serialization.

**Acceptance**：A canary test writes via `aput` and flushes pending writes via `aput_writes`, then
asserts neither `checkpoint_blobs` nor `checkpoint_writes` contains a verbatim biz cell value.

**Trace**：REQ-004 → `contracts/checkpoint-redaction.contract.yml` (INV-4) →
`contracts/behavior.feature` (scenario "Both on-disk write paths carry no verbatim biz cell value") →
`tests/smoke/test_memory_redaction_canary.py::{test_aput_path_no_verbatim_value, test_aput_writes_path_no_verbatim_value, test_plain_saver_leaks_on_both_paths}`.

## Non-goals (see design.md §4)

- Does NOT cover biz values echoed in the assistant's natural-language answer (AIMessage) —
  answer-side / egress control, out of scope.
- Does NOT relax any data boundary (ADR-006/009/000); the memory DB was never a biz-table path.
- Forward-only: pre-deploy checkpoints keep full rows unless a one-time backfill is funded.
