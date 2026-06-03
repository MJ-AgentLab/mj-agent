---
type: ai-context-investigation
subtype: readiness-eval
investigation: a3-a2-hook-improver-body-readiness
auditor: "ai-agent (claude-opus-4-7 via claude-code; HITL-supervised by ranzuozhou)"
scope:
  - adr-024-a8-a11-waiver
  - eval-framework-phase-2-readiness
  - a2-hook-improver-body-m5-defer
phase: M4-Stage-A-unit-A-3
date: 2026-05-22
findings_summary: "R-2 verdict (defer M5+); 0/4 ADR-024 §A8/A11 prereq fully met; Episode #A3-6 (5 SKILLs baseline drift to 9) + #A3-7 (Main条款 4 done Phase D-3 vs Waiver Prereq #4 implementation split) clarify Phase E closure roadmap"
related_episodes:
  - "#A3-1 ADR-024 §A8/A11 prereq verbatim confirmed (L78-83)"
  - "#A3-2 docs/evaluation/ empty/absent (Prereq #1 NOT MET)"
  - "#A3-3 eval_references only system.md placeholder (Prereq #3 NOT MET)"
  - "#A3-4 check_frontmatter.py impl status resolved via split per #A3-7"
  - "#A3-5 TEMPLATE_EVAL.md exists with ADR-024 §4.2 微差 (Phase E align scope; non-blocker)"
  - "#A3-6 ADR-024 '5 SKILLs' baseline drift (9 current vs 5 spec; 4 new since 2026-05-09)"
  - "#A3-7 ADR-024 Main条款 4 (EVAL type-conditional; DONE Phase D-3) vs Waiver Prereq #4 (SKILL/PROMPT enforcement; NOT IMPLEMENTED) split"
parent_artifacts:
  - "A-1 brief §0 Episode #3 (V4 Mode B docstring-only finding; commit 683c700)"
  - "A-2 commit 501cae8 (BODY-SHA256 + V4 Mode B joint investigation report)"
  - "Phase M4 outline §1 Stage A unit A-3 entry (Gate-1 disposition; default reframe M5-FU per Gate-1 B-3)"
---

# A-3 Readiness Eval — A2-HOOK-IMPROVER-BODY Phase E Prerequisite Status

## §1 Goal + Scope

**Phase M4 Stage A Unit A-3** — read-only readiness eval of ADR-024 §A8/A11 transitional waiver 4 prerequisites; determine R-X verdict (R-1 unblock OR R-2 defer M5+) per Gate-1 B-3 disposition default。

**Anchored sources**: ADR-024 §A8/A11 prereq list (L78-83) + Main条款 4 EVAL type-conditional spec (L85-94); A-1 brief §0 Episode #3 (V4 Mode B finding; bundled disposition with this A-3 readiness eval per Gate-1); `.claude/hooks/stop-claude-md-improver/` (target hook for A2-HOOK-IMPROVER-BODY real logic; stub body lines 72-77 of on-stop.ps1)。

**Output**: this memo (1 new file at `evidence/ai-context-audit/2026-05-22_a3-readiness-eval.md`); NO fix to ADR / hook / check_frontmatter.py / SKILL / EVAL framework — verdict + disposition only。

## §2 4 Prereq Empirical Status

| # | Prereq | Empirical Evidence | State |
|---|---|---|---|
| #1 | docs/evaluation/ ≥ 3 active EVAL | Glob returns 0 files; directory empty/absent | ❌ NOT MET |
| #2 | EVAL runtime MVP (dataset / judges / metric / regression detection) | tests/eval/ has `__init__.py` (empty) + `golden_seed.jsonl` + 2 prototypes (`test_component_against_seed.py` + `test_golden_seed_schema.py`); 0 judges/metric/regression infra; 4 sub-class dirs absent | ❌ NOT MET |
| #3 | 5 SKILLs + 1 PROMPT `eval_references` (Option β baseline = 9 SKILLs + 1 PROMPT per Episode #A3-6) | Grep matches 0/9 in-source SKILLs; system.md L13 has `eval_references: []` placeholder (empty array, not real references) | ❌ NOT MET |
| #4 | check_frontmatter.py SKILL/PROMPT type-conditional A8/A11 校验 | Functional fixture: type:skill state:active missing eval_references → 0 violations (no enforcement); Main条款 4 EVAL type-conditional IS implemented but separate scope per Episode #A3-7 | ❌ NOT MET (Waiver scope; Main条款 4 EVAL impl bonus is separate concern) |

**Episode #A3-6 baseline note**: ADR-024 L25 "5 in-source SKILLs" wording stale; 4 new SKILLs added since ADR creation 2026-05-09 (biz-schema-exploration / mj-ddd-semantics / monthly-report / query-optimization)。Option β (current reality = 9 SKILLs + 1 PROMPT) used for verdict; L25 refresh = M5+ ADR amendment candidate。

## §3 R-2 Verdict + Rationale (4 Components; order 1→2→4→3)

**Verdict**: **R-2 (defer M5+)** empirically locked per Gate-1 B-3 default。0/4 fully met < 3/4 threshold。

### (1) Empirical evidence chain
4 prereq 全部 NOT MET via direct empirical verify (Glob + Grep + functional fixture)。No prereq is borderline; verdict unambiguous。

