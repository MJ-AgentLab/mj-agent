---
name: Documentation
about: 仅文档变更；走 sdd/workflows/ + mj-agent-doc-* skill family
title: "[Documentation] <one-line summary>"
labels: ["documentation"]
assignees: []
---

> Phase M0 skeleton template — 完整字段在 Phase M2 内容填充.

## TL;DR

<一句话：要修改 / 新增 / 归档什么文档？>

## Scope

- **新增**：新 ADR / 新 GUIDE / 新 RUNBOOK / 新 capability artifact
- **修改**：现有 STANDARD / ADR / GUIDE 更新
- **归档**：deprecated 内容迁入 `archive/`（走 `sdd/workflows/archive-capability.md`）

## Target Path

- 新路径：`<sdd/ | policies/ | decisions/ | capabilities/<dom>/<cap>/ | docs/ | archive/>`
- 如修改：列出受影响文件

## Cross-Reference Impact

- 是否需更新 `docs/INDEX.md` / `decisions/INDEX.md` / `capabilities/INDEX.md`？
- 是否需更新 `CLAUDE.md`（root / 4 subdir）？
- 是否触发 A1-A6 + A7-A10 + A12-A14 PR gate？

## Acceptance Criteria

- [ ] AC-1 <可验证陈述>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] 修改 `policies/**`？（HITL required；business policy 元规则）
- [ ] 修改 `AGENTS.md`？（AI 协作边界）
- [ ] 修改 `CLAUDE.md` > 50 行？（AI 主入口）
- [ ] 修改 ADR `state` 字段（draft → active / active → deprecated）？
- [ ] 触发 archive ceremony（≥ 10 文件迁移）？

---

> *Phase M0 skeleton — Phase M2 起按 doc 工作流实例细化字段.*
