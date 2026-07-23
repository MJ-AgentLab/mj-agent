# Verification: both-paths canary + smoke round-trip PASS (#365 AC4-6)

- **Capability**: data-agent.memory-checkpointer
- **Evidence kind**: verification
- **Verified by**: ranzuozhou · **Date**: 2026-07-22

## Scope

At-rest checkpoint redaction (ADR-038 mechanism B). Two layers:

- **Container (this file's focus)** — REQ-001/003/004 against the live `mj-agent-postgres`
  container: no verbatim biz cell value survives on **either** on-disk write path (REQ-004), and
  the digested envelope round-trips on cold resume with `executed_sql` retained (REQ-003) + rows
  minimized (REQ-001). Plus the `open_checkpointer()` flag→saver routing (the config default this
  slice flips).
- **Offline (CI; cross-referenced)** — REQ-002 (live in-process state untouched) is verified by the
  BDD + unit layer, not the container: the redacting saver hands `super()` clones and never mutates
  the live message objects. See the "Offline layers" section below.

## Environment

- `langgraph-checkpoint` 4.0.2 / `langgraph-checkpoint-postgres` 3.0.5 (pinned wheels; T-001).
- `mj-agent-postgres` container up (host `5433` → container `5432`); memory role reachable.
- `settings.mj_agent_memory_redact_biz_rows = True` (default-on since this slice).
- Platform: win32, Python 3.13; `SelectorEventLoop` (issue #283).

## Method

`tests/smoke/test_memory_redaction_canary.py` (`-m smoke`, gated by `memory_db`):

1. **AC4 aput path** — write a checkpoint via `aput` carrying an `execute_sql` ToolMessage whose
   rows hold a distinctive value `CANARY-ACME-9973`; read the raw `checkpoint_blobs.blob` (BYTEA)
   with plain SQL; assert the value's bytes are absent and `rows_redacted` is present.
2. **AC4 aput_writes path** — same via `aput_writes` → `checkpoint_writes.blob`. Both paths are
   asserted because overriding only one leaks rows through the other (ADR-029 #288 class).
3. **Negative control** — the stock `AsyncPostgresSaver` persists the value on **both** paths,
   proving the canary genuinely detects a leak (not a vacuous pass).
4. **AC5 smoke round-trip** — redacting-saver persist → a fresh saver instance (new-process
   resume) `aget_tuple` reads back a digested envelope (`rows_redacted: true`, empty rows, no
   verbatim value) with `executed_sql` retained.
5. **Flag routing** — `open_checkpointer()` yields `RedactingAsyncPostgresSaver` when the flag is
   on (the default this slice flips) and the stock `AsyncPostgresSaver` when off — the actual
   config-default→saver wiring, not the redacting class in isolation.

## Result — PASS

```
tests/smoke/test_memory_redaction_canary.py::test_aput_path_no_verbatim_value PASSED
tests/smoke/test_memory_redaction_canary.py::test_aput_writes_path_no_verbatim_value PASSED
tests/smoke/test_memory_redaction_canary.py::test_plain_saver_leaks_on_both_paths PASSED
tests/smoke/test_memory_redaction_canary.py::test_smoke_round_trip_digested_on_resume PASSED
tests/smoke/test_memory_redaction_canary.py::test_open_checkpointer_routing_honors_flag PASSED
============================== 5 passed in 0.82s ==============================
```

Raw-byte observations (per the design validation run):

| Saver | `CANARY` in checkpoint_blobs | `CANARY` in checkpoint_writes | round-trip `rows_redacted` | round-trip `executed_sql` |
|---|---|---|---|---|
| `AsyncPostgresSaver` (control) | **present** | **present** | n/a | n/a |
| `RedactingAsyncPostgresSaver` | absent | absent | true | retained |

Offline layers (no container, run in CI):

```
tests/bdd/data_agent/memory_checkpointer/  → 3 passed (REQ-001/002/003; REQ-002 live-untouched here)
tests/unit/test_memory_digest.py + test_memory_redaction.py → 15 passed
tests/unit/test_memory_redact_flag.py → 1 passed (config default flip False→True locked)
```

REQ-002 (live in-process state untouched) is asserted specifically by
`test_req_002_live_state_untouched` (BDD) and `test_redact_checkpoint_live_state_untouched` /
`test_redact_value_list_clones_only_execute_sql` (unit) — the redacting saver mutates only clones.

## CI-safety

- The canary/smoke module carries `@pytest.mark.smoke`; `pyproject.toml addopts` deselects it by
  default → CI (no container) does **not** run it (verified: `5 deselected`).
- Without `MJ_AGENT_MEMORY_USER` the `memory_db` fixture skips cleanly (verified: `5 skipped`),
  so a `-m smoke` run without creds never fails.
- The default-flip itself is locked by the container-free `test_memory_redact_flag.py`, which runs
  in CI.

## Conclusion

REQ-001/002/003/004 verified (REQ-002 offline; the rest on-disk + round-trip on the container).
The both-hooks-or-it-leaks invariant (INV-4) holds on both on-disk paths; the negative control
demonstrates the canary would catch a regression; the flag→saver routing behind the default flip
is exercised end-to-end. Basis for `lifecycle_state: active`.
