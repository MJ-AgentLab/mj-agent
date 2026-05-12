---
name: mj-agent-git-push
description: This skill should be used when the user asks to push code, run pre-push checks, set up dual-push to Gitee and GitHub, troubleshoot push errors, or handle CHANGELOG updates in mj-agent. Make sure to use this skill whenever the user says "推送代码", "push code", "git push", "推到远端", "push to remote", "dual push", "Gitee push", "推送失败", "push error", "CHANGELOG", "推送前检查", "pre-push check" in the mj-agent context. Runs an 8-item pre-push checklist and executes dual-push (Gitee first, GitHub second). Do not use for: commit creation (use mj-agent-git-commit), PR creation (use mj-agent-git-pr), force-push of an amended commit (handle directly via git push --force-with-lease), or branch deletion after merge (use mj-agent-git-delete in PR-B3+).
---

# mj-agent Git Push

## Overview

8 步 pre-push checklist + 双推（Gitee first, GitHub second）执行 for mj-agent。CI Runner 默认从 Gitee 拉镜像（与 mj-system 一致策略），因此两个 remote 必须都收到 push。

> **前置技能**：`/mj-agent-git-commit` 已在提交阶段验证 commit message 格式 + type/branch 纪律。本技能 Step 1-2 是二次确认。

**Workflow position**: Stage 13 of HITL_Prompt 17-stage flow.

详细 push 流程见 [[../../../docs/infrastructure/git/[GUIDE]_Git_Push_Workflow|Git_Push_Workflow GUIDE]]（mj-agent v1.0；本 SKILL 是其交互式封装）。

## Pre-Push Checklist（按顺序）

```bash
# 1. Commit message 格式检查
git log --oneline develop..HEAD
# 验证每行：<type>(<scope>): <summary> — 小写、冒号后空格、不以句号结尾、≤72 字符

# 2. Commit type 与 branch type 匹配（5 branch × 7 type 矩阵）
# feature/* → feat / perf / refactor / test / docs
# bugfix/*  → fix / test / docs
# documentation/* → docs（仅）
# maintain/* → infra / docs
# hotfix/*  → fix（仅）
# 不匹配 → git commit --amend 或 interactive rebase 修正后再 push

# 3. CHANGELOG 检查
git diff develop -- CHANGELOG.md
# 输出空 + 有 feat / fix commits = 缺 CHANGELOG 更新
# 修复：编辑 CHANGELOG.md [Unreleased] block → git add CHANGELOG.md → git commit -m "docs: 补充 CHANGELOG"

# 4. 工作目录干净
git status --short
# 必须为空。否则用 /mj-agent-git-commit 暂存提交，或加 .gitignore

# 5. 分支命名验证
git branch --show-current
# 必须匹配：<type>/<desc> 或 <type>/<issue-id>-<desc>；type ∈ 5 类

# 6. 同步 base branch（详见 /mj-agent-git-sync，PR-B3 落地）
git fetch origin && git merge origin/develop   # feature/bugfix/documentation/maintain
git fetch origin && git merge origin/main      # hotfix/* only
# 冲突 → git status → 解 → git add . → git commit -m "merge: 合并 origin/develop 解决冲突"

# 7. 双推执行
# 首次 push（需 -u 设 upstream）：
git push -u gitee <branch> && git push -u origin <branch>
# 后续 push（推荐 alias）：
git pushall

# 8. 确认远程收到
git log origin/<branch> --oneline -3
git log gitee/<branch> --oneline -3
```

## CHANGELOG 更新规则

| Commit Type | CHANGELOG Section | 是否记录 |
|---|---|---|
| `feat` | `### Added` | **必记** |
| `fix` | `### Fixed` | **必记** |
| `perf` | `### Changed` | **必记** |
| `refactor` | `### Changed` | 仅当 user-visible |
| `infra` | `### Added` 或 `### Changed` | 仅当显著 infra 变更 |
| `docs` | — | 跳过 |
| `test` | — | 跳过 |

条目加在 `## [Unreleased]` block 下。Phase A / B 的 docs 类 PR 默认不更新 CHANGELOG（按 §6.2 规则）。

