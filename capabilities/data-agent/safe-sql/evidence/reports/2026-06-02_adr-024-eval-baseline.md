# ADR-024 EVAL Baseline — Stage E α' E-4 (2026-06-02)

- **Stage**: Phase M4 Stage E α' E-4 (E-4-PR2)
- **Branch**: `documentation/spec-anchored-refactor-m4-e-4-eval-baseline`
- **Commit**: `23bc58e` (develop tip; #200 merged)
- **Source**: ADR-024 (`decisions/ADR-024_Eval_Framework_Spec.md`)
- **Outcome**: ADR-024 EVAL baseline **established** — `tests/eval` 93/93 PASS (pass_rate 1.0); component (precheck) + golden-seed schema layers, no live DB / LLM.
- **Prereqs landed**: #198 (E-0b runbook curation) + #199 (E-1/E-2 G21/G22 BLOCKING flip) + #200 (E-4 soak tracker).
- **Placement note**: filed under `safe-sql` (not `llm-provider`) because the component layer runs `precheck_sql` (safe-sql L1b) and shares its rule source per the test docstring; `llm-provider/evidence` covers provider switching (ADR-027), unrelated to the seed/precheck eval.

## §1 Context

Stage E α' E-4 requires an ADR-024 EVAL baseline before M4 closure. This records the first
runnable (no-live-dependency) baseline.

## §2 Command

```bash
uv run pytest tests/eval -q
```

Run at commit `23bc58e` (develop venv; rootdir = `spec-anchored-refactor-m4-e-4-eval-baseline`
worktree). There is no `eval` pytest marker registered (`markers = [smoke, contract]`), so the
default selection runs `tests/eval` directly.

## §3 Result

- exit_code: `0`
- baseline_metric: `eval.baseline.pass_rate`
- baseline_value: `1.0`
- test_count: `93`
- passed: `93`
- failed: `0`
- skipped: `0`
- duration: `~10.7s`
- environment: local; component + schema layers only (no live biz DB / LLM)
- seed corpus: 15 cases (`tests/eval/golden_seed.jsonl`)

## §4 Scope + Layers

- `test_golden_seed_schema.py` — structural validation of `golden_seed.jsonl` (≥15 cases, top-level
  / input / expected schema, difficulty mix, id uniqueness). No DB/LLM (per its docstring).
- `test_component_against_seed.py` — L3 Component check: `precheck_sql` on each seed reference SQL;
  shares rule source with the runtime L1b precheck per the MVP commitment. No DB/LLM.
- **NOT in baseline**: outcome eval (rows match expected) — requires a live DB and is covered by the
  smoke layer (excluded by default `-m 'not smoke and not contract'`).

## §5 Interpretation

- Baseline established: `pass_rate = 1.0` across the 93 component + schema assertions.
- This is the regression floor for ADR-024 EVAL in CI-runnable (no-live-dep) mode.
- No skipped tests → baseline denominator = 93 (all included).
- The outcome-layer eval (live DB) remains a smoke / Phase-2 concern, not part of this baseline.

## §6 Related Artifacts

- `plans/stage-e-alpha-prime-e-4-soak.md` (E-4 tracker)
- `plans/[PLAN]_spec_anchored_refactor.md` (master plan; `phase_progress.M4.E`)
- `tests/eval/` (`golden_seed.jsonl` + `test_component_against_seed.py` + `test_golden_seed_schema.py`)
- `decisions/ADR-024_Eval_Framework_Spec.md`

## §7 Codex

Codex invocation: NONE
