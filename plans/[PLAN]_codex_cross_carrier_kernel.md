---
type: plan
slug: codex-cross-carrier-kernel
summary: >-
  Agent Kernel v8：在单一 authoring SoT、闭合 manifest/lock/fidelity/probe contract、非破坏性
  reconcile、离线测试与数据边界下，为 Claude Code 与 Codex 建立 18 项 required capability 的
  repository-native carrier；按单 Epic、18 个串行 PR、人工 merge barrier 实施
owner: ranzuozhou
created: 2026-08-12
updated: 2026-08-27
state: active
version: 8.0
track: shared
---

# [PLAN] mj-agent Tool-Neutral Governance Kernel — Claude–Codex Cross-Carrier v8

> **Epic:** [#499](https://github.com/MJ-AgentLab/mj-agent/issues/499) — single Epic；exact create content 已获 Owner 批准。
> **v8 rebaseline:** `origin/develop@c549880f6d1e5342c6402d9fb6d84639090020b5`
> （2026-08-13 JST；本地 develop、tracking ref、GitHub/Gitee remote 已核对一致，pre-change develop worktree clean；本地 `develop` 无 upstream，命令必须显式使用
> `origin/develop`）。
> **External v8 input:** Owner vault v8，SHA-256
> `ce87a6a928ce539433db678f1158c50f725ab0f14ec8a0a250ef783c21e9a76a`（immutable external evidence）。
> **v8 upstream provenance:** external v8 自记的 v7 basis digest 仅属历史 provenance，不得冒充本次输入 digest。
> **Lifecycle:** Owner 于 2026-08-13 在当前 Codex task 对下述 exact lifecycle / ADR-036 disposition diff
> 给出独立 procedural approval；本 PR-0a change tree 因此记录本 plan `active`、ADR-039 `active/accepted`。
> 该状态仅在 PR-0a 人工 merge 后进入 shared `develop`；在此之前 `origin/develop` 仍以 ADR-036/v1 为生效基线。
> 该批准不覆盖 commit、push、PR create、merge 或 PR-0b。
> **执行上限:** `max_active_stage = 1`；任何时刻最多一个 delivery unit、一个 goal、一个 branch/worktree、
> 一个 open implementation PR。
> **终点:** 每个 goal 只到 `AWAITING_HUMAN_MERGE`；禁止 merge、auto-merge、提前建立下一阶段 worktree。

## Global Constraints

1. 所有新分支只用 `git worktree add ... -b ... origin/develop` 创建；禁止 `checkout -b` /
   `switch -c`。所有非 hotfix PR 显式 `--base develop`。
2. 前一 PR 必须由人类 merge，且 merge commit 已进入 `origin/develop`，下一 delivery unit 才 eligible。
3. commit、push、PR create、merge 分别是独立 Owner gate；前一次批准不覆盖下一动作、amend/force-push、
   scope 扩张或下一阶段。merge 永远不由本 goal 执行。
4. 不读取 `.env`、`config/secrets*.enc`、private harness state；不直连 biz DB。biz 数据只走
   `find_biz_context → list_biz_tables → describe_biz_table → execute_sql`，且本计划只提交脱敏 snapshot/evidence。
5. `.agents/**`、`.agents.lock.json`、`.codex/**` 的 declared generated outputs 不手改；修改 source 后运行
   generator，同 change tree 提交 source、artifact、lock、tests/evidence。
6. `policies/**` 与 `sdd/**` 修改均需 kernel-meta Owner HITL，但不虚构为 canonical 10-enum；canonical
   inventory 仍逐行填 No/Yes，并在 AI Self-Check 单列 kernel approval。
7. 同一 worktree 单 writer；子代理只做互不冲突的只读调查/审阅，任何写入由一个 implementer 串行完成。
8. current counts、pass totals、CLI build、gate posture 与 paths 都是 evidence，不进入 schema 常量；每阶段从
   最新 `origin/develop` 重新派生。
9. 回滚不删除历史 evidence；P0 安全迁移只 forward repair。其他节点按依赖有界回滚，不宣称“每节点独立回滚”。
10. 本计划不改变 Claude 现有行为，除 PR-0b/PR-0c 经 exact Owner approval 的安全 source repair；之后进入 freeze。

## 0. v8 revision basis and accepted decisions

### 0.1 Current-state rebaseline

| Fact | 2026-08-13 fresh evidence |
|---|---|
| Manifest | `sdd/development-agent.yml` schema v1 |
| Required set | 18，当前只有 5 项 `projection: project` |
| Lock | legacy flat map，无 `schema_version` |
| Codex project surface | `.agents/skills` 5 项；`.codex/config.toml` only |
| Sync/check surface | `skills | mcp | all`；无 enforcement |
| Reconcile | 仍会删除未声明的 `.codex` 邻居，空 MCP 时可递归删除目录 |
| V8/V9/V10 | blocking（#399）；V11 day-1 blocking（#330） |
| Newer gates | `check-commit-messages` warning；`kernel-section-refs` warning |
| Test entry | CI 当前三条 direct `uv run pytest`；`tests/conftest.py` 会加载 `.env` |
| Biz route | `fetch_biz_schema.py` 仍加载 dotenv，并绕过完整 agent tool-chain 直接调用 introspection wrapper；contract/skills 仍有 direct route |
| Plan implementation | Epic #499 已创建；PR-0a worktree 已从 fresh base 建立；后续 17 units 均未开始 |

**PR-0a incremental re-audit（2026-08-13 JST）：**

- prior audit SHA `9d5ce71560d9d310087639490963edde570b81fc` 是 current base 的 ancestor；
- current base = `c549880f6d1e5342c6402d9fb6d84639090020b5`，ahead 2 / behind 0；
- 唯一 drift = `plans/[PLAN]_spec_anchored_refactor.md` 2 insertions / 2 deletions 的 lifecycle 收尾；
  Agent Kernel source/manifest/projection 面无 diff，但所有 live counts 仍重新派生；
- manifest census = 37 total / 18 required / 19 optional；
  projection = 5 project / 21 after-neutralization / 11 never；
  required projection = 5 project / 10 after-neutralization / 3 never；
- lock 仍为 6-key legacy flat map（无 `schema_version`）；`.agents/skills` 仍为 5；
- V8/V9 = 0 error / 0 warning；V10/V11/`--surface all` drift checks clean；
- CI 仍有 3 条 direct `uv run pytest`；`tests/conftest.py` 仍加载 `.env`；
- pre-creation duplicate census：无同主题 open Epic、open PR、matching local/GitHub/Gitee branch 或额外 worktree；
  Issue #499 获批创建后，当前恰有一个 intended local branch/worktree
  `documentation/499-codex-cross-carrier-kernel-v8`，仍无 matching remote branch、open PR 或额外 worktree；
  open #479/#497 仅为邻接 drift risk，worktree creation gate 已满足，PR preview 前继续复核；
- default `check_no_cross_repo_refs.py` = exit 0、15 warnings / 11 of 35 files，仍是 informational warning，
  未启用 strict 时不得称 blocking。

这些事实证明旧架构一致，不证明本计划已部分完成。每个 delivery unit 的 Stage 3 必须重新核对，发现漂移时先
更新 active plan；不得照抄本表继续。

### 0.2 Accepted repository adoption of v8 decisions

| ID | Decision |
|---|---|
| V8-001 | 单 Epic #499；中间 PR 只使用 exact `Refs #499`，仅 PR-G 使用 `Closes #499` |
| V8-002 | 18 个 delivery PR 严格串行；删除 PR-A/P1a 并行 |
| V8-003 | P0 拆为 PR-0b offline boundary、PR-0c biz snapshot/source repair、PR-0d EVAL+baseline |
| V8-004 | P1a/P1b 都是独立 evidence PR；无“非 PR 调查节点” |
| V8-005 | A0/A1、C mount/anchor、D mount/anchor 分别拆 PR |
| V8-006 | PR-F 保持 plan active；PR-G 才做 lifecycle closure |
| V8-007 | direct pytest 对人类/IDE 安全可用；Agent/CI 必须经 hardened runner；不建立全仓 direct-pytest 禁令 |
| V8-008 | deterministic discovery/path/collision/budget 是 hard gate；implicit model selection 仅 telemetry |
| V8-009 | manifest/lock/fidelity/probe/receipt/ledger 都采用 closed versioned schema |
| V8-010 | V12/V13 按实际 run command/path 登记；V13 observation 与未来 D2 blocking predicate 完全相同 |
| V8-011 | canonical HITL 仍为 10-enum；kernel-meta approval 独立记账 |
| V8-012 | P0 只 forward repair；其他 rollback 按依赖顺序新开 repair/revert PR |
| V8-013 | runtime-skill post-merge EVAL 不作为 PR-0c pre-merge AC；结果与 Task-0 baseline 由 PR-0d 承载 |

**Procedural disposition:** 本 plan 接受 ADR-039 对 ADR-036 D-011/D-012/D-014 的定向修订：
唯一 scoped generator exception 扩展到 closed typed managed surfaces；generated artifact/lock/ownership/reconcile
合同升级为 v2；manifest v2 选择 5 byte-copy + 13 translated required carriers。D-013/D-015/D-016/D-017、
canonical 10-enum 与 ADR-000/006/009 数据边界保持不变；关系是 revise，不是整体 supersede。

### 0.3 Two independent “18” contracts

- **Execution loop = 18 stages:** 当前 kernel 列出 Stage 0–17，尽管标题仍写 “17-stage”。本计划按实际
  索引称 `18-stage loop`；修正 kernel 标题属于后续 kernel-meta hunk，不在 PR-0a 偷渡。
- **Delivery graph = 18 PRs:** §5 的 PR-0a 至 PR-G 共 18 个 delivery units。每个 unit 都完整走一次
  Stage 0–17；两个“18”只是数量相同，不是一一映射。

### 0.4 Requirements traceability

| Requirement | Design | Delivery | Proof |
|---|---|---|---|
| 18 required native carriers | §2.1–§2.4 | PR-B/PR-P1b/PR-C0/PR-C1 | V8/V9/V10/V12 + deterministic probe |
| Non-destructive ownership | §1.2/§2.6/§3.3 | A0/A1/B | orphan/owner/path negative fixtures |
| Safe test/data boundary | §3.3/§5.2–§5.3 | PR-0b/PR-0c | standalone red signal + offline pytest/contracts |
| Fidelity | §2.7–§2.8 | PR-P1b/PR-C0/PR-C1 | independent inventory + immutable approval binding |
| Enforcement/Stop | §2.8/§5.9–§5.11 | D1a/D1b/D2/E | V13 predicate, hook/rule canary, receipt |
| Strict staged delivery | §4.5/§5/§11 | all | Epic unit ledger + merged ancestry checks |
| Honest closure | §1.3/§1.4/§5.12 | F/G | fresh evidence + lifecycle diff/approval |

## 1. Non-negotiable decisions

### 1.1 Claude behavior invariant

PR-0a 将仓内 plan/ADR 激活、PR-0b 与 PR-0c 完成安全修复、PR-0d 重新建立 Task 0 baseline 后，
冻结面分两档。

**Hard-frozen（zero diff，全计划）：**

```text
.claude/**
.claudeignore
.mcp.json
CLAUDE.md
capabilities/{CLAUDE,AGENTS}.md
docker/{CLAUDE,AGENTS}.md
src/mj_agent/{CLAUDE,AGENTS}.md
tests/{CLAUDE,AGENTS}.md
tests/unit/test_guard_git_workflow_hook.py
```

**Controlled-frozen（仅允许具名 hunk）：**

```text
AGENTS.md   — 仅 PR-C1 的 carrier ownership hunk 与 PR-D1a 的 hooks/rules cooperative-scope hunk
```

约束：

- compiler、renderer 与 sync 永不写 `.claude/**`。
- Claude 的全部 canonical skills（集合由 Task 0 派生）、settings、plugins、commands、Git guard、Stop hook、permission/HITL
  交互和既有 stage 顺序保持不变。`tests/unit/test_guard_git_workflow_hook.py` 冻结的理由：它是
  `mj-agent-git-branch` 的声明证据物，也是「G1/G2 不变」这一头号断言的唯一可执行证明。
- root `CLAUDE.md` zero diff。
- `.claude/scheduled_tasks.lock` 等 ignored/private harness 状态不得由 agent/CI 打开、打印、hash 或传输；
  只接受 §4.2 Task-0 与 §5.12 final evidence 规定的 Owner private attestation。
- 如果实施必须改变上述行为或冻结路径，停止对应 PR，另开 ADR、兼容矩阵与 Owner 决策；不得在本计划内
  临时扩大 allowlist。

PR-0b/PR-0c 是本 plan 预定的冻结前 source-repair units；只有各自 entry gate 满足并对 exact hunk 单独取得
Owner approval 后方可执行，PR-0a 不预先授权其写入。其合并结果是 Task 0 baseline 的组成部分，不算本计划
保留的 divergence。不存在“先改源码、后补 active plan/ADR”的例外。

### 1.2 Native carrier 与 producer 分离

"native" 描述运行时实际消费的 artifact，不代表 artifact 必须手写：

| Runtime | Native carrier | Production strategy | Owner |
|---|---|---|---|
| Claude | `.claude/skills/<name>/SKILL.md` | authored-reference + validate-reference | 人工维护，protected edit |
| Codex direct | `.agents/skills/<name>/SKILL.md` | byte-copy render | `agents_sync.py` |
| Codex translated | `.agents/skills/<name>/SKILL.md` | deterministic translated render | `agents_sync.py` |
| Codex enforcement | declared `.codex/hooks.json`、`.codex/rules/*.rules` | deterministic render-reconcile | `agents_sync.py` |

不虚构 filesystem transaction。sync 可以留下可识别的部分状态，但每一步必须：

- 只写 declared target；
- 使用临时文件 + 原子替换处理单文件；
- 在失败信息中列出已完成/未完成 target；
- 下一次 sync 可安全重试并收敛；
- 不写「错误时零写入」这类当前实现无法保证的承诺。

**并发与 preflight 合同：**

- sync/adopt 在读取输入前取得 worktree-local writer lock；锁已占用时 exit 2，零 artifact/lock/source 写入。
- writer 建立完整 input snapshot，并在第一笔 apply 前复核 source、manifest、registry/map/preface/template、
  renderer module 与旧 lock digest；任一变化时 exit 2，零 managed-output 写入。
- unknown manifest/lock/typed-source schema、path escape、owner collision、casefold collision、symlink/reparse
  ancestor 与 adopt CAS mismatch 都属于 preflight failure，必须零写入；通过 preflight 后的多文件 apply
  仍遵守上面的“可识别部分状态 + 可重试收敛”，不虚构跨文件事务。
- 不同 Git worktree 使用各自 lock，技术上可并行运行；但本 Epic 的 delivery state machine 仍强制
  `max_active_stage=1`，不得借此并行阶段。同 worktree 的 sync 与 adopt 互斥。
- 只允许 merge `origin/develop` 来解决 canonical source、manifest、workflow/translation/enforcement typed source 冲突；
  rebase 全程禁止。generated artifacts 与 lock 不做人工三方合并，merge 更新 base 后重新运行 sync。

### 1.3 Assurance 分层

| Tier | 能证明什么 | 不能证明什么 |
|---|---|---|
| Static structure | schema、classification、closure、desired render、digest、declared ownership 闭合 | 运行时确实加载、模型实际遵循 |
| Ready-host discovery | fresh process 在受信任项目中发现 skill/hook/rule | 所有工程师机器、所有未来版本恒成立 |
| Behavioral observation | fixture 中触发 stop/deny/route，且无禁读 | authenticated Owner、OS/MDM 强制边界 |
| Managed device | Future plan 的管理员/ACL/requirements 实测 | 本计划不交付 |

PR-F 只允许声称：

- 18 项 carrier 的确定性结构闭合；
- 已列 ready-host 场景的实际 PASS；
- 指定 fixture 的行为观察结果。

不得声称「Claude/Codex 语义等价已证明」「Owner 身份已认证」「项目规则不可绕过」或「错误时零写入」。
digest 只证明 reproducibility，不证明语义 fidelity（fidelity 走 §2.7/§5.7 的人工分层复核）。

“长期不漂移”只允许指：安全关键 schema/path/tracked-ownership/desired-render/dependency/lexicon closure 已由
branch-protected blocking gate 或 blocking Tests backstop 覆盖。V12/V13 尚为 warning 时，只能声明其
impact telemetry 处于观察期；不得把 warning streak、real-host SKIP 或人工签署当作 blocking guarantee。

### 1.4 诚实状态纪律

- 未执行的 runtime leg 是 `SKIP`，不是 PASS。
- 环境缺失、未 trust、未 review hook 或未安装所需 CLI 都必须进入结构化 status。
- 所有 warning-first gate 只把 `EXECUTED_CLEAN` 计入 streak。
- `SKIP_*` 不增加 streak，也不伪装 clean；`EXECUTED_NON_CLEAN` 与 `ERROR` 重置当前 qualification epoch
  的 streak。
- classifier、status schema、clean predicate、base/head 推导规则、self-trigger set 或计数规则发生语义变化时，
  新建 epoch 并重新 anchor；纯诊断文案/附加字段不重置。

---

## 2. Target data model

### 2.1 Manifest v2

**判别器：manifest v2 = `schema_version: 2`。** 它只判别 manifest；lock 与每个新增 typed source 各有
自己的 `schema_version`，禁止拿 manifest version 猜测另一文件格式。
评审期观测：`check_development_agent.py:37` 与 `check_agents_projection.py:54` 均钉
`KNOWN_MANIFEST_SCHEMA_VERSIONS = {1}` 且未知版本 exit 2 / FatalCheckError——PR-B 必须**先**把两处放宽为
`{1, 2}`（dormant：彼时真实树仍为 v1），PR-C1 才能写入 v2。

保留现役 `required`、`projection`、既有 Claude support/approval/enforcement 字段；新增：

```yaml
schema_version: 2
capabilities:
  - id: mj-agent-flow-plan
    required: true
    projection: project
    codex_carrier: translated
    carrier_binding:
      workflow_id: flow-plan
```

Schema：

- `codex_carrier: none | byte-copy | translated`。
- `none` 与 `byte-copy` 必须没有 `carrier_binding`；`translated` 必须有且只能有
  `carrier_binding.workflow_id`。
- output path 不进入 manifest：由 capability id 唯一派生为
  `.agents/skills/<capability-id>/SKILL.md`。capability id 必须满足现有 id 语法，normalized repo-relative
  path 必须位于该根下；拒绝 absolute、drive/UNC、`..`、空 segment、casefold collision、symlink/junction/
  reparse ancestor 与重复 owner。
- `workflow_id` 必须在 `development-agent-workflows.yml` 中恰好存在一次，且 registry 的
  `capability_id` 必须反向等于当前 capability；未知或重复 ID fail closed。
- `codex.support_mode` 继续使用现有五枚举
  `native | adapter-backed | script-ci | manual | unsupported`；本轮有 project carrier 的 required
  capability 使用 `native`，不引入不存在的 `carrier-backed`。
- 本轮不序列化 `scope` 与 `discoverability_required`；它们由 required、workflow registry、path ownership
  和 carrier 派生。等出现首个真实 claude-only/codex-only capability 时，再用独立 schema migration 引入 scope。

强制 invariant：

1. `codex_carrier != none` 当且仅当 `projection == project`。
2. `required == true` 必须有 Codex carrier。
3. `.agents` expected set、reconcile set 与 lock entries 从 `codex_carrier != none` 派生。
4. `--adopt` eligible set 只从 `codex_carrier == byte-copy` 派生。
5. translated/none 的 `--adopt <name>` 必须 exit 2，且 source、artifact、lock 均零写入。
6. PR-C1 cutover snapshot 预期为 5 个 byte-copy、13 个 translated、19 个 none；测试从冻结 manifest
   动态派生期望并把 snapshot 写入 evidence，schema/validator 不硬编码这三个数字。
7. 5 个 byte-copy 的 adopt 仍是会写 protected Claude source 的 Owner-gated 操作，本计划不执行；legacy
   v1 lock 下 adopt 固定 `ADOPT_REQUIRES_LOCK_V2` / exit 2 / 三面零写，只有切到 verified v2 lock 后才可能
   满足 §2.7 CAS；13 个 translated 永久不 eligible。

V8（`check_development_agent.py`）在 PR-B 同步获得 `codex_carrier`/`carrier_binding`、合法
`support_mode`、path derivation 与 invariant 1–2 的 DA 级校验，使 manifest 自身的 blocking gate 对新字段
不盲。workflow ID 反向闭合由 blocking V9 与 real-tree blocking Tests pin 双重验证。

### 2.2 Required 18 carrier matrix

现有 5 项 byte-copy：

| Capability | `projection` | `codex_carrier` |
|---|---|---|
| mj-agent-flow-diagnose | project | byte-copy |
| mj-agent-git-commit | project | byte-copy |
| mj-agent-git-delete | project | byte-copy |
| mj-agent-git-push | project | byte-copy |
| mj-agent-git-sync | project | byte-copy |

新增 13 项 translated（PR-C1 cutover 时全部翻为 `projection: project`）：

| Capability | `codex_carrier` |
|---|---|
| mj-agent-doc-validate | translated |
| mj-agent-flow-intake | translated |
| mj-agent-flow-plan | translated |
| mj-agent-flow-implement | translated |
| mj-agent-flow-repo-scan | translated |
| mj-agent-flow-verify | translated |
| mj-agent-flow-scope-drift | translated |
| mj-agent-flow-self-review | translated |
| mj-agent-flow-review-respond | translated |
| mj-agent-flow-post-merge | translated |
| mj-agent-git-branch | translated |
| mj-agent-git-issue | translated |
| mj-agent-git-pr | translated |

对三个既有 `projection: never` 必须在 ADR-039 逐项记录反转理由，并且 **PR-C1 cutover 同树把这三行的
manifest rationale 注释改为指向 ADR-039，并将 `codex.support_mode` 改为现有合法枚举 `native`**（carrier
strategy 由正交字段 `codex_carrier: translated` 表达，禁止发明 `carrier-backed` support mode；避免
「script-ci equivalent」旧注释与新事实并存）：

- `mj-agent-doc-validate`：script/CI 可以执行 validator，但不能替代交互式验证路由、结果解释和停止条件。
- `mj-agent-flow-verify`：CI 不能替代 Level A/B/C、Owner stop 与 evidence orchestration。
- `mj-agent-git-issue`：`gh` 只是 transport，不能替代 template routing、preview、confirm、assignee 与 HITL。

Issue template 的当前数量与「5 branch-type + 3 topical」只作为由 `.github/ISSUE_TEMPLATE/` 实时枚举得到的
evidence；validator 不把 8 写成永久常量。

#### 2.2.1 终态 18-carrier canonical matrix

PR-C1 必须逐行断言下表；除 `codex_carrier` 与 translated 的 `workflow_id` 外，所有行的
`required=true`、`projection=project`、`codex.support_mode=native` 均相同。byte-copy 行不得携带
`workflow_id`，translated 行必须携带且只能携带所列 ID。

| Capability | codex_carrier | workflow_id | required | projection | codex.support_mode |
|---|---|---|---|---|---|
| mj-agent-flow-diagnose | byte-copy | absent | true | project | native |
| mj-agent-git-commit | byte-copy | absent | true | project | native |
| mj-agent-git-delete | byte-copy | absent | true | project | native |
| mj-agent-git-push | byte-copy | absent | true | project | native |
| mj-agent-git-sync | byte-copy | absent | true | project | native |
| mj-agent-doc-validate | translated | doc-validate | true | project | native |
| mj-agent-flow-intake | translated | flow-intake | true | project | native |
| mj-agent-flow-plan | translated | flow-plan | true | project | native |
| mj-agent-flow-implement | translated | flow-implement | true | project | native |
| mj-agent-flow-repo-scan | translated | flow-repo-scan | true | project | native |
| mj-agent-flow-verify | translated | flow-verify | true | project | native |
| mj-agent-flow-scope-drift | translated | flow-scope-drift | true | project | native |
| mj-agent-flow-self-review | translated | flow-self-review | true | project | native |
| mj-agent-flow-review-respond | translated | flow-review-respond | true | project | native |
| mj-agent-flow-post-merge | translated | flow-post-merge | true | project | native |
| mj-agent-git-branch | translated | git-branch | true | project | native |
| mj-agent-git-issue | translated | git-issue | true | project | native |
| mj-agent-git-pr | translated | git-pr | true | project | native |

### 2.3 Optional 19 disposition

本轮 optional capability 不获得 Codex native carrier。下表的「Codex route」列是**描述性 disposition
（保留既有审计口径），不是 §2.5 `codex_substitute` 枚举的成员**；边级的规范性替代路由一律在 dependency
registry 按 §2.5 的闭合枚举登记。

| Capability | Existing projection | Codex route in this plan |
|---|---|---|
| mj-agent-doc-author | after-neutralization | adapter-backed shared semantics |
| mj-agent-doc-migrate | after-neutralization | adapter-backed shared semantics |
| mj-agent-doc-plan | after-neutralization | adapter-backed shared semantics |
| mj-agent-doc-review | after-neutralization | adapter-backed shared semantics |
| mj-agent-doc-sync | after-neutralization | adapter-backed shared semantics |
| mj-agent-git-check-merge | after-neutralization | owner/manual route |
| mj-agent-git-review-pr | after-neutralization | adapter-backed shared semantics |
| mj-agent-infra-app-start | never | manual; no carrier |
| mj-agent-infra-app-stop | never | manual; no carrier |
| mj-agent-infra-docker-compose | never | manual; no carrier |
| mj-agent-infra-env-setup | never | manual; no carrier |
| mj-agent-infra-env-teardown | never | manual; no carrier |
| mj-agent-infra-llm-endpoint-probe | never | manual; no carrier |
| mj-agent-infra-storage-stack | never | manual; no carrier |
| mj-agent-infra-studio-probe | never | manual; source-backed advisory edge allowed |
| mj-agent-runtime-biz-catalog-sync | after-neutralization | protected owner-manual route |
| mj-agent-runtime-eval-baseline | after-neutralization | adapter-backed route |
| mj-agent-runtime-prompt-version-bump | after-neutralization | protected owner-manual route |
| mj-agent-runtime-skill-doc-improve | after-neutralization | protected owner-manual route |

「没有 carrier」不等于「依赖可以消失」。任何 18 项 carrier 指向上述目标的 source-backed edge，必须在
dependency registry 中声明可执行 substitute，并被实际渲染进来源 carrier。

### 2.4 Translation ownership

具名 source：

```text
sdd/adapters/codex-skill-translation.yml   # schema_version + lexicon + transform/no-op + interaction/site registry
sdd/adapters/codex-skill-preface.md        # 所有 translated carrier 的稳定 Codex 前言
sdd/workflows/development-agent-workflows.yml   # schema_version + workflow/dependency 语义 registry
```

职责边界：

- `development-agent-workflows.yml` 是 workflow/dependency 语义 registry。
- 每个 translated workflow 还拥有 tool-specific metadata 字段 `codex_discovery_summary` 与
  `required_trigger_terms`：summary 是 Codex discovery budget 的确定性紧凑投影，不是第二份 workflow prose；
  source description、summary、正/负 trigger fixtures 与人工 fidelity attestation 必须闭合。
- `codex-skill-translation.yml` 是 harness primitive 处置的 SoT，不是 workflow 语义 SoT；它不重复
  dependency route，只通过 edge ID 引用 registry。
- 两个 YAML 各自固定 `schema_version: 1`、known-version set 与 canonical slice serialization；unknown
  version 在任何写入/删除前 exit 2。每个 interaction site 使用稳定 `site_id` +
  `source_evidence.marker`，marker 在指定 source 中必须唯一命中；不再用易漂移的
  `(heading, occurrence-index)` 作为 identity。
- `codex-skill-preface.md` 前置于每个 translated carrier，内容至少包含：本文件为生成产物、语义差异声明
  （Claude harness 的 ask-gates/权限 prompt/PreToolUse hooks 在 Codex 不在场，正文中对它们的引用一律读作
  AGENTS.md 自守义务——沿用 root `AGENTS.md` semantic caveat 的先例）、`superpowers:*` 与其他可选
  skill 必须先做当前 Codex capability discovery：可发现时以 `$skill-name` 或显式 “use skill-name”
  调用，不可发现时执行正文给出的手工等价流程；不得硬编码为 Claude-only。
- renderer 保留 source 正文、heading、编号步骤、validator、Level A/B/C、精确 handler 名、G1/G2、issue
  路由和 policy refs。

**变换模型 = 三个替换类 + preface 覆盖的 no-op 类 + lexicon fail-closed：**

替换类（全部机器可判定）：

| 类 | 规则 | 判定方式 |
|---|---|---|
| T1a Owner gate | stable template 原样保留 prompt、options、default 与待批准 action，再追加 `OWNER_APPROVAL_REQUIRED(<canonical-reason>)` + ask/stop/wait；只有 registry 标为 owner-gate 且与 manifest reason 闭合才使用 | stable site ID + marker + manifest/registry + typed template |
| T1b 普通交互 | stable site template 原样保留 prompt、options 与默认值，并发射 tool-neutral 指令“ask the user and wait before continuing”；不升级为 Owner gate | stable site ID + marker + typed interaction template；未分类 `AskUserQuestion` fail closed |
| T2a Layer-A skill 调用 | 三区域内 carrier target 的 `/mj-agent-*` → Codex `$mj-agent-*`；无 carrier target → registry edge 的 substitute route | §2.5 三区域定位 + edge ID |
| T2b Layer-B route | registry 声明 construct type 与 placement；parser 验证完整 construct boundary 后插入带 identity 的确定性 route；frontmatter description 使用 scalar-safe identity，不向 YAML 中插 Markdown block | 唯一 marker + edge ID + typed construct/placement template |
| T3 同侪 carrier 路径 | `.claude/skills/<name>/SKILL.md` 且 `<name>` 在 carrier 集内 → 重写为 `.agents/skills/<name>/SKILL.md` | 路径正则 + manifest 派生集 |

T1 分类依据是语义 registry，不是工具名字符串。例：`mj-agent-git-issue` 当前
`approval.mode: none`，其模板选择/preview/confirm 属 T1b；只有 manifest/registry 明确登记的拍板位点才属
T1a。任何 `AskUserQuestion` token 没有唯一 site classification 时 renderer 必须红，禁止 blanket upgrade。
T1a 与 T1b 使用不同 template/golden；两者都必须逐字段证明 prompt/options/default/action 未丢失。T1a 以
canonical reason + “ask the Owner, stop, and wait”终止；T1b 以“ask the user and wait before continuing”
终止，不能把任一交互改成可自行继续的建议。

T2b 的闭合枚举为 `construct: paragraph | list-item | table | fenced-block | frontmatter-description`，对应
`placement: after-paragraph | after-list-item | after-table | after-fenced-block | replace-description-scalar`；不接受
自由字符串。renderer 先用 Markdown/frontmatter parser 证明 marker 位于所声明 construct 且 boundary 唯一，
再插入 block。body identity 固定为 `<!-- codex-route:<edge-id> -->`；frontmatter identity 固定为单行
`[codex-route:<edge-id>]` 并计入 discovery summary 长度；source marker 仍在原 description 中唯一匹配，
renderer 把 route identity/template 确定性追加到 registry summary，而不是把旧 description 原样带入。
paragraph/list/table/fence/frontmatter 五类分别有
precommitted golden；类型不符、marker 跨 boundary 或插入点不唯一均 fail closed。

T2a 也按 construct 安全发射，不能只做裸字符串替换：

- Handoff/Sub-skill 的 paragraph/list/table 中只把 exact slash token 改为 `$<capability-id>` 或短的
  `Codex substitute <edge-id>`；在整个 construct boundary **之后**另起一行发射
  `<!-- codex-route:<edge-id> -->` 与确定性 route block。多 edge 按 edge ID 排序；table identity 永不插入 cell。
- `dot` fenced block 内，carrier target 只在 quoted label 中用 DOT-escaped `$<capability-id>`；无-carrier
  target 使用 DOT-escaped `Codex substitute <edge-id>` 短标签，完整 route 与 HTML identity 一律放在 closing
  fence 后，绝不把 HTML/Markdown/长 substitute 塞进 DOT grammar。
- paragraph/list/table/DOT 各有 exact-byte golden；Markdown parser 与 Graphviz parser（或仓库已批准的等价
  DOT parser）必须证明输出仍有效。identity placement、escaping 或 construct type 不闭合即红。

preface 覆盖的 no-op 类（原样透传，由 preface 声明兜住语义；处置在 lexicon 中显式登记）：

- harness-enforcement 引用（`PreToolUse`、hook、`guard-git-workflow`、`.claude/settings.json`、
  `.claude/scripts/**`）——carrier 正文**永不改写为点名 `.codex/hooks`/rules**，从而渲染结果对 PR-D1a
  是否落地保持不变（translation-map invariant：PR-D1a 落地不需要任何 carrier 重渲）；
- ask-gate/permissions 词汇（含否定语境，如「无 `permissions.ask`」——透传天然保真）；
- Claude 工具名（Edit/Write 等）、Claude 自称；
- `superpowers:*`（preface 统一给出 capability-discovery fallback，不宣称不可调用）；
- 拍板/必停/`OWNER_APPROVAL_REQUIRED` 散文（本就 tool-neutral，零处置）；
- 非 carrier 集或跨仓的 `.claude` 路径（provenance 引用，声明 no-op）；
- 相对 wikilink（两侧目录深度相同，零改写）。

**Harness-token lexicon（fail-closed 的检测域）：** `codex-skill-translation.yml` 内置版本化 lexicon，
种子 = 评审期 census 的全部类别（`.claude/` 路径模式、`superpowers:`、`AskUserQuestion`、`PreToolUse`、
hook、`guard-git-workflow`、`permissions.ask`/ask-gate/`settings.json`、Claude 工具名、Claude 自称）。
**fail-closed 定义：正文或 frontmatter 中任一 lexicon 命中，若无对应替换规则或显式 no-op 归类，渲染必须
失败**，并输出：

```text
capability id
source path 与 source 行文本
命中的 lexicon 类与 token
translation map 路径与期望的 key/section
建议的 remediation 顺序
```

不承诺「map 精确行号」；per-site override 用稳定 `site_id` + capability/path + 唯一 verbatim marker
锚定。marker 零命中或多命中、site ID 重复、edge ID 不存在都必须红（不只对未知 token 红）。

**Renderer wire format：**

- byte-copy carrier 返回并写入 source raw bytes，包含原始 BOM/EOL/final-newline；其 identity 是 raw
  SHA-256，不做 LF normalization。
- translated carrier 先解析完整 frontmatter；opening `---` 必须是输出第一字节，输出顺序固定为
  `frontmatter → closing delimiter → Codex preface → translated body`。
- frontmatter 的 exact allowlist 与 fixed key order 都是 `name`、`description`；缺失、额外、重复 key、非 scalar
  或 YAML tag/alias 均在写入前失败，禁止静默丢字段。decoded `name` 值逐字不变；source `description` 走与
  body 相同的 lexicon/classifier，但 translated 输出的 `description` 使用 registry 的
  `codex_discovery_summary`，以 UTF-8、`ensure_ascii=false` 的 JSON-style double-quoted YAML scalar 发射。
  summary 必须单行、包含全部 `required_trigger_terms`、通过 lexicon，并由正/负 implicit-trigger golden 与
  fidelity attestation 证明没有扩大/缩小触发语义；输入 quoted/folded 形态不得影响输出。
- translated 输出固定 UTF-8 无 BOM、LF、恰一个 final newline。preface 前后空行数固定在 golden files。
- scanner 覆盖 frontmatter、正文、fenced code、inline code 与 Markdown link；transform 只作用于已分类
  exact token/path/site，禁止裸全局 regex。shell/text fence 中的 slash command 可按 T2 转换；示例/禁止项
  可在 map 标为 no-op；link destination 的同侪 path 按 T3 转换，link label 独立分类。
- census 在 PR-B 用**未剥离 frontmatter** 的版本重测。translated lock digest 覆盖整个 canonical output
  （含 frontmatter 与 preface）；CRLF、BOM、quoted/folded description、Unicode、fence、inline-code 与 link
  都有预提交 golden fixture。

### 2.5 Dependency registry

每条 edge 使用三个正交轴：

```yaml
edges:
  - id: edge-flow-implement-diagnose
    from: mj-agent-flow-implement
    to: mj-agent-flow-diagnose
    relation: call
    activation: conditional
    closure: carrier-required
    source_evidence:
      marker_id: flow-implement-diagnose-delegation
      path: .claude/skills/mj-agent-flow-implement/SKILL.md
      marker: "委派判据（硬 bug / perf / flaky）"
      # marker 是机器锚：checker 验证该 verbatim 子串在 path 中唯一存在，零/多命中均红。
      # section 字段可选，仅人读注释，不做机器校验。
```

枚举：

- `relation: call | handoff | reference`
- `activation: always | conditional | owner-gated`
- `closure: carrier-required | substitute-required | advisory`

**Source evidence 两层模型：**

层 A——机器扫描（自动、双向 fail-closed）。扫描域为 18 个 carrier 源文件中、位于下列**三个区域**内、
形如 `/mj-agent-<id>` 或 `/mj-agent-<prefix>-*` 的**词边界 slash-form token**：

1. Handoff 区：标题匹配既有 V9 parser 语义（`^(#{2,})\s*Handoff`，前缀匹配 + 层级退出——评审期观测
   `check_agents_projection.py:71-73` 与 `:146-164`；该 parser 随 PR-A1 抽入 shared loader，V9 与本
   scanner 读同一实现）。
2. Sub-skill 区：标题匹配
   `^#{1,6}\s+(?:Sub-skill(?:\s*/\s*Tool Calls|\s+Calls)?|Tool Calls)(?:\s|$)`
   （alternation 必须分组并锚定；评审期观测：18 项中 9 个有此节，形态含
   `## Sub-skill / Tool Calls` 与 `## Sub-skill Calls`；`flow-verify` 的 `## Direct Bash Calls（No
   Sub-skill Delegation）` 是显式非匹配）。
3. 图区：`dot` fenced code block（**graphviz DOT，不是 Mermaid**——评审期观测仓库 mermaid fence = 0、dot fence = 24；
   18 项中 11 个有图，7 个 git-* 无图，故图区永远不是必需构造）。

层 A 之外的一切**不构成自动边**：散文提及、路径片段（如 `/tmp/mj-agent-issue-body-<type>.md`）、
frontmatter、禁止行（`❌ 不调 …`）、裸 `mj-agent-…` token（容器名、形容词）均按构造非边。

层 B——marker 锚定的声明边。真实依赖不在三区域内的（散文委派判据、description 内路由），由 registry
显式登记 `marker_id/path/marker`；checker 对每条声明边验证 marker 在 path 中唯一命中。renderer 按 T2b
把 edge route 写回来源 carrier：正文 marker 后插入 edge-ID 标记的 deterministic block；frontmatter marker
只在 description scalar 内替换。零/多命中、重复 marker ID、已有输出 marker 冲突或 route template 缺失均红。

双向 gate：

- source → registry：层 A 每条解析出的 edge 必须恰有一个 registry classification；
- registry → source：每条 registry edge 必须有层 A 命中或层 B marker 命中；无 unchecked exemption；
- renderer 将 edge ID 与 route/substitute 按 T2a/T2b 写入来源 Codex carrier；checker 同时验证每个声明
  edge 恰好出现一次相应 `codex-route:<edge-id>` identity（frontmatter 使用方括号 identity；Layer-A 的
  identity 位于完整 construct/DOT fence 之后的独立 comment，不污染原语法）；
- fixture 断言 `carrier-required` 指向无 carrier 时非零退出；
- fixture 断言三条禁止行（评审期观测 `flow-scope-drift:170`、`flow-self-review:266`、`flow-intake:305`）
  **(a) 不产生 registry edge、(b) 渲染后 token 原样保留且不追加 substitute route**。

判定规则：

- source workflow 的声明 outcome 若依赖某个无条件编号步骤子调用，通常是 `closure: carrier-required`。
- 条件性、Owner-gated 与 handoff 不自动决定 closure；按「目标缺失时来源 carrier 是否仍能完成所声明
  outcome」判定。
- `carrier-required` 目标必须有 carrier，不能用 substitute 冒充；`carrier-required → none` 始终硬失败。
- 任何 target 无 carrier 的 source-backed edge（包括 advisory）都必须有非空 `codex_substitute` 或明确的
  by-design disposition；advisory 只表示该边不阻断来源 outcome，不豁免 Codex route。
- 非 advisory 的无-carrier edge 必须是 `substitute-required`。
- `infra-studio-probe` 的路由表引用注册为层 B 声明边（advisory + substitute/disposition），不设
  no-route 豁免。
- `mj-agent-runtime-*` wildcard 在 scanner 中确定性展开，展开集与 digest 写入 lock；新增匹配项造成显式
  drift。

`codex_substitute` 闭合枚举与**选择规则**：

| Value | 判据 | 必填字段 |
|---|---|---|
| tool-neutral-command | 存在 Codex 会话可独立执行的命令/validator | `route_ref` |
| inline-procedure | substitute 是 registry 内过程描述，无单一命令 | `route_ref` |
| owner-manual-route | 完成必须经 Owner 动作 | `route_ref` + `policy_ref` |
| claude-only-by-design | Codex 侧无完成路径 | `rationale` + `policy_ref` |

### 2.6 Lock v2 与统一 desired-artifact oracle

**顶层 envelope 与序列化合同：**

```json
{
  "entries": {
    ".agents/skills/mj-agent-flow-plan/SKILL.md": {
      "entry_kind": "skill-translated",
      "inputs": {
        "manifest_slice_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "preface_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "renderer_module": "scripts.sdd._common.skill_renderer",
        "renderer_module_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "renderer_version": 1,
        "source_path": ".claude/skills/mj-agent-flow-plan/SKILL.md",
        "source_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "translation_map_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "workflow_slice_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "normalization_policy": "translated-utf8-lf-v1",
      "output_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "owner": "capability:mj-agent-flow-plan",
      "strategy": "translated",
      "surface_members": ["skills"]
    }
  },
  "generator_protocol_version": 1,
  "schema_version": 2
}
```

- 上例重复使用已知 SHA-256 仅展示 64-hex wire shape；实现必须从对应 bytes 实算，fixture 断言不同输入不能
  被常量 digest 代替。
- lock 是 JSON；key 与 object key 均按 Unicode code point 排序，UTF-8 无 BOM、LF、2-space indent、
  `ensure_ascii=false`、恰一个 final newline。任何非 canonical bytes 在 check 中判 drift。
- v2 顶层只允许 `schema_version`、`generator_protocol_version`、`entries`，当前 known protocol set = `{1}`；
  unknown protocol、额外/缺失顶层 key、entry 的未知字段或 output-class 不允许的 input 字段都按 malformed
  处理，sync/adopt 零写/零删。`surface_members` 是非空、排序去重的 `skills | mcp | enforcement` 子集。
- JSON parser 必须用 duplicate-key-rejecting mode；任何层级重复 key 在 canonicalization 前就 malformed。
  digest 字段均为 JSON string 且匹配 `^[0-9a-f]{64}$`（只有 legacy v1 value 带 `sha256:`）；version 是
  JSON integer 且 `>= 1`；path/owner/enum 是非空 JSON string；array 类型、排序、唯一性都严格验证。

**v2 entry closed union（没有 optional catch-all）：** 每个 entry 的 common required keys 恰为
`entry_kind / owner / surface_members / strategy / normalization_policy / output_sha256`，再按 kind 选择
`inputs` 或 composite member fields；额外、缺失、wrong-type 与 cross-kind 组合全部失败。

| `entry_kind` | `surface_members` | `strategy` | `normalization_policy` | `owner` shape | exact kind-specific required fields |
|---|---|---|---|---|---|
| `skill-byte-copy` | `["skills"]` | `byte-copy` | `raw-bytes-v1` | `capability:<id>` | `inputs` = source_path/source_sha256/manifest_slice_sha256/renderer_module/renderer_module_sha256/renderer_version |
| `skill-translated` | `["skills"]` | `translated` | `translated-utf8-lf-v1` | `capability:<id>` | `inputs` = source_path/source_sha256/manifest_slice_sha256/workflow_slice_sha256/translation_map_sha256/preface_sha256/renderer_module/renderer_module_sha256/renderer_version |
| `skills-readme` | `["skills"]` | `rendered` | `generated-utf8-lf-v1` | `system:skills-readme` | `inputs` = manifest_slice_sha256/template_path/template_sha256/template_version/renderer_module/renderer_module_sha256/renderer_version |
| `codex-config-mcp` | `["mcp"]` | `rendered` | `canonical-toml-v1` | `system:codex-config` | `inputs` = mcp_source_path/mcp_source_sha256/manifest_mcp_slice_sha256/codex_posture_slice_sha256/renderer_module/renderer_module_sha256/renderer_version |
| `codex-config-composite` | `["enforcement", "mcp"]` | `rendered` | `canonical-toml-v1` | `system:codex-config` | `member_inputs` + `member_input_sha256` + `member_output_sha256`（wire 见下）; `inputs` forbidden |
| `codex-hook` | `["enforcement"]` | `rendered` | `canonical-json-v1` | `system:codex-hooks` | `inputs` = enforcement_source_sha256/policy_refs_sha256/renderer_module/renderer_module_sha256/renderer_version |
| `codex-rule` | `["enforcement"]` | `rendered` | `generated-utf8-lf-v1` | `system:codex-rules:` + normalized repo-relative output path | `inputs` = enforcement_source_sha256/policy_refs_sha256/renderer_module/renderer_module_sha256/renderer_version |

`inputs` 本身也是 closed object，表中 slash 分隔的是 exact key 集、无 optional key；owner/path 必须与
entry key/manifest/typed source 唯一重建结果相等。每个 kind 都有 missing/extra/wrong-type/wrong-owner/
wrong-surface/wrong-strategy/wrong-normalization/invalid-digest negative fixtures。
- entry key 是 NFC、POSIX slash、case-preserving 的 normalized repo-relative output path；同一物理 path/
  casefold path 只能有一个 owner。absolute、drive/UNC、`.`/`..`、空 segment、root escape、symlink/
  junction/reparse ancestor 或 file-type collision 在 preflight 阶段 exit 2、零写/零删。
- byte-copy entry 使用 `normalization_policy: raw-bytes-v1` 且 source/output digest 都是 raw SHA-256；
  translated entry 使用 §2.4 canonical bytes。不得把 byte-copy 暗中 LF-normalize。
- v1 skill digest 是 LF-normalized、剥 frontmatter 的 body hash（评审期观测 `_normalized_body_hash`）；reserved
  `.codex/config.toml` 复用 `body_sha256`，因 TOML 无 frontmatter而覆盖完整 LF-normalized text。v1/v2 digest
  域仍不同，dispatch 必须按 key class 分开，禁止静默互换。
- `renderer_module_sha256` 只摘该 output class 的专用模块。skill、README、MCP/config、hooks、rules 各有
  聚焦 module/version，改 README template/renderer 不得 churn 13 个 skill entry。

**版本兼容矩阵：**

| Manifest | Lock | `--check` | `sync` |
|---|---|---|---|
| v1 | legacy v1 flat map（无 `schema_version`；value 严格匹配 `^sha256:[0-9a-f]{64}$`） | 保持当前 clean 语义 | 保持 legacy 行为；adopt 禁用 |
| v2 | v2 envelope | 按 v2 entry/closure 校验 | 正常 deterministic converge |
| v1 | verified v2 | mismatch，非零 | 仅把 v2 entries 当只读 ownership ledger，按 v1 desired set 收敛并写回 v1 lock；用于 rollback |
| v2 | verified v1 | mismatch，非零 | 仅把 v1 keys 当只读 ownership ledger，渲染全部 v2 desired outputs 并写出 v2 envelope；用于 cutover |
| 任意 | unknown/malformed/mixed | 非零 | exit 2，artifact/source/lock 零写入、零删除 |

legacy v1 key 只允许两类：reserved output key `.codex/config.toml`，或能通过 v1 manifest 唯一映射到
`.agents/skills/<capability-id>/SKILL.md` 的 capability ID；其 digest 域继续是现役
`_normalized_body_hash`，不是 raw/full-file hash。bare 64-hex、错误前缀/大小写、路径式 skill key、envelope/flat-map
混合体都属于 malformed，negative fixtures 固定为零写/零删。

“verified old lock”至少要求上述格式严格、重建后的所有 path 通过 containment/casefold/reparse 检查、owner 可从
对应 legacy manifest 唯一重建；否则不允许把它作为 deletion ledger。v2 → v1 rollback 的 golden scenario
必须精确删除 13 个 old-owned translated carrier，保留 5 个 byte-copy 与全部 unowned 邻居。

**特殊 output：**

- `.agents/README.md` 有独立 raw Markdown template `sdd/adapters/codex-skills-readme.md`、独立 renderer module/
  version 与独立 lock entry（`surface_members: ["skills"]`）。它从 manifest 派生 strategy 统计与说明；
  enforcement ownership/review 文案来自模板自己的 inputs，不通过修改 shared skill renderer 偷渡。
- Markdown template 本身不是 typed source：README template version 由 manifest v2 的
  `codex_readme_template_version` 所有，preface version 由 `codex-skill-translation.yml` 的
  `preface_template_version` 所有；lock 同时记录 raw template SHA-256。只有 YAML/JSON typed sources 自带
  `schema_version`/known-version preflight，禁止假装 Markdown 有未定义的 schema discriminator。
- enforcement entries 使用同一 envelope，inputs 含 `enforcement_source_sha256` 与各自 renderer digest。
  MCP entry 继续属于 `mcp`。
- 同一 output path 只能有一个 entry。若 P1 的 explicit route 必须把 binding 写入
  `.codex/config.toml`，entry 使用排序后的 `surface_members: ["enforcement", "mcp"]`，并记录
  `member_output_sha256.mcp` 与 `member_output_sha256.enforcement`，另有 `output_sha256` 覆盖整文件。

```json
{
  "member_input_sha256": {
    "enforcement": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "mcp": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "shared": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "member_inputs": {
    "enforcement": {
      "binding_slice_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "enforcement_source_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "mcp": {
      "codex_posture_slice_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "manifest_mcp_slice_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "mcp_source_path": ".mcp.json",
      "mcp_source_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "shared": {
      "renderer_module": "scripts.sdd._common.codex_config_renderer",
      "renderer_module_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "renderer_version": 1
    }
  },
  "member_output_sha256": {
    "enforcement": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "mcp": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```

上述重复使用已知 SHA-256 只表示 wire grammar；fixture 必须使用不同输入实算不同 digest。
三个 member object/key set 都是 exact closed schema；`member_input_sha256.<member>` 是按 lock canonical
JSON 规则序列化相应 `member_inputs.<member>` 后的 SHA-256。

| Member | 唯一拥有的 parsed TOML data | 不拥有的 bytes |
|---|---|---|
| `mcp` | top-level `approval_policy`、`sandbox_mode`、`project_doc_max_bytes` 与完整 `mcp_servers` subtree | 注释、空白、key order |
| `enforcement` | P1 证明后写入 typed binding schema 的 exact、closed、与 MCP 不相交的 top-level/subtree keys | 注释、空白、key order |
| shared renderer | generated header、注释、空白、排序、quote 与 final newline | 任何语义 key/value |

- member hash = 将该 member 的 parsed typed TOML data 投影为 closed object 后，按 lock 的 canonical JSON
  规则序列化所得 bytes 的 SHA-256；comments/header/whitespace 不进入任何 member hash，只进入 full
  `output_sha256` 与 shared renderer digest。full-file renderer 顺序固定，且必须能由两个 member objects +
  renderer version 唯一重建。
- scoped `--check --surface mcp`/V11 只判断 MCP member inputs/hash；enforcement-only drift 由 enforcement
  check/Tests/V13 判断。scoped sync 仍重渲整份物理文件并只更新这一 shared lock entry，但 apply 前必须证明
  未选 member 的 input closure/hash 与旧 lock 一致；否则 exit 2 并要求 `--surface all`，不能夹带另一 member
  的变化。选中 member 的 closure/input hash 与 output hash更新；未选 member 的对象/hash 必须重算后仍与旧
  lock 相等；full output hash随整文件更新。`--surface all` 比较 full desired bytes/output hash，并反向重建
  两 member output hashes与三个 member input hashes。任一未归属 TOML
  key、key overlap、无法重建或 scoped member 偷变均 blocking 失败。若实现无法做到该隔离，必须在启用
  explicit route 前为 V11 scope expansion 取得独立 `ci-blocking-gate-toggle`，不得借既有 V11 绕过 V13。
- shared renderer module/version 是两个 member 的共同 input；它变化时任何 scoped sync 都 exit 2 并要求
  `--surface all`，不能以“只有 comments/whitespace”绕过全文件 review。
- direct route 不需要 binding 时，`.codex/config.toml` 保持纯 MCP entry。
- explicit route 会扩展评审期固定三元组 `_POSTURE_KEYS` 的输入模型；PR-B 必须在 D-017 Owner 拍板后
  更新 typed posture/binding schema、emitter 与 negative fixtures，禁止 ad-hoc extra key。

V10 的唯一 oracle：

```text
canonicalize(actual, normalization_policy)
  == canonicalize(render_desired_artifact(all declared inputs), normalization_policy)
```

- byte-copy 也走该接口；renderer 返回原始 source bytes，sync 写入保持 byte-identical。
- translated 走 source + manifest slice + workflow slice + map + preface + renderer module digest +
  renderer version。
- check 同时验证 lock input/output digest closure；任一输入变化但未重渲必须失败。
- orphan 检测按 `surface → owned lock keys` 映射执行，不再以 skills/mcp 的二分 `if/else` 推断。
- **V9 `check_lock`（PJ030–PJ034）按 lock schema 分派**：v1 树保持现有语义原样通过；v2 树按上述 entry
  结构校验。PJ030/PJ032/PJ033/PJ034 的 co-landing、hash-mismatch、orphan 语义在两种 schema 下都保留，
  **任何 PJ03x 不得为通过 PR-C1 而退休或重排**。
- V9 同时承担 blocking path/owner/unknown-tracked closure；V10 承担 blocking skills desired-render。
  enforcement desired-render 在 PR-D2 通过 branch-protected blocking Tests backstop 执行，V13 只记录
  impact/status telemetry。

### 2.7 13 项 translated carrier 的稳态编辑协议（PR-G 合并后的 steady state；PR-B–PR-F 仍受 §1.1 freeze）

Claude 工程师与 Codex 工程师遵守同一路径；“谁使用哪个工具”不改变 source ownership：

| 发起者 | 允许的变更入口 | Claude 侧结果 | Codex 侧结果 |
|---|---|---|---|
| Claude 工程师 | 经 Owner gate 修改 authoring SoT，运行 sync | 直接消费新 source | deterministic carrier + lock 更新 |
| Codex 工程师 | 经同一 Owner gate 修改同一 authoring SoT，运行同一 sync | 直接消费新 source | deterministic carrier + lock 更新 |
| 任一工程师直接改 generated carrier | 禁止；blocking drift | 无 source 变化 | V9/V10/Tests 报错；不得把 artifact 当第二 SoT |

CI 不替工程师自动提交生成物，但 blocking check 强制 source + artifact + lock 同 change tree；因此“自动同步”
指相同输入得到确定输出并由 Git gate 强制收敛，不指后台进程在两个 artifact 间互相覆盖。

1. 取得 `.claude/**` protected-path Owner approval。若还要修改 workflow/interaction registry、translation
   map、preface/README raw template、fidelity schema、canonical serializer、renderer module/version 或任何
   schema/lexicon，必须再取得其对应 `declared-contract-change`/D-017 Owner approval；前一个 gate 不代替后一个。
2. 修改 authoring source skill；不得先改生成 artifact。当前 Phase A 的 prose SoT 位于
   `.claude/skills/**`，这只是历史 authoring location，不表示 Claude 工程师拥有独占编辑权。
3. 运行 scanner；未知 lexicon 命中**或无法解析/已过期的 per-site 锚**必须先红。
4. 若 workflow edge 改变，更新 workflow registry；若 carrier translation 规则改变，更新 translation
   map/preface。
5. renderer 行为改变时 bump `renderer_version`；纯 registry/map 数据变化不伪 bump code version。
6. 运行 sync，重渲 artifact 与 lock。
7. 同一 change tree 提交 source、registry/map、artifact、lock、tests、重新计算的 fidelity attestation 与
   必要 evidence。
8. `--adopt` 永远不适用于 translated carrier。
9. fidelity coverage report 由 renderer **机器生成**，枚举每个 source heading、Owner-stop、禁止项、
   validator、**frontmatter description**、edge route 的输出覆盖；先由独立 checker 做 exact inventory closure，
   再由具名 reviewer 确认 trigger/语义 judgment、抽查正文 fidelity 并创建 immutable approval record，不做无辅助
   全文对读，也不允许作者代填 reviewer verdict。

**byte-copy `--adopt` 是 recovery/import escape hatch，不是常规“双向同步”：**

- v1 lock 的 body-only digest 无法证明 frontmatter 未变，所以一律
  `ADOPT_REQUIRES_LOCK_V2` / exit 2 / source-artifact-lock 零写；不得用 v1→v2 隐式升级夹带 adopt。
- 取得 writer lock 后，artifact path 必须恰为 manifest 派生 path，verified v2 lock owner/strategy 必须为
  当前 capability/`byte-copy`。下表中的 `base` 是 v2 entry 记录的 source/output raw digest：

  | Current source | Current artifact | Result |
  |---|---|---|
  | base | base | no-op，exit 0，零写 |
  | base | changed | adopt success candidate：artifact raw bytes 成为新 source |
  | base | missing | exit 2，零写 |
  | changed | base | exit 2，零写 |
  | changed | changed（即使两者 bytes 相同） | exit 2，零写 |
  | changed | missing | exit 2，零写 |
  | missing | base | missing-source recovery candidate |
  | missing | changed | exit 2，零写 |
  | missing | missing | exit 2，零写 |

- changed/missing 判定覆盖完整 raw bytes（含 frontmatter/BOM/EOL）。source-missing recovery 还要求 source
  path 通过 containment/type 检查；任何 ambiguous/mixed state 均不猜测意图。
- CAS 通过后只写该 source，再用新 source 重新执行 normal sync 更新 artifact/lock；apply 前再次复核
  source/artifact/lock digest。任何复核失败零写。
- translated/none adopt、unknown lock、owner/path mismatch、symlink/reparse 与 casefold collision 永远
  exit 2 且零写。

`sdd/adapters/codex-skill-fidelity.yml` 是 tracked、`schema_version: 1` 的签署索引；13 个 translated
capability 必须被 3–4 个 tranche 恰好分区且无遗漏/重叠。set digest 的 wire 固定为：normalized
repo-relative path 按 Unicode code point 排序，构造 closed canonical JSON object `path → raw_sha256`，再对
UTF-8 canonical bytes 求 SHA-256；source/artifact/report set 不得使用目录 mtime、Git tree hash 或未排序 concat。

每个 tranche 记录 §2.8.5 的 manifest/source/artifact/translation/workflow/preface/renderer/coverage exact
digests、每项 source-description→discovery-summary trigger judgment，以及 provider-neutral
`approval_binding`。record ID 在索引中全局唯一；已 merge 记录不可原地改 reviewer/verdict，重审必须创建新
ID。checker 只能验证结构、唯一性、commit/digest binding，**不能凭文件内容认证人类身份**；
PR-C0/PR-C1 Owner gate 必须打开具名 review provider/ledger 的 immutable record，核对 reviewer、approved verdict 与
reviewed commit/source-set 后，才允许把该 record 标为 accepted。

`scripts/sdd/check_fidelity_attestations.py` 不 import renderer 的 coverage generator：它从 source/frontmatter、
manifest 与 workflow registry 独立派生 heading、Owner-stop、禁止项、validator、description、Level/handler/
Git/issue 与 route inventory，并要求 renderer coverage report 与该 inventory exact set closure。branch-protected
Tests 从当前树重算全部 input/set/report digest；unknown schema、缺签、分区错误、inventory 漏项或任一 digest
不同立即非零。negative fixture 故意让 renderer 与其自生成 report 同时漏掉同一 heading/stop/route，独立
checker 仍必须红。因此签署后变化会机器可证地 stale，但“签署真实”仍由上述 Owner record verification 承担。
PR-C1/后续 change tree 引用 exact attestation digest；checker/golden 不能由 renderer 运行时自填 expected。

---

### 2.8 Closed schema registry（v8 normative closure）

本节关闭 v7 评审中仍可由实现者猜测的字段；与 §2.1–§2.7 有冲突时以本节为准。

#### 2.8.1 Common canonicalization

- JSON：UTF-8 无 BOM、LF、2-space indent、`ensure_ascii=false`、object key 按 Unicode code point
  排序、array 保持 schema 指定顺序、恰一个 final newline；duplicate key 在 canonicalization 前拒绝。
- YAML typed source：只接受 safe scalar/list/map；拒绝 tag、alias、merge key、duplicate key、unknown
  schema version、extra key。进入 digest 前投影为本节声明的 closed JSON。
- path：NFC、POSIX slash、repo-relative、case-preserving；拒绝 absolute、drive/UNC、空 segment、`.` /
  `..`、root escape、casefold collision、symlink/junction/reparse ancestor、非 regular-file collision。
- SHA-256：lowercase 64-hex，对 schema 指定的 raw/canonical bytes 实算；测试必须证明不同输入产生不同 digest。
- unknown version、extra/missing/wrong-type、unknown enum 或 closure 不完整：check 非零；sync/adopt 在第一笔
  managed write/delete 前 exit 2。

Evidence scalar conventions:

- `started_at`、`completed_at` 与 `recorded_at` 固定为 UTC RFC 3339 second precision
  (`YYYY-MM-DDTHH:MM:SSZ`)，且 `completed_at >= started_at`。
- full Git SHA 使用 40 位 lowercase hex；所有 `*_sha256` 使用 64 位 lowercase hex。
- producer run ID 固定为
  `<schema-name>-<YYYYMMDDTHHMMSSZ>-<head12>`；时间段来自 UTC `started_at`。同路径已存在即 fail
  closed，不覆盖旧 evidence。
- 除明确表示执行顺序的 `observations` 外，schema 中的 set-like arrays 在 digest 前去重并按本节指定
  stable key 排序；任何未声明顺序不得由 filesystem enumeration 决定。

#### 2.8.2 Canonical slice definitions

| Digest | Exact canonical projection |
|---|---|
| `manifest_slice_sha256` | capability 的 `id,required,projection,codex_carrier,carrier_binding,codex.support_mode,approval,enforcement` |
| `workflow_slice_sha256` | exact workflow record + resolved edge records + §2.8.3 wildcard expansion object |
| `translation_map_sha256` | schema/version、lexicon、sites、templates 与 preface version 的完整 closed projection |
| `codex_posture_slice_sha256` | manifest `codex.posture` 的 declared keys only |
| `manifest_mcp_slice_sha256` | manifest MCP server projection records，按 server id 排序 |
| `binding_slice_sha256` | enforcement typed source 中属于 `.codex/config.toml` 的 binding member |
| `policy_refs_sha256` | §2.8.4 的 explicit policy-ref inventory；不得对目录/通配符直接 hash |

slice 不包含注释、mtime、Git tree hash、当前时间或未声明字段。

#### 2.8.3 Wildcard expansion wire

每个 workflow 的 wildcard 解析必须把集合和 digest 同时写进 translated lock entry：

```json
{
  "wildcard_expansions": [
    {
      "pattern": "/mj-agent-git-*",
      "resolved_ids": ["mj-agent-git-branch", "mj-agent-git-commit"]
    }
  ],
  "wildcard_expansions_sha256": "<sha256-of-canonical-array>"
}
```

- item exact keys = `pattern,resolved_ids`；pattern 按 code point 排序，`resolved_ids` 非空、排序、去重。
- 无 wildcard 时固定 `wildcard_expansions: []`，digest 仍必填。
- `skill-translated.inputs` 的 exact keys在 §2.6 表基础上新增上述两项；两者必须与
  `workflow_slice_sha256` 中的 expansion 完全一致。集合变化但 carrier 未重渲必红。

#### 2.8.4 Policy reference inventory

`codex-enforcement.yml` 只允许 explicit repo-relative `policy_refs[]`，不接受 glob。renderer 构造：

```json
{
  "schema_version": 1,
  "files": [
    {"path": "AGENTS.md", "raw_sha256": "<64-hex>"},
    {"path": "policies/ai-agent.md", "raw_sha256": "<64-hex>"}
  ]
}
```

`files` 按 path 排序且非空；item exact keys = `path,raw_sha256`。对 canonical bytes 求
`policy_refs_sha256`，并写入每个 `codex-hook`/`codex-rule` entry。声明文件缺失、path 不安全、digest
不一致或 typed source 漏列实际读取文件均 fail closed。

#### 2.8.5 Fidelity schemas and binding

Tracked index：`sdd/adapters/codex-skill-fidelity.yml`。Coverage：
`evidence/development-agent-v8/fidelity/coverage/<capability-id>.json`。

Coverage v1 exact top keys：

```text
schema_version, capability_id, source_path, artifact_path,
source_sha256, artifact_sha256, inventory_sha256, items
```

item exact keys：

```text
item_id, item_kind, source_locator, source_sha256,
artifact_locator, artifact_sha256, transform_class, status
```

- `item_kind` = `heading | owner-stop | prohibition | validator | frontmatter-description |
  dependency-route | level-handler | git-rule | issue-route`。
- `transform_class` = `T1a | T1b | T2a | T2b | T3 | NOOP`。
- `status` = `COVERED | INTENTIONALLY_NOOP`；缺失不以 status 表达，直接导致 inventory closure 失败。
- `inventory_sha256` 对 items 的 canonical closed projection求 digest；独立 checker 从 source/manifest/
  registry 重新派生 inventory，禁止 import renderer coverage generator。
- coverage 的 `source_sha256`/`artifact_sha256` 与 item-level digests 均覆盖对应文件或 locator slice 的
  raw UTF-8 bytes；set digests 使用 §2.7 的 sorted `path → raw_sha256` canonical object。

Fidelity index v1 exact top keys = `schema_version,translated_capabilities,coverage_reports,tranches`。
13 个 translated capability 必须被 3–4 个 tranche 恰好分区，无遗漏/重叠。每个 tranche exact keys：

```text
tranche_id, capability_ids, candidate_commit_sha,
manifest_set_sha256, source_set_sha256, artifact_set_sha256,
translation_set_sha256, workflow_set_sha256, preface_sha256,
renderer_set_sha256, coverage_set_sha256, approval_binding
```

`approval_binding` exact keys：

```text
record_system, immutable_record_id, reviewer_identity, verdict,
reviewed_candidate_commit_sha, reviewed_source_set_sha256,
reviewed_artifact_set_sha256, recorded_at
```

`verdict` 只允许 `approved | rejected`。PR-C0 绑定已存在的 candidate commit 与 exact set digests；
PR-C1 只需复现相同 digests，不要求 record 绑定未来 PR-C1 HEAD。机器验证 closure/binding，Owner 打开
外部 immutable record 核验 reviewer/verdict；作者不得自签。

#### 2.8.6 Runtime probe schemas

具名 producer：`scripts/sdd/run_codex_carrier_probe.py`。它产生两份互不聚合的 JSON：

**`deterministic-gate-v1`** exact top keys：

```text
schema_version, probe_kind, run_id, started_at, completed_at,
repo_head, codex_build, cases, verdict
```

case exact keys：

```text
case_id, capability_id, surface, fixture_id, fixture_sha256,
config_sha256, tool_version, expected_sha256, actual_sha256,
status, evidence_sha256, reason_code
```

- `surface` = `skill | hook | rule | config`。
- `status` = `PASS | FAIL | BLOCKED_PREREQUISITE | ERROR`。
- `verdict` = `PASS` only if every required case is PASS；其余按优先级
  `ERROR > FAIL > BLOCKED_PREREQUISITE`。
- exact 18 inventory、project path、collision、description budget、artifact digest、fresh-process discovery、
  config/trust route 与 hook/rule canary 都是 deterministic case。
- Codex 无可复验 inspection interface 时必须 `BLOCKED_PREREQUISITE`，禁止用模型回答冒充 PASS。

**`model-telemetry-v1`** exact top keys：

```text
schema_version, probe_kind, run_id, started_at, completed_at,
repo_head, codex_build, model_id, sampling_config,
prompt_fixture_sha256, repetitions, observations, warnings
```

observation exact keys =
`capability_id,prompt_id,run_index,observed_class,warning_codes`；
`repetitions` 固定 3。不得记录 transcript、Secrets、chain-of-thought。任意 telemetry 结果都不能改变
deterministic verdict。

`sampling_config` 是 closed object，exact keys =
`reasoning_effort,temperature,seed,cli_args_sha256,project_config_sha256`；runtime 未公开可固定的
`temperature`/`seed` 必须使用 JSON `null`，不得猜测默认值。`warnings` 是按 warning code 排序、去重的
string array。`observations` 按 `capability_id,prompt_id,run_index` 排序；`run_index` 只能为 1–3 且每个
`capability_id,prompt_id` 恰有三行。Prompt corpus 是预提交 fixture set；`prompt_fixture_sha256` 按 §2.7
set-digest wire 计算。

#### 2.8.7 Enforcement, receipt and ready-host schemas

`sdd/adapters/codex-enforcement.yml` 为 schema v1 typed source，closed top keys =
`schema_version,policy_refs,config_binding,hooks,rules,receipt_policy`。hook/rule output 只能从这里与
explicit policy refs 派生。

Release receipt 位于 typed source 声明的 gitignored
`.mj-agent-local/receipts/`，schema v1 exact keys：

```text
schema_version, gate_id, status, head_sha, tree_state,
porcelain_v2_sha256, command_id, route_version,
verifier_module_sha256, verifier_config_sha256,
started_at, completed_at, ttl_seconds
```

固定 `status: EXECUTED_CLEAN`、`tree_state: clean`、`ttl_seconds: 900`。HEAD、clean tree、route/module/
config digest、schema、regular non-reparse path 或 TTL 任一不符即 stale；SKIP/non-clean/error 不生成 receipt。

Tracked ready-host evidence 是
`evidence/ai-context-audit/YYYY-MM-DD_codex-ready-host.md` 内唯一
`codex-ready-host-v1` fenced JSON，exact keys =
`schema_version,run_id,started_at,completed_at,repo_head,codex_build,host_state,local_json_sha256,cases,verdict`。
case exact keys =
`case_id,surface,capability_id,status,evidence_sha256,reason_code`；status enum =
`EXECUTED_CLEAN | EXECUTED_NON_CLEAN | SKIP_NOT_INSTALLED | SKIP_NOT_AUTHENTICATED |
SKIP_NOT_TRUSTED | SKIP_HOOK_NOT_REVIEWED | ERROR`。deterministic required case 全 clean 才
`verdict: PASS`；model telemetry 单列且不参与 verdict。日期从 UTC `started_at` 派生，不覆盖旧证据。

`host_state` 是 closed object，exact keys =
`os,codex_installation,codex_authentication,project_trust,hook_review`；后四项枚举均为
`READY | NOT_READY | UNKNOWN`。`cases` 按 `case_id` 排序且 ID 唯一；`local_json_sha256` 对
gitignored producer JSON 的 raw bytes 求值，tracked Markdown 只保存 digest 与最小 schema，不嵌入 raw
transcript/config/Secrets。

## 3. Scope, ownership, governance, and planned files

### 3.1 In scope

- required 18 的 v2 manifest/registry/translation/carrier/lock/fidelity/probe。
- non-destructive desired-state reconcile；shared `.codex/config.toml` member ownership。
- project Codex hooks/rules、V12/V13 telemetry、blocking enforcement backstop、bounded Stop receipt。
- PR-0b offline test boundary与 PR-0c sanitized biz snapshot/source repair。
- strict serial Epic ledger、ready-host evidence、final lifecycle closure。

### 3.2 Out of scope

- 19 optional capabilities 的 native carrier。
- system prompt、SQL guardrail、qcm catalog body、DB migration、Secrets、prod compose、Docker external image refs。
- managed/admin policy、authenticated Owner proxy、least-privilege subagents、network proxy。
- 全部 18 份从零重写的 tool-neutral prose；本期只对 13 translated outputs 做 deterministic translation fidelity。
- 自动 merge、auto-merge、stacked unmerged stages、后台自动提交 generated artifacts。

### 3.3 Planned ownership by delivery unit

| Unit | Primary owned files/surfaces |
|---|---|
| PR-0a | `plans/[PLAN]_codex_cross_carrier_kernel.md`、ADR-039、`decisions/INDEX.md` |
| PR-0b | offline boundary checker/runner、`tests/conftest.py`、config seam、CI test commands、agent-facing test instructions |
| PR-0c | biz snapshot validator/diff、disabled fetch tombstone、contract tests、biz/runbook/source skill truth-up、`.gitignore` |
| PR-0d | Task-0 freeze/evidence、PR-0c post-merge EVAL result |
| PR-P1a | versioned deterministic/model probe producer + evidence fixtures/results |
| PR-A0 | D-017/kernel/PR-template exact governance anchors |
| PR-A1 | shared loader/Handoff parser、owned-only reconcile、PJ045 narrowing |
| PR-B | dormant manifest/lock v2、workflow registry、translation map/preface、renderer/oracle、fidelity/probe checkers |
| PR-P1b | production-renderer/canary evidence only |
| PR-C0 | fidelity coverage/index/review bindings only |
| PR-C1 | manifest v2 cutover、18 carriers、README、lock v2、V12 warning mount |
| PR-C2 | V12 anchor registration only |
| PR-D1a | typed enforcement、hooks/rules/config member、V13 warning mount |
| PR-D1b | V13 anchor registration only |
| PR-D2 | existing Tests context中的 identical enforcement predicate blocking backstop |
| PR-E | Stop guard、receipt policy、ready-host evidence |
| PR-F | fresh final evidence/private attestation；plan remains active |
| PR-G | merge-SHA ledger snapshot、plan completed、ADR implementation disposition、Epic close |

文件名可因真实布局作窄幅调整，但职责不得合并成一个万能脚本；等价复用必须在 active plan ledger 记录
owner、interface 与 tests。generated outputs 仍禁止手改。

### 3.4 Approval inventory

| Moment | Required approval |
|---|---|
| PR-0a Issue/plan active/ADR-039 active | Issue external write；plan lifecycle；ADR procedural state；ADR-036 D-011/12/14 disposition |
| PR-0b | protected `.claude/**` hunks；kernel-meta `sdd/**`；无 canonical enum unless exact scope新增 |
| PR-0c | protected `.claude/**`；`runtime-skill-content-change` exact hunk；post-merge EVAL |
| PR-A0/A1 | kernel-meta + D-017 `mcp-server-trust-posture-change` adjacent exact objects |
| PR-B | D-017 + `declared-contract-change` for all closed schemas/renderer/registry |
| PR-C0/C1 | D-017/contract + immutable reviewer record verification；C1 cutover |
| PR-C2/D1b | anchor record exact values；不得夹带行为变化 |
| PR-D1a/E | D-017 exact enforcement/Stop inputs与 generated paths；Codex hook hash review |
| PR-D2 | eligibility evidence + 独立 `ci-blocking-gate-toggle` |
| PR-F/G | private no-content attestation；phase/lifecycle closure procedural approval |
| Every unit | protected edit（如有）、commit、push、PR create 分开；merge out of goal |

canonical enum 仍逐 PR 输出完整 10 行 inventory。`policies/** + sdd/**` approval 单列在 AI Self-Check，
不把它伪装成第 11 个 enum。

## 4. Baseline, freeze, and execution ledger

### 4.1 PR-0a pre-change evidence

PR-0a 不运行本地 pytest，因为当前 conftest 会读取 `.env`。仅运行 Git/read-only、文档、V8–V11 与
sync check；GitHub PR CI 继续运行仓库当前 workflow，不在 PR-0a 改其行为。

### 4.2 Task-0 timing

Task-0 只能在 PR-0b 与 PR-0c 已人工合并、PR-0c post-merge EVAL 已有结果后，由 PR-0d 从 fresh
`origin/develop` 建立。它记录：

- tracked path inventory、raw SHA-256、mode 与 owning surface；
- 18 source skill census、当前 manifest/lock/gate状态；
- hard/controlled freeze identity；
- known divergence ledger（每项有 owner、reason、expiry/closure）；
- pre-change V8–V11、doc gates与 full safe offline verification；
- Owner private attestation，只允许 `ATTESTED_CLEAN | ATTESTED_NON_CLEAN | SKIP_PRIVATE`。

`ATTESTED_NON_CLEAN` 或 unattributed frozen diff 立即停止；不得把私有内容、路径或 hash 读入 evidence。

### 4.3 Freeze enforcement

PR-0d merge 后：

- hard-frozen = §1.1 列表；zero diff。
- controlled `AGENTS.md` 只允许 PR-C1 carrier ownership 与 PR-D1a hook/rule cooperative-scope 两个具名 hunk。
- 后续每 PR 比较 `origin/develop` merge-base → HEAD 与 Task-0 identity；任何其他差异
  `STOP_FROZEN_SURFACE_DRIFT`。
- PR-B 至 PR-F 不修改 Claude authoring behavior；PR-G 只改 lifecycle/ledger docs。

### 4.4 Unit ledger carrier

单 Epic 是 live ledger。每个 delivery unit merge 后添加一个不可省略的 Stage-17 comment，内含
`execution-ledger-v1` JSON。PR-G 将 PR-0a..PR-F 的最终 snapshots 落
`evidence/development-agent-v8/execution-ledger.json`；PR-G 自身 Stage 17 只留在 Epic，避免无限 closure PR。

Top exact keys：

```text
schema_version, epic_id, unit_id, branch, base_sha, head_sha,
pr_number, merge_commit_sha, records, result_code
```

18 个 `records` 恰好覆盖 stage 0..17；record exact keys：

```text
stage, name, status, started_at, completed_at, actor,
input_refs, evidence_refs, owner_decision_refs, result_code
```

status enum =
`PENDING | IN_PROGRESS | EXECUTED_CLEAN | EXECUTED_WITH_OWNER_DECISION | BLOCKED | ERROR`。
最多一个 IN_PROGRESS；stage/time 单调；后继不能越过非成功前态。Stage 17 成功且 merge commit 已进入
`origin/develop` 才允许下一 unit Stage 0。

### 4.5 Per-unit 18-stage loop

| Stage | Required record |
|---:|---|
| 0 | Intake/scope/risk |
| 1 | 首单元创建 Epic；后续绑定并更新同一 Epic，不建子 Issue |
| 2 | fresh worktree/typed branch |
| 3 | repo/current-policy/current-CI scan |
| 4 | active plan update或“核对后无需改”证据 |
| 5 | HITL Gate 1 |
| 6 | SPEC/ADR/contract update或“无需改”证据 |
| 7 | HITL Gate 2 |
| 8 | implementation/evidence work |
| 9 | scope drift gate |
| 10 | local verification |
| 11 | AI self-review |
| 12 | commit（独立 approval） |
| 13 | push（独立 approval；Gitee then GitHub） |
| 14 | PR create（独立 approval；explicit base） |
| 15 | CI/review remediation |
| 16 | merge gate；goal 终止于 `AWAITING_HUMAN_MERGE` |
| 17 | 人工 merge 后 post-merge/EVAL/ledger；完成后下一 unit 才 eligible |

## 5. Strict serial delivery graph

```text
PR-0a → PR-0b → PR-0c → PR-0d → PR-P1a → PR-A0 → PR-A1 → PR-B
→ PR-P1b → PR-C0 → PR-C1 → PR-C2 → PR-D1a → PR-D1b
→ OBSERVATION → PR-D2 → PR-E → PR-F → PR-G
```

### 5.1 Delivery ledger

| # | Unit / branch pattern | Entry condition | Unique delivery | Merge condition |
|---:|---|---|---|---|
| 1 | PR-0a `documentation/499-codex-cross-carrier-kernel-v8` | Epic #499 exact create content Owner-approved and Issue created | active v8 plan、active accepted ADR-039、INDEX、ledger | doc/governance gates green |
| 2 | PR-0b `bugfix/499-offline-test-boundary` | PR-0a merged | safe direct pytest + hardened Agent/CI runner | boundary tests + offline suite green |
| 3 | PR-0c `bugfix/499-biz-snapshot-boundary` | PR-0b merged | sanitized snapshot-only biz route + source truth-up | fixture-only contracts + protected approvals |
| 4 | PR-0d `documentation/499-task0-baseline` | PR-0c merged + EVAL result | Task-0 freeze/baseline | zero unattributed drift |
| 5 | PR-P1a `documentation/499-runtime-feasibility` | PR-0d merged | deterministic feasibility + model telemetry | deterministic `PASS_CANDIDATE` |
| 6 | PR-A0 `maintain/499-governance-anchor` | P1a merged | D-017/kernel exact anchors | governance checks green |
| 7 | PR-A1 `bugfix/499-non-destructive-reconcile` | A0 merged | shared loader + owned-only reconcile | destructive-neighbor negatives green |
| 8 | PR-B `feature/499-dormant-v2-engine` | A1 merged | dormant v2 engine, real tree stays v1 | v1/v2 differential + zero real-tree diff |
| 9 | PR-P1b `documentation/499-production-render-evidence` | B merged | exact production renderer/canary evidence | deterministic `PASS` |
| 10 | PR-C0 `documentation/499-fidelity-attestation` | P1b merged | coverage/review/digest binding | all 13 approved, exact partition |
| 11 | PR-C1 `feature/499-carrier-cutover` | C0 merged | atomic v2 + 18 carriers + V12 warning mount | all blocking checks green; V12 recorded |
| 12 | PR-C2 `maintain/499-v12-anchor` | C1 merged + first real CI known | V12 registration only | anchor reproducible; zero behavior diff |
| 13 | PR-D1a `feature/499-codex-enforcement` | C2 merged | hooks/rules + V13 warning mount | deterministic enforcement canaries |
| 14 | PR-D1b `maintain/499-v13-anchor` | D1a merged + first real CI known | V13 registration only | anchor reproducible; zero behavior diff |
| — | OBSERVATION | D1b merged | ≥14 days AND ≥20 consecutive clean | no active implementation goal |
| 15 | PR-D2 `maintain/499-enforcement-blocking` | eligible + Owner toggle | identical predicate in blocking Tests | full CI green |
| 16 | PR-E `feature/499-bounded-stop-guard` | D2 merged | receipt/Stop/ready-host | deterministic ready-host PASS |
| 17 | PR-F `documentation/499-final-evidence` | E merged | fresh full matrix + private attestation | all claims evidence-bound; plan active |
| 18 | PR-G `documentation/499-lifecycle-closure` | F merged | merge SHA/ledger/plan+ADR closure/Epic close | closure gates green; human merge |

#### 5.1.1 Per-unit AC / evidence / approval / rollback closure

§5.1 同一 unit 行给出 branch、entry condition、unique delivery 与 merge condition；下表补齐每个
delivery unit 的 AC、evidence、approval 与 rollback/repair。两表按 `Unit` 一一 join 后构成完整
per-unit contract。除下列专属 approval 外，每个 unit 还必须分别取得 commit、push、PR-create approval；
merge 始终只由人类执行。

| Unit | AC | Required evidence | Required approval | Rollback / repair |
|---|---|---|---|---|
| PR-0a | AC-01, AC-02 | Epic #499、fresh SHA/census、plan/ADR/INDEX diff、doc/governance gates、PR-0a scope/frozen-path diff（不是 PR-0d Task-0 freeze） | Issue-create；plan/ADR lifecycle + ADR-036 disposition procedural approval | 新 documentation repair PR；不擦除 decision history |
| PR-0b | AC-07 | standalone boundary RED→GREEN、runner contract、targeted + full offline suite | exact protected/source + kernel-meta hunks | forward repair only；不得恢复 dotenv/external route |
| PR-0c | AC-08 | synthetic snapshot contracts、source truth-up diff、post-merge EVAL handoff | exact protected hunk + `runtime-skill-content-change` | forward repair only；不得恢复 direct DB route |
| PR-0d | AC-02, AC-13 | PR-0c EVAL result、Task-0 identity、freeze/divergence ledger、private no-content attestation | evidence/freeze acceptance + private attestation | 新 evidence repair PR；保留历史 baseline |
| PR-P1a | AC-09 | versioned producer、deterministic verdict、每 capability 3× implicit telemetry | evidence scope acceptance | 新 evidence correction PR；不得把 telemetry 升格为 verdict |
| PR-A0 | AC-02, AC-06 | D-017/kernel exact anchor diff、governance gates | kernel-meta + protected-adjacent exact objects | 在 A1 前 revert；有依赖后用 forward repair |
| PR-A1 | AC-05, AC-06 | loader/parser tests、owned-only reconcile negative matrix | kernel-meta / D-017 reconcile ownership | 先 disable deletion，再 repair checker/loader |
| PR-B | AC-03–AC-06, AC-10 | v1/v2 differential、schema/path/owner/adopt/fidelity/probe tests、real-tree zero diff | `declared-contract-change` + D-017 exact schemas | C1 前可 revert B；真实树保持 v1 |
| PR-P1b | AC-09, AC-10 | production renderer exact-byte/canary result = `PASS` | immutable candidate/evidence acceptance | evidence correction PR；不得改 production renderer |
| PR-C0 | AC-10 | exact 13-way partition、coverage report、candidate/source digests、independent review binding | immutable reviewer approvals；author 不自签 | C1 前补/重做 review binding |
| PR-C1 | AC-03, AC-04, AC-10, AC-11 | complete 18-carrier matrix、V8–V12、render/lock/fidelity closure | D-017/contract + cutover approval | 以 verified v2 lock 作只读 owner ledger 的有界 forward repair |
| PR-C2 | AC-11 | first real V12 CI、mount SHA/time、actual command/path、epoch/self-exclusion | exact anchor-value approval | anchor-only correction PR；零 behavior diff |
| PR-D1a | AC-11, AC-12 | typed enforcement、hook/rule/config canaries、V13 warning execution | D-017 exact enforcement inputs/outputs | 先 disable typed source/mount，再 sync convergence |
| PR-D1b | AC-11 | first real V13 CI、actual future-blocking predicate、epoch/self-exclusion | exact anchor-value approval | anchor-only correction PR；零 behavior diff |
| PR-D2 | AC-11 | ≥14 days + ≥20 clean、zero waiver/open warning、predicate byte equality | independent `ci-blocking-gate-toggle` | independent Owner toggle 回 warning；保留 predicate |
| PR-E | AC-12 | receipt/Stop no-read spies、clean-head binding、ready-host deterministic PASS | D-017 exact Stop/receipt inputs + generated paths | disable typed Stop route，sync remove owned output |
| PR-F | AC-13 | fresh full matrix、freeze closure、second private no-content attestation | final evidence/claim + private attestation | evidence correction PR；plan 保持 active |
| PR-G | AC-01, AC-02, AC-14 | PR-F merge SHA、execution-ledger snapshot、exact lifecycle diff、Epic state check | plan/ADR lifecycle + Epic closure procedural approval | correction PR；不改写历史 ledger/evidence |

### 5.2 PR-0b — safe direct pytest and hardened Agent/CI runner

This PR resolves the apparent conflict by separating **safe default behavior** from **automation hardening**:

1. `tests/conftest.py` removes every dotenv/repo/home discovery and sets offline test mode before any
   `mj_agent` import. Direct `uv run pytest ...` remains supported for humans/IDE and is always offline.
2. Credential presence alone never enables live/external tests. Biz live legs are permanently unavailable to pytest.
   Non-biz external testing requires a future separate Owner-approved profile; absent it, structured
   `SKIP_POLICY_EXTERNAL_DEPENDENCY`.
3. `src/mj_agent/config.py` gains one construction seam: offline test construction passes
   `_env_file=None, _secrets_dir=None` before settings sources are created; production entry behavior remains unchanged.
4. Add `scripts/sdd/check_test_offline_boundary.py` as the only pre-change red signal. It performs static/AST checks and
   never imports pytest/application or reads environment values.
5. Add `scripts/sdd/run_offline_pytest.py` for Agent/CI only. It builds a sanitized child environment from a named
   non-secret OS allowlist, temp HOME/profile roots, `PYTHONNOUSERSITE=1` and
   `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; it loads only project-required, lock-verified plugins and restricts targets to
   tracked non-reparse `tests/**`.
6. CI default/BDD/contract pytest entries and agent-facing automation instructions use the runner. Human README/IDE
   instructions may retain direct pytest because that path is now safe; the checker must not flag those as defects.
7. Parent `PYTEST_ADDOPTS/PYTEST_PLUGINS/PYTHONPATH` and credential/token/URL/password/key variables do not enter
   the child. Runner/checker logs never print environment values.
8. Safety hunk lands before the first pytest execution. RED = standalone checker on old tree；GREEN = checker +
   targeted boundary tests + complete offline suite.

PR-0b does not touch biz snapshot/fetch/source-skill semantics; those belong exclusively to PR-0c.

### 5.3 PR-0c — sanitized biz snapshot and source truth-up

- `fetch_biz_schema.py` becomes a fail-closed tombstone: no dotenv/DB/network imports; exit 2 with sanctioned-route guidance.
- `diff_biz_schema.py` reads only closed schema v1 snapshots under gitignored
  `.mj-agent-local/biz-schema-snapshots/`; explicit paths must remain within the root, regular/non-reparse and size-bounded.
- Snapshot exact required fields = `schema_version,captured_at,provenance,sanitized,payload`；
  `provenance: sanctioned-agent-tool-chain`、`sanitized: true`；unknown/sensitive/tag/alias rejected。
- Max age = 7 days with injectable clock. No snapshot and stale snapshot emit
  `SKIP_NO_SNAPSHOT` / `SKIP_STALE_SNAPSHOT`, exit 0, and never pretend PASS/current DB freshness.
- Contract tests consume synthetic snapshot fixtures only; no introspection imports、credential gate、DB/network fallback。
- Agent-facing repo-scan/verify/self-review/review/biz-sync paths remove live/direct guidance and preserve explicit SKIP.
- Runtime skill exact hunk requires `runtime-skill-content-change` approval and PR-0c post-merge EVAL; PR-0d records result.
- Provenance field is Owner attestation, not cryptographic proof that capture used the sanctioned chain.

### 5.4 PR-0d and PR-P1a

PR-0d performs §4 Task-0 and freezes current post-repair truth. PR-P1a then runs the versioned producer from §2.8.6
against all 18 source candidates in root/nested/worktree and isolated/actual-user-layer layouts.

Hard verdict covers inventory/path/collision/budget/digest/fresh discovery route. Three implicit positive/near-negative runs
per capability are telemetry only. Any deterministic `FAIL/ERROR/BLOCKED_PREREQUISITE` stops before A0.

### 5.5 PR-A0 / PR-A1

- A0 is governance only and must merge first. It amends D-017 exact anchors for shared loader/reconcile ownership and
  PR-B/D/E sources; no implementation.
- A1 extracts shared loader/Handoff parser, changes reconcile from “directory allowlist” to verified lock-owned paths, and
  narrows PJ045 so valid future hooks/rules/unowned neighbors are preserved.
- Deletion requires verified old/current lock owner + safe path + absence from desired set. Unknown/malformed/mixed lock,
  owner ambiguity or path hazard means zero delete/write.
- Negative fixtures include unrelated `.codex/hooks.json`, rules dir, user file, casefold/reparse collision and empty MCP set.

### 5.6 PR-B / PR-P1b

PR-B adds all v2 sources/renderers/checkers dormant while real manifest/lock/artifacts remain byte-identical v1. Both
manifest versions are accepted; unknown remains exit 2. Tests cover every closed schema, v1↔v2 compatibility, partial
apply retry, shared config member isolation, lexicon/site/edge closure, adopt CAS and negative path/owner cases.

PR-P1b uses exactly the production renderer/module/version against the frozen PR-B merge commit, runs deterministic and
canary legs, and writes evidence only. `PASS_CANDIDATE` from P1a is insufficient; only P1b `PASS` allows C0.

### 5.7 PR-C0 / PR-C1 / PR-C2

- C0 creates all coverage reports, exact 13-way partition and immutable review bindings. Candidate commit and set digests
  exist before review; author cannot self-sign.
- C1 atomically writes manifest v2, 18 `projection: project` carriers（5 byte-copy + 13 translated）、
  `codex.support_mode: native`, README, lock v2 and V12 warning execution. It must reproduce C0 artifact/source digests.
- C1 performs two approved commits only if necessary for reviewability, but no step may require an unmerged commit from the
  same PR. Final tree must be internally complete.
- C2 changes only registration/evidence: gate id, real mount commit/time, run-command/path, applicability, threshold/epoch,
  self-exclusion and clean predicate. If behavior/config changes are needed, stop and open repair before C2.

### 5.8 V12

V12 = **Cross-Carrier Structure**. It reports manifest↔registry↔artifact↔lock↔fidelity impact using the same underlying
blocking checkers, but remains warning telemetry in this plan. A future V12 blocking flip is a separate plan/toggle.

| Registration field | V12 value |
|---|---|
| Gate ID / name | `V12 / Cross-Carrier Structure`。**§4.1.1 要求的一一对应三元组**：`sdd/gates.md` §2 行名 `V12 Cross-Carrier-Structure` ↔ `ci.yml` step 名 `V12 cross-carrier structure (WARNING per plan §5.8; anchor PENDING_PR_C1_FIRST_CI)`。⚠ step 名里的 `PENDING_…` 是**首挂期的历史标识串，非活体断言** —— PR-C2 刻意不改 ci.yml 以守住「零 behavior diff」，真值以本表为准（残余 = F16）|
| Exact execution | `uv run python scripts/sdd/check_cross_carrier.py --status-json .mj-agent-local/status/cross-carrier.json` |
| Applicability | every PR; no path filter（`ci` job 无 `paths:` 过滤器，随每个 PR 必跑 → 适用 `policies/ci-gates.md` §4.1.3 head-SHA 去重口径，**不**适用 §4.1.4 三态口径）。⚠ **`develop` 上的 merge commit 不触发任何 run** —— `ci.yml` 的 push 过滤器只含 5 个临时分支类型（不含 `develop`），`pull_request` 只对 base 为 main 或 develop 的 PR 触发；故 merged 单元的「首次真实 CI」只能取其 **PR head SHA** 上的 run（实测 `d810746` 的 `actions/runs` `total_count = 0`）|
| Observation anchor | **CI 首挂锚 `2fbf700` 2026-08-27 14:11:11 +0900 #499**（判据 = §4.1.2 run-命令 pickaxe，单一命中；为非 merge 实现 commit）。**Epoch 起点 = 该 commit 上的首次真实 CI** —— run `33041866036`（event=push，`run_started_at 2026-08-27T05:14:15Z`），其 V12 step（job `98417034436`）`05:14:57Z`→`05:14:58Z`、`conclusion=success`、输出 `EXECUTED_CLEAN`（7/7 join）。同一 head SHA 的 run `33041907780`（event=pull_request，`05:15:04Z`；job `98417167238`，step `05:15:42Z`）输出**逐字节相同**，按去重口径与前者合计 **1 次观测**。原始实测值 → `evidence/development-agent-v8/c2-v12-anchor-evidence.md` |
| Eligibility | **两腿 AND（合取）**：日历腿 = anchor + ≥14 natural days **AND** 计数腿 = ≥20 consecutive head-SHA-deduplicated `EXECUTED_CLEAN` runs |
| Streak semantics | `SKIP` is neutral; warning/error/non-clean resets the epoch。执行体口径（§4.1.3「执行体输出是 SoT」）：`EXECUTED_CLEAN` 计 1 · `SKIP_MANIFEST_V1` 中性 · `EXECUTED_WITH_FINDINGS`(rc 1) 与 `ERROR_UNREADABLE`(rc 2) 重置。⚠ **run 级 conclusion 不可用作判据** —— V12 step 带 `continue-on-error: true`，且 `EXECUTED_CLEAN` 与 `SKIP_MANIFEST_V1` **同为 rc 0**，二者只能由 stdout 的 result_code 区分。⚠ **head-SHA 去重是必需而非可选**：`ci.yml` 同时挂 `pull_request` 与 `push[feature/bugfix/documentation/maintain/hotfix]`，故**分支名命中该 5 类前缀**的 PR 每个 head SHA 产生 **2 次** `ci` run；不去重会把 streak **高估近一倍**（静默失效，无 gate 可查）。⚠ **成对是「可能」不是「保证」**：`dependabot/*` 等不在 push 过滤器内的分支同样能对 develop 开 PR，只产生 **1 次**（pull_request）—— 故计数一律按 head SHA 归并，**不得**用「run 数 ÷ 2」反推观测数 |
| Self-exclusions | PR-C1 mount, PR-C2 anchor and any future blocking-flip PR。**§4.1.3 末条（注册时须明写）**：翻转 PR **自身分支产生的 run 不计入其自身的资格证据**，计数须锚在**翻转分支之前的那个 commit** |
| v8 disposition | warning-only; no blocking flip in this plan |

**注册载体声明（PR-C2 落）**：本表即 V12 的 `policies/ci-gates.md` §4.1.1 **明文观察期注册**（该节要求
「构成要件 = 事先在 `plans/` 注册」；本 plan 创建于 2026-08-12，早于 2026-08-27 的首挂，满足「事先」）。
`policies/ci-gates.md` 自述为「规则 + 指针层，**不复制姿态真值**」，故**不**在该文件登记逐 gate 值；
`sdd/gates.md` §2 承载逐 gate 真值行并回指本表。
⚠ **耐久性缺口（明写，不掩饰）**：ADR-039 第 11 条与本 plan §5.12 规定 PR-G 在 PR-F 合并后把本 plan 翻
`active → completed`，而 V12 的日历腿最早 2026-09-10 才到期 —— 届时注册表将位于**已闭合的项目记录**中。
这正是 `policies/ci-gates.md` §4.1.2/§4.1.3 因 issue #403 从 `plans/[PLAN]_dual-agent-compat.md` 逐字提升为
政策原生条文的同一失效模式。**未来的 blocking-flip 单元必须先把本表 re-home 到它自己的 M-FU 注册工件**
（或提升为政策原生条文），不得直接引用一个 `completed` plan 作为活体注册表。
该义务落在一个 PR-G 会关闭的 plan 里，本身就是它所描述的失效模式，故**另立 follow-up `F17` 承载**
（见 `evidence/development-agent-v8/c2-v12-anchor-evidence.md` §8.3）；V13 在 §5.9 同构，届时一并 re-home。

### 5.9 PR-D1a / PR-D1b

D1a renders project `.codex/hooks.json`、`.codex/rules/mj-agent.rules` and optional config binding from typed
enforcement source. Hook deny canary must block before side effect; rule fixtures use `codex execpolicy check` and choose
the strictest decision. Raw transcript/assistant message/Secrets/private state are never inputs.

V13 = **Codex Enforcement Drift**. D1a mounts warning telemetry. D1b registers the real first-mount commit/time and the
exact future blocking command; D1b contains no behavior change.

| Registration field | V13 value |
|---|---|
| Gate ID / name | `V13 / Codex Enforcement Drift` |
| Exact execution | `uv run python scripts/sdd/agents_sync.py --check --surface enforcement` |
| Applicability | every PR; no path filter |
| Observation anchor | PR-D1b records the first real CI run from merged PR-D1a; until then `PENDING_PR_D1A_FIRST_CI` |
| Eligibility | anchor + ≥14 natural days + ≥20 consecutive head-SHA-deduplicated `EXECUTED_CLEAN` runs |
| Streak semantics | `SKIP` is neutral; warning/error/non-clean resets the epoch |
| Self-exclusions | PR-D1a mount, PR-D1b anchor and PR-D2 toggle |
| blocking route | V13 remains warning; PR-D2 mounts the exact same predicate/command in the existing blocking Tests path |

### 5.10 Observation and PR-D2

Eligibility is conjunctive:

- calendar leg: mount anchor + at least 14 natural days;
- count leg: at least 20 consecutive, head-SHA-deduplicated `EXECUTED_CLEAN` runs after D1b merge;
- zero waiver and zero open warning;
- mount, anchor and D2 self-generated runs excluded;
- SKIP is neutral; non-clean/error resets the epoch;
- predicate/schema/route/self-trigger semantics change starts a new epoch.

V13 telemetry must execute exactly the command later inserted into blocking Tests:
`uv run python scripts/sdd/agents_sync.py --check --surface enforcement`. D2 only changes posture/carrier of that
identical predicate after independent `ci-blocking-gate-toggle` approval. V13 itself remains warning.

### 5.11 PR-E

Implements §2.8.7 receipt and bounded Stop:

- release receipt only from same clean committed HEAD after full verifier `EXECUTED_CLEAN`;
- dirty/staged development receives diagnostics but no release receipt;
- Stop reads allowlisted event controls such as `stop_hook_active`, public repo metadata and exact receipt only;
- one continuation per completion cycle; no loops;
- no raw event、last assistant message、transcript、ignored neighbor、Secrets、DB/network access;
- ready-host hard cases must PASS; model-selection telemetry remains non-blocking.

### 5.12 PR-F / PR-G

PR-F uses a fresh worktree from current develop, reruns every applicable blocking/warning/ready-host leg, performs the
second private no-content attestation, proves frozen-surface/drift closure, and limits claims to §1.3. Plan remains active.

After F is human-merged, PR-G records F merge SHA, snapshots prior ledgers, updates plan
`active → completed` and ADR implementation disposition under procedural approval, and closes the Epic. PR-G goal also
stops before human merge; its own Stage 17 stays in Epic.

## 6. Verification matrix

### 6.1 Every PR preflight

- fetch/compare explicit `origin/develop`；local clean；previous PR `MERGED` and merge commit ancestor of remote develop。
- derive current required workflows/commands from workflow files；required-check empty set is not treated as success。
- run frontmatter、wikilink strict、kernel-section refs、AI context audit and applicable stale/cross-repo checks。
- V8/V9 use current `--fail-on warning`；V10 skills、V11 mcp and `all` remain clean。
- after a commit exists: `check_commit_messages.py origin/develop HEAD`。
- before/after verification: `git status --short` and frozen diff.
- warning gates are reported separately; default `check_no_cross_repo_refs.py` is informational unless strict env is
  explicitly approved/used.

### 6.2 Stage-dependent commands

| From | Additional verification |
|---|---|
| PR-0a | no local pytest；doc/governance + V8–V11 only |
| PR-0b | standalone boundary checker first；then targeted boundary tests + complete hardened offline suite |
| PR-0c | fixture-only biz unit/contract tests；no DB/network client |
| PR-0d | full safe offline suite + freeze identity |
| PR-P1a | deterministic probe + telemetry schema checks |
| PR-A1 | loader/reconcile negative matrix |
| PR-B | v1/v2 differential, schema/path/owner/adopt/fidelity/probe tests；real-tree zero diff |
| PR-P1b | production renderer exact-byte/canary |
| PR-C0 | independent fidelity inventory and approval binding |
| PR-C1 | V8–V12 + all real-tree render/drift checks |
| PR-D1a | hook/rule/config canaries + V13 warning |
| PR-D2 | identical enforcement predicate under blocking Tests |
| PR-E/F | receipt/Stop no-read spies + ready-host deterministic PASS |

No command is run before its producer/CLI lands. In particular enforcement/V12/V13 commands do not appear in early PRs.

### 6.3 Failure handling

- Local/CI code failure: remain on same branch/PR, root-cause/TDD, rerun targeted then full matrix; new commit/push needs new approval.
- Network/CI transient: same operation at most 3 retries, then `WAIT_EXTERNAL`。
- Gitee success/GitHub fail or SHA mismatch: no PR create；repair same branch，confirm both SHA equal。
- develop drift/conflict: merge `origin/develop`, never rebase；rerun full verification/freeze。
- protected/scope expansion: stop, preview exact hunk, obtain new approval；old approval does not widen。
- same blocker for 3 consecutive goal turns with no new evidence: report blocked per goal protocol；no next stage。

## 7. Acceptance criteria

### 7.1 Program-level AC

- AC-01 single Epic exists and all 18 units reference it；only PR-G closes it。
- AC-02 at most one active delivery unit；each next unit proves previous Stage-17 merge ancestry。
- AC-03 all 18 required rows end `required=true,projection=project,codex_carrier!=none,codex.support_mode=native`。
- AC-04 exact target composition dynamically derives 5 byte-copy + 13 translated at cutover; validators do not hardcode counts。
- AC-05 generated expected/reconcile/lock sets have one owner per path and preserve every unowned neighbor。
- AC-06 unknown/malformed/mixed schemas and unsafe paths fail before managed writes/deletes。
- AC-07 direct pytest never loads dotenv/Secrets or enables external legs；Agent/CI runner sanitizes parent state。
- AC-08 biz tests/scripts contain no direct DB/introspection/credential route；snapshot validation is closed/offline。
- AC-09 deterministic probe PASS；model telemetry cannot alter verdict。
- AC-10 fidelity inventory exact closure and immutable approved binding cover all 13 translated carriers。
- AC-11 V12/V13 records name actual command/path；D2 predicate equals observed predicate byte-for-byte。
- AC-12 Stop receipt is clean-head/TTL/config-bound and no-read spies cover forbidden inputs。
- AC-13 final evidence distinguishes PASS/SKIP/NON_CLEAN/ERROR and makes no unsupported semantic/identity/managed claims。
- AC-14 PR-G alone performs lifecycle closure after F merge。

### 7.2 Per-PR merge checklist

Each PR body maps its unit to AC IDs, evidence paths, exact approval records, test/CI output and rollback prerequisite.
Developer-ready means:

- open PR, explicit base develop, no conflict, GitHub mergeable;
- Gitee and GitHub branch heads equal approved commit SHA;
- all applicable required workflows complete/green;
- no developer-actionable Fail/Pending；human review may be the only Pending；
- full AI Self-Check: Codex contribution, HITL hit, BDD/TDD impact, subagents；
- complete canonical 10-enum inventory plus separate kernel-meta approval；
- output `AWAITING_HUMAN_MERGE` and stop。

## 8. Rollback and forward repair

| Surface | Recovery |
|---|---|
| PR-0a docs/ADR | new documentation repair PR；do not erase decision history |
| PR-0b/0c safety | forward repair only；never restore dotenv/direct DB route |
| A1 reconcile | disable deletion first，retain owned ledger，repair checker/loader |
| B dormant engine | revert B before cutover，real tree remains v1 |
| C1 cutover | use verified v2 lock as read-only ownership ledger，render v1 desired set，remove only 13 old-owned translated outputs |
| D1 enforcement | disable typed source/mount first，sync convergence，then posture change if needed |
| D2 blocking | independent Owner toggle to warning after evidence；do not delete predicate |
| E Stop | disable typed Stop route，sync remove owned output，retain receipts/evidence |
| F/G docs | correction PR；never rewrite historical evidence/immutable review record |

Any rollback/revert is its own issue-linked PR, uses merge-not-rebase, obtains the same protected/commit/push/PR approvals,
and stops before human merge.

## 9. Future separate plans

以下项目不能借本计划的 warning streak 或 Owner approval：

1. 18 份从零重写的 tool-neutral prose contracts；本期 13 translated 的 deterministic fidelity 已在 scope 内关闭。
2. `codex.posture` permission-profile schema、emitter keys、XOR/precedence 与版本兼容（本计划只做
   explicit-route 所需的最小输入模型扩展）。
3. managed configuration、Admin roles、requirements、ProgramData/ACL、Windows/WSL2 支持矩阵。
4. authenticated Owner proxy。
5. least-privilege subagents。
6. network proxy 与 managed network。
7. V12 blocking flip 与 V13 telemetry 自身的 blocking flip；本期只在 D2 把 identical enforcement predicate 加入既有 blocking Tests。
   ready-host observation 的 gate 化以 CI 具备 ready host 为前提，另立计划。

未来 V12 flip 的 branch 必须由当时已关联 issue ID 按现行 maintain 命名规则派生，commit 使用
`infra(ci): enable V12 blocking after qualification`，保持既有 blocking flip 的 git auditability。
工期不足时可以推迟 flip，不能删除结构 gate 本身。

---

## 10. Official and repository references

官方 Codex 文档：

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Hooks](https://learn.chatgpt.com/docs/hooks)
- [Rules](https://learn.chatgpt.com/docs/agent-configuration/rules)
- [Permissions](https://learn.chatgpt.com/docs/permissions)
- [Managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration)
- [Codex CLI commands / doctor](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-doctor)

仓库权威面：

```text
AGENTS.md
policies/ai-agent.md
policies/ci-gates.md
sdd/lifecycle.md
sdd/workflows/execution-loop.md
sdd/gates.md
sdd/development-agent.yml
sdd/adapters/development-agent.md
decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection.md
scripts/sdd/agents_sync.py
scripts/sdd/check_development_agent.py
scripts/sdd/check_agents_projection.py
scripts/check_ai_context_audit.py
scripts/diff_biz_schema.py
scripts/fetch_biz_schema.py
.claude/scripts/guard-git-workflow.ps1
.github/workflows/ci.yml
tests/AGENTS.md
tests/unit/test_agents_sync.py
tests/unit/test_guard_git_workflow_hook.py
```

官方文档说明：Codex 从 cwd 到 repo root 扫描 `.agents/skills`；显式调用使用 `$skill`/skill mention；
初始 skill list 有 2% context（未知时 8,000 字符）预算并可能缩短/遗漏 description；project-local
config/hooks/rules 只在 trusted project layer 中加载，且非 managed hooks 按当前 hash review/trust。因此本
计划保留 18 项同时加载的 P1/ready-host evidence，不能用文档存在替代实机验证。产品文档与实施版本行为不
一致时，以 P1 记录的精确版本结果决定路线是否可执行，并把差异登记为 evidence，而不是修改安全边界迎合实现。

---

## 11. Execution handoff

### 11.1 Unit state machine

```text
PREVIOUS_STAGE17_CONFIRMED
→ PREFLIGHT
→ WAIT_EDIT_APPROVAL (if applicable)
→ WORKTREE_READY
→ IMPLEMENTING
→ VERIFYING
→ SELF_REVIEWED
→ WAIT_COMMIT_APPROVAL
→ COMMITTED
→ WAIT_PUSH_APPROVAL
→ PUSHED_BOTH
→ WAIT_PR_CREATE_APPROVAL
→ PR_OPEN
→ CI_REMEDIATION
→ AWAITING_HUMAN_MERGE
→ [human merge only]
→ STAGE17_RECORDED
→ next unit eligible
```

### 11.2 Entry gate

Except PR-0a, all must prove:

1. previous PR state = MERGED，`mergedAt`/`mergeCommit.oid` present；
2. merge commit is ancestor of current `origin/develop`；
3. local develop/fresh base equals latest explicit remote SHA and is clean；
4. previous `execution-ledger-v1` Stage 17 is successful；
5. no other active goal/worktree/implementation PR for this Epic；
6. branch name/type matches §5 and is created by `git worktree add`；
7. root and nested AGENTS read；exact scope/HITL/verification declared。

### 11.3 Exit gate

`AWAITING_HUMAN_MERGE` requires all §7.2 conditions. Output exact:

- Epic and PR URL/number；
- base/head branch and approved head SHA；
- Gitee/GitHub remote SHA；
- local tests and CI workflows with conclusions；
- warning telemetry separately；
- approvals/HITL/evidence/freeze summary；
- `NEXT_STAGE_BLOCKED_UNTIL_HUMAN_MERGE`。

Then stop. Never call merge, enable auto-merge, create next branch/worktree, or perform cleanup.

### 11.4 PR-0a current execution

PR-0a must:

1. use the exact-approved single Epic [#499](https://github.com/MJ-AgentLab/mj-agent/issues/499)；
2. preserve the external v8 file as immutable input evidence and record its SHA-256 in this repository port；
3. use `documentation/499-codex-cross-carrier-kernel-v8` created from
   `origin/develop@c549880f6d1e5342c6402d9fb6d84639090020b5`；
4. first add draft plan、draft/proposed ADR-039 and proposed/draft INDEX row；
5. preview the exact `draft → active` / `proposed → accepted` diff and ADR-036
   D-011/D-012/D-014 relationship，then land only that exact transition after procedural Owner approval；
6. run §6 PR-0a matrix without local pytest；
7. obtain separate commit、push、PR-create approvals；
8. wait for green CI and stop at `AWAITING_HUMAN_MERGE`。

Current state code = `ACTIVE_ACCEPTED_PR0A_IN_PROGRESS`。该状态在 shared `develop` 上只于 PR-0a 人工 merge 后
生效，也不授权 stage 2 / PR-0b。

---

*Repository port v8.0, 2026-08-13 — fresh re-audit against `origin/develop@c549880f6d1e5342c6402d9fb6d84639090020b5`；external input SHA-256 `ce87a6a928ce539433db678f1158c50f725ab0f14ec8a0a250ef783c21e9a76a`. This revision replaces
the v7 parallel/non-PR execution DAG with a single-Epic, 18-PR serial protocol; closes the previously ambiguous
schema/probe/fidelity/receipt contracts; and preserves human merge authority.*
