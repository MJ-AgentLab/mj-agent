---
type: adr
domain: WORKFLOW
summary: Codex 由「只读外部评审 / 非参与」升为完整开发参与者（可运行命令 + 编辑 / 提交 / 迁移，受同一 HITL 必停 + 数据边界约束）；本 ADR 仅反转书面政策，技术使能（插件 + 权限 wiring）延后为独立 opt-in，硬前置 = 先定义 Codex 如何 honor 5 必停面 + HITL gates；使能前 Claude Code 仍是唯一 active implementer；数据边界 ADR-006/009/000 不变；revise ADR-031 Phase M0 写入 AGENTS.md + ai-agent §1 的「Codex 非参与」native 内容
owner: ranzuozhou
created: 2026-07-06
updated: 2026-07-06
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - codex
  - ai-agent
  - workflow
  - roster
---

# ADR-035: Codex Promoted to Full Development Participant

## Context

mj-agent 自 ADR-031 Phase M0 起把 Codex 定位为「**只读外部评审工具、非开发参与者**」，并把该
边界作为 native 内容直接写进 `AGENTS.md`（Roster + Codex Boundaries + "If you are a
non-Claude-Code agent" 段）与 `policies/ai-agent.md §1`（"Codex 非参与策略层"，标注 native /
最高优先级）。核心禁令：Codex MUST NOT 运行任何 test 或 command、不修改文件、不 commit / push、
不迁移、不改 CI / config；每次任务输出须声明 `Codex invocation: NONE`。

该边界当时的四条 rationale：单一问责（Claude Code session 连续性）、工具执行面受控（单 agent
permission model 易审计）、4 项 in-source 专属必停须单一 decision-maker enforce、CLAUDE.md HITL
规则按 Claude Code 读写契约校准。

**驱动**：项目负责人（Owner）决策解除「Codex 不得运行命令」的限制，并进一步把 Codex 提升为
**完整开发参与者**（可运行命令 + 编辑 / 提交 / 迁移），使其与 Claude Code 同属实施 agent。

