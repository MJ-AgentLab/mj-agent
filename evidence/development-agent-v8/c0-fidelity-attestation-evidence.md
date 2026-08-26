---
type: evidence
summary: >-
  Epic #499 PR-C0 fidelity attestation —— 具名 producer
  `scripts/sdd/build_fidelity_attestations.py` 在 PR-P1b 冻结的候选 commit
  `36f298a9995f` 上重渲候选 carrier（20/20 digest 逐字节复现 PR-P1b 发布值），
  由 renderer 机器生成 13 份 coverage report（**617 items**），并经**独立
  checker** `check_fidelity_attestations.py` 做 exact inventory closure ——
  **13/13 capability 逐 kind 精确闭合**。13 项 translated 由 **4 个 tranche
  恰好分区**（3/3/3/4，item 159/184/135/139），每 tranche 的 8 个 digest
  （7 个按 §2.7 set-digest wire，`preface_sha256` 为单文件 raw blob digest）
  计算并发布。**approval_binding 尚未落盘**：`verdict` 闭合枚举
  只有 `approved|rejected`（无 pending 态），具名 reviewer 评审尚未执行，
  故本单元按 §1.4 诚实状态纪律记为 **BLOCKED_PREREQUISITE**，AC-10 未达成。
owner: ranzuozhou
created: 2026-08-26
updated: 2026-08-26
state: active
track: agent
---

# Fidelity Attestation — Epic #499 (PR-C0)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §2.7 第 9 条（coverage 由 renderer
> 机器生成 → 独立 checker 做 exact inventory closure → 具名 reviewer 确认并创建 immutable
> approval record）与 §2.8.5（fidelity schemas and binding）。Delivery unit = **PR-C0**，
> AC = **AC-10**，merge condition = **all 13 approved + exact partition**（§5.1 row 10）。
> approval = immutable reviewer approvals，**author 不得自签**；rollback = C1 前补/重做
> review binding（§5.1.1）。

## 0. 入场锚点与 Owner 拍板记录

