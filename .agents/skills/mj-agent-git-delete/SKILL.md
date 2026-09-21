---
name: mj-agent-git-delete
description: "适用于 mj-agent 的删worktree/branch/已合并清理。输入：分支tip、绝对路径、dirty、合并证据、双remote范围。流程：目标→fetch状态→范围→H1/H2/H3→顺序删除→摘要。输出：逐目标已删/保留/未知状态，恢复tip及未提交备份说明。Use when：准备清理已合并feature worktree和分支。Do not use for：删除develop以节省空间；拒绝保护分支删除。授权：main/develop拒绝；删除/force需具体批准与可用路线；聊天批准不自动解锁 hook。独立调用完成后结束，委派返回调用者；不自动跨阶段、提交或发布外部消息。"
---


# mj-agent Git Delete

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。独立调用只完成本技能；委派时记录调用者与返回阶段，同阶段必要校验完成后返回。下游 Handoff 均为建议，不能自动跨阶段或发布。受保护动作先完成可审阅草案；Owner 批准与宿主执行能力分开，hook 硬阻断时返回 `BLOCKED_EXECUTION_ROUTE`。


## 触发与职责详述

This skill should be used when the user asks to delete branches, remove worktrees, or clean up after a PR merge in mj-agent. Make sure to use this skill whenever the user says "删除分支", "清理分支", "branch cleanup", "delete branch", "worktree remove", "PR 合并后清理", "分支已合并", "Stage 17 sub", "post-merge cleanup", "remove worktree" in the mj-agent context. Enforces correct deletion order (worktree then local branch then optional remote with dual-remote gitee+origin) with safety checks and human confirmation for all destructive steps; protects main + develop from deletion. Do not use for: hotfix→develop sync (use mj-agent-git-sync), full post-merge cleanup orchestration (use mj-agent-flow-post-merge which sub-calls this skill), or branch creation (use mj-agent-git-branch).


## Overview

删除 mj-agent 中的 Git 分支，支持 Bare Repo Worktree 模式下的安全清理。删除是不可逆，每个关键节点需 user 确认。**Stage 17 sub** of HITL_Prompt 17-stage 闭环。

## 快速开始（交互模式）

### Step 0 — 确认分支名

若用户未提供：

```bash
git worktree list
```

询问"要删除哪个分支？"

### Step 0.5 — 同步远程状态（自动）

```bash
git fetch origin --prune
git fetch gitee --prune 2>/dev/null || true
```

> 目的：确保本地远程追踪最新，避免过期状态误判合并情况。

### Step 1 — 确认删除范围（人工，必填）

询问选 1/2/3：

> **1. 仅本地**：移 worktree + 删本地分支（保留远程；适合 PR 已合并 + 平台 auto-delete-on-merge 已删远程）
>
> **2. 仅远程**：删 gitee + origin 远程，保留本地 worktree + 分支
>
> **3. 本地及远程**：完整清理 — 本地 worktree + 本地分支 + 双端远程
>
> （hotfix 分支合并后建议选 **3**，需完整清理）

## 命令序列

### 选项 1：仅本地

```bash
# 必须在其他 worktree 内执行（如 develop/），不能在被删 worktree 内
git worktree remove ../<type>/<desc>
git branch -d <type>/<desc>
```

> 若 `git branch -d` 报错（含未合并提交）→ **H2**

### 选项 2：仅远程

```bash
git push gitee --delete <type>/<desc>
git push origin --delete <type>/<desc>
```

### 选项 3：本地及远程（完整清理）

```bash
# Step 1: 移 worktree
git worktree remove ../<type>/<desc>

# Step 2: 删本地分支
git branch -d <type>/<desc>

# Step 3: 删双端远程（对应双推顺序）
git push gitee --delete <type>/<desc>
git push origin --delete <type>/<desc>
```

