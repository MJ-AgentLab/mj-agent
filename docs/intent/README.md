---
type: guide
domain: WORKFLOW
summary: INTENT 正本的目录入口与来源、责任、身份和接受边界
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: draft
track: shared
---

# INTENT 需求原意入口

正式 INTENT 使用本目录的 `[INTENT]_INT-YYYY-NNN_<English_Topic>.md`；规则正文见 [文档政策](../../policies/documentation.md) §2.8、状态见 [生命周期](../../sdd/lifecycle.md) §4.2，创作使用 [INTENT 模板](../_templates/TEMPLATE_INTENT.md) 和 doc-author。

先核真实来源、提出者/代表、维护责任与完整适用基线。简单任务可以真实 Issue 原意区为唯一正本；来源/责任未明只存真实类型 working 草稿，不冒充正式 INTENT。ID 创建及合并前查含 deprecated 的完整集合和历史已用 ID，失败保留 UNKNOWN；本入口不分配 ID、不复制实时进度。

原意核对、内容接受、执行授权、交付接受分记；接受指向固定提交完整文件或完整可恢复快照准确位置。Plan/Issue 完成不改变 INTENT 状态或 ID；退役原位 deprecated 保留旧决定、原因和后继。一个 INTENT 可支撑多个 Plan，关联须写承担/依赖/背景。

运行 `python scripts/check_frontmatter.py`、`python scripts/check_working_docs.py`、`python scripts/check_wikilinks.py` 验结构；PASS 不认证语义忠实、真实来源或任何接受决定。
