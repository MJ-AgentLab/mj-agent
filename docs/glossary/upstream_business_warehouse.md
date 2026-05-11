---
type: glossary
domain: SYS
summary: 定义 mj-agent 文档中"上游业务系统 / Upstream Business Warehouse"中性术语；与代码层 literal `mj-system-backend-network` 等的边界
owner: 项目负责人
created: 2026-05-11
updated: 2026-05-11
state: active
track: shared
---

# 术语：上游业务系统 / Upstream Business Warehouse

## 定义

mj-agent 通过 `analyst` 只读 PostgreSQL 角色访问的 **外部业务数据仓库**。
mj-agent 仅作为 **read-only 消费者**（per [[../adr/[ADR]_006_Fail_Safe_Reads|ADR-006]] + [[../adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]]），无 schema 演进权。

## 何时用本术语

文档（`docs/**/*.md` + `CLAUDE.md` + `INDEX.md`）的 **prose 叙述** 中描述外部业务库时统一用 **"上游业务系统"**（中文）或 **"Upstream Business Warehouse"**（英文）。这是 PR-118 cross-repo decoupling 决策（D2）后采用的中性措辞。

**典型场景**：
- ADR/SPEC Context 段描述 mj-agent 的数据来源
- HITL_Prompt 必停规则（§3.1）解释 schema migration 触发场景
- README / Onboarding GUIDE 介绍系统边界

## 何时**不**用本术语

下列场景保留代码层 / 部署层 literal，**不要替换**为本中性术语：

| 场景 | literal | 理由 |
|---|---|---|
| Docker network 名 | `mj-system-backend-network` | 真实 network 标识；`docker network ls` / compose `external: true` 引用必须精确 |
| pg URL env var | `MJ_AGENT_PG_BIZ_*` | 真实环境变量名；脚本 / `.env` / `.env.example` 引用必须精确 |
| `.mcp.json` server 配置 | `mj-system-pg` 等 server 名 | MCP server 实例标识 |
| `infra/docker/docker-compose*.yml` | network bridge / volume / service literal | YAML 字面值不可改写 |
| `scripts/*.{py,ps1}` | 字符串常量、注释中的 literal | 代码层精确引用 |
| CHANGELOG.md 历史条目 | 既有引用 | per Keep-a-Changelog 不可改写历史 |
| `docs/archive/**` | 既有引用 | per [[../adr/[ADR]_019_Archive_Naming_Convention|ADR-019]] frozen snapshot |

## 等价表达备选

为避免行文重复，下列等价表达可在同一文档内交替使用（**保持单文档内一致**）：

- **首选**：上游业务系统 / Upstream Business Warehouse
- 备选 1：业务域上游 / biz domain upstream
- 备选 2：only-read 业务库 / read-only biz pg

## 关联文档

- [[../adr/[ADR]_006_Fail_Safe_Reads|ADR-006 Fail-Safe Reads]]（4 层 guardrail；本术语在 L1-L4 层均有出现）
- [[../adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009 Biz Domain as Primary Data Source]]（biz 域 only / 不访问 ODS/DWD）
- [[../adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]]（co-deployment 边界）
- `CLAUDE.md` "Data boundary" 段
