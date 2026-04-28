---
type: standard
domain: SYS
summary: 元框架（v1.1 升级）—— 引入 track 字段与双轨子框架，治理 types/layers/lifecycle/archive 跨轨规则；骨架交付 Phase 0.5
owner: 项目负责人
created: 2026-04-27
updated: 2026-04-28
state: active
version: v2.0
track: shared
derives_from: mj-agent@archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1
supersedes:
  - "mj-agent@archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1"
tags:
  - standard
  - documentation
  - framework
  - meta
  - dual-track
  - skeleton
aliases:
  - MJ-Agent Documentation Meta Framework v2.0
  - mj-agent 文档治理元框架 v2.0
---

# MJ-Agent 文档治理元框架 v2.0

> **骨架状态（Phase 0.5）**：本文档以 `state: draft` 进入 `docs/rule/`，与 v1.1（保持 `state: active`）共存。Phase 0.5 promote PR 完成后，v1.1 移入 `docs/archive/rule/` + state 改 deprecated；本文档转 `state: active`。详见 [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-3。
> **派生自**：[[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|Framework v1.1（archive）]]
> **首要变更**：引入 `track` frontmatter 字段 + 双轨子框架（Code_Side + Agent_Side）+ 跨轨治理协议
> **决策记录**：[[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]

---

## 0. v1.1 → v2.0 升级范围速览

| 维度 | v1.1 现状 | v2.0 目标态 |
|---|---|---|
| 治理类型枚举 | 12 类 canonical（8 继承 + 4 自有） | **保留**（不改类型枚举） |
| Frontmatter | 必填字段 + 类型专属字段 | **+ 新增 `track` 字段**（code / agent / shared） |
| Authoring 深度规则 | Framework 内嵌（散落 §3.4 等） | **外包给 Code_Side + Agent_Side 两份子框架** |
| §7.1 PR 校验门禁 | A1-A10 全部内嵌 | **A1-A6 → Code_Side；A7-A10 + 新 A11 → Agent_Side；§7.5 / §7.6 → Meta** |
| §6.4 CLAUDE.md sync | 单一 allowlist | **按 track 分段**（code 与 agent reviewer 各管一段，§6.4.1） |
| §9 Domain 枚举 | 15 项 | **保留**（增加 track 倾向列） |
| §7.6 `.claude/` 边界 | 整体出 governance | **TODO Phase 1**：区分 marketplace 边界 vs 项目级 `settings.json` |
| OB1-OB5 非阻塞观察 | v1.1 漏继承 | **由 Code_Side §7.2 引入**（解 v1.1 Gap A9） |

---

## 1. 设计目标

> 元框架的职责是治"跨轨共同规则"，**不**治某一轨的具体内容深度。

承接 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §1.1 全部核心原则；新增双轨原则：

| 原则 | 说明 |
|---|---|
| 真实资产优先 | 见 v1.1 §1.1 |
| 目录即职责 | 见 v1.1 §1.1 |
| 真相源最小化 | 见 v1.1 §1.1 |
| 流程与文档解耦 | 见 v1.1 §1.1 |
| 生成优先于手工维护 | 见 v1.1 §1.1 |
| in-source 治理 | 见 v1.1 §1.1 |
| **双轨分轨**（v2.0 新增） | Track A 代码侧 vs Track B 智能体侧文档治理分离；元框架仅治共同元规则；Track A/B 失败模式根本不同（响亮 vs 沉默） |
| **skeleton-first 演进**（v2.0 新增） | 架构演进先交付骨架（含完整 frontmatter + 章节大纲 + 引用回旧版本），内容随 phase 渐进填充；不留内容真空率超 30% 的空壳 |

详细行业精度（Hugging Face / MLflow / LangChain Hub / Anthropic Skills 仓 / DSPy / Semantic Kernel / NIST AI BoM）见 [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] §Context。

---

## 2. 三层文档模型

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §2 全部规则。**目录结构无变化**。新增 §2.5 显式标注双轨子框架位置。

### 2.5 双轨子框架（v2.0 新增）

```
docs/rule/
├── [STANDARD]_..._Meta_Framework_v2.0.md            ← 元层（本文）
├── [STANDARD]_..._Code_Side_Framework_v1.0.md       ← Track A
├── [STANDARD]_..._Agent_Side_Framework_v1.0.md      ← Track B
├── [STANDARD]_GitHub_Markdown_v1.0.md               ← 归 Code_Side（治渲染语法）
└── [STANDARD]_..._Commit_Message_Convention_v1.0.md ← 归 Code_Side（治代码规约）
```

---

## 3. 类型与目录

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §3。**类型枚举不变**（12 类 canonical）。

每类的"track 倾向"在 Code_Side / Agent_Side 子框架的对应章节详细定义。简表：

| 类型 | 默认 track | 由哪个子框架治理深度规则 |
|---|---|---|
| GUIDE | code | [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0\|Code_Side]] §3.1 |
| ADR | shared（按主题决定） | Code_Side（code-ADR）/ Agent_Side（agent-ADR） |
| SPEC | shared | 同 ADR |
| RUNBOOK | code | Code_Side §3.4 |
| POSTMORTEM | shared | 按事件类型 |
| STANDARD | shared | Meta（治跨轨）/ Code_Side（治代码规约） |
| ISSUE | shared | 按主题 |
| ASSESSMENT | shared | 按评估对象 |
| **SKILL** | **agent** | [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0\|Agent_Side]] §3.1 |
| **PROMPT** | **agent** | Agent_Side §3.2 |
| **EVAL** | **agent** | Agent_Side §3.3 |
| **CONTRACT** | shared | Agent_Side（agent-facing tool）/ Code_Side（cross-service） |

