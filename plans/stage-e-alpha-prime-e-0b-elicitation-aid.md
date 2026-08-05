---
type: planning-aid
slug: stage-e-alpha-prime-e-0b-elicitation-aid
summary: Elicitation aid for M-FU#7 owner curation — owner (Zack) provides domain facts per scenario in rough form;Claude Code structures into 4-field runbook justification ready to paste into per-pilot runbook.md;non-fabrication boundary per R-13-3 + R-13-10 + R-16-6 enforced via "every output字 must trace to owner-provided fact" rule.
owner: ranzuozhou
created: 2026-05-29
updated: 2026-08-05
state: completed
track: shared
related_m_fu:
  - M-FU#7 — M4-FU-RUNBOOK-JUSTIFICATION-CURATE-ALL-PILOTS (companion;this aid supports owner workstream)
  - M-FU#1 — M4-FU-LLM-PROVIDER-TRACE-YML-BDD-COMPLETE (RESOLVED PR #195;S12 now properly tracked)
companion_docs:
  - plans/stage-e-alpha-prime-m-fu-7-runbook-curation-worksheet.md (PR #193;observable hints worksheet)
---

# Stage E α' E-0b Elicitation Aid — Owner Domain Facts → 4-Field Runbook Justification

> Companion to the M-FU#7 curation worksheet (PR #193 shipped). The worksheet
> provides observable hints (existing tests / TBD-M3 markers / ADR refs);this
> aid provides the elicitation structure for owner (Zack) to supply domain
> facts that Claude Code then structures into 4-field justification text
> ready to paste into per-pilot runbook.md。

## Why This Aid Exists

E-0b (M-FU#7 owner curation) blocks E-1 G21 BLOCKING flip + E-2 G22 BLOCKING
flip (per R-15-3 coupling;G21+G22 share runbook justification source per
R-15-1)。15 critical|high × unautomated scenarios across 4 pilots × 4-field
justification = significant authoring work。

**Two unhelpful patterns to avoid**:

1. **Claude Code fabricates from observable hints** — defeats G22 gate
   semantic (R-16-6 anti-gate-defeat;the justification is supposed to be
   real domain reasoning,not plausible-but-wrong text;rubber-stamp risk)
2. **Owner authors verbose prose from scratch per field** — high friction;
   may delay E-0b → blocks E-1+E-2 unnecessarily

**This aid's path**: owner provides **rough domain facts** (memory,planning
notes,docstring lookup) per the prompts below;Claude Code structures into
4-field runbook text ready for paste。 Form is automated;judgment stays
with owner。

## Role Boundary (R-13-3 + R-13-10 + R-16-6 Enforced)

| Role | Responsibility |
|---|---|
| **Owner (Zack) = Content Source** | Supply true domain facts per scenario: why currently unautomated / what alternative verification covers gap / what triggers automation / estimated timeline。Can be rough / casual / Chinese / English / bullet form。 |
| **Claude Code = Scribe / Structurer** | Take owner's facts → format into 4-field justification (原因 / 替代验证手段 / 升级触发条件 / 预计时间) ready to paste into runbook.md。 NEVER invent content not provided by owner。 |

**Sound test for non-fabrication**: every word in the structured output must
trace to a fact the owner provided。 If owner says "TBD-M3 step defs land",
the output may include "升级触发条件: M3 step definitions landing per TBD-M3
markers"。 If owner provides no input for a field, output that field as
**TBD (owner input pending)** — never invent。

## How to Use This Aid

1. **Owner picks scenarios** to provide facts for (any subset;Tier 1
   recommended:safe-sql S1-S4 critical first for early observable progress)
2. **Owner fills the prompts** below in rough form (~30 seconds per
   scenario for someone with the domain context);no need for prose polish
3. **Owner pastes filled prompts back to Claude Code**
4. **Claude Code structures** into 4-field justification blocks per pilot
5. **Owner reviews structured output** + pastes into each pilot's
   `runbook.md` (via Edit tool or manual)
6. **SDD verifies E-0b progress**: re-run `check_bdd_unautomated.py --all`
   + `check_bdd_acceptance.py --all` → WARN count drops as scenarios get
   4-field justification → target 0W from both G21 + G22
7. **At 15/15 ✓ (G21+G22 双 0W)**: paste queued E-1/E-2 combined flip brief

## Tier Recommendation (per Worksheet PR #193)

- **Tier 1 (critical;safe-sql S1-S4)** — 4 critical scenarios;each closure
  accelerates Stage E α' confidence
- **Tier 2 (1 high per pilot;S7 / S10 / S13)** — demonstrates pattern across
  all 4 pilots
- **Tier 3 (remaining 8 high)** — incremental progress to 15/15

## Elicitation Prompts (15 Scenarios)

### Pilot 1: safe-sql (6 scenarios;4 critical + 2 high)
Target file after structuring: `capabilities/data-agent/safe-sql/runbook.md`

#### S1 — `L1 regex guardrail rejects blocked-keyword statement before DB contact`
- REQ-001 / **critical** / Adapter: python
- **为何现在没自动化**:
- **现在靠什么验证（如 existing unit tests / 手测 / 暂未覆盖）**:
- **什么条件会触发自动化（如 M3 step defs / live_db ready / 某 ADR 落地）**:
- **预计何时自动化（Phase M3? M4 EOL? 具体里程碑?）**:

#### S2 — `L1b precheck rejects biz_dws fact-table query missing time-column predicate`
- REQ-002 / **critical** / Adapter: python
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S3 — `L3 connection enforces read-only transaction + bounded timeouts via DSN options`
- REQ-003 / **critical** / Adapter: python / Hint: 现存 tests TBD-M3 markers (test_dsn_options.py + test_readonly_cursor.py 暂未实装)
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S4 — `L4 statement_timeout cancellation translates to Chinese self-correction hint`
- REQ-004 / **critical** / Adapter: python / Hint: @reference-contract mj-system R__analyst_permissions.sql 跨仓 dep;TBD-M4 live_db contract test
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S5 — `execute_sql return envelope contains 8 required keys with documented types`
- REQ-005 / **high** / Adapter: python / Hint: TBD-M3 envelope tests markers
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S6 — `handle_sql_tool_errors middleware converts tool ValueError into ToolMessage`
- REQ-006 / **high** / Adapter: langchain-agent / ADR-029 / Hint: 现存 `tests/unit/test_tool_error_middleware.py` 5+ cases;TBD-M3 integration + smoke
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

---

### Pilot 2: biz-catalog (3 scenarios;3 high)
Target file: `capabilities/data-agent/biz-catalog/runbook.md`

#### S7 — `load_catalog rejects YAML whose root parses to a list (not a mapping)`
- REQ-001 / **high** / Adapter: python
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S8 — `Catalog signal_tables must resolve in live biz_dws`
- REQ-002 / **high** / Adapter: python / **@gated:live_db**
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S9 — `Active SKILL bodies reference only resolvable catalog symbols and DB tables`
- REQ-003 / **high** / Adapter: runtime-skill / **@gated:live_db**
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

---

### Pilot 3: llm-provider (3 scenarios;3 high) ★ S12 post M-FU#1 fix
Target file: `capabilities/data-agent/llm-provider/runbook.md`

#### S10 — `Ark provider raises clear LLMConfigError when both ARK_API_KEY and LLM_API_KEY are empty`
- REQ-001 / **high** / Adapter: python / ADR-027
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S11 — `Local provider constructs ChatOpenAI without extra_body.thinking`
- REQ-002 / **high** / Adapter: python / ADR-027
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S12 — `effective_llm_api_key returns "EMPTY" sentinel for local provider when LLM_API_KEY is empty`
- REQ-003 / **high** / Adapter: python / ★ Post M-FU#1 quote fix correctly tracked from G22 filter
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

---

### Pilot 4: docker-compose (3 scenarios;3 high)
Target file: `capabilities/infrastructure/docker-compose/runbook.md`

#### S13 — `DEV profile loads with explicit -f chain + --env-file`
- REQ-001 / **high** / Adapter: docker-container / ADR-026
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S14 — `Postgres healthcheck rejects half-initialized DB`
- REQ-002 / **high** / Adapter: docker-container
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

#### S15 — `Postgres init handles password with shell metacharacters unmangled`
- REQ-003 / **high** / Adapter: docker-container / ADR-030
- **为何现在没自动化**:
- **现在靠什么验证**:
- **什么条件会触发自动化**:
- **预计何时自动化**:

---

## What Owner Gets Back (Per Pilot)

After owner pastes filled prompts (any subset),Claude Code outputs per-pilot
runbook.md justification blocks in the canonical 4-field format,e.g.:

```markdown
### G22/G21 Justification: <Scenario Name>

- **原因**: <structured from owner facts>
- **替代验证手段**: <structured from owner facts>
- **升级触发条件**: <structured from owner facts>
- **预计时间**: <structured from owner facts>
```

Owner reviews → pastes into corresponding pilot's `runbook.md` (under §3
existing structure OR new §7 per runbook layout)。 Re-run G22 + G21
dry-runs to verify WARN count drops。

## Cross-Reference

- bdd-tdd.md L121 (G22 justification 4-field spec)
- bdd-tdd.md L160 + L161 (G21 + G22 share runbook source per R-15-1
  resolution + Action-N-1 codification PR #192)
- Worksheet PR #193 (observable hints per scenario;use jointly with this aid)
- PR #195 (E-0a;G21 evidence predicate + R-18-4 intended WARN-raise;runbook
  fallback path implemented)
- plans/[PLAN]_spec_anchored_refactor.md (Stage E α' outline + R-13-3
  Scoping Option (b) + R-13-10 SDD/product boundary + R-15-1 coupling)

> Owner authoring stays domain knowledge work (R-13-3 Option b boundary);
> this aid only provides structure。 Anti-fabrication discipline (R-16-6)
> preserved: form automated,judgment owner-owned。
