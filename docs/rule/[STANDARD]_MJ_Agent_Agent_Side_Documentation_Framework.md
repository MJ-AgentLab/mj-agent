---
type: standard
domain: SYS
summary: Track B 智能体侧文档治理 v1.2 — §4 EVAL Authoring 完整规范（4 子类 + body 八段 + frontmatter schema；ADR-024 决议）；其他 §1-§9 沿用 v1.1
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-09
state: active
version: v1.2
track: agent
supersedes:
  - "mj-agent@archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.1"
  - "mj-agent@archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0"
tags:
  - standard
  - documentation
  - track-b
  - agent-side
  - eval-framework
aliases:
  - MJ-Agent Agent-Side Documentation Framework v1.2
  - MJ-Agent Agent-Side Documentation Framework
  - Track B 子框架 v1.2
---

# MJ-Agent 智能体侧文档治理框架（Track B）

> **状态（Phase D-3 完成后）**：`state: active`，`version: v1.2`。v1.1 已 archive 至 `docs/archive/rule/[DEPRECATED]_..._v1.1.md` + `state: deprecated`。**Active canonical 路径稳定**（ADR-018 §4.4）：本文件名无 `_vX.Y` 后缀。
> **职责**：治理 Track B 文档（SKILL / PROMPT / EVAL / agent-facing CONTRACT / ADR-agent / SPEC-agent / GUIDE-agent）的 authoring 深度规则、PR 校验、loader 契约 ——**仅限 `src/mj_agent/{skills,prompts}/**` 范围**（in-source canonical）+ EVAL 文档（`docs/evaluation/**`）。
> **失败模式**：**沉默失败**（runtime 输出错 → 业务决策偏差）—— 审阅强度高于 Track A。
> **派生自**：[[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.1|v1.1（archive）]]
> **首要变更（v1.1 → v1.2）**：§4 EVAL Authoring 从占位 "沿用 v1.0 §4 全部 TODO Phase 2 项" 升级为完整规范（4 子类 + body 八段 + frontmatter schema + A8/A11 transitional waiver 明确延续 Phase E）。详见 [[decisions/ADR-024_Eval_Framework_Spec|ADR-024]]。

> [!info]
> **v1.1 → v1.2 变化速览**（issue #95 / Phase D-3）：
> - §4 EVAL Authoring 从 4 行占位改 ~150 行完整规范
> - 4 EVAL 子类显式定义（outcome / trajectory / component / integration）
> - frontmatter schema 落实（eval_kind / target_skill / dataset_path / baseline_metric+value / regression_threshold / judges）
> - body 八段（Purpose / Eval Design / Dataset / Judges / Baseline / Regression Criteria / Run History / Open Questions）
> - A8 PROMPT eval_references / A11 SKILL eval_references **transitional waiver 延续到 Phase E**（本 v1.2 不强制；roadmap 显式记录）
> - §5/§6 / §7.1 / §7.5 sustained from v1.1
> - 上一版（v1.1）归档于 [docs/archive/rule/[DEPRECATED]_..._v1.1.md](../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.1.md)

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

承接 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.1]] §1，针对智能体侧补充五条独有原则（沿用 v1.0 §1）：

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
> 三者 schema 边界 [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] + Meta v2.1 §1 plugin loader 边界尊重原则锁定。

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

## 4. EVAL Authoring（v1.2 完整规范；ADR-024 决议）

> **派生自** 上游业务系统 上游 EVAL framework（如有）+ industry references（LangChain Hub / DSPy / Anthropic Skills 仓 model evals 模式 / OpenAI Evals）；**mj-agent 原生**（上游业务系统 暂无对位）。
> **scope**：本节治理 `docs/evaluation/**` 下的 `[EVAL]_*.md` 文档（mj-agent runtime 行为评估单元）。

### 4.1 EVAL 子类（4 类）

| 子类 | 定义 | 范围 | 关注 |
|---|---|---|---|
| **outcome** | 端到端业务结果评估 | 完整 agent trajectory 输出（如 `find_biz_context → execute_sql` 完整链路） | 业务正确性 / 数据准确性 / 输出可读性 |
| **trajectory** | agent 决策路径评估 | tool 调用顺序 / 数量 / argument 正确性 | 调用效率 / 边界判断 / 错误恢复 |
| **component** | 单 skill / prompt 单元评估 | 1 skill 或 1 prompt 的孤立行为 | 触发准确性 / output schema 合规 / latency |
| **integration** | 多 skill 协作评估 | 跨 skill 链路（如 biz-domain-context → safe-sql-analysis） | 上下文传递 / 决策一致性 / scope 守约 |

### 4.2 EVAL frontmatter schema（A9 强制）

```yaml
---
type: eval
domain: AGENT
summary: <20-60 字 描述本 EVAL 的目标 + 范围 + 子类>
owner: <负责人 / 团队>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
state: draft | active | deprecated
track: agent
eval_kind: outcome | trajectory | component | integration   # 4 子类必选 1
target_skill: <stable path / src/mj_agent/skills/<name>/SKILL.md>   # component/trajectory 子类必填；其他子类可选
target_prompt: <src/mj_agent/prompts/<name>.md>             # component 子类（仅 prompt 评估时）必填
dataset_path: <relative path or external URL>              # state: active 时强制（A9）
baseline_metric: <metric name；如 accuracy / precision / latency_p95>
baseline_value: <numeric or threshold>                     # state: active 时强制（A9）
regression_threshold: <numeric or % >                      # 触发回归告警的相对阈值
judges:
  - <judge identifier；如 LLM-as-judge model id / human-rule / programmatic>
---
```

