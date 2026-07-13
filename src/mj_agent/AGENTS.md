# src/mj_agent/AGENTS.md

> Tool-neutral local constraints for `src/mj_agent/` runtime code — binds every AI agent
> working here (roster in root `AGENTS.md`). Codex discovers this file hierarchically
> (root → cwd); Claude Code imports it via the sibling `src/mj_agent/CLAUDE.md`. Rules live
> once in the kernel (`policies/` + `sdd/adapters/`) — this file only points.

## The 4 mj-agent-specific hard-stop surfaces (OWNER_APPROVAL_REQUIRED)

| Canonical enum | Path | Discipline |
|---|---|---|
| `sql-guardrail-relax` | `tools/sql/{guardrail,precheck}.py` | never relax unilaterally |
| `runtime-skill-content-change` | `skills/*/SKILL.md` body | propose → Owner approves → apply |
| `prompt-version-or-body-change` | `prompts/system.md` body or `version` | propose → Owner approves → apply |
| `biz-catalog-sync` | `biz_catalog/qcm_catalog.yaml` | mirror of the upstream dictionary; sync flow only |

Claude Code has these enforced by its harness (`ask` gates); Codex self-enforces per root
`AGENTS.md` boundary 3. The stop point is identical either way (`policies/ai-agent.md` §4).

## Data boundary (ADR-006 / ADR-009 — never bypass)

- biz-warehouse access ONLY through the agent tool chain
  `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`; read-only
  `analyst` role; no direct DB clients, no writes, no DDL (root `AGENTS.md` boundary 1).
- mj-agent's own memory PostgreSQL (checkpointer) is a separate capability — do not conflate
  it with the biz boundary.

## Loading contracts

- Runtime skills load via `load_skill()`, which strips frontmatter (gate A11,
  `sdd/adapters/runtime-skill.md`); never `open(SKILL.md).read()` directly.
- Active skill roster + count: single source of truth is `agent.py:_ACTIVE_SKILLS` — do not
  hardcode the list elsewhere.
- 4 freeze surfaces here carry `content_hash` anchors (prompt + runtime-skill contracts);
  body drift without a sanctioned re-freeze fails CI.

## Verification (either tool, from repo root)

```bash
uv run mypy src/mj_agent          # strict — CI gate
uv run ruff check src/mj_agent
uv run pytest tests/unit -q
```

## See also

- Root `AGENTS.md` · `src/mj_agent/CLAUDE.md` (same layer) · `policies/data-boundary.md`
- `policies/ai-agent.md` §4 (canonical 10-enum) + §7 (pre-flight verification discipline)
- `sdd/adapters/python.md` · `sdd/adapters/runtime-skill.md` · `sdd/adapters/prompt.md`
