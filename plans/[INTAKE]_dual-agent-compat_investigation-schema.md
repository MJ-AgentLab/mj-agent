---
type: intake
summary: investigation-type schema 正式化切片（a2 finding #2-9 / #347 §三.2 A6 follow-up 的 Intake §9-1）的 Stage 0 Intake 落盘——maintain/Medium/预计 1 PR；在 evidence/ai-context-audit/SCHEMA.md §2 正式定义 ai-context-investigation frontmatter schema + 扩 scripts/check_ai_context_audit.py 按 filename（YYYY-MM-DD_*.md）选中并校验 investigation 条目；两既存 investigation 文件（05-22 a2/a3）green day-one；Gate 5 拍板 D1=formalize+validate、D2=same blocking gate day-one（coverage-expansion of already-blocking gate，无 continue-on-error flip、无 ci.yml edit；§三.1 carry-forward：不自判 ci-blocking-gate-toggle/§4:41 N/A，Owner 选项即显式治理裁定，PR 记录类比 V11 #330 / A6 #360）；对应 issue #362；非 #312 tracker 行，是 #359 / #347 §三.2 的 follow-up
owner: ranzuozhou
created: 2026-07-20
updated: 2026-07-20
state: active
track: shared
---

# [INTAKE] investigation-type schema 正式化切片（issue #362）

> Stage 0 输出于 2026-07-20 会话内产生并当日落盘（worktree 内，保 develop 干净）；触发 §2.1 落盘判定
> （family convention：dual-agent-compat 恒落 [INTAKE]+[PLAN] 成对；HITL 点：D1 disposition + D2 CI posture
> + commit/push/PR + 治理面〔blocking gate coverage 扩展〕）。
> 上游输入：`evidence/ai-context-audit/2026-05-22_a2-investigation.md` finding **#2-9**（"SCHEMA.md type enum
> currently ai-context-audit only; investigation-type files need amendment"）+ 该文件 `schema_extension_request: true`
> frontmatter flag；A6 切片 `[PLAN]_dual-agent-compat_a6-durability.md` §5.2 选 Option (a)〔只校 audit〕、拒 Option (c)
> 〔"撑大切片"〕并把 investigation 正式化登记为 follow-up（该 plan Intake §9-1）。
> **非 #312 tracker 行**——是 #359 / #347 §三.2 的独立 follow-up（brief §四.F 候选 F）。
> 前序：#359 A6 durability gate 全闭环，develop @ `983db0e`。

## 1 Task Classification

- **Type**: `maintain`（validator 脚本 + 已 blocking 的 CI gate coverage 扩展 + canonical 治理 schema 文档 + 单测）
- **Base**: develop → PR `--base develop`
- **影响范围**：
  - `evidence/ai-context-audit/SCHEMA.md` — canonical 治理 schema 文档（**非** 必停面；在 `check_frontmatter.py` SCAN_ROOTS 外）
  - `scripts/check_ai_context_audit.py` — A6 validator（扩：按 filename 选中 investigation + 校验 investigation schema；docstring 更新）
  - `tests/unit/test_check_ai_context_audit.py` — 加 investigation 用例；**改** 两个编码旧行为的既有测试
  - `CHANGELOG.md`
  - `.github/workflows/ci.yml` — **预期无改动**（同一 blocking step 校更多；Stage 3 确认）

## 2 Risk Assessment

- **Level**: **Medium** — additive/structural、设计上 green day-one，但触及 (a) canonical 治理 schema、(b) 一个**已 blocking 的 CI gate 的 coverage**。
- **触发 §3.1 必停项**：**4 项 mj-agent 专属全不触**（非 runtime-skill / prompt-version / biz-catalog / sql-guardrail）。无 D-017（不动 `agents_sync.py`/manifest/`.agents/`/`.codex/`）。无 A14（不动 `.mcp.json`）。
- **治理 flag（承 §三.1 carry-forward）**：把一个 already-blocking gate 的 coverage 扩到此前未受门的文件类型 = 对那些文件是 **new blocking behavior**。承 A6 教训，**不自判** `ci-blocking-gate-toggle` / ci-gates §4:41 为 "N/A" → 交 Owner 显式裁定（见 §3 D2）。

## 3 Gate 5 拍板（2026-07-20，AskUserQuestion）

- **D1 = Formalize + validate**（Recommended）：在 SCHEMA §2 正式定义 `ai-context-investigation` schema **并** 扩 validator 按 filename（`YYYY-MM-DD_*.md`）选中 + 校验 investigation 条目。设计上让 2 个既存文件 day-one 通过。= A6 plan 的 Option (c)，现作为独立切片——#2-9 所求的 durable answer + 清 `schema_extension_request`。
- **D2 = Same blocking gate, day-one**（Recommended）：把 investigation 校验并入既有 already-blocking 的 `check_ai_context_audit.py` step（**无** `continue-on-error` flip、**无** ci.yml edit）。语料 = 2 文件、均设计为 green。视作 **coverage-expansion of an existing blocking gate**（非 §4:41-scoped 的 new gate）。
  - **治理裁定记录**：Owner 选此项即对 §三.1 问题作显式裁定——treat as coverage-expansion，非新增 blocking gate；PR body + 本切片 plan §治理 记录该裁定，类比 **V11 #330 / A6 #360**。此为承 §三.1「新 blocking 行为勿自判 N/A」的合规路径（Owner 裁定，非 AI 单方）。

## 4 §2.1 落盘判定

- 落盘 `plans/[INTAKE]+[PLAN]_dual-agent-compat_investigation-schema.md`：**是** — family convention（dual-agent-compat 恒成对落盘）；写在 worktree 内保 develop 干净（brief §六.1）。

## 5 Next Step

Stage 3 Repo Scan（确认 schema 字段集 / filename 选择 / 无 ci.yml edit）→ Stage 4 计划落盘（本 worktree，同 PR）→ Stage 8 TDD 实施 → Stage 10/11 验证/自评（含 5-lens）→ Gate 13 PR → 交 Owner 合并 → Stage 17 post-merge（state flip PR + 分支双清 + worktree remove + 手动关 #362）。
