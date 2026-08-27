---
name: mj-agent-git-branch
description: "Create branches for the bare-repo worktree model: pick the branch type (feature/bugfix/documentation/maintain/hotfix) and generate the worktree add command; use for 创建分支, create branch, starting new work; branches are never created in-place with checkout -b."
---

# Codex carrier preface

> **This file is a generated artifact.** It is a deterministic translation of
> `.claude/skills/<this-skill>/SKILL.md` produced by `scripts/sdd/agents_sync.py`;
> never edit it — edit the source through its own gates and re-run sync.
>
> **Semantic difference declaration.** The Claude Code harness primitives this
> body references — `ask`-gates, permission prompts, protected-path prompts,
> `PreToolUse` hooks, `.claude/settings.json`, `guard-git-workflow` — are NOT
> present under your harness. Read every such reference as an AGENTS.md
> self-enforced duty (repo-root `AGENTS.md`, "Self-enforced boundaries"): the
> stop points themselves are tool-neutral; only the carrier differs. Claude
> tool names (Edit / Write / Read / Bash and friends) and Claude
> self-references likewise read as "your own equivalent tool / yourself".
> `OWNER_APPROVAL_REQUIRED` stop points bind you exactly as written.
>
> **Optional skill calls.** Before following any `superpowers:*` or other
> optional-skill reference, run your CURRENT capability discovery: if the skill
> is discoverable, invoke it (`$skill-name` or an explicit "use skill-name");
> if it is not, perform the manual equivalent the body describes. These
> references are not Claude-only and must not be skipped on the assumption
> that they are.
>
> **Peer skills.** `$mj-agent-*` names and `.agents/skills/<name>/SKILL.md`
> paths refer to your native carriers of the same shared skills; dependency
> routes annotated as `codex-route:<edge-id>` blocks carry the registered
> substitute when a target has no carrier.

# mj-agent Git Branch

## Overview

Creates and manages Git branches for **mj-agent** following the project's bare-repo + worktree-per-branch convention. **5 temporary branch types** (per [[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention v1.0]] §5)—`feature/*`、`bugfix/*`、`documentation/*`、`maintain/*`、`hotfix/*`—plus 2 protected permanent branches (`main`、`develop`)。

> mj-agent **不**用 `optimization/`（与 mj-system 差异；详见 ADR-010 / Commit Convention §5.2）。

**Workflow position**: Stage 2 of HITL_Prompt 17-stage flow.

```text
[mj-agent-git-issue] -> [mj-agent-git-branch] -> ...编码... -> [mj-agent-git-commit] -> ...
```

## HARD REQUIREMENT — G1: 新分支必须 `git worktree add`

新分支用：

```bash
git worktree add ../<branch-name> -b <branch-name>
```

**禁止** 在已有 worktree（`develop/`、`documentation/...`、`feature/...` 等）
中 `git checkout -b` / `git checkout -B` / `git switch -c` / `git switch -C`。
bugfix 同样适用 —— PR #154 (2026-05-12) 是 G1 规则诞生前的 precipitating
incident（详见 `plans/[PLAN]_g1_g2_workflow_enforcement.md` 根因 + 时间线）。

钩子 `.claude/scripts/guard-git-workflow.ps1` 在 PreToolUse 拦截 `git
checkout -b`（详见 `.claude/settings.json`）。

## Prerequisite Check

```bash
# 当前在 mj-agent 仓内（任一 worktree）
git rev-parse --git-common-dir
# 期望返回 .bare 路径（mj-agent 用 bare repo）

# 工作树干净
git status --short
# 干净时输出空；有未提交变更建议先 commit / stash 再切分支
```

## 快速开始（交互模式）

| 已知信息 | 行动 |
|---|---|
| 任务性质不明确（"要开始开发" / "改代码"） | 问："这次任务是新功能、bug 修复、纯文档、基础设施维护，还是生产紧急修复？" |
| 类型明确，但无英文描述词 | 问："请用 2-5 个英文单词描述此任务（kebab-case，e.g. `add-flow-intake-skill`、`fix-yaml-loader-encoding`）" |
| 类型 + 描述词均有，缺 issue-id | 直接生成（issue-id 可选，不追问）。若需先创建 Issue，提示 `/mj-agent-git-issue` |
| 信息完整 | 直接生成命令 |

