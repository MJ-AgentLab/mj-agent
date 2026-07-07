---
type: capability-design
capability: data-agent.safe-sql
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-07-07
---

# Design: Safe SQL 4-Layer Guardrails

> Phase M1 baseline (≤ 200 lines per R-G3 ceiling).

## §1 Context

mj-agent is a data agent letting analysts explore the upstream business
warehouse (biz domain) through natural language. The LLM generates SQL which is
executed against a read-only PostgreSQL connection. **Without strong guardrails,
LLM-generated SQL is a string-to-DB execution path** — a category of risk
distinct from human-written SQL.

**Threats**：

1. Generated SQL contains DDL/DML/DCL (intentional or accidental hallucination)
2. Generated SQL omits time predicate on a billion-row fact table → 60s timeout +
   wasted DB resources
3. Generated SQL uses `SELECT *` → unbounded payload back to LLM (context blast)
4. Generated SQL multi-statement injection
5. Connection accidentally allows write transactions
6. Tool exceptions crash the graph instead of being surfaced to LLM

**Non-threats（out of scope）**：

- Comment-hiding / string-literal-hiding SQL injection (per `guardrail.py:27-31`
  doc — would require full parser; sqlglot in L1b mitigates parse-level)
- Multi-user privilege escalation (single-user `analyst` role; no per-request
  identity)
- Application-level rate limiting (separate concern)

## §2 Decision

**4-layer defense + envelope contract + middleware wrapper**：

| Layer | Mechanism | Source | Owner |
|---|---|---|---|
| L1 | regex + AST-allowlist guardrail (`is_safe_select`) | `tools/sql/guardrail.py` | mj-agent |
| L1b | sqlglot AST precheck (`precheck_sql`) | `tools/sql/precheck.py` | mj-agent |
| L3 | DSN options on read-only connection | `integrations/mj_system_db.py` | mj-agent |
| L4 | role-level `statement_timeout` + GRANT | `mj-system:R__analyst_permissions.sql` | **upstream (reference contract)** |
| envelope | 8-key return contract (`execute_sql`) | `tools/sql/execute.py` | mj-agent |
| middleware | `ToolMessage` wrapper (ADR-029) | `middleware/tool_errors.py` | mj-agent |

**No L2 in mj-agent code** — L2 in the original ADR-006 4-layer model is
SKILL.md semantic guidance (which biz_dwd tables the agent may discuss). It's
not an execution-time guardrail; it's prompt-side instruction. Not in scope of
this capability's contract; governed by `data-agent.entry-points` (Phase 2+)
prompt adapter.

**Why these 4 layers + not fewer / more**：

- L1 alone is insufficient (regex misses semantic anti-patterns like SELECT *
  on fact tables → L1b complements)
- L1 + L1b alone are insufficient (LLM-generated SQL could still bypass via
  bugs / regex coverage gaps → L3 + L4 are DB-side fallback)
- L3 + L4 alone are insufficient (DB-side errors are slow to surface and don't
  prevent malformed SQL from being dispatched → L1 + L1b are agent-side fast
  rejection)

**Why timeout 60s / lock 5s / idle 10s**：tuned in early MVP via load testing
against biz_dws cardinality (Phase 0); not subject to change without HITL
(L3 cross-capability impact on UX). See `runbook.md` for tuning rationale.

## §3 Architecture

```
User natural-language question
      │
      ▼
[LangChain Agent (make_graph)]
      │  (LLM generates SQL string)
      ▼
[handle_sql_tool_errors middleware]  ──── ADR-029 (REQ-006)
      │                                    catches ValueError/RuntimeError
      ▼                                    returns ToolMessage (graph step survives)
[execute_sql(sql)]  ──── REQ-005 envelope
      │
      ├──► L1: is_safe_select(...)        ──── REQ-001
      │       └─► ValueError on reject
      │
      ├──► L1b: precheck_sql(...)         ──── REQ-002
      │       ├─► ValueError on errors
      │       └─► warnings → envelope.precheck_warnings
      │
      ├──► readonly_cursor()              ──── REQ-003 (L3 DSN options)
      │       └─► default_transaction_read_only=on / lock_timeout=5s / idle=10s
      │
      ├──► cursor.execute(sql)
      │       └─► psycopg.errors.QueryCanceled (60s)  ──── REQ-004 (L4 catch)
      │             └─► RuntimeError + Chinese hint
      │
      └──► return envelope (8 keys)       ──── REQ-005

Upstream (reference contract):                              ──── REQ-004 GRANT
  mj-system R__analyst_permissions.sql:
    - ALTER ROLE analyst SET statement_timeout='60s'
    - GRANT SELECT ON biz_dws.* + biz_dwd.{2 dim tables} TO analyst
```

