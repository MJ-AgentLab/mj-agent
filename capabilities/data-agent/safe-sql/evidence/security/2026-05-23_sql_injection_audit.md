# safe-sql SQL Injection Attack Vector Audit (2026-05-23)

- **Stage**: Phase M4 Stage C unit C-1c
- **Branch**: `documentation/spec-anchored-refactor-m4-bc`
- **Outcome**: 7 attack vectors audited × 4 defense layers (L1+L1b+L3+L4); FIRST file in security/ subdir sets convention precedent; 1 §4.1 SUT-internal-docstring drift surfaced (execute.py L4-15 2-layer numbering vs spec/behavior/runbook 4-layer authoritative); cross-repo L4 reference-contract limitation acknowledged
- **Cluster**: safe-sql C-1a (L1 verification) / C-1b (L1b verification) / **C-1c (this; SQL injection audit closure)**

## §1 Goal + Scope

Audit `safe-sql` 4-layer defense-in-depth against canonical SQL injection attack vector taxonomy per spec.yml REQ-001/002/003/004 + behavior.feature 4 critical-risk scenarios. Cross-layer perspective: each attack vector evaluated against L1 (regex guardrail) + L1b (sqlglot precheck) + L3 (read-only connection) + L4 (statement_timeout + GRANT) coverage. C-1c **sets convention precedent for `security/` subdir** — inherits C-1a/b verification/ template (NO YAML frontmatter; H1 + Stage/Branch/Outcome/Cluster bullets; 6 sections) with §3 format adjustment: audit qualitative matrix (vs verification quantitative per-keyword/rule-ID table). Closes safe-sql C-1a/b/c cluster (Phase M4 outline §1 Stage C).

**Out of scope**: REQ-005 envelope schema verification (run-time data contract; not security boundary); REQ-006 middleware behavior (orthogonal to injection vectors; ADR-029). 4-layer GRANT (L4) authoritative source is cross-repo `mj-system/sql/migrations/repeatable/R__analyst_permissions.sql` per behavior.feature L4 `@reference-contract` — SUT-side audit limitation acknowledged.

## §2 Method

Per-layer canonical implementation references:

- **L1 regex guardrail** — `src/mj_agent/tools/sql/guardrail.py::is_safe_select()` (L49-111); `_BLOCKED` regex (L36-40; 16 keywords + SET SESSION special); `_STMT_START` (L33); `_QUAL_REF` (L43-46); multi-statement detection (L73-74)
- **L1b sqlglot precheck** — `src/mj_agent/tools/sql/precheck.py::precheck_sql()` (L83-141); 5 rule IDs at L113 (no_select_star) / L124 (require_time_range) / L134 (require_limit warn) / L155 (limit_too_large warn) / L102+L106 (sqlglot_parse_failed graceful)
- **L3 read-only connection** — `src/mj_agent/integrations/mj_system_db.py::readonly_cursor()`; DSN options `default_transaction_read_only=on` + `lock_timeout=5000ms` + `idle_in_transaction_session_timeout=10000ms` per spec.yml REQ-003
- **L4 statement_timeout + GRANT** — cross-repo `mj-system/sql/migrations/repeatable/R__analyst_permissions.sql` (`ALTER ROLE analyst SET statement_timeout='60s'` + table-level GRANTs); SUT-side timeout catch at `execute.py` L106-110 (psycopg.errors.QueryCanceled → RuntimeError + Chinese self-correction hint)

Attack vector taxonomy derived from canonical SQL injection categories (UNION-based / Boolean-blind / Time-based / Stacked queries / Comment-based / Out-of-band exfiltration / Stored procedure abuse). Per-vector × per-layer coverage evaluated against empirical test corpus (L1+L1b unit tests; L3 partial integration tests; L4 reference-contract).

## §3 Results

**Basis: Mixed** (L1+L1b Empirical via `tests/unit/test_guardrail.py` 23 tests + `tests/unit/test_precheck.py` 13 tests; L3 Partial Empirical via `tests/integration/test_mj_system_db.py` 5 tests gated on `live_db`; L4 Reference-contract per `behavior.feature` L4 `@reference-contract` cross-repo).

