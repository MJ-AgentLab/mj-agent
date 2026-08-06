---
type: standard
domain: SYS
summary: mj-agent 的 Conventional Commits 规范，定义 type、mj-agent 专属 scope、分支对齐矩阵与示例
owner: 项目负责人
created: 2026-04-25
updated: 2026-08-06
state: active
version: v1.1
track: code
tags:
  - standard
  - commit
  - git
  - conventional-commits
aliases:
  - MJ Agent Commit Message Convention
  - mj-agent Commit Message 规范
---

# mj-agent Commit Message 规范

> **适用范围**：mj-agent 仓库所有 Git 提交的消息格式
> **目标受众**：全部贡献者
> **版本**：v1.0
> **最后更新**：2026-04-25
> **关联文档**：[[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from 上游业务系统]]（决策记录；保留原 ADR 编号 + 文件名以稳定 wikilink，标题中 "上游业务系统" 保留作历史决策语境）、[[capabilities/infrastructure/evidence/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|配套适配评估 v1.0]]

---

## 目录

1. [概述](#1-概述)
2. [格式规范](#2-格式规范)
3. [类型（type）](#3-类型type)
4. [范围（scope）](#4-范围scope)
5. [分支类型与 Commit 类型](#5-分支类型与-commit-类型)
6. [提交拆分指南](#6-提交拆分指南)
7. [示例](#7-示例)
8. [脚注（Footers）](#8-脚注footers)
9. [促活条件](#9-促活条件)
10. [参考资料](#10-参考资料)

---

## 1 概述

本规范定义 mj-agent 仓库 Git commit message 的统一格式，基于 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) 行业标准。

规范化 commit message 的目标：

- **可读性**：贡献者一眼即知变更性质（feat / fix / infra ...）
- **可追溯性**：`git log --grep` 可按类型与子系统筛选
- **自动化友好**：为后续 PR-title 校验与 CHANGELOG 生成（详见 [[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]] §References 中的 `amannn/action-semantic-pull-request` 计划）提供结构化输入
- **跨项目运维一致性**：与上游业务系统的 commit 习惯保持表层相同（同一开发者跨仓切换无需切换语法）；scope 列表针对 mj-agent 模块重建。ADR-008 已确定两项目独立 compose project + 环境矩阵对齐

> [!NOTE]
> mj-agent 自有规则要点（不依赖外部 commit 规范继承）：
> - **scope 列表 mj-agent 原生**：12 项按 `src/mj_agent/` 模块结构定义（§4）；不沿用其它项目 ETL 服务名缩写
> - **分支模型与 type 对齐矩阵**（§5）：5 类临时分支 × 7 类 commit type 闭合矩阵
> - **types 数量**：7 个常用 + `merge` 自动

---

## 2 格式规范

### 2.1 完整格式

```text
<type>(<scope>): <summary>

[可选正文 — 解释变更原因，每行不超过 72 字符]

[可选脚注 — 仅限 §8 列出的标准 git trailers]
```

### 2.2 格式要点

| 规则 | 正确 | 错误 |
|------|------|------|
| `type` 与 `scope` 全部小写 | `feat(skill):` | `Feat(SKILL):` |
| `scope` 用小括号包裹 | `feat(skill):` | `feat[skill]:` |
| `:` 后加一个空格 | `feat(skill): 新增` | `feat(skill):新增` |
| `summary` 不以句号结尾 | `新增 metrics-glossary skill` | `新增 metrics-glossary skill。` |
| 整行（header）不超过 72 字符 | — | 超长摘要 |
| 中英文摘要均可 | `add metrics skill` / `新增 skill` | — |
| `scope` 可省略（仅在真正跨范围时） | `docs: 更新 README` | — |
| 命令式语态，不用过去时 | `add skill` / `新增 skill` | `added skill` / `已新增 skill` |

---

## 3 类型（type）

### 3.1 类型定义

| 类型 | 含义 | 何时使用 |
|------|------|---------|
| `feat` | 新功能 | 新增用户/Agent 可感知的功能或能力（新 skill、新 tool、新 prompt 段落） |
| `fix` | Bug 修复 | 修复已有功能的缺陷（guardrail 漏洞、SQL 转义错误、loader 解析异常） |
| `perf` | 性能优化 | 以性能为目的的变更（缓存、并发、prompt token 压缩） |
| `refactor` | 重构 | 不改变外部行为的代码重组（目的是"更清晰"，不是"修 bug"或"加功能"） |
| `test` | 测试相关 | 新增或修改测试用例（单元、集成、smoke、eval） |
| `docs` | 文档变更 | 仅修改文档文件（`docs/`、`README.md`、`CHANGELOG.md`、in-source `SKILL.md` 与 `prompts/*.md` 的非语义改动） |
| `infra` | 基础设施 | CI/CD、Docker、依赖更新、脚本、`.env.example`、`pyproject.toml` 配置等不影响业务源码的变更 |

> `merge` 用于合并提交（`merge: 合并 develop 最新内容，解决冲突`），由合并操作自动产生，不由开发者手动选择。

### 3.2 类型选择规则

- 一次提交只能有一个 type
- type 描述的是 **本次 commit 的变更性质**，不是整个分支的目的
- 如果一次变更同时包含多种性质，应拆分为多个 commit（见 [§6 提交拆分指南](#6-提交拆分指南)）

### 3.3 类型判断辅助

不确定该用哪个 type 时，问"这次变更的目的是什么"：

- 让 Agent **多做一件事** → `feat`
- 让 Agent **不出错** → `fix`
- 让 Agent **更快/更省 token** → `perf`
- 让代码 / 文档 / SKILL **更清晰**（行为不变） → `refactor`（代码） / `docs`（文档）
- 改的是 **工具链/CI/Docker/依赖** → `infra`

> [!IMPORTANT]
> **prompt / SKILL.md 的语义变更（影响 LLM 输出）算 `feat` 或 `fix`，不是 `docs`**。
> 例：`feat(prompt): system.md 追加只读边界声明` 算 `feat`，因为 LLM 行为会变。
> `docs(prompt): 修正 system.md 的拼写` 才算 `docs`，因为 LLM 行为不变。

---

## 4 范围（scope）

> [!IMPORTANT]
> mj-agent 的 scope 列表完全 mj-agent 原生，**按仓库真实结构定义**：`src/mj_agent/` 的模块面 + git 跟踪的顶层目录。其它项目（含上游业务系统）使用的 ETL 服务名缩写（如 `aec/dqv/qvl/qcm/sac/fc`）对 mj-agent 无效。下列 **35 项**构成闭合 scope 白名单。

> **v1.1 重建缘由（#443）**：v1.0 的 12 项白名单只建模了 `src/mj_agent/` 代码面（§4 原文即写「按 `src/mj_agent/` 实际模块结构定义」），而实测 **59% 的提交是 `docs` 型**，工作重心早已移到 `sdd/` `policies/` `decisions/` `plans/` `capabilities/` `docs/rule/` —— 这些区域在 12 项里**一个都没有**。结果是 45 种野生 scope、211 次使用、**51% 的提交带违规**，其中 65% 属「真实存在的仓库区域，白名单却没有」。
>
> **根因是白名单相对仓库结构不完整，不是纪律松弛。** 故 v1.1 以**完整性**为重建原则：下列 35 项对 `src/mj_agent/` 全部模块目录与顶层 `.py`、以及全部 git 跟踪的顶层治理目录**无遗漏**；§4.5 把维持这一不变量的责任落到具体 PR，避免重蹈 v1.0 的覆辙。

### 4.1 代码范围（`src/mj_agent/`）

14 项，覆盖全部 9 个模块目录与全部 7 个顶层 `.py`：

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `agent` | `agent.py`、`runtime.py`、`state.py`、graph 装配、`make_graph` | `feat(agent): 接入 describe_biz_table 到 ALL_TOOLS` |
| `llm` | `llm.py`、provider 工厂、模型配置 | `fix(llm): 空 ARK_API_KEY 时抛 LLMConfigError` |
| `config` | `config.py`、`env_drift.py`、pydantic-settings 字段 | `feat(config): 新增 LLM_THINKING_ENABLED 默认值` |
| `prompt` | `prompts/`（in-source canonical） | `feat(prompt): system.md v0.3 追加安全章节` |
| `skill` | `skills/`（in-source runtime skill，含同目录 Python） | `feat(skill): 新增 metrics-glossary skill` |
| `sql` | `tools/sql/`（`guardrail` / `precheck` / `execute` / `introspect`） | `fix(sql): guardrail 收紧尾随分号` |
| `tools` | `tools/` 下 `sql/` 以外（`analysis/` `charts/` `excel/` `biz_context.py`） | `feat(tools): charts 支持双轴折线` |
| `db` | `integrations/`（含 `mj_system_db.py`、连接池、role） | `infra(db): 连接池初始化时强制 read-only` |
| `memory` | `memory/`（checkpointer） | `feat(memory): 新增 TTL 逐出 CLI` |
| `middleware` | `middleware/` | `fix(middleware): 补 awrap_tool_call 异步实现` |
| `biz_catalog` | `biz_catalog/`（`loader` / `finder` / `qcm_catalog.yaml`） | `feat(biz_catalog): finder 支持同义词匹配` |
| `entity` | `entity/` | `feat(entity): 新增机构实体归一` |
| `server` | `server/`（`cli.py` 等入口） | `feat(server): mj-agent check 增加 --live` |
| `ui` | `ui.py`（Chainlit） | `fix(ui): 流式输出丢失最后一段` |

> **「零使用」不构成删除理由**：`db` 在 v1.0 全期零使用，但 `integrations/` 是 [[../../decisions/ADR-006_Fail_Safe_Reads|ADR-006]] 数据边界 L3 层的载体，是真实且受维护的模块面；§3 的 `perf` type 同样零使用而显然仍有效。零使用只说明该面近期无改动，不说明它不需要命名。v1.1 保留 `db` 并把覆盖路径由单文件放宽到整个 `integrations/`。

### 4.2 跨代码范围

#### 4.2.1 工程、测试与构建（10 项）

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `tests` | `tests/` 下 `bdd/` `contract/` `eval/` 以外（`unit/` `integration/` `smoke/` `fixtures/` `conftest.py`） | `test(tests): live_db fixture 在环境缺失时改为 skip` |
| `bdd` | `tests/bdd/` + `capabilities/**/behavior.feature` | `test(bdd): safe-sql 补 blocked-keyword scenario` |
| `contract` | `capabilities/**/contracts/` + `tests/contract/` | `test(contract): docker contract 增加 compose-config 校验` |
| `eval` | `tests/eval/` 与 `[EVAL]` 关联代码 | `test(eval): 增加 5 条 biz_dws 基线问题` |
| `ci` | `.github/`（`workflows/` / `ISSUE_TEMPLATE/` / PR 模板 / `dependabot.yml`） | `infra(ci): 引入 ruff 检查到 PR 工作流` |
| `deps` | `pyproject.toml`、`uv.lock` | `infra(deps): 升 langgraph 到 1.1.9` |
| `docker` | `docker/`、`.dockerignore` | `infra(docker): compose 增加 test overlay` |
| `scripts` | `scripts/`（含 `scripts/sdd/`） | `infra(scripts): 新增 setup-env.ps1` |
| `claude` | `.claude/`（`settings.json` / `skills/` / `hooks/` / `scripts/`）、`.mcp.json`、`.claudeignore` | `docs(claude): flow-intake skill 补 grilling 段` |
| `agents` | AI-agent 契约与生成投影面：`AGENTS.md`（根 + 嵌套）、`.agents/`、`.codex/`、`.agents.lock.json` | `docs(agents): 投影清单改指 manifest` |

#### 4.2.2 文档与治理（10 项）

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `sdd` | `sdd/`（kernel：`lifecycle` / `gates` / `workflows/` / `adapters/`） | `docs(sdd): gates.md 注册 check-stale-docs 行` |
| `policies` | `policies/` | `docs(policies): ci-gates §4.1 提升为原生条文` |
| `decisions` | `decisions/` + `archive/decisions/` | `docs(decisions): ADR-038 转 accepted` |
| `plans` | `plans/`（`[PLAN]` / `[INTAKE]`） | `docs(plans): flip docker-build-gate-flip 为 completed` |
| `capabilities` | `capabilities/`（其 `contracts/` 与 `evidence/` 另有 scope） | `docs(capabilities): data-agent spec.yml 补 REQ-005` |
| `evidence` | `evidence/` + `capabilities/**/evidence/` | `docs(evidence): 补 2026-08 CI 审计账本` |
| `rule` | `docs/rule/`（`[STANDARD]`）、`docs/_templates/` | `docs(rule): 重建 commit scope 白名单` |
| `guide` | `docs/guide/`、`docs/infrastructure/**`（含 `[RUNBOOK]`）、`docs/_baselines/` | `docs(guide): Developer_Onboarding 补 §7 Studio 走查` |
| `glossary` | `docs/glossary/`、`GLOSSARY.md` | `docs(glossary): 补上游仓术语归属段` |
| `archive` | `archive/`（归档仪式本身；被归档内容的领域 scope 另计） | `docs(archive): 迁 v2.2 trio 入 archive/rule` |

#### 4.2.3 兜底（1 项）

| scope | 覆盖路径 | 示例 header |
|---|---|---|
| `infra` | 无更精确 scope 的基础设施面：仓库根 `config/`（secrets pipeline）、`.env.example`、`langgraph.json`、`.gitignore` / `.gitattributes` 等 | `infra(infra): .gitignore 排除 .worktrees/` |

> **命名冲突提示**：scope `config` 指 **`src/mj_agent/config.py`**（应用配置模型），**不是**仓库根的 `config/` 目录（secrets pipeline）。后者归 `infra`。

### 4.3 Scope 约束

mj-agent 通用约束（后三条为 v1.1 新增，各附实测证据）：

- **`docs` 仅作 type 使用，不得作为 scope**。文档改动应取所在区域的 scope（`docs(sdd)` / `docs(rule)` / `docs(plans)`）；若跨区域，省略 scope：`docs: 更新 README`。*（历史误用 3 次）*
- **不得以 type 作 scope**。`refactor` / `test` / `feat` 等属 §3 的 type 命名空间，不是 scope。*（历史上 `refactor` 被误用作 scope **25 次**，为单项最多的违规）*
- **不得以项目阶段 / 里程碑作 scope**。阶段信息写进 summary 或 body，不占 scope 位。*（`stage-e` 13 次 + `phase0` / `phase-0.5` 各 1 次）*
- **一次 commit 只能有一个 scope**。`type(a)(b):` 的双括号形式不合规。*（Dependabot 早期产出的 `maintain(infra)(deps)` 属此类；其 `commit-message.prefix` 已于 2026-08-05 `aade0c2` 修正为 `infra`）*
- 真正混合无主导 scope 时，省略：`feat: <summary>`

### 4.4 多范围规则

| 情况 | 范围选择 |
|------|---------|
| 所有文件在同一子系统 | 使用该子系统 scope |
| 跨子系统但同一层（如多个 SQL 工具） | 使用层 scope（如 `sql`） |
| 基础设施 + 关联文档 | 使用基础设施 scope（如 `ci` / `deps`） |
| `.claude/**` 与 `.github/**` 混合面 | 省略 scope |
| 文档跨多个治理目录（如同时改 `sdd/` 与 `policies/`） | 省略 scope |
| 真正混合，无主导 scope | 省略 scope：`feat: <summary>` |

### 4.5 引入新 scope 的规则

scope 列表是封闭白名单。引入新 scope 必须通过修订本 STANDARD（`state: active` 后变更需要 minor 版本号），常见触发：

- `src/mj_agent/` 下新增 top-level 模块目录或顶层 `.py` 模块
- git 跟踪的顶层目录新增
- 新增独立子系统（如 Phase 2 的 `gateway`）
- 跨仓库契约目录

> **责任归属（v1.1 新增，本节的关键补丁）**：满足上述任一触发时，**由引入该目录 / 子系统的那个 PR 同批更新 §4.1-§4.2 表格**，不得留作无主待办。
>
> **教训来源**：v1.0 的本节已把「Phase 1 的 `memory`」明列为触发条件，而 `src/mj_agent/memory/` 落地后 scope **从未加入** —— 规范预写了自己的扩展触发，扩展却因无人负责而从未发生，`memory` 只能以野生 scope 形式出现。**触发条件不绑定责任人，等于触发条件不会被执行。**

### 4.6 历史别名映射（v1.1 新增）

v1.0 时期产生的野生 scope 按下表归并。**新提交一律使用右列的正式 scope**；本表仅供阅读历史 commit 与迁移期对照，不扩大白名单。

| 历史写法 | 正式 scope | 说明 |
|---|---|---|
| `plan` | `plans` | 取目录名本身（历史上单复数各 20 次，完全对半分裂） |
| `capability` | `capabilities` | 同上（6 : 2） |
| `adr` | `decisions` | 目录名为 `decisions/`（4 : 1） |
| `skills`、`safe-sql` | `skill` | 指 `src/mj_agent/skills/` 下的 runtime skill |
| `prompts` | `prompt` | |
| `mcp`、`hooks`、`setup`、`skill-index` | `claude` | 均落在 `.claude/` 或 `.mcp.json` 面。**注意 `skill-index` 指 `.claude/skills` 索引，不是 `skill`** —— `skill` scope 专指 `src/mj_agent/skills/` |
| `unit` | `tests` | |
| `guardrail` | `sql` | |
| `runbook` | `guide` | `docs/runbook/` 并不存在；RUNBOOK 实住 `docs/infrastructure/**` |
| `governance` | `policies` | 文档治理规则面（个别历史用例实际落在 `docs/infrastructure/`，按实际路径取 `guide`） |
| `adapter`、`sdd-adapter`、`metrics`、`meta` | `sdd` | `metrics` 指 SDD 结构度量报告；`meta` 指已归档的 Meta framework，其治理内容已并入 kernel |
| `workflow` | `ci` **或** `claude` | **该别名一词两义**：`ci(workflow)` 指 `.github/workflows/`；`docs(workflow)` 指 `.claude/skills/` 的 flow 家族。按实际改动路径二选一 |
| `template` | `rule` | `docs/_templates/`，已并入 `rule` 覆盖路径 |
| `env`、`scaffold` | `infra` | `.env.example` / `.gitignore` 等根级基础设施 |
| `changelog` | 省略 scope | 项目根 5 文件不构成 scope 区域 |

> **单复数规则**：一律与目录名本身一致。白名单内不得同时出现同一概念的单复数两形。

---

## 5 分支类型与 Commit 类型

### 5.1 命名区分

分支类型与 commit 类型采用 **不同的命名空间** 避免混淆：

| 分支类型（全称/复合词） | Commit 类型（缩写/不同词） | 命名区分方式 |
|------------------------|--------------------------|------------|
| `feature` | `feat` | 全称 ≠ 缩写 |
| `bugfix` | `fix` | 复合词 ≠ 简称 |
| `documentation` | `docs` | 全称 ≠ 缩写 |
| `maintain` | `infra` | 完全不同的词 |
| `hotfix` | `fix` | 复合词 ≠ 简称 |

常见错误：用 `feature` 作为 commit type，或 `feat` 作为分支名前缀。

### 5.2 分支内允许的 Commit 类型

mj-agent 5 分支 × 7 commit type 对齐矩阵：

| 分支类型 | 允许的 Commit 类型 | 说明 |
|---------|-------------------|------|
| `feature/*` | `feat`, `perf`, `refactor`, `test`, `docs` | 功能开发常伴随性能优化、重构、测试与文档 |
| `bugfix/*` | `fix`, `test`, `docs` | 修复 Bug 常伴随测试补充 |
| `documentation/*` | `docs` | 纯文档分支应只有 `docs` 类型 |
| `maintain/*` | `infra`, `docs` | `infra` 用于所有基础设施变更（CI/CD、依赖、脚本、配置） |
| `hotfix/*` | `fix` | 紧急修复应只有 `fix` 类型 |

> Code Review 时可对照此表检查：`hotfix/*` 分支中不应出现 `feat` 类型的 commit。

---

## 6 提交拆分指南

mj-agent 通用拆分原则（含本仓常见示例）：

### 6.1 拆分原则

**逻辑相关** 的变更合为一个 commit；**独立** 的变更拆分提交。

### 6.2 应拆分的信号

| 信号 | mj-agent 示例 | 拆分方式 |
|------|------|---------|
| 暂存文件跨 2+ 个不相关子系统 | skill 改动 + db 配置 | 按子系统拆分 |
| 代码 + 文档涉及不同主题 | agent 代码 + skill 文档 | 按主题拆分 |
| 混合 feat + refactor/perf | 新 tool + 重构旧 tool | 按 commit type 拆分 |
| Schema/契约变更 + 应用代码 | guardrail 白名单更新 + skill 调用 | guardrail 先提交，skill 后提交 |
| 差异超过 ~300 行跨 5+ 文件 | 大型重构 | 按逻辑单元拆分 |

### 6.3 推荐提交顺序

| 顺序 | 内容 | 原因 |
|------|------|------|
| 1 | 数据/契约层（guardrail 白名单、`[CONTRACT]` 文档） | 其他代码可能依赖 |
| 2 | 核心应用代码（agent / tool / skill） | 主要交付物 |
| 3 | 测试（unit / integration / smoke） | 验证步骤 2 |
| 4 | 文档（docs/ / SKILL.md 非语义更新） | 描述已完成的内容 |
| 5 | 基础设施（CI、依赖、脚本） | 支持性变更 |

### 6.4 不应拆分的情况

- 功能代码 + 其单元测试（同一逻辑单元）
- guardrail 正则 + 立刻使用该正则的 tool（同一安全单元）
- 少于 5 个文件、少于 100 行差异、单一 scope

---

## 7 示例

### 7.1 正确示例

```text
feat(skill): 新增 metrics-glossary skill
fix(sql): guardrail 正则收紧尾随分号
perf(agent): 工具调用并行化以减少端到端 latency
refactor(llm): 提取 thinking 模式开关为独立函数
infra(ci): 引入 ruff 检查到 PR 工作流
infra(deps): 升 langgraph 到 1.1.9
docs(skill): 修正 query-writing skill 中的 schema 名拼写
test(tests): live_db fixture 在环境缺失时改为 skip
test(eval): 增加 5 条 biz_dws 基线问题
docs: 更新 README 的 Phase 0 状态
```

### 7.2 常见错误

| 错误类型 | 错误示例 | 正确示例 |
|---------|---------|---------|
| 大写 type | `Feat(skill): ...` | `feat(skill): ...` |
| 句号结尾 | `feat(skill): 新增功能。` | `feat(skill): 新增功能` |
| 缺少空格 | `feat(skill):新增功能` | `feat(skill): 新增功能` |
| 分支类型作 commit type | `feature(skill): ...` | `feat(skill): ...` |
| `docs` 作 scope | `feat(docs): ...` | `docs: ...` 或 `docs(skill): ...` |
| 模糊摘要 | `fix(sql): fix bug` | `fix(sql): guardrail 正则未拦截多语句` |
| 过去时态 | `feat(skill): added skill` | `feat(skill): add skill` |
| 用了不存在的 scope | `feat(rag): ...`（mj-agent 暂无 rag） | 等待 §4.5 流程把 `rag` 入白名单 |

### 7.3 复杂示例（带 body 与 footer）

```text
fix(guardrail): 拦截多语句 SQL 中的尾随分号

之前的正则 `^\s*SELECT.*$` 在多行 SQL 上以 . 不匹配换行通过校验，
导致 `SELECT 1; DROP TABLE x;` 第二段语句进入 execute 路径。
新正则用 re.DOTALL + 强制单语句尾部分号检测拦截。

Refs: #42
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## 8 脚注（Footers）

仅允许使用以下 **标准 git trailers**：

| Footer | 用途 | 示例 |
|---|---|---|
| `Co-Authored-By:` | 多人协作 | `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` |
| `Refs:` / `Closes:` / `Fixes:` | 关联 issue/PR | `Fixes: #12` |
| `BREAKING CHANGE:` | Conventional Commits 1.0.0 normative | `BREAKING CHANGE: load_skill 不再返回 frontmatter` |
| `Signed-off-by:` | DCO（mj-agent 当前不强制） | `Signed-off-by: Some Dev <dev@example.com>` |

> [!CAUTION]
> **不要发明自定义 footer 关键字**（如 `Eval-Score:`、`Prompt-Version:`、`Trace-ID:`）。
> 背景研究确认：[[capabilities/infrastructure/evidence/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|本规范的评估文档]] §4 引用的 8 个数据 Agent OSS 项目（LangChain / LangGraph / Vanna / DB-GPT / WrenAI / AutoGPT / Aider / Open Interpreter）**0/8** 使用自定义 footer。
> - prompt 版本 → 写在 `src/mj_agent/prompts/<name>.md` frontmatter 的 `version` 字段
> - eval 分数 → 写在 PR 描述里、或附带 `[EVAL]` 文档
> - LangSmith trace → 写在 `[POSTMORTEM]` 文档的 `trace_ref` 字段（Framework v1.0 §4.4）

---

## 9 促活条件

本规范当前为 `state: draft`。提升为 `state: active` 的条件（满足任意一个即可）：

1. **量化达标**：≥20 次提交（任意非 `main` 分支）严格遵循本规范，违规率 ≤ 10%
2. **自动化达标**：`.github/workflows/` 中已部署 `amannn/action-semantic-pull-request`（参见 [LangChain pr_lint.yml](https://github.com/langchain-ai/langchain/blob/master/.github/workflows/pr_lint.yml) 范例），强制校验 PR 标题
3. **阶段达标**：Phase 0 退出（即 `plans/mj-agent-roadmap-v1.6.md` Phase 0 退出条件全部达成）

提升为 `active` 时同步更新：
- 本文 frontmatter `state: draft → state: active` + bump `updated`
- `CLAUDE.md` §Repo conventions 段补一行指向本规范
- `docs/INDEX.md` 同步状态

---

## 10 参考资料

### 10.1 项目内部

- [[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from 上游业务系统]] —— 历史决策记录（保留原 ADR 编号 + 文件名以稳定 wikilink；ADR-010 在 PR-Γ 候选 archive）
- [[capabilities/infrastructure/evidence/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|配套适配评估 v1.0]] —— 决策依据
- [[policies/documentation|policies/documentation]] §7（CLAUDE.md sync allowlist；§7.2 三轨分段）—— CLAUDE.md 同步触发条件（原 Meta §6.4/§6.4.1；tri-track trio 已 M6 PR4 archive）
- [[[STANDARD]_GitHub_Markdown|GitHub-Flavored Markdown 编写规范 v1.0]] —— 本文 Markdown/YAML 语法依据
- `CLAUDE.md §Repo conventions` —— 仓库级 commit 约定（待与本规范同步）

### 10.3 行业规范

- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) —— 基础规范
- [Angular commit-message-guidelines.md](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md) —— scope=package 模式起源
- [amannn/action-semantic-pull-request](https://github.com/amannn/action-semantic-pull-request) —— LangChain/LangGraph 使用的 PR 标题校验 Action（Phase 1 计划引入）
