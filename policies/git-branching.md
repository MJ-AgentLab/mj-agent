---
type: policy
artifact: git-branching
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: Git Branching

> Phase M0 skeleton — branch type / commit type / G1/G2 worktree 规则.
> 完整 11 branch type（Phase 6 扩充）+ 历史事故记录 + G1/G2 enforcement 在 Phase M2 内容填充.

## §1 Branch Types

当前 mj-agent 5 branch type（per `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`
§5；本 policy 由 Phase M5 平移此 STANDARD 时整合）：

- `feature/`（新功能 / 新 skill / 新 tool / 重构）
- `bugfix/`（develop 上发现 bug 修复）
- `documentation/`（仅文档变更）
- `maintain/`（CI/CD / Docker / deps / scripts / 配置）
- `hotfix/`（生产紧急修复；base = main）

Phase M6 扩充至 11 type（per blueprint §§21 关键变更汇总）：
+ `optimization/` / `release/` / `archive/` / `runtime/` / `data/` / `agent/`.

> TBD: Phase M5 平移 — Commit Message Convention v1.0 § Branch ↔ commit-type alignment matrix.

## §2 Commit Types

| Type | 用途 |
|---|---|
| `feat` | 新功能 |
| `fix` | bug 修复 |
| `perf` | 性能优化 |
| `refactor` | 重构（行为不变） |
| `test` | 测试 |
| `docs` | 文档 / ADR |
| `infra` | CI/CD / Docker / scripts / 配置 |

> TBD: Phase M6 — 扩充至 11 commit type（与 11 branch type 对齐矩阵）.

## §3 G1 / G2 Worktree Rules

### G1 — 新分支必须 `git worktree add`

新分支用：

```bash
git worktree add ../<branch-name> -b <branch-name>
```

**禁止** 在已有 worktree 中 `git checkout -b` / `git checkout -B` / `git switch -c` /
`git switch -C`. bugfix 同样适用.

执行机制：`.claude/scripts/guard-git-workflow.ps1` PreToolUse hook 拦截 `git checkout -b`.

### G2 — base = develop（除 hotfix）

PRs from `feature/` / `bugfix/` / `documentation/` / `maintain/` **必须** `--base develop`；
只有 `hotfix/` 才 `--base main`.

执行机制：同 G1 hook + PR template + `mj-agent-git-pr` skill 自动填 `--base`.

### 历史事故

- PR #158（2026-05-12）：`maintain/...` 误合到 main（缺 `--base develop` 显式）→ 触发 G2 立规
- PR #154（2026-05-12）：`git checkout -b` 而非 `git worktree add` → 触发 G1 立规
- 后续：PR #159 sync develop ← main 修复；`plans/[PLAN]_g1_g2_workflow_enforcement.md` 根因
  分析 + 3 层防御设计

> TBD: Phase M2 — G1/G2 与 mj-agent-git-* skill family enforcement 详细联动表.

## §4 PR Template + Commit Message Validation

PR-body templates live in `.github/PULL_REQUEST_TEMPLATE/` (6 files). This section is
the **rule-level summary** (M6 X6 — absorbed from
`docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`, which keeps the
operational how-to: per-template field detail, `gh` CLI usage, self-check ↔
code-review alignment).

### §4.1 Template × branch type × target branch (per G2)

| Template | Branch type | Target | Scenario |
|---|---|---|---|
| `feature.md` | `feature/*` | develop | new skill / tool / prompt / refactor |
| `bugfix.md` | `bugfix/*` | develop | bug found on develop |
| `documentation.md` | `documentation/*` | develop | docs-only |
| `maintain.md` | `maintain/*` | develop | CI/CD / deps / scripts / config |
| `hotfix.md` | `hotfix/*` | **main** | production emergency |
| `release.md` | develop → main | **main** | version release (Phase 1+; see `policies/release`) |

`gh pr create --base <develop|main> --template <name>.md` — base is `develop` for all
except `hotfix` / `release` → `main` (G2).

### §4.2 Branch type × allowed commit type (PR self-check verifies)

| Branch type | Allowed commit types |
|---|---|
| `feature/*` | feat / perf / refactor / test / docs |
| `bugfix/*` | fix / test / docs |
| `documentation/*` | docs |
| `maintain/*` | infra / docs |
| `hotfix/*` | fix |

Full commit-type allowlist + branch↔commit alignment matrix:
`docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §4-§5.

> TBD: Phase M2 — automated commit-message regex validation (CI gate).

## §5 与 SDD Workflows 联动

| Branch type | Workflow（per `sdd/workflows/`） |
|---|---|
| `feature/` 新 capability | `new-capability.md` |
| `feature/` 演进 capability | `evolve-capability.md` |
| `bugfix/` | `bugfix-drift.md` |
| `feature/` / `maintain/` 跨 capability | `cross-capability-change.md` |
| `hotfix/` | `hotfix.md` |
| `documentation/` archive ceremony | `archive-capability.md` |

---

> *Phase M0 skeleton — Phase M5 整合 Commit Message Convention STANDARD 时大幅扩充.*
