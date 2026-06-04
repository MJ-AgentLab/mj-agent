---
name: mj-agent-git-pr
description: This skill should be used when the user asks to create a Pull Request, select a PR template, fill PR fields, prepare a PR body, or perform a release for mj-agent. Make sure to use this skill whenever the user says "创建PR", "新建PR", "提PR", "create PR", "pull request", "PR模板", "PR description", "发版", "release", "合并到main", "merge to main", "fill PR template" in the mj-agent context. Uses gh CLI with --body-file and the correct template per branch type. mj-agent has 5 PR templates (feature/bugfix/documentation/maintain/hotfix) plus implicit release flow. Includes dual-track A1-A10 self-check + Phase B+ A12-A14 (post v2.1 promote). Do not use for: review-respond on incoming review comments (use mj-agent-flow-review-respond in PR-B3+), merge readiness gate after CI green (use mj-agent-git-check-merge in PR-B3+), or post-merge cleanup (use mj-agent-flow-post-merge in PR-B3+).
---

# mj-agent Git PR

## Overview

为 mj-agent 创建 Pull Request，按 branch type 选择 5 个 PR 模板之一。Claude Code 是非交互模式，**永远不**用 `--body` inline；正确流程：读模板 → 填内容 → 写临时文件 → `--body-file` 传入。

**Workflow position**: Stage 14 of HITL_Prompt 17-stage flow.

## HARD REQUIREMENT — G2: `gh pr create` 必须显式 `--base`

| 分支类型 | `--base` 值 |
|---|---|
| feature / bugfix / documentation / maintain | `develop` |
| hotfix | `main` |

缺 `--base` 时 `gh` 会 fallback 到 GitHub repo default (`main`)，导致
非-hotfix 分支误合到 main。PR #158 (2026-05-12) 是该漂移的历史教训。

钩子 `.claude/scripts/guard-git-workflow.ps1` 在 PreToolUse 拦截缺
`--base` 的 `gh pr create`（详见 `.claude/settings.json`）。

## Template Selection Matrix

| Template | Branch | Target | Special |
|---|---|---|---|
| `feature.md` | `feature/*` | develop | — |
| `bugfix.md` | `bugfix/*` | develop | 必含 root cause + 影响范围 + 自测 |
| `documentation.md` | `documentation/*` | develop | — |
| `maintain.md` | `maintain/*` | develop | 含影响评估 |
| `hotfix.md` | `hotfix/*` | **main** | **回滚预案 mandatory** + 同步回 develop 计划 |
| `release.md` | develop | **main** | **版本号 bump 必填** |

模板位于 `.github/PULL_REQUEST_TEMPLATE/`。

## Prerequisite Check

```bash
gh auth status        # GitHub CLI 已登录
git branch --show-current
git log --oneline develop..HEAD   # 确认有 commits to PR
```

## 快速开始（交互模式）

| 已知信息 | 行动 |
|---|---|
| 用户说"开 PR" 但分支 / target 不明 | 自动用 `git branch --show-current` + branch type matrix 确定 template + target |
| 关联 Issue 不明确 | 询问"这个 PR 是否关联某个 Issue？给出 issue number 或 'no'" |
| Plan / SPEC / ADR 关联不明 | 跑 `git log` 提取 commit message 中的引用，自动填 `## 关联` |
| 信息完整 | 直接装配 PR body |

## Command Format（非交互模式必须）

```bash
# Step 1: 读对应模板
cat .github/PULL_REQUEST_TEMPLATE/<branch-type>.md

# Step 2: 填写完成后写临时文件
# Windows: $env:TEMP/mj-agent-pr-body-<branch>.md
# Unix: /tmp/mj-agent-pr-body-<branch>.md

# Step 3: 创建 PR
# 标准分支（feature/bugfix/documentation/maintain → target develop）：
gh pr create \
  --base develop \
  --head <branch-name> \
  --title "<type>(<scope>): <summary>" \
  --body-file <tmp-file>

# Hotfix → target main：
gh pr create \
  --base main \
  --head hotfix/<desc> \
  --title "fix(<scope>): <summary>" \
  --body-file <tmp-file>

# Release → develop → main：
gh pr create \
  --base main \
  --head develop \
  --title "Release v<X.Y.Z>" \
  --body-file <tmp-file>

# Step 4: 创建后清理临时文件
# PowerShell: Remove-Item <tmp-file>
# Unix: rm <tmp-file>
```

> **PROHIBITED**：`--body` inline（绕过模板结构）；`gh pr create --template` 单独使用（需要终端打开编辑器，非交互模式失败）

## PR Title Format

`<type>(<scope>): <summary>` 与 commit message 一致格式（参 [[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]]）

例：

- `feat(skill): add mj-agent-flow-intake workflow skill`
- `fix(memory): drop AsyncPostgresSaver connections leak under load`
- `docs: tri-track framework v2.1 trio + ADR-014 (skeleton)`
- `infra(deps): bump langgraph 1.1.8 → 1.1.9`
- `Release v0.2.0`（release PR 例外，不用 commit format）

> mj-agent **不**像 mj-system 有 `[partial-reset]` / `[full-reset]` deploy strategy 关键词注入——mj-agent 没有 SQL DDL / 部署策略矩阵（与 mj-system 差异）。

## Per-Template Required Fields（mj-agent 5 templates）

