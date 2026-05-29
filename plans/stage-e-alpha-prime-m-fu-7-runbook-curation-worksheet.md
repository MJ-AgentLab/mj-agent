---
type: planning-worksheet
slug: stage-e-alpha-prime-m-fu-7-runbook-curation
summary: M-FU#7 owner curation worksheet — 15 critical|high × unautomated scenarios × 4-field justification (原因 / 替代验证手段 / 升级触发条件 / 预计时间) per bdd-tdd.md L121; SDD scaffold-only per R-13-3 Option (b); owner (Zack) authors domain content + writes to per-capability runbook.md; E-0b verify = G22 dry-run WARN → 0.
owner: ranzuozhou
created: 2026-05-28
updated: 2026-05-28
state: active
track: shared
related_m_fu:
  - M-FU#7 — M4-FU-RUNBOOK-JUSTIFICATION-CURATE-ALL-PILOTS (primary;G22 prereq)
  - M-FU#1 — M4-FU-LLM-PROVIDER-TRACE-YML-BDD-COMPLETE (S12 requires M-FU#1 quote fix first)
  - M-FU#4 — M4-FU-G21-EVIDENCE-PASS-RATE-STRICT (G21 justification location resolved post §0 → same runbook source per L121+L160+L161)
---

# Stage E α' M-FU#7 Runbook Curation Worksheet

> SDD scaffold-only per R-13-3 Option (b) + R-13-10 SDD/product boundary。Owner (Zack)
> authors 4-field domain content per scenario based on observable hints provided;writes
> final justifications to per-capability `runbook.md`。 E-0b verify (SDD task) = re-run
> G22 dry-run → expect WARN → 0。

## Curation Target

- **Scope**: 15 critical|high × unautomated scenarios across 4 pilots
  (mcp-server-governance medium-only excluded per D-3 R-9-1 filter scope)
- **Predicate** (per bdd-tdd.md L121): justification 4-field 段落 in runbook.md:
  - **原因** — Why this scenario is currently unautomated
  - **替代验证手段** — Existing alternative verification (unit tests / manual / etc.)
  - **升级触发条件** — When automation should land (Phase / event / dependency)
  - **预计时间** — Estimated automation target timeline
