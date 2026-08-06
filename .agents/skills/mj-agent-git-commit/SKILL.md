---
name: mj-agent-git-commit
description: This skill should be used when the user asks to stage files, create commits, write commit messages, check commit format, split changes into logical commits, or prepare code before push in mj-agent. Make sure to use this skill whenever the user says "git add", "git commit", "提交代码", "暂存文件", "commit message", "提交格式", "拆分提交", "准备提交", "stage files", "怎么写 commit", "提交规范" in the mj-agent context. Enforces type(scope) summary format + 35-scope closed allowlist + branch-type discipline at commit time, preventing rework at push stage. Do not use for: branch creation (use mj-agent-git-branch), push (use mj-agent-git-push), PR creation (use mj-agent-git-pr), or amending an already-pushed commit (handle via interactive rebase + force-push directly).
---

# mj-agent Git Commit

## Overview

暂存文件并创建符合 [[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention v1.1]] 规范的 Git 提交。6 步 Pre-Commit 工作流覆盖文件筛选、暂存策略、commit message 格式校验、type/branch 纪律（5 branch × 7 type 矩阵）、35 scope 闭合 allowlist 推导、拆分指导。衔接 `/mj-agent-git-branch`（创建分支）与 `/mj-agent-git-push`（推送）之间的缺口。

**Workflow position**: Stage 12 of HITL_Prompt 17-stage flow.

## 前置条件

- 在 mj-agent worktree 内执行（bare repo 根目录无 working tree）
- 当前分支为临时分支（feature/bugfix/documentation/maintain/hotfix），不在 `main` 或 `develop` 上直接提交

## 快速开始（交互模式）

| 已知信息 | 行动 |
|---|---|
| 用户说"提交"但未说明提交什么 | 跑 `git status --short`，展示修改列表，询问"全部提交还是部分？" |
| 有修改文件，但变更性质不明 | 询问："这次修改是 feat / fix / perf / refactor / docs / test / infra？" |
| 变更性质明确，未提供 scope | 从修改文件路径推断 scope（见 Step 3 推导表），不追问 |
| 信息完整 | 直接生成 commit 命令 |

---

## Pre-Commit Workflow（6 步）

### Step 1 — Verify Working Location

```bash
git branch --show-current
# 必须返回 feature/bugfix/documentation/maintain/hotfix 之一；
# 若 main / develop → STOP (H5)

git worktree list
# 确认在某个 worktree 内
```

### Step 2 — Review Changes & File Selection

```bash
git status --short
git diff             # 未暂存差异
git diff --cached    # 已暂存差异
```

**文件排除规则**（mj-agent 专属）：

| 模式 | 原因 | 发现后行为 |
|---|---|---|
| `.env` | 含 ARK_API_KEY / POSTGRES_PASSWORD / LANGSMITH_API_KEY | **H1**: 硬性阻断 |
| `secrets.enc` 解密产物（如临时 .env.decrypted） | 团队口令解密的明文 | **H1**: 硬性阻断 |
| `*.pem` / `*.key` / `*.p12` | 私钥 / 证书 | **H1**: 硬性阻断 |
| 文件 > 10 MB | 大文件不宜入 git | **H2**: 询问用户 |
| `__pycache__/` / `*.pyc` / `.venv/` | Python 运行时 | 静默跳过 |
| `.claude/settings.local.json` | 个人配置（已 gitignore） | 静默跳过（不应在 staged 里） |
| `.worktrees/` | bare repo worktree 目录 | 静默跳过 |

**暂存策略**：

```bash
# 推荐：按文件名逐个暂存（最安全）
git add src/mj_agent/skills/biz-domain-context/SKILL.md

# 可接受：按目录暂存（该目录全部文件都应提交时）
git add src/mj_agent/skills/biz-domain-context/

# 可接受：仅暂存已追踪的修改文件
git add -u

# 避免：git add -A 或 git add .（会暂存所有未追踪文件，含可能漏掉的本地文件）
```

