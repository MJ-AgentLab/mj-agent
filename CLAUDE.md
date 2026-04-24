# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project

`mj-agent` is the MJ-AgentLab data agent — a LangChain 1.x + LangGraph 1.1.8
Python 3.13 service (managed with `uv`) that lets internal analysts explore
the mj-system business metrics warehouse through natural language. Currently
in **Phase 0 Foundation** per `docs/mj-agent-roadmap-v1.6.md`.

## Architecture

```
Entry   : LangGraph Studio (langgraph.json) / CLI
Runtime : langchain.agents.create_agent(model, tools, system_prompt)
Skills  : src/mj_agent/prompts/system.md + src/mj_agent/skills/*/SKILL.md
Tools   : src/mj_agent/tools/sql/{guardrail,execute,introspect}.py
Infra   : src/mj_agent/integrations/mj_system_db.py — psycopg pool, read-only
Config  : src/mj_agent/config.py — pydantic-settings over .env
```

The agent is wired in `src/mj_agent/agent.py` — a ~20-line file that composes
the system prompt, loads the active skills, and returns the compiled
LangGraph via `create_agent`. That symbol is what Studio imports.

## Data boundary

mj-agent accesses only the mj-system biz domain through the `analyst`
PostgreSQL role. Visibility is enforced at four layers (see ADR-006):

| Layer | Mechanism | Location |
| --- | --- | --- |
| L1 guardrail | regex: single-statement, SELECT-only, schema allowlist | `tools/sql/guardrail.py` |
| L2 semantics | SKILL.md lists the visible tables | `skills/*/SKILL.md` |
| L3 connection | `default_transaction_read_only=on` | `integrations/mj_system_db.py` |
| L4 role | GRANT + `statement_timeout=60s` | mj-system `R__analyst_permissions.sql` |

Accessible schemas: `biz_dws` (all tables) + `biz_dwd` (two dimension tables
only — enforced DB-side). `biz_ods`, `biz_ads`, and any `ops_*` schema are
not reachable.

## Commands

```bash
uv sync                                    # install / lock dependencies
uv run langgraph dev                       # LangGraph Studio (local)
uv run pytest tests/unit                   # fast, no external deps
uv run pytest tests/integration            # needs live biz DB
uv run pytest tests/smoke -m smoke         # needs biz DB + LLM
uv run ruff check                          # lint
uv run mypy src/mj_agent                   # type-check
```

## LLM provider

mj-agent talks to Volcengine Ark's OpenAI-compatible endpoint (DeepSeek V3
as the default model). The `make_llm()` factory in `src/mj_agent/llm.py`
builds a `ChatOpenAI` instance with `base_url=ARK_BASE_URL`, the key from
`ARK_API_KEY`, and `extra_body.thinking` driven by `LLM_THINKING_ENABLED`.
Missing `ARK_API_KEY` raises `LLMConfigError` at graph build time.

## Environment variables

Aligned with mj-system's naming so co-deployment can merge .env files
safely: `POSTGRES_{DEV,TEST,PROD}_HOST/PORT` + `POSTGRES_ANALYST_USER/
PASSWORD` + `MJ_CONFIG_PROFILE`. See `.env.example` for the full list.

## Repo conventions

- Branches follow MJ-AgentLab's worktree model: `feature/<desc>` from
  `develop`, `hotfix/<desc>` from `main`.
- Commits follow Conventional Commits.
- ADRs live in `docs/adr/`; Phase 0 ships 000/001/002/003/006/008/009.
