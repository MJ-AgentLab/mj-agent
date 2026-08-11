---
type: policy
artifact: git-branching
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: Git Branching

> Branch type / commit type / G1/G2 worktree 规则 / PR 模板与 commit-message 校验.
> （原 skeleton 注 "完整 11 branch type（Phase 6 扩充）" 已 DECLINED — 见 §1 Decision 块；
> 维持 5 branch type + 7 commit type。本文件自 v0.2 起**无待填充块**。）

## §1 Branch Types

当前 mj-agent 5 branch type（per `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`
§5；本 policy 由 Phase M5 平移此 STANDARD 时整合）：

- `feature/`（新功能 / 新 skill / 新 tool / 重构）
- `bugfix/`（develop 上发现 bug 修复）
- `documentation/`（仅文档变更）
- `maintain/`（CI/CD / Docker / deps / scripts / 配置）
- `hotfix/`（生产紧急修复；base = main）

> **Decision（2026-06-10；completion-audit PR3；M6-FU-BRANCH-TYPE-5LOCK）**：原蓝图
> "Phase M6 扩充至 11 type（+ `optimization/` / `release/` / `archive/` / `runtime/` /
> `data/` / `agent/`）" **DECLINED — 维持 5 type**。理由：M0-M6 全程 ~70 个 PR 无一需要
> 新类型——archive ceremony 实际走 `documentation/*`（M6 PR4 先例）、release 流程由
> `policies/release.md` 承载（develop→main 不需要专用 branch type）、runtime/data/agent
> 类变更均被 `feature/`+scope 覆盖；空集扩类只增加 guard hook + PR 模板 + CI 触发分支
> 矩阵的维护面。按 `M4-FU-V4-MODE-B-IMPL` WITHDRAWN 先例归档。**复活条件**：连续 ≥3 个
> PR 因类型不匹配被迫误标（如 release 自动化落地后 develop→main 需要专属 CI 触发），由
> owner 重开 ADR 评估。

