# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project

`mj-agent` is the MJ-AgentLab data agent — a LangChain 1.x + LangGraph 1.1.8
Python 3.13 service (managed with `uv`) that lets internal analysts explore
the mj-system business metrics warehouse through natural language. Currently
in **Phase 0 Foundation** per `plans/mj-agent-roadmap-v1.6.md`; canonical
docs entry: `docs/INDEX.md`.

## Architecture

```
Entry   : LangGraph Studio (langgraph.json) / CLI
Runtime : langchain.agents.create_agent(model, tools, system_prompt)
Skills  : src/mj_agent/prompts/system.md + src/mj_agent/skills/*/SKILL.md
Tools   : src/mj_agent/tools/sql/{guardrail,execute,introspect}.py
Infra   : src/mj_agent/integrations/mj_system_db.py — psycopg pool, read-only
Config  : src/mj_agent/config.py — pydantic-settings over .env
```

The agent is wired in `src/mj_agent/agent.py`: `_build_system_prompt()`
concatenates `prompts/system.md` with the active skills, and `make_graph()`
calls `create_agent(model, tools, system_prompt)`. `make_graph` is the
symbol `langgraph.json` points at — Studio calls it lazily, so importing
the module never forces `make_llm()` (matters for unit tests and
type-checking with no `ARK_API_KEY`). The wired tool registry lives in
`src/mj_agent/tools/__init__.py:ALL_TOOLS` — `execute_sql`,
`list_biz_tables`, `describe_biz_table`.

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

`pyproject.toml` pins `addopts = "-m 'not smoke'"`, so plain `uv run pytest`
excludes smoke by default — pass `-m smoke` to opt in. `tests/conftest.py`
session fixtures `live_db` and `agent` *skip* (not fail) when
`POSTGRES_ANALYST_USER` / `ARK_API_KEY` are unset, so empty-env runs of
integration/smoke look green without actually exercising those paths.
CI (`.github/workflows/ci.yml`) currently runs only `python -m compileall`;
ruff / mypy / pytest are **local-only gates** for now.

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

- Branches follow MJ-AgentLab's worktree model: 5 types
  (`feature/bugfix/documentation/maintain/hotfix`). See
  `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0.md` §5
  for the branch ↔ commit-type alignment matrix.
- Commits follow `<type>(<scope>): <summary>` per
  `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0.md`
  (state: draft; promotion criteria in §9). Types:
  `feat / fix / perf / refactor / test / docs / infra`. Scopes derive
  from `src/mj_agent/` modules — see STANDARD §4 for the closed allowlist.
- ADRs live in `docs/adr/`; Phase 0 ships 000/001/002/003/006/008/009/010/011.
  See ADR-010 + matching `docs/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0.md`
  for the git/commit adoption rationale and Keep/Adapt/Defer matrix.
  See ADR-011 for the doc versioning + archive convention installed in v1.1
  of the Framework standard.

## Documentation

All canonical documentation follows
`docs/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md`
(derived from mj-system v5.0) for field semantics, and
`docs/rule/[STANDARD]_GitHub_Markdown_v1.0.md` for Markdown + YAML syntax
(GFM rendering target). Entry point: `docs/INDEX.md`.

Versioning rule (Framework v1.1 §4.2 + §5.6): types with `version` frontmatter
(STANDARD/SPEC/EVAL/CONTRACT/ASSESSMENT) carry `_vX.Y` in the filename. On
formal version evolution (HITL judgment at PR review), the old file moves to
`docs/archive/<original-subdir>/`, the new file lands as `_v<new>.md`,
`state` flips to `deprecated` on the archive copy, and corpus-wide references
are audited (Living updates to `_v<new>`; Frozen pins to `_v<old>`). Daily
edits stay in-place — the rename + archive ceremony fires only when the
change qualifies as substantive evolution. ADR-011 documents the rationale.

Key implications for code changes:

- **In-source canonical**: `src/mj_agent/skills/**/SKILL.md` and
  `src/mj_agent/prompts/*.md` carry YAML frontmatter and are governed as
  canonical documents. The loaders `load_skill` / `load_prompt` strip
  frontmatter via `python-frontmatter` before returning content — do not
  bypass them, do not read these files with `open().read()`. Companion
  `load_skill_meta` / `load_prompt_meta` return the frontmatter dict for
  documentation tooling (A7/A8 validation, INDEX generation in Phase 2).
- **Templates**: `docs/_templates/TEMPLATE_{ADR,SKILL,PROMPT,CONTRACT}.md`.
  Copy, don't improvise frontmatter.
- **PR gates**: the A1-A10 checklist in the STANDARD §7.1 applies to every
  PR touching canonical docs or in-source canonical files. PR templates
  already embed the checklist.
- **New skill**: create `src/mj_agent/skills/<name>/` with a `SKILL.md`
  based on `TEMPLATE_SKILL.md`, then wire it in `src/mj_agent/agent.py`.
- **New prompt version**: update `src/mj_agent/prompts/<name>.md` body +
  bump `version` in frontmatter; promote to `state: active` only with an
  accompanying `[EVAL]` reference (Phase 2 onwards).
