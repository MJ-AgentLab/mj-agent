---
type: evidence
summary: >-
  Epic #499 PR-D1a Codex cooperative enforcement carrier —— 从 typed source
  `sdd/adapters/codex-enforcement.yml`（schema v1）渲染 `.codex/hooks.json`
  与 `.codex/rules/mj-agent.rules`，并把 **V13 = Codex Enforcement Drift** 以
  **warning** 姿态挂上 `ci.yml`。Gate 1 四问 + Gate 2 两问 Owner 全取推荐：
  **DIRECT 路线**（不渲染 config binding → `.codex/config.toml` 保持
  `codex-config-mcp`，BLOCKING V11 scope 不动）、**三段式诚实验收**、
  **result_code 只在 `--surface enforcement` 输出**、**AGENTS.md 只落
  change-path + cooperative caveat**。⚠ 本单元用掉 §1.1 的**最后一处** controlled
  额度，落盘后 Task-0 identity 必然重锚。**Stage 11 对抗评审改正了三处会让本单元
  失效的缺陷**：(1) `hooks.json` 顶层键 `_generated` 使**整个文件在 codex 里解析
  失败、零 hook 注册**（`HooksFile` 只收 `description`/`hooks`）；(2) handler 命令
  `python` 在本机**根本不存在**（uv-only）；(3) 两处既存 real-tree 钉线跑
  `--check`（surface=all），把 warning-only 的 V13 **变成事实 blocking**。
  **明确未证明**：本仓不执行 Codex harness，故「harness 在副作用前拒绝」未被证明。
owner: ranzuozhou
created: 2026-08-28
updated: 2026-08-28
state: active
track: agent
---

# Codex Enforcement Carrier — Epic #499 (PR-D1a)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §5.9（PR-D1a/D1b）+ §2.8.7
> （enforcement typed source schema）+ §2.8.4（policy reference inventory）+
> §5.10（observation / PR-D2）。Delivery unit = **PR-D1a**，AC = **AC-11 + AC-12**，
> merge condition = **deterministic enforcement canaries**（§5.1 row 13）。
> approval = **D-017 exact enforcement inputs/outputs**（§5.1.1）+ §3.4 的
> **Codex hook hash review**；rollback = **先 disable typed source/mount，再 sync
> convergence**。

## 0. 入场锚点与 Owner 拍板记录

| 项 | 实测值 |
|---|---|
| 前序单元 PR-C2 | #518 **MERGED**，head `e63f19c825768dc7d355a0768d86098341989185`，merge `70a9db4f3e00746a54bea4d18a285995d18a3f76`，`2026-08-27T10:09:45Z`（ranzuozhou） |
| develop 三方 | local = origin = gitee = `70a9db4f3e00746a54bea4d18a285995d18a3f76` |
| C2 Stage 17 ledger | `#499#issuecomment-5437577003`，body **23817 B**、纯 LF、SHA-256 `279912c40a896b5708ae41dd1fe1f2e70c568cebbd9aa29fb4d652f75aabd378` **逐字节复算吻合**（口径 = API `body` 去尾换行）；`created_at == updated_at` → 从未编辑；18 records 全终态 |
| Task-0 preflight | `CONTROLLED_SURFACE_CHANGED` / **rc 1**，identity `a0124cff7e2ea306abc38043208dfa44afc8a62905da068302204ef29ecff0c4`，hard-frozen **58 零 diff** —— C1 用掉首个授权 hunk 后的**预期授权态** |
| 工作树 EOL | 新 worktree 实测 **55/55 `w/lf`**，零 `w/crlf`；`sync` 未重写任何 carrier |
| 其他 | #499 / #504 均 OPEN；无 open PR；worktree 数 2 → 建分支后 3 |

**Gate 1（四问一次呈清，Owner 全取推荐项）**：

| # | 问题 | Owner 拍板 |
|---|---|---|
| Q1 | 是否渲染 `.codex/config.toml` enforcement binding | **DIRECT 路线**：不渲染 binding，config 保持 `codex-config-mcp`。依据 §5.9 自称 binding 为 "optional"、§2.6 明设逃生口；避免动到 **BLOCKING day-1 的 V11** scope |
| Q2 | 「hook deny canary 在副作用前拦截」如何算达成 | **三段式诚实拆分**：(a) blocking 离线测试证明 **render/reconcile 半边**写入前拒绝；(b) `codex execpolicy check` rule fixtures **本机实跑**；(c) hook **执行腿**如实记 SKIP。AC 措辞**不得**声称 harness 在副作用前拒绝 |
| Q3 | V13 的 clean predicate 词汇 | **只在 `--surface enforcement` 增发 result_code 行**，V10/V11 stdout 逐字节不变 |
| Q4 | AGENTS.md hunk 的内容形态 | **change-path + cooperative caveat 两条 bullet**，一处连续块；不改 heading、不加 trailer、不内联 V13 posture、不写易变派生计数 |

