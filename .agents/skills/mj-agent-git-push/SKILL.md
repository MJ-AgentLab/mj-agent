---
name: mj-agent-git-push
description: 适用于 mj-agent 的推送/推送前检查/双推。输入：branch、commit、lint/type/tests/docs/changelog状态、remotes。流程：八项pre-push→文档/日志→worktree→双推→状态。输出：两端SHA/失败端/未执行端分别确认。Use when：检查当前分支是否可双推，给检查报告。Do not use for：我还没commit，替我提交所有改动；转git-commit建议，不顺带stage/commit。新单仓App材料仅受控后台注入，现有个人/MCP秘密不读，实际拒绝不绕过。授权：按任务范围复用，普通实现自主；安全/业务/权限/breaking/接受标准及门禁实质变化先Owner；技术拒绝不绕过。独立调用完成后结束，委派返回调用者；完整闭环已有授权时按检查点继续，不新增外部授权。
---



# mj-agent Git Push

## 本技能的执行约定

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。先核接受基线、任务授权及实际workspace/ref/SHA；基线内普通实施自主，实质安全/业务/权限/breaking/AC/gate变化先Owner决定。授权未撤销且目标/对象/环境/权限/风险未实质变化时复用，普通内容迭代仍核版本但不逐内容重批。技术拒绝保留原错并返回 `BLOCKED_EXECUTION_ROUTE`，不绕过。独立调用返回本范围结果；完整闭环已获授权时按检查点继续；委派返回协调者。


## 触发与职责详述

This skill should be used when the user asks to push code, run pre-push checks, set up dual-push to Gitee and GitHub, troubleshoot push errors, or handle CHANGELOG updates in mj-agent. Make sure to use this skill whenever the user says "推送代码", "push code", "git push", "推到远端", "push to remote", "dual push", "Gitee push", "推送失败", "push error", "CHANGELOG", "推送前检查", "pre-push check" in the mj-agent context. Runs an 8-item pre-push checklist and executes dual-push (Gitee first, GitHub second). Do not use for: commit creation (use mj-agent-git-commit), PR creation (use mj-agent-git-pr), force-push of an amended commit (handle directly via git push --force-with-lease), or branch deletion after merge (use mj-agent-git-delete in PR-B3+).


## Overview

默认执行 8 步 pre-push checklist + 双推（Gitee first, GitHub second）。gitee 是 GitHub 的**被动冗余镜像**：当前 CI 跑在 GitHub-hosted runner（`actions/checkout` 拉 **origin**），**不读 gitee**——默认两个 remote 都须收到 push。具名任务例外先按下节核对象及有效决定，不从 App 可用或技术权限推定例外。

## 任务限定发布例外

Owner Q10 对 `agent-first-delivery` / `maintain/agent-first-delivery` 及 Plan 中原已授权具名 canary，限定向 `MJ-AgentLab/mj-agent` 的 origin 发布，Gitee 镜像延期；接受基线、精确对象及实际版本见 `repo:plans/[PLAN]_agent_first_delivery.md`。先完成适用 pre-push 核验，再由具名新 App 正常发布 GitHub 并核实际 origin ref/SHA；Step 7/8 不执行或探测 Gitee 鉴权，报告 origin 实际结果与 Gitee DEFERRED/NOT_EXECUTED，不勾选 dual push 完成。新 App 例外不扩 Gitee，不借用现有个人/MCP秘密；补镜像另核具名身份、对象及动作授权。其他任务仍按默认双推。

同任务 Q11 将宿主运行验收单列 DEFERRED，不计 PASS；保留原生信任、无个人 config 修改及无 bypass 边界。该延期不免除实际 GitHub CI/canary、有效批准、版本核验或 Owner 最终接受。

> **前置技能**：`mj-agent-git-commit` 已在提交阶段验证 commit message 格式 + type/branch 纪律。本技能 Step 1-2 是二次确认。

**Workflow position**: Stage 13 of HITL_Prompt 17-stage flow.

详细 push 流程见 `repo:docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md`（mj-agent v1.0；本 SKILL 是其交互式封装）。

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
# 必须为空。否则用 mj-agent-git-commit 暂存提交，或加 .gitignore

# 5. 分支命名验证
git branch --show-current
# 必须匹配：<type>/<desc> 或 <type>/<issue-id>-<desc>；type ∈ 5 类

# 6. 同步 base branch（详见 mj-agent-git-sync，PR-B3 落地）
git fetch origin && git merge origin/develop   # feature/bugfix/documentation/maintain
git fetch origin && git merge origin/main      # hotfix/* only
# 冲突 → git status → 解 → git add . → git commit -m "merge: 合并 origin/develop 解决冲突"

