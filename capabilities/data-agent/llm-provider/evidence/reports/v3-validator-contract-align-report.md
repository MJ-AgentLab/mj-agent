# V3 Validator Contract-Align Fix Report — M3-FU-VALIDATOR-CONTRACT-ALIGN

**Plan:** `plans/[PLAN]_m3_fu_validator_contract_align.md`
**Resolved on:** Phase M3 Stage A (branch `documentation/spec-anchored-refactor-m3`)
**Outcome:** Stage A validator vs Stage B canonical drift resolved for V3; cross-validator helper added.

## Root cause

`scripts/sdd/check_prompt_contracts.py` was implemented in Stage A before
Stage B/C canonical was finalised. Two schema-shape drifts emerged when
Stage C #3 (`capabilities/data-agent/llm-provider/contracts/prompt.contract.yml`)
landed using the Stage B canonical form:

| field | Stage A validator expected | Stage B canonical (Stage C uses) |
|---|---|---|
| `content_hash` prefix | bare hex (no prefix) | `sha256:<hex>` |
| body section field name | `body_section_names` | `body_section_heads` |
| body section heading text | text only (e.g. `Identity`) | with marker (e.g. `# Identity`) |

First two are documented in the plan §1; the third surfaced only after
the second was fixed (validator started reading the previously-ignored
field and immediately hit the marker mismatch).

## Fix

- New helper `content_hash_matches(expected, actual)` in
  `scripts/sdd/_common/frontmatter.py` — strips a case-insensitive
  `sha256:` prefix on both sides before exact hex compare; tolerates
  either format on either side.
- `check_prompt_contracts.py` uses the helper for content_hash comparison;
  accepts either `body_section_heads` (canonical) or `body_section_names`
  (legacy) on the contract side; strips the leading `# ` heading marker
  from contract entries before comparing against `extract_headings()`
  output (which is marker-stripped).
- 7 new unit tests in `tests/unit/test_sdd_frontmatter.py` cover the
  helper: both-prefixed / both-bare / mixed / case-insensitive / different /
  None handling / empty strings (≥5 per plan AC).

## V3 output before vs after

| | PASS | WARN | FAIL |
|---|---:|---:|---:|
| before fix | 0 | 1 | 1 (content_hash drift) |
| after content_hash fix only | 1 | 5 (4 new heading-marker mismatches) | 0 |
| after final fix | 1 | 1 (informational `allowed_state_transitions`) | 0 |

## Acceptance criteria

| AC | Status |
|---|---|
| V3 PASS for Stage C #3 (no FAIL on content_hash) | ✅ |
| V3 accepts both `sha256:<hex>` and `<hex>` formats | ✅ (canonical = prefix form) |
| V3 accepts `body_section_heads` field (with `body_section_names` legacy fallback) | ✅ |
| Cross-validator hash helper in `_common` (reusable for future V4 Mode B / runtime-skill validator) | ✅ |
| Stage C 4 contracts all validator PASS (#3 in scope here; #4 already ADR-013-lint PASS post M3-FU-V4) | ✅ for #3 (V3); ✅ for #4 (V4 Mode A lint clean — Mode B contract-hash enforcement is genuine deferred future scope, not this plan) |
| Unit tests ≥ 5 cases | ✅ 7 cases (test_hash_matches_*) |
| Independent PR; `fix(sdd)` commit | ✅ this commit |

## Plan §6 严格守约 compliance

- ✅ Stage C 4 contracts untouched
- ✅ Stage B 7 adapter docs untouched
- ✅ No gate toggled to blocking (warning-mode preserved)
- ✅ No 必停 surface modified

## Regression checks

- `uv run pytest tests/unit -q` → 195 passed (was 188 + 7 new = 195)
- `uv run python scripts/sdd/check_claude_skill_contracts.py --all` → 28 PASS / 6 WARN / 0 FAIL (unchanged from P0-1)
- `uv run python scripts/sdd/check_runtime_expected.py --all` → 1 PASS / 1 WARN (skeleton; unchanged)
- `uv run ruff check` on touched files → clean
- `uv run mypy src/mj_agent` → clean (44 files)

## Files changed

- `scripts/sdd/_common/frontmatter.py` — added `content_hash_matches`
- `scripts/sdd/_common/__init__.py` — re-export
- `scripts/sdd/check_prompt_contracts.py` — use helper + accept dual field name + strip heading marker
- `tests/unit/test_sdd_frontmatter.py` — 7 new tests
- `capabilities/data-agent/llm-provider/evidence/reports/v3-validator-contract-align-report.md` — this file
- `plans/[PLAN]_m3_fu_validator_contract_align.md` — state: completed + §7 Resolution
