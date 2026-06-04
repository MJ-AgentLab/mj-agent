---
type: standard
domain: SYS
summary: 元框架 v2.2 — 引入 §4.4 active canonical 路径稳定原则（ADR-018 决议）；3-PR 序列第 2 步；其他 §1-§10 沿用 v2.1
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-18
state: deprecated
version: v2.2
track: shared
archived: 2026-06-04
replaced-by: "../../policies/documentation.md"
supersedes:
  - "mj-agent@archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1"
  - "mj-agent@archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0"
tags:
  - standard
  - documentation
  - framework
  - meta
  - tri-track
  - engineering-workflow
  - active-path-stability
aliases:
  - MJ-Agent Documentation Meta Framework v2.2
  - MJ-Agent Documentation Meta Framework
  - mj-agent 文档治理元框架 v2.2
  - mj-agent 文档治理元框架
---

# MJ-Agent 文档治理元框架（已归档；deprecated）

> [!warning]
> **本副本为 M6 PR4 归档（state: deprecated；archived: 2026-06-04）**。本 STANDARD 的文档治理内容已迁移至 **SDD kernel**：taxonomy / track / A1-A6 / frontmatter / sync-allowlist → `policies/documentation`；archive triggers / path-stability / ceremony → `policies/archive`；working-doc lifecycle → `sdd/lifecycle`；§3.10 + §7.7-A12 + new-dir → `sdd/adapters/claude-code-skill`；A13 → `policies/ci-gates §5.1`；A14 → `policies/ai-agent §4`。本副本作为 M6 PR4 时期 cite-by-vintage frozen snapshot 保留（per ADR-011 §5.6 + ADR-019；归档文件不更新内部 wikilink）；当前权威以 SDD kernel 为准。

