---
type: standard
domain: SYS
summary: 元框架（v2.0 升级）—— 引入第三轨 engineering-workflow（治理 .claude/ 与工程流程 STANDARD），track 字段允许值扩到四值，A12-A14 PR 门禁加入；骨架交付 Phase A
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-09
state: deprecated
version: v2.1
track: shared
derives_from: mj-agent@archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0
supersedes:
  - "mj-agent@archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0"
tags:
  - standard
  - documentation
  - framework
  - meta
  - tri-track
  - engineering-workflow
aliases:
  - MJ-Agent Documentation Meta Framework v2.1
  - mj-agent 文档治理元框架 v2.1
archived: 2026-05-09
replaced-by: "../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md"
---

# MJ-Agent 文档治理元框架 v2.1（已归档；deprecated）

> [!warning]
> **本副本为 v2.1 历史归档（state: deprecated；archived: 2026-05-09）**。已被 [[../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.2（stable path）]] 取代。归档原因：v2.2 引入 §4.4 active canonical 路径稳定原则（[[../../adr/[ADR]_018_Active_Path_Stability|ADR-018]] 决议；partial supersede ADR-011 §4.2 + §5.6.2）+ filename rename 触发 [[../../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]] §5.9 trigger #4。本副本作为 v2.1 时期 cite-by-vintage 参考保留；当前权威以 v2.2 stable path 为准。

