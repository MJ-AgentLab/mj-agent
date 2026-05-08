# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project

`mj-agent` is the MJ-AgentLab data agent — a LangChain 1.x + LangGraph 1.1.8
Python 3.13 service (managed with `uv`) that lets internal analysts explore
the mj-system business metrics warehouse through natural language. Currently
executing the **data-agent MVP** as a Phase 1 sub-milestone per
`plans/[PLAN]_mj-agent-data-agent-mvp-framework.md` (Studio + Claude Code
入口；Chainlit + 5 skills 仍是 Phase 1 终态——见
`plans/mj-agent-roadmap-v1.6.md`）。Canonical docs entry: `docs/INDEX.md`.

## Architecture

```
Entry   : LangGraph Studio (langgraph.json) / Chainlit (src/mj_agent/ui.py) / CLI
Runtime : langchain.agents.create_agent(model, tools, system_prompt[, checkpointer])
Skills  : src/mj_agent/prompts/system.md
        + src/mj_agent/skills/{biz-domain-context,qcm-analysis,
          safe-sql-analysis}/SKILL.md (statically full-loaded)
Tools   : src/mj_agent/tools/biz_context.py            (find_biz_context)
          src/mj_agent/tools/sql/introspect.py          (list/describe)
          src/mj_agent/tools/sql/guardrail.py           (L1 regex)
          src/mj_agent/tools/sql/precheck.py            (L1b sqlglot AST)
          src/mj_agent/tools/sql/execute.py             (envelope + DB)
Catalog : src/mj_agent/biz_catalog/qcm_catalog.yaml     (mirror STANDARD §2-§4)
          src/mj_agent/biz_catalog/{loader,finder}.py
Memory  : src/mj_agent/memory/checkpointer.py           (Phase 1 sub 1.A;
          AsyncPostgresSaver against mj_agent_memory DB on the dedicated
          mj-agent-postgres container — storage-stack PR; was originally
          colocated with mj-system's mj-postgres in 1.A and 1.H, then
          decoupled to its own pg + a redis container (future use).
          Async variant required because Chainlit drives graph.astream;
          sync PostgresSaver lacks aget_tuple — see bugfix
          /async-checkpointer.)
CLI     : src/mj_agent/server/cli.py                    (typer; `mj-agent
          serve` / `mj-agent check`)
Infra   : src/mj_agent/integrations/mj_system_db.py — psycopg pool, read-only
          infra/docker/{Dockerfile, entrypoint.sh,           (Phase 1 sub
          docker-compose.mj-agent.yml, README.md,            1.H; E2)
          postgres-init/01-bootstrap-mj-agent-memory.sh      (storage-stack
          }                                                   PR; auto-creates
                                                             memory DB on
                                                             container init)
Storage : mj-agent-postgres container — memory checkpointer (langgraph
          AsyncPostgresSaver tables). Decoupled from mj-system's mj-postgres
          so analyst-RO biz queries and mj-agent's own RW state never
          share connection pools.
          mj-agent-redis container — provisioned but no Python client
          wired yet; reserved for session cache / streaming buffer /
          rate limit (storage-stack PR).
Config  : src/mj_agent/config.py — pydantic-settings over .env
```

The agent is wired in `src/mj_agent/agent.py`: `_ACTIVE_SKILLS` lists
the three MVP skills; `_build_system_prompt()` concatenates
`prompts/system.md` with them in order, and `make_graph()` calls
`create_agent(model, tools, system_prompt)`. `make_graph` is the
symbol `langgraph.json` points at — Studio calls it lazily, so importing
the module never forces `make_llm()` (matters for unit tests and
type-checking with no `ARK_API_KEY`). The wired tool registry lives in
`src/mj_agent/tools/__init__.py:ALL_TOOLS` — `find_biz_context`,
`list_biz_tables`, `describe_biz_table`, `execute_sql` (called in this
default order by the LLM per the system prompt).

## Data boundary

mj-agent accesses only the mj-system biz domain through the `analyst`
PostgreSQL role. Visibility is enforced at four layers (see ADR-006):

| Layer | Mechanism | Location |
| --- | --- | --- |
| L1 guardrail | regex: single-statement, SELECT-only, **schema + biz_dwd table allowlist** | `tools/sql/guardrail.py` |
| L1b precheck | **sqlglot AST**: `no_select_star`, `require_time_range` on biz_dws fact tables, `require_limit` advisory; rule source shared with `[PROMPT]_component_judge.md` | `tools/sql/precheck.py` |
| L2 semantics | SKILL.md lists the visible tables; `qcm_catalog.yaml` mirrors mj-system STANDARD §2-§4 | `skills/*/SKILL.md` + `biz_catalog/qcm_catalog.yaml` |
| L3 connection | `default_transaction_read_only=on` + `lock_timeout=5s` + `idle_in_transaction_session_timeout=10s` | `integrations/mj_system_db.py` |
| L4 role | GRANT + `statement_timeout=60s` | mj-system `R__analyst_permissions.sql` |

Accessible schemas: `biz_dws` (all tables) + `biz_dwd` (only
`dwd_dim_product_interface` / `dwd_dim_institution` — enforced both at
L1 via `BIZ_ALLOWED_DWD_TABLES` and DB-side via GRANT). `biz_ods`,
`biz_ads`, and any `ops_*` schema are not reachable.

`statement_timeout` (60s) is caught explicitly in `execute_sql` and
re-raised as a friendly Chinese hint. The result envelope carries
`executed_sql / columns / rows / row_count / truncated /
statement_timeout_hit / business_summary / precheck_warnings`.

## Commands

```bash
uv sync                                    # install / lock dependencies
uv run langgraph dev                       # LangGraph Studio (local)
uv run mj-agent serve                      # Phase 1: Chainlit UI on CHAINLIT_HOST:PORT
uv run mj-agent check                      # Phase 1: probe DB + LLM creds (Docker healthcheck)
uv run pytest tests/unit                   # fast, no external deps
uv run pytest tests/eval                   # seed schema + Component check (no DB)
uv run pytest tests/integration            # needs live biz DB
uv run pytest tests/smoke -m smoke         # needs biz DB + LLM
uv run ruff check                          # lint
uv run mypy src/mj_agent                   # type-check

# Phase 1 sub 1.H — Docker (independent compose project; attaches
# mj-system-backend-network for biz pg consumer access via analyst RO role)
docker build -f infra/docker/Dockerfile -t mj-agent:0.1 .
docker run --rm --env-file .env -p 8001:8000 mj-agent:0.1

# Storage-stack — independent compose project (mj-agent + 自带 postgres + redis)
# From mj-agent repo root, single -f, no env var, mj-system stack untouched:
#   docker compose -f infra/docker/docker-compose.mj-agent.yml up -d
#   docker compose -f infra/docker/docker-compose.mj-agent.yml down
# Pre-req: mj-system 栈已 up (mj-system-backend-network + mj-postgres exist).
# (depends_on automatically pulls in mj-agent-postgres + mj-agent-redis)
```

Studio dev walkthrough (env + verification matrix + LangSmith trace
toggles + diagnostic table) lives in
`docs/runbook/dev_studio_walkthrough.md`.

`pyproject.toml` pins `addopts = "-m 'not smoke'"`, so plain `uv run pytest`
excludes smoke by default — pass `-m smoke` to opt in. `tests/conftest.py`
session fixtures `live_db` and `agent` *skip* (not fail) when
`POSTGRES_ANALYST_USER` / `ARK_API_KEY` are unset, so empty-env runs of
integration/smoke look green without actually exercising those paths.
CI (`.github/workflows/ci.yml`) runs the same gates locally devs run:
`python -m compileall` + `ruff check` + `mypy src/mj_agent` (strict) +
`pytest` (default selection: unit + eval + integration; smoke + contract
deselected) + `pytest tests/contract -m contract` (skip-clean without
DB creds). Smoke (`-m smoke`) is the only band CI never touches — it
needs live biz DB + Ark and runs locally only.

## LLM provider

mj-agent talks to Volcengine Ark's OpenAI-compatible endpoint (DeepSeek V3
as the default model). The `make_llm()` factory in `src/mj_agent/llm.py`
builds a `ChatOpenAI` instance with `base_url=ARK_BASE_URL`, the key from
`ARK_API_KEY`, and `extra_body.thinking` driven by `LLM_THINKING_ENABLED`.
Missing `ARK_API_KEY` raises `LLMConfigError` at graph build time.