| Template | 必填字段 |
|---|---|
| `feature.md` | 变更摘要 / 影响范围 / 审核要点 / 自检结果（含 CHANGELOG updated） |
| `bugfix.md` | Bug 描述 / 根因分析 / 修复方案 / 影响范围 / 自检结果（含 CHANGELOG updated） |
| `documentation.md` | 文档变更内容 / 变更原因 / 自检结果（双轨 A1-A10 checklist） |
| `maintain.md` | 变更摘要 / 影响评估 / 审核要点 / 自检结果 |
| `hotfix.md` | 事故描述 / 影响范围 / 根因分析 / 修复方案 / **回滚预案 mandatory** / 自检结果 |

## CHANGELOG Requirement

- **feature/* 与 bugfix/* PR**：MUST 更新 `CHANGELOG.md [Unreleased]` block 后再开 PR
- 自检 item："CHANGELOG.md [Unreleased] 区块已更新"
- documentation/* / maintain/* PR 默认不要求（除非 PR 实质改了用户可见行为）

## Hotfix Special Rules

1. target = `main`（**不**是 develop）
2. **回滚预案 mandatory**——描述如何回退如果修复引入新问题
3. PR description 必须确认 hotfix → develop 同步计划（PR merge 后用 `/mj-agent-git-sync`，PR-B3 落地）
4. PR merge 后：在 main 打 patch tag → main → develop 同步

## Self-Check Checklist（按 track 选填）

mj-agent 三轨道治理现状（**v2.2 trio active 终态**：Meta v2.2 + Code_Side v1.1 + Agent_Side v1.1 + HITL_Prompt v1.1 Track C 主 STANDARD；v2.0/v2.1 trio 已 archive 至 `docs/archive/rule/`）；自检 checklist 按 track 选填（详见 [[../../../policies/documentation|policies/documentation]] §5.1 A1-A6）：

### Code-Side（A1-A6 + OB1-OB5）

- A1 路径与文件名合法
- A2 Frontmatter schema 完整（type/domain/summary/owner/created/updated/state；STANDARD/SPEC/EVAL/CONTRACT/ASSESSMENT 含 version）
- A3 state 取值合法
- A4 Wikilinks 检查：`uv run python scripts/check_wikilinks.py` 0 violations
- A5 INDEX.md 已同步
- A6 CLAUDE.md sync allowlist 检查
- OB1-OB5 非阻塞观察项

### Agent-Side（A7-A11；本 PR 涉及 src/mj_agent/{skills,prompts}/ 时）

- A7 SKILL 路径与目录一致；Python 实现存在
- A8 PROMPT `state: active` 时 `eval_references` 非空（Phase 2 起强制）
- A9 EVAL `state: active` 时 `dataset_path` 存在
- A10 CONTRACT `state: active` 时 `schema_ref` 存在
- A11 SKILL `state: active` 时 `eval_references` 非空（Phase D 起强制）

### Engineering-Workflow（A12-A14；v2.1 promote 后激活，Phase B PR-B3 之后）

- A12 `.claude/skills/<name>/SKILL.md` ADR-013 native schema + description ≥ 200 chars + 正向 / 反向触发
- A13 `.claude/settings.json` allowlist diff 评审（Phase C+ 阈值文档定稿后强制）
- A14 `.mcp.json` server 增删声明 trust posture + credential mode（Phase C+ 强制）

## 验证

PR 创建前推荐跑：

```bash
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
uv run ruff check
uv run mypy src/mj_agent
# 涉及 src/ 改动时还跑 pytest（Stage 10 Level A）
```

## 人工介入场景（STOP & ASK）

| # | 触发条件 | skill 行为 |
|---|---|---|
| H1 | gh CLI 未登录 | 输出 `gh auth login` 指令 |
| H2 | branch 不在远程（未 push） | 重定向到 `/mj-agent-git-push` |
| H3 | 模板缺字段（如 hotfix 缺回滚预案） | 列出缺字段 + 询问填值 |
| H4 | hotfix PR target 不是 main | **硬性阻断**：hotfix 必须 base = main |
| H5 | feature/bugfix PR 但 CHANGELOG 未更新 | 询问：(1) 加 CHANGELOG 后再开 PR (2) 跳过（明确不影响 user-visible） |
| H6 | release PR 但版本号未 bump | 列出需 bump 的文件（pyproject.toml / Dockerfile / etc.）；引导手动 bump |
| H7 | 同名 PR 已存在 | 询问：(1) 加 commit + force-push 更新现有 PR (2) 关闭旧 PR 开新 |

## Anti-patterns

- **不要** 用 `--body` inline PR 描述
- **不要** 跳过模板（每个 branch type 都有对应模板）
- **不要** 把详细实现塞进 PR body（那是 SPEC / commit history 的职责；PR body 高层概括即可）
- **不要** 在 release 之外的 PR 改 `CHANGELOG.md` 的 `[X.Y.Z]` 段（只能改 `[Unreleased]`）
- **不要** 在 stacked PR 链中忘记 base 切换（PR-A1 / A2 / A3 已踩过这坑——A2/A3 base 没切到 develop，留在 stack 上游 base）

## Handoff to mj-agent-git-check-merge

```
PR 创建完成 ✓
下一步：等 CI 跑完，用 `/mj-agent-git-check-merge`（PR-B3 落地）检查合并就绪。
  已完成：模板选择 ✓、描述填写 ✓、双轨自检 ✓
  待检查：合并冲突、CI 状态、Review 审批、merge commit 格式
```

## Detailed → docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md

完整字段填写指引 + 示例 + per-template guidance 见 [[../../../docs/infrastructure/git/[GUIDE]_PR_Description_Convention|PR_Description_Convention GUIDE]]。本 SKILL 是其交互式封装。
