---
type: plan
summary: T-5 真实 e2e 采纳——provider 切 DGX（.env 纯配置）跑通 make_graph 端到端 + tool-calling 捕获；ADR-027 §Cross-ref pending→active + ADR-033 槽位/锚点同步；consumer evidence；先合取 hash 交 dgx-mlops Slice-E2E。闭 dgx-mlops M7 Phase-2 出口①②③⑤（mj-agent 半边）
owner: 项目负责人
created: 2026-07-02
updated: 2026-07-03
completed: 2026-07-03
state: completed
track: shared
---

# [PLAN] mj-agent T-5 — DGX 真实 e2e 采纳（ADR-027 active + consumer evidence）

> **Issue**：[#255](https://github.com/MJ-AgentLab/mj-agent/issues/255)（T-anchor；本 plan 闭 T-5 关单项；T-2 核对已于 2026-07-03 完成——#255 comment，零 drift @ dgx-mlops `72933bb`）
> **关联**：dgx-mlops **M7 Phase-2 Slice-E2E**（roadmap M7 Phase-2 出口①②③⑤）。dgx-mlops 侧 spec = owner vault `sdd-development/dgx-mlops/dgx-mlops-M7-Phase2-e2e-design-2026-07-02.md` §4；dgx-mlops 侧 plan = `dgx-mlops-M7-Phase2-sliceE2E-plan-2026-07-02.md`。
> **触发**：dgx-mlops 侧 DGX serving up + mj-agent readiness 已回报（切换 = 纯 `.env` 配置零代码，ADR-027 §D.3）。
> **性质**：**config + documentation + evidence PR**（`.env` = owner 手工；ADR/evidence/CHANGELOG/plan = AI 落盘）。**不触** 5 in-source 必停面、`src/mj_agent/llm.py`、provider factory（零代码改动）。
> **HITL-CROSS 双签 = dgx-mlops owner + mj-agent owner（双帽 @ranzuozhou）；本 PR 先合，merge hash 交 dgx-mlops Slice-E2E PR。**

## Goal / Architecture

**Goal**：在 mj-agent 仓完成 DGX endpoint 的真实 e2e 采纳——(1) provider 经 `.env` 切到 DGX vLLM endpoint（`LLM_MODEL_ID` override + base-url，零代码）；(2) 经真实 runtime 路径（`make_graph()` + metric 问题 → `find_biz_context` 工具调用）跑通端到端 + 捕获 ≥1 纯 completion + ≥1 tool-calling completion（交 dgx-mlops 侧做 schema/S1-S4 断言）；(3) `decisions/ADR-027` §Cross-ref 状态 `pending dgx-mlops Phase 2 integration` → **`active`** + `decisions/ADR-033` §Cross-ref 槽位/§跟踪锚点 T-5 同步；(4) consumer evidence 落 `capabilities/data-agent/llm-provider/evidence/runtime/`。落地后 = dgx-mlops M7 Phase-2 出口①②③⑤ 的 mj-agent 半边（joint，HITL-CROSS 双签）。

**Architecture**：单一 config+documentation+evidence PR；**零 src / 零 contract content mutation**（仅 mj-agent ADR 状态 flip + consumer evidence）。HITL-CROSS integration-test 元素 = **live e2e**（真实业务请求 + tool-calling，非 Phase-1 的 consistency-check-only）。本 PR **先合** → merge hash 交 dgx-mlops Slice-E2E PR。

## Global Constraints（每 Task 隐含）

- **不改**：`src/mj_agent/llm.py`、provider factory、5 in-source 必停面、6 infra-freeze skills、`capabilities/data-agent/llm-provider/` 的 contracts/trace（footprint 仅 ADR-027 + ADR-033 + evidence/runtime）。
- **`.env` = AI permission-deny 面**：所有 `.env` 改动 owner 手工（AI 给内容块）；AI 不读不写 `.env` / 真实凭据（Lane C 口径）。
- **cross-ref 预算**：≤5（ADR-033 §Decision 4 语义口径）；状态 flip 非新增指针；本切片新增 dgx `ADR-023` 反向 anchor → 实计 **3/5**。
- **HITL**：AI 提议 → owner 拍板；合并 owner-only；HITL-CROSS 双签（PR body）。
- **commit**：无 scope 的 `docs: …`（跨 `decisions/` + `capabilities/` + `plans/` + `CHANGELOG.md` 无主导 scope）。

## Task Breakdown（执行态）

### Task 1 — 建分支（G1 worktree）✅ 2026-07-03

- [x] `git worktree add ../dgx-e2e-t5 -b documentation/dgx-e2e-t5` + `uv sync`；基线 develop `2fabce3`、干净树。

### Task 1b — 落 plan 正文 ✅ 2026-07-03

- [x] 本文件（`state: active`；post-merge `/mj-agent-flow-post-merge` 翻 `completed`）。

### Task 2 — T-2 provider 切换（`.env` 纯配置，owner 手工）✅ 2026-07-03（提前于本 plan，T-4 演练即完成并持久化）

- [x] `.env`：`LLM_PROVIDER=local-openai-compat` + `LLM_MODEL_ID=nemotron-3-super`（≠ 默认 Ark 云 id ✓）+ `LLM_BASE_URL` + `NO_PROXY`；api-key 401 判别 = 200 无鉴权（`"EMPTY"` sentinel）。
- [x] **持久化超出原计划**：4 键回写 `config/secrets.enc` + `config/secrets.example` §2c（ADR-030 管道；develop `2fabce3`）。
- **拓扑偏差（如实记录）**：serving 绑 DGX loopback → `LLM_BASE_URL=http://127.0.0.1:18000/v1`（SSH 隧道），非原预填的 LAN 直连 `http://<DGX_HOST>:8000/v1`。

### Task 3 — T-5 e2e 执行 + 捕获 ✅ 2026-07-03

- [x] 真实 runtime 路径一轮 metric 问题 → turn 1 `finish_reason="tool_calls"`（`find_biz_context`）+ turn 2 `finish_reason="stop"`，HTTP 200 ×2。
- [x] 捕获 raw JSON（脚本级 `httpx.Client.send` tee，零 src 改动）→ redacted `resp-tool.json` / `resp-pure.json` + `CAPTURE_MANIFEST.md` 交 dgx-mlops 会话。
- [x] 廉价加固：unknown-model → 404 + 标准 `NotFoundError` envelope；burst 429 诚实 defer。
- [x] **gate 已过**：dgx-mlops 侧回报 **S1-S4 + S1a 全 PASS**（`validate_e2e.py`，jsonschema draft 2020-12，2026-07-03）→ flip/PR 解锁。

### Task 4 — cross-ref 预算复核 ✅

- [x] **3/5（语义/document-level 口径）**：mj ADR-027 + ADR-033（flip 为状态字段变化非新增）+ dgx `ADR-023` 反向 anchor = 1 新指针；≤5 通过。per-edge caveat 备案（owner 如改判口径，flip 收为纯状态字段版）。

### Task 5 — ADR-027 flip active + ADR-033 同步 ✅ 2026-07-03

- [x] ADR-027：frontmatter `updated: 2026-07-03`；§Cross-ref 状态行 `pending`→`active`（含 evidence 指针 + dgx `ADR-023` / 分支名，不写 dgx PR#——先合序）；**§Cross-ref 标题同批去 pending 字样**（原计划未列；标题/正文自洽所需，PR body 标注）。
- [x] ADR-033：frontmatter `updated: 2026-07-03`；§槽位状态行 flip；§跟踪锚点 T-5 行 ✅ done（PR# 开 PR 后回填）+ T-2 行 ✅ done（#255 comment 2026-07-03）。
- [x] e2e 标记用例（`tests/integration`）：本批 HITL 决定**不加**（隧道依赖 CI 不可复现；接入条件 = serving LAN 绑定 + api-key 另议）。

### Task 6 — consumer evidence ✅

- [x] `capabilities/data-agent/llm-provider/evidence/runtime/2026-07-03_dgx_e2e.md`（runtime 层惯例；redacted；含拓扑偏差、S1-S4 权威归因 dgx 侧、429 defer 注记）。

### Task 7 — CHANGELOG ✅

- [x] `## [Unreleased]` `### Changed` 条目（见 CHANGELOG.md）。

### Task 8 — 验证 ✅

- [x] `check_frontmatter` + `check_wikilinks` PASS；ruff + mypy + pytest unit PASS（零 src 改动）。
- [x] consistency check（pre-commit 面）：4 CTR ID 与 dgx-mlops develop `72933bb` 逐字一致（2026-07-03 T-2 核对）；本 PR 两 flip = `active`。状态三处一致 = dgx 侧后置核（先合序，dgx readiness §3 此刻 pending 属正常非 drift）。

### Task 9 — issue #255 关联

- [x] PR body `Refs #255`（不 Closes——T-5 勾选后是否关单 owner 定）。
- [x] merge 后勾 `[x] T-5` + comment（PR #274 merge `3b8924e` + dgx 分支 + 预算 3/5；2026-07-03 已落）。

### Task 10 — PR（HITL-CROSS 半边，先合）

- [x] commit + push + PR `--base develop`（HITL-CROSS body）。
- [x] owner 拍板合并（owner-only，先合；merge `3b8924e` 2026-07-03）→ **merge hash 已交 dgx-mlops Slice-E2E PR**。

## Verification / AC（汇总）

- [x] AC1 provider 切 DGX（model-id override ≠ 默认）；e2e HTTP 200
- [x] AC2 捕获 ≥1 纯 + ≥1 tool-calling（redacted 交 dgx）
- [x] AC3 ADR-027 flip active + ADR-033 槽位/锚点同步
- [x] AC4 两 ADR `updated: 2026-07-03`（日期偏差 v1 预填 07-02 → 实际执行日，更新记录备案）
- [x] AC5 consumer evidence 落地（redacted）
- [x] AC6 预算 3/5 ≤5
- [x] AC7 gates PASS（状态三处一致 = dgx 侧后置核）
- [x] AC8 PR 先合（前置 S1-S4+S1a 全 PASS 已达成；PR #274 merge `3b8924e`），merge hash 交 dgx-mlops
- [x] AC9 零 src / 5 必停面 / contract 正文改动
- [x] AC10 plan 落盘随 PR（本文件）

## 跨仓协调（dgx-mlops Slice-E2E，非本 PR）

本 T-5 PR merge 后，dgx-mlops 会话执行 Slice-E2E（`feature/m7-phase2-e2e-closure`）：ADR-023 + integration verification evidence（S1-S4）+ workflow-run assessment（含双方 hash）+ CTR-BRIDGE-001 契约本体 mutation + readiness §4 ①②③⑤ ☑ + §3 状态注记 + M7 收官。**依赖本 PR merge commit hash**。

## 严格不做

- 不动 5 in-source 必停面 / 6 infra-freeze skills / `src/mj_agent/llm.py` / provider factory（零代码）。
- 不改 `capabilities/data-agent/llm-provider/` contracts/trace。
- 不改 dgx-mlops `CTR-BRIDGE-001` / `CTR-AGENTOUT-001` contract 正文。
- 不擅自改 ≤5 预算 / 不擅自删绑定面。
- 不碰真实秘密值 / `.env`（owner 手工，Lane C）。

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-07-02 | v1 | 初稿。由 dgx-mlops 会话产出（Slice-E2E spec v0.3.3 §4 APPROVED + readiness §6.1.1 回报）。 |
| 2026-07-03 | v1.1（执行落盘） | 按实际执行修订：① 全日期 2026-07-02 → 2026-07-03（evidence 文件名 / flip 日期 / frontmatter updated）；② Task 2 拓扑偏差备案（serving loopback-bound → SSH 隧道 `127.0.0.1:18000`，非 LAN 直连）+ 持久化超出原计划（secrets.enc 回写，develop `2fabce3`）；③ ADR-027 §Cross-ref 标题同批去 "pending" 字样（自洽所需，原计划未列）；④ Task 4 预算实计 3/5 确认；⑤ e2e 标记用例本批 HITL 决定不加；⑥ dgx 侧 S1-S4+S1a 全 PASS 回报（2026-07-03）解锁 flip/PR。 |
