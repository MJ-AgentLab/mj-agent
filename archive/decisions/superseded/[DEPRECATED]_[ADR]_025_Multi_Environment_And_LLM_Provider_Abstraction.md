---
type: adr
domain: OPS
summary: PR-1/2/3/4 multi-env+DGX+MCP bundle 跨多 domain 决策统一记录 — docker-compose 4-file 分层（dev/test/prod）+ LLM provider 抽象（Ark + local-openai-compat for DGX）+ .mcp.json 13 servers governance；DGX 仅作算力提供（不部署 mj-agent）；ADR-008 独立 secrets pipeline 保留
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: deprecated
archived: 2026-05-11
replaced-by:
  - decisions/ADR-026_Multi_Environment_Compose_Profile.md
  - decisions/ADR-027_LLM_Provider_Abstraction.md
  - decisions/ADR-028_MCP_Server_Inventory_And_Governance.md
decision: accepted
track: shared
tags:
  - adr
  - infrastructure
  - docker
  - llm
  - mcp
  - dgx
  - mj-system-derivation
---

# ADR 025: Multi-Environment Deployment + LLM Provider Abstraction + MCP Governance Bundle

## Context

Phase 1 sub 1.H（PR #40）落地 mj-agent dev compose 后，mj-agent 一直处于 dev-only 形态。具体缺口：

- **多环境**：ADR-008 § Decision 已经明确 "环境矩阵 DEV/TEST/PROD 时间表对齐 mj-system"；但 `infra/docker/docker-compose.mj-agent.yml` 单文件硬编码 dev profile（`POSTGRES_DEV_HOST: mj-postgres` / `com.mj-agent.environment: "development"` 写死、无 `MJ_CONFIG_PROFILE` 注入、无资源限制）；TEST/PROD 覆盖文件从未补齐。无法在 192.168.0.179 (TEST) / .106 (PROD) 主机部署。
- **LLM provider**：`src/mj_agent/llm.py` 仅 Volcengine Ark；DGX-Spark (192.168.0.189) 即将上线作为团队本地 LLM 算力节点（vLLM/SGLang/Ollama serving；deployment 责任另议），mj-agent 无路径切到 OpenAI-compatible local endpoint。
- **MCP**：CLAUDE.md §A14 引用 `[STANDARD]_MJ_Agent_MCP_Server_Governance` 但 STANDARD **不存在**（dangling reference）；仓库根**无 `.mcp.json`** — Claude Code 内开发者无法直连 mj-agent-memory 调试 langgraph_checkpoints 表，也无法 SSH 到 DGX-Spark 维护 LLM serving 容器。

2026-05-09 plan-mode AskUserQuestion 与项目负责人确认 5 项关键决策，分 4 PR 实施：

1. mj-agent 容器栈跟随 mj-system 在 TEST/PROD 同主机部署
2. **DGX 仅作算力提供，不部署任何应用服务（含 mj-agent 与 mj-system）** → DGX 支持本质是 LLM provider 抽象，**不**是新加 profile
3. LLM serving 部署责任另议；mj-agent 仅做消费侧
4. Phase 1 仅做配置抽象，不写 `docker-compose.dgx.yml`
5. `.mcp.json` 完整对标 mj-system 模式

每项单独 ADR 过细（4 micro ADR 增加治理噪声 + 决策面交叉）；bundle 单个 ADR-025 + 4 顺序 PR 实落代码与文档。

## Decision

### D.1 docker-compose 4-file 分层（PR-1 / mj-system v3.2.2 派生）

参考 mj-system `docker-compose.{yml,override.yml,test.yml,prod.yml}` 模式：