> **Decision（2026-08-11；#482 / `M6-FU-POLICIES-TBD-SWEEP`）**：原 TBD "Phase M5 平移 —
> Commit Message Convention v1.0 § Branch ↔ commit-type alignment matrix" **已兑现，落点是本
> 文件 §4.2** —— `0bf53bb`（M6 X6，2026-06-08）把 git RULES 吸收进 kernel 时一并带入；5 branch
> type × 允许 commit type 的完整矩阵在那里，与 STANDARD
> `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §5.2 逐行一致。**此处不复制该
> 矩阵** —— 同一张表在同一文件出现两次必然漂移；§2 Decision 块的"对齐矩阵现状见 §4.2"是同一
> 指向。⚠ 原 TBD 写的 STANDARD 版本 `v1.0` 已过时：现为 **v1.1**（#443 把 scope 白名单从 12 项
> 重建为 35 项闭合白名单）。

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

> **Decision（2026-06-10；completion-audit PR3；M6-FU-BRANCH-TYPE-5LOCK）**：扩充至 11
> commit type DECLINED — **维持 7**（与 §1 维持 5 branch type 同决策同理由；对齐矩阵现状
> 见 §4.2）。复活条件同 §1 Decision 块。

## §3 G1 / G2 Worktree Rules

### G1 — 新分支必须 `git worktree add`

新分支用：

```bash
git worktree add ../<branch-name> -b <branch-name>
```

**禁止** 在已有 worktree 中 `git checkout -b` / `git checkout -B` / `git switch -c` /
`git switch -C`. bugfix 同样适用.

执行机制：L3 PreToolUse hook `.claude/scripts/guard-git-workflow.ps1` 拦截 `git checkout -b` /
`-B` 与 `git switch -c` / `-C`（完整判定面 + 边界见 §3.1）.

### G2 — base = develop（除 hotfix）

PRs from `feature/` / `bugfix/` / `documentation/` / `maintain/` **必须** `--base develop`；
只有 `hotfix/` 才 `--base main`.

执行机制：同 G1 hook（拦截缺 `--base` 的 `gh pr create`）+ `mj-agent-git-pr` skill 的
`gh pr create` 示例一律带 `--base`（见 §3.1）. ⚠ **PR body 模板不是本规则的载体** —— 模板管的是
PR 正文，物理上管不到 `gh pr create` 的 `--base` 旗标；`.github/PULL_REQUEST_TEMPLATE/` 里与
target 相关的只有 `hotfix.md` 顶部一句"目标分支为 `main`"的提醒.

### 历史事故

- PR #158（2026-05-12）：`maintain/...` 误合到 main（缺 `--base develop` 显式）→ 触发 G2 立规
- PR #154（2026-05-12）：`git checkout -b` 而非 `git worktree add` → 触发 G1 立规
- 后续：PR #159 sync develop ← main 修复；`plans/[PLAN]_g1_g2_workflow_enforcement.md` 根因
  分析 + 3 层防御设计

### §3.1 执行机制联动表（G1/G2 × `mj-agent-git-*` skill family × hook）

3 层防御框架 per `plans/[PLAN]_g1_g2_workflow_enforcement.md` §3（`ed785b6` 首发）：

| 层 | 载体 | G1 | G2 |
|---|---|---|---|
| L1 提示层 | `.claude/skills/mj-agent-git-branch/SKILL.md` 的 `HARD REQUIREMENT — G1` 块 | ✅ 规则 + `worktree add` 命令模板 | — |
| L1 提示层 | `.claude/skills/mj-agent-git-pr/SKILL.md` 的 `HARD REQUIREMENT — G2` 块 | — | ✅ 分支类型→`--base` 值映射表；全部 `gh pr create` 示例均带 `--base` |
| L1 交接 | `.claude/skills/mj-agent-git-push/SKILL.md` 末步 | — | ⚠ 仅一条指针（"`gh pr create` 显式 `--base`, per policies/git-branching.md G2"），无 HARD REQUIREMENT 块 |
| L2 规范层 | `CLAUDE.md` "Repo conventions" · `AGENTS.md` Self-enforced boundaries 第 5 条 | ✅ | ✅ |
| L3 运行时层 | `.claude/scripts/guard-git-workflow.ps1`（挂载点 `.claude/settings.json` 的 `hooks.PreToolUse` matcher `Bash`） | ✅ 拦截 | ✅ 拦截 |

**family 覆盖面**：`mj-agent-git-*` 共 **9** 个 skill（`branch` / `check-merge` / `commit` /
`delete` / `issue` / `pr` / `push` / `review-pr` / `sync`），其中**只有 `branch`（G1）与 `pr`
（G2）带 HARD REQUIREMENT 块**；`push` 只有上表那条交接指针；其余 6 个不在 G1/G2 面上。

**L3 判定面（从实现取证）**：

| 规则 | 拦截（exit 2） | 放行（exit 0） |
|---|---|---|
| G1 | `git checkout -b` / `-B`、`git switch -c` / `-C`；跨全局选项（`git -C <path> checkout -b`）、跨复合段（`cd sub && git checkout -b`）、混入非 ASCII 文本均照拦 | `git worktree add ... -b`；不带 `-b` 的 `git checkout <branch>`；把 `checkout -b` 写进别的子命令参数（`git commit -m "... checkout -b ..."`）或非 git 段（`echo ...`） |
| G2 | `gh pr create` 未给 base | `--base <v>` / `--base=<v>` / `-B <v>` / `-B=<v>` |

判定是**按 shell 分隔符切段后逐段 token 化**（再跳过 git 全局选项定位子命令位置），**不是**对整条
命令行做正则匹配 —— 上述 plan §3.2 记载的正则表是 `ed785b6` 时的历史快照，已被 #313 PR-2 的
token 实现取代；**引用时以实现为准**。

**输入协议 fail-closed**（dual-agent-compat v5 §5.4 / #313）：stdin 非 JSON、空、缺
`tool_input.command`、`tool_name` ≠ `Bash`、`hook_event_name` ≠ `PreToolUse` —— 一律 **exit 2
拒绝**，绝不静默放行。⚠ 同一 plan §3.1 记载的"非 JSON stdin → exit 0"是收紧前的旧行为。

**契约钉线**：`tests/unit/test_guard_git_workflow_hook.py` —— 3 个测试函数 / 21 个参数化用例
（8 blocked + 8 allowed + 5 malformed-stdin），subprocess 端到端跑真实 hook；宿主无
`pwsh` / `powershell` 时 skip 而非 fail。

**两处边界（明写而非默默吸收）**：

- **L3 只绑 Claude Code harness**。hook 由 `.claude/settings.json` 挂载，Codex 跑在自己的
  harness 下**不经过它** —— 对 Codex，G1/G2 是 `AGENTS.md` "Self-enforced boundaries" 第 5 条
  的 prose 义务（per ADR-035）。**规则是工具中立的，载体不是。**
- **L3 不是 CI gate**，未登记于 `sdd/gates.md` §1 的 G 系列。⚠ 那里的 `G1` / `G2` 是**另一套
  编号**（`check_capability_schema.py` / `check_traceability.py`），与本节的 G1/G2 同形不同义；
  本 hook 在 `sdd/gates.md` 全文只被提及一次，且是作为"不拦 4 必停面 Edit/Write"的对照物。

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

STANDARD `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`（现 **v1.1**）分三处承载：
**§3** = 7 项 commit type 定义 · **§4** = 35 项闭合 scope 白名单 · **§5.2** = 上表的对齐矩阵
（上表与 §5.2 逐行一致）。

### §4.3 自动化 commit-message 校验（CI gate；2026-08-07 起在线）

原 TBD "Phase M2 — automated commit-message regex validation (CI gate)" **已兑现**：
`scripts/check_commit_messages.py` + 独立 workflow `.github/workflows/check-commit-messages.yml`
（`cd79b5c`，2026-08-07，#444）。**判定细则的 SoT 是 `sdd/gates.md` §2 的
`check-commit-messages` 行**，此处只给规则级摘要：

| 维度 | 现状 |
|---|---|
| 判定输入 | PR **自身新增**的 non-merge commit（`<base>..<head>`）的 header |
| 判定面 | **只有 type + scope** —— type ∈ STANDARD §3 的 7 项，scope ∈ §4 的 35 项闭合白名单 |
| **不**判 | **§4.2 的分支×commit-type 矩阵**；§2.2 中独立于这两张表的外观规则（`:` 后空格 / 句号 / 72 字符）。有意为之 —— 一次判太多会令 warning 输出不可读 |
| 规则来源 | **从 STANDARD 的表格派生**（按表头单元格定位，非章节号），脚本内无任何 scope / type 字面量；改 STANDARD 即改判定，无需改代码 |
| 姿态 | **warning@ci** —— **job 层** `continue-on-error: true`；红 job 不阻塞 merge |
| 触发面 | `pull_request` only、**无 `paths:` 过滤器** → 每个 PR 必跑，恒产出恰好一个 check run（永不 `skipped`） |
| fail-closed | STANDARD 不可读 / 解析出 0 个 scope / 提交范围不可解析 → exit 2 + 诊断（per #429 判例：取不到输入不得当作"没问题"） |
| 翻 blocking | 观察期已按 `policies/ci-gates.md` §4.1.1 于落地同批注册：`plans/[PLAN]_m-fu-commit-message-gate-flip.md`（日历腿 ≥ 2026-08-21 **AND** 计数腿 ≥ 20，两腿 AND）。翻转本身是独立的 Owner `ci-blocking-gate-toggle` 拍板 |

⚠ **"regex validation" 是原 TBD 的措辞，不是实现的准确描述**：正则只用来拆
`<type>(<scope>): <summary>` 这个 header 形状；**判定**靠的是从 STANDARD 派生的白名单成员检查。
同理，该 gate **判大小写**（`Feat(agent)` / `feat(AGENT)` 因成员检查失败被报出），那是"派生"的
必然结果而非独立规则 —— 不得把它描述成"不判大小写"。

**与 §4.2 的分工**：§4.2 的分支×commit-type 矩阵**没有机器强制**，由 PR 模板的自检项承载 ——
`.github/PULL_REQUEST_TEMPLATE/` 6 份模板里，**5 份分支类型模板**（`feature` / `bugfix` /
`documentation` / `maintain` / `hotfix`）各带一条"允许类型"勾选；`release.md` **无此项**，且这是
对的：release PR 的每条 commit 早已在各自并入 develop 的 PR 上判过（与 §4.3 gate 的 release-PR
豁免同理）。把判定面扩到 §4.2 须另起观察期（详注册工件 §5.4）。**自检项是人工勾选，与 §4.2
的一致性无 gate 兜底，须随 §4.2 / STANDARD §5.2 手工同步。**

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

> *`state: draft` — 全文均为 live SoT；自 v0.2 起本文件**无待填充块**（§1 有 1 个 DECLINED
> 决策块 + 1 个"已兑现"决策块，§2 有 1 个 DECLINED 决策块）。*
>
> *v0.2（2026-08-11）：#482 — 处置本文件在 `M6-FU-POLICIES-TBD-SWEEP` 中的 3 个 TBD 块，
> **全部 filled、无 decline**（三块的共同结论一致：规则实体早已在仓内，是文档没跟上）。
> **§1 末块摘壳真值化**：原 TBD 要平移的 "Branch ↔ commit-type alignment matrix" 早已由
> `0bf53bb`（M6 X6，2026-06-08）落在本文件 §4.2，与 STANDARD §5.2 逐行一致 —— 故记 Decision
> 指向 §4.2 而**不复制矩阵**（同一张表在同一文件出现两次必然漂移）；顺带更正原 TBD 里已过时的
> STANDARD 版本 `v1.0`（现 v1.1，#443 把 scope 白名单从 12 项重建为 35 项闭合白名单）。
> **§3 新增 §3.1 联动表**：从实现取证，记 3 层防御的 G1/G2 × skill family 对应关系（9 个
> `mj-agent-git-*` 里只有 `branch` / `pr` 带 HARD REQUIREMENT，`push` 仅一条交接指针）、L3 的
> 实际判定面与 fail-closed 输入协议、契约钉线（`tests/unit/test_guard_git_workflow_hook.py`，
> 3 函数 / 21 参数化用例），并明写两处边界 —— L3 只绑 Claude Code harness（Codex 走
> `AGENTS.md` 自守），L3 不是 CI gate 且 `sdd/gates.md` §1 的 `G1` / `G2` 是**同形不同义的
> 另一套编号**。同时记录：该 plan §3.2 的正则表与 §3.1 的"非 JSON → exit 0"均是 `ed785b6`
> 时的历史快照，已被 #313 PR-2 的 token 实现 + fail-closed 取代，引用须以实现为准。
> **§4 新增 §4.3**：原 TBD 声称待做的 "automated commit-message regex validation (CI gate)"
> 早已由 `cd79b5c`（2026-08-07，#444）实装，记其判定面（**只 type + scope，不判 §4.2 矩阵**）、
> warning@ci 的 **job 层** `continue-on-error` 载体、fail-closed 语义与已注册的翻转观察期；
> 并指出 "regex validation" 是失真措辞 —— 正则只拆 header 形状，判定靠从 STANDARD 表格派生的
> 白名单成员检查。**两处如实修正**：(a) §3 G2 原写"执行机制 = 同 G1 hook + **PR template** +
> skill" —— PR body 模板**不是** G2 的载体（实测 6 份模板对 `--base` 零内容，只有 `hotfix.md`
> 顶部一句目标分支提醒），该项已删除并写明理由；(b) §4.2 脚注原把 "commit-type allowlist"
> 一并指向 STANDARD `§4-§5` —— type 定义实际在 **§3**、§4 是 scope 白名单、对齐矩阵在 **§5.2**，
> 已按三处分别指明。**一处发现另立单**：`.github/PULL_REQUEST_TEMPLATE/feature.md:19` 的允许
> 类型漏 `perf`，与 §4.2 及 STANDARD §5.2 不一致，而该矩阵无机器强制、这条人工勾选是唯一载体
> —— 该文件在 `.github/` 不属本 sweep scope，已开 **#488**（Owner 2026-08-11 拍板另立）。
> `state` 不动：内容填充不构成 live-kernel-home 意义上的操作必要性（per #480 /
> `sdd/lifecycle.md` §4.1）。*
