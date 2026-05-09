---
type: plan
summary: 4-PR bundle — mj-agent 多环境 docker-compose 分层 (dev/test/prod) + LLM provider 抽象 (Ark + DGX 本地 vLLM/SGLang/Ollama 消费侧) + .mcp.json 完整建设 (10 servers，对标 mj-system) + ADR-025
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] mj-agent multi-env + DGX LLM provider + .mcp.json bundle

> 4-PR sequential bundle，落地 mj-agent 与 mj-system 的部署运维一致性 + DGX 算力消费支持 + Claude Code MCP 配置补齐。Phase 1 sub。

## Context

mj-agent 当前是 dev-only 形态：单一 `docker-compose.mj-agent.yml` 硬编码 dev profile（`POSTGRES_DEV_HOST: mj-postgres` / `com.mj-agent.environment: "development"` 写死，无 `MJ_CONFIG_PROFILE` 注入，无资源限制），`src/mj_agent/llm.py` 仅 Volcengine Ark provider，仓库根**无 `.mcp.json`**。

ADR-008 § Decision 已经明确 "环境矩阵 DEV/TEST/PROD 时间表对齐 mj-system" — 但 Phase 1 sub 1.H 只补了 dev compose，TEST/PROD 覆盖文件从未补齐。同时 DGX-Spark (192.168.0.189) 即将作为团队本地 LLM 算力节点（vLLM/SGLang serving；部署责任另议），mj-agent 需要支持把 LLM 调用切换到 OpenAI-compatible local endpoint。

**用户决策**（2026-05-09 plan-mode AskUserQuestion 已确认）：
1. mj-agent 容器栈跟随 mj-system 在 TEST (179) / PROD (106) 同主机部署
2. DGX 仅作算力提供（**不部署**任何应用服务，含 mj-agent 与 mj-system）→ DGX 支持本质是 LLM provider 抽象，**不**是新加 profile
3. LLM serving 部署责任另开 issue；mj-agent 仅做**消费侧**配置
4. Phase 1 仅做配置抽象（**不**写 `docker-compose.dgx.yml`）
5. `.mcp.json` 完整对标 mj-system 模式

详细设计 + 文件级 diff sketch + 验证矩阵见 Claude Code plan-mode artifact `~/.claude/plans/mj-system-d-workspace-10-software-proje-snug-dongarra.md`（plan-mode 内部产物，不入仓）。

## Scope（4 PRs sequential）

### PR-1: `feature/98-multi-env-compose-layering`（issue [#98](https://github.com/MJ-AgentLab/mj-agent/issues/98)）
- Refactor `infra/docker/docker-compose.mj-agent.yml` 为 env-agnostic base
- 新建 `infra/docker/docker-compose.{override,test,prod}.yml`
- 更新 `infra/docker/README.md` profile matrix
- 更新 `mj-agent-infra-docker-compose` SKILL.md（4 profile -f 命令 + DGX preflight）
- **重要 quirk**：dev 也用显式 `-f base -f override`（auto-load 仅在 cwd default 模式触发，本仓 compose 在 `infra/docker/` 子目录 + `-f` 显式 base 时不生效）

### PR-2: `feature/llm-provider-abstraction`
- `src/mj_agent/config.py` 加 `llm_provider` / `llm_base_url` / `llm_api_key` 字段 + `effective_llm_*` cached_property（**不**改 `Profile` enum）
- `src/mj_agent/llm.py` `make_llm()` factory 分支（`ark` 路径不变；`local-openai-compat` 路径 ChatOpenAI 不带 `extra_body.thinking`）
- `src/mj_agent/server/cli.py` provider-aware healthcheck
- `.env.example` §2 rewrite + 保留 `ARK_*` 向后兼容
- 新建 `mj-agent-infra-llm-endpoint-probe` SKILL（DGX vLLM /v1/models 探针）
- 更新 `mj-agent-infra-env-setup` + `mj-agent-infra-studio-probe` SKILLs

### PR-3: `feature/mcp-json-and-governance`
- `.mcp.json` 10 servers（github / serena / pg-mj-agent-memory × 5 / pg-mj-system-biz × 5 / ssh-manager 含 DGX-LAN/WAN）
- `.claude/scripts/pg-server-{start.cmd,wrapper.mjs}` verbatim 从 mj-system 复制
- `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md` + `INDEX.md`（**领域专属** placement per ADR-022 C.3.2 + Meta v2.2 §3.7；**无版本后缀** per ADR-018）
- `.env.example` §8 (SSH 密码) + §9 (MCP pg URL)
- `config/secrets.example` 同步

