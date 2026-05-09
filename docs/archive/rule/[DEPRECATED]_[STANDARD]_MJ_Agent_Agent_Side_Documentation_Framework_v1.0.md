---
type: standard
domain: SYS
summary: Track B 智能体侧文档治理 — SKILL/PROMPT/EVAL/agent-facing CONTRACT 的 authoring 深度规则；A7-A10 + A11 + 渐进披露 + EVAL coupling + frontmatter strip §7.5
owner: 项目负责人
created: 2026-04-27
updated: 2026-04-29
state: deprecated
version: v1.0
track: agent
derives_from: mj-agent@[STANDARD]_MJ_Agent_Documentation_Meta_Framework
tags:
  - standard
  - documentation
  - track-b
  - agent-side
  - skeleton
aliases:
  - MJ-Agent Agent-Side Documentation Framework v1.0
  - Track B 子框架 v1.0
archived: 2026-05-09
replaced-by: "../../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md"
---

# MJ-Agent 智能体侧文档治理框架 v1.0（Track B，archived）

> **归档状态（Phase B PR-B3c-promote 完成后）**：本文档已 `state: deprecated`，被 [[../../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]] 取代。归档原因：v1.1 minor bump 加 §2/§7.5 scope 明确 in-source only（`.claude/skills/**` 排除出本框架治理，划归 Meta v2.1 §3.10）；与 Meta v2.1 同期 promote。详见 [[../../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]。
>
> **历史骨架状态（Phase 0.5，紧迫度高于 Code_Side）**：以 `state: draft` 落地，与 [[../[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] 同期 promote。
> **职责**：治理 Track B 文档（SKILL / PROMPT / EVAL / agent-facing CONTRACT / ADR-agent / SPEC-agent / GUIDE-agent）的 authoring 深度规则、PR 校验、loader 契约。
> **失败模式**：**沉默失败**（runtime 输出错 → 业务决策偏差）—— 审阅强度高于 Track A。
> **派生自**：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]]

---

## 0. 范围

| 类型 | 默认 track | Authoring 章节 | 紧迫度 |
|---|---|---|---|
| **SKILL** | agent | §3.1 | **Phase 0.5（最紧迫）** |
| **PROMPT** | agent | §3.2 | Phase 1 |
| **EVAL** | agent | §3.3 | Phase 2 |
| **CONTRACT (agent-facing tool)** | agent | §3.4 | Phase 0.5（与 SQL guardrail 同期） |
| ADR-agent | agent | §3.5 | Phase 1 |
| SPEC-agent | agent | §3.6 | Phase 1 |
| GUIDE-agent | agent | §3.7 | Phase 1 |

跨轨（`track: shared`）文档：本框架 §7.1 校验仍执行；§3 章节按对应类型走；额外审阅角色见 §8。

---

## 1. 设计目标

承接 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] §1，针对智能体侧补充五条独有原则：

| 原则 | 说明 |
|---|---|
| **文档即 runtime code** | SKILL.md / system.md 的 body 字面被 LLM 消费 —— 字面修改即行为修改 |
| **沉默失败需主动检测** | EVAL coupling 是必须；不能依赖人类发现错答案 |
| **渐进披露** | scripts/ + references/ + assets/ 三类 bundled resources（skill-creator 范式） |
| **触发描述质量** | description 决定 skill 是否被调用；undertriggering 是默认问题，需主动用"pushy"短语对抗 |
| **frontmatter strip 契约** | loader 必须剥离 YAML 后只返回 body —— 否则元数据泄露入 LLM 上下文，污染 system prompt |

---

## 2. SKILL Authoring（§3.1，Phase 0.5 主体填充）

