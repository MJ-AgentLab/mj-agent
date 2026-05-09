---
type: adr
domain: SYS
summary: 决议引入双轨文档治理（Code_Side + Agent_Side + Meta 元层）+ skeleton-first 演进 + 双 plugin 骨架（mj-agent-agent-doc / mj-agent-code-doc）
owner: 项目负责人
created: 2026-04-27
updated: 2026-04-29
state: draft
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - dual-track
  - architecture
  - skeleton
---

# ADR 012: Two-Track Documentation Governance

## Context

mj-agent Phase 0 Foundation 已交付 [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|Framework v1.1（archive）]]（含 SKILL / PROMPT / EVAL / CONTRACT 4 类自有 + A7-A10 + 15 domain），覆盖了"文档治理范畴"。但在 Phase 0 收口前的 brainstorming 评估中，发现两个相关问题：

### 问题 1：单一 Framework 文档无法支撑 Documents-Driven-Development × Claude Code

- **体量**：v1.1 已 ~700 行；若内嵌 SKILL body 模板 + 渐进披露 + B 类（plugin / hook / subagent / command / MCP / marketplace）将膨胀到 1500-2500 行
- **社区共识**：plugin-dev plugin 7 skills（plugin-structure / hook-development / agent-development / skill-development / command-development / mcp-integration / plugin-settings）；mj-sys-doc plugin 6 skills（plan / author / migrate / sync / review / validate）；Diátaxis 4 quadrants —— 均显著切分
- **本仓库已开切分先例**：v1.1 + [[../rule/[STANDARD]_GitHub_Markdown|GitHub_Markdown_v1.0]] 共存

### 问题 2：代码侧文档与智能体侧文档存在根本性双轨

| 维度 | Track A 代码侧 | Track B 智能体侧 |
|---|---|---|
| 直接消费者 | 人类（开发 / Reviewer / Ops） | LLM 在 runtime **直接读入** system prompt |
| 失败模式 | **响亮失败**（编译 / 测试 / 部署中断） | **沉默失败**（错答案 / 幻觉 / 业务决策偏差） |
| 测试体系 | pytest / ruff / mypy | EVAL（dataset / judges / baseline / regression_threshold） |
| 审阅者 | SWE Reviewer 充分 | Domain Expert + Prompt Engineer + SWE 三方 |
| 客户面影响 | 间接（服务可用性） | **直接**（每次回答都是输出） |
| DDD 哲学 | 文档**描述**代码 | 文档**就是**代码（body→system prompt） |

行业精度（成熟 AI 系统都是天然双轨）：

- **Hugging Face Hub**：Code repos / Datasets / Models 三 Hub 完全独立
- **MLflow / Kubeflow**：Code (git) + Experiments (runs) + Models (registry) 三轨
- **LangChain Hub**：langchain-core 代码仓 + LangChain Hub（prompts 注册中心）独立
- **Anthropic**：`anthropics/skills` + `claude-code` + Anthropic SDK 三仓分离
- **DSPy**（Stanford）：Programs / Signatures / Teleprompters / Metrics 四轨
- **Semantic Kernel**（Microsoft）：Skills + Plans + Connectors 各独立
- **Google Model Cards / Datasheets for Datasets**（Mitchell 2019; Gebru 2018）：AI artifact 必须有独立结构化文档
- **NIST AI BoM / SPDX-AI**：AI Bill of Materials 标准制定中

mj-agent 在物理（src/skills 与 src/{tools, integrations, agent.py}）/ loader（`load_skill` / `load_prompt` 与一般 import 隔离）/ frontmatter（专属字段）/ 部分 PR 校验（A7-A10）层已分；但**治理层（Framework / PR 模板 / 审阅角色）仍单轨**。这种"物理分但治理混"的过渡态长期产生治理摩擦：同 PR 内 code 改动与 prompt 改动被同一组 reviewer 用同一模板审阅，跳过 EVAL 闭环、不触发 Domain Expert。

---

## Decision

引入双轨文档治理 v2.0 架构，按 skeleton-first 原则演进。

### 决策点 1：v1.1 → v2.0 升级，引入双轨子框架

