---
type: glossary
domain: SYS
summary: 定义 mj-agent 文档中"上游业务系统 / Upstream Business Warehouse"中性术语；与代码层 literal `mj-system-backend-network` 等的边界
owner: 项目负责人
created: 2026-05-11
updated: 2026-05-18
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

## 如何引用上游业务系统（mj-system）

> 本段定义 mj-agent active 文档**唯一允许**含 mj-system inline URL 的位置（per [[../adr/[ADR]_019_Archive_Naming_Convention|ADR-019]] archive 例外 + 本段元文档例外）。其他 active 文档应通过 wikilink 引用本段，不要 inline URL。

### 仓库定位

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/MJ-AgentLab/mj-system` |
| 团队边界 | MJ-AgentLab；与 mj-agent 同团队，team member 默认 read 权限，无访问障碍 |
| 主分支 | `main`（稳定 / 已发布）+ `develop`（active 主线）|

### Branch / Ref 选择规则

mj-agent active 文档若需引用 mj-system 具体内容，按场景选择 ref：

| 场景 | 推荐 ref | 示例用途 |
|---|---|---|
| 历史 attribution（frozen 状态快照）| **commit SHA**（immutable；首选）| ADR / POSTMORTEM 中"本设计 derived from upstream @ commit `abc1234` §X.Y" |
| 当前最佳实践参照 / 持续追踪 | `develop`（active 主线）| "对照上游 develop 当前实现，未来引入" |
| 已发布稳定版本对照 | `main` 或 release tag | "本规范对齐上游 v5.2 release" |
| 仅概念 / 术语（不指 specific file 或行）| **不放 URL** | 用本术语 prose（"上游业务系统"）即可 |

> **首选 SHA-pin**：mj-agent active 文档若一定要 inline URL，**推荐 SHA-pin** —— `develop` / `main` 都会随时间漂移，旧 ADR 中的 URL 会失效或语义偏离。

### 跨仓引用的最小化原则

mj-agent 大多数 active 文档**不需要** inline mj-system URL —— body 应自洽（决策推导独立可读）。如确需 attribution，wikilink 到本 glossary 段 + 一句话内联描述即可：

```markdown
本设计的 directory-scan 思路与上游业务系统脚本工具的常见模式一致
（详见 [[../glossary/upstream_business_warehouse|glossary §如何引用上游业务系统]]）。
```

### 例外（允许 inline URL 的位置）

- 本 glossary 段（唯一合法 active inline URL 持有者；元文档边界）
- `docs/archive/adr/[DEPRECATED]_*.md`：per ADR-019 frozen snapshot，既有 URL 不动
- 代码层 fenced code block 中的 literal（罕见；如展示外部脚本片段对照）

### Forward guard

`scripts/check_no_cross_repo_refs.py` 在 `SKIP_FILES` 已豁免本 glossary 文件路径（warning-mode 期间不会自我命中本段 URL；strict-mode 切换后行为不变）。

### 跨项目文档治理结构借鉴 attribution（2026-05-18）

mj-agent 部分文档治理**结构与判定模式**借鉴 mj-system 项目同名文档（仓库见上文 §仓库定位）。借鉴边界**严格限制为结构、章节切分、表格密度、判定模式**——所有内容（具名文件清单、术语条目、命令、栈细节、申请方式措辞）均按 mj-agent 自身资产派生（`pyproject.toml` / `CLAUDE.md` / `src/mj_agent/` 结构 / `plans/[PLAN]_g1_g2_workflow_enforcement.md` / `config/README.md` 等）。

| mj-agent 落地物 | 借鉴 mj-system 文档 | 借鉴维度（仅结构与写法） |
|---|---|---|
| `README.md`（PR #171） | `README.md` 8 段结构 | 技术栈表 + 前置条件表 + 文档导航 + 常见问题速查 |
| `docs/guide/[GUIDE]_Quick_Start_Setup.md`（PR #171 新建） | `docs/guide/[GUIDE]_Quick_Start_Setup.md` | 9 步编号 + 速查表 + Troubleshooting 表 |
| `docs/guide/[GUIDE]_Developer_Onboarding.md`（PR #172 4 处增强） | `docs/guide/[GUIDE]_Developer_Onboarding.md` | 权限申请清单 + ASCII 代码仓库导航 + Quick Checklist |
| `docs/rule/[STANDARD]_GitHub_Markdown.md` §14（本 PR 新加） | `[STANDARD]_Documentation_Management_Framework.md` §3.1 | 项目根特殊文件清单 + 例外条款写法 |
| `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` §2.6（本 PR 新加） | 同上 §3.1 | 5 文件具名职责表 + 治理例外条款 |
| `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` §6.4（本 PR 显式展开） | 同上 §6.4 + §7.1 A6 | 3 类 allowlist + A6 PR gate；mj-agent 加第 4 类「runtime 语义」（LLM provider + Data boundary + HITL gates）为 mj-agent 特化 |
| `CONTRIBUTING.md`（PR-D 待新建） | `CONTRIBUTING.md` 8 段 + 「摘要+跳转」模式 | 段结构 + 顶部边界声明「环境已就绪 / 准备提交 PR」 |
| `GLOSSARY.md`（PR-D 待新建） | `GLOSSARY.md` A-W 字母分段 + 二字段格式 | 字母分段 + 「定义 + 相关术语」二字段 + 边界声明「不作通用百科解释」 |

**禁止的复制行为**（per [[../../CLAUDE|CLAUDE.md]] L269-278「跨项目借鉴边界」段）：

- 不引入 mj-system 特有的栈细节（如 Java / Spring / Maven / Flyway）—— mj-agent 是 Python 3.13 + uv + LangChain
- 不引入 mj-system 特有的 frontmatter 字段（如 `revision:`）—— mj-agent 用 `updated:` 字段
- 不照搬段数（如 INTAKE 按 `.claude/skills/mj-agent-flow-intake/SKILL.md` §Output Format 7 段而非 mj-system 11 段）
- 不引用 mj-system inline URL（per 本 glossary §如何引用上游业务系统 + §例外）

## 关联文档

- [[../adr/[ADR]_006_Fail_Safe_Reads|ADR-006 Fail-Safe Reads]]（4 层 guardrail；本术语在 L1-L4 层均有出现）
- [[../adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009 Biz Domain as Primary Data Source]]（biz 域 only / 不访问 ODS/DWD）
- [[../adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]]（co-deployment 边界）
- `CLAUDE.md` "Data boundary" 段
