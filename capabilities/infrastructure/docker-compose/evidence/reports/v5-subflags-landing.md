# V5 Sub-flags Landing — M3-FU-V5-SUBFLAGS

**Plan section:** `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown → M3-FU-V5-SUBFLAGS
**Resolved on:** Phase M3 Stage A (branch `documentation/spec-anchored-refactor-m3`)
**Outcome:** 3 additive sub-flags `--bdd` / `--tdd` / `--compose-config` landed in `scripts/sdd/check_docker_contracts.py`; CI V5 step updated to exercise all three.

## Why

V5 5.1 (Phase M2 Stage A) shipped core Dockerfile + compose static lint.
Three deferred sub-flags surfaced as a M2→M3 follow-up (M3-FU-V5-SUBFLAGS):
- `--bdd`: docker-bdd-scenario-check sub-mode (healthcheck schema presence)
- `--tdd`: docker-tdd-contract-test sub-mode (schema-layer completeness)
- `--compose-config`: static `docker compose config` analog (compose YAML
  structural validation without invoking docker daemon)

## Sub-flag semantics (additive; do not replace core lint)

### `--bdd` — docker-bdd-scenario-check

- `docker.contract.yml` MUST declare `healthcheck` block (dict) with `cmd`.
- Each service in `compose.contract.yml` `services{}` MUST declare a
  `healthcheck` key (REQ-002 startup order; LangGraph Studio + Chainlit
  startup gating).

### `--tdd` — docker-tdd-contract-test

- `docker.contract.yml` MUST declare `runtime_stage_contract` dict with
  sub-fields `user` / `forbidden_in_image` / `entrypoint`.
- `compose.contract.yml` MUST declare `invocation_contract` with all 3
  profile commands: `dev_command` / `test_command` / `prod_command`.

### `--compose-config` — static `docker compose config` analog

- Loads each compose file declared in `compose.contract.yml`
  `file_layering.base` + `file_layering.overlays[].path`.
- Verifies each file's YAML root is a mapping.
- Verifies the BASE file (index 0 in the chain) declares `services{}`.
- Verifies — per Docker compose **merge semantics** — that every service
  has `image` or `build` SOMEWHERE in the chain (not necessarily in every
  overlay). Avoids spurious WARN on overlay files that only inject env or
  network overrides.

## Output against M1 docker-compose capability

| Mode | PASS | WARN | FAIL |
|---|---:|---:|---:|
| core (no sub-flag) | 2 | 4 | 0 |
| `--bdd` | 2 | 4 | 0 (BDD fields all present) |
| `--tdd` | 2 | 4 | 0 (TDD schema complete) |
| `--compose-config` | 2 | 4 | 0 (merge-semantics-aware; no spurious overlay WARN) |
| all 3 sub-flags | 2 | 4 | 0 |

All 4 existing WARN are pre-existing schema-deviation informational lines
(M1 nested vs M0 flat). No new WARN added by sub-flags against current
contracts.

## Acceptance criteria

| AC | Status |
|---|---|
| 3 sub-flags added (`--bdd` / `--tdd` / `--compose-config`) | ✅ |
| ~60-80 lines new code | ✅ ~95 lines added (5 helper functions + argparse + wire-up) |
| No regression on V5 5.1 core lint | ✅ core unchanged 2P/4W/0F |
| Unit tests | ✅ 15 cases in `tests/unit/test_sdd_v5_subflags.py` |
| CI exercises sub-flags | ✅ V5 step updated to `--all --bdd --tdd --compose-config` |
| Independent PR; `feat(sdd)` commit | ✅ this commit |

## Regression checks

- `uv run pytest tests/unit -q` → 236 passed (was 221 + 15 new)
- `uv run ruff check` on touched files → clean (auto-fix applied to test imports)
- V1-V7 + G1/G2/G9 outputs unchanged (V5 sub-flag adds optional WARN only when invoked with sub-flag)

## Plan §6 严格守约 compliance

- ✅ No V5 5.1 core logic modified (sub-flags are additive)
- ✅ No Stage C contracts modified
- ✅ No 必停 surfaces modified
- ✅ No CI blocking toggle (V5 stays warning at M3; M4 schedule)

## Files changed

- `scripts/sdd/check_docker_contracts.py` — 5 new helpers + argparse wiring (~95 lines added)
- `tests/unit/test_sdd_v5_subflags.py` — new, 15 tests
- `.github/workflows/ci.yml` — V5 step name + invocation updated
- `capabilities/infrastructure/docker-compose/evidence/reports/v5-subflags-landing.md` — this file
- `plans/[PLAN]_spec_anchored_refactor.md` — §M3 Task Breakdown M3-FU-V5-SUBFLAGS marked completed
