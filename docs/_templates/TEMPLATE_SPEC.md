---
type: spec
domain: SYS
summary: 20-60 字摘要，一句话说这份 SPEC 定义什么契约（接口 / 数据 / 工具行为 / 流程）
tags:
  - spec
aliases: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
version: v0.1
track: code
task_type: <1 / 2 / 3 / 4 / 5 / 6 / 7 / 8>  # 见 [GUIDE]_MJ_Agent_SPEC_Authoring §3 决策树；按主导类填；多类共触在 §1 Context 注明次要类
owner: 项目负责人
---

# <SPEC 标题：被定义实体的功能性短语，如"MJ-Agent QCM 时间维度过滤行为规范"或"execute_sql 工具结果 envelope 字段规范"</SPEC 标题>

> **适用范围**：本 SPEC 定义的实体边界（哪个模块 / 哪个工具 / 哪个流程）
> **目标受众**：开发者（实现方）+ 集成方（调用方）+ Reviewer
> **版本**：v0.1
> **最后更新**：YYYY-MM-DD
> **任务类型**：本 SPEC 任务类型为 #X — 按 [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §4.X 裁剪本模板（必填段 / 可选段 / 不涉及段显式标注）
> **关联文档**：相关 ADR / GUIDE / RUNBOOK / CONTRACT 的 wikilink

---

## §0 Task Type Identification

