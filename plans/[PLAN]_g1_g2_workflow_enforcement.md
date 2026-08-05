---
type: plan
summary: 把 G1 (新分支必须 worktree)、G2 (gh pr create 必须 --base) 两条 mj-agent git workflow 约定从纯文档约束升级为 3 层运行时强制 — L1 SKILL.md HARD REQUIREMENT + L2 CLAUDE.md Repo conventions + L3 .claude/scripts/guard-git-workflow.ps1 PreToolUse hook；起源于 2026-05-12 同日发生的 PR #154 (bugfix 用 git checkout -b) 与 PR #158 (gh pr create 缺 --base 误合到 main) 两起 precipitating incident
owner: ranzuozhou
created: 2026-05-13
updated: 2026-08-05
state: completed
track: engineering-workflow
---

# [PLAN] G1 / G2 Git Workflow Enforcement (worktree-required + base-develop)

> 把两条只写在文档里的 git 约定升级为 PreToolUse hook 硬约束，并把 commit message + 文档里的悬空引用 `plans/pasted-text-1-21-valiant-deer.md` 替换为本 plan 文件。

## 1. Linked Artifacts

- 起源 PR：
  - **PR #154** (`bugfix/sql-tool-error-middleware`, merged 2026-05-12 21:27) — first commit `af0e81d` 创建于 2026-05-12 17:58，在已存在 worktree 中用 `git checkout -b` 创建（非 worktree-add 路径）；当时**无 G1 规则**，属 precipitating incident
  - **PR #158** (`maintain/env-memory-port-default-flip`, merged 2026-05-12, commit `9cd82d2`) — `gh pr create` 缺 `--base` 旗标，被 fallback 到 GitHub repo default branch (`main`)，导致非-hotfix 分支误合到 main
  - **PR #159** (`maintain/sync-develop-with-main-post-pr-158`, merged 2026-05-12, commit `ccd6998`) — 修复 PR #158 漂移：把 develop fast-forward 到 main
- 起源 commit：
  - **`ed785b6`** (`infra(infra): enforce G1/G2 git workflow via PreToolUse hook`, 2026-05-12 23:49) — 3 层防御首发；本 plan 里的 Step 2 / Step 3 是其 follow-up
- 相关 STANDARD：
  - [[../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention v1.0]] §5（5 分支类型 ↔ commit type ↔ PR base 对应矩阵）
  - [[../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]] §1（17-stage flow；G1 = Stage 2 / G2 = Stage 14 落地点）
- 相关 ADR：
  - [[../docs/adr/[ADR]_010_Adopt_MJ_System_Git_Conventions|ADR-010]] (mj-agent 采纳 MJ-AgentLab 5-branch-type 模型 + worktree-per-branch)
  - [[../docs/adr/[ADR]_013_In_Tree_Skill_Native_Schema|ADR-013]] (`.claude/skills/mj-agent-*` 2-field native schema 治理；本 plan 改的 2 个 SKILL.md 在该 schema 下)
- in-tree skills referenced：
  - `.claude/skills/mj-agent-git-branch/SKILL.md`（HARD REQUIREMENT G1 块）
  - `.claude/skills/mj-agent-git-pr/SKILL.md`（HARD REQUIREMENT G2 块）

## 2. Context

### 2.1 双 incident 时间线（2026-05-12）

```text
17:58:23  bugfix/sql-tool-error-middleware first commit (af0e81d)
                ↑ 用 git checkout -b 在已存在 worktree 中创建
                ↑ G1 规则当时不存在
21:27:17  PR #154 merged → develop
22:xx     maintain/env-memory-port-default-flip first commit
22:xx     gh pr create (无 --base) → base = repo default = main
22:xx     PR #158 merged → main (应该到 develop)
23:xx     发现漂移：develop 落后于 main (含 PR #158 的 PORT 翻转)
23:xx     PR #159 (sync develop ← main) merged → 修复漂移
23:49:36  ed785b6 commit — G1/G2 3 层防御首发
```

### 2.2 根因

两起 incident 的共同根因是 **mj-agent 约定只写在 CLAUDE.md / SKILL.md 文档层，缺乏运行时硬约束**：

