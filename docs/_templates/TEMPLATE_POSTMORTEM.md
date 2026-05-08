---
type: postmortem
domain: SYS
summary: 20-60 字摘要，一句话说这次事件 / 异常 / 失败的范围与影响
tags:
  - postmortem
aliases: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v1.0
track: code
derives_from: ""
owner: 项目负责人
severity: P0 / P1 / P2
incident_date: YYYY-MM-DD
resolved_at: YYYY-MM-DD HH:MM
---

# <服务/模块缩写> <事故简述>

> **适用范围**：mj-agent 中 <agent / llm / sql / db / config / biz_catalog / infra> 模块事故复盘
> **目标受众**：开发 + 运维 + 项目负责人
> **严重程度**：<P0/P1/P2>（<影响简述>）
> **发生日期**：YYYY-MM-DD
> **修复状态**：resolved-and-verified / resolving / pending-fix
> **派生自**：（如非派生则写"mj-agent 原生"；mj-system 上游有对位事件时引用）

---

## TL;DR

- **事件性质**：<production incident / dev mode incident / data boundary breach / infra failure>
- **持续时长**：<HH:MM 到 HH:MM，共 N 分钟>
- **数据影响**：<无 / 描述损失范围>
- **mj-agent 数据边界（ADR-006/009）违反？**：<是 / 否>（**是**则升级为 P0 + 立即停服）

---

## 目录

