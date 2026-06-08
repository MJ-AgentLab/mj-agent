# CLAUDE.md

Guidance for Claude Code. **Detail lives in the SDD kernel (`policies/` + `sdd/`) +
`docs/INDEX.md`; this file is the high-frequency cache — 指针, not source-of-truth.**

## Codex Status

Codex is **NOT** in the dev workflow — read-only external review only (advisory). All
implementation (edits / tests / migrations / docs / verification) is Claude Code's; never
delegate execution to Codex. Each task output declares `Codex invocation: NONE`. Full
boundary: `AGENTS.md` + `policies/ai-agent.md` §1.

## Project

`mj-agent` = MJ-AgentLab data agent: LangChain 1.x + LangGraph 1.1.8, Python 3.13, `uv`.
Lets internal analysts explore the mj-system biz metrics warehouse in natural language.
Executing the **data-agent MVP** (Phase 1) per `plans/[PLAN]_mj-agent-data-agent-mvp-framework.md`
+ `plans/mj-agent-roadmap-v1.6.md`. Docs entry: `docs/INDEX.md`. Upstream-warehouse terms +
cross-repo attribution: `docs/glossary/upstream_business_warehouse.md` (bootstrap borrowed
external problem-framing only; all active governance is mj-agent-native).

## 必停 surfaces (pause for HITL — never edit / flip unilaterally)

- **Data/agent 必停** (5): `src/mj_agent/tools/sql/guardrail.py` (L1) ·
  `tools/sql/precheck.py` (L1b) · `prompts/system.md` · `skills/*/SKILL.md` bodies ·
  `biz_catalog/qcm_catalog.yaml`.
- **Infra freeze skills** (6): `.claude/skills/mj-agent-infra-*/SKILL.md` —
  content-hash freeze per `policies/ai-agent.md` §7; record in
  `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`.
- **Gated actions**: CI gate blocking-flip (`continue-on-error true→false`) =
  `ci-blocking-gate-toggle`; `.mcp.json` trust-posture change = A14; `.env` is
  permission-denied. HITL canonical 10-enum + pre-flight discipline:
  `policies/ai-agent.md` §4 / §7. HITL gates fire at execution-loop stages 5/7/9/11/13.

## Architecture

Entry: LangGraph Studio (`langgraph.json`) / Chainlit (`src/mj_agent/ui.py`) /
CLI (`server/cli.py`: `mj-agent serve|check`). Runtime:
`create_agent(model, tools, system_prompt, middleware)`.

- `agent.py` — `make_graph()` is the `langgraph.json` entry; lazy `make_llm()` so
  import never needs `ARK_API_KEY`. `_ACTIVE_SKILLS` (3 MVP skills) +
  `_build_system_prompt()` concatenates `prompts/system.md` + skill bodies.
- `tools/__init__.py:ALL_TOOLS` — `find_biz_context` → `list_biz_tables` →
  `describe_biz_table` → `execute_sql` (default LLM order). SQL chain:
  `tools/{biz_context,sql/introspect,sql/guardrail,sql/precheck,sql/execute}.py`.
- `middleware/tool_errors.py` — `@wrap_tool_call` turns SQL ValueError/RuntimeError
  into a `ToolMessage` so the LLM self-corrects (ADR-029).
- `memory/checkpointer.py` — AsyncPostgresSaver on the dedicated `mj-agent-postgres`
  container. `integrations/mj_system_db.py` — read-only psycopg pool. `llm.py` —
  `make_llm()` provider factory. `config.py` — pydantic-settings over `.env`.
  `biz_catalog/{loader,finder}.py` + `qcm_catalog.yaml` (mirrors upstream data-dictionary).
  Infra: `docker/{Dockerfile,compose*.yml,postgres-init/}` (redis provisioned, unused).

## Data boundary (ADR-006; 4 layers, `analyst` RO PG role)

