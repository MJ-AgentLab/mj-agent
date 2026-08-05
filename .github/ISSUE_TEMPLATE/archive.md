---
name: Archive
about: ★ NEW — 归档已弃用 capability / STANDARD / ADR；走 sdd/workflows/archive-capability.md
title: "[Archive] <one-line summary>"
labels: ["maintain"]
assignees: []
---

## TL;DR

<一句话：要归档什么 + 为什么>

## Archive Scope

- **Capability**：`capabilities/<dom>/<cap>/` → `archive/capabilities/<dom>/<cap>/<YYYY-MM-DD>/`
- **STANDARD**：`docs/rule/[STANDARD]_X.md` → `archive/rule/[ARCHIVED]_X/`
- **ADR**：`docs/adr/[ADR]_NNN_X.md` → `archive/decisions/superseded/`
- **Other**：`docs/<subdir>/<file>` → `archive/<corresponding>`

## Reason

<≥ 10 字符；说明 superseded by what + 业务驱动>

## superseded_by

- <active 文件 1>
- <active 文件 2>

## ai_visibility 字段值（必填）

- `hidden`（默认 — AI 不应读取）
- `reference`（AI 可查阅历史背景）

## retention_class（必填）

- `permanent`（不可物理删；重大 ADR / 历史 framework / 合规相关）
- `5-year`
- `1-year`

## Pre-Archive Reference Scan

`scripts/sdd/check_archived_references.py` 输出：

```
<paste scan result; expect all active references migrated or marked archive-safe>
```

## TOMBSTONE.md 起草

`<target archive path>/TOMBSTONE.md` 内容计划：

- §1 Superseded By: ...
- §2 What this artifact was: ...
- §3 Why archived: ...
- §4 Migration Guide: ...
- §5 Related Artifacts: ...

## Acceptance Criteria

- [ ] AC-1 <可验证陈述>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] 归档 ≥ 10 文件？（大规模目录迁移 HITL）
- [ ] 跨 capability 归档？（走 cross-capability workflow）
- [ ] 项目负责人 + capability owner 已确认？
