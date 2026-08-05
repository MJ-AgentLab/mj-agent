---
name: mj-agent-git-issue
description: This skill should be used when the user asks to create a GitHub Issue, draft an issue body, file a bug report, or start a new task in mj-agent. Make sure to use this skill whenever the user says "创建issue", "新建issue", "提issue", "报bug", "新任务", "开新工作", "create issue", "new issue", "report bug", "file issue", "open issue", "start new task" in the mj-agent context. Uses gh CLI with --body-file. Fills the matching .github/ISSUE_TEMPLATE/ file (8 templates, in-repo since 2026-05-20) selected by branch-type taxonomy + Intake Result. Do not use for: branch creation (use mj-agent-git-branch), commit message authoring (use mj-agent-git-commit), PR creation (use mj-agent-git-pr), or Issue triage on existing issues.
---

# mj-agent Git Issue

## Overview

Creates GitHub Issues for **mj-agent** repo (https://github.com/MJ-AgentLab/mj-agent). The repo
has **8 issue templates under `.github/ISSUE_TEMPLATE/`** (in-repo since `6c84efc`, 2026-05-20).
This skill **fills the matching template** — it does not invent a parallel body structure — with
the template chosen by branch-type taxonomy
([[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]] §5) + the
Intake Result from Stage 0.

> **Why template-first**: the templates carry `HITL Trigger Check` checklists — including the
> `docker/Dockerfile` external-registry supply-chain stop (#408 / #413), a surface with **no
> harness carrier and no CI gate**. A hand-rolled inline body silently drops those checks. Keeping
> one source of truth is what stops the two structures drifting apart again.

> **Distinct artifact — do not confuse**: `docs/_templates/TEMPLATE_ISSUE.md` is the skeleton for
> *local* `[ISSUE]` docs under `docs/issues/` (a doc-track artifact, delivered by Phase D-1 /
> #90). It is **not** a GitHub issue form and is not used by this skill.

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
| 1 | feature | `enhancement` | New feature / new skill / new tool / refactor |
| 2 | bugfix | `bug` | Bug found on develop, needs fix |
| 3 | documentation | `documentation` | Docs only, no code changes |
| 4 | maintain | `maintain` | CI/CD / Docker / deps / env / scripts |
| 5 | hotfix | `bug` | Production emergency (auto-selected if Step 1a = Yes) |

> **Label column = labels that actually exist in this repo.** Verify with `gh label list` before
> passing `--label`; `gh issue create` **fails** on an unknown label. There are deliberately no
> `feature` / `bugfix` / `hotfix` labels — those are *branch* types, and per Commit Convention
> §5.1 the branch namespace is kept distinct from other namespaces. `hotfix` maps to `bug`
> because the repo carries no priority label; the `[Hotfix]` title prefix is what marks urgency.

> mj-agent **不**用 `optimization/` 类型（与 mj-system 差异；详见 ADR-010 + Commit Convention v1.0）。

## Step 2: Build Issue Body（fill the matching template）

**Source of truth = `.github/ISSUE_TEMPLATE/<name>.md`.** Do **not** hand-roll a parallel body
structure — a second structure is what drifted out of sync before (#422).

### Step 2a: Route branch type → template

| Branch type | Template | Title prefix | Label |
|---|---|---|---|
| feature | `feature_request.md` | `[Feature]` | `enhancement` |
| bugfix | `bug_report.md` | `[Bugfix]` | `bug` |
| documentation | `documentation.md` | `[Documentation]` | `documentation` |
| maintain | `maintenance.md` | `[Maintain]` | `maintain` |
| hotfix | `hotfix.md` | `[Hotfix]` | `bug` |

Three topical templates have no 1:1 branch type — pick them by subject; the branch type still
comes from the table above:

| Template | Use for | Title prefix | Label |
|---|---|---|---|
| `agent.md` | Agent 行为 / Tool / SKILL / Prompt / Eval | `[Agent]` | `track:agent` |
| `runtime.md` | 运行时 / 部署 / Studio / 监控 | `[Runtime]` | `maintain` |
| `archive.md` | 归档已弃用 capability / STANDARD / ADR | `[Archive]` | `maintain` |

### Step 2b: Fill it

1. Read `.github/ISSUE_TEMPLATE/<name>.md`.
2. **Strip the YAML frontmatter** — `name` / `about` / `title` / `labels` / `assignees` are
   GitHub form metadata and must never appear in the body.
3. Replace every `<...>` placeholder. For checklist items that do not apply, answer them
   `— No` rather than deleting the line: a visibly-answered check is evidence, a deleted one is
   indistinguishable from one nobody considered.
4. Fill `HITL Trigger Check` honestly — for several surfaces it is the **only** carrier. The
   `docker/Dockerfile` external-registry supply-chain stop has no harness gate and no CI gate
   (`policies/docker-runtime.md` §4); skipping the checkbox is how that stop goes unnoticed.
5. Write the filled body to a temp file → `gh issue create --body-file` (Step 5). `--template`
   only takes effect for interactive / web-UI creation and is silently inert in non-interactive
   use — `--body-file` is the required carrier here.

> **Scope 段·纵切片归属**（承 `/mj-agent-flow-plan` Step 2 纵切纪律）：若本 issue 是某 milestone
> 的一个**端到端纵切片**，In-scope 应是**自身可验、可独立 review-合**的窄完整路径；用
> `blocked-by` 标依赖序，**不**按层水平切。

> **Acceptance Criteria 段**：每条须能对应一条可跑命令（intake Step 4 的 AC 可验证性准入门）。
> 写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

> `bugfix` / `hotfix` 的 Reproduction / Expected vs Actual / Environment 段**已在
> `bug_report.md` / `hotfix.md` 模板内**，不必另行拼接。

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
- `[Agent] describe_biz_table returns wrong column names for biz_dws`（专题模板）
- `[Runtime] Studio probe fails after LLM endpoint switch`（专题模板）
- `[Archive] Retire v1.1 trio into archive/rule/`（专题模板）

> Prefix 与 Step 2a 表一一对应，且**与模板 frontmatter `title:` 一致**——改一处必须改另一处。

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

# 把 Step 2b 填好的模板正文（已剥 frontmatter）写入临时文件后
gh issue create \
  --title "[<Type>] <短描述>" \
  --body-file <tmp-file> \
  --label "<Step 2a 表中的 label>" \
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
| H5 | Step 2a 路由到的模板文件读不到（被删 / 改名 / 移位） | **停**并报出缺失路径。**不要**退回内联自造 body——那正是 #422 的成因。先确认模板是被有意移除还是误删，再决定补回文件还是改 Step 2a 路由表 |
| H6 | `gh issue create` 因 label 不存在而失败 | 用 `gh label list` 核对实际 label。**不要**顺手新建 label——建 label 是仓库级外向改动，需 Owner 拍板；改用 Step 2a 表中已存在的 label |

## Anti-patterns

- **不要** 用 `--body` inline Issue 描述（违反 ADR-013 + mj-system mj-sys-git-issue 风格；非交互模式应用 `--body-file`）
- **不要** 绕开 `.github/ISSUE_TEMPLATE/` 自造 body 结构（#422：并行结构必然漂移，且会丢掉模板携带的 `HITL Trigger Check`）
- **不要** 把模板的 YAML frontmatter 一起写进 body（`name/about/title/labels` 是 GitHub 表单元数据）
- **不要** 因为某个勾选项不适用就删掉它（标 `— No`：已回答与没人看过必须可区分）
- **不要** 在没有 Intake Result 时直接创建 Issue（跳过 §3.1 必停 HITL trigger）
- **不要** 在 Issue body 中塞详细实现计划（那是 Plan / SPEC 的职责）
- **不要** 用 `feat(scope)` 这种 commit message 格式做 Issue title prefix（commit type ≠ Issue type label；详见 [[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]] §5.1）

## Handoff to mj-agent-git-branch

Issue 创建后用 `/mj-agent-git-branch` 创建对应 worktree，分支命名 `<type>/<issue-number>-<short-description>`。
