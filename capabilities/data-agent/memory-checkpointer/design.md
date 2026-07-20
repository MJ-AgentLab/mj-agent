---
type: capability-design
capability: data-agent.memory-checkpointer
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-07-20
updated: 2026-07-20
---

# Design: Memory Checkpoint At-Rest Desensitization

## §1 Context

The memory checkpointer (`src/mj_agent/memory/checkpointer.py:88`) constructs
`AsyncPostgresSaver(pool)` **raw** — no custom `serde=`, no wrapper, no interception hook between
graph state and Postgres. It persists the full LangGraph message state (incl. `execute_sql`
ToolMessages whose envelope `rows` carries verbatim biz cell values, ≤ `sql_max_rows`=500) into the
**independent** `mj_agent_memory` DB (dedicated `mj-agent-postgres` container; read-write creds
`mj_agent_memory_user` ≠ biz `analyst` RO). No TTL/retention exists; rows accumulate per `thread_id`.

This is **not** a data-boundary breach — reading the memory DB cannot reach biz tables, bypass
L1/L1b, or issue new queries; it only yields historical, already-guardrail-approved results. But it
**is** a second at-rest copy of biz-derived rows, now also Codex-readable post-ADR-037. ADR-037
named "Phase-2 checkpoint 摘要/脱敏" as a driver with no mechanism designed. This capability is the
Phase-2 hardening.

Verified facts (2026-07-20): durable cross-session resume is **not shipped** today
(`src/mj_agent/ui.py:137` mints a fresh `uuid4` per `on_chat_start`; no `on_chat_resume`) — so
persisted rows are write-mostly, read-back-rarely; roadmap-fragile (LangGraph Studio resumes by
`thread_id`).

## §2 Decision

Direction fixed by [ADR-038](../../../decisions/ADR-038_Memory_Checkpoint_At_Rest_Desensitization.md):

- **Ruling 1 (scope)** — store-at-rest minimization is the target (independent of who reads it);
  ADR-037's Codex projection stays.
- **Ruling 2 (mechanism B)** — at **persist time**, replace the `execute_sql` ToolMessage `rows`
  with a deterministic per-column digest, retain `executed_sql` for recoverable-by-refetch, leave
  the live conversation untouched. Optional pairing with C (TTL) is out of scope for this capability.

## §3 Architecture

```
graph.astream() ──► langgraph internal ──► RedactingAsyncPostgresSaver
                                             ├─ aput(checkpoint)      ─┐  (planned modules)
                                             └─ aput_writes(writes)   ─┤
                                                                       ▼
                          _redact_messages(msgs)  ── clone-not-mutate ──► super().aput* ──► Postgres
                                    │
                                    └─ memory/digest.py: pure per-column aggregate (no LLM call)
```

Planned modules (build slice #365 AC3-6):

- `src/mj_agent/memory/digest.py` — pure deterministic per-column **count** aggregation
  (`{non_null, distinct}` counts only — `min`/`max` are excluded because they would be verbatim biz
  cell values, which REQ-001 forbids), microsecond-scale, unit-testable, **no LLM call** (an LLM
  summary would re-egress biz rows + be non-deterministic).
- `src/mj_agent/memory/redaction.py` — `RedactingAsyncPostgresSaver(AsyncPostgresSaver)` overriding
  **both** `aput` and `aput_writes`; identifies `execute_sql` ToolMessages by `name == "execute_sql"`
  AND a JSON-envelope shape guard (`executed_sql` + `rows` + `row_count`); emits `model_copy` clones
  with `rows` → digest + `rows_redacted: true`.
- Swap the single constructor at `checkpointer.py:88` to the subclass (feature-flagged).

Hook rationale: a LangGraph middleware operates on **live** state (cannot do persist-only); a custom
serde walks opaque bytes. The `aput`/`aput_writes` override is the last point the data exists as
typed message objects before serialization — the only place that redacts at-rest while leaving live
state intact.

## §4 Tradeoffs

| Choice | Pros | Cons | Rationale |
|---|---|---|---|
| **B: persist-time digest + keep SQL** (chosen) | at-rest minimized; live untouched; recoverable-by-refetch; deterministic/testable; no key mgmt; no new dep; non-必停 | forward-only; refetch drifts for relative-time queries; digest is still biz-derived (aggregates) | Best fits Ruling 1 (minimize) while keeping the store useful to Codex (envelope shape/stats/SQL), aligned with retained ADR-037 |
| A: hard-stub redact (rejected as primary) | maximal minimization; cheapest | irreversible cold-resume loss; roadmap-fragile; less signal to Codex | Retained as fallback if digest cost is unjustified |
| C: TTL/retention (complement) | bounds standing window | doesn't minimize live/recent copies | Optional add-on, not this capability |
| D: encrypt-at-rest (rejected) | lossless; confidentiality | not minimization (data stays); opaque to Codex (conflicts ADR-037); AES key mgmt | Off-target for the minimization goal |

Threats addressed: a reader of the second store (dump/backup/insider/Codex) gets column stats + SQL,
not verbatim customer/institution values. NOT addressed: biz values echoed in the assistant NL
answer (AIMessage — egress/answer-side control); the cloud-LLM in-flight egress (roadmap 代号化).

Cross-capability dependency: the `execute_sql` envelope shape (`data-agent.tool-chain`, Phase 2+) is
the redaction target; a change to the envelope keys would require re-checking the shape guard.

## §5 Open Questions (resolved during the build slice)

1. **langgraph pinned-wheel verification** — the `aput`/`aput_writes` / `_dump_blobs` / `_dump_writes`
   / default `JsonPlusSerializer` contract must be verified against the installed wheel before coding;
   a canary test on persisted bytes locks the both-hooks-or-it-leaks footgun (ADR-029 #288 class).
2. **`name == "execute_sql"` reliability** — confirm the success-path ToolMessage carries `name`
   end-to-end through `create_agent`'s tool node; the JSON-envelope triple is the fallback selector.
3. **digest head-sample `k`** — whether to keep the first `k` rows verbatim (fidelity dial); default 0.
4. **forward-only vs backfill** — whether to fund a one-time scrub of pre-deploy `checkpoint_blobs`.
5. **BDD risk levels** — whether the build-slice `behavior.feature` scenarios warrant @risk:high (with
   trace.yml + runbook justification) or stay medium; deferred with the build.
