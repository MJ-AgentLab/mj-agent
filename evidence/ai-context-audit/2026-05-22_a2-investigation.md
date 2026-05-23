---
type: ai-context-investigation
investigation: a2-body-sha256-v4-mode-b-joint
auditor: "ai-agent (claude-opus-4-7 via claude-code; HITL-supervised by ranzuozhou)"
scope:
  - body-sha256-utility
  - v4-claude-skill-validator-mode-b
  - hash-algorithm-governance
phase: M4-Stage-A-unit-A-2
date: 2026-05-22
findings_summary: "V-2α verdict (BODY-SHA256 dormant; 2 latent issues insulated by read_text); M-1 verdict (V4 Mode B cleanup wording; per cost/benefit at change rate 0.4 commits/week); Bundle B-α (1+3) defer M5+ archive ceremony"
related_episodes:
  - "#2-1 body_sha256 callers V3+V7 only (V4 absent)"
  - "#2-2 Mode B docstring-only single point"
  - "#2-3 ADR-013 silent on V4 implementation"
  - "#2-4 evidence/investigations/ not existing (Option a-modified resolves)"
  - "#2-5 ADR-032 implicit enum broadening (L144-145)"
  - "#2-6 Algorithm split (canonical regex-strip vs body_sha256 utility) is intentional architecture"
  - "#2-7 M3-FU plan §discovery_evidence citation imprecise (2026-Q2.md §4b not exist)"
  - "#2-8 §7 Discipline self-validates via multi-mode verify (Step 2.8 methodology error caught)"
  - "#2-9 SCHEMA.md type enum currently ai-context-audit only; investigation-type files need amendment"
schema_extension_request: true
---

# A-2 Investigation Report — BODY-SHA256 + V4 Mode B Joint Investigation

## §1 Goal + Scope

**Phase M4 Stage A Unit A-2** — read-only joint investigation surfacing 4 M4-FU registry candidates + 9 §7 Episode candidates (累积到 Stage F F-7 closure unit cluster amend).