**Gate 2（protected / D-017）**：AGENTS.md hunk **逐字批准**；D-017
`mcp-server-trust-posture-change` 面全部批准。

## 1. 交付面（17 文件，+2739 / −20）

| 文件 | 动作 | 依据 |
|---|---|---|
| `sdd/adapters/codex-enforcement.yml` | **新增** typed source（schema v1，8844 B） | §2.8.7；D-017 (c) PR-A0 具名预登记 |
| `scripts/sdd/_common/enforcement_source.py` | **新增**共享 loader | §2.8.7 fail-closed；D-017 (b)（本 PR 扩列） |
| `scripts/sdd/_common/codex_hook_renderer.py` | **新增** output-class renderer | §2.6；模块名由 PR-B fixture 预钉 |
| `scripts/sdd/_common/codex_rule_renderer.py` | **新增** output-class renderer | 同上 |
| `scripts/sdd/codex_hook_guard.py` | **新增**运行期 PreToolUse guard | §5.9 输入纪律；D-017 (b)（本 PR 扩列） |
| `.codex/hooks.json` | **新增**生成产物（1242 B） | ADR-039 D-011 已具名 |
| `.codex/rules/mj-agent.rules` | **新增**生成产物（1860 B） | 同上 |
| `.agents.lock.json` | 再生（20 → **22** entries） | owner ledger |
| `scripts/sdd/agents_sync.py` | enforcement surface + **surface 路由修正** + result_code | §2.6 / §5.9 |
| `scripts/sdd/check_agents_projection.py` | **PJ045 改为 lock-aware**（诱发性 stale） | 见 §6.2 |
| `.github/workflows/ci.yml` | **V13 warning 挂载** | §5.9 |
| `AGENTS.md` | §1.1 授权的**最后一处** controlled hunk（+13 / −0） | §1.1 / §4.3 |
| `policies/ai-agent.md` | D-017 (b) 扩列四个新模块 | Gate 2 |
| `tests/unit/test_codex_enforcement_d1a.py` | **新增** 46 个测试函数 → 收集 **86** 项 | AC-11 / AC-12 |
| `tests/unit/test_agents_sync.py` | real-tree 钉线**收窄到两个 blocking surface** + docstring | 见 §6.1 |
| `tests/unit/test_v2_engine.py` | 同上 + 以 surface 覆盖完备性断言替代 bare `--check` | 见 §6.1 |

⚠ **`policies/ci-gates.md` 刻意不改**：初稿曾把 §6 的 `V1-V12` 改为 `V1-V13`，
Stage 11 证伪 —— `git log -S "V1-V12" -- policies/ci-gates.md` **只有一个 commit**
（`e63f19c` = PR-C2，**注册单元**），而 **PR-C1（V12 的 mount 单元，与本单元同构）
未碰 `policies/` 任何文件**。该范围表述跟踪的是**进入 `sdd/gates.md` §2 的成员**，
不是 ci.yml 挂载；本单元刻意不加 V13 行（归 D1b），故改成 `V1-V13` 会**断言一个
SoT 尚未承载的 gate ID**。已回退，留给 PR-D1b 与 gates.md 行一并落。

## 2. Typed source → artifact 的 digest 闭合（实测）

```text
sdd/adapters/codex-enforcement.yml   2dc524960b54424c4e97acc631d16f854c5b3c6cfe1895b1da809790acf4bb9e
.codex/hooks.json                    9ec35eda641ab32a885e6840b252f9b8e1feba17457223126e84e5d2c8773cb8
.codex/rules/mj-agent.rules          7bb231e36e042897e2f2e2c3b1ab6dcc9de6e5728b915d66d52faaab7b7d2529
policy_refs inventory (canonical)    a030fa8b26f2f7019c646f1be223e2430f0b503bd771a9d4e10114140fde9a3a
```

