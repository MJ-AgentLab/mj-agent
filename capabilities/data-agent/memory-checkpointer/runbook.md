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

> Operational runbook for the memory checkpointer at-rest controls: mechanism B (redaction hook,
> ADR-038; §1-§5) + mechanism C (TTL eviction, #386; **§6**). Both live entirely in
> `src/mj_agent/memory/` (a separate capability, NOT a 4-必停 surface per `src/mj_agent/AGENTS.md`);
> B is wired behind `settings.mj_agent_memory_redact_biz_rows` (default **on** since the #365 AC4-6
> activation), C behind `MJ_AGENT_MEMORY_TTL_DAYS` (default **0 = off**, opt-in). References
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

- `contracts/checkpoint-redaction.contract.yml` — INV-1..INV-4 (mechanism B persist-path invariants)
- `contracts/checkpoint-retention.contract.yml` — INV-R1..INV-R4 (mechanism C eviction invariants)
- `contracts/behavior.feature` — 6 Gherkin scenarios (REQ-001..005)
- `spec.yml` / `requirements.md` / `design.md` — REQ statements + mechanism B/C rationale (design §6 = C)
- `decisions/ADR-038_Memory_Checkpoint_At_Rest_Desensitization.md` — direction (Ruling 1/2; C stack-on)
- `decisions/ADR-037_Memory_PG_MCP_Projection_To_Codex.md` — the driver (Codex-readable residual)
- `src/mj_agent/memory/{digest,redaction,retention,checkpointer}.py` — implementation
- `src/mj_agent/server/cli.py` — `mj-agent memory-evict` (mechanism C)
- `tests/smoke/test_memory_redaction_canary.py` — both-paths canary + smoke round-trip (B)
- `tests/unit/test_memory_retention.py` + `tests/smoke/test_memory_retention_smoke.py` — TTL eviction (C)

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

## §6 Mechanism C — TTL/retention eviction (REQ-005; opt-in)

Bounds the at-rest lifetime of stale checkpoint threads (ADR-038 optional stack-on). **Opt-in +
irreversible**: disabled unless a positive TTL is set, and it never auto-runs (no in-app scheduler).

### Usage

```bash
# Dry-run FIRST — reports the stale threads, deletes nothing:
uv run mj-agent memory-evict --older-than 90 --dry-run

# Real eviction (deletes threads whose newest checkpoint is > 90 days old):
uv run mj-agent memory-evict --older-than 90

# Or set a default TTL in .env and run without --older-than:
#   MJ_AGENT_MEMORY_TTL_DAYS=90
uv run mj-agent memory-evict
```

- `TTL <= 0` (unset) -> no-op, exit 0 (opt-in). Memory creds absent -> SKIP, exit 0.
- Deletion is per-thread via langgraph `adelete_thread` (checkpoints + checkpoint_blobs +
  checkpoint_writes). A thread's age = its newest checkpoint's uuid6 timestamp; strict boundary
  (age exactly at the cutoff is retained).

### Periodic retention (external cron)

mj-agent has no in-app scheduler — wire `memory-evict` into external cron / Windows Task Scheduler:

```cron
# daily 03:00 — evict checkpoint threads idle > 90 days (validate with --dry-run first)
0 3 * * *  cd /path/to/mj-agent && uv run mj-agent memory-evict --older-than 90 >> /var/log/mj-agent-evict.log 2>&1
```

**Quiescence caveat (TOCTOU)**: `adelete_thread` wipes a whole thread with no age predicate, so a
thread that goes stale-at-scan but receives a fresh checkpoint before its delete would lose that
write. `evict_stale_threads` re-checks each thread's age immediately before deleting and skips one
that is no longer stale (logged), which shrinks but does not fully close the window. For a hard
guarantee, run eviction while the app is quiescent (low-traffic window). This is low-risk today:
eviction is opt-in and durable cross-session resume is not shipped (the shipped Chainlit UI mints a
fresh `thread_id` per session; only LangGraph Studio resumes by `thread_id`).

**Backup caveat (ADR-038)**: effective retention window = `MIN(TTL, backup-retention)`. No backup
pipeline exists today (the compose `com.mj-agent.volume.backup` entries are labels, not a job), so
TTL alone is the control; if a backup regime is later added, its retention must be bounded too.

### Troubleshooting

- **"nothing to do (opt-in)"** — TTL is 0; set `MJ_AGENT_MEMORY_TTL_DAYS` or pass `--older-than N`.
- **"SKIP: memory DB credentials absent"** — `MJ_AGENT_MEMORY_USER/PASSWORD` not set (same gate as B).
- **A thread you expected to be evicted survived** — it has a checkpoint newer than the TTL
  (age = `MAX(checkpoint_id)` per thread). Confirm with `--dry-run`.
- **Health check**: `uv run pytest tests/unit/test_memory_retention.py -q` (offline) +
  `uv run pytest tests/smoke/test_memory_retention_smoke.py -m smoke -q` (needs container; skip-clean
  without creds).

---

> Activation baseline (#365 AC4-6, 2026-07-22). The design-space evaluation (mechanisms
> A/B/C/D + tradeoffs) lives in `design.md` §4 + ADR-038.