## Environment variables

Aligned with mj-system's naming for **operational consistency** (DEV/TEST/
PROD profile 矩阵统一)，**not** for shared .env files. mj-agent 与
mj-system 是独立 compose project（ADR-008），各自有独立的 secrets 解密
管道（独立 `secrets.enc` + 独立团队口令；详见 `config/README.md`）.
Common keys: `POSTGRES_{DEV,TEST,PROD}_HOST/PORT` + `POSTGRES_ANALYST_USER/
PASSWORD` + `MJ_CONFIG_PROFILE`. Phase 1 sub 1.A added `MJ_AGENT_MEMORY_*`
(separate RW user + database for langgraph checkpointer) and
`CHAINLIT_HOST/PORT`. The storage-stack PR added
`MJ_AGENT_MEMORY_HOST/PORT` (decoupled from biz pg) +
`MJ_AGENT_REDIS_HOST/PORT/PASSWORD` (future use; container ready, no
Python client wired). See `.env.example` for the full list.

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

> **元规则段（cross-track meta）**: this section governs all three tracks.
> Per Meta_Framework v2.1 §6.4.1, this 元规则 段 sits **above** the
> `Code-Side Documentation`, `Agent-Side Documentation`, and
> `Engineering-Workflow Documentation` sections so Claude reads
> cross-track rules first before track-specific guidance.

