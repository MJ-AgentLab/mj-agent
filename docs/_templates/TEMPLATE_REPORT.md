---
type: template
domain: WORKFLOW
summary: 任务证据报告模板，明确来源、完整基线、责任、决定与交付范围
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: draft
track: shared
---

# TEMPLATE: REPORT

保存到 `plans/<topic>/[REPORT]_<purpose>.md`，按用途命名不机械补号；共享报告只有一个主归属，其他目录引用。独立报告任务可始终没有 Plan；不要仅为整体接受补 Plan。

```markdown
---
type: report
summary: <本报告交付范围与实际结论>
owner: <报告维护者>
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
track: <按实际主题>
---

# <用途与结论>

## 范围、预期与来源

<使用者/任务、权威预期、完整基线准确位置、本报告自身交付条件；关联 Plan/INTENT 的承担/依赖/背景>

## 真实环境与方法

<实际 workspace/ref/commit SHA、环境、时点、批次、工具身份、输入、命令与退出；原执行和新验证分开>

## 结论与证据

| AC/问题 | 权威预期 | 实际观察 | 可复现证据 | 结果 |
|---|---|---|---|---|
| <逐项> | <预期> | <实际> | <准确位置/命令> | <PASS/FAIL/UNKNOWN/DEFERRED/NOT_TESTED> |

## 限制、风险与恢复

<未测/失败/非核心延期的原因影响恢复条件；结构 PASS 不证明真实原意、来源、运行或接受>

## 交付状态与下一步

<报告自身条件满足可由 Agent 标 completed；自身含 Owner 接受则先满足。报告 completed 只是文档交付，不推导整个 Plan/任务接受。独立任务整体接受由 Owner 在既有 Issue/会话/任务记录表达。>
```

## 关联文档

- [文档政策](../../policies/documentation.md) §2.7/§2.8
- [生命周期](../../sdd/lifecycle.md) §2/§4.2
- [Plan 模板](TEMPLATE_PLAN.md)
