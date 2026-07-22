---
type: capability-runbook
capability: data-agent.memory-checkpointer
state: active
version: 1.0
owner: ranzuozhou
created: 2026-07-22
updated: 2026-07-22
last_verified: 2026-07-22
---

# Runbook: Memory Checkpoint At-Rest Desensitization

> Operational runbook for the at-rest redaction hook (ADR-038 mechanism B). The mechanism
> lives entirely in `src/mj_agent/memory/` (a separate capability, NOT a 4-必停 surface per
> `src/mj_agent/AGENTS.md`); it is wired behind `settings.mj_agent_memory_redact_biz_rows`
> (default **on** since the #365 AC4-6 activation). References
> `docs/guide/[GUIDE]_Developer_Onboarding.md` §7 for shared startup context.

## §1 Startup

The redaction hook is passive — it activates automatically whenever the checkpointer is
constructed with the flag on. No separate process.

```bash
# 1. Deps + secrets → .env
uv sync
.\scripts\setup-env.ps1

# 2. Bring up the dedicated memory container (host 5433 → container 5432)
docker compose --env-file .env -f docker/compose.yaml -f docker/compose.override.yml up -d mj-agent-postgres

# 3. Confirm the redacting saver is importable + wired
uv run python -c "from mj_agent.memory.redaction import RedactingAsyncPostgresSaver; from mj_agent.memory.checkpointer import open_checkpointer; print('redaction wired')"

# 4. Confirm the flag default (opt-out to disable)
uv run python -c "from mj_agent.config import settings; print('redact_biz_rows =', settings.mj_agent_memory_redact_biz_rows)"
```

To **disable** the redaction (revert to storing verbatim rows), set
`MJ_AGENT_MEMORY_REDACT_BIZ_ROWS=false` in `.env` and restart. This is a reversible,
config-only switch — no data migration.

## §2 Health Check

```bash
# Offline transform (no container): unit + BDD
uv run pytest tests/unit/test_memory_digest.py tests/unit/test_memory_redaction.py -q
uv run pytest tests/bdd/data_agent/memory_checkpointer -q
# Expected: all pass; no DB needed.

# On-disk both-paths canary + smoke round-trip (needs mj-agent-postgres + MJ_AGENT_MEMORY_USER)
uv run pytest tests/smoke/test_memory_redaction_canary.py -m smoke -q
# Expected with container up: 4 passed. Without creds: 4 skipped (clean).
```

**Expected outcomes**：

| Command | Container up + memory creds | Creds absent |
|---|---|---|
| `pytest tests/unit -k "digest or redact"` | all pass | all pass (no DB needed) |
| `pytest tests/bdd/data_agent/memory_checkpointer` | all pass | all pass (offline) |
| `pytest tests/smoke -m smoke -k memory_redaction` | 4 passed | 4 skipped (clean) |

## §3 Troubleshooting

### Symptom: a checkpoint blob still contains a verbatim biz cell value

**Diagnostic**：redaction did not fire on one of the two write paths (the
both-hooks-or-it-leaks footgun, same class as ADR-029 #288). Either the flag is off, or a
langgraph upgrade moved serialization so one override no longer runs.

**Resolution**：

- Confirm `settings.mj_agent_memory_redact_biz_rows` is `True`.
- Run the both-paths canary (`tests/smoke/test_memory_redaction_canary.py`): it reads the raw
  `checkpoint_blobs` (aput) AND `checkpoint_writes` (aput_writes) bytes and fails loudly on a
  leak; `test_plain_saver_leaks_on_both_paths` is the negative control proving it detects leaks.
- On a langgraph bump, re-verify the `aput` / `aput_writes` override points against the new
  wheel (design.md §5 Open Question 1) before trusting the canary green.

### Symptom: the execute_sql ToolMessage is NOT redacted (still has full rows)

**Diagnostic**：the message failed the envelope shape guard (`name == "execute_sql"` +
`executed_sql` / `rows` / `row_count` keys). Error-path ToolMessages (plain-string content)
and chart/excel envelopes are skipped by design.

**Resolution**：

- Confirm the tool actually emitted the standard `execute_sql` result envelope (see
  `data-agent.tool-chain` — `src/mj_agent/tools/sql/execute.py`). If the envelope keys were
  renamed upstream, update the shape guard `_ENVELOPE_KEYS` in `redaction.py` (cross-capability
  change; see `trace.yml` cross_capability_refs → data-agent.tool-chain).

### Symptom: cold resume needs a specific row value that was digested away

**Diagnostic**：mechanism B keeps only `executed_sql` + per-column counts at rest (REQ-003).
The verbatim rows are recoverable-by-refetch, not stored.

**Resolution**：

- Re-run `executed_sql` through the guardrail chain to re-fetch rows. Caveat: relative-time /
  "latest" queries may drift on re-fetch (documented, not a defect).
- Durable cross-session resume is not shipped today (`ui.py` mints a fresh `thread_id` per
  session), so this path is roadmap-only; LangGraph Studio resumes by `thread_id`.

## §4 Related artifacts

- `contracts/checkpoint-redaction.contract.yml` — INV-1..INV-4 (the persist-path invariants)
- `contracts/behavior.feature` — 4 Gherkin scenarios (REQ-001..004)
- `spec.yml` / `requirements.md` / `design.md` — REQ statements + mechanism B rationale
- `decisions/ADR-038_Memory_Checkpoint_At_Rest_Desensitization.md` — direction (Ruling 1/2)
- `decisions/ADR-037_Memory_PG_MCP_Projection_To_Codex.md` — the driver (Codex-readable residual)
- `src/mj_agent/memory/{digest,redaction,checkpointer}.py` — implementation
- `tests/smoke/test_memory_redaction_canary.py` — both-paths canary + smoke round-trip

## §5 Post-mortem Trigger

Escalate to `evidence/postmortems/` writeup when:

- A verbatim biz cell value is found in `checkpoint_blobs` or `checkpoint_writes` with the flag
  on (redaction regression — highest priority; both-hooks-or-it-leaks class).
- The live conversation degrades because redaction mutated live state (REQ-002 violation — the
  saver must hand `super()` clones, never mutate live messages).
- A langgraph upgrade silently moves serialization so the canary green no longer reflects the
  real on-disk bytes.

Postmortem path: `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` per
`policies/archive.md` retention class `permanent`.

---

> Activation baseline (#365 AC4-6, 2026-07-22). The design-space evaluation (mechanisms
> A/B/C/D + tradeoffs) lives in `design.md` §4 + ADR-038.
