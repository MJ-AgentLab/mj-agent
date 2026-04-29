---
type: standard
domain: SYS
summary: Track A 代码侧文档治理 — GUIDE/ADR-code/SPEC-code/RUNBOOK/POSTMORTEM-code/STANDARD-code/ISSUE-code/ASSESSMENT-code 的 authoring 深度规则；A1-A6 + OB1-OB5
owner: 项目负责人
created: 2026-04-27
updated: 2026-04-29
state: active
version: v1.0
track: code
derives_from: mj-agent@[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0
tags:
  - standard
  - documentation
  - track-a
  - code-side
  - skeleton
aliases:
  - MJ-Agent Code-Side Documentation Framework v1.0
  - Track A 子框架 v1.0
---

# MJ-Agent 代码侧文档治理框架 v1.0（Track A）

> **骨架状态（Phase 0.5）**：以 `state: draft` 落地，与 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] 同期 promote 为 active（[[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-3）。
> **职责**：治理 Track A 文档（GUIDE / ADR-code / SPEC-code / RUNBOOK / POSTMORTEM-code / STANDARD-code / ISSUE-code / ASSESSMENT-code）的 authoring 深度规则与 PR 校验。
> **不**治理：4 类自有（SKILL / PROMPT / EVAL / agent-facing CONTRACT）—— 见 [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side]]。
> **派生自**：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]]

---

## 0. 范围

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

跨轨（`track: shared`）文档：本框架 §7.1 校验仍执行；§3 章节按对应类型走；额外审阅角色见 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework]] §跨轨治理协议（TODO Phase 1）。

---

## 1. 设计目标

承接 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] §1，针对代码侧补充：

| 原则 | 说明 |
|---|---|
| **代码-文档双向追溯** | 代码 PR 同 PR 内更新对应 ADR / SPEC / GUIDE；不容许"代码已变、文档未跟"长期存在 |
| **失败响亮** | 代码 bug 通过 build / test / deploy 链路放大；与 Track B 的沉默失败相反 |
| **审阅角色单一** | SWE Reviewer 充分；不强制 Domain Expert（除非 ADR / SPEC 触及业务） |
| **继承自 mj-system v5.0** | 本框架自包含；间接继承 mj-system v5.0 的成熟实践，但不要求读者读 v5.0 |

---

## 2. 派生关系

- 大部分规则继承自 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] §3-§6（命名 / Frontmatter / 状态生命周期 / 索引）
- 部分规则间接继承自 mj-system v5.0；本框架自包含使用，不强求读 v5.0
- 8 类继承类的 frontmatter / body 模板沿用 [[../_templates/TEMPLATE_ADR|TEMPLATE_ADR]] 等（Phase 1 补 GUIDE / RUNBOOK 等模板）

---

## 3. 类型 Authoring 章节

> **骨架阶段（Phase 0.5）**：各章节仅含 TODO 占位 + 引用回 v1.1。Phase 1 主体填充。

### 3.1 GUIDE Authoring

> **TODO Phase 1**：
> - body 模板：`Purpose / Prerequisites / Steps / Verification / Troubleshooting`
> - 沿用 v1.1 §3.2 GUIDE 类定义；增补字段表与示例
> - 配套 `docs/_templates/TEMPLATE_GUIDE.md`（Phase 0.5 不存在，Phase 1 创建）

引用：v1.1 §3.2

### 3.2 ADR-code Authoring

> **TODO Phase 1**：
> - 沿用 [[../_templates/TEMPLATE_ADR|TEMPLATE_ADR]]（已存在）
> - code-track 特有：决策应在 PR 内同步实施；不允许"决策接受、代码未改"
> - 引用：v1.1 §3.2 ADR 类定义

现有 ADR-code 范例：[[../adr/[ADR]_001_Python_Only_Agent_Runtime|ADR-001]]、[[../adr/[ADR]_008_Co_Deployment_With_MJ_System|ADR-008]]、[[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]

### 3.3 SPEC-code Authoring

> **TODO Phase 1**：body 模板与 frontmatter 字段表

### 3.4 RUNBOOK Authoring

> **TODO Phase 0.5 末 / Phase 1**（与 [[../../plans/[PLAN]_D_Setup_Env_Scripts|PLAN D]] 协同）：
> - body 模板：`Trigger / Pre-checks / Steps / Rollback / Post-mortem trigger`
> - 配套 `docs/_templates/TEMPLATE_RUNBOOK.md`（v1.1 §8.2 已声明 Phase 0.5 补）

### 3.5 POSTMORTEM-code Authoring

> **TODO Phase 2**：
> - code-track 事故：编译错 / 部署中断 / 服务宕机 / 性能回归
> - 区别于 Agent_Side 的 POSTMORTEM-agent（输出错答案 / 幻觉 / 业务决策偏差）
> - body 模板：`Timeline / Root Cause / Resolution / Action Items`

### 3.6 STANDARD-code Authoring

> **TODO Phase 1**：
> - 现有范例：
>   - [[STANDARD]_GitHub_Markdown_v1.0|GitHub_Markdown_v1.0]]
>   - [[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0|Commit_Message_Convention_v1.0]]
> - 这两份在 v1.1 → v2.0 升级时增补 `track: code` 字段
> - 跨轨规则的 STANDARD（如 Meta_Framework 自身）归 Meta 治理

