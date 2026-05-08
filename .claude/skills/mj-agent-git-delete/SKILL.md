---
name: mj-agent-git-delete
description: This skill should be used when the user asks to delete branches, remove worktrees, or clean up after a PR merge in mj-agent. Make sure to use this skill whenever the user says "删除分支", "清理分支", "branch cleanup", "delete branch", "worktree remove", "PR 合并后清理", "分支已合并", "Stage 17 sub", "post-merge cleanup", "remove worktree" in the mj-agent context. Enforces correct deletion order (worktree then local branch then optional remote with dual-remote gitee+origin) with safety checks and human confirmation for all destructive steps; protects main + develop from deletion. Do not use for: hotfix→develop sync (use mj-agent-git-sync), full post-merge cleanup orchestration (use mj-agent-flow-post-merge which sub-calls this skill), or branch creation (use mj-agent-git-branch).
---

# mj-agent Git Delete

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
> - 三个 Step 按序执行；**每个失败不阻塞后续**
> - Step 1 worktree remove 元数据移除但目录残留（Windows 文件锁常见）：记提示，**继续 Step 2/3**
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
| **H2** | `git branch -d` 报错（含未合并提交） | ⚠️ 先 `git log -1 --format=%H <branch>` 取 tip commit；再 `git branch -r --contains <tip-commit> \| grep origin/develop` 查远程是否已合并。**已合并**：告知"提交已通过 PR 合并到 origin/develop，本地未同步导致误报，可安全 `-D`"+ 自动 `-D`。**未合并**：展示错误，询问"未合并提交，是否 `-D` 强制删除？提交将永久丢失。" |
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
- **不要** 在选项 3 错误时阻塞后续 Step（独立处理）

## Reference Files

- [[../../../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1.0|HITL_Prompt v1.0]] §4.15 Rule 2（branch cleanup 触发依据）
- [[../../../docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy|Git_Branch_Strategy]]（Branch lifecycle）
- `.claude/skills/mj-agent-flow-post-merge/SKILL.md`（Stage 17 主 orchestrator，Step 7 sub-call 本 skill）
- mj-system `.claude/skills/mj-sys-git-delete/SKILL.md`（直接派生源；mj-agent 改用 mj-agent 仓 path + 5 branch type）

## Handoff

```
分支清理完成 ✓
下一步：
- 如本任务还未结束 → 回到 develop / 其他 worktree 继续
- 如 hotfix 已合并 → /mj-agent-git-sync（main → develop 回同步）
- 进下一任务 → /mj-agent-flow-intake 起首
```