# 7. 默认双推执行；上述 Q10 任务仅按具名 origin 发布范围执行
# 首次 push（需 -u 设 upstream）：
git push -u gitee <branch> && git push -u origin <branch>
# 后续 push（推荐 alias）：
git pushall

# 8. 确认适用远程收到；Q10 仅核 origin，Gitee 报 DEFERRED/NOT_EXECUTED
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

**默认顺序强制**：Gitee first, GitHub second——保持 gitee 冗余镜像一致的既有约定；具名任务例外仅按「任务限定发布例外」执行，不改 remote/alias 或默认规则。

## Worktree Validation

复用当前任务对分支、提交范围和目标 remote 的明确 push 批准；不包含 commit、PR、merge 或 `push --delete`。执行前核对实际本地 tip 和授权范围内远程 tip；默认按 Gitee → origin 分开执行，Q10 具名任务只核 origin。下文 alias/复合命令是历史人工用法，不作为原生 hook 拒绝后的改写路线；普通调用使用有限识别的单条 push，新 App 使用已核验受控后台的固定动作。

每端执行后用成功的远程引用查询核对收到的 SHA，不能只看旧 remote-tracking ref。部分成功时成功端不重复推送，结果未知先对账。项目 rules 无 Git 条目，never 单独不阻断 push；支持 -u/--set-upstream 合法换序和显式源:目标 refspec。HEAD 仅可作显式源；执行前用源提交及目标 refs/heads 引用绑定授权，核验实际两端 tip；空源、force 前缀、通配和未列参数保持 UNKNOWN。只读 inspect_push 核对源 SHA、目标 tip 和快进证据，不 fetch 或推送。已有实际拒绝未解除时后端记 NOT_EXECUTED，不换 remote 试探；经审阅的规则变更须核实目标会话实际加载，仅网络恢复或重复同意不足以解除拒绝。核对授权及两端 tip 后只做剩余项。不默认 force，不自动提交工作区的新内容。

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
| `remote: Unauthorized`（Gitee） | 现有鉴权不可用 | 保留错误/未执行状态，不读取或更改已有个人凭据；新单仓App例外不扩展Gitee |
| `error: src refspec ... does not match any` | 分支不在远程 | 加 `-u` 设 upstream |

## 人工介入场景（STOP & ASK）

| # | 触发条件 | skill 行为 |
|---|---|---|
| H1 | Commit message 格式不规范 | 列出问题行 + 建议 amend |
| H2 | Type/branch 不匹配 | 重定向到 `mj-agent-git-commit` H3 流程 |
| H3 | CHANGELOG 缺更新且本 PR 含 feat/fix | 询问：(1) 加 CHANGELOG 后再 push (2) 跳过（仅 docs PR） |
| H4 | 工作目录有未提交变更 | 重定向到 `mj-agent-git-commit` |
| H5 | base branch 远程有 diverge | 触发 sync 流程；冲突时实质变化才HITL |
| H6 | 远程 push 失败（H1-permission / H2-token-expired） | 显示错误 + 修复指引 |
| H7 | 用户要求 force-push 到 main / develop | **硬性阻断**：保护分支不允许 force-push |

## Anti-patterns

- **不要** force-push 到 `main` / `develop`（H7 硬性阻断）
- **不要** 在默认双推或没有具名例外时跳过 Gitee；Q10 任务按限定范围报告延期，不把镜像失配写成已双推。
- **不要** 在 bare repo 根 push（会失败；必须 cd 进 worktree）
- **不要** 在 push 前忘记跑 Level A 验证（Stage 10）—— `uv run ruff check` + `uv run mypy src/mj_agent` 失败 push 后 CI 会红
- **不要** 用 `git push --force` 不加 `--force-with-lease`（覆盖他人修改风险）

## Handoff

```
推送完成
下一步：创建 Pull Request（`gh pr create` 显式 `--base`，per policies/git-branching.md G2）。
  已验证项：commit format、type/branch、CHANGELOG及适用远端实际SHA逐项填真实结果；默认双推分别核两端，Q10任务报告origin结果与Gitee DEFERRED/NOT_EXECUTED
  待执行项：选 PR template、填 PR body、--body-file 创建 PR
```

## Detailed → docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md

完整流程（含 .gitignore 策略 / 可选 pre-push hook / 全部 troubleshooting）见 `repo:docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md`。本 SKILL 是其交互式封装。