Cross-layer SQL injection attack vector × defense layer coverage matrix:

| Attack Vector | L1 (regex) | L1b (sqlglot) | L3 (read-only) | L4 (timeout/GRANT) | Per-row Basis |
|---|---|---|---|---|---|
| **UNION-based** (e.g. `SELECT x UNION SELECT secrets`) | Allow (UNION not blocked) | Partial (no_select_star fires on UNION SELECT *) | Block (read-only refuses writes; SELECT-only enforced) | Cancel (60s timeout if exfil large) | L1+L1b Empirical / L3 Partial / L4 Reference |
| **Boolean-blind** (`AND 1=1` / `AND SLEEP(1)`) | Allow (no DML keyword) | Allow (passes; rule set focused on biz schema) | Block (read-only; no side effects) | Cancel (60s timeout on slow SLEEP-based extraction) | L3 Partial / L4 Reference |
| **Time-based** (`pg_sleep(70)` or `WAITFOR DELAY`) | Allow (no DML keyword) | Allow (passes; function call not blocked) | N/A (no DDL bypass needed) | **Cancel (60s statement_timeout; primary defense)** | L4 Reference-contract (primary) |
| **Stacked queries** (`SELECT 1; DROP TABLE x`) | **Block** (multi-statement at guardrail.py:73-74) | Block (sqlglot parse rejects second stmt) | N/A (never reaches DB) | N/A | L1+L1b Empirical |
| **Comment-based** (`-- ` / `/* */` bypass attempts) | **Block** (post-guardrail comments preserved; UNION + comment still hits multi-stmt OR _BLOCKED) | Partial (sqlglot strips comments; may unmask hidden DML) | Block (read-only fallback) | N/A | L1 Empirical (primary) |
| **OOB exfiltration** (`COPY x TO PROGRAM` / `dblink`) | **Block** (COPY in _BLOCKED list at guardrail.py:38) | N/A | Block (read-only refuses COPY) | N/A | L1 Empirical (primary) |
| **Stored procedure abuse** (`CALL sp_inject(...)`) | **Block** (CALL in _BLOCKED list at guardrail.py:38) | N/A | Block (read-only refuses sp_inject side effects) | N/A | L1 Empirical (primary) |

Coverage summary: **7 attack vectors × 4 layers = 28 coverage cells**. Per-layer aggregate: L1 blocks 4 vectors primary + 2 partial; L1b partial on 2 vectors (UNION + Comment); L3 blocks 4 vectors fallback; L4 blocks 2 vectors primary (Time + Boolean-blind). Per-vector aggregate: 5 of 7 vectors have ≥ 2 layer coverage (defense-in-depth); Time-based + Boolean-blind rely on L4 (cross-repo reference-contract) as primary defense.

## §4 Observations

### §4.1 SUT-Internal-Docstring Drift (#C1c-4; 3rd Distinct Drift Type)

3-source triangulation evidence:

- **`src/mj_agent/tools/sql/execute.py` L4-15 module docstring** (verbatim):
  > "1. L1 regex guardrail (`guardrail.is_safe_select`) — blocks DML/DDL... / 2. L2 sqlglot precheck (`precheck.precheck_sql`) — Component-Judge-aligned static rules... / 3. Read-only psycopg cursor with DB-side `statement_timeout = 60s`"

  Uses **2-layer numbering** (1./2./3.); labels sqlglot as "L2" (not "L1b"); merges L3 read-only + L4 statement_timeout into single bullet 3.

- **`spec.yml` REQ-001/002/003/004** + **`behavior.feature` 6 BDD scenarios** + **B-1 c961dfc `runbook.md` §3 + §6** — all consistently use authoritative **4-layer naming** (L1 / L1b / L3 / L4).

**Discrepancy summary**: execute.py docstring is the outlier; spec.yml + behavior.feature + runbook form authoritative 4-layer SoT triplet.