**Key modules and freeze anchors (Phase M1 baseline; guardrail.py since modified for #280)**：

- `src/mj_agent/tools/sql/guardrail.py:42-151` — L1 regex + AST allowlist extraction (`_qualified_refs`; sqlglot-parse-fail → fail-closed; modified for #280)
- `src/mj_agent/tools/sql/precheck.py:58-159` — L1b AST + helpers
- `src/mj_agent/tools/sql/execute.py:56-127` — execute_sql pipeline + envelope
- `src/mj_agent/tools/sql/introspect.py:57-146` — GRANT visibility (REQ-004 sut-side)
- `src/mj_agent/integrations/mj_system_db.py:27-86` — L3 DSN + pool + rollback
- `src/mj_agent/middleware/tool_errors.py:32-86` — REQ-006 sync + async wrappers
- `src/mj_agent/prompts/system.md` — frontmatter only (v1.8 / active / deepseek-v3); body NOT touched (prompt-version-bump 必停)

**Cross-capability dependency (1 ref; R-G7 satisfied)**：

- `data-agent.biz-catalog` — REQ-002 `require_time_range` reads
  `qcm_catalog.yaml periods.*.time_column` via `_all_time_columns()` in
  `precheck.py:58-59`. catalog drift → REQ-002 BDD scenario breaks (intentional;
  catalog is L2-semantic SOR).

## §4 Tradeoffs

| Choice | Pros | Cons | Rationale |
|---|---|---|---|
| **A. Regex + AST hybrid (chosen)** | Fast reject path (regex) + semantic depth (AST); graceful parse-fail fallback | Two engines → maintenance cost | LLM-generated SQL is mostly well-formed; rare parse failures degrade to DB-side, not block |
| B. Single full parser only | Single source of truth | Slow per-call; parser bugs block valid SQL | Rejected — performance and graceful degradation matter more |
| C. Generate SQL via parameterized query builder | No string-to-DB at all | LLM less expressive; semantic-to-SQL gap large | Rejected — analysts need full SELECT expressiveness; constrained query builder defeats purpose of NL→SQL agent |
| **D. DSN options at session start (chosen)** | DB-side enforcement; can't bypass via client | Static config; can't tune per-query | Conservative is correct; per-query tuning is a future capability (out of scope here) |
| E. Application-level read-only check | More flexible | Application bugs → write path | Rejected — defense in depth requires DB-side |
| **F. Middleware wraps tools (chosen, ADR-029)** | Graph step survives; LLM self-correct loop works | One more layer to debug | Critical for UX — graph crashing on tool ValueError caused a frontend hang incident (2026-05-12; precipitating ADR-029) |
| G. Let exceptions propagate | Simpler stack | Graph crashes; UX disaster | Rejected — Production UX requires graceful tool errors |

## §5 Open Questions（revisit in Phase M3+）

1. **`statement_timeout_hit` envelope field always False on success path** — currently
   reserved for caller-side catch logic; should be set `True` in the RuntimeError
   path before raising? Or remain caller-set? (REQ-005 specifies current behavior;
   M3 contract test will lock).

2. **Per-table allowlist signature surface** — `is_safe_select` accepts
   `allowed_tables_per_schema` as optional kwarg; `execute_sql` always passes
   `settings.biz_allowed_dwd_tables`. Should `is_safe_select` make the kwarg
   required (force callers to be explicit)? Current backward-compat treats absent
   map as wildcard. (HITL on signature change because affects all callers.)

3. **Catalog drift impact on REQ-002** — `qcm_catalog.yaml periods.*.time_column`
   is the time-column SOR. If upstream renames a column (e.g. `data_date` →
   `stat_date`), catalog mirror updates → REQ-002 BDD scenario starts rejecting
   queries with old column names. Is this desired? Document expected drift cycle
   (catalog sync via `mj-agent-runtime-biz-catalog-sync` skill).

4. **Async middleware coverage** — **RESOLVED (#288, 2026-07-07)**。该缺口实际成灾：
   sync-only middleware 被 langchain factory 同时纳入 async 链，Chainlit/Studio 下每次
   工具调用在 tools 节点炸 `NotImplementedError`（前端永久转圈）。修复 = 单
   `SQLToolErrorMiddleware` 同时 override `wrap_tool_call` + `awrap_tool_call`
   （两个单侧实例并注册也不行——对侧模式各自炸）；async 路径由
   `tests/unit/test_agent_async_tool_path.py` 常驻回归。ADR-029 见 2026-07-07 amendment。

> Phase M2 will fill in adapter-side §BDD Rules + §TDD Rules per
> `sdd/adapters/{python,langchain-agent,bdd-tdd}.md`.
