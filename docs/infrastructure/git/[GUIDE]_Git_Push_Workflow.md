---
type: guide
domain: SYS
summary: mj-agent Git 推送工作流 — 7 步推送前检查 + 双推 Gitee/GitHub + .gitignore 策略 + 可选 pre-push hook
tags:
  - guide
  - git
  - push
  - workflow
aliases:
  - mj-agent Git Push Workflow
  - mj-agent Git 推送工作流
created: 2026-04-30
updated: 2026-05-06
state: draft
version: v1.0
track: code
owner: 项目负责人
---

# mj-agent Git 推送工作流

> **适用范围**：mj-agent 开发人员完成编码和提交后、推送分支到远程仓库前的标准操作流程
> **目标受众**：开发
> **版本**：v1.0
> **最后更新**：2026-04-30
> **派生自**：mj-system v5.0 同名 GUIDE（推送流程逐字保留；§2 CHANGELOG / §10 Q6 按 mj-agent Phase 0 实际状态调整）
> **关联文档**：[[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]]、[[GUIDE]_PR_Description_Convention|PR 描述规范指南]]

---

## TL;DR

- **阅读时间**：~10 分钟
- **涵盖范围**：从 commit 质量检查到推送后验证的完整推送流程（7 个检查步骤 + 推送操作），包含推送前检查规范、`.gitignore` 策略和可选 pre-push hook
- **适用场景**：完成编码和提交后、准备将分支推送到远程仓库时

## Prerequisites

- **必备知识**：Git 基础操作（add、commit、push、pull）
- **必备知识**：项目分支模型（详见 [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]]）
- **必备知识**：Commit Message 格式（详见 [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]]）
- **建议了解**：GitHub CLI（`gh`）

---

## 目录

