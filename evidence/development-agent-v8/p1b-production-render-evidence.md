---
type: evidence
summary: >-
  Epic #499 PR-P1b production render evidence —— 具名 producer
  `scripts/sdd/run_codex_carrier_probe.py --unit p1b` 以 **恰好是 production 的
  renderer / module / version**（PR-B 落地的 `_common/{skill_renderer,
  codex_config_renderer,codex_readme_renderer}.py`，均 RENDERER_VERSION=1）针对冻结的
  PR-B merge commit `36f298a9995f` 渲染候选 18 carrier + README + Codex config，
  跑 deterministic（exact-byte）与 canary（fresh-process discovery / budget /
  trust route / hook·rule）两腿：**103 cases 全 PASS，verdict = `PASS`**
  （P1a 的 unit 级标签 `PASS_CANDIDATE` 不足，只有本单元的 `PASS` 才允许进 PR-C0）。
  新事实：production 渲染后 **18/18 描述零截断**（P1a 为 12/18 截断），
  translated 的 codex_discovery_summary 落在 218–277 字符；byte-copy 的
  `raw-bytes-v1` 在 Windows checkout 上与 blob 相差 CRLF（F9 实测量化）。
owner: ranzuozhou
created: 2026-08-26
updated: 2026-08-26
state: active
track: agent
---

# Production Render Evidence — Epic #499 (PR-P1b)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §2.8.6（probe schemas）与 §5.6
> （P1b 定义）。Delivery unit = **PR-P1b**，AC = **AC-09 + AC-10**，merge condition =
> deterministic **`PASS`**（§5.1 row 9）。Rollback = evidence correction PR；
> **不得改 production renderer**（§5.1.1）。

## 0. 入场锚点与 Owner 拍板记录

