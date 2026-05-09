---
name: mj-agent-git-issue
description: This skill should be used when the user asks to create a GitHub Issue, draft an issue body, file a bug report, or start a new task in mj-agent. Make sure to use this skill whenever the user says "创建issue", "新建issue", "提issue", "报bug", "新任务", "开新工作", "create issue", "new issue", "report bug", "file issue", "open issue", "start new task" in the mj-agent context. Uses gh CLI with --body-file. mj-agent currently has no .github/ISSUE_TEMPLATE/ (Phase D will add) — this skill builds Issue body structure from branch-type taxonomy + Intake Result. Do not use for: branch creation (use mj-agent-git-branch), commit message authoring (use mj-agent-git-commit), PR creation (use mj-agent-git-pr), or Issue triage on existing issues.
---

# mj-agent Git Issue

## Overview

Creates GitHub Issues for **mj-agent** repo (https://github.com/MJ-AgentLab/mj-agent). mj-agent **does not yet have `.github/ISSUE_TEMPLATE/`** (Phase D PR-D1 will add `TEMPLATE_ISSUE.md`); this skill builds Issue body inline based on branch-type taxonomy ([[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]] §5) + the Intake Result from Stage 0.

**Workflow position**: optional pre-step before `mj-agent-git-branch`.

```text
[mj-agent-flow-intake] -> [mj-agent-git-issue] -(optional)-> [mj-agent-git-branch] -> ...
```

## Prerequisite Check

```bash
gh auth status
```

If not installed or not logged in → output install/login guidance and **stop** (H1).

## 快速开始（交互模式）

| 已知信息 | 行动 |
|---|---|
| 用户说"创建 issue"但 Intake Result 缺失 | 提示先跑 `/mj-agent-flow-intake`（PR-B2 落地） |
| Intake Result 有，分支类型已确定 | 跳到 Step 2 直接装配 body |
| Intake Result 有，但分支类型不明（feature vs bugfix vs maintain） | Step 1b AskUserQuestion 选 |
| 信息完整 | 直接生成 `gh issue create` 命令 |

## Step 1: Identify Issue Type

### Step 1a: Urgency Check（AskUserQuestion）

"Is this a production emergency bug requiring immediate hotfix?"

- **Yes** → type = `hotfix`. 提醒：`Hotfix branches are created from main, and the PR target is also main` (H4)
- **No** → Step 1b

### Step 1b: Choose Branch Type（AskUserQuestion，5 options）

mj-agent 5 branch types ([[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]] §5)：

| Option | Type | Label | When to choose |
|---|---|---|---|
| 1 | feature | `feature` | New feature / new skill / new tool / refactor |
| 2 | bugfix | `bugfix` | Bug found on develop, needs fix |
| 3 | documentation | `documentation` | Docs only, no code changes |
| 4 | maintain | `maintain` | CI/CD / Docker / deps / env / scripts |
| 5 | hotfix | `hotfix` | Production emergency (auto-selected if Step 1a = Yes) |

> mj-agent **不**用 `optimization/` 类型（与 mj-system 差异；详见 ADR-010 + Commit Convention v1.0）。

## Step 2: Build Issue Body（5 fields）

**mj-agent Issue body 结构**（Phase D `TEMPLATE_ISSUE.md` 落地前的临时约定，与 PR 模板字段对位）：

```markdown
## What

<feature: 做什么；bugfix/hotfix: 现象；documentation: 变更内容；maintain: 改什么>

## Why

<motivation；如对应已有 ADR/SPEC 给 wikilink>

## Scope

- **In-scope**: <本 issue 覆盖的具体范围>
- **Out-of-scope**: <相邻但不覆盖>

## Acceptance Criteria

- [ ] 验收标准 1（可验证 / 可测试）
- [ ] 验收标准 2

## Risk

- **Risk level**: Low / Medium / High（来自 Intake §7）
- **Risk areas**: <e.g., in-source canonical 改动 / biz catalog 镜像 / SQL guardrail / system.md version bump（4 项 mj-agent 专属 §3.1 必停 trigger）>

## Verification Plan

- `uv run pytest tests/<bands>` <按改动范围选 unit/eval/integration/smoke/contract>
- `uv run ruff check` + `uv run mypy src/mj_agent`
- <如需 Studio 探针 / mj-agent check：列出>

## Related Docs

- ADR / SPEC / GUIDE / RUNBOOK wikilinks（如有）
- Plan: `plans/[PLAN]_*.md`（如已起草）
```

**bugfix / hotfix 加段**（参 mj-system mj-sys-git-issue v3.0 完整 Bug 模板）：

```markdown
## Reproduction

1. <步骤 1>
2. <步骤 2>
...

## Expected vs Actual

- **Expected**: <期望行为>
- **Actual**: <实际行为>

## Environment

- mj-agent version / commit:
- Python / uv versions:
- Profile: DEV / TEST / PROD
```

## Step 3: Title Format

```
[<Type>] <短描述>
```

例：
- `[Feature] Add mj-agent-flow-scope-drift skill`
- `[Bugfix] qcm_catalog YAML loader fails on Chinese chars`
- `[Documentation] Phase B PR-B1 backfill notes`
- `[Maintain] Bump langgraph 1.1.8 → 1.1.9`
- `[Hotfix] AsyncPostgresSaver checkpointer drops connections under load`

## Step 4: Preview & Confirm

展示完整 Issue（Title + Labels + Body）；AskUserQuestion 3 options：

1. **Submit** → Step 5
2. **Edit** → 询问哪个字段重填 → 回到预览
3. **Cancel** → 清理临时文件，停止 (H2)

### Step 4b: Assignee（可选）

AskUserQuestion 3 options：
1. **Assign to me** → `--assignee @me`
2. **Assign to someone else** → 询问用户名 → `--assignee <username>`
3. **Skip**

## Step 5: Create Issue

```bash
# Windows: $env:TEMP/mj-agent-issue-body-<type>.md
# Unix: /tmp/mj-agent-issue-body-<type>.md

# 写 body 到临时文件后
gh issue create \
  --title "[<Type>] <短描述>" \
  --body-file <tmp-file> \
  --label "<type>" \
  [--assignee <user>]

# 创建后清理临时文件
rm <tmp-file>  # PowerShell: Remove-Item <tmp-file>
```

如失败 → H3。

## Step 6: Output & Handoff

```
## Issue Created

- **URL**: https://github.com/MJ-AgentLab/mj-agent/issues/<number>
- **Number**: #<number>
- **Title**: <title>
- **Labels**: <type>

### Next Step

To start development, use `/mj-agent-git-branch` to create:
  <type>/<issue-number>-<short-description>
```

handoff **suggestive，不强制**——`mj-agent-git-branch` 的 issue-id 是可选参数。

## 人工介入场景（STOP & ASK）

| # | 触发条件 | skill 行为 |
|---|---|---|
| H1 | `gh` 未安装 / 未登录 | 输出 install/login 指令，停止 |
| H2 | 用户在预览阶段 cancel | 清理临时文件，停止 |
| H3 | `gh issue create` 失败 | 显示错误，建议检查网络 / 权限 / GitHub token |
| H4 | 用户选 hotfix | 加注：`Hotfix branch from main, PR target also main`（与 mj-agent-git-branch / mj-agent-git-pr 对位） |
| H5 | mj-agent 仓 .github/ISSUE_TEMPLATE/ 缺失 | 默认行为（v1.0 期间正常状态）；按 Step 2 inline body；提示用户 Phase D PR-D1 会落地 TEMPLATE_ISSUE.md |

## Anti-patterns

- **不要** 用 `--body` inline Issue 描述（违反 ADR-013 + mj-system mj-sys-git-issue 风格；非交互模式应用 `--body-file`）
- **不要** 在没有 Intake Result 时直接创建 Issue（跳过 §3.1 必停 HITL trigger）
- **不要** 在 Issue body 中塞详细实现计划（那是 Plan / SPEC 的职责）
- **不要** 用 `feat(scope)` 这种 commit message 格式做 Issue title prefix（commit type ≠ Issue type label；详见 [[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]] §5.1）

## Handoff to mj-agent-git-branch

Issue 创建后用 `/mj-agent-git-branch` 创建对应 worktree，分支命名 `<type>/<issue-number>-<short-description>`。