> **状态（Phase C-1a 完成后）**：`state: active`，`version: v2.2`（frontmatter）。**Active canonical 路径稳定原则**首次落地：本文档文件名**无 `_vX.Y` 后缀**（stable path = `[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`）；版本仅在 frontmatter `version` 字段。详见 §4.4 + [[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]。
> **派生自**：[[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta_Framework v2.1（archive）]]
> **首要变更**（v2.1 → v2.2）：§4.4 active canonical 路径稳定原则（ADR-018；partial supersede ADR-011 §4.2 + §5.6.2）+ 6 STANDARDs 文件名去后缀
> **决策记录**：[[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]

> [!info]
> **v2.1 → v2.2 主要变化**（issue [#78](https://github.com/MJ-AgentLab/mj-agent/issues/78)）：
> - §4.4 新增 "Active canonical 路径稳定原则" — active 文件名默认无 `_vX.Y` 后缀；版本只在 frontmatter；legacy 反向必带后缀
> - 6 active STANDARDs 同期 rename（5 个 in-place + Meta v2.1 archive ceremony）
> - PR_TEMPLATE drift 同步修（Phase B 漏改）
> - scripts/check_wikilinks.py NEEDLES 扩 6 模式（临时；C-3 通用化）
> - **Partial supersede ADR-011** §4.2 filename rule + §5.6.2 file-move-step；ADR-011 §5.6.1（已被 ADR-017 §5.9 细化）/ §5.6.3 / §5.6.4 保留有效
> - 上一版（v2.1）归档于 [docs/archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1.md](../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1.md)

---

## 0. v2.0 → v2.1 升级范围速览（保留为历史记录）

> v2.1 引入第三轨 engineering-workflow（含 §3.10 + §6.4.1 三段化 + §7.7 A12-A14）。v2.2 不改 v2.1 三轨设计；仅加 §4.4。

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

承接 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] §1 全部核心原则；新增三轨原则：

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
| **Active canonical 路径稳定**（v2.2 新增） | Active 文件名默认无 `_vX.Y` 后缀（version 仅在 frontmatter）；legacy 反向必带后缀；drop-suffix rename 视为 rule application（非 §5.9 #4 改名 trigger）；详见 §4.4 + ADR-018 |

详见 [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]] §Context 与 [[../adr/[ADR]_018_Active_Path_Stability|ADR-018]] §Context。

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
│   ├── rule/                           # 含 v2.1 trio active + HITL_Prompt + 工程流程 STANDARD（v2.2: 全部 stable path 无后缀）
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
| **Legacy** | `docs/archive/**` | 历史材料；v2.x 起 archive 子目录按原 subdir 镜像（rule/ 等） | 否，仅保留可读性 | `docs/archive/rule/[STANDARD]_..._v2.1.md` |

> **关键边界**：`.claude/settings.local.json` + `~/.claude/**`（用户全局）+ marketplace plugin（`mj-agentlab-marketplace/**`）**不**纳入本框架治理。详见 §7.6。

### 2.3 in-source canonical 设计理由

沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §2.3。仅治 `src/mj_agent/{skills,prompts}/**`；§7.5 frontmatter strip 契约只对此范围有意义。

### 2.4 分层规则（v2.1 加 Track C 行）

| 规则 | 正确 | 错误 |
|------|------|------|
| 权威文档进 canonical | `docs/rule/[STANDARD]_*.md` | `plans/[STANDARD]_*.md` |
| 运行时 skill 进 in-source canonical | `src/mj_agent/skills/biz-domain-context/SKILL.md` | `docs/design/skills/[SKILL]_*.md` |
| **工程流程 skill 进 in-tree `.claude/skills/`**（v2.1 新增） | `.claude/skills/mj-agent-flow-intake/SKILL.md` | `src/mj_agent/skills/mj-agent-flow-intake/`（混入运行时，loader 错装） |
| 任务计划进 working | `plans/[PLAN]_*.md` | `docs/plans/...` |
| 历史材料进 archive | `docs/archive/rule/[STANDARD]_..._v2.1.md` | `docs/postmortem/<legacy-report>.md` |
| **Active canonical 文件名稳定**（v2.2 新增） | `docs/rule/[STANDARD]_..._Meta_Framework.md`（无后缀） | `docs/rule/[STANDARD]_..._Meta_Framework_v2.2.md`（除非多 active 主版本并存） |

### 2.5 三轨子框架（v2.2 stable path）

```
docs/rule/
├── [STANDARD]_..._Meta_Framework.md                      ← 元层（本文，v2.2；stable path）
├── [STANDARD]_..._Code_Side_Documentation_Framework.md   ← Track A（v1.1；stable path）
├── [STANDARD]_..._Agent_Side_Documentation_Framework.md  ← Track B（v1.1；stable path）
├── [STANDARD]_..._AI_Engineering_Execution_HITL_Prompt.md ← Track C 主 STANDARD（v1.0；stable path）
├── [STANDARD]_GitHub_Markdown.md                         ← 归 Code_Side（v1.0；stable path）
└── [STANDARD]_..._Commit_Message_Convention.md           ← 归 Code_Side（v1.0；stable path）
```

> **过渡**：v2.1 → v2.2 落地后，6 active STANDARDs 全部 stable path（无后缀）。Meta v2.1 归档至 `docs/archive/rule/`。其他 5 STANDARDs 不触发 archive ceremony（rule application 解读；ADR-018 §Decision）。

### 2.6 项目根目录具名特殊文件（v2.2 in-place 加；2026-05-18）

> **起源**：借鉴 mj-system `[STANDARD]_Documentation_Management_Framework.md` §3.1（根目录特殊文件清单）的**结构与判定模式**；具体文件清单 + 职责描述按 mj-agent 自身资产派生（与 mj-agent 现实根目录文件状态一致）。详见 [[../glossary/upstream_business_warehouse|跨项目 attribution]]。

以下文件保留在项目根目录，**不使用** `[TYPE]_` 前缀；被单独点名赋予固定职责：

| 文件 | 职责 |
|------|------|
| `README.md` | 项目入口和快速启动 |
| `CONTRIBUTING.md` | 协作与提交流程（摘要 + 跳转 `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` + `docs/infrastructure/git/`） |
| `CHANGELOG.md` | 版本变更日志 |
| `GLOSSARY.md` | 项目术语索引（不与 `docs/glossary/<topic>.md` 专题词典重叠） |
| `CLAUDE.md` | AI 高频上下文缓存（同步策略见 §6.4） |

#### 2.6.1 治理例外条款

项目根 5 文件**不进入 canonical 治理表**：

- 不强制 frontmatter（[[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]] §7.1 A2 frontmatter schema 校验不适用）
- 不强制 GUIDE / STANDARD 等 canonical 类型 body 骨架
- 不计入 A1-A3 PR 门禁校验

**但仍受**：

- A4 wikilink 完整性（`[[...]]` 形式；普通 markdown 链接不强制）
- A6 CLAUDE.md sync 检查（§6.4 4 类 allowlist 触发时同步）
- [[STANDARD]_GitHub_Markdown|GitHub_Markdown]] §14 项目根 README 与 Markdown 特例（语法约束）

#### 2.6.2 与 §4.3.1 path-to-track 决策树的衔接

为避免 §2.6 例外与 §4.3.1 决策树之间出现解释空白：§4.3.1 决策树第 **0 条**显式覆盖项目根 markdown 归类（"不适用 track"），具体见 §4.3.1。

---

## 3. 类型与目录

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §3 全部规则。**类型枚举不变**（12 类 canonical）；track 默认值表加 engineering-workflow 行：

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

### 3.7 STANDARD 归属：全局规则 vs 领域专属（v2.2 加；ADR-022 C.3.2）

> 当前 mj-agent 全 STANDARD 在 `docs/rule/`（全局规则）；本节订立规则为未来引入域专属 STANDARD（如 db / docker）做准备。

| 范畴 | 路径 | 判定 |
|---|---|---|
| **全局规则** | `docs/rule/` | 跨领域、跨服务、跨工具的项目级规范（如本框架、Commit_Message_Convention、GitHub_Markdown） |
| **API 专属** | `docs/api/` | 跨服务的 API 约定（mj-agent 当前空） |
| **领域专属** | `docs/infrastructure/<domain>/` | 与具体技术领域绑定（database / docker / git / cicd / 等）；与该域 GUIDE / RUNBOOK / SPEC 同目录扁平 |

**就近原则**：领域专属 STANDARD 与对应 GUIDE/RUNBOOK/SPEC 同目录；不引入 `docs/rule/<topic>/` 嵌套；不引入 `docs/infrastructure/<domain>/<sub>/` 嵌套。

