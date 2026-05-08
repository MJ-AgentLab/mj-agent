---
type: standard
domain: SYS
summary: Track B 智能体侧文档治理（v1.0 → v1.1 minor bump）— §2 scope 加注 engineering-workflow `.claude/skills/SKILL.md` 不归本节治理；§7.5 frontmatter strip 契约 scope 明确为 in-source only；与 Meta v2.1 同 PR 落地
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-08
state: active
version: v1.1
track: agent
derives_from: mj-agent@archive/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0
supersedes:
  - "mj-agent@archive/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0"
tags:
  - standard
  - documentation
  - track-b
  - agent-side
aliases:
  - MJ-Agent Agent-Side Documentation Framework v1.1
  - Track B 子框架 v1.1
---

# MJ-Agent 智能体侧文档治理框架 v1.1（Track B）

> **状态（Phase B PR-B3c-promote 完成后）**：`state: active`。v1.0 已 archive 至 `docs/archive/rule/` + `state: deprecated`。与 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] 同期 promote。
> **职责**：治理 Track B 文档（SKILL / PROMPT / EVAL / agent-facing CONTRACT / ADR-agent / SPEC-agent / GUIDE-agent）的 authoring 深度规则、PR 校验、loader 契约 ——**仅限 `src/mj_agent/{skills,prompts}/**` 范围**。
> **失败模式**：**沉默失败**（runtime 输出错 → 业务决策偏差）—— 审阅强度高于 Track A。
> **派生自**：[[../archive/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|v1.0（archive）]]
> **首要变更**：仅 minor bump —— §0 / §2 / §7.5 加 scope 明确条款，把 engineering-workflow `.claude/skills/SKILL.md` 排除出本框架治理（划归 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] §3.10 / §7.7）。

---

## 0. 范围（v1.1 scope 明确）

| 类型 | 默认 track | Authoring 章节 | 紧迫度 |
|---|---|---|---|
| **SKILL（in-source）** | agent | §2 | **Phase 0.5（最紧迫）** |
| **PROMPT** | agent | §3 | Phase 1 |
| **EVAL** | agent | §4 | Phase 2 |
| **CONTRACT (agent-facing tool)** | agent | §5 | Phase 0.5（与 SQL guardrail 同期） |
| ADR-agent | agent | §6 | Phase 1 |
| SPEC-agent | agent | §6 | Phase 1 |
| GUIDE-agent | agent | §6 | Phase 1 |

跨轨（`track: shared`）文档：本框架 §7.1 校验仍执行；§3 章节按对应类型走；额外审阅角色见 §8。

> **v1.1 scope 明确（防误读）**：本框架的 SKILL/PROMPT 治理**仅限 `src/mj_agent/{skills,prompts}/**` 范围**。`.claude/skills/<name>/SKILL.md`（in-tree engineering-workflow 技能）**不**归本框架治理 —— 那是 Meta v2.1 §3.10 / §7.7（A12-A14）治理范围，使用 ADR-013 native 2 字段 schema，由 Claude Code 主进程加载，不经 mj-agent Python loader。详见 §2 scope note + §7.5 scope。
>
> 简言之：
> - `src/mj_agent/skills/biz-domain-context/SKILL.md` → 本框架 §2（13 字段 + 五段式）
> - `.claude/skills/mj-agent-flow-intake/SKILL.md` → Meta v2.1 §3.10（2 字段 ADR-013 native）

---

## 1. 设计目标

承接 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta_Framework v2.1]] §1，针对智能体侧补充五条独有原则（沿用 v1.0 §1）：

| 原则 | 说明 |
|---|---|
| 文档即 runtime code | SKILL.md / system.md 的 body 字面被 LLM 消费 —— 字面修改即行为修改 |
| 沉默失败需主动检测 | EVAL coupling 是必须；不能依赖人类发现错答案 |
| 渐进披露 | scripts/ + references/ + assets/ 三类 bundled resources（skill-creator 范式） |
| 触发描述质量 | description 决定 skill 是否被调用；undertriggering 是默认问题 |
| frontmatter strip 契约 | loader 必须剥离 YAML 后只返回 body（仅对 `src/mj_agent/{skills,prompts}/**` 生效；§7.5） |

> **v1.1 加注**：上述原则中"文档即 runtime code"和"frontmatter strip 契约"**仅对 in-source canonical** 有效；对 `.claude/skills/**`（engineering-workflow）不适用 —— 那些 skill 的 body 是 Claude Code 上下文（开发者看的工作流编排），不是 mj-agent runtime LLM 上下文。

---

## 2. SKILL Authoring（§3.1，Phase 0.5 主体填充）