两个 entry 的 `inputs` 完全对位 PR-B 在 `tests/unit/test_lock_v2.py` 预钉的 exact key 集：

| key | `.codex/hooks.json` | `.codex/rules/mj-agent.rules` |
|---|---|---|
| `entry_kind` | `codex-hook` | `codex-rule` |
| `owner` | `system:codex-hooks` | `system:codex-rules:.codex/rules/mj-agent.rules` |
| `surface_members` | `["enforcement"]` | `["enforcement"]` |
| `normalization_policy` | `canonical-json-v1` | `generated-utf8-lf-v1` |
| `renderer_module` | `scripts.sdd._common.codex_hook_renderer` | `scripts.sdd._common.codex_rule_renderer` |
| `renderer_version` | `1` | `1` |

**DIRECT 路线自证**：`.codex/config.toml` 的 `entry_kind` 实测仍为 **`codex-config-mcp`**。
lock `entry_kind` 直方图实测 = `{codex-config-mcp: 1, codex-hook: 1, codex-rule: 1,
skill-byte-copy: 5, skill-translated: 13, skills-readme: 1}`（合计 22）。

### 2.1 「AGENTS.md 是 policy_ref ⇒ 编辑即 re-render 触发」的自证

写完 AGENTS.md hunk 后先跑 `--check --surface enforcement`，它**先报 drift 再报 clean**：

```text
# 编辑 AGENTS.md 之后、re-sync 之前
[DRIFT] lock entry out of date for '.codex/hooks.json' (input/output digest closure; ...)
[DRIFT] lock entry out of date for '.codex/rules/mj-agent.rules' (...)
EXECUTED_WITH_FINDINGS                      # rc 1
# re-sync 之后
OK: projection in sync (surface=enforcement, 18 skills, lock consistent)
EXECUTED_CLEAN                              # rc 0
```

⇒ AGENTS.md hunk 与 render **必须同一 commit**。

## 3. Codex 0.147.0 wire 的**实证**来源（含一处**曾经臆造**的更正）

仓内对 `.rules` 语法与 hooks 配置 wire **零文档**。以下形状取自**已安装的
codex-cli 0.147.0** 二进制串表：

- **hook 事件词汇**（`HookEventNameWire`）：`PreToolUse` / `PermissionRequest` /
  `PostToolUse` / `PreCompact` / `PostCompact` / `SessionStart` / `SessionEnd` /
  `UserPromptSubmit` / `SubagentStart` / `SubagentStop` / `Stop`。
- **PreToolUse 输出 wire**：`{"decision":"block","reason":"<non-empty>"}` 受支持；
  `decision:approve`、`permissionDecision:allow`、`permissionDecision:ask` 均
  **unsupported**，`decision:block` **必须带非空 reason**。⇒ allow 路径**不输出任何东西**。
- **PreToolUse 输入字段**：`session_id, turn_id, agent_id, agent_type,
  transcript_path, cwd, hook_event_name, model, permission_mode, trigger,
  tool_name, tool_input, tool_use_id`（另有 `agent_transcript_path` /
  `last_assistant_message` / `stop_hook_active`）。§5.9 禁止作为输入的那几项**确实
  在 payload 里** —— 这正是 §5 no-read spy 必须存在的原因。
- **apply_patch 信封**：`*** Begin Patch` / `*** Add File:` / `*** Delete File:` /
  `*** Update File:` / `*** Move to:` / `*** End Patch`，以
  `{"command":["apply_patch","*** Begin Patch\\n..."]}` 到达（二进制另有
  `CommandDidNotStartWithApplyPatch`，证实首 token 必须是 `apply_patch`）。
- **`.rules` 方言**：Starlark，`prefix_rule(pattern=[...], decision="...")`。
- **hooks 文件容器**（**Stage 11 才补上的一项**）：`HooksFile` 的 serde 字段表实测
  = **`description` + `hooks` 两个键**（`0xe16bd53` 处
  `...internally tagged enum HookHandlerConfig` `HooksFile` `description` `hooks`）；
  handler 配置类型 `HookHandlerConfig::Command` 的字段为
  `command / commandWindows / timeout / async / statusMessage /
  additionalContextLimit`（`0xdf7173a`，**6 elements**）。