> **历史状态（Phase B PR-B3c-promote 完成后）**：`state: active`（已翻为 deprecated）。v2.0 trio 已 archive 至 `docs/archive/rule/` + `state: deprecated`。本文档及同期 [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]] / [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]] / [[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.0]] 全部转 active；A12-A14 PR 门禁强制启用。节奏对齐 [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] HITL A3 模式 + [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §决策点 3 skeleton-first。
> **派生自**：[[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0（archive）]]
> **首要变更**：引入第三轨 `engineering-workflow`（治理 `.claude/` + 工程流程 STANDARD + HITL_Prompt 类资产）+ A12-A14 PR 门禁 + §6.4.1 CLAUDE.md sync 三段化 + §7.6 `.claude/` 边界从 TODO 升级为正式条款
> **决策记录**：[[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]

---

## 0. v2.0 → v2.1 升级范围速览

| 维度 | v2.0 现状 | v2.1 目标态 |
|---|---|---|
| Track 枚举 | 3 值（`code` / `agent` / `shared`） | **+ `engineering-workflow`**（4 值；§4.3.1 更新） |
| 治理 artifact 范围 | 仅 `docs/**` + `src/mj_agent/{skills,prompts}/**` | **+ `.claude/skills/**` + `.claude/scripts/**` + `.claude/settings*.json` + `.claude/hooks/**` + `.mcp.json`**（§7.6 填实） |
| §7.1 PR 门禁 | A1-A6 + OB1-OB5 + A7-A11 | **+ A12-A14**（engineering-workflow 专属阻塞门禁；§7.7 引入） |
| §6.4.1 CLAUDE.md sync | 双轨分段（code / agent + 元规则） | **三轨分段**（code / agent / engineering-workflow + 元规则；§6.4.1 更新） |
| §7.6 `.claude/` 边界 | TODO Phase 1 占位 | **正式条款**：marketplace 私有仍出 governance；项目级 in-tree `.claude/` 纳入 engineering-workflow track 治理 |
| 类型枚举 | 12 类 canonical | **保留**（不改类型枚举；engineering-workflow track 主要治理 SKILL（in-tree workflow 形态）+ STANDARD（HITL_Prompt 类）+ ADR-eng-workflow） |
| Frontmatter 必填字段 | 通用 + 类型专属 | **保留**（不改字段集；track 仅多一个允许值） |
| 8 类继承类与 4 类自有 | 沿用 | **保留** |
| Code_Side / Agent_Side 同期版本 | v1.0 / v1.0 | **v1.1 / v1.1**（与本 v2.1 同 PR 落地，最小补丁） |

**不变项**（防止误读）：

- 类型枚举不变（仍 12 类 canonical）
- 字段集不变（仅 `track` 允许值多一个）
- §7.5 frontmatter strip 契约范围不变（仅治 `src/mj_agent/{skills,prompts}/**`，不扩到 `.claude/skills/**`）
- ADR-013 in-tree vs marketplace plugin schema 边界不变；本 v2.1 不让 §2（Agent_Side 13 字段 schema）扩到 `.claude/skills/`，详见 [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]] §2 scope note

---

## 1. 设计目标

> 元框架的职责是治"跨轨共同规则"，**不**治某一轨的具体内容深度。

承接 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §1 全部核心原则；新增三轨原则：

| 原则 | 说明 |
|---|---|
| 真实资产优先 | 见 v2.0 §1 |
| 目录即职责 | 见 v2.0 §1 |
| 真相源最小化 | 见 v2.0 §1 |
| 流程与文档解耦 | 见 v2.0 §1 |
| 生成优先于手工维护 | 见 v2.0 §1 |
| in-source 治理 | 见 v2.0 §1（仅扩到 `src/mj_agent/{skills,prompts}/**`，不扩到 `.claude/`） |
| 双轨分轨（v2.0） | Track A 代码侧 vs Track B 智能体侧；失败模式响亮 vs 沉默 |
| skeleton-first 演进（v2.0） | 见 v2.0 §1 |
| **三轨分轨**（v2.1 新增） | 在双轨之外引入 Track C engineering-workflow；治理"开发者使用 Claude Code 执行任务时"的工作流资产（`.claude/skills/` + HITL_Prompt + `.mcp.json`）；失败模式为**流程漂移**（HITL 跳过 / 错 skill / settings 退化），与 Track A 响亮失败和 Track B 沉默失败均不同 |
| **plugin loader 边界尊重**（v2.1 新增） | Track C 资产由 Claude Code 主进程 load，不经 mj-agent Python loader；§7.5 frontmatter strip 契约对其无效；Track C SKILL 仅用 ADR-013 native 2 字段 schema |

详见 [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §Context。

---

## 2. 三层文档模型

### 2.1 目录结构（v2.1 扩充）

```text
mj-agent/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── GLOSSARY.md
├── CLAUDE.md
├── .claude/                            # ← v2.1 纳入治理（仅 in-tree 项；marketplace 私有出 governance）
│   ├── settings.json                   # 项目级、提交到 git；A13 治理
│   ├── settings.local.json             # 用户私有、本地 override；不强治理（出 §7.1）
│   ├── skills/                         # engineering-workflow SKILL（mj-agent-* namespace；A12 治理）
│   ├── scripts/                        # 工程流程辅助脚本（如有）
│   └── hooks/                          # PreToolUse/PostToolUse 等（如有）
├── .mcp.json                           # MCP server 配置（A14 治理）
├── docs/                               # canonical 层
│   ├── INDEX.md
│   ├── _templates/
│   ├── adr/
│   ├── api/
│   ├── assessments/
│   ├── contracts/
│   ├── design/
│   ├── evaluation/
│   ├── guide/
│   ├── infrastructure/
│   ├── issues/
│   ├── postmortem/
│   ├── rule/                           # 含 v2.0 trio + v2.1 trio + HITL_Prompt + 工程流程 STANDARD
│   ├── runbook/
│   └── archive/
├── plans/                              # working 层
├── src/mj_agent/
│   ├── skills/<name>/SKILL.md          # canonical (in-source；Track B；不动)
│   └── prompts/*.md                    # canonical (in-source；Track B；不动)
└── evaluation/                         # Phase 2+
```

### 2.2 三层定义（v2.1 扩 canonical 路径覆盖）

| 层级 | 路径 | 作用 | 强治理 | 示例 |
|------|------|------|-----|------|
| **Canonical** | `docs/**`（排除 `archive/legacy/`）+ `src/mj_agent/{skills,prompts}/**` + **`.claude/skills/**`**（v2.1 加入）+ **`.claude/scripts/**`**（v2.1 加入）+ **`.claude/settings.json`**（v2.1 加入）+ **`.mcp.json`**（v2.1 加入） | 项目权威文档 / 工作流资产 | 是 | `[STANDARD]`、`[SKILL]`、`[ADR]`、`mj-agent-flow-intake/SKILL.md` |
| **Working** | `plans/**` | 任务计划 | 否，轻治理 | `[PLAN]_*.md` |
| **Legacy** | `docs/archive/legacy/**` | 历史材料 | 否，仅保留可读性 | 暂无 |

> **关键边界**：`.claude/settings.local.json` + `~/.claude/**`（用户全局）+ marketplace plugin（`mj-agentlab-marketplace/**`）**不**纳入本框架治理。详见 §7.6。

### 2.3 in-source canonical 设计理由

沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §2.3。仅治 `src/mj_agent/{skills,prompts}/**`；§7.5 frontmatter strip 契约只对此范围有意义。

### 2.4 分层规则（v2.1 加 Track C 行）

| 规则 | 正确 | 错误 |
|------|------|------|
| 权威文档进 canonical | `docs/rule/[STANDARD]_*.md` | `plans/[STANDARD]_*.md` |
| 运行时 skill 进 in-source canonical | `src/mj_agent/skills/biz-domain-context/SKILL.md` | `docs/design/skills/[SKILL]_*.md` |
| **工程流程 skill 进 in-tree `.claude/skills/`**（v2.1 新增） | `.claude/skills/mj-agent-flow-intake/SKILL.md` | `src/mj_agent/skills/mj-agent-flow-intake/`（混入运行时，loader 错装） |
| 任务计划进 working | `plans/[PLAN]_*.md` | `docs/plans/...` |
| 历史材料进 legacy | `docs/archive/legacy/<file>.md` | `docs/postmortem/<legacy-report>.md` |
| 版本退役进 archive subdir | `docs/archive/rule/[STANDARD]_..._v1.1.md` | `docs/rule/old/...` |

### 2.5 三轨子框架（v2.1 升级）

```
docs/rule/
├── [STANDARD]_..._Meta_Framework_v2.1.md            ← 元层（本文，v2.1）
├── [STANDARD]_..._Code_Side_Framework_v1.1.md       ← Track A（v2.0 → v1.1，与本 v2.1 同 PR 落地）
├── [STANDARD]_..._Agent_Side_Framework_v1.1.md      ← Track B（v2.0 → v1.1，与本 v2.1 同 PR 落地）
├── [STANDARD]_..._AI_Engineering_Execution_HITL_Prompt_v1.0.md   ← Track C 主 STANDARD（PR-A2 落地）
├── [STANDARD]_GitHub_Markdown.md               ← 归 Code_Side（治渲染语法）
└── [STANDARD]_..._Commit_Message_Convention_v1.0.md ← 归 Code_Side（治代码规约）
```

> **过渡期**：Phase A 期间 v2.0 trio（active）与 v2.1 trio（draft）共存；Phase B promote PR 后 v2.0 trio 转 archive。

---

## 3. 类型与目录

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §3 全部规则。**类型枚举不变**（12 类 canonical）；track 默认值表加 engineering-workflow 行：

| 类型 | 默认 track | 由哪个子框架治理深度规则 |
|---|---|---|
| GUIDE | code | [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.1 |
| ADR | shared（按主题决定） | Code_Side（code-ADR）/ Agent_Side（agent-ADR）/ **本框架（engineering-workflow-ADR，如 ADR-014/015/016）** |
| SPEC | shared | 同 ADR |
| RUNBOOK | code | Code_Side §3.4 |
| POSTMORTEM | shared | 按事件类型 |
| STANDARD | shared | Meta（治跨轨）/ Code_Side（治代码规约）/ **本框架（治 engineering-workflow，如 HITL_Prompt v1.0）** |
| ISSUE | shared | 按主题 |
| ASSESSMENT | shared | 按评估对象 |
| **SKILL** | **agent**（默认）/ **engineering-workflow**（路径 `.claude/skills/**` 时） | Agent_Side §3.1（in-source）/ **本框架 §3.10（v2.1 新增，engineering-workflow，仅引用 ADR-013 native schema）** |
| **PROMPT** | **agent** | Agent_Side §3.2 |
| **EVAL** | **agent** | Agent_Side §3.3 |
| **CONTRACT** | shared | Agent_Side（agent-facing tool）/ Code_Side（cross-service） |

### 3.5 目录归属优先级

沿用 v2.0 §3.5。**新增 0 号优先级**（v2.1）：

0. **Engineering-workflow 专属**：进入 `.claude/skills/<name>/`、`.claude/scripts/`、`.claude/hooks/`、`.claude/settings.json`、`.mcp.json`（不进入 `docs/` 或 `src/`）
1. Agent 专属（沿用 v2.0）
2. 子系统专属
3. 基础设施专属
4. 跨子系统 API 约定
5. 跨领域通用规则
6. 跨领域操作指南

### 3.6 新目录准入规则

沿用 v2.0 §3.6。**新增条目**（v2.1）：

| 规则 | 说明 |
|------|------|
| `.claude/skills/<group>/` 子目录可由 PR 直接新增 | 不需修订本元框架；仅需 ADR-016 接受 `mj-agent-*` namespace |
| `.claude/hooks/` 首次启用时需修订 §7.6.x（hooks 子条款，待 Phase C+） | hooks 影响所有工具调用，治理强度高 |
| `.mcp.json` server 增删需联动 `[STANDARD]_MJ_Agent_MCP_Server_Governance_*`（待 Phase C+） | A14 阻塞门禁 |

### 3.10 Engineering-workflow `[SKILL]` 治理（v2.1 新增）

> **scope**：仅治 `.claude/skills/<name>/SKILL.md`（in-tree 工程流程技能）。**不**治 `src/mj_agent/skills/<name>/SKILL.md`（运行时；归 [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]] §2）。**不**治 marketplace plugin SKILL.md（出 governance；详见 [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]）。

#### 3.10.1 Frontmatter schema（ADR-013 native）

```yaml
---
name: <mj-agent-group-verb>
description: <长 description；含 "Make sure to use this skill whenever..." 式触发短语；含"不适用于"反例；可中英双语>
---
```

**仅 2 字段**。不引入 Agent_Side §2 的 13 字段。理由见 [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] + 本框架 §1 plugin loader 边界尊重原则。

> **A12 阻塞门禁**：`description` ≥ 200 chars，含正向触发短语 + `Do not use for:` 反向触发段（与 marketplace 现存 mj-sys-* 4 plugin 风格一致）。校验由 Phase C+ engineering-workflow 子规范细化。

#### 3.10.2 Body 结构

参考 mj-system marketplace 现存 mj-sys-flow-* / mj-sys-doc-* / mj-sys-git-* skill 风格：

```markdown
## Overview
## When to Run This Skill（或 When to use）
## Workflow（步骤化；可含 graphviz/dot 流程图）
## Output Format（或 Quick Reference / Common patterns）
## Anti-patterns（可选）
```

不强制五段式（Agent_Side §2.1 的 Purpose / When to use / Planning workflow / Common patterns / Anti-patterns）。允许 per-skill 灵活调段；同一 group 内 skill 段名应一致。

#### 3.10.3 命名空间

强制前缀 `mj-agent-<group>-<verb>`：

- `<group>`：`flow` / `git` / `doc` / `runtime` / `infra`（5 类，详见 [[../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]，PR-B1 落地）
- `<verb>`：动作短词（`intake` / `commit` / `validate` / `studio-probe` 等）

slash command 自然成形 `/mj-agent-<group>-<verb>`。

#### 3.10.4 与 in-source SKILL 的区分

| 维度 | Track B（in-source） | Track C（in-tree workflow） |
|---|---|---|
| 路径 | `src/mj_agent/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` |
| 命名 | 无前缀（如 `biz-domain-context`） | `mj-agent-*` 前缀（如 `mj-agent-flow-intake`） |
| Schema | 13 字段（Agent_Side §2） | 2 字段（ADR-013 native） |
| Loader | mj-agent Python `load_skill()`，剥 frontmatter | Claude Code 主进程，不剥 |
| 失败模式 | 沉默（业务输出错） | 流程漂移（HITL 跳过、错 skill） |
| Reviewer | Domain Expert + SWE（≥2） | Tooling Reviewer + SWE |

---

## 4. 命名与 Frontmatter

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §4 全部规则。**仅扩 §4.3.1 `track` 字段允许值**：

### 4.3.1 track 字段（v2.1 扩值）

```yaml
---
...
track: code | agent | engineering-workflow | shared
---
```

| 取值 | 含义 | 默认值 |
|---|---|---|
| `code` | Track A — 代码侧文档（开发 / 部署 / 运维） | 见 §3 类型表 |
| `agent` | Track B — 智能体侧文档（runtime 直接影响业务） | 见 §3 类型表 |
| **`engineering-workflow`**（v2.1 新增） | Track C — 工程流程文档（`.claude/` + HITL_Prompt + 工程流程 STANDARD） | 见 §3 类型表（physical 路径在 `.claude/**` 或 `docs/rule/[STANDARD]_*_HITL_Prompt*.md` / `_AI_Engineering_*.md` / `_Claude_Code_Settings_*.md` / `_MCP_Server_Governance_*.md` 时强制） |
| `shared` | 跨轨 — 多 track reviewer 都需介入 | **过渡期**默认值；Phase 1 末收紧为 explicit required（沿用 v2.0） |

边界 artifact 归属规则见 [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §Decision 决策点 4。

> **path-to-track 决策树**（v2.1 引入，避免 PR 反复争议）：
> 1. 路径在 `src/mj_agent/{skills,prompts}/**`？→ **agent**
> 2. 路径在 `src/mj_agent/{其他}/**`？→ **code**
> 3. 路径在 `.claude/**` 或 `.mcp.json` 或 `docs/rule/[STANDARD]_*_HITL_Prompt*.md` / `_AI_Engineering_*.md` / `_Claude_Code_Settings_*.md` / `_MCP_Server_Governance_*.md`？→ **engineering-workflow**
> 4. 路径在 `docs/evaluation/`？→ **agent**
> 5. 路径在 `docs/{infrastructure,runbook,api}/`？→ **code**
> 6. 路径在 `docs/rule/` 但治"engineering 流程"？→ **engineering-workflow**
> 7. 路径在 `docs/rule/` 治文档/代码/数据？→ **code** 或 **shared**
> 8. 其他 → 默认 `shared` 并 PR body 论证

---

## 5. 状态与生命周期

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §5 全部规则（含 §5.6 Major.Minor 版本演进 + archive 流程；详见 [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]）。

### 5.7 双轨语境下的 archive

沿用 v2.0 §5.7。三轨语境同样适用：archive 时保留原 `track` 字段值（含新值 `engineering-workflow`）；living/frozen 引用判断不受 track 影响。

### 5.8 v2.0 → v2.1 升级路径（v2.1 新增）

本文档自身的"v2.0 → v2.1"升级遵循 ADR-011 §5.6.2 流程的**延迟 promote** 变体：

1. Phase A：v2.1 trio + ADR-014 + HITL_Prompt v1.0 以 `state: draft` 落地 `docs/rule/`，与 v2.0 trio（保持 active）共存；不立即 archive v2.0 trio
2. Phase B（核心 `.claude/skills/` 落地后；HITL_Prompt §5 矩阵不再指向占位）：promote PR — v2.0 trio → archive；v2.1 trio + HITL_Prompt v1.0 → active；CLAUDE.md / INDEX.md / 受影响引用一次性 audit 升级
3. 此变体的理由：v2.0 trio 已 active 但 engineering-workflow 资产空白；先骨架后促生工具有用，避免一次过载

### 5.9 归档触发判定（v2.1 in-place 加；ADR-017 决议）

> **派生自** mj-system v5.2 `[STANDARD]_Documentation_Management_Framework.md` §10.1。
> [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6.1 仅给 HITL 触发的文字描述，缺量化标准；本节落显式判定。

| 触发归档？ | 场景 | 说明 |
|---|---|---|
| ✅ 是 | **框架大版本升级** | 如 Meta v2.x → v3.0；trio 整体演进 |
| ✅ 是 | **STANDARD 结构性重构** | 如章节模板换代（12 章 → 5 章）；归档名加 `_pre_<新版本>` |
| ✅ 是 | **70%+ 内容改写**（量化阈值） | 衡量原文 ≥ 70% 文本被替换 |
| ✅ 是 | **拆分 / 合并 / 改名** | 1 doc → N doc；N doc → 1 doc；scope / 命名重定义 |
| ❌ 否 | 小修小补、patch 升级、字段补充、typo / 链接修 | → git 历史承担；不进归档目录 |

**判定优先级**：4 类必触发条件按 (1)→(2)→(3)→(4) 顺序短路判定（满足任一即触发）。

**反例边界**：单段加新内容（如本节加 §5.9）属字段补充；§3 加新类目（如 v2.1 加 SKILL track C）属字段补充；§5 加新生命周期阶段属字段补充。仅当**整文档结构** / **规则枚举集合** / **filename / scope** 发生变化时才升级触发。

**HITL 入口**：本节判定结果直接喂给 [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6.1 HITL trigger；reviewer 在 PR review 阶段对照本节 5 类显式 cite。

**Cross-ref**：[[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]]（决策记录 + mj-system §10.1 派生论证 + Alternatives）；ADR-011 §5.6（Living/Frozen + filename rule，部分待 Phase C-1a ADR-018 反转）。

---

## 6. 索引与引用规则

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §6 全部规则。**仅更新 §6.4.1**：

### 6.4 CLAUDE.md 同步策略

沿用 v2.0 §6.4。三类 allowlist 不变。

#### 6.4.1 CLAUDE.md 三轨分段（v2.1 升级；v2.0 双轨分段）

CLAUDE.md 内部按 track 分段，元规则放最顶。落地结构（详见 [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]）：

- 顶部 **元规则段**：Meta_Framework v2.x 自身 + `track: shared` 的 ADR（如 ADR-011 / ADR-012 / ADR-013 / ADR-014）
- `## Code-Side Documentation`：所属 allowlist 中 `track: code` 的项；Phase 1+ 由 `mj-agent-doc-sync`（in-tree workflow skill，PR-C1）维护
- `## Agent-Side Documentation`：`track: agent` 项；维护方同上
- **`## Engineering-Workflow Documentation`**（v2.1 新增）：`track: engineering-workflow` 项；A12-A14 门禁说明 + slash command 命名空间 + skill catalog 表 + HITL_Prompt 引用

PR 触发 §6.4 allowlist 同步检查时，按文档自身 `track` 落入对应段；`shared` 落入元规则段。

---

## 7. 自动校验与 PR 集成

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §7 全部规则。**校验门禁加 A12-A14**：

### 7.1 PR 校验门禁（v2.1 三轨重新分配）

| 编号 | 检查项 | 由哪个子框架治理 | 适用 track |
|---|---|---|---|
| A1-A6 | 路径 / frontmatter / state / Wikilink / INDEX / CLAUDE.md sync | [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §7.1 | **全部 track**（hygiene 通用） |
| OB1-OB5 | 非阻塞观察项 | Code_Side §7.2 | 全部 track |
| A7-A10 | SKILL/PROMPT/EVAL/CONTRACT 专属（in-source） | [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework\|Agent_Side v1.1]] §7.1 | **agent** |
| A11 | SKILL `state: active` 时 `eval_references` 非空（in-source） | Agent_Side §7.1 | **agent** |
| §7.5 frontmatter strip | loader 契约 | Agent_Side §7.5 | **agent**（仅 in-source） |
| **A12**（v2.1 新增） | `.claude/skills/<name>/SKILL.md` ADR-013 native schema 合规 + description 质量（≥200 chars + 正向/反向触发） | 本框架 §7.7 + Phase C+ engineering-workflow 子规范 | **engineering-workflow** |
| **A13**（v2.1 新增） | `.claude/settings.json` allowlist diff 审查（不允许无审批 Bash 通配 + secret pattern 进 deny） | 本框架 §7.7（Phase C `[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0` 落地后细化） | **engineering-workflow** |
| **A14**（v2.1 新增） | `.mcp.json` server 增删需声明 trust posture + credential mode | 本框架 §7.7（Phase C+ `[STANDARD]_MJ_Agent_MCP_Server_Governance_v1.0` 落地后细化） | **engineering-workflow** |

### 7.6 `.claude/` 边界（v2.1 正式条款；v2.0 §7.6 TODO 升级）

> v2.0 §7.6 整体出 governance 的过渡条款被本节取代。

`.claude/` 内部按文件分两类：

| 类别 | 路径 | 治理 |
|---|---|---|
| **项目级 in-tree**（团队共享，提交到 git） | `.claude/settings.json`、`.claude/skills/**`、`.claude/scripts/**`、`.claude/hooks/**` | **纳入** engineering-workflow track；触发 A12-A14 + §6.4 sync allowlist |
| **用户私有 / marketplace 配置** | `.claude/settings.local.json`（gitignore'd）、`~/.claude/**`、marketplace plugin 仓 `mj-agentlab-marketplace/**` | **不**纳入；沿用 v2.0 整体出 governance 条款 |

边界争议处理：见 §4.3.1 path-to-track 决策树第 3 条。

### 7.7 Engineering-workflow PR 门禁细则（v2.1 引入）

> 本节细化 A12-A14 的判定规则。Phase C+ engineering-workflow 子规范（`[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0` / `_MCP_Server_Governance_v1.0`）落地后此节迁移为 cross-ref。

#### A12 — `.claude/skills/<name>/SKILL.md` 校验

阻塞条件：

1. Frontmatter 仅含 `name` + `description` 两字段（不允许塞 `track` / `type` / `version` 等 Agent_Side §2 字段，避免 Claude Code 解析污染）
2. `name` 等于目录名 `<name>`，且符合 `mj-agent-<group>-<verb>` 命名模式
3. `description` ≥ 200 chars
4. `description` 含正向触发短语（如 "Make sure to use this skill whenever..."、用户提到 X / 改 Y / 加 Z 等场景描述）
5. `description` 含 `Do not use for:` 反向触发段（明确不适用场景，避免 over-triggering）
6. Body 含 `## Overview` + `## Workflow` 两段（其他段名灵活）

非阻塞观察：5-iteration trigger eval recall ≥ 70% / precision ≥ 90%（参考 skill-creator 工作流）。

#### A13 — `.claude/settings.json` 校验

阻塞条件：

1. `permissions.allow` 不出现裸 `Bash`（无 sub-pattern 限定）—— 需用具体 pattern（如 `Bash(uv run *)`）
2. `permissions.deny` 包含 secret pattern 兜底（如 `Read(./.env)` / `Edit(./.env)` / `Write(./.env)`）
3. 任何 `enabledPlugins` 增删需 PR body 描述用途与来源

非阻塞观察：与 ADR-013 决策一致；与 Phase C `[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0` 阈值（待落地）对齐。

#### A14 — `.mcp.json` 校验

阻塞条件：

1. server 增删 PR body 声明：`(a)` server 用途、`(b)` trust posture（first-party / third-party / community）、`(c)` credential mode（无密钥 / OAuth / API key）
2. server `command` 不引入"任意 shell 拼接"模式
3. 任何 server 涉及外网调用需 PR body 标记 data-egress 风险等级

非阻塞观察：与 Phase C+ `[STANDARD]_MJ_Agent_MCP_Server_Governance_v1.0`（待落地）对齐。

---

## 8. 迁移与落地规则

### 8.1 v2.0 → v2.1 升级路径（Phase A 起步 + Phase B promote）

> 详见本文 §5.8 + [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §Decision。

1. **Phase A**（PR-A1，本 PR）：v2.1 trio（Meta v2.1 / Code_Side v1.1 / Agent_Side v1.1）+ ADR-014 + CLAUDE.md 三段化 以 `state: draft` 落地；v2.0 trio 保持 `state: active`
2. **Phase A 续作**（PR-A2 / PR-A3）：HITL_Prompt v1.0 + ADR-015 + 模板补缺（RUNBOOK / SPEC / HITL_STAGE）
3. **Phase B**（PR-B1...B4）：`.claude/skills/` 落地（git family + flow family + doc family）+ ADR-016；末次 PR（PR-B3）做 promote：v2.0 trio archive + v2.1 trio + HITL_Prompt → active
4. **Phase C**：mj-agent 专属 skills（doc 完成 / runtime / infra）+ engineering-workflow 子规范（Claude_Code_Settings / MCP_Server_Governance）
5. **Phase D**：Phase 2 alignment（EVAL framework / 模板补全 POSTMORTEM/ISSUE/ASSESSMENT/EVAL）

### 8.2 后续 phase 填充计划

详见外部计划文件（项目负责人本地 `C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon.md`，工作驱动文档）+ ADR-014 §References；如演化为正式工作记录，将由后续 PR 在 `plans/` 落地 `[PLAN]_G_Tri_Track_And_Engineering_Workflow.md`。

---

## 9. Domain 枚举

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §9 全部 15 项 + track 倾向。**新增 1 项**（v2.1）：

| 编号 | Domain | 默认 track | 说明 |
|---|---|---|---|
| 1-15 | （沿用 v2.0） | （沿用） | （沿用） |
| **16** | **WORKFLOW**（v2.1 新增） | **engineering-workflow** | engineering 流程编排 / HITL / Claude Code 工作流配置（HITL_Prompt / `.claude/skills/` / `.claude/settings.json` / `.mcp.json`） |

`engineering-workflow` track 默认 domain `WORKFLOW`，但跨领域工作流（如 git 流程、doc 流程）可保留各自原 domain（`SYS` / `OPS` 等）+ `track: engineering-workflow`。

---

## 10. 快速操作清单

> 沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|v2.0]] §10。**更新 §10.6**：

### 10.6 选择 track（v2.1 升级）

新建 canonical 文档时按以下顺序确定 track：

1. **路径决策树**（§4.3.1 path-to-track）：物理路径强制
2. **类型默认**（见 §3 类型表）：SKILL/PROMPT/EVAL → `agent`；GUIDE/RUNBOOK → `code`；engineering 流程 STANDARD → `engineering-workflow`；其他先 `shared`
3. **主题归属**：
   - 业务 runtime 影响（输出错就是业务事故）→ `agent`
   - 开发 / 部署 / 运维（影响服务可用性）→ `code`
   - **开发者使用 Claude Code 执行任务的工作流**（HITL 流程、技能编排、settings、MCP 配置）→ `engineering-workflow`（v2.1 新增）
   - 跨轨 / 模糊 → `shared`
4. **边界规则**：见 [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §Decision 决策点 4 边界 artifact 归属表

---

## 参考

- 派生自：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]]
- 决策记录：[[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]
- 同期子框架：
  - [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]
  - [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]
- Track C 主 STANDARD（PR-A2 落地）：`[[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt]]`
- Track C 后续子规范（Phase C+ 落地）：
  - `[[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0]]`（A13 阈值）
  - `[[STANDARD]_MJ_Agent_MCP_Server_Governance_v1.0]]`（A14 阈值）
- 上游参考：mj-system v5.0+ `.claude/skills/` 35 in-tree skills + `[STANDARD]_AI_Engineering_Execution_HITL_Prompt.md` v1.0
- 关联 ADR：
  - [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] — 版本演进 + archive 工作流；本 v2.1 升级延迟 promote 即此模式变体
  - [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] — v1.1 → v2.0 双轨决策；本 v2.1 在其上加 Track C
  - [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] — in-tree vs marketplace SKILL schema 分离；本 v2.1 §3.10 / §7.7 A12 直接引用
- 行业精度：Hugging Face / MLflow / LangChain Hub / Anthropic Skills 仓 / DSPy / Semantic Kernel / Twelve-Factor / NIST AI BoM（沿用 v2.0）；新增：mj-system `.claude/skills/` 35 skills + HITL_Prompt v1.0 17-stage 闭环（mj-agent 直接派生源）