### Step 3 — Compose Commit Message

**格式**：`<type>(<scope>): <summary>`

**规则**（参 Commit Convention §2）：

1. `type` ∈ `{feat, fix, perf, refactor, test, docs, infra}`（小写）
2. `scope` ∈ 35 闭合 allowlist（小写）
3. `:` 后加一个空格
4. `summary` 不以句号结尾，不超过 72 字符
5. 中英文均可

**Scope 推导**（参 Commit Convention v1.1 §4，闭合 allowlist 35 项）：

| 修改路径模式 | Scope |
|---|---|
| **代码面 —— `src/mj_agent/`（§4.1，14 项）** | |
| `agent.py` / `runtime.py` / `state.py` / graph 装配 | `agent` |
| `llm.py` / provider 工厂 | `llm` |
| `config.py` / `env_drift.py` | `config` |
| `prompts/`（in-source canonical） | `prompt` |
| `skills/`（in-source canonical） | `skill` |
| `tools/sql/` | `sql` |
| `tools/` 下 `sql/` 以外（`analysis/` `charts/` `excel/` `biz_context.py`） | `tools` |
| `integrations/` | `db` |
| `memory/` | `memory` |
| `middleware/` | `middleware` |
| `biz_catalog/` | `biz_catalog` |
| `entity/` | `entity` |
| `server/` | `server` |
| `ui.py` | `ui` |
| **工程 / 测试 / 构建（§4.2.1，10 项）** | |
| `tests/{unit,integration,smoke,fixtures}/` / `conftest.py` | `tests` |
| `tests/bdd/` / `capabilities/**/behavior.feature` | `bdd` |
| `capabilities/**/contracts/` / `tests/contract/` | `contract` |
| `tests/eval/` / `[EVAL]` 关联代码 | `eval` |
| `.github/`（workflows / ISSUE_TEMPLATE / PR 模板 / dependabot） | `ci` |
| `pyproject.toml` / `uv.lock` | `deps` |
| `docker/` / `.dockerignore` | `docker` |
| `scripts/`（含 `scripts/sdd/`） | `scripts` |
| `.claude/` / `.mcp.json` / `.claudeignore` | `claude` |
| `AGENTS.md` / `.agents/` / `.codex/` / `.agents.lock.json` | `agents` |
| **文档 / 治理（§4.2.2，10 项）** | |
| `sdd/` | `sdd` |
| `policies/` | `policies` |
| `decisions/` / `archive/decisions/` | `decisions` |
| `plans/` | `plans` |
| `capabilities/`（其 `contracts/` `evidence/` 另有 scope） | `capabilities` |
| `evidence/` / `capabilities/**/evidence/` | `evidence` |
| `docs/rule/` / `docs/_templates/` | `rule` |
| `docs/guide/` / `docs/infrastructure/**` / `docs/_baselines/` | `guide` |
| `docs/glossary/` / `GLOSSARY.md` | `glossary` |
| `archive/`（归档仪式本身） | `archive` |
| **兜底（§4.2.3，1 项）** | |
| 根 `config/`（secrets pipeline）/ `.env.example` / `langgraph.json` / `.gitignore` | `infra` |
| **跨区域混合**（含 `.claude/**` + `.github/**`、跨多个治理目录） | **省略 scope**（§4.4） |

> **重要**：scope 是闭合 allowlist；引入新 scope 必须修订 `[STANDARD]_MJ_Agent_Commit_Message_Convention`（minor 版本号 bump），且**由引入该目录 / 子系统的那个 PR 同批更新**（v1.1 §4.5 责任归属条款）。
>
> **三条硬禁止**（v1.1 §4.3）：`docs` 不得作 scope（用所在区域的 scope，如 `docs(sdd)`）；不得以 **type** 作 scope（`refactor` / `test` / `feat` 属 type 命名空间）；不得以**项目阶段 / 里程碑**作 scope（如 `stage-e` / `phase0`）——阶段信息写进 summary 或 body。
>
> **历史别名**：读旧 commit 时参 v1.1 §4.6 映射表（如 `plan`→`plans`、`adr`→`decisions`、`skill-index`→`claude`）。注意 `skill` scope **专指** `src/mj_agent/skills/`，`.claude/skills/` 归 `claude`。

