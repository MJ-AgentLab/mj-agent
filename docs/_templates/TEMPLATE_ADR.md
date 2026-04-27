---
type: adr
domain: AGENT
summary: 20-60 字决策摘要，描述此 ADR 解决的问题或确立的原则
owner: 项目负责人
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
decision: accepted
---

# ADR NNN: <决策标题>

> 复制本模板到 `docs/adr/[ADR]_NNN_<Decision_Title>.md`。
> NNN 为 3 位递增序号；`decision` 取值 `accepted / superseded / rejected`。
> `domain` 从本框架 §9 domain 枚举中选取一个最主要的。

## Context

描述做出此决策时的背景、约束、利益相关方。回答"为什么现在要做这个决策"。
若决策源于某个外部驱动（合规、性能指标、上游依赖变更），在此明确引用。

## Decision

清晰陈述决策本身，一到两段即可。应当可以独立阅读，不要求读者必须读完 Context。

## Consequences

- **正面**：决策带来的好处或解锁的能力
- **负面**：引入的约束、技术债、运维成本
- **中性**：不影响好坏但需要团队知道的副作用

## Alternatives considered

列出认真评估过但未采纳的方案，并说明未采纳原因。
无候选方案时写"无其他被认真评估的方案"。

## References

- 相关 ADR：`[[ADR]_XXX_*]]`
- 相关 SPEC / STANDARD
- 外部链接（论文、文档、基准测试）
