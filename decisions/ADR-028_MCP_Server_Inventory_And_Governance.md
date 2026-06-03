---
type: adr
domain: WORKFLOW
summary: 引入 .mcp.json 13 servers + 新建 docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md（领域专属 STANDARD placement）+ A14 PR gate 实施细则；独立 secrets pipeline 保留
owner: 项目负责人
created: 2026-05-11
updated: 2026-05-11
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - mcp
  - claude-code
  - governance
  - infrastructure
---

# ADR-028: MCP Server Inventory + Governance STANDARD

> **历史**：本 ADR 与 [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]] / [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] 由历史 ADR-025 拆分而来（ADR-025 已 archive）。本 ADR 聚焦 MCP servers 与 governance STANDARD 一题。

## Context

CLAUDE.md §A14 引用 `[STANDARD]_MJ_Agent_MCP_Server_Governance` 但 STANDARD **不存在**（dangling reference）；仓库根**无 `.mcp.json`** — Claude Code 内开发者：

- 无法直连 mj-agent-memory 调试 langgraph_checkpoints 表
- 无法 SSH 到 DGX-Spark 维护 LLM serving 容器（per [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] DGX 算力节点）
- 无 GitHub MCP / 无 code semantic search MCP

项目负责人 2026-05-09 决策：完整对标行业成熟 .mcp.json 模式，引入 13 servers + 落地 governance STANDARD。

## Decision

### D.1 `.mcp.json` 13 servers inventory

| # | Server name | Trust posture | Credential mode | 用途 |
|---|---|---|---|---|
| 1 | `github` | first-party (`@modelcontextprotocol/server-github`) | API key (`${GITHUB_PERSONAL_ACCESS_TOKEN}`) | GitHub issue / PR 操作 |
| 2 | `serena` | third-party (oraios) | none | 代码语义索引 |
| 3-7 | `pg-mj-agent-memory-{dev,test-lan,test-wan,prod-lan,prod-wan}` (5) | third-party (`@modelcontextprotocol/server-postgres`) + wrapped | wrapped script (URL 含 `${MJ_AGENT_PG_MEMORY_*_URL:-default}`) | langgraph checkpointer DB 查询 |
| 8-12 | `pg-mj-system-biz-{dev,test-lan,test-wan,prod-lan,prod-wan}` (5；保留原 server 命名 literal) | third-party (`@modelcontextprotocol/server-postgres`) + wrapped | wrapped script (URL 含 `${MJ_AGENT_PG_BIZ_*_URL:-default}` + analyst RO role) | 上游业务系统 biz pg 数据探查（biz_dws / biz_dwd allowlist；ADR-006/009 数据边界由 DB-side GRANT 兜底）|
| 13 | `ssh-manager` | third-party (`@iflow-mcp/mcp-ssh-manager`) | API key (5 个 `${MJ_AGENT_SSH_SERVER_*_PASSWORD}`；9 SSH targets：cloud + 4 hosts × 2 lan/wan) | SSH 5 主机运维（cloud / runner / test / prod / **DGX-Spark**） |

**省略**：n8n-docs（mj-agent 无 n8n 集成）。

### D.2 STANDARD placement：领域专属 → `docs/infrastructure/mcp/`

新建 [[../infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance|STANDARD MCP Server Governance v1.0]]，路径 `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`（与 git/cicd 子目录平行；filename 无 `_v1.0` 后缀 per active path stability 原则）。

STANDARD 提供：

- **Trust posture 3 等级矩阵**：first-party / third-party / community + 降级规则
- **Credential mode 5 类**：none / OAuth / API key (env var) / wrapped script (env var via cmd) / template var
- **PR-body 强制声明模板**（A14 实施细则）
- **季度 audit cadence**：trust posture 重评 + credential 安全检查 + wrapper script 漂移检测 vs 内部 baseline
- **Cross-references** 至 ADR-008（独立 secrets pipeline）/ ADR-013（SKILL schema）/ Meta v2.2 §3.7（STANDARD placement）

### D.3 Independent secrets pipeline

所有 `MJ_AGENT_*` 命名空间 env vars 由 mj-agent 自己的 secrets pipeline 注入；与上游业务系统 `MJ_SYS_*` env var 命名空间隔离（per [[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]]）。

**注入路径自 [[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]] 起升级为 2-bundle 拆分**：app secrets 走 `config/secrets.enc → scripts/setup-env.ps1 → .env`；MCP secrets 走 `config/secrets-mcp.enc → .claude/scripts/setup-mcp-secrets.ps1 → HKCU\Environment`（**不入 .env**）。原 `.claude/scripts/setup-mcp-env.ps1`（mirror .env → OS env）已废弃删除。

