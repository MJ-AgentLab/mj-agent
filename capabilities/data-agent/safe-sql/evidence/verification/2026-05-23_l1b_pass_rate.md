# safe-sql L1b sqlglot Precheck Pass Rate Verification (2026-05-23)

- **Stage**: Phase M4 Stage C unit C-1b
- **Branch**: `documentation/spec-anchored-refactor-m4-bc`
- **Outcome**: 13/13 unit tests PASS (100% pass rate; 5/5 rule-ID coverage = 100% empirical); 2 findings — positive null on rule count alignment + §4.1 SUT-runbook drift on limit_too_large threshold (10000 vs 1000)
- **Cluster**: safe-sql C-1a (L1) / C-1b (L1b) / C-1c (SQL injection audit)

## §1 Goal + Scope

Verify `src/mj_agent/tools/sql/precheck.py::precheck_sql()` enforces REQ-002 (L1b sqlglot AST precheck) against the empirical `tests/unit/test_precheck.py` corpus. Per `capabilities/data-agent/safe-sql/spec.yml` REQ-002 statement:

> "L1b sqlglot AST precheck enforces 5 rule IDs (no_select_star / require_time_range / require_limit / limit_too_large / sqlglot_parse_failed)"

Scope **excludes** L1 regex guardrail (REQ-001; covered by C-1a) and SQL injection security audit (cross-cap C-1c). Evidence basis: **Empirical** — actual test corpus pass count from `tests/unit/test_precheck.py` (123 lines; 4 test classes; 13 tests). C-1a verification/ subdir convention reused (NO frontmatter; H1 + bullets header; 6 sections).

## §2 Method

Test corpus enumerated by class (per `tests/unit/test_precheck.py`):

- `TestNoSelectStar` (3 tests) — REQ-002 rule `no_select_star` (precheck.py L113); `SELECT *` rejection + `COUNT(*)` exempt + explicit-columns positive case
- `TestRequireTimeRange` (5 tests) — REQ-002 rule `require_time_range` (precheck.py L124); biz_dws fact-table missing time predicate rejection + `data_date` / `month` time-column positive cases + signal_tables (L31-37 registry) exempt + biz_dwd dimension table exempt
- `TestRequireLimit` (4 tests) — REQ-002 rules `require_limit` (L134; warning) + `limit_too_large` (L155; warning, threshold 1000); detail SELECT without LIMIT warns + GROUP BY exempt + COUNT(*) exempt + LIMIT 5000 triggers limit_too_large
- `TestParseFailureGracefulFallback` (1 test) — REQ-002 rule `sqlglot_parse_failed` (L102+L106; graceful degradation); unparseable SQL does NOT block (warning, not error)

Total: **3 + 5 + 4 + 1 = 13 tests** ran. Execution per `runbook.md §2 Health Check`:

```bash
uv run pytest tests/unit/test_precheck.py -q
```

Pass rate derived by direct test outcome inspection. No DB contact (L1b is sqlglot AST static; pre-DB layer like L1).

## §3 Results

**Basis: Empirical** (per `tests/unit/test_precheck.py` 13-test corpus).

| Rule ID | Test Class | Count | Pass | Severity |
|---|---|---|---|---|
| `no_select_star` | TestNoSelectStar | 3 | 3 (100%) | Error (P0; reject) |
| `require_time_range` | TestRequireTimeRange | 5 | 5 (100%) | Error (P0; reject) |
| `require_limit` | TestRequireLimit (3 of 4) | 3 | 3 (100%) | Warning (P1; advisory) |
| `limit_too_large` | TestRequireLimit (1 of 4) | 1 | 1 (100%) | Warning (P1; advisory) |
| `sqlglot_parse_failed` | TestParseFailureGracefulFallback | 1 | 1 (100%) | Warning (graceful) |
| **Total** | — | **13** | **13 (100%)** | 2 Error + 3 Warning |

All 5 rule IDs from `spec.yml` REQ-002 enumerated have direct test coverage (5/5 = 100% rule-ID empirical coverage; richer than C-1a L1 keyword coverage 9/16 = 53%).

## §4 Observations

### Positive null on rule count alignment (contrast to C-1a §4.1)

Per `spec.yml` REQ-002 claim ("5 rule IDs: no_select_star / require_time_range / require_limit / limit_too_large / sqlglot_parse_failed") ↔ `precheck.py` implementation (5 rule IDs at L113 / L124 / L134 / L155 / L102+L106 graceful fallback) — **NO SUT-spec drift on rule count axis** (opposite of C-1a §4.1 keyword count drift where spec said 14 but `_BLOCKED` regex had 16+SET SESSION = 17). Positive null strengthens REQ-002 verification claim.

### §4.1 SUT-runbook drift on `limit_too_large` threshold

