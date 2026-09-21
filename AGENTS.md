# AGENTS.md

# mj-agent Codex 开发入口

Codex 是本项目开发执行者，Owner 保持决策与验收单点。规则正文在 `policies/`、`sdd/` 和 capability contracts。

## Native asset ownership

`.agents/skills/`、`.agents/references/`、`.agents/README.md` 与 `.codex/{config.toml,hooks.json,rules/}` 直接维护。不再由投影、翻译、lock、sync 或 adopt 维护。正式维护权切换的依据为 ADR-040；历史客户端资产仅留作 P5 具名清理候选，不参与执行，不双份维护。

`.codex/**`、原生守卫、冻结 infra、契约、政策/SDD 元规则及 CI gate 仍须相应 Owner 批准。MCP 只包含既有 GitHub、Playwright、Serena、memory×5；biz×5 与 ssh-manager 永久禁入。不迁入个人或其他来源的服务。秘密按变量名传递；应用与 MCP 凭据分离。

项目和 hooks 信任均由工程师独立审阅；不得改个人配置、自动信任或激活 hooks。

## Local constraints

编辑前读取 `capabilities/AGENTS.md`、`docker/AGENTS.md`、`src/mj_agent/AGENTS.md` 或 `tests/AGENTS.md`。局部规则与根入口共同生效。

### Self-enforced boundaries (READ THIS — it is the only guardrail on you)

Codex 必须自守 `policies/ai-agent.md` §4 的 OWNER_APPROVAL_REQUIRED。原生 hooks/rules 是协作保护，不是完整沙箱。聊天批准不解锁 hook；无可执行路线返回 BLOCKED_EXECUTION_ROUTE，禁止建凭证、换工具或改权限绕过。

1. **Data boundary (ADR-006 / ADR-009 / ADR-000) — never bypass it.** All business-warehouse (biz)
   data access MUST go through the agent tool-chain (`find_biz_context → list_biz_tables →
   describe_biz_table → execute_sql`). Do NOT connect to any database directly (psql / psycopg / any
   client) — that bypasses the L1/L1b SQL guardrails and may use non-analyst credentials. biz access
   is **read-only** via the `analyst` role; no writes, no DDL, no schema changes.
2. **Secrets — never read or exfiltrate.** Do NOT open, print, log, or transmit `.env`,
   `config/secrets*.enc`, or any credential; do not use secrets to reach services outside the
   sanctioned tool-chain.
3. **4 项 in-source 专属必停 + protected surfaces — Owner HITL 拍板 required before editing.** Do NOT
   edit `src/mj_agent/tools/sql/{guardrail,precheck}.py`, `src/mj_agent/prompts/system.md`,
   `src/mj_agent/skills/*/SKILL.md` bodies, or `src/mj_agent/biz_catalog/qcm_catalog.yaml` without
   explicit Owner sign-off (per `policies/ai-agent.md` §4 canonical 10-enum). Same for `.codex/**` trust posture, native guard/configuration, frozen infra contracts, `config/secrets*.enc` / GRANT SQL, and `docker/compose.prod.yml`.
   **Also `docker/Dockerfile` external registry image refs** — `FROM <image>` and
   `COPY --from=<registry image>` (internal `COPY --from=<stage>`, e.g. `--from=builder`, is NOT in
   scope; every other Dockerfile line needs ≥ 2 reviewer, not Owner sign-off). This one is stated
   here explicitly because it binds you and **nothing else does**: it has no `permissions.ask` entry
   and no CI gate, and `docker/AGENTS.md` — where its local table lives — only loads once your cwd is
   under `docker/`. Rule body + approval levels: `policies/docker-runtime.md` §4; canonical enum
   anchor `secrets-grants-or-prod-config` (per #408 / #413).
4. **Commit / push / PR / merge — `OWNER_APPROVAL_REQUIRED` (Owner HITL 拍板).** You may prepare
   changes and run verification freely, but treat commit, push, PR creation, and merge as gated
   actions needing the Owner's go-ahead (per ADR-034).
5. **Git workflow discipline (G1/G2) binds you too.** New branches ONLY via
   `git worktree add ../<branch-name> -b <branch-name>` — never `git checkout -b` / `git switch -c`
   (G1); `gh pr create` must carry an explicit `--base` (non-hotfix → develop, hotfix → main) (G2).
   原生守卫识别范围有限；你仍必须自守 `policies/git-branching.md`。
6. **Parity of authority = parity of constraint.** Being authorized relaxes no security surface.
   When in doubt, stop and ask the Owner.

**Owner remains the single decision-maker** (HITL 拍板); each PR declares which agent implemented,
and git authorship records provenance.


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

## Commands

```bash
uv run ruff check
uv run mypy src/mj_agent
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit -q
python scripts/sdd/check_codex_native.py
python scripts/sdd/check_native_skills.py
```

离线 pytest 的外部依赖一律 SKIP_POLICY_EXTERNAL_DEPENDENCY；凭据存在不启用外部测试。live probe、容器生命周期、部署和凭据写入另需授权；SKIP、静态检查和批准不等于运行证据。

## Documentation and workflow

`docs/INDEX.md` 是文档入口，`sdd/workflows/execution-loop.md` 是17阶段工作流；本次请求只执行获授权阶段。技能发现见 `.agents/skills/SKILL_INDEX.md`，模板见 `docs/_templates/`。runtime skill 由 `load_skill()` 去 frontmatter，开发技能由 Codex 发现，两者不能混用。

Git 新分支只用 worktree；PR 显式 base（通常 develop，hotfix 为 main），人工 merge。提交格式与 scope 以 `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` 为准。ADR 编号先核对 `decisions/` 与归档命名空间。报告实施来源、HITL、BDD/TDD、委派和未验证项。
