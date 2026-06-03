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

- E-0a (G21 evidence predicate + trace/spec amend): done via #195
- E-0b runbook justification curation: done via #198
- E-3 (G24 bugfix-workflow readiness): done via #194
- E-1/E-2 combined BLOCKING flip: done via #199
- E-4 soak: active (EVAL #201 · M3 carry-over #202/#203 · Action-N-2 #204 · promotion-preflight #205 · F8 #206 · ADR-025 reconcile E-4-PR8)
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

### G21/G22 Blocking Soak — 🟡 checkpoint 2026-06-02 (E-4-PR6); window NOT yet elapsed

**Soak Checkpoint (E-4-PR6)**:
- checkpoint_date: 2026-06-02
- observed_since: 2026-06-02 (#199 flip merged same day)
- latest_develop_commit: `626b00c` (#204)
- G21 strict: 15P/0W/0F aggregate — per-cap: safe-sql 6P / biz-catalog 3P / llm-provider 3P / docker-compose 3P / mcp-governance SKIP (medium-only)
- G22 strict: 15P/0W/0F aggregate (same per-cap split)
- early signal: 5 PRs (#200-#204) merged under BLOCKING gates since the flip — **0 false-positives, 0 real violations**
- false_positive_observed: no
- real_violation_observed: no
- **Decision: continue soak before promotion** — the 1–2 wk calendar window has NOT elapsed (flip landed same day); early signal is clean but insufficient for the window criterion.

- [x] Confirm new PRs execute G21/G22 as blocking checks (#200-#204 ✓)
- [x] Confirm no false-positive from G21 (0 across #200-#204)
- [x] Confirm no false-positive from G22 (0 across #200-#204)
- [ ] If false-positive appears, record capability / scenario / validator message (none so far)
- [ ] If real violation appears, confirm CI blocks as intended (none so far)
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

- [x] Prepare promotion for 5 pilot capabilities from drafting to active — **preflight done (E-4-PR6); NOT promoted this PR**
- [x] Do not promote until EVAL baseline and soak status are recorded — EVAL ✅ #201; soak checkpoint recorded above (window not elapsed → hold)
- [x] Confirm trace / runbook / evidence consistency before promotion — all 5 have the full 9-artifact suite (spec / req / design / tasks / runbook / trace + contracts incl. behavior.feature + evidence subdirs)

**Capability Promotion Readiness Preflight (E-4-PR6; 2026-06-02)** — readiness only; **no `lifecycle_state` changed**:

| Capability | Current | Artifacts | G21/G22 | Readiness | Blocker / Next |
|---|---|---|---|---|---|
| `data-agent.safe-sql` | drafting | full ✓ | 6P/0W/0F | **ready · wait-soak** | none; promote after soak window |
| `data-agent.biz-catalog` | drafting | full ✓ | 3P/0W/0F | **ready · wait-soak** | none; promote after soak window |
| `data-agent.llm-provider` | drafting | full ✓ | 3P/0W/0F | **ready · wait-soak** | none; promote after soak window |
| `infrastructure.docker-compose` | drafting | full ✓ | 3P/0W/0F | **ready · wait-soak** | none; promote after soak window |
| `infrastructure.mcp-server-governance` | drafting | full ✓ | SKIP (medium-only) | **ready · wait-soak** ⚠ | no G21/G22 coverage (scenarios @risk:medium); readiness rests on its own contracts (mcp-server-inventory) + evidence — owner confirm acceptable before promotion |

Promotion rule: separate PR; gated on a **clean soak window elapsed** + no readiness blocker. mcp-governance owner should confirm the medium-only (no-G21/G22-coverage) caveat is acceptable.

### Stage F Preparation

- [ ] Prepare M4 closure update
- [ ] Prepare `phase-m4-complete` tag only after E-4 is complete
