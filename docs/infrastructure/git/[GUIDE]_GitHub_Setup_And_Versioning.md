---
type: guide
domain: SYS
summary: GitHub 仓库初始化与版本管理（mj-agent 适配版） — 双推 remote、分支保护、SemVer 规则与 Phase 0 文件清单
tags:
  - guide
  - git
  - github
  - versioning
aliases:
  - mj-agent GitHub Setup and Versioning
  - mj-agent GitHub 设置与版本管理
created: 2026-04-30
updated: 2026-04-30
state: draft
version: v1.0
track: code
owner: 项目负责人
---

# mj-agent GitHub 设置与版本管理

> **适用范围**：mj-agent 仓库初始化配置、双推镜像设置、语义化版本管理规范
> **目标受众**：开发 + 维护者
> **版本**：v1.0
> **最后更新**：2026-04-30
> **历史背景**：仓库初始化与版本管理实践已按 mj-agent 12 scope、Phase 0 状态、v2.0 frontmatter 改造。
> **关联文档**：[[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]]、[[GUIDE]_Git_Push_Workflow|Git 推送工作流]]、[[GUIDE]_PR_Description_Convention|PR 描述规范指南]]

---

## TL;DR

- **阅读时间**：~8 分钟
- **涵盖范围**：GitHub 仓库创建与推送、Gitee 镜像配置、分支保护规则、语义化版本规则、Phase 0 版本号管理（轻量级，仅 `pyproject.toml`）
- **适用场景**：首次推送仓库到 GitHub、配置镜像仓库、未来发布版本时参考

## Prerequisites

- **目标读者**：项目负责人、需要理解版本管理的开发者
- **必备知识**：
  - Git 基础操作（remote、push、tag）
  - [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] 中的分支模型
- **建议了解**：GitHub 仓库管理、PowerShell 脚本基础

---

## 目录

