---
type: template
domain: WORKFLOW
summary: 任务目录内可独立执行的 Plan，分记原意承担范围、接受基线、授权、逐 AC 证据及 Owner 接受
owner: ranzuozhou
created: 2026-05-11
updated: 2026-10-29
state: draft
version: v0.3
track: engineering-workflow
---

# TEMPLATE: Agent-first Plan

在 `plans/<topic>/[PLAN]_<topic>.md` 复用骨架；目录和主文件的 topic 完全一致。四种 topic、真实主要关联与受控补号规则见 [文档政策](../../policies/documentation.md) §2.7。每目录最多一个主 Plan；Intake 可先保存，独立报告目录可始终无 Plan，子 Plan 各有独立目录。主 PR 优先整体集成 PR，未明确则省 P，不猜分支数字或第一/最新 PR。

新 Plan 默认 draft，有明确采纳依据后才 active；普通 Plan 在已有任务授权内自主维护，不固定等待阶段审批。小任务可复用既有 Issue/PR 等价记录。SPEC 管行为/接口/口径，ADR 管长期取舍，INTENT 或 Issue 原意区管期望，Report 管真实结论/证据/限制。

## Plan body 模板

````markdown
---
type: plan
summary: <目标、范围与交付结果>
owner: <维护负责人>
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
track: engineering-workflow
---

# [PLAN] <topic>

## 目标、使用者与范围

- 问题现状、使用者和期望价值：
- 包含、排除、非核心延期（原因/影响/恢复条件）：
- 真实主要 Issue / 主要 PR；其他关联及其贡献：
- 采纳依据与实际状态：未采纳 / 真实决定位置；不以关联对象 open 代替采纳。

## 原意来源、完整接受基线与本 Plan 承担范围

| 原意正本/准确位置 | 固定提交文件或完整可恢复快照 | 本次实际交付范围 | 依赖/背景（不承担） |
|---|---|---|---|
| <INTENT 或真实 Issue 原意区> | <可恢复完整内容位置；不只摘要/日期/hash> | <明确条款> | <明确条款> |

- 提出者/代表、维护责任、原意核对与内容接受的真实记录：
- 原意核对 / 内容接受 / 执行授权 / 交付接受分记，不推导或合并为一个状态。
- 当前完整适用基线、冲突与权威预期：来源分权威；实质未决列责任人和恢复点。
- 可观察 AC、质量、必要运行条件与严格真实环境/不可逆窗口：
- 实质变化保留旧决定/来源/原因/影响，旧接受只覆盖旧基线；纯路径调整记录映射、不自动重置接受。

## 执行授权、对象与停止条件

- 授权来源、允许动作：Plan/实现/离线验证/commit/push/PR/merge 等按实际列明。
- 精确仓库、workspace/branch/ref、对象、环境、工具身份、输入、remote：
- 权限、副作用、必须保护资源、资源/并发限制及停止条件：
- 删除/权限变更/高风险不可逆动作的独立具名条件：
- 授权失效：撤销或目标/对象/环境/权限/风险实质变化；普通内容迭代核版本、不逐内容重批。
- 前置 READY / NOT_READY、真实缺项；技术权限/凭据/CI 成功不产生授权。
- biz 仅四工具只读链，秘密不读取；新 App 材料只经已授权受控后台；宿主拒绝保留原错，BLOCKED_EXECUTION_ROUTE，不改个人配置或绕过。
- Owner 对实际成果/SHA 作决定；不同于作者/末推送者的 Owner 身份执行有效平台审核，App 无 admin/checks-write/bypass；补推重核。

## 入口顺序、任务与依赖

| 顺序/任务 | 文件入口和输入 | 依赖 | 有界产物 | AC | 验证/返回点 |
|---|---|---|---|---|---|
| <1> | <先读什么、再改什么> | <前置> | <可用结果> | <AC> | <命令/观察> |

- 文档决策：按实际受影响对象逐项 Create / Update / None、路径、理由；doc-plan 只做缺口评估。
- PR 模式、每条精确 head/base、整体交付主要 PR、平台前置和触发副作用：
- 委派：目标/AC/决定位置、文件归属/输入依赖、实际工作区/ref/比较 SHA、证据、授权/资源/停止与返回点；记录真实 effort 配置依据。

