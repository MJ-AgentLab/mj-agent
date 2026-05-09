---
type: standard
domain: SYS
summary: Track A 代码侧文档治理（v1.0 → v1.1 minor bump）— 加注 Track C engineering-workflow 共享 A1-A6 + §3.9 cross-ref engineering-workflow STANDARDs；与 Meta v2.1 同 PR 落地
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-09
state: active
version: v1.1
track: code
derives_from: mj-agent@archive/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0
supersedes:
  - "mj-agent@archive/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0"
tags:
  - standard
  - documentation
  - track-a
  - code-side
aliases:
  - MJ-Agent Code-Side Documentation Framework v1.1
  - Track A 子框架 v1.1
---

# MJ-Agent 代码侧文档治理框架 v1.1（Track A）

> **状态（Phase B PR-B3c-promote 完成后）**：`state: active`。v1.0 已 archive 至 `docs/archive/rule/` + `state: deprecated`。与 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] 同期 promote。
> **职责**：治理 Track A 文档（GUIDE / ADR-code / SPEC-code / RUNBOOK / POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code）的 authoring 深度规则与 PR 校验。
> **不**治理：4 类自有（SKILL / PROMPT / EVAL / agent-facing CONTRACT）—— 见 [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]；**不**治理 engineering-workflow 资产（`.claude/**` / HITL_Prompt）—— 见 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] §3.10 / §7.7。
> **派生自**：[[../archive/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|v1.0（archive）]]
> **首要变更**：仅 minor bump —— §0 / §3.9（新增）/ §7.3 加注 Track C engineering-workflow 共享 A1-A6 hygiene 门禁。

---

## 0. 范围（v1.1 加注）

| 类型 | 默认 track | Authoring 章节 |
|---|---|---|
| GUIDE | code | §3.1 |
| ADR-code | code | §3.2 |
| SPEC-code | code | §3.3 |
| RUNBOOK | code | §3.4 |
| POSTMORTEM-code | code | §3.5 |
| STANDARD-code | code | §3.6 |
| ISSUE-code | code | §3.7 |
| ASSESSMENT-code | code | §3.8 |

跨轨（`track: shared`）文档：本框架 §7.1 校验仍执行；§3 章节按对应类型走；额外审阅角色见 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] §跨轨治理协议。

> **v1.1 加注**：第三轨（`track: engineering-workflow`，Meta v2.1 引入）的 canonical 资产**也共享本框架 §7.1 A1-A6 hygiene 门禁**（路径 / frontmatter / state / Wikilink / INDEX / CLAUDE.md sync）—— 这些是通用 hygiene 检查，与 track 失败模式无关。但 engineering-workflow 资产的**专属阻塞门禁**（A12-A14）由 Meta v2.1 §7.7 治理，不属本框架。
>
> 简言之：A1-A6 通用；本框架的"代码侧专属"治理只对 §0 表内 8 类生效。

---

## 1. 设计目标

承接 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.1]] §1，针对代码侧补充：

| 原则 | 说明 |
|---|---|
| 代码-文档双向追溯 | 沿用 v1.0 §1 |
| 失败响亮 | 沿用 v1.0 §1 |
| 审阅角色单一 | 沿用 v1.0 §1（SWE Reviewer 充分） |
| 继承自 mj-system v5.0 | 沿用 v1.0 §1 |
| **与 Track C 协同**（v1.1 加注） | 代码侧 ADR / SPEC 引入 CI hook、build script、部署流程时，应交叉引用 engineering-workflow 子规范（HITL_Prompt v1.0 / Claude_Code_Settings / MCP_Server_Governance）作为 Stage 8 Implementation 的执行依据 |

---

## 2. 派生关系

- 大部分规则继承自 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.1]] §3-§6（命名 / Frontmatter / 状态生命周期 / 索引）
- 部分规则间接继承自 mj-system v5.0；本框架自包含使用，不强求读 v5.0
- 8 类继承类的 frontmatter / body 模板沿用 [[../_templates/TEMPLATE_ADR|TEMPLATE_ADR]] 等（Phase A PR-A3 补 RUNBOOK / SPEC / HITL_STAGE 模板）