### Step 4 — Enforce Type/Branch Discipline

```bash
git branch --show-current
# 提取分支类型前缀
```

| 分支类型 | 允许的 Commit 类型 | 常见误用 |
|---|---|---|
| `feature/*` | `feat` / `perf` / `refactor` / `test` / `docs` | `fix` / `infra` |
| `bugfix/*` | `fix` / `test` / `docs` | `feat` / `perf` / `refactor` / `infra` |
| `documentation/*` | `docs`（仅此一项） | 其他所有 |
| `maintain/*` | `infra` / `docs` | `feat` / `fix` / `perf` / `refactor` |
| `hotfix/*` | `fix`（仅此一项） | 其他所有 |

> mj-agent **不**用 `optimization/`（与 mj-system 差异）

**若不匹配** → H3。

### Step 5 — Evaluate Split Necessity

**拆分信号**（任一触发即评估）：

| 信号 | 示例 | 动作 |
|---|---|---|
| 暂存文件跨 2+ 不相关 scope | `agent` 代码 + `prompt` 改动 | 按 scope 拆分 |
| 代码 + 文档涉不同主题 | Python 代码 + Docker 文档 | 分开提交 |
| 混合 feat + refactor | 新 skill + 重构旧代码 | 按 type 拆分 |
| in-source SKILL/PROMPT 改动 + 纯代码 | SKILL.md body + agent.py | **必拆**（B 风味永远 HITL；C 风味属 infra） |
| 差异 > 300 行跨 5+ 文件 | 大型重构 | 按逻辑单元拆分 |

**不应拆分**：功能代码 + 其测试；< 5 文件 < 100 行单一 scope。

### Step 6 — Execute Commit

```bash
# 最终确认
git diff --cached --stat
git branch --show-current

# 提交
git commit -m "<type>(<scope>): <summary>"
# 长描述用 heredoc：
git commit -m "$(cat <<'EOF'
<type>(<scope>): <summary>

<long body>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

# 验证
git log --oneline -1
git status --short
```

---

## Multi-scope Rules（Commit Convention §4.4）

| 情况 | 范围选择 |
|---|---|
| 所有文件在同一 scope | 用该 scope |
| 跨 scope 但同一层（如 SQL guardrail + execute） | 用层 scope（`sql`） |
| 基础设施 + 关联文档 | 用基础设施 scope（`ci` / `deps` / `infra`） |
| 真正混合无主导 scope | **省略 scope**：`docs: <summary>` 或 `feat: <summary>` |

---

## 人工介入场景（STOP & ASK）

| # | 触发条件 | 技能行为 |
|---|---|---|
| **H1** | `.env` / `secrets.enc` 解密产物 / 私钥在暂存区 | **硬性阻断**（不提供"继续"选项）：展示文件名 + 警告 + `git reset HEAD <file>` |
| **H2** | 大文件（>10 MB）在暂存区 | 展示文件名 + 大小，询问是否确认 |
| **H3** | Commit type 与 branch type 不匹配 | 展示允许列表 + 提供 (1) 修改 type (2) 确认例外 |
| **H4** | 暂存区为空但用户要求提交 | 告知暂存区为空 + 展示 `git status --short` |
| **H5** | 当前分支为 `main` 或 `develop` | **硬性阻断**：拒绝提交，告知切换到工作分支 |
| **H6** | Commit message 不符合格式（缺 type / scope 不在 allowlist / summary 含句号 / 大写 / > 72 chars） | 展示格式要求 + 修正建议 |
| **H7** | 检测到可拆分的大变更（Step 5） | 建议拆分方案，询问是否拆分 |
| **H8** | 暂存区含 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/system.md` body 改动 | 提示：B 风味 in-source canonical 改动是 §3.1 必停 HITL 项；建议先 `/mj-agent-runtime-skill-doc-improve` 或 `/mj-agent-runtime-prompt-version-bump`（PR-C2 落地）propose diff |

> **H1** + **H5** 是硬性阻断（不提供"继续"选项）。其他场景允许用户覆盖。

---

## 示例

### 示例 1：常规 feature 提交

```bash
# 当前在 feature/63-add-flow-intake-skill worktree
git branch --show-current   # → feature/63-add-flow-intake-skill ✓

