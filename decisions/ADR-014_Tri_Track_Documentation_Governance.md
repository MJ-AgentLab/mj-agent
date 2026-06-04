---
type: adr
domain: SYS
summary: 决议引入第三轨 engineering-workflow（治理 .claude/ + HITL_Prompt + 工程流程 STANDARD），与 v2.0 双轨并行；A12-A14 PR 门禁加入；mj-agent-* 命名空间；skeleton-first 落地（v2.1 trio + ADR-014 初次 draft，Phase B promote）
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-08
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - tri-track
  - engineering-workflow
  - architecture
  - skeleton
---

# ADR 014: Tri-Track Documentation Governance v2.1

## Context

[[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] +  [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|Code_Side v1.0]] + [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side v1.0]]（"v2.0 trio"）2026-04-29 落地为 active 状态后，dual-track 治理体系（code / agent / shared）已运行 ~1 个月。但 v2.0 期间留下的两个未解决空白逐步显现：

### 空白 1：v2.0 §7.6 `.claude/` 边界长期 TODO

v2.0 §7.6 把 `.claude/` 整体出 governance 作为过渡条款，并标注 "TODO Phase 1 区分 marketplace 边界 vs 项目级 `settings.json`"。Phase 0.5 末以来：

- mj-agent 仓 `.claude/settings.json` + `.claude/settings.local.json` 已存在（团队共享 + 个人 override）；前者实际被 commit 但**没有治理**——allowlist 修改无 PR 评审标准、无变更说明强制要求
- `.claude/skills/` 目录在 mj-agent 仓**完全空白**（与 mj-system v5.0+ 35 in-tree skills 形成强烈反差）
- `.mcp.json` 暂未引入，但任何 MCP server 加入都需要治理框架兜底

### 空白 2：mj-system 工程流程编排范式未引入

mj-system 在 2026-05 期间沉淀出 `.claude/skills/mj-sys-flow-*` (9) + `mj-sys-doc-*` (7) + `mj-sys-git-*` (9) + `mj-sys-n8n-*` (7) + `mj-sys-ops-*` (4) 共 35 个 in-tree 工程流程编排技能，并以 `[STANDARD]_AI_Engineering_Execution_HITL_Prompt.md` v1.0（17-stage 闭环 + HITL gates 5/7/9/11/13）作为顶层规范。这套体系成熟、可派生。

mj-agent 项目负责人 2026-05-08 brainstorming 中确定要：

1. 把这套范式按 mj-agent 上下文派生（去 n8n / 去 ETL；加 runtime 类目治理 in-source SKILL/PROMPT 改动；加 infra 类目治理 Docker compose / studio probe 等）
2. 全部 in-tree（不走 marketplace；mj-system 风格）
3. HITL_Prompt 全量 17-stage 派生（不删减）
4. 框架本身升级为 tri-track（不只是加 STANDARD）

### 矛盾结论

如果不升级框架治理：

- `.claude/` 资产纳入 v2.0 后只能塞进 `track: code`（不准确——失败模式不是"编译/部署崩"，是"流程漂移"）或 `track: shared`（兜底但失去具体治理强度）
- HITL_Prompt v1.0 这种治"开发者使用 Claude Code 执行任务的工作流"的 STANDARD 在 v2.0 trio 找不到合适归属——它既不是 code 类（不影响 build / deploy），也不是 agent 类（不影响 runtime 输出）
- `.claude/skills/SKILL.md` 与 `src/mj_agent/skills/SKILL.md` 共享 type `[SKILL]` 但 schema / loader / reviewer 完全不同——v2.0 双轨没有显式区分通道

不加 ADR 锁定决策，下次有人按 v2.0 trio 起草新 .claude/ 资产时仍会落入"没合适 track"的尴尬。

---

## Decision

引入三轨治理 v2.1 架构，按 skeleton-first 原则演进（与 ADR-012 v2.0 升级节奏一致）。

### 决策点 1：v2.0 → v2.1 升级，引入第三轨 engineering-workflow

```
docs/rule/
├── [STANDARD]_..._Meta_Framework_v2.1.md            ← 元层（治跨轨规则；扩 track 允许值 + A12-A14）
├── [STANDARD]_..._Code_Side_Framework_v1.1.md       ← Track A 子框架（minor bump）
├── [STANDARD]_..._Agent_Side_Framework_v1.1.md      ← Track B 子框架（minor bump）
└── [STANDARD]_..._AI_Engineering_Execution_HITL_Prompt_v1.0.md   ← Track C 主 STANDARD（PR-A2 落地）
```