**Disposition** (per C-1a §4.1 SUT-spec + C-1b §4.1 SUT-runbook cumulative precedent): F-7 cluster amend §4.1 observation candidate; **NOT new M4-FU entry** (orthogonal to existing 6 M4-FU registry candidates; consistent with C-1a/b §4.1 disposition); **NOT modified in C-1c execution** (batch boundary discipline 守约: current C-1c batch does NOT modify execute.py canonical surface). Reconcile path: Phase F-7 closure cumulative amend OR independent post-M4-BC small docs PR correcting execute.py L4-15 module docstring 2-layer "1./2./3." → 4-layer "L1/L1b/L3/L4" naming alignment.

### §4.2 Cross-Layer Defense-in-Depth Analysis

Cross-layer combination scenarios (multi-layer required for full defense):

- **Stacked queries**: L1 blocks via multi-statement detection (guardrail.py:73-74) AND L1b would reject second statement at sqlglot parse — but L1 fires first; L1b never reaches in normal path
- **Comment-based bypass**: L1 strip trailing `;` only (L71-72); comments preserved; if `-- DROP TABLE` hidden, L1 `_BLOCKED` regex still catches DROP keyword; L1b sqlglot strips comments before AST eval — could unmask hidden DML if L1 missed (defense-in-depth)
- **UNION exfiltration**: L1 allows UNION (not in `_BLOCKED`); L1b `no_select_star` partial defense if SELECT *; L3 read-only blocks DB writes triggered by UNION subquery; L4 cancels long-running exfiltration

Single-layer-sufficient scenarios (no cross-layer dependency):
- Comment-based standalone, Stored-proc abuse, OOB exfiltration — all blocked at L1 alone (regex sufficient for `--` / `CALL` / `COPY` keywords)

**Cross-repo gap**: L4 GRANT + statement_timeout authoritative source is `mj-system/sql/migrations/repeatable/R__analyst_permissions.sql` per behavior.feature L4 `@reference-contract`; mj-agent SUT-side cannot empirically verify L4 — only consume timeout-catch via `execute.py` L106-110. Audit coverage limited to: (a) `psycopg.errors.QueryCanceled` catch wiring; (b) Chinese self-correction hint string; (c) error envelope shape. Actual `statement_timeout='60s'` enforcement + table-level GRANT enforcement live in upstream repo.

### §4.3 Edge Cases

- **SET SESSION special case**: per C-1a §4.1 observation, `_BLOCKED` regex at guardrail.py:38 includes `\bSET\s+SESSION\b` as separate pattern (beyond 16 main keywords; e.g. `SET SESSION authorization` bypass attempt blocked)
- **Empty SQL**: handled at guardrail.py:77 (rejects empty/whitespace-only before regex evaluation)
- **Sqlglot parse failure graceful fallback**: precheck.py L102+L106 — unparseable SQL does NOT block (warning only); rationale: L1 already rejected most garbage; sqlglot version drift should not break execution (graceful degradation; DB is ultimate validator)

## §5 Cross-references

- `capabilities/data-agent/safe-sql/spec.yml` — REQ-001 (L1 regex) / REQ-002 (L1b sqlglot 5 rule IDs) / REQ-003 (L3 read-only DSN) / REQ-004 (L4 statement_timeout + GRANT reference-contract)
- `capabilities/data-agent/safe-sql/contracts/behavior.feature` 6 BDD scenarios:
  - L23-31 REQ-001 `@CTR-sql-guardrail @risk:critical @adapter:python` (L1 DROP rejection)
  - L35-42 REQ-002 `@CTR-sql-guardrail @risk:critical @adapter:python` (L1b require_time_range)
  - L46-54 REQ-003 `@CTR-execute-sql @risk:critical @adapter:python` (L3 DSN options enforcement)
  - L58-65 REQ-004 `@CTR-execute-sql @risk:critical @adapter:python @reference-contract` (L4 statement_timeout)
  - L69-81 REQ-005 `@CTR-execute-sql @risk:high` (envelope schema; OUT OF SCOPE)
  - L85-93 REQ-006 `@CTR-python @risk:high @adr:ADR-029` (middleware; OUT OF SCOPE)
