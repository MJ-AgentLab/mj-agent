---
type: plan
summary: Phase C-1b — archive [DEPRECATED]_ 前缀 + frontmatter (archived/replaced-by) + ADR-019；3-PR 序列收尾
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] Phase C-1b — Archive 命名规范化（C.1.2 + C.2.1）

> **3-PR 序列收尾（第 3 步）**：~~Phase C-2~~（PR #77）→ ~~Phase C-1a~~（PR #79）→ **Phase C-1b（本 PR）**
> **关联 Issue**：[#80](https://github.com/MJ-AgentLab/mj-agent/issues/80)
> **关联私有计划**：`C:\Users\Admin\.claude\plans\d-workspace-10-software-project-projects-glistening-shannon.md` §C.1.2 + §C.2.1 + §D.3
> **派生源**：`mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md` §10.2 lines 642-660
> **Repo Scan 实测**：37 cascading FROZEN refs（非 archive scope）/ 16 files

## 1. Context

借鉴 mj-system v5.2 §10.2 archive 命名规则（7 步动作清单中的 step 1-3）：
- **Step 1**：archive 文件名加 `[DEPRECATED]_` 前缀
- **Step 2**：legacy 文件名必带版本/时代标记（v2.x 系列已遵守）
- **Step 3**：frontmatter 加 `state: deprecated`（v2.x 系列已遵守）+ `archived: <YYYY-MM-DD>` 时间戳 + `replaced-by: <stable-path>` 直接指向当前活跃版本

mj-agent 当前 6 个 archived 文件均无 `[DEPRECATED]_` 前缀 + 无 `archived` / `replaced-by` 字段。本 PR 一次性补全。完成 3-PR 序列；mj-agent 文档治理与 mj-system v5.2 双向兼容。

## 2. Scope

### Group 1: 6 archived 文件 rename（git mv 加 `[DEPRECATED]_` 前缀）

| 旧名 | 新名 |
|---|---|
| `[STANDARD]_..._Documentation_Management_Framework_v1.0.md` | `[DEPRECATED]_[STANDARD]_..._Documentation_Management_Framework_v1.0.md` |
| `[STANDARD]_..._Documentation_Management_Framework_v1.1.md` | `[DEPRECATED]_[STANDARD]_..._Documentation_Management_Framework_v1.1.md` |
| `[STANDARD]_..._Documentation_Meta_Framework_v2.0.md` | `[DEPRECATED]_[STANDARD]_..._Documentation_Meta_Framework_v2.0.md` |
| `[STANDARD]_..._Documentation_Meta_Framework_v2.1.md` | `[DEPRECATED]_[STANDARD]_..._Documentation_Meta_Framework_v2.1.md` |
| `[STANDARD]_..._Code_Side_Documentation_Framework_v1.0.md` | `[DEPRECATED]_[STANDARD]_..._Code_Side_Documentation_Framework_v1.0.md` |
| `[STANDARD]_..._Agent_Side_Documentation_Framework_v1.0.md` | `[DEPRECATED]_[STANDARD]_..._Agent_Side_Documentation_Framework_v1.0.md` |

### Group 2: 6 archived 文件 frontmatter 增强

每份加：

```yaml
archived: 2026-05-09           # 本 PR 引入字段；统一使用 frontmatter 落地日期
replaced-by: <relative-path>   # 直接指向当前活跃 stable path（无 _vX.Y 后缀）
```

`replaced-by` 映射：

| Archive | replaced-by |
|---|---|
| Documentation_Management_Framework_v1.0 | `../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` |
| Documentation_Management_Framework_v1.1 | 同上 |
| Documentation_Meta_Framework_v2.0 | 同上 |
| Documentation_Meta_Framework_v2.1 | 同上 |
| Code_Side_Documentation_Framework_v1.0 | `../../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md` |
| Agent_Side_Documentation_Framework_v1.0 | `../../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md` |

`replaced-by` **直接指向 stable path**（per mj-system §10.2 line 653 模式）；不指 legacy chain 中间版本，方便随框架升级一键追溯到现役版本。

### Group 3: ADR-019 新建

| 项 | 值 |
|---|---|
| 路径 | `docs/adr/[ADR]_019_Archive_Naming_Convention.md` |
| state | active |
| decision | accepted |
| track | shared |
| 关键 §Decision | (a) Archive 文件名必加 `[DEPRECATED]_` 前缀；(b) frontmatter 必含 `archived: <YYYY-MM-DD>` + `replaced-by: <stable-path>`；(c) `replaced-by` 直接指 stable path（不指 legacy chain）；(d) Add `[DEPRECATED]_` 前缀 rename 视为 rule application（与 ADR-018 §4.4.4 同模式，不触发 archive ceremony 套娃）；(e) **Partial supersede ADR-011** §5.6.2 第 2 段（file move step naming）；ADR-011 §5.6.1（已被 ADR-017 §5.9 量化）+ §5.6.3（archive 目录语义）+ §5.6.4（Living/Frozen）保留 |

### Group 4: 全仓 ~37 cascading FROZEN ref 更新

涉 16 文件：

- `docs/INDEX.md`：archive 表 6 entries 路径更新（4 处） + ADR 表加 ADR-019 row
- ADR-010 / ADR-011 / ADR-012：cross-ref archive 路径（共 5 处）
- ASSESSMENT_..._Git_Conventions_Adoption（2 处）
- docs/rule/Meta_Framework / Code_Side / Agent_Side（3 个 active STANDARDs；frontmatter `derives_from` + `supersedes` + body "派生自"块；总 21 处）
- plans/PLAN_E / PLAN_F / PLAN_C-1a（10 处；working docs 含 historical refs）
- .claude/skills/mj-agent-doc-migrate/SKILL.md（3 处）
- CLAUDE.md（1 处）

**bulk perl** 一次性替换：`archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_` → `archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_`（scope 限定 non-archive 文件；archive body 内自引保留 frozen）。

### Group 5: scripts/check_wikilinks.py NEEDLES + ARCHIVE_PREFIXES 同步

```python
NEEDLES = (
    "[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.0",
    "[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1",
    "[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0",
    "[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1",
    "[DEPRECATED]_[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0",
    "[DEPRECATED]_[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0",
)
ARCHIVE_PREFIXES = tuple(f"archive/rule/{n}" for n in NEEDLES)
```

### Group 6: 同步索引

- `docs/INDEX.md`：archive 表 entries 更新；ADR 表加 ADR-019
- `CLAUDE.md`：Versioning rule 段加 ADR-019 mention
- `CHANGELOG.md`：Unreleased 加 Phase C-1b 入条 + "3-PR 序列收尾" 标记

## 3. 文档决策

| 类型 | Action | 路径 | 触发 §5.9？ |
|---|---|---|---|
| Archived 6 rename | git mv add `[DEPRECATED]_` prefix | `docs/archive/rule/[DEPRECATED]_*.md` | ❌ rule application（ADR-019 §Decision 子条款；与 ADR-018 §4.4.4 同模式） |
| Archived 6 frontmatter | Edit add `archived` + `replaced-by` | 6 frontmatter | ❌ 字段补充（§5.9 反例 #5） |
| ADR-019 | Create | `docs/adr/[ADR]_019_*.md` | N/A（新建非演进） |
| ~37 cascading refs | Bulk perl replace | 16 files non-archive scope | N/A |
| Script | Edit | `scripts/check_wikilinks.py` | N/A |
| INDEX/CLAUDE/CHANGELOG | Edit | 3 files | N/A |

## 4. ADR-019 内容大纲（待落盘）

```
## Context
- mj-agent Phase C-1a 完成 active path stability（ADR-018）；archive 命名规则尚未引入
- mj-system v5.2 §10.2 step 1-3 提供成熟模式：[DEPRECATED]_ prefix + archived + replaced-by
- 6 archived 文件均无规范 frontmatter（archived 时间戳缺失；无 replaced-by 字段）

## Decision
(a) Archive 文件名必加 [DEPRECATED]_ 前缀
(b) frontmatter 必含 archived: <YYYY-MM-DD> + replaced-by: <stable-path>
(c) replaced-by 直接指向当前活跃 stable path
(d) Add [DEPRECATED]_ 前缀 rename = rule application；不触发 archive ceremony
(e) Partial supersede ADR-011 §5.6.2 第 2 段；§5.6.1/3/4 sustained

## Consequences
正面：(1) archive 文件名一眼可识 deprecated；(2) archived 时间戳为 retention/GC 提供数据；
(3) replaced-by 一键追溯当前版本（直指 stable path）；(4) mj-system v5.2 双向兼容

负面：(1) 与 ADR-018 形成"双 partial supersede ADR-011"；reviewer 需读 3 个 ADR 才完整；
(2) Phase C-3 通用化前 NEEDLES 仍硬编码

中性：(1) archived body 内部 wikilinks 不更新（mj-system §10.3 frozen 原则）；
(2) 自洽 dogfood：本 PR rename 不触发 archive ceremony（rule application）

## Alternatives considered
A. 不加 [DEPRECATED]_ 前缀（仅加 frontmatter）— 拒：mj-system 实测前缀辨识度高
B. archived body 内部 wikilinks 同步更新 — 拒：违反 §10.3 frozen 原则
C. 等 Phase D 与 EVAL framework 一起 — 拒：3-PR 序列收尾需求；PRs 已分隔；C-1b 独立合理

## References
- mj-system §10.2 派生
- ADR-011（partial supersede §5.6.2 第 2 段；§5.6.1/3/4 sustained）
- ADR-017（§5.9 trigger #4 与本 rename 互不触发）
- ADR-018（active path stability；与本 archive 命名互补）
```

## 5. 风险控制

| 风险 | 缓解 |
|---|---|
| 6 文件 rename 影响 git history | git mv 保留；GitHub blame 跟随 |
| ~37 cascading refs 易遗漏 | perl 一次性 bulk replace + grep 余量 + check_wikilinks 兜底（refactored NEEDLES） |
| ADR-011 三重 partial supersede（ADR-017 §5.6.1 + ADR-018 §4.2/§5.6.2 第 1 段 + ADR-019 §5.6.2 第 2 段） | ADR-019 §References 详记三 ADR 分工；ADR-011 整体 sustained，仅条款细化 |
| archive body 内部断链 | 接受 per mj-system §10.3；archive INDEX 提供 forward gateway |
| `replaced-by` 路径错误 | 单元 audit：grep `replaced-by:` 验证 6 个 entries 都指 stable path（无 `_vX.Y` 后缀） |

## 6. 验证计划

```powershell
cd D:/workspace/10-software-project/projects/mj-agent/documentation/doc-governance-phase-c-1b

uv run python scripts/check_frontmatter.py        # 含 archived + replaced-by 字段（schema 暂不强制；本 PR 仅在 deprecated 文件加）
uv run python scripts/check_wikilinks.py          # NEEDLES 含 [DEPRECATED]_ 后 0 violations
uv run ruff check
uv run mypy src/mj_agent
uv run pytest                                     # 默认选
```

### AI 自检

- 6 archived 文件 `[DEPRECATED]_` 前缀（filename）
- 6 archived 文件 frontmatter 含 `archived: 2026-05-09` + `replaced-by: <stable-path>`
- `replaced-by` 全部指 stable path（grep 验证：无 `_vX.Y` 后缀的字符串作为 replaced-by 值）
- ADR-019 §References 含 ADR-011 partial supersede + ADR-017 + ADR-018 cross-ref
- docs/INDEX.md archive 表 6 entries 路径全更新
- CLAUDE.md "Versioning rule" 段含 ADR-019 mention
- CHANGELOG.md Unreleased 加 Phase C-1b 入条
- 全仓 grep `archive/rule/[STANDARD]_..._v` 0 命中（应全部已改为 `archive/rule/[DEPRECATED]_[STANDARD]_..._v`；archive body 自引除外）

## 7. 完成标准

- [ ] 6 archived 文件 rename + frontmatter 增强
- [ ] ADR-019 创建
- [ ] ~37 cascading FROZEN refs 全部更新
- [ ] scripts/check_wikilinks.py NEEDLES + ARCHIVE_PREFIXES 同步
- [ ] CLAUDE.md / docs/INDEX.md / CHANGELOG.md sync
- [ ] 5 项本地验证全绿
- [ ] HITL Gate 5 ✅ / Gate 7 / Gate 9 / Gate 11 / Gate 13 全部经 user 确认
- [ ] PR 创建并通过 CI
- [ ] Issue #80 close via PR merge

## 8. 后续（不在本 PR；非 3-PR 序列范围）

- Phase C-3+：scripts/check_wikilinks.py 通用化（auto-discover from `docs/archive/`，不再硬编码 NEEDLES）
- Phase C-3+：working state 4 态机（completed / archived；评估 plan §C.2.3）
- Phase D+：其他 P1/P2 借鉴项（per plans/glistening-shannon §C.2 + §C.3）