Evidence chain (3 source triangulation):
- **B-1 commit `c961dfc` runbook §3 line 99**: "`limit_too_large: ...` — LIMIT > threshold (currently 10000); **warning only**; tunable per query pattern"
- **`precheck.py` L155**: `if limit_value > 1000:` (threshold = 1000)
- **`tests/unit/test_precheck.py` L111** (`test_limit_too_large_warns`): uses `LIMIT 5000` to trigger warning (5000 > 1000 fires per precheck.py; would NOT fire under runbook's claimed 10000 threshold)

**Magnitude**: 10× discrepancy (10000 runbook claim vs 1000 precheck.py authoritative). `precheck.py` + `test_precheck.py` form internally-consistent SUT pair; runbook §3 line 99 wording is the outlier.

**Disposition** (per C-1a §4.1 SUT-spec drift precedent): F-7 cluster amend §4.1 observation candidate; **NOT new M4-FU entry** (orthogonal to existing 6 M4-FU registry candidates; consistent with C-1a §4.1 disposition); **NOT modified in C-1b execution** (batch boundary discipline 守约: current C-1b batch does NOT modify B-1 c961dfc committed content). Reconcile path: Phase F-7 closure cumulative amend OR independent post-M4-BC small docs PR correcting runbook §3 L99 wording 10000 → 1000.

### Additional exemption mechanism observations

- `require_time_range` exempts 2 categories: (a) signal_tables (3 hardcoded at `precheck.py` L31-37: `dws_qcm_preprocessed_data` / `dws_qcm_etl_metrics` / `dws_qcm_ready_signal`) per `test_signal_table_no_time_required`; (b) non-biz_dws-fact tables (biz_dwd dim tables / non-`dws_qcm_*` names) per `test_dimension_table_no_time_required` + helper `_is_biz_dws_fact_table` at L62-70
- `require_limit` exempts via `_has_aggregation` helper at L77-80 (GROUP BY clause OR any `exp.AggFunc` including COUNT) per `test_aggregate_without_limit_clean` + `test_count_aggregate_without_limit_clean`

## §5 Cross-references

- `capabilities/data-agent/safe-sql/spec.yml` REQ-002 — "L1b sqlglot AST precheck enforces 5 rule IDs (no_select_star / require_time_range / require_limit / limit_too_large / sqlglot_parse_failed)" (per §4 positive null finding)
- `capabilities/data-agent/safe-sql/contracts/behavior.feature` L35-42 — REQ-002 Gherkin scenario (require_time_range biz_dws fact-table missing time predicate)
- `capabilities/data-agent/safe-sql/runbook.md` §3 L1b block (L92-107; landed via B-1 commit `c961dfc`) — 5 rule IDs documented + line 99 SUT-runbook drift evidence (§4.1 disposition)
- `src/mj_agent/tools/sql/precheck.py` (canonical 必停 surface; read-only):
  - signal_tables frozenset registry: L31-37
  - `_all_time_columns` / `_is_biz_dws_fact_table` / `_references_any_column` / `_has_aggregation` helpers: L58-80
  - `no_select_star` rule: L113-117
  - `require_time_range` rule: L124-127
  - `require_limit` rule (warning): L134-137
  - `limit_too_large` rule (warning; authoritative threshold = 1000): L155-159
  - `sqlglot_parse_failed` graceful fallback: L102 + L106
- `tests/unit/test_precheck.py` — 123 lines / 4 classes / 13 tests (3 + 5 + 4 + 1) — empirical pass rate source (100% rule-ID coverage)
- `policies/data-boundary.md` — 数据-LLM 三原则 + 4 项必停 governance
- `decisions/ADR-006_Fail_Safe_Reads.md` — 4-layer defense origin (L1b sqlglot AST is layer 2 per ADR-006 §Component judge rule mirror)

## §6 Forward

This evidence file (C-1b) is the second of the safe-sql verification cluster (after C-1a):

- **C-1a** (`2026-05-23_l1_pass_rate.md`; 80 lines; commit `82ff0ab`) — L1 regex guardrail empirical pass rate (REQ-001)
- **C-1b** (this file) — L1b sqlglot precheck empirical pass rate (REQ-002)
- **C-1c** (next) — SQL injection security audit (cross-layer L1+L1b+L3+L4); will live at `evidence/security/2026-05-23_sql_injection_audit.md` (first file in `security/` subdir; reuses verification/ subdir convention precedent — NO YAML frontmatter; H1 + bullets header; 6 sections)

Stage C cluster trajectory: C-1a → C-1b (this) → C-1c → C-2 (biz-catalog freshness) → C-3 (llm-provider endpoint probe) → C-4 (docker-compose smoke) → C-5 (mcp-server-governance Q2 audit). Stage C close → PR #M4-BC with 12 commits cumulative.
