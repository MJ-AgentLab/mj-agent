---
type: planning-aid
slug: stage-f-m4-closure-prep
summary: Stage F (M4 closure) preparation — drafted during the E-4 soak window (E-4-PR10). Records the soak-wait plan (promotion held until the 1-2 wk G21/G22 blocking soak elapses; no early promote), the Stage F entry gate, the M4-closure execution sequence, and the verified remaining-work disposition across Stage F / M5 / M6. This doc executes NOTHING gated — no capability promotion, no phase_progress flip, no phase-m4-complete tag.
owner: ranzuozhou
created: 2026-06-03
updated: 2026-06-03
state: active
track: shared
related_m_fu:
  - "M-FU#9 — M4-FU-G23-TASKS-CURATION-SURFACE (→ M6)"
  - "F-7 cluster — DOCSTRING-CLARIFY / V4-MODE-B-CLEANUP / OUTLINE-WORDING / DOCSTRING-DRIFT-DETECTOR / G22-BDD-HELPERS-CONSOLIDATE (→ Stage F)"
companion_docs:
  - plans/[PLAN]_spec_anchored_refactor.md (master plan; phase_progress.M4.E/F + §M4-FU Registry)
  - plans/stage-e-alpha-prime-e-4-soak.md (E-4 soak tracker + capability promotion preflight)
---

# Stage F — M4 Closure Prep (drafted during E-4 soak)

> **This is a PREP doc only.** It crosses no gate: no capability promotion, no
> `phase_progress` flip, no `phase-m4-complete` tag, no F-7 execution. It records
> the soak-wait plan (option 1) + the Stage F closure plan (option 3) so the work
> is ready to execute the moment the soak window elapses.

## §1 E-4 ledger (done) — verified against develop @ #208

| E-4 workstream | PR |
|---|---|
| G21/G22 BLOCKING flip (E-1/E-2 combined; `--strict`) | #199 |
| ADR-024 EVAL baseline (`eval.baseline.pass_rate=1.0`; 93P) | #201 / E-4-PR2 |
| M3 carry-over triage + 5segment adapter-align | #202 / #203 |
| Action-N-2 M-FU registry reconciliation | #204 |
| Capability promotion-readiness preflight + soak checkpoint | #205 |
| F8-SKILL-STEP-8 worktree-safe guard note | #206 |
| 11-FILE-ADR-025 reconcile — 4 free refs | #207 |
| 11-FILE-ADR-025 reconcile — 6 locked infra SKILLs + contract re-freeze | #208 |

## §2 E-4 completion blockers (what stands between now and Stage F)

