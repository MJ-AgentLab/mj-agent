---
name: mj-agent-doc-plan
description: 适用于 mj-agent 的文档需求与Documentation Decision缺口评估。输入：diff、Issue、SPEC、已有docs、变更scope。流程：scope→类型判定→track/风味→缺口矩阵→任务列表。输出：每个受影响对象有create/update/none及理由。Use when：评估新增工具接口需要哪些文档。Do not use for：要求直接写完整开发Plan；建议flow-plan，保留文档需求子任务边界。授权：按任务范围复用，普通实现自主；安全/业务/权限/breaking/接受标准及门禁实质变化先Owner；技术拒绝不绕过。独立调用完成后结束，委派返回调用者；完整闭环已有授权时按检查点继续，不新增外部授权。
---

# mj-agent Documentation Decision

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。本技能只评估文档缺口，输出按依赖排序的 Create/Update/None 决策；完整实施计划由 flow-plan 写，单份文档由 doc-author 写。已有任务闭环授权按检查点继续，文档评估不是新增审批门。

## 1. 固定评估输入

核实际 workspace/ref/SHA、diff、明确 Issue/INTENT/SPEC 与接受范围，读取 `policies/documentation.md` 及已有入口。Issue 来自用户明确链接或真实任务记录；不解析分支任意数字。代码证明现状，原始来源/INTENT 证明目标，SPEC/契约证明应有行为。冲突分别列明，不让当前代码覆盖需求原意。

创建、迁移 working 或涉及 INTENT 时先读 [创作与引用说明](../../references/working-docs-and-intent.md)，核真实关联、已有正本和维护责任。

## 2. 按实际内容确定类型与归属

每个受影响对象都判 Create/Update/None 并给证据；优先扩展现有正本。遍历政策中的适用类型和任务实际材料，行数由影响决定，不以固定十类表漏掉 INTENT、Intake、Report、EVAL、CONTRACT 或治理入口。

| 内容 | 归属与任务边界 |
|---|---|
| 原始问题、结果、成功判断、约束 | 正式 INTENT；简单任务可为 Issue 原意区。来源/维护责任不明只存 working 草稿 |
| 任务适配与未决项 | `plans/<topic>/[INTAKE]_<topic>.md`；可先于 Plan，也可独立存在 |
| 本次实施顺序、验证与恢复 | `plans/<topic>/[PLAN]_<topic>.md`；由 flow-plan 写完整正文 |
| 真实结论、证据与限制 | working Report/Assessment；长期参考型 Assessment 按 canonical schema |
| 行为、接口、业务口径 | SPEC/CONTRACT；保持已有边界与引用 |
| 长期决策、规则或运行操作 | ADR、policy、STANDARD、GUIDE、RUNBOOK 等实际类型 |
| 证据评估、事故、长期问题 | EVAL、POSTMORTEM、local ISSUE 等实际类型 |
| 导航及发布说明 | INDEX/README/AGENTS/CHANGELOG 等实际受影响入口 |

track 按 `policies/documentation.md` 路径与主题选 code/agent/engineering-workflow/shared；working 也必填。项目根入口、kernel、capability package、原生开发技能和 runtime adapter 分别遵从其既有 schema，不强套通用 frontmatter。

## 3. 输出缺口矩阵和依赖

| 对象/实际类型 | Action | 目标路径/已有正本 | 理由与来源 | Track/schema | 依赖/必须就绪时点 |
|---|---|---|---|---|---|
| 每个实际受影响对象 | Create / Update / None | 准确路径或尚未分配 | diff/真实来源/现有覆盖或无需改动的证据 | 按实际归属 | 前置对象与验证方法 |

边界明确的普通技术分类自主确定；真实业务原意用中性选项澄清，工程/机制取舍给推荐。仅新的目标/业务/授权/接受基线等实质变化进入 Owner 决定包，已定方案不重问。未决项保持待答，预选/沉默/超时不作决定。

逐项建立依赖：原意保存 → 任务适配 → 必要 SPEC/ADR → 实施和证据 → 导航。Report 任务可以无 Plan，不为矩阵补造工件。Issue 汇总覆盖/进度/依赖，INTENT 与 INDEX 不复制实时进度。

## 返回

交回逐对象矩阵、按依赖排序的文档任务及未决/延期的影响和恢复条件。只做缺口评估，不在此写完整 Plan、保存新正文或声称业务接受。runtime prompt/skill/catalog/SQL 改动按实际语义走领域技能，保留既有 EVAL 与数据边界。

政策依据：`repo:policies/documentation.md`、`repo:sdd/workflows/execution-loop.md`、`repo:.agents/references/execution-boundaries.md`。