---

## 4. 命名与 Frontmatter

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §4 全部规则。**新增 `track` 字段**：

### 4.3.1 track 字段（v2.0 新增）

```yaml
---
...
track: code | agent | shared
---
```

| 取值 | 含义 | 默认值 |
|---|---|---|
| `code` | Track A — 代码侧文档（开发 / 部署 / 运维） | 见 §3 类型表 |
| `agent` | Track B — 智能体侧文档（runtime 直接影响业务） | 见 §3 类型表 |
| `shared` | 跨轨 — 双轨 reviewer 都需介入 | **过渡期**默认值；Phase 1 末收紧为 explicit required |

边界 artifact 归属规则见 [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] §Decision。

---

## 5. 状态与生命周期

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §5 全部规则（含 §5.6 Major.Minor 版本演进 + archive 流程）。

### 5.7 双轨语境下的 archive（v2.0 新增）

archive 时保留原 `track` 字段值；living/frozen 引用判断不受 track 影响。本文档自身的"v1.1 → v2.0"升级即遵循此规则。

---

## 6. 索引与引用规则

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §6 全部规则。

### 6.4.1 CLAUDE.md 双轨分段（v2.0 新增）

> **TODO Phase 1**：填充完整规则。

CLAUDE.md 内部按 track 分两段：

- `## Code-Side Documentation`：由 `mj-agent-code-doc-sync` skill 自动维护
- `## Agent-Side Documentation`：由 `mj-agent-agent-doc-sync` skill 自动维护

跨轨段（如 Meta_Framework 自身、`track: shared` 的 ADR）放在文档顶部独立段。

---

## 7. 自动校验与 PR 集成

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §7 全部规则。**校验门禁按轨重新分配**：

### 7.1 PR 校验门禁（v2.0 重新分配）

| 编号 | 检查项 | 由哪个子框架治理 |
|---|---|---|
| A1-A6 | 路径 / frontmatter / state / Wikilink / INDEX / CLAUDE.md sync | [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0\|Code_Side]] §7.1（同时被 shared 文档继承） |
| **OB1-OB5** | 非阻塞观察项（v2.0 引入，解 v1.1 Gap A9） | Code_Side §7.2 |
| A7-A10 | SKILL/PROMPT/EVAL/CONTRACT 专属 | [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0\|Agent_Side]] §7.1 |
| **A11**（v2.0 新增） | SKILL `state: active` 时 `eval_references` 非空（解 v1.1 Gap A4，与 A8 对称） | Agent_Side §7.1 |
| A7.x（语义校验） | 行为对齐（doc 描述 vs 代码实现） | Agent_Side §7.1（draft，Phase 2 实现） |
| §7.5 frontmatter strip | loader 契约 | Agent_Side §7.5（沿用 v1.1 §7.5） |
| §7.6 `.claude/` 边界 | TODO Phase 1 细化 | Meta（本文）§7.6 |