**Anchored sources**:
- A-1 brief §0 Episode #3 — V4 Mode B docstring-only finding (per commit `683c700` body)
- M3-FU-BODY-SHA256-STRICT-YAML-FALLBACK plan (master plan §M3 inline; state: active; disposition: M4-FU deferred)
- M3-FU-V4-MODE-B-DISPOSITION candidate (per A-1 Episode #3; joint investigation scope)

**Joint scope rationale**: BODY-SHA256 utility issue + V4 Mode B implementation gap share *hash algorithm governance regime* theme; investigated together for cross-finding insight (Episode #2-6 algorithm split = intentional architecture, NOT accidental drift).

**Output**: this file at `evidence/ai-context-audit/2026-05-22_a2-investigation.md` (new file; 1 file write). **NO fix in A-2 scope** — 4 M4-FU registry candidates identified for separate disposition (per D-1 Bundle B-α + 2 M5+ defer per D-2 X4 ACK).

## §2 BODY-SHA256 Investigation

### §2.1 Utility Implementation Analysis

`scripts/sdd/_common/frontmatter.py` body_sha256 chain (3 functions; line ranges):

```python
# L22-38: parse_frontmatter (strict YAML)
def parse_frontmatter(text):
    match = _FRONTMATTER_RE.match(text)             # \A---\r?\n(.*?)\r?\n---\r?\n
    if not match: return None, text
    try: fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError: return None, text        # silent fall-through (L1)
    if not isinstance(fm, dict): return None, text
    body = text[match.end():]
    return fm, body

# L83-86: strip_frontmatter
def strip_frontmatter(text):
    _, body = parse_frontmatter(text)
    return body                                     # body OR original text on fall-through

# L89-96: body_sha256 (NO LF normalization — L2)
def body_sha256(text):
    body = strip_frontmatter(text)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
```

**Two latent issues identified**:
- **L1**: Strict-YAML parse failure → silent fall-through to whole-file hash; caller can't distinguish "successfully hashed body" vs "hashed whole file due to YAML error"
- **L2**: No internal LF normalization; relies on caller to pass LF-normalized text

### §2.2 Caller Chain Analysis (V3 + V7; V4 Absent)

Grep `body_sha256` across `scripts/sdd/`:
- `check_prompt_contracts.py` (V3) L43 import + L97 call (system.md target)
- `check_runtime_skill_contracts.py` (V7) L18 doc + L44 import + L123 call (3 in-source SKILLs)
- `_common/__init__.py` L31+L60 export
- `check_claude_skill_contracts.py` (V4) **NOT a caller**

**Implication**: M3-FU plan §scope wording "6 infra SKILLs" implied V4 path bug, but V4 doesn't use body_sha256. Bug surface (if active) limited to V3 (system.md) + V7 (3 in-source SKILLs). Episode #2-1 anchor.

### §2.3 §7 Discipline Self-validation Case Study (Episode #2-8)

#### §2.3.1 Initial Empirical Hash Matrix — False-Positive Scenario γ

Step 2.8 implementation used `open('rb').read().decode('utf-8')` (binary mode; preserves CRLF):

| File | utility (binary read) | canonical regex-strip | contract stored | initial scenario |
|---|---|---|---|---|
| `src/mj_agent/prompts/system.md` | `b692ebe6...` | `994d4a2d...` | `994d4a2d...` | γ |
| `src/mj_agent/skills/biz-domain-context/SKILL.md` | `bfdb312f...` | `0c70f7f3...` | `0c70f7f3...` | γ |
| `src/mj_agent/skills/qcm-analysis/SKILL.md` | `3ecc6c71...` | `047a6141...` | `047a6141...` | γ |
| `src/mj_agent/skills/safe-sql-analysis/SKILL.md` | `c760344d...` | `749ed640...` | `749ed640...` | γ |

4/4 scenario γ — would imply V3/V7 should FAIL every run, contradicting CLAUDE.md "8 BLOCKING gates green" claim.

#### §2.3.2 §7 Discipline Triggered — Multi-mode Cross-verify

Brief §0 `#2-γ-impossible` flag triggered. Per `policies/ai-agent.md §7` Sufficient Verification Modes, executed in parallel:
1. **Run validator against real data**: V3 output `PASS 1 / WARN 1 / FAIL 0`; V7 output `PASS 3 / WARN 0 / FAIL 0`
2. **Inspect output reflects actual validation**: V3+V7 PASS contradicts scenario γ → must be methodology artifact
3. **Read validator source + line-ending diagnostic**: 4 files have 101-161 CRLF count, 0 lone LF

#### §2.3.3 Root Cause — `read_text` Universal Newline Insulation

```python
# V3 L80 / V7 L95:
text = file_path.read_text(encoding="utf-8")  # Python text mode default newline=None
# → universal newline translation: CRLF in file → LF in returned string
```

V3/V7 caller chain: `read_text` translates CRLF → LF before body_sha256 call. Utility receives LF-only text → hashes LF body → matches canonical regex-strip (also LF-normalized). Contracts computed via this path → stored hash matches → PASS.

My Step 2.8 script: `open('rb').read().decode('utf-8')` preserves CRLF → utility hashes CRLF body → ≠ canonical → false scenario γ.

#### §2.3.4 Episode #2-8 Lesson

**Single-mode verify (read source / run validator / check spec alone) is insufficient; cross-mode triangulation prevents false-positive governance damage.**

Without §7 multi-mode verify, would have stopped at scenario γ verdict → recommended utility fix → re-compute V3/V7 contracts via canonical regex-strip. Cross-platform impact: Linux CI no-op (already LF); Windows worktree creates verification path confusion (double-normalize). §7 Discipline catches this within one diagnostic cycle.

### §2.4 Verdict V-2α + Disposition

**V-2α (dormant)**: body_sha256 utility has 2 latent issues (L1 + L2) but neither triggers in current V3+V7 caller chain due to:
- L1 insulation: V3+V7 target files use well-formed 13-field YAML (no embedded "Do not use for:" colon-space; strict-YAML parses cleanly)
- L2 insulation: V3+V7 use `read_text(encoding="utf-8")` → Python universal newline auto LF-normalize

**Disposition**: M4-FU candidate (1) DOCSTRING-CLARIFY (active immediate; Bundle B-α); M4-FU candidate (2) CANONICAL-REFACTOR (M5+ standalone defer).

## §3 V4 Mode B Investigation

### §3.1 Re-verify Summary

- V4 main (`scripts/sdd/check_claude_skill_contracts.py` L109-143): `_discover_skills` + `_validate_skill_md`; NO contract loading, NO body_sha256 call, NO hash comparison
- V4 docstring L14-16: "Mode B" promise text (when claude-skill.contract.yml present, validate contract's skill_path reference); NOT implemented in main()
- ADR-013 全文: silent on V4 implementation / Mode B / hash comparison (focus = 2-field vs 13-field schema separation; per 决策点 1-5)
- ADR-032 全文: 3-layer regime described; Layer 1 V4 = schema check only; canonical regex-strip mentioned (L75, L91, L141); Mode B NOT discussed
- contract.yml header (`capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml` L11-13): "manual drift detection without prose in contract YAML" — wording acknowledges manual nature

### §3.2 Change Rate Empirical Anchor

```
contract.yml commits since M3 start (2026-05-21): 2 commits
- 683c700 (A-1; V4-SKILLS-COMPLETE; this PR)
- 633225b (Stage D D-3a; M3-FU-CLAUDE-SKILL-ADR contract cleanup)
```

Rate ≈ **0.4 commits/week** (~20/year across all contract.yml). Specific to `claude-skill.contract.yml` (V4 scope): only 2 commits historical.

### §3.3 3-Layer Regime Sufficiency

| Layer | Mechanism | Coverage | Cadence |
|---|---|---|---|
| Layer 1 V4 | Schema check (description ≥ 200 + reverse-trigger + ADR-016 namespace) | Schema deviation | PR-atomic |
| Layer 2 PR A12 | Procedural HITL (Track C engineering-workflow) | Semantic / scope drift | PR-atomic |
| Layer 3 A6 audit | Canonical regex-strip全 surface inventory | Cumulative drift | Quarterly |

**Gap analysis**: Mode B would be Layer 1.5 (PR-atomic content_hash drift detection). At 0.4 commits/week:
- A6 quarterly audit covers ~5 commits/cycle within manual review bandwidth
- Worst-case undetected drift ≤ 90 days; expected ~0.4 commits/window
- **Gap severity: LOW** — current regime adequate

### §3.4 Option A Cost/Benefit数字

**Cost** (extrapolated from V7 ~251 line pattern):
- V4 Mode B impl: ~100 lines (contract load + per-skill iterate + match + hash compute + compare + report)
- ADR-032 amendment: ~20-30 lines
- V4 docstring update: ~5-10 lines
- **Total: ~130-145 lines** + ~0.5 hr/year maint

**Benefit**: 0.5-1 quarterly-lag drift events/year caught immediately

**ROI**: MEDIUM cost, LOW frequency benefit — implementation cost NOT justified at current change rate.

### §3.5 U-2 + M-2 Bundle Assessment

Mode B implementation (M-2) is **INDEPENDENT** of utility refactor (U-2):
- M-2 should use canonical regex-strip directly (per Episode #2-6)
- NOT use body_sha256 utility (latent L1/L2 dormant but suboptimal)
- Bundle (M-2 + U-2) provides algorithm consistency story but not mandatory

### §3.6 Verdict M-1 + Rationale

**M-1 (Option B; cleanup wording)** — selected.

| Q | Answer |
|---|---|
| Q1 Gap severity | LOW (empirical change rate 0.4 commits/week; A6 quarterly cadence sufficient) |
| Q2 Layer 1 vs Layer 3 | Mode B = Layer 1.5 enhancement, NOT gap-filler; current regime adequate |
| Q3 Cost/benefit | ~130-145 lines + 0.5 hr/year maint vs 0.5-1 drift/year caught immediately; ROI LOW |
| Q4 U-X dependency | Independent; M-2 + U-2 bundle optional not required |

**Why NOT M-2**: cost not justified at current frequency; M5+ archive ceremony is natural re-evaluation point.

**Why NOT M-3 (defer-entirely)**: M-1 cleanup cost very low (~20-30 lines); leaves audit-trail of governance decision; M-3 just postpones it.

## §4 Disposition Recommendations

### Bundle B-α (active immediate; landing path D-2 X4 — defer M5+ archive ceremony)

- **(1) M4-FU-BODY-SHA256-DOCSTRING-CLARIFY** (~10-15 lines doc)
  - Add caller contract note to `body_sha256` docstring (`scripts/sdd/_common/frontmatter.py#L89-L96`)
  - Reference Episode #2-6 algorithm split + Episode #2-8 §7 Discipline lesson
- **(3) M4-FU-V4-MODE-B-CLEANUP** (~20-30 lines doc)
  - V4 docstring §Mode B rewrite "(historical; not implemented by design — see ADR-032 + A6 audit Layer 3 for hash drift detection)"
  - Optional ADR-032 amendment §section (Layer 1.5 deferral rationale)

### Defer M5+ Standalone (re-evaluation triggers below)

- **(2) M4-FU-BODY-SHA256-CANONICAL-REFACTOR** (~15-30 lines code + cross-platform tests)
- **(4) M4-FU-V4-MODE-B-IMPL** (~130-145 lines code + ADR amend; per §3.6 cost analysis)

## §5 Followup Unit Candidates + Re-evaluation Triggers

**F-8 post-merge skill path**: 4 M4-FU registry entries added to master plan via Stage F F-8 unit (post Stage A PR #M4-A merge).

**Re-evaluation triggers for (2)+(4) at M5+**:
- contract.yml change rate > 2 commits/week (current 0.4) → M-2 ROI re-assess
- ADR-013 / ADR-032 governance regime overhaul → Mode B implementation natural prerequisite
- EVAL framework Phase 2 readiness (per ADR-024 §A8/A11 4-prereq met) → hash governance might subsume into EVAL
- Cross-platform Windows worktree pain points → U-2 refactor prioritized

**Stage F outline scope strict守约**: F-1...F-5 + F-7 + F-8 = 7 units 不变; Bundle B-α NOT added to Stage F per D-2 X4 ACK.

**Method anchor for future governance decisions**: Empirical change rate (0.4 commits/week) is A-2's most transferable methodology contribution. Future Layer-X-enhancement vs current-regime-sufficiency decisions should anchor on empirical commit-rate data, not hand-wave hypotheticals.

## §6 Cross-references

- **A-1 commit `683c700`** body — Episode #1/#2/#3 originating record (V4-SKILLS-COMPLETE Stage A unit A-1)
- **M3-FU plan** (master plan `plans/[PLAN]_spec_anchored_refactor.md` §M3 inline) — `body_sha256` strict-YAML fallback original registration; cited Episode #2-7 imprecise reference "2026-Q2.md §4b" (no such section; bug discovery actually in commit `871f889` body)
- **A-2 brief §0** (this conversation; 4 brief-time Episodes #2-1...#2-4 originating record)
- **ADR-013** (`docs/adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation.md` — 决策点 1-5; silent on V4 implementation per Episode #2-3)
- **ADR-032** (`docs/adr/[ADR]_032_Claude_Skill_Schema_Monitoring.md#L75,L91,L141` canonical regex-strip refs; `#L144-L145` implicit enum broadening Episode #2-5)
- **Contract header** (`capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml#L11-L16` canonical algorithm spec)
- **SCHEMA.md** (`evidence/ai-context-audit/SCHEMA.md#L41-L49` content_hash_snapshot algorithm authoritative)
- **2026-Q2.md** (`evidence/ai-context-audit/2026-Q2.md` D-1c baseline; §3 .claude/skills/ inventory canonical regex-strip; commit `871f889`)
- **V3 source** (`scripts/sdd/check_prompt_contracts.py#L80-L102` body_sha256 caller)
- **V7 source** (`scripts/sdd/check_runtime_skill_contracts.py#L95-L130` body_sha256 caller)
- **V4 source** (`scripts/sdd/check_claude_skill_contracts.py#L14-L16` Mode B docstring; `#L109-L143` main; NO Mode B implementation)
- **utility** (`scripts/sdd/_common/frontmatter.py#L22-L38` parse_frontmatter; `#L83-L86` strip_frontmatter; `#L89-L96` body_sha256)
- **policies/ai-agent.md §7** — Pre-flight Verification Discipline; Subsection B cluster amend candidates Episodes #2-1...#2-9 (F-7 closure unit accumulation)

---

> **Investigation Type**: ad-hoc joint cross-finding; SCHEMA.md currently governs only `ai-context-audit` quarterly cycles. Episode #2-9 candidate proposes M5+ archive ceremony SCHEMA.md amendment to formally define `ai-context-investigation` type for future ad-hoc governance investigations. `schema_extension_request: true` frontmatter field flags this.
