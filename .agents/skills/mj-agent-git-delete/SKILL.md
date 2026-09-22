---
name: mj-agent-git-delete
description: "适用于 mj-agent 的删worktree/branch/已合并清理。输入：分支tip、绝对路径、dirty、合并证据、双remote范围。流程：目标→当前引用→范围→H1/H2/H3→顺序删除→摘要。输出：逐目标已删/保留/未知状态，恢复tip及未提交备份说明。Use when：准备清理已合并feature worktree和分支。Do not use for：删除develop以节省空间；拒绝保护分支删除。授权：main/develop拒绝；删除/force需具体批准与可用路线；聊天批准不自动解锁 hook。独立调用完成后结束，委派返回调用者；不自动跨阶段、提交或发布外部消息。"
---


# mj-agent Git Delete

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。独立调用只完成本技能；委派时记录调用者与返回阶段，同阶段必要校验完成后返回。下游 Handoff 均为建议，不能自动跨阶段或发布。受保护动作先完成可审阅草案；Owner 批准与宿主执行能力分开，hook 硬阻断时返回 `BLOCKED_EXECUTION_ROUTE`。


## 触发与职责详述

This skill should be used when the user asks to delete branches, remove worktrees, or clean up after a PR merge in mj-agent. Make sure to use this skill whenever the user says "删除分支", "清理分支", "branch cleanup", "delete branch", "worktree remove", "PR 合并后清理", "分支已合并", "Stage 17 sub", "post-merge cleanup", "remove worktree" in the mj-agent context. Enforces correct deletion order (worktree then local branch then optional remote with dual-remote gitee+origin) with safety checks and explicit approval for the exact destructive scope, reusing an existing approval while that scope and its contents remain unchanged; protects main + develop from deletion. Do not use for: hotfix→develop sync (use mj-agent-git-sync), full post-merge cleanup orchestration (use mj-agent-flow-post-merge which sub-calls this skill), or branch creation (use mj-agent-git-branch).


## Overview

删除 mj-agent 中的 Git 分支，支持 Bare Repo Worktree 模式下的安全清理。删除前必须取得具体目标和动作的明确批准；当前任务已批准且目标/内容未变化时复用批准，不逐节点重复确认或索取额外理由。**Stage 17 sub** of HITL_Prompt 17-stage 闭环。

## 快速开始（交互模式）

### Step 0 — 确认分支名

若用户未提供：

```bash
git worktree list
```

询问"要删除哪个分支？"

### Step 0.5 — 核对当前远程引用和合并证据

```bash
git ls-remote --refs --heads gitee refs/heads/<type>/<desc>
git ls-remote --refs --heads origin refs/heads/<type>/<desc>
```

> 查询失败保留错误并标 UNKNOWN，不能吞错当不存在。清单逐端列 repo/remote、精确引用、批准时及当前 tip 与合并证据。已有本地对象不足时标未知，不把旧 remote-tracking ref 当最新。真实 merge 核对覆盖提交；squash/rebase 核对实际 PR head、MERGED 状态和 base 中的 merge commit，不单凭祖先关系。两端 tip 不同、批准后更新、未合并或保护规则拒绝，暂停受影响项。

### Step 1 — 确认删除范围（人工，必填）

先检查当前任务是否已明确批准目标及以下范围；已明确则复用，不重复询问。仅缺少具体范围时询问选 1/2/3：

> **1. 仅本地**：移 worktree + 删本地分支（保留远程；适合 PR 已合并 + 平台 auto-delete-on-merge 已删远程）
>
> **2. 仅远程**：删 gitee + origin 远程，保留本地 worktree + 分支
>
> **3. 本地及远程**：完整清理 — 本地 worktree + 本地分支 + 双端远程
>
> （hotfix 分支合并后建议选 **3**，需完整清理）

远程引用删除是独立动作，普通 push、PR、merge 或仅本地清理批准不包含它；明确批准一端就只核验/处理该端，明确两端则复用该批准。保护 main/develop 及仓库其他明确保护分支。本地分支/worktree 已不存在时，从其他合法现有工作树继续核验远端，不自动重建目标或处理无关工作树。

