---
type: adr
domain: OPS
summary: 把 MCP 基础设施 secrets（5 SSH + 10 PG URL）从 config/secrets.enc 拆出到独立的 config/secrets-mcp.enc，解密后直接写 OS env，永不入 .env；对齐 mj-system v2.3 secrets-sys-ops.enc 范式
owner: 项目负责人
created: 2026-05-12
updated: 2026-05-12
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - secrets
  - mcp
  - governance
  - infrastructure
---

# ADR-030: Secrets Bundle Split for MCP Isolation

## Context

### 当前状态（PR #158 / PR #159 后）

`mj-agent` 当前用**单一** `config/secrets.enc` 加密包装载全部 secrets：

| 来源 | 类目 | KEYs |
|---|---|---|
| 应用层 | analyst pg / memory pg / ARK LLM / LangSmith | ~6-8 |
| 基础设施层（MCP） | 5 个 `MJ_AGENT_SSH_SERVER_*_PASSWORD` | 5 |
| 基础设施层（MCP） | 10 个 `MJ_AGENT_PG_{MEMORY,BIZ}_*_URL` | 10 |

注入路径 = `secrets.enc → setup-env.ps1 → .env → setup-mcp-env.ps1 → OS env`。15 个 MCP secrets 在中途**经过 `.env` 磁盘明文**才能到达 OS env 给 Claude Code 主进程读 `.mcp.json` `${VAR}` 用。

### mj-system 范式（v2.3 SPEC `[SPEC]_SYS_Secrets_Encryption_And_Setup_Automation`）

mj-system 早已分了三份独立 `.enc`：

| 文件 | 类目 | KEYs | 注入路径 |
|---|---|---|---|
| `config/secrets.enc` | 应用 secrets | 11 | `→ setup-env.ps1 → .env`（Python 应用读）|
| `config/secrets-sys-git.enc` | GitHub PAT | 1 | `→ setup-sys-git-env.ps1 → HKCU\Environment`（**不入 .env**）|
| `config/secrets-sys-ops.enc` | 5 SSH + 5 PG URL | 10 | `→ setup-sys-ops-env.ps1 → HKCU\Environment`（**不入 .env**）|

mj-system 的 MCP secrets 不经 `.env` 中转，直接进 OS env。

### 触发事件链

| 时点 | 事件 |
|---|---|
| 2026-05-12 | 用户报 `mj-agent check` 报"memory DB unreachable" |
| 2026-05-12 | 分析揭示三个独立 root cause：`MJ_AGENT_MEMORY_PORT` 默认 5432 vs storage-stack 5433（PR #158 修） + compose CLI 缺 `--env-file .env`（PR #155 已修） + **MCP secrets 与 app secrets 混在一个 .enc**（本 ADR 修） |
| 2026-05-12 | 用户提出"对齐 mj-system 注入范式"诉求 |
| 2026-05-12 | 评估并采纳"方案 B 部分对齐"（详见 Decision）|

### 业务零影响硬约束

`grep MJ_AGENT_SSH_ src/ tests/` → 0 命中。`grep MJ_AGENT_PG_.*_URL src/ tests/` → 0 命中。15 个 MCP secrets 只在 `.mcp.json` 里以 `${VAR}` 占位符出现，由 Claude Code 主进程从 OS env 解析，**业务代码完全不读**。这是本 ADR 推进的硬前提。

## Decision

### D.1 Secrets bundle 二分

新增 `config/secrets-mcp.enc`：

| 文件 | 类目 | KEYs | 来源章节 |
|---|---|---|---|
| `config/secrets.enc`（保留，体积缩减）| 应用 secrets | ~6-8 | secrets.example §1–§4 |
| `config/secrets-mcp.enc`（新）| 5 SSH + 10 PG URL | 15 | secrets-mcp.example §1+§2 |

两个 bundle **共享同一团队口令**（不为口令隔离，仅为信任边界 + 注入路径隔离）。

### D.2 注入路径

| Bundle | 解密脚本 | 目标 | 副作用 |
|---|---|---|---|
| `secrets.enc` | `scripts/setup-env.ps1`（已存在；行为不变）| `.env` 文件 | Python 应用、docker compose 通过 `.env` 消费 |
| `secrets-mcp.enc` | `.claude/scripts/setup-mcp-secrets.ps1`（新）| `HKCU\Environment`（OS User-level env）| **不写 `.env`**；Claude Code 主进程启动时读 OS env 解析 `.mcp.json` `${VAR}` |

### D.3 setup-mcp-env.ps1 删除

旧的 `.claude/scripts/setup-mcp-env.ps1`（read `.env` → mirror to OS env）在拆分后**完全没事可做**——`.mcp.json` 16 个 `${VAR}` 全是 secrets（15 个 mj-agent MCP + 1 个 `GITHUB_PERSONAL_ACCESS_TOKEN`），新 `setup-mcp-secrets.ps1` 直接覆盖 15 个，剩下 1 个 GitHub PAT 由外部提供（不在 mj-agent secrets pipeline 范围）。

**删除** `setup-mcp-env.ps1`，所有引用路径迁移到 `setup-mcp-secrets.ps1`。

### D.4 一次性迁移脚本

新增 `scripts/migrate-secrets-bundle-split.ps1`：team admin 一次性运行，解密旧 secrets.enc，按 D.1 表格拆分 keys，重加密生成新的 `secrets.enc` + `secrets-mcp.enc`。运行后两个 `.enc` 提交进仓，团队成员拉取后跑 `setup-env.ps1` + `setup-mcp-secrets.ps1` 即可。

### D.5 反向不对齐项（显式保留 mj-agent 现有选择）