### 3.7 ISSUE-code Authoring

> **TODO Phase 1**：
> - 沿用 v1.1 §3.2 ISSUE 类定义 + 专属字段（`priority`、`resolution`）
> - code-track 特有：与代码 issue tracker 关联（GitHub Issue / Jira）

### 3.8 ASSESSMENT-code Authoring

> **TODO Phase 1**：
> - 现有范例：[[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|MJ_System_Git_Conventions_Adoption_v1.0]]
> - body 模板：`Background / Dimensions / Findings / Keep / Adapt / Defer`

---

## 7. PR 校验门禁

### 7.1 阻塞式检查（A1-A6，Code_Side 范围）

沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §7.1 的 A1-A6 定义：

| 编号 | 检查项 | 自动化阶段 |
|---|---|---|
| A1 | 路径与文件名合法 | Phase 2 CI |
| A2 | Frontmatter schema 完整 | Phase 2 CI |
| A3 | state 与专属字段枚举合法 | Phase 2 CI |
| A4 | 内部链接目标存在 | Phase 2 CI |
| A5 | INDEX.md 已同步或可重建 | Phase 2 CI |
| A6 | allowlist 文档变更同步检查 CLAUDE.md | Phase 0 PR review（沿用） |

> **TODO Phase 1**：每条 A 项的 schema / 实现细节细化（继承 mj-sys-doc plugin 的 `validate_doc.py` 思路）。

### 7.2 非阻塞式观察 OB1-OB5（v1.0 引入，解 Meta v1.1 Gap A9）

mj-system v5.0 §7.2 定义了 5 项非阻塞观察项；mj-agent v1.1 漏继承。本 v1.0 显式引入：

| 编号 | 观察项 | 备注 |
|---|---|---|
| OB1 | 文档长度区间提示 | TODO Phase 1：定义 GUIDE/RUNBOOK/SPEC 的推荐长度区间（参考 mj-system v5.0） |
| OB2 | 时态一致性 | TODO Phase 1 |
| OB3 | 内容边界（不偏离 frontmatter `summary`） | TODO Phase 1 |
| OB4 | 摘要质量（`summary` 字段是否清晰） | TODO Phase 1 |
| OB5 | 内部一致性（同一文档 PR 内陈述不矛盾） | TODO Phase 1 |

详细规则与判定阈值：Phase 1 移植 mj-system v5.0 §7.2 + 按 mj-agent 实际调整。

### 7.3 跨轨文档（`track: shared`）的处理

`track: shared` 文档由本框架 §7.1 + [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side]] §7.1 共同执行：A1-A6 由本框架；A7-A10 + A11 + §7.5 由 Agent_Side。审阅角色见 §8。

---

## 8. 审阅角色

- **必要**：SWE Reviewer 一名
- **可选**：Domain Expert（特定 ADR / SPEC 触及业务时）
- **跨轨文档**：双轨 reviewer 都需介入（SWE + Domain Expert + Prompt Engineer）

---

## 9. Plugin 关联

本框架的执行工具是 `mj-agent-code-doc` plugin（marketplace `mj-agentlab-marketplace/plugins/mj-agent-code-doc/`）。**2026-04-29 sequencing 更新**：`plan` + `author` 两 skill 提前到 Phase 0.5 部分骨架（原全推迟 Phase 1）；`validate` + `sync` 仍 Phase 1（依赖 §7.2 OB1-OB5 阈值定稿 + §7.6 `.claude/` 边界细化）。详见 [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-5 Revision banner；marketplace 仓内容蓝图见独立 PLAN（`temp-ai-chat/mj-agentlab-marketplace/[PLAN]_Marketplace_Plugin_Construction.md`）。

| Skill | 章节对应 | Phase |
|---|---|---|
| `mj-agent-code-doc-plan` | 跨章节（Track A 文档治理需求规划） | **Phase 0.5（部分骨架）** |
| `mj-agent-code-doc-author` | §3.1-§3.8（按 type dispatch 处理 8 继承类） | **Phase 0.5（部分骨架）** |
| `mj-agent-code-doc-validate` | §7.1（A1-A6）+ §7.2（OB1-OB5） | Phase 1 |
| `mj-agent-code-doc-sync` | Meta v2.0 §6（INDEX 同步 + CLAUDE.md `Code-Side` 段维护） | Phase 1 |

---

## 参考

- 派生自：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]]
- 间接继承：mj-system v5.0
- 决策记录：[[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]
- 同期子框架：[[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side v1.0]]
- 实施计划：[[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]]
- 现有 Code_Side STANDARDs（升级时补 `track: code`）：
  - [[STANDARD]_GitHub_Markdown_v1.0]]
  - [[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0]]