1. **G21/G22 soak window NOT elapsed** — the 1–2 wk calendar observation (R-13-6) has not passed; the flip (#199) merged the same day (2026-06-02) as the checkpoint. Early signal is **clean** (PRs #200–#208 ran under blocking gates: 0 false-positives, 0 real violations) but insufficient for the *window* criterion.
2. **5 pilot capabilities still `drafting`** — all 5 are *ready* (full 9-artifact suite; G21/G22 clean) per the #205 preflight, but promotion to `active` is held by the promotion rule: separate PR gated on **clean soak window elapsed** + no readiness blocker. `mcp-server-governance` carries a caveat (G21/G22 SKIP — scenarios `@risk:medium`, no coverage; readiness rests on its own contracts + evidence → **owner must confirm** the medium-only posture is acceptable before promotion).
3. **`phase-m4-stage-e-alpha-prime-complete` tag** not yet eligible (gated on the same soak pass; Action-N-2 close-trigger fires on soak pass + tag eligible).

## §3 Soak-wait plan (option 1 — hold; do NOT promote early)

- **Window start**: 2026-06-02 (#199 flip merged).
- **Criterion** (R-13-6): 0 FAIL across G21+G22 (+G24) over a 1–2 wk CI-run window; monitor CI run history; M-FU on any FAIL surge.
- **Estimated unblock**: 2026-06-09 (1 wk, earliest) → 2026-06-16 (2 wk).
- **Promotion fires when**: soak observed clean **AND** `mcp-server-governance` medium-only caveat owner-confirmed.
- **Decision: hold.** Early promotion would contradict the #205 "wait-soak" decision; only an explicit owner override promotes before the window elapses.

## §4 Stage F closure sequence (execute only when E-4 complete)

> Entry gate: **E-4 fully complete** = soak observed clean + all 5 capabilities promoted `drafting → active` + `phase-m4-stage-e-alpha-prime-complete` tag eligible, with no open E-4 readiness blocker (per master-plan F-8 closure note).

1. **Capability promotion PR** — 5× `spec.yml` `lifecycle_state: drafting → active` (the E-4-completion trigger; verify trace/runbook/evidence per cap; owner-confirm mcp-governance caveat). *This is the soak-gated step.*
2. **F-7 cluster amend** — batch the Stage-F M-FU items + the cumulative §7 governance insights (see §5).
3. **G26–G28 conditional + EVAL placeholders** — per the master-plan `phase_progress.M4.F` definition ("G26-G28 conditional + EVAL placeholders + F-7/F-8 closure; F-6 dropped per A-3 R-2 verdict").
4. **M4 closure update** — flip `phase_progress.M4.E → completed`, `M4.F → completed`, `M4: overall → completed`.
5. **Tag** `phase-m4-complete` (after the full test suite is green).
6. **Rollover** remaining items → M5 / M6 (see §5).

## §5 Remaining-work disposition (verified)

### Stage F (F-7 cluster amend)
- `M4-FU-BODY-SHA256-DOCSTRING-CLARIFY`
- `M4-FU-V4-MODE-B-CLEANUP`
- `M4-FU-OUTLINE-STAGE-B-WORDING-REFRAME`
- `M4-FU-DOCSTRING-DRIFT-DETECTOR` (~150-300 line detector + ci.yml integration)
- `M4-FU-G22-BDD-HELPERS-CONSOLIDATE` (post-Stage-E paired-edit consolidation; drift-guard test enforces parity meanwhile)

### M5 (archive ceremony — ~2 wk, 5 sub-PRs + 1 independent)
- **Archive ceremony (5 sub-PRs)**: old tri-track STANDARDs → `archive/rule/` (+ archive.yml + TOMBSTONE); 9 deprecated ADRs → `archive/decisions/superseded/`; 30 active ADRs → `decisions/`; `docs/runbook/` → capability runbooks; `docs/assessments/` → capability evidence; `docs/infrastructure/git|mcp/` → policies/capability; **`infra/docker/` → `docker/`** (ADR-026; the only source/infra path move allowed per §7); `docs/INDEX.md` → redirect map.
- **`M5-FU-TEMPLATE-ALIGN`** (independent small PR): align `sdd/templates/contracts/` with M2 adapter-doc evolution (5 known drifts: `skills[]` collection, `frontmatter_freeze`, `schema_compliance`, `namespace_pattern`, `description_hash`).
- **3 M5-deferred carries**: `M4-FU-BODY-SHA256-CANONICAL-REFACTOR` ⚠ (disposition row says M5; Cat-Triage says "M6 Horizon" — **resolve at M5 startup**), `M4-FU-V4-MODE-B-IMPL` (likely WITHDRAW), `M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER`.
- **M5 risks**: R-G1 (dir-move ref breakage → grep + redirect map + G14/G15 blocking), R-G5 (archive misread → ai_visibility + G17 + TOMBSTONE).

### M6 (~3-4 wk)
- CLAUDE.md root slim ≤150 lines (**force-retain** 4 项必停 + Codex Status + archive rules; R-G4 → ≥5 AI-task case studies at M6 end).
- 8 adapter gates → all BLOCKING.
- **G23** flip → BLOCKING + curate `tasks.md` `tdd.test_list` across the 5 critical/high tasks (M-FU#9).
- **G20** (bdd-step-coverage) — deferred to M5+/M6; **still has no validator** (`check_bdd_step_coverage.py` absent) → implement + flip, or explicitly defer post-refactor with rationale (do not leave silently unscoped).
- EVAL Phase-2 baseline PASS; 4 `mj-agent-evidence-*` skills; first metrics report (capability# / contract# / evidence-coverage / HITL-frequency); full test suite (unit+contracts+bdd+tdd+integration+smoke) green; `phase-m6-complete` tag.

## §6 Non-goals (this PR / E-4-PR10)

- No capability `lifecycle_state` promotion (held for soak).
- No `phase_progress` flip; no `phase-m4-complete` / `phase-m4-stage-e-alpha-prime-complete` tag.
- No F-7 cluster execution; no M5/M6 work.
- No CI / contract / 必停 / runtime change. Docs-only.

> Codex invocation: NONE
