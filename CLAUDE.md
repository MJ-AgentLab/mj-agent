# CLAUDE.md

Guidance for Claude Code. **Detail lives in the SDD kernel (`policies/` + `sdd/`) +
`docs/INDEX.md`; this file is the high-frequency cache — 指针, not source-of-truth.**

@AGENTS.md

> ↑ 工具中立协作契约（同层导入，不复制正文；per dual-agent-compat v5 P1）。嵌套局部约束在
> `capabilities/` `docker/` `src/mj_agent/` `tests/` 各自 `AGENTS.md`，由同层 `CLAUDE.md` 同款导入。

## Codex Status

Codex is an **authorized full development participant** (per ADR-035 + 2026-07-06 amendment) — the
former "read-only / NOT in dev workflow" boundary is retired. As a **standalone agent (path A)**,
Codex may run commands + do dev work now, governed by `AGENTS.md` (its operating contract) + its own
"Full access" permission — it runs under **its own harness**, so mj-agent's `ask`-gates /
protected-path prompts do **not** bind it; the 5 必停 + data boundary (ADR-006/009/000 unchanged) are
**self-enforced via AGENTS.md prose**. Still deferred: **(B) Claude Code invoking Codex** as a
sub-tool (the `codex:` plugin — needs `.claude/` wiring); (B) does not limit (A). Each task declares
Codex participation (`NONE` or its contribution). Full contract: `AGENTS.md` +
`policies/ai-agent.md` §1 + `decisions/ADR-035`.

## Project

`mj-agent` = MJ-AgentLab data agent: LangChain 1.x + LangGraph 1.1.8, Python 3.13, `uv`.
Lets internal analysts explore the mj-system biz metrics warehouse in natural language.
Executing the **data-agent MVP** (Phase 1) per `plans/[PLAN]_mj-agent-data-agent-mvp-framework.md`
+ `plans/mj-agent-roadmap-v1.6.md`. Docs entry: `docs/INDEX.md`. Upstream-warehouse terms +
cross-repo attribution: `docs/glossary/upstream_business_warehouse.md` (bootstrap borrowed
external problem-framing only; all active governance is mj-agent-native).

## 必停 surfaces (pause for HITL 拍板 — AI 提议 + Owner 拍板后 AI 落盘；never flip unilaterally)

> **HITL 模型 (ADR-034 / execution-loop §3.0)**：暂停 ≠ 让 Owner 手动转写。AI 呈现方案/diff →
> Owner 拍板（AskUserQuestion 选 / 权限 prompt 批准）→ **AI 直接落盘**。下列前 3 类必停面由
> `.claude/settings.json` `permissions.ask` / protected-path prompt 逐写拍板门 enforce
> （原 `deny` 物理硬锁已解除），A13/A14 合并审查兜底；**仅交互模式成立**（`auto`/`bypass` 下
> 放宽类改动被 classifier 硬拦）。**第 4 类（docker 供应链面）没有 harness 载体**，与
> `policies/ai-agent.md` §4 的 D-017 扩展邻接面同属「声明为必停但靠纪律 + merge review 兜底」一档。

- **Data/agent 必停** (5; `ask`-gated): `src/mj_agent/tools/sql/guardrail.py` (L1) ·
  `tools/sql/precheck.py` (L1b) · `prompts/system.md` · `skills/*/SKILL.md` bodies ·
  `biz_catalog/qcm_catalog.yaml`.
- **Infra freeze skills** (8): `.claude/skills/mj-agent-infra-*/SKILL.md` —
  content-hash freeze per `policies/ai-agent.md` §7; record in
  `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml`.
- **Protected paths** (`.claude/**` / `.mcp.json` / `.claude.json`): harness 硬编码——交互模式
  写入必弹权限 prompt（= 拍板，`allow` 不可抑制）；AI 改、Owner 拍板、A13/A14 兜底（per §9）.
- **Docker 供应链面**（**无 harness 保护、无审批类 CI gate —— 靠纪律**；`docker-build` 只验镜像
  可构建、V5 只 lint 契约字段，均不判拍板）: `docker/Dockerfile` 外部
  registry 镜像引用（`FROM <image>` + `COPY --from=<registry image>`；内部 `COPY --from=<stage>`
  **不**在内）改前须 Owner 拍板。规则体 `policies/docker-runtime.md` §4；canonical anchor =
  `secrets-grants-or-prod-config`（#408 / #413）。**刻意不进 `ask` 列表**——`ask` 只能整文件匹配，
  会把 #408 排除的内部 stage 拷贝一并纳入。Dockerfile 其余行 = ≥ 2 reviewer，非必停。
- **Gated actions**: CI gate blocking-flip (`continue-on-error true→false`) =
  `ci-blocking-gate-toggle`; `.mcp.json` trust-posture change = A14; `.env` /
  `config/secrets*.enc` 保持 permission-`deny`（AI 取不到的外部 secret 走 §8 给 Owner 步骤）.
  HITL canonical 10-enum + pre-flight discipline: `policies/ai-agent.md` §4 / §7 / §8 / §9.
  HITL gates fire at execution-loop stages 5/7/9/11/13.

