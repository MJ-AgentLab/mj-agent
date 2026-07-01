---
type: plan
summary: T-1 跨仓 cross-ref 采纳——ADR-027 增 dgx-mlops provider-contract cross-ref 段 + ADR-033 槽位填实（纯 documentation PR）；闭 dgx-mlops M7 Phase-1 出口第 3 项
owner: 项目负责人
created: 2026-06-29
updated: 2026-07-01
state: active
track: shared
---

# [PLAN] mj-agent T-1 — DGX cross-ref 采纳（ADR-027 + ADR-033）

> **Issue**：[#255](https://github.com/MJ-AgentLab/mj-agent/issues/255)（T-anchor；本 plan 关 T-1 关单项之一）
> **关联**：dgx-mlops **M7 Phase-1 closure**（roadmap M7 Phase-1 出口第 3 项「mj-agent ADR-027 已 cross-ref dgx-mlops contract ID」）。dgx-mlops 侧设计 = owner vault `sdd-development/dgx-mlops/dgx-mlops-M7-Phase1-closure-T1-cross-ref-design-2026-06-29.md`。
> **触发**：dgx-mlops bridge contract 已产实 ID（`CTR-AGENTOUT-001` / `CTR-BRIDGE-001` 自 dgx-mlops M2/M4 在位）——ADR-033 T-1 触发条件**已满足**。
> **性质**：纯 documentation PR（ADR + 配套）。**不触** 5 in-source 必停面、`src/mj_agent/llm.py`、provider factory。`/mj-agent-doc-author`（ADR 模板）+ A1-A6 doc gates + G1 worktree + G2 base develop + 17-stage HITL loop。
> **入口提示**：在 mj-agent develop 会话说「按 vault `[PLAN]_mj-agent_T1_DGX_Cross-ref_Phase1_Closure.md` 执行」，走 `/mj-agent-flow-intake → /mj-agent-flow-plan`（正式落 `plans/[PLAN]_*.md`）→ branch（G1 worktree）→ `/mj-agent-doc-author` → verify → PR。

---

## Goal / Architecture

**Goal**：在 mj-agent 仓采纳 dgx-mlops provider-side contract 的反向 cross-ref——`decisions/ADR-027` 增「Cross-ref — dgx-mlops provider contracts」段 + `decisions/ADR-033` 「Cross-ref 槽位」由占位填实，绑定 2 PRIMARY 契约（`CTR-AGENTOUT-001` + `CTR-BRIDGE-001`），状态标 **pending dgx-mlops Phase 2 integration**。落地后 = dgx-mlops M7 Phase-1 出口第 3 项闭合的 mj-agent 半边（joint，HITL-CROSS 双签）。

**Architecture**：单一 documentation PR；零 contract content mutation（仅 mj-agent ADR 增反向引用）；零 src 改动。HITL-CROSS = doc-only cross-ref → integration test 元素 = cross-contract consistency check（非 live runtime test；后者 = Phase-2 / T-5）。

## Global Constraints（每 Task 隐含）

- **不改**：`src/mj_agent/llm.py`、5 in-source 必停面（`tools/sql/guardrail.py` / `tools/sql/precheck.py` / `prompts/system.md` / `src/mj_agent/skills/*/SKILL.md` / `biz_catalog/qcm_catalog.yaml`）、6 infra-freeze skills、`capabilities/data-agent/llm-provider/`（footprint 仅 ADR-027 + ADR-033，owner 拍板）。
- **cross-ref 预算**：dgx-mlops ↔ mj-agent 文档 cross-ref 总数 **≤ 5**（ADR-033 §Decision 4 自设）。绑定面最小化（2 PRIMARY；informational 仅追溯）。**预算复核见 Task 4；溢出 → mj-agent owner 拍板，不擅自改预算**。
- **状态语义**：全程标 **pending dgx-mlops Phase 2 integration**；`pending → active` 仅 T-5（真实 e2e）。
- **HITL（ADR-034）**：documentation PR **不在** 5 必停面；AI 提议 → owner 拍板 → AI 落盘；**合并 owner-only**。
- **wikilink 风格**：`[[decisions/ADR-NNN_<stem>|ADR-NNN]]`（stem 无 `.md`）。
- **commit**：无 scope 的 `docs: …`（Commit Convention STANDARD §4.3：`docs` 不得作 scope、`decisions` 不在封闭 12-scope 白名单；本改动跨 `decisions/` + `plans/` + `CHANGELOG.md` 无主导 scope → 省略 scope）。
- **frontmatter**：被改 ADR 的 `updated:` 字段 bump 至 `2026-06-29`；其余 frontmatter schema 不变。

---

## Scope

- **In-scope**：
  - `plans/[PLAN]_255_dgx-cross-ref-t1.md`：本 plan 正文落盘物（Task 1b；随本 PR 提交）。
  - `decisions/ADR-027_LLM_Provider_Abstraction.md`：增「Cross-ref — dgx-mlops provider contracts」段（Task 2）。
  - `decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md`：「Cross-ref 槽位（T-1 填实）」段占位填实（Task 3）。
  - 两 ADR frontmatter `updated:` bump（Task 2/3）。
  - cross-ref 预算（≤5）复核 + 溢出 escalation（Task 4）。
  - `decisions/INDEX.md` 评估（Task 5；大概率零改动）。
  - `CHANGELOG.md` 条目（Task 6）。
  - 验证 + A1-A6 + wikilink/frontmatter gate（Task 7）。
  - issue #255 勾 T-1 + comment（Task 8）。
  - PR `--base develop` + HITL-CROSS body（Task 9）。
- **Out-of-scope（严格守约）**：
  - `src/mj_agent/llm.py` / provider factory（无需求）。
  - `capabilities/data-agent/llm-provider/`（消费侧 capability contracts/trace；owner 拍板 footprint=ADR-027+033 only；记 optional Phase-2 候选）。
  - `cross-ref pending → active`（= T-5 / Phase-2）。
  - live integration / e2e test（= Phase-2 / T-5；`tests/integration` e2e 标记用例由 T-5 当批 HITL 决定）。
  - dgx-mlops 侧 Bundle B（joint closure evidence + roadmap flip）= dgx-mlops 仓，另会话，须本 PR merge commit hash。
  - 改 `CTR-BRIDGE-001` / `CTR-AGENTOUT-001` contract 正文（= HITL-CROSS Phase-2 mutation）。

---

## Task Breakdown

### Task 1 — 建分支（G1 worktree）

- [ ] **Step 1**：worktree 建分支（禁 `git checkout -b`）

```bash
git worktree add ../dgx-cross-ref-t1 -b documentation/dgx-cross-ref-t1
cd ../dgx-cross-ref-t1
uv sync
```

- [ ] **Step 2**：确认基线 `develop @ 030f4dc`（或更新）+ 干净树

```bash
git log --oneline -1
git status --porcelain
```
Expected：HEAD = develop 顶；working tree clean。

---

### Task 1b — 落 plan 正文（flow-plan → `plans/`）

**Files**：Create `plans/[PLAN]_255_dgx-cross-ref-t1.md`

- [ ] **Step 1**：`/mj-agent-flow-plan` 在 Owner 拍板（Stage 5 Gate 1）后，由 AI 直接 Write 本 vault plan 正文至 `plans/[PLAN]_255_dgx-cross-ref-t1.md`（flow-plan 命名 `plans/[PLAN]_<issue-id>_<short-desc>.md`；ADR-034 propose→拍板→apply，非手工粘贴）。
- [ ] **Step 2**：落盘 frontmatter `state: draft → active`（起工）；`type: plan` / `track: shared` 保持。post-merge 由 `/mj-agent-flow-post-merge` 自动翻 `active → completed`。
- [ ] **Step 3**：确认 plan frontmatter 7 字段齐（`type/summary/owner/created/updated/state/track`，无 `domain`）匹配 `TEMPLATE_PLAN.md` → A1-A6 就绪（见 Task 7）。

> **落盘物随本 PR 提交**（仓约定：plan 与实现同 PR；实证 `[PLAN]_g1_g2_workflow_enforcement.md` 与代码同 commit `cbd0c1f`）。vault 原稿是 ephemeral plan-mode artifact（不入 git），`plans/` 拷贝才是受治理 committed 制品。

---

### Task 2 — ADR-027 增 cross-ref 段

**Files**：Modify `decisions/ADR-027_LLM_Provider_Abstraction.md`

- [ ] **Step 1**：frontmatter `updated:` `2026-06-11` → `2026-06-29`（`created:` 不动）。

- [ ] **Step 2**：在 **`## Alternatives considered` 段后、`## References` 段前**插入新段（末尾内容段）：

```markdown
## Cross-ref — dgx-mlops provider contracts（T-1；pending dgx-mlops Phase 2 integration）

本 ADR 的 `local-openai-compat` provider 分支，其 DGX-Spark 侧 provider 落地由姊妹仓
`MJ-AgentLab/dgx-mlops` `capabilities/mj-agent/llm-provider-bridge/` 治理（见
[[decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary|ADR-033]]）。mj-agent 作为唯一 consumer，
**绑定**下列 dgx-mlops 契约 ID：

| dgx-mlops contract | 角色 | binding? |
|---|---|---|
| `CTR-AGENTOUT-001`（agent.output.schema.json） | consumer 解析的 OpenAI-compat 输出 schema（`object==chat.completion` / `tool_calls` / `usage`） | **PRIMARY（binding）** |
| `CTR-BRIDGE-001`（cross-capability.contract.md） | 跨仓 API 契约 + model-id `${LLM_MODEL_ID}` 参数化 + HITL-CROSS 治理 | **PRIMARY（binding）** |
| `CTR-VLLM-001` / `CTR-HEALTH-002` | provider-internal realization（vLLM served-model 行为 / `/health` 200）；consumer 无需直接绑定 | informational（追溯） |

- **cross-ref 状态 = pending dgx-mlops Phase 2 integration**：真实 e2e（[[decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary|ADR-033]] §跟踪锚点 T-5）跑通后转 active。
- 对上述 binding 契约的任何跨仓变更走 **HITL-CROSS**（双仓 owner 双签 + 双侧 PR），per ADR-033 §Decision 4（跨仓反耦合预算）+ dgx-mlops `REQ-BRIDGE-002`。
```

- [ ] **Step 3**：本地核验 wikilink target 存在（`decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md` 在位）+ 表格 markdown 渲染正常。

> **预算注**：若 Task 4 复核判定须降 cross-ref 数，则从本表删 informational 行（`CTR-VLLM-001`/`CTR-HEALTH-002`），仅留 2 PRIMARY（informational 仍在 ADR-033 槽位 / dgx-mlops 侧追溯）。**该删除须 mj-agent owner 拍板**。（**语义口径下无需**——informational 行不计入预算；本注仅作字面口径兜底。）

---

### Task 3 — ADR-033 槽位填实

**Files**：Modify `decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md`

- [ ] **Step 1**：frontmatter `updated:` `2026-06-11` → `2026-06-29`。

- [ ] **Step 1b（C4 计数口径入 ADR）**：在 `## Decision` 第 4 项「跨仓反耦合预算」句末（`…保持各自可独立演进）` 之后）**追加**一句——独立于 Step 2 的槽位替换，不影响其逐字匹配：

```markdown
（**计数口径**：仅计双仓 decision/capability 文档间的真实 cross-ref 指针；不计自动生成的 INDEX 行 / CHANGELOG 历史条目 / 运维 SKILL 提及。）
```
使 T-2/T-5 不再复议口径。

- [ ] **Step 2**：替换现「## Cross-ref 槽位（T-1 填实）」段**正文**（标题改为「已填实」+ 日期）：

替换前（现状）：
```markdown
## Cross-ref 槽位（T-1 填实）

dgx-mlops `capabilities/mj-agent/llm-provider-bridge/` contract ID 集合：**pending dgx-mlops M2**——bridge contract draft 产生实 ID 后，由 T-1 documentation PR 填实本槽位，并在 ADR-027 增 cross-ref 段（标 "pending dgx-mlops Phase 2 integration"）。
```

替换后：
```markdown
## Cross-ref 槽位（T-1 已填实 2026-06-29）

dgx-mlops `capabilities/mj-agent/llm-provider-bridge/` contract ID 集合：
- **PRIMARY（mj-agent 绑定）**：`CTR-AGENTOUT-001`（输出 schema）+ `CTR-BRIDGE-001`（跨仓 API 契约）
- **informational（追溯，不绑定）**：`CTR-VLLM-001`（vLLM served-model）+ `CTR-HEALTH-002`（`/health` 200）

cross-ref 状态 = **pending dgx-mlops Phase 2 integration**（[[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]
§Cross-ref 段；真实 e2e（T-5）跑通后转 active）。
```

- [ ] **Step 2c（C5 时态修）**：改本 ADR `## References` 段引 ADR-027 那行——`…（`make_llm()` factory；**T-1 将增** cross-ref 段）` → `…（`make_llm()` factory；**T-1 已增** cross-ref 段，见 §Cross-ref）`（避免 T-1 落地后残留未来时态；段名与 ADR-027 实际标题「Cross-ref — dgx-mlops provider contracts」统一走通用锚 `§Cross-ref`）。

- [ ] **Step 3（可选，executor + owner 定）**：「## 跟踪锚点」表 T-1 行末加状态注（如 `✅ done 2026-06-29 PR #<本PR>`）。**低权重**——issue #255 勾选 + 槽位段日期已足；若加则 PR # 须 PR 开后回填。默认**不加**，靠 issue #255 + 槽位日期。

---

### Task 4 — cross-ref 预算（≤5）复核 + escalation

> ADR-033 §Decision 4：dgx-mlops ↔ mj-agent 文档 cross-ref 总数 ≤ 5（自设）。**计数口径 = 语义 cross-ref**（owner 拍板 2026-07-01）：只计双仓 decision/capability 文档间的**真实 cross-ref 指针**；**排除**自动生成的 `decisions/INDEX.md` + `docs/INDEX.md` 行、`CHANGELOG.md` 历史条目、运维 `SKILL.md` 提及。实测锚点 = ADR-033（唯一 canonical 跨仓引用），ADR-027 是 ADR-033 §跟踪锚点**预留的 T-1 目标** → 加 ADR-027 cross-ref 段后实计 **~1–2/5，在预算内，不触发 escalation**。

- [ ] **Step 1**：按语义口径复核。下列 grep 仅作**枚举辅助**（非计数口径——字面命中含 INDEX/CHANGELOG/SKILL，均不计入预算）：

```bash
# 枚举辅助（字面命中；语义口径下 INDEX/CHANGELOG/SKILL 不计）
grep -rIl "dgx-mlops" --include="*.md" . 2>/dev/null | grep -v "/archive/"
# 当前字面命中 5 文件（SKILL / CHANGELOG / ADR-033 / decisions-INDEX / docs-INDEX）；加 ADR-027 段后字面=6。
# 语义 cross-ref 实计 ~1–2（仅 ADR-033 锚点 + ADR-027 预留目标）。
```

- [ ] **Step 2**：判定加 ADR-027 cross-ref 段后语义计数。
  - **正常路径（语义口径）**：实计 ~1–2/5 → 通过，记 `~2/5（语义口径）` 于 PR body + issue #255 comment。
  - **兜底（仅当 owner 改判字面口径 → >5 时）**：**停 → mj-agent owner 拍板**（HITL）：选项 (i) ADR-033 §Decision 4 预算调整（如 ≤6，记 ADR rationale）；或 (ii) 从 ADR-027 删 informational 行（Task 2 Step 2 预算注），仅留 2 PRIMARY 降数。**不擅自改预算 / 不擅自删绑定面**。

---

### Task 5 — decisions/INDEX.md 评估

**Files**：（条件）Modify `decisions/INDEX.md`

- [ ] **Step 1**：评估 INDEX summary 是否需反映 cross-ref。ADR-033 行 summary 已含「跨仓 cross-ref ≤5」；ADR-027 行 summary 述 provider 抽象。T-1 **不增删 ADR**，core decision 不变 → **大概率零改动**。
- [ ] **Step 2**：若 owner 要 ADR-027 summary 反映 cross-ref，则加 ≤1 短语（不破 INDEX 手工维护格式）；否则跳过。

---

### Task 6 — CHANGELOG 条目

**Files**：Modify `CHANGELOG.md`

- [ ] **Step 1**：在 `## [Unreleased]` 段下加 Keep-a-Changelog `### Changed` 子节（现行 CHANGELOG 格式 = `### <Category> — <标题>` + 粗体引导 bullet；T-1 改既有 ADR → `Changed`；**非** 裸 `docs(...)` commit 式 bullet）：

```markdown
### Changed — T-1 dgx-mlops cross-ref 采纳（ADR-027 + ADR-033）
- **`decisions/ADR-027_LLM_Provider_Abstraction.md`（`docs`，branch `documentation/dgx-cross-ref-t1`）**：增「Cross-ref — dgx-mlops provider contracts」段，绑定 `CTR-AGENTOUT-001` + `CTR-BRIDGE-001`（PRIMARY），状态 pending dgx-mlops Phase 2 integration。
- **`decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md`**：「Cross-ref 槽位」由 pending 占位填实为实 ID 集合；闭 dgx-mlops M7 Phase-1 exit #3 的 mj-agent 半边（HITL-CROSS）。Refs #255
```

> CHANGELOG 同锚点冲突注（PR-B 历史教训）：若与并行 PR 同段冲突，rebase 后 `--force-with-lease` 重推。

---

### Task 7 — 验证（A1-A6 doc gates + frontmatter/wikilink）

- [ ] **Step 1**：文档 gate

```bash
uv run python scripts/check_frontmatter.py
uv run python scripts/check_wikilinks.py
```
Expected：PASS。**注**：wikilink 解析须本地核验新增 `[[decisions/ADR-033_…|ADR-033]]` / `[[decisions/ADR-027_…|ADR-027]]` target 存在（A4 root-file 解析已 blocking #271；ADR-内 wikilink 按现行 gate 口径）。

- [ ] **Step 2**：A1-A6 doc gates（`policies/documentation.md`）——覆盖 **2 ADR + CHANGELOG + `plans/[PLAN]_255_dgx-cross-ref-t1.md`**（`/mj-agent-doc-author` + `/mj-agent-flow-plan` 流程内置）；确认各文件 frontmatter schema / track / path-to-track 一致（plan 文件 frontmatter 已匹配 `TEMPLATE_PLAN.md`；`plans/` 非 root-file → A4 不解析其 wikilink，目标 ADR 均在位 → 本地核验 PASS）。

- [ ] **Step 3**：Level A sanity（无 src 改动，应不受影响）

```bash
uv run ruff check && uv run mypy src/mj_agent && uv run pytest tests/unit
```
Expected：PASS（无 src 改动 → 行为不变）。

- [ ] **Step 4（pre-commit 阻塞 · C6）**：consistency check（HITL-CROSS integration-test 元素）——核对两侧 contract ID 字面一致：ADR-027 §Cross-ref + ADR-033 §槽位 列 `CTR-AGENTOUT-001` / `CTR-BRIDGE-001`（PRIMARY）+ `CTR-VLLM-001` / `CTR-HEALTH-002`（informational），与 dgx-mlops `capabilities/mj-agent/llm-provider-bridge/contracts/` + readiness assessment §3 逐字一致（无 ID typo / 版本 drift）。**这 4 个 ID 在 dgx-mlops 仓、mj-agent 内不可自证**——执行时须 dgx-mlops 仓 / 设计文档 `dgx-mlops-M7-Phase1-closure-T1-cross-ref-design-2026-06-29.md` 在手逐字对齐**方可 commit**；不可得则**暂停（HITL）**，不提交未核 ID。

---

### Task 8 — issue #255 关联

- [ ] **Step 1**：PR body 含 `Refs #255`。
- [ ] **Step 2**：merge 后勾 `[x] T-1 落地（documentation PR merged）`（comment 或 edit checkbox）+ comment 记：本 T-1 PR #、dgx-mlops 对应 Bundle B PR（待）、预算复核结果 `N/5`。
- [ ] **Step 3**：**issue 不关单**（T-2 / T-5 仍 open）。

---

### Task 9 — PR（HITL-CROSS 半边）

- [ ] **Step 1**：commit

```bash
git add plans/[PLAN]_255_dgx-cross-ref-t1.md decisions/ADR-027_LLM_Provider_Abstraction.md decisions/ADR-033_DGX_Ops_Sister_Repo_Boundary.md CHANGELOG.md
# 若 Task 5 改了 INDEX：git add decisions/INDEX.md
git commit -m "docs: T-1 dgx-mlops cross-ref 采纳（ADR-027 + ADR-033）"
```

- [ ] **Step 2**：push + PR `--base develop`

```bash
git push -u origin documentation/dgx-cross-ref-t1
gh pr create --base develop --title "docs: T-1 dgx-mlops cross-ref 采纳（ADR-027 + ADR-033）"
```

- [ ] **Step 3**：PR body 含（**HITL-CROSS 半边**，per dgx-mlops REQ-BRIDGE-002 B1/B2）：
  - `Refs #255`；
  - **HITL-CROSS** 声明：本 PR = mj-agent 半边；双仓 owner 双签 approver（mj-agent owner + dgx-mlops owner，命名）；dgx-mlops 对应 PR = Bundle B（joint closure，待本 PR merge hash）；
  - 零 contract schema mutation；integration-test 元素 = consistency check（Task 7 Step 4）；live e2e 归 Phase-2 / T-5；
  - 预算复核结果 `N/5`。

- [ ] **Step 4**：owner 拍板 + 合并（**owner-only**）。merge commit hash 交 dgx-mlops 侧 Bundle B。

---

## Risk Control

- **Risk level**：**Low-Medium**（纯 documentation；跨仓 HITL-CROSS 协调 + 预算约束抬到 Medium；不触 5 必停面 / src）。
- **缓解**：
  - **R1 预算溢出（首要）**：Task 4 复核 + owner escalation；绑定面最小化（2 PRIMARY）；informational 可降数 fallback。**不擅自改预算**。
  - **R2 HITL-CROSS 解释分歧**（consistency-check vs live test）：dgx-mlops owner spec-review 已认可 consistency-check（doc-only，零 runtime 变更）；live e2e 明确归 T-5。
  - **R3 frontmatter 漏 bump / wikilink 失效**：Task 2/3 显式 `updated:` bump；Task 7 gate + 本地 wikilink 核验。
  - **R4 CHANGELOG 同锚点冲突**：rebase + `--force-with-lease`（PR-B 教训）。
  - **R5 状态语义混淆**：全程 `pending dgx-mlops Phase 2 integration`；active 仅 T-5。
  - **R6 CTR ID drift（外部不可自证）**：4 个 CTR ID 在 dgx-mlops 仓——Task 7 Step 4 pre-commit 逐字对齐；dgx-mlops 侧不可得则暂停，不提交未核 ID。
- **HITL gates**：Stage 5/7/9/11/13（17-stage loop）；合并 owner-only；HITL-CROSS 双签（PR body）。

## Verification（汇总）

- **Level A 必跑**：`uv run ruff check && uv run mypy src/mj_agent && uv run pytest tests/unit`（应不受影响）。
- **文档校验**：`scripts/check_frontmatter.py` + `scripts/check_wikilinks.py`（PASS）+ A1-A6 doc gates。
- **consistency check**：两侧 contract ID 字面一致（Task 7 Step 4）。
- **Acceptance Criteria**：
  - [ ] AC1：ADR-027 含「Cross-ref — dgx-mlops provider contracts」段，列 2 PRIMARY（`CTR-AGENTOUT-001`/`CTR-BRIDGE-001`）binding + 2 informational，状态标 `pending dgx-mlops Phase 2 integration`。
  - [ ] AC2：ADR-033 「Cross-ref 槽位」由 `pending dgx-mlops M2` 填实为实 ID 集合 + 状态同 AC1。
  - [ ] AC3：两 ADR frontmatter `updated: 2026-06-29`。
  - [ ] AC4：cross-ref 预算复核 ≤ 5（或 owner 拍板处置记录）。
  - [ ] AC5：`check_frontmatter` + `check_wikilinks` + A1-A6 PASS；consistency check 两侧 ID 一致（4 个 CTR ID 与 dgx-mlops 侧逐字一致）。
  - [ ] AC6：PR body 含 HITL-CROSS 双签 + `Refs #255` + 预算结果；issue #255 T-1 勾选（merge 后）。
  - [ ] AC7：零 src / 5 必停面 / contract 正文改动。
  - [ ] AC8：plan 正文落 `plans/[PLAN]_255_dgx-cross-ref-t1.md` 并入本 PR（`state: active`），A1-A6 PASS。

## 跨仓协调（Bundle B，dgx-mlops 侧，非本 PR）

本 T-1 PR merge 后，dgx-mlops 侧另会话执行 **Bundle B**（Lane A）：记 joint closure evidence（含本 PR + Bundle B PR 双 commit hash，cross-capability-change Step 9）+ flip dgx-mlops roadmap M7 Phase-1 exit #3 + readiness assessment §3 de-draft。**依赖本 PR merge commit hash**。dgx-mlops M7 header 维持 🔄（Phase-2 真实 e2e 未启）。

## 严格不做

- 不动 5 in-source 必停面 / 6 infra-freeze skills / `src/mj_agent/llm.py`。
- 不改 `capabilities/data-agent/llm-provider/`（footprint=ADR-027+033 only）。
- 不 `pending → active`（= T-5）。
- 不写 / 不跑 live integration e2e（= Phase-2 / T-5）。
- 不改 dgx-mlops `CTR-BRIDGE-001` / `CTR-AGENTOUT-001` contract 正文（= HITL-CROSS Phase-2 mutation）。
- 不擅自改 ≤5 预算 / 不擅自删 binding 面。

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-06-29 | v1 | 初稿。由 dgx-mlops 会话产出（owner 入口五拍板 + spec-review a–d approved；dgx-mlops 侧设计 = vault `dgx-mlops-M7-Phase1-closure-T1-cross-ref-design-2026-06-29.md`）。9 Task；exact ADR-027/033 diff 内嵌；预算复核 + HITL-CROSS 双签 + consistency-check（doc-only）。待 mj-agent 会话执行。 |
| 2026-07-01 | v2 | mj-agent develop 会话评估修订（C1–C6，owner 拍板预算=语义口径 / plan=落盘并入 PR）：① commit scope `docs(decisions)`→无 scope `docs:`（STANDARD §4.3，`decisions` 非白名单）；② CHANGELOG 改 Keep-a-Changelog `### Changed` 子节（非裸 commit bullet）；③ 补 Task 1b 落 `plans/[PLAN]_255_dgx-cross-ref-t1.md` 并入 PR（+Scope/Task9 git-add/Task7 A1-A6/AC8）；④ 预算改语义口径（+ADR-033 §Decision 4 计数口径行 Step 1b；收敛「~5/5 临界」无据表述）；⑤ ADR-033 References 时态 将增→已增 + 段名统一 `§Cross-ref`；⑥ CTR ID consistency-check 升 pre-commit 阻塞（+R6/AC5）。实仓核验：基线 030f4dc / issue #255 T-1 勾选框逐字 / ADR-033 L43 逐字替换匹配 / ADR-027 插入点 均属实。 |
| 2026-07-01 | active | mj-agent develop 会话起工落盘（`state: draft → active`）；本文件 = 受治理 committed 制品（vault 原稿 ephemeral）；随本 documentation PR 提交。 |