### 3.8 STANDARD 大型规范拆分阈值（v2.2 加；ADR-022 C.3.6）

> 订立拆分判定阈值。

当 STANDARD **同时**满足以下三条件时，拆分为多份单一主题 STANDARD（每份用 5 章模板）：

| 条件 | 阈值 |
|---|---|
| 行数 | >500 |
| 主题章节 | ≥5 个独立 |
| 跨文件引用 | ≥10 处 |

**例外**：单一主题大型 STANDARD 即使满足以上三条件，可不拆（如 Meta v2.2 ~610 行但单一主题"文档治理元框架"）。

**HITL 入口**：拆分判定结果纳入 §5.9 trigger #4（拆分/合并/改名 → archive ceremony）。

### 3.10 Engineering-workflow `[SKILL]` 治理（v2.1 新增）

> **scope**：仅治 `.claude/skills/<name>/SKILL.md`（in-tree 工程流程技能）。**不**治 `src/mj_agent/skills/<name>/SKILL.md`（运行时；归 [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]] §2）。**不**治 marketplace plugin SKILL.md（出 governance；详见 [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]）。

#### 3.10.1 Frontmatter schema（ADR-013 native）

```yaml
---
name: <mj-agent-group-verb>
description: <长 description；含 "Make sure to use this skill whenever..." 式触发短语；含"不适用于"反例；可中英双语>
---
```

**仅 2 字段**。不引入 Agent_Side §2 的 13 字段。理由见 [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] + 本框架 §1 plugin loader 边界尊重原则。

> **A12 阻塞门禁**：`description` ≥ 200 chars，含正向触发短语 + `Do not use for:` 反向触发段（成熟 marketplace plugin 实践）。校验由 Phase C+ engineering-workflow 子规范细化。

#### 3.10.2 Body 结构

参考成熟 in-tree workflow skill 实践（典型段名）：

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

- `<group>`：`flow` / `git` / `doc` / `runtime` / `infra`（5 类，详见 [[decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]，PR-B1 落地）
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

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §4 全部规则。**v2.1 扩 §4.3.1（track 字段）；v2.2 加 §4.4（active path stability）**。

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

边界 artifact 归属规则见 [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]] §Decision 决策点 4。

> **path-to-track 决策树**（v2.1 引入，避免 PR 反复争议；v2.2 加 0 条覆盖项目根 markdown）：
> 0. 路径是项目根 markdown（`README.md` / `CONTRIBUTING.md` / `CHANGELOG.md` / `GLOSSARY.md` / `CLAUDE.md`）？→ **不适用 track**（per §2.6 例外条款；不写 frontmatter；A1-A3 不适用）
> 1. 路径在 `src/mj_agent/{skills,prompts}/**`？→ **agent**
> 2. 路径在 `src/mj_agent/{其他}/**`？→ **code**
> 3. 路径在 `.claude/**` 或 `.mcp.json` 或 `docs/rule/[STANDARD]_*_HITL_Prompt*.md` / `_AI_Engineering_*.md` / `_Claude_Code_Settings_*.md` / `_MCP_Server_Governance_*.md`？→ **engineering-workflow**
> 4. 路径在 `docs/evaluation/`？→ **agent**
> 5. 路径在 `docs/{infrastructure,runbook,api}/`？→ **code**
> 6. 路径在 `docs/rule/` 但治"engineering 流程"？→ **engineering-workflow**
> 7. 路径在 `docs/rule/` 治文档/代码/数据？→ **code** 或 **shared**
> 8. 其他 → 默认 `shared` 并 PR body 论证

### 4.5 ISSUE 命名约定（v2.2 加；ADR-022 C.3.3）

`docs/issues/` 文件命名格式：

```
[ISSUE]_NNN_DomainAbbr_Description.md
```

- `NNN`：3 位顺序编号（001 起；与 ADR 编号独立）
- `DomainAbbr`：mj-agent domain 缩写（per §9：`SYS / AGENT / DATA / SKILL / PROMPT / GUARDRAIL / OPS / INTEGRATION / WORKFLOW / ...`）
- `Description`：英文描述，`_` 连接，无空格

`docs/issues/` 当前空；规则在首个 ISSUE 创建时启用。

### 4.6 supersedes 字段多文档语义（v2.2 加；ADR-022 C.3.4）

任意 canonical 类型的 frontmatter `supersedes` 字段接受 **list**（非单一 string），用于以下场景：

```yaml
supersedes:
  - "<old-path-1>"
  - "<old-path-2>"
```

**典型用例**：

- 单一替代：1 旧 doc → 1 新 doc，list 含单 string
- 拆分替代：1 旧 doc → N 新 docs，每个新 doc 的 list 都列旧 doc
- 合并替代：N 旧 docs → 1 新 doc，list 含 N strings

`scripts/check_frontmatter.py` 已隐式支持 list（YAML 自动解析）；本节仅文档化规则。

mj-agent 当前所有 supersedes 都是 list（含单 string），与本规则一致。

### 4.4 Active canonical 路径稳定原则（v2.2 新增；ADR-018 决议）

