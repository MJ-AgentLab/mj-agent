---
type: plan
slug: m3-fu-v4-skills-complete
summary: M3 follow-up plan — add "Do not use for:" reverse-trigger block to 6 mj-agent-infra-* SKILL.md files (the 6 real WARN findings V4 surfaces post M3-FU-V4-VALIDATOR-INVESTIGATE parser fix); cross-capability change with cascading content_hash + claude-skill.contract.yml amend + HITL gate trigger
state: completed
version: 0.1
owner: ranzuozhou
created: 2026-05-21
updated: 2026-06-02
track: shared
refines:
  - plans/[PLAN]_spec_anchored_refactor.md
supersedes: []
related_adrs: []
---

# [PLAN] M3-FU-V4-SKILLS-COMPLETE — Backfill ADR-013 Reverse-Trigger Block in 6 mj-agent-infra-* SKILLs

> M3 follow-up plan；deferred from Stage C C-a flip strategy；refines
> `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown；blocks Stage C
> V4 blocking-gate flip (not done in Stage C C-a per Phase M2 §3.6 frozen surface
> rule).

> **✅ CLOSED 2026-06-02 (E-4-PR3 triage)** — superseded by **PR #183 (M4-A "V4-SKILLS-COMPLETE")**. All §4 AC met, verified on develop @ `a457cd2`:
> - 10 target `.claude/skills/mj-agent-{infra,runtime}-*/SKILL.md` all carry the `Do not use for:` reverse-trigger block (0 missing).
> - V4 `check_claude_skill_contracts.py --all` → **34 PASS / 0 WARN / 0 FAIL**.
> - V4 ci.yml step is BLOCKING (`'V4 claude-skill contracts (BLOCKING per M3-FU-V4-SKILLS-COMPLETE; 34P/0W/0F clean)'`).
> No further action; `state: completed`.

## §1 Background

Phase M3 Stage A P0-1 (M3-FU-V4-VALIDATOR-INVESTIGATE; commit `a5614c4`) fixed the
V4 H2 parser bug — V4 output went from 0 PASS / 34 spurious WARN → 28 PASS /
6 real WARN. The 6 remaining WARN are **genuine ADR-013 quality bar gaps**:

```
[WARN] .claude/skills/mj-agent-infra-docker-compose/SKILL.md: description missing reverse-trigger block ('Do not use for:'; ADR-013 anti-over-broad triggering)
[WARN] .claude/skills/mj-agent-infra-storage-stack/SKILL.md: ...
[WARN] .claude/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md: ...
[WARN] .claude/skills/mj-agent-runtime-eval-baseline/SKILL.md: ...
[WARN] .claude/skills/mj-agent-runtime-prompt-version-bump/SKILL.md: ...
[WARN] .claude/skills/mj-agent-runtime-skill-doc-improve/SKILL.md: ...
```

Phase M3 Stage C Gate-1 decision selected **C-a (don't flip V4)** because fixing
the 6 SKILLs touches Phase M2 Stage C #4 **必停 surface** (the 6
mj-agent-infra-* SKILLs are content_hash-locked in
`capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`).
Modifying them triggers cascading audit actions:

- 6 × `body_content_hash` recompute
- 6 × `description_hash` recompute (if description itself is amended)
- `claude-skill.contract.yml` amend (`frozen_at` refresh + new hashes)
- HITL Gate-2 `mcp-server-trust-posture-change` trigger (per §3.6 must-stop surface rule)

This is cross-capability cumulative — out of Stage C blocking-gate-flip scope.

## §2 Scope

### Included

- Edit 6 `.claude/skills/mj-agent-infra-*/SKILL.md` and 4 `.claude/skills/mj-agent-runtime-*/SKILL.md`
  to insert `Do not use for: ...` reverse-trigger block within the existing
  `description` frontmatter field. Per-file 1-2 line edit (no body change; only
  frontmatter description string).
- Recompute `body_content_hash` + `description_hash` for the 6 infra SKILLs that
  are anchored in `claude-skill.contract.yml`.
- Amend `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`:
  - 6 × `body_content_hash: sha256:<new-hex>` (note: body unchanged → hashes unchanged IF only description in frontmatter changes)
  - 6 × `description_hash: sha256:<new-hex>` (description IS changed → these refresh)
  - 6 × `frozen_at: <new-ISO-8601-timestamp>`
- Rerun V4 validator (`check_claude_skill_contracts.py --all`) → expected
  outcome: **34 PASS / 0 WARN / 0 FAIL**.
- Update Stage C ci.yml V4 step: flip from `continue-on-error: true` to
  blocking (M4-equivalent rollout, but landed at this plan's PR rather than M4
  bulk flip).

### Excluded

- 4 runtime SKILLs (`mj-agent-runtime-*`) are NOT in `claude-skill.contract.yml`
  (only the 6 infra SKILLs are content_hash-locked). Their fix is mechanical
  (no contract amend needed). They CAN be bundled into this plan's PR or split.
  Default: **bundle into single PR** for review efficiency.
- No SUT change to V4 validator (parser fix landed in M3-FU-V4-VALIDATOR-INVESTIGATE;
  this plan only adds qualifying content to SKILL.md files).
- No `name` / non-description frontmatter changes (preserves ADR-013 native
  2-field schema invariant).
- No ADR-013 schema redesign.

## §3 Verification

```bash
# After SKILL.md edits + contract amend
uv run python scripts/sdd/check_claude_skill_contracts.py --all
# Expected: 34 PASS / 0 WARN / 0 FAIL

