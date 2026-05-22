---
type: adr
domain: WORKFLOW
summary: establish 3-layer monitoring regime for ongoing `.claude/skills/` ADR-013 native 2-field schema compliance — validator gate (V4; M3 warning / M4 blocking) + PR template A12 prompt + 季度 A6 audit; reframes original M3-FU-CLAUDE-SKILL-ADR scope from "fix existing 34/34 markdown-body-only deviation" (premise empirically false per 03f1bc7 reverify) to "prevent future deviation"
owner: ranzuozhou
created: 2026-05-22
updated: 2026-05-22
state: draft
decision: proposed
track: engineering-workflow
tags:
  - adr
  - claude-code-skill
  - schema
  - monitoring
  - drift-prevention
  - adr-013
  - adr-016
---

# ADR 032: Claude Skill Schema Monitoring Regime

## Context

[[[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] established the native 2-field schema
(`name` + `description` only) for `.claude/skills/*/SKILL.md` files, distinct from
`src/mj_agent/skills/*/SKILL.md` (Agent_Side v1.0 §2 13-field schema).
[[[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] governs the `.claude/skills/` ecosystem
itself — naming (`mj-agent-<family>-<verb>`), 5 families (doc / flow / git / infra / runtime),
34 SKILLs target.

The M3-FU-CLAUDE-SKILL-ADR plan was originally registered (per `plans/[PLAN]_spec_anchored_refactor.md`
commit `3c9ce77`) under premise Q-A3: "34/34 SKILL markdown-body-only convention" — implying
all 34 SKILLs lacked ADR-013 frontmatter and needed normalization. Phase M2 Stage C batch 2
pre-outline reverify (commit `03f1bc7`) performed empirical full deep scan and established the
**opposite**: 34/34 SKILLs ARE ADR-013 native 2-field schema compliant (zero deviation).
The Q-A3 premise was categorically false (corroborated by M3-FU-V4-VALIDATOR-INVESTIGATE
which traced V4 validator's false "34/34 markdown-body-only" output to a yaml.safe_load
parser bug rather than actual SKILL content deviation; fix landed `a5614c4`).

The M3-FU-CLAUDE-SKILL-ADR scope was reframed (`f6290cc`): no longer "fix existing deviation"
— instead "prevent future deviation". Future SKILL additions or edits could violate ADR-013
intent (e.g., adding non-canonical frontmatter keys, drifting description format, breaking
namespace pattern) without a monitoring regime to catch it. This ADR defines that regime.

## Decision

A **3-layer monitoring regime** for `.claude/skills/` ADR-013 schema compliance:

### Layer 1 — V4 validator gate (`scripts/sdd/check_claude_skill_contracts.py`)

- Validates each `.claude/skills/*/SKILL.md` against ADR-013 schema: frontmatter present
  + only `name` + `description` keys + `description` ≥ 200 chars + `name` matches ADR-016
  namespace pattern + body present.
- Current state (Stage C `02b1cc8`): warning mode (`continue-on-error: true`) because of
  6 real WARN findings (genuine ADR-013 reverse-trigger gaps in mj-agent-infra-* +
  mj-agent-runtime-* SKILLs; tracked separately as M3-FU-V4-SKILLS-COMPLETE).
- Future state (M4 per `sdd/gates.md §5` + M3-FU-V4-SKILLS-COMPLETE resolution):
  blocking mode after 10 SKILL gap-fills.
- Drift coverage: schema-level deviations caught at PR-time CI.

### Layer 2 — PR template A12 prompt (existing per Meta v2.1 §7.7)

- A12 PR gate in tri-track checklist (Engineering-Workflow track) requires
  `.claude/skills/<name>/SKILL.md` modifications to be reviewed against ADR-013 + ADR-016.
- Reviewer self-checklist explicitly prompts for: native 2-field schema preserved + `name`
  matches dir + `description` ≥ 200 + reverse-trigger present + body has `## Overview` +
  `## Workflow`.
- Drift coverage: human-readable review at PR-time; catches semantic drift (e.g.,
  trigger language degradation) that schema validator can't.

### Layer 3 — A6 quarterly audit (per `evidence/ai-context-audit/SCHEMA.md`)

- Each cycle's audit entry includes `.claude/skills/` full inventory (34 SKILLs + per-SKILL
  canonical regex-strip body hash). Future cycles diff against prior `content_hash_snapshot`
  to surface drift not caught at PR-time.
- 2026-Q2 baseline established `871f889` (Stage D D-1c). Quarterly cadence; manual +
  reminder (per SCHEMA.md §3).
- Drift coverage: longitudinal drift detection across PR-time gates; catches gradual
  erosion that per-PR review misses.

Three layers are **defense-in-depth**: each catches a different drift class (schema /
semantic / longitudinal). All three must be maintained for the regime to function.

## Consequences

### Positive

- Multi-layer drift detection (schema validator + PR review + periodic audit).
- Builds on existing infrastructure: V4 validator (Stage A `f3c9852`...`a5614c4`) +
  Meta v2.1 §7.7 A12 PR template (existing) + A6 audit framework (Stage D D-1c `871f889`).
- Quarterly audit catches the "frog-boiling" pattern where individually OK changes
  accumulate to spec drift.
- Explicit drift-prevention regime replaces ad-hoc reactivity.

### Negative

- 3 maintenance surfaces (validator + PR template + audit) instead of 1 — increases
  governance overhead.
- A6 audit requires per-quarter manual action; lapse policy mitigates but doesn't
  eliminate risk.
- Validator (Layer 1) currently has 6 real WARN findings deferred to M3-FU-V4-SKILLS-COMPLETE;
  Layer 1 not yet fully effective until those resolve.

### Neutral

- Depends on V4 validator promotion to blocking (M4 per gate schedule). Until M4, Layer
  1 surfaces warnings only.
- A6 cycle ownership requires manual reminder (per SCHEMA.md §3 `M-FU-AI-AUDIT-<cycle>`
  pattern) — fragile if M-FU plan ownership lapses.

## Alternatives Considered

### Alt-A: Single-layer (validator only)

Rely solely on V4 validator. Rejected — schema validator catches structural drift but
misses semantic drift (e.g., a description that meets ≥200 chars but is degraded /
unclear / out-of-date). Need human review (Layer 2) + longitudinal scan (Layer 3).

### Alt-B: Manual review only (no automation)

Rely on PR reviewer to enforce ADR-013 + ADR-016 by hand. Rejected as un-scalable —
review fatigue + reviewer turnover degrade enforcement over time; schema validator
provides mechanical guarantee.

### Alt-C: Auto-fix on detection

V4 validator or A6 audit auto-corrects deviations. Rejected as too aggressive —
silent mutation of LLM-facing trigger content has high blast radius; could degrade
SKILL effectiveness without human review.

## References

- [[[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] — native 2-field schema baseline
- [[[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] — `.claude/skills/` ecosystem
  governance (naming / families / lifecycle)
- `decisions/ADR-031_Spec_Anchored_Refactor.md` — M1 framework; 7 adapter enablement list
  includes claude-code-skill adapter
- `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`
  — Layer 1 freeze anchor for the 6 mj-agent-infra-* SKILLs (description_hash +
  body_content_hash; canonical regex-strip algorithm)
- `scripts/sdd/check_claude_skill_contracts.py` — Layer 1 V4 validator implementation
  (Stage A `f3c9852` + parser fix `a5614c4`)
- `policies/ai-agent.md §4` — Canonical 10-Enum (includes `mcp-server-trust-posture-change`
  for `.mcp.json` changes; SKILL changes covered by `runtime-skill-content-change` enum)
- `policies/ai-agent.md §7` — Pre-flight Verification Discipline (Stage D `4a59dc5`;
  parent rule for spec-vs-reality verification)
- `evidence/ai-context-audit/SCHEMA.md` — Layer 3 audit framework spec (Stage D `871f889`)
- `evidence/ai-context-audit/2026-Q2.md` — first baseline cycle (Stage D `871f889`)
- M3-FU-V4-SKILLS-COMPLETE plan — blocking Layer 1 promotion to BLOCKING (6 infra +
  4 runtime SKILL gap-fill)

## Decision Date / Authors

- Date: 2026-05-22
- Authors: ranzuozhou (HITL-supervised); ai-agent (claude-opus-4-7 via claude-code) drafted
- Promote draft → accepted: at next HITL Gate-3 review after Layer 1 promotion to blocking
  (M4 work; tracked via M3-FU-V4-SKILLS-COMPLETE landing + V4 ci.yml `continue-on-error: false`
  flip)
