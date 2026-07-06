# Contributing to mj-agent

> **面向对象**：环境已就绪、准备提交 PR 的开发者。
> 如需搭建开发环境，请先阅读 [docs/guide/[GUIDE]_Developer_Onboarding.md](docs/guide/[GUIDE]_Developer_Onboarding.md)（15 分钟完整版）或 [docs/guide/[GUIDE]_Quick_Start_Setup.md](docs/guide/[GUIDE]_Quick_Start_Setup.md)（5 分钟赶时间版）。
> 本文档遵循「**摘要 + 跳转**」模式：每段精炼概览，深度细则跳转对应 STANDARD / GUIDE。
> 项目根具名文件治理边界：见 [policies/documentation.md](policies/documentation.md) §2.6 + [docs/rule/[STANDARD]_GitHub_Markdown.md](docs/rule/[STANDARD]_GitHub_Markdown.md) §14。

## 目录

1. [快速开始](#快速开始)
2. [分支策略](#分支策略)
3. [Commit 规范](#commit-规范)
4. [PR 流程](#pr-流程)
5. [Code Review 标准](#code-review-标准)
6. [CI 流水线](#ci-流水线)
7. [文档贡献规范](#文档贡献规范)
8. [相关文档](#相关文档)

---

## 快速开始

**前提条件**：

- 已在 mj-agent 仓库父目录运行 `mj-agent-clone-bare.ps1` 完成 bare-repo + worktree 布局
- 已在 `develop/` worktree 跑通 `uv sync` + `uv run mj-agent check`（详见 [README §Quick start](./README.md#quick-start)）
- 已获 GitHub `MJ-AgentLab/mj-agent` 写权限（[Developer_Onboarding §0.5 权限/账号申请清单](docs/guide/[GUIDE]_Developer_Onboarding.md)）

**标准贡献流程 5 步**：

1. 从 `develop` 用 `git -C develop worktree add ../<dir> -b <branch> develop` 起新 worktree（G1 worktree-required；不要用 `git checkout -b`）
2. 编码 + 本地自测（`uv run pytest tests/unit` + `uv run ruff check` + `uv run mypy src/mj_agent`）+ 按规范 commit
3. 推送分支到 GitHub（origin）+ Gitee（镜像）+ 用 `gh pr create --base develop`（G2 hook 拦截缺 `--base`）
4. 等待 review，按反馈修改
5. PR merge 后：删除已合并的 worktree + 分支（[`/mj-agent-flow-post-merge`](https://github.com/MJ-AgentLab/mj-agent/blob/develop/.claude/skills/mj-agent-flow-post-merge/SKILL.md) 提供清理 workflow）

---

## 分支策略

### 5 分支模型

```
main              ← 稳定可部署（受保护；只接受 PR 合并）
│
├── develop       ← 开发主线（受保护；只接受 PR 合并）
│   │
│   ├── feature/xxx         ← 新功能 / 新模块 / 重构
│   ├── bugfix/xxx          ← develop 上发现的 Bug
│   ├── documentation/xxx   ← 独立文档更新
│   └── maintain/xxx        ← CI / Docker / 依赖 / 工具脚本
│
└── hotfix/xxx    ← 紧急修复（从 main 创建，merge 回 main，再同步 develop）
```

### 命名规范

格式：`<类型>/<short-description>`（或 `<类型>/<issue-id>-<short-description>` 含 issue 编号）。完整 5 类用途见 [docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md](docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md)。

### G1 worktree-required（PreToolUse hook 强制）

- 起新分支**必须**用 `git -C develop worktree add ../<dir> -b <branch> develop`
- **禁用** `git checkout -b` / `git switch -c`（`.claude/scripts/guard-git-workflow.ps1` PreToolUse hook 拦截 exit code 2）

### G2 base=develop-except-hotfix（PreToolUse hook 强制）

- `feature / bugfix / documentation / maintain` 分支 PR 必须 `gh pr create --base develop`
- 仅 `hotfix/*` 分支允许 `--base main`
- 缺 `--base` 时 hook 拦截 + 提示

事故起源：PR #158（缺 `--base` 误合 main）+ PR #154（`git checkout -b` 非 worktree-add）；3 层防御设计见 [plans/[PLAN]_g1_g2_workflow_enforcement.md](plans/[PLAN]_g1_g2_workflow_enforcement.md)。

---

## Commit 规范

### 格式

```
<type>(<scope>): <summary>

[可选正文 — 解释变更原因，不超过 72 字符/行]

[可选脚注 — 如 Refs: #12]
```

### Type

| 类型 | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `perf` | 性能优化 |
| `refactor` | 重构（不改外部行为） |
| `test` | 测试相关 |
| `docs` | 文档变更（`docs/**` / `README.md` / `CHANGELOG.md` / `CONTRIBUTING.md` / `GLOSSARY.md` / `CLAUDE.md`） |
| `infra` | 基础设施（CI / Docker / 依赖 / 脚本） |

### Scope

mj-agent scope 派生自 `src/mj_agent/` 模块（如 `agent` / `llm` / `tools` / `skills` / `prompts` / `middleware` / `memory` / `integrations` / `server` / `ui`）+ 基础设施 scope（`docker` / `ci` / `deps`）+ 文档 scope（`rule` / `guide` / `adr`）。完整 scope allowlist + 示例见 [docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md](docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md) §4。

### 示例

```
feat(agent): wire handle_sql_tool_errors middleware in make_graph
fix(tools): clarify L1 guardrail regex for biz_dwd allowlist
perf(memory): batch checkpointer writes within single graph step
refactor(llm): factor make_llm provider branches into factory
infra(ci): bump python-version matrix to 3.13
docs(guide): add Quick_Start_Setup 5-min version
```

---

## PR 流程

### 推送分支（双远端）

mj-agent 双推 GitHub（`origin`）+ Gitee（`gitee`）镜像；PR 仅在 GitHub 开：

```bash
git push -u origin <branch>
git push -u gitee  <branch>      # 镜像，可后推
```

详细推送清单见 [docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md](docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md)。

### 创建 PR

```bash
gh pr create --base develop --head <branch> --title "<type>(<scope>): <summary>" --body "..."
```

- **必须**带 `--base develop`（G2 hook 拦截）—— 仅 `hotfix/*` 允许 `--base main`
- PR body 推荐用 ` ## Summary` + `## Test plan` + `## PR 门禁自检` 三段；详细字段说明见 [docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md](docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md)

### 响应 Review

- **Approve** → 维护者执行 `gh pr merge <PR_NUM> --squash`（默认 squash；非 squash 需 PR body 注明）
- **Request changes** → 本地修复后 `git push`，旧 Approve 自动失效，需重新 review

---

## Code Review 标准

| 检查项 | 说明 |
|---|---|
| 代码逻辑正确 | 无明显 bug；变更范围与 PR 描述一致 |
| Commit message 规范 | 符合 `<type>(<scope>): <summary>` 格式（见 §3） |
| 无硬编码 | IP / 端口 / 密码 / 绝对路径全部走 `.env` / pydantic-settings |
| 无调试残留 | 无 `print` / `breakpoint` / `TODO hack` |
| 变更原子性 | 每个 PR 只做一件事；混合范围拆为多 PR |
| 文档 PR 门禁 | 触发 A1-A14 时（见 §7）已自检通过 |
| AI 自检 | AI 生成内容已对照 mj-agent 现状验证（无幻觉 / 引用路径有效 / 与既有规范一致） |

> **本地验证 vs AI 自检**严格区分（per [sdd/workflows/execution-loop.md](sdd/workflows/execution-loop.md) §5 本地验证 / §6 AI 自检）：「测试通过」是本地验证，**不是** AI 自检通过；「代码看起来正常」是 AI 自检，**不是** 本地验证。

---

## CI 流水线

每次 push/PR 触发 `.github/workflows/ci.yml`，执行（per [CLAUDE.md §Commands](./CLAUDE.md)）：

| 步骤 | 命令 | 阻塞？ |
|------|------|------|
| 1. 字节码编译 | `python -m compileall` | 是 |
| 2. Lint | `uv run ruff check` | 是 |
| 3. 类型检查 | `uv run mypy src/mj_agent`（strict） | 是 |
| 4. pytest（默认 band） | `uv run pytest` — unit + eval + integration（smoke + contract deselected） | 是 |
| 5. pytest contract | `uv run pytest tests/contract -m contract`（skip-clean if no DB creds） | 是 |

**Smoke 测试**（`-m smoke`）CI 永不跑——需 live biz DB + Ark；仅本地手工跑。

---

## 文档贡献规范

修改 `docs/**` 文档时遵循 mj-agent **三轨道**治理（[policies/documentation.md](policies/documentation.md)）：

| 轨道 | 范围 | 主 STANDARD |
|---|---|---|
| Track A 代码侧 | GUIDE / ADR-code / SPEC-code / RUNBOOK / POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code | [policies/documentation.md](policies/documentation.md) |
| Track B 智能体侧 | in-source SKILL / PROMPT / EVAL / agent-facing CONTRACT | [sdd/adapters/runtime-skill.md](sdd/adapters/runtime-skill.md)（+ [policies/documentation.md](policies/documentation.md) §5.3 门禁） |
| Track C 工程编排侧 | `.claude/skills/mj-agent-*/SKILL.md` / `.claude/settings.json` / `.mcp.json` / 执行闭环 | [sdd/workflows/execution-loop.md](sdd/workflows/execution-loop.md)（+ [sdd/adapters/claude-code-skill.md](sdd/adapters/claude-code-skill.md) for Meta §3.10 / §7.7） |
| Shared 元层 | types / layers / lifecycle / archive / `track` 字段 | [policies/documentation.md](policies/documentation.md)（+ [policies/archive.md](policies/archive.md)） |

### A1-A14 PR 门禁速查

| 编号 | 适用 track | 说明 |
|---|---|---|
| A1-A6 | 全部 | 路径 / frontmatter / state / Wikilink / INDEX / CLAUDE.md sync（hygiene 通用） |
| OB1-OB5 | 全部 | 非阻塞观察（长度 / 时态 / 边界 / 摘要 / 内部一致性） |
| A7-A10 | agent | in-source SKILL / PROMPT / EVAL / CONTRACT 专属 |
| A11 | agent | `state: active` SKILL `eval_references` 非空（Phase 2 起强制） |
| A12 | engineering-workflow | `.claude/skills/` ADR-013 native schema 合规 + description 质量 |
| A13 | engineering-workflow | `.claude/settings.json` 不裸 `Bash` 通配 + secret pattern 进 deny |
| A14 | engineering-workflow | `.mcp.json` server 增删声明 trust posture + credential mode |

### 项目根 5 文件例外

项目根 `README.md` / `CONTRIBUTING.md` / `CHANGELOG.md` / `GLOSSARY.md` / `CLAUDE.md` **不进入 canonical 治理表**（不写 frontmatter；不强制 body 骨架；A1-A3 不适用；A4 + A6 仍适用；语法约束见 GitHub_Markdown §14）。`AGENTS.md`（AI agent 指令契约）同为根操作文件例外，同样处理（per ADR-035）。详见 [policies/documentation.md §2.6](policies/documentation.md)。

### 新文档默认值

- `state: draft`（active 需 reviewer 单独 promote）
- STANDARD / SPEC / EVAL / CONTRACT / ASSESSMENT 类的 `version` 初始 `v1.0`；GUIDE 初始 `v0.1`
- frontmatter 用 mj-agent native 字段（**不**引入 `revision:` 等 mj-agent 无的字段）

---

## 相关文档

| 主题 | 文档 |
|------|------|
| 分支策略详解 | [Git Branch Strategy](docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md) |
| 推送工作流 | [Git Push Workflow](docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md) |
| Commit 规范完整版 | [Commit Message Convention](docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md) |
| PR 描述字段详解 | [PR Description Convention](docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md) |
| HITL 17-stage 执行闭环 | [sdd/workflows/execution-loop.md](sdd/workflows/execution-loop.md) |
| 三轨道文档治理 | [policies/documentation.md](policies/documentation.md) |
| GitHub Markdown 语法 | [GitHub Markdown v1.1](docs/rule/[STANDARD]_GitHub_Markdown.md) |
| 文档总入口 | [docs/INDEX.md](docs/INDEX.md) |
| 术语表 | [GLOSSARY.md](GLOSSARY.md) |

---

> **派生说明**：本文档结构借鉴 mj-system `CONTRIBUTING.md` 8 段「摘要 + 跳转」模式，所有命令 / 类型 / scope / 矩阵均按 mj-agent 自身资产派生。跨项目 attribution 见 [docs/glossary/upstream_business_warehouse.md](docs/glossary/upstream_business_warehouse.md) §跨项目文档治理结构借鉴 attribution。