按 [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §3 决策树识别本 SPEC 的任务类型：

- **主导类**：#X <类型名>（如 #1 Python 应用代码）
- **次要类**（如多类共触）：#Y <类型名>，理由：<...>
- **触发的 §3.1 必停项**（按 GUIDE §6 表）：<list；空写 "无 §3.1 触发"；任何 §3.1 触发即升 Risk = High>

**裁剪决策**：按 GUIDE §4.X 列出本类的 [必填段] / [可选段] / [不涉及段]；下方 §1-§9 中 "不涉及" 段保留标题 + 显式 `不涉及（理由：...）`。

---

## TL;DR

- **被规范实体**：（如：`execute_sql` 工具 / qcm_catalog 镜像规则 / Studio 探针矩阵）
- **核心契约**：1-2 句话，最重要的不变量
- **是否影响 runtime LLM 行为**：是 / 否（是 → 触发 Track B Domain Expert review）
- **是否影响数据边界**：是 / 否（是 → 触发 ADR-006 / ADR-009 review）

---

## §1 Context（背景）

为什么写本 SPEC？

应包含：

- 触发本 SPEC 的需求来源（用户故事 / Issue / 上游决策 ADR）
- 当前 mj-agent 在该领域的现状（如：当前 `execute_sql` 已实现但缺 envelope 字段定义）
- 为什么需要正式 SPEC 而非仅 ADR / GUIDE（SPEC 用于"细节级契约"，ADR 用于"决策级取舍"，GUIDE 用于"步骤级操作"）

---

## §2 Scope（范围）

### §2.1 In-scope

- 本 SPEC 覆盖的具体行为 / 数据结构 / 接口字段

### §2.2 Out-of-scope

- 与本 SPEC 相邻但**不**覆盖的部分（明确划界，避免后续无谓争议）
- 如有，引用其他 SPEC / ADR / 待定 issue

---

## §3 Contract（契约）

> 这是 SPEC 的核心章节。按下列子节铺开；某些子节"不涉及"时显式写"不涉及（理由：...）"，不要保留空标题或占位符。

### §3.1 输入 schema

- 每个输入字段：name / type / 是否必填 / 取值范围 / 默认值 / 验证规则
- mj-agent 习惯用 pydantic 模型；如本 SPEC 描述工具，给出 pydantic field 等价定义

### §3.2 输出 schema

- 每个输出字段：name / type / 含义 / 单位（如适用）/ 边界值
- 如 envelope 模式：列全部 envelope 字段（如 mj-agent `execute_sql` 的 `executed_sql / columns / rows / row_count / truncated / statement_timeout_hit / business_summary / precheck_warnings`）

### §3.3 行为不变量

- 对所有合法输入，输出必须满足的**不变量**（如：返回的 row_count ≤ row_cap；truncated=true 当且仅当原始结果超过 row_cap）
- 如果输入有副作用，列出副作用的边界（如：状态修改限于 X；不影响 Y）

### §3.4 幂等性 / 重试语义

- 是否幂等？给出可重试的判定规则
- 重试时是否产生副作用？如何识别"已成功一次"？

---

## §4 Configuration（配置）

可调整的配置项 / 环境变量 / pyproject.toml 字段：

| 配置项 | 类型 | 默认值 | 取值范围 | 何时调整 |
|---|---|---|---|---|
| `EXAMPLE_VAR` | int | 60 | 1-300 | （如：DB 慢查询时调高） |

如**不涉及配置**，写"§4 不涉及（理由：本 SPEC 仅定义内部行为不变量，无外部可调参数）"。

---

## §5 Error handling（错误处理）

### §5.1 错误分类

| 错误类型 | 触发条件 | 用户可见信息 | 是否可重试 |
|---|---|---|---|
| `ValidationError` | （如：输入字段越界） | 友好中文提示 + 字段名 | 否（需用户修改输入） |
| `TimeoutError` | （如：SQL > statement_timeout） | 中文提示"查询超时（60s）" | 是（用户修改后重试） |
| `InternalError` | （如：DB 连接断开） | 通用错误 + traceID | 是（自动重试 N 次） |

### §5.2 异常 → envelope 映射

如本 SPEC 描述 envelope 模式工具，列出 envelope 字段在异常时的取值（如 `statement_timeout_hit: true` 当且仅当超时；`rows: []` 当且仅当无数据）。

---

## §6 Rollback / Compatibility（回滚 / 兼容性）

### §6.1 升级兼容性

- 本 SPEC v0.1 → v0.2 升级时哪些字段是 breaking、哪些是兼容
- 如何升级：reader 升级前 / writer 升级前？

### §6.2 数据回滚

- 如本 SPEC 涉及持久化数据，回滚操作步骤
- 如不涉及，写"§6.2 不涉及"

---

## §7 Verification（验证）

### §7.1 单元测试覆盖

- `tests/unit/...` 覆盖的具体行为（每个 §3 不变量 → 至少 1 个 unit test）

### §7.2 集成 / smoke 测试覆盖

- `tests/integration/...` 或 `tests/smoke/...` 覆盖的端到端验证

### §7.3 EVAL 覆盖（agent-side SPEC 时）

- 如本 SPEC 影响 in-source SKILL/PROMPT 行为，列出对应 `[EVAL]` 文档（Phase 2+）
- 如不影响 LLM 行为，写"§7.3 不涉及（pure code SPEC）"

---

## §8 Observability（可观测性）

### §8.1 日志

- 关键路径需 log 的内容（input hash / output 摘要 / 错误码 / 耗时）
- 日志级别选择（DEBUG / INFO / WARNING / ERROR）

### §8.2 指标

- 如有，列出推送到 LangSmith / Prometheus / Grafana 的指标名 + 含义
- 如不涉及，写"§8.2 不涉及"

### §8.3 追踪

- 是否触发 LangSmith trace（如本 SPEC 描述 LLM 工具）
- trace 中应包含的 metadata 字段

---

## §9 Open questions（开放问题）

> 起草时发现但**不影响 SPEC v0.1 promote** 的开放问题。Phase 2+ 演进 SPEC 时回头处理。

- 问题 1：（如：是否需要支持 multi-row update？）
- 问题 2：...

---

## 关联文档

- [[wikilink-related-1|描述]]
- [[wikilink-related-2|描述]]

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| YYYY-MM-DD | v0.1 | 初稿 |