```
docs/rule/
├── [STANDARD]_..._Documentation_Meta_Framework_v2.0.md   ← 元层（治跨轨规则）
├── [STANDARD]_..._Code_Side_Framework_v1.0.md            ← Track A 子框架
└── [STANDARD]_..._Agent_Side_Framework_v1.0.md           ← Track B 子框架
```

PR 校验门禁拆分：

- A1-A6 + OB1-OB5（v2.0 引入 OB1-OB5，解 v1.1 Gap A9）→ Code_Side
- A7-A10 + **A11**（v2.0 引入：SKILL active 时 `eval_references` 非空，与 A8 对称，解 v1.1 Gap A4）+ §7.5 frontmatter strip 契约 → Agent_Side
- §7.6 `.claude/` 边界 + 跨轨治理协议 + CLAUDE.md sync 双轨分段 → Meta

### 决策点 2：双 plugin 骨架（marketplace）

```
mj-agentlab-marketplace/plugins/
├── mj-agent-agent-doc/   ← Track B 工具（7 skills，紧迫度高）
└── mj-agent-code-doc/    ← Track A 工具（4 skills）
```

Plugin 命名：`mj-agent-agent-doc` 与 `mj-agent-code-doc` 形成对仗；与 marketplace 既有 `mj-sys-*` 命名分流原则一致；用户 brainstorming 中明确选定。

### 决策点 3：skeleton-first 演进