| Layer | Mechanism | Location |
| --- | --- | --- |
| L1 | regex: single-stmt, SELECT-only, schema + biz_dwd allowlist | `tools/sql/guardrail.py` |
| L1b | sqlglot AST: `no_select_star` / `require_time_range` / `require_limit` | `tools/sql/precheck.py` |
| L2 | visible tables in SKILL.md + `qcm_catalog.yaml` | `skills/*/SKILL.md` |
| L3 | `default_transaction_read_only` + lock/idle timeouts | `integrations/mj_system_db.py` |
| L4 | GRANT + `statement_timeout=60s` | upstream `R__analyst_permissions.sql` |

Accessible: `biz_dws` (all) + `biz_dwd` (only `dwd_dim_product_interface` / `dwd_dim_institution`;
`BIZ_ALLOWED_DWD_TABLES` + GRANT); `biz_ods` / `biz_ads` / `ops_*` unreachable. `execute_sql`
envelope: `executed_sql / columns / rows / row_count / truncated / statement_timeout_hit / business_summary / precheck_warnings`.

## Commands

```bash
uv sync                                          # deps
uv run langgraph dev                             # Studio (local)
uv run mj-agent serve | check                    # Chainlit UI | DB+LLM creds probe
uv run pytest tests/{unit,eval,integration}      # smoke: add -m smoke (needs DB+LLM)
uv run ruff check && uv run mypy src/mj_agent    # lint + types (CI runs both, mypy strict)
```

Docker — independent compose project (ADR-026 4-file profile; attaches
`mj-system-backend-network`): `docker compose --env-file .env -f docker/compose.yaml
-f docker/compose.{override,test,prod}.yml up -d` (DEV/TEST/PROD; both `--env-file` and
explicit `-f base -f overlay` required — `docker/` subdir auto-load quirk). 3-level teardown:
`/mj-agent-infra-env-teardown`. Studio walkthrough: `Developer_Onboarding` §7. CI = compileall +
ruff + mypy(strict) + pytest(unit/eval/integration + contract); smoke local-only.
`tests/conftest.py` *skips* (not fails) on missing `POSTGRES_ANALYST_USER`/`ARK_API_KEY`.

## LLM provider (ADR-025 / ADR-027)

`LLM_PROVIDER` env: `ark` (default; `ARK_*` creds; passes DeepSeek `thinking`) |
`local-openai-compat` (`LLM_BASE_URL` required; DGX vLLM/SGLang/Ollama; `thinking` NOT
passed → would 422). `make_llm()` in `llm.py` branches; missing creds →
`LLMConfigError` at graph build. Endpoint health: `/mj-agent-infra-llm-endpoint-probe`.
`Profile` enum stays `dev|test|prod` — DGX is an LLM-endpoint switch, not a deploy target.

## Environment variables & secrets (ADR-008 / ADR-030)

mj-agent and mj-system are independent compose projects with independent secrets pipelines.
Keys (full list in `.env.example`, ASCII-only): `POSTGRES_*` + `POSTGRES_ANALYST_USER/PASSWORD`
+ `MJ_CONFIG_PROFILE` + `MJ_AGENT_MEMORY_*` / `_REDIS_*` + `LLM_*` + `MJ_AGENT_SSH_SERVER_*_PASSWORD`
(5) + `MJ_AGENT_PG_{MEMORY,BIZ}_*_URL` (10). **2-bundle split**: app `config/secrets.enc` →
`scripts/setup-env.ps1` → `.env`; MCP `config/secrets-mcp.enc` → `.claude/scripts/setup-mcp-secrets.ps1`
→ HKCU OS env (not `.env`; for `.mcp.json` `${VAR}`). `mj-agent check` does `.env.example`→`.env`
drift detection. Detail: `config/README.md`.

## Documentation governance (SDD kernel — this file only points)