## Dual-Push Setup（一次性）

```bash
# 检查 gitee remote 是否存在
git remote -v

# 添加 gitee remote（如缺）
git remote add gitee https://gitee.com/ranzuozhou/mj-agent.git

# 配置 pushall alias
git config alias.pushall '!git push gitee HEAD && git push origin HEAD'

# 首次 push 新分支（需 -u 设 upstream）
git push -u gitee <branch> && git push -u origin <branch>

# 后续 push
git pushall
```

**顺序强制**：Gitee first, GitHub second——CI Runner 默认从 Gitee 拉。

## Worktree Validation

**Push 必须在 worktree 内执行**——`mj-agent/` 根是 bare repo 无 working tree，root 执行 push 会失败。

```bash
# Push 前确认在正确 worktree：
git worktree list
pwd
git branch --show-current

# 正确：在 worktree 内 push
cd D:/workspace/10-software-project/projects/mj-agent/feature/63-add-flow-intake-skill
git pushall

# 错误：bare repo 根目录 push（会失败）
# cd D:/workspace/10-software-project/projects/mj-agent   ← 这里 push 会失败
```

## Force Push（amend 后）

```bash
# 仅在个人开发分支用，永远不在 main / develop 上
git commit --amend -m "<corrected message>"
git push --force-with-lease   # 比 --force 安全（检查远程未被他人改）
```

## Common Errors

| 错误 | 原因 | 修复 |
|---|---|---|
| `rejected - non-fast-forward` | 远程有你没有的 commit | Step 6: fetch + merge |
| `fatal: no upstream branch` | 首次 push 没加 `-u` | `git push -u gitee <branch> && git push -u origin <branch>` |
| `remote: Permission denied` | 没写权限 | `gh auth status`，检查 GitHub 权限 |
| `remote: Unauthorized`（Gitee） | Gitee token 过期 | 检查凭据管理器，重新认证 |
| `error: src refspec ... does not match any` | 分支不在远程 | 加 `-u` 设 upstream |

## 人工介入场景（STOP & ASK）

| # | 触发条件 | skill 行为 |
|---|---|---|
| H1 | Commit message 格式不规范 | 列出问题行 + 建议 amend |
| H2 | Type/branch 不匹配 | 重定向到 `/mj-agent-git-commit` H3 流程 |
| H3 | CHANGELOG 缺更新且本 PR 含 feat/fix | 询问：(1) 加 CHANGELOG 后再 push (2) 跳过（仅 docs PR） |
| H4 | 工作目录有未提交变更 | 重定向到 `/mj-agent-git-commit` |
| H5 | base branch 远程有 diverge | 触发 sync 流程；冲突时强制 HITL |
| H6 | 远程 push 失败（H1-permission / H2-token-expired） | 显示错误 + 修复指引 |
| H7 | 用户要求 force-push 到 main / develop | **硬性阻断**：保护分支不允许 force-push |

## Anti-patterns

- **不要** force-push 到 `main` / `develop`（H7 硬性阻断）
- **不要** 跳过 Gitee push（CI Runner 拉不到代码会跑失败）
- **不要** 在 bare repo 根 push（会失败；必须 cd 进 worktree）
- **不要** 在 push 前忘记跑 Level A 验证（Stage 10）—— `uv run ruff check` + `uv run mypy src/mj_agent` 失败 push 后 CI 会红
- **不要** 用 `git push --force` 不加 `--force-with-lease`（覆盖他人修改风险）

## Handoff to mj-agent-git-pr

```
推送完成
下一步：使用 `/mj-agent-git-pr` 创建 Pull Request。
  已验证项：commit format ✓、type/branch ✓、CHANGELOG ✓、dual push ✓
  待执行项：选 PR template、填 PR body、--body-file 创建 PR
```

## Detailed → docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md

完整流程（含 .gitignore 策略 / 可选 pre-push hook / 全部 troubleshooting）见 [[../../../docs/infrastructure/git/[GUIDE]_Git_Push_Workflow|Git_Push_Workflow GUIDE]]。本 SKILL 是其交互式封装。