---

## 3. 类型 Authoring 章节

> 沿用 v1.0 §3 全部规则。各章节内容沿用 v1.0；Phase 1 主体填充。**新增 §3.9**（v1.1）。

### 3.1 GUIDE Authoring

沿用 [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|v1.0]] §3.1（含 §3.1.1 frontmatter / §3.1.2 body 骨架 / §3.1.3 复用原则 / §3.1.4 实例参考）。

### 3.2 ADR-code Authoring

> **TODO Phase 1**（沿用 v1.0 §3.2）：
> - 沿用 [[../_templates/TEMPLATE_ADR|TEMPLATE_ADR]]
> - code-track 特有：决策应在 PR 内同步实施
> - 引用：v1.1 archive §3.2

### 3.3 SPEC-code Authoring

> **TODO Phase 1**（沿用 v1.0 §3.3）。Phase A PR-A3 落地 `TEMPLATE_SPEC.md`。

### 3.4 RUNBOOK Authoring

> **Phase A PR-A3 落地 `TEMPLATE_RUNBOOK.md`**。body 模板：`Trigger / Pre-checks / Steps / Rollback / Post-mortem trigger`。

### 3.5 POSTMORTEM-code Authoring

> **TODO Phase 2**（沿用 v1.0 §3.5）。

### 3.6 STANDARD-code Authoring

> **TODO Phase 1**（沿用 v1.0 §3.6）。现有范例：
> - [[STANDARD]_GitHub_Markdown|GitHub_Markdown_v1.0]]
> - [[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit_Message_Convention_v1.0]]

### 3.7 ISSUE-code Authoring

> **TODO Phase 1**（沿用 v1.0 §3.7）。

### 3.8 ASSESSMENT-code Authoring

> **TODO Phase 1**（沿用 v1.0 §3.8）。现有范例：[[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|MJ_System_Git_Conventions_Adoption_v1.0]]。

### 3.9 Track C engineering-workflow cross-ref（v1.1 新增）

代码侧文档（特别是 ADR-code / SPEC-code / RUNBOOK）涉及以下场景时，应在 `## References` 段交叉引用 engineering-workflow 子规范作为 `Consult If Affected`：

| 代码侧场景 | 引用 engineering-workflow STANDARD |
|---|---|
| 新增 CI hook（pre-commit / `.github/workflows/*.yml` 修改） | [[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt\|HITL_Prompt v1.0]] §4.10 Stage 10 Local Verification（PR-A2 落地后激活） |
| 引入 / 删除 MCP server | [[STANDARD]_MJ_Agent_MCP_Server_Governance_v1.0\|MCP_Server_Governance v1.0]]（Phase C+ 落地后激活） |
| 改动 `.claude/settings.json` 共享配置 | [[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0\|Claude_Code_Settings v1.0]]（Phase C+ 落地后激活） |
| 引入 / 修改 `.claude/hooks/**`（Phase C+ 启用后） | 待定 hooks 子规范（Phase C+） |
| 部署流程涉及 Claude Code 自动化 | HITL_Prompt v1.0 §4.7 Stage 7 + §4.8 Stage 8 |

> **不强制双向**：engineering-workflow STANDARD 自然承担 ADR/SPEC 角色时，可不反向引用代码侧 STANDARD（避免循环引用），由 PR reviewer 判断必要性。

---

## 7. PR 校验门禁

### 7.1 阻塞式检查（A1-A6，全部 track 共享）

沿用 [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|v1.0]] §7.1 全部 A1-A6 定义。**适用范围扩到全部 track**（v1.1 加注，与 Meta v2.1 §7.1 一致）：