> ⚠ **本节初稿的自我更正**：初稿声称「全部形状取自已安装的 codex-cli 0.147.0…而非
> 臆造」，但**容器 schema 当时并不在取证清单里**——渲染器把 provenance 写成了自造的
> 顶层键 `_generated`。`HooksFile` 是 `deny_unknown_fields`，**任何多余顶层键都会让
> 整个文件解析失败、零 hook 注册**，且因为「无法解析的 hooks 文件是 warning 而非
> error」，**失败是静默的**。Stage 11 refuter 用 `codex app-server` 的 `hooks/list`
> 对**当时那份字节**复现了错误
> ``unknown field `_generated`, expected `description` or `hooks` at line 2 column 14``，
> 并证明删掉该键后同一文件即可加载两个 hook（`"source": "project"`）。
> 已改为写入 `description`（合法字段）。**这条是本单元最接近「交付了一个不工作的
> 产物」的一次**，记在此处而不是轻描淡写。
> 同时被 refuter 证伪的两个次生怀疑：配置文件里的键**确实**是 `timeout`（`timeoutSec`
> 只是 app-server 投影 `HookMetadata` 的字段），且项目根 `.codex/hooks.json`
> **确实**是被发现的一层（`HookSource: "project"`），**不需要** config binding ——
> 即 DIRECT 路线不影响 hook 发现。

### 3.1 两个会让 fixture 变成**空断言**的陷阱（本机实测）

```text
$ codex execpolicy check --rules probe.rules git checkout -b feature/x
{"matchedRules":[{...,"decision":"forbidden"}],"decision":"forbidden"}
rc=0                     # ← 陷阱 1：forbidden 也 rc=0，退出码不是判据

$ codex execpolicy check --rules probe.rules ls -la
{"matchedRules":[]}
rc=0                     # ← 陷阱 2：无匹配时 `decision` 键"整个缺失"，不是 "allow"
```

⇒ fixture 必须解析 JSON **且断言 `"decision" in result`**。写成
`result.get("decision") != "allow"` 对「forbidden」和「根本没匹配上」**同时为真**。

### 3.2 「取最严判定」= 断言 codex 自己报的值

实测 codex 已在**所有匹配规则之间、以及多个 `--rules` 文件之间**取最严
（`allow` < `prompt` < `forbidden`）。故 §5.9 的 "choose the strictest decision"
在实现上等于「断言它报出来的 `decision`」，renderer 不重实现优先级。

### 3.3 生成产物在 codex 里的**真实**判定（本机实跑，显式 `--rules`）

| 命令 | codex 判定 |
|---|---|
| `git checkout -b feature/x` | `forbidden` |
| `git switch -c x` | `forbidden` |
| `gh pr merge 519` | `forbidden` |
| `psql -h host` | `forbidden` |
| `git commit -m x` | `prompt` |
| `git push origin develop` | `prompt` |
| **`git worktree add ../x -b x`** | **无匹配（放行）** |
| `ls -la` | 无匹配（放行） |

最后两行是重点：**G1 的正确路径没有被误伤**。
⚠ 该表是**显式传 `--rules <path>` 的判定**；「codex 在会话中自动加载
`.codex/rules/mj-agent.rules`」**未被本单元证明**（见 §9.4）。

## 4. Deny canary：证明「写入之前」而不是「写入之后回滚」

loader 只接受 **`PreToolUse`**（`ALLOWED_EVENTS`）—— codex 在**工具调用执行前**评估它
（二进制串 `Tool call blocked by PreToolUse hook: `）。**`PostToolUse` 被硬拒**并有专门
负测试：PostToolUse deny 语义上是回滚，不是 §5.9 要的 block。

render/reconcile 半边用**全树字节快照**证明：

```python
before = snapshot(root)          # .agents/** + .codex/** + .agents.lock.json 全字节
_write(root / SOURCE_RELPATH, mutated)
assert sync_main(["sync"], repo_root=root) != 0
assert snapshot(root) == before  # 一个字节都没动
```

四种畸形源各跑一遍，且快照先断言非空（`assert before`）。

**Stage 11 对该 canary 的证伪尝试与结论**：finder 主张「快照基线取自已收敛的树，
而 `_do_sync_v2` 在内容已相同时跳过 `_atomic_write`，故对『写了正确字节』盲」，
并声称构造出了「校验移到写之后」仍能通过的回归。**Refuter 复现了该回归，结论相反**：
四个参数**全部**被 canary 捕获。决定性输入是 finder 漏算的 —— `snapshot()` 含
`.agents.lock.json`，而两个 enforcement entry 都绑定 `enforcement_source_sha256`，
故**任何**对 typed source 字节的改动都会改变 lock 文本，先跑的写阶段必然可见。
唯一不敏感的形状是「写入与磁盘上完全相同的正确字节后再拒绝」，那恰恰就是 docstring
声称的后置条件（树逐字节不变、内容正确），不是缺陷；而且第四个参数
（`post-tool-use`）实测**同时**改变了渲染字节并触发校验失败。