### 输出格式（信息收集完毕后，**只输出单行命令**）

```bash
# feature / bugfix / documentation / maintain（从 develop/ 内执行）
cd D:/workspace/10-software-project/projects/mj-agent/develop && \
  git worktree add ../<type>/<desc> -b <type>/<desc> develop

# hotfix（从 main 创建；若 main/ worktree 不存在则先建）
git worktree add D:/workspace/10-software-project/projects/mj-agent/main main && \
  cd D:/workspace/10-software-project/projects/mj-agent/main && \
  git worktree add ../hotfix/<desc> -b hotfix/<desc> main
```

**示例**：

```bash
# feature
cd D:/workspace/10-software-project/projects/mj-agent/develop && \
  git worktree add ../feature/63-add-flow-intake-skill -b feature/63-add-flow-intake-skill develop

# documentation（如本 PR-B1）
cd D:/workspace/10-software-project/projects/mj-agent/develop && \
  git worktree add ../documentation/phase-b1-git-family -b documentation/phase-b1-git-family develop

# hotfix
git worktree add D:/workspace/10-software-project/projects/mj-agent/main main && \
  cd D:/workspace/10-software-project/projects/mj-agent/main && \
  git worktree add ../hotfix/async-checkpointer-leak -b hotfix/async-checkpointer-leak main
```

## Branch Type Decision

| 触发问题 | → Branch Type |
|---|---|
| 新功能 / 新 skill / 新 tool / 重构？ | `feature/` |
| develop 上发现 bug，需要修？ | `bugfix/` |
| 仅文档变更，无代码？ | `documentation/` |
| 文档与代码同 PR？ | 跟代码类型（`feature/` 或 `maintain/`） |
| CI/CD / Docker / deps / scripts / 配置？ | `maintain/` |
| 生产紧急修复？ | `hotfix/`（base = main） |

> `CHANGELOG.md` 是 release process 的一部分，**不**单独开分支。

## Naming Format

```
<type>/<issue-id>-<description>   # 与 GitHub Issue 关联
<type>/<description>              # 无 Issue（也合法，如 PR-A1 用 documentation/tri-track-framework-v2.1）
```

合法 type：`feature` / `bugfix` / `documentation` / `maintain` / `hotfix`

规则：lowercase，仅允许字母数字 + 连字符 `-`；no spaces / uppercase。

## Commands by Branch Type

### feature / bugfix / documentation / maintain（base = develop）

```bash
# Step 1: 创建 worktree（在 develop/ 内执行）
cd D:/workspace/10-software-project/projects/mj-agent/develop
git worktree add ../feature/63-add-flow-intake-skill -b feature/63-add-flow-intake-skill develop

# Step 2: 进入新 worktree
cd ../feature/63-add-flow-intake-skill
git rev-parse --is-inside-work-tree   # 期望: true；false → §Bare Worktree Health Check

# ... 编码 → commit → push ...
# 开发中如需同步 develop 最新代码 → 用 /mj-agent-git-sync（PR-B3 落地）

# PR merge 后清理（用 /mj-agent-git-delete，PR-B3 落地；或手动）
cd D:/workspace/10-software-project/projects/mj-agent/develop
git worktree remove ../feature/63-add-flow-intake-skill
git branch -d feature/63-add-flow-intake-skill
```

### hotfix（base = main，6 步）

```bash
# Step 1: 若 main/ worktree 不存在则先创建
git worktree add D:/workspace/10-software-project/projects/mj-agent/main main

# Step 2: 在 main/ 内创建 hotfix worktree
cd D:/workspace/10-software-project/projects/mj-agent/main
git worktree add ../hotfix/async-checkpointer-leak -b hotfix/async-checkpointer-leak main

# Step 3: 进入修复 + commit（仅 fix 类型）
cd ../hotfix/async-checkpointer-leak
git rev-parse --is-inside-work-tree   # 期望: true
# ... 修复 → commit ...
git commit -m "fix(memory): drop AsyncPostgresSaver connections leak"

# Step 4: Push（双推 gitee + origin）
git push -u gitee hotfix/async-checkpointer-leak && git push -u origin hotfix/async-checkpointer-leak

# Step 5: PR 创建（base = main，target = main；用 /mj-agent-git-pr）

# Step 6: PR merge 后
#   (a) 在 main 上打 patch 版本 tag
#   (b) hotfix → develop 同步（用 /mj-agent-git-sync，PR-B3 落地）
#   (c) 清理 hotfix worktree（用 /mj-agent-git-delete）
```