The v2.x tri-track trio (Meta v2.2 / Code_Side v1.1 / Agent_Side v1.2 / HITL_Prompt v1.1)
was archived M6 PR4 (ADR-031) → `archive/rule/` (frozen; see `archive/rule/TOMBSTONE.md`).
Active doc-governance now lives in the kernel:

- `policies/documentation.md` — 12-type taxonomy + `track` field + path-to-track tree +
  **PR gates A1-A6 + OB1-OB5** + frontmatter schema + per-type body depth + **CLAUDE.md
  sync-allowlist (§7)** + 项目根 5-file 例外 (§2.6).
- `policies/archive.md` — triggers / active-path-stability / `archive.yml` / ceremony /
  ai_visibility / retention. `sdd/lifecycle.md` — 9/4/5-state (capability / working-doc / canonical).
- `sdd/workflows/execution-loop.md` — 17-stage HITL loop (gates 5/7/9/11/13) + §7 post-merge.
  `sdd/adapters/{runtime-skill,prompt,contract,claude-code-skill}.md` — **A7-A12** + loader
  frontmatter-strip contract.
- `policies/ai-agent.md` §4 — HITL 10-enum + Codex boundary + **A14**; `policies/ci-gates.md`
  §5.1 — **A13**. `policies/git-branching.md` + `policies/release.md` — branch / G1·G2 /
  PR-template / SemVer (M6 X6; how-to in `docs/infrastructure/git/`). `decisions/ADR-024` —
  EVAL spec (active). Markdown: `docs/rule/[STANDARD]_GitHub_Markdown.md`; onboarding:
  `docs/guide/[GUIDE]_Developer_Onboarding.md`.
- **跨项目借鉴边界**: borrow only external problem-framing; concrete schemes are mj-agent-native (attribution → glossary).
- **项目根 5 文件**（README/CONTRIBUTING/CHANGELOG/GLOSSARY/CLAUDE.md；不入 canonical 治理；A1-A3 不适用，A4/A6 适用）.

## Three-source SKILL distinction (两类 skill 严格区分 — 施加约束前先分类)

| Source | Path | Schema | Loader | Track |
| --- | --- | --- | --- | --- |
| in-source runtime | `src/mj_agent/skills/<name>/` | 13-field | `load_skill()` (strips frontmatter) | B — 业务；LLM 输入 |
| in-tree workflow | `.claude/skills/mj-agent-<group>-<verb>/` | 2-field (ADR-013) | Claude Code main process | C — 工程编排 |
| marketplace plugin | `mj-agentlab-marketplace/plugins/<plugin>/` | 2-field | plugin loader | out of governance |

## Repo conventions

- **Branches (G1/G2)** — 5 types (`feature/bugfix/documentation/maintain/hotfix`). G1:
  new branch via `git worktree add ../<name> -b <name>` (never `git checkout -b`). G2:
  PR `--base develop` except `hotfix`→main. Enforced by
  `.claude/scripts/guard-git-workflow.ps1`. Rules: `policies/git-branching.md`.
- **Commits** — `<type>(<scope>): <summary>` (feat/fix/perf/refactor/test/docs/infra);
  scopes from `src/mj_agent/` modules. STANDARD:
  `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`.
- **In-tree skills** — ~34 active across 5 families (flow/git/doc/runtime/infra);
  namespace `/mj-agent-<group>-<verb>`; auto-discover (no registration). `runtime-*` are
  read-only-by-design (propose diffs; never write `src/mj_agent/{skills,prompts,agent,tools}`).
  Stage→skill map: `sdd/workflows/execution-loop.md`.
- **Templates** — `docs/_templates/TEMPLATE_*.md`; copy, don't improvise frontmatter.
- **ADRs** — active in `decisions/` (M5-PR3a); 9 superseded in `archive/decisions/superseded/`.
  Key: ADR-006 (data boundary) / ADR-008 (deploy) / ADR-029 (tool-error mw) / ADR-031 (SDD refactor).
