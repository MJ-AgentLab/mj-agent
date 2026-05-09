---
type: adr
domain: SYS
summary: scripts/check_wikilinks.py 改为 auto-discover NEEDLES from docs/archive/rule/[DEPRECATED]_*.md glob；删 ADR-019 transitional 硬编码债务；零维护
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - script
  - archive
  - auto-discovery
  - mj-system-derivation
---

# ADR 020: Archive Auto-Discovery（check_wikilinks.py 通用化）

## Context

[[../adr/[ADR]_019_Archive_Naming_Convention|ADR-019]]（Phase C-1b）落地了 archive `[DEPRECATED]_` 前缀 + frontmatter 规则。同期 `scripts/check_wikilinks.py` 的 `NEEDLES` 改为 6 个硬编码 tuple（含 `[DEPRECATED]_` 前缀）。

ADR-019 §References + §Consequences 已显式标记此为 **transitional 方案**，Phase C-3 通用化是计划内 follow-up：

> ADR-019 §Consequences 负面 (2): `scripts/check_wikilinks.py` NEEDLES 仍硬编码 — Phase C-3 通用化（auto-discover from `docs/archive/`）推迟

每次新加 archive（如未来 v2.2 → v3.0）都需手工同步 NEEDLES + ARCHIVE_PREFIXES（两次同步）；易遗漏。

mj-system `scripts/find_stale_docs.py`（v5.2 §7.1.1）用类似目录扫描思路：扫 `docs/archive/` 派生 needles，零维护。本 ADR 在 mj-agent 既有 `check_wikilinks.py` 上应用同模式。

## Decision

### 主条款

`scripts/check_wikilinks.py` 改为 **auto-discover NEEDLES** from `docs/archive/rule/[DEPRECATED]_*.md` glob：

```python
ARCHIVE_DIR = Path("docs/archive/rule")
ARCHIVE_FILE_GLOB = "[[]DEPRECATED[]]_*.md"  # bracket escape for glob

def discover_needles(root):
    archive_dir = root / ARCHIVE_DIR
    if not archive_dir.exists():
        return (), ()
    needles = tuple(sorted(p.stem for p in archive_dir.glob(ARCHIVE_FILE_GLOB)))
    archive_prefixes = tuple(f"archive/rule/{n}" for n in needles)
    return needles, archive_prefixes
```

每个 archived 文件的 stem（不带 `.md` 后缀）作为 NEEDLE；对应的 ARCHIVE_PREFIX = `archive/rule/{stem}`。

### 与 ADR-019 关系

本 ADR **不 supersede** ADR-019；仅落实 ADR-019 §References + §Consequences 标记的"Phase C-3 通用化" follow-up 工作项。

ADR-019 §Decision 主条款（archive 文件名 `[DEPRECATED]_` 前缀 + frontmatter 必含 archived/replaced-by）**完全保留**有效。本 ADR 仅改 `check_wikilinks.py` 实现。

### 不引入完整 find_stale_docs.py（Phase D 范畴）

mj-system v5.2 §7.1.1 的 `find_stale_docs.py` 完整版含：path-level rename 检测 + warning-mode CI + GH workflow + 4 周观察期。本 ADR 仅借鉴 "目录扫描派生 needles" 思路；不引入完整版 — 那是 Phase D 工作。

## Consequences

### 正面

1. **零维护** — 未来新加 archive 自动纳入校验；无需改 script
2. **关闭 ADR-019 §Consequences 第 2 项 transitional 工作** — Phase C-3 计划内 follow-up 落地
3. **deterministic** — `sorted()` 保证跨平台稳定输出
4. **mj-system 双向兼容更近一步** — 同模式（dir scan）；未来引入完整 find_stale_docs.py 时基础已就绪

### 负面

1. **依赖 `[DEPRECATED]_` 前缀约定** — 已由 ADR-019 §Decision 主条款强制；非新负担
2. **不含 path-level rename 检测**（mj-system find_stale_docs.py 完整版功能） — Phase D 范畴
3. **glob bracket escape `[[]DEPRECATED[]]_`** — Python pathlib 特殊语法；代码注释已说明

### 中性

1. **与 ADR-019 配套**（不 supersede）；ADR-011/017/018/019 partial supersede 矩阵不变
2. **空 archive 目录处理**：返回 `OK: no archived files discovered`；exit 0；不破坏 CI
3. **本 ADR 自身按 ADR-017 §5.9 判定**：trigger #1-4 均 ❌；反例 #5 字段补充 ✅（脚本逻辑改进）→ 不触发 archive ceremony

## Alternatives considered

### A. 保持硬编码 NEEDLES

**拒绝原因**：transitional 债务累积；每次 archive 演进需手动同步；易遗漏；ADR-019 §References 已标记 Phase C-3 通用化为 follow-up 工作。

### B. 引入完整 find_stale_docs.py（含 warning-mode CI + path-level rename detection）

**拒绝原因**：scope 超出 Phase C-3 P1 范围；Phase D 工作；本 PR 严格限定为 \`check_wikilinks.py\` 通用化（最小可工作改动）。

### C. 使用 frontmatter scan 派生 NEEDLES（基于 archived 文件 frontmatter `state: deprecated`）

**拒绝原因**：复杂度高（需 yaml 解析）；filename 已含必要信息（`[DEPRECATED]_` 前缀 + 全名）；filename-based 更直接、更快、更易测试。

## References

- 派生源：[mj-system@scripts/find_stale_docs.py](https://github.com/MJ-AgentLab/mj-system/blob/develop/scripts/find_stale_docs.py)（仅借鉴目录扫描思路；不引入完整版）+ mj-system v5.2 §7.1.1
- 落实：[[../adr/[ADR]_019_Archive_Naming_Convention|ADR-019]] §References transitional 跟进；§Consequences 负面第 2 项关闭
- 落地：`scripts/check_wikilinks.py`（refactor）
- 关联 GitHub Issue：[#82](https://github.com/MJ-AgentLab/mj-agent/issues/82)
- 后续（Phase D）：完整 `find_stale_docs.py` warning-mode CI + 4 周观察期 + path-level rename detection
