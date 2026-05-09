---
type: plan
summary: Phase C-3-1 — check_wikilinks.py 通用化（auto-discover NEEDLES from docs/archive/rule/）；删 transitional 硬编码；Phase C-3 子包 1/3
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] Phase C-3-1 — check_wikilinks.py 通用化

> **3-PR 序列 P0 完成后第 1 个 P1 增强**（Phase C-3 子包 1/3）
> **关联 Issue**：[#82](https://github.com/MJ-AgentLab/mj-agent/issues/82)
> **关联**：ADR-019 §References 标记 \`scripts/check_wikilinks.py\` 硬编码 NEEDLES 是 transitional；Phase C-3 通用化是计划内 follow-up

## 1. Context

ADR-019（Phase C-1b）落地时，\`scripts/check_wikilinks.py\` NEEDLES 是 6 个硬编码 tuple。每次新加 archive（如未来 v2.2 → v3.0）都需手工同步 NEEDLES + ARCHIVE_PREFIXES。本 PR 改为 auto-discover，零维护。

mj-system \`scripts/find_stale_docs.py\` (v5.2 §7.1.1) 用类似目录扫描思路；本 PR 在 mj-agent 既有 \`check_wikilinks.py\` 上应用同模式（不引入 mj-system 完整版 + warning CI；那是 Phase D 范畴）。

## 2. Scope

| 改动 | 文件 |
|---|---|
| script refactor | `scripts/check_wikilinks.py`（NEEDLES 改为 glob `docs/archive/rule/[DEPRECATED]_*.md`） |
| ADR-020 新建 | `docs/adr/[ADR]_020_Archive_Auto_Discovery.md`（state: active；落 ADR-019 §References transitional 跟进） |
| sync | `docs/INDEX.md` ADR 表 + `CLAUDE.md` Versioning rule + `CHANGELOG.md` Unreleased |
| plan | 本文件 |

预计 ~6 文件改动。

## 3. 实现思路

新 \`scripts/check_wikilinks.py\` 核心：

```python
from pathlib import Path

ARCHIVE_DIR = Path("docs/archive/rule")
ARCHIVE_FILE_GLOB = "[[]DEPRECATED[]]_*.md"  # bracket escape for glob

def discover_needles(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    archive_dir = root / ARCHIVE_DIR
    if not archive_dir.exists():
        return (), ()
    needles = tuple(sorted(p.stem for p in archive_dir.glob(ARCHIVE_FILE_GLOB)))
    archive_prefixes = tuple(f"archive/rule/{n}" for n in needles)
    return needles, archive_prefixes

# 在 main() 里调用
NEEDLES, ARCHIVE_PREFIXES = discover_needles(repo_root())
```

注：glob bracket escaping — `[DEPRECATED]_*.md` 在 pathlib glob 中需 `[[]DEPRECATED[]]_*.md`（因 `[]` 是 char class）。

## 4. ADR-020 大纲

```
## Context
- ADR-019 hardcoded NEEDLES 是 transitional；§References 标记 Phase C-3 通用化
- 6 archived 文件需手动同步 NEEDLES list
- mj-system find_stale_docs.py 类似模式

## Decision
- check_wikilinks.py 改为 auto-discover NEEDLES from docs/archive/rule/[DEPRECATED]_*.md glob
- 删除硬编码；零维护
- 不引入 find_stale_docs.py 完整版（Phase D 范畴）

## Consequences
正面：(1) 零维护；(2) 未来 archive 自动纳入；(3) ADR-019 transitional 工作项关闭
负面：(1) 依赖 [DEPRECATED]_ 前缀约定（已由 ADR-019 §Decision 强制）；
(2) 不含 path-level rename 检测（mj-system find_stale_docs.py 完整版功能；Phase D）
中性：(1) 与 ADR-019 配套；不 supersede（仅落实 follow-up）

## Alternatives considered
A. 保持硬编码（拒：transitional 债务累积）
B. 引入完整 find_stale_docs.py（拒：Phase D 范畴；scope 超出 P1）
C. 使用 frontmatter scan 派生 needles（拒：复杂度高；filename 已含必要信息）
```

## 5. 风险与缓解

| 风险 | 缓解 |
|---|---|
| glob bracket escape 错误 | 写测试用例；首次运行实测 OK 0 violations |
| 目录名变化（如未来引入 docs/archive/legacy/） | ARCHIVE_DIR 常量；改一处 |
| edge case：archive INDEX.md（如未来加） | glob 仅匹配 `[DEPRECATED]_*.md`，不匹配 INDEX.md ✓ |

## 6. 验证

- check_frontmatter（应 OK；无新 canonical doc 问题）
- check_wikilinks（应 OK 0 violations；功能等价）
- ruff / mypy / pytest

## 7. 完成标准

- [ ] script refactor + auto-discover 工作
- [ ] ADR-020 创建
- [ ] 3 sync（INDEX/CLAUDE/CHANGELOG）
- [ ] 验证 0 violations
- [ ] commit + push + PR + CI 绿 + merge
