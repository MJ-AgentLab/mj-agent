---
type: assessment
domain: SYS
summary: 20-60 字摘要，一句话说这次优化或改造的范围、维度与结论
tags:
  - assessment
aliases: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v1.0
track: shared
owner: 项目负责人
dimensions:
  - architecture
  - performance
period: YYYY-MM-DD ~ YYYY-MM-DD
---

<!-- 使用说明：选择的维度章节保留，未选择的维度章节删除。至少保留 2 个维度章节。 -->

# <Service/Module> <优化主题> 评估报告

> **评估范围**：<what was optimized；mj-agent 模块 / 跨 mj-agent 与 mj-system biz pg 边界 / infra / docs / 工程编排技能体系>
> **优化周期**：YYYY-MM-DD ~ YYYY-MM-DD
> **评估维度**：<选择的维度列表>
> **版本**：v1.0

---

## TL;DR

- **优化目标**：<1-2 句话>
- **达标度**：<达标 / 部分达标 / 未达标>
- **关键指标改善**：<如 SQL 平均延迟 12s → 2s；in-source SKILL.md 五段式覆盖 0/9 → 5/9>
- **遗留问题**：<list；指向 [ISSUE]_*.md 或开 follow-up>

---

## §1 优化概述

<≤ 3 段：做了什么优化、为什么、范围>

### §1.1 优化目标

<目标列表>

### §1.2 评估维度选择

| 维度 | 是否评估 | 理由 |
|---|---|---|
| D1 架构变化 | 是/否 | <一句话> |
| D2 性能指标 | 是/否 | <一句话> |
| D3 质量与流程 | 是/否 | <一句话> |
| D4 数据一致性 | 是/否 | <一句话> |
| D5 资源利用 | 是/否 | <一句话> |
| **D6 in-source canonical 行为变化（mj-agent 专属）** | 是/否 | <一句话；含 SKILL/PROMPT body 变化 + LLM 行为对比> |
| **D7 数据边界合规（mj-agent 专属）** | 是/否 | <一句话；含 ADR-006/009 + biz_catalog drift> |
| **D8 工程编排技能体系覆盖（mj-agent 专属）** | 是/否 | <一句话；含 17-stage / A1-A14 PR 门禁覆盖度> |
| <D{N} 自定义维度> | 是/否 | <一句话> |

---

## §2 评估总结

| 维度 | 优化前概要 | 优化后概要 | 评价 |
|---|---|---|---|
| <每个选中维度> | <摘要> | <摘要> | 达标 / 部分达标 / 未达标 |

---

## §3 评估方法与限制

| 项目 | 说明 |
|---|---|
| 基线来源 | <优化前数据、报告、测试记录或提交范围> |
| 测量方法 | <如何采集、计算或对比指标> |
| 样本范围 | <数据规模、时间窗口、环境范围；mj-agent 专属：dev / test profile / 不在 prod 跑 R1/R2> |
| 评估限制 | <无法覆盖的场景、误差来源、未验证的内容> |

---

## D1 架构变化评估

### D1.1 优化前架构

<优化前架构描述，可附图或文字说明>

### D1.2 优化后架构

<优化后架构描述>

### D1.3 关键变化

| 变化项 | 优化前 | 优化后 | 影响范围 |
|---|---|---|---|
| <变化项 1> | <描述> | <描述> | <影响范围> |
| <变化项 2> | <描述> | <描述> | <影响范围> |

---

## D2 性能指标评估

### D2.1 测试环境与方法

<测试环境（profile / 硬件 / 软件 / 数据规模）+ 测试方法>

### D2.2 指标对比

| 指标 | 优化前 | 优化后 | 变化幅度 | 目标值 |
|---|---|---|---|---|
| <execute_sql 平均延迟> | <值> | <值> | <+/- %> | <目标> |
| <Studio probe H1/H2/H3 通过率> | <值> | <值> | <+/- %> | <目标> |
| <smoke test 通过率> | <值> | <值> | <+/- %> | <目标> |
| <find_biz_context 召回精度> | <值> | <值> | <+/- %> | <目标> |

