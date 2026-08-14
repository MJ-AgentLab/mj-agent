---
type: evidence
summary: >-
  Epic #499 Task-0 baseline —— 从 fresh `origin/develop@829482b` 建立的 tracked path
  inventory（789 文件 / raw SHA-256 / mode / owning surface）、18-carrier census、
  manifest/lock/gate 现状、hard+controlled freeze identity、known divergence ledger、
  pre-change 全量安全离线验证，以及 Owner private attestation = SKIP_PRIVATE。
  freeze identity digest = 36f64771efeed88ca95bc98fadf3b3a0d1e56cc0b3e9f46afa675d9dbf88a6a7
owner: ranzuozhou
created: 2026-08-14
updated: 2026-08-14
state: active
track: agent
---

# Task-0 Baseline — Epic #499 (PR-0d)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §4.2（Task-0 timing / 六项记录）与
> §4.3（freeze enforcement）。Delivery unit = **PR-0d**，AC = **AC-02 / AC-13**。

## 0. 基线锚点与入场门

| 项 | 值 |
|---|---|
| Task-0 revision | `829482b26139f7e23af4c015d6f509d71e1524ed`（= `origin/develop`，fresh） |
| 前序 unit | PR-0c = [#503](https://github.com/MJ-AgentLab/mj-agent/pull/503)，MERGED `2026-08-14T03:33:57Z`，merge commit 即上行 |
| 前序 Stage 17 ledger | [#499 comment 5289157069](https://github.com/MJ-AgentLab/mj-agent/issues/499#issuecomment-5289157069)，body SHA-256 `dec8278da7cdd2fa8381e71d3f456d5d60268d4f4ed290b85d714e2da9cf3555`（纯 LF；raw 与 LF-归一同值），18 records / stage 0-17 全终态 |
| 本 unit branch | `documentation/499-task0-baseline`，由 `git worktree add` 从 `origin/develop` 建立（G1） |
| PR-0c post-merge EVAL | **`SKIP`（deferred to Phase 2）**，evidence = [#504](https://github.com/MJ-AgentLab/mj-agent/issues/504)；详 §5 D-2 |

§11.2 入场门 7 项逐条满足：前序 MERGED 且 `mergedAt`/`mergeCommit.oid` 齐备 · merge commit 是当前 `origin/develop`（二者同 SHA）· local/Gitee/GitHub 三方 develop 一致且工作区干净 · 前序 Stage 17 成功 · 本 Epic 无其他 active goal/worktree/PR · branch 名与类型符 §5 且由 worktree 建立 · root + 4 个 nested `AGENTS.md` 已读、exact scope / HITL / verification 已声明。

## 1. Tracked path inventory（§4.2 第 1 项）

机器可读工件：[`task0-inventory.json`](./task0-inventory.json)（schema `task0-inventory-v1`）。

- **789** 个 tracked path，**全部 mode `100644`** —— 无 symlink（120000）、无可执行位（100755）、无 submodule / gitlink（160000）。该结论**可从工件本身复核**：inventory 逐条记录 `mode`，且 `git ls-tree -r` 的全部四种 entry 形态（regular / executable / symlink / gitlink）都会被收录，故「一个都没有」是可观察的空集，而非「本工具不表示这些形态」造成的假象。
- **content basis = git blob，不是工作区字节**。`.gitattributes` 设 `* text=auto` 并对 `.py/.yml/.json/...` 显式 `eol=lf`；`.md` 不在显式列表内，故 Windows 检出为 CRLF 而 blob 为 LF。实测 `README.md`：工作区 12 924 字节 / 273 个 CRLF，blob 12 651 字节 / 0 个 CRLF，两者 SHA-256 完全不同。**按工作区字节做 identity 会铸出 Linux CI 永远无法复现的平台局部值**，故一律哈希 blob 内容。
- 只遍历 git-**tracked** 路径。这从构造上满足 §1.1「`.claude/scheduled_tasks.lock` 等 ignored/private harness 状态不得由 agent/CI 打开、打印、hash 或传输」——此类路径未被 tracked，被排除是结构性的，不依赖会腐坏的 allowlist。

### Owning surface 分布（18 桶，无 `other` 兜底命中）

| Surface | 文件数 | | Surface | 文件数 |
|---|---:|---|---|---:|
| tests | 134 | | plans | 80 |
| capability | 114 | | runtime-src | 61 |
| evidence | 86 | | **hard-frozen** | **58** |
| scripts | 55 | | kernel-sdd | 43 |
| docs | 35 | | decisions | 29 |
| archive | 28 | | ci-workflow | 20 |
| repo-root | 12 | | kernel-policies | 10 |
| docker | 9 | | generated-projection | 8 |
| config | 6 | | **controlled-frozen** | **1** |

合计 789 = `file_count`（已断言）。分类为 first-match-wins，冻结桶遮蔽通用前缀——例如 `src/mj_agent/AGENTS.md` 归 `hard-frozen` 而非 `runtime-src`。

## 2. Hard / controlled freeze identity（§4.2 第 3 项）

机器可读工件：[`task0-freeze-identity.json`](./task0-freeze-identity.json)（schema `task0-freeze-identity-v1`）。

| 档 | 文件数 | digest |
|---|---:|---|
| hard-frozen | 58 | `43bb10d40d59f0d1fbfb265bf4e1c8f04324faa5d8209991921022fecfa1e957` |
| controlled-frozen | 1 | `124d830374a607587f10ddc7d504c045577edf7766462d7d7ee8d5e2450bdd14` |
| **identity_digest** | — | **`36f64771efeed88ca95bc98fadf3b3a0d1e56cc0b3e9f46afa675d9dbf88a6a7`** |

58 = 46（`.claude/` 前缀）+ 12（exact）。12 个 exact 模式**全部命中**，`absent_exact_patterns` 为空 —— 即 §1.1 列出的每一条冻结路径在本仓都真实存在：

`.claudeignore` · `.mcp.json` · `CLAUDE.md` · `capabilities/{AGENTS,CLAUDE}.md` · `docker/{AGENTS,CLAUDE}.md` · `src/mj_agent/{AGENTS,CLAUDE}.md` · `tests/{AGENTS,CLAUDE}.md` · `tests/unit/test_guard_git_workflow_hook.py`

Controlled-frozen = 仓根 `AGENTS.md` 单文件，按 §4.3 仅允许 PR-C1 的 carrier-ownership hunk 与 PR-D1a 的 hooks/rules cooperative-scope hunk 两个具名改动。

**digest 序列化口径**（`--check` 的可复现性依赖它；任何改动等同 schema bump，不是静默修复）：对每个 surface 按 path 排序，逐行 `path\0mode\0sha256`，以 `\n` join 后取 SHA-256；`identity_digest` = SHA-256(`hard_digest\0controlled_digest`)。

**identity 是 `(path, mode, sha256)` 三元组，不是内容单轴。** mode 翻转——冻结的 hook 脚本被加上可执行位、或普通文件变成 symlink——按 git 自身口径就是一次改动，即便 blob 逐字节相同，也必须触发 §4.3。gitlink（mode 160000）被**记录而非跳过**：submodule 挂到 hard-frozen 前缀下会把任意第三方内容接进该面；gitlink 在本树没有 blob，故按 `sha256("gitlink:" + <commit sha1>)` 给一个域分隔的替身摘要，该约定以 `gitlink_sha256_convention` 字段写在两个工件的头部。此外 `--check` 以 `identity_digest` 相等作**兜底**：若逐文件比对定位不到差异而摘要却不同，判定为漂移而非干净——否则脚本可能在屏幕上打印两个明显不同的 digest 却仍返回 `TASK0_FREEZE_CLEAN`。

### 执行载体

§4.3 要求「后续每 PR 比较 `origin/develop` merge-base → HEAD 与 Task-0 identity；任何其他差异 `STOP_FROZEN_SURFACE_DRIFT`」。**在 PR-0d 之前这条规则没有任何可执行载体**（§3.3 逐 unit 核对过，无其他 unit 拥有它），789 个文件的哈希对比也不具备人工执行性。本 unit 交付 [`scripts/sdd/task0_freeze.py`](../../scripts/sdd/task0_freeze.py)：

```bash
uv run python scripts/sdd/task0_freeze.py --check     # 后续每 PR preflight
uv run python scripts/sdd/task0_freeze.py --emit      # 仅在 Owner 批准的 baseline 重建时
```

| 结果码 | exit | 含义 |
|---|---:|---|
| `TASK0_FREEZE_CLEAN` | 0 | 全部冻结面与 baseline 一致 |
| `STOP_FROZEN_SURFACE_DRIFT` | 1 | hard-frozen 路径被改 / 新增 / 删除 |
| `CONTROLLED_SURFACE_CHANGED` | 1 | controlled-frozen 面变化（须确认属两个具名 hunk 之一） |
| `ERROR_NO_BASELINE` | 2 | baseline 工件缺失 —— **什么都没验证；缺 baseline 不是通过** |
| `ERROR_MALFORMED_BASELINE` | 2 | baseline 不可解析 / schema 不符 —— 什么都没验证 |
| `ERROR_NOT_A_REPO` | 2 | git 调用失败 —— 什么都没验证 |

沿用 PR-0c 的「SKIP 永远不是 PASS」纪律：缺失或损坏的 baseline 退出 2 而非 0，调用方无法把 exit 0 误读成「冻结面干净」。该脚本**不挂 CI**——§6.2 规定「producer/CLI 未落地前不得运行其命令」，且新挂 blocking gate 属 `ci-blocking-gate-toggle` 必停；它按 §6.1 作为 agent preflight 命令使用。

## 3. 18-carrier census 与 manifest / lock / gate 现状（§4.2 第 2 项）

### 3.1 Manifest

`sdd/development-agent.yml`：`schema_version: 1`，`snapshot: 2026-07-13`，**37** 个 capability，其中 `required: true` **18** 个。

18 项 required 的当前 projection 分布与 §2.2 的分类**逐项吻合**：

| 当前 projection | 数量 | capability | §2.2 对位 |
|---|---:|---|---|
| `project` | 5 | flow-diagnose · git-commit · git-delete · git-push · git-sync | 恰为「现有 5 项 byte-copy」 |
| `never` | 3 | doc-validate · flow-verify · git-issue | 恰为 §2.2 点名需 ADR-039 逐项记录反转理由的 3 项 |
| `after-neutralization` | 10 | flow-{intake,plan,implement,repo-scan,scope-drift,self-review,review-respond,post-merge} · git-branch · git-pr | 与上面 3 项合为「新增 13 项 translated」 |

当前 `codex.support_mode` 分布：`native` 1（flow-diagnose）· `adapter-backed` 8 · `manual` 7 · `script-ci` 2（合计 18）。注意 `support_mode` 与 `projection` 是**正交**的两轴——`git-issue` 是 `projection: never` 但 `support_mode: manual`，不要把 never 层的 3 项当成 script-ci 的 3 项。

**与 §2.2.1 终态矩阵的差距（计划内，非缺陷）**：`codex_carrier` 与 `workflow_id` 两个字段目前在 manifest 中**完全不存在**（37 项均无），13 项需 `projection → project`，17 项需 `support_mode → native`。这是 PR-B（dormant v2 engine）与 PR-C1（cutover）的工作面。

### 3.2 Lock 与 projection

| 项 | 现状 |
|---|---|
| `.agents.lock.json` | v1 形态，**6** 个条目：`.codex/config.toml` + 5 个 project-tier skill 的 `sha256:` |
| `.agents/skills/` | 5 个目录（与 project tier 一一对应）+ `.agents/README.md` |
| `.codex/config.toml` | 存在；G7 实测 **8 个 server**，仅按名引用 env var，无 env table、无字面凭据形状 |
| `.claude/skills/` | **37** 个目录（37-skill SoT） |

V10 / V11 / `--surface all` 三种口径均报 `projection in sync ... lock consistent`。

### 3.3 Gate 现状

4 个 workflow / 4 个 job。**姿态载体不止一种**，逐层实测：

| Workflow | job-level `continue-on-error` | step-level warning 步数 | 净姿态 |
|---|---|---:|---|
| `ci.yml` | `false` | 9 | 按 step 分档 |
| `check-commit-messages.yml` | **`true`** | 0 | WARNING（载体在 **job** 级） |
| `check-stale-docs.yml` | `false` | 1 | WARNING |
| `docker-build.yml` | 显式 `false` | 0 | BLOCKING（#385 翻转） |

> 只扫 step 级会把 `check-commit-messages` 误读成 BLOCKING —— 该文件自身 L23-32 即写明这个易误读的区别。

`ci.yml` 共 43 个 step，其中可识别的 G/V/A 系列 gate **26** 个。`sdd/gates.md` 声明姿态与 `ci.yml` 实况 **26/26 全部一致**，零偏差。A6（`check_ai_context_audit.py`）不在 `sdd/gates.md` 内属设计使然——A 系列（A1-A6）由 `policies/documentation.md` 治理，`sdd/gates.md` 只治 G/V 系列。

## 4. Pre-change 验证矩阵（§4.2 第 5 项 · §6.1 + §6.2 PR-0d 行）

全部在 PR-0d worktree 实测。Agent 发起的 pytest 一律走 `scripts/sdd/run_offline_pytest.py`，无 direct pytest、无 DB / network client。

| 组 | 结果 |
|---|---|
| 语法 / lint / 类型 | `compileall src tests scripts` clean · `ruff check` **All checks passed** · `mypy src/mj_agent` **48 files, no issues** |
| Doc gates | frontmatter **138 OK** · wikilinks A4-strict **0 unresolved**（13 archived 自动发现）· kernel-section-refs **0 violations / 20 sections** · A6 **2 cycle + 3 investigation** OK · cross-repo warning-mode OK · old-completed-plans 无候选 |
| 能力 / 归档 | G1 **6P/0W/0F** · G2 **6P/0W/0F** · G9 1P · G11/G12 rc0 · G14/G15 rc0 · archive INDEX rc0 |
| 契约 | V1 **9P/11W/0F** · V2 rc0 · V3 **1P/1W/0F** · V4 **37 skills / 0W** · V5 **2P/4W/0F** · V6 **1P/1W/0F** · V7 **3P/0W/0F** |
| BDD / TDD | G8 **5P/0W/0F/1SKIP** · G19 **24P/0W/0F** · G21 **16P/0W/0F** · G22 **4P/0W/0F** · G23 **15P/5W/0F** · G24 0P（非 bugfix 分支，branch-conditional SKIP）· G3 **6P/0W/0F** · G7 **4P/0W/0F** · G25 0P（PR-context only） |
| **V8-V11** | V8 **0E/0W/0I** · V9 **0E/0W/0I** · V10 in sync（skills，5 skills，lock consistent）· V11 in sync（mcp）· `--surface all` in sync |
| Offline boundary | `check_test_offline_boundary.py` → `OFFLINE_BOUNDARY: GREEN (static/AST boundary closed)` |
| Full safe offline suite | Tests **1032 passed / 6 skipped / 82 deselected** · BDD **13 passed / 7 skipped** · Contract **63 passed / 1 skipped** |
| Task-0 载体自检 | `task0_freeze --check` → `TASK0_FREEZE_CLEAN` · `tests/unit/test_task0_freeze.py` **23 passed** |

**测试数增量对账**：PR-0c Stage 17 ledger 记录 full offline suite = 1009 passed；本 unit 新增 23 个 test，1009 + 23 = **1032**，与实测一致。

**平台口径**：上表全部为 **Windows worktree** 实测。GitHub CI 跑 ubuntu-latest，pass / skip 的分配合法地不同（若干用例按平台分支跳过），`passed + skipped` 总数才是平台不变量——本地为 1032 + 6 = **1038**。比对 CI 与本表时按总数对账，不要按 passed 单项。CI 的实测分配以本 PR 的 CI 结论为准，不在此预填。

### 负控 —— 证明断言不是空转

全部在真实树上实测，变异后均已还原并复绿（23/23）。

| # | 变异 | 观察结果 |
|---|---|---|
| N-1 | `HARD_FROZEN_PREFIXES` 清空 | 4 个测试转红；`--check --rev origin/develop` 输出 `hard-frozen = 12 files (baseline 58)` + 46 行 `[hard] REMOVED` + `STOP_FROZEN_SURFACE_DRIFT`，rc=1 |
| N-2 | 「baseline 缺失」的返回值由 2 改成 0 | 2 个测试转红 |
| N-3 | `_compare_block` 忽略 mode / `list_tree` 丢弃 gitlink / 移除 identity 兜底（三处同时回退） | 恰好 3 个对应测试转红，其余 20 个仍绿 |

**端到端（真实历史，非合成 fixture）**：以本 baseline 校验 PR-0c 的 base commit `c6ef1e8`，输出 `STOP_FROZEN_SURFACE_DRIFT`、rc=1，逐条列出 5 个 `.claude/skills/**` 文件的 MODIFIED 及新旧 sha256。该清单与独立口径 `git diff --name-only c6ef1e8 fd050b9` 过滤 §1.1 冻结面的结果**逐条一致**——即该载体在真实历史数据上确实拦得住冻结面漂移。

> 本节曾记载「`--check` 在真实树上误报 `TASK0_FREEZE_CLEAN`（只认到 4 个 hard-frozen 文件）」。该陈述**不成立**，已按上表更正：当时被当作真实树输出读取的那段文本，`current rev` 是合成 fixture 仓的 commit 而非 `829482b`，实为 pytest 捕获的 fixture 输出；且彼时 baseline 工件尚未 emit，真实树上的 `--check` 只会返回 `ERROR_NO_BASELINE`。真值是载体比原记载**更强**，不是更弱。

skip 全部为结构化外部依赖跳过（`SKIP_POLICY_EXTERNAL_DEPENDENCY`：biz live legs 永久不可用 / 无 Owner 批准的非 biz profile / Windows 符号链接权限 / 非 Windows 平台分支），无一是静默跳过。

## 5. Known divergence ledger（§4.2 第 4 项）

每项含 owner / reason / expiry-closure。**记录不等于修复**——本 unit 一项都不修（§3.3 owned files 与规则「不夹带后续单元」）。

| ID | 项 | Owner | Reason | Expiry / Closure |
|---|---|---|---|---|
| **D-1** | **6 个 CI step 名内嵌基线计数陈旧**：G1 `5P`→实测 6P · G2 `5P`→6P · G8 `4P`→5P · G19 `17P`→24P · G21 `15P`→16P · G3 `5P`→6P。另 9 处（G22/G23/G7/V1/V3/V5/V7/V8/V9）吻合 | Owner（F3 follow-up） | 计数硬编码在 step 名里，**无任何 gate 读取它**，故随能力增长静默陈旧 | 待 F3 issue；PR-0c ledger 的 F3 只记了 G21，**实际低估 5 处**，开单时需按本行口径 |
| **D-2** | PR-0c post-merge EVAL 为 **`SKIP`**，非 PASS | Owner | 仓内无可跑 LLM 的 EVAL runner（`tests/eval/` 只对 reference SQL 跑 `precheck_sql`，不调 LLM，且语料指向 QVL 表族）；`execution-loop` §7.3 规则体自身即把执行归 Phase D | [#504](https://github.com/MJ-AgentLab/mj-agent/issues/504) close 于 Phase 2 baseline 实测完成 |
| **D-3** | A11 `eval_references` 在**全部 9 个** in-source runtime skill 中缺失；`system.md` 有该字段但为 `[]` + TODO 注释 | Owner（F4 follow-up） | A11 transitional waiver 期内允许 | Phase 2 EVAL framework 落地后强制 |
| **D-4** | `ACTIVE_ACCEPTED_PR0A_IN_PROGRESS` 相关陈述在 plan + ADR-039 中陈旧 | Owner（F2 follow-up） | Owner 于 PR-0c Gate 1 裁定「全部排除、另立 follow-up」 | 两文件按 §3.3 归 PR-0a、lifecycle 收尾按 AC-14 归 PR-G |
| **D-5** | manifest 缺 `codex_carrier` / `workflow_id` 字段；13 项待 `projection → project`、17 项待 `support_mode → native` | PR-B / PR-C1 | §2.2.1 终态矩阵尚未 cutover | PR-C1 cutover 时逐行断言终态矩阵 |
| **D-6** | ignored / private harness 面**未经核验** | Owner | §1.1 禁止 agent 打开、打印、hash 或传输该面；只接受 Owner private attestation | 见 §6；PR-F 的 final evidence 会再取一次 attestation |

## 6. Owner private attestation（§4.2 第 6 项）

```text
ATTESTATION = SKIP_PRIVATE
```

Owner 拍板取 `SKIP_PRIVATE`（枚举仅允许 `ATTESTED_CLEAN | ATTESTED_NON_CLEAN | SKIP_PRIVATE`）。

按 plan §1.4 诚实状态纪律，**`SKIP_PRIVATE` 不是 `ATTESTED_CLEAN`**：它意味着私有 / ignored harness 面在本次 Task-0 **未被核验**，而非已确认干净。本 baseline 的任何后续消费方不得把它读作 clean 断言。未触发 §4.2 的「`ATTESTED_NON_CLEAN` 或 unattributed frozen diff 立即停止」条件。

本 unit 全程未读取、未枚举、未 hash、未传输任何私有内容、路径或 hash —— inventory 只遍历 git-tracked 路径，该性质由 `test_untracked_paths_never_enter_the_inventory` 钉住。

## 7. AC 对位

| AC | 陈述 | 本 unit 的满足方式 |
|---|---|---|
| **AC-02** | at most one active delivery unit；each next unit proves previous Stage-17 merge ancestry | §0 入场门 7 项 + PR-0c Stage 17 ledger 哈希复算 + 三方 develop 同 SHA + 全仓仅 2 个 worktree / 0 open PR |
| **AC-13** | final evidence distinguishes PASS/SKIP/NON_CLEAN/ERROR and makes no unsupported semantic/identity/managed claims | §4 逐项区分 passed / skipped（全部结构化）/ deselected；§5 D-2 记 EVAL 为 SKIP 非 PASS；§6 记 attestation 为 SKIP_PRIVATE 非 CLEAN；§2 结果码表把「缺 baseline」定为 exit 2 而非 0 |

本文件不声称：Claude/Codex 语义等价、Owner 身份已认证、项目规则不可绕过、错误时零写入。digest 只证明 reproducibility，不证明语义 fidelity（per §1.3）。

## 8. Cross-refs

- `plans/[PLAN]_codex_cross_carrier_kernel.md` §1.1 / §1.4 / §2.2 / §3.3 / §4.2 / §4.3 / §5.1 / §6 / §7 / §11
- `decisions/ADR-039_Codex_Cross_Carrier_Kernel.md`
- Epic [#499](https://github.com/MJ-AgentLab/mj-agent/issues/499) · PR-0c [#503](https://github.com/MJ-AgentLab/mj-agent/pull/503) · EVAL backlog [#504](https://github.com/MJ-AgentLab/mj-agent/issues/504)
- [`task0-inventory.json`](./task0-inventory.json) · [`task0-freeze-identity.json`](./task0-freeze-identity.json) · [`scripts/sdd/task0_freeze.py`](../../scripts/sdd/task0_freeze.py)