> **错误恢复（选项 3）**：
> - 三个 Step 按序执行；**先对账，只有独立且授权仍有效的后续动作可以继续**
> - Step 1 worktree remove 元数据移除但目录残留（Windows 文件锁常见）：记路径与元数据现状；确认独立分支/远端删除仍获授权才继续，绝不自动递归清目录
> - Step 2 触 H2 → 按 H2 流程后继续 Step 3
> - Step 3 触 H4 → 按 H4 流程
> - 最终输出清理摘要：

```
清理摘要：
✅ Step 1: worktree 已移除（⚠️ 目录残留需手动: <path>）
✅ Step 2: 本地分支已删除
✅ Step 3: 远程分支已删除（gitee ✅ / origin ✅）
```

## 人工介入场景（STOP & ASK）

| # | 触发 | 行为 |
|---|---|---|
| **H1** | `git status` 显示未提交修改 | ⚠️ 展示 status，询问"修改将永久丢失，确认继续？" |
| **H2** | `git branch -d` 报错（含未合并提交） | ⚠️ 先 `git log -1 --format=%H <branch>` 取 tip commit；再 `git branch -r --contains <tip-commit> \| grep origin/develop` 查远程是否已合并。**已合并**：告知"提交已通过 PR 合并到 origin/develop，本地未同步导致误报，可安全 `-D`"；`-D` 仍需明确批准和可用执行路线。**未合并**：展示错误，询问"未合并提交，是否 `-D` 强制删除？提交将永久丢失。" |
| **H3** | 当前 shell 在被删 worktree 目录 | 🚫 暂停，告知 `cd ../develop` 后再继续 |
| **H4** | 远程分支不存在（push --delete 失败） | ℹ️ 告知远程不存在，询问"继续完成本地清理？" |

> **原则**：删除不可逆，有不确定性应先暂停。

## 安全规则

1. **禁止删受保护分支**：`main` 和 `develop` 不可删，触发时直接拒绝
2. **执行位置**：`git worktree remove` 必须在其他 worktree 内执行（→ H3）
3. **`-d` vs `-D`**：已合并用 `-d`（安全）；有未合并提交时才用 `-D` + H2 确认

## 示例

```bash
# 用户：帮我删 documentation/phase-b3a-flow-completion 分支

# Step 0
git worktree list
# D:/workspace/.../mj-agent/.bare        (bare)
# D:/workspace/.../mj-agent/develop      [develop]
# D:/workspace/.../mj-agent/documentation/phase-b3a-flow-completion  [documentation/phase-b3a-flow-completion]

# Step 0.5（自动 fetch）
git fetch origin --prune

# Step 1: 询问 → 用户选"本地及远程"

# Step 2: 输出命令（从 develop/ 内执行）
cd D:/workspace/.../mj-agent/develop
git worktree remove ../documentation/phase-b3a-flow-completion
git branch -d documentation/phase-b3a-flow-completion
git push gitee --delete documentation/phase-b3a-flow-completion
git push origin --delete documentation/phase-b3a-flow-completion
```

## Anti-patterns

- **不要** 删 main / develop（受保护，直接拒绝）
- **不要** 在被删 worktree 内执行 worktree remove（H3）
- **不要** 用 `-D` 跳过 H2 确认（未合并提交永久丢失）
- **不要** 跳过 Step 0.5 远程状态同步（误判已合并）
- **不要** 在前置状态不明时盲目执行后续 Step；对账后只继续独立且获授权动作

## Reference Files

- `repo:sdd/workflows/execution-loop.md` §1（Stage 17 post-merge cleanup 在 17-stage loop 的位置；branch cleanup 触发依据）
- `repo:docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`（Branch lifecycle）
- `.agents/skills/mj-agent-flow-post-merge/SKILL.md`（Stage 17 主 orchestrator，Step 7 sub-call 本 skill）

## Handoff

```
分支清理完成 ✓
下一步：
- 如本任务还未结束 → 回到 develop / 其他 worktree 继续
- 如 hotfix 已合并 → mj-agent-git-sync（main → develop 回同步）
- 进下一任务 → 从 Stage 0 任务受理（sdd/workflows/execution-loop.md §4 映射表）起首
```
