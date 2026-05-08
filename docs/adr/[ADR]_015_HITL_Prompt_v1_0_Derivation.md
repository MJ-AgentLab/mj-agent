---
type: adr
domain: WORKFLOW
summary: 决议从 mj-system v1.0 派生 mj-agent HITL_Prompt v1.0；§1-§3 verbatim + §4 mj-agent 适配（去 n8n / 加 3 风味实现 / 加 runtime+infra 类目）+ §5 mj-agent skill 矩阵；Lite Phase A（Intake / Repo_Scan 子规范延后 Phase B+）
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-08
state: active
decision: accepted
track: engineering-workflow
tags:
  - adr
  - hitl
  - prompt
  - engineering-workflow
  - derivation
  - skeleton
---

# ADR 015: HITL_Prompt v1.0 Derivation from mj-system

## Context

[[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] 引入第三轨 engineering-workflow，但其下治"AI 工程执行闭环"的具体规范缺位。mj-system 在 2026-05 期间沉淀出 `[STANDARD]_AI_Engineering_Execution_HITL_Prompt.md` v1.0，覆盖 17-stage 闭环（Intake → Post-merge）+ §2 Prompt 通用结构 + §3 HITL 通用规则 + §4 15 个 stage prompts + §5 36 skills hint matrix + §6 终则。该 STANDARD 已在 mj-system 实际使用 ~1 个月，证明可行。

mj-agent 项目负责人 2026-05-08 brainstorming 中明确选定 **"全量 17 stage 派生（按 mj-agent 调整）"** 作为 HITL 深度。但 mj-agent 与 mj-system 在以下几个层面存在显著差异，不能 1:1 复制：

### 差异 1：技术栈与流程构件

| 维度 | mj-system | mj-agent |
|---|---|---|
| 语言 / 包管理 | Java + Maven | Python 3.13 + uv |
| 测试 | Maven test | pytest（unit / eval / integration / smoke / contract 五类） |
| Lint / 类型 | maven plugins | ruff + mypy strict |
| ETL 编排 | n8n（7 个 plugin skill 治理） | **不使用** |
| 数据库 schema 演进 | Flyway + Trigger + pg_cron + DDL workflow | **只读消费者**（ADR-006 + ADR-009；无 schema 演进权） |
| 服务架构 | 多服务（aec / dqv / qvl / qcm / sac / fc）+ FastAPI | 单服务（LangGraph + Chainlit + CLI）+ Studio |
| 部署 | 多 compose project | **独立 compose project**（与 mj-system 并行；ADR-008） |

直接复制 mj-system §4 prompts 会引用 n8n / Flyway / 多服务 endpoints，对 mj-agent 无意义；§4.7 / §4.8 关于 SQL DDL 验证的详细 rules 也不适用。

### 差异 2：in-source canonical 的运行时角色

mj-agent 的 `src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/system.md` 是 **runtime LLM 上下文的字面输入**（[[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side]] §2 + §7.5 frontmatter strip 契约）。任何 body 修改 = LLM 行为修改，是 §3.1 必停 HITL 项；mj-system 没有这种 in-source canonical 模式。

### 差异 3：业务数据语义镜像

mj-agent 的 `src/mj_agent/biz_catalog/qcm_catalog.yaml` 是 mj-system 上游 `[STANDARD]_Biz_DWS_Naming_Stability` §2-§4 的**镜像**。任何镜像漂移导致 `find_biz_context` tool 返回错误业务语义；mj-system 自身定义这个 STANDARD，没有镜像漂移问题。

### 差异 4：上游子规范引用链

mj-system §4.1 / §4.4 分别引用其自有子规范 `[STANDARD]_AI_Engineering_Intake.md` 与 `[STANDARD]_AI_Engineering_Repo_Scan.md`。mj-agent 派生时这两个子规范也应该派生，但全量派生会显著加重 Phase A 体量（用户 2026-05-08 follow-up 确认采用 Lite Phase A，先用上游占位，差异显著时 Phase B+ 派生）。

### 差异 5：skill 命名空间与覆盖矩阵

mj-system 有 36 个 in-tree skills（含 7 n8n + 4 ops；不适用 mj-agent）。mj-agent 目标态是 32 个 in-tree skills（5 family：flow 9 / git 9 / doc 6 / runtime 4 / infra 4），与 mj-system 范围有交集但不重合：

- **保留对位**：flow 9 / git 9（与 mj-system 一致）+ doc family 重组（6 个，去 n8n 子集）
- **mj-agent 专属新增**：runtime（4 个，**read-only by design**，治 in-source canonical 改进）+ infra（4 个，治 mj-agent 专属 Docker compose / Studio probe / storage stack / env-setup）
- **完全不引入**：n8n family（mj-agent 不用）+ ops family（mj-agent 不需 ETL 编排）

### 矛盾结论

不立 ADR 锁定 derivation 决策：

- 后续 PR 起草 §4 stage prompt 时反复争议"哪些 verbatim、哪些改写"
- §5 矩阵 5 个 family 的 skill 列表反复变化
- Lite Phase A vs Full Phase A 的边界不清晰，可能误把 Intake / Repo_Scan 子规范扩进 Phase A

---

## Decision

引入 mj-agent HITL_Prompt v1.0，按以下原则派生自 mj-system v1.0。

### 决策点 1：派生模式 = §1-§3 verbatim + §4 适配 + §5 mj-agent 矩阵 + §6 verbatim

| 章节 | mj-agent 处理 | 理由 |
|---|---|---|
| §1 总体流程 | **verbatim**（17 stages 不变） | 17-stage 闭环是普适 AI engineering workflow，与具体技术栈无关 |
| §2 Prompt 通用结构 | **verbatim**（仅 mj-sys-* → mj-agent-* skill 命名空间替换） | Task / Reference Docs / Skill Hint / Rules / Output 是普适结构 |
| §3 HITL 通用规则 | **verbatim 大体**（删 1 项 n8n + 加 4 项 mj-agent 专属） | §3.1 必停规则是普适项；mj-agent 专属新增 4 项（runtime SKILL/PROMPT body / qcm_catalog 镜像 / SQL guardrail / system prompt version bump）由差异 2-3 触发 |
| §4 15 个 stage prompts | **mj-agent 适配**（每个 stage 内容按 mj-agent 调；refs 替换；rules 加风味区分） | 差异 1-3 决定每个 stage 的具体内容必须重写 |
| §5 Skill Hint matrix | **mj-agent 重建**（5 family 32 skills，去 n8n + ops；加 runtime + infra） | 差异 5 决定矩阵不能复制 |
| §6 终则原则 | **verbatim**（仅替换 mj-sys → mj-agent 上下文） | 终则是普适思维框架 |

### 决策点 2：Lite Phase A（用户 2026-05-08 follow-up 确认）

mj-system v1.0 §4.1 / §4.4 引用的两个子规范（`[STANDARD]_AI_Engineering_Intake.md` + `[STANDARD]_AI_Engineering_Repo_Scan.md`）**不**在 Phase A 同期派生 mj-agent 版。Phase A 期间 §4.1 / §4.4 直接引用 mj-system 上游 STANDARD（`mj-system@docs/rule/[STANDARD]_AI_Engineering_Intake.md` / `_AI_Engineering_Repo_Scan.md`）作为占位，标记 Lite Phase A 来源。

mj-agent 调版触发条件（Phase B+）：

- 当 mj-agent-flow-intake / mj-agent-flow-repo-scan skill 落地后（PR-B2），开发实践中发现 mj-system 上游规则与 mj-agent 上下文偏差太大（如 §6 multi-service scan 在单服务 mj-agent 不适用）
- 或者外部 reviewer 反馈"读 HITL_Prompt §4.1 跳到 mj-system 仓很跳脱"
- 触发后开 follow-up PR：`[STANDARD]_MJ_Agent_AI_Engineering_Intake_v1.0` + `_Repo_Scan_v1.0`，与 mj-agent-flow-* skill 同 PR 落地，闭环

### 决策点 3：Stage 8 Implementation 三风味区分（mj-agent 专属）

mj-agent §4.7 引入 3 种实现风味（mj-system §4.7 没有显式区分，因为它没有 in-source canonical）：

- **风味 A：纯代码**（`src/mj_agent/{config,server,memory,integrations,...}/` + `tests/` + `infra/docker/`）—— TDD red-green；ruff/mypy strict；与 mj-system §4.7 大体一致
- **风味 B：in-source canonical**（`src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md`）—— **永远 HITL**；A11 EVAL 门禁；frontmatter strip 契约不破坏；五段式 body 保持
- **风味 C：infra**（`infra/docker/` + `pyproject.toml` + `langgraph.json` + `qcm_catalog.yaml` + `.env.example` + `scripts/`）—— `mj-agent check` healthcheck 必过；compose up/down 排练；`uv lock` + `uv sync`

每种风味在 §4.7 Rules 段有专属硬约束（B: rules 9-12；C: rules 13-15）。

### 决策点 4：Runtime 类目硬约束（read-only by design）

`mj-agent-runtime-*` 4 个 skill（`-skill-doc-improve` / `-prompt-version-bump` / `-biz-catalog-sync` / `-eval-baseline`）都是 **read-only inspect** 设计：

- **职责**：propose diff、跑反向扫描、列出影响清单、给项目负责人审批材料
- **禁止**：直接 `Edit` / `Write` 工具调用到 `src/mj_agent/{skills,prompts,agent.py,tools}/`
- **强制机制**：每个 SKILL.md "Anti-patterns" 段必须明文写"Do NOT modify src/mj_agent/...";A12 描述质量门禁（[[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]] §7.7）校验该 anti-pattern 是否在 description 中提及
- **理由**：保持用户硬约束（"不能改变 mj-agent 项目本身的代码运行逻辑"）；Phase D 评估是否需要引入 hooks 兜底

### 决策点 5：EVAL backlog ticket 自动开单（A11 transitional waiver 衰减）

§4.15 Post-merge Rule 11（mj-agent 专属，v1.0 引入）：若 PR 触及 in-source canonical body 修改，无论本 PR 是否带 EVAL 引用，均自动开 follow-up Issue 标记 `[EVAL backlog]`。

理由：

- A11 EVAL 强制（[[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side]] §7.1）目前在 transitional waiver 期内（允许 SKILL `state: active` 但 `eval_references` 注释 TODO）
- 自动开 backlog ticket 让 transitional waiver 期内的所有改动有可追溯凭证；Phase D（Phase 2）启动时一次性补 EVAL 不会有遗漏
- mj-system 没有此机制因为它的 SKILL.md 不是 runtime canonical，沉默失败模式不存在

### 决策点 6：HITL gates 集中位置 = stages 5 / 7 / 9 / 11 / 13（与 mj-system 一致）

不改动 HITL gates 触发位置；mj-system §4 实践中已验证这 5 个位置的 HITL 触发率与开发体验最佳。

---

## Consequences

### 正面

- **快速落地**：派生而非从零设计，节省 ~80% 设计成本；mj-system 实践 1 个月成熟度直接继承
- **一致性**：mj-agent 与 mj-system 开发者切换两仓时无须切换 mental model；§1-§3 / §6 完全一致；§4 各 stage 触发条件一致
- **mj-agent 专属差异显式化**：§3.1 + §4 风味区分 + §4.15 EVAL backlog 让 in-source canonical 与 biz catalog 漂移这两类 mj-agent 独有失败模式被显式管控
- **Lite Phase A 节奏可控**：Phase A 体量收敛到 PR-A1 + PR-A2 + PR-A3 三个 PR；Intake / Repo_Scan 派生延后到差异显著时再做，避免无谓工作
- **Runtime 类目硬约束让用户硬约束有显式机制**："不能改变 mj-agent 项目本身的代码运行逻辑" → Anti-patterns 段 + A12 描述质量门禁 + Phase D hooks 兜底（待评估）
- **HITL_Prompt v1.0 与 ADR-014 形成完整 Track C 体系**：v2.1 trio 是骨架；HITL_Prompt 是骨架上跑的具体规则；§5 矩阵指引哪个 skill 在哪个 stage 用

### 负面

- **§4 占位 skill 引用语义债**：Phase A 落地时 §4 各 stage 的 Preferred Skill 都是占位（PR-B+ 落地）；HITL_Prompt v1.0 在 Phase A 期间无法实际通过 skill 触发执行，仅作为人读规范使用
- **`mj-system@...` 引用语义弱**：Lite Phase A 期间 §4.1 / §4.4 跨仓引用 mj-system 上游 STANDARD；wikilink 在 mj-agent 仓内无法解析；只能以注释路径形式引用，reviewer 需手动跳到 mj-system 仓查看
- **维护双源**：mj-system 上游 HITL_Prompt v1.0+ 后续演进（如增加 stage、修改 §3.1 项）时，mj-agent 版本需要 sync；目前没有 sync skill（待 Phase D `mj-agent-doc-sync` 扩展）
- **Phase B+ Intake/Repo_Scan 派生的工作量未计入 Phase A 估算**：Lite Phase A 节省的工作转嫁到 Phase B+；如果差异预判错误（mj-system 上游版与 mj-agent 完全不适配），Phase B 工作量会膨胀

### 中性

- **§5 矩阵 32 skills 分 4 phase 落地**：P0 13 个（PR-B+，Phase B 完成）+ P1 14 个（PR-B/C，Phase C 完成）+ P2 5 个（PR-D，Phase D Phase 2）；进度条按 phase 推进，不影响 v1.0 STANDARD 自身 promote
- **HITL_Prompt v1.0 自身 state: draft → active 触发条件**：§5 §5.1-§5.5 矩阵中 P0 13 个 skill 全部落地后（PR-B3 末），HITL_Prompt v1.0 转 active，与 v2.1 trio promote 同 PR
- **后续 ADR 编号占用**：本 ADR-015 + ADR-016（in-tree skills ecosystem）连续；ADR-017+ 待 Phase B/C 期间产生

### 风险

- **HITL_Prompt 触发 LLM 频率与 token 成本**：HITL_Prompt 在 Claude Code 内不会被自动加载（不像 SKILL.md 有 description 触发），开发者要主动引用；Phase B 起 mj-agent-flow-* skills 引用 HITL_Prompt 各 stage 内容时，会引入额外 token 消耗（缓解：每个 stage prompt 在 SKILL.md 内已 inline 关键 rules，不需复读 HITL_Prompt 全文）
- **§4 文字与 §5 矩阵漂移**：§4 各 stage 列出的 Preferred Skill 必须与 §5 矩阵一致；mj-system 经验是每次加 skill 都需要 §4 / §5 双更（mj-system 2026-05-04 issue #260 经验）；mj-agent 落地相同问题，需 Phase B 起 PR description 强制 cross-check
- **Lite Phase A 选择被反悔风险**：若 Phase B PR-B2 落地 mj-agent-flow-intake / mj-agent-flow-repo-scan 时发现 mj-system 上游规则差异巨大且无法忍受占位，需追加 PR-B5 派生 Intake / Repo_Scan STANDARD（缓解：Phase B 落地 flow skill 时同步评审 mj-system 上游内容，差异显著则触发追加）

---

## Alternatives considered

### 方案 I（Full Phase A）：派生 Intake + Repo_Scan + HITL_Prompt + ADR-015

把 mj-system 的 Intake STANDARD + Repo_Scan STANDARD + HITL_Prompt v1.0 三个一次性派生到 mj-agent 仓。

**未采纳**：

- 用户 2026-05-08 follow-up 明确选择 Lite Phase A
- Phase A 体量从 3 PR 上升到 5-6 PR，过长打断 Phase B 启动
- Intake / Repo_Scan 与 mj-system 差异判断需要等 Phase B mj-agent-flow-* skill 起首落地后回看才准；现在派生有"过早优化"风险

### 方案 II（Verbatim 全 STANDARD，无 mj-agent 适配）

直接 git copy mj-system v1.0 STANDARD 到 mj-agent 仓，仅替换 file path 的 mj-sys → mj-agent。

**未采纳**：

- 差异 1-5 让 verbatim 复制不可行（n8n / Flyway / multi-service / in-source canonical 不存在的概念会出现在 §4 中）
- 不能在 §3.1 显式列出 mj-agent 专属 4 项必停规则
- §5 矩阵会引用 36 个不存在的 skill

### 方案 III（重写不派生）

完全从零写 mj-agent HITL_Prompt v1.0，不引用 mj-system。

**未采纳**：

- 失去 mj-system 1 个月实践成熟度
- §1-§3 / §6 是普适内容，重写浪费工作量
- mj-agent 与 mj-system 开发者切换 mental model 增成本

### 方案 IV（不引入 HITL_Prompt，仅用 ADR-014 + skill 各自治理）

不立独立 HITL_Prompt STANDARD；HITL 触发条件分散写在每个 mj-agent-* skill 的 SKILL.md 内。

**未采纳**：

- §3 通用 HITL 规则（必停 / 自动 / 6 段问法）需要单一权威源；分散在 32 个 skill 中维护成本高且容易漂移
- §1 17-stage 顺序需要在 STANDARD 层定义，否则 skill 之间的 stage 衔接关系不清楚
- 与 mj-system 范式割裂，违背派生设计目的

### 方案 V（HITL_Prompt 不分 §4 stage prompts，只留 §1-§3 + §5 + §6）

§4 完全空白；HITL_Prompt 只作"通用规则索引"，具体 stage prompt 内容全在 SKILL.md。

**未采纳**：

- §4 的具体 stage prompt（每个 stage 的 Reference Docs / Rules / Output）是 STANDARD 的核心价值——它告诉 reviewer "这个 stage 应该输出什么 / 应该参考什么"
- 缺 §4 时 SKILL.md 没有"骨干文档"可参考，每个 SKILL.md 重复 §2 prompt 结构是冗余的
- mj-system §4 实证有效，没必要砍

---

## References

- 直接前置：
  - [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1|Meta v2.1]]（v2.1 tri-track 升级，PR-A1 落地）
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]（tri-track 决策，PR-A1 落地）
- 同期落地（PR-A2，本 PR）：
  - [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1.0|HITL_Prompt v1.0]]