> **Partial supersede** [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] §4.2 filename rule + §5.6.2 file-move-step。

#### 4.4.1 主条款

Active canonical 文件名**默认不带 `_vX.Y` 后缀**；文件名保持稳定路径。例如本框架的稳定路径是 `[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`，而不是带版本后缀。文档语义版本写在 frontmatter `version` 字段和正文版本说明里，不写进文件名。

#### 4.4.2 例外

仅"多 active 主版本确需并存"（如 v1/v2 API 长期共存的 STANDARD）才允许文件名加 `_vX.Y` 区分；这是例外而非默认。

#### 4.4.3 Legacy 反向规则

归档文件**必须**保留 `_vX.Y` 或 `_pre_vX.Y` 后缀（cite-by-vintage；详见 ADR-011 §5.6 motivation Q1 + ADR-018 §Decision）。

#### 4.4.4 rename 解读子规则

drop `_vX.Y` 后缀的 rename 视为 **rule application**（首次应用 §4.4 主条款），**非** §5.9 触发 #4 "改名"。仅当 STANDARD 同时发生 substantive content evolution 时才触发 archive ceremony。

**先例**：业界引入 stable-path 规则时常见模式：框架文件 archive（substantive 演进 + 改名双重）；其他 STANDARDs rename only（rule application）。本 PR Phase C-1a 沿此模式：Meta v2.1 archive ceremony；其他 5 STANDARDs in-place rename。

#### 4.4.5 Cross-ref

