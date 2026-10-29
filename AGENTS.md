# AGENTS.md

# mj-agent Codex 开发入口

Codex 是本项目开发执行者，Owner 保持决策与验收单点。规则正文在 `policies/`、`sdd/` 和 capability contracts。

需要 Owner 作新决策时，Codex 先完成可审阅的准备工作，再提供具体可行的选项，明确标注推荐项并简述理由与影响；Owner 选择后，由 Codex 在获批范围内使用正常工具执行并验证。独立Agent完成技术核验；需宿主正常机制的步骤核实际支持，技术拒绝保留原错，不改权限或个人配置绕过。

## Native asset ownership

`.agents/skills/`、`.agents/references/`、`.agents/README.md` 与 `.codex/config.toml` 直接维护；依据 ADR-040。Agent-first 治理依据 [ADR-042](decisions/ADR-042_Agent_First_Delivery_Governance.md)，执行正文在 `policies/ai-agent.md` §2/§4 与 `sdd/workflows/execution-loop.md`。

## 接受基线、授权与技术边界

启动任务分别记录结果 AC 与允许操作、对象、环境、权限、副作用、资源及停止条件。目标、对象、环境、权限和风险边界未实质变化且未撤销时复用任务授权；普通技术选择、Plan、实现、测试、文档及局部修复自主推进。提交/普通推送/PR/merge 可集中授权，删除和权限变更独立列明。工具、权限和 CI 通过不产生授权。

风险标签用于定位，不以路径命中自动审批。四类 runtime 面与兼容契约的基线内安全保持、重构及修复自主完成并提供行为/负例证据；SQL 安全不变量、数据范围、业务口径、外发边界、breaking 承诺、接受标准、必要门禁、信任/权限及生产策略变化由 Owner 作实质决定。

存在未决定的实质变化或缺动作授权时标 `OWNER_APPROVAL_REQUIRED`，先准备具体可审阅方案；风险未知或技术拒绝只暂停受影响步骤。

编辑前读取目标目录 `capabilities/AGENTS.md`、`docker/AGENTS.md`、`src/mj_agent/AGENTS.md` 或 `tests/AGENTS.md`。

1. **业务数据边界 — never bypass it**：biz 访问始终经 `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`，analyst 只读。Do NOT connect to any database directly；禁止直连 DB、写、DDL 或绕过 L1/L1b。
2. **秘密与服务边界 — never read or exfiltrate**：模型不读取/打印/记录/传输 `.env`、`config/secrets*.enc` 或真实凭据。仅新建单仓mj-agent-delivery-executor App的私钥/短期token允许由受控后台创建、DPAPI保存、签名、注入和撤销；模型、聊天、日志不可见。现有应用/MCP/DB/个人秘密永不读取，该例外不扩大服务、权限或操作授权。应用/MCP 凭据分离，仅变量名传递。项目 MCP 为 GitHub、Playwright、Serena、memory×5 和具名 ssh-manager（B：9入口/既有账户含cloud root及生产）；SSH按任务授权，不准绕业务链或读秘密。biz×5和个人/其他来源服务永久禁入；SSH细则见 policies/codex-development.md。
3. **信任与技术拒绝**：项目Codex采用MCP-only结构，现行要求见 `repo:policies/codex-development.md`；实际宿主限制和按需MCP连接分别验证，旧项目守卫加载不作为日常开发前置。实际拒绝保留原错、按证据定位；无法定位标未知，受阻步骤返回 `BLOCKED_EXECUTION_ROUTE`，禁止建凭证、换工具、编码、改写命令或改权限绕过。
4. **删除与重入**：具名授权删除前核验绝对路径、Git 跟踪/未提交/未跟踪/忽略内容、必要备份、占用及目标/后代重解析点。复用具体清单；实质变化只暂停受影响项。部分成功或结果未知先对账，成功项不重复。
5. **Git**：新分支只用 `git worktree add ../<branch-name> -b <branch-name>`；PR 显式 base，通常 develop、hotfix main；release独立发布需接受/授权及未来具名规则映射，当前有限解析器不声称支持；任务集成例外按 `policies/git-branching.md` 登记精确 head/base。Owner在聊天对实际成果/SHA作批准或接受决定；Agent依该真实决定以不同于作者/最后推送者的Owner身份执行平台审核，补推须重新取得有效决定/审核，批准与业务接受分记；App承担作者/推送/PR/merge，无Administration、Checks write或bypass。
6. **交付与接受**：独立核验从 AC 建立期望、读取真实成果并复现；阶段是检查点，不固定人工暂停。仓库批准、集成、运行验证、交付及 Owner 接受分别记录；Plan completed 须 AC 满足、成果可用且 Owner 明确接受版本。门禁自降防护首期依赖 Owner 审阅补偿，独立可信核验仍延期。

## 会话维护

用户明确要求归档本次对话、推荐标题、命名或重命名当前任务时，读取 [会话维护规则](sdd/workflows/session-maintenance.md)。普通归档和推荐标题默认只生成文字；明确重命名复用已有授权并调用实际客户端功能，成功才报告。额外保存/客户端归档按明确请求处理。

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

新 working 放 `plans/<topic>/`，主 `[PLAN]_<topic>.md` 与目录一致；独立目录可只有 Intake/报告。四种真实主要 I/P 命名、受控补号/引用修复和七字段见 `policies/documentation.md` §2.7。仅主 Plan completed 必须 AC/可用成果/Owner准确版本接受；其他 working 按自身交付条件，报告完成不推导整体接受；完成原位保留、不运行 working GC。

原意正本用正式 `docs/intent/` INTENT 或简单任务唯一 Issue 原意区，来源/责任不明仅 working 草稿。ID/九字段/原位退役及原意核对、内容接受、执行授权、交付接受分记见 `policies/documentation.md` §2.8；接受须可恢复完整基线，机器 PASS 不认证真实决定。新增目录/深相对链接检查为 `python scripts/check_working_docs.py`。

创建或维护 mj-agent 项目附属 Site 前，读取并遵循 [Site 命名规范](docs/rule/[STANDARD]_MJ_Agent_Site_Naming_Convention.md)。

Git 新分支只用 worktree；PR显式base（通常develop，hotfix main；release独立发布需接受/授权及未来具名规则映射，当前有限解析器不声称支持，分层关系精确登记）；授权内merge须有效平台审核及门禁满足。提交格式与 scope 以 `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` 为准。ADR 编号先核对 `decisions/` 与归档命名空间。报告实施来源、HITL、BDD/TDD、委派和未验证项。