`AGENTS.md §Future evolution` 自述：把新 AI agent 纳入开发流程须 `ADR + AGENTS.md 更新 +
CLAUDE.md 更新 + Owner HITL 拍板`。本 ADR 即该流程要求的决策锚。[[ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]
（HITL propose→拍板→apply）是结构同类的「谁可落盘」反转先例。

**现状事实（勘查确认）**：该边界**纯属书面 / 治理约束**——无 hook / CI gate /
`settings.json` deny / MCP / plugin 配置强制它；仓库根本未接入任何 Codex 工具
（`.claude/plugins.json` 未启用 codex 插件、`.mcp.json` 无 codex server、`.claude/settings.json`
无 codex 权限）。故仅反转书面政策不会让 Codex 真的能运行命令；实际技术使能是独立、additive 的动作。

## Decision

1. **Codex 升为完整开发参与者**：Codex 由「只读外部评审 / 非参与」升为**完整开发参与者**——可
   运行命令（tests / builds / git / docker）、编辑 / 新建 / 删除文件、commit / push、迁移、改
   CI / config，**与 Claude Code 同一授权类**。相应地，**授权对等 → 约束对等**：Codex 同样受
   mj-agent 全部 HITL 必停（`policies/ai-agent.md §4` canonical 10-enum）+ 数据边界
   （[[ADR-006_Fail_Safe_Reads|ADR-006]] / [[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]] /
   ADR-000）约束——授权对等不放宽任何安全面。

2. **Scope = 仅书面政策边界**。本 ADR 只反转 `AGENTS.md` + `policies/ai-agent.md §1` +
   `CLAUDE.md §Codex Status` 的书面姿态。**技术使能**——注册 codex 插件（`.claude/plugins.json`）、
   授予工具权限（`.claude/settings.json`）、任何 runtime / MCP wiring——是**独立、延后的
   opt-in**，本 ADR 不做。

3. **使能前 Claude Code 仍是唯一 active implementer**。因技术使能延后，Codex 目前**并未接入、
   无法真正运行命令**；实践上 Claude Code 仍是唯一在跑的实施 agent。文档须把「**已授权**（书面）/
   **尚未接入**（技术）/ **CC 仍唯一 active**」三层说清，避免「Codex 已在协同开发」的误导。

4. **技术使能的硬前置（重要连贯点）**：现有 4 项 in-source 专属必停的 `.claude/settings.json`
   `ask` 门 + protected-path 强制权限 prompt 是 **Claude Code harness 专属**机制；Codex 运行在
   不同 harness 下**不受其自动约束**。故未来做技术使能前**必须先定义 Codex 如何 honor 5 必停面
   （4 in-source + `.mcp.json` trust posture）+ HITL gates + 数据边界**（Codex 侧等价 enforcement），
   否则不得 wiring。使能本身届时另立 ADR / 走 protected-path 拍板 + A13 / A14，不在本 ADR 覆盖。

5. **问责模型（重述原四条 rationale）**：
   - 单一问责 → 改为「**Owner 仍是唯一决策者**（HITL 拍板）+ 每 PR 声明由哪个 agent 实施 +
     git authorship 记溯源」；实施可双 agent，决策与验收单点不变。
   - 工具执行面 → 两实施 agent **共用同一 permission model / 数据边界**；Codex 使能后须在等价
     guardrail 下运行（见第 4 点）。
   - 4 项专属必停 → 仍由 HITL 拍板 enforce（第 4 点把「Codex 如何被同样拦」列为使能硬前置）。
   - CLAUDE.md HITL 契约按 Claude Code 校准 → Codex 需要自己的校准契约，由 `AGENTS.md` 承载
     （本 ADR 起 AGENTS.md 从「禁令清单」转为「Codex 参与契约」）。

6. **声明纪律 reframe**：`policies/ai-agent.md §1` / PR 模板原「必声明 `Codex invocation: NONE`」
   改为「每任务 / PR **声明 Codex 参与情况**（`NONE` 或描述其具体贡献）」。因技术使能延后，当下
   该声明仍恒为 `NONE`——但语义由「Codex 被禁」变为「本次 Codex 未参与」。

7. **数据边界不变**（收口）：本 ADR 改的是「**谁可实施 / 谁可运行命令**」，**非**「可访问什么
   数据」。ADR-006 四层 SQL guardrail / ADR-009 biz 域 only / ADR-000 三原则**不放宽**——Codex
   使能后同样受这四层约束。

8. **修订声明**：本 ADR **revise** ADR-031 Phase M0 直接写入 `AGENTS.md` +
   `policies/ai-agent.md §1`（"Codex 非参与策略层"）的 native 内容。不 supersede 任何 Codex 专属
   ADR（不存在）。`AGENTS.md §Future evolution` 的「纳入新 agent 须 ADR + 文档更新 + Owner 拍板」
   流程**保留**，适用于未来其他 agent。

## Consequences

- **正面**：解除「Codex 不得运行命令」的 Owner 目标达成；`AGENTS.md` 从单纯禁令清单升级为
  「Codex 参与契约」，为未来真正引入 Codex 协作留好书面地基；决策有 ADR 可追溯，符合仓库
  §Future-evolution 自述流程。
- **负面**：书面政策与技术现实之间出现「**已授权但未接入**」的 gap 窗口——须靠文档三层措辞
  （Decision 3）+ 使能硬前置（Decision 4）守住，避免误读为「Codex 已可协作」。原「单一实施 agent」
  的审计简洁性在未来使能后下降（two implementers）；本 ADR 以「Owner 单一决策 + 对等约束 + 使能
  硬前置」补偿，但真正的 Codex 侧 enforcement 设计留待使能 ADR。
- **中性**：当下**无运行时 / 行为变化**——Codex 仍未接入，Claude Code 仍是唯一 active implementer，
  `Codex invocation` 声明仍恒 `NONE`。本次为 docs-only 变更，不触任何代码 / 配置 / CI。

## Alternatives considered

- **A. 仅放宽命令子句（Codex 可跑只读命令、仍不可写）**：拒绝。Owner 拍板选「完整开发参与者」
  （Q1），非仅命令子句；只读命令中间态非本次意图。
- **B. 本 ADR 同时做技术使能（启用插件 + 授权）**：延后（作为「未来」保留）。Owner 拍板「仅改
  政策 / 文档」（Q2）；且使能是 additive + protected-path（A13 / A14）+ 须先定义 Codex 侧必停
  enforcement（Decision 4），不宜与政策反转同 PR。
- **C. 轻量文档改动、不立 ADR**：拒绝。`AGENTS.md §Future-evolution` + ADR-034 先例均要求「改
  agent 角色须立 ADR + Owner 拍板」；跳过 ADR 则决策无记录且偏离仓库自述流程。
- **D. 维持「Codex 非参与」边界**：拒绝。与 Owner 指令直接冲突。

## References

- [[ADR-031_Spec_Anchored_Refactor|ADR-031]] — 本 ADR revise 的 Phase M0 native 内容来源
  （AGENTS.md + ai-agent §1 的「Codex 非参与」）
- [[ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]] — 结构同类「谁可落盘」反转先例；问责 /
  HITL propose→拍板→apply 模型
- [[ADR-006_Fail_Safe_Reads|ADR-006]] / [[ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]] /
  ADR-000 — 数据边界**不变**（本 ADR 改「谁可实施」非「可访问什么」）
- [[../AGENTS|AGENTS]] — Roster + Codex 参与契约（本 ADR 起由禁令清单改写）+ §Future evolution
- [[../policies/ai-agent|policies/ai-agent]] §1（Codex 参与策略层）/ §4（HITL 10-enum，Codex 同样
  受约束）/ §7（pre-flight，去「只读」限定）
- `.claude/plugins.json` / `.claude/settings.json` / `.mcp.json` — 技术使能延后目标（本 ADR 不改）