## 5. No-read spy（AC-12）

`project_payload()` 是 guard 的**第一个动作**，把 payload 投影到
`ALLOWED_INPUT_KEYS = (hook_event_name, tool_name, tool_input)`，此后所有代码只读投影
结果 ——「永不作为输入」因此是**结构性质**。测试用记录键访问的 `dict` 子类断言 6 个禁止
字段零读取，并断言 evaluate 确实产生了判定（防空断言）。

Stage 11 补齐的覆盖缺口：初稿**没有任何测试执行 `main()`** —— 也就是
`.codex/hooks.json` 真正调用的那个函数，block-decision wire 零覆盖。现已补：
block wire 形状（`{"decision","reason"}` 两键、reason 非空）、allow 路径**静默**
（`decision:approve` 不受支持）、四种不可用 payload 的 fail-open、无 typed source 时静默。
`main()` 的审计追踪实测只有**一次** `open(sdd/adapters/codex-enforcement.yml)`，
无 socket / subprocess / 写操作。

## 6. Surface 路由：本单元**最重要**的回归防线

PR-D1a 之前 `_do_check_v2` 用 `is_mcp = key == CODEX_LOCK_KEY` 的二分法决定 surface，
即「凡不是 config key 的都算 skills」。若原样落地，`.codex/hooks.json` 会掉进 skills 桶，
**V10（BLOCKING）** 会去执行 V13 的 scope —— 正是 §2.6 禁止的形态。已改为按 entry 自身的
`surface_members` 路由。这是**收窄回登记 scope**，不是扩大 blocking 面，故**不触发**
`ci-blocking-gate-toggle`。

```text
hooks.json 被手改后：
  --surface skills       → rc 0     # V10 BLOCKING，不受影响
  --surface mcp          → rc 0     # V11 BLOCKING，不受影响
  --surface enforcement  → rc 1     # V13 warning，正确捕获
```

### 6.1 ⚠ 但 surface 路由**不足以**保住 warning 姿态（Stage 11 高危发现）

`_in_scope` 在 `surface == "all"` 时对**每个** entry 返回真 —— 这是正确的。问题在于
**既存的 real-tree 钉线跑 bare `--check`（默认 surface=all），而它们在 BLOCKING 的
`Tests` step 里**。本 PR 把 enforcement 纳入 `all`，于是 real-tree enforcement drift
会打红一个 blocking step —— **V13 的 predicate 事实上变成 blocking**，正是本单元被明令
不得打开的后门，且 blast radius 包含**任何**对三个 `policy_refs`
（AGENTS.md / policies/ai-agent.md / policies/git-branching.md）的编辑而未重跑 `sync`。

修复了**两处**（review 只找到第一处，第二处由作者复扫补出）：

| 位置 | 原断言 | 改为 |
|---|---|---|
| `tests/unit/test_agents_sync.py::test_real_tree_projection_in_sync` | `sync_main(["--check"], REPO_ROOT) == 0` | 拆成 `--surface skills` + `--surface mcp` 两条 |
| `tests/unit/test_v2_engine.py::…real_tree…` | 同上（且注释自述 bare `--check` 是「load-bearing」） | 同上，并**新增**「每个 lock entry 至少属于一个 surface」的结构断言，保住原意图中不依赖 enforcement 内容的那半 |

两处都写明 **PR-D2 连同 `ci-blocking-gate-toggle` 记录一起恢复 bare `--check`**。

### 6.2 PJ045 的诱发性 stale（本 PR 造成、本 PR 修）

`check_agents_projection.py`（V9，**BLOCKING**）此前硬编码「`.codex/` 下除 config 外
一律是 UNOWNED NEIGHBOR」。PR-D1a 让两个产物变成 lock-owned 之后，该 info 行成为
**一个 blocking gate 打印的事实性假话**。已改为 lock-aware（v1/v2 双 schema 都读）。
实测 V9 的 info 计数由 **2 → 0**。

## 7. V13 挂载（`ci.yml`）