> **Scope（[[[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]] 锁定，2026-04-29）**：本节（§2 全部子节，包含 13 字段 frontmatter + 五段式 body + 渐进披露 + 触发描述质量 + EVAL 耦合）**仅适用于 mj-agent 仓内 in-source SKILL.md**（路径 `src/mj_agent/skills/**/SKILL.md`），由 mj-agent loader（§7.3/§7.5 frontmatter strip）解析。
> **不适用于 marketplace plugin SKILL.md**（路径 `mj-agentlab-marketplace/plugins/<plugin>/skills/<skill>/SKILL.md`）。Plugin SKILL.md 由 Claude Code 加载，使用 Claude Code 原生 schema（仅 `name` + `description` 两字段）；body 结构与 marketplace 现存 mj-sys-* plugin 风格对齐，不强制本节五段式。详见 ADR-013 §Decision + 本文件 §9 Plugin 关联。
> **范围速记**：`src/mj_agent/**` → 本节生效；`mj-agentlab-marketplace/plugins/**` → ADR-013 决策生效。

### 2.1 body 五段式（解 Meta v1.1 Gap A1）

每个 `SKILL.md` body 必须含以下五段（顺序固定，便于 LLM 解析）：

```markdown
## Purpose
（1-2 段，能力的目的；回答"这个 skill 在做什么"）

## When to use
（明确触发条件 / 用例 / 反例；为读 SKILL.md 的 LLM 提供"是否选用本 skill"的判定依据）

## Planning workflow
（应该按什么步骤思考 / 计划；让 LLM 在执行前先规划，避免一上来就动手）

## Common patterns
（典型模式 / 范例 / "黄金路径"；可包含示例代码、输入输出格式）

## Anti-patterns
（应避免的错误模式；与 Common patterns 对照）
```

> **TODO Phase 1**：每段的字数推荐（如 Purpose 100-300 字 / When to use 200-500 字）/ 范例 / 反例。

### 2.2 渐进披露（解 Meta v1.1 Gap A2）

```
src/mj_agent/skills/<name>/
├── SKILL.md              ← 主文件（<500 行；frontmatter + 五段式 body）
├── scripts/              ← 可选：bundled 可执行脚本（按需加载，不进 LLM 上下文）
│   └── *.py
├── references/           ← 可选：详细参考资料（被 SKILL.md 显式引用，需要时加载）
│   └── *.md
└── assets/               ← 可选：模板 / 数据 / 静态资源
    └── *
```

> **TODO Phase 1**：
> - bundled resources 的 frontmatter 要求（是否需 type / version / track 字段）
> - 版本同步规则（SKILL.md bump 时 scripts/references/assets 是否必须同 PR 改）
> - "孤儿文件"检测（bundled 文件未被 SKILL.md 引用 → 警告）

### 2.3 触发描述质量（解 Meta v1.1 Gap A3）

frontmatter `activation` 字段：

```yaml
activation:
  when_to_use: "<具体触发短语，'pushy' 风格；例：用户提到 X / 改 Y / 加 Z>"
  when_not_to_use: "<negative space；例：不替代 W；不用于 Q>"
```

> **TODO Phase 1**：引入 skill-creator 风格的 5-iteration 描述优化循环：
> 1. 起 description 初稿
> 2. 生成 20-query trigger eval（10 should-trigger + 10 should-not-trigger）
> 3. 用户审核 eval set
> 4. 跑 5 轮迭代优化 description
> 5. 选 test score 最高的 description（避免 train 过拟合）

### 2.4 EVAL 耦合（解 Meta v1.1 Gap A4，对应新 A11）

SKILL `state: active` 时 frontmatter 必须含 `eval_references`，与 PROMPT A8 对称：

```yaml
state: active
eval_references:
  - "[EVAL]_Component_Skill_QueryWriting_..._v1.0"
```

> **TODO Phase 2**：A11 校验项（待 EVAL 体系建立后激活；当前 Phase 0.5 / 1 期间允许 SKILL `state: active` 但 `eval_references` 为空，需在 frontmatter 注释说明"待 Phase 2 补"）。

### 2.5 现有 SKILL 范例

- [[../../src/mj_agent/skills/query-writing/SKILL|query-writing/SKILL.md]]（Phase 0 唯一 skill）
  - **TODO Phase 0.5**：升级为五段式 body + 增补 scripts/references/assets 渐进披露脚手架（即使初始为空目录也建立）

---

## 3. PROMPT Authoring（§3.2）

### 3.1 版本演进

沿用 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] §5.5（PROMPT 版本演进 + deprecate 移动）。

### 3.2 EVAL 引用（A8）

`state: active` 时 `eval_references` 非空（沿用 v1.1 §7.1 A8）。

### 3.3 token_budget_estimate

可选字段；建议填写以辅助 token 预算管理与 ADR-012（Aggregate-first，v1.6 重编号后的 ADR-015）的实现。

### 3.4 model_binding

记录 prompt 的目标模型（如 `deepseek-v3` / `claude-opus-4-7`）。跨模型 prompt 需独立版本。

> **TODO Phase 1**：详细字段表 / 示例 / 反例 / 跨模型迁移规则。

### 3.5 现有 PROMPT 范例

- [[../../src/mj_agent/prompts/system|system.md]]（Phase 0 唯一 system prompt）

---

## 4. EVAL Authoring（§3.3，Phase 2 填充）

> **TODO Phase 2**：
> - eval_kind 4 子类（outcome / trajectory / component / integration）的语义与适用场景
> - dataset_path 强约束（A9）+ 数据集格式规范（jsonl / 字段表）
> - judges 类型（LLM-judge / rule-based / human）
> - baseline_metric + baseline_value + regression_threshold 的设定方法
> - target_skill / `whole-agent` 特殊值

骨架阶段引用 v1.1 §3.4.3 EVAL 类定义。

---

## 5. CONTRACT (agent-facing tool) Authoring（§3.4，~~Phase 0.5 紧迫~~ → phase 推迟，待项目负责人决议）

