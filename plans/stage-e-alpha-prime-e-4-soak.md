---
type: planning-aid
slug: stage-e-alpha-prime-e-4-soak
summary: E-4 soak kickoff tracker, opened after the G21/G22 combined BLOCKING flip landed (#199). Opens the 1-2 week soak observation window for G21/G22 blocking mode and tracks the remaining E-4 workstreams (ADR-024 EVAL baseline, Action-N-2 M-FU registry batch, M3 carry-over closure, 5 pilot capability state promotion, Stage F closure prep) as a checklist. Tracker/status only — the opening PR makes no code / CI / validator / test changes.
owner: ranzuozhou
created: 2026-06-02
updated: 2026-06-02
state: active
track: shared
related_m_fu:
  - M-FU#6 — M4-FU-G22-MODE-WARN-TO-BLOCKING-FLIP (RESOLVED PR #199)
  - M-FU#7 — M4-FU-RUNBOOK-JUSTIFICATION-CURATE-ALL-PILOTS (RESOLVED PR #198)
companion_docs:
  - plans/[PLAN]_spec_anchored_refactor.md (master plan; phase_progress.M4.E)
  - plans/stage-e-alpha-prime-e-0b-elicitation-aid.md (PR #196)
  - plans/stage-e-alpha-prime-m-fu-7-runbook-curation-worksheet.md (PR #193)
---

# Stage E α' E-4 Soak Kickoff

> Opened after the G21/G22 combined BLOCKING flip landed via #199. This doc is a
> tracker / status artifact only — the opening PR makes no code / CI / validator /
> test changes. Each E-4 workstream below is pursued as a separate follow-up PR.

## Stage E α′ Status

- E-0b runbook justification curation: done via #198
- E-1/E-2 combined BLOCKING flip: done via #199
- E-4 soak: active
- Stage F closure: pending
- Phase M5 archive ceremony: not started

## E-4 Scope

E-4 tracks:

1. G21/G22 blocking soak
2. ADR-024 EVAL baseline
3. Action-N-2 M-FU registry batch
4. M3 carry-over closure
5. 5 pilot capability state promotion
6. Stage F closure preparation

## E-4 Entry Verification

- #198 merged: yes
- #199 merged: yes
- G21 strict baseline: 15P/0W/0F
- G22 strict baseline: 15P/0W/0F
- Validator severity rewrite: not needed (blocking achieved via `--strict`)
- Codex invocation: NONE

## E-4 Non-goals

- No M5 archive ceremony
- No `phase-m4-complete` tag yet
- No CI gate toggle
- No validator severity rewrite
- No source code changes
- No test changes
- No 4-stop-surface changes

## E-4 Soak Checklist

Observation window: 1–2 weeks

### G21/G22 Blocking Soak

- [ ] Confirm new PRs execute G21/G22 as blocking checks
- [ ] Confirm no false-positive from G21
- [ ] Confirm no false-positive from G22
- [ ] If false-positive appears, record capability / scenario / validator message
- [ ] If real violation appears, confirm CI blocks as intended
- [ ] Confirm `--strict` path remains sufficient
- [ ] Do not reclassify validator severity unless explicitly required by owner review

### ADR-024 EVAL Baseline — ✅ established 2026-06-02 (E-4-PR2)

- [x] Locate current EVAL entrypoint under `tests/eval/`
- [x] Run minimal EVAL baseline — `uv run pytest tests/eval -q` → 93 passed / 0 failed / 0 skipped, exit 0
- [x] Record `baseline_metric` — `eval.baseline.pass_rate`
- [x] Record `baseline_value` — `1.0` (93 component + golden-seed-schema assertions; 15-case seed; no live dep)
- [x] EVAL ran (no blocker); outcome-layer eval (live DB) stays smoke-only, not in baseline denominator
- Evidence: `capabilities/data-agent/safe-sql/evidence/reports/2026-06-02_adr-024-eval-baseline.md`

### Action-N-2 Registry Batch — ✅ completed 2026-06-02 (E-4-PR5)

- [x] Reviewed all 18 registry entries + 2 M3 carry-over plans (per Cat Triage)
- [x] Marked completed/superseded items (Cat-1 ×6 via #194/#195/#198/#199; M-FU#2; M3 carry-over via #202/#203)
- [x] Kept active/deferred items explicit with target phase (M-FU#9 → M6; 3 carries → M5; 6 → Stage F/F-7; 2 ready as independent small PRs)
- [x] No new M-FU numbers pre-allocated; master plan registry is SoT
- [x] No capability promotion / Stage F closure mixed in

Evidence: **Action-N-2 M-FU Registry Reconciliation Batch** table in `plans/[PLAN]_spec_anchored_refactor.md` (§M4-FU Registry).

### M3 Carry-over Closure — ✅ triaged 2026-06-02 (E-4-PR3)

- [x] Review `m3_fu_skill_5segment_normalize` → **closed (resolved by E-4-PR4)**
- [x] Review `m3_fu_v4_skills_complete` → **closed (superseded by #183)**
- [x] Decide each: closed / active / obsolete

| Carry-over | Decision | Rationale | Follow-up |
|---|---|---|---|
| `m3_fu_v4_skills_complete` | **closed** (`state: completed`) | All AC met & verified @ `a457cd2`: 10 SKILLs carry `Do not use for:`; V4 34P/0W/0F; V4 ci.yml BLOCKING "per M3-FU-V4-SKILLS-COMPLETE" (executed #183 / M4-A). | none |
| `m3_fu_skill_5segment_normalize` | **closed** (`state: completed`) | Resolved by E-4-PR4: `sdd/adapters/runtime-skill.md` `body_section_heads` now documents `## Related` as the allowed 6th section, aligning the adapter doc with the contract-frozen 6-section shape (option B). No SKILL.md / contract / 必停 touch. | none |

- [x] No unresolved carry-over silently kept; the one active item has a concrete minimal follow-up (not dragged to M6).
- No Action-N-2 registry or capability-promotion changes in this PR.

### Capability State Promotion

- [ ] Prepare promotion for 5 pilot capabilities from drafting to active
- [ ] Do not promote until EVAL baseline and soak status are recorded
- [ ] Confirm trace / runbook / evidence consistency before promotion

### Stage F Preparation

- [ ] Prepare M4 closure update
- [ ] Prepare `phase-m4-complete` tag only after E-4 is complete