# Re-verify all other validators unchanged
uv run pytest tests/unit -q  # 236+ PASS
uv run ruff check
uv run mypy src/mj_agent
```

## §4 AC

- [ ] 10 SKILL.md files have `Do not use for: ...` reverse-trigger block in
      their `description` frontmatter
- [ ] V4 validator output: 34 PASS / 0 WARN / 0 FAIL
- [ ] `claude-skill.contract.yml` `description_hash` × 6 + `frozen_at` × 6
      refreshed (`body_content_hash` × 6 unchanged because body bytes don't change)
- [ ] HITL Gate-2 ack on `mcp-server-trust-posture-change` (PR review checklist)
- [ ] V4 ci.yml step flipped to blocking (`continue-on-error: false`) as part of
      the same PR
- [ ] Independent PR; commit type `docs(skill)` (frontmatter description edit)
      + `ci(workflow)` (V4 flip) split or combined per granularity decision

## §5 估时 / Dependencies

- 估时 ~2-3h（6 + 4 × 2-line edit + content_hash recompute + 1 × contract amend + HITL review cycle）
- **Blocked-by M3-FU-V4-VALIDATOR-INVESTIGATE** (completed `a5614c4`; required
  because V4 must surface genuine WARN, not parser-bug spurious WARN, before
  fixing the genuine WARN makes sense)
- Independent of M3-FU-V5-SUBFLAGS / M3-FU-G1G2G9-IMPL / Stage C flip arc

## §6 严格守约

- ✅ V4 validator unchanged (parser fix already landed)
- ✅ ADR-013 native 2-field schema invariant preserved (only description content changes)
- ⚠️ Phase M2 Stage C #4 必停 surface IS touched — HITL Gate-2 trigger expected per
  `claude-skill.contract.yml hitl_required: [mcp-server-trust-posture-change]`
- ✅ 4 runtime SKILLs not in contract; mechanical edit (no cascade)
- ✅ ADR-016 namespace pattern unchanged

---

> *M3 follow-up plan — `state: active`；blocked-by M3-FU-V4-VALIDATOR-INVESTIGATE
> (completed `a5614c4`)；deferred from Stage C C-a flip strategy；independent PR
> after Stage C lands.*