### PR-4: `documentation/env-teardown-and-doc-sync`
- 新建 `mj-agent-infra-env-teardown` SKILL（镜像 mj-sys-ops-env-teardown 3-level）
- 新建 ADR-025 `Multi_Environment_And_LLM_Provider_Abstraction`（`track: shared`）
- 同步 CLAUDE.md（5 段更新 + §A14 行 STANDARD 引用路径 + §Documentation ADR summary block 加 ADR-025 段）
- 同步 `config/README.md` + `infra/docker/README.md`
- 小更新 `mj-agent-infra-storage-stack` SKILL

## 严格守约（Out-of-Scope）

- **不**写 `docker-compose.dgx.yml`（用户决策 4；Phase 1 仅配置抽象）
- **不**加 `Profile = Literal[..., "dgx"]` 到 config.py（DGX 不部署 mj-agent，没有"DGX 部署 profile"概念）
- **不**加 `POSTGRES_DGX_HOST/PORT`（DGX 上无 biz pg）
- **不**部署 LLM serving 容器（用户决策 2/3；另开 issue）
- **不**关闭 A8/A11 EVAL transitional waiver（per ADR-024，Phase E 工作；本 plan 新建的 in-tree workflow skills 不受 EVAL 约束）
- **不**修改 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/system.md`（in-source canonical；HITL §3.1 mj-agent 专属必停项；本 bundle 不涉及）
- **不**修改 `src/mj_agent/biz_catalog/qcm_catalog.yaml`（HITL §3.1 必停项）
- **不**修改 `src/mj_agent/tools/sql/{guardrail,precheck}.py`（HITL §3.1 必停项；ADR-006/009 数据边界红线）

## HITL Gates

- **Stage 5 Gate 1（Plan 确认）**：已在 plan-mode AskUserQuestion 阶段完成（2026-05-09）
- **Stage 7 Gate 2（设计确认）**：PR-4 ADR-025 草稿后必触发 — `track: shared` ADR 涉及 multi-domain 决策（compose + LLM provider + MCP），需 SWE Reviewer + Tooling Reviewer + (optional) Domain Expert
- **Stage 9 Scope drift gate**：每 PR 实现中如出现偏离上文 Scope 的修改，必停
- **Stage 11 Self-review**：每 PR commit 前
- **Stage 13 Push gate**：每 PR push 前

## 关键 ADR / STANDARD 引用

- ADR-006 / ADR-009 — 数据边界（不动）
- ADR-008 — mj-agent 独立 compose project（不动；4-file 分层不破坏 `name: mj-agent` 单 project name）
- ADR-013 — in-tree SKILL native schema（新 SKILL 用此 schema）
- ADR-016 — in-tree skills ecosystem（命名空间 `mj-agent-<group>-<verb>`）
- ADR-018 — active path stability（STANDARD 文件名无 `_vX.Y` 后缀）
- ADR-022 C.3.2 — STANDARD placement 决策（领域专属 → `docs/infrastructure/<domain>/`）
- ADR-024 — Agent_Side v1.2 §4 EVAL spec（A8/A11 waiver 延续 Phase E；in-tree skill 不受约束）
- ADR-025 — **本 bundle 引入**（PR-4）
- HITL_Prompt v1.0 §3.1 — mj-agent 专属必停项（本 bundle 不触及）

## 进度

- ✅ **PR-1** — `feature/98-multi-env-compose-layering`（issue [#98](https://github.com/MJ-AgentLab/mj-agent/issues/98)；PR [#99](https://github.com/MJ-AgentLab/mj-agent/pull/99)；merged 2026-05-09 commit `804310a`）
- 🔄 **PR-2** — `feature/100-llm-provider-abstraction`（issue [#100](https://github.com/MJ-AgentLab/mj-agent/issues/100)；in-progress；待 commit + push + PR 创建 + merge）
- ⏳ PR-3 — `feature/mcp-json-and-governance`（blocked by PR-2 merge）
- ⏳ PR-4 — `documentation/env-teardown-and-doc-sync`（blocked by PR-3 merge）
