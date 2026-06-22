---
name: mj-agent-git-check-merge
description: This skill should be used when the user asks to check if a PR is ready to merge, verify CI status, review approvals, merge conflicts, or PR description completeness for mj-agent. Make sure to use this skill whenever the user asks "PR 能合并吗", "check merge readiness", "PR 审核状态", "可以合并了吗", "PR ready", "代码准备好了吗", "可以让人 review 了吗", "Stage 16", "merge gate", "PR readiness" in the mj-agent context. Runs 5 checks (4 gating + 1 info) — no merge conflicts / CI / Review approvals / PR description completeness（mj-agent 5 branch types：feature/bugfix/documentation/maintain/hotfix）/ Merge commit info — and outputs a structured table with action items. Do not use for: architecture review of someone else's PR (use mj-agent-git-review-pr), drafting replies to review comments on own PR (use mj-agent-flow-review-respond), or post-merge cleanup (use mj-agent-flow-post-merge or mj-agent-git-delete).
---

# mj-agent Git Check Merge

## 前置条件

- `gh` CLI 已认证（`gh auth status`）
- 在 mj-agent worktree 内（bare repo 根无 working tree）

## Overview

PR 创建后的合并就绪检查。5 项检查（4 项门控 + 1 项信息），输出表格 + 失败项建议操作。**Stage 16** of HITL_Prompt 17-stage 闭环。

## 快速开始（交互模式）

### Step 1 — 识别 PR

```bash
git branch --show-current
gh pr list --head <branch> --state open --json number,title
```

| 结果 | 处理 |
|---|---|
| 0 个 open PR | 询问"当前分支无 open PR，请提供 PR 号：" |
| 1 个 open PR | 自动用，输出 `→ 检查 PR #<n>: <title>` |
| 多个 open PR | 列出，询问选 |

### Step 2 — 获取 PR 全部数据（合并调用）

```bash
gh pr view <number> --json number,title,headRefName,mergeable,body,reviews,statusCheckRollup
```

> 单次调用获取 4 项检查所需全部数据。`statusCheckRollup` 始终 exit 0，避免 `gh pr checks` exit code 8（pending）问题。

### Step 3 — 5 项检查

| # | 检查 | 数据来源 |
|---|---|---|
| [1] 合并冲突 | `mergeable` 字段：MERGEABLE / CONFLICTING / UNKNOWN（CONFLICTING → 解冲突走 `/mj-agent-git-sync` §H2a 按意图纪律） |
| [2] CI 检查 | `statusCheckRollup` JSON 数组 |
| [3] Review 状态 | `reviews` 字段（≥1 Approve = Pass / 否则 Pending） |
| [4] PR 描述完整性 | `body` + `headRefName`（按 mj-agent 5 branch type 分支感知必填字段） |
| [5] Merge Commit 检测（信息项） | `gh api repos/MJ-AgentLab/mj-agent/pulls/<n>/commits` parents ≥ 2 |

### Step 4 — 输出结果

见下方"输出格式"。

## 描述完整性检查（分支类型感知，mj-agent 5 类）

| 分支类型 | 必检字段 |
|---|---|
| `feature/*` | 变更摘要、影响范围、审核要点、自检清单（含 CHANGELOG 勾选）|
| `bugfix/*` | Bug 描述、根因分析、修复方案、影响范围、自检清单（含 CHANGELOG 勾选） |
| `documentation/*` | 文档变更内容、变更原因、自检清单（dual-track A1-A10 + A12-A14 v2.1 promote 后） |
| `maintain/*` | 变更摘要、影响评估、审核要点、自检清单 |
| `hotfix/*` | 事故描述、影响范围、根因分析、修复方案、**回滚预案**（mandatory）、自检清单 |
| `develop`（release） | Highlights、审核要点 checklist、版本号 bump |

> mj-agent **不**用 `optimization/*`（与 mj-system 差异；详见 ADR-010 + Commit Convention v1.0）

判定逻辑：Section header 存在 + header 下有非空、非 HTML 注释、非空 checkbox 的文本 = Pass。

## 输出格式

```
## PR #<n>「<title>」Merge Readiness

| 检查项 | 状态 | 说明 |
|---|---|---|
| 无合并冲突 | ✅ Pass | 可正常合并 |
| CI 检查通过 | ❌ Fail | 2 项未通过：`ruff`, `mypy` |
| Review 已批准 | ⚠️ Pending | 0/1 Approve（等待审核人）|
| PR 描述完整 | ❌ Fail | 缺：审核要点、自检清单未勾选 |
| Merge Commit | ℹ️ Info | 1 个 merge commit，涉及 3 文件 |

**总判断：Not Ready to Merge**

### 待处理
1. **CI**: `gh pr checks <n>` 查详情 → 修复后 push
2. **描述**: 补"审核要点" + 完成自检勾选
3. **Review**: 联系 PM

### Merge Commit 详情
| Commit | Message | 涉及文件 |
|---|---|---|
| `abc1234` | merge: ... | ... |
```