仅治理 `contract_kind: tool` 与 agent-facing `contract_kind: mcp`；跨服务 CONTRACT 见 [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side]]（或 `track: shared`）。

> **TODO Phase 0.5**（紧迫，与 SQL guardrail 接口稳定同期）：
> - tool 子类必填字段：input_schema / output_schema / 错误码 / 幂等性 / 副作用 / SLO
> - agent-facing MCP 子类：额外要求 schema_ref 强校验（A10），引用 JSON Schema / OpenAPI 文件
> - 现有需求：`[CONTRACT]_Tool_SQLExecute_v1.0`（待 Phase 0.5 SQL guardrail 接口稳定时落地）

---

## 6. ADR-agent / SPEC-agent / GUIDE-agent Authoring（§3.5-§3.7）

> **TODO Phase 1**：与 Code_Side 等价类的差异点：
> - 更注重 runtime 影响（决策对 LLM 输出的后果）
> - 更强调 EVAL 闭环（决策若改 SKILL/PROMPT，需附 EVAL 计划）
> - 模板可复用 [[../_templates/TEMPLATE_ADR|TEMPLATE_ADR]]，但 Track B ADR 的 §Consequences 必须含"对 agent 行为的预期影响"段

现有 ADR-agent 范例：
- [[../adr/[ADR]_002_Skills_As_First_Class_Citizens|ADR-002]]
- [[../adr/[ADR]_003_Progressive_Disclosure|ADR-003]]

---

## 7. PR 校验门禁

### 7.1 阻塞式检查（Agent_Side 范围）

| 编号 | 检查项 | 自动化阶段 |
|---|---|---|
| A7 | SKILL 路径与目录一致；Python 实现存在（沿用 v1.1 §7.1） | Phase 0 PR review；Phase 2 CI |
| A8 | PROMPT `state: active` 时 `eval_references` 非空（沿用 v1.1 §7.1） | Phase 0 PR review；Phase 2 CI |
| A9 | EVAL `state: active` 时 `dataset_path` 存在；`baseline_metric` + `baseline_value` 必填（沿用 v1.1 §7.1） | Phase 2 CI |
| A10 | CONTRACT `state: active` 时 `schema_ref` 存在并指向存在文件（沿用 v1.1 §7.1） | Phase 0 PR review；Phase 2 CI |
| **A11**（v1.0 新增） | SKILL `state: active` 时 `eval_references` 非空（解 Meta v1.1 Gap A4，与 A8 对称） | **Phase 2 激活**（Phase 0.5 / 1 期间允许空，frontmatter 加注释） |

### 7.2 渐进披露检查（v1.0 新增）

> **TODO Phase 1**：
> - 当 SKILL 含 scripts/references/assets 子目录时，每个 bundled 文件须被 SKILL.md 显式引用（防"孤儿文件"）
> - 引用方式：相对路径（`see scripts/foo.py`）或 Wikilink（`[[scripts/foo.py]]`）
> - 校验工具：`mj-agent-agent-doc-validate` skill 内的 `check_skill_bundled_resources()`

### 7.3 frontmatter strip 契约（§7.5，硬约束）

> 沿用 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §7.5。

加载 in-source canonical（`src/mj_agent/skills/**/SKILL.md`、`src/mj_agent/prompts/*.md`）作为 LLM prompt 输入的代码必须：

1. 用 `python-frontmatter` 或等价 YAML frontmatter 解析器
2. 把 YAML frontmatter 剥离后，**仅返回 body**
3. 独立提供 `load_<kind>_meta(name)` 接口返回解析后的 frontmatter 字典

实现位置：

- `src/mj_agent/skills/__init__.py`：`load_skill()` / `load_skill_meta()`
- `src/mj_agent/prompts/__init__.py`：`load_prompt()` / `load_prompt_meta()`

### 7.4 §7.5 自检（A11.x，可选升级）

> **TODO Phase 2**：单元测试断言 loader 返回值不以 `---\n` 开头；调用 `load_skill_meta('query-writing')` 后断言返回 dict 含必填字段。

### 7.5 语义对齐校验（A7.1 / A7.2，解 Meta v1.1 Gap A6）

> **TODO Phase 2**：
> - A7.1：SKILL.md 描述的工具依赖（`tool_dependencies` 列表）与代码实际 `import` 是否一致
> - A7.2：SKILL.md `When to use` 触发短语与 skill-creator 风格的 trigger eval 通过率是否符合阈值

骨架阶段不强制；Phase 2 自动校验器实现后激活。

---

## 8. 审阅角色

> **强 reviewer 要求**（与 Track A 单一 SWE Reviewer 形成对比）：

