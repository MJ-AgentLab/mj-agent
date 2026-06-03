# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Codex Status

**Codex is NOT part of the development workflow.** If Codex is used, it is **only for
read-only external review** (advisory; not authoritative). All implementation — file edits,
test runs, migrations, docs, verification — is done by Claude Code. Claude Code MUST NOT
delegate execution to Codex. See [AGENTS.md](./AGENTS.md) + `policies/ai-agent.md` §1 for
the full boundary; each task output must declare `Codex invocation: NONE`.

> **项目起源说明（2026-05-11 update）**：mj-agent 文档治理框架在 bootstrap
> 阶段曾参考某内部上游业务系统的实践沉淀（详见 `docs/archive/adr/[DEPRECATED]_*`
> 9 个 archived ADR 与 `docs/archive/rule/[DEPRECATED]_*` 框架历史版本）；
> 当前所有 active STANDARD 已独立维护，无跨仓依赖。runtime 层 mj-agent
> 通过 `analyst` 只读 PostgreSQL 角色访问"上游业务系统"（术语见
> `docs/glossary/upstream_business_warehouse.md`）；代码层 literal
> （`mj-system-backend-network` Docker network 等）保留作真实部署对象的
> 精确引用。

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
Middleware: src/mj_agent/middleware/tool_errors.py      (LangChain 1.x
          @wrap_tool_call; converts SQL tool ValueError/RuntimeError into
          ToolMessage so the LLM self-corrects rather than the graph
          crashing silently. Sync + async variants wired in make_graph
          as `middleware=[handle_sql_tool_errors]`. See ADR-029.)
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
          docker/{Dockerfile, entrypoint.sh,                 (Phase 1 sub
          compose.yaml,                                      1.H; E2;
            compose.override.yml,                            ADR-025
            compose.test.yml,                                multi-env
            compose.prod.yml,                                compose
          README.md,                                         layering)
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
`create_agent(model, tools, system_prompt, middleware=[...])` — the
middleware list currently contains `handle_sql_tool_errors` which
catches `ValueError` / `RuntimeError` from the SQL tool chain and
returns a `ToolMessage` so the LLM can self-correct (ADR-029). `make_graph` is the
symbol `langgraph.json` points at — Studio calls it lazily, so importing
the module never forces `make_llm()` (matters for unit tests and
type-checking with no `ARK_API_KEY`). The wired tool registry lives in
`src/mj_agent/tools/__init__.py:ALL_TOOLS` — `find_biz_context`,
`list_biz_tables`, `describe_biz_table`, `execute_sql` (called in this
default order by the LLM per the system prompt).

## Data boundary

mj-agent accesses only the upstream business warehouse biz domain through
the `analyst` PostgreSQL role (term defined in `docs/glossary/upstream_business_warehouse.md`).
Visibility is enforced at four layers (see ADR-006):

| Layer | Mechanism | Location |
| --- | --- | --- |
| L1 guardrail | regex: single-statement, SELECT-only, **schema + biz_dwd table allowlist** | `tools/sql/guardrail.py` |
| L1b precheck | **sqlglot AST**: `no_select_star`, `require_time_range` on biz_dws fact tables, `require_limit` advisory; rule source shared with `[PROMPT]_component_judge.md` | `tools/sql/precheck.py` |
| L2 semantics | SKILL.md lists the visible tables; `qcm_catalog.yaml` mirrors upstream business warehouse data dictionary STANDARD | `skills/*/SKILL.md` + `biz_catalog/qcm_catalog.yaml` |
| L3 connection | `default_transaction_read_only=on` + `lock_timeout=5s` + `idle_in_transaction_session_timeout=10s` | `integrations/mj_system_db.py` |
| L4 role | GRANT + `statement_timeout=60s` | upstream `R__analyst_permissions.sql` |

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
docker build -f docker/Dockerfile -t mj-agent:0.1 .
docker run --rm --env-file .env -p 8001:8000 mj-agent:0.1

# Storage-stack — independent compose project (mj-agent + 自带 postgres + redis)
# 4-file profile layering per ADR-026 (mirror mj-system v3.2.2). All 3 profiles
# use explicit `-f base -f overlay` chain (override.yml auto-load doesn't apply
# because compose files live in docker/ subdir and base loaded via -f).
# `--env-file .env` is also required for the same reason: docker compose CLI
# looks for .env in the project directory (= the directory of the first -f
# file = docker/), NOT the developer's cwd; without it the `${VAR}`
# substitutions in compose YAML fall through to their `:-default` sentinels
# and the postgres init script bakes a placeholder password into the volume.
# Pre-req: mj-system 栈已 up (mj-system-backend-network + mj-postgres exist).
#
# DEV (本地)
#   docker compose --env-file .env -f docker/compose.yaml \
#                  -f docker/compose.override.yml up -d
# TEST (192.168.0.179)
#   docker compose --env-file .env -f docker/compose.yaml \
#                  -f docker/compose.test.yml up -d
# PROD (192.168.0.106)
#   docker compose --env-file .env -f docker/compose.yaml \
#                  -f docker/compose.prod.yml up -d
#
# DGX 算力消费侧：DGX 不部署 mj-agent (用户决策；ADR-025 §D.2)。任一 profile 下
# 在 .env 设 LLM_PROVIDER=local-openai-compat + LLM_BASE_URL=http://192.168.0.189:8000/v1
# 即可消费 DGX vLLM/SGLang/Ollama；endpoint 健康用 /mj-agent-infra-llm-endpoint-probe.
#
# Teardown (与 up 用同样 -f 链): /mj-agent-infra-env-teardown 提供 3-level safety
# (down / down -v / down -v --rmi local; H3 hard-confirm Level 2/3).
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

mj-agent supports two providers via `LLM_PROVIDER` env (ADR-025 §D.2). Default
`ark` keeps current behavior fully back-compat; `local-openai-compat` enables
DGX-Spark local LLM consumption.

| Provider | base_url | api_key | extra_body.thinking | 用途 |
|---|---|---|---|---|
| `ark` (default) | `effective_llm_base_url` fallback `ARK_BASE_URL` | `effective_llm_api_key` fallback `ARK_API_KEY` | passed (DeepSeek V3 reasoning toggle) | 公网 Ark + DeepSeek V3 |
| `local-openai-compat` | `LLM_BASE_URL` (required; missing → `LLMConfigError`) | `LLM_API_KEY` 或 `"EMPTY"` sentinel | NOT passed (vLLM/SGLang/Ollama 不接受 Ark `thinking` 参数，传入会 422) | DGX-Spark 192.168.0.189 vLLM/SGLang/Ollama/TGI/llama.cpp |

The `make_llm()` factory in `src/mj_agent/llm.py` branches on
`settings.llm_provider`. Missing required creds raises `LLMConfigError` at
graph build time (ark: `ARK_API_KEY`/`LLM_API_KEY`; local-openai-compat:
`LLM_BASE_URL`). `mj-agent check` is provider-aware (outputs `llm provider =
<name> (endpoint=<url>)`). Endpoint healthcheck for local-openai-compat:
`/mj-agent-infra-llm-endpoint-probe` (3-step probe: reachable + model id match
+ 1-token chat smoke; Ollama `/api/tags` fallback).

**`Profile` enum unchanged** (`Literal["dev","test","prod"]`) — DGX is NOT a
deployment target for mj-agent (per user decision; ADR-025 §D.2 / Alternative
B). DGX support is purely an LLM endpoint switch orthogonal to
`MJ_CONFIG_PROFILE` (which decides biz pg host).

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
Python client wired). ADR-025 (PR-2) added LLM provider abstraction:
`LLM_PROVIDER` (ark | local-openai-compat) + `LLM_BASE_URL` + `LLM_API_KEY`
(legacy `ARK_BASE_URL` / `ARK_API_KEY` preserved as ark-provider fallback).
ADR-025 (PR-3) added MCP server SSH passwords + pg URL placeholders for the
13-server `.mcp.json`: `MJ_AGENT_SSH_SERVER_{CLOUD,RUNNER,TEST,PROD,DGX}_PASSWORD`
(5 unique secrets driving 9 ssh-manager entries) +
`MJ_AGENT_PG_{MEMORY,BIZ}_{DEV,TEST_LAN,TEST_WAN,PROD_LAN,PROD_WAN}_URL`
(10 optional URL overrides; WAN required for FRP-tunneled remote pg).
See `.env.example` for the full list.