**A9 强制条件**（PR 校验门禁）：`state: active` 的 EVAL 必须含 `dataset_path` 路径存在 + `baseline_metric` + `baseline_value`。

### 4.3 body 八段

```markdown
## 1. Purpose
20-60 字 描述：评估目标 / 业务场景 / 关心的失败模式

## 2. Eval Design
评估设计：测试输入分布 / 输出收集方式 / metric 计算公式 / 抽样策略

## 3. Dataset
数据集说明：来源 / 大小 / 字段 schema / 标注方式 / 版本管理 / 隐私/合规边界

## 4. Judges
判分方式：LLM-as-judge（model id + prompt 链接）/ 人工 rule / programmatic（regex / JSON schema）；judge 可信度 / 偏差缓解

## 5. Baseline
基线建立：date / git commit / model id / config snapshot / 实测数值 + 误差区间

## 6. Regression Criteria
回归判定：相对 baseline 偏差超过 threshold 触发；告警 / 阻塞合并 / 记录但通过 三选一

## 7. Run History
历史运行记录：date / commit / metric / 与 baseline 偏差 / 备注（异常归因 / 改进 hypothesis）

## 8. Open Questions
未解决问题 / 计划改进 / 已知 limitation / 后续迭代候选
```

### 4.4 现有 EVAL 范例

mj-agent 当前 `docs/evaluation/` 空（Phase D-3 未创建 sample EVAL）。Phase E 起首批：
- `[EVAL]_biz_domain_context_outcome.md`（针对 `biz-domain-context` skill；outcome 子类）
- `[EVAL]_safe_sql_trajectory.md`（针对 `safe-sql-analysis` skill；trajectory 子类）
- `[EVAL]_qcm_analysis_integration.md`（biz-domain-context + qcm-analysis + safe-sql-analysis 三 skill 链路；integration 子类）

具体 sample EVAL 落地由 Phase E PR 起首；本 v1.2 仅落 spec。

### 4.5 与 §2 SKILL Authoring (A11) / §3 PROMPT Authoring (A8) 的耦合

| 关联 | 含义 |
|---|---|
| §2.4 EVAL 耦合（A11） | SKILL `state: active` 时 frontmatter 必须含 `eval_references` 指向 1+ 本节 EVAL 文档 |
| §3 PROMPT EVAL 引用（A8） | PROMPT `state: active` 时 frontmatter 必须含 `eval_references` 指向 1+ 本节 EVAL 文档 |
| §7.1 A8/A11 enforcement | **transitional waiver 延续 Phase E**（v1.2 不强制；roadmap 见 §4.6） |

### 4.6 A8/A11 transitional waiver roadmap（v1.2 决议）

**当前状态（Phase D-3 完成后）**：

- A8/A11 规则文本已落（§7.1）
- `scripts/check_frontmatter.py` **不**强制 A8/A11（Phase E 关闭 transitional waiver 时再加）
- mj-agent 6 in-source canonical（5 SKILLs + 1 PROMPT）frontmatter 不含 `eval_references` 字段（合法）

**Phase E 关闭 transitional waiver 的前置条件**：

1. `docs/evaluation/` 至少 3 个 active EVAL 落地（覆盖 5 个 SKILL + 1 PROMPT 的核心评估）
2. EVAL runtime 框架（dataset / judges / metric collection / regression detection）有 MVP 实现
3. 5 SKILLs + 1 PROMPT frontmatter 加 `eval_references` 字段（指向新落 EVAL 文档）
4. `scripts/check_frontmatter.py` 加 SKILL/PROMPT type-conditional A8/A11 校验（state: active 强制）

**Phase E 触发器**：mj-agent 进入 Phase 2 业务功能开发（per `mj-agent-roadmap-v1.6.md`）；EVAL runtime 是 Phase 2 必备项。

### 4.7 Cross-ref

- [[decisions/ADR-024_Eval_Framework_Spec|ADR-024]]（决策记录 + Alternatives + transitional waiver 延续 roadmap）
- [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3 类型表（EVAL 默认 track: agent）
- §2.4 SKILL EVAL 耦合 A11
- §3.2 PROMPT EVAL 引用 A8
- §7.1 PR 校验门禁 A8/A9/A11

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

沿用 v1.0 §9 与 §9.1（[[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]] 锁定的 dual schema）+ §9.2 plugin skill 章节对应表。

> **v1.1 加注**：随 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] 引入 in-tree `.claude/skills/`（engineering-workflow track；命名空间 `mj-agent-*`），mj-agent 仓内同时存在三种 SKILL 实体：
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

- 派生自：[[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|v1.0]]
- 上层：[[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.1]]
- 决策记录：
  - [[decisions/ADR-012_Two_Track_Documentation_Governance|ADR-012]]（双轨原始决策）
  - [[decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（dual schema 锁定）
  - [[decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]]（v1.1 同期 tri-track 升级）
- 同期子框架：[[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]
- 行业精度：沿用 v1.0（Anthropic Skills 仓 / skill-creator / DSPy / LangChain Hub / Semantic Kernel / Mitchell 2019 / Gebru 2018）
- 现有 in-source canonical（沿用）：
  - `src/mj_agent/skills/{biz-domain-context, biz-schema-exploration, mj-ddd-semantics, monthly-report, probe-fixture, qcm-analysis, query-optimization, query-writing, safe-sql-analysis}/SKILL.md`
  - `src/mj_agent/prompts/system.md`
