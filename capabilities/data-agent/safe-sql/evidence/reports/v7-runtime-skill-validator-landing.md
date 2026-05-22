# V7 Runtime-Skill Validator Landing — M3-FU-RUNTIME-SKILL-VALIDATOR

**Plan:** `plans/[PLAN]_m3_fu_runtime_skill_validator.md`
**Resolved on:** Phase M3 Stage A (branch `documentation/spec-anchored-refactor-m3`)
**Outcome:** new validator `scripts/sdd/check_runtime_skill_contracts.py` landed; 2/2 Stage C runtime-skill contracts PASS (safe-sql + biz-catalog covering 3 in-source SKILLs); CI gate V7 wired in warning mode.

## Why a separate validator

`check_runtime_expected.py` is docker-only (validates
`runtime.expected.yaml` for compose containers + healthcheck + network).
`runtime-skill.contract.yml` is a completely different schema — it freezes
in-source SKILL.md body content_hash + frontmatter `version` / `state`.
Conflating them into one validator would mix unrelated concerns; per the
plan §1 spot-check confirmed Stage C batch 1 temporarily downgraded
verification to `yaml.safe_load` + `git diff` because no dedicated
validator existed.

## Validator scope

Per skill entry in `contract.skills[]`:

| Field | Check | Severity if mismatched |
|---|---|---|
| `file` | exists on disk | FAIL |
| `version` | string-exact vs frontmatter `version` (no v-prefix strip / no normalize) | FAIL |
| `state` | string-exact vs frontmatter `state` | FAIL |
| `content_hash` | matches `body_sha256(text)` per canonical algorithm (strip frontmatter + LF-normalize body + SHA-256 hex); `sha256:` prefix tolerated via `content_hash_matches` | **FAIL** (runtime-skill-content-change HITL gate) |
| `body_section_heads` | level-2 headings present in body via `extract_headings(body, level=2)`; tolerates `## ` marker prefix per Stage B canonical | WARN |
| frozen_at / variables / triggers_visible / used_by_agent / eval_references / cross_skill_refs | informational; not enforced at M3 |

Per accumulated AC: 9-field prose-like exclude (type / domain / summary /
owner / created / updated / track / eval_references / supersedes) is NOT
validated as frozen — these are prose, indirectly covered by body
content_hash via the freeze anchor.

## Output against actual Stage C contracts

```
check_runtime_skill_contracts.py — validating 2 runtime-skill.contract.yml

capabilities/data-agent/biz-catalog/contracts/runtime-skill.contract.yml
  [PASS] src/mj_agent/skills/biz-domain-context/SKILL.md: version + state + content_hash + body_section_heads all PASS
  [PASS] src/mj_agent/skills/qcm-analysis/SKILL.md: version + state + content_hash + body_section_heads all PASS

capabilities/data-agent/safe-sql/contracts/runtime-skill.contract.yml
  [PASS] src/mj_agent/skills/safe-sql-analysis/SKILL.md: version + state + content_hash + body_section_heads all PASS

=== Summary ===
PASS: 3 / WARN: 0 / FAIL: 0
```

## Acceptance criteria

| AC | Status |
|---|---|
| `check_runtime_skill_contracts.py` ≥ 80 lines with real validation logic | ✅ ~210 lines |
| 2 Stage C runtime-skill contracts PASS (safe-sql + biz-catalog) | ✅ 3 SKILLs across 2 contracts, all PASS |
| Reuses `_common.frontmatter` API (no duplicate strip/parse) | ✅ uses `parse_frontmatter`, `body_sha256`, `content_hash_matches`, `extract_headings` |
| content_hash drift detection FAIL (LF-normalised) | ✅ verified by `test_content_hash_drift_fails` |
| Unit tests ≥ 5 cases | ✅ 10 cases in `tests/unit/test_sdd_runtime_skill_validator.py` (happy / drift / strip-contract / empty / version-string-exact / state-string-exact / missing-field / missing-file / section-warn / wrong-contract-id) |
| CI workflow integrated (warning at M3; M4 strict) | ✅ V7 step added after V6 in `.github/workflows/ci.yml`; `continue-on-error: true` per Phase M3 mode |
| Independent PR; `feat(sdd)` commit | ✅ this commit |

## §6 严格守约 compliance

- ✅ 7 adapter docs untouched
- ✅ 必停 surfaces (3 in-source SKILLs) untouched — read-only validation
- ✅ `check_runtime_expected.py` untouched (docker-only scope preserved)
- ✅ Stage C 2 runtime-skill contracts untouched (validator IS the reverse check)
- ✅ no new ADR (validator impl is not architectural)
- ✅ no EVAL framework integration (deferred to M4-FU)

## Design notes

- Per-skill validation modifies the contract-level `Summary` in place
  (rather than nested Summary + merge) — `Summary.merge()` is counts-only
  by design; nesting would lose per-skill messages. Local pre/post
  `fail_count` snapshot detects "no FAIL added by this skill" for the
  aggregate-pass message.
- `content_hash_matches` (added in P0-2 / M3-FU-VALIDATOR-CONTRACT-ALIGN)
  is reused — V7 is the first non-V3 caller, validating the helper's
  cross-validator reusability per that plan's stated motivation.

## Regression checks

- `uv run pytest tests/unit -q` → 205 passed (was 195 + 10 new V7 tests)
- `uv run ruff check` on touched files → clean (after auto-fix on test imports)
- `uv run mypy src/mj_agent` → clean (44 files)
- V1-V6 outputs unchanged (V7 is additive)
- `uv run python scripts/sdd/check_runtime_skill_contracts.py --all` → 3 PASS / 0 WARN / 0 FAIL

## Files changed

- `scripts/sdd/check_runtime_skill_contracts.py` — new file, ~210 lines
- `tests/unit/test_sdd_runtime_skill_validator.py` — new file, 10 tests
- `.github/workflows/ci.yml` — V7 step added (warning mode)
- `capabilities/data-agent/safe-sql/evidence/reports/v7-runtime-skill-validator-landing.md` — this file
- `plans/[PLAN]_m3_fu_runtime_skill_validator.md` — state: completed + §7 Resolution