Secrets injection follows **2-bundle trust-boundary split** (ADR-030;
aligns mj-agent with mj-system v2.3 secrets-sys-ops.enc pattern):

- **App bundle** `config/secrets.enc` (6-8 keys): `POSTGRES_ANALYST_USER/
  PASSWORD`, `ARK_API_KEY`, `LLM_API_KEY` (optional), `LANGSMITH_API_KEY`,
  `MJ_AGENT_MEMORY_USER/PASSWORD`. Decrypt via `.\scripts\setup-env.ps1`
  → merged into `.env` (read by Python runtime, docker compose).
- **MCP bundle** `config/secrets-mcp.enc` (15 keys): 5 SSH passwords + 10 PG
  URL overrides. Decrypt via `.\.claude\scripts\setup-mcp-secrets.ps1` →
  written **directly** to User-level OS env (`HKCU\Environment`), bypassing
  `.env` entirely. Read by claude.exe at startup for `.mcp.json` `${VAR}`
  substitution.

Both bundles use the same team-distributed password (AES-256-CBC + PBKDF2).
Manual `cp .env.example .env` is a fallback for developers without the team
password. Rotation/onboarding flow lives in `config/README.md`.
`.env.example` is intentionally ASCII-only — python-dotenv used inside
`langgraph_api` opens the file with the OS default encoding, which
fails on Chinese Windows if the file is UTF-8 with non-ASCII content.

