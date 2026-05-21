# G1 / G2 / G9 SDD Validators — Real Implementation Landing (M3-FU-G1G2G9-IMPL)

**Plan:** `plans/[PLAN]_m3_fu_g1g2g9_impl.md`
**Resolved on:** Phase M3 Stage A (branch `documentation/spec-anchored-refactor-m3`)
**Outcome:** all 3 SDD skeleton validators replaced with real implementations; CI warning gates updated to drop `--dry-run` and exercise real logic.

## Skeleton → real impl

| Gate | Script | Before | After |
|---|---|---|---|
| G1 | `scripts/sdd/check_capability_schema.py` | M0 `[skeleton]` notice + `return 0` | ~150 lines real schema validation; 5/5 pilot PASS |
| G2 | `scripts/sdd/check_traceability.py` | M0 `[skeleton]` notice + `return 0` | ~170 lines real schema validation; 5/5 pilot PASS |
| G9 | `scripts/sdd/generate_index.py` | M0 `[skeleton]` notice + `return 0` | ~200 lines generator; writes `capabilities/INDEX.auto.md`; `--check` mode for idempotency; 5/5 pilot PASS |

## G1 — `check_capability_schema.py`

Validates `capabilities/*/spec.yml` against the documented schema:

- Required top-level fields (12): id / name / domain / lifecycle_state /
  archive_state / adapter_coverage / last_verified / owner / created /
  updated / summary / requirements
- `id` matches `<domain>.<slug>` pattern
- `lifecycle_state` ∈ 9-state enum + `drafting` (M1 transitional state used
  by all 5 pilot specs; safe-sql/spec.yml:96 documents `drafting → contracted`
  transition planned at M3 contract-test landing; M4 will formalise
  vocabulary)
- `archive_state` ∈ 5-state enum
- `adapter_coverage` ⊆ 8 slugs (7 canonical + `bdd-tdd` alias)
- `requirements[]` non-empty; each has REQ-NNN id + statement + rationale +
  priority ∈ {critical / high / medium / low}

Result: 5/5 pilot capabilities PASS.

## G2 — `check_traceability.py`

Validates `capabilities/*/trace.yml` against schema v1.2:

- Required top-level: capability / schema_version / links
- `capability` matches `<domain>.<slug>` pattern
- `schema_version == "1.2"`
- `links[]` non-empty; each `req` matches REQ-NNN pattern
- Per-link `bdd` object (when present): feature + non-empty scenarios +
  automation_status ∈ {automated / manual / unautomated}
- `cross_capability_refs[]` (when present): target + direction (outbound /
  inbound / bidirectional) + surface + rationale; R-G7 budget ≤ 5 warning

Standalone schema validation (no `jsonschema` dependency added).

Result: 5/5 pilot trace.yml PASS.

## G9 — `generate_index.py`

Generates `capabilities/INDEX.auto.md` from `spec.yml` + `trace.yml`. Output
is a **separate file** from the manually-curated `INDEX.md` so rich narrative
sections (Risk Inventory / Test Coverage Snapshot / Next Phase) stay
untouched. M4+ may consolidate.

Modes:
- default (write): regenerate `INDEX.auto.md`.
- `--check`: regenerate to memory, byte-compare against committed file, WARN
  on drift (G9 idempotency).
- `--dry-run`: count spec.yml, no I/O.

Sections generated:
- Active Capabilities table (id / name / domain / lifecycle / archive /
  last_verified / adapter_coverage), skipping `archived` and `purge-eligible`.
- Cross-Capability References table compiled from all `trace.yml`
  `cross_capability_refs[]`.

Link paths relative to `INDEX.auto.md` location (matches manual INDEX.md
style; e.g. `./data-agent/safe-sql/spec.yml`).

Result: 5/5 pilot specs included in committed `INDEX.auto.md`; `--check`
PASSes against committed file.

## Acceptance criteria

| AC | Status |
|---|---|
| 3 validator scripts ≥ 80 lines real validation logic (no `[skeleton]` notice) | ✅ G1 ~150 / G2 ~170 / G9 ~200 |
| 3 validators pass against 5 pilot capabilities + 4 Stage C contracts | ✅ all 5 pilot PASS; Stage C contract-yml files are validated separately by V1-V7 |
| violation count meaningful (WARN with reason) | ✅ verified via unit tests for missing field / invalid enum / invalid pattern |
| Unit tests cover happy + missing field + invalid schema + drift detection | ✅ 16 cases in `tests/unit/test_sdd_g1g2g9_validators.py` |
| CI workflow stays warning mode until M4 | ✅ all 3 steps `continue-on-error: true` |
| CLI consistent with Stage A 6 adapter validators (3 modes) | ✅ all 3 use `build_argparser` with `--dry-run / --capability / --all / --strict` |
| Independent PR; `feat(sdd)` commit | ✅ this commit |

## §6 严格守约 compliance

- ✅ No G1/G2/G9 blocking toggle (warning mode preserved; M4 work)
- ✅ No 4 项专属必停 surface modified (validators are read-only)
- ✅ No new ADR (validator impl is not architectural; spec.yml lifecycle
  vocabulary `drafting` acceptance is a M3 compat decision, documented
  inline in source)

## Schema vocabulary note (M3 → M4 follow-up)

The `_LIFECYCLE_STATES` set includes `drafting` because all 5 pilot specs
use it (per safe-sql/spec.yml:96 documented `drafting → contracted`
transition planned at M3 contract-test landing). The 9-state enum in
spec.yml header comments lists 9 distinct states *omitting* `drafting`,
so this is a known schema-vs-usage drift. M4 should formalise the
vocabulary either by:

- promoting `drafting` to the canonical 10-state enum (codified somewhere
  in `sdd/`); or
- migrating all 5 pilot specs to `specified` (the closest 9-state
  equivalent for "spec exists but not yet contracted").

Either resolution is M4 scope (not this plan).

## Regression checks

- `uv run pytest tests/unit -q` → 221 passed (was 205 + 16 new = 221)
- `uv run ruff check` on touched files → clean (auto-fixed import order)
- `uv run mypy src/mj_agent` → clean (44 files)
- V1-V7 (Stage A 6 + V7 from P1-3) outputs unchanged

## Files changed

- `scripts/sdd/check_capability_schema.py` — replaced M0 skeleton (~150 lines)
- `scripts/sdd/check_traceability.py` — replaced M0 skeleton (~170 lines)
- `scripts/sdd/generate_index.py` — replaced M0 skeleton (~200 lines)
- `tests/unit/test_sdd_g1g2g9_validators.py` — new, 16 tests
- `.github/workflows/ci.yml` — G1/G2/G9 steps switched from `--dry-run` to real invocations
- `capabilities/INDEX.auto.md` — new, committed initial generator output
- `capabilities/data-agent/safe-sql/evidence/reports/g1g2g9-real-impl-landing.md` — this file
- `plans/[PLAN]_m3_fu_g1g2g9_impl.md` — state: completed + §7 Resolution