- **Phase 0.5（本 ADR 落地阶段）**：3 STANDARD 骨架（含完整 frontmatter + 章节大纲 + 显式 TODO + 引用回 v1.1）以 `state: draft` 落地 `docs/rule/`，与 v1.1（保持 active）共存；本 ADR-012 同期落地 `state: draft, decision: accepted`
- **Phase 0.5 末**（[[../../plans/[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]] V1-V13 全绿后）：promote PR — v1.1 → archive；v2.0 + 双轨 STANDARDs → active
- **Phase 1**：双 plugin 骨架在 marketplace 仓建立；Track A / B 子框架内容主体填充
- **Phase 2**：EVAL 章节填充；A11 激活
- **Phase 3+**：description-optimize / migrate / hook-author / subagent-author / Plugin_Authoring 等按需加入

骨架内容真空率上限：≤30%（章节大纲 + TODO 之外的实质内容 ≥70%）。

### 决策点 4：frontmatter `track` 字段

新增三值字段 `track: code | agent | shared`，在 [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] §4.3.1 定义。Phase 1 末收紧为 explicit required（移除默认 `shared`）。

边界 artifact 归属规则（**预先写死，避免后续 PR 反复争议**）：

| Artifact / 范例 | 归属 | 理由 |
|---|---|---|
| ADR-002 (Skills as First-Class Citizens) | `agent` | 决策影响 agent runtime |
| ADR-008 (Cross-System Boundary) | `code` | 部署 / 运维决策 |
| ADR-006 (Fail Safe Reads) | `shared` | guardrail 跨代码 + agent；reviewer 双轨 |
| `[CONTRACT]_Tool_SQLExecute` | `agent` | agent-facing tool |
| `[CONTRACT]_MJ_Agent_To_MJ_System_Biz` | `shared` | 跨服务契约 |
| Framework 自身 / Meta_Framework | `shared` | 元层特例 |
| Commit STANDARD / GitHub_Markdown | `code` | 代码侧规约 |
| `src/mj_agent/skills/*/SKILL.md` | `agent` | 默认归属 |
| `src/mj_agent/prompts/*.md` | `agent` | 默认归属 |
| POSTMORTEM-code-incident | `code` | 代码侧故障 |
| POSTMORTEM-agent-misbehavior | `agent` | agent 输出错误 |

---

## Consequences

### 正面

- **审阅角色清晰**：Track B PR 强制 Domain Expert + Prompt Engineer 介入，降低沉默失败风险
- **Framework 体量控制**：每份 STANDARD 维持在 < 300 行，不突破 progressive disclosure 警戒线
- **行业对齐**：与 MLOps Level 2 / Anthropic / Hugging Face / DSPy 等成熟实践对齐
- **plugin 化的演进准备就绪**：marketplace 既有 `mj-sys-*` / `mj-agent-*` 命名分流可承接 `mj-agent-agent-doc` + `mj-agent-code-doc`
- **未来灵活性**：双轨命名让"未来某 ADR 决定走 mj-sys-doc 合并方案 γ"时仍可平移工作量
- **解 v1.1 既有 gap**：A4（SKILL eval coupling）通过 A11 解决；A6（A7 语义校验）在 Agent_Side §7.5 占位；A9（OB1-OB5 漏继承）在 Code_Side §7.2 引入

### 负面

- **运营成本**：3 STANDARD + 2 plugin 共存，维护成本高于单 Framework 方案
- **过渡期混乱**：Phase 0.5 期间 v1.1（active）与 v2.0（draft）共存，新文档作者需明确知道当前权威版本（缓解：`docs/INDEX.md` + CLAUDE.md 同步说明）
- **边界 artifact 决策成本**：`track: shared` 文档需双 reviewer，PR 周期延长（缓解：边界规则预写在本 ADR §Decision 决策点 4）
- **ADR 编号占用**：见下"风险"

### 中性

- **v1.6 roadmap 影响**：roadmap 中已预留 ADR-012/013/014 给 Aggregate-first / Gen UI dataRef / Customer Anonymization 三主题（见 `plans/mj-agent-roadmap-v1.6.md` line 13-15、1333-1335）。本 ADR-012 占用 012 后，roadmap 中那三主题需重编为 ADR-015/016/017。具体重编工作由更新 v1.6 roadmap 的 PR 完成（不属于本 ADR）。

### 风险

- **ADR 编号冲突已知**：用户在 brainstorming 中明确决定使用 ADR-012（接受让 v1.6 roadmap 中的 Aggregate-first / Gen UI dataRef / Customer Anonymization 重编号到 ADR-015/016/017 的成本）。本 ADR §References 列出所有受影响的 v1.6 roadmap 行号，便于维护者操作。
- **mj-sys-doc 长期合并可能性**：若 `mj-agent-code-doc` 实践证明对 mj-system 也有价值，可能 Phase 2+ 触发 mj-sys-doc 升级为通用方案 γ。本 ADR 不做此承诺；留给未来 ADR 决定。
- **plugin 命名最终性**：用户在 brainstorming 中暂定 `mj-agent-agent-doc` 与 `mj-agent-code-doc`，本 ADR 接受此命名并视为最终。如未来发现 `mj-agent-runtime-doc` 更合适，需另开 ADR 修订（涉及 marketplace 仓 plugin 改名 + 用户重新安装）。
- **Phase 0.5 promote PR 推迟**：若 [[../../plans/[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]] V1-V13 长期不全绿，v2.0 三 STANDARD 持续保持 draft；不影响 v1.1 active 状态；可任意推迟无副作用。

---

## Alternatives considered

- **方案 I（Light）**：仅 Framework v1.2 + frontmatter `track` 字段，无 STANDARD 拆分、无 plugin。**未采纳**：太轻；不解决体量与审阅角色问题。
- **方案 II（Medium）**：Framework v1.2 + 单一 Agent_Side_Framework + 4 类 type-specific Authoring STANDARDs（按类型切）。**未采纳**：未充分体现 Track A vs B 的根本性差异；4 个 type STANDARDs 仍可能过度细分（每类一份独立 STANDARD 维护成本高）。
- **方案 IV（Annotation-only）**：仅加 `track` 字段，不拆 STANDARD、不建 plugin。**未采纳**：等同于"做了又没做"；无强制力。
- **方案 α（贡献 skills 给 mj-sys-doc）**：mj-agent 4 类 author skill 加入 mj-sys-doc plugin。**未采纳**：mj-agent 类型定义混入 mj-sys 命名空间，违反 marketplace 命名分流原则；mj-system 团队需为 mj-agent 类型背书。
- **方案 γ（mj-sys-doc 升级为通用）**：mj-sys-doc 纳入 12 类 + A1-A10 + 跨域 domain。**保留为未来选项**：本 ADR 不做合并；如 Phase 2+ 实践证明合并价值，另开 ADR。
- **方案 δ（纯 STANDARD 文档驱动，不做 plugin）**：仅写规则，不做工具化。**未采纳**：违背 DDD 工具化精神；与 mj-sys-doc 已建立的 plugin 化预期相悖。

---

## References

- 上游评估：`C:\Users\Admin\.claude\plans\claude-code-documents-driven-developmen-virtual-finch.md`（本仓外，brainstorming research brief）
- 实施计划：[[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]]
- 同期 STANDARDs：
  - [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]]
  - [[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.0]]
  - [[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.0]]
- 互补 ADR：
  - [[[ADR]_002_Skills_As_First_Class_Citizens|ADR-002]]（Track B 起源）
  - [[[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]（v1.1 → v2.0 升级遵循的 archive 流程）
- v1.6 roadmap 受影响行号（需重编号到 015+）：
  - line 13-15（ADR-012 / 013 / 014 三主题声明）
  - line 118-120（数据流原则映射表）
  - line 185-221（三 ADR 详细说明）
  - line 465-466（实现位置注释）
  - line 1333-1335（ADR 索引表）
  - line 1347 / 1350 / 1351（实现产物表）
- 关联现有 PLAN：
  - [[../../plans/[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]]（v1.1 出厂验证；本 ADR 在 PLAN E 全绿后才进入 Phase 0.5 promote）
  - [[../../plans/[PLAN]_C_Smoke_Expansion_and_ADR_Backfill|PLAN C]]（ADR backfill 应同步增补 `track` 字段）
- 行业精度详细引用：
  - Hugging Face Hub: https://huggingface.co/docs/hub
  - MLflow Model Registry: https://mlflow.org/docs/latest/model-registry.html
  - LangChain Hub: https://smith.langchain.com/hub
  - Anthropic Skills: https://github.com/anthropics/skills
  - plugin-dev plugin: 7 skills 切分（Anthropic 官方 marketplace）
  - DSPy: https://github.com/stanfordnlp/dspy
  - Semantic Kernel: https://github.com/microsoft/semantic-kernel
  - Diátaxis: https://diataxis.fr/
  - Mitchell et al. 2019, "Model Cards for Model Reporting"
  - Gebru et al. 2018, "Datasheets for Datasets"
  - NIST AI RMF + SPDX-AI 提案（2024）

---

## Revision Notes（本 ADR 决策不变；仅记录执行 sequencing 调整）

> ADR 决策本身（双 plugin / 双 STANDARD / Meta 元层 / skeleton-first / 命名）**不变**。本节仅记录 plugin 构建 sequencing 在 Phase 0.5 期间的调整轨迹，方便 reviewer 追溯。

| 日期 | sequencing 调整 | 触发原因 | 承载文档 |
|---|---|---|---|
| 2026-04-27 | 初稿 sequencing：agent-doc Phase 0.5 紧迫（3 skill 骨架）；code-doc Phase 1 全推迟 | brainstorming + ADR-012 决策 | PLAN F §V-skel-4 / §V-skel-5（初稿） |
| 2026-04-29 | **sequencing 翻转**：agent-doc 整体推迟到后续 phase 决议；code-doc 的 `plan` + `author` 提前到 Phase 0.5 部分骨架；code-doc 的 `validate` + `sync` 仍 Phase 1 | 项目负责人决定（runtime 侧 SKILL/PROMPT/EVAL/CONTRACT 框架尚未到使用密度阈值，agent-doc 短期利用率低；优先用 code-doc 验证 plugin 构建工艺） | PLAN F §Revision History + §V-skel-4/5 Revision banner；marketplace 内容蓝图见外部笔记 `temp-ai-chat/mj-agentlab-marketplace/[PLAN]_Marketplace_Plugin_Construction.md` |

> 注：上文 §Decision 决策点 2 中 `mj-agent-agent-doc/` 描述为"7 skills，紧迫度高"——这是 ADR 起草时的上下文判断，不是 ADR 决策的一部分；2026-04-29 起，"紧迫度高"应解读为"ADR 起草时的上下文"，当前实际 sequencing 由 PLAN F 主导。