PR 校验门禁拆分（v2.0 → v2.1 增量）：

- A1-A6 hygiene：v2.0 已定，对**全部 track** 生效（沿用 Code_Side §7.1）
- OB1-OB5：v2.0 已定，对全部 track 生效
- A7-A11 agent-side：v2.0 已定，仅对 `track: agent` 触及 SKILL/PROMPT/EVAL/CONTRACT 时生效
- §7.5 frontmatter strip：v2.0 已定，仅对 `src/mj_agent/{skills,prompts}/**` 生效
- **A12-A14 engineering-workflow**（v2.1 新增）：仅对 `track: engineering-workflow` 触及 `.claude/**` / `.mcp.json` 时生效——见 Meta v2.1 §7.7

### 决策点 2：第三轨命名为 `engineering-workflow`

考虑过的备选：`workflow` / `tooling` / `claude-code` / `eng-workflow`。最终选 `engineering-workflow`，理由：

- 与 `code` / `agent` 同 noun phrase 风格（不是 acronym 也不是 brand）
- 明确语义：治"engineering 流程"，不是治"代码"也不是治"agent runtime"
- 不绑定具体工具（"claude-code" 会让未来切到其他 IDE 时改名；"engineering-workflow" 是稳定语义层）
- 与 mj-system HITL_Prompt §1.1 "AI 工程执行闭环" 措辞对齐

### 决策点 3：skeleton-first 演进（与 ADR-012 节奏一致）

- **Phase A（本 ADR 落地阶段）**：v2.1 trio（Meta v2.1 / Code_Side v1.1 / Agent_Side v1.1）+ ADR-014 + HITL_Prompt v1.0 + 模板补缺（RUNBOOK / SPEC / HITL_STAGE）以 `state: draft` 落地 `docs/rule/`，与 v2.0 trio（保持 active）共存；本 ADR-014 同期落地 `state: draft, decision: accepted`；不立即 archive v2.0 trio
- **Phase B 末**（PR-B3，核心 `.claude/skills/` 落地后；HITL_Prompt §5 矩阵不再指向占位）：promote PR——v2.0 trio → archive；v2.1 trio + HITL_Prompt v1.0 → active；CLAUDE.md / INDEX.md / 受影响引用一次性 audit
- **Phase C**：mj-agent 专属 skills（doc 完成 / runtime / infra）+ engineering-workflow 子规范（Claude_Code_Settings / MCP_Server_Governance）落地
- **Phase D**：Phase 2 alignment（EVAL framework / 模板补全 POSTMORTEM/ISSUE/ASSESSMENT/EVAL）

骨架内容真空率上限：≤30%（章节大纲 + TODO 之外的实质内容 ≥70%；与 ADR-012 §决策点 3 一致）。

### 决策点 4：边界 artifact 归属规则（预先写死）

| Artifact / 范例 | 归属 | 理由 |
|---|---|---|
| `.claude/settings.json`（项目级 in-tree） | `engineering-workflow` | 团队共享 Claude Code 配置 |
| `.claude/settings.local.json` | **出 governance** | 用户私有 override；不强治理 |
| `.claude/skills/mj-agent-flow-intake/SKILL.md` | `engineering-workflow` | in-tree 工程流程技能 |
| `.claude/scripts/*.ps1` | `engineering-workflow` | 工程流程辅助脚本 |
| `.claude/hooks/**`（Phase C+ 启用后） | `engineering-workflow` | 工具调用编排 |
| `.mcp.json` | `engineering-workflow` | MCP server 编排配置 |
| `~/.claude/**`（用户全局） | **出 governance** | 用户私有 |
| `mj-agentlab-marketplace/plugins/**` | **出本仓 governance** | marketplace 仓自治；ADR-013 已锁定边界 |
| `[STANDARD]_..._AI_Engineering_Execution_HITL_Prompt_v1.0` | `engineering-workflow` | 治工程流程 |
| `[STANDARD]_..._Claude_Code_Settings_v1.0`（Phase C+） | `engineering-workflow` | A13 阈值规范 |
| `[STANDARD]_..._MCP_Server_Governance_v1.0`（Phase C+） | `engineering-workflow` | A14 阈值规范 |
| `[STANDARD]_..._AI_Engineering_Intake_v1.0`（Phase B+ 可选） | `engineering-workflow` | 与 mj-system §4.1 同步 |
| `[STANDARD]_..._AI_Engineering_Repo_Scan_v1.0`（Phase B+ 可选） | `engineering-workflow` | 与 mj-system §4.4 同步 |
| ADR-014 / ADR-015 / ADR-016 自身 | `shared`（决策跨多 track）/ `engineering-workflow`（决策仅治 Track C） | ADR-014 跨 v2.0 trio + 新引入 Track C，归 `shared`；ADR-015/016 仅治 Track C，归 `engineering-workflow` |
| `src/mj_agent/skills/<name>/SKILL.md` | `agent`（不变） | in-source；ADR-013 + Agent_Side v1.1 §2 |
| `src/mj_agent/prompts/*.md` | `agent`（不变） | 同上 |

