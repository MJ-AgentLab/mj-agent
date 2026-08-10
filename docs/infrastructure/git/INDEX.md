---
type: standard
domain: SYS
summary: docs/infrastructure/git/ 子目录索引 — 4 份 GUIDE（GitHub 设置 / 分支策略 / 推送工作流 / PR 描述规范）
owner: 项目负责人
created: 2026-04-30
updated: 2026-08-10
state: draft
track: code
---

# Git 基础设施索引

> **所属目录**：`docs/infrastructure/git/`
> **说明**：4 份 GUIDE 是 mj-agent git 治理基础设施；规则权威见下方「规则真相源」段，本目录只保留 operational how-to。摘要取自每份文档 frontmatter `summary`。
>
> **规则真相源（M6 X6）**：git **规则**（分支类型 / G1·G2 worktree / PR 模板矩阵 / SemVer bump）的权威已迁入 SDD kernel — [[policies/git-branching|policies/git-branching]] + [[policies/release|policies/release]]；本目录 4 份 GUIDE 保留为 **operational how-to**（仓库初始化、worktree 搭建、推送前检查、gh CLI 用法），**不归档**。

---

## 文档列表

| 文档 | 类型 | 摘要 |
|------|------|------|
| [GitHub 设置与版本管理](./[GUIDE]_GitHub_Setup_And_Versioning.md) | GUIDE | GitHub 仓库初始化与版本管理（mj-agent 适配版） — 双推 remote、分支保护、SemVer 规则与 Phase 0 文件清单 |
| [Git 分支策略指南](./[GUIDE]_Git_Branch_Strategy.md) | GUIDE | mj-agent Git 分支策略指南 — 5 分支模型 + 命名规范 + 分支×commit 类型矩阵 + worktree 操作 |
| [Git 推送工作流](./[GUIDE]_Git_Push_Workflow.md) | GUIDE | mj-agent Git 推送工作流 — 7 步推送前检查 + 双推 Gitee/GitHub + .gitignore 策略 + 可选 pre-push hook |
| [PR 描述规范指南](./[GUIDE]_PR_Description_Convention.md) | GUIDE | mj-agent PR 描述规范指南 — 6 模板 × gh CLI × 自检清单（含 ruff/mypy/pytest） |

---

## 关联入口

- [返回上级索引](../../INDEX.md)
- [[policies/documentation|policies/documentation]]（原 Meta 框架；tri-track M6 PR4 archived → kernel）
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]]
- [[archive/decisions/superseded/[DEPRECATED]_[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions]]（archived）
- [[capabilities/infrastructure/evidence/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|上游业务系统 Git 规范在 mj-agent 的适配评估 v1.0]]（M6 X1 迁入 capability evidence）

---

## 派生说明

| 本文件 | 上游业务系统 源 | 主要改造 |
|--------|------------|---------|
| `[GUIDE]_GitHub_Setup_And_Versioning.md` | 同名 | 删除 §5 bump-version.ps1 整段；§4.1 文件清单缩减为 mj-agent Phase 0 实际（仅 pyproject.toml + README + CLAUDE.md）；§3 SemVer / §4.2 标注 Phase 1+ 启用 |
| `[GUIDE]_Git_Branch_Strategy.md` | 同名 | §0 / §2.3 / §4 / §7 命名示例与 commit scope 改 mj-agent 12 scope；URL 改 `MJ-AgentLab/mj-agent`；其余结构性内容（5 分支模型 + worktree 用法）逐字保留 |
| `[GUIDE]_Git_Push_Workflow.md` | 同名 | §2 CHANGELOG 章节加注 Phase 0.5+ 启用；§10 删除 Q6（Gitee shallow fetch / `upload-pack: not our ref`，mj-agent CI 不复现）；§6.5 双推说明改 mj-agent 实际（Phase 0 CI 仅 compileall） |
| `[GUIDE]_PR_Description_Convention.md` | 同名 | §3.1 实际案例改为 mj-agent 占位；§4.3 自检对齐表删除 Docker / SQL / 硬编码三行，新增 ruff / mypy / pytest / skill loader frontmatter strip 四行 |
