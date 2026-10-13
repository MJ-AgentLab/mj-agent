---
name: mj-agent-git-sync
description: 适用于 mj-agent 的开发期/热修回同步/同分支自更新。输入：branch/base、remote状态、dirty、模式。流程：precheck→模式→fetch→差异→merge按意图解冲突→验证。输出：目标ref纳入，冲突清零且工作树一致。Use when：同步origin/develop到当前feature分支。Do not use for：把已合并分支及worktree删掉；建议git-delete，不把sync当cleanup。授权：按任务范围复用，普通实现自主；安全/业务/权限/breaking/接受标准及门禁实质变化先Owner；技术拒绝不绕过。独立调用完成后结束，委派返回调用者；完整闭环已有授权时按检查点继续，不新增外部授权。
---



# mj-agent Git Sync

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。先核接受基线、任务授权及实际workspace/ref/SHA；基线内普通实施自主，实质安全/业务/权限/breaking/AC/gate变化先Owner决定。授权未撤销且目标/对象/环境/权限/风险未实质变化时复用，普通内容迭代仍核版本但不逐内容重批。技术拒绝保留原错并返回 `BLOCKED_EXECUTION_ROUTE`，不绕过。独立调用返回本范围结果；完整闭环已获授权时按检查点继续；委派返回协调者。


## 触发与职责详述

This skill should be used when the user asks to sync the latest develop or main changes into the current working branch, or sync main back to develop after a hotfix merge in mj-agent. Make sure to use this skill whenever the user mentions their branch is behind, has conflicts with develop, wants to update their branch, pulling or merging upstream changes, or says "同步分支", "拉取最新", "sync branch", "pull develop", "merge develop", "update branch", "rebase", "分支落后", "branch behind", "合并最新代码", "develop 有新代码", "branch outdated", "catch up with develop", "同步 main 到 develop", "hotfix 合并后同步", "sync main to develop", "自更新", "origin 有新提交", "协作者推了代码", "self-update" in the mj-agent context. Three modes: dev-time sync (work branch ← origin/develop), hotfix回sync (develop ← origin/main), self-update (any branch ← origin/<same>). Forces merge over rebase per project policy. Do not use for: branch creation (use mj-agent-git-branch), branch deletion (use mj-agent-git-delete), or push (use mj-agent-git-push).


## Overview

同步基线分支（develop / main）的最新代码到当前工作分支，或 origin 拉取同名分支远端提交。**侧循环辅助操作**，非线性链节点——branch→push 之间任意时刻多次调用。

```
branch → [开发] → sync ↻ → commit → push → pr → check-merge → delete
                     ↑          |
                     └──────────┘ (可多次调用)
```

**三模式**：
- **开发中同步**：工作分支（feature/bugfix/documentation/maintain/hotfix）拉基线
- **Hotfix 回同步**：在 develop 上把 main（含 hotfix）merge 回 develop 并推
- **自更新**：任何分支从 origin/<当前> 拉远端最新（多机器 / 协作者 / PR merged 后更新本地）

## 前置条件

- mj-agent worktree 内执行（bare repo 根无 work tree）
- `main` 上禁止跨分支合并（自更新 origin/main → main 例外）

## 快速开始（交互模式）

| 已知 | 行动 |
|---|---|
| "同步"未指定分支 | `git branch --show-current` 自动推导基线 |
| "rebase" | 告知项目用 merge 策略，引导 merge (H5) |
| 在 develop + 意图明确 | 进 hotfix 回同步 / 自更新 |
| 信息明确 | 直接执行 |

### 意图识别（概念区分）

- **自更新** = origin/<当前> → 本地（同名）；信号：origin / 远端 / 协作者 / 另一台机器
- **跨分支同步** = origin/<基线> → 本地（不同）；信号：develop / main / 基线 / 落后 / behind
- **意图模糊** = 无法区分时由 H-code 解决

## Sync Workflow（6 步）

### Step 0a — 工作树自检（防 bare worktree config 漂移，自动）

```bash
git rev-parse --is-inside-work-tree
```

- `true` → 继续 Step 0
- `false` → **H8**（worktree 缺 `config.worktree`，需先修复）

### Step 0 — 环境检测（三模式，自动）

```bash
git branch --show-current
git worktree list
```

**检测逻辑**：

```
意图 = 自更新 → 任何分支 → 自更新模式（base = origin/<current>）

意图 = 跨分支同步 →
  main → H4 硬阻断
  develop → Hotfix 回同步模式
  work branch → 开发中同步模式
    feature/bugfix/documentation/maintain → base = develop
    hotfix → base = main
    其他前缀 → H6 询问

意图 = Hotfix 回同步 → develop → Hotfix 回同步模式

意图 = 模糊 →
  main → H4a：自更新 or 取消
  develop → H4b（三选一）：自更新 / hotfix 回同步 / 取消
  work branch → Smart H7（数据驱动）
```