[[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]（决策记录 + Alternatives 4 拒）；[[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6（partial supersede）；[[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]] §5.9（trigger #4 改名）。

---

## 5. 状态与生命周期

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §5 全部规则（含 §5.6 Major.Minor 版本演进 + archive 流程；详见 [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]]）。

### 5.7 双轨语境下的 archive

沿用 v2.0 §5.7。三轨语境同样适用：archive 时保留原 `track` 字段值（含新值 `engineering-workflow`）；living/frozen 引用判断不受 track 影响。

### 5.8 v2.0 → v2.1 升级路径（v2.1 新增；保留为历史记录）

本文档自身的"v2.0 → v2.1"升级遵循 ADR-011 §5.6.2 流程的**延迟 promote** 变体：

1. Phase A：v2.1 trio + ADR-014 + HITL_Prompt v1.0 以 `state: draft` 落地 `docs/rule/`，与 v2.0 trio（保持 active）共存；不立即 archive v2.0 trio
2. Phase B（核心 `.claude/skills/` 落地后；HITL_Prompt §5 矩阵不再指向占位）：promote PR — v2.0 trio → archive；v2.1 trio + HITL_Prompt v1.0 → active；CLAUDE.md / INDEX.md / 受影响引用一次性 audit 升级
3. 此变体的理由：v2.0 trio 已 active 但 engineering-workflow 资产空白；先骨架后促生工具有用，避免一次过载

### 5.9 归档触发判定（v2.1 in-place 加；ADR-017 决议）

> [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6.1 仅给 HITL 触发的文字描述，缺量化标准；本节落显式判定。

| 触发归档？ | 场景 | 说明 |
|---|---|---|
| ✅ 是 | **框架大版本升级** | 如 Meta v2.x → v3.0；trio 整体演进 |
| ✅ 是 | **STANDARD 结构性重构** | 如章节模板换代（12 章 → 5 章）；归档名加 `_pre_<新版本>` |
| ✅ 是 | **70%+ 内容改写**（量化阈值） | 衡量原文 ≥ 70% 文本被替换 |
| ✅ 是 | **拆分 / 合并 / 改名** | 1 doc → N doc；N doc → 1 doc；scope / 命名重定义；**注**：drop `_vX.Y` 后缀的 rename 视为 rule application（§4.4.4），**非**本触发；详见 [[../adr/[ADR]_018_Active_Path_Stability|ADR-018]] §Decision |
| ❌ 否 | 小修小补、patch 升级、字段补充、typo / 链接修 | → git 历史承担；不进归档目录 |

**判定优先级**：4 类必触发条件按 (1)→(2)→(3)→(4) 顺序短路判定（满足任一即触发）。

**反例边界**：单段加新内容（如本节加 §5.9）属字段补充；§3 加新类目（如 v2.1 加 SKILL track C）属字段补充；§5 加新生命周期阶段属字段补充。仅当**整文档结构** / **规则枚举集合** / **filename / scope** 发生变化时才升级触发。

**HITL 入口**：本节判定结果直接喂给 [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6.1 HITL trigger；reviewer 在 PR review 阶段对照本节 5 类显式 cite。

**Cross-ref**：[[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]]（决策记录 + Alternatives）；ADR-011 §5.6（Living/Frozen + filename rule，§4.2 + §5.6.2 已被 ADR-018 partial supersede）；ADR-018 §Decision 子条款 §4.4.4（rename 解读）。

### 5.10 v2.1 → v2.2 升级路径（v2.2 新增）

本 STANDARD 自身的"v2.1 → v2.2"升级触发 §5.9 trigger #4（filename 改 + substantive 演进引入 §4.4）：

1. **Phase C-1a**（PR-2 of 3-PR sequence；本 PR）：v2.1 → archive at `docs/archive/rule/[STANDARD]_..._Meta_Framework_v2.1.md`（`state: deprecated`）；v2.2 stable path（无后缀）at `docs/rule/[STANDARD]_..._Meta_Framework.md`（`state: active`；`version: v2.2`）
2. 其他 5 STANDARDs（Code_Side / Agent_Side / HITL_Prompt / Commit_Message / GitHub_Markdown）同 PR rename only（§4.4.4 rule application 解读；ADR-018 §Decision 子条款）
3. ADR-018 创建（partial supersede ADR-011 §4.2 + §5.6.2）；ADR-017 §5.9 trigger #4 sustained
4. PR_TEMPLATE drift 同步修（Phase B 漏改）；scripts/check_wikilinks.py NEEDLES 扩 6 模式（C-3 通用化推迟）
5. CLAUDE.md / docs/INDEX.md / CHANGELOG.md sync

### 5.11 Working 文档生命周期（v2.2 in-place 加；ADR-021 决议）

> 落实 \`plans/**\` 工作文档的"任务完成"语义；区别于 canonical 文档的 \`deprecated\`（"被新版本替代"）。

#### 5.11.1 Working state 4 态机

\`plans/**\` 使用 4 状态机：

| state | 含义 | 触发 |
|---|---|---|
| \`draft\` | 仍在拟订；未对齐 | 新建文档默认 |
| \`active\` | 已采纳；任务执行期 | 关联 issue/PR open |
| \`completed\` | 任务自然完成 | 关联 PR merged / Issue closed / Release deployed |
| \`archived\` | 物理归档（GC；Phase D 范畴） | \`completed\` ≥ 6 月 + 引用 0 时 |

#### 5.11.2 Stage 17 Post-merge 自动化

\`mj-agent-flow-post-merge\` SKILL Step 9 自动识别 PR/Issue 关联的 \`[PLAN]_*.md\` / \`[INTAKE]_*.md\`，state 由 \`active\` 改 \`completed\` 并刷 \`updated\` 字段；**不移动文件位置**；保留所有跨文档 reference。

#### 5.11.3 边界

| 项 | 处理 |
|---|---|
| \`completed\` 文件位置 | 保留 \`plans/\` 原路径；不移 \`plans/archive/\`（避免断跨文档引用） |
| \`completed\` 文件 INDEX | \`plans/\` 不维护 INDEX |
| 跨文档引用稳定性 | 仅 state 改变 → 引用路径不变 → 全仓 reference 稳定 |
| 长期 \`draft\` abandon | 保持 \`draft\`（留重启余地）；如确认废弃可手工标 \`archived\`（不移文件） |
| \`completed\` 文件 grep | 仍可命中；state 字段标识其已落地 |

#### 5.11.4 Cross-ref

[[../adr/[ADR]_021_Working_Doc_Lifecycle|ADR-021]]（决策记录 + Alternatives）；Stage 17 自动化：[[../../.claude/skills/mj-agent-flow-post-merge/SKILL]] Step 9。

#### 5.11.5 archived 物理归档实施指引（v2.2 加；ADR-023 落实 ADR-021 follow-up）

> 本节落实 ADR-021 §Consequences 标记的 Phase D follow-up：archived 物理归档实现。

**触发条件**：

- `state: completed` 持续 ≥ 6 个月（180 天；可调）
- 全仓 grep ref count = 0
- HITL 人工 review 确认（不自动跑 GC）

**操作流程**：

1. 跑 `scripts/find_old_completed_plans.py` 获候选清单
2. 人工 grep 验证每个候选的引用计数（避免误删 active 引用）
3. 创建 `plans/archive/` 子目录（首次 GC 时；不预先创建空目录）
4. `git mv plans/<name>.md plans/archive/<name>.md`
5. 改 frontmatter：`state: completed` → `state: archived`；加 `archived: <YYYY-MM-DD>` 字段
6. archived 文件**不更新**内部 wikilinks（frozen snapshot 原则；与 ADR-019 archive 处理一致）
7. 不更新 docs/INDEX.md（plans/ 不入 INDEX）；CHANGELOG 可入 GC 操作记录条目

**当前状态**（2026-05-09）：mj-agent plans/ 中最早 completed 文件距今 < 1 月（PLAN_F / PLAN_G 等）；6 月阈值未到；本节仅指引；首次 GC 操作约在 2026-11+。

**Cross-ref**：[[../adr/[ADR]_023_Stale_Doc_And_Plan_GC_Infra|ADR-023]]（infra 决策 + scripts 派生）；ADR-021 §Consequences 负面 #2；frozen snapshot 原则（与 ADR-019 一致）。

#### 5.11.6 Retroactive 补落 working 文档（v2.2 in-place 加；2026-05-18）

> 落实 working 文档生命周期治理的"漏落盘事后补救"路径，区别于 §5.11.2 Stage 17 自动化（`active → completed`）和 §5.11.5 archived 物理归档（`completed → archived`）。

**触发场景**：任务实施期间漏按 §5.11.1 落盘 `plans/[PLAN]_*.md` 或 `plans/[INTAKE]_*.md`，事后审计发现且符合以下任一条件时，应 retroactive 补落：

1. **多 PR 链** ≥ 3 PR 且不满足 [[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt]] §3.2 Stage 4 豁免（即不是单文件 Low Risk bugfix/documentation）
2. **High 风险**（含 [[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt]] §3.1 mj-agent 专属 4 项 trigger 之一：runtime-skill-content-change / prompt-version-bump / biz-catalog-sync / sql-guardrail-relax）
3. **跨 ≥ 5 个 canonical 文档** 或 **改动 Track C primary STANDARD**（HITL_Prompt）

**Retroactive 补落规则**：

- **state 直接 `completed`**：所有关联 PR 已 merged → `state: completed` + `completed: <最后 PR merged 日期 ISO>`（不走 `draft → active` 中间态）
- **frontmatter 加 `retroactive: true` 字段**：机器可识别；与"真实 Stage 0/4 落盘"区分（`scripts/check_frontmatter.py` 对未知字段宽容，加此字段不破坏 schema）
- **头部 `> [!warning]` 声明框**：醒目提示"事后回填，非真实 Stage 0/4 输出"；引导读者关注内容 trace 而非作为流程"标准模板"使用
- **凭证 trace 段必加**：每段内容来源（PR description / commit / memory / CLAUDE.md update / vault 草稿）逐段引用，避免 time-shift bias
- **本节追加 1 行 retroactive 记录**：按下方 § Retroactive 落地记录 格式

**不补落判定**（事后审计发现但凭证已充分，可跳过补落）：满足以下任一即可不补：

- `CLAUDE.md` 已有同等深度的 "YYYY-MM-DD update" 段记录
- memory feedback/project 文件已完整覆盖决策点
- commit message + PR body 已含 7 段 PLAN 同等信息（per [[[PLAN]_multi_env_dgx_mcp_bundle|[PLAN]_multi_env_dgx_mcp_bundle]] mj-agent native 7 段结构）

#### 5.11.6.1 Retroactive 落地记录

按时间序追加。

- **2026-05-18** — 首次 retroactive：**cross-repo decoupling cleanup** 任务（PR [#118](https://github.com/MJ-AgentLab/mj-agent/pull/118) / [#121](https://github.com/MJ-AgentLab/mj-agent/pull/121) / [#122](https://github.com/MJ-AgentLab/mj-agent/pull/122) / [#123](https://github.com/MJ-AgentLab/mj-agent/pull/123) / [#124](https://github.com/MJ-AgentLab/mj-agent/pull/124)，2026-05-11 02:44-04:47Z，5 PR / 2h 03min / 85 文件 / +1755/-462 lines）实施期间未落盘 INTAKE/PLAN，事后补 [[[INTAKE]_cross_repo_decoupling_cleanup|[INTAKE]_cross_repo_decoupling_cleanup]] + [[[PLAN]_cross_repo_decoupling_cleanup|[PLAN]_cross_repo_decoupling_cleanup]]（均 `state: completed` + `retroactive: true`）。凭证密度评估：memory `project_cross_repo_decoupling_completion.md` + CLAUDE.md "项目起源说明（2026-05-11 update）" 段 + 5 PR description 完整 → 重建可信。流程债根因：实施跳过 Stage 0 Intake 落盘判定（[[../../.claude/skills/mj-agent-flow-intake/SKILL]] §2.1 6 项触发未识别）+ Stage 4 Plan body 落盘漏（HITL_Prompt §3.2 5 PR 链不豁免）；mj-agent 已通过 PR #163 PreToolUse hook 防 G1/G2 漏，工作流 SKILL 加硬性 gate（参考 hook-based defense pattern）留独立 follow-up 评估。

**Cross-ref**：[[../adr/[ADR]_021_Working_Doc_Lifecycle|ADR-021]]（working doc 4 态机框架决策；archived per PR #122，wikilink 由 [[decisions/ADR-020_Archive_Auto_Discovery|ADR-020]] auto-discover 解析）；[[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt]] §3.2 Stage 4 豁免 / §4.15 Rule 12 PR-state 联动；[[../../.claude/skills/mj-agent-flow-intake/SKILL]] §2.1 落盘判定。

---

## 6. 索引与引用规则

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §6 全部规则。**仅更新 §6.4.1**：

### 6.4 CLAUDE.md 同步策略（v2.2 显式展开 + 加 mj-agent 特化第 4 类）

> v2.2 起本节**显式展开** v2.0 隐式继承的 3 类 allowlist 内容，并加入 mj-agent 特化的第 4 类「runtime 语义」（CLAUDE.md 中占比 ~40% 的 mj-agent native 高频内容）。起源借鉴 mj-system `[STANDARD]_Documentation_Management_Framework.md` §6.4 三类 allowlist 写法；类目内容按 mj-agent 自身资产派生。详见 [[../glossary/upstream_business_warehouse|跨项目 attribution]]。

以下 4 类文档变更触发 §7.1 A6 PR gate（同步检查 `CLAUDE.md`）：

| 类别 | mj-agent 具体例 |
|---|---|
| **类 1 — 全局高频标准** | trio（Meta / Code_Side / Agent_Side）+ HITL_Prompt + Commit_Message + GitHub_Markdown + 跨轨元规则 ADR（如 011 / 012 / 013 / 014 / 017 / 018） |
| **类 2 — 高频运行信息** | 入口命令矩阵（`uv run mj-agent serve` / `check` / `langgraph dev`）+ 端口规则（8000 Chainlit / 2024 LangGraph Studio）+ 关键环境变量（`ARK_API_KEY` / `MJ_CONFIG_PROFILE` / `LLM_PROVIDER`） |
| **类 3 — 项目目录入口** | `docs/INDEX.md` + 核心运行时模块位置（`src/mj_agent/{agent,llm,config}.py` + `tools/` / `skills/` / `prompts/`） |
| **类 4（v2.2 mj-agent 特化加） — runtime 语义** | LLM provider matrix（Ark vs `local-openai-compat` 二分；`make_llm()` 实现，[[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]）+ Data boundary L1-L4（regex guardrail / sqlglot precheck / SKILL semantics / read-only conn + GRANT；[[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]）+ HITL gates（stage 5 plan / 7 SPEC / 9 self-review / 11 push / 13 review-CI；[[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt]]） |

其余文档默认通过按需读取获取；**不要求**把全部细节缓存进 `CLAUDE.md`。

> **mj-agent 特化第 4 类理由**：CLAUDE.md 中 LLM provider + Data boundary + HITL gates 三块占比 ~40%，是 mj-agent native 而 mj-system 无的内容；显式列入避免 reviewer 在「这条规则改是否要 sync CLAUDE.md」上反复判断。

#### 6.4.1 CLAUDE.md 三轨分段（v2.1 升级；v2.0 双轨分段）

CLAUDE.md 内部按 track 分段，元规则放最顶。落地结构（详见 [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]]）：

- 顶部 **元规则段**：Meta_Framework v2.x 自身 + `track: shared` 的 ADR（如 ADR-011 / ADR-012 / ADR-013 / ADR-014 / ADR-017 / ADR-018）
- `## Code-Side Documentation`：所属 allowlist 中 `track: code` 的项；Phase 1+ 由 `mj-agent-doc-sync`（in-tree workflow skill，PR-C1）维护
- `## Agent-Side Documentation`：`track: agent` 项；维护方同上
- **`## Engineering-Workflow Documentation`**（v2.1 新增）：`track: engineering-workflow` 项；A12-A14 门禁说明 + slash command 命名空间 + skill catalog 表 + HITL_Prompt 引用

PR 触发 §6.4 allowlist 同步检查时，按文档自身 `track` 落入对应段；`shared` 落入元规则段。

---

## 7. 自动校验与 PR 集成

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §7 全部规则。**校验门禁加 A12-A14**：

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

### 8.1 v2.0 → v2.1 → v2.2 升级路径

> 详见 §5.8 + §5.10 + [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]] §Decision + [[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]。

1. **Phase A**（PR-A1）：v2.1 trio + ADR-014 + CLAUDE.md 三段化 以 `state: draft` 落地；v2.0 trio 保持 `state: active`
2. **Phase A 续作**（PR-A2 / PR-A3）：HITL_Prompt v1.0 + ADR-015 + 模板补缺（RUNBOOK / SPEC / HITL_STAGE）
3. **Phase B**（PR-B1...B4）：`.claude/skills/` 落地（git family + flow family + doc family）+ ADR-016；末次 PR 做 promote：v2.0 trio archive + v2.1 trio + HITL_Prompt → active
4. **Phase C-2**（3-PR 序列第 1 步；PR #77 已合并 ff37b5f）：ADR-017 + Meta v2.1 §5.9 archive trigger quantification
5. **Phase C-1a**（3-PR 序列第 2 步；本 PR）：ADR-018 + active path stability + Meta v2.1 archive ceremony + 5 STANDARDs rename + PR_TEMPLATE drift fix
6. **Phase C-1b**（3-PR 序列第 3 步；待起）：ADR-019 + archive `[DEPRECATED]_` 前缀 + `archived` / `replaced-by` frontmatter
7. **Phase C-2/3**：mj-agent 专属 skills（doc 完成 / runtime / infra）+ engineering-workflow 子规范（Claude_Code_Settings / MCP_Server_Governance）
8. **Phase D**：Phase 2 alignment（EVAL framework / 模板补全 POSTMORTEM/ISSUE/ASSESSMENT/EVAL）

### 8.2 后续 phase 填充计划

详见外部计划文件（项目负责人本地 `C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-glistening-shannon.md`，工作驱动文档）+ ADR-014 §References + ADR-017 §References + ADR-018 §References。

---

## 9. Domain 枚举

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §9 全部 15 项 + track 倾向。**新增 1 项**（v2.1）：

| 编号 | Domain | 默认 track | 说明 |
|---|---|---|---|
| 1-15 | （沿用 v2.0） | （沿用） | （沿用） |
| **16** | **WORKFLOW**（v2.1 新增） | **engineering-workflow** | engineering 流程编排 / HITL / Claude Code 工作流配置（HITL_Prompt / `.claude/skills/` / `.claude/settings.json` / `.mcp.json`） |

`engineering-workflow` track 默认 domain `WORKFLOW`，但跨领域工作流（如 git 流程、doc 流程）可保留各自原 domain（`SYS` / `OPS` 等）+ `track: engineering-workflow`。

---

## 10. 快速操作清单

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|v2.0]] §10。**更新 §10.6 + §10.7（v2.2 新增）**：

### 10.6 选择 track（v2.1 升级）

新建 canonical 文档时按以下顺序确定 track：

1. **路径决策树**（§4.3.1 path-to-track）：物理路径强制
2. **类型默认**（见 §3 类型表）：SKILL/PROMPT/EVAL → `agent`；GUIDE/RUNBOOK → `code`；engineering 流程 STANDARD → `engineering-workflow`；其他先 `shared`
3. **主题归属**：
   - 业务 runtime 影响（输出错就是业务事故）→ `agent`
   - 开发 / 部署 / 运维（影响服务可用性）→ `code`
   - **开发者使用 Claude Code 执行任务的工作流**（HITL 流程、技能编排、settings、MCP 配置）→ `engineering-workflow`（v2.1 新增）
   - 跨轨 / 模糊 → `shared`
4. **边界规则**：见 [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]] §Decision 决策点 4 边界 artifact 归属表

### 10.7 选择文件名（v2.2 新增；§4.4 落地清单）

新建 / 演进 active canonical 文档时，按 §4.4 决定文件名是否带 `_vX.Y`：

1. **首版 STANDARD/SPEC/EVAL/CONTRACT/ASSESSMENT**：文件名**无后缀**（stable path）；frontmatter `version: v1.0`
2. **演进** — 同时满足以下两条之一才触发 archive ceremony 并保留 active 文件名稳定（§4.4.4 + §5.9 trigger #4）：
   - (a) substantive content evolution（§5.9 trigger #1/#2/#3 之一）
   - (b) 多 active 主版本并存（§4.4.2 例外）
3. **Drop-suffix rename**（如 `_v1.0.md` → 无后缀）：视为 rule application；不触发 archive
4. **Legacy 归档**：必带 `_vX.Y` 或 `_pre_vX.Y` 后缀（§4.4.3）

---

## 修订记录（v2.2 in-place sustained 序列）

本节按时间序追加 v2.2 sustained 内 in-place 字段补充记录（区别于触发 archive ceremony 的 substantive evolution）。判定依据：§5.9 反例边界「单段加新内容属字段补充」+ 「§3 加新类目属字段补充」+ 「§5 加新生命周期阶段属字段补充」类比。

| 日期 | sustained 变更 | 依据 |
|---|---|---|
| 2026-05-18 | §2.6 新加「项目根目录具名特殊文件」（5 文件 + 治理例外条款）+ §4.3.1 决策树补 0 条（覆盖项目根 markdown）+ §6.4 显式展开 3 类 allowlist 内容 + 加 mj-agent 特化第 4 类「runtime 语义」（LLM provider matrix + Data boundary L1-L4 + HITL gates） | 借鉴 mj-system `[STANDARD]_Documentation_Management_Framework.md` §3.1 + §6.4 + §7.1 A6 的结构与判定模式；§5.9 反例「单段加新内容 / §3 加新类目」类比；详细 attribution 见 [[../glossary/upstream_business_warehouse|跨项目 attribution]] |

---

## 参考

- 派生自：[[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta_Framework v2.1（archive）]]
- 决策记录：
  - [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]]（v2.0 → v2.1 三轨）
  - [[../adr/[ADR]_017_Archive_Trigger_Quantification|ADR-017]]（v2.1 §5.9 trigger 量化）
  - [[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]（v2.2 §4.4 active path stability；partial supersede ADR-011 §4.2 + §5.6.2）
- 同期子框架：
  - [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]
  - [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]
- Track C 主 STANDARD：`[[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]]`
- Track C 后续子规范（Phase C+ 落地）：
  - `[[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0]]`（A13 阈值）
  - `[[STANDARD]_MJ_Agent_MCP_Server_Governance_v1.0]]`（A14 阈值）
- 内部沉淀：mj-agent in-tree workflow skills（5 family / 32 active）+ HITL_Prompt v1.0 17-stage 闭环 + 历史归档框架（v1.x → v2.x trio 演进；详见 `docs/archive/rule/`）
- 关联 ADR：
  - [[decisions/ADR-011_Doc_Versioning_And_Archive_Convention|ADR-011]] — 版本演进 + archive 工作流；§4.2 + §5.6.2 已被 ADR-018 partial supersede；§5.6.1 已被 ADR-017 §5.9 细化；§5.6.3 / §5.6.4 保留
  - [[decisions/ADR-012_Two_Track_Documentation_Governance|ADR-012]] — v1.1 → v2.0 双轨决策；本 v2.1 在其上加 Track C
  - [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] — in-tree vs marketplace SKILL schema 分离；本 v2.1 §3.10 / §7.7 A12 直接引用
- 行业精度：Hugging Face / MLflow / LangChain Hub / Anthropic Skills 仓 / DSPy / Semantic Kernel / Twelve-Factor / NIST AI BoM（沿用 v2.0）；v2.1 新增：in-tree workflow skill 编排 + HITL_Prompt v1.0 17-stage 闭环；v2.2 新增：active path stability 实践（多 active 主版本并存例外保留 `_vX.Y` 后缀）
