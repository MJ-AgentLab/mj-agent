# Verification: mechanism C — TTL/retention eviction (#386, REQ-005)

- **Capability**: data-agent.memory-checkpointer
- **Evidence kind**: verification
- **Verified by**: ranzuozhou (AI-implemented, Claude Code) · **Date**: 2026-07-23

## Scope

Mechanism C (ADR-038 optional stack-on; REQ-005): opt-in TTL eviction of stale checkpoint threads via
`mj-agent memory-evict`. Two layers:

- **Offline (CI-run) — PASS**: pure uuid6->epoch extraction (pin-verified against langgraph 1.1.8
  `UUID.time`), stale-thread selection + strict age boundary, dry-run-deletes-nothing, and selective
  eviction control-flow through a fake saver. Plus `mj-agent memory-evict` opt-in / SKIP gates. ruff + mypy(strict).
- **Container (real DELETE) — DEFERRED**: the real-DB selective eviction (incl. SQL `MAX`-picks-newest)
  is in `tests/smoke/test_memory_retention_smoke.py`; its **execution is pending** — the feature
  worktree has no `.env`, so the `memory_db` fixture skips. To be run against `mj-agent-postgres` on
  `develop/` at Stage 17 (post-merge) or by the Owner. The module **collects** cleanly (2 tests).

## Environment

- `langgraph` 1.1.8 / `langgraph-checkpoint-postgres` >= 3.0.5 (pinned; `adelete_thread` present,
  covers checkpoints + checkpoint_blobs + checkpoint_writes — verified via `inspect.getsource`).
- `checkpoint_id` = langgraph uuid6 (v6, time-ordered); the stdlib field extraction matches
  `UUID.time` exactly (delta ~3e-5 s from real write time on a live generation).
- Platform: win32, Python 3.13.

## Method + Result

### Offline unit — PASS (CI-run)

`tests/unit/test_memory_retention.py` (10) + `tests/unit/test_cli_memory_evict.py` (5): `15 passed`.

Retention logic: uuid6 epoch pin vs langgraph 1.1.8, generation-time proximity, builder round-trip,
non-uuid6 raise, selective eviction, dry-run-deletes-nothing, strict boundary, empty DB, **non-uuid6
row skipped (not whole-pass abort)**, **raced-fresh thread skipped at delete** (the last two added
after the adversarial review — see below).

CLI glue: opt-in gate (TTL=0 no-op), accurate opt-out message for `--older-than 0`, creds-absent SKIP,
`--older-than` override of the config default + days->seconds, dry-run flag threading + message.

Full unit suite unaffected: `704 passed, 1 skipped` (689 prior + 15 new).

### Lint + types — PASS

```
uv run ruff check ...                 -> All checks passed!
uv run mypy src/mj_agent              -> Success: no issues found in 48 source files
```

### CLI offline paths — PASS

```
$ uv run mj-agent memory-evict                          # TTL=0 default, no .env
[memory-evict] TTL not set (MJ_AGENT_MEMORY_TTL_DAYS=0 and no --older-than) - nothing to do (opt-in). ...   exit=0
$ uv run mj-agent memory-evict --older-than 30 --dry-run   # creds absent
[memory-evict] SKIP: memory DB credentials absent.                                                          exit=0
```

Confirms INV-R3 (opt-in / creds-absent SKIP, both exit 0) at the CLI boundary.

### Container smoke — DEFERRED (pending execution)

`tests/smoke/test_memory_retention_smoke.py` seeds threads with crafted uuid6 ids (old / fresh /
old+fresh) and asserts a purely-old thread is removed from all three tables while the fresh and
old+fresh (MAX-picks-newest) threads survive; plus a dry-run leaves rows on disk. **Not yet executed**
(feature worktree has no `.env`). Collection verified: `2 deselected` (marker-gated, no import error).

Run to complete this evidence (container up + `MJ_AGENT_MEMORY_USER` set):

```
uv run pytest tests/smoke/test_memory_retention_smoke.py -m smoke -q   # expect 2 passed; skip-clean without creds
```

## CI-safety

- Smoke module carries `@pytest.mark.smoke` → deselected in CI (no container); `memory_db` fixture
  skips cleanly without `MJ_AGENT_MEMORY_USER`.
- The eviction logic (age extraction, boundary, dry-run, selective deletion via fake saver) is fully
  covered by the container-free `test_memory_retention.py`, which runs in CI.

## Adversarial review (5 dimensions x find -> verify)

A multi-agent review (age-math / boundary / destructive-safety / cli-gates / test-adequacy, each
finding adversarially verified) produced 14 raw findings -> **5 confirmed, all LOW** after
verification (9 refuted as speculative / hypothetical / intended-behavior). It **confirmed correct**:
the uuid6 60-bit reconstruction (byte-identical to langgraph 1.1.8 `UUID.time`), the offset/`/1e7`
conversion, the strict-`<` boundary, and that SQL `MAX(checkpoint_id)` truly returns the temporally
newest checkpoint. Actions taken:

| Finding | Severity | Resolution |
|---|---|---|
| Non-uuid6 / corrupt id aborted the whole pass | low (fail-safe) | `_thread_latest_epochs` now skips-with-warning per row (test: `test_non_uuid6_row_skipped_not_whole_pass_aborted`) |
| TOCTOU: stale-at-scan thread wiped after gaining fresh activity | low | re-check age immediately before delete + skip if fresh (test: `test_raced_fresh_thread_skipped_at_delete`); quiescence caveat in runbook §6 |
| Opt-out message misreported cause on `--older-than 0` | low (cosmetic) | message reworded (test: `test_opt_out_message_accurate_for_explicit_zero`) |
| `memory-evict` CLI had zero tests | low (coverage) | added `tests/unit/test_cli_memory_evict.py` (5 tests, function-seam stubbed) |
| INV-R4 proven only by the deferred smoke | low (CI-confidence) | unchanged — the deferred container smoke is the open item below |

## Conclusion

REQ-005 offline logic (INV-R1 age boundary, INV-R2 dry-run, INV-R3 opt-in/SKIP) verified in CI + at
the CLI boundary; ruff + mypy green. INV-R4 (all-three-tables real DELETE) is proven by the container
smoke test, whose **execution is deferred** to a `.env`-bearing environment (develop/ Stage 17 or Owner
run) — tracked in the PR body. Mechanism C is code-complete and offline-verified; the container smoke
is the one open verification item.
