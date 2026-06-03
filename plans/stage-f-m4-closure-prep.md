---
type: planning-aid
slug: stage-f-m4-closure-prep
summary: Stage F (M4 closure) — drafted as prep during the E-4 soak window (E-4-PR10), then EXECUTED in E-4-PR11 (2026-06-03). Records the soak EARLY-ACCEPT (run-based criterion + owner risk acceptance; calendar window waived), the executed closure (4/5 capabilities promoted drafting->active; mcp-server-governance held -> M4-FU-MCP-GOV-PROMOTION-DEFER; phase_progress.M4 E/F/overall -> completed; phase-m4-complete tag applied post-merge), and the remaining-work disposition (F-7 polish/code cluster descoped from M4 -> post-M4 tail/M5; G26-G28 -> M6).
owner: ranzuozhou
created: 2026-06-03
updated: 2026-06-03
state: active
track: shared
related_m_fu:
  - "M-FU#9 — M4-FU-G23-TASKS-CURATION-SURFACE (→ M6)"
  - "F-7 cluster — DOCSTRING-CLARIFY / V4-MODE-B-CLEANUP / OUTLINE-WORDING / DOCSTRING-DRIFT-DETECTOR / G22-BDD-HELPERS-CONSOLIDATE (descoped from M4 → post-M4 tail / M5)"
  - "M4-FU-MCP-GOV-PROMOTION-DEFER — mcp-server-governance drafting→active deferred (E-4-PR11; owner caveat-accept OR @risk:high|critical coverage)"
companion_docs:
  - plans/[PLAN]_spec_anchored_refactor.md (master plan; phase_progress.M4.E/F + §M4-FU Registry)
  - plans/stage-e-alpha-prime-e-4-soak.md (E-4 soak tracker + capability promotion preflight)
---

# Stage F — M4 Closure Prep (drafted during E-4 soak)

> **✅ EXECUTED (E-4-PR11; 2026-06-03).** This started as a prep doc; the closure it planned
> has now been executed. Owner early-accepted the G21/G22 soak on a **run-based criterion**
> (10 clean blocking-runs #200-#209 + negative-test gate-block verification; calendar window
> waived) → **4/5 capabilities promoted drafting→active** + `phase_progress.M4` flipped completed
> (`phase-m4-complete` tag applied post-merge). `mcp-server-governance` held → `M4-FU-MCP-GOV-PROMOTION-DEFER`.
> Sections below are retained as the executed plan of record.

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

## §2 E-4 completion blockers — ✅ ALL RESOLVED (E-4-PR11; 2026-06-03)

1. ~~G21/G22 soak window NOT elapsed~~ → **resolved via run-based early-accept** (owner re-based R-13-6's calendar criterion to N clean blocking-runs): 10 clean runs #200-#209 (0 FP / 0 real-violation) + a negative test proving the gate blocks on a real violation (broke 1 runbook 4-field → G21+G22 both exit 1; restored clean). Calendar window waived (auditable owner risk acceptance).
2. ~~5 pilots still `drafting`~~ → **4/5 promoted** drafting→active (safe-sql / biz-catalog / llm-provider / docker-compose; G8 4P/0W/0F/1SKIP; INDEX regenerated). `mcp-server-governance` **held** (medium-only caveat NOT accepted this round) → tracked `M4-FU-MCP-GOV-PROMOTION-DEFER`; not blocking M4 (it's a follow-up).
3. ~~tag not eligible~~ → **`phase-m4-complete` applied post-merge** (Action-N-2 trigger fired on the run-based early-accept).

## §3 Soak-wait plan (option 1) — ⛔ SUPERSEDED by run-based early-accept (E-4-PR11)

- **Window start**: 2026-06-02 (#199 flip merged).
- **Criterion** (R-13-6): 0 FAIL across G21+G22 (+G24) over a 1–2 wk CI-run window; monitor CI run history; M-FU on any FAIL surge.
- **Estimated unblock**: 2026-06-09 (1 wk, earliest) → 2026-06-16 (2 wk).
- **Promotion fires when**: soak observed clean **AND** `mcp-server-governance` medium-only caveat owner-confirmed.
- **Decision: hold** *(superseded 2026-06-03)* — the explicit owner override anticipated here did occur: owner re-based the criterion to run-based + accepted the risk (see banner + soak tracker "Soak Early-Accept"). Promotion proceeded without waiting for the calendar window.

## §4 Stage F closure sequence — ✅ EXECUTED (E-4-PR11; 2026-06-03)

> Entry gate (as originally planned) = soak observed clean + **all 5** capabilities promoted + `phase-m4-stage-e-alpha-prime-complete` tag eligible.
>
> **Gate actually applied (E-4-PR11; superseded the planned gate):** soak **EARLY-ACCEPTED on run-based criterion** (owner risk acceptance; calendar window waived) + **4/5** capabilities promoted (mcp-server-governance held → `M4-FU-MCP-GOV-PROMOTION-DEFER`; a follow-up, not M4-blocking) + `phase-m4-complete` tag deferred post-merge. The `phase-m4-stage-e-alpha-prime-complete` sub-tag is **subsumed by `phase-m4-complete`** (not separately applied).

1. **Capability promotion** ✅ — **4/5** `spec.yml` `lifecycle_state: drafting → active` (safe-sql / biz-catalog / llm-provider / docker-compose; trace/runbook/evidence verified per cap; G8 4P/0W/0F/1SKIP). mcp-server-governance **held** (medium-only caveat NOT accepted) → `M4-FU-MCP-GOV-PROMOTION-DEFER`. *This was the soak-gated step — unblocked by the run-based early-accept.*
2. **F-7 cluster amend** — batch the Stage-F M-FU items + the cumulative §7 governance insights (see §5).
3. **G26–G28 conditional + EVAL placeholders** — per the master-plan `phase_progress.M4.F` definition ("G26-G28 conditional + EVAL placeholders + F-7/F-8 closure; F-6 dropped per A-3 R-2 verdict").
4. **M4 closure update** — flip `phase_progress.M4.E → completed`, `M4.F → completed`, `M4: overall → completed`.
5. **Tag** `phase-m4-complete` (after the full test suite is green).
6. **Rollover** remaining items → M5 / M6 (see §5).

## §5 Remaining-work disposition (verified)

### F-7 cluster — ⏩ DESCOPED from M4 → post-M4 tail / M5 (NOT executed in E-4-PR11)

> These are M4-FU follow-ups (polish + one ~150-300-line code deliverable), not M4-blocking deliverables. The E-4-PR11 closure captured the F-7 **governance insights** (see master plan F-7 note) but descoped the items below to post-M4/M5. Registry-of-record: master plan Action-N-2 SoT table.

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

## §6 Non-goals (E-4-PR10 prep PR only — NOT the E-4-PR11 closure, which executed §4)

- *(As of E-4-PR10 prep — ALL SUPERSEDED by the E-4-PR11 closure; see banner)* No capability `lifecycle_state` promotion (held for soak).
- *(superseded by E-4-PR11)* No `phase_progress` flip; no `phase-m4-complete` / `phase-m4-stage-e-alpha-prime-complete` tag.
- No F-7 cluster execution; no M5/M6 work.
- No CI / contract / 必停 / runtime change. Docs-only.

> Codex invocation: NONE