| 文件 | 加载 | 关键差异 | 资源限制 |
|---|---|---|---|
| `docker-compose.mj-agent.yml` | 始终 | env-agnostic base；env vars `${VAR:-default}`；`name: mj-agent`；通用 env (`MJ_AGENT_MEMORY_HOST` / `CHAINLIT_HOST=0.0.0.0`)；networks + volumes 声明 | 无 |
| `docker-compose.override.yml` | dev `-f` 显式 | `build:` 本地 Dockerfile；`MJ_CONFIG_PROFILE=dev`；`POSTGRES_DEV_HOST=mj-postgres`；`MJ_AGENT_LOG_LEVEL=debug` | 无 |
| `docker-compose.test.yml` | test `-f` 显式 | Harbor pull `8.135.38.175/mj-agent/mj-agent:0.1`；`MJ_CONFIG_PROFILE=test`；`POSTGRES_TEST_HOST=mj-postgres` | mj-agent 8C/12G；mj-agent-postgres 4C/8G |
| `docker-compose.prod.yml` | prod `-f` 显式 | Harbor pull；`MJ_CONFIG_PROFILE=prod`；`POSTGRES_PROD_HOST=mj-postgres`；`MJ_DEBUG=false`；`MJ_AGENT_LOG_LEVEL=warning`；json-file logging | mj-agent 4C/12G；mj-agent-postgres 4C/8G |

**重要 quirk**：dev 也用显式 `-f base -f override`。原因：本仓 compose 文件在 `infra/docker/` 子目录 + 用 `-f` 显式 base 时，docker compose 的 override.yml auto-load **不生效**（auto-load 仅在 cwd default 模式触发；mj-system compose 在仓根所以可以 auto-load）。让 dev/test/prod 都用相同 `-f base -f overlay` 形态反而更可读。

**Compose project name**：`name: mj-agent` 跨 4 profile 不变（per ADR-008 独立 compose project）。

### D.2 LLM provider 抽象（PR-2）

`src/mj_agent/llm.py` `make_llm()` 从单一 Ark 路径扩展为 provider 分支 factory：

| Provider | base_url | api_key | extra_body | 适用 |
|---|---|---|---|---|
| `ark`（默认） | `effective_llm_base_url` fallback `ark_base_url` | `effective_llm_api_key` fallback `ark_api_key` | `{"thinking": {"type": "enabled\|disabled"}}` | 公网 Ark + DeepSeek V3 |
| `local-openai-compat` | `llm_base_url`（必填；缺即 LLMConfigError） | `llm_api_key` 或 `"EMPTY"` sentinel | **不带**（vLLM/SGLang/Ollama 不接受 Ark `thinking` 参数，传入会 422） | DGX-Spark vLLM/SGLang/Ollama/TGI/llama.cpp |

**`Profile` enum 不变**（保持 `Literal["dev","test","prod"]`） — DGX 不部署 mj-agent，没有 "dgx" profile 概念；DGX 支持是 LLM endpoint 切换，**正交**于 `MJ_CONFIG_PROFILE`（biz pg host 决定）。

**向后兼容**：`LLM_PROVIDER` 默认 `ark` + `effective_llm_*` cached_property fallback 至 `ark_*` 字段 → 现有 `.env` 不动则 `make_llm()` 行为完全一致。

### D.3 .mcp.json + STANDARD MCP_Server_Governance（PR-3）

`.mcp.json` 13 servers，对标 mj-system 模式但用独立 secrets 命名空间：

- `github` (first-party) + `serena` (third-party oraios)
- `pg-mj-agent-memory-{dev,test-lan,test-wan,prod-lan,prod-wan}` × 5（langgraph checkpointer DB）
- `pg-mj-system-biz-{dev,test-lan,test-wan,prod-lan,prod-wan}` × 5（biz pg via analyst RO；ADR-006/009 数据边界 DB-side GRANT 兜底）
- `ssh-manager` (third-party `@iflow-mcp`；9 SSH entries: cloud + 4 hosts × 2 lan/wan，含 **DGX-Spark 192.168.0.189**)
- 省略 `n8n-docs`（mj-agent 无 n8n 集成）

