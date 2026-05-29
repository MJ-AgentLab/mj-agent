---
type: guide
domain: SYS
summary: mj-agent Git 分支策略指南 — 5 分支模型（feature/bugfix/documentation/maintain/hotfix）+ 命名规范 + 分支×commit 类型矩阵 + worktree 操作
tags:
  - guide
  - git
  - branch
  - workflow
aliases:
  - mj-agent Git Branch Strategy
  - mj-agent Git 分支策略指南
created: 2026-04-30
updated: 2026-04-30
state: draft
version: v1.0
track: code
owner: 项目负责人
---

# mj-agent Git 分支策略指南

> **适用范围**：mj-agent 项目全体开发人员的 Git 分支操作规范
> **目标受众**：开发者、维护者
> **版本**：v1.0
> **最后更新**：2026-04-30
> **历史背景**：5 分支模型与 worktree 用法源自团队成熟实践；命名示例与 commit scope 已按 mj-agent 12 scope 调整。
> **关联文档**：[[GUIDE]_Git_Push_Workflow|Git 推送工作流]]、[[GUIDE]_PR_Description_Convention|PR 描述规范指南]]

---

## TL;DR

- **阅读时间**：~12 分钟
- **涵盖范围**：获取项目代码、分支模型、命名规范、分支类型与 Commit 类型的关系、五种分支的操作流程、Git Worktree 用法
- **适用场景**：日常开发中创建、使用和清理 Git 分支时参考

## Prerequisites

- **必备知识**：Git 基础操作（add、commit、push、pull）
- **建议了解**：GitHub Pull Request 流程

---

## 目录