### D2.3 性能分析

<指标对比的解读 + 是否达到预期>

---

## D3 质量与流程评估

### D3.1 代码质量

| 维度 | 优化前 | 优化后 | 说明 |
|---|---|---|---|
| ruff check 警告数 | <值> | <值> | <说明> |
| mypy strict 错误数 | <值> | <值> | <说明> |
| pytest 通过率（unit/eval/integration/smoke/contract）| <值> | <值> | <说明> |
| 文档 frontmatter 合规率（A2）| <值> | <值> | <说明> |
| 文档 wikilink 通过率（A4）| <值> | <值> | <说明> |
| <其他> | <值> | <值> | <说明> |

### D3.2 开发流程

<优化对开发流程的影响：HITL_Prompt 17-stage 闭环 / .claude/skills/ 编排 / dual-track A1-A11 / tri-track A12-A14 PR 门禁>

### D3.3 运维影响

<对 docker compose lifecycle / mj-agent-postgres / mj-agent-redis / Studio probe / mj-agent check 的影响>

---

## D4 数据一致性验证

### D4.1 验证方法

<如何验证：scripts/diff_biz_schema.py / Studio probe / smoke test 跑 reference_sql 对比>

### D4.2 验证结果

| 验证项 | 预期结果 | 实际结果 | 是否通过 |
|---|---|---|---|
| <验证项 1> | <预期> | <实际> | 是 / 否 |
| <验证项 2> | <预期> | <实际> | 是 / 否 |

### D4.3 差异分析

<若存在差异，分析原因及影响；若无差异，简述验证通过结论>

---

## D5 资源利用评估

| 资源 | 优化前 | 优化后 | 变化幅度 | 说明 |
|---|---|---|---|---|
| LLM token 消耗（per query 平均）| <值> | <值> | <+/- %> | <说明；Ark API key 限流压力> |
| mj-agent-postgres 容器内存 | <值> | <值> | <+/- %> | <说明> |
| mj-agent-postgres volume 占用 | <值> | <值> | <+/- %> | <说明> |
| mj-agent process 内存 | <值> | <值> | <+/- %> | <说明> |

---

## D6 in-source canonical 行为变化（mj-agent 专属，B 风味专属维度）

> 仅当本次 optimization 触及 src/mj_agent/{skills,prompts}/ body 改动时填本节。

### D6.1 改动范围

| 文件 | version 改动 | 改动性质 |
|---|---|---|
| src/mj_agent/skills/<name>/SKILL.md | v0.1 → v0.2 | 五段式补齐 / Common patterns 加例 / Anti-patterns 强化 |
| src/mj_agent/prompts/system.md | v1.7 → v1.8 | hard rule 收紧 / soft rule 加 |

### D6.2 LLM 行为对比（dev profile，per /mj-agent-infra-studio-probe）

| Studio probe ID | 优化前 trajectory | 优化后 trajectory | 评价 |
|---|---|---|---|
| H1 biz_dws 表查询 | <trajectory + tool calls> | <trajectory + tool calls> | <优化 / 持平 / 退步> |
| H2 7 天趋势 | <trajectory> | <trajectory> | <评价> |
| H3 Top 10 机构月度 | <trajectory> | <trajectory> | <评价> |
| **R1 biz_ods 拒绝**（red line） | <trajectory> | <trajectory> | **必须保持 ✅；如退步 = 数据边界事故** |
| **R2 导出全部数据**（red line） | <trajectory> | <trajectory> | **必须保持 ✅** |

### D6.3 EVAL 引用（A8/A11 transitional waiver decay 进度）

- 改动前 eval_references：<list 或 TODO>
- 改动后 eval_references：<list 或 TODO；Phase D PR-D2 后强制非空>
- EVAL backlog tickets 开单（per HITL_Prompt §4.15 Rule 11）：<list>