**领域专属 STANDARD placement** per ADR-022 §C.3.2：`docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`（与 git/cicd 子目录平行；filename 无 `_v1.0` 后缀 per ADR-018）。STANDARD 提供 trust posture 3 等级 + credential mode 5 类矩阵 + PR-body 强制声明模板（A14 实施细则）+ 季度 audit cadence。

**Independent secrets pipeline**：所有 `MJ_AGENT_*` 命名空间 env vars 与 mj-system 的 `MJ_SYS_*` 隔离 per ADR-008。

**Wrapper script verbatim 复用**：`.claude/scripts/pg-server-{start.cmd,wrapper.mjs}` byte-for-byte 复制 mj-system；STANDARD §6 季度 audit 同步 mj-system upstream 漂移。

### D.4 env-teardown skill + CLAUDE.md sync（PR-4 收尾）

- `mj-agent-infra-env-teardown` SKILL（镜像 `mj-sys-ops-env-teardown` 3-level 模式：`down` / `down -v` / `down -v --rmi local`；profile-aware Step 0；H3 二次确认 Level 2/3）
- CLAUDE.md 5 段更新（Architecture / Commands / LLM provider / Environment variables / Active in-tree skills）+ §A14 行修订（STANDARD 路径调整）+ §Documentation ADR summary block 加 ADR-025 段
- `config/README.md` §6 + `infra/docker/README.md` cross-link

## Consequences

### 正面

- **operational consistency**：mj-agent 4 profile compose 模式与 mj-system v3.2.2 一致，分析师切环境心智负担 0；4 主机（dev / test / prod / DGX）部署语义清晰
- **DGX 算力消费即插即用**：开发者切 `LLM_PROVIDER=local-openai-compat` + `LLM_BASE_URL=http://192.168.0.189:8000/v1` 即可消费 DGX vLLM；不需新写 compose 文件 / Profile enum 扩展
- **A14 PR gate 正式生效**：之前 dangling reference 关闭；MCP server 增删必走 STANDARD §4 declaration template
- **Claude Code 内运维就近**：13 MCP servers 让分析师 / 运维直接在 Claude Code 内查 mj-agent-memory + biz pg + SSH 5 主机（含 DGX）
- **向后兼容**：默认 `LLM_PROVIDER=ark` + `Profile=dev/test/prod`（不含 dgx）+ 现有 `.env` 不改 → 既有 dev / Phase 1 流程行为完全一致

### 负面

- **dev 命令更长**：dev 也用显式 `-f base -f override`（auto-load 不生效）— PR-1 quirk 文档化在 base header / README §Profile Matrix / SKILL `Do not use for:`
- **4 profile compose 维护负担**：base 改 service 结构需要同步审查 3 个 overlay 是否冲突 — 接受（与 mj-system 一致负担）
- **Harbor image 依赖**：test/prod profile 引用 `8.135.38.175/mj-agent/mj-agent:0.1`；CI build & push 流程 + Harbor namespace 创建是 ADR-025 范围之外的依赖（PR-1 PR body Risk 段已标）
- **MCP wrapper script 与 mj-system 同步债**：`.claude/scripts/pg-server-*` verbatim 复制；mj-system 后续修改需季度 audit 同步（STANDARD §6 写明）
- **Plan complexity**：4 sequential PRs（每个 issue + branch + commit + PR + review + merge + cleanup）— 接受为换取 reviewer 视角清晰

### 暂未实现（用户决策；out-of-scope）

- **`docker-compose.dgx.yml`**：用户决策 4 — Phase 1 仅配置抽象；DGX 不部署 mj-agent
- **`Profile = Literal[..., "dgx"]`**：用户决策 2 — DGX 不部署 mj-agent，无 profile 概念
- **`POSTGRES_DGX_HOST/PORT`**：DGX 上无 biz pg；mj-agent 在 DGX 模式下访问 biz pg 仍走 PROD/TEST `POSTGRES_*_HOST`
- **LLM serving 容器部署**：用户决策 3 — 责任另议（专门 issue）
- **mj-system 同名 STANDARD 派生**：mj-agent 原生 ADR-025；mj-system 当前无对位 STANDARD（informant：mj-system 未来可派生 mj-agent 模式）

