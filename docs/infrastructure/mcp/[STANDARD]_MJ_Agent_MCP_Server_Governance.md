---
type: standard
domain: WORKFLOW
summary: mj-agent .mcp.json MCP server 治理规范 — trust posture 分级、credential mode 矩阵、PR-body 强制声明模板、initial 13-server inventory、季度 audit cadence；填补 CLAUDE.md §A14 dangling reference
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: engineering-workflow
version: v1.0
tags:
  - standard
  - mcp
  - governance
  - claude-code
  - engineering-workflow
---

# mj-agent MCP Server 治理规范 v1.0

> **所属目录**：`docs/infrastructure/mcp/`（**领域专属**落点 per [[../../adr/[ADR]_022_P2_Framework_Enhancements|ADR-022]] C.3.2 + Meta v2.2 §3.7；与 `docs/infrastructure/git/` / `docs/infrastructure/cicd/` 平行）
> **状态**：`state: active`（PR-3 of multi-env+DGX+MCP bundle 落地）
> **填补**：CLAUDE.md §Engineering-Workflow Documentation §A14 行原引用 `[STANDARD]_MJ_Agent_MCP_Server_Governance` 但文件不存在（dangling reference）；本 STANDARD 落地后 A14 约束正式生效

## §1 范围

本 STANDARD 治理 mj-agent 仓库根 `.mcp.json` 中所有 MCP server entry 的：

- **trust posture**（信任分级）：first-party / third-party / community
- **credential mode**（凭证模式）：none / OAuth / API key (env var) / wrapped script (env var via cmd) / template var
- **PR-body 强制声明模板**（A14 PR gate）：每次 `.mcp.json` 增删 / credential 模式变更必走
- **server inventory**：当前 13 个 server 的分类 + 凭证状态
- **audit cadence**：增删按 PR 触发；不变集季度 review

