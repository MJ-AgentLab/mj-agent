---
type: policy
artifact: archive
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Policy: Archive

> Phase M0 skeleton — 归档判定标准 + retention 类别 + ai_visibility 规则 + 旧 STANDARD 整体
> 归档 ceremony 流程. 详细内容在 Phase M5 archive ceremony 启动前内容填充.

## §1 归档判定标准

| 状态 | 触发条件 |
|---|---|
| deprecated | 显式宣告弃用（per `sdd/lifecycle.md` §2）；ADR 决议 + HITL Gate |
| frozen | deprecated ≥ N 个月仍无引用清理；不再修改但保历史 |
| archived | 物理迁入 `archive/<type>/` 目录；`ai_visibility: hidden`（默认） |

## §2 retention_class

| 类别 | 保留期 | 适用 |
|---|---|---|
| `permanent` | 不可删 | 重大 ADR / 历史 framework / 合规相关 |
| `5-year` | 5 年后 purge-eligible | 一般 capability / runbook |
| `1-year` | 1 年后 purge-eligible | working plan / 临时 evidence |

> TBD: Phase M5 — retention 到期 → purge-eligible 检测脚本 + 物理删除流程.

## §3 ai_visibility 规则

| 值 | 含义 |
|---|---|
| `hidden`（默认） | AI 不应读取（适用 superseded STANDARD 等"不能当作当前事实"的内容） |
| `reference` | AI 可查阅历史背景（适用 deprecated ADR 等"了解决策历史"的内容） |

**必填**：每 `archive.yml` 必填 `ai_visibility` 字段（G11/G12 blocking from Phase M5）.

**G14/G15 联动**：active 文件不引用 `archive/` 路径；引用必须先看 `ai_visibility = reference`
才合法（详 `scripts/sdd/check_archived_references.py`）.

## §4 旧 STANDARD 整体归档 ceremony

> TBD: Phase M5 — 详 `mj-agent-refactored-structure.md` §7 archive/ + Phase M5 实施细节：
> - tri-track STANDARD 4 文件整体迁入 `archive/rule/`
> - 现 `docs/archive/` 内容并入 `archive/decisions/superseded/`
> - 现 `docs/archive/rule/` 内容并入 `archive/rule/`
> - active 文件批量 grep + redirect map 制作
> - `archive/INDEX.md` + per-archive-unit `archive.yml` + `TOMBSTONE.md` 起草

## §5 与 SDD Workflows 联动

`sdd/workflows/archive-capability.md` — capability 归档流程；本 policy 是元规则.

---

> *Phase M0 skeleton — Phase M5 archive ceremony 主用.*