## 风险、恢复与监控

| 风险/未知 | 对 AC 的影响 | 防护/监控 | 恢复方式与验证状态 | 责任/恢复条件 |
|---|---|---|---|---|
| <项> | <影响> | <可执行控制> | <实测或未验证> | <入口> |

## 逐 AC 验证与独立验收包

| AC/权威预期 | 方法/命令 | head/base/测试版本 | 环境/时点/批次 | 实际与证据位置 | 状态/限制 |
|---|---|---|---|---|---|
| <逐项> | <可复现> | <真实 SHA> | <真实环境> | <产物/日志> | <PASS/FAIL/UNKNOWN/DEFERRED/NOT_TESTED> |

- 行为变化采用失败断言→观察 RED→实现→GREEN；适用 lint/type/offline unit/BDD/CLI/文档/native 检查。
- 外部依赖一律 SKIP_POLICY_EXTERNAL_DEPENDENCY，不因凭据存在启用；live/prod/容器按具名授权。
- 未参与实现的独立上下文模拟使用者/运维/审查者，独立建期望、读真实成品并复现；绑定 commit SHA、环境、时点、命令。同对象最多两轮，分歧汇总交 Owner；模拟不代替最终接受。
- 机器结构 PASS 不证明真实原意、决定、运行或成品接受；未测/延期逐项保留。

## 产物、检查点与下一步

- 可使用成果及观察入口：
- 实际 workspace/ref/SHA、候选集成/验证/交付状态、证据：
- 在途副作用、失败/未知/延期、下一步与停止条件：
- 重入先核现实与副作用，成功动作不重复。
- 改名记录：旧/新路径、真实主要关联变化与原因、完整性/引用/路由核验；task_id/INTENT ID/历史基线不变。

## 独立使用七题

1. 解决什么问题，范围、排除和延期是什么？
2. 权威预期和完整接受基线在哪里，来源冲突如何处理？
3. 先读/改哪些文件，入口顺序和依赖是什么？
4. 用什么工具/身份/精确对象与输入？
5. 获准做什么、保护什么、何时停止？
6. 如何验证、绑定哪个版本/环境/时点/批次，证据在哪？
7. 什么是候选完成，何时正式生效与被 Owner 接受？

逐题指向前文实际答案；关键缺项列未决、影响、责任和恢复点，不留给实施者猜。

## 候选完成、正式生效与 Owner 接受

- 候选完成：逐 AC 真实验证、可用产物、独立核验与限制齐备。
- 正式生效/集成：<任务实际必要平台、部署或发布条件；无则说明>。
- Owner 接受：<准确成果版本、完整基线、真实决定位置、范围和时点；当前可为待接受>。
- 只有主 Plan 在 AC 满足、成果可用且 Owner 明确接受准确版本后才 completed；merge/closed/报告完成不推导接受。
- 一次明确的主 Plan 接受可同时覆盖所列整体任务范围；其他 working 按自身交付条件完成，独立任务整体接受在已有记录表达，不补造 Plan。
````

## 分层 PR 的机器可读路由

仅分层模式在实际主 Plan 正文放一份路由块；前置未满足保持 `active: false`。登记供 `scripts/sdd/task_delivery.py` 与守卫观察，不认证授权。`task_id` 是稳定身份，与 `feature/task-<task_id>-integration` 一致，不从目录名推导或因补号变化；repo/children 使用真实精确标识，不用 glob。旧根 Plan 兼容读取。

```markdown
<!-- agent-first-routes
{"schema_version":1,"routes":[{"task_id":"example","repo":"MJ-AgentLab/mj-agent","active":false,"integration":"feature/task-example-integration","mainline":"develop","children":["feature/example-core","maintain/example-harness"]}]}
-->
```

## 关联文档

- [文档与原意政策](../../policies/documentation.md) §2.7/§2.8
- [接受与授权政策](../../policies/ai-agent.md) §4
- [执行闭环](../../sdd/workflows/execution-loop.md)
- [任务生命周期](../../sdd/lifecycle.md) §2
- [交付指南](../guide/[GUIDE]_Agent_First_Delivery.md)

## 更新记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10-29 | v0.3 | #608：任务目录、draft 默认、原意/完整基线承担范围、七题及逐 AC 独立验证；按类型完成 |