1. [推送到 GitHub](#1-推送到-github)
2. [核心问题解答](#2-核心问题解答)
3. [语义化版本规则](#3-语义化版本规则)
4. [版本号管理流程](#4-版本号管理流程)
5. [验证清单](#5-验证清单)
6. [速查表](#6-速查表)

---

## 1 推送到 GitHub

### 1.1 GitHub 网页创建仓库

1. 打开 <https://github.com/new>
2. Repository name: **mj-agent**
3. Owner: **MJ-AgentLab**
4. 可见性: **Private**
5. **不要勾选** "Add a README file"、".gitignore"、"Choose a license"（本地已有完整内容）
6. 点击 **Create repository**

### 1.2 初始化 Bare Repo 并推送

```powershell
# 初始化 bare repo worktree（已在本地有代码时）
cd d:\workspace\10-software-project\projects
mkdir mj-agent && cd mj-agent
git clone --bare <local-path-or-existing-repo> .bare

# 创建 gitdir 指针（Windows PowerShell）
New-Item .git -ItemType File -Value "gitdir: ./.bare"

# 修复 fetch refspec
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 添加远程仓库并推送（从 develop worktree 内执行）
git worktree add develop develop
cd develop

# 添加远程仓库（GitHub + Gitee）
git remote add origin https://github.com/MJ-AgentLab/mj-agent.git
git remote add gitee https://gitee.com/ranzuozhou/mj-agent.git

# 推送所有分支（双推：先 Gitee 再 GitHub）
git push -u gitee main && git push -u origin main
git push -u gitee develop && git push -u origin develop

# 推送所有标签（Phase 0 暂无 tag，本步预留）
git push gitee --tags && git push origin --tags

# 配置双推 alias（简化日常推送）
git config alias.pushall '!git push gitee HEAD && git push origin HEAD'

# 验证
git remote -v          # 应看到 origin (GitHub) 和 gitee (Gitee)
git branch -r
```

> [!NOTE]
> CI Runner 无法直接访问 GitHub（HTTPS/SSH 均被阻断），后续 Phase 1+ 引入 CI/CD 流水线时会改为从 Gitee 镜像 checkout。Phase 0 阶段 CI 仅 `python -m compileall`，不依赖此机制；但开发者推送时仍建议双推保持镜像同步。详见 [[GUIDE]_Git_Push_Workflow|Git 推送工作流]] §6。

### 1.3 配置分支保护规则

推送完成后，在 GitHub 仓库页面配置分支保护：

**路径**：GitHub 仓库 → Settings → Branches → Add branch protection rule

| 分支 | 保护规则 |
|------|---------|
| `main` | PR 必须 · 至少 1 个 Approve · CI 通过 · CODEOWNERS 审核 · 禁止 force push |
| `develop` | PR 必须 · 至少 1 个 Approve · CI 通过 · 禁止 force push |

> [!NOTE]
> 分支保护确保所有代码变更都经过 PR 审查，防止误操作直接推送到主分支。

---

## 2 核心问题解答

### 问题 1：可部署版本在哪里？

**答：`main` 分支 + `v*` 标签 = 可部署版本（Phase 1+ 启用）**

```text
main 分支时间线（Phase 1+ 目标态）：

  init ──── ... ──── [合并 develop] ──── ...
                              │
                        tag: v0.1.0  ← 这就是可部署版本
```

- `main` 分支始终只接受从 `develop` 合并过来的、经过测试的代码
- 每次合并到 `main` 后打一个 **Git Tag**（如 `v0.1.0`），标记为可部署快照
- **Phase 0 现状**：mj-agent 尚未引入正式版本发布流程；`pyproject.toml` 内的 `version` 即唯一权威（默认 `0.1.0`）。Phase 1+ 与 docs/runbook/ 共同落地

> 查看历史可部署版本：`git tag -l "v*"` 列出所有版本标签；`git checkout v0.1.0` 切换到指定版本。

### 问题 2：成员如何拉取项目？

**答：初始化 Bare Repo Worktree，在 `develop/` 目录内工作**

```powershell
# 第 1 步：初始化 bare repo（只需执行一次）
mkdir mj-agent && cd mj-agent
git clone --bare https://github.com/MJ-AgentLab/mj-agent .bare

# 第 2 步：创建 gitdir 指针（Windows PowerShell）
New-Item .git -ItemType File -Value "gitdir: ./.bare"

# 第 3 步：修复 fetch refspec
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 第 4 步：拉取分支，创建 develop worktree
git fetch origin
git worktree add develop develop

# 第 5 步：进入 develop worktree，配置环境
cd develop
uv sync

# 第 6 步：创建 .env 文件（从团队共享渠道获取，不在 Git 中）
# 参考 .env.example 或向项目负责人索取
```

> [!IMPORTANT]
> 完整初始化步骤待 Phase 0.5 `docs/guide/[GUIDE]_Developer_Onboarding.md` 落地后引用；当前以本节为权威。

**为什么使用 Bare Repo 而不是普通 clone？**

| 对比项 | Bare Repo + Worktree | 普通 clone |
|--------|---------------------|-----------|
| 操作 | 5 步初始化（一次性） | `git clone` 一步，但需要 checkout |
| main 分支可见性 | 无 main 代码文件夹，目录更干净 | main 代码始终存在于根目录 |
| 多分支并行 | 每个分支独立子目录，互不干扰 | 需频繁 checkout 或额外 worktree add |
| 误操作风险 | 根目录无工作树，天然防止误 checkout | 可能误 checkout 到错误分支 |
| Claude Code 对齐 | 与 `superpowers:using-git-worktrees` 技能默认行为一致 | 与技能默认行为存在路径冲突 |

> [!NOTE]
> Bare Repo 初始化稍复杂，但日常工作目录更干净，所有分支以独立子目录形式存在，与项目 worktree 工作流完全对齐。

### 问题 3：功能完成后版本号如何变更？

**答：Phase 0 阶段开发期间版本号不变，未来发布时统一变更（Phase 1+ 启用）**

```text
时间线（Phase 1+ 目标态）：

  develop (0.1.0) ──┬── feature/A 合并 ──── feature/B 合并 ──── feature/C 合并
                    │        ↑                    ↑                   ↑
                    │   版本号不变            版本号不变          版本号不变
                    │
                    └── 所有功能完成，测试通过后：
                        1. develop 合并到 main
                        2. 在 main 上打标签 v0.1.0（可部署）
                        3. 在 develop 上改版本号为 0.2.0（开启下一轮开发）
```

**关键原则**（Phase 1+ 启用后生效）：

| 原则 | 说明 |
|------|------|
| 功能分支不改版本号 | feature/xxx 中的代码保持当前版本号 |
| 合并不改版本号 | feature 合并回 develop 时，版本号不变 |
| 发布时改版本号 | develop 合并到 main 后，打正式标签 |
| 新一轮改版本号 | 打完标签后，在 develop 上把版本号改为下一个 |

> [!NOTE]
> Phase 0 阶段 mj-agent 尚未引入正式发布流程；`pyproject.toml` 中的 `version` 由维护者按需手工调整即可。本节作为 Phase 1+ 引入版本流程的前瞻指引。

---

## 3 语义化版本规则

### 3.1 版本号格式：`MAJOR.MINOR.PATCH`

```text
          0  .  1  .  0
          │     │     │
          │     │     └── PATCH: bug 修复 / 小优化（不影响 API）
          │     └──────── MINOR: 新功能 / 新 skill（向后兼容）
          └────────────── MAJOR: 破坏性变更（API 不兼容）
```

### 3.2 版本号变更规则

| 场景 | 版本变化 | 示例 |
|------|---------|------|
| 新增 skill / tool / 子系统（如新增 metrics-glossary skill） | MINOR +1, PATCH 归零 | 0.1.0 → 0.2.0 |
| Bug 修复 / 性能优化 / 文档修正 | PATCH +1 | 0.1.0 → 0.1.1 |
| 数据边界 / SKILL/PROMPT 契约不兼容变更 | MAJOR +1, 其余归零 | 0.1.0 → 1.0.0 |
| 紧急热修复（从 main 分支出 hotfix） | PATCH +1 | 0.1.0 → 0.1.1 |

### 3.3 开发版本 vs 发布版本

| 阶段 | 代码中版本号 | Git 标签 | 所在分支 | 说明 |
|------|------------|---------|---------|------|
| 开发中 | `0.1.0` | `v0.1.0-dev` | develop | 持续开发，功能陆续合并 |
| 发布 | `0.1.0` | `v0.1.0` | main | 合并到 main 后打正式标签 |
| 下一轮 | `0.2.0` | — | develop | 改版本号，开启新一轮开发 |

> [!NOTE]
> Phase 0 阶段 mj-agent `pyproject.toml` 中 `version = "0.1.0"`，与 develop 分支默认一致；Phase 1+ 引入正式发布流程后再启用本节区分。

---

## 4 版本号管理流程

### 4.1 版本号存在的文件位置

> [!IMPORTANT]
> mj-agent 当前 `pyproject.toml` 为唯一权威；其他承载版本号的文件待 Phase 1+ 引入。

| 文件 | 版本号位置 | 说明 |
|------|-----------|------|
| `pyproject.toml` | `version = "0.1.0"` | **唯一权威来源** |
| `README.md` | 标题中的版本号 | 项目文档（可选） |
| `CLAUDE.md` | 多处引用 | Claude Code 指导（手动更新） |

> [!NOTE]
> Phase 1+ 引入更多版本承载文件（如 `Dockerfile`、`docker-compose.yml`、`CHANGELOG.md`、`QUICK_STATUS_SUMMARY.txt`、`main.py` 等）后，本表会同步扩展。当前仅 3 个文件，无需批量更新脚本。

### 4.2 发布流程概览

mj-agent Phase 0 暂未引入版本发布流程；待 Phase 1+ 与 `docs/runbook/[RUNBOOK]_Release_Process.md`（Phase 0.5/1 启用）共同落地。

开发者核心职责（Phase 1+ 目标态）：

1. **开发阶段**：在 feature 分支的 `CHANGELOG.md [Unreleased]` 区块记录变更（Phase 0.5+ CHANGELOG 引入后）
2. **测试验证**：在测试机验证功能，在 GitHub Issue 更新验证状态

> [!NOTE]
> mj-agent 暂未引入批量更新脚本；版本号集中存于 `pyproject.toml`，发布时手工更新即可。Phase 1+ 引入更多版本承载文件后会同步建立脚本（参见 [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]] §Defer）。

---

## 5 验证清单

### 5.1 推送到 GitHub 后

- [ ] `git remote -v` → 确认 origin 指向 `https://github.com/MJ-AgentLab/mj-agent`
- [ ] `git remote -v` → 确认 gitee 指向 `https://gitee.com/ranzuozhou/mj-agent`
- [ ] `git branch -r` → 确认 main、develop 都在远程
- [ ] GitHub 网页确认仓库内容完整
- [ ] GitHub 网页确认 `.env` 文件**未出现**在仓库中
- [ ] GitHub → Settings → Branches → 确认分支保护规则已生效

### 5.2 团队成员首次加入

- [ ] Bare Repo + Worktree 初始化成功（见 §1.2 / §2 问题 2）
- [ ] `git checkout develop` 成功（或 `git worktree add develop develop`）
- [ ] `uv sync` 安装依赖成功
- [ ] `.env` 文件已创建（手动）
- [ ] `uv run langgraph dev` Studio 本地启动正常

### 5.3 版本发布后（Phase 1+ 启用）

- [ ] `main` 分支已合并最新 develop
- [ ] 正式标签已创建并推送（如 `v0.1.0`）
- [ ] develop 分支版本号已更新为下一版本

---

## 6 速查表

### Git 操作速查

| 操作 | 命令 |
|------|------|
| 克隆仓库 | `git clone https://github.com/MJ-AgentLab/mj-agent.git` |
| 添加 Gitee 镜像 remote | `git remote add gitee https://gitee.com/ranzuozhou/mj-agent.git` |
| 双推到 Gitee + GitHub | `git push gitee HEAD && git push origin HEAD` |
| 配置双推 alias | `git config alias.pushall '!git push gitee HEAD && git push origin HEAD'` |
| 查看所有标签 | `git tag -l "v*"` |
| 切到指定版本 | `git checkout v0.1.0` |
| 打标签 | `git tag -a v0.1.0 -m "描述"` |
| 推送标签 | `git push origin v0.1.0` |

### 版本号规则速查

| 变更类型 | 版本变化 | 示例 |
|----------|---------|------|
| 新功能 / 新 skill | MINOR +1 | 0.1.0 → 0.2.0 |
| Bug 修复 / 优化 | PATCH +1 | 0.1.0 → 0.1.1 |
| 破坏性变更 | MAJOR +1 | 0.1.0 → 1.0.0 |
| 热修复 | PATCH +1 | 0.1.0 → 0.1.1 |

---

## Troubleshooting

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `git push` 提示 `Permission denied` | 没有仓库写入权限 | 联系项目负责人添加 Collaborator 权限 |
| 分支保护规则未生效 | GitHub 设置未保存 | 重新检查 Settings → Branches |
| `pyproject.toml` 版本号未同步到 README/CLAUDE.md | 当前阶段需手工更新 | 手动搜索替换；Phase 1+ 引入脚本（见 §4.2 注） |

---

## 关联文档

- [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] — 分支模型、命名规范、操作流程
- [[GUIDE]_Git_Push_Workflow|Git 推送工作流]] — 推送前检查 + 推送流程
- [[GUIDE]_PR_Description_Convention|PR 描述规范指南]] — PR 模板使用
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] — 提交消息格式
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from 上游业务系统]] — 决策依据与 Keep/Adapt/Defer 矩阵
- [[../../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|上游业务系统 Git 规范在 mj-agent 的适配评估 v1.0]] — 适配证据
- CI/CD 发布流程手册 —— Phase 0.5/1 待 `docs/runbook/[RUNBOOK]_Release_Process.md` 启用，参见 ADR-010 §Defer
- 开发者上手指南 —— Phase 0.5 待 `docs/guide/[GUIDE]_Developer_Onboarding.md` 启用

---

## 更新记录

| 日期 | 版本 | 内容 |
|------|------|------|
| 2026-04-30 | v1.0 | 派生自 上游业务系统 v5.0 同名 GUIDE：仓库 URL 改 mj-agent；§4.1 文件清单缩减为 mj-agent Phase 0 实际（仅 pyproject.toml + README + CLAUDE.md）；删除 §5 bump-version.ps1 整段；§4.2 / §3 SemVer 标注 Phase 1+ 启用；保留双推 + 分支保护章节 |

---

> **参考资源**
>
> - [语义化版本规范 (SemVer)](https://semver.org/lang/zh-CN/)
> - [Git 分支模型 (Git Flow)](https://nvie.com/posts/a-successful-git-branching-model/)