0. [适用场景](#0-适用场景)
1. [Commit 质量检查](#1-commit-质量检查)
2. [CHANGELOG 更新确认](#2-changelog-更新确认)
3. [工作目录干净检查](#3-工作目录干净检查)
4. [分支命名验证](#4-分支命名验证)
5. [远程分支同步](#5-远程分支同步)
6. [执行推送](#6-执行推送)
7. [推送后验证](#7-推送后验证)
8. [下一步 — 创建 PR](#8-下一步--创建-pr)
9. [速查清单](#9-速查清单)
10. [常见问题](#10-常见问题)

---

## 0 适用场景

本指南覆盖从编码完成到 PR 创建之间的"推送分支"阶段。在整个开发流程中的位置如下：

```text
Issue → 创建分支 → 编码 → 自测 → 提交 → ★ 推送 → 创建 PR → Review → 合并
                                          ^^^^^^^^
                                         本指南范围
```

> [!NOTE]
> 适用分支类型
> 本指南适用于所有从 `develop` 创建的临时分支：`feature/*`、`bugfix/*`、`documentation/*`、`maintain/*`。
> `hotfix/*` 分支同样适用，但基准分支为 `main` 而非 `develop`（同步步骤需调整）。

在执行本指南之前，你应该已经完成了：

| 前置步骤 | 参考文档 |
|---------|---------|
| 创建开发分支 | [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] |
| 本地开发与自测 | `uv run pytest tests/unit` / `uv run ruff check` / `uv run mypy src/mj_agent`；完整流程见 [[../../guide/[GUIDE]_Developer_Onboarding\|开发者上手指南]] |
| 提交代码 | [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] |
| 更新 CHANGELOG.md | 本指南 [[#2 CHANGELOG 更新确认]] |

---

## 1 Commit 质量检查

推送前先检查提交质量，避免不规范的 commit 进入远程仓库。

### 1.1 检查 Commit Message 格式

查看当前分支上的所有提交：

```bash
git log --oneline develop..HEAD
```

逐条确认每个 commit message 是否符合 `<type>(<scope>): <summary>` 格式。快速检查要点：

| 规则 | 正确示例 | 错误示例 |
|------|---------|---------|
| type + scope 小写 | `feat(skill):` | `feat(SKILL):` |
| `:` 后一个空格 | `feat(skill): 新增` | `feat(skill):新增` |
| 摘要不以句号结尾 | `新增 metrics-glossary skill` | `新增 metrics-glossary skill。` |
| header 不超过 72 字符 | — | 过长的摘要 |

> 完整格式规范详见 [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] §2。

### 1.2 检查 Commit 类型与分支类型一致性

确认分支中的 commit 类型符合该分支类型的允许范围：

| 分支类型 | 允许的 Commit 类型 |
|---------|-------------------|
| `feature/*` | `feat`, `perf`, `refactor`, `test`, `docs` |
| `bugfix/*` | `fix`, `test`, `docs` |
| `documentation/*` | `docs` |
| `maintain/*` | `infra`, `docs` |
| `hotfix/*` | `fix` |

例如：`documentation/*` 分支中不应出现 `feat` 或 `fix` 类型的 commit。

> 详见 [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] §3。

### 1.3 检查提交拆分合理性

确认每个 commit 是一个**逻辑完整、可独立理解**的变更单元。常见的拆分问题：

- 一个 commit 混合了不相关的变更（如 skill 代码 + db 配置）
- 修改同一模块的紧密关联文件被拆成了过多 commit

> 拆分指南详见 [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] §6。

### 1.4 修复不规范的 Commit

如果发现最近一条 commit message 有误：

```bash
# 修改最后一条 commit message（仅限尚未推送的 commit）
git commit --amend -m "<type>(<scope>): <修正后的摘要>"
```

> [!WARNING]
> `--amend` 会修改 commit 的 hash。如果该 commit 已推送到远程，需要 `git push --force-with-lease`（仅限个人开发分支）。

---

## 2 CHANGELOG 更新确认

开发过程中应在 `CHANGELOG.md` 的 `[Unreleased]` 区块下记录变更。`CHANGELOG.md`
已就位（PLAN G PR4 落地，2026-05-06）；推送前必须确保本节流程被执行。

### 2.1 哪些变更需要记录

| Commit Type | CHANGELOG 分类 | 是否记录 |
|-------------|---------------|---------|
| `feat` | `### Added` | 必须记录 |
| `fix` | `### Fixed` | 必须记录 |
| `perf` | `### Changed` | 必须记录 |
| `refactor` | `### Changed` | 用户可感知的重构需记录 |
| `infra` | `### Added` 或 `### Changed` | 显著的基础设施变更需记录 |
| `docs` | — | 通常不记录 |
| `test` | — | 不记录 |

### 2.2 验证 CHANGELOG 已更新

```bash
# 查看 CHANGELOG 相对于 develop 的差异
git diff develop -- CHANGELOG.md
```

如果输出为空但本次变更包含 `feat` 或 `fix` 类型的 commit，说明遗漏了 CHANGELOG 更新。

> [!WARNING]
> 补充 CHANGELOG
> 如果发现 CHANGELOG 未更新，创建一条额外的 commit：
> ```bash
> # 编辑 CHANGELOG.md，在 [Unreleased] 区块添加变更记录
> git add CHANGELOG.md
> git commit -m "docs: 补充 CHANGELOG 变更记录"
> ```

---

## 3 工作目录干净检查

推送前必须确认所有应提交的文件都已纳入 commit，防止文件遗漏。

### 3.1 核心原则

> [!IMPORTANT]
> 推送前 `git status --short` 必须为空
> 要么文件已提交，要么已被 `.gitignore` 排除。

### 3.2 问题根因

典型的遗漏场景：

```text
开发完成 → git add <部分文件> → git commit → git push
                                     ↑
                              其余修改仍在工作目录，未被发现
```

**根本原因**：提交后未检查 `git status`，未确认工作目录是否干净。

**加重因素**：`.claude/settings.local.json` 等本地配置始终显示为修改状态，产生视觉噪音，使开发者习惯性忽略 `git status` 输出。

### 3.3 检查流程

```text
git status --short
    │
    ├── 输出为空 → 可以继续
    │
    └── 有输出 → 逐项确认
                    │
                    ├── 应提交的文件 → git add + commit
                    ├── 应忽略的文件 → 加入 .gitignore
                    └── 临时文件 → 手动清理
```

### 3.4 操作示例

```bash
# 1. 检查工作目录状态
git status --short

# 2. 如果有输出，分析每个文件
#    M  = 已修改未暂存
#    ?? = 未追踪
#    A  = 已暂存

# 3. 处理完毕后，再次确认为空
git status --short
```

### 3.5 .gitignore 排除干扰文件

将不应纳入版本控制的本地文件加入 `.gitignore`，使 `git status` 输出仅包含真正需要关注的文件。

#### 已排除的文件

```gitignore
# ========== Claude Code 本地配置 ==========
.claude/settings.local.json
```

#### 排除原则

| 应排除 | 不应排除 |
|--------|----------|
| 含本地机器路径的配置 | `.claude/settings.json`（团队共享配置） |
| IDE 个人偏好设置 | 项目级 IDE 配置 |
| 运行时生成的数据文件 | 源代码、文档、SQL 脚本 |
| 敏感信息（`.env`、密钥） | 环境模板（`.env.example`） |

#### 已从 Git 追踪中移除的操作

```bash
# 如果文件已被 Git 追踪，需先移除缓存再提交
git rm --cached .claude/settings.local.json
git add .gitignore
git commit -m "infra(ci): 将 .claude/settings.local.json 加入 .gitignore"
```

> [!TIP]
> Claude Code 协作规则
> 在 `CLAUDE.md` 中可加入以下规则，确保 Claude Code 在辅助提交时自动执行检查：
> - 每次 `git push` 前必须先执行 `git status --short`，确认工作目录为空
> - 如有残留修改，逐项确认是否应纳入当前提交
> - 不得提交 `.gitignore` 中列出的文件
> - 提交后立即执行 `git status --short` 验证

---

## 4 分支命名验证

推送前确认分支名符合项目命名规范，因为分支名推送到远程后修改成本较高。

### 4.1 查看当前分支名

```bash
git branch --show-current
# 输出示例：feature/12-metrics-glossary-skill
```

### 4.2 命名格式

```text
<类型>/<issue-id>-<描述>      # 关联 Issue 时
<类型>/<描述>                  # 无关联 Issue 时
```

合法的类型：`feature`、`bugfix`、`documentation`、`maintain`、`hotfix`

### 4.3 常见命名问题

| 问题 | 错误示例 | 正确示例 |
|------|---------|---------|
| 类型拼写错误 | `feat/skill-author` | `feature/skill-author` |
| 使用大写 | `Feature/Skill-Author` | `feature/skill-author` |
| 使用空格 | `feature/skill author` | `feature/skill-author` |
| 缺少类型前缀 | `skill-author` | `feature/skill-author` |

> 完整命名规范详见 [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] §2。

### 4.4 修正分支名

如果分支**尚未推送到远程**，可以直接重命名：

```bash
git branch -m <旧名> <新名>
# 例如：git branch -m feat/skill-author feature/12-skill-author
```

---

## 5 远程分支同步

推送前将基准分支的最新内容合并到你的分支，减少后续 PR 合并时的冲突。

### 5.1 获取远程最新状态

```bash
git fetch origin
```

### 5.2 合并基准分支

```bash
# 普通分支（feature / bugfix / documentation / maintain）
git merge origin/develop

# hotfix 分支
git merge origin/main
```

### 5.3 处理合并冲突

如果出现冲突：

1. `git status` 查看冲突文件列表
2. 在 VS Code / Cursor 中逐个解决冲突
3. `git add .` 标记已解决
4. `git commit -m "merge: 合并 develop 最新内容，解决冲突"`

如果冲突过于复杂，可以取消合并：

```bash
git merge --abort
```

> 详细的冲突解决方法见 [[../../guide/[GUIDE]_Developer_Onboarding|开发者上手指南]]。

> [!TIP]
> 在功能开发周期中**定期同步** develop 分支（而非仅在推送前），可以显著减少冲突规模。

---

## 6 执行推送

完成以上所有检查后，执行推送操作。

### 6.1 首次推送（设置上游跟踪）

```bash
git push -u origin <分支名>
# 例如：git push -u origin feature/12-metrics-glossary-skill
```

`-u`（即 `--set-upstream`）会将本地分支与远程分支建立跟踪关系，后续推送只需 `git push` 即可。

### 6.2 后续推送

如果已设置上游跟踪，直接推送：

```bash
git push
```

### 6.3 Worktree 环境注意事项

本项目使用 Bare Repo Worktree 结构（详见 [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] §6）。**推送前必须在正确的 worktree 子目录中执行** —— `mj-agent/` 根目录是 bare repo，没有工作树，在根目录执行 `git push` 会失败。

```bash
# 确认当前目录和分支
git worktree list          # 列出所有 worktree 及其路径
pwd                        # 确认当前目录
git branch --show-current  # 确认当前分支

# 正确：从 worktree 子目录推送
cd mj-agent/feature/12-metrics-glossary-skill
git pushall

# 错误：从 bare repo 根目录推送（会失败）
# cd mj-agent   ← 根目录无工作树，git push 报错
```

### 6.4 常见推送错误

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `rejected - non-fast-forward` | 远程分支有你本地没有的提交 | 先执行 [[#5 远程分支同步]] |
| `fatal: The current branch has no upstream` | 首次推送未设置上游 | 使用 `git push -u origin <分支名>` |
| `remote: Permission denied` | 没有仓库写入权限 | 检查 GitHub 访问权限，运行 `gh auth status` |
| `fatal: 'origin' does not appear to be a git repository` | remote 未配置 | 运行 `git remote -v` 检查 |
| `remote: Unauthorized` (Gitee) | Gitee 认证失败或 Token 过期 | 运行 `git remote -v` 确认 gitee remote URL 正确；检查本地 credential 是否已缓存过期的 Token |
| `fatal: not a git repository` / push 无反应 | 从 bare repo 根目录 (`mj-agent/`) 执行推送 | `cd` 进入对应 worktree 子目录（如 `mj-agent/develop/`）再推送 |

### 6.5 双推操作（Gitee + GitHub）

> [!IMPORTANT]
> 为什么需要双推
> 镜像仓库设置：mj-agent 同步推送到 Gitee（`gitee.com/ranzuozhou/mj-agent`）与 GitHub（`MJ-AgentLab/mj-agent`）。Phase 0 阶段 CI 仅 `python -m compileall`，但保持双推可让后续 Phase 1+ 引入 CI/CD 流水线（无法直接访问 GitHub 时改从 Gitee 拉）时无需追溯历史。

#### 配置 Gitee remote（首次）

```bash
# 添加 Gitee 镜像作为第二个 remote
git remote add gitee https://gitee.com/ranzuozhou/mj-agent.git

# 验证 remote 配置
git remote -v
# 应看到 origin (GitHub) 和 gitee (Gitee) 两个 remote
```

#### 推送流程

每次推送时，**先推 Gitee 再推 GitHub**：

```bash
# 手动双推
git push gitee HEAD && git push origin HEAD
```

#### 使用 alias 简化

配置一次即可永久使用：

```bash
git config alias.pushall '!git push gitee HEAD && git push origin HEAD'

# 此后使用一条命令完成双推
git pushall
```

> [!TIP]
> 首次推送新分支
> 新分支首次推送时需要设置上游跟踪：
> ```bash
> git push -u gitee <分支名> && git push -u origin <分支名>
> ```
> 后续推送使用 `git pushall` 即可。

---

## 7 推送后验证

推送成功后，确认远程仓库状态正确。

### 7.1 确认远程分支存在

```bash
git ls-remote --heads origin <分支名>
# 应返回该分支的 commit hash
```

### 7.2 确认提交完整

```bash
git log origin/<分支名> --oneline -5
# 确认所有预期的 commit 都已推送
```

### 7.3 GitHub 网页验证（可选）

使用 GitHub CLI 快速打开仓库页面：

```bash
gh browse
```

在 GitHub 网页上确认分支和提交记录可见。

---

## 8 下一步 — 创建 PR

分支推送成功后，下一步是创建 Pull Request。根据分支类型选择 PR 目标分支：

| 分支类型 | PR 目标分支 |
|---------|-----------|
| `feature/*`、`bugfix/*`、`documentation/*`、`maintain/*` | `develop` |
| `hotfix/*` | `main` |

使用 `gh` CLI 创建 PR：

```bash
gh pr create \
  --base develop \
  --head <分支名> \
  --reviewer "<项目负责人 GitHub 用户名>"
```

> 完整 PR 流程见 [[GUIDE]_PR_Description_Convention|PR 描述规范指南]]。

---

## 9 速查清单

每次推送前按此清单逐项确认：

- [ ] `git log --oneline develop..HEAD` — Commit message 格式正确
- [ ] Commit 类型与分支类型一致
- [ ] `git diff develop -- CHANGELOG.md` — CHANGELOG 已更新
- [ ] `git status --short` — 输出为空
- [ ] `git branch --show-current` — 分支名符合规范
- [ ] `git fetch origin && git merge origin/develop` — 已同步基准分支
- [ ] `git push gitee HEAD && git push origin HEAD` — 已双推到 Gitee + GitHub
- [ ] `git log origin/<分支名> --oneline -3` — 远程提交已确认

---

## 10 常见问题

### Q1：推送后发现遗漏了文件怎么办？

补充提交并再次推送：

```bash
git add <遗漏的文件>
git commit -m "<type>(<scope>): 补充遗漏的文件"
git push
```

> 为避免此问题，推送前务必执行 [[#3 工作目录干净检查]]。

### Q2：推送后发现 commit message 有误怎么办？

如果是最后一条 commit 且**仅你自己在使用该分支**：

```bash
git commit --amend -m "<type>(<scope>): 修正后的摘要"
git push --force-with-lease
```

> [!WARNING]
> `--force-with-lease` 仅在个人开发分支上使用，切勿在 `main` 或 `develop` 上使用。

### Q3：首次推送提示 "no upstream branch" 怎么办？

使用 `-u` 标志设置上游跟踪：

```bash
git push -u origin <分支名>
```

### Q4：Worktree 环境下推送到了错误的分支怎么办？

1. 使用 `git worktree list` 确认各目录对应的分支
2. 切换到正确的 worktree 目录
3. 在正确目录中执行推送

> [!TIP]
> 推送前执行 `git branch --show-current` 确认当前分支名。

### Q5：为什么需要双推？忘了推 Gitee 怎么办？

**为什么需要双推**：保持 Gitee 镜像与 GitHub 一致。Phase 0 阶段 CI 仅 `python -m compileall`，未触发跨平台 fetch；但 Phase 1+ 引入 CI/CD 流水线时若需从 Gitee 拉，缺失的提交将无法构建。

**忘了推 Gitee 的补救**：

```bash
# 补推到 Gitee
git push gitee HEAD

# 如果是新分支且未设置过 Gitee 上游
git push -u gitee <分支名>
```

> [!TIP]
> 配置 `git pushall` alias 后始终使用 `git pushall` 代替 `git push`，避免遗漏。详见 [[#65-双推操作gitee-github]]。

### Q6：如何用 Git Pre-push Hook 自动化检查？（可选）

可以安装 pre-push hook 实现推送前自动检查未提交文件，有未提交文件时发出警告。

#### 安装

将以下内容写入 `.git/hooks/pre-push`（需 `chmod +x`）：

```bash
#!/bin/bash
# .git/hooks/pre-push — 推送前检查未提交文件

UNCOMMITTED=$(git status --porcelain)

if [ -n "$UNCOMMITTED" ]; then
    echo ""
    echo "======================================"
    echo "  Warning: 发现未提交的修改"
    echo "======================================"
    echo ""
    git status --short
    echo ""
    echo "请确认这些文件是否应纳入提交。"
    echo "继续推送？(y/N)"
    read -r answer < /dev/tty
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        echo "推送已取消。"
        exit 1
    fi
fi
```

#### Windows 注意事项

- Git for Windows 使用 MSYS2 环境，hook 脚本使用 bash 语法即可
- 文件路径：`<worktree-root>/.git/hooks/pre-push`（worktree 的 `.git` 是文件而非目录，hook 需放在主仓库的 `.git/hooks/` 中）
- 如使用 Git Worktree，所有 worktree 共享主仓库的 hooks

#### Hook 生效范围

| 场景 | Hook 是否生效 |
|------|---------------|
| `git push` | 生效 |
| `git push --no-verify` | 被跳过 |
| GitHub Desktop 推送 | 取决于客户端实现 |
| CI/CD 自动推送 | 不适用 |

---

## 关联文档

- [[GUIDE]_Git_Branch_Strategy|Git 分支策略指南]] — 分支模型、命名规范、操作流程
- [[GUIDE]_GitHub_Setup_And_Versioning|GitHub 设置与版本管理]] — 仓库配置与版本号管理
- [[GUIDE]_PR_Description_Convention|PR 描述规范指南]] — PR 模板使用
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]] — 提交消息格式
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from mj-system]] — 决策依据
- [[../../guide/[GUIDE]_Developer_Onboarding|开发者上手指南]] —— mj-agent 新成员端到端上手路径
- CI/CD 发布流程手册 —— Phase 0.5/1 待 `docs/runbook/[RUNBOOK]_Release_Process.md` 启用，参见 ADR-010 §Defer

---

## 更新记录

| 日期 | 版本 | 内容 |
|------|------|------|
| 2026-04-30 | v1.0 | 派生自 mj-system v5.0 同名 GUIDE：推送流程逐字保留；§2 CHANGELOG 章节加注 Phase 0.5+ 启用；§10 删除 Q6（Gitee shallow fetch），原 Q7 重编号为 Q6；§6.5 双推说明改 mj-agent 实际（Phase 0 CI 仅 compileall） |
| 2026-05-06 | v1.0 (patch) | §0:84 / §6 冲突解决段 / §文末延伸阅读 — 三处 `Phase 0.5 待 docs/guide/[GUIDE]_Developer_Onboarding.md 启用` forward-reference 升级为 active wikilink（PLAN G PR2 落地）；非结构性补丁，version 不升 |
| 2026-05-06 | v1.0 (patch) | §2 删除 Phase 0.5+ 目标态 IMPORTANT 段头与 5 处「Phase 0.5+ 启用后」限定语；§2 流程从前瞻 stub 翻转为 active（PLAN G PR4 落地）；非结构性补丁，version 不升 |