| 项 | 值 |
|---|---|
| 候选 revision（冻结面） | `36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f`（= PR-B merge commit；**不是**当前 develop head，`--rev` 显式钉定） |
| 前序 unit | PR-P1b = [#515](https://github.com/MJ-AgentLab/mj-agent/pull/515)，MERGED `2026-08-26T05:46:09Z`（head `af8cbf943615`，merge `02caf3eac8d4`） |
| 前序 Stage 17 ledger | [#499 comment 5421191708](https://github.com/MJ-AgentLab/mj-agent/issues/499#issuecomment-5421191708)，body SHA-256 `f5328e1f6736ca14d58349d4f9dc45799a0a8b67403197bcd029e2149e286a73`（17 463 B，纯 LF，逐字节复算吻合；18 records 全终态，治理事实 6 条 + 新 runtime 事实 3 条精读） |
| 本 unit branch | `documentation/499-fidelity-attestation`，`git worktree add` 自 `02caf3e`（G1） |
| Task-0 preflight | `task0_freeze --check` = `TASK0_FREEZE_CLEAN`，identity `8c7c1e4847b8c5efe843009fd4d6c2b357488325f1f67ca2e1ec409546cce443` 不变（58 hard + 1 controlled；本单元变更集全在冻结面外） |
| merge condition 前置 | PR-P1b 的 deterministic `verdict = PASS`（103/103）已解锁 C0（§5.6：P1a 的 `PASS_CANDIDATE` 不足） |

**Owner 拍板（Gate 1，实施前一次呈清四问，四项均取推荐方案）**：

1. **评审者与 record 载体 = 第三方 collaborator + GitHub PR review**。由 `ranzuozhou`
   以外的具名 collaborator 在本 PR 上逐 tranche 提交 review；GitHub 结构性禁止自批，
   因此「author 不得自签」有机器级证据而非仅靠声明。`record_system` =
   `github-pull-request-review`，`immutable_record_id` = review id。
2. **tranche 分区 = 4 个，按 HITL 阶段族**（3/3/3/4）。每个 tranche 是一次语义连贯的评审
   坐次；4 条独立 record 让「补/重做某一个 tranche 的 binding」（§5.7 rollback）代价最小。
3. **`renderer_set_sha256` = det-12 的 7 个模块**。PR-P1b Stage 11 判例：只钉声明了
   `RENDERER_VERSION` 的 3 个模块时，未提交的编排层（`agents_sync`）改动会同时污染
   fixture 与 run，使全部 exact-byte case「drifted vs drifted」一致通过。7 个才封得住。
4. **PR 结构 = 单 PR 两阶段**。commit 1 落机器面 → 评审在本 PR 上进行 → commit 2 补
   index 与 record ID。这解开了「record ID 只有评审后才存在、却要写进被评审的 PR」的
   循环；若评审最终未到位，PR 停在 commit 1 + `BLOCKED_PREREQUISITE`，机器面成果不浪费。

## 1. 交付面

| 文件 | 变更 | 角色 |
|---|---|---|
| `scripts/sdd/build_fidelity_attestations.py` | 新增 | 具名 producer：`build-coverage` / `build-packet` / `build-index` |
| `evidence/development-agent-v8/fidelity/coverage/<capability-id>.json` × 13 | 新增 | renderer 机器生成的 coverage report（§2.8.5 coverage v1） |
| `evidence/development-agent-v8/fidelity/review-packet/<tranche-id>.md` × 4 | 新增 | 具名 reviewer 的评审材料（trigger judgment + 待抄录 digest） |
| `tests/unit/test_fidelity_attestations_c0.py` | 新增 | 26 条契约测试（closure / binding / partition / producer 负控），**全部不依赖 git 历史** |
| 本文件 | 新增 | tracked 证据摘要 |
| `sdd/adapters/codex-skill-fidelity.yml` | **尚未创建** | 签署索引；**须待真实 reviewer record 存在后**由 `build-index --bindings` 生成（见 §4） |

**零变更面（实测复认）**：`.claude/**`、`.agents/**`、`.codex/**`、`.agents.lock.json`、
`.mcp.json`、`sdd/development-agent.yml`、全部 typed sources 与 7 个 renderer/编排模块
**均未改动**。合并前实测 `agents_sync.py --check --surface {skills,mcp,all}` 全 `in sync`，
V8/V9 `--all --fail-on warning` = 0E/0W，`task0_freeze --check` = CLEAN。
**真实树仍是 manifest v1 + legacy v1 flat lock，v2 引擎依旧 dormant** —— 本单元只做
attestation，cutover 是 PR-C1。

**`documentation/*` 分支携带 `.py`**：按 PR-0d `dc05c36` / PR-P1a 先例，commit type 仍取
`docs`（STANDARD §5.2：`documentation/*` 仅允许 `docs`），并在 commit body 与 PR body 据实
声明携带脚本与测试。`check_commit_messages` 不校验分支 × 类型矩阵，此声明是人工兜底。

## 2. Coverage 生成与独立 closure（§2.7 第 9 条）

### 2.1 候选重渲：20/20 逐字节复现

producer 先用 PR-P1b 的 `build_candidate_render(repo_root, rev, work_dir)`（**equivalent
reuse**，owner = PR-P1b，interface 与 tests 按 §3.3 记录于此）从 **git blob 字节**物化渲染
输入并渲染两次，然后与仓内 tracked fixture 逐路径比对：

| 检查 | 结果 |
|---|---|
| 二次渲染字节相同（`deterministic`） | `True` |
| `candidate_manifest_violations` | `[]` |
| 逐路径 digest vs `p1b-deterministic-expected.json` | **20/20 相同** |
| `candidate_set_sha256` 复算 | `54235bb5a1f149dc743907e72a2a4bf720eac529f4075f250ce4a07851b5444a` = 发布值 |

任一不符即 `exit 2` 并零写 —— 候选 digest 是评审对象，不允许静默重锚。以非 `36f298a` 的
`--rev` 调用同样 `exit 2`（实测）。

### 2.2 独立 closure：13/13 逐 kind 精确闭合

coverage 由 renderer 的 `skill_renderer.generate_coverage()` **机器生成**；判定由
`scripts/sdd/check_fidelity_attestations.py` 承担 —— 它**不 import** 该生成器，而是从
source / frontmatter / workflow registry 用自己那套（刻意重复的）抽取规则重新派生 inventory，
再要求 report 对该 inventory **exact set closure**（漏项与多项同样报红）。

**这条 closure 到底证明了什么，需要精确说**：checker 比对的是**逐 item_kind 的条目数**，
不是逐 item 的内容匹配。它能抓住「renderer 与它自己的 report 同时漏掉某个 heading/stop/route」
（这正是 §2.7 规定的负控），也能抓住凭空多出的条目；它**不**验证某个 item 的 artifact 切片
在语义上忠实于 source —— 那是人工分层复核的职责（§1.3：digest 只证 reproducibility）。

**13/13 capability 的逐 kind 计数完全相等**，共 **617 items**：

| item_kind | 计数 |
|---|---:|
| `heading` | 251 |
| `prohibition` | 147 |
| `validator` | 61 |
| `level-handler` | 51 |
| `owner-stop` | 51 |
| `dependency-route` | 34 |
| `frontmatter-description` | 13 |
| `issue-route` | 6 |
| `git-rule` | 3 |
| **合计** | **617** |

`status` 全部为 `COVERED`（无 `INTENTIONALLY_NOOP`）；`transform_class` 落在 `NOOP` /
`T2a` / `T2b`。**缺失不以 status 表达** —— generate_coverage 在任一 inventory item 找不到
artifact 覆盖时直接 `TranslationError`，独立 checker 则以 closure 失败报红。

**617 项的完整归账**（Stage 11 促成；四类互斥且求和恰为 617）：

| 类别 | 数量 | 含义 |
|---|---:|---|
| 逐字节相同 | **548** | source 与 artifact digest 相等 —— 不可能改变语义，仅凭仓内 source 即可核验 |
| 仅缩进差异 | **19** | `transform_class = NOOP` 但 digest 不等，实测**全部**可由「report 取 raw source 行、artifact 取 stripped 切片」解释（逐项验证 `sha256(line.strip()) == artifact_sha256`） |
| description 替换 | **13** | frontmatter description → discovery summary，即 §2.7 要求的 trigger judgment 本身 |
| 声明的转换 | **37** | `T2a` 36 + `T2b` 1 —— 跨 skill 引用改写为 Codex carrier 路径 / edge-route 标记 |

这张表把 reviewer 的正文抽查面从「617 项」收敛到 **37 项**，其余三类各自有独立的、
不依赖候选字节的核验路径。**判据是 `transform_class`，不是 digest 是否相等** —— 后者会把
19 项纯缩进差异误报成「被转换」（本单元 Stage 11 自己踩过这个坑，已由测试钉住）。

### 2.3 digest 一律取 git blob，不读工作区

本机 checkout 在 `* text=auto` 下是 CRLF。实测：13/13 translated source 的**工作区字节
digest 与 blob digest 全不同**。因此 producer 的每一个入库 digest 都取 blob（或渲染内存
字节）。两点实测补充：

- `generate_coverage` 的 **source 侧对 EOL 免疫**（内部 `\r\n → \n` 归一）：blob 与工作区
  两种输入产出**逐字段相同**的 report（0/13 差异）。所以 source digest 恰好两条路殊途同归。
- **artifact 侧对 EOL 敏感**：把候选文本 CRLF 化后 `artifact_sha256` 立刻改变。候选字节
  只来自渲染内存（实测 0 个候选产物含 CRLF），从不读磁盘。
- 由此确认 **F9 不影响 C0 的 binding**：C0 的 4 个 tranche（13 项 translated）只覆盖 translated，其 render
  内部已 LF 归一；F9 的争点是 byte-copy 的 `raw-bytes-v1` 与 checkout EOL 的交互，**C1 前
  仍必须裁定**。

## 3. Tranche 分区与 set digest 口径（C1 复现锚点）

### 3.1 4-way exact partition

| tranche_id | capability_ids | items |
|---|---|---:|
| `tranche-1-flow-entry` | `mj-agent-flow-intake` / `mj-agent-flow-repo-scan` / `mj-agent-flow-plan` | 159 |
| `tranche-2-flow-build` | `mj-agent-flow-implement` / `mj-agent-flow-verify` / `mj-agent-flow-self-review` | 184 |
| `tranche-3-flow-close` | `mj-agent-flow-scope-drift` / `mj-agent-flow-review-respond` / `mj-agent-flow-post-merge` | 135 |
| `tranche-4-doc-git` | `mj-agent-doc-validate` / `mj-agent-git-branch` / `mj-agent-git-issue` / `mj-agent-git-pr` | 139 |

无遗漏、无重叠，合计 13 capability / 617 items。

「哪 13 项」这条断言用**四个互相独立的口径**复扫，**四者集合完全相同**（实测）：

| 口径 | 来源 | 计数 |
|---|---|---:|
| 规范矩阵 | plan §2.2.1 终态 18-carrier 表中 `codex_carrier = translated` 的行 | 13 |
| 上游证据 | PR-P1b fixture 的 `carrier_partition.translated` | 13 |
| 运行时派生 | workflow registry `workflows` 列表中各记录的 `capability_id` 取值集合（该键在 YAML 里是 list，不是 mapping；记录的 `workflow_id` 刻意不等于 capability id） | 13 |
| 本单元声明 | producer 的 `TRANCHES` 常量展开 | 13 |

同时实测 byte-copy 侧 plan 与 fixture 同为 5 项，且 **translated ∩ byte-copy = ∅**。
（复扫脚本对「plan 口径解析出空集」显式断言 —— 空集会与任何集合「一致」，是这类穷尽性
断言最常见的假阴性来源。）

### 3.2 8 个 digest 的 declared 组成

wire 固定为 §2.7 的 set digest：normalized repo-relative path 按 code point 排序，构造
closed canonical JSON object `path → raw_sha256`，再对其 canonical UTF-8 字节求 SHA-256。
该 wire 由 `test_set_digest_wire_reproduces_the_published_candidate_set` **对已发布值钉住**
（用它重算 PR-P1b 的 20 项 `candidate_output_sha256` 必须落在 `candidate_set_sha256` 上）。

**tranche-scoped**（成员随 tranche 变）：

| 字段 | 组成 | tranche-1 | tranche-2 | tranche-3 | tranche-4 |
|---|---|---|---|---|---|
| `source_set_sha256` | 成员的 `.claude/skills/<id>/SKILL.md` blob | `3abcc076…1595` | `f2a4ef57…92e3` | `8df53f38…9c81` | `68d44de1…d9f9` |
| `artifact_set_sha256` | 成员的 `.agents/skills/<id>/SKILL.md` 候选渲染字节 | `173e45cf…eacc` | `363a1bfb…0a23` | `283f1cf5…0441` | `543c6789…39d7` |
| `coverage_set_sha256` | 成员的 `evidence/.../coverage/<id>.json` 入库字节 | `77814ae0…a321` | `0927fbaf…472f` | `f89c8ac9…71e7` | `fff69dc0…4a4f` |

**whole-input**（四个 tranche 相同 —— 它们是同一批渲染输入，实测 `identical=True`）：

| 字段 | 组成 | 值 |
|---|---|---|
| `manifest_set_sha256` | `sdd/development-agent.yml` | `2fe7d95445b343eaeb90aaa3d40c77b465652ca37ab40c08d925a11dfc822f36` |
| `translation_set_sha256` | `sdd/adapters/codex-skill-translation.yml` | `285be8ce904b1eea1e859826df1c00c6952137e964a970f21834093c8af91e6c` |
| `workflow_set_sha256` | `sdd/workflows/development-agent-workflows.yml` | `a322e13a2925c6bf150139c64c2e7de40de7ea0f7d3a285aae31b5fcf6a18d19` |
| `preface_sha256` | `sdd/adapters/codex-skill-preface.md` 的 **raw blob** digest（字段名无 `_set_`，故非 set 口径） | `f9247051a529783a12b1c61ecbf6ccfc027e1aac872a723f118db6207a496c66` |
| `renderer_set_sha256` | det-12 的 7 个模块 blob | `ca6b5da7b05a4fdc27b3546c7f7a1a9ae40303c7659e2448a42f8ac6265a102e` |

**PR-C1 必须复现上表**（§5.7：C1 只需复现相同 digests，不要求 record 绑定 C1 HEAD）。
若 C1 合法地改动了 `mcp` / `codex.posture` 等 D-017 停面，`manifest_set` 会随之变化，
届时应当**重走 C0 binding**，而不是把差异当成 C1 的实现缺陷。

## 4. Approval binding —— 状态：`BLOCKED_PREREQUISITE`

`approval_binding` 的 `verdict` 是闭合枚举 `approved | rejected`，**没有 pending 态**。
索引一旦落盘，就是在断言评审已经发生。截至本文件写入时，Gate 1 指定的具名 reviewer
**尚未执行评审**，因此：

```text
APPROVAL_STATE = BLOCKED_PREREQUISITE
```

按 §1.4 诚实状态纪律，**`BLOCKED_PREREQUISITE` 不是 `approved`**，也不是 `rejected`：
它意味着评审这一步**未被执行**，而非已确认合格。任何后续消费方不得把它读作已签署。

机器侧对此的强制：`build_fidelity_attestations.py build-index` 在缺少 `--bindings` 时
**`exit 2` 且该路径实测零写**，错误码即 `BLOCKED_PREREQUISITE`。

**这条强制的边界必须说清楚**（否则就成了 §1.3 禁止的那类过度断言）：producer 能做到的是
**拒绝默认出一个 verdict**、**拒绝绑定到与本树不符的 `reviewed_*`**；它**不能**判断一条
record 是否真的出自 reviewer 之手 —— 一个执意造假的作者手写一份 bindings 文件即可通过全部
机器检查。所以「author 不得自签」最终**不是**由机器保证的，而是由两件事承担：(1) Gate 1 选定
的载体是 GitHub PR review，**GitHub 结构性禁止自批**；(2) §2.7 要求 Owner 在 gate 上亲自打开
外部 immutable record 核对 reviewer 与 verdict。机器只负责让「诚实的疏忽」不可能发生，
不负责让「蓄意造假」不可能发生。

### 4.1 评审如何进行（4 步，每 tranche 一遍）

1. reviewer 打开 `evidence/development-agent-v8/fidelity/review-packet/<tranche-id>.md`：
   内含该 tranche 每个 capability 的 **Claude 侧 source `description`** 与 **Codex 侧渲染出的
   `codex_discovery_summary`** 并排全文、coverage 逐 kind 计数、三个待抄录 digest。
2. 做 §2.7 要求的**两项判断**：per-capability **trigger judgment**（summary 是否既未放宽
   也未收窄触发语义）＋ **正文 fidelity 抽查**（§2.7 明言「抽查」，不做无辅助全文对读）。
3. reviewer 在本 PR 上提交 review，正文写明逐项 trigger judgment 与结论；review id 即
   `immutable_record_id`。
4. 作者把 reviewer 给出的 **8 个字段原样**填入 bindings 文件，跑
   `build-index --bindings <file>`。producer 会校验 record 的 `reviewed_candidate_commit_sha`
   / `reviewed_source_set_sha256` / `reviewed_artifact_set_sha256` **等于本树计算出的值**，
   不等即 `exit 2` —— 针对旧输入做的评审无法被静默改绑到新 digest 上。

bindings 文件是**一次性输入，不入库**（它只是把外部 record 搬运进来的载体）。形状 = 4 条
记录的 JSON 列表，每条 = `tranche_id` + §2.8.5 的 8 个 exact key：

```json
[
  {
    "tranche_id": "tranche-1-flow-entry",
    "record_system": "github-pull-request-review",
    "immutable_record_id": "<review id from gh api .../pulls/<N>/reviews>",
    "reviewer_identity": "<reviewer github login, 不得是 author>",
    "verdict": "approved",
    "reviewed_candidate_commit_sha": "36f298a9995fd3b7c0dd9ad7d4f9d4fec233422f",
    "reviewed_source_set_sha256": "3abcc076e932fac7be3150993b1a568ff9f7a09938f2458b2ec6a51e0e4e1595",
    "reviewed_artifact_set_sha256": "173e45cf5c293a2795ecc56f822eec8e4218795355484605d844921ec30feacc",
    "recorded_at": "<review submitted_at, RFC3339 Z>"
  }
]
```

多一个键、少一个键、`verdict` 取枚举外的值（含 `pending`）、`immutable_record_id` 重复、
或任一 tranche 缺 record，都是 `exit 2` 零写（各配负控，见 §5）。

### 4.2 Dry run：机器面已完备，缺口精确地只是「真实 record」

为了把「还差什么」量化到可核验，在**临时树**里做过一次 end-to-end dry run（**未向仓内
写入任何文件**，实测复认 `sdd/adapters/codex-skill-fidelity.yml` 在仓内仍不存在）：用本树
真实计算出的 8 个 digest 组装 4 条 binding（`reviewer_identity` 显式写成
`DRYRUN-NOT-A-REAL-REVIEWER`），生成完整 index，连同真实 source / registry / **仓内已提交的
13 份 coverage report** 一起交给独立 checker：

| 项 | 结果 |
|---|---|
| 仓内 coverage 与重新生成的字节比对 | **零漂移**（13/13 相同） |
| `check_fidelity_attestations --all`（dry-run 树） | **`rc = 0`**，errors: 0 |
| index | 4 tranches / 13 translated / 4 approved |

结论：**closure、分区、schema、digest binding 全部已经就位**；C0 未闭环的原因**不是**机器面
有缺口，而是 §4 那一条 —— 具名 reviewer 尚未评审。这也正是本 dry run 只能在临时树进行、
其 binding 绝不可入库的原因：它的 verdict 是假的。

### 4.3 独立 checker 的能力边界（不是缺陷，是分工）

`check_fidelity_attestations.py` 只验证**结构、唯一性与枚举**：exact top/tranche/binding
keys、3–4 个 tranche 的精确分区、`verdict` 闭合枚举、`immutable_record_id` 全局唯一。
它**不能凭文件内容认证人类身份**，也**不校验** `reviewed_*` 是否等于同 tranche 的
digest —— 后者由本单元的 producer 在生成时把关（`test_build_index_refuses_a_record_reviewed
_against_other_inputs` 三个参数化负控钉住）。「签署真实」最终由 PR-C0/PR-C1 Owner gate
打开具名 review provider 的 immutable record 核对来承担（§2.7）。

## 5. 验证结果

| 项 | 结果 |
|---|---|
| offline 全量 | **1343 passed / 16 skipped / 82 deselected**（PR-P1b 基线 1310 → +33，即本单元新增测试数） |
| 本单元测试 | **33 passed**：digest wire 3 / coverage 与 binding 7 / 独立 closure 3 / reviewer packet 4 / partition 1 / producer approval 15。其中 **16 条是负控**（漂移、漏项、多项、缺 record、4 个非枚举 verdict、重用 record id、非 exact keys、3 个 `reviewed_*` 不匹配、frontmatter 不可解析、2 个 `--check` 越界模式），每条都驱动被测函数的真实入口 |
| `ruff check` | All checks passed |
| `mypy src/mj_agent`（strict） | Success: no issues found in 48 source files |
| `compileall` | 干净 |
| V8 `check_development_agent --all` | 0E / 0W / 0I |
| V9 `check_agents_projection --all --fail-on warning` | 0E / 0W / 0I |
| V10/V11 `agents_sync --check --surface {skills,mcp,all}` | 全部 `in sync`，lock consistent |
| `task0_freeze --check` | `TASK0_FREEZE_CLEAN` @ `8c7c1e48…`（未重锚） |
| `check_fidelity_attestations --all`（真实树） | `exit 2` —— index 尚未创建，这是**设计中的 dormant 行为**（脚本 docstring 明载），不是失败 |
| `check_frontmatter` | `OK: 138 canonical docs`（与变更前同值）。**注意**：`SCAN_ROOTS` = `docs/` `plans/` `decisions/` `src/mj_agent/{skills,prompts}`，**不含 `evidence/`** —— 本文件的 frontmatter **不在该 gate 覆盖内**，系照 `p1a`/`p1b` 同目录既有约定（`type: evidence` / `track: agent` / 6 字段）**人工核验**。别把 138 读成「本文件已被校验」 |
| `check_wikilinks` | 0 unresolved（A4 目标解析只覆盖 5 个根文件）。本文件自身无相对链接；4 份 review packet 共 13 条 `../coverage/<id>.json` 相对链接在 gate 外，已逐条脚本核验 **13/13 指向真实文件** |
| producer 负路径 | 缺 `--bindings` → `exit 2`；错 `--rev` → `exit 2`；`build-coverage --check` → `rc=0` 零漂移 |

## 5b. Stage 11 对抗性自评审记录

**方法**：对抗性 refutation workflow，规模按既定指示压到一次可跑完 —— **3 finder 镜头
（contract / code / honesty）→ 21 findings（去重后 21）→ 按严重度取前 8 进 refutation，
每 finding 2 refuter（code-reading / contract-and-plan 两角度）**。计划 19 agents，
**19 全部完成，0 失败**（与 PR-P1b 的 22/23 不同，本轮无 API 过滤中断）。

**覆盖缺口如实披露**：去重后 **13 项未经 refuter 验证**（cap 之外）。作者逐条自查，
其中 **9 项判定为真并在本 PR 内修复**、**1 项判定为真但保留**（见下）、3 项为已在别处
覆盖的重复描述。1 survive / 7 refuted 之外的这 13 项**不是「已验证为假」，而是「未验证」**。

**结果**：1 survive（MEDIUM）、7 refuted（其中 5 项 HIGH 被 2/2 驳回）。

**本 PR 内闭合的 10 项**（含唯一 survivor）：

| # | 面 | 问题 | 处置 |
|---|---|---|---|
| 1 | producer | **survivor**：`--check` 只在 `build-coverage` 分支被读取，`build-packet` / `build-index` 忽略它并照常写盘 —— 一个 help 写着「instead of writing」的 flag 会写文件 | 越界模式直接 `parser.error`，配 2 条负控 |
| 2 | producer | `frontmatter_description` 返回 `None` 时被 `or ""` 吞掉，会发布**空的** trigger judgment 并 `exit 0`（正是 P1b「失败分支不可达」判例的同类） | 改为 `_die` 失败关闭，配正控 + 负控 |
| 3 | packet | §3 让 reviewer 跑 `emit-fixtures` —— 它会写进**仓内 tracked** 的 `probe/fixtures/`，且产出的是 digest 不是 carrier 正文，与小标题「Regenerating the candidate bytes」不符 | §3 重写为 `build-coverage --check` + 临时目录渲染单个 carrier 的配方，并显式警告不要跑 `emit-fixtures`；配负控扫描 |
| 4 | packet | 「作者**不**为你计算 `reviewed_*` digest —— 请从 §2 抄录」自相矛盾（§2 正是作者算的） | 改为据实表述：作者算并发布，reviewer 须先自行复算确认 |
| 5 | producer | `renderer_set_sha256` 复用 `renderer_identity.blob_sha256`（**LF 归一**口径），而 §2.7 wire 要求 `raw_sha256`；其余 6 项都走 raw blob | 统一走 raw blob 闭包。**实测 7/7 模块两口径同值，发布 digest 一字未变** —— 消除的是潜在分歧而非现存错误 |
| 6 | producer | `--rev` 不做规范化：正确 commit 的**缩写**会被 pin 守卫当成重锚企图拒绝 | `main` 里先 `resolve_rev` 再全程传规范值 |
| 7 | producer | `GitError` 未经 `_die`，未 fetch 的 rev 会以 traceback + exit 1 结束，违背自述的退出码契约 | 包裹为 `exit 2` |
| 8 | 测试 | `build_packet` / `tranche_digests` **零测试覆盖** —— reviewer 要签的 digest 竟未被钉住 | 新增 4 条 packet 测试，其中 digest 表**从仓内 P1b fixture 独立重算**（不经 `tranche_digests`，故 CI 浅克隆下也能跑） |
| 9 | 证据 | §4 断言「producer 没有任何路径可以合成 verdict…机器级落实」——过度断言：手写 bindings 可通过全部机器检查 | 改写为明确的能力边界（§4）：机器只防疏忽，不防蓄意；自签由 GitHub 结构性禁自批 + Owner 核验承担 |
| 10 | 证据 | 三处口径/措辞错误：「13 个 tranche」（实为 4）、frontmatter 称 8 个全是 set digest（`preface_sha256` 不是）、「workflow registry 的 `workflows` 键集」（YAML 里是 list，且 `workflow_id ≠ capability_id`） | 逐条改正 |

**判定为真但保留 1 项**：tranche 的 `capability_ids` 按 HITL 阶段序而非 code point 序输出，
与 `translated_capabilities` 的排序惯例不一致。保留理由 —— 该顺序**承载评审坐次语义**
（tranche-1 = intake→repo-scan→plan 的实际执行序），plan §2.8.5 未规定该字段顺序，
checker 亦不关心。已在 `TRANCHES` 常量处注明。

**被 2/2 驳回的 5 个 HIGH**（记录以便后续单元不重复提出）：packet 的 `emit-fixtures`
写入实测为**字节相同的 no-op**（两个 refuter 各自复算 `b4f74930…`，`git status` 保持干净，
且 fixture 并非唯一锚点 —— 20 个 digest 同时存在于不可覆盖的 P1b deterministic 结果文件里）；
`build_index` 接受 `rejected` verdict 是 schema 要求（§5.7 rollback 路径），非缺陷；
「exact set closure 夸大」被判为使用了 checker 自身的术语——但本单元仍按其精神在 §2.2
补了一段精确说明；「§1.3 禁止的零写断言」被判为 tier 混淆（§1.3 约束的是 PR-F 对
enforcement 系统的终局断言，不是对某个脚本某条路径的实测陈述）；§3.3 equivalent-reuse
记录被判已满足。**其中第 3 项的驳回理由本身部分误读了本文措辞**（refuter 称 §3「从未提供
可读字节」，而小标题当时确实写着「Regenerating the candidate bytes」）——按「refuted 不等于
已排除」的纪律，该项仍按上表第 3 行修复。

## 6. 本单元明确未证明的事（§1.3 assurance 分层）

- **未证明翻译的语义保真**。digest 只证 reproducibility；fidelity 走 §2.7/§5.7 的人工分层
  复核，而该复核**尚未执行**（§4）。
- **未证明任何人类身份**。checker 无此能力；binding 为真依赖 Owner 在 gate 上打开外部
  immutable record 核对 reviewer 与 verdict。
- **未证明真实树已携带这些 carrier**。真实树仍 v1，`.agents/**` 零变更，13 个
  `artifact_path` 指向的文件在本单元结束时**尚不存在**——它们绑定的是候选 commit 的渲染
  产物，C1 cutover 时才写入。
- **未证明跨 OS / 跨 Python 版本的渲染一致性**。本单元的复现实测只发生在本机；`ci.yml`
  是 shallow checkout，无法在 CI 内按 `36f298a` 重渲，故所有测试改为绑定仓内 tracked
  fixture（见 §5）。跨平台一致性要等 C1 的 CI 实跑。

## 7. AC 对位

| AC | 陈述 | 本 unit 的满足方式 |
|---|---|---|
| **AC-10** | fidelity inventory exact closure and immutable **approved** binding cover all 13 translated carriers | **前半达成**：13/13 exact closure 由独立 checker 实测（§2.2），4-way exact partition（§3.1）。**后半未达成**：approved binding 尚不存在，记 `BLOCKED_PREREQUISITE`（§4）。**故 AC-10 整体未达成，C0 未闭环。** |

## 8. 与后续 unit 的接口

- **PR-C1（cutover）**：§3.2 的 8 个 digest 是 C1 的复现锚点；C1 写出的真实 v2 产物必须
  重现 `artifact_set_sha256`，否则说明引入了本单元未覆盖的语义变更。**C1 的入场前置是
  C0 闭环**（all 13 approved），当前未满足。C1 前还须裁定 **F9**。
- **本单元遗留**：`sdd/adapters/codex-skill-fidelity.yml` 未创建；4 条 reviewer record
  未产生。补齐路径见 §4.1，无需重跑 coverage（`build-coverage --check` 可验证零漂移）。

### 8.1 为什么 `check_fidelity_attestations.py` 本单元**不**挂 CI（刻意）

三条理由，任一单独成立即足以推迟：

1. **挂上就红**。index 尚未创建，checker 对此返回 `exit 2`（「dormant until PR-C0」是它
   docstring 里明写的行为）。在 index 落盘前挂 CI 会把一个诚实的 BLOCKED 状态伪装成构建故障。
2. **新增 CI gate 是治理动作**，不是实现细节。CI 里的 V1–V11 每一格都有独立的挂载与
   warning→blocking 记录；给 checker 分配 gate 编号并挂载，属 Owner 拍板面，不该由本单元
   顺手夹带（rule 7 / §3.3「职责不得合并」）。
3. **§6.2 明令**「No command is run before its producer/CLI lands」。C0 的 PR-C0 行只要求
   *independent fidelity inventory and approval binding*，未要求挂 gate。

→ **F11（新增 follow-up）**：index 落盘后（本 PR 的 commit 2，或 PR-C1）为
`check_fidelity_attestations.py --all` 分配 gate 编号并按既有 warning-first 惯例挂载；
挂载本身需 Owner 的 `ci-blocking-gate-toggle` 类记录。**不阻塞 C0**，但**在 C1 声称
「render/lock/fidelity closure」之前应当完成**——否则 fidelity 面在 CI 上始终无守。