### (2) Episode #A3-7 implementation split
ADR-024 has 2 separate check_frontmatter.py requirements:
- **Main条款 4** (L85-94): EVAL type-specific fields enforcement (eval_kind / dataset_path / baseline_metric / baseline_value / regression_threshold for `type: eval` state:active) — **DONE Phase D-3** (functional fixture confirms 5 violations per spec)
- **Waiver Prereq #4** (L83): SKILL/PROMPT type-conditional eval_references enforcement — **NOT IMPLEMENTED** (functional fixture confirms 0 violations for type:skill state:active missing eval_references)

These are 2 separate scopes; both needed for full Phase E waiver closure。Phase E closure work for Prereq #4 ≈ ~10-20 lines extension to check_frontmatter.py (add `type_specific_required["skill"]` + `["prompt"]` entries with `eval_references` requirement)。

### (4) Cross-phase continuity recognition
Phase D-3 (M3 期间) 已 lay groundwork — Main条款 4 EVAL type-conditional check_frontmatter.py implementation IS done。Phase E closure 不是 "from scratch defer" 而是 "Phase D-3 done partial; Phase E closes remaining 4 work items where Prereq #4 是 well-scoped sub-implementation"。A-3 verdict R-2 reflects this realistic dependency mapping。

### (3) F-6 drop traceability
A-3 R-2 verdict → **Phase M4 outline §1 Stage F units count: 8 → 7** (F-6 A2-HOOK-IMPROVER-BODY 真逻辑 dropped from M4 scope)。F-6 work reframed as M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER registry candidate (§4 below)。F-7 closure unit cluster amend records F-6 drop + 7 Episode candidates (#A3-1...#A3-7)。F-8 master plan update propagates M4-FU registry entry。

## §4 Disposition + M4-FU Registry Candidate (6 Facets + Phase E Cross-link)

**M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER** registry entry scope:

| Facet | Detail |
|---|---|
| Replacement target | `.claude/hooks/stop-claude-md-improver/on-stop.ps1` lines 72-77 (stub body: Write-Host x2 + exit 0) |
| Reuse (intact) | Lines 22-70 defense layer: bypass双通道 + WriteAllowlist (1 pattern) + WriteDenylist (15 patterns incl. 10 必停 surface) + Test-PathAllowed function (Deny优先 + Allow + closed-world default deny) |
| Output convention | `evidence/ai-context-audit/<YYYY-MM-DD>_session_<id>_proposed_claude_md_update.md` (per Allowlist + A6 audit cycle naming align) |
| Invariants | R-G21 mitigation (per spec-anchored-calm-lampson.md §10): draft only; NO auto-write/auto-commit/auto-Edit CLAUDE.md; NO read archive/; user manual review + apply via mj-agent-doc-sync skill |
| Pre-condition dependency | Phase E closure of ADR-024 §A8/A11 waiver — Prereq #1 + #2 + #3 (per Episode #A3-6 baseline = 10 items) + #4 (per Episode #A3-7 split = ~10-20 lines extension); Main条款 4 already done Phase D-3 |
| Scope estimate | ~100-200 lines real-logic substitution (session signal analysis + draft generator); depends on EVAL runtime maturity for trace/judge consumption; possible ADR amendment for governance regime sync; integration tests ~30-50 lines additional |

**Phase E closure roadmap cross-link**: M4-FU-A2-HOOK-IMPROVER-BODY-M5-DEFER unblocking depends on Phase E (per master plan §Phase M5+) closing ADR-024 §A8/A11 waiver — Prereq #1 (`docs/evaluation/` ≥ 3 active EVAL) + Prereq #2 (EVAL runtime MVP with dataset / judges / metric / regression detection) + Prereq #3 (`eval_references` 填充 10 items per Option β baseline) + Prereq #4 SKILL/PROMPT type-conditional enforcement extension (~10-20 lines per Episode #A3-7 split)。

## §5 Cross-references

- ADR-024 §A8/A11: `decisions/ADR-024_Eval_Framework_Spec.md#L78-L83` 4 prereq verbatim; `#L85-L94` Main条款 4 EVAL type-conditional spec; `#L25` "5 SKILLs" baseline (Episode #A3-6 candidate refresh)
- A-1 brief §0 Episode #3 — V4 Mode B docstring-only finding; commit `683c700` body
- A-2 commit `501cae8` — BODY-SHA256 + V4 Mode B joint investigation report (Episode #2-1...#2-9 originator; co-pattern frontmatter Option a)
- `.claude/hooks/stop-claude-md-improver/on-stop.ps1#L22-L70` defense layer + `#L72-L77` stub body; Stage D D-1b commit `0d086c2` (defense layer landing) + commit `550e46b` (original draft-producer design)
- `scripts/check_frontmatter.py#L122-L144` Main条款 4 EVAL type-conditional implementation (Phase D-3 done; Episode #A3-7)
- Gate-1 B-3 disposition: Phase M4 outline §1 Stage A A-3 entry (default reframe M5-FU on R-2 verdict)
- `spec-anchored-calm-lampson.md §10 R-G21` — Stop hook 自改失控 mitigation rationale
- Phase M4 outline §1 Stage F units count impact: 8 → 7 (F-6 dropped per A-3 R-2 verdict; reframed M4-FU registry candidate)
- 7 Episode candidates (#A3-1...#A3-7) accumulate to Stage F F-7 closure unit cluster amend (alongside A-1 3 + A-2 9 = 19 candidates total)

---

> **Investigation type**: ad-hoc readiness eval; reuses A-2 Option a-modified frontmatter convention (`type: ai-context-investigation` + new `subtype: readiness-eval` field); does NOT require SCHEMA.md amendment (subtype field extension within existing type per A-2 Episode #2-9 already-proposed M5+ amendment scope)。
