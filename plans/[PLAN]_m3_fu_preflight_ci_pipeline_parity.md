---
type: plan
slug: m3-fu-preflight-ci-pipeline-parity
summary: M3 follow-up plan — extend Pre-flight Verification Discipline so new dev dep additions (pyproject.toml [dependency-groups] dev / [tool.uv] / [project] dependencies) trigger a full local CI-pipeline re-run, not only gate-affected checks; B-1 pytest-bdd → gherkin-official latent Py2-file SyntaxError surfaced only at Stage C push because Stage A/B pre-flight covered ruff/mypy/pytest but not the compileall step
state: active
version: 0.1
owner: ranzuozhou
created: 2026-05-21
updated: 2026-05-21
track: shared
refines:
  - plans/[PLAN]_spec_anchored_refactor.md
supersedes: []
related_adrs: []
---

# [PLAN] M3-FU-PREFLIGHT-CI-PIPELINE-PARITY — Local Pre-flight Must Mirror CI Pipeline on Dep Changes

> M3 follow-up plan；deferred from Phase M3 Stage C F-1 fix (compileall scope
> escape); refines `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown
> and extends Phase M3 kickoff outline Pre-flight Verification Discipline
> standing rule (`policies/ai-agent.md` §X pending).

## §1 Background

Phase M3 Stage C ci.yml flip commit `02b1cc8` pushed to
`origin/documentation/spec-anchored-refactor-m3` on 2026-05-21. First CI run
(`26229732363`) failed at the `Syntax check (compileall)` step — well before
any flipped blocking gate executed. All downstream steps were skipped due to
the early-exit; the flip itself was never actually validated.

Root cause: `compileall -q .` recurses into `.venv/`. The pytest-bdd dev dep
introduced in Stage B-1 commit `9464e5c` transitively pulled in
`gherkin-official`, which ships `count_symbols_py2.py` containing
Py2-only `ur'[\uD800-\uDBFF]...'` raw-unicode literal. The file is runtime
version-gated and never imported on Python 3, but `compileall` doesn't know
that — it just walks every `.py` and parses it.

Why latent until Stage C push: per the Phase M3 Stage A closure plan,
**Stage B was intentionally LOCAL-ONLY**; "single push after Stage C lands"
was the explicit instruction. The latent failure was sitting since B-1
(2026-05-21) but never exercised CI.

Why local pre-flight didn't catch it: Stage A and Stage B per-commit verify
ran `ruff check src tests` + `mypy --strict src/mj_agent` + targeted
validator scripts + targeted pytest paths. None of these recurse into
`.venv/` — they're (correctly) scoped to project code. Only `compileall -q .`
(at the CI layer) walks the whole tree.

## §2 Scope

### Included

- **Discipline extension** (the deliverable): expand the Pre-flight
  Verification Discipline standing rule (Phase M3 kickoff outline item 1;
  pending formal write-in under M3-FU PREFLIGHT-DISCIPLINE-WRITE-IN that
  lands the rule into `policies/ai-agent.md` §X — see Phase M3 kickoff
  outline) to add:

  > Any change touching `pyproject.toml [dependency-groups]`,
  > `[project.dependencies]`, `[tool.uv]`, or `uv.lock` MUST locally run the
  > full CI pipeline steps before the next push, not only the gate steps
  > directly affected by the change. Specifically: `compileall` over the
  > scope CI runs (currently `src tests scripts` after Phase M3 Stage C F-1
  > fix), `ruff check` over CI scope, `mypy --strict` over CI scope,
  > `pytest --collect-only`, plus any other CI-layer steps not already
  > exercised by gate-specific local commands.

- **Pre-commit hook proposal** (optional sub-deliverable): add a `pre-push`
  hook that detects `pyproject.toml` / `uv.lock` changes in the push and
  runs the full local CI mirror automatically. Deferred to M5+; scope note
  only.

### Excluded

- Not changing the CI pipeline itself further (Phase M3 Stage C F-1 already
  fixed the compileall scope; that fix stands).
- Not auditing/fixing existing third-party packages in `.venv/` (upstream
  concern; not this repo's responsibility).
- Not adding compileall to `pyproject.toml` `addopts` or `[tool.pytest]`
  (compileall is not a pytest concern; lives in CI yaml).
- Not refactoring Stage A/B/C per-commit reverify pattern retroactively
  (only forward; Phase M4+ adoption).

## §3 Verification

After the discipline write-in lands:

```bash
# Standing rule triggers when any of these change since HEAD~1:
git diff HEAD~1 -- pyproject.toml uv.lock
# If non-empty diff, the discipline requires the following before the next
# push or commit-amend:

uv run python -m compileall -q src tests scripts  # CI-equivalent scope
uv run ruff check src tests                        # CI-equivalent scope
uv run mypy --strict src                            # CI-equivalent scope
uv run pytest --collect-only                       # surface collection errors
```

The discipline applies to: any AI agent or human contributor touching
dep state, regardless of whether the rest of the change is "obviously
unrelated to dep-affected gates."

## §4 AC

- [ ] `policies/ai-agent.md` §X (Pre-flight Verification Discipline) section
      amended with the dep-change sub-rule (after the §X parent write-in
      lands).
- [ ] Each Phase M3 Stage A/B/C-style atomic commit checklist (per
      `[STANDARD]_..._AI_Engineering_Execution_HITL_Prompt`) updated to
      reference this rule when the commit touches dep state.
- [ ] Optional: pre-push hook script that auto-runs the 4 commands above
      when `pyproject.toml` or `uv.lock` differ between local and origin
      (deferred to M5+; record as a Phase M5 entry).
- [ ] Independent PR; commit type `docs(policies)`.

## §5 估时 / Dependencies

- 估时 ~30-60 min (amend `policies/ai-agent.md` standing rule, add
  cross-ref to this plan).
- **Blocked-by Phase M3 Pre-flight Verification Discipline parent
  write-in** (the standing rule itself is currently outlined but not yet
  formally written into `policies/ai-agent.md` per Phase M3 kickoff
  outline item 1).
- Independent of other M3-FU plans; can land any time after parent rule.

## §6 严格守约

- ✅ No CI pipeline modification beyond what landed in Phase M3 Stage C F-1.
- ✅ No third-party / `.venv/` modifications.
- ✅ No retroactive enforcement on commits before this plan lands; forward
  rule only.
- ✅ No 必停 surface touched.

---

> *M3 follow-up plan — `state: active`；deferred from Stage C F-1 fix
> discipline gap (2026-05-21)；blocked-by Pre-flight Verification Discipline
> parent write-in；M3+ adoption.*
