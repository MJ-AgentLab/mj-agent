---
type: guide
domain: SYS
summary: mj-agent PR 描述规范指南 — 6 模板（feature/bugfix/documentation/maintain/hotfix/release）× gh CLI × 自检清单（含 ruff/mypy/pytest）
tags:
  - guide
  - git
  - pr
  - workflow
aliases:
  - mj-agent PR Description Convention
  - mj-agent PR 描述规范指南
created: 2026-04-30
updated: 2026-04-30
state: draft
version: v1.0
track: code
owner: 项目负责人
---

# mj-agent PR 描述规范指南

> **适用范围**：为不同分支类型选择正确的 PR 模板，并写出清晰、有效的 PR 描述
> **目标受众**：开发
> **版本**：v1.0
> **最后更新**：2026-04-30
> **历史背景**：6 模板分类 + gh CLI 用法源自团队成熟实践；§3 案例与 §4.3 自检对齐表已换成 mj-agent 工具链 ruff/mypy/pytest。
> **关联文档**：[[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]]、[[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]]

---

## TL;DR

- **阅读时间**：~10 分钟
- **涵盖范围**：6 种 PR 模板的使用场景、字段填写指引、`gh` CLI 命令示例
- **适用场景**：创建 Pull Request 时选择对应模板并填写描述

## Prerequisites

- **目标读者**：所有提交 PR 的开发者
- **必备知识**：
  - Git 分支模型（[[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]]）
  - `gh` CLI 基础
- **建议了解**：[[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]]

---

## 目录

