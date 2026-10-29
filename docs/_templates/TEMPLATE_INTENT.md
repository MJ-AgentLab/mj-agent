---
type: template
domain: WORKFLOW
summary: 原意正本模板，明确来源、完整基线、责任、决定与交付范围
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: draft
track: shared
---

# TEMPLATE: INTENT

在 `docs/intent/[INTENT]_INT-YYYY-NNN_<English_Topic>.md` 创建正式原意正本。先通过 doc-author 核真实来源、维护责任与完整 ID 集合（含 deprecated 和 Git 历史已用 ID）；集合不全/读取失败为 UNKNOWN，不能当空集合。每年首次登记用 001–999，共享冲突或耗尽交 Owner；修订/跨年/拆任务不换 ID，删除撤销不释放。English_Topic 以英文字母开头，后续字母数字下划线。简单任务可只用真实 Issue 原意区；来源/责任未明仅保存 working 草稿，不分配正式身份。

```markdown
---
type: intent
domain: <实际领域>
summary: <问题与期望结果>
owner: <维护责任人>
created: YYYY-MM-DD
updated: YYYY-MM-DD
state: draft
intent-id: INT-YYYY-NNN
track: <code|agent|engineering-workflow|shared>
---

# <English_Topic 对应可读标题>

## 来源、责任与决定记录

- 提出者/代表及其关系：
- 原始来源：<真实会话/Issue/访谈位置；AI 整理与原话区分>
- 维护责任：<owner 不自动等于提出者或接受人>
- 原意核对：<谁、核对范围、真实决定与准确位置；未核对明确写出>
- 内容接受：<谁、范围、真实决定及固定提交完整文件或完整可恢复快照的准确位置>
- 当前位置与完整适用基线：<准确可恢复位置，不只摘要/日期/版本/hash>
- 真实主 Issue：<URL 或未建立；不为命名补造>
- 执行授权：<独立记录位置，不从内容接受推导>
- 交付接受：<独立记录位置，不从 active/CI 推导>
- AI 整理说明：<整理内容、推断、未决；不把建议/预选/沉默/超时当决定>

## 问题现状

<提出者面对的问题、背景和可核事实；实现现状不反向改写期望>

## 期望结果

<希望谁得到什么改变；真实业务原意澄清中性列选项>

## 成功判断

<可观察的判断、必要运行条件及由谁作内容/交付接受；机器结构不证明语义>

## 范围约束

<包含/排除/资源/环境/安全/权限；工程取舍给推荐及影响>

| 关联 Plan/Issue | 明确承担范围 | 实际交付/依赖/背景 |
|---|---|---|
| <准确链接> | <条款> | <角色> |

一个 INTENT 可支撑多个 Plan，一个 Plan 可承担多个 INTENT 的明确范围。实时进度/覆盖/依赖汇总在 Issue，不在 INTENT/INDEX 复制；SPEC 管行为接口口径，Report 管证据限制。

## 未决项

| 问题/冲突 | 缺失来源或决定 | 影响 | 责任与恢复条件 |
|---|---|---|---|
| <项或无> | <UNKNOWN 保留> | <影响> | <入口> |

## 修订与退役记录

- 实质变化保留旧决定/原始来源/原因/影响；旧接受仅覆盖旧基线，新内容取得所需决定。
- 纯路径调整保留映射和旧可恢复位置，不自动重置业务接受。
- 状态仅 draft/active/deprecated；active 不代替真实决定。Plan/Issue 完成不改变状态。
- deprecated 原路径保留 ID、旧决定、原因与后继，不归档迁移、不释放 ID。
```

## 关联文档

- [文档政策](../../policies/documentation.md) §2.7/§2.8
- [生命周期](../../sdd/lifecycle.md) §2/§4.2
- [Plan 模板](TEMPLATE_PLAN.md)