```yaml
- name: 'V13 codex enforcement drift (WARNING per plan §5.9)'
  continue-on-error: true
  run: uv run python scripts/sdd/agents_sync.py --check --surface enforcement
```

- `continue-on-error: true` **显式书写** —— 省略该键等于 BLOCKING（V11 即如此）。
- step 名**刻意不含 anchor 占位串**：V12 把 `PENDING_PR_C1_FIRST_CI` 写进 step 名，
  该串随后成为 follow-up **F16**。此名即 §4.1.1 要求 D1b 逐字转写的 gate 标识。
- **rc 0 有两种含义**，故 step conclusion 不可作判据。result_code 只在
  `--surface enforcement` 输出；实测 `skills` / `mcp` / `all` 三种 stdout **不含**任何
  result_code token（有专门测试钉住）。
- **四态 result_code**（按执行体源登记，不按 clean 输出登记）：
  `EXECUTED_CLEAN`（rc 0）· `EXECUTED_WITH_FINDINGS`（rc 1）·
  `SKIP_MANIFEST_V1` / `SKIP_NO_ENFORCEMENT_SOURCE`（rc 0，中性）·
  **`ERROR_UNREADABLE`（rc 2）**。最后一项是 Stage 11 补的：typed source 加载失败时
  原本**什么 token 都不打**，而 `continue-on-error: true` 会把 rc 2 抹成绿色 step，
  D1b 将无从观测到需要重置 epoch 的错误态；且 D1b 是零 behavior diff 的 anchor-only
  单元，**没有任何后续单元能补这段代码**，故必须在本单元修。

姿态用 `yaml.safe_load` **结构断言**复核：V8/V9/V10 `continue-on-error: False`、
V11 键缺失（=BLOCKING）、V12/V13 `True`；离线 pytest runner step 仍恰为 **3** 个。

## 8. 验证结果

| 项 | 结果 |
|---|---|
| V8 dual-agent manifest | rc 0 — errors 0 / warnings 0 / info 0 |
| V9 agents projection | rc 0 — errors 0 / warnings 0 / **info 0**（PJ045 修复前为 2） |
| V10 skills drift（BLOCKING） | rc 0 — in sync（18 skills） |
| V11 mcp drift（BLOCKING） | rc 0 — in sync |
| V12 cross-carrier | rc 0 — `EXECUTED_CLEAN`，pass 7 / warn 0 / err 0 |
| **V13 enforcement（新）** | rc 0 — `EXECUTED_CLEAN` |
| `--check`（surface=all） | rc 0 — in sync |
| fidelity attestations `--all` | rc 0 — errors 0 |
| offline boundary checker | rc 0 — GREEN |
| G7 secret exposure | rc 0 — 4P / 0W / 0F |
| ruff / mypy / compileall | rc 0 / rc 0（48 files）/ rc 0 |
| frontmatter / wikilinks / stale-docs / kernel refs | 138 docs OK / 0 unresolved / OK / 0 violations（20 sections） |
| offline pytest（全量） | **1453 passed / 16 skipped / 2 failed**（见下） |
| 新增测试单独跑 | **86 passed**（含 `codex execpolicy` 实跑腿，非 skip） |

**2 项 failed 的性质（如实登记）**：
`tests/unit/test_run_codex_carrier_probe_p1b.py` 的两条，断言
`imported_sha256 == blob_sha256`，其中 `blob_sha256` 取自 **`git show HEAD:<path>`**。
本单元修改了 `scripts/sdd/agents_sync.py` 与 `scripts/sdd/check_agents_projection.py`
而尚未 commit，故必然不等。判据链：(a) rev 取 `probe.git_head(REPO_ROOT)` = HEAD；
(b) 两侧都做 `\r\n`→`\n` 归一，两文件实测 `i/lf w/lf`；(c) 逐一比对 7 个 production
module，**只有这两个与 HEAD 不同**，其余 5 个 `git diff --quiet HEAD` 全净。
⇒ **commit 后即消失**，已列为 post-commit 复验义务（§10）。

### 8.1 EOL 无关性（实测，非假设）

把两个产物就地改成 CRLF 后 `--check --surface enforcement` 仍 `EXECUTED_CLEAN`
（两种 normalization policy 两侧都做 LF 归一）⇒ **不需要** `.gitattributes` pin
（与 C1 的 `raw-bytes-v1` byte-copy 情形不同）。

## 9. 本单元明确**未**证明的事（§1.3 assurance 分层）

