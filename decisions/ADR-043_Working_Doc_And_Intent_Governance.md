---
type: adr
domain: WORKFLOW
summary: 以稳定任务目录聚合 working 文档并设独立 INTENT 正本，分离文档完成、决定与整体接受
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: draft
decision: accepted
track: shared
---

# ADR-043: Working Doc and Intent Governance

## Context

Owner 已确认 Issue #608 的最终方案及四项 grilling 决定，并授权实施规则、模板、技能与校验。本 ADR 记录这项已作的机制决定；不表示未来成品已验收或主 Plan 已 completed。活动 `decisions/` 与 `archive/decisions/` 两命名空间在创建前核查，043 未占用；旧 accepted ADR 与冻结材料保留。

旧 working 文件平铺，元数据/状态和技能入口不一致，交付路由只发现根 Plan，GC 仍将完成文档推向物理归档。需求原意、实施安排和接受事实容易互相推导，无法可靠恢复接受的完整基线。

## Decision

1. 新 working 使用 `plans/<topic>/`，主 `[PLAN]_<topic>.md` 与目录一致，每目录一个主 Plan；无 Plan 的独立任务合法，Intake 可先落盘。子 Plan 各有目录、共享报告唯一归属。topic 仅真实主要 I/P 关联与小写 slug，主要 PR 优先整体集成 PR，未知省 P；首次明确/纠错/明确换主关联才受控改名，不追随子 PR，task_id 不从目录推导。
2. working 统一七字段，默认 draft、有明确采纳依据才 active。只有主 Plan completed 必须 AC 满足、成果可用且 Owner 明确接受准确版本；其他 working 按自身交付条件，由 Agent 完成，自身包含 Owner 接受时仍满足。报告完成不代表整个 Plan 或任务接受；独立任务整体接受用已有 Issue/会话/任务记录表达，不另造接受系统或补主 Plan。
3. 取消 working 物理归档、180 天 GC、候选检测和相关 CI，完成文件原位保留，废弃 draft 保持 draft；archived 仅历史兼容。其他 canonical archive 不变。
4. 独立 canonical INTENT 位于 `docs/intent/[INTENT]_INT-YYYY-NNN_<English_Topic>.md`，九字段，五正文与真实来源/责任/决定前置信息。一个 INTENT 可支撑多个 Plan，Plan 明确实际承担/依赖/背景；简单任务可只用 Issue 原意区。来源或责任不明仅 working 草稿。
5. INTENT 的首次年度 ID `001–999` 稳定且不复用，创建/合并前含 deprecated 和历史既用 ID 查重，集合失败为 UNKNOWN；共享冲突/耗尽交 Owner。状态只 draft/active/deprecated，退役原路径保留 ID/旧决定/原因/后继，不随 Plan/Issue 完成传播。
6. 原意核对、内容接受、执行授权、交付接受分记；接受绑定固定提交完整文件或完整可恢复快照准确位置，摘要/日期/版本/hash 单独不足。实质变化保留旧决定和来源原因影响，旧接受仅旧基线，纯路径调整不自动重置。真实业务原意澄清中性列选项；工程/机制/授权问题给推荐及影响，沉默/预选/超时不作决定。
7. 权威正文在既有 policies/、lifecycle 与 execution-loop；复用 doc-author→flow-intake→flow-plan，不新增技能 family 或追溯数据库。校验新旧布局、路由安全、元数据/日期/ID/状态/深相对链接；结构 PASS 不认证真实编号、语义或决定。未参与实现的独立上下文验真实成品，同对象最多两轮，Owner 最终接受另记。

## Consequences

- 正面：任务材料可定位，原意独立维护，接受可恢复，机器规则与创作入口一致。
- 成本：目录改名须修活动引用与路由，保留旧完整基线；ID 分配须核集合/历史，不以校验器代替来源核对。
- 兼容：旧根文件继续读取；历史批量迁移、删除、秘密/权限/生产及 SQL/runtime 业务边界不在本次范围；不改固定提交、冻结快照或旧 accepted ADR。
- 边界：canonical/working 类型与状态有专属例外；新 HEAD 仍核有效平台审核；Owner 对机制方案的采纳不等于成品交付接受。

## Alternatives considered

- 所有独立目录强制 Plan、所有 working completed 都要求 Owner 接受：未采纳，报告交付与整体任务接受职责不同；四项 grilling 已确定。
- 以第一条/最新 PR 自动补 P、从分支数字猜 Issue：未采纳，易改变主题身份或虚构关联。
- 将 INTENT 放在 Plan 目录并随任务归档：未采纳，一个原意可支撑多个 Plan 且生命周期独立。
- 保留 180 天 GC 或默认历史批量迁移：未采纳，完成原位保留并维护活动引用即可，旧证据不得改写。

## References

- [Issue #608](https://github.com/MJ-AgentLab/mj-agent/issues/608)：Owner 已确认方案与 AC；实际成品接受另记。
- [Documentation policy](../policies/documentation.md) §2.7/§2.8
- [AI agent policy](../policies/ai-agent.md) §4
- [Lifecycle](../sdd/lifecycle.md) §2/§4.2
- [Archive policy](../policies/archive.md) §8
- [Execution loop](../sdd/workflows/execution-loop.md) §3.4
- [ADR-042](ADR-042_Agent_First_Delivery_Governance.md)
