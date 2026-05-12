---
type: runbook
domain: SYS
summary: mj-agent 发布运维流程 Minimal 起步版 — CHANGELOG cut + version bump + git tag + 双推 GitHub/Gitee + GitHub Release；deploy/CD 留 Phase 1 stub
tags:
  - runbook
  - release
  - cicd
aliases:
  - mj-agent Release Process
  - mj-agent 发布流程手册
created: 2026-05-06
updated: 2026-05-06
state: draft
version: v0.1
track: code
owner: 项目负责人
---

# mj-agent Release Process Runbook

> **适用范围**：mj-agent v0.x 准备 release 时手动执行的发布流程
> **目标受众**：项目负责人 / 发布执行人
> **版本**：v0.1
> **最后更新**：2026-05-06
> **关联文档**：[[../git/[GUIDE]_Git_Push_Workflow|Git 推送工作流]]、
> [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit STANDARD]]、
> [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]

---

## TL;DR

- **阅读时间**：~10 分钟
- **涵盖范围**：CHANGELOG `[Unreleased]` → `[vX.Y.Z]` cut；`pyproject.toml` version
  bump；`infra(release):` commit；annotated git tag；双推 origin + gitee；GitHub
  Release 创建；rollback 与 post-mortem 触发条件
- **适用场景**：Phase 0.5 阶段任意 v0.x 节点 release；Phase 1+ 部署 / CD 自动化
  作为 Step 7 stub 占位

## Prerequisites

- **目标读者**：项目负责人 / 维护者；具备 mj-agent 仓库写权限 + 双 remote 凭据
- **必备知识**：
  - [[../git/[GUIDE]_Git_Push_Workflow|Git 推送工作流]] 7 步前置检查
  - [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit STANDARD]]
    §4 类型 allowlist（`infra(release):`）
  - SemVer 基本规则（major / minor / patch）
- **建议了解**：
  - [Keep a Changelog](https://keepachangelog.com/zh-CN/) 格式
  - `uv version` 命令

---

## Trigger

准备 v0.x release 时**手动**触发。Phase 0.5 / Phase 1 阶段尚未自动化；
任意 maintainer 决定 cut 一个版本时按本 runbook 顺序执行。

未来触发条件演进：Phase 1 末或 v1.0 release 时引入 GitHub Actions / CI 检查
（详见 §Steps Step 7 stub）。

---

## Pre-checks

执行 release 前在 `develop` worktree 内**全部通过**以下检查：

- [ ] `uv run ruff check` ✅
- [ ] `uv run mypy src/mj_agent` ✅
- [ ] `uv run pytest tests/unit` ✅
- [ ] `CHANGELOG.md` `[Unreleased]` 完整且经 audit（[[../git/[GUIDE]_Git_Push_Workflow|Push_Workflow]]
      §2 跨 PR audit 节）；近期 commit 全部反映在 `Added / Changed / Removed` 子段
- [ ] `develop` 分支已合并所有意图随版发布的 PR；`git status` clean
- [ ] `.env.example` 字段对齐当前代码所需（无遗漏）

> 任一项未过 → 不要进入 §Steps；先回到 develop / 对应 PR 修复后再 release。

---

## Steps

> 本节为 Minimal 起步版（Phase 0.5）。Phase 1+ 增 deploy / CD 章节。

### Step 1 — Cut CHANGELOG

把 `CHANGELOG.md` 的 `[Unreleased]` 整段重命名为 `[vX.Y.Z] - YYYY-MM-DD`，
并在文件顶部新建空白 `[Unreleased]`：

```markdown
## [Unreleased]

### Added
### Changed
### Removed

## [v0.1.0] - 2026-05-06   ← 由旧 [Unreleased] 改名而来
...
```

### Step 2 — Version bump

```powershell
uv version --bump <major|minor|patch>
```

`pyproject.toml` 的 `[project] version` 字段会同步更新。

### Step 3 — Commit

```powershell
git add CHANGELOG.md pyproject.toml uv.lock
git commit -m "infra(release): bump to vX.Y.Z"
```

> **注**：commit 类型选 `infra` 是基于
> [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit STANDARD]]
> §4 当前 allowlist 中 `infra` 的范围。STANDARD 演进时本 RUNBOOK 同步更新。