1. **「Codex harness 在副作用前拒绝」未被证明。** 本仓不执行 Codex harness。已证明的是
   **render/reconcile 侧在写入前拒绝**（§4）与 **`.rules` 在显式 `--rules` 下的真实判定**
   （§3.3）。PR-P1a 的 det-09/det-10 只证到「构造面存在」，其证据文件把执行级 canary
   交给 PR-D1a —— 本单元**部分**兑现：规则腿实跑，hook 腿未跑。
2. **hook 执行腿 = SKIP。** codex 0.147.0 的 hooks 受**持久化 per-hook 哈希信任**门控
   （`trusted_hash`）。本机未持久化任何 hook 信任，本单元亦未执行 hook canary，
   记为 **SKIP_HOOK_NOT_REVIEWED**。**刻意不用** `--dangerously-bypass-hook-trust`：
   那测的是非生产机制，且 D-015 明令仓内脚本不得代写信任状态。
3. **本单元自己没能复现「文件可被加载」。** §3 里那次 `_generated` 修复的**证伪**
   来自 Stage 11 refuter 的 `codex app-server` + `hooks/list` 复现；作者随后尝试复刻
   该探针**未能取得 `hooks/list` 响应**（`initialize` 正常，该方法疑似受实验开关门控）。
   故「修复后文件确实能被 codex 加载」目前依据是 **(a) 二进制 `HooksFile` serde 字段表
   只含 `description`/`hooks`，(b) refuter 的复现**，**不是**作者的直接实测。按 §1.4
   记为 **未由本单元执行**。
4. **`.codex/rules/*.rules` 的自动加载未证。** §3.3 全部判定都显式传 `--rules <path>`；
   codex 在会话中是否自动加载项目根的该文件，本单元没证。二进制存在项目级 rules 路由
   的迹象（`--ignore-rules` 帮助文本），但目录未确认。
5. **CI 里跑不到 codex。** 四个 workflow 均 `ubuntu-latest` 且无 node/codex 安装步骤，
   故 `codex execpolicy` 腿在 CI **恒 SKIP**（by construction）。V13 自身是纯 Python。
6. **`.rules` 方言与 hooks wire 钉在 codex-cli 0.147.0。** 仓内无规范文档；未来版本可能变更。
7. **guard 在未知 payload 形态下 fail-open。** 无法解析 / 非 PreToolUse / typed source
   缺失时**不拦截**。刻意选择：cooperative aid 不应因不认识的 payload 卡死 Codex 会话。
   代价是它不能被当作边界。
8. **shell 组合可绕过 `command` / `command_arg` 面（Stage 11 新增披露）。** 匹配是
   **token 前缀**锚定在 argv[0]，故 `cd /tmp && psql ...`、`echo hi; git checkout -b x`
   一类组合命令**不会触发**；实测 `.codex/rules/mj-agent.rules` 在 `codex execpolicy`
   下有**同样**的前缀-only 性质。裸命令（`psql ...` / `cat .env` / `git checkout -b x`）
   均正确拦截。这是 cooperative aid 的已知上限，AGENTS.md 散文仍是真边界。
9. **`path` 面只覆盖写入目标。** apply_patch hunk 头 + `file_path`/`path` 键（+ 任意
   字符串值里的信封）。经 shell 重定向 / 变量展开 / 管道构造的写入不在覆盖内。
10. **det-12 未覆盖两个新 renderer。** 见 §11.3 F19。

## 10. AC 对位

| AC | 达成方式 | 判定 |
|---|---|---|
| **AC-11** | V13 的 `run` 与 plan §5.9/§5.10 声明**逐字一致**（Stage 11 复核：sha `6c37a730…`、len 70、byte-identical）。该命令在 PR-D1a 之前**跑不通**（argparse 只收 `{skills,mcp,all}`，exit 2），本 PR 使其可执行；clean predicate 由 `--surface enforcement` 实发 `EXECUTED_CLEAN` 兑现，且四态 result_code 齐全 | **PASS**（anchor 值本身归 D1b） |
| **AC-12** | `project_payload` 投影 + 记录键访问的 spy，断言 6 个禁止字段零读取；`main()` 全路径覆盖；审计钩子实测只开 typed source 一个文件 | **PASS**（receipt/TTL 部分归 PR-E） |