`uv run mj-agent check` also runs **`.env.example` → `.env` template
drift detection** (warn-only, does not affect exit code; mirrors the
`[DRIFT]` block in `setup-env.ps1`). This catches the case where
`.env.example` gains new keys after a rename / feature PR but the
developer's existing `.env` was never refreshed — see
`src/mj_agent/env_drift.py` for the algorithm and
`tests/unit/test_env_drift.py` for the contract. Drift scope is **app keys
only** (post ADR-030; MCP keys are tracked separately via
`setup-mcp-secrets.ps1 -Reload` against `config/secrets-mcp.example`).

Claude Code does **not** auto-load `.env`; `.mcp.json` `${VAR}`
substitution reads claude.exe's process env at startup. Per ADR-030, MCP
secrets land in OS env **directly from secrets-mcp.enc** (never via .env
mirroring). Run `.\.claude\scripts\setup-mcp-secrets.ps1` once after first
clone or any secret rotation; restart terminal + claude code afterwards.
See `config/README.md` §6.4 for security tradeoffs and `-Reload` diagnostics.

## Documentation

> **元规则段（cross-track meta）**: this section governs all three tracks.
> Per Meta_Framework v2.1 §6.4.1, this 元规则 段 sits **above** the
> `Code-Side Documentation`, `Agent-Side Documentation`, and
> `Engineering-Workflow Documentation` sections so Claude reads
> cross-track rules first before track-specific guidance.