All canonical documentation follows the **v2.1 tri-track trio** + HITL_Prompt
v1.0 (Phase B PR-B3c-promote completed; v2.0 trio archived to
`docs/archive/rule/` + `state: deprecated`):

- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1.md`
  (active) — cross-track meta rules (types / layers / lifecycle /
  archive / `track` frontmatter field with 4 values: code | agent |
  engineering-workflow | shared / CLAUDE.md tri-track sync §6.4.1 /
  §3.10 in-tree workflow SKILL governance / §7.7 .claude/ boundary +
  A12-A14 PR gates).
- `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.1.md`
  (active) — Track A authoring depth + PR gates A1-A6 + OB1-OB5 for
  code-side canonical types (GUIDE / ADR-code / SPEC-code / RUNBOOK /
  POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code).
  v1.1 minor bump: §0/§3.9/§7.3 cross-ref engineering-workflow
  STANDARDs.
- `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.1.md`
  (active) — Track B authoring depth + PR gates A7-A10 + A11 + loader
  frontmatter-strip contract for agent-side canonical types (SKILL /
  PROMPT / EVAL / agent-facing CONTRACT). v1.1 minor bump: §2/§7.5
  scope clarified to in-source only (`.claude/skills/**` excluded —
  governed by Meta v2.1 §3.10 instead).
- `docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1.0.md`
  (Track C primary STANDARD; active) — 17-stage HITL execution loop
  derived from mj-system v1.0; governs `.claude/skills/` workflow +
  Stage prompts + HITL gates at stages 5/7/9/11/13. Phase A Lite
  derivation: §4.1 / §4.4 reference mj-system upstream
  `[STANDARD]_AI_Engineering_Intake.md` / `_Repo_Scan.md` as
  placeholders pending Phase B+ derivation. Stage 8 Implementation
  has three flavors (A pure code / B in-source canonical always-HITL /
  C infra) — see ADR-015.

Archived (`docs/archive/rule/`, `state: deprecated`):
- `[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0.md` — replaced
  by v2.1 (tri-track + A12-A14)
- `[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0.md` —
  replaced by v1.1 (engineering-workflow cross-ref)
- `[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0.md` —
  replaced by v1.1 (in-source only scope)

Markdown + YAML syntax (GFM rendering target):
`docs/rule/[STANDARD]_GitHub_Markdown_v1.0.md`. Entry point:
`docs/INDEX.md`. New-member onboarding path:
`docs/guide/[GUIDE]_Developer_Onboarding.md` (mj-agent end-to-end day-1 +
refresher; covers repo / branches / env / tests / docs / commit / Studio).
ADR-012 documents the v1.1 → v2.0 dual-track split
(`docs/adr/[ADR]_012_Two_Track_Documentation_Governance.md`); the archived
predecessor lives at
`docs/archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md`
(state: deprecated). The corpus-wide guard `scripts/check_wikilinks.py`
enforces that any reference to the v1.1 filename outside `docs/archive/`
must be frozen (archive-prefixed) — living refs are migrated to the v2.0
trio.

Versioning rule (Meta_Framework v2.1 §4.2 + §5.6 sustained from v2.0 +
Framework v1.1): types with `version` frontmatter (STANDARD/SPEC/EVAL/
CONTRACT/ASSESSMENT) carry `_vX.Y` in the filename. On formal version
evolution (HITL judgment at PR review), the old file moves to
`docs/archive/<original-subdir>/`, the new file lands as `_v<new>.md`,
`state` flips to `deprecated` on the archive copy, and corpus-wide
references are audited (Living updates to `_v<new>`; Frozen pins to
`_v<old>`). Daily edits stay in-place — the rename + archive ceremony
fires only when the change qualifies as substantive evolution. ADR-011
documents the rationale; ADR-014 §决策点 3 skeleton-first describes the
延迟 promote 变体 used for v2.0 → v2.1.

`track` frontmatter field (Meta v2.1 §4.3.1): every canonical doc
declares `track: code | agent | engineering-workflow | shared`. Boundary
rules are written into ADR-012 §Decision 决策点 4 (v2.0 dual-track origin)
+ ADR-014 §Decision 决策点 4 (v2.1 tri-track) to avoid per-PR re-litigation.
Phase 1 末 will collapse the implicit default and require `track`
explicitly. The path-to-track decision tree is in Meta v2.1 §4.3.1
(block quote). `scripts/check_frontmatter.py` enforces the 4-value
TRACK_VALUES enum.

## Code-Side Documentation

> **Track A (code-side)** — governed by Code_Side_Framework v1.1 §7.1
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
- ADRs live in `docs/adr/`; Phase 0 ships 000/001/002/003/006/008/009/010/011/012/013 (012/013 `state: draft`, others `state: active`; all `decision: accepted`).
  See ADR-010 + matching `docs/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0.md`
  for the git/commit adoption rationale and Keep/Adapt/Defer matrix.
  See ADR-011 for the doc versioning + archive convention installed in v1.1
  of the Framework standard.
- 操作性 git 指南（分支、推送、PR 描述、初始化与版本管理）见
  `docs/infrastructure/git/INDEX.md`（4 份 GUIDE，派生自 mj-system v5.0
  `docs/infrastructure/git/`，按 mj-agent scope 与 Phase 0 状态改造）。
- Templates: `docs/_templates/TEMPLATE_{ADR,GUIDE,SKILL,PROMPT,CONTRACT}.md`.
  Copy, don't improvise frontmatter.

## Agent-Side Documentation

> **Track B (agent-side)** — governed by Agent_Side_Framework v1.1 §7.1
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
- **PR template**: the tri-track A1-A14 checklist in PR templates is
  visually grouped (Code-Side `<details>` block A1-A6 + OB1-OB5;
  Agent-Side `<details>` block A7-A10 + A11; Engineering-Workflow
  `<details>` block A12-A14 — PR-B3c-promote 完成后正式启用) so reviewers
  self-select by track.

## Engineering-Workflow Documentation

> **Track C (engineering-workflow)** — governed by Meta_Framework v2.1
> §3.10 / §7.7 (A12-A14 阻塞式) + `[STANDARD]_..._AI_Engineering_Execution_HITL_Prompt_v1.0`
> (Track C primary STANDARD; PR-A2). Reviewer: Tooling Reviewer + SWE.
> Failures are **process drift** (HITL skipped / wrong skill invoked /
> settings.json regression) — distinct from Track A loud failures and
> Track B silent failures.

PR gates A12-A14 (blocking, see Meta v2.1 §7.7):

- **A12**: `.claude/skills/<name>/SKILL.md` uses ADR-013 native schema
  only (`name` + `description` only — NO 13-field Agent_Side schema);
  `description` ≥ 200 chars with positive triggers + `Do not use for:`
  reverse-trigger block; `name` matches directory and conforms to
  `mj-agent-<group>-<verb>` namespace; body has `## Overview` +
  `## Workflow` (other sections flexible).
- **A13**: `.claude/settings.json` allowlist diffs reviewed against
  `[STANDARD]_..._Claude_Code_Settings_v1.0` (Phase C+); no bare `Bash`
  in `permissions.allow`; secret patterns required in `permissions.deny`;
  `enabledPlugins` changes require PR-body justification.
- **A14**: `.mcp.json` server changes declare trust posture (first-party
  / third-party / community) + credential mode (none / OAuth / API key)
  in PR body; cross-referenced in `[STANDARD]_..._MCP_Server_Governance_v1.0`
  (Phase C+).

In-tree skill catalog: `.claude/skills/mj-agent-*/` (target ~32 skills
across 5 families: flow / git / doc / runtime / infra). Slash-command
namespace `/mj-agent-<group>-<verb>`. Stage mapping: see HITL_Prompt v1.0
§5 Skill Hint Matrix. ADR-016 governs namespace + lifecycle.

Active in-tree skills（按 family 分组；填充随 phase 推进）:

| Family | Skill | Stage | Status |
|---|---|---|---|
| git | `/mj-agent-git-issue` | 1 | **active**（PR-B1） |
| git | `/mj-agent-git-branch` | 2 | **active**（PR-B1） |
| git | `/mj-agent-git-commit` | 12 | **active**（PR-B1） |
| git | `/mj-agent-git-push` | 13 | **active**（PR-B1） |
| git | `/mj-agent-git-pr` | 14 | **active**（PR-B1） |
| git | `/mj-agent-git-review-pr` | 15 (review 别人 PR) | **active**（PR-B3b） |
| git | `/mj-agent-git-check-merge` | 16 | **active**（PR-B3b） |
| git | `/mj-agent-git-delete` | 17 sub | **active**（PR-B3b） |
| git | `/mj-agent-git-sync` | 17 sub / hotfix | **active**（PR-B3b） |
| flow | `/mj-agent-flow-intake` | 0 | **active**（PR-B2） |
| flow | `/mj-agent-flow-repo-scan` | 3 | **active**（PR-B2） |
| flow | `/mj-agent-flow-plan` | 4 | **active**（PR-B2） |
| flow | `/mj-agent-flow-implement` | 8 | **active**（PR-B2） |
| flow | `/mj-agent-flow-verify` | 10 | **active**（PR-B3a） |
| flow | `/mj-agent-flow-self-review` | 11 | **active**（PR-B3a） |
| flow | `/mj-agent-flow-scope-drift` | 9 | **active**（PR-B3a） |
| flow | `/mj-agent-flow-review-respond` | 15 | **active**（PR-B3a） |
| flow | `/mj-agent-flow-post-merge` | 17 | **active**（PR-B3a） |
| doc | `/mj-agent-doc-plan` | 4 sub | **active**（PR-B4） |
| doc | `/mj-agent-doc-author` | 6 | **active**（PR-B4） |
| doc | `/mj-agent-doc-validate` | 11 sub | **active**（PR-B4） |
| doc | `/mj-agent-doc-{sync,review,migrate}` | 8 sub / 15 sub / 罕用 | P1/P2（PR-C1） |
| runtime | `/mj-agent-runtime-{skill-doc-improve,prompt-version-bump,biz-catalog-sync}` | 8 (B-flavor) sub | **read-only by design**；P1（PR-C2） |
| runtime | `/mj-agent-runtime-eval-baseline` | 8 sub / EVAL | P2（PR-D2，Phase 2） |
| infra | `/mj-agent-infra-env-setup` | 8 (C-flavor) | **active**（PR-B3b） |
| infra | `/mj-agent-infra-studio-probe` | 10 sub | **active**（PR-B3b） |
| infra | `/mj-agent-infra-{docker-compose,storage-stack}` | 8 (C-flavor) | P1（PR-C3） |

**v2.1 promote** (Phase B PR-B3c-promote 完成 ✅) ：v2.0 trio 已 archive 至 `docs/archive/rule/` + `state: deprecated`；v2.1 trio + HITL_Prompt v1.0 + ADR-014/015/016 全部 `state: active`；A12-A14 PR 门禁正式启用（不再 "v2.1 promote 前预自检"）；scripts/check_frontmatter.py TRACK_VALUES 已扩 4 值。

Repo conventions (engineering-workflow track):

- `.claude/skills/<name>/` is **NOT** loaded by `mj-agent` Python loader;
  `.claude/` resources are read by Claude Code main process.
  §7.5 frontmatter strip contract does NOT apply here.
- `.claude/scripts/*.ps1` follows existing `scripts/setup-env.ps1` pattern;
  prefer reference (call existing top-level `scripts/`) over duplicate.
- `.mcp.json` server entries declare trust posture + credential mode.
- New slash commands auto-discover; no registration step.
- HITL gates fire at HITL_Prompt §1 stages **5 / 7 / 9 / 11 / 13** (Plan
  / SPEC-design / Self-review / Push / Review-CI). At these stages, AI
  must pause and ask user before proceeding.
- **runtime family skills** (`mj-agent-runtime-*`) are **read-only by
  design** — they propose diffs and run reverse-scans, but do **NOT**
  modify `src/mj_agent/{skills,prompts,agent.py,tools}/` directly.
  This is enforced by SKILL.md `## Anti-patterns` text + A12 description
  quality gate; project-level setting deny-list is a backstop.

Three-source SKILL distinction (avoid confusion):

| Source | Path | Schema | Loader | Governance |
|---|---|---|---|---|
| in-source (runtime) | `src/mj_agent/skills/<name>/` | 13-field (Agent_Side §2) | `load_skill()` strip frontmatter | Track B (Agent_Side v1.x) |
| in-tree (workflow) | `.claude/skills/mj-agent-*/` | 2-field (ADR-013 native) | Claude Code main process | Track C (Meta v2.1 §3.10) |
| marketplace plugin | `mj-agentlab-marketplace/plugins/<plugin>/` | 2-field (ADR-013 native) | Claude Code plugin loader | out of mj-agent governance |
