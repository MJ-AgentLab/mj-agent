---
type: adr
domain: SYS
summary: 引入 plans/ working 文档 4 态机（draft → active → completed → archived）；mj-system v5.2 §10.5 派生；落 Meta v2.2 §5.11 + mj-agent-flow-post-merge SKILL Step 9
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - working-doc
  - lifecycle
  - mj-system-derivation
---

# ADR 021: Working 文档生命周期 4 态机

## Context

mj-agent 当前 `plans/**` 工作文档使用 `draft / active / deprecated` 3 态（沿用 canonical 文档生命周期），但 working 文档"任务结束"语义与 canonical 文档"被新版本替代"语义**不同**：

- Canonical `deprecated`：表示"被新版本取代"（如 Meta v2.0 → v2.1 archive）
- Working "任务完成"：表示"PR merged / Issue closed / Release deployed"，**没有**新版本替代关系

用 `deprecated` 标已完成 plan 语义错配。当前 mj-agent `plans/` 中已完成的 PLAN（如 PLAN_D_Setup_Env_Scripts、PLAN_F_Documentation_Track_Split、PLAN_G_Docs_Infrastructure_Git）部分仍标 `draft`，部分标 `completed`（不一致）。

mj-system v5.2 §10.5 "Working 文档生命周期"提供 4 态机模式（draft → active → completed → archived），引入 `completed` 终止态专为 working 任务自然结束设计。mj-system 1 个月实测有效。

`scripts/check_frontmatter.py` STATE_VALUES 已含 `completed`（之前预先加），但**规则未文档化**；本 PR 补全规则 + retroactive 标记 + Step 9 自动化引用更新。

## Decision

### 主条款（落 Meta v2.2 §5.11）

`plans/**` 工作文档使用 **4 态机**（区别于 canonical 文档的 3 态）：

| state | 含义 | 触发 |
|---|---|---|
| `draft` | 仍在拟订；未对齐 | 新建文档默认 |
| `active` | 已采纳；任务执行期 | 关联 issue/PR open |
| `completed` | 任务自然完成 | 关联 PR merged / Issue closed / Release deployed |
| `archived` | 物理归档（GC） | (Phase D 范畴；本 ADR 不实施) |

### Stage 17 Post-merge 自动化

`mj-agent-flow-post-merge` SKILL Step 9（已存在）自动识别 PR/Issue 关联的 `[PLAN]_*.md` / `[INTAKE]_*.md`，state 由 `active` 改 `completed` 并刷 `updated` 字段。本 ADR 仅更新 SKILL.md 中 cross-ref 从 "Meta v2.0 §10.5"（前瞻性）改为 "Meta v2.2 §5.11"（实落）。

### Retroactive 标记

按 mj-system §10.5.5 模式，本 PR 同期把 7 个明显已完成的 plan state 由 `active`/`draft` → `completed`：

- 5 PLAN_doc_governance_*（C-2/C-1a/C-1b/C-3-1/C-3-2 — 本会话刚完成）
- PLAN_F_Documentation_Track_Split（v2.0 trio promote 已落地）
- PLAN_G_Docs_Infrastructure_Git_From_MJ_System（CHANGELOG 显示已完成）

其他 plans（如 PLAN_A/B/C/E/Phase0）保持 `draft`（per mj-system §10.5.5 "长期 draft 不动留 abandon 余地"）；roadmap + mvp-framework 保持 `active`。

### 与既有 ADR 关系

不 supersede 任何 ADR；与 ADR-011/017/018/019 互补（lifecycle + canonical archive/active 路径正交）。

## Consequences

### 正面

1. **任务完成语义清晰** — 区别于 deprecated；reviewer 一眼可识 plan 已落地
2. **`scripts/check_frontmatter.py` STATE_VALUES `completed` 文档化** — 规则与实现对齐
3. **Stage 17 自动化引用归位** — SKILL Step 9 不再 forward-ref Meta v2.0 §10.5；改为 Meta v2.2 §5.11 实落
4. **mj-system 双向兼容** — 同模式
5. **跨文档 reference 稳定** — `completed` 文件位置不变，仅 state 改

### 负面

1. **plans/ retroactive 标记需逐一审 PR merge 状态** — 易误标；本 PR 仅标 7 个明显已完成的；其他保留现状
2. **`archived` 物理归档延后** — Phase D 范畴；本 ADR 仅 lifecycle 定义，不实施 GC

### 中性

1. **不动 canonical 3 态** — Code_Side / Agent_Side / Meta 等 canonical 仍用 `draft / active / deprecated`
2. **本 PR 自身按 ADR-017 §5.9 判定**：trigger #1-4 ❌；反例 #5 字段补充 ✅（Meta §5.11 in-place 加段；ADR-021 新建非演进）→ 不触发 archive ceremony

## Alternatives considered

### A. 不引入 `completed` 状态（继续用 `deprecated`）

**拒绝原因**：语义错配（deprecated 含"被替代"含义；working 任务无替代关系）。reviewer/作者社区共识弱（mj-agent 当前 plan state 不一致）。

### B. 仅引入 `completed`（不引入 `archived`）

**接受**（即本 PR 的方案 — 仅引入前两态新增）：`archived` 物理归档延 Phase D；当前 plans/ 量级不需 GC。

### C. 把 working 4 态机加进 canonical（统一 5/6 态机）

**拒绝原因**：(a) canonical 与 working 治理目标不同（canonical "权威性"；working "可执行性"）；(b) mj-system §10.5 显式分两套 lifecycle；mj-agent 跟随；(c) `state: active` 在 canonical 与 working 中均存在但语义略不同（canonical = "可被引用为权威"；working = "任务执行中"）；保持分立更清晰。

### D. 等 Phase D 与 EVAL framework 一起

**拒绝原因**：plan §F 选定 Phase C-3 三联包，本 PR 是子包 3/3 收尾。post-merge SKILL Step 9 引用已存在但 Meta cross-ref 是 forward-ref；尽快补齐避免债务累积。

## References

- 派生源：[mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md §10.5](https://github.com/MJ-AgentLab/mj-system/blob/develop/docs/rule/%5BSTANDARD%5D_Documentation_Management_Framework.md) lines 688-741
- 落地：[[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11（本 ADR 同步落 STANDARD）
- Stage 17 自动化：[[../../.claude/skills/mj-agent-flow-post-merge/SKILL]] Step 9（cross-ref 从 Meta v2.0 §10.5 改 Meta v2.2 §5.11）
- 关联 ADR：ADR-011/017/018/019/020 全部 sustained；与本 ADR 互补不重叠
- 私有评估：plan §C.2.3
- 关联 GitHub Issue：[#86](https://github.com/MJ-AgentLab/mj-agent/issues/86)
- Phase C-3 P1 三联包子包 3/3（收尾）
- 后续（Phase D）：`archived` 物理归档实现（移到 `plans/archive/` 子目录；GC trigger ≥ 6 月 + 引用 0）
