---
type: template
domain: WORKFLOW
summary: 复用任务记录分记接受基线、执行授权、验证和可恢复检查点的 Plan 模板
owner: ranzuozhou
created: 2026-05-11
updated: 2026-10-12
state: draft
version: v0.2
track: engineering-workflow
---

# TEMPLATE: Agent-first Plan

> 在 `plans/[PLAN]_<topic>.md` 复用此骨架；小任务可用既有Issue/PR等价记录。普通Plan在任务授权内自主编写，不固定等待stages 5/7/9/11/13。接口契约归SPEC、长期取舍归ADR。

## Plan body 模板

```markdown
---
type: plan
summary: <目标、范围与交付结果摘要>
owner: <负责人>
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: active
track: engineering-workflow
---

# [PLAN] <任务>

## 接受基线

- 目标/使用者/预期价值：
- 交付范围/延期/排除：
- AC：逐项可观察预期、质量与必要运行条件；严格窗口：
- 基线来源与版本：
- 风险/必须保护资源/停止条件：

## 执行授权

- 授权来源、任务及允许动作：
- 对象/workspace/branch/ref、环境、权限、remote：
- 附带副作用、资源预算/并发/尝试限制：
- 删除/权限变更/高风险不可逆操作的独立具名条件：
- 失效：撤销或目标/对象/环境/权限/风险实质变化；普通内容迭代核版本但不重复内容批准。
- 启动前置状态：READY / NOT_READY，列实际缺项；技术权限、工具或CI成功不产生授权。

## 任务与依赖

- <任务：输入→有界产物→对应AC→验收/返回点>
- 文档矩阵：每影响对象create/update/none与理由。
- PR模式：单PR / 多个独立PR / 分层，真实base与平台规则/触发/副作用。
- 委派：实际工作区、比较基线/SHA、文件归属、证据、授权/资源/停止条件及effort配置依据。

## 验证与验收包

- 适用离线unit/BDD/CLI、lint/type、文档及原生资产检查；external为SKIP_POLICY_EXTERNAL_DEPENDENCY。
- 独立核验：从AC建立期望、读取真实成果并复现，覆盖适用角色视角；不固定真人或人数。
- 逐AC预期/实际/状态/证据；head/base/测试版本、产物/输入/依赖摘要、环境/时点/命令exit。
- 首期新证据走实际CI仓外artifact，历史能力逐步迁移；延期结构合规不计行为PASS。
- 成果如何观察/使用、限制延期、风险/监控/恢复、Owner待决定；未测恢复明确未验证。

## 检查点与完成

- 当前目标/AC/授权、workspace/ref/SHA、候选集成状态：
- 已验证/证据位置、在途副作用、失败/未知/延期：
- 下一步与停止条件；重入先核现实，成功动作不重复。
- 集成、验证、交付、待Owner接受、已接受分别记录。AC满足、成果可用且Owner明确接受版本后才completed。
```

## 分层 PR 的机器可读路由

仅分层模式在真实Plan正文放一份下列块；无相应前置保持 `active: false`。登记准确关系供 `scripts/sdd/task_delivery.py` 与守卫观察，不认证Owner授权。`task_id`与integration必须一致；repo和children使用实际精确标识，不用glob。

```markdown
<!-- agent-first-routes
{"schema_version":1,"routes":[{"task_id":"example","repo":"MJ-AgentLab/mj-agent","active":false,"integration":"feature/task-example-integration","mainline":"develop","children":["feature/example-core","maintain/example-harness"]}]}
-->
```

## 关联文档

- [接受与授权政策](../../policies/ai-agent.md) §4
- [执行闭环](../../sdd/workflows/execution-loop.md)
- [任务生命周期](../../sdd/lifecycle.md) §2
- [交付指南](../guide/[GUIDE]_Agent_First_Delivery.md)