0. [获取项目代码](#0-获取项目代码)
1. [什么是分支模型](#1-什么是分支模型)
2. [分支该怎么命名](#2-分支该怎么命名)
3. [分支类型与 Commit 类型的关系](#3-分支类型与-commit-类型的关系)
4. [如何创建和使用分支](#4-如何创建和使用分支)
5. [分支的生命周期是怎样的](#5-分支的生命周期是怎样的)
6. [用 Git Worktree 并行开发](#6-用-git-worktree-并行开发)
7. [速查表](#7-速查表)

---

## 0 获取项目代码

开始分支操作之前，你需要先把项目代码克隆到本地。

### 0.1 获取仓库访问权限

本项目为 **Private 仓库**，首次克隆前需要向项目负责人申请访问权限。

仓库地址：`https://github.com/MJ-AgentLab/mj-agent`

### 0.2 克隆代码

```bash
# 进入工作目录
cd d:\workspace\10-software-project\projects

# 克隆仓库
git clone https://github.com/MJ-AgentLab/mj-agent.git

# 进入项目目录
cd mj-agent
```

### 0.3 验证克隆完整性

```bash
git log --oneline -5
# 应能看到最近的提交记录

git branch -a
# 应能看到 main、develop 和远程分支
```

### 0.4 搭建 Bare Repo Worktree 开发结构

项目使用 Bare Repo Worktree 实现多分支并行开发（详见 [[#6 用 Git Worktree 并行开发]]），克隆后需执行以下初始化步骤：

```bash
# Step 1：创建容器目录并克隆为 bare repo
mkdir mj-agent && cd mj-agent
git clone --bare https://github.com/MJ-AgentLab/mj-agent .bare

# Step 2：创建 gitdir 指针文件
# Windows PowerShell：
New-Item .git -ItemType File -Value "gitdir: ./.bare"
# bash：echo "gitdir: ./.bare" > .git

# Step 3：修复 fetch refspec（必须，否则无法追踪远程分支）
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# Step 4：拉取远程分支，创建 develop worktree
git fetch origin
git worktree add develop develop
```

搭建完成后的目录结构：

```text
mj-agent/
├── .bare/            (bare repo 实体，隐藏)
├── .git              (gitdir 指针文件，隐藏)
└── develop/          (develop worktree，可见)
```

> [!TIP]
> 所有 Worktree 目录共享同一个 Git 仓库。**注意：所有 Git 命令必须在 worktree 目录内执行**（`mj-agent/` 根目录无工作树）。

---

## 1 什么是分支模型

在开始日常开发之前，先了解一下项目的分支结构。mj-agent 采用的分支模型如下：

```text
main              ← 可部署版本（受保护，只接受 PR 合并）
│
├── develop       ← 开发主线（受保护，只接受 PR 合并）
│   │
│   ├── feature/xxx         ← 功能开发（新功能、新 skill、重构）
│   ├── bugfix/xxx          ← 常规修复（develop 上发现的 Bug）
│   ├── documentation/xxx   ← 文档变更（独立的纯文档更新）
│   └── maintain/xxx        ← 维护变更（CI/CD、依赖、工具脚本、配置）
│
└── hotfix/xxx    ← 紧急修复（从 main 创建，PR 到 main，再同步到 develop）
```

简单来说，项目有两条**永久分支**和若干**临时分支**。下面分别介绍。

### 永久分支

> **定义**：永久分支是始终存在于仓库中、不会被删除的分支。任何人都不能直接推送代码，只能通过 Pull Request 合并。

| 分支 | 作用 | 保护级别 |
|------|------|---------|
| `main` | 存放可部署到生产环境的代码 | 最高（需审查 + 批准） |
| `develop` | 日常开发的集成主线 | 高（需审查 + 批准） |

### 临时分支

> **定义**：临时分支是开发者为完成某项具体工作而按需创建的分支。工作完成并通过 PR 合并后，该分支即被删除。

| 分支类型 | 谁创建 | 什么时候删除 |
|---------|--------|------------|
| `feature/*` | 开发者 | PR 合并后 |
| `bugfix/*` | 开发者 | PR 合并后 |
| `documentation/*` | 开发者 | PR 合并后 |
| `maintain/*` | 开发者 | PR 合并后 |
| `hotfix/*` | 维护者 | PR 合并后 |

---

## 2 分支该怎么命名

好的命名让团队成员一眼就能看出分支的用途。

### 2.1 命名格式

分支名由**类型**和**描述**组成，中间用 `/` 分隔：

```text
<类型>/<issue-id>-<描述>      # 关联 GitHub Issue 时，把 issue 编号放在描述前面
<类型>/<描述>                  # 没有关联 Issue 时，直接写描述即可
```

例如 `feature/12-metrics-glossary-skill` 表示这个功能分支对应 Issue `#12`，内容是新增 metrics-glossary skill。

### 2.2 五种分支类型

> **定义**：分支类型（Branch Type）标识一段**工作的性质** —— 你要做的是新功能开发、Bug 修复、文档更新还是基础设施维护。分支类型决定了从哪个基准分支创建、PR 合并到哪个目标分支。

不确定该用哪种类型？可以参考下表：

| 类型 | 格式 | 从哪创建 | PR 目标 | 适用场景 |
|------|------|---------|---------|---------|
| 功能 | `feature/<描述>` | develop | develop | 新 skill、新 tool、新 prompt 段落、重构（可包含伴随的文档更新） |
| 修复 | `bugfix/<描述>` | develop | develop | 开发过程中发现的常规 Bug（guardrail 漏洞、SQL 转义错误、loader 解析异常） |
| 文档 | `documentation/<描述>` | develop | develop | `docs/` 目录、`README.md`、in-source `SKILL.md` 与 `prompts/*.md` 的非语义改动 |
| 维护 | `maintain/<描述>` | develop | develop | `.github/`（workflow、模板）、依赖更新、构建脚本、配置 |
| 热修复 | `hotfix/<描述>` | main | main | 生产环境紧急 bug（合并后需同步到 develop） |

> [!TIP]
> 判断小技巧
> - 这次改动是**新功能或重构**？→ 用 `feature/`
> - 在 develop 上发现了 **Bug** 需要修复？→ 用 `bugfix/`
> - 这次改动**只改文档，不改代码**？→ 用 `documentation/`
> - 文档**伴随代码一起改**？→ 跟着代码走，用 `feature/` 或 `maintain/`
> - 改的是 **CI/依赖/脚本/配置**等非业务内容？→ 用 `maintain/`
> - 生产环境出了**紧急 Bug**？→ 用 `hotfix/`
> - `CHANGELOG.md` 属于发布流程的一部分（Phase 0.5+ 引入），不需要单独建分支

> [!NOTE]
> Issue 模板
> 每种分支类型都有对应的 GitHub Issue 模板（`.github/ISSUE_TEMPLATE/`，Phase 0.5+ 启用）。创建 Issue 时选择对应类型的模板，模板底部会提示正确的分支命名格式。

### 2.3 命名示例

看几个实际的例子，帮助你建立直觉：

| 场景 | 分支名 |
|------|--------|
| Issue #12 要求新增 metrics-glossary skill | `feature/12-metrics-glossary-skill` |
| 新增 SQL guardrail 增强工具 | `feature/add-guardrail-enhancements` |
| skill 体系从单文件拆分为目录化 | `feature/skill-bundle-restructure` |
| Issue #25 修复 guardrail 正则未拦截多语句 | `bugfix/25-guardrail-regex-fix` |
| 修复 ARK 客户端在空 API key 时崩溃 | `bugfix/llm-empty-api-key-error` |
| Issue #15 更新 SKILL.md frontmatter 字段 | `documentation/15-skill-frontmatter-update` |
| 补充 SQL guardrail 设计文档 | `documentation/add-guardrail-design-doc` |
| 更新 README | `documentation/update-readme` |
| Issue #8 新增 PR 模板 | `maintain/8-add-pr-template` |
| 升 langgraph 到 1.1.9 | `maintain/bump-langgraph` |
| Issue #20 修复生产环境 SQL 超时 | `hotfix/20-sql-timeout` |

---

## 3 分支类型与 Commit 类型的关系

### 3.1 为什么要区分这两个概念

项目中有两套分类体系：**分支类型**和 **Commit 类型**（详见 [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]]）。它们描述的层次不同：

- **分支类型**标识一段工作的整体性质（我在做什么类型的工作）
- **Commit 类型**标识单次提交的变更性质（这次提交做了什么类型的改动）

一个分支内可以包含多种类型的 commit。例如，开发一个新 skill（`feature/*` 分支）时，你可能会产生 `feat` 提交（功能代码 + SKILL.md）、`test` 提交（测试用例）和 `docs` 提交（文档更新）。

### 3.2 命名设计原则

> **定义**：Commit 类型（Commit Type）是 commit message 中标识单次提交变更性质的前缀关键词（如 `feat`、`fix`、`docs`），遵循 [Conventional Commits](https://www.conventionalcommits.org/) 行业标准。

为避免分支类型和 commit 类型混淆，两者采用**不同的命名空间**：

- **分支类型**使用**完整词或复合词**（如 `feature`、`bugfix`、`documentation`、`maintain`、`hotfix`）
- **Commit 类型**使用**短缩写或不同词**（如 `feat`、`fix`、`perf`、`docs`、`infra`），基于 Conventional Commits 行业标准扩展

| 分支类型 | Commit 类型 | 命名区分 |
|----------|-----------|---------|
| `feature` | `feat` | 全称 ≠ 缩写 |
| `bugfix` | `fix` | 复合词 ≠ 简称 |
| `documentation` | `docs` | 全称 ≠ 缩写 |
| `maintain` | `infra` | 完全不同的词 |
| `hotfix` | `fix` | 复合词 ≠ 简称 |

### 3.3 分支内允许的 Commit 类型

| 分支类型 | 允许的 Commit 类型 | 说明 |
|---------|-------------------|------|
| `feature/*` | `feat`, `perf`, `refactor`, `test`, `docs` | 功能开发常伴随性能优化、重构、测试和文档 |
| `bugfix/*` | `fix`, `test`, `docs` | 修复 Bug 常伴随测试补充 |
| `documentation/*` | `docs` | 纯文档分支应只有 `docs` 类型 |
| `maintain/*` | `infra`, `docs` | `infra` 用于所有基础设施变更（CI/CD、依赖、脚本、配置） |
| `hotfix/*` | `fix` | 紧急修复应只有 `fix` 类型 |

> [!TIP]
> 一致性检查
> Code Review 时可对照此表检查：`hotfix/*` 分支中不应出现 `feat` 类型的 commit；`documentation/*` 分支中不应出现 `feat` 或 `fix` 类型的 commit。

---

## 4 如何创建和使用分支

下面通过五种分支类型，分别演示完整的操作流程。每种类型的核心步骤都是：**创建 → 开发 → 推送 → PR → 清理**。

### 4.1 Feature 分支

功能分支是你最常用的分支类型。从 `develop` 创建，完成后通过 PR 合并回 `develop`。

```bash
# Step 1：在 develop worktree 内拉取最新代码，创建 feature worktree
# 执行位置：mj-agent/develop/
git pull origin develop
git worktree add ../feature/12-metrics-glossary-skill -b feature/12-metrics-glossary-skill develop

# Step 2：进入新 worktree，开发、提交（可以多次提交）
cd ../feature/12-metrics-glossary-skill
git add <files>
git commit -m "feat(skill): 新增 metrics-glossary skill"

# Step 3：推送到远程仓库（推送前检查流程详见 [[GUIDE]_Git_Push_Workflow|Git 推送工作流]]）
git push -u gitee feature/12-metrics-glossary-skill && git push -u origin feature/12-metrics-glossary-skill

# Step 4：到 GitHub 上创建 Pull Request，目标分支选 develop

# Step 5：PR 合并后，移除 worktree 并清理本地分支
# 执行位置：mj-agent/develop/（或任意其他 worktree）
git worktree remove ../feature/12-metrics-glossary-skill
git branch -d feature/12-metrics-glossary-skill
```

### 4.2 Bugfix 分支

在 develop 上发现的常规 Bug，使用 bugfix 分支修复。流程和 feature 分支类似：

```bash
# Step 1：在 develop worktree 内拉取最新代码，创建 bugfix worktree
# 执行位置：mj-agent/develop/
git pull origin develop
git worktree add ../bugfix/25-guardrail-regex-fix -b bugfix/25-guardrail-regex-fix develop

# Step 2：进入新 worktree，修复 Bug、提交
cd ../bugfix/25-guardrail-regex-fix
git add <files>
git commit -m "fix(sql): guardrail 正则收紧尾随分号"

# Step 3：推送到远程（推送前检查流程详见 [[GUIDE]_Git_Push_Workflow|Git 推送工作流]]）
git push -u gitee bugfix/25-guardrail-regex-fix && git push -u origin bugfix/25-guardrail-regex-fix

# Step 4：到 GitHub 上创建 PR，目标分支选 develop

# Step 5：合并后移除 worktree 并清理本地分支
git worktree remove ../bugfix/25-guardrail-regex-fix
git branch -d bugfix/25-guardrail-regex-fix
```

> [!WARNING]
> bugfix 和 hotfix 的区别
> - **bugfix**：从 `develop` 创建，用于修复开发过程中发现的常规 Bug，PR 目标是 `develop`
> - **hotfix**：从 `main` 创建，用于修复生产环境的紧急 Bug，PR 目标是 `main`，合并后还需同步到 `develop`

#### G24 BLOCKING gate（`bugfix/*` 专属;Stage D D-5 + Stage E α' E-3 lock-in）

`bugfix/*` 分支 PR **必含 regression test**（per sdd/gates.md L63 + sdd/adapters/bdd-tdd.md L197-199 G24 BLOCKING）：

- **Primary 验证**: PR diff 必含至少 1 个 `tests/` 路径下的文件（NEW 或 modified）。Validator
  `scripts/sdd/check_tdd_test_list.py --check g24` 自动 enforce;CI 失败 → PR 阻塞合并。
- **覆盖语义**: regression test 须 reproduce 待修 Bug（per bdd-tdd.md L197-199 spec），
  即 failing-before-fix → passing-after-fix。

#### G24 Escape Hatch（Commit Trailer;R-16-3 Option d;Anti-Gate-Defeat 原则 R-16-6）

合法 no-test bugfix（如 doc-only / config-only / migration-only fix）经由 **HEAD commit
message trailer** 显式豁免；非 silent bypass（per R-16-6 anti-gate-defeat 原则）：

```text
fix(docs): typo in CLAUDE.md

Trivial typo fix; no functional change.

G24-Exempt: doc-only fix; no behavior change to test
```

- **Trailer 格式**: `G24-Exempt: <reason>`（冒号空格分隔;reason ≥1 char hard;≥10 char soft via reviewer culture）。
- **Trailer location** (R-16-9): **HEAD commit only**（CI 在 branch tip 验）;后续 commit
  无 trailer 不计;需 amend OR add HEAD commit 应用。
- **Reviewer culture**: trailer 不绕过 review;reason 的合理性由 reviewer 判断（rubber-stamp = process drift）。

简例汇总：

| 场景 | tests/ in diff | G24-Exempt trailer | G24 结果 |
|---|---|---|---|
| 标准 bugfix（含 regression test） | ✅ | — | PASS |
| Doc-only / config-only bugfix（无 test） | ❌ | ✅ + non-empty reason | PASS (with exempt note) |
| Bugfix 漏 test 且无 trailer | ❌ | ❌ | **FAIL (BLOCKING)** |
| 非 `bugfix/*` 分支 | — | — | SKIP (branch-conditional) |

> [!NOTE]
> G24 不适用 `hotfix/*`（生产紧急修复路径优先速度;hotfix 有独立 review 严格度）;不适用
> `feature/*` / `documentation/*` / `maintain/*`（per sdd/adapters/bdd-tdd.md L198 "仅 bugfix/* 分支触发"）。

### 4.3 Documentation 分支

当你需要**单独更新文档**（不涉及代码改动）时，使用 documentation 分支。流程和 feature 分支类似：

```bash
# Step 1：在 develop worktree 内拉取最新代码，创建 documentation worktree
# 执行位置：mj-agent/develop/
git pull origin develop
git worktree add ../documentation/15-skill-frontmatter-update -b documentation/15-skill-frontmatter-update develop

# Step 2：进入新 worktree，修改文档、提交
cd ../documentation/15-skill-frontmatter-update
git add docs/ src/mj_agent/skills/
git commit -m "docs(skill): 修正 query-writing skill 中的 schema 名拼写"

# Step 3：推送到远程（推送前检查流程详见 [[GUIDE]_Git_Push_Workflow|Git 推送工作流]]）
git push -u gitee documentation/15-skill-frontmatter-update && git push -u origin documentation/15-skill-frontmatter-update

# Step 4：到 GitHub 上创建 PR，目标分支选 develop

# Step 5：合并后移除 worktree 并清理本地分支
git worktree remove ../documentation/15-skill-frontmatter-update
git branch -d documentation/15-skill-frontmatter-update
```

### 4.4 Maintain 分支

CI 配置、依赖更新、工具脚本等"非业务代码"的变更，用 maintain 分支：

```bash
# Step 1：在 develop worktree 内拉取最新代码，创建 maintain worktree
# 执行位置：mj-agent/develop/
git pull origin develop
git worktree add ../maintain/8-add-pr-template -b maintain/8-add-pr-template develop

# Step 2：进入新 worktree，修改配置文件、提交
cd ../maintain/8-add-pr-template
git add .github/
git commit -m "infra(ci): 新增 PR 模板"

# Step 3：推送到远程（推送前检查流程详见 [[GUIDE]_Git_Push_Workflow|Git 推送工作流]]）
git push -u gitee maintain/8-add-pr-template && git push -u origin maintain/8-add-pr-template

# Step 4：到 GitHub 上创建 PR，目标分支选 develop

# Step 5：合并后移除 worktree 并清理本地分支
git worktree remove ../maintain/8-add-pr-template
git branch -d maintain/8-add-pr-template
```

### 4.5 Hotfix 分支

> [!WARNING]
> Hotfix 的流程和其他分支不同 —— 它从 `main` 创建，PR 也合并到 `main`，合并后还需要**同步到 develop**，以确保修复不会在后续开发中丢失。

```bash
# Step 1：确保 main worktree 存在（首次 hotfix 时需创建）
# 执行位置：mj-agent/ 根目录
git worktree add main main  # 已存在则跳过此步

# Step 2：进入 main worktree，拉取最新，创建 hotfix worktree
cd main
git pull origin main
git worktree add ../hotfix/20-sql-timeout -b hotfix/20-sql-timeout main

# Step 3：进入 hotfix worktree，修复并提交
cd ../hotfix/20-sql-timeout
git add <files>
git commit -m "fix(sql): 修复 statement_timeout 设置漂移"

# Step 4：推送并创建 PR，目标分支选 main
git push -u gitee hotfix/20-sql-timeout && git push -u origin hotfix/20-sql-timeout

# Step 5：PR 合并后，在 main worktree 上打 patch 版本标签（Phase 1+ 启用版本流程后）
cd ../main
git pull origin main
git tag -a v0.1.1 -m "Hotfix: 修复 statement_timeout 设置漂移"
git push gitee v0.1.1 && git push origin v0.1.1

# Step 6：把修复同步到 develop（这一步很重要，不要遗漏）
cd ../develop
git pull origin develop
git merge main
git push gitee develop && git push origin develop

# Step 7：移除 hotfix worktree 并清理本地和远程分支
git worktree remove ../hotfix/20-sql-timeout
git branch -d hotfix/20-sql-timeout
git push origin --delete hotfix/20-sql-timeout
```

---

## 5 分支的生命周期是怎样的

了解分支从创建到删除的完整过程，有助于你把握每个环节该做什么。

### 5.1 Feature / Bugfix / Documentation / Maintain 分支

这四种分支的生命周期是一样的：

```text
develop ───●─────────────────●───
           │                 │
           │  创建分支        │  PR 合并 + 删除分支
           │                 │
branch     └──●──●──●──●────┘
              开发   提交   推送
```

整个流程可以概括为五步：

1. 从 `develop` 创建分支
2. 在本地开发、提交
3. 推送到远程，创建 PR（目标：`develop`）
4. 审查通过后合并
5. 删除本地和远程分支

### 5.2 Hotfix 分支

Hotfix 分支的生命周期稍微复杂一些，因为它需要在合并到 `main` 后，额外同步到 `develop`：

```text
main    ───●──────────●──tag──●───
           │          │           │
           │  创建     │  PR 合并   │  同步到 develop
           │          │           │
hotfix     └──●──●───┘           │
              修复  推送          │
                                 │
develop ─────────────────────────●───
                              merge main
```

六个步骤依次是：

1. 从 `main` 创建分支
2. 修复、提交、推送
3. 创建 PR（目标：`main`），审查后合并
4. 在 `main` 上打 patch 标签
5. 将 `main` 同步合并到 `develop`
6. 删除本地和远程分支

---

## 6 用 Git Worktree 并行开发

项目采用 **Bare Repo Worktree** 模式，所有分支以独立目录的形式存在于 `mj-agent/` 内部，互不干扰，无需切换。

> [!WARNING]
> Bare Repo 根目录（`mj-agent/`）无工作树，所有 git 命令必须在 worktree 子目录内执行。
> 不要对已有 worktree 的分支执行 `git checkout`，否则会报 "already used by worktree" 错误。

### 6.1 如何创建新分支 Worktree

从任意已有 worktree（通常是 `develop/`）内执行：

```bash
# 在 mj-agent/develop/ 内执行
git worktree add ../feature/12-metrics-glossary-skill -b feature/12-metrics-glossary-skill develop
```

目录名与分支名层级同构：`feature/12-metrics-glossary-skill` 分支 → `mj-agent/feature/12-metrics-glossary-skill/` 目录。

### 6.2 创建后的目录结构

```text
mj-agent/
├── .bare/                                  (bare repo 实体，隐藏)
├── .git                                    (gitdir 指针，隐藏)
├── develop/                                (develop worktree)
├── feature/
│   └── 12-metrics-glossary-skill/          (feature worktree)
├── bugfix/
│   └── 25-guardrail-regex-fix/             (bugfix worktree)
└── hotfix/                                 (按需创建)
```

### 6.3 常用命令

| 操作 | 命令 | 执行位置 |
|------|------|---------|
| 查看所有 worktree | `git worktree list` | 任意 worktree 内 |
| 创建新分支 worktree | `git worktree add ../<type>/<name> -b <type>/<name> develop` | `develop/` 内 |
| 移除 worktree | `git worktree remove ../<type>/<name>` | 任意其他 worktree 内 |
| 切换工作目录 | `cd ../develop` 或 `cd ../feature/xxx` | shell |

---

## 7 速查表

以下是日常操作中最常用的命令，方便快速查阅。

### 分支操作速查

| 操作 | 命令 |
|------|------|
| 创建功能分支 | `cd develop && git worktree add ../feature/<描述> -b feature/<描述> develop` |
| 创建修复分支 | `cd develop && git worktree add ../bugfix/<描述> -b bugfix/<描述> develop` |
| 创建文档分支 | `cd develop && git worktree add ../documentation/<描述> -b documentation/<描述> develop` |
| 创建维护分支 | `cd develop && git worktree add ../maintain/<描述> -b maintain/<描述> develop` |
| 创建热修复分支 | `cd main && git worktree add ../hotfix/<描述> -b hotfix/<描述> main` |
| 推送分支 | `git push -u origin <分支名>` |
| 删除本地分支 | `git branch -d <分支名>` |
| 删除远程分支 | `git push origin --delete <分支名>` |

### 分支命名速查

| 类型 | 格式 | 从哪创建 | PR 目标 |
|------|------|---------|---------|
| 功能 | `feature/<issue-id>-<描述>` | develop | develop |
| 修复 | `bugfix/<issue-id>-<描述>` | develop | develop |
| 文档 | `documentation/<issue-id>-<描述>` | develop | develop |
| 维护 | `maintain/<issue-id>-<描述>` | develop | develop |
| 热修复 | `hotfix/<issue-id>-<描述>` | main | main |

> `<issue-id>` 为可选项，关联 GitHub Issue 时使用。

### 分支类型与 Commit 类型对照速查

| 分支类型 | Commit 类型 | 命名区分 |
|----------|-----------|---------|
| `feature` | `feat` | 全称 ≠ 缩写 |
| `bugfix` | `fix` | 复合词 ≠ 简称 |
| `documentation` | `docs` | 全称 ≠ 缩写 |
| `maintain` | `infra` | 完全不同的词 |
| `hotfix` | `fix` | 复合词 ≠ 简称 |

### mj-agent 12 scope 速查

| scope | 覆盖 | 示例 commit header |
|---|---|---|
| `agent` | `src/mj_agent/agent.py`、graph 装配 | `feat(agent): 接入 describe_biz_table 到 ALL_TOOLS` |
| `llm` | `src/mj_agent/llm.py`、Ark client | `fix(llm): 空 ARK_API_KEY 时抛 LLMConfigError` |
| `prompt` | `src/mj_agent/prompts/*.md` | `feat(prompt): system.md v0.3 追加安全章节` |
| `skill` | `src/mj_agent/skills/*` | `feat(skill): 新增 metrics-glossary skill` |
| `sql` | `src/mj_agent/tools/sql/*` | `fix(sql): guardrail 正则收紧尾随分号` |
| `db` | `src/mj_agent/integrations/mj_system_db.py` | `infra(db): 连接池初始化时强制 read-only` |
| `config` | `src/mj_agent/config.py` | `feat(config): 新增 LLM_THINKING_ENABLED 默认值` |
| `tests` | `tests/**` | `test(tests): live_db fixture 在环境缺失时改为 skip` |
| `eval` | Phase 2+ `evaluation/` | `test(eval): 增加 5 条 biz_dws 基线问题` |
| `ci` | `.github/workflows/`、PR templates | `infra(ci): 引入 ruff 检查到 PR 工作流` |
| `deps` | `pyproject.toml`、`uv.lock` | `infra(deps): 升 langgraph 到 1.1.9` |
| `infra` | 跨领域兜底 | `infra(infra): 新增 scripts/setup-env.ps1` |

完整 scope 定义见 [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] §4。

---

## 关联文档

- [[GUIDE]_Git_Push_Workflow|Git 推送工作流]] — 推送前检查 + 推送流程
- [[GUIDE]_GitHub_Setup_And_Versioning|GitHub 设置与版本管理]] — 仓库配置与版本号管理
- [[GUIDE]_PR_Description_Convention|PR 描述规范指南]] — PR 模板使用
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] — 提交消息格式
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from 上游业务系统]] — 决策依据
- CI/CD 发布流程手册 —— Phase 0.5/1 待 `docs/runbook/[RUNBOOK]_Release_Process.md` 启用，参见 ADR-010 §Defer

---

## 更新记录

| 日期 | 版本 | 内容 |
|------|------|------|
| 2026-04-30 | v1.0 | 派生自 上游业务系统 v5.0 同名 GUIDE：5 分支模型 + worktree 用法逐字保留；§0 / §2.3 / §4 / §7 命名示例与 commit scope 改 mj-agent 12 scope；URL 改 `MJ-AgentLab/mj-agent` |