git status --short
# A  .claude/skills/mj-agent-flow-intake/SKILL.md

# Step 3-4: type=docs（feature 分支允许 docs）, scope=省略（跨子系统）
git add .claude/skills/mj-agent-flow-intake/SKILL.md
git commit -m "docs: add mj-agent-flow-intake workflow skill"
```

### 示例 2：需要拆分的 maintain 提交

```bash
# 当前在 maintain/update-ci-and-docs

git status --short
# M  .github/workflows/ci.yml
# M  pyproject.toml
# M  docs/infrastructure/cicd/release.md

# Step 5: CI + deps + docs → 拆 3 个 commit
git add .github/workflows/ci.yml
git commit -m "infra(ci): bump actions/checkout to v4.1"

git add pyproject.toml uv.lock
git commit -m "infra(deps): bump langgraph 1.1.8 → 1.1.9"

git add docs/infrastructure/cicd/release.md
git commit -m "docs: update release process for v0.2"
```

### 示例 3：H3 触发（type 与 branch 不匹配）

```bash
# 当前在 bugfix/qcm-yaml-encoding
# 用户想提交：feat(skill): add new metric

# Step 4 检测：feat ∉ bugfix/* 允许列表 [fix, test, docs]
# H3 触发：
# 「当前分支 bugfix/qcm-yaml-encoding 仅允许 fix/test/docs。
#   你使用了 feat。选择：
#   (1) 修改为 fix(skill): fix metric registration on Chinese qcm names
#   (2) 确认例外并继续」
```

### 示例 4：H8 触发（in-source canonical 改动）

```bash
# 当前在 feature/upgrade-biz-domain-skill
git status --short
# M  src/mj_agent/skills/biz-domain-context/SKILL.md

# Step 5 + H8 触发：
# 「检测到 in-source SKILL.md body 改动（B 风味 implementation；
#   §3.1 必停 HITL 项）。
#   建议先用 /mj-agent-runtime-skill-doc-improve（PR-C2 落地）propose diff，
#   由项目负责人 review 后再 commit。
#   或者：(1) 确认例外，继续 commit  (2) 撤销暂存」
```

## Anti-patterns

- **不要** 用 `git add -A` / `git add .`（误暂存未跟踪文件含 secrets / artifacts）
- **不要** 跳过 Step 4 type/branch matrix 校验（push 阶段 H3 会重新触发，浪费时间）
- **不要** 引入未在 35 闭合 allowlist 内的 scope（应该先修订 Commit Convention §4 minor bump）
- **不要** 用 type 当 scope（`refactor` / `test` / `feat`）或用项目阶段当 scope（`stage-e` / `phase0`）——v1.1 §4.3 已明文禁止
- **不要** 在 commit message 中嵌入 `Generated by Claude Code` 之类自动化签名（用 `Co-Authored-By: Claude Opus ...` 标准 trailer）
- **不要** 在 in-source SKILL.md / system.md body 改动时跳过 §3.1 必停 HITL（H8 触发；这是 mj-agent 专属硬约束）

## Handoff to mj-agent-git-push

```
提交完成
下一步：使用 `/mj-agent-git-push` 执行 pre-push 检查（双推 gitee + origin）。
  已验证项：commit message 格式 ✓、type/branch 纪律 ✓、35-scope allowlist ✓
  待检查项：CHANGELOG 更新、工作目录干净、base branch 同步、双推
```