#### Smart H7 — 数据驱动路由

```bash
git fetch origin
SELF_GAP=$(git rev-list --count HEAD..origin/<current> 2>/dev/null || echo 0)
```

- origin/<current> 不存在 → 跳过自更新，直接跨分支同步
- SELF_GAP = 0 → 默认跨分支同步
- SELF_GAP > 0 → 询问"origin/<current> 有 N 远端提交。要：(1) 先拉远端再同步基线（推荐）/ (2) 仅同步基线 / (3) 仅拉远端 / (4) 取消"

> **Solo 开发者** SELF_GAP 几乎永远 0，H7 不触发；只有真协作者提交时才询问。

### Step 1 — 工作目录干净检查

```bash
git status --short
```

- 干净 → 继续
- 有修改 → **H1**（三选一：commit / stash / 取消）

### Step 2 — 远程最新

```bash
git fetch origin
```

> Smart H7 已 fetch 时跳过。

### Step 3 — 核对分歧与动作授权

```bash
git rev-list --count HEAD..origin/<base>      # 基线领先多少
git rev-list --count origin/<base>..HEAD      # 当前领先多少
git log --oneline HEAD..origin/<base>         # 即将合并的提交
```

- count = 0 → "已最新"，结束
- sync 授权、对象和风险未变化 → Step 4
- 缺授权/实质取舍 → 给 Owner 具体选项；显式取消 → 终止

### Step 4 — 执行合并

```bash
# 开发中同步
git merge origin/develop   # feature/bugfix/documentation/maintain
git merge origin/main      # hotfix

# Hotfix 回同步
git merge origin/main      # 在 develop 上

# 自更新
git merge origin/<current>
```

- 无冲突 → Step 5
- 有冲突 → **H2**（基线内保持双方意图自主解决；实质取舍由 Owner 决定）

### Step 5 — 同步后验证

```bash
git status --short
git log --oneline -3
```

**开发中同步**：
- 若 Step 1 stash → `git stash pop`（pop 冲突 → H3）
- Handoff："同步完成 ✓ 可继续开发，完成后 → mj-agent-git-commit → mj-agent-git-push"

**Hotfix 回同步**（额外）：
```bash
git pushall   # 推 develop 到 gitee + origin
```
- Handoff："hotfix 修复已同步到 develop 并推送 ✓"

**自更新**：
- main/develop/工作分支自更新 → **不**pushall（本地同步即可）
- H7 选(1)→ 自更新完后回 Step 3 跨分支同步
- Handoff："自更新完成 ✓（已从 origin/<branch> 拉最新）"

## 人工介入场景（STOP & ASK）

| # | 触发 | 行为 | 级别 |
|---|---|---|---|
| **H1** | git status 有未提交修改 | ⚠️ 三选：commit / stash / 取消 | Soft |
| **H2** | merge 冲突 | 基线内按双方意图自主解决；实质目标/风险取舍给 Owner 具体选项（详见 H2） | Conditional |
| **H3** | stash pop 冲突 | 核 stash 来源/未提交内容，按 H2a 保持双方意图自主解决；删除 stash 独立核具名授权 | Conditional |
| **H4** | 当前 main + 跨分支合并意图 | 🚫 硬阻断：main 不允跨分支 merge | Hard |
| **H4a** | main + 意图模糊 | ⚠️ "你在 main。要从 origin/main 拉最新（如 release PR 合并后）还是误操作？" 选 (1) 自更新 (2) 取消 | Soft |
| **H4b** | develop + 意图模糊 | ⚠️ 三选：(1) origin/develop 自更新 (2) Hotfix 回同步 main (3) 取消 | Soft |
| **H5** | 用户要 rebase | ℹ️ 引导 merge："项目统一 merge 策略（团队协作安全 / 历史一致 / 无 force push），改用 merge" | Info |
| **H6** | 分支前缀无法匹配 | ⚠️ "无法推导基线，确认 develop or main？" | Soft |
| **H7** | 工作分支 + 模糊 + SELF_GAP > 0 | ⚠️ 见 Smart H7（4 选项） | Soft |
| **H8** | Step 0a 返回 false（bare worktree config 漂移） | ⚠️ 三选：(1) 自动写 config.worktree 修复（推荐）(2) 手动按 mj-agent-git-branch §Bare Worktree Health Check 修复 (3) 取消 | Soft |

> sync 动作已具名授权且目标/风险未变化时不固定追加确认；缺动作授权或意图不明先核实。