**跨项目借鉴边界**：mj-agent 文档治理框架曾参考某内部上游业务系统实践沉淀（详见
开篇项目起源说明 + `docs/archive/`），当前所有 active 治理已独立维护。AI 在写
mj-agent 文档/代码时**只借鉴**外部参考源的问题识别框架 + 评估思路；
**具体方案**（文件结构、字段命名、段数、术语）必须按 mj-agent 自身规范设计 —
例如 INTAKE 按 `.claude/skills/mj-agent-flow-intake/SKILL.md` §Output Format 7 段
而非外部 11 段；`[PLAN]` mirror `plans/[PLAN]_multi_env_dgx_mcp_bundle.md` 等
mj-agent native 范本而非外部模板；frontmatter 用 mj-agent 自身 pattern（如
`updated:` 字段；不引入 `revision:` 等 mj-agent 无的字段）。跨项目 attribution
集中到 `docs/glossary/upstream_business_warehouse.md` §如何引用上游业务系统
元文档段。

All canonical documentation follows the **v2.1 tri-track trio** + HITL_Prompt
v1.0 (Phase B PR-B3c-promote completed; v2.0 trio archived to
`docs/archive/rule/` + `state: deprecated`):

- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`
  (active) — cross-track meta rules (types / layers / lifecycle /
  archive / `track` frontmatter field with 4 values: code | agent |
  engineering-workflow | shared / CLAUDE.md tri-track sync §6.4.1 /
  §3.10 in-tree workflow SKILL governance / §7.7 .claude/ boundary +
  A12-A14 PR gates). **v2.2 sustained 2026-05-18** (借鉴 mj-system §3.1
  + §6.4 结构): §2.6 项目根 5 文件具名职责表（README / CONTRIBUTING /
  CHANGELOG / GLOSSARY / CLAUDE.md）+ 例外条款 (A1-A3 不适用 / A4+A6 仍
  适用) + §4.3.1 path-to-track 决策树补 0 条覆盖项目根 markdown +
  §6.4 显式展开 3 类 allowlist + 加 mj-agent 特化第 4 类「runtime 语义」
  (LLM provider matrix + Data boundary L1-L4 + HITL gates).
- `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md`
  (active) — Track A authoring depth + PR gates A1-A6 + OB1-OB5 for
  code-side canonical types (GUIDE / ADR-code / SPEC-code / RUNBOOK /
  POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code).
  v1.1 minor bump: §0/§3.9/§7.3 cross-ref engineering-workflow
  STANDARDs.
- `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md`
  (active) — Track B authoring depth + PR gates A7-A10 + A11 + loader
  frontmatter-strip contract for agent-side canonical types (SKILL /
  PROMPT / EVAL / agent-facing CONTRACT). v1.1 minor bump: §2/§7.5
  scope clarified to in-source only (`.claude/skills/**` excluded —
  governed by Meta v2.1 §3.10 instead).
- `docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md`
  (Track C primary STANDARD; active) — 17-stage HITL execution loop
  governing `.claude/skills/` workflow + Stage prompts + HITL gates at
  stages 5/7/9/11/13. §4.1 (Intake) / §4.4 (Repo Scan) content is
  inlined and mj-agent-native (PR #118 commit-3 supplements). Stage 8
  Implementation has three flavors (A pure code / B in-source canonical
  always-HITL / C infra). Original derivation provenance archived to
  `docs/archive/adr/[DEPRECATED]_[ADR]_015_*`.

Archived (`docs/archive/rule/`, `state: deprecated`):
- `[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` — replaced
  by v2.1 (tri-track + A12-A14)
- `[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md` —
  replaced by v1.1 (engineering-workflow cross-ref)
- `[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md` —
  replaced by v1.1 (in-source only scope)

Markdown + YAML syntax (GFM rendering target):
`docs/rule/[STANDARD]_GitHub_Markdown.md` (**v1.1 minor bump 2026-05-18**:
§14 项目根 README 与 Markdown 特例新加 — Badges / 行内 HTML 例外 /
多语言 README / ASCII 架构图 / 项目根 markdown 不进入 canonical 治理；
原 §14 参考改 §15；in-place stable path 不触发 archive). Entry point:
`docs/INDEX.md`. New-member onboarding path:
`docs/guide/[GUIDE]_Developer_Onboarding.md` (mj-agent end-to-end day-1 +
refresher; covers repo / branches / env / tests / docs / commit / Studio).

**项目根具名文件 5 件（Meta v2.2 §2.6；不入 canonical 治理表，A1-A3 不适用，A4+A6 仍适用）**：
- `README.md` — 项目入口和快速启动（PR #171 借鉴 mj-system 8 段结构扩写）
- `CONTRIBUTING.md` — 协作与提交流程（PR-D 新建；「摘要 + 跳转」模式 8 段；环境已就绪开发者入口；
  与 Developer_Onboarding 互补不重复）
- `CHANGELOG.md` — 版本变更日志
- `GLOSSARY.md` — 项目术语索引（PR-D 新建；A-W 字母分段 ~40 术语；专题深度词典在 `docs/glossary/`）
- `CLAUDE.md` — AI 高频上下文缓存（本文件；同步策略见 Meta v2.2 §6.4 4 类 allowlist）


ADR-012 documents the v1.1 → v2.0 dual-track split
(`decisions/ADR-012_Two_Track_Documentation_Governance.md`); the archived
predecessor lives at
`docs/archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md`
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
延迟 promote 变体 used for v2.0 → v2.1. ADR-020 (Phase C-3-1) 把 `scripts/check_wikilinks.py` 改为 auto-discover
NEEDLES from `docs/archive/rule/[DEPRECATED]_*.md` glob — 零维护 archive
引用校验；新增 archive 文件自动纳入校验。
ADR-024 (Phase D-3) EVAL framework spec：Agent_Side v1.1 → v1.2 archive
ceremony；§4 EVAL Authoring 完整规范（4 子类 outcome/trajectory/component/
integration + body 八段 + frontmatter schema）；A8/A11 transitional waiver
**延续 Phase E**（前置条件 4 项 roadmap）；check_frontmatter.py EVAL 类型
条件；不 supersede；mj-agent 原生；Phase D 收尾。

ADR-026/027/028 (PR-Γ；ADR-025 拆分；2026-05-11)：
- **ADR-026 Multi-Environment Compose Profile**：docker-compose 4-file 分层
  (base + override + test + prod)；compose project name 跨 profile 不变；
  dev 也用显式 `-f base -f override` 因本仓 compose 在 `docker/`
  子目录 + `-f` 显式 base 时 auto-load 不生效（quirk）。
- **ADR-027 LLM Provider Abstraction**：`make_llm()` 抽象为 provider 分支
  factory（`ark` 默认 + `local-openai-compat` for DGX-Spark vLLM/SGLang/
  Ollama）；`Profile` enum 不扩 dgx — DGX 仅作算力节点，不部署 mj-agent；
  endpoint 健康用 `/mj-agent-infra-llm-endpoint-probe`。
- **ADR-028 MCP Server Inventory + Governance**：`.mcp.json` 13 servers
  + 新建领域专属 STANDARD `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`
  (per ADR-022 §C.3.2；A14 PR gate 正式生效)；独立 secrets pipeline
  (`MJ_AGENT_*` 命名空间 vs 上游 `MJ_SYS_*`；per ADR-008)；wrapper script 内部
  baseline 在 `docs/_baselines/pg_server_baseline.md`。

历史归档：ADR-010/015/017/018/019/021/022/023/025 共 9 个 ADR 已批量
archive 至 `docs/archive/adr/`（PR-Γ；2026-05-11；cross-repo decoupling
cleanup）— 决策内容已沉淀为对应 framework STANDARD 段；详见
[[docs/archive/adr/INDEX|archive/adr/INDEX]]。

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
  (`feature/bugfix/documentation/maintain/hotfix`).
  - **Rule G1 (worktree-required)**: every new branch (incl. bugfix)
    MUST be created via `git worktree add ../<name> -b <name>` —
    `git checkout -b` inside an existing worktree is **forbidden**.
    Enforced by `.claude/scripts/guard-git-workflow.ps1` PreToolUse hook.
  - **Rule G2 (base=develop-except-hotfix)**: PRs from
    feature/bugfix/documentation/maintain MUST set `--base develop` on
    `gh pr create`; only hotfix targets main. Enforced by the same hook.
  - Historical precipitating incidents: PR #158 (缺 `--base` 误合到 main) +
    PR #154 (`git checkout -b` 而非 worktree-add) on 2026-05-12; recovery
    closed by PR #159 (sync develop ← main). Root cause + 3-layer defense
    design: `plans/[PLAN]_g1_g2_workflow_enforcement.md`. See
    `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §5
    for the branch ↔ commit-type alignment matrix.
- Commits follow `<type>(<scope>): <summary>` per
  `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`
  (state: draft; promotion criteria in §9). Types:
  `feat / fix / perf / refactor / test / docs / infra`. Scopes derive
  from `src/mj_agent/` modules — see STANDARD §4 for the closed allowlist.
- ADRs live in `docs/adr/`; Phase 0 ships 000/001/002/003/006/008/009/010/011/012/013 (012/013 `state: draft`, others `state: active`; all `decision: accepted`). ADR-029 (2026-05-12) adds the `handle_sql_tool_errors` middleware policy — SQL tool exceptions surface to the LLM as `ToolMessage` instead of crashing the graph; supersedes the implicit ToolNode raise-through behavior that produced the 2026-05-12 frontend hang.
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
  / third-party / community) + credential mode (none / OAuth / API key /
  wrapped script) in PR body per the §4 declaration template in
  `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`
  (active per ADR-025 PR-3；领域专属 placement per ADR-022 §C.3.2). Quarterly
  audit (per STANDARD §6) re-evaluates trust posture + syncs `.claude/scripts/
  pg-server-*` against mj-system upstream.

In-tree skill catalog: `.claude/skills/mj-agent-*/` (target ~32 skills
across 5 families: flow / git / doc / runtime / infra). Slash-command
namespace `/mj-agent-<group>-<verb>`. Stage mapping: see HITL_Prompt v1.1
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
| doc | `/mj-agent-doc-sync` | 8 sub | **active**（PR-C1） |
| doc | `/mj-agent-doc-review` | 15 sub | **active**（PR-C1） |
| doc | `/mj-agent-doc-migrate` | 罕用 / archive workflow | **active**（PR-C1） |
| runtime | `/mj-agent-runtime-skill-doc-improve` | 8 (B-flavor) sub | **active read-only by design**（PR-C2） |
| runtime | `/mj-agent-runtime-prompt-version-bump` | 8 (B-flavor) sub | **active read-only by design**（PR-C2） |
| runtime | `/mj-agent-runtime-biz-catalog-sync` | 8 (B-flavor) sub | **active read-only by design**（PR-C2） |
| runtime | `/mj-agent-runtime-eval-baseline` | 8 sub / EVAL | **active read-only by design**（PR-D2-skill；framework-independent 设计阶段；Phase 2 EVAL framework 落地后由 PR-D2-enforcement 跑 baseline 实测）|
| infra | `/mj-agent-infra-env-setup` | 8 (C-flavor) | **active**（PR-B3b） |
| infra | `/mj-agent-infra-studio-probe` | 10 sub | **active**（PR-B3b） |
| infra | `/mj-agent-infra-docker-compose` | 8 (C-flavor) | **active**（PR-C3） |
| infra | `/mj-agent-infra-storage-stack` | 8 (C-flavor) | **active**（PR-C3） |
| infra | `/mj-agent-infra-llm-endpoint-probe` | 10 sub | **active**（ADR-025 PR-2） |
| infra | `/mj-agent-infra-env-teardown` | 17 sub / 8 (C-flavor) | **active**（ADR-025 PR-4） |

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