**不在本 STANDARD 范围**：
- `.claude/skills/` SKILL governance（治理在 [[../../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] + [[../../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] + Meta v2.2 §3.10）
- `mj-agentlab-marketplace` plugins MCP（治理在 marketplace 仓）
- `.claude/settings.json` permissions allowlist（治理在 §A13 + 未来 `[STANDARD]_..._Claude_Code_Settings`）
- 上游业务系统仓的 `.mcp.json`（独立 secrets pipeline per ADR-008；mj-agent 不审上游 MCP）

## §2 Trust posture 分级

| 等级 | 定义 | 示例 | 审核要求 |
|---|---|---|---|
| **first-party** | Anthropic / Microsoft / GitHub 官方维护 | github (`@modelcontextprotocol/server-github`) | 信任度高；版本升级 PR-body 简单声明即可 |
| **third-party** | 知名组织 / 开源社区维护，有持续投入 | serena (oraios) / pg (`@modelcontextprotocol/server-postgres`) / ssh-manager (`@iflow-mcp`) | PR-body 声明上游仓库 URL + maintenance status |
| **community** | 个人维护 / 实验性 / 无明确组织背书 | （当前无）| PR-body 声明 review of latest 3 commits + last-commit date；强烈建议 wrap in `.claude/scripts/` 兜底 |

**降级规则**：third-party server 如出现 maintainer 失联（90 天无 commit）/ security issue 未响应（30 天）→ 降为 community；触发 PR review。

## §3 Credential mode 矩阵

| 模式 | 描述 | 安全特性 | 适用场景 |
|---|---|---|---|
| **none** | 无凭证 | 公开服务（如 HTTP MCP） | 文档/参考类 server |
| **OAuth** | 浏览器 OAuth flow 注入 token | 用户控制；token 不入 .mcp.json / .env | Google / GitHub OAuth |
| **API key (env var)** | `${VAR}` 模板从 env 注入 | 凭证不入 .mcp.json；user 必须 set env 或 `.env` | github (`${GITHUB_PERSONAL_ACCESS_TOKEN}`) / ssh-manager 密码 |
| **wrapped script (env var via cmd)** | `cmd /c <wrapper.cmd> <URL>` + URL 含 `${VAR}` 默认值 | wrapper 可加 timestamp 修复 / 缓存修复等 client-side patch | pg-mj-agent-memory-* / pg-mj-system-biz-* |
| **template var** | URL 含 `${VAR}` 形式直接传入 | 与 API key 等价 | （当前 .mcp.json 通过 wrapped script 包装；未直接使用此模式）|

**禁止**：
- ❌ 凭证（密码 / token / 连接串明文）直接写入 `.mcp.json`
- ❌ `.mcp.json` 中含真实 IP 但凭证在 unprotected 文件
- ❌ wrapper script 含 hard-coded credential

**强制**：
- 所有 ${VAR} 模板的 env var **必须**在 `.env.example` 中声明 placeholder（即使值为空），让 onboard 开发者知晓需要哪些 secret。

## §4 PR-body 强制声明模板（A14 PR gate）

任何修改 `.mcp.json` 的 PR，body 中**必须**包含如下表格段（缺则 reviewer 阻塞合并）：

```markdown
## MCP Server Governance Declaration（A14 / STANDARD §4）

### 增删 / 修改的 server entries

| Action | Server name | Trust posture | Credential mode | Justification |
|---|---|---|---|---|
| ADD / MODIFY / REMOVE | `<name>` | first-party / third-party / community | none / OAuth / API key / wrapped script | 1-sentence reason |

### Trust posture 变化

- 任何 server 从 third-party → community 降级 → 关联 issue / 升级措施
- 任何新 community-tier server → 上游 URL + last-commit date + 3-commit review summary

### Credential 安全审查

- [ ] 无明文凭证写入 `.mcp.json`
- [ ] ${VAR} placeholder 已添加到 `.env.example`
- [ ] wrapper script（如有）已 Read 验证无 hard-coded credential
```

## §5 Initial Server Inventory（v1.0；2026-05-09 PR-3 落地）

13 个 server entries（mj-agent `.mcp.json`）：

| # | Server name | Trust posture | Credential mode | 用途 |
|---|---|---|---|---|
| 1 | `github` | first-party (`@modelcontextprotocol/server-github`) | API key (`${GITHUB_PERSONAL_ACCESS_TOKEN}`) | GitHub issue / PR 操作 |
| 2 | `serena` | third-party (oraios) | none | 代码语义索引 |
| 3-7 | `pg-mj-agent-memory-{dev,test-lan,test-wan,prod-lan,prod-wan}` (5) | third-party (`@modelcontextprotocol/server-postgres`) + wrapped (mj-agent `.claude/scripts/pg-server-*`) | wrapped script (URL 含 `${MJ_AGENT_PG_MEMORY_*_URL:-default}`) | langgraph checkpointer DB 查询（mj_agent_memory） |
| 8-12 | `pg-mj-system-biz-{dev,test-lan,test-wan,prod-lan,prod-wan}` (5；保留原 server 命名 literal) | third-party (`@modelcontextprotocol/server-postgres`) + wrapped | wrapped script (URL 含 `${MJ_AGENT_PG_BIZ_*_URL:-default}` + analyst RO role) | 上游业务系统 biz pg 数据探查（biz_dws / biz_dwd allowlist；ADR-006/009 数据边界由 DB-side GRANT 兜底）|
| 13 | `ssh-manager` | third-party (`@iflow-mcp/mcp-ssh-manager`) | API key (5 个 `${MJ_AGENT_SSH_SERVER_*_PASSWORD}`；9 SSH targets：cloud + 4 hosts × 2 lan/wan) | SSH 5 主机运维（cloud / runner / test / prod / **DGX-Spark**） |

**省略**：n8n-docs（mj-agent 无 n8n 集成，不需要）。

**Wrapped script 来源**：`.claude/scripts/pg-server-{start.cmd,wrapper.mjs}` 内容快照保存为 `docs/_baselines/pg_server_baseline.md`（Phase Γ 落地；当前为 placeholder）。理由：第三方 `@modelcontextprotocol/server-postgres` 默认对 timestamp 列做 JS Date 转换，导致 SELECT 返 UTC "Z" 字符串而非数据库原始字符串；wrapper 通过 `pg.types.setTypeParser(1114/1184, val => val)` overrides 修复。季度 audit 比对 baseline 检测漂移（见 §6）。

**Independent secrets pipeline**：所有 `MJ_AGENT_*` 命名空间 env vars 由 mj-agent 自己的 `scripts/setup-env.ps1` + `config/secrets.enc` 注入，**与上游业务系统 `MJ_SYS_*` env var 命名空间隔离**（保留 `MJ_SYS_*` 作上游 env var literal；per ADR-008）。

## §6 Audit cadence

| 触发 | Action | Reviewer |
|---|---|---|
| `.mcp.json` 增 / 删 server | PR-time §4 declaration table 必填 | Tooling Reviewer + SWE |
| `.mcp.json` 修改 server credential mode | PR-time §4 declaration table 必填 | Tooling Reviewer + SWE + Security （如 mode 变化降级）|
| `.claude/scripts/pg-server-*` 修改 | PR-time 声明（diff vs `docs/_baselines/pg_server_baseline.md` 内部基线快照） | SWE |
| **季度 audit**（每年 4 次） | (1) 重新评估每个 server trust posture（第三方 maintainer 是否仍活跃 / 90 天 commit）；(2) 比对 `.claude/scripts/pg-server-*` 与 `docs/_baselines/pg_server_baseline.md` 内部基线是否漂移；(3) verify 所有 ${VAR} 在 `.env.example` 声明；(4) verify 无明文凭证；(5) 必要时 bump version (v1.0 → v1.1) | Tooling Reviewer |
| 上游 maintainer 失联 / security issue | 触发降级评估 → community tier；触发 PR review | Tooling Reviewer + Security |

季度 audit 输出落 `docs/assessments/[ASSESSMENT]_MCP_Server_Audit_<YYYY-Q>.md`（首次 audit 在 2026-Q3）。

## §7 Cross-references

- [[../../adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] — 独立 secrets pipeline；`MJ_AGENT_*` 命名空间隔离上游 `MJ_SYS_*`（env var literal）
- [[../../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] — `.claude/skills/` SKILL governance（与本 STANDARD 互补；本 STANDARD 治理 `.mcp.json`，ADR-013 治理 `.claude/skills/`）
- [[../../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §A14 — PR gate 来源
- [[../../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] — `.claude/` 边界
- [[../../adr/[ADR]_018_Active_Path_Stability|ADR-018]] — 本 STANDARD 文件名无 `_v1.0` 后缀依据
- [[../../adr/[ADR]_022_P2_Framework_Enhancements|ADR-022]] §C.3.2 — 领域专属 STANDARD placement 决策（本文件落 `docs/infrastructure/mcp/` 而非 `docs/rule/`）
- ADR-025（PR-4 落地；Multi-environment + LLM provider abstraction） — 跨 4 PR 的整体决策记录
- [[../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.7（STANDARD placement）+ §3.10（in-tree workflow SKILL governance；与本 STANDARD 平行）+ §7.7（A12-A14 PR gates）
- `docs/_baselines/pg_server_baseline.md`（Phase Γ 落地；wrapper script 内部快照；季度 audit 漂移基准）
- CLAUDE.md §Engineering-Workflow Documentation §A14（本 STANDARD 是 A14 的实施细则）

## §8 演进

- v1.0（2026-05-09，本文件）— Initial inventory（13 servers）；A14 约束正式生效
- 后续 minor bump 触发条件（per ADR-022 §C.3.6 拆分阈值）：trust posture 降级条件细化 / credential mode 新增类目 / inventory > 25 servers 且 trust 分级混杂
- major bump（v2.0）触发条件：MCP protocol 重大演进（如远程 HTTP MCP 成主流，需 §3 重写） / Claude Code 治理框架重大调整