- `capabilities/data-agent/safe-sql/runbook.md` (B-1 commit `c961dfc` landed):
  - §3 6 symptom blocks (L1 / L1b / L4 statement_timeout / Generic DB / Chainlit / Catalog drift)
  - §6.1 L2 Schema/Table Whitelist Extension SOP (L199-214)
  - §6.2 L3 Statement Timeout & Lock Timeout Tuning SOP (L216-232)
  - §6.3 L4 Upstream DB Connection & Index Tuning SOP (L234-250)
- `src/mj_agent/tools/sql/guardrail.py` — L33 `_STMT_START` / L36-40 `_BLOCKED` (16 keywords + SET SESSION) / L43-46 `_QUAL_REF` / L73-74 multi-stmt / L93-109 allowlist
- `src/mj_agent/tools/sql/precheck.py` — L31-37 signal_tables / L58-80 helpers / L113 no_select_star / L124 require_time_range / L134 require_limit / L155 limit_too_large (threshold 1000) / L102+L106 graceful parse_failed
- `src/mj_agent/tools/sql/execute.py` — REQ-005 envelope at L118-127; L102-110 QueryCanceled timeout catch; **L4-15 module docstring 2-layer drift per §4.1**
- `src/mj_agent/integrations/mj_system_db.py` — L3 `readonly_cursor()` + DSN options
- `tests/unit/test_guardrail.py` (23 tests; L1 empirical; per C-1a evidence) + `test_precheck.py` (13 tests; L1b empirical; per C-1b evidence)
- `tests/integration/test_mj_system_db.py` (5 tests gated on `live_db`; L3 partial empirical: list_biz_tables / describe_biz_table / execute_sql + 2 L1 reject integration confirmations)
- Cross-repo `mj-system/sql/migrations/repeatable/R__analyst_permissions.sql` — L4 GRANT + statement_timeout authoritative source per spec.yml REQ-004 `reference_contract` block; SUT-side cannot empirically verify
- `policies/data-boundary.md` — 数据-LLM 三原则 + 4 项必停 governance
- `decisions/ADR-006_Fail_Safe_Reads.md` — 4-layer defense origin
- `decisions/ADR-009_Biz_Domain_As_Primary_Data_Source.md` — biz domain scope
- `decisions/ADR-029_Tool_Error_Surfacing_To_LLM.md` — REQ-006 middleware (OUT OF SCOPE for this audit)

## §6 Forward

This evidence file (C-1c) closes the safe-sql verification + security cluster:

- **C-1a** (`evidence/verification/2026-05-23_l1_pass_rate.md`; 80 lines; commit `82ff0ab`) — L1 regex guardrail empirical pass rate (REQ-001); §4.1 SUT-spec drift
- **C-1b** (`evidence/verification/2026-05-23_l1b_pass_rate.md`; 95 lines; commit `92ebb9f`) — L1b sqlglot precheck empirical pass rate (REQ-002); §4.1 SUT-runbook drift (10× magnitude)
- **C-1c** (this file) — SQL injection cross-layer audit (REQ-001/002/003/004); §4.1 SUT-internal-docstring drift (execute.py docstring 2-layer vs 4-layer authoritative); FIRST file in `security/` subdir setting convention precedent

**Stage C cluster trajectory**: C-1a → C-1b → C-1c (this; safe-sql closure) → C-2 (biz-catalog freshness; `evidence/runtime/2026-05-23_freshness_check.md`; ~60-100 lines) → C-3 (llm-provider endpoint probe; `evidence/runtime/2026-05-23_endpoint_probe.md`; ~80-120 lines) → C-4 (docker-compose smoke; `evidence/runtime/2026-05-23_compose_smoke.md`; ~100-150 lines) → C-5 (mcp-server-governance Q2 audit; `evidence/runtime/2026-05-23_quarterly_audit_q2.md`; ~120-180 lines).

Stage C close → m4-bc累计 12 commits → user-driven Step 13 (push + PR #M4-BC targeting develop)。Cumulative 3 drift findings (C-1a SUT-spec / C-1b SUT-runbook / C-1c SUT-internal-docstring) feed F-7 cluster amend epistemic value-transfer per cross-Stage §7 pre-flight discipline observation。