---

## D7 数据边界合规（mj-agent 专属）

> 任何 SQL guardrail / biz_catalog / 数据访问相关 optimization 必填本节。

### D7.1 ADR-006 4 层 guardrail 加固

| 层 | 优化前 | 优化后 | 说明 |
|---|---|---|---|
| L1 regex（单语句 / SELECT-only / schema + biz_dwd allowlist）| <规则集> | <规则集> | <加 / 删 / 调 何条> |
| L1b sqlglot AST precheck（no_select_star / require_time_range / require_limit advisory）| <规则集> | <规则集> | <说明> |
| L2 semantics（SKILL.md + qcm_catalog.yaml）| <现状> | <现状> | <说明> |
| L3 connection（read-only / lock_timeout / idle_in_transaction_session_timeout）| <值> | <值> | <说明> |
| L4 role（GRANT / statement_timeout 60s）| <配置> | <配置> | <说明（mj-system 侧改动需上游协调）> |

### D7.2 ADR-009 biz 域边界

- biz_dws 全表可访问？<是 / 否（应是）>
- biz_dwd allowlist：<当前；如有变更说明>
- biz_ods / biz_ads / ops_* 不可访问？<验证通过 / 失败（事故级）>

### D7.3 biz_catalog 镜像与上游一致性

- 上游 mj-system [STANDARD]_Biz_DWS_Naming_Stability §2-§4 当前版本：<commit / 日期>
- 本 optimization 同步前后差异：<scripts/diff_biz_schema.py 输出>
- 同步状态：<在 sync / sync 前 / 待 sync>

---

## D8 工程编排技能体系覆盖（mj-agent 专属）

> 仅当本 optimization 涉及 .claude/skills/ 或工程流程演进时填本节。

### D8.1 17-stage 闭环覆盖度

| Stage | 优化前 Preferred Skill 状态 | 优化后状态 |
|---|---|---|
| <list 受影响 stage> | <P0/P1/P2 / active> | <active> |

### D8.2 A1-A14 PR 门禁实施

- A1-A6 通用门禁 PR 通过率：<%> → <%>
- A7-A11 agent track 门禁 PR 通过率：<%> → <%>
- A12-A14 engineering-workflow 门禁 PR 通过率（v2.1 promote 后启用）：<%> → <%>

### D8.3 §3.1 必停 4 项 mj-agent 专属触发率

- runtime-skill-content-change：<次数 / PR 数>
- prompt-version-bump：<次数>
- biz-catalog-sync：<次数>
- sql-guardrail-relax：<次数>

---

## D{N} <自定义维度> 评估

### D{N}.1 优化前状态

<优化前该维度的现状描述>

### D{N}.2 优化后状态

<优化后该维度的现状描述>

### D{N}.3 对比分析

<对比分析；是否达到预期>

---

## §4 综合评价与后续建议

### §4.1 整体评价

<≤ 5 个要点>

### §4.2 遗留问题

<链接到 [[../issues/[ISSUE]_*]]，如有>

### §4.3 后续优化建议

<≤ 5 项；含具体 PR / Plan / mj-agent-runtime-* 调用建议>

### §4.4 mj-system 上游协调（如适用）

<是否需要上游 mj-system 调整 STANDARD §2-§4 / SQL guardrail / GRANT；如有，开 issue 给 mj-system>

---

## 关联文档

- 相关 ADR：<list>
- 相关 SPEC：<list>
- 相关 RUNBOOK：<list>
- 相关 ISSUE：<list>
- 相关 POSTMORTEM：<如本评估由事故 follow-up>
- 相关 PR：<list>
- mj-system 上游协调 issue：<如适用>

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| YYYY-MM-DD | v1.0 | 初稿（period 结束后 ≤ 1 周内）|
| YYYY-MM-DD | v1.1 | 行动项 update / 后续 metric 更新 |
