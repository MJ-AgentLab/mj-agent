---
type: plan
summary: Phase C-1a — active 路径稳定化（去 _vX.Y）+ Meta v2.1→v2.2 archive ceremony + ADR-018 + PR_TEMPLATE 漂移修；3-PR 序列第 2 步
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] Phase C-1a — Active 路径稳定化 + Meta v2.2 + ADR-018

> **3-PR 序列第 2 步**：Phase C-2（已合并 PR #77）→ **Phase C-1a（本 PR）** → Phase C-1b
> **关联 Issue**：[#78](https://github.com/MJ-AgentLab/mj-agent/issues/78)
> **关联私有计划**：`C:\Users\Admin\.claude\plans\d-workspace-10-software-project-projects-glistening-shannon.md` §C.1.1 / §D.3
> **派生源**：`mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md` §4.1 + changelog 2026-05-05
> **Repo Scan 实测**：511 occurrences / 82 files（post-C-2 状态）

## 1. Context

mj-agent 当前每次文档 minor bump 触发 ~500 处 reference audit。ADR-011 §Decision Q1 motivation "Filename-as-version-signal" 在 Phase A→B 实测中显著低估了 audit 成本；ADR-011 §Consequences "负面"第一条已承认此痛点。

借鉴 mj-system v5.2 §4.1 + changelog 2026-05-05 active 路径稳定原则：active canonical 文件名**默认无 `_vX.Y` 后缀**；版本仅在 frontmatter `version` 字段。Legacy 反过来必带后缀。本 PR 自我应用此规则（dogfood）。

3-PR 序列上下文：

- ✅ Phase C-2（PR #77 merged）：ADR-017 + Meta v2.1 §5.9 §10.1 触发量化判定
- 🔄 **Phase C-1a（本 PR）**：ADR-018 + active 路径稳定化 + PR_TEMPLATE 漂移修
- ⏭ Phase C-1b：ADR-019 + archive `[DEPRECATED]_` 前缀 + `archived` / `replaced-by` frontmatter

## 2. Scope

### Group 1: Meta v2.1 → v2.2 archive ceremony（substantive 演进）

按 ADR-017 §5.9 trigger #4 "改名"（filename change）触发 archive ceremony；本次同时是 substantive 演进（引入新规则）。

| Action | 路径 |
|---|---|
| Archive (move + frontmatter flip) | `docs/rule/[STANDARD]_..._Meta_Framework_v2.1.md` → `docs/archive/rule/[STANDARD]_..._Meta_Framework_v2.1.md` |
| Frontmatter on archive | `state: deprecated`；`updated: 2026-05-09`；保留 `version: v2.1` |
| 顶部 banner | "本副本为 v2.1 历史归档；当前活跃版本：[Meta_Framework](../../rule/...md)；归档原因：v2.2 引入 active path stability 规则（ADR-018）" |
| Create new active | `docs/rule/[STANDARD]_..._Meta_Framework.md`（stable path；无 suffix） |
| Frontmatter on new | `version: v2.2`；`state: active`；`updated: 2026-05-09`；`derives_from: mj-agent@archive/rule/..._v2.1`；`supersedes: [..._v2.1]` |

### Group 2: 5 STANDARDs in-place rename（rule application，**非** §10.1 #4 改名 trigger）

解读：drop `_vX.Y` 后缀的 rename **是 rule application**（active path stability 规则首次应用），**非** §10.1 #4 "改名"（scope/identity rename）。precedent: mj-system v5.2 引入 stable-path 时其他 STANDARDs 同样直接 rename（无 archive ceremony）。本规则将由 ADR-018 §Decision 显式记录。

| 改名 |
|---|
| `..._Code_Side_Documentation_Framework_v1.1.md` → `..._Code_Side_Documentation_Framework.md` |
| `..._Agent_Side_Documentation_Framework_v1.1.md` → `..._Agent_Side_Documentation_Framework.md` |
| `..._AI_Engineering_Execution_HITL_Prompt_v1.0.md` → `..._AI_Engineering_Execution_HITL_Prompt.md` |
| `..._Commit_Message_Convention_v1.0.md` → `..._Commit_Message_Convention.md` |
| `..._GitHub_Markdown_v1.0.md` → `..._GitHub_Markdown.md` |

每份 frontmatter `updated: 2026-05-09`；version 字段不动；body 不动（除可能的自引用 cleanup）。

### Group 3: ADR-018 新建

| 项 | 值 |
|---|---|
| 路径 | `docs/adr/[ADR]_018_Active_Path_Stability.md` |
| state | active |
| decision | accepted |
| track | shared |
| 关键 §Decision | (a) Active canonical 文件名**默认无 `_vX.Y` 后缀**；版本只在 frontmatter；多 active 主版本并存例外允许加后缀；(b) Legacy 必保留 `_vX.Y` 后缀；(c) **Partial supersede ADR-011** §4.2 filename rule + §5.6.2 file-move-step；ADR-011 §5.6.1（已被 ADR-017 细化）+ §5.6.3（archive 目录语义）+ §5.6.4（Living/Frozen）保留 |
| §Decision 子条款 | "drop `_vX.Y` 后缀的 rename 视为 rule application，非 §10.1 #4 改名 trigger"（避免雪崩 6 archive ceremony；mj-system v5.2 先例） |

### Group 4: PR_TEMPLATE drift fix（Phase B 漏改）

7 templates：

- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/PULL_REQUEST_TEMPLATE/release.md`
- `.github/PULL_REQUEST_TEMPLATE/maintain.md`
- `.github/PULL_REQUEST_TEMPLATE/hotfix.md`
- `.github/PULL_REQUEST_TEMPLATE/feature.md`
- `.github/PULL_REQUEST_TEMPLATE/documentation.md`
- `.github/PULL_REQUEST_TEMPLATE/bugfix.md`

每份替换：
- `Documentation_Meta_Framework_v2.0` → `Documentation_Meta_Framework`（同时把"v2.0" 文字改 "v2.2"）
- `Code_Side_Documentation_Framework_v1.0` → `Code_Side_Documentation_Framework`（v1.0 → v1.1）
- `Agent_Side_Documentation_Framework_v1.0` → `Agent_Side_Documentation_Framework`（v1.0 → v1.1）

### Group 5: scripts/check_wikilinks.py NEEDLE 扩展

当前硬编码：`NEEDLE = "Documentation_Management_Framework_v1.1"`

扩为列表（含 6 archived 模式）：

```python
NEEDLES = [
    "Documentation_Management_Framework_v1.0",
    "Documentation_Management_Framework_v1.1",
    "Documentation_Meta_Framework_v2.0",
    "Documentation_Meta_Framework_v2.1",  # new in C-1a
    "Code_Side_Documentation_Framework_v1.0",
    "Agent_Side_Documentation_Framework_v1.0",
]
ARCHIVE_PREFIXES = [
    "archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.0",
    "archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1",
    "archive/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0",
    "archive/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.1",  # new
    "archive/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0",
    "archive/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0",
]
```

scan_file 改为遍历 NEEDLES；任一 NEEDLE 命中且对应 ARCHIVE_PREFIX 不在同一行 → violation。Phase C-3 通用化（自动从 archive 目录扫 needles）推迟到独立 PR。

### Group 6: 全仓 Reference audit（~500 occurrences / 82 files）

**策略**：6 个 substring 替换；scope 限定 non-archive 文件 + non-.venv：

| Old | New | 备注 |
|---|---|---|
| `Code_Side_Documentation_Framework_v1.1` | `Code_Side_Documentation_Framework` | living refs |
| `Agent_Side_Documentation_Framework_v1.1` | `Agent_Side_Documentation_Framework` | living refs |
| `AI_Engineering_Execution_HITL_Prompt_v1.0` | `AI_Engineering_Execution_HITL_Prompt` | living refs |
| `Commit_Message_Convention_v1.0` | `Commit_Message_Convention` | living refs |
| `GitHub_Markdown_v1.0` | `GitHub_Markdown` | living refs |
| `MJ_Agent_Documentation_Meta_Framework_v2.1` | `MJ_Agent_Documentation_Meta_Framework` | living refs；exceptional：ADR-018 / archive banner / Meta v2.2 §5.x 历史叙述需保留 v2.1 字面 |

**Frozen exceptions（保留 `_v2.1` 等字面）**：

- `docs/archive/**` 全部内容（脚本不进入此目录）
- ADR-018 §References / §Alternatives / §Context 中"指向 v2.1 archive"的特定段落（人工把控）
- ADR-011 / ADR-014 / ADR-015 / ADR-017 历史叙述段（语境含义 = "v2.x 那一版"，不是"当前活跃版本"；人工抽检）
- CHANGELOG.md "Phase C-1a 入条"中描述 archive ceremony 时的 `_v2.1` 字面（保留）
- Meta v2.2 文件顶部 banner / §5.10 升级历史段中 "v2.1 archived" 的字面引用

执行：先用 sed 批量替换；然后 grep 余量 + 人工逐项审；fix exceptions。

### Group 7: 同步索引

- `docs/INDEX.md` ADR 表加 ADR-018 行；STANDARD 表 6 个 entry 改 stable path；archive 表加 Meta v2.1 entry
- `CLAUDE.md` "## Documentation" 段加 ADR-018 mention（"Versioning rule" 段更新提及 ADR-018 替代 ADR-011 §4.2 + §5.6.2）；6 个 STANDARD 路径引用全部去 suffix
- `CHANGELOG.md` Unreleased 加 Phase C-1a 入条

### Group 8: worktree-local plan（本文件）

`plans/[PLAN]_doc_governance_phase_c_1a.md`（type: plan；track: shared）

## 3. 文档决策

| 类型 | Action | 路径 | 触发 §5.9？ |
|---|---|---|---|
| ADR | Create | `[ADR]_018_*.md` | N/A（新建非演进） |
| STANDARD | **Archive ceremony** | Meta v2.1 → archive | ✅ trigger #4 改名 + substantive 演进（双重） |
| STANDARD | Rename only | 5 其他 → no suffix | ❌ 解读为 rule application（ADR-018 §Decision 显式条款） |
| Templates | Bulk replace | 7 PR templates | N/A |
| Script | Refactor | check_wikilinks.py | N/A |
| INDEX/CLAUDE/CHANGELOG | Edit | 3 files | N/A |

**关键判断**：本 PR 触发 ADR-017 §5.9 trigger #4（仅 Meta v2.1 → v2.2 archive；其他 5 解读为 rule application）。这是 ADR-017 §5.9 触发表的第二个 dogfood 案例（C-2 是反例 dogfood；C-1a 是正例 dogfood）。

## 4. ADR-018 内容大纲（待落盘）

```
## Context
- ADR-011 §Decision Q1 motivation "Filename-as-version-signal" 在 Phase A→B 实测显著低估 audit 成本（~24 estimated → ~500 actual）
- ADR-011 §Consequences "负面"第一条已承认此痛点
- mj-system v5.2 §4.1 + changelog 2026-05-05 引入 active path stability 规则；mj-agent 借鉴

## Decision
**主条款**：
- (a) Active canonical 文件名**默认无 `_vX.Y` 后缀**（version 仅在 frontmatter）
- (b) 多 active 主版本并存（如 API v1/v2 长期共存）才允许 `_vX.Y` 后缀（例外，非默认）
- (c) Legacy 反过来必带 `_vX.Y` 后缀（cite-by-vintage）

**子条款（解决 §10.1 trigger #4 解读）**：
- drop `_vX.Y` 后缀的 rename 视为 rule application（非 §10.1 #4 "改名" trigger）；
- 仅当 STANDARD 同时发生 substantive content evolution 时才触发 archive ceremony；
- 在本 PR 中：Meta v2.1 触发（rule introduction = substantive）；其他 5 仅 rename（rule application）；
- mj-system v5.2 引入 stable-path 时同样：框架文件 archive；其他 STANDARDs rename only。

**Partial supersede ADR-011**：
- §4.2 filename rule（"`version` 必填类型 filename 必带 `_vX.Y`"）→ 反转
- §5.6.2 file-move-step（"老文件移入 archive；新文件 `_v<new>.md`"）→ 修正为"老 archive 保留版本后缀；新 active 无后缀"
- §5.6.1 HITL trigger → 保留有效（已被 ADR-017 §5.9 量化）
- §5.6.3 archive 目录语义 → 保留有效
- §5.6.4 Living/Frozen 引用判定 → 保留有效

## Consequences
正面：
- 消除每次 minor bump 的 corpus-wide rename 风暴（实测 ~500 ref / 82 files）
- 与 mj-system 规则双向兼容（同源派生）
- ADR-011 §Decision Q1 motivation "Filename-as-version-signal" 反转，但 cite-by-vintage 通过 archive 保留
- PR_TEMPLATE.md 等"过时引用"自动随 active stable path 修复

负面：
- 反转 ADR-011 已 accepted 决策（需正面论证）
- "rule application vs §10.1 #4 改名"解读边界仍含主观判断
- check_wikilinks.py 临时扩 NEEDLES list；通用化推迟 Phase C-3
- 需要一次性 ~500 ref audit（最后一次 corpus rename 风暴）

中性：
- ADR-011 状态不变（仍 active，仅部分 supersede）
- 自洽 dogfood：本 PR 触发 ADR-017 §5.9 trigger #4（Meta archive ceremony 部分）
- 其他 5 STANDARDs 的 git history 通过 git mv 保留（IDE / GitHub 链接稳定）

## Alternatives considered
A. 保持 ADR-011 §4.2 filename rule（不去版本化）
   拒：实测 audit 成本远超原估计；不可持续
B. 全部 6 STANDARDs 都触发 archive ceremony（更严格 cite-by-vintage）
   拒：增加 PR 体量 +5 archive 文件；mj-system 先例不支持；rule application 解读更经济
C. 仅 active 重命名，不动 archive；老 archive 已是 `_v1.1` 格式
   拒：不一致；新 archive (Meta v2.1) 需要决定命名策略（与现有 archive 风格对齐 = 不加 [DEPRECATED]_，C-1b 再统一）
D. 一并落 [DEPRECATED]_ 前缀（合 C-1b 进 C-1a）
   拒：用户 2026-05-09 决策 5 选 A；保持 C-1a / C-1b 解耦降 PR 体量

## References
- ADR-011（partial supersede，不 deprecate）
- ADR-017（C-2，§5.9 trigger #4 触发本 PR Meta archive 部分）
- mj-system 派生：[STANDARD]_Documentation_Management_Framework.md §4.1 lines 292-308 + §4.2 lines 320-327 + changelog 2026-05-05
- 私有评估：plans/glistening-shannon §C.1.1
- 关联 GitHub Issue：#78
- 后续 ADR-019（Phase C-1b）将引入 archive [DEPRECATED]_ 前缀 + frontmatter（archived/replaced-by）
```

## 5. Meta v2.2 §4.4 内容大纲（新段，待落盘）

```markdown
### 4.4 Active canonical 路径稳定原则（v2.2 新增；ADR-018 决议）

> **派生自** mj-system v5.2 §4.1 + changelog 2026-05-05。
> 反转 ADR-011 §4.2 filename rule（部分 supersede）。

Active canonical 文件名**默认不带 `_vX.Y` 后缀**；文件名保持稳定路径——例如 Meta Framework 的稳定路径就是 `[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`，而不是带版本后缀。文档语义版本写在 frontmatter `version` 字段和正文版本说明里，不写进文件名。

**例外**：仅"多 active 主版本确需并存"（如 v1/v2 API 长期共存的 STANDARD）才允许文件名加 `_vX.Y` 区分；这是例外而非默认。

**Legacy 反向规则**：归档文件**必须**保留 `_vX.Y` 或 `_pre_vX.Y` 后缀（cite-by-vintage；详见 [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6 motivation Q1 + ADR-018 §Decision）。

**rename 解读子规则**：drop `_vX.Y` 后缀的 rename 视为 rule application（非 §5.9 触发 #4 "改名"）；仅当 STANDARD 同时发生 substantive content evolution 时才触发 archive ceremony。

**Cross-ref**：[[../adr/[ADR]_018_Active_Path_Stability|ADR-018]]（决策记录 + Alternatives）；ADR-017 §5.9（archive 触发判定，含 trigger #4 改名）。
```

## 6. CLAUDE.md sync（待落盘）

"## Documentation" 段 "Versioning rule" 段更新：

> ADR-018 (Phase C-1a) reverses ADR-011 §4.2 filename rule (partial
> supersede): active canonical filenames default to **no** `_vX.Y` suffix
> (stable path); legacy files retain version suffix. Drop-suffix rename
> treated as rule application, not §5.9 trigger #4 改名 (mj-system v5.2
> precedent).

并把 6 个 STANDARD 路径全部改为 stable path（去 suffix）。

## 7. CHANGELOG.md sync（待落盘）

```markdown
### Changed — Phase C-1a (ADR-018 + Active Path Stability + PR_TEMPLATE drift fix)

- **PR Phase-C-1a — active 路径稳定化（`docs(rule)`，issue #78）**：
  按 mj-system v5.2 §4.1 派生，引入 active canonical 路径稳定原则
  （文件名默认无 `_vX.Y` 后缀；版本仅在 frontmatter）。落地：
  - 新建 ADR-018（partial supersede ADR-011 §4.2 + §5.6.2）
  - Meta v2.1 → v2.2 archive ceremony（双重触发：rule introduction +
    filename rename）
  - 5 其他 STANDARDs in-place rename（rule application 解读，非 §5.9 #4 改名）
  - 7 PR_TEMPLATE drift 修（Phase B 漏改 + 同步 active path）
  - scripts/check_wikilinks.py NEEDLE 扩 6 模式（临时；C-3 通用化）
  - ~500 ref audit（CLAUDE.md / docs/** / .claude/skills/** /
    src/mj_agent/{skills,prompts}/__init__.py 等）
  3-PR 序列第 2 步；out-of-scope：Phase C-1b（archive [DEPRECATED]_ 前缀）。
```

## 8. 风险控制

| 风险 | 缓解 |
|---|---|
| ~500 ref audit 易遗漏 | sed 批量 + grep 余量验证 + check_wikilinks 兜底 |
| ADR-011 §Decision Q1 反转需正面论证 | ADR-018 §Context + §Alternatives + §Consequences 详细记录 |
| `_v2.1` 替换漂移到不该改的位置（Frozen exceptions） | 替换后人工 grep 余量；预期 exceptions ~10 处；按列表逐个核对 |
| 6 文件 rename 影响 IDE / GitHub 链接稳定性 | 全部用 git mv 保留 history；GitHub 自动跟随 |
| check_wikilinks.py NEEDLE 扩展可能漏模式 | NEEDLES list 与 ARCHIVE_PREFIXES list 对齐；test 验证 |
| `MJ_Agent_Documentation_Meta_Framework_v2.1` 替换需保留 frozen 字面（archive banner + ADR-011 历史叙述）| 替换前先列 exception 文件清单；脚本 skip exceptions；人工 review |
| `MJ_Agent_Documentation_Management_Framework_v1.1` 现存 NEEDLE 兼容性 | 保留 v1.1 NEEDLE；新加 v2.1 NEEDLE；list 而非 string |
| 自洽 dogfood：本 PR 触发 ADR-017 §5.9 #4 | 仅 Meta archive ceremony；其他 rename 解读为 rule application；ADR-018 显式记录 |

## 9. 验证计划

### 本地验证（在 worktree 内）

```powershell
cd D:/workspace/10-software-project/projects/mj-agent/documentation/doc-governance-phase-c-1a

uv run python scripts/check_frontmatter.py        # 60+1+1=62 canonical docs all pass（Meta v2.2 + Meta v2.1 archive + ADR-018 + 6 renamed）
uv run python scripts/check_wikilinks.py          # 0 violations（NEEDLES 扩展后兼容）
python -m compileall scripts/ src/                # 0 errors
uv run ruff check                                 # clean
uv run mypy src/mj_agent                          # clean
uv run pytest                                     # default selection green
```

### AI 自检

- 6 个 STANDARD 全部存在于 `docs/rule/<no-suffix>.md`
- Meta v2.1 存在于 `docs/archive/rule/<v2.1>.md`（state: deprecated）
- ADR-018 存在；§Decision 含子条款；§References 含 ADR-011 partial supersede
- grep `_v2\.1` 仅在 `docs/archive/**` + ADR-018/Meta v2.2 §历史叙述段 + ADR-011/014/015/017 历史叙述
- grep `_v1\.1` 仅在 `docs/archive/**`（v1.1 archive of Documentation_Management_Framework）+ 历史叙述
- grep `_v1\.0` 仅在 `docs/archive/**` + 历史叙述
- grep `_v2\.0` 仅在 `docs/archive/**` + 历史叙述
- 7 PR_TEMPLATE 全部 `Meta_Framework`（无 `_v2.0`）+ `Code_Side_Documentation_Framework`（无 `_v1.0`）+ `Agent_Side_Documentation_Framework`（无 `_v1.0`）
- check_wikilinks.py NEEDLES list 含 6 项；scan 0 violations
- docs/INDEX.md ADR 表加 ADR-018；6 STANDARD 路径 stable
- CLAUDE.md "Versioning rule" 段加 ADR-018 mention
- CHANGELOG.md Unreleased 加 Phase C-1a 入条

### 人工抽检

- CLAUDE.md（A6 sync 6 处 + ADR-018 mention）
- docs/INDEX.md（ADR 表 + STANDARD 表 + archive 表）
- ADR-018（§Decision 子条款 + Alternatives 4 拒）
- Meta v2.2 §4.4 新段（cross-ref ADR-018 + ADR-017）
- Meta v2.1 archive banner（顶部 [!warning] block）

## 10. 完成标准

- [ ] Meta v2.1 → archive；Meta v2.2 stable path（active）
- [ ] 5 其他 STANDARDs 改名（git mv 保留 history）
- [ ] ADR-018 创建（state: active；decision: accepted）
- [ ] 7 PR_TEMPLATE 漂移修
- [ ] scripts/check_wikilinks.py NEEDLES 扩展
- [ ] 全仓 ~500 ref 替换 + Frozen exceptions 保留
- [ ] CLAUDE.md / docs/INDEX.md / CHANGELOG.md sync
- [ ] 6 项本地验证全绿
- [ ] HITL Gate 5 ✅ / Gate 7 / Gate 9 / Gate 11 / Gate 13 全部经 user 确认
- [ ] PR 创建并通过 CI
- [ ] Issue #78 close via PR merge

## 11. 后续（不在本 PR）

- **Phase C-1b**（PR-3，3-PR 序列第 3 步）：archive `[DEPRECATED]_` 前缀（6 archived 文件 + 现有 5 同步）+ frontmatter（`archived` / `replaced-by`）+ ~50 wikilink 级联 + **ADR-019**（细化 ADR-011 §5.6.2 archive 命名规则）