1. [为什么需要区分 PR 模板](#1-为什么需要区分-pr-模板)
2. [模板总览](#2-模板总览)
3. [各模板详解](#3-各模板详解)
4. [使用方式](#4-使用方式)
5. [速查表](#5-速查表)

---

## 1 为什么需要区分 PR 模板

### 1.1 不同分支类型的审核关注点不同

PR 描述的核心目的是**帮助审核者快速理解变更并做出判断**。不同类型的变更，审核者关注的信息完全不同：

| 分支类型 | 审核者最关心的问题 |
|---------|-----------------|
| `feature/*` | 这个功能做了什么？影响哪些 skill / tool / agent 模块？ |
| `bugfix/*` | Bug 的根因是什么？修复方案会不会引入回归？ |
| `documentation/*` | 文档格式对不对？wikilink 有没有失效？INDEX 同步了吗？ |
| `maintain/*` | 基础设施变更会不会影响现有环境？依赖升级是否兼容？ |
| `hotfix/*` | 生产问题有多严重？修复失败怎么回滚？ |
| Release PR | 版本号对不对？CHANGELOG 完整吗？（Phase 0.5+ 启用） |

### 1.2 通用模板的局限

通用模板只能覆盖最大公约数，导致两个问题：

- **关键信息缺失**：hotfix 场景需要「回滚预案」，通用模板没有这个字段
- **冗余字段干扰**：documentation PR 不需要类似 ruff/mypy 等代码检查项，但通用模板中有

### 1.3 与 Code Review 检查清单对齐

每种模板的「自检结果」字段，与项目负责人的 Code Review 检查清单保持对齐。开发者在提交 PR 时的自检，正是项目负责人审核时的逐项复核。

---

## 2 模板总览

### 2.1 模板 × 分支类型 × 目标分支

项目提供 6 种 PR 模板，每种模板对应一种分支类型或发布场景：

| 模板文件 | 适用分支类型 | 目标分支 | 适用场景 |
|---------|------------|---------|---------|
| `feature.md` | `feature/*` | develop | 新 skill、新 tool、新 prompt 段落、重构 |
| `bugfix.md` | `bugfix/*` | develop | develop 上发现的常规 Bug |
| `documentation.md` | `documentation/*` | develop | 纯文档变更（不涉及代码） |
| `maintain.md` | `maintain/*` | develop | CI/CD、依赖、工具脚本、配置 |
| `hotfix.md` | `hotfix/*` | **main** | 生产环境紧急 Bug |
| `release.md` | develop → main | **main** | 版本发布（Phase 1+ 启用） |

模板文件位于 `.github/PULL_REQUEST_TEMPLATE/` 目录（mj-agent 已存在 6 份）。

### 2.2 分支类型 × Commit 类型 × PR 模板三维关系

分支类型决定了允许的 Commit 类型（详见 [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] §3），而 PR 模板的自检清单会验证这一约束：

| 分支类型 | 允许的 Commit 类型 | PR 模板自检验证 |
|---------|-------------------|---------------|
| `feature/*` | `feat`, `perf`, `refactor`, `test`, `docs` | 检查 Commit message 规范 |
| `bugfix/*` | `fix`, `test`, `docs` | 检查仅含 `fix` / `test` / `docs` |
| `documentation/*` | `docs` | 检查仅含 `docs` |
| `maintain/*` | `infra`, `docs` | 检查仅含 `infra` / `docs` |
| `hotfix/*` | `fix` | 检查仅含 `fix` |

---

## 3 各模板详解

### 3.1 Feature PR 模板

**适用场景**：功能开发分支（`feature/*`）合并到 `develop`。包括新 skill、新 tool、新 prompt 段落、重构。

**字段说明**：

| 字段 | 填写指引 | 示例 |
|------|---------|------|
| **变更摘要** | 一段话概括变更内容和目的，回答"做了什么"和"为什么做" | 新增 metrics-glossary skill，让 agent 在用户提到业务指标缩写时主动展开释义 |
| **影响范围** | 列出受影响的 skill / tool / 配置 | `src/mj_agent/skills/metrics-glossary/`、`src/mj_agent/agent.py`（注册到 ALL_SKILLS）、SKILL.md 索引 |
| **审核要点** | 提示审核者重点关注什么，降低审核负担 | 重点检查 SKILL.md frontmatter 是否完整（含 track: agent）、五段式 body 是否覆盖、loader 路径是否被 `load_skill` 而非 `open().read()` 加载 |
| **自检结果** | 逐项勾选自检清单 | — |

**`gh` CLI 示例**：

```bash
gh pr create \
  --base develop \
  --head feature/12-metrics-glossary-skill \
  --template feature.md \
  --reviewer "<项目负责人 GitHub 用户名>"
```

> [!TIP]
> 使用 `--template` 后不需要 `--body`
> `gh` 会从 `.github/PULL_REQUEST_TEMPLATE/feature.md` 加载模板，并在系统编辑器（`$EDITOR`）中打开供你填写。保存并退出编辑器后，PR 即提交。

**实际案例占位**：

> [!NOTE]
> 首份 mj-agent feature PR 案例待 mj-agent 完成首个完整 feature 流程后回填。字段填法可参考 上游业务系统 同名 GUIDE 历史案例（QCM DWS 迁移）。

---

### 3.2 Bugfix PR 模板

**适用场景**：在 `develop` 上发现的常规 Bug，使用 `bugfix/*` 分支修复后合并回 `develop`。

**字段说明**：

| 字段 | 填写指引 |
|------|---------|
| **Bug 描述** | 一句话描述 Bug 的外在现象，让审核者快速了解问题 |
| **根因分析** | 简述问题的根本原因（而非表象），帮助审核者评估修复方案是否对症 |
| **修复方案** | 描述修复方法和关键改动，让审核者知道改了什么、怎么改的 |
| **影响范围** | 列出受影响的 skill / tool / 配置 |
| **自检结果** | 逐项勾选，注意 bugfix 分支仅允许 `fix` / `test` / `docs` 类型 commit |

**`gh` CLI 示例**：

```bash
gh pr create \
  --base develop \
  --head bugfix/25-guardrail-regex-fix \
  --template bugfix.md \
  --reviewer "<项目负责人 GitHub 用户名>"
```

---

### 3.3 Documentation PR 模板

**适用场景**：**纯文档变更**（不涉及代码改动），使用 `documentation/*` 分支。如果文档变更伴随代码一起改，应跟随代码使用 `feature/*` 或 `maintain/*` 分支。

**字段说明**：

| 字段 | 填写指引 |
|------|---------|
| **文档变更内容** | 列出新增或修改的文档文件名及变更摘要 |
| **变更原因** | 为什么需要这次文档更新（补充遗漏 / 规范变更 / 内容过时等） |
| **自检结果** | 重点检查文件命名规范、wikilink 有效性、INDEX.md 更新 |

这是最轻量的模板，文档 PR 的审核重点在于格式和内容准确性，不需要代码检查字段。

**`gh` CLI 示例**：

```bash
gh pr create \
  --base develop \
  --head documentation/15-skill-frontmatter-update \
  --template documentation.md \
  --reviewer "<项目负责人 GitHub 用户名>"
```

---

### 3.4 Maintain PR 模板

**适用场景**：CI/CD 配置、依赖更新、工具脚本等基础设施变更，使用 `maintain/*` 分支。

**字段说明**：

| 字段 | 填写指引 |
|------|---------|
| **变更摘要** | 简述维护变更的内容和目的 |
| **影响评估** | 重点说明受影响的**环境**（开发 / 测试 / 生产）和工具链，基础设施变更往往影响面广 |
| **审核要点** | 提示审核者关注的内容，如 CI 流水线兼容性、环境变量变更等 |
| **自检结果** | 重点检查配置语法、敏感信息，maintain 分支仅允许 `infra` / `docs` 类型 commit |

**`gh` CLI 示例**：

```bash
gh pr create \
  --base develop \
  --head maintain/8-add-pr-template \
  --template maintain.md \
  --reviewer "<项目负责人 GitHub 用户名>"
```

---

### 3.5 Hotfix PR 模板

**适用场景**：生产环境紧急 Bug 修复，使用 `hotfix/*` 分支，**目标分支为 `main`**。

> [!WARNING]
> Hotfix 与 Bugfix 的区别
> - **Bugfix**：从 `develop` 创建，PR 目标为 `develop`，用于修复开发过程中的常规 Bug
> - **Hotfix**：从 `main` 创建，PR 目标为 `main`，用于修复**生产环境**的紧急 Bug，合并后需同步到 `develop`
>
> 详见 [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] §4.2 和 §4.5

**字段说明**：

| 字段 | 填写指引 |
|------|---------|
| **事故描述** | 一句话描述生产环境的问题现象（用户看到了什么） |
| **影响范围** | 受影响的用户群体、功能或服务 |
| **根因分析** | 简述根本原因 |
| **修复方案** | 描述修复方法和关键改动 |
| **回滚预案** | **必填** —— 如修复引入新问题，如何快速回滚到修复前的状态 |
| **自检结果** | hotfix 分支**仅允许 `fix` 类型** commit，且需确认合并后同步 develop 的计划 |

**`gh` CLI 示例**：

```bash
gh pr create \
  --base main \
  --head hotfix/20-sql-timeout \
  --template hotfix.md \
  --reviewer "<项目负责人 GitHub 用户名>"
```

---

### 3.6 Release PR 模板

**适用场景**：版本发布，将 `develop` 合并到 `main`。由项目负责人创建。

> [!NOTE]
> Phase 0 阶段 mj-agent 暂未启用版本发布流程；本节作为 Phase 1+ 启用后的指引。

**字段说明**：

| 字段 | 填写指引 |
|------|---------|
| **Release 标题** | 格式：`Release vX.Y.Z — <版本主题>`，如 `Release v0.2.0 — 引入 metrics-glossary skill` |
| **Highlights** | 本版本的核心变更列表，从 CHANGELOG.md 中提取重点（Phase 0.5+ 启用） |
| **审核要点** | 使用 checklist 逐项确认：CHANGELOG 完整性、版本号一致、无调试残留、SKILL/PROMPT 契约稳定 |
| **Details** | 指向 CHANGELOG.md 的链接，供审核者查看完整 Release Notes |

**`gh` CLI 示例**：

```bash
gh pr create \
  --base main \
  --head develop \
  --title "Release vX.Y.Z" \
  --template release.md \
  --reviewer "<其他成员 GitHub 用户名>"
```

---

## 4 使用方式

### 4.1 通过 `gh` CLI 使用（推荐）

项目统一使用 `gh pr create` 创建 PR。通过 `--template` 参数指定模板：

```bash
gh pr create \
  --base <目标分支> \
  --head <当前分支> \
  --template <模板名>.md \
  --reviewer "<审核者 GitHub 用户名>"
```

`--template` 参数会从 `.github/PULL_REQUEST_TEMPLATE/` 目录加载指定模板的内容，并在系统编辑器（`$EDITOR`）中打开供你交互式填写。保存并退出编辑器后，PR 即创建完成。

> [!TIP]
> 不再需要内联 `--body`
> 使用 `--template` 后，不需要再用 `--body` 参数手写 PR 描述。`gh` 会将模板内容加载到编辑器中，你只需在对应位置填入具体内容。

### 4.2 通过 GitHub 网页使用

在 GitHub 网页创建 PR 时，通过 URL 参数指定模板：

```text
https://github.com/MJ-AgentLab/mj-agent/compare/<base>...<head>?template=feature.md
```

将 `template=` 后面的值替换为对应的模板文件名。

### 4.3 自检清单与 Code Review 的关系

每种模板的「自检结果」字段，是项目负责人 Code Review 检查清单的**开发者视角镜像**。对应关系如下：

| Code Review 检查项（项目负责人视角） | 对应模板自检项（开发者视角） | 适用模板 |
|------------------------------|--------------------------|---------|
| 代码逻辑正确，无明显 bug | Bug 已复现并验证修复 / `uv run pytest tests/unit` 通过 | bugfix, feature |
| Commit message 符合规范 | Commit message 符合 `<type>(<scope>): <summary>` 规范 | 全部 |
| Lint 无错误 | `uv run ruff check` 无 lint 错误 | feature, bugfix, maintain |
| 类型检查通过 | `uv run mypy src/mj_agent` 通过 | feature, bugfix |
| 单元测试通过 | `uv run pytest tests/unit` 通过 | feature, bugfix |
| Skill / Prompt loader 行为一致 | skill loader frontmatter strip 行为不被绕过（如触及 `src/mj_agent/skills/` 或 `src/mj_agent/prompts/`，必须用 `load_skill` / `load_prompt`） | feature |
| 无调试残留 | 无残留调试代码 | feature, bugfix |
| 变更范围合理 | 仅含允许的 Commit 类型 | bugfix, documentation, maintain, hotfix |
| PR 描述清晰 | 各字段已按模板填写 | 全部 |
| — | CHANGELOG.md `[Unreleased]` 区块已更新（Phase 0.5+） | feature, bugfix |

> [!NOTE]
> mj-agent 与 上游业务系统 自检清单的差异
> - **删除**：「本地 Docker 环境自测通过」、「SQL 脚本：命名规范、schema 正确」、「无硬编码 IP / 密码 / 路径」（mj-agent Phase 0 暂不适用）
> - **新增**：ruff / mypy / pytest 三件套；skill loader frontmatter strip 自检
> - **延后**：「CHANGELOG.md `[Unreleased]` 区块已更新」 — Phase 0.5+ 引入 CHANGELOG 后启用

---

## 5 速查表

### 分支类型 → 模板 → 目标分支 → `gh` 命令

| 分支类型 | 模板文件 | 目标分支 | `gh pr create` 命令 |
|---------|---------|---------|-------------------|
| `feature/*` | `feature.md` | develop | `gh pr create --base develop --template feature.md` |
| `bugfix/*` | `bugfix.md` | develop | `gh pr create --base develop --template bugfix.md` |
| `documentation/*` | `documentation.md` | develop | `gh pr create --base develop --template documentation.md` |
| `maintain/*` | `maintain.md` | develop | `gh pr create --base develop --template maintain.md` |
| `hotfix/*` | `hotfix.md` | **main** | `gh pr create --base main --template hotfix.md` |
| Release | `release.md` | **main** | `gh pr create --base main --template release.md` |

### 模板核心字段速查

| 模板 | 核心字段 |
|------|---------|
| `feature.md` | 变更摘要、影响范围、审核要点、自检结果 |
| `bugfix.md` | Bug 描述、根因分析、修复方案、影响范围、自检结果 |
| `documentation.md` | 文档变更内容、变更原因、自检结果 |
| `maintain.md` | 变更摘要、影响评估、审核要点、自检结果 |
| `hotfix.md` | 事故描述、影响范围、根因分析、修复方案、回滚预案、自检结果 |
| `release.md` | Highlights、审核要点 checklist、Details |

---

## 关联文档

- [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] — 分支模型、命名规范、操作流程
- [[GUIDE]_Git_Push_Workflow|Git 推送工作流]] — 推送前检查 + 推送流程
- [[GUIDE]_GitHub_Setup_And_Versioning|GitHub 设置与版本管理]] — 仓库配置与版本号管理
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] — 提交消息格式
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from 上游业务系统]] — 决策依据
- CI/CD 发布流程手册 —— Phase 0.5/1 待 `docs/runbook/[RUNBOOK]_Release_Process.md` 启用，参见 ADR-010 §Defer

---

## 更新记录

| 日期 | 版本 | 内容 |
|------|------|------|
| 2026-04-30 | v1.0 | 派生自 上游业务系统 v5.0 同名 GUIDE：6 模板分类与 gh CLI 用法逐字保留；§3.1 实际案例改为 mj-agent 占位（首份案例待回填）；§4.3 自检对齐表删除 Docker / SQL / 硬编码三行，新增 ruff / mypy / pytest / skill loader frontmatter 四行；section 标题去掉 上游业务系统 服务专属字眼 |