| 编号 | 检查项 | 适用 track | 自动化阶段 |
|---|---|---|---|
| A1 | 路径与文件名合法 | **code / agent / engineering-workflow / shared** | Phase 2 CI |
| A2 | Frontmatter schema 完整 | code / agent / engineering-workflow / shared | Phase 2 CI |
| A3 | state 与专属字段枚举合法 | code / agent / engineering-workflow / shared | Phase 2 CI |
| A4 | 内部链接目标存在 | code / agent / engineering-workflow / shared | Phase 2 CI（沿用 `scripts/check_wikilinks.py`） |
| A5 | INDEX.md 已同步或可重建 | code / agent / engineering-workflow / shared | Phase 2 CI |
| A6 | allowlist 文档变更同步检查 CLAUDE.md | code / agent / engineering-workflow / shared | Phase 0 PR review（沿用） |

> **engineering-workflow 专属补丁**：A2 schema 完整在 `track: engineering-workflow` + 路径 `.claude/skills/**` 时，schema 是 ADR-013 native 2 字段（`name` + `description`），不是 13 字段。详见 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] §3.10.1 + §7.7 A12。

### 7.2 非阻塞式观察 OB1-OB5

沿用 v1.0 §7.2 全部 5 项。Phase 1 阈值定稿；engineering-workflow track 资产同样适用 OB1-OB5（文档长度 / 时态 / 内容边界 / 摘要质量 / 内部一致性）。

### 7.3 跨轨文档（`track: shared`）的处理（v1.1 加注三轨）

`track: shared` 文档由 Meta v2.1 + 本框架 §7.1 + [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]] §7.1 + Meta v2.1 §7.7（engineering-workflow A12-A14）共同执行：

- A1-A6（hygiene）由本框架，对全部 track 生效
- A7-A11（agent-side 专属）由 Agent_Side，仅对 `track: agent` 或 `track: shared` 触及 SKILL/PROMPT/EVAL/CONTRACT 时生效
- A12-A14（engineering-workflow 专属）由 Meta v2.1 §7.7，仅对 `track: engineering-workflow` 或 `track: shared` 触及 `.claude/**` / `.mcp.json` 时生效

审阅角色见 §8。

---

## 8. 审阅角色

- **必要**：SWE Reviewer 一名
- **可选**：Domain Expert（特定 ADR / SPEC 触及业务时）
- **跨轨文档**：双轨 reviewer 都需介入（SWE + Domain Expert + Prompt Engineer）
- **`track: shared` + 涉及 engineering-workflow 资产**（v1.1 加注）：再加 Tooling Reviewer（熟悉 `.claude/skills/` / HITL_Prompt 流程的 SWE）

---

## 9. Plugin 关联

沿用 v1.0 §9 全部 4 skill 表。**v1.1 加注**：

`mj-agent-code-doc` plugin（marketplace）治"代码侧文档撰写"工作流；与本 v1.1 引入的 engineering-workflow track（in-tree `.claude/skills/`）形成对位：

| 维度 | mj-agent-code-doc（marketplace plugin） | in-tree `.claude/skills/mj-agent-doc-*`（v2.1 引入） |
|---|---|---|
| 物理位置 | `mj-agentlab-marketplace/plugins/mj-agent-code-doc/` | `.claude/skills/mj-agent-doc-*/`（PR-B4 起落地） |
| 跨项目复用 | ✅ 任意 mj-agent-* 仓 | ❌ 仅 mj-agent 仓 |
| Stage 集成 | 通用 | 与 HITL_Prompt v1.0 §4.6 stage 6 紧耦合 |
| Schema | ADR-013 native（已确立） | ADR-013 native（同样） |

两者**共存**，详见 [[../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]（PR-B1 落地）+ [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]。

---

## 参考

- 派生自：[[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|v1.0]]
- 上层：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.1]]
- 决策记录：
  - [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]（双轨原始决策）
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]（v1.1 同期 tri-track 升级）
- 同期子框架：[[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]
- Track C 引用（cross-ref 用）：
  - `[[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt]]`（PR-A2）
  - `[[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0]]`（Phase C+）
  - `[[STANDARD]_MJ_Agent_MCP_Server_Governance_v1.0]]`（Phase C+）
- 现有 Code_Side STANDARDs（沿用）：
  - [[STANDARD]_GitHub_Markdown]]
  - [[STANDARD]_MJ_Agent_Commit_Message_Convention]]
