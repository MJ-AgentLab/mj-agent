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

The standard way to provision `.env` is `.\scripts\setup-env.ps1`, which
decrypts `config/secrets.enc` (AES-256-CBC + PBKDF2) using a
team-distributed password and merges 4 secrets (`POSTGRES_ANALYST_USER/
PASSWORD`, `ARK_API_KEY`, `LANGSMITH_API_KEY`) into `.env`. Manual
`cp .env.example .env` is a fallback for developers without the team
password. Rotation/onboarding flow lives in `config/README.md`.
`.env.example` is intentionally ASCII-only — python-dotenv used inside
`langgraph_api` opens the file with the OS default encoding, which
fails on Chinese Windows if the file is UTF-8 with non-ASCII content.

## Documentation

> **元规则段（cross-track meta）**: this section governs both tracks.
> Per Meta_Framework v2.0 §6.4.1, this 元规则 段 sits **above** the
> `Code-Side Documentation` and `Agent-Side Documentation` sections so
> Claude reads cross-track rules first before track-specific guidance.

All canonical documentation follows the v2.0 trio (derived from mj-agent
Framework v1.1, which itself derived from mj-system v5.0):

- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0.md` —
  cross-track meta rules (types / layers / lifecycle / archive / `track`
  frontmatter field / CLAUDE.md dual-track sync §6.4.1).
- `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0.md`
  (Track A) — authoring depth + PR gates A1-A6 + OB1-OB5 for code-side
  canonical types (GUIDE / ADR-code / SPEC-code / RUNBOOK / POSTMORTEM-code
  / STANDARD-code / ISSUE-code / ASSESSMENT-code).
- `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0.md`
  (Track B) — authoring depth + PR gates A7-A10 + loader frontmatter-strip
  contract for agent-side canonical types (SKILL / PROMPT / EVAL /
  agent-facing CONTRACT).

Markdown + YAML syntax (GFM rendering target):
`docs/rule/[STANDARD]_GitHub_Markdown_v1.0.md`. Entry point:
`docs/INDEX.md`. ADR-012 documents the v1.1 → v2.0 dual-track split
(`docs/adr/[ADR]_012_Two_Track_Documentation_Governance.md`); the archived
predecessor lives at
`docs/archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md`
(state: deprecated). The corpus-wide guard `scripts/check_wikilinks.py`
enforces that any reference to the v1.1 filename outside `docs/archive/`
must be frozen (archive-prefixed) — living refs are migrated to the v2.0
trio.

Versioning rule (Meta_Framework v2.0 §4.2 + §5.6 sustained from Framework
v1.1): types with `version` frontmatter (STANDARD/SPEC/EVAL/CONTRACT/
ASSESSMENT) carry `_vX.Y` in the filename. On formal version evolution
(HITL judgment at PR review), the old file moves to
`docs/archive/<original-subdir>/`, the new file lands as `_v<new>.md`,
`state` flips to `deprecated` on the archive copy, and corpus-wide
references are audited (Living updates to `_v<new>`; Frozen pins to
`_v<old>`). Daily edits stay in-place — the rename + archive ceremony
fires only when the change qualifies as substantive evolution. ADR-011
documents the rationale.

`track` frontmatter field (Meta v2.0 §4.3.1): every canonical doc declares
`track: code | agent | shared`. Boundary rules are written into ADR-012
§Decision 决策点 4 to avoid per-PR re-litigation. Phase 1 末 will collapse
the implicit default and require `track` explicitly.

## Code-Side Documentation

> **Track A (code-side)** — governed by Code_Side_Framework v1.0 §7.1
> (A1-A6 阻塞式) + §7.2 (OB1-OB5 非阻塞观察). Reviewer: SWE Reviewer
> 充分（per Code_Side §8）. Failures are **loud** (compile / test /
> deploy break).

PR gates A1-A6 (blocking, see Code_Side §7.1):

- **A1**: 路径与文件名合法 — `[TYPE][_Subject]_Description[_vX.Y].md` or
  type-specific format.
- **A2**: Frontmatter schema 完整 — `type / domain / summary / owner /
  created / updated / state`; types with `version` (STANDARD/SPEC/EVAL/
  CONTRACT/ASSESSMENT) also carry `version`.
- **A3**: `state` 取值在 `draft / active / deprecated`; type-specific
  enums legal (`decision` / `resolution` / `eval_kind` / `contract_kind`).
- **A4**: 内部 Wikilink `[[...]]` 目标存在于仓库中.
- **A5**: 必要的 `docs/INDEX.md` / `docs/**/INDEX.md` 已同步或可重建.
- **A6**: allowlist 文档（框架/架构/核心运行入口）变更已同步检查
  `CLAUDE.md` (this file).

Non-blocking observations OB1-OB5 (see Code_Side §7.2; Phase 1 fills the
thresholds): 文档长度区间 / 时态一致性 / 内容边界 / 摘要质量 / 内部一致性.

Repo conventions (code-side, all governed by Track A standards):

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
- 操作性 git 指南（分支、推送、PR 描述、初始化与版本管理）见
  `docs/infrastructure/git/INDEX.md`（4 份 GUIDE，派生自 mj-system v5.0
  `docs/infrastructure/git/`，按 mj-agent scope 与 Phase 0 状态改造）。
- Templates: `docs/_templates/TEMPLATE_{ADR,SKILL,PROMPT,CONTRACT}.md`.
  Copy, don't improvise frontmatter.

## Agent-Side Documentation

> **Track B (agent-side)** — governed by Agent_Side_Framework v1.0 §7.1
> (A7-A10 阻塞式) + §7.5 (frontmatter strip 契约). Reviewer: Domain
> Expert / Prompt Engineer **+** SWE (≥ 2 reviewers per Agent_Side §8).
> Failures are **silent** (wrong answers / hallucinations / business
> decision drift) — every LLM call that consumes SKILL/PROMPT body is a
> production output.

PR gates A7-A10 (blocking, see Agent_Side §7.1):

- **A7**: 新增/修改 `[SKILL]` 时 `src/mj_agent/skills/<name>/` 目录与
  文档身份一致（同名）.
- **A8**: 新增/修改 `[PROMPT]` 时 `version` 填写; `state: active` 时
  `eval_references` 非空（Phase 2 起强制）.
- **A9**: 新增/修改 `[EVAL]` 时 `dataset_path` 存在、`baseline_metric`
  / `baseline_value` 填写（Phase 2 起强制）.
- **A10**: 新增/修改 `[CONTRACT]` `state: active` 时 `schema_ref`
  存在并指向存在 schema 文件.

Frontmatter strip 契约 (Agent_Side §7.5, hard constraint): code that
loads in-source canonical docs as LLM input **must** strip YAML
frontmatter. Implementation:

- **In-source canonical**: `src/mj_agent/skills/**/SKILL.md` and
  `src/mj_agent/prompts/*.md` carry YAML frontmatter and are governed as
  canonical documents. The loaders `load_skill` / `load_prompt` strip
  frontmatter via `python-frontmatter` before returning content — do not
  bypass them, do not read these files with `open().read()`. Companion
  `load_skill_meta` / `load_prompt_meta` return the frontmatter dict for
  documentation tooling (A7/A8 validation, INDEX generation in Phase 2).

Agent-side authoring quick reference:

- **New skill**: create `src/mj_agent/skills/<name>/` with a `SKILL.md`
  based on `TEMPLATE_SKILL.md` (body 五段式 per Agent_Side §2.1: Purpose
  / When to use / Planning workflow / Common patterns / Anti-patterns),
  then wire it in `src/mj_agent/agent.py`.
- **New prompt version**: update `src/mj_agent/prompts/<name>.md` body +
  bump `version` in frontmatter; promote to `state: active` only with an
  accompanying `[EVAL]` reference (Phase 2 onwards).
- **PR template**: the dual-track A1-A10 checklist in PR templates is
  visually grouped (Code-Side `<details>` block A1-A6 + OB1-OB5;
  Agent-Side `<details>` block A7-A10) so reviewers self-select by track.