### 决策点 5：命名空间锁定 `mj-agent-<group>-<verb>`

`.claude/skills/<name>/` 中 `<name>` 强制使用 `mj-agent-<group>-<verb>` 三段式：

- `<group>`：5 类（详见 [[decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]，PR-B1 落地）
  - `flow`（编排 stage 0/3/4/8/9/10/11/15/17，~9 skills）
  - `git`（编排 stage 1/2/12/13/14/16/17，~9 skills）
  - `doc`（doc 创建 / 校验 / 同步 / 迁移，~6 skills）
  - `runtime`（**read-only inspect** in-source SKILL/PROMPT/biz_catalog；**永不写 src/**，~4 skills）
  - `infra`（env-setup / docker-compose / storage-stack / studio-probe，~4 skills）
- `<verb>`：动作短词（intake / commit / validate / studio-probe / skill-doc-improve 等）

slash command 自然成形 `/mj-agent-<group>-<verb>`。理由：

- 与 mj-system `mj-sys-*` 命名分流原则一致
- 不与 marketplace `mj-agent-code-doc-*`（含义清晰）冲突——marketplace 是仓外、跨项目；in-tree 是仓内、项目专用
- "mj-agent-" 前缀避免与 Claude Code 内置/superpowers 默认 skill 冲突

### 决策点 6：与 marketplace plugin 共存（不替代）

`mj-agentlab-marketplace/plugins/mj-agent-code-doc/`（已存在 `*-author` 与 `*-plan` 两个 skill）继续保留并使用，不被本 v2.1 in-tree `.claude/skills/mj-agent-doc-*/` 替代。两者关系：

| 维度 | marketplace `mj-agent-code-doc-*` | in-tree `.claude/skills/mj-agent-doc-*` |
|---|---|---|
| 物理位置 | marketplace 仓 | mj-agent 仓 `.claude/skills/` |
| 跨项目复用 | ✅ 任何 mj-agent-* 仓可装 | ❌ 仅 mj-agent 仓 |
| 内容耦合 | 通用文档治理（Documents-Driven-Development） | 与 HITL_Prompt v1.0 §4 stage 紧耦合（如 stage 6 SPEC/ADR/RUNBOOK 时调用） |
| Schema | ADR-013 native（已定） | ADR-013 native（同样） |
| 升级触发 | marketplace 仓 PR | mj-agent 仓 PR |

允许两者**有 30% 概念重叠**——marketplace 提供"通用 author"能力；in-tree 提供"stage 6 author"能力（含 mj-agent 特定 stage 上下文）。Phase D 后视使用情况决议是否需要进一步分工。

---

## Consequences

### 正面

- **`.claude/` 资产首次进入治理**：解 v2.0 §7.6 长期 TODO；A13/A14 让 settings.json + .mcp.json 不再"无人审"
- **Engineering-workflow 失败模式获专属治理强度**：流程漂移（HITL 跳过、错 skill）的修复责任明确归 Tooling Reviewer + SWE
- **HITL_Prompt v1.0 等工程流程 STANDARD 找到合适归属**：不再尴尬塞 `track: code`
- **mj-system 范式成功派生**：35 in-tree skills 编排结构 + 17-stage HITL_Prompt 直接复用，节省从零设计成本
- **解 v2.0 既有 gap**：§7.6 TODO 落实为 §7.7 正式条款；A12-A14 与 A1-A11 形成完整 PR gates
- **三种 SKILL 实体边界清晰化**：in-source（13 字段，agent）/ in-tree workflow（2 字段，engineering-workflow）/ marketplace plugin（2 字段，出本仓），由 §3.10 + ADR-013 共同锁定
- **skeleton-first 节奏验证**：与 v1.1 → v2.0（ADR-012）相同节奏，已被证明可行

### 负面

- **三 STANDARDs + 1 主规范（HITL_Prompt）维护成本**：v2.0 已是 3 STANDARD；v2.1 加 1 主规范 + Phase C+ 加 2-3 子规范（Claude_Code_Settings / MCP_Server_Governance / 可选 Intake / Repo_Scan），运营成本上升
- **过渡期混乱（Phase A → Phase B 末）**：v2.0 trio（active）+ v2.1 trio + HITL_Prompt（draft）共存约 2-3 周；新文档作者需明确知道当前权威版本（缓解：CLAUDE.md 顶部加 "skeleton-first 演进期" 提示 + INDEX.md 双行展示）
- **A12 描述质量门禁的人力成本**：每个 `.claude/skills/` skill 需 5-iteration trigger eval；32 skills 全套需 ~20 工时（缓解：批量化 + 借用 skill-creator skill）
- **runtime 类目的"read-only by design" 难以技术性强制**：`mj-agent-runtime-*` skills 通过 SKILL.md "Anti-patterns" 段约束 LLM 不写 src/；但 Claude Code 没有 per-skill 的 tool allowlist 隔离机制（缓解：A12 描述质量校验 + Anti-patterns 反复强化；Phase D 评估是否需要 hooks 兜底）

### 中性

- **ADR 编号占用**：ADR-014 / ADR-015（HITL_Prompt 派生）/ ADR-016（in-tree skills ecosystem）三个连续编号；ADR-017+ 留给后续。`v1.6 roadmap` 中后续 ADR 占用顺延（沿用 ADR-012 §中性 处理方式）
- **Phase B promote PR 推迟可能**：若 Phase B 核心 skills 长期不全绿，v2.1 trio + HITL_Prompt 持续保持 draft；不影响 v2.0 trio active 状态；可任意推迟无副作用
- **Track C 反向引用 v2.0 trio**：Meta v2.1 §3.10 依赖 ADR-013（v2.0 期间确立），不打破 v2.0 trio 任何规则；只是在其上加增量

### 风险

- **HITL_Prompt §4.1 / §4.4 引用占位的语义债**：HITL_Prompt v1.0 在 Phase A 落地时，stage 0 Intake / stage 3 Repo Scan 引用 mj-system 上游 STANDARD（`[[mj-system@docs/rule/[STANDARD]_AI_Engineering_Intake]]` / `[[mj-system@docs/rule/[STANDARD]_AI_Engineering_Repo_Scan]]`）作为占位；mj-agent 调版若 Phase B 后期发现差异过大，需追加 PR 派生 mj-agent 版（Lite Phase A 已确认；详见 [[../../C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon|外部 plan file]] §10 Open follow-ups）
- **mj-agent runtime SKILL/PROMPT 改动 Long-term：跨 ADR 决策风险**：本 ADR 决策点 5 把 `runtime/` 类目限定为 read-only inspect；如未来项目负责人需求"in-tree skill 能直接 propose + 一键 apply 修改 src/mj_agent/skills"，需另开 ADR 修订 read-only 约束（涉及 hooks 引入 + tool allowlist 设计）
- **A12 描述质量在多 skill 间漂移**：32 skills 的 description 在不同 phase 由不同人起草，trigger 风格可能不一致；缓解：PR-B1 起首 git family 5 P0 skill 的 description 作为 reference style；后续 PR 必须 sample 比对

---

## Alternatives considered

### 方案 I（Light）：仅加 STANDARD，不升级 Meta 框架

仅在 `docs/rule/` 落地 HITL_Prompt v1.0 + Claude_Code_Settings + MCP_Server_Governance 三 STANDARD，`track` 字段都用 `code`（兜底）；不引入第三轨。

**未采纳**：

- `track: code` 与失败模式不匹配（流程漂移 ≠ 编译/部署崩）
- A1-A6 hygiene 之外**没有专属阻塞门禁**（A12-A14 没地方挂）
- §7.6 TODO 仍是 TODO，没解决空白 1
- CLAUDE.md 只能在 `## Code-Side Documentation` 段塞 engineering-workflow 内容，结构不清晰

### 方案 II（Medium）：双轨 + STANDARD 但加专属门禁组

保留 v2.0 双轨 + 在 Code_Side 加 §3.9 "Engineering Workflow Authoring" 章节 + Code_Side 加 A12-A14 子门禁。

**未采纳**：

- `.claude/skills/` 资产塞进 Code_Side §3.9 概念上扭曲（它们既不是文档，也不是代码——是工作流编排的可执行 prompt）
- A12-A14 挂在 Code_Side 让 SWE Reviewer 承担过多——Tooling Reviewer 角色无法清晰浮现
- 长期方向不对：mj-system 已用三类（治、用、被治）的范式，mj-agent 走 Medium 方案会让未来再升级时多一次大改

### 方案 III（Heavy）：四轨（code / agent / engineering-workflow / infrastructure）

引入第四轨 `infrastructure` 治 Docker compose / `.github/workflows/` / `infra/**`。

**未采纳**：

- v2.0 已把 Docker compose / `.github/workflows/` 归 `track: code`，运行良好——失败模式确实是响亮（CI 红 / 部署失败）
- 拆 infrastructure 出来过度细分，增加治理成本
- mj-system 同期没有走四轨——保持与 mj-system 节奏对齐

### 方案 IV（marketplace 路线）：所有 in-tree 工程流程技能进 marketplace 而非 in-tree

把本 v2.1 提议的 32 个 `mj-agent-*` skills 全部放进 `mj-agentlab-marketplace/plugins/mj-agent-flow/` + `/mj-agent-git/` + `/mj-agent-doc/` + `/mj-agent-runtime/` + `/mj-agent-infra/` 5 个 plugin。

**未采纳**（用户在 brainstorming 中明确选择"全部 in-tree（mj-system 风格）"，理由）：

- mj-system 全 in-tree 已被证明可行（35 skills + 零配置激活）
- in-tree skills 与仓库版本绑定，不会有"marketplace 已升级但项目仍在用旧版"的版本漂移
- mj-agent 团队规模小（1 主要贡献者），跨项目复用价值低
- HITL_Prompt §5 矩阵直接引用 `/mj-agent-flow-intake` 而非 `/mj-agent-flow:intake`，slash command 命名空间扁平化（沿用 mj-system 2026-05-04 issue #260 的 namespace 扁平化经验）

### 方案 V（混合）：核心 in-tree + 边缘 marketplace

flow + git family in-tree（与项目流程紧耦合）；doc + runtime + infra family 进 marketplace。

**未采纳**：

- runtime + infra family 与 mj-agent 项目深度耦合（read-only src/ 约束 / 项目特定 storage stack 编排），不适合 marketplace 通用化
- 用户在 brainstorming 中明确选择"全部 in-tree"，本方案与 hybrid 方案 IV 类似已被预先排除

---

## References

- 直接前置：
  - [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]]（被 v2.1 升级）
  - [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|Code_Side v1.0]]（被 v1.1 minor bump）
  - [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side v1.0]]（被 v1.1 minor bump）
