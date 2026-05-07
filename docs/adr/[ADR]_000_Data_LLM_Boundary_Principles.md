---
type: adr
domain: DATA
summary: 最小必要出网、通道隔离、工具中介——后续所有安全相关决策的理论基础
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-24
state: active
decision: accepted
track: shared
---

# ADR-000: Data-LLM Boundary Principles

## Context

mj-agent 作为内部数据分析助手，需要把业务数据（biz 域）暴露给分析师，同时这些数据通过 LLM API 流出内网。
LLM provider（Volcengine Ark，DeepSeek V3）物理上位于公司边界之外，每一次调用都是一次数据出网事件。
biz 域数据归属公司下游客户，受保密协议约束（但不含 PII）。缺少一个**成文的边界原则**，后续的 guardrail、skills、prompts、tools、memory 都会各自解读"什么可以流出"，最终形成碎片化且不可追溯的安全态势。

本 ADR 不规定具体实现机制，只确立后续所有安全相关 ADR（006/012/013/014）的**共同理论基础**。

## Decision

确立三条原则，所有涉及 LLM 出网的组件必须明确引用至少一条：

- **P1 最小必要出网（Minimum Necessary Egress）**
  只有回答问题所必需的最小数据量才允许通过 LLM API 离开公司网络。聚合优于明细；必须看明细时，保持紧凑（例如 top-N 而非全表）。

- **P2 通道隔离（Channel Isolation）**
  LLM 收到的是数据的**引用与摘要**，不是原始 payload。渲染表格/图表时，LLM 返回侧重洞察，不做数据倾泻。明细数据在 UI 层独立通道呈现（Phase 3 `dataRef` 模式是此原则的实现）。

- **P3 工具中介操作（Tool-Mediated Operation）**
  LLM 永不直接触碰数据库。它规划查询并调用受控工具；工具读库，返回**有界**结果。工具层承担 guardrail、分页截断、脱敏。

## Consequences

**正面**
- 所有涉及数据流转的 ADR 可以在一处找到共同原则基础，方便审计追溯
- 三原则足够具体，可以作为 PR review 的检查点（"这段代码违反哪条原则？"）
- 为未来新成员提供一个简短可记忆的安全心智模型

**负面**
- 某些"看起来简单"的查询（如"给我看这条记录的所有字段"）需要先经过聚合/抽样工具，增加实现复杂度
- P2 的落实需要前端与 agent 侧有约定的 `dataRef` 协议（Phase 3 才完成）

**中性**
- 所有后续安全类 ADR 必须在 References 部分显式引用本 ADR 的受影响原则编号
- 本 ADR 不涉及客户间数据隔离（内部分析师允许跨客户分析），不涉及多租户（mj-agent 服务单一信任域）

## Alternatives considered

**合规驱动的字段级黑/白名单**：要求每个字段先登记其敏感级别再决定可否出网。拒绝——维护成本高，且当前数据无 PII、粒度不足以支撑；三原则已经覆盖目标威胁模型。

**完全禁止明细出网**：拒绝——会使部分合法用例（抽查单条异常记录）无法完成；P1 的"最小必要"允许明细，但要求压缩到最小规模。

## References

- 实现：[[ADR]_006_Fail_Safe_Reads|ADR-006]]（P3 工具中介的数据库侧强制）
- 实现（Phase 1）：ADR-012 Aggregate-first Analysis Loop（P1 落地机制）
- 实现（Phase 3）：ADR-013 Generative UI with Data Handle Pattern（P2 落地机制）
- 实现（Phase 1+2）：ADR-014 Customer Data Anonymization（P1/P2 补强）
- Tools / Skills 体系：P3 的运行时实现