1. [§1 事件摘要](#1-事件摘要)
2. [§2 影响范围](#2-影响范围)
3. [§3 事件时间线](#3-事件时间线)
4. [§4 根因分析](#4-根因分析)
5. [§5 行动项](#5-行动项)
6. [§6 检测与响应评估](#6-检测与响应评估)
7. [§7 经验教训](#7-经验教训)
8. [§8 mj-agent 数据边界专属审计](#8-mj-agent-数据边界专属审计)（含数据边界事件时必填）

---

## §1 事件摘要

<≤ 3 句话，概述发生了什么、影响是什么、如何解决的>

---

## §2 影响范围

| 维度 | 详情 |
|---|---|
| 受影响 mj-agent 模块 | agent / llm / prompt / skill / sql / db / config / biz_catalog / infra |
| 受影响用户数 | <N 个分析师 / 全部 / 仅 dev profile> |
| 持续时间 | 从 HH:MM 到 HH:MM，共 N 分钟 |
| 数据损失 | <无 / 描述损失范围> |
| 受影响功能 | <list；如 find_biz_context / execute_sql / Studio probe H1/H2/H3/R1/R2> |
| **mj-agent 数据边界违反** | <无 / 触 ADR-006 L1-L4 哪一层 / 触 ADR-009 biz 域 only / biz_dwd allowlist 越界> |
| 上游 mj-system biz pg 影响 | <无 / 描述（如 mj-agent 误发 write 请求触发 mj-system DBA 告警）> |

---

## §3 事件时间线

（精确到分钟，≤ 20 条）

| 时间 | 事件 |
|---|---|
| HH:MM | <事件描述> |
| HH:MM | <发现告警 / Studio probe 失败 / smoke test 失败> |
| HH:MM | <开始响应> |
| HH:MM | <根因确认> |
| HH:MM | <修复完成并验证> |

---

## §4 根因分析

**技术根因**：<一句话概括根因>

### 5-Whys 分析

1. **为什么**发生了 <现象>？→ 因为 <原因 1>
2. **为什么** <原因 1>？→ 因为 <原因 2>
3. **为什么** <原因 2>？→ 因为 <原因 3>
4. **为什么** <原因 3>？→ 因为 <原因 4>（根因）

**根因**：<根本原因描述>

### mj-agent 专属根因维度（含一项即标）

- ☐ **A 风味事件**（pure code）：tools / memory / integrations / config / agent.py 错
- ☐ **B 风味事件**（in-source canonical）：SKILL.md / system.md body 错；`/mj-agent-runtime-*`（PR-C2 落地 skill）propose-diff 流程是否有效
- ☐ **C 风味事件**（infra）：docker compose / mj-agent-postgres / mj-agent-redis / langgraph.json
- ☐ **数据边界事件**（ADR-006/009）：必填 §8

---

## §5 行动项

（每项含描述、负责人、优先级、截止日期、状态，≤ 10 条）

| 行动项 | 负责人 | 优先级 | 截止日期 | 状态 |
|---|---|---|---|---|
| <行动描述> | <人员/角色> | P0 / P1 / P2 | YYYY-MM-DD | open / in_progress / done |

---

## §6 检测与响应评估

| 评估维度 | 表现 | 改进方向 |
|---|---|---|
| 检测速度 | <多久发现问题> | <改进措施> |
| 响应速度 | <多久开始处理> | <改进措施> |
| 修复速度 | <多久恢复服务> | <改进措施> |
| Studio probe 是否捕获 | 是 / 否；如否，何时该被捕获 | <改进 H1/H2/H3/R1/R2 矩阵> |

---

## §7 经验教训

（≤ 5 条，聚焦系统和流程，遵循 Blameless 原则）

1. <教训 1>
2. <教训 2>
3. <教训 3>

### 与 HITL_Prompt §3.1 必停规则的关系

- 本事件是否触 §3.1 必停 13 项之一？<是 / 否；如是，哪几项>
- 触发但未 HITL 暂停的原因？<开发者跳过 / skill 漏触发 / 其他>
- 是否需要修订 §3.1（更严的触发条件）？<是 / 否；具体建议>

---

## §8 mj-agent 数据边界专属审计（仅当 §2 标"违反"时必填）

### §8.1 触发的边界

| 边界层 | 是否触发 | 详情 |
|---|---|---|
| ADR-006 L1 regex guardrail | <是 / 否> | <如是：什么 SQL 绕过> |
| ADR-006 L1b sqlglot AST precheck | <是 / 否> | <如是：什么 AST 检查失效> |
| ADR-006 L2 semantics（SKILL.md / qcm_catalog）| <是 / 否> | <如是：哪个 SKILL 提示了错误业务语义> |
| ADR-006 L3 connection（read-only / lock_timeout / idle_in_transaction_session_timeout）| <是 / 否> | <如是：什么连接配置失效> |
| ADR-006 L4 role（GRANT / statement_timeout 60s）| <是 / 否> | <如是：role 越权> |
| ADR-009 biz 域 only（biz_dws + biz_dwd allowlist）| <是 / 否> | <如是：访问 biz_ods / biz_ads / ops_*>|
| ADR-008 双隔离（mj-agent-postgres ≠ biz pg）| <是 / 否> | <如是：mj-agent 误访 biz pg / 反方向> |

### §8.2 上游 mj-system 影响

- <是否对 mj-system biz pg 造成 incident（如 lock 超时、连接耗尽）>
- <是否需要通知 mj-system DBA / 项目负责人>
- <是否需要在 mj-system 仓开 issue 反馈>

### §8.3 加固方案

- <修 4 层 guardrail 哪一层；如 L1 regex 加新 pattern / L1b precheck 新规则 / L4 GRANT 收紧>
- <加 ADR / SPEC 防止再发>

---

## 关联文档

- 相关 ADR：<list>
- 相关 SPEC：<list>
- 相关 RUNBOOK：<list；如新建 RUNBOOK 防止再发>
- 相关 ISSUE：<list>
- mj-system 上游通知 PR / Issue：<如适用>

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| YYYY-MM-DD | v1.0 | 初稿（事件发生后 24-72h 内）|
| YYYY-MM-DD | v1.1 | 行动项 update / blameless review 后修订 |

---

> **不可变声明**：本文档正式发布（state: active）后正文不可修改。
> 如需追加信息，在文末「追加记录」区域添加并标注日期。

## 追加记录

<事后补充信息：行动项进度更新 / 后续 incident reuse 等；按时间顺序追加，不修改前文>