> **Scope 明确（v1.1 升级；ADR-013 锁定 + 本 v1.1 § scope）**：本节（§2 全部子节，包含 13 字段 frontmatter + 五段式 body + 渐进披露 + 触发描述质量 + EVAL 耦合）**仅适用于 mj-agent 仓内 `src/mj_agent/skills/**/SKILL.md`**（in-source canonical），由 mj-agent loader（§7.3 / §7.5 frontmatter strip）解析。
>
> **不适用于**：
> 1. **`.claude/skills/<name>/SKILL.md`**（in-tree engineering-workflow 技能；v2.1 引入）—— 由 Meta v2.1 §3.10 / §7.7 治理，使用 ADR-013 native 2 字段 schema（仅 `name` + `description`）
> 2. **marketplace plugin SKILL.md**（路径 `mj-agentlab-marketplace/plugins/<plugin>/skills/<skill>/SKILL.md`）—— 出 governance；同样使用 ADR-013 native schema
>
> **范围速记**：
> - `src/mj_agent/skills/**` → 本节 §2 生效（13 字段 + 五段式）
> - `.claude/skills/**` → Meta v2.1 §3.10（2 字段 ADR-013 native；与 marketplace plugin 同 schema）
> - `mj-agentlab-marketplace/plugins/**` → ADR-013 决策（出本仓治理）
>
> 三者 schema 边界 [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] + Meta v2.1 §1 plugin loader 边界尊重原则锁定。

### 2.1 body 五段式

沿用 v1.0 §2.1：每个 in-source `SKILL.md` body 必须含 Purpose / When to use / Planning workflow / Common patterns / Anti-patterns 五段。

> **TODO Phase 1**：每段字数推荐 / 范例 / 反例（沿用 v1.0 TODO）。

### 2.2 渐进披露

沿用 v1.0 §2.2：`src/mj_agent/skills/<name>/` 目录可含 `scripts/` / `references/` / `assets/` 子目录。

> **TODO Phase 1**（沿用）：bundled resources frontmatter 要求 / 版本同步 / 孤儿文件检测。

### 2.3 触发描述质量

沿用 v1.0 §2.3：frontmatter `activation` 字段 + 5-iteration 描述优化循环。

### 2.4 EVAL 耦合（A11）

沿用 v1.0 §2.4：SKILL `state: active` 时 frontmatter 必须含 `eval_references`。

> **Phase 0.5 / 1 transitional waiver**（沿用 v1.0）：允许 SKILL `state: active` 但 `eval_references` 为空，需 frontmatter 注释说明"待 Phase 2 补"。Phase D PR-D2 起强制（即 transitional waiver decay）。

### 2.5 现有 SKILL 范例

沿用 v1.0 §2.5：`src/mj_agent/skills/{biz-domain-context, biz-schema-exploration, mj-ddd-semantics, monthly-report, probe-fixture, qcm-analysis, query-optimization, query-writing, safe-sql-analysis}/SKILL.md`（9 in-source skills；v1.0 列举的 query-writing 之外其他 8 个均已存在）。

> **本 v1.1 不动 in-source SKILL**：按用户硬约束（"不能改变 mj-agent 项目本身的代码运行逻辑"）。Phase D PR-D3 通过 `mj-agent-runtime-skill-doc-improve` workflow skill（Phase C 落地）propose 升级 diff 给项目负责人审。

---

## 3. PROMPT Authoring（§3.2）

沿用 v1.0 §3 全部规则。

- §3.1 版本演进：Meta v2.1 §5.5
- §3.2 EVAL 引用：A8（沿用）
- §3.3 token_budget_estimate：可选字段（沿用）
- §3.4 model_binding：跨模型 prompt 需独立版本（沿用）
- §3.5 现有 PROMPT 范例：`src/mj_agent/prompts/system.md`（v1.7+，沿用）

> **TODO Phase 1**：详细字段表 / 示例 / 反例 / 跨模型迁移规则。

---

## 4. EVAL Authoring（§3.3，Phase 2 填充）

沿用 v1.0 §4 全部 TODO Phase 2 项。

---

## 5. CONTRACT (agent-facing tool) Authoring

沿用 v1.0 §5 全部规则与 TODO 项。

---

## 6. ADR-agent / SPEC-agent / GUIDE-agent Authoring

沿用 v1.0 §6（v1.0 §3.5-§3.7）。

---

## 7. PR 校验门禁

### 7.1 阻塞式检查（Agent_Side 范围）

沿用 v1.0 §7.1 全部 5 项（A7 / A8 / A9 / A10 / A11）。**适用范围明确**（v1.1 加注）：

| 编号 | 检查项 | 适用范围 |
|---|---|---|
| A7 | SKILL 路径与目录一致；Python 实现存在 | **仅 `src/mj_agent/skills/**`**（in-source）；`.claude/skills/**` 由 Meta v2.1 §7.7 A12 处理 |
| A8 | PROMPT `state: active` 时 `eval_references` 非空 | 仅 `src/mj_agent/prompts/**` |
| A9 | EVAL `state: active` 时 `dataset_path` 存在 + `baseline_metric` + `baseline_value` 必填 | `docs/evaluation/**` + Phase 2 `evaluation/**` |
| A10 | CONTRACT `state: active` 时 `schema_ref` 存在并指向存在文件 | `docs/contracts/**` |
| A11 | SKILL `state: active` 时 `eval_references` 非空 | 仅 `src/mj_agent/skills/**`；transitional waiver 至 Phase D PR-D2 |

### 7.2 渐进披露检查