## Alternatives considered

- **A. 单一 compose 文件 + 多 `MJ_CONFIG_PROFILE` 分支**：sed/template 在 entrypoint 切换 — 拒绝。compose 4-file 模式是 mj-system 既有约定，operational consistency 优先；reviewer 看 diff 更清晰。
- **B. 加 `Profile = "dgx"` 到 enum + 写 `docker-compose.dgx.yml`**：本来是 plan-mode 初版假设 — 用户决策 2 否决。DGX 仅算力，无 biz pg / 应用服务部署，加 profile 只会引入混淆。
- **C. mj-agent 部署 LLM serving 容器（vLLM in compose）**：拒绝。GPU runtime + 模型权重 mount + 显存预留 = 大幅扩 compose 范围；用户决策 3 明示 "mj-agent 仅消费侧"。
- **D. STANDARD 落 `docs/rule/`（全局规则）**：拒绝。MCP 是领域专属（Claude Code 工具集成），per ADR-022 §C.3.2 决策矩阵应落 `docs/infrastructure/mcp/`。
- **E. 单大 PR 一次性落地（不拆 4 PR）**：拒绝。变更面跨 compose / Python runtime / .mcp.json / STANDARD / ADR / CLAUDE.md，单 PR 难以 reviewer 视角清晰；4 sequential PR 各自 ~150-550 行 diff，可独立审查 + 失败回滚。

## References

- [[[ADR]_006_Fail_Safe_Reads|ADR-006]] / [[[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]] — 数据边界（不动）
- [[[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] — 独立 compose project + 独立 secrets pipeline；4-file 分层不破坏 `name: mj-agent`
- [[[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] — in-tree SKILL native schema（新增 env-teardown / llm-endpoint-probe SKILL 用此 schema）
- [[[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] — in-tree skills `mj-agent-<group>-<verb>` 命名
- [[[ADR]_018_Active_Path_Stability|ADR-018]] — STANDARD 文件名无 `_vX.Y` 后缀
- [[[ADR]_022_P2_Framework_Enhancements|ADR-022]] §C.3.2 — STANDARD placement 决策矩阵（领域专属 → `docs/infrastructure/<domain>/`）
- [[[ADR]_024_Eval_Framework_Spec|ADR-024]] — Agent_Side v1.2 §4 EVAL spec；A8/A11 EVAL transitional waiver 延续 Phase E（本 bundle 新建的 in-tree workflow skills 不受 EVAL 约束）
- [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.7 / §3.10 / §7.7 — STANDARD placement / in-tree SKILL 治理 / A12-A14 PR gates
- [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.0]] §3.1 / §4.15 — 必停 HITL 项 / Stage 17 post-merge cleanup
- [[../infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance|STANDARD MCP Server Governance]] v1.0 — PR-3 落地；A14 实施细则
- mj-system reference: `docker-compose.{yml,override.yml,test.yml,prod.yml}` (v3.2.2)、`.mcp.json` (8 servers)、`mj-sys-ops-env-teardown` SKILL
- 4 PR 序列：[#99](https://github.com/MJ-AgentLab/mj-agent/pull/99)（compose layering）→ [#101](https://github.com/MJ-AgentLab/mj-agent/pull/101)（LLM provider）→ [#103](https://github.com/MJ-AgentLab/mj-agent/pull/103)（.mcp.json + STANDARD）→ #104（本 PR：env-teardown + ADR-025 + CLAUDE.md sync 收尾）
- Plan: `plans/[PLAN]_multi_env_dgx_mcp_bundle.md`