**状态图例**：
- `✅ Pass` — 通过
- `❌ Fail` — 失败，必修
- `⚠️ Pending` — 已请求未完（如 Review）
- `⏭️ Skip` — 不适用
- `ℹ️ Info` — 信息展示，不影响总判断

**总判断规则**：
- 全 Pass/Skip/Info → **Ready to Merge ✅**
- 任一 Fail → **Not Ready to Merge ❌**
- 仅有 Pending（无 Fail）→ **Waiting for Review ⏳**

## CI 状态判定（statusCheckRollup）

```
数组空 → ⏭️ Skip（无 CI 配置）

CheckRun (__typename: "CheckRun"):
  conclusion ∈ {FAILURE, CANCELLED, TIMED_OUT, ACTION_REQUIRED, STARTUP_FAILURE} → ❌ Fail
  status ∈ {IN_PROGRESS, QUEUED} 或 conclusion = null → ⚠️ Pending
  conclusion ∈ {SUCCESS, NEUTRAL, SKIPPED} → ✅ Pass

StatusContext (__typename: "StatusContext"):
  state ∈ {FAILURE, ERROR} → ❌ Fail
  state = PENDING → ⚠️ Pending
  state = SUCCESS → ✅ Pass

汇总：任一 ❌ → Fail；无 ❌ 但有 ⚠️ → Pending；全 ✅ → Pass
```

去重规则：同一 check name 多条记录（多次 push）→ 按 `name` 去重，取 `startedAt` 最晚。

## Review 状态判定

只有 Pass 或 Pending：
- `≥1 Approve` → ✅ Pass
- `0 Approve` → ⚠️ Pending

理由：Approve 依赖外部，不是开发者能自修的；Pending 单独一档。

## Merge Commit 判定

通过 `gh api` 获取 PR commits，筛 `parents.length >= 2`：
- API 调用失败 → `⏭️ Skip`（H4）
- 无 merge commit → `⏭️ Skip`
- 有 → `ℹ️ Info`（列数量 + 涉及文件）

## Handoff

### Ready to Merge ✅

```
检查完成 ✓ PR 满足所有合并条件。
下一步：通知 PM 审核合并。合并后 → /mj-agent-flow-post-merge 收尾 + /mj-agent-git-delete 清理。
```

### Not Ready to Merge ❌

```
检查完成 — 存在待修复项。
下一步：按"待处理"修复 → push → 再次 /mj-agent-git-check-merge。
```

### Waiting for Review ⏳

```
检查完成 — 等待外部审核。
下一步：联系审核人。其他检查项均通过。
```

## 人工介入场景（STOP & ASK）

| # | 触发 | 处理 |
|---|---|---|
| **H1a** | `gh pr list --head <branch>` 返回空 | 询问输入 PR 号 |
| **H1b** | 多个 open PR | 列出让用户选 |
| **H2** | mergeable = UNKNOWN | "GitHub 正在计算合并状态，请稍后重试" |
| **H3** | statusCheckRollup 空 | 标 ⏭️ Skip，注"无 CI 配置" |
| **H4** | `gh api` 失败 | Merge Commit 标 ⏭️ Skip，注"无法获取 commit 信息"，不影响总判断 |

## Anti-patterns

- **不要** 用 `gh pr checks` 与其他命令并行（exit code 8 会取消其他调用）
- **不要** 把 Pending 当 Fail（Pending 单独一档；Approve 依赖外部）
- **不要** 在 mergeable=UNKNOWN 时强制判 Pass/Fail（让 user 等 GitHub 计算完）
- **不要** 跳过 PR 描述完整性检查（mj-agent 5 branch type 各有必填字段）

## Reference Files

- [[../../../sdd/workflows/execution-loop|sdd/workflows/execution-loop]] §1（Stage 16 Merge Gate 在 17-stage loop 的位置）
- [[../../../docs/infrastructure/git/[GUIDE]_PR_Description_Convention|PR_Description_Convention]]（描述字段依据）
- `.github/PULL_REQUEST_TEMPLATE/{feature,bugfix,documentation,maintain,hotfix}.md`（5 PR templates）
- mj-system `.claude/skills/mj-sys-git-check-merge/SKILL.md`（直接派生源；mj-agent 改 5 branch type，去 optimization）