### 7.6 `.claude/` 边界（待细化）

> **TODO Phase 1**：区分两类 `.claude/` 用法：
> 1. **marketplace 配置 / 用户私有**（如 `~/.claude/settings.json`、`.claude/*.local.json`）：保持出 governance（沿用 v1.1 §7.6）
> 2. **项目级 `.claude/settings.json`**（团队共享、提交到 git）：纳入 §6.4 sync allowlist

当前阶段沿用 v1.1 §7.6 整体排除作为过渡。

---

## 8. 迁移与落地规则

### 8.1 v1.1 → v2.0 升级路径（Phase 0.5 promote）

> 详见 [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]] §V-skel-3。

1. 本文档 `state: draft → active`
2. v1.1 走 v1.1 §5.6.2 archive：`git mv docs/rule/[STANDARD]_..._Framework_v1.1.md docs/archive/rule/[STANDARD]_..._Framework_v1.1.md`；frontmatter `state: active → deprecated`；body 顶部加状态横幅指向 v2.0
3. Code_Side / Agent_Side 子框架同期由 `state: draft → active`
4. 现有 canonical 文档增补 `track` 字段（默认 `shared`，逐文档审计实际归属）
5. PR 模板拆分为 code-track / agent-track / shared-track 三套 reviewer 期望
6. CLAUDE.md 内部分段（§6.4.1）

### 8.2 后续 phase 填充计划

详见 [[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]]。

---

## 9. Domain 枚举

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §9 全部 15 项。**新增 track 倾向**列：

| 编号 | Domain | 默认 track | 说明 |
|---|---|---|---|
| 1 | AGENT | agent | agent 编排 / 状态 / 生命周期 |
| 2 | SKILL | agent | skill 定义 |
| 3 | PROMPT | agent | system prompt / prompt 模式 |
| 4 | TOOL | agent | 工具实现（agent 调用方） |
| 5 | GUARDRAIL | shared | 运行时安全（跨代码 + agent） |
| 6 | MEMORY | agent | checkpointer / store / cache |
| 7 | EVAL | agent | 评估数据集 / judges / baselines |
| 8 | GATEWAY | shared | LLM Gateway（跨代码 + agent） |
| 9 | INTEGRATION | shared | 跨仓库契约 |
| 10 | UI | shared | 前端（前端代码 + agent 输出契约） |
| 11 | OPS | code | 部署 / CI/CD / 监控 |
| 12 | SYS | shared | 跨领域元层 |
| 13 | SEC | shared | 认证 / 授权 / RBAC |
| 14 | OBS | code | 观测性 / 追踪 / 告警 |
| 15 | DATA | shared | 数据治理 / 匿名化 / 审计 |

`shared` domain 内部仍可按文档主题决定 `track` 字段；domain 与 track 不强 1:1。

---

## 10. 快速操作清单

> 沿用 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|v1.1（archive）]] §10。**新增 §10.6**：

### 10.6 选择 track（v2.0 新增）

新建 canonical 文档时按以下顺序确定 track：

1. **类型默认**（见 §3 类型表）：SKILL/PROMPT/EVAL → `agent`；GUIDE/RUNBOOK → `code`；其他先 `shared`
2. **主题归属**：
   - 业务 runtime 影响（输出错就是业务事故）→ `agent`
   - 开发 / 部署 / 运维（影响服务可用性）→ `code`
   - 跨轨 / 模糊 → `shared`
3. **边界规则**：见 [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] §Decision 边界 artifact 归属表

---

## 参考

- 派生自：[[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|Framework v1.1（archive）]]
- 决策记录：[[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]
- 子框架：
  - [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|Code_Side v1.0]]
  - [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side v1.0]]
- 实施计划：[[../../plans/[PLAN]_F_Documentation_Track_Split_And_Plugin_Skeleton|PLAN F]]
- 关联现有：[[../../plans/[PLAN]_E_Phase0_Docs_Governance_Verification|PLAN E]]（v1.1 验证；v2.0 promote 必须在 PLAN E 全绿后）
- 行业精度：Hugging Face Hub / MLflow Model Registry / LangChain Hub / Anthropic Skills 仓 / DSPy / Semantic Kernel / Twelve-Factor App / Google Model Cards (Mitchell 2019) / NIST AI BoM