只读清单辅助：`repo:scripts/sdd/check_git_actions.py` 的 `inspect_remote_deletion` / CLI 核对精确引用与期望 tip，返回 READY_FOR_REVIEW、CHANGED、REMOTE_TIPS_DIFFER、NOT_MERGED、MERGE_EVIDENCE_MISMATCH、PROTECTED、ALREADY_ABSENT 或 UNKNOWN。输入与输出不是授权凭证，PR 证据和其他保护分支须独立查实；CLI 仅采用本地祖先关系，squash/rebase 另由 API 接收已核实证据。

## 命令序列

### 选项 1：仅本地

```bash
# 必须在其他 worktree 内执行（如 develop/），不能在被删 worktree 内
git worktree remove ../<type>/<desc>
git branch -d <type>/<desc>
```

> 若 `git branch -d` 报错（含未合并提交）→ **H2**

### 选项 2：仅远程

以下命令每次只执行一端，经正常审批后成功查询该端引用。执行前已不存在记 ALREADY_ABSENT；执行后成功查询不存在才记 DELETED，失败/被拒/未执行/结果未知分别保留，不用查询失败证明删除。

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
> - 已知 prompt×never 阻断适用于两端时，不换 remote 试探：Gitee 记 REJECTED、origin 记 NOT_EXECUTED。重复“同意/继续”或仅网络/文件权限恢复不解除模式阻断；工程师恢复后先核对有效模式、授权、合并证据与两端 tip，只处理剩余项。响应丢失先查询对账，成功项不重复。
> - 最终输出清理摘要：

```
清理摘要：
本地：worktree 元数据 / 目录残留 / 分支各列实际状态和证据
Gitee：DELETED / ALREADY_ABSENT / REJECTED / FAILED / NOT_EXECUTED / UNKNOWN
origin：DELETED / ALREADY_ABSENT / REJECTED / FAILED / NOT_EXECUTED / UNKNOWN
计划：实际 state；文档提交：COMMITTED / UNCOMMITTED / UNKNOWN
其他任务：OUT_OF_SCOPE（不因本清理处置 #552 的 issue、旧 worktree 或未提交成果）
```

## 人工介入场景（STOP & ASK）

| # | 触发 | 行为 |
|---|---|---|
| **H1** | 有未提交、未跟踪或被忽略内容 | 展示目标状态与必要恢复来源；已审阅并明确批准同一内容时复用，否则仅暂停该项目并说明新增差异。未跟踪/被忽略不是可丢弃依据。 |
| **H2** | `git branch -d` 报错（含未合并提交） | 记录 tip 和原错，按 Step 0.5 的真实合并证据核对；不凭旧引用或单一祖先关系宣称安全。未覆盖内容暂停并展示差异；`-D` 仍需具名批准及可用路线，不在 #555 中默认使用。 |
| **H3** | 当前 shell 在被删 worktree 目录 | 🚫 暂停，告知 `cd ../develop` 后再继续 |
| **H4** | 远程删除失败、被拒或响应未知 | 保留原始错误并只读对账；成功查询后才判定不存在，查询失败记 UNKNOWN；已不存在不重复执行。已知共同审批阻断不换 remote，独立且已授权的本地工作可继续。 |

> **原则**：核验遵循共用执行边界；绝对路径、Git 状态、全部内容、必要备份、占用及重解析点逐项检查。不确定性只暂停受影响项，核验通过且已授权的删除由 Codex 通过正常工具完成；实际拒绝按原始证据定位，无法定位标未知，不改写命令或换工具重试。

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

# Step 0.5（两端查询，失败不得当不存在）
git ls-remote --refs --heads gitee refs/heads/documentation/phase-b3a-flow-completion
git ls-remote --refs --heads origin refs/heads/documentation/phase-b3a-flow-completion

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
- **不要** 跳过 Step 0.5 当前引用查询与合并证据核验（误判已合并）
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