| mj-system 选择 | mj-agent 保留 | 原因 |
|---|---|---|
| `python-dotenv` + `os.getenv` 散落 | `pydantic-settings` 集中 `Settings` 类 | mj-agent 演进先行，不退化 |
| compose `environment: ${VAR}` 隐式注入 | compose `env_file: ../../.env` 显式注入 | 显式更利于"compose 在 `infra/docker/` 子目录"场景的可读性 |
| 3 份独立 `.enc`（app + git + ops）| 2 份独立 `.enc`（app + MCP）| mj-agent 无 `mj-sys-git` 风格的独立 GitHub workflow secret；GitHub PAT 借用外部 OS env，不入 mj-agent 治理域 |

## Consequences

### 正面

- **信任边界对齐 mj-system v2.3 SPEC**：MCP infrastructure secrets（SSH root 密码、远程 PG URL）与 app secrets（ARK API key、analyst RO 密码）物理隔离；丢失一类不波及另一类的轮换/回收。
- **MCP secrets 永不入磁盘明文 `.env`**：减少一处明文落地点。`.env` 仅保留应用必需的 6-8 个 secrets。
- **`.env` 体积下降 ~95 行**：从 ~235 行降到 ~140 行；更聚焦应用配置。
- **Onboarding 双轨独立**：MCP-only 开发者（如运维）可只跑 `setup-mcp-secrets.ps1` 而无需配 `ARK_API_KEY`；分析师可只跑 `setup-env.ps1` 而无需 MCP secrets。
- **业务零影响**：业务代码不读 MCP secrets；pydantic-settings / compose / Python runtime 路径完全不变。

### 负面

- **+1 个 onboarding 步骤**：新开发者从"跑 setup-env.ps1 + setup-mcp-env.ps1"变成"跑 setup-env.ps1 + setup-mcp-secrets.ps1"（步数不变，但脚本名换了；config/README.md / SKILL / CLAUDE.md 已同步）。
- **多一个 `.enc` 文件**：team admin 维护 2 份加密包；轮换 secret 时需重加密对应那份。
- **一次性迁移成本**：team admin 跑 `migrate-secrets-bundle-split.ps1` 一次；commit 两份新 `.enc`；通知团队 pull + re-run 两个 setup 脚本。

### 中性

- 共享团队口令：两份 `.enc` 用同一口令。理论上未来可演进为独立口令（更高隔离），但当前简化口令管理。
- `migrate-secrets-bundle-split.ps1` 是一次性工具：跑过一次后可在 follow-up cleanup PR 中删除（保留至少 1 个 minor version 让未及时迁移的 fork 也能用）。

## Alternatives considered

### A. 仅文档对齐（不动 .enc / 脚本结构）

写一份 SPEC 把现状正式化，cross-ref mj-system 范式说明"为什么不拆"。**拒绝**：(1) 没解决 MCP secrets 入磁盘明文的问题；(2) 信任边界仍混；(3) 文档化"反范式"会变成技术债。

### C. 完全对齐（含 pydantic-settings 退化 + compose 隐式注入）

镜像 mj-system 的所有差异。**拒绝**：(1) pydantic-settings 是 mj-agent 在 Python 配置加载上**领先 mj-system 一代**的演进，不应退回 `python-dotenv` + `os.getenv` 散落；(2) compose `env_file` 显式注入对"compose 在子目录"的可读性更好（已被 PR #155 文档化）。

### D. 三份独立 `.enc`（app + llm + mcp）

把 ARK + LangSmith 也拆成独立 `secrets-llm.enc`。**拒绝**：(1) LLM key 是应用核心依赖，与 analyst pg 同生命周期，无需拆分；(2) mj-system 也没拆出 LLM key；(3) 增加复杂度无收益。

### E. 保持现状（1-enc）

**拒绝**：触发事件链已表明 1-enc 的诊断负担（"memory DB unreachable / auth failed" 实际有 3 个独立 root cause；secrets 边界不清晰增加排查成本）。

## References

- [[decisions/ADR-008_Co_Deployment_With_Upstream_Warehouse|ADR-008]] — 独立 compose project + 独立 secrets pipeline 的早期决策；本 ADR 把 secrets pipeline 隔离推进到文件粒度
- [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]] — MCP server inventory + STANDARD MCP_Server_Governance；本 ADR 是 ADR-028 §D.3 "Independent secrets pipeline" 的落地细化
- [[../infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance|STANDARD MCP Server Governance v1.0]] — §3 credential mode "wrapped script (env var via cmd)" 行为不变；本 ADR 改的是注入这些 env 的**机制**（从 .env mirror 改为 .enc direct）
- [[archive/decisions/superseded/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction|ADR-025（archive）]] — PR-3 把 MCP secrets 加入 single secrets.enc 的初始决策；本 ADR 修订其注入路径声明
- [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.9 — 本 ADR 触发 "决策性变更" 条件（secrets 边界重新划分 + 注入路径切换）
- mj-system 参考实现：`D:\workspace\10-software-project\projects\mj-system\develop\.claude\scripts\setup-sys-ops-env.ps1`（蓝本）
- mj-system 治理蓝本：`D:\workspace\10-software-project\projects\mj-system\develop\docs\design\SecretsEncryption\[SPEC]_SYS_Secrets_Encryption_And_Setup_Automation.md` v2.3
- 实施 PR：本 ADR 同 PR 一并 merge（待补 PR 链接）
- 前置 PR：[#158](https://github.com/MJ-AgentLab/agent/pull/158) PORT 修复 + [#159](https://github.com/MJ-AgentLab/mj-agent/pull/159) develop ← main sync
