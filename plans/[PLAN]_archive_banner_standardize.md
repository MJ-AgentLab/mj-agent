---
type: plan
summary: Phase C-3-2 — 5 旧 archived 文件 banner 格式统一（[!warning] block + stable path link + ADR cross-refs + cite-by-vintage）；Phase C-3 子包 2/3
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: completed
track: shared
---

# [PLAN] Phase C-3-2 — Archive banner 规范化

> Phase C-3 P1 三联包子包 2/3。
> Issue: [#84](https://github.com/MJ-AgentLab/mj-agent/issues/84)

## Scope

5 旧 archived 文件 body 顶部 banner 标准化（v2.1 archive 在 Phase C-1a 已规范，不在本 PR）：

- `[DEPRECATED]_..._Documentation_Management_Framework_v1.0`：从 `[!WARNING]`（大写）改 `[!warning]` + 链接改 stable path
- `[DEPRECATED]_..._Documentation_Management_Framework_v1.1`：从 `**DEPRECATED**` 短文本改 `[!warning]` 完整块
- `[DEPRECATED]_..._Documentation_Meta_Framework_v2.0`：prepend `[!warning]` 标识 + 链接改 stable path + 加 ADR cross-refs
- `[DEPRECATED]_..._Code_Side_Documentation_Framework_v1.0`：同上
- `[DEPRECATED]_..._Agent_Side_Documentation_Framework_v1.0`：同上

每个新 banner 含：
- `> [!warning]` callout（lowercase；GFM 标准）
- "本副本为 vX.Y 历史归档（state: deprecated；archived: 2026-05-09）"
- 链接 → **stable path**（无 `_vX.Y`）+ 当前版本号
- 归档原因 + ADR cross-refs（含 ADR-018/019）
- "cite-by-vintage 参考保留" 语义

## 验证

- check_frontmatter / check_wikilinks（应保持 OK）
- ruff / mypy / pytest

## Phase C-3 子包

- ✅ C-3-1（PR #83 merged）— check_wikilinks.py 通用化
- 🔄 **C-3-2**（本 PR）— archive banner 规范化
- ⏭ C-3-3 — working doc 4 态机