- Phase B 起首：
  - [[../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]（mj-agent-* in-tree skills 命名空间 + lifecycle）
  - PR-B1...B4 落地 §5 矩阵 P0 13 个 skill
- 上游派生源（mj-system v1.0）：
  - `mj-system/develop@docs/rule/[STANDARD]_AI_Engineering_Execution_HITL_Prompt.md`（17-stage 闭环 + §4 15 stage prompts + §5 36 skills hint matrix）
  - `mj-system/develop@docs/rule/[STANDARD]_AI_Engineering_Intake.md`（Lite Phase A 占位引用，§4.1 用）
  - `mj-system/develop@docs/rule/[STANDARD]_AI_Engineering_Repo_Scan.md`（Lite Phase A 占位引用，§4.4 / §4.5 / §4.9 用）
  - `mj-system/develop@docs/rule/[GUIDE]_SPEC_Authoring_For_AI_Agents.md`（Lite Phase A 占位引用，§4.6 / §4.13 / §4.15 用）
  - `mj-system/develop@.claude/skills/mj-sys-flow-*/`（9 flow 编排器范式，PR-B2/B3 派生时直接参考）
  - `mj-system/develop@.claude/skills/mj-sys-git-*/`（9 git 编排器范式，PR-B1 派生时直接参考）
  - `mj-system/develop@.claude/skills/mj-sys-doc-*/`（7 doc 编排器范式，PR-B4 派生时直接参考）
- 关联 ADR：
  - [[../adr/[ADR]_006_Fail_Safe_Reads|ADR-006]]（数据边界 4 层 guardrail；§3.1 必停规则参照）
  - [[../adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]]（biz 域 only；§4.4 引用）
  - [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]（archive 工作流；本 ADR 自身的 promote 节奏与 ADR-011 §5.6.2 一致）
  - [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（in-tree vs marketplace SKILL schema 边界；§5 矩阵的 in-tree 方向决策依据）
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]（v2.1 tri-track 升级；本 ADR 是 tri-track 第三轨的具体内容）
- 用户互动证据：
  - 2026-05-08 brainstorming session：4 决策（建设侧 / skill 放置 / HITL 深度 / 框架重构）+ 2 follow-up（Lite Phase A / skeleton-first）
  - 外部 plan 文件：`C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon.md` §3 HITL_Prompt v1.0 Design + §10 Open follow-ups
- 行业精度：
  - HITL（Human-in-the-Loop）：MLOps Level 2 + AI Safety 标准做法
  - mj-system v1.0 实践成熟度：2026-05-01 落地 → 2026-05-08 已运行 ~7 天，36 skills + 17 stages 全套覆盖；mj-agent 派生时取材已验证版本