## Bare Repo Worktree 模型

mj-agent 用 bare repo + 多 worktree 模型（与 mj-system 一致）：

```
D:/workspace/10-software-project/projects/mj-agent/
├── .bare/                                  ← bare repo（git 仓库本身）
├── .git                                    ← 单行指针 (gitdir: ./.bare)
├── develop/                                ← develop 分支 worktree
├── main/                                   ← main 分支 worktree（hotfix 时创建）
├── feature/<branch-name>/                  ← feature 分支 worktree
├── bugfix/<branch-name>/
├── documentation/<branch-name>/
├── maintain/<branch-name>/
└── hotfix/<branch-name>/
```

> **SAFETY**：`git checkout` 切换分支在 `mj-agent/` 根目录**不可用**——bare repo 根没有 working tree。**永远** `cd` 进目标 worktree 目录。

### 初次初始化（仓库还没 clone 时）

```bash
# Step 1: 创建容器目录
mkdir mj-agent && cd mj-agent

# Step 2: bare clone
git clone --bare https://github.com/MJ-AgentLab/mj-agent.git .bare

# Step 3: 单行 gitdir 指针
echo "gitdir: ./.bare" > .git
# Windows PowerShell: New-Item .git -ItemType File -Value "gitdir: ./.bare"

# Step 4: 修复 fetch refspec（bare clone 默认遗漏）
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# Step 5: fetch + 创建 develop worktree
git fetch origin
git worktree add develop develop

# Step 6: 验证
git worktree list   # 应见 .bare + develop
```

详见 [[../../../docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning|GitHub_Setup_And_Versioning]]。

## Bare Worktree Health Check（防 config.worktree 漂移）

如果 `git rev-parse --is-inside-work-tree` 返回 `false`（应为 `true`）：

```ini
# 写入 .bare/worktrees/<wt-name>/config.worktree
[core]
  bare = false
  worktree = <worktree 绝对路径，正斜杠>
```

PowerShell 一键修复（`mj-agent/` 根执行）：

```powershell
$wtName  = "<worktree-name>"      # .bare/worktrees/ 下的目录名
$wtAbs   = "<worktree 绝对路径，正斜杠>"
$cfgPath = ".bare/worktrees/$wtName/config.worktree"
@"
[core]
  bare = false
  worktree = $wtAbs
"@ | Set-Content -Path $cfgPath -NoNewline -Encoding utf8
```

## 人工介入场景（STOP & ASK）

| # | 触发条件 | skill 行为 |
|---|---|---|
| H1 | 工作目录不干净（git status 有变更） | 询问：先 commit / stash / 还是放弃改动？ |
| H2 | base branch 不存在（如 main/ worktree 没建过） | 自动跑 `git worktree add main main`（hotfix 场景） |
| H3 | 分支名已存在 | 询问：用现有分支还是改新名？ |
| H4 | 用户选 hotfix | 加注：`hotfix base = main, PR target = main, PR merge 后需 main → develop 同步` |
| H5 | `git rev-parse --is-inside-work-tree` 返回 false | 触发 §Bare Worktree Health Check 修复流程 |

## Anti-patterns

- **不要** 在 mj-agent 仓根（bare repo）执行 `git checkout`——会失败
- **不要** 跳过 worktree 直接 `git checkout -b <branch>`——破坏 worktree-per-branch 模型
- **不要** 用 `optimization/` 类型——mj-agent 不支持（与 mj-system 差异）
- **不要** 在 develop / main 上直接 commit——这两个是受保护永久分支
- **不要** 一次创建多个 worktree（一次只工作在一个上下文）

## Handoff to mj-agent-git-commit

worktree 创建后进入分支编码，commit 阶段用 `$mj-agent-git-commit`（PR-B1 落地）。

<!-- codex-route:edge-git-branch-git-commit -->
> Codex route: invoke `$mj-agent-git-commit` (native carrier; handoff, always)