## Architecture

Entry: LangGraph Studio (`langgraph.json`) / Chainlit (`src/mj_agent/ui.py`) /
CLI (`server/cli.py`: `mj-agent serve|check`). Runtime:
`create_agent(model, tools, system_prompt, middleware)`.

- `agent.py` — `make_graph()` is the `langgraph.json` entry; lazy `make_llm()` so
  import never needs `ARK_API_KEY`. `_ACTIVE_SKILLS` (active skill set — names/count live in the `agent.py` tuple, not cached here) +
  `_build_system_prompt()` concatenates `prompts/system.md` + skill bodies.
- `tools/__init__.py:ALL_TOOLS` — `find_biz_context` → `list_biz_tables` →
  `describe_biz_table` → `execute_sql` (default LLM order). SQL chain:
  `tools/{biz_context,sql/introspect,sql/guardrail,sql/precheck,sql/execute}.py`.
- `middleware/tool_errors.py` — `SQLToolErrorMiddleware`（single middleware, BOTH
  `wrap_tool_call` + `awrap_tool_call` hooks — never split; ADR-029 amendment #288）
  turns SQL ValueError/RuntimeError into a `ToolMessage` so the LLM self-corrects.
- `memory/checkpointer.py` — AsyncPostgresSaver on the dedicated `mj-agent-postgres`
  container. `integrations/mj_system_db.py` — read-only psycopg pool. `llm.py` —
  `make_llm()` provider factory. `config.py` — pydantic-settings over `.env`.
  `biz_catalog/{loader,finder}.py` + `qcm_catalog.yaml` (mirrors upstream data-dictionary).
  Infra: `docker/{Dockerfile,compose*.yml,postgres-init/}` (redis provisioned, unused).

## Data boundary (ADR-006; 4 layers, `analyst` RO PG role)

| Layer | Mechanism | Location |
| --- | --- | --- |
| L1 | hybrid: regex single-stmt/SELECT-only/blocked-keyword + sqlglot-AST schema + biz_dwd allowlist | `tools/sql/guardrail.py` |
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
  sync-allowlist (§7)** + 项目根 5-file + `AGENTS.md` 例外 (§2.6).
- `policies/archive.md` — triggers / active-path-stability / `archive.yml` / ceremony /
  ai_visibility / retention. `sdd/lifecycle.md` — 9/4/5-state (capability / working-doc / canonical).
- `sdd/workflows/execution-loop.md` — 17-stage HITL loop (gates 5/7/9/11/13) + §7 post-merge.
  `sdd/adapters/{runtime-skill,prompt,contract,claude-code-skill}.md` — **A7-A12** + loader
  frontmatter-strip contract.
- `policies/ai-agent.md` §1 — Codex 参与策略 · §4 — HITL 10-enum + **A14**; `policies/ci-gates.md`
  §5.1 — **A13**. `policies/git-branching.md` + `policies/release.md` — branch / G1·G2 /
  PR-template / SemVer (M6 X6; how-to in `docs/infrastructure/git/`). `decisions/ADR-024` —
  EVAL spec (active). Markdown: `docs/rule/[STANDARD]_GitHub_Markdown.md`; onboarding:
  `docs/guide/[GUIDE]_Developer_Onboarding.md`.
- **跨项目借鉴边界**: borrow only external problem-framing; concrete schemes are mj-agent-native (attribution → glossary).
- **项目根 5 文件**（README/CONTRIBUTING/CHANGELOG/GLOSSARY/CLAUDE.md）+ **AGENTS.md**（AI agent 指令契约，per ADR-035）；均不入 canonical 治理；A1-A3 不适用，A4/A6 适用（§2.6）.

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
  **35-scope closed allowlist** (v1.1 — `src/mj_agent/` modules + engineering/test/build +
  doc-governance areas); omit scope when genuinely mixed. STANDARD:
  `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`.
- **In-tree skills** — active across 5 families (flow/git/doc/runtime/infra);
  namespace `/mj-agent-<group>-<verb>`; auto-discover (no registration). `runtime-*` follow
  propose→拍板→apply (ADR-034): propose diff → stop at `OWNER_APPROVAL_REQUIRED` → apply via
  `ask` gate; never write `src/mj_agent/{skills,prompts,agent,tools}` without 拍板.
  Stage→skill map: `sdd/workflows/execution-loop.md`.
- **Templates** — `docs/_templates/TEMPLATE_*.md`; copy, don't improvise frontmatter.
- **ADRs** — active in `decisions/` (M5-PR3a); 9 superseded in `archive/decisions/superseded/`.
  Key: ADR-006 (data boundary) / ADR-008 (deploy) / ADR-029 (tool-error mw) / ADR-031 (SDD refactor).