| Incident | 根因 | 修复 |
|---|---|---|
| PR #154 G1 漂移 | `git checkout -b` 与 `git worktree add` 行为外观相似，CLAUDE.md 的"5-branch-type + worktree-per-branch" 约定未在工具层硬性区分 | L3 PreToolUse hook 在执行前 block `git checkout -b` / `git switch -c` |
| PR #158 G2 漂移 | gh CLI 默认 base = GitHub repo default branch (`main`)，而 mj-agent 集成线是 `develop` —— 默认值与约定相反 | L3 PreToolUse hook 在执行前 block 缺 `--base` 的 `gh pr create` |

### 2.3 nuance：PR #154 是 incident 不是 violation

`ed785b6` commit message 把 PR #154 列为 "G1 violation"，但严格按时间线：

- 17:58 bugfix branch 创建（用 checkout -b）
- 23:49 G1 规则诞生（hook 落地）

PR #154 创建时 G1 还不存在，称作 violation 不严谨。本 plan 的措辞统一为 **precipitating incident**（"促发事件"），表达"这次事件促使我们立法"而非"违反了已存在的规则"。

## 3. 3 层防御设计（ed785b6 已完成 + 本 plan 后续）

| 层 | 内容 | 文件 | 状态 |
|---|---|---|---|
| L1 提示层 | `mj-agent-git-branch` / `mj-agent-git-pr` SKILL.md 顶部 HARD REQUIREMENT block | `.claude/skills/mj-agent-git-{branch,pr}/SKILL.md` | ed785b6 ✓ + 本 plan Step 3 措辞纠正 |
| L2 规范层 | CLAUDE.md "Repo conventions" 定义 G1+G2 并引用 hook | `CLAUDE.md` | ed785b6 ✓ + 本 plan Step 3 引用更新 |
| L3 运行时层 | PreToolUse hook (PowerShell) 拦截违规 Bash 命令 | `.claude/scripts/guard-git-workflow.ps1` + `.claude/settings.json` | ed785b6 ✓ + 本 plan Step 2 收紧 `-B`/`-C` |

### 3.1 hook 协议

- **触发**：`.claude/settings.json` 中 `hooks.PreToolUse[].matcher: "Bash"` 把所有 `Bash` 工具调用走 hook
- **输入**：stdin JSON（含 `tool_input.command`）
- **退出码**：`0` = allow（命令继续执行），`2` = block（命令被拦下，stderr 反馈给 agent）
- **非 JSON stdin**：exit 0（兼容手工测试 / 非 Claude Code 调用）

### 3.2 正则覆盖（本 plan Step 2 后）

| 规则 | 正则 | 覆盖 |
|---|---|---|
| G1-checkout | `(^\|[\s;&\|])git\s+checkout\s+-[bB]\b` | `git checkout -b foo` ✓ / `git checkout -B foo`（force-recreate）✓ |
| G1-switch | `(^\|[\s;&\|])git\s+switch\s+-[cC]\b` | `git switch -c foo` ✓ / `git switch -C foo`（force-recreate）✓ |
| G1-exempt | 上述 2 条均要求 `git\s+(checkout\|switch)` 直接相邻 | `git worktree add ../foo -b foo` ✓ exempted（`worktree add` 截断 `git`→`-b` 链） |
| G2 | `(^\|[\s;&\|])gh\s+pr\s+create\b` AND NOT `(^\|\s)(--base\|-B)(\s\|=)` | `gh pr create` 缺 base block ✓ / `--base develop`、`-B main`、`--base=develop` 三种语法 allow ✓ |

### 3.3 covered / not covered

| 命令 | 期望 | 覆盖来源 |
|---|---|---|
| `git checkout -b foo` | block | G1-checkout |
| `git checkout -B foo` | block | G1-checkout (本 plan Step 2 新覆盖) |
| `git switch -c foo` | block | G1-switch |
| `git switch -C foo` | block | G1-switch (本 plan Step 2 新覆盖) |
| `gh pr create` | block | G2 |
| `gh pr create --title x` | block | G2 |
| `git worktree add ../foo -b foo` | allow | G1-exempt |
| `gh pr create --base develop` | allow | G2 |
| `gh pr create -B main` | allow | G2 |
| `gh pr create --base=develop` | allow | G2 |
| `echo "git checkout -b foo"` | allow | 引号内字符串不算 shell 命令边界 |
| `gh pr create --base-url X`（gh CLI 无此旗标）| 当前 allow | academic / out of scope |
| `GH pr create`（大写）| 当前 allow | academic / 实际 gh CLI 区分大小写 |

## 4. 本 plan 5 步执行

### Step 1 — 落地本 plan 文件本身