沿用 v1.0 §7.2 TODO 项。

### 7.3 frontmatter strip 契约（§7.5，硬约束）— Scope 明确

> **v1.1 scope 明确**：本节硬约束**仅适用于 `src/mj_agent/{skills,prompts}/**`** —— 其他路径（`.claude/skills/**` / marketplace plugin）的 SKILL.md 不经 mj-agent Python loader，由 Claude Code 主进程加载，frontmatter strip 契约对其无意义。

#### 7.3.1 实现要求

沿用 v1.0 §7.3：加载 in-source canonical 的代码必须用 `python-frontmatter` 解析，剥离 YAML 后仅返回 body；独立 `load_<kind>_meta(name)` 接口返回 frontmatter dict。

实现位置：

- `src/mj_agent/skills/__init__.py`：`load_skill()` / `load_skill_meta()`
- `src/mj_agent/prompts/__init__.py`：`load_prompt()` / `load_prompt_meta()`

#### 7.3.2 边界澄清（v1.1 新增）

下列**不**触发本契约：

- Claude Code 主进程加载 `.claude/skills/**/SKILL.md`（不经 mj-agent loader）
- marketplace plugin loader 加载 `mj-agentlab-marketplace/plugins/**/SKILL.md`（出本仓）
- 任何工具读 `.claude/settings.json` 或 `.mcp.json`（不是 SKILL.md，无 frontmatter）

如未来某代码路径出现"加载 `.claude/skills/**/SKILL.md` 作为 mj-agent runtime LLM 上下文"的设计，需先行写 ADR 推翻 plugin loader 边界尊重原则（Meta v2.1 §1）。当前不允许此模式。

### 7.4 §7.5 自检（A11.x，可选升级）

沿用 v1.0 §7.4 TODO Phase 2。

### 7.5 语义对齐校验（A7.1 / A7.2）

沿用 v1.0 §7.5 TODO Phase 2。

### 7.6 跨轨文档（`track: shared`）的处理（v1.1 加注）

沿用 v1.0 §7.6。**v1.1 加注**：当 `track: shared` 文档同时触及 agent-side runtime（如 ADR 改 SKILL.md）+ engineering-workflow（如同 PR 加 `.claude/skills/mj-agent-runtime-skill-doc-improve/`）时，需双 reviewer：Domain Expert + Prompt Engineer + SWE（agent-side）+ Tooling Reviewer（engineering-workflow）。

---

## 8. 审阅角色

沿用 v1.0 §8：

- **必要 1**：Domain Expert / Prompt Engineer（业务理解 + prompt 经验）
- **必要 2**：SWE Reviewer（frontmatter strip 契约 + Python loader 兼容）
- 至少 2 名 reviewer

跨轨文档（`track: shared`）：双轨 reviewer 都需介入（SWE + Domain Expert + Prompt Engineer，至少 3 名）。

> **v1.1 加注**：`track: shared` 同时涉及 engineering-workflow 资产时，再加 Tooling Reviewer（≥4 名 reviewer）。

---

## 9. Plugin 关联

沿用 v1.0 §9 与 §9.1（[[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] 锁定的 dual schema）+ §9.2 plugin skill 章节对应表。

> **v1.1 加注**：随 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] 引入 in-tree `.claude/skills/`（engineering-workflow track；命名空间 `mj-agent-*`），mj-agent 仓内同时存在三种 SKILL 实体：
>
> | 实体 | 路径 | Schema | Loader | 治理章节 |
> |---|---|---|---|---|
> | in-source SKILL（runtime） | `src/mj_agent/skills/<name>/` | 13 字段 | mj-agent Python loader（剥 frontmatter） | 本框架 §2 |
> | in-tree engineering-workflow SKILL | `.claude/skills/mj-agent-*/` | 2 字段 ADR-013 native | Claude Code 主进程（不剥） | Meta v2.1 §3.10 |
> | marketplace plugin SKILL | `mj-agentlab-marketplace/plugins/<plugin>/skills/<skill>/` | 2 字段 ADR-013 native | Claude Code plugin loader | ADR-013（出本仓） |
>
> 三者 body 概念性内容由 `mj-agent-doc-sync`（in-tree workflow skill，Phase 1+ 落地）做内容同步；schema 各自独立演化。

---

## 参考

- 派生自：[[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|v1.0]]
- 上层：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta_Framework v2.1]]
- 决策记录：
  - [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]（双轨原始决策）
  - [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（dual schema 锁定）
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]（v1.1 同期 tri-track 升级）
- 同期子框架：[[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.1|Code_Side v1.1]]
- 行业精度：沿用 v1.0（Anthropic Skills 仓 / skill-creator / DSPy / LangChain Hub / Semantic Kernel / Mitchell 2019 / Gebru 2018）
- 现有 in-source canonical（沿用）：
  - `src/mj_agent/skills/{biz-domain-context, biz-schema-exploration, mj-ddd-semantics, monthly-report, probe-fixture, qcm-analysis, query-optimization, query-writing, safe-sql-analysis}/SKILL.md`
  - `src/mj_agent/prompts/system.md`
