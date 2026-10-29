---
type: template
domain: WORKFLOW
summary: 需求受理模板，明确来源、完整基线、责任、决定与交付范围
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: draft
track: shared
---

# TEMPLATE: INTAKE

保存到 `plans/<topic>/[INTAKE]_<topic>.md`；可先于 Plan，也可作为独立任务仅有 Intake。原意正本先经 doc-author 判定为独立 INTENT、Issue 原意区或来源/责任待明的真实类型 working 草稿；flow-intake 适配实施范围，flow-plan 再组织计划，不新增 flow-intent。

```markdown
---
type: intake
summary: <目标与待澄清范围>
owner: <维护责任人>
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
track: <按实际主题>
---

# Intake <topic>

## 问题、使用者与原意来源

<正本准确位置、提出者/代表、维护责任；不把当前代码当权威期望>

## 期望、成功判断与范围

<目标、可观察 AC、包含/排除/延期及恢复条件；关联 INTENT 的实际承担/依赖/背景>

## 原意与决定核对

<原意核对/内容接受/执行授权/交付接受分记；固定提交文件或完整可恢复快照完整基线>

真实业务原意用中性选项；工程/机制/授权取舍给推荐与理由/影响；AI 建议、预选、沉默和超时不作决定。

## 执行授权与边界

<动作、精确对象、环境、权限、副作用、资源、停止/失效；永久安全与秘密边界>

## 依赖、风险与文档决策

<每影响对象 Create/Update/None；Plan 是否需要及理由；非核心延期不阻塞核心>

## 未决与下一步

<缺项、影响、责任、恢复点；进入 Plan / 直接小任务 / 暂存草稿的实际条件>

## 本文档交付与任务接受

<自身已确定交付条件、验证与真实状态；Agent 可按条件 completed，条件含 Owner 接受则满足它。本文档完成不表示整体接受，整体接受在既有 Issue/会话/任务记录表达。>
```

## 关联文档

- [文档政策](../../policies/documentation.md) §2.7/§2.8
- [生命周期](../../sdd/lifecycle.md) §2/§4.2
- [Plan 模板](TEMPLATE_PLAN.md)