- **G21 justification coupling** (post §0 resolution): G21 evidence pass_rate fallback
  uses SAME runbook.md justification source per bdd-tdd.md L160 + L161 parsimonious
  reading → E-1 G21 flip ALSO benefits from this worksheet (NOT independent
  justification mechanism per M-FU#4 reduced scope)

## How Owner Uses This Worksheet

1. Per scenario below, author 4-field justification using observable hints + domain knowledge
2. Format suggested for runbook.md (insert under existing §3 / new §7 per runbook structure):
   ```markdown
   ### G22 Justification: <Scenario Name>

   - **原因**: <domain explanation>
   - **替代验证手段**: <existing verification mechanisms>
   - **升级触发条件**: <automation trigger condition>
   - **预计时间**: <estimated timeline>
   ```
3. Write to corresponding pilot's `runbook.md`
4. Signal owner curation complete → SDD runs E-0b verify (G22 dry-run → expect 0 WARN)
5. E-1 G21 flip + E-2 G22 flip unblocked post-verify

---

## Pilot 1: safe-sql (6 scenarios; 4 critical + 2 high)

`capabilities/data-agent/safe-sql/runbook.md` (current 255 lines)

### S1 — L1 regex guardrail rejects blocked-keyword statement before DB contact
- **REQ**: REQ-001 / **Risk**: critical / **Adapter**: python
- **Observable hints**:
  - Existing tests: `tests/unit/test_guardrail.py` (TestAccepted + TestRejected + TestTableLevelAllowlist;~28 cases per trace.yml L30-39)
  - TBD-M3: `tests/bdd/data_agent/safe_sql/safe_sql.feature::<scenario>` (per trace.yml L40)
  - Likely automation pattern: pytest-bdd step defs landing Phase M3
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S2 — L1b precheck rejects biz_dws fact-table query missing time-column predicate
- **REQ**: REQ-002 / **Risk**: critical / **Adapter**: python
- **Observable hints**:
  - Existing tests: `tests/unit/test_precheck.py` (TestNoSelectStar + TestRequireTimeRange + TestRequireLimit + TestParseFailureGracefulFallback;~13 cases per trace.yml L58-61)
  - TBD-M3: pytest-bdd step defs
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S3 — L3 connection enforces read-only transaction + bounded timeouts via DSN options
- **REQ**: REQ-003 / **Risk**: critical / **Adapter**: python
- **Observable hints**:
  - Existing tests: **NONE currently** (TBD-M3 markers in trace.yml L80-83: test_dsn_options.py + test_readonly_cursor.py)
  - Hint: connection-layer test infrastructure may need build-out
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S4 — L4 statement_timeout cancellation translates to Chinese self-correction hint
- **REQ**: REQ-004 / **Risk**: critical / **Adapter**: python / **@reference-contract**
- **Observable hints**:
  - Existing tests: TBD-M3+M4 contract test markers (trace.yml L110-111: test_execute_sql_timeout.py + test_safe_sql_grant_visibility.py live_db gated)
  - **reference_contracts**: mj-system R__analyst_permissions.sql cross-repo dependency
  - Hint: live_db gating likely affects 升级触发条件
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S5 — execute_sql return envelope contains 8 required keys with documented types
- **REQ**: REQ-005 / **Risk**: high / **Adapter**: python
- **Observable hints**:
  - Existing tests: TBD-M3 envelope tests markers (trace.yml L128-130)
  - Hint: envelope schema validation likely deferred to Phase M3 envelope test landing
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S6 — handle_sql_tool_errors middleware converts tool ValueError into ToolMessage
- **REQ**: REQ-006 / **Risk**: high / **Adapter**: langchain-agent / **ADR**: ADR-029
- **Observable hints**:
  - Existing tests: `tests/unit/test_tool_error_middleware.py` (5+ cases TestValueErrorConversion / TestRuntimeErrorConversion / TestUnexpectedExceptionFallback per trace.yml L147-151)
  - TBD-M3: `test_middleware_wrap_integration.py` + smoke tests
  - Hint: middleware behavior partially covered;BDD-level integration deferred
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

---

## Pilot 2: biz-catalog (3 scenarios; 3 high)

`capabilities/data-agent/biz-catalog/runbook.md` (current 192 lines)

### S7 — load_catalog rejects YAML whose root parses to a list (not a mapping)
- **REQ**: REQ-001 / **Risk**: high / **Adapter**: python
- **Observable hints**:
  - Catalog loader behavior;likely covered by existing catalog tests
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S8 — Catalog signal_tables must resolve in live biz_dws
- **REQ**: REQ-002 / **Risk**: high / **Adapter**: python / **@gated:live_db**
- **Observable hints**:
  - live_db gating = automation requires live DB fixture (Phase M3+ when test infra ready)
  - Hint: live_db gating naturally explains "升级触发条件"
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S9 — Active SKILL bodies reference only resolvable catalog symbols and DB tables
- **REQ**: REQ-003 / **Risk**: high / **Adapter**: runtime-skill / **@gated:live_db**
- **Observable hints**:
  - runtime-skill adapter + live_db gating;cross-validation
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

---

## Pilot 3: llm-provider (3 scenarios; 3 high) ★ S12 requires M-FU#1 fix first

`capabilities/data-agent/llm-provider/runbook.md` (current 151 lines)

### S10 — Ark provider raises clear LLMConfigError when both ARK_API_KEY and LLM_API_KEY are empty
- **REQ**: REQ-001 / **Risk**: high / **Adapter**: python / **ADR**: ADR-027
- **Observable hints**:
  - ADR-027 context: provider abstraction;config error class established
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S11 — Local provider constructs ChatOpenAI without extra_body.thinking
- **REQ**: REQ-002 / **Risk**: high / **Adapter**: python / **ADR**: ADR-027
- **Observable hints**:
  - ADR-027 context: vLLM/SGLang/Ollama don't accept thinking param
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S12 — `effective_llm_api_key returns "EMPTY" sentinel for local provider when LLM_API_KEY is empty` ★ M-FU#1 quote fix prereq
- **REQ**: REQ-003 / **Risk**: high / **Adapter**: python
- **★ Prereq**: M-FU#1 trace.yml L67 quote fix (single → double quotes around EMPTY;mechanical SDD task in E-0a) lands BEFORE this scenario surfaces in G22 14W → 15W
- **Observable hints**:
  - "EMPTY" sentinel design choice;config edge case
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

---

## Pilot 4: docker-compose (3 scenarios; 3 high)

`capabilities/infrastructure/docker-compose/runbook.md` (current 208 lines)

### S13 — DEV profile loads with explicit -f chain + --env-file
- **REQ**: REQ-001 / **Risk**: high / **Adapter**: docker-container / **ADR**: ADR-026
- **Observable hints**:
  - ADR-026 4-file compose profile pattern;DEV/TEST/PROD layering
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S14 — Postgres healthcheck rejects half-initialized DB
- **REQ**: REQ-002 / **Risk**: high / **Adapter**: docker-container
- **Observable hints**:
  - Docker healthcheck pattern;init script + readiness probe
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

### S15 — Postgres init handles password with shell metacharacters unmangled
- **REQ**: REQ-003 / **Risk**: high / **Adapter**: docker-container / **ADR**: ADR-030
- **Observable hints**:
  - ADR-030 secrets pipeline context;2-bundle trust-boundary split
- **4-field (owner authors)**:
  - **原因**:
  - **替代验证手段**:
  - **升级触发条件**:
  - **预计时间**:

---

## Completion Signaling

Once all 15 × 4-field justifications authored + written to corresponding runbook.md
files:

1. **Owner signal**: "M-FU#7 runbook curation complete (all 15 scenarios across 4 pilots)"
2. **SDD E-0b verify task**:
   - Re-run G22 dry-run: `uv run python scripts/sdd/check_bdd_unautomated.py --all`
   - Expect: **0P / 0W / 0F SKIP** (or per actual scenario count post M-FU#1 fix)
   - OR if WARN persists: investigate per-scenario which 4-field is missing/insufficient
3. **Unblocks**:
   - E-1 G21 BLOCKING flip (per resolved G21-justification = runbook source coupling)
   - E-2 G22 BLOCKING flip

## Cross-Reference

- bdd-tdd.md L121 (G22 justification spec — 4 fields)
- bdd-tdd.md L161 (G21 justification fallback — same runbook source per L160 parsimony)
- bdd-tdd.md L108-111 (risk-level automation thresholds — critical 100% / high 70% baseline)
- gates.md L62 (G23 phased M4→M6) + L63 (G24 immediate M4 blocking) + L96 (Phase M4)
- plans/[PLAN]_spec_anchored_refactor.md (Stage E α' outline § + 18 M-FU registry)

> 本 worksheet 是 planning artifact;NOT canonical contract;owner authoring 完成后 final
> content 进 capabilities/*/runbook.md (capability product domain;owner workstream per
> R-13-3 + R-13-10)。