### Step 4 — 创建 annotated tag

```powershell
git tag -a vX.Y.Z -m "<one-liner: e.g. mj-agent v0.1.0 — Phase 0.5 governance milestone>"
```

### Step 5 — 双推

```powershell
git push --follow-tags origin develop
git push --follow-tags gitee develop
```

`--follow-tags` 让 `git push` 在传送 commit 的同时把指向被推送 commit 的
annotated tag 一起带上。

### Step 6 — GitHub Release

在 GitHub UI（`https://github.com/MJ-AgentLab/mj-agent/releases/new`）：

1. 选择 tag `vX.Y.Z`
2. Release title：`vX.Y.Z`（或 `v0.1.0 — Phase 0.5 治理里程碑` 之类有语义的）
3. Description：粘贴本次 CHANGELOG 节（即 Step 1 cut 出来的 `[vX.Y.Z]` 整段）
4. 不勾 "Set as a pre-release"（v0.x 仍按正式 release 处理；mj-agent 暂无 RC 流程）
5. **Publish release**

### Step 7 — 部署到目标环境（Phase 1 落地）

> **当前留 stub**：Phase 0.5 阶段 release 仅限仓库层（tag + 包版本号），未涉及
> 生产部署。Phase 1+ 由后续 RUNBOOK 章节或新 RUNBOOK 覆盖部署到 DEV/TEST/PROD
> profile 的步骤（参考 ADR-008 mj-agent 独立 compose project + 通过
> 上游业务系统-backend-network external 作为 consumer 访问 上游业务系统 biz pg 的部署模型）。

---

## Rollback

### Tag 误推（最常见）

```powershell
# 双远端各删一次
git push --delete origin vX.Y.Z
git push --delete gitee vX.Y.Z
git tag -d vX.Y.Z
```

修正 commit / CHANGELOG 后从 §Steps Step 3 重新执行。

### Commit 已 merge 但 release 内容有重大错误

在 `develop` 起 hotfix 分支：

```powershell
git -C develop worktree add ../hotfix/release-vX.Y.Z-rollback -b hotfix/release-vX.Y.Z-rollback develop
cd ../hotfix/release-vX.Y.Z-rollback
git revert <release-commit-sha>
# 复原 [Unreleased]：把 [vX.Y.Z] 段重新合并回 [Unreleased]
```

走 `.github/PULL_REQUEST_TEMPLATE/hotfix.md` PR 模板（如该模板存在）；
合并后再走一次完整 §Steps。

### 边界

Phase 0.5 阶段 release 未涉及生产部署；rollback **仅限仓库层**（tag + commit
+ CHANGELOG）。Phase 1+ 需扩展到环境层 rollback。

---

## Post-mortem trigger

满足以下任一条件，起 `[POSTMORTEM]_Release_<vX.Y.Z>_<slug>.md`（POSTMORTEM
模板待 Phase 1 落地；当前以普通 markdown 临时记录于 `docs/postmortem/`）：

- 发生 rollback（Step 1 或 Step 2 路径之一）
- 影响外部下游（上游业务系统 栈下游服务、analyst 用户）
- 误推 tag 在线保留 ≥ 1 小时（即使后续删除也算）

记录内容至少含：时间线、根因、临时缓解、永久修复、预防措施。

---

## 关联文档

- [[../git/[GUIDE]_Git_Push_Workflow|Git 推送工作流]] — §2 CHANGELOG / §6 双推
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit STANDARD]] — §4 类型 allowlist
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]] — §Defer 中的 release 流程承诺
- [[../../guide/[GUIDE]_Developer_Onboarding|开发者上手指南]] — §6 提交与推送
- `pyproject.toml` `[project] version` — version bump 目标字段
- `CHANGELOG.md` — Step 1 cut 操作目标

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-06 | v0.1 | 初稿（PLAN G PR3 落地）—— Minimal 起步版（CHANGELOG cut + version bump + tag + 双推 + GitHub Release）；deploy/CD/post-mortem template 留 Phase 1 stub |