**post-commit 复验义务（Stage 10 未完部分）**：commit 之后必须重跑
`task0_freeze.py --check`（identity 将重锚，属预期）与全量 offline pytest
（上述 2 项 P1b 失败应转绿）。**未跑完这两项不得建 PR。**

## 10b. Stage 11 对抗性自评审记录

6 finder 镜头 + 8 refuter（按 must_fix 优先、再按严重度取 top-8），**14 计划 / 14 完成 /
0 失败**。**47 findings**（9 high / 16 medium / 14 low / 8 info），其中 **11 条标
must_fix**。**F15 纪律已遵守 —— refuter 运行期间全程未改树。**

进入 refutation 的 8 条中 **5 条未被驳倒、3 条被驳倒**；被驳倒的三条都读了理由正文而非
只看布尔值，其中两条的**更正版本反而更严重**：

- `_generated` 那条 finder 原判是「容器 schema 未验证」（UNVERIFIED），refuter 驳倒了
  它的两个次生论据（`timeoutSec`、需要 config binding），却**证实并升级**了核心：
  文件**根本无法加载**。
- 「deny canary 是空断言」被**实证驳倒**（refuter 复现了 finder 声称的回归，四参数全部
  被捕获）。
- 「`bash -lc` 包装绕过」的**机制**被驳倒（codex 0.147.0 的 shell 工具不是那个形态，
  二进制内 `bash -lc` 字面量为 0），但**结论的实质保留**：前缀-only 匹配确实被
  shell 组合绕过，已写入 §9.8 披露。

⚠ **覆盖缺口如实披露**：refuter cap = 8，**39 条未经对抗性证伪**，闭合判据仅为作者复核
与逐条实测。作者复扫另外补出 **1 条 review 未发现的同类缺陷**（§6.1 的第二处 real-tree
钉线），说明 must_fix 列表本身不是穷尽的。

## 11. 与后续 unit 的接口

### 11.1 给 PR-D1b（V13 anchor）的现成口径

1. **gate 标识三元组**：plan §5.9 表 ↔ `sdd/gates.md` §2 行（**D1b 新增**）↔ `ci.yml`
   step 名 `V13 codex enforcement drift (WARNING per plan §5.9)`（逐字转写，勿改）。
2. **anchor 只能取 PR head run** —— merge commit 不触发任何 run（C1/C2 两次独立实证）。
3. **首次真实 CI 取 push run**（早于 PR run；C2 实测相差约 45 秒）。
4. **计数按 head SHA 归并**；「同 head SHA 恒 2 次 run」是伪不变式。
5. **rc 0 有两种含义** —— 必须读 stdout `result_code`。V13 的**四态**集合见 §7，
   **按执行体源登记**：`SKIP_*` 两态与 `ERROR_UNREADABLE` 在正常树上永不打印。
6. **`sdd/gates.md` 升版三件套**：升 `version` + 刷 `updated` + 写 changelog 条目
   （历史 12/12 一致，且 `check_frontmatter.py` 的 SCAN_ROOTS 不含 `sdd/**`）。
7. **`policies/ci-gates.md` §6 的 `V1-V12` → `V1-V13` 归 D1b**，与 gates.md 行同 PR
   （本单元已把该改动回退，理由见 §1）。

### 11.2 F17 提醒（顺序约束未解除）

V12(§5.8) 与 **V13(§5.9)** 的观察期注册表**都寄居在 PR-G 会翻 `completed` 的 plan 里**。
本单元没有扩大该问题（V13 注册表是 PR-0a 就写好的 skeleton，本 PR 一字未改），
也没有解决它。**PR-G 之前必须 re-home 两份注册表**。

### 11.3 F19（本单元新增）

`run_codex_carrier_probe.production_modules()` 的 7 模块元组未含
`codex_hook_renderer` / `codex_rule_renderer` / `enforcement_source` / `codex_hook_guard`，
故 det-12 的 renderer-identity 钉线不覆盖它们。**不在本单元处理**：该元组属 PR-P1b 的
immutable evidence 语义面。现有覆盖 = lock 的 `renderer_module_sha256` + `--check`
（warning 门）。

### 11.4 F20（本单元新增）

**PR-D2 恢复 bare `--check` 时必须同时处理两处 real-tree 钉线**（§6.1 表），
且那次恢复**本身就是**把 enforcement 纳入 blocking，故必须携带独立的
`ci-blocking-gate-toggle` Owner 记录 —— 与 §5.10 对 D2 的要求一致。