- 同期落地（PR-A1）：
  - [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta_Framework v2.1]]
  - [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.1|Code_Side v1.1]]
  - [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.1|Agent_Side v1.1]]
- 同期 Phase A 后续 PR：
  - PR-A2：[[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1_1|HITL_Prompt v1.1]] + [[[ADR]_015_HITL_Prompt_v1_0_Derivation|ADR-015]]
  - PR-A3：3 模板（RUNBOOK / SPEC / HITL_STAGE）
- Phase B 起首：[[decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] + git family 5 P0 skills
- 关联现有 ADR：
  - [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] —— 版本演进 + archive 工作流；本 v2.1 升级延迟 promote 即此模式变体
  - [[decisions/ADR-012_Two_Track_Documentation_Governance|ADR-012]] —— v1.1 → v2.0 双轨决策；本 v2.1 在其上加 Track C
  - [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] —— in-tree vs marketplace SKILL schema 分离；本 v2.1 §3.10 / §7.7 A12 直接引用
- 上游派生源（mj-system v5.0+）：
  - `mj-system/docs/rule/[STANDARD]_AI_Engineering_Execution_HITL_Prompt.md`（17-stage HITL 闭环）
  - `mj-system/docs/rule/[STANDARD]_Documentation_Management_Framework.md` v5.2（doc 治理框架；mj-agent v1.1 / v2.0 间接派生源）
  - `mj-system/.claude/skills/mj-sys-*/`（35 in-tree skills，5 family 编排范式）
- 用户互动证据：
  - 2026-05-08 brainstorming session：4 决策（建设侧 / skill 放置 / HITL 深度 / 框架重构）+ 2 follow-up（Phase A 范围 / v2.1 落地状态）
  - 外部 plan 文件：`C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon.md`
- 行业精度：
  - mj-system v5.0+ 已验证模式
  - Anthropic Skills 仓 in-tree pattern：`anthropics/skills` repo 结构
  - Claude Code plugin marketplace 与 in-tree 二元生态：[Claude Code docs](https://docs.claude.com/en/docs/claude-code/plugins.md)
  - HITL（Human-in-the-Loop）：MLOps Level 2 + AI Safety 标准做法