| 项 | 值 |
|---|---|
| 探测 revision（冻结面） | `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f`（= PR-B merge commit = `origin/develop`） |
| 前序 unit | PR-B = [#514](https://github.com/MJ-AgentLab/mj-agent/pull/514)，MERGED `2026-08-26T01:48:29Z`（head `ef1efbac57c3`） |
| 前序 Stage 17 ledger | [#499 comment 5419504853](https://github.com/MJ-AgentLab/mj-agent/issues/499#issuecomment-5419504853)，body SHA-256 `66c4ca7ced747f521957692737666975b5d32f1172fa4150e9905b3b55a23518`（纯 LF，逐字节复算吻合；18 records 全终态，治理事实 6 条精读） |
| 本 unit branch | `documentation/499-production-render-evidence`，`git worktree add` 自 `36f298a`（G1） |
| Task-0 preflight | `task0_freeze --check` = `TASK0_FREEZE_CLEAN`，identity `8c7c1e4847b8c5efe843009fd4d6c2b357488325f1f67ca2e1ec409546cce443` 不变（58 hard + 1 controlled；本单元变更集全在冻结面外） |
| codex 载体 | codex-cli **0.147.0**（npm vendor 原生 `codex.exe`；与 P1a 同 build） |

**Owner 拍板（Gate 1，实施前一次呈清四问，四项均取推荐方案）**：

1. **fixture 落位 = 新建 p1b 专属文件**。P1b 的期望值是「production 渲染产物」，与 P1a
   的「raw source」不是同一类工件；`probe/fixtures/p1b-deterministic-expected.json`
   pinned@`36f298a9995f` 新增，P1a 的 `deterministic-expected.json` 保持 **字节不变**
   （pinned@`33dd984fa642`），P1a 已发布证据因此仍可复算。producer 加 `--unit p1a|p1b`。
2. **渲染输入字节 = blob 物化 LF 树 @36f298a**。渲染所需输入（18 source + 4 typed/template
   + manifest + `.mcp.json`，共 24 项）按 git blob 字节物化到临时树后再渲染，因此本单元
   发布的每一个候选 digest 都与机器无关、Linux CI 可复算。代价与 F9 的耦合见 §5。
3. **telemetry 腿 = 全 18 项、108 次真实 `codex exec`**（sanctioned probe 载体）。13 项
   translated 现在携带 ~250 字的紧凑 summary，与 P1a 探测的 raw 长描述完全不同，
   「紧凑 summary 是否仍能驱动正确的隐式触发」是 cutover 前唯一未验的行为面。
4. **候选产物 = 只发布 digest**。逐路径 SHA-256 + set digest + renderer 模块 digest/version
   入库；20 个渲染产物本身不入库——渲染确定性已实测（det-14），PR-C0 用同一 producer
   重跑即可逐字节复现，避免在仓内留下与 C1 将写内容重复的 260 KB 副本。

## 1. 交付面（Gate 1 批准的 exact scope）

| 文件 | 变更 | 角色 |
|---|---|---|
| `scripts/sdd/run_codex_carrier_probe.py` | 修改 | 具名 producer 增 `--unit` / `--rev` + P1b 候选渲染管线 + 8 个新 case 家族；**§2.8.6 的两个结果 schema 未动** |
| `tests/unit/test_run_codex_carrier_probe_p1b.py` | 新增 | 34 条 P1b 契约测试，**每个新 case 家族各配一条负控**（Stage 11 后补齐了直接驱动真实函数的负控） |
| `tests/unit/test_run_codex_carrier_probe.py` | 修改 | P1a 契约随 `det-00-fixture-pin` 更新（70 → 71 cases）+ 新增 stale-pin 判别测试 + 渲染失败落 case 的负控 |
| `evidence/development-agent-v8/probe/fixtures/p1b-deterministic-expected.json` | 新增 | P1b 预提交期望值（pinned@`36f298a9995f`） |
| `evidence/development-agent-v8/probe/deterministic-gate-v1-20260826T053136Z-36f298a9995f.json` | 新增 | deterministic + canary 真实 run 结果（§2） |
| `evidence/development-agent-v8/probe/model-telemetry-v1-20260826T041829Z-36f298a9995f.json` | 新增 | telemetry 真实 run 结果（§4） |
| 本文件 | 新增 | tracked 证据摘要 |

**零变更面（实测复认）**：`.agents/**`、`.codex/**`、`.agents.lock.json`、`.mcp.json`、
`sdd/development-agent.yml`、全部 typed sources 与 3 个 production renderer 模块**均未改动**。
合并前实测 `agents_sync.py sync` = `OK: up to date (5 skills)`，V8/V9 `--all --fail-on warning`
= 0E/0W，V10/V11/`--surface all` clean，`task0_freeze --check` = CLEAN。
**真实树仍是 manifest v1 + legacy v1 flat lock，v2 引擎依旧 dormant**——本单元只渲染候选、
只写 evidence，不做 cutover（cutover 是 PR-C1）。

Raw 捕获（prompt-input JSON / mcp list / exec 事件流）落 **gitignored**
`.mj-agent-local/probe/<run-id>/`，tracked 结果只存 digest。

## 2. deterministic-gate-v1 结果（真实 run）

结果工件：[`probe/deterministic-gate-v1-20260826T053136Z-36f298a9995f.json`](./probe/deterministic-gate-v1-20260826T053136Z-36f298a9995f.json)
（79 765 B，raw SHA-256 `c5053b6418d150c1eb08206fa9c361837ba0c600696736eb21e4a4189629f7e8`，纯 LF）。

- **verdict = `PASS`**；**103 cases 全 PASS，reason_code 全 `OK`**（零 FAIL / 零
  BLOCKED_PREREQUISITE / 零 ERROR）。
- `repo_head = 36f298a9995f…`（显式 `--rev`，不是 branch HEAD），
  `codex_build = codex-cli 0.147.0`，run 窗口 `2026-08-26T05:31:36Z → 05:31:43Z`。
- 非空泛证据：103 个 case 的 expected/actual 全为 64-hex，**53 个互异的 expected digest**，
  det-13 的 20 个 actual digest 两两互异——不是「空集互等」式的假 PASS。
- 重编码解析结果逐字节复现文件（`canonical_json_bytes(doc) == file bytes`）。

### Case 家族（103 = 结构 76 + canary 27）

| 家族 | 数 | 判什么 | 载体 |
|---|---:|---|---|
| det-00 fixture-pin | 1 | fixture 的 `pinned_head` == 被探测 revision | 纯静态（**新增**） |
| det-01 manifest-required-inventory | 1 | manifest 派生 required 集 == §2.2.1 的 18 | `sdd/development-agent.yml` |
| det-02 source-present | 18 | source blob 存在、raw SHA 与 fixture 一致、frontmatter 合法 | git blob |
| det-03 derived-path | 18 | `.agents/skills/<id>/SKILL.md` 路径安全 | 纯静态 |
| det-04 casefold-collision | 1 | 18 派生路径 casefold 互不冲突 | 纯静态 |
| det-05 description-budget | 18 | **渲染后**描述的呈现形态 == fixture 预测 | staged 布局 `codex debug prompt-input` |
| det-06 artifact-digest | 5 | 真实树 byte-copy artifact raw SHA == source raw SHA（v1 树仍自洽） | git blob |
| det-07 fresh-discovery | 4 | fresh 进程 discovery 集合精确匹配（staged root/nested/worktree = 18；real-root-user-layer = 5） | `debug prompt-input`（无模型调用） |
| det-08 config/trust route | 3 | user-layer trust 覆盖仓根；staged 差分（trust-less `[]` vs trusted canary）；真实树 project 8 server 全载入 | trust 表解析 + `mcp list --json` |
| det-09/10 hook/rule canary | 2 | `features list` `hooks stable true` + `--dangerously-bypass-hook-trust` / `--ignore-rules` 旗标在位 | 构建面存在性 |
| **det-11 candidate-manifest-v2-schema** | 1 | 候选 v2 manifest 通过 production V8 的对象级检查（top-level + DA090-096 + posture），零 error | `check_development_agent` |
| **det-12 renderer-identity** | 7 | 实际执行的 renderer 模块 LF-归一 digest == 冻结 commit 的 blob digest，且 `RENDERER_VERSION` == fixture | `module_source_sha256` vs blob |
| **det-13 render-exact-byte** | 20 | 每个候选产物逐字节复现 fixture 钉定的 digest | production `_v2_desired_state` |
| **det-14 render-determinism** | 1 | 同输入两次独立渲染，20 个产物全字节相同 | 双渲染比对 |
| **det-15 candidate-set-digest** | 1 | 候选集合 set digest（§2.7 wire）== fixture | 纯静态 |
| **det-16 carrier-partition** | 1 | 派生分区 == §2.2.1（5 byte-copy + 13 translated，互斥，并集 = 18） | workflow registry 派生 |
| **det-17 render-inputs** | 1 | 24 项渲染输入 blob digest == fixture | git blob |
| **det-18 candidate-render** | 0※ | 候选渲染失败时的兜底：落 `ERROR` case 并仍写出 evidence | 异常收敛 |

（加粗 = P1b 新增家族；det-00 亦为新增，两个 unit 共用。※ det-18 与 det-11–det-17 互斥：
渲染成功时它不出现，渲染失败时只出现它——本次 run 渲染成功，故为 0。）

### 「恰好是 production 的 renderer / module / version」如何成为可核验事实

§5.6 要求用 exact production renderer。本单元不靠声明，靠 det-12：候选产物由
`scripts.sdd.agents_sync._v2_desired_state()` —— **production 的 desired-state 派生入口本身** ——
产出，其内部导入并调用 production renderer 模块；det-12 再把「实际被导入执行的模块文件」的
LF-归一 digest 与「冻结 commit 上该模块 blob」的 LF-归一 digest 对比：

| 模块 | 角色 | RENDERER_VERSION | LF-归一 digest（imported == blob） |
|---|---|---:|---|
| `scripts.sdd._common.skill_renderer` | translated 渲染 | 1 | `6d50f964d49c7d3a…` |
| `scripts.sdd._common.codex_readme_renderer` | README 渲染 | 1 | `7af18ed60f832f66…` |
| `scripts.sdd._common.codex_config_renderer` | Codex config 渲染 | 1 | `f26dafdd9c28ed43…` |
| `scripts.sdd.agents_sync` | **desired-state 编排 + byte-copy 分支** | — | `d761014c9beb8039…` |
| `scripts.sdd._common.projection_loader` | digest / slice 助手 | — | `802e3ce272b17290…` |
| `scripts.sdd.check_agents_projection` | MCP projection（config 输入） | — | `46231e0c69c690d6…` |
| `scripts.sdd.check_development_agent` | det-11 的 checker | — | `a90df5f58ee89da2…` |

**覆盖面是全管线，不只是三个声明了 `RENDERER_VERSION` 的模块**（Stage 11 修复）。这一点是必需的：
fixture 与 deterministic run 由**同一棵工作树**产出，若编排层未被钉住，一个未提交的
`agents_sync.py` 改动会同时污染两侧，使 det-13/14/15/17 全部「drifted vs drifted」一致通过，
而 evidence 仍宣称用了 PR-B 的 production renderer。`agents_sync` 尤其关键：5 项 byte-copy 的
字节由它的分支直接 `read_bytes()` 产出，不经任何声明了 `RENDERER_VERSION` 的模块。

负控在测试里：本机改过的模块**不能自证**——`imported != blob` 时 det-12 报
`RENDERER_MODULE_NOT_FROZEN`（`test_det12_fails_when_the_module_is_not_the_frozen_one`）；
某个模块整体退出管线时报 `RENDERER_MODULE_ABSENT`（det-12 按 observed ∪ expected 遍历，
`test_det12_reports_a_module_that_dropped_out_of_the_pipeline`）。

### 候选 manifest 是**派生**的，不是抄的（AC-04）

候选 v2 manifest 由两条既有 SoT 机械派生，producer 内不写死任何计数：

- **translated** ← `sdd/workflows/development-agent-workflows.yml` 的 `capability_id` 集合
  （registry 是 §2.5 的 workflow 语义 SoT）；`carrier_binding.workflow_id` 取自同一记录。
- **byte-copy** ← 当前 manifest 里已是 `projection: project` 的行。
- 其余一律 `codex_carrier: none`。

派生结果与 plan §2.2.1 的对照放在 det-16 作为**被报告的 case**，而不是 producer 内的断言——
不符时给 `CARRIER_PARTITION_MISMATCH` 红，而不是崩掉。实测：byte-copy 5 / translated 13 /
交集 ∅ / 并集 == 18。

### 候选产物 digest（PR-C0 binding / PR-C1 复现锚点）

`candidate_set_sha256` = `54235bb5a1f149dc743907e72a2a4bf720eac529f4075f250ce4a07851b5444a`
（§2.7 set-digest wire，20 项）。`candidate_manifest_slice_sha256` =
`1688c5c4a46a677f665ec0077c04c57ba7645672db30c0a004f0672bcb39715f`。
逐路径 digest 见 fixture 的 `candidate_output_sha256`
（[`probe/fixtures/p1b-deterministic-expected.json`](./probe/fixtures/p1b-deterministic-expected.json)，
12 348 B，raw SHA-256 `b4f74930c5b04fb9674127a3397329ed78d7213f2efb8d3397699fee0f954c93`）。

**这些 digest 对 manifest 的注释/排版不敏感**。精确地说，候选**产物字节**只经三条 manifest
通路（不是 §2.8.2 的 lock slice —— 那是 lock entry 的口径，本单元不发布 lock）：

| 通路 | 影响哪些产物 | manifest 的哪部分 |
|---|---|---|
| 派生 carrier 分区 → `carrier_ids` | 13 项 translated（边闭合 / 路由渲染） | 每行的 `codex_carrier` |
| `strategy_summary` 计数 | `.agents/README.md` | 全部 capability 行的 `codex_carrier` |
| `load_mcp_projection` | `.codex/config.toml` | `mcp.servers.*.projection_policy` + `codex.posture` |

5 项 byte-copy 的字节完全不取决于 manifest（逐字节复制 source）；manifest 只决定它们**是否**
被投影。因此 PR-C1 写出的真实 v2 manifest，只要在上述三条通路上与本单元的候选语义等价，
就必须复现同一批 digest —— 这让「C1 复现 C0/P1b 的 artifact digest」成为一个真检验，
而不是同义反复；反过来，C1 若改动了 `mcp` / `codex.posture`（D-017 停面），`.codex/config.toml`
的 digest 就会合法地变化，届时应当重新走 C0 binding，而不是把差异当成 C1 的实现缺陷。

## 3. 新发现（本 probe 产出的 runtime 事实）

**F-P1b-1｜production 渲染后 18/18 描述零截断（P1a 为 12/18 截断）。** P1a 的
F-P1a-1 测得 Codex discovery 预算 = 1024 字符且 12/18 raw candidate 超限。本单元测的是
**渲染后**的 carrier：

| capability | carrier | P1a raw 字符 / 形态 | P1b 渲染后字符 / 形态 |
|---|---|---:|---:|
| doc-validate | translated | 1143 truncated | **270 complete** |
| flow-implement | translated | 1521 truncated | **277 complete** |
| flow-review-respond | translated | 1391 truncated | **270 complete** |
| flow-post-merge | translated | 1315 truncated | **250 complete** |
| flow-self-review | translated | 1236 truncated | **246 complete** |
| flow-verify | translated | 1180 truncated | **258 complete** |
| flow-repo-scan | translated | 1179 truncated | **250 complete** |
| flow-plan | translated | 1155 truncated | **259 complete** |
| flow-scope-drift | translated | 1095 truncated | **218 complete** |
| flow-intake | translated | 1063 truncated | **256 complete** |
| git-branch | translated | 791 complete | **258 complete** |
| git-pr | translated | 879 complete | **218 complete** |
| git-issue | translated | 712 complete | **232 complete** |
| flow-diagnose | byte-copy | 1322 truncated ※ | **1003 complete** |
| git-sync | byte-copy | 1062 truncated ※ | **1002 complete** |
| git-commit / git-delete / git-push | byte-copy | 746 / 771 / 739 complete | 同值 complete |

※ 这两行的变化**不是渲染造成的**（byte-copy 逐字节复制 source）：它们是 Owner 依 P1a
F-P1a-1 的建议在 `83fe8e6`（`docs(claude): fit two projected skill descriptions in Codex
1024 budget`）缩短了 source description 的结果。这也是 P1a fixture（pinned@`33dd984fa642`）
对当前树 det-02×2 / det-05×2 必然 FAIL 的**全部**原因——即 plan follow-up **F6** 所述的
程序性前置，本单元已按 Gate 1 第 1 项以独立 fixture 重发布消化（§0）。除这 2 个 source 外，
`33dd984fa642..36f298a` 之间 `.claude/skills/` 零变更（实测 `git diff --name-status` = 2 文件）。

- 13 项 translated 的 `codex_discovery_summary` 落在 **218–277 字符**：这 13 项的描述总量
  由 raw 的 **14 660 字符压到 3 262 字符**（−77.8%），其中 10/13 原本超限。全 18 项的总量是
  19 300 → 7 523 字符，但这个口径**不能全部记在 renderer 头上**——差额里有 379 字符来自
  上面 ※ 标注的两个 byte-copy source 缩短（commit `83fe8e6`），另外 3 项 byte-copy 逐字节
  未变。renderer 的贡献恰是 translated 的那一档。
- renderer 侧另有一道独立闸门：`skill_renderer.DISCOVERY_SUMMARY_MAX_BYTES = 1024`，
  按 **UTF-8 字节** 判定，而 Codex 的 1024 是**字符**预算。UTF-8 下字节数 ≥ 字符数，
  故「≤1024 字节」蕴含「≤1024 字符」——渲染侧的约束严于消费侧，方向是安全的。
- **余量警示**：两项 byte-copy 现在只剩 **21 / 22 字符**余量（flow-diagnose 1003、
  git-sync 1002，均对 1024）。byte-copy 终态没有 summary 兜底，任何一次几十字的
  description 追加都会让它们重新落入截断。建议在 C1 之后择机为这两项加一条钉线。

**F-P1b-2｜translated carrier 的 description 是双引号 YAML 标量，比较前必须解引号。**
translated renderer 把 `codex_discovery_summary` 写成 JSON 风格的双引号标量，而 Codex 的
loader 呈现的是**解析后的值**。P1a 的行式 frontmatter 解析器保留引号，直接比较会对全部
13 项 translated 报 `malformed`（实测：`classify(quoted) = malformed` /
`classify(unquoted) = complete` / `body == json.loads(desc)` 逐字节相等）。这是**探针侧
解析口径缺口，不是 renderer 缺陷**——production 渲染产物本身合法且被 Codex 正确加载
（det-07 discovery 18/18）。producer 已加 `unquote_frontmatter_scalar`；并钉线
「当前 18 个 raw source 无一使用引号标量」（`test_no_live_source_uses_a_quoted_description`），
以保证该步骤不改变 P1a 的口径。

**F-P1b-3｜byte-copy 的 `raw-bytes-v1` 在 Windows checkout 上与 blob 不同（F9 量化）。**
`_v2_desired_state` 的 byte-copy 分支直接读工作区字节，而 `.gitattributes` 的 `* text=auto`
使 Windows 检出为 CRLF。实测同一 revision 下：

| capability | git blob | Windows 工作区 | 工作区 CRLF 数 |
|---|---:|---:|---:|
| mj-agent-git-sync | 11 541 B | 11 793 B | 252 |
| mj-agent-git-commit | — | — | 310 |
| mj-agent-git-delete | — | — | 156 |
| mj-agent-git-push | — | — | 164 |
| mj-agent-flow-diagnose | — | — | 124 |

本单元按 Gate 1 第 2 项从 blob 字节渲染，因此 **5/5 byte-copy 候选 digest 逐字节复现了
`36f298a` 上已提交的 `.agents/skills/<id>/SKILL.md`**，而 5/5 的工作区字节 digest 与之不同。
translated 分支不受影响（`parse_source_document` 内部先做 `\r\n → \n` 归一），
3 个 renderer 模块 digest 也已 LF-归一。该事实是 plan follow-up **F9** 的直接输入，见 §5。

**F-P1b-4｜staged 探测项目刻意不放渲染出的 `.codex/config.toml`。** 该产物声明了 8 个真实
MCP server（含 5 个数据库型 `pg-mj-agent-memory-*`）。一次性探测项目没有理由持有可能拉起
它们的路由；且 telemetry 腿的 `project_config_sha256` 只有在「无 project config 生效」时
才是诚实的。因此 staging 只放 `.agents/**`。

该决定的**可复算依据**是两个已发布的 case，而不是任何一次性观察：产物本身的逐字节正确性由
det-13 覆盖（`.codex/config.toml` 是 20 项候选之一），trust/config 路由由 det-08 用专门的
单 server canary 覆盖。另有一条**非 tracked 的本地观察**（记录在此仅为说明，不作证据）：
telemetry 的 gitignored 事件流里没有出现 MCP server 活动——这与预期一致（telemetry 走
`--ignore-user-config`，无 trust 条目，project config 本就不会生效），但 `model-telemetry-v1`
的 §2.8.6 闭合 schema 不含任何 MCP 字段，所以**这一条无法从入库工件复算**，读者不应把它
当作本单元的结论。

## 4. model-telemetry-v1 结果（真实 run）

结果工件：[`probe/model-telemetry-v1-20260826T041829Z-36f298a9995f.json`](./probe/model-telemetry-v1-20260826T041829Z-36f298a9995f.json)
（23 330 B，raw SHA-256 `b4c21c053290bf9e39ea20cf7e56e1da4e805b83c5299cf1c1a0a099aafe3603`，纯 LF）。
run 窗口 `2026-08-26T04:18:29Z → 05:30:07Z`（约 72 分钟，108 次真实 `codex exec` 串行）。

| 项 | 值 |
|---|---|
| `model_id` | `gpt-5.6-terra`（CLI `-m` 显式钉定，与 P1a 同） |
| `codex_build` | codex-cli 0.147.0 |
| `repo_head` | `36f298a9995f…`（显式 `--rev`） |
| `repetitions` | 3（每 capability×prompt 恰 3 行，机器断言） |
| `prompt_fixture_sha256` | `64aa18debf2a5ee5cc2774863bd1f1b8343a2b88b082e78de347d3be9675c31f`（与 P1a **同一份** corpus，未改动——两次 run 因此可逐格对比） |
| `sampling_config.project_config_sha256` | `38e0b9de817f645c…` = canonical-null 的 absent-value digest，**与 P1a 同值**——实证 staging 不含 project config（F-P1b-4 的机器可核验形式） |
| `warnings` | `["EXEC_TIMEOUT"]`（1/108 行） |

**这一腿探测的是与 P1a 不同的东西**：staged 载体是 **production 渲染产物**，13 项 translated
携带 ~250 字的紧凑 `codex_discovery_summary`，而 P1a 探测的是 712–1521 字的 raw description
（其中 12 项被 1024 预算截断）。corpus 与模型完全相同，因此差异可归因到载体。

**Observation 分布（108 行 = 18 capability × 正/负 × 3 run）**：

| | TRIGGERED_TARGET | TRIGGERED_OTHER | NOT_TRIGGERED |
|---|---:|---:|---:|
| **P1b** positive（54） | **53** | 0 | 1 |
| **P1b** near-negative（54） | 20 | 17 | 17 |
| P1a positive（54） | 54 | 0 | 0 |
| P1a near-negative（54） | 18 | 15 | 21 |

- **正向隐式触发 53/54**；按 capability 看 **17/18 是 3/3**，byte-copy 5/5 全 3/3，
  translated 12/13 全 3/3。
- **唯一的未触发行与唯一的 `EXEC_TIMEOUT` 是同一行**（`mj-agent-flow-scope-drift--positive`
  run 2，180 s 截止被 kill）。该 capability 的另外两次正向 run 均为 TRIGGERED_TARGET。因此
  这一行是**被截断的观察，不是「模型没有选中该 carrier」的证据**——诚实口径是「不确定」，
  不计为触发，也不据此声称紧凑 summary 降低了发现率。
- near-negative 侧 P1b 比 P1a 略"更爱触发"（TARGET 20 vs 18、OTHER 17 vs 15、
  NOT 17 vs 21）。样本量下这类个位数差异不足以支撑任何结论，仅作记录。

**结构性纪律（schema 即约束，机器断言）**：

- **AC-09 结构性成立**：`model-telemetry-v1` 顶层键中**没有 `verdict`**（实测 `"verdict" not in doc`）；
  两份 JSON 互不聚合，telemetry 的任何结果都无法改变 §2 的 deterministic verdict。
- observation 的键恰为 `capability_id,prompt_id,run_index,observed_class,warning_codes`，
  按该三元组排序，`run_index ∈ {1,2,3}` 且每对恰 3 行——**无 transcript、无 Secrets、
  无 chain-of-thought、prompt 正文不入库**（实测断言）。
- `temperature` / `seed` / `reasoning_effort` 运行时未公开可固定 → JSON `null`（不猜默认值）。

**这一腿证明了什么、没证明什么**：它是**观察**，不是保证。它显示在这份固定 corpus、这个模型、
这个 codex build 下，把 13 项 translated 的发现面从「被截断的长描述」换成「~250 字紧凑
summary」后，正向触发没有出现可观测的退化（53/54，唯一缺口可归因于超时）。它**不**证明
语义等价、不证明其他 prompt 分布下同样成立、也不构成 cutover 后的行为保证。

## 4b. Stage 11 对抗性自评审记录

规模按 Owner 指示压缩到一次可跑完的量级：**3 finder 镜头**（verdict 完整性 / 渲染保真 /
evidence 诚实性）→ 去重 → **每 finding 2 refuter**（code-reading 与 contract-and-plan 两个
不同角度）。计划 23 agents，**22 完成 / 1 失败**。

**覆盖缺口如实披露（两处，均非「已验证」）**：

1. `refute:1:contract-and-plan` 因 API 安全过滤报错中断 → 该 finding（P1B-VERDICT-02，
   renderer identity 覆盖面）只得到 **1/1** 而非 2/2 独立验证。其同族发现 P1B-02 由另一对
   refuter 独立复核（1/2），两者指向同一缺陷，已修复。
2. 去重后 15 项按严重度取前 **10** 进入 refutation，**5 项未经 refuter 验证**（见下表）。
   本文作者已逐条自查，其中 **4 项判定为真、已修**，1 项判定为措辞澄清、已改。

**结果：15 raw → 15 去重 → 10 验证（6 survive / 4 refuted）+ 5 未验证。**

| # | 严重度 | 判定 | 处置 |
|---|---|---|---|
| `candidate_manifest_violations` 用 `v.capability`，production `Violation` 的字段是 `capability_id` | HIGH | **6/6 确认**（3 个镜头各自独立发现，各 2 refuter 全确认） | **已修**。原代码使 det-11 的 FAIL 分支不可达：genexp 先过滤 severity，f-string 只在「确有 error 级违规」时求值 → `AttributeError` 逃出 `run_deterministic`，**不写任何 evidence 文件**就 traceback 退出。原负控把格式化好的字符串直接塞进 `CandidateRender`，从未调用被测函数，因此对此完全盲。已改 `capability_id` + 新增直接驱动真实函数的负控 + 把渲染失败收敛成 `det-18-candidate-render` / `ERROR` / `CANDIDATE_RENDER_FAILED` 并仍写出 evidence |
| det-12 只钉 3 个声明了 `RENDERER_VERSION` 的模块，编排层 `agents_sync` 未钉 | HIGH | 1/1 确认（另一同族 1/2） | **已修**。det-12 覆盖面 3 → **7 个模块**（含 `agents_sync` / `projection_loader` / `check_agents_projection` / `check_development_agent`）。修复后 `candidate_set_sha256` 不变（`54235bb5…`），证明这次改动只增加了背书面、未触及渲染字节 |
| evidence 把 telemetry 说成已交付、并引用其中的观察 | MEDIUM | 2/2 确认（窄化版） | **已修**。§4 现载入真实结果；F-P1b-4 的 MCP 观察改为显式标注「非 tracked、不可从入库工件复算、不作证据」 |
| 候选 manifest 只钉 ID 分区，`workflow_id` 等字段无人验证 | HIGH | **0/2（驳回）** | 接受驳回：`load_workflow_registry` 对重复 `capability_id` 是 fail-closed 的，所述触发路径不存在 |
| telemetry 腿未跑/非交付 | HIGH ×2 | **0/2（驳回）** | 接受驳回：评审期该腿正在执行；且 §5.1.1 的 P1b 必需证据只有 deterministic/canary |
| verdict token 无法区分 P1a/P1b run | MEDIUM | **0/2（驳回）** | 接受驳回：`repo_head` 是 §2.8.6 顶层键且两份不同 |
| 「19 300 → 7 523」把全 18 的总量说成 13 项 translated 的成果 | MEDIUM | 未验证（cap 外） | 自查判定**为真，已修**：translated 口径是 14 660 → 3 262；差额 379 字符来自 `83fe8e6` 的 source 缩短，已在正文分开归因 |
| 「C1 语义等价 ⇒ 同 digest」所列 manifest 输入不准确 | MEDIUM | 未验证（cap 外） | 自查判定**为真，已修**：改为逐通路表（carrier 分区 / README 计数 / mcp+posture），并说明 lock slice 不是本单元口径 |
| det-12 只遍历 observed，模块掉出则零 case | LOW | 未验证（cap 外） | 自查判定**为真，已修**：改为 observed ∪ expected，新增 `RENDERER_MODULE_ABSENT` 与负控 |
| det-14 在同一解释器内渲染两次，测不到跨进程不确定性 | LOW | 未验证（cap 外） | 自查判定**为真但已被覆盖**：fixture 由 `emit-fixtures` 在**另一个进程**产出，det-13 拿本进程渲染结果与之逐字节比对——跨进程确定性由 det-13 承担，det-14 只加同进程重入这一层。已在 §6 明确 det-14 的边界 |
| 把 P1a 描述为 `PASS_CANDIDATE` | LOW | 未验证（cap 外） | 自查判定为**措辞澄清**：`PASS_CANDIDATE` 是 §5.1 的 unit 级标签，P1a 的 JSON `verdict` 字段确实是 `PASS`（§2.8.6 闭合枚举无 `PASS_CANDIDATE`）。摘要已加「unit 级标签」限定 |

修复轮后复验：offline 全量 **1310 passed / 16 skipped**，ruff / compileall / mypy 干净，
V8–V11 0E/0W，`sync` = up to date，`task0 --check` CLEAN，deterministic 重跑
**103 cases 全 PASS**。

## 5. Rollback / repair（§5.1.1）与 F9 交接

新 evidence correction PR；**不得改 production renderer**，也不得把 telemetry 升格为 verdict。
deterministic 若在未来复跑中出现 FAIL/ERROR/BLOCKED_PREREQUISITE，按 §5.6 停在 PR-C0 之前。

**F9（`raw-bytes-v1` 与 `* text=auto` 的交互）在本单元已从「可能」变为「实测」**，且本单元的
选择对它有约束力：P1b 发布的 byte-copy 候选 digest 是 **LF/blob 口径**。因此 PR-C1 落真实
v2 lock 前的二选一裁定仍然必须做，且两个选项现在有了明确后果：

- **选项 A —— `.gitattributes` 为这些路径钉 `eol=lf`**：C1 在任何 checkout 上读工作区字节
  都得到 LF，与 P1b/C0 的候选 digest 一致；代价是新增 `.gitattributes` 规则面。
- **选项 B —— 把 `raw-bytes-v1` 的定义改为按 git blob 字节**：与 P1b 的取字节方式一致，
  且与 renderer module digest 已采用的 LF-归一口径同构；代价是改 lock 语义（`declared-contract-change`）。
- **不裁定的后果**：C1 若在 Windows checkout 上按现行实现生成 lock，5 个 byte-copy entry 的
  `output_sha256` 会同时与 P1b 候选 digest、与仓内已提交的 `.agents` artifact 不一致
  （本节 F-P1b-3 已量化），而 Linux CI 复算又是另一个值。

## 6. 与后续 unit 的接口

- **PR-C0（fidelity attestation）**：`candidate_set_sha256`
  `54235bb5a1f149dc…` 与逐路径 digest 即「review 前就存在的 candidate digest」（§5.7）。
  候选字节未入库是刻意的——用同一 producer 在 `36f298a` 上重跑 `--unit p1b` 即可逐字节复现
  （det-14 已实测渲染确定性）。C0 的 13-way partition 可直接取 fixture 的 `carrier_partition`。
- **PR-C1（cutover）**：真实 v2 manifest 只要与本单元的候选**语义等价**，就必须复现同一批
  digest；否则说明 C1 引入了本单元未覆盖的语义变更。C1 前须先裁定 F9（§5）。
- **本单元明确未证明的事**（per §1.3 assurance 分层 / §1.4 诚实状态纪律）：
  - 未证明真实树已携带这些 carrier —— 真实树仍是 v1，v2 引擎仍 dormant，`.agents/**` 零变更；
  - 未证明翻译的**语义保真**——digest 只证 reproducibility，fidelity 走 §2.7/§5.7 的人工分层复核（PR-C0）；
  - 未证明「所有工程师机器 / 所有未来 codex 版本」恒成立——证据锚定在 codex-cli 0.147.0
    与本机 actual-user-layer；
  - 未证明 cutover 后的 MCP/config 路由——det-08 走的是专门 canary，渲染出的
    `.codex/config.toml` 只做了逐字节比对（det-13），未在探测项目中生效（F-P1b-4）；
  - telemetry 的分布是**观察数据**，不参与任何 verdict（§4），也不外推为保证；
  - det-14 只证明**同一进程内**重入渲染字节相同。跨进程确定性由 det-13 承担——fixture 由
    `emit-fixtures` 在另一个进程写出，deterministic run 在本进程重新渲染后与之逐字节比对；
    两者合起来仍不覆盖「跨 OS / 跨 Python 版本」的渲染一致性，那要等 C1 的 CI 实跑。