### H2 冲突解决流程

> 基线内实现冲突由 Codex 自主解决并验证；涉及业务/安全/接受标准或目标取舍，由 Owner 决定受影响项。

1. 展示冲突概况：`git diff --name-only --diff-filter=U`
2. 核 sync 授权、真实双方版本与停止条件；存在未知或实质取舍时只暂停相关区域，其余已授权独立工作继续。
4. 逐文件读冲突区，分析双方语义（按 H2a「按意图」纪律），保持接受基线和双方意图，记录方案及理由。
5. 普通冲突自主修复并验证；只有实质目标/风险取舍或缺动作授权时，给 Owner 具体可行选项及推荐理由。Owner 显式选择 abort 时执行已授权退出操作。
6. 执行：`git add <files>` → `git commit -m "merge: 合并 <base> 最新内容，解决冲突"` → 交付前跑 Level A（H2a 第 4 点）

#### H2a 按意图解冲突纪律

> 借「resolving-merge-conflicts」思路、按 mj-agent native 承载（与 evidence-before-assertion + 留痕文化同构；正文工艺过 `repo:docs/rule/[STANDARD]_MJ_Agent_Skill_Authoring_Craft.md` §9）。**默认解冲突、按原始意图保真**——`git merge --abort` 是 user 显式选的安全出口，**不是 AI 默认动作**。

1. **先找 why**：每段冲突 hunk，读相关 commit message / 关联 PR / issue，弄清两侧改动各自**意图**（非只看语法谁覆盖谁）。
2. **保留双方意图**：能并存则并存；冲突时选**匹配本次 sync 目标**的一侧，merge commit body **文档化取舍**（选哪侧、为何）。
3. **绝不发明**：只解既有冲突，不引入两侧都没有的新行为。
4. **续行前跑 Level A**：解完（或 `git stash pop` 后）先跑 `uv run ruff check` / `uv run mypy src/mj_agent` / `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit`（矩阵见 `repo:sdd/workflows/execution-loop.md` §5）确认绿，再交付 / 续 rebase 链。
5. **承诺解完**：AI 默认把冲突解到底（含 stacked-PR rebase 链续到底），**不主动** `--abort` 逃避。

**安全出口（user-only）**：任何步骤 **user** 说"放弃" → `git merge --abort`，告知"合并已中止，分支恢复同步前状态"。此为 HITL 安全阀，**AI 不主动触发**。

### H8 详细流程（bare worktree config 漂移修复）

诊断：

```bash
git rev-parse --git-dir         # 应返回 .bare/worktrees/<wt-name>
git rev-parse --git-common-dir  # 应返回 .bare
```

告知"当前 worktree 缺 `config.worktree`，git 回退读 `.bare/config` 的 `core.bare = true`，导致工作树命令被拒"。

🔴 人工选：(1) 自动修复（推荐）(2) 手动（参 `mj-agent-git-branch` §Bare Worktree Health Check）(3) 取消

自动修复（PowerShell，仅路径 1）：

```powershell
$wtAbs   = (Get-Location).Path -replace '\\','/'
$wtName  = (Split-Path -Leaf $wtAbs)
$bareDir = (git rev-parse --git-common-dir) -replace '\\','/'
$cfgPath = "$bareDir/worktrees/$wtName/config.worktree"

@"
[core]
`tbare = false
`tworktree = $wtAbs
"@ | Set-Content -Path $cfgPath -NoNewline -Encoding utf8
```

回归验证：`git rev-parse --is-inside-work-tree` 应返 true → 回 Step 0 重启 sync。

## 安全规则

1. **禁止 main 上跨分支 merge**：H4 硬拒；自更新（origin/main → main）例外
2. **develop 上允许自更新和 hotfix 回同步**：非两者触 H4b
3. **merge 策略强制**：rebase 引导 merge (H5)
4. **冲突保护**：保持双方意图，基线内自主修复/验证；实质目标/风险变化先 Owner 决定

## Anti-patterns

- **不要** 在 main 上跨分支 merge（H4 硬阻断）
- **不要** 用 rebase（H5 引导 merge）
- **不要** 跳过 Step 0a 自检（H8 漂移会让后续命令全失败）
- **不要** 在 H2 冲突中丢失双方意图、越过任务授权或用语法通过替代行为验证
- **不要** 自更新模式下 push（仅本地同步）

## Reference Files

- `repo:sdd/workflows/execution-loop.md` §1（Stage 13 Push / Stage 17 hotfix → develop 同步在 17-stage loop 的位置；base branch 同步 + hotfix sync 引用本 skill）
- `repo:docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md`（pushall 双推依据）
- `repo:docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`（Bare Worktree Health Check H8 依据）
