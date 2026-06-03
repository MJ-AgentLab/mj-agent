---
type: planning-aid
slug: stage-e-alpha-prime-e-4-soak
summary: E-4 soak kickoff tracker, opened after the G21/G22 combined BLOCKING flip landed (#199). Opens the 1-2 week soak observation window for G21/G22 blocking mode and tracks the remaining E-4 workstreams (ADR-024 EVAL baseline, Action-N-2 M-FU registry batch, M3 carry-over closure, 5 pilot capability state promotion, Stage F closure prep) as a checklist. Tracker/status only — the opening PR makes no code / CI / validator / test changes.
owner: ranzuozhou
created: 2026-06-02
updated: 2026-06-03
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

- E-0a (G21 evidence predicate + trace/spec amend): done via #195
- E-0b runbook justification curation: done via #198
- E-3 (G24 bugfix-workflow readiness): done via #194
- E-1/E-2 combined BLOCKING flip: done via #199
- E-4 soak: ✅ EARLY-ACCEPTED on run-based criterion 2026-06-03 (EVAL #201 · M3 carry-over #202/#203 · Action-N-2 #204 · promotion-preflight #205 · F8 #206 · ADR-025 reconcile #207/#208 · Stage F prep #209 · M4 closure E-4-PR11)
- Stage F closure: ✅ done (E-4-PR11; 4/5 capabilities promoted drafting→active; mcp-gov held → M4-FU-MCP-GOV-PROMOTION-DEFER; `phase_progress.M4` completed)
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
- No `phase-m4-complete` tag yet *(scoped to this soak-kickoff PR #200; the tag is applied post-merge of the E-4-PR11 closure — see "Stage F Preparation → EXECUTED" below)*
- No CI gate toggle
- No validator severity rewrite
- No source code changes
- No test changes
- No 4-stop-surface changes

## E-4 Soak Checklist

Observation window: 1–2 weeks

### G21/G22 Blocking Soak — ✅ EARLY-ACCEPTED 2026-06-03 (E-4-PR11; run-based criterion + owner risk acceptance)

**Soak Checkpoint (E-4-PR6)**:
- checkpoint_date: 2026-06-02
- observed_since: 2026-06-02 (#199 flip merged same day)
- latest_develop_commit: `626b00c` (#204)
- G21 strict: 15P/0W/0F aggregate — per-cap: safe-sql 6P / biz-catalog 3P / llm-provider 3P / docker-compose 3P / mcp-governance SKIP (medium-only)
- G22 strict: 15P/0W/0F aggregate (same per-cap split)
- early signal: 5 PRs (#200-#204) merged under BLOCKING gates since the flip — **0 false-positives, 0 real violations**
- false_positive_observed: no
- real_violation_observed: no
- **Decision (E-4-PR6, superseded): continue soak** — at the 2026-06-02 checkpoint the 1–2 wk calendar window had not elapsed. **Superseded by the E-4-PR11 early-accept below.**

**Soak Early-Accept (E-4-PR11; 2026-06-03)** — owner re-based the criterion from calendar to **run-based**:
- decision: **early-accept on run-based criterion + owner risk acceptance** (calendar window waived)
- run-based evidence: **N≥5 clean post-flip blocking-runs** — #200-#204 = 5 genuine post-flip CI runs (per the E-4-PR6 checkpoint above) + #205-#209 = same-workstream closure-prep PRs (weaker observations; #209 is the prep doc itself), **all clean** (0 false-positives / 0 real violations across all). G24 is branch-conditional (SKIP on these non-bugfix `documentation/*` PRs → no G24 soak signal expected; R-13-6's "+G24" is satisfied by the #194 fire-path validation, not these runs).
- **2 negative tests (active gate-block verification)** proving the gate blocks on real violations:
  - (a) **runbook-fallback path** (R-15-1 coupling): broke safe-sql runbook 4-field (`预计时间` ×7) → G21 **9P/6W/0F exit 1** + G22 **9P/6W/0F exit 1** (the same 6 scenarios flip in both gates); restored → 15P/0W/0F exit 0.
  - (b) **TAG hard-FAIL path**: dropped one `@REQ-NNN` tag from a critical scenario in safe-sql `behavior.feature` → G21 **14P/0W/1F exit 1** (hard FAIL, not WARN); restored → 15P/0W/0F exit 0.
  - both restored clean (git clean); together they cover the soft (justification regression; `--strict` WARN→exit 1) AND hard (tag-binding regression; FAIL) blocking paths.
- rationale: R-13-6's 1–2 wk *calendar* window is a self-imposed governance criterion, not a hard technical gate; re-based to a **run-based** criterion (N≥5 clean blocking-runs) — satisfied; tradeoff (time-coverage → speed) accepted, risk low (clean signal + simple `--strict` gate on a stable 0W baseline + verified blocking). **Provenance**: owner authorized the re-base + risk acceptance in-session 2026-06-03 (this E-4-PR11 closure PR = recorded artifact, reviewed at merge).

- [x] Confirm new PRs execute G21/G22 as blocking checks (#200-#204 ✓)
- [x] Confirm no false-positive from G21 (0 across #200-#204)
- [x] Confirm no false-positive from G22 (0 across #200-#204)
- [ ] If false-positive appears, record capability / scenario / validator message (none so far)
- [x] If real violation appears, confirm CI blocks as intended — **actively verified via negative test (E-4-PR11)**: injected runbook violation → G21+G22 both exit 1 (block); restored clean
- [x] Confirm `--strict` path remains sufficient (15P/0W/0F under `--strict`)
- [x] Do not reclassify validator severity (none reclassified)

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

### Soak-period cleanup — ✅ F8-SKILL-STEP-8 completed 2026-06-02 (E-4-PR7)

- `M4-FU-F8-SKILL-STEP-8-WORKTREE-SYNC-FIX` → **completed**. Finding: the recipe is already worktree-safe — post-merge Step 8 delegates to `/mj-agent-git-sync`, whose Step 4 uses `git merge origin/develop` (not bare-repo `update-ref`); the #185 incident was ad-hoc, not a recipe bug. Resolution: added a `#185-lesson` worktree-safe guard note to `.claude/skills/mj-agent-flow-post-merge/SKILL.md` Step 8 (in-tree workflow skill — NOT the 必停 `src/mj_agent/skills/`; NOT content_hash-locked).
- `11-FILE-ADR-025-RECONCILE`: ✅ done (E-4-PR8/#207 4 free refs + E-4-PR9 6 locked SKILLs reconciled & re-frozen; see below).

### Soak-period cleanup — ✅ ADR-025 ref reconcile complete (E-4-PR8/#207 + E-4-PR9; 2026-06-03)

- `M4-FU-11-FILE-ADR-025-RECONCILE` → **partially done**. Scoped via a verification workflow (adversarial lock/必停 classification of all 11 candidate files).
  - **Fixed (4 free refs)**: `src/mj_agent/llm.py` L3 + `src/mj_agent/config.py` L62 + `.env.example` L54 (ADR-025 → ADR-027); `infra/docker/docker-compose.mj-agent.yml` L2 (ADR-025 → ADR-026).
  - **N/A**: `src/mj_agent/tools/sql/execute.py` — has **no** ADR reference (the registry assumption was wrong); inserting one is authoring, not a stale-fix → skipped.
  - **✅ Resolved in E-4-PR9 (6 content_hash-locked infra SKILLs)**: llm-endpoint-probe / storage-stack / studio-probe / docker-compose / env-setup / env-teardown — 15 stale ADR-025 refs → ADR-026/027/028 (LLM→027, compose→026, MCP→028); `claude-skill.contract.yml` re-frozen (6 `body_content_hash` + 3 `description_hash` + `frozen_at` 2026-06-03; V4 34P/0W/0F; all 6 hashes verified vs live files); `mcp-server-trust-posture-change` HITL declared (satisfied at PR review/merge).
- Also fixed 3 tracker-drift items surfaced by the #200-#206 consistency audit (master-plan Action-N-2 "Outcome" prose + E-4 progress bullet re F8; this tracker's M3 "one active item" stale wording).

### M3 Carry-over Closure — ✅ triaged 2026-06-02 (E-4-PR3)

- [x] Review `m3_fu_skill_5segment_normalize` → **closed (resolved by E-4-PR4)**
- [x] Review `m3_fu_v4_skills_complete` → **closed (superseded by #183)**
- [x] Decide each: closed / active / obsolete

| Carry-over | Decision | Rationale | Follow-up |
|---|---|---|---|
| `m3_fu_v4_skills_complete` | **closed** (`state: completed`) | All AC met & verified @ `a457cd2`: 10 SKILLs carry `Do not use for:`; V4 34P/0W/0F; V4 ci.yml BLOCKING "per M3-FU-V4-SKILLS-COMPLETE" (executed #183 / M4-A). | none |
| `m3_fu_skill_5segment_normalize` | **closed** (`state: completed`) | Resolved by E-4-PR4: `sdd/adapters/runtime-skill.md` `body_section_heads` now documents `## Related` as the allowed 6th section, aligning the adapter doc with the contract-frozen 6-section shape (option B). No SKILL.md / contract / 必停 touch. | none |

- [x] No unresolved carry-over: both items closed (`v4-skills-complete` #183/#202; `5segment-normalize` #203/E-4-PR4); none dragged to M6.
- No Action-N-2 registry or capability-promotion changes in this PR.

### Capability State Promotion

- [x] Prepare promotion for 5 pilot capabilities from drafting to active — preflight #205; **4/5 promoted in E-4-PR11** (mcp-gov held → `M4-FU-MCP-GOV-PROMOTION-DEFER`)
- [x] Do not promote until EVAL baseline and soak status are recorded — EVAL ✅ #201; soak ✅ early-accepted (run-based + negative-test, above); G8 4P/0W/0F/1SKIP + INDEX regenerated post-promotion
- [x] Confirm trace / runbook / evidence consistency before promotion — all 5 have the full 9-artifact suite (spec / req / design / tasks / runbook / trace + contracts incl. behavior.feature + evidence subdirs)

**Capability Promotion Readiness Preflight (E-4-PR6) → EXECUTED (E-4-PR11; 2026-06-03)** — 4/5 promoted; `lifecycle_state` changed for the 4 covered caps:

| Capability | Current | Artifacts | G21/G22 | Readiness | Blocker / Next |
|---|---|---|---|---|---|
| `data-agent.safe-sql` | **active** | full ✓ | 6P/0W/0F | ✅ **promoted (E-4-PR11)** | done |
| `data-agent.biz-catalog` | **active** | full ✓ | 3P/0W/0F | ✅ **promoted (E-4-PR11)** | done |
| `data-agent.llm-provider` | **active** | full ✓ | 3P/0W/0F | ✅ **promoted (E-4-PR11)** | done |
| `infrastructure.docker-compose` | **active** | full ✓ | 3P/0W/0F | ✅ **promoted (E-4-PR11)** | done |
| `infrastructure.mcp-server-governance` | drafting | full ✓ | SKIP (medium-only) | ⏸ **held** → `M4-FU-MCP-GOV-PROMOTION-DEFER` | no G21/G22 coverage (scenarios @risk:medium); promote on owner caveat-accept OR added coverage |

Promotion (E-4-PR11): 4/5 promoted drafting→active under the run-based soak early-accept; G8 4P/0W/0F/1SKIP; `INDEX.auto.md` regenerated (G9 ✓). mcp-server-governance held — owner caveat-accept (medium-only) OR added @risk:high|critical coverage promotes it (tracked: `M4-FU-MCP-GOV-PROMOTION-DEFER`).

### Stage F Preparation → ✅ EXECUTED (E-4-PR11; 2026-06-03)

- [x] Prepare M4 closure update → drafted (#209): `plans/stage-f-m4-closure-prep.md`
- [x] **Stage F closure executed (E-4-PR11)**: 4/5 capabilities promoted; `phase_progress.M4.E/F/overall` → completed; F-7 cluster + remaining M4-FU roll forward (post-M4 tail / M5 / M6); G26-G28 → M6
- [x] `phase-m4-complete` tag — **applied post-merge** (after the closure PR merges + full test suite green)
- Soak-wait plan (option 1) **superseded**: owner early-accepted on run-based criterion 2026-06-03 (calendar window ~06-09→06-16 waived; see Soak Early-Accept above). `mcp-server-governance` promotion deferred (not blocking M4) → `M4-FU-MCP-GOV-PROMOTION-DEFER`.