新建 `plans/[PLAN]_g1_g2_workflow_enforcement.md`（即本文件），作为根因 + 防御设计 + 时间线的 durable 沉淀。

### Step 2 — 收紧 G1 正则

`.claude/scripts/guard-git-workflow.ps1` 行 39-40：

```diff
-if ($cmd -match '(^|[\s;&|])git\s+checkout\s+-b\b' -or `
-    $cmd -match '(^|[\s;&|])git\s+switch\s+-c\b') {
+if ($cmd -match '(^|[\s;&|])git\s+checkout\s+-[bB]\b' -or `
+    $cmd -match '(^|[\s;&|])git\s+switch\s+-[cC]\b') {
```

回归 0 风险：字符类 `[bB]` / `[cC]` 兼容旧用例（block 行为不变）+ 新增大写 force-recreate 块。

### Step 3 — 修复 3 处悬空引用 + 措辞纠正

| 文件 | 行 | 变更 |
|---|---|---|
| `CLAUDE.md` | 407 | 路径 `pasted-text-1-21-valiant-deer.md` → `[PLAN]_g1_g2_workflow_enforcement.md` |
| `.claude/scripts/guard-git-workflow.ps1` | 11 | 同上路径替换 |
| `.claude/skills/mj-agent-git-branch/SKILL.md` | 29-30 | 路径替换 + 措辞 "G1 violation" → "G1 规则诞生前的 precipitating incident" |

`ed785b6` commit message 里的旧路径不可改，但 PR #154/#158 引用仍指向真实 PR。

### Step 4 — 11 cases smoke test

| # | command | 期望 |
|---|---|---|
| B1 | `git checkout -b foo` | block (G1) |
| B2 | `git switch -c foo` | block (G1) |
| B3 | `git checkout -B foo` | **block (G1, 新)** |
| B4 | `git switch -C foo` | **block (G1, 新)** |
| B5 | `gh pr create` | block (G2) |
| A1 | `git worktree add ../foo -b foo` | allow |
| A2 | `gh pr create --base develop` | allow |
| A3 | `gh pr create -B main` | allow |
| A4 | `gh pr create --base=develop` | allow |
| A5 | `git status` | allow |
| A6 | `echo "git checkout -b"` | allow |

调用方式：

```bash
echo '{"tool_input":{"command":"<CMD>"}}' \
  | pwsh -NoProfile -File .claude/scripts/guard-git-workflow.ps1
echo "exit=$?"
```

通过门槛：11/11 命中期望（block 5 + allow 6）。

### Step 5 — commit + push + PR

```bash
# Stage 11 self-review HITL → user OK
# Stage 12 commit
git add plans/[PLAN]_g1_g2_workflow_enforcement.md \
        CLAUDE.md \
        .claude/scripts/guard-git-workflow.ps1 \
        .claude/skills/mj-agent-git-branch/SKILL.md
git commit -m "..."

# Stage 13 push HITL → user OK
git push -u origin documentation/git-workflow-enforcement

# Stage 14 PR (G2 self-witness: 必须 --base develop)
gh pr create --base develop --title "..." --body-file <(...)
```

## 5. Verification

1. **Hook smoke**（Step 4 11 cases，本地 pwsh）— 100% 通过为门槛；输出粘进 PR 描述
2. **G2 self-witness**：本 PR 的 `gh pr create` 自己用 `--base develop`；如果忘传，hook 在 PreToolUse 拦下 `[G2 VIOLATION]` —— PR 创建过程本身就是验证
3. **可逆性**：所有改动局限于 `.claude/`、`CLAUDE.md`、`plans/*` —— 不触碰 `src/mj_agent/`、`tests/`、`infra/docker/`，CI 三 gates (ruff / mypy / pytest) 不受影响
4. **悬空引用清零**：merge 后 `grep -r 'pasted-text-1-21' --exclude-dir=.git` 仅在历史 commit message 中出现，工作树 0 命中

## 6. Out of Scope

- G2 正则 `--base-url` / 大写 `GH` 边缘案例（academic，gh CLI 实际不支持）
- hook 加 CI 测试（pwsh 在 Linux runner 配置复杂；smoke 手工跑足够）
- 任何 `src/mj_agent/`、tests、docker 编排改动
- 把本 plan 升格为 ADR（如有未来回顾需要可再升格；本次先以 plan 形式沉淀）
- 工作流外其他 git 命令的 hook 覆盖（`git push --force`、`git rebase -i` 等 — 未来若再发生 incident 再扩展正则）