- **必要 1**：Domain Expert / Prompt Engineer（具备业务理解 + prompt 经验）
- **必要 2**：SWE Reviewer 一名（确保不破坏 frontmatter strip 契约 + Python loader 兼容）

→ **至少 2 名 reviewer**。

PR 流程建议：

- 先 Domain Expert / Prompt Engineer 审 body 内容（语义、business correctness、EVAL 计划）
- 再 SWE Reviewer 审 frontmatter / loader 契约 / 测试

跨轨文档（`track: shared`）：双轨 reviewer 都需介入（SWE + Domain Expert + Prompt Engineer，至少 3 名）。

---

## 9. Plugin 关联

本框架的执行工具是 `mj-agent-agent-doc` plugin（marketplace `mj-agentlab-marketplace/plugins/mj-agent-agent-doc/`）。**2026-04-29 sequencing 翻转**：原 Phase 0.5 紧迫的 plugin 骨架（含 skill-author / validate / tool-contract-author 三 skill）整体推迟，phase 时间窗待项目负责人决议；详见 [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-4 Revision banner。

### 9.1 Plugin SKILL.md schema（[[[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]，2026-04-29）

marketplace plugin SKILL.md **不复用本框架 §2 的 13 字段 schema**，改用 Claude Code 原生格式：

```yaml
---
name: <plugin-name>-<skill-name>
description: <长 description；含「Make sure to use this skill whenever...」式触发短语；含"不适用于"反例；可中英双语 trigger 词>
---
```

理由（详见 ADR-013 §Context）：
1. Claude Code plugin loader 只读 `description` 字段做触发匹配，不识别 §2 的 `type / domain / state / version / track / owner / summary / activation.triggers / related_prompts / eval_references` 等字段。
2. marketplace 现存 4 个 mj-sys-* plugin（v2.0+）已使用 2 字段 schema 作为既定事实标准。
3. §7.3 / §7.5 frontmatter strip 契约只对 mj-agent in-source loader 有意义，与 Claude Code plugin loader 无关。

mj-agent 仓内 in-source SKILL.md（`src/mj_agent/skills/**/SKILL.md`）与 marketplace plugin SKILL.md 的内容同步由 `mj-agent-code-doc-sync` skill（Phase 1，PLAN F §V-content-2）处理；同步的是 body 中的概念性内容，不同步 frontmatter schema。

`docs/_templates/TEMPLATE_SKILL.md` 仅服务 in-source SKILL.md；plugin SKILL.md 起草时不引用此模板，可参考 ADR-013 §Decision 内嵌范本或 marketplace 现存 mj-sys-* plugin 实例。

### 9.2 Plugin Skill 章节对应表（既有内容）

| Skill | 章节对应 | Phase |
|---|---|---|
| `mj-agent-agent-doc-plan` | 跨章节（agent-side 文档需求规划） | 推迟（待决） |
| `mj-agent-agent-doc-skill-author` | §2（SKILL Authoring 全套） | ~~Phase 0.5（紧迫）~~ → 推迟（待决） |
| `mj-agent-agent-doc-prompt-author` | §3（PROMPT Authoring） | 推迟（待决） |
| `mj-agent-agent-doc-tool-contract-author` | §5（agent-facing CONTRACT） | ~~Phase 0.5（紧迫）~~ → 推迟（待决） |
| `mj-agent-agent-doc-eval-author` | §4（EVAL Authoring） | Phase 2 |
| `mj-agent-agent-doc-validate` | §7.1 + §7.2 + §7.3 + §7.4 | ~~Phase 0.5（紧迫）~~ → 推迟（待决） |
| `mj-agent-agent-doc-sync` | Meta v2.0 §6（INDEX 同步 + CLAUDE.md `Agent-Side` 段维护） | 推迟（待决） |

> 注：本表所有 phase 标签于 **2026-04-29** 调整为"推迟（待决）"或保留原 phase。仅 `eval-author` 仍按原 Phase 2 计划（其专属依赖是 EVAL infra，与 plugin sequencing 无关）。

---

## 参考

- 派生自：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]]
- 决策记录：[[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]
- 同期子框架：[[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.0]]
- 实施计划：[[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]]
- 行业精度：
  - Anthropic Skills 仓（github.com/anthropics/skills）：SKILL.md + bundled resources 工业标准
  - skill-creator plugin：5-iteration 描述优化循环
  - DSPy（github.com/stanfordnlp/dspy）：Programs / Signatures / Teleprompters / Metrics 四轨
  - LangChain Hub（smith.langchain.com/hub）：prompt 独立 registry
  - OpenAI Function Calling / Assistants API：function schema 强类型化分离
  - Semantic Kernel：`*.skprompt.txt` + `config.json` 双文件模式
- 现有 in-source canonical（升级时补 `track: agent`）：
  - `src/mj_agent/skills/query-writing/SKILL.md`
  - `src/mj_agent/prompts/system.md`