### D.4 Wrapper script + 内部 baseline

`.claude/scripts/pg-server-{start.cmd,wrapper.mjs}` 作为 pg MCP wrapper（修复第三方 `@modelcontextprotocol/server-postgres` 的 timestamp 列 JS Date 转换问题：`pg.types.setTypeParser(1114/1184, val => val)` overrides）。

内容快照保存为 `docs/_baselines/pg_server_baseline.md`，作为季度 audit 的漂移基准。

## Consequences

### 正面

- **A14 PR gate 正式生效**：之前 dangling reference 关闭；MCP server 增删必走 STANDARD §4 declaration template
- **Claude Code 内运维就近**：13 MCP servers 让分析师 / 运维直接在 Claude Code 内查 mj-agent-memory + 上游 biz pg + SSH 5 主机（含 DGX）
- **领域专属 STANDARD placement**：MCP 是 Claude Code 工具集成领域，落 `docs/infrastructure/mcp/` 而非 `docs/rule/`，与 git/cicd 平行
- **季度 audit cadence**：不积累 trust posture 漂移；wrapper script 漂移检测有内部 baseline 兜底

### 负面

- **secrets 管理负担**：5 个 SSH passwords + 4 WAN postgres URLs = 9 个新 env var；onboard 开发者必须跑 `setup-env.ps1` + `setup-mcp-env.ps1` 两步
- **OS-env 安全代价**：`HKCU\Environment` 明文持久化；用户已接受 trade-off（详见 `config/README.md` §6.4）
- **Wrapper script 维护**：`pg-server-{start.cmd,wrapper.mjs}` 需季度 audit 防漂移；Phase D+ 评估是否升 PR-time CI 阻塞
- **4 WAN MCP servers 暂不可连**：`secrets.conf` §6 字面值为空；FRP 路由 + 真实远程 pg 凭据填入是 follow-up

### 暂未实现（out-of-scope）

- **Auto-inject OS env**：手动跑 `setup-mcp-env.ps1` 是设计意图（`secret rotation 后必跑`）
- **Profile / IDE 启动 claude 配置**：个人 dev environment 范畴；OS-level 持久化后所有入口都自动可见

## Alternatives considered

- **A. STANDARD 落 `docs/rule/`（全局规则）**：拒绝。MCP 是领域专属（Claude Code 工具集成），per Code_Side §3.7 placement 决策矩阵应落 `docs/infrastructure/mcp/`
- **B. 不引入 wrapper script，直接用第三方 server 默认行为**：拒绝。timestamp 列 UTC "Z" 转换会导致与 DB 原始字符串不匹配，影响数据探查正确性
- **C. SSH MCP 不引入，用本地 `ssh` CLI**：拒绝。Claude Code 内 SSH 是运维高频操作；MCP 提供的结构化输出对 Claude 推理更友好
- **D. 把所有 13 servers 拆成单独 ADR**：拒绝。13 servers 是同一治理模型实例化，单 ADR + STANDARD §5 inventory 表是合理颗粒度

## References

- [[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] — 独立 secrets pipeline；`MJ_AGENT_*` 命名空间隔离
- [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] — 与 SKILL governance 互补：本 ADR 治 `.mcp.json`，ADR-013 治 `.claude/skills/`
- [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]] §A14 — PR gate 来源
- [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]] / [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] — ADR-025 拆分姊妹
- [[decisions/ADR-030_Secrets_Bundle_Split_For_MCP_Isolation|ADR-030]] — 本 ADR §D.3 secrets pipeline 升级；2-bundle 拆分把 MCP secrets 从 `secrets.enc` 析出
- [[../infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance|STANDARD MCP Server Governance]] v1.0 — 本 ADR 落地的实施细则
- [[archive/decisions/superseded/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction|ADR-025（archive）]] — 历史 bundle ADR
- `.mcp.json` — 13 servers 实文件
- `.claude/scripts/{pg-server-start.cmd,pg-server-wrapper.mjs,setup-mcp-env.ps1}` — wrapper + env sync 脚本
- `docs/_baselines/pg_server_baseline.md` — wrapper 内部 baseline（季度 audit 漂移基准）
- 实施 PR：[#103](https://github.com/MJ-AgentLab/mj-agent/pull/103)（PR-3 of original ADR-025 4-PR sequence）
