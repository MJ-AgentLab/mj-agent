---
type: sdd-workflow
artifact: archive-capability
state: draft
version: "0.2"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-12
track: shared
ai_visibility: source-of-truth
---

# Workflow: Archive Capability

> Phase M0 skeleton — Capability 归档流程（TOMBSTONE 撰写 + ai_visibility + 引用清理）.
> Phase M5 archive ceremony 时主用. 完整流程在 Phase M5 内容填充.

## Purpose

`deprecated` 或 `frozen` 态 capability 迁入 `archive/capabilities/<domain>/<capability>/<date>/`
目录；保历史且防 AI 误读为当前事实.

## Trigger

- Capability `lifecycle_state: deprecated`（per `sdd/lifecycle.md` §1）已稳定 ≥ N 个月
- 业务能力下线（不再有用户使用）
- Capability 拆分 / 合并（旧实例归档，新实例 idea → ... active）

## High-Level Steps

1. **归档授权核对** — Owner对实质退出决定，具名迁移授权复用.
2. **Reference scan** — `scripts/sdd/check_archived_references.py` 反向扫描；列出所有 active
   引用此 capability 的位置；先迁引用，再归档.
3. **TOMBSTONE.md** — `capabilities/<cap>/TOMBSTONE.md` 起草（顶部红 NOTE + supersedes 表 +
   迁移指南）.
4. **archive.yml** — `capabilities/<cap>/archive.yml` 起草（archive.schema.json 校验通过）.
5. **Move** — `git mv capabilities/<cap>/ archive/capabilities/<dom>/<cap>/<YYYY-MM-DD>/`.
6. **INDEX update** — `capabilities/INDEX.md` 移除条目（由 `generate_index.py` 自动）;
   `archive/INDEX.md` 追加条目（由 `generate_archive_index.py` 自动）.
7. **PR + 独立核验/平台审核** — review 重点：`ai_visibility` 字段合法、`retention_class` 合理、
   `superseded_by` 完整.

## 决定与授权

具名迁移/删除、对象、必要备份及损失控制独立列授权；已有同清单复用。归档数量不自动重审批，实质变化只停受影响项。保留冻结历史，living引用和索引闭合。

## TBD: Phase M5 内容填充

- TOMBSTONE.md 模板（顶部红 NOTE + 迁移引导）
- archive.yml 各字段在不同归档情境（capability vs STANDARD vs ADR vs snapshot）的取值差异
- retention_class 到期触发 purge-eligible → 物理删除流程

---

> *Phase M0 skeleton — `state: draft`. 详 Phase M5 archive ceremony 主用.*
