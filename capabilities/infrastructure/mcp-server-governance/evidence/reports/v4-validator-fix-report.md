# V4 Validator Fix Report — M3-FU-V4-VALIDATOR-INVESTIGATE

**Plan:** `plans/[PLAN]_m3_fu_v4_validator_investigate.md`
**Resolved on:** Phase M3 Stage A (branch `documentation/spec-anchored-refactor-m3`)
**Outcome:** root cause = H2 (parser bug); fix landed; AC met.

## Root cause

`scripts/sdd/_common/frontmatter.py::parse_frontmatter()` delegates to
`yaml.safe_load()`, which rejects any unquoted plain scalar containing a
`: ` (colon + space) — interpreting the second `:` as a nested mapping start
and raising `YAMLError: mapping values are not allowed here`. The 34 in-tree
SKILL.md files all include the literal anti-trigger phrase
`Do not use for: ...` inside their `description` value, so every file fails
the YAML parse, returns `(None, text)`, and the V4 validator emits the
spurious `no frontmatter block` warning.

Reproducer (truncated `.claude/skills/mj-agent-doc-author/SKILL.md`):

```
---
name: mj-agent-doc-author
description: A skill ... Do not use for: documentation gap analysis (use ...).
---
```

`yaml.safe_load("name: ...\ndescription: ... Do not use for: ...")` raises:

```
yaml.scanner.ScannerError: mapping values are not allowed here
  in "<unicode string>", line 2, column 849
```

H1 (wrong directory) and H3 (Q-A3 brief misread) ruled out — V4 was reading
the correct paths and the brief faithfully echoed V4's wrong output.

## Fix

New helper `parse_native_frontmatter()` in `scripts/sdd/_common/frontmatter.py`
takes each top-level `<key>: <value>` line literally — the value is the
rest-of-line, preserving embedded `:` characters — matching Claude Code's
own SKILL.md loader semantics. `parse_frontmatter()` is unchanged (kept
strict for PROMPT and runtime-skill 13-field schemas that benefit from
yaml.safe_load's type coercion + nested structures). `check_claude_skill_contracts.py`
switched its import to the native variant.

11 unit tests in `tests/unit/test_sdd_frontmatter.py` cover: simple 2-field,
embedded colon (regression), no frontmatter, empty block, YAML comments,
extra keys, partial keys, indented continuation, first-colon-as-separator,
strict parser unchanged for full YAML, strict parser still breaks on the
embedded-colon case (so future readers see why both variants exist).

## V4 output before vs after

| | PASS | WARN | FAIL |
|---|---:|---:|---:|
| before fix | 0 | 34 (all spurious "no frontmatter block") | 0 |
| after fix  | 28 | 6 (all real ADR-013 `Do not use for:` reverse-trigger gaps) | 0 |

Remaining 6 WARN findings (now genuine ADR-013 quality bar deviations,
not parser noise; tracked separately, not in this plan's scope):

- `.claude/skills/mj-agent-infra-docker-compose/SKILL.md` (frozen surface)
- `.claude/skills/mj-agent-infra-storage-stack/SKILL.md` (frozen surface)
- `.claude/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md`
- `.claude/skills/mj-agent-runtime-eval-baseline/SKILL.md`
- `.claude/skills/mj-agent-runtime-prompt-version-bump/SKILL.md`
- `.claude/skills/mj-agent-runtime-skill-doc-improve/SKILL.md`

The 6-WARN end-state matches the validator docstring prediction:
"expected to surface ≥5 natural WARN across 34 SKILLs (per Subagent C
survey + user augmentation expectation)."

## Acceptance criteria

| AC | Status |
|---|---|
| V4 re-run + reverify table comparison | ✅ documented above (0/34 → 28/6/0) |
| Root cause confirmed (H1/H2/H3) | ✅ H2 confirmed; H1 + H3 ruled out |
| Fix PR + unit tests + CI integration | ✅ permissive parser added; 11 unit tests; existing CI step picks up next push automatically |
| Independent small PR; commit type `fix(sdd)` | ✅ this commit |

## Regression checks

- `uv run pytest tests/unit -q` → 188 passed (was 177 + 11 new)
- `uv run python scripts/sdd/check_prompt_contracts.py --all` → 1 FAIL pre-existing (M3-FU-VALIDATOR-CONTRACT-ALIGN scope; out of this plan)
- `uv run python scripts/sdd/check_runtime_expected.py --all` → 1 PASS / 1 WARN (skeleton; expected)
- `uv run ruff check` on 4 touched files → clean
- `uv run mypy src/mj_agent` → clean (44 files)

## Files changed

- `scripts/sdd/_common/frontmatter.py` — added `parse_native_frontmatter`
- `scripts/sdd/_common/__init__.py` — re-export
- `scripts/sdd/check_claude_skill_contracts.py` — switched parser
- `tests/unit/test_sdd_frontmatter.py` — new, 11 tests
- `capabilities/infrastructure/mcp-server-governance/evidence/reports/v4-validator-fix-report.md` — this file
- `plans/[PLAN]_m3_fu_v4_validator_investigate.md` — state: completed + §8 Resolution
