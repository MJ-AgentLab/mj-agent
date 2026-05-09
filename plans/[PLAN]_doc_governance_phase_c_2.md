---
type: plan
summary: Phase C-2 — 引入文档归档量化触发表（mj-system §10.1 借鉴）；3-PR 序列第 1 步
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: active
track: shared
---

# [PLAN] Phase C-2 — 文档归档量化触发表（C.1.3）

> **3-PR 序列第 1 步**：Phase C-2 → Phase C-1a → Phase C-1b
> **关联 Issue**：[#76](https://github.com/MJ-AgentLab/mj-agent/issues/76)
> **关联私有计划**：`C:\Users\Admin\.claude\plans\d-workspace-10-software-project-projects-glistening-shannon.md` §C.1.3 / §D.3
> **派生源**：`mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md` §10.1 lines 633-641

## 1. Context

当前 mj-agent ADR-011 §5.6.1 仅写"PR review HITL 判定为正式版本演进"，无量化标准。Reviewer 与作者共识依赖经验，新外部贡献者 onboarding 成本高（ADR-011 §Consequences "负面"第二条已明确承认此痛点）。

借鉴 mj-system v5.2 §10.1 4 类必触发 + 1 类反例，把判断从"个人经验"落回"显式规则"。

## 2. Scope

| 文件 | Action | 说明 |
|---|---|---|
| `docs/adr/[ADR]_017_Archive_Trigger_Quantification.md` | **Create** | 新建 ADR；记录"量化归档触发"决策 + mj-system §10.1 派生论证 + Alternatives |
| `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` | **Edit (in-place, no version bump)** | §5 末加 §5.9 段；4+1 触发表 + cross-ref ADR-017；`updated:` 刷至 2026-05-09 |
| `docs/INDEX.md` | **Edit** | ADR 区表加 ADR-017 行 |
| `CLAUDE.md` | **Edit** | "## Documentation" §（元规则段）"Versioning rule" 段末加 ADR-017 mention（A6 allowlist sync） |
| `CHANGELOG.md` | **Edit** | "Unreleased" 段加入条 |

**out-of-scope**：

- `.claude/skills/mj-agent-doc-author/SKILL.md` 与 `mj-agent-doc-validate/SKILL.md` 不改（C-1a 可顺手；保持 C-2 PR 最小）
- ADR-011 不改（保留 active；ADR-017 仅 cross-ref，不 supersede）
- 任何 src/ / tests/ / infra/ / .github/ 改动

## 3. 文档决策

| 类型 | Action | 路径 | 触发自 §10.1 触发表？ |
|---|---|---|---|
| ADR | Create | `docs/adr/[ADR]_017_*.md` | N/A（新建非演进）|
| STANDARD | Edit (in-place) | Meta v2.1 §5.9 加段 | **No** — 属于"字段补充" / 单段加新内容 ≪ 70%；§10.1 trigger #5 "小修小补、patch 升级、字段补充 → git 历史" |
| INDEX | Edit | docs/INDEX.md ADR 表加行 | N/A（生成物）|
| CLAUDE.md | Edit | A6 sync | N/A |
| CHANGELOG | Edit | 入条 | N/A |

**关键判断**：Meta v2.1 加新 §5.9 段是 in-place edit，**不**触发 archive ceremony（§10.1 trigger #2 "结构性重构"指 12 章 → 5 章这种重大结构调整；本次只增 1 段）。这本身就是 §10.1 触发表的一个 dogfood 案例。

## 4. ADR-017 内容（已落盘）

落盘路径：`docs/adr/[ADR]_017_Archive_Trigger_Quantification.md`

骨架：

- §Context — ADR-011 §5.6.1 trigger 判定模糊；mj-system v5.2 §10.1 实测 1 月有效；mj-agent 5 archived 文件已具规模
- §Decision — 4+1 判定表；双轨落地（ADR-017 决策记录 + Meta v2.1 §5.9 规则文本）；不 supersede ADR-011；与 ADR-018/019 future 无 scope 重叠
- §Consequences — 正面 5（onboarding / cite / PR 自检 / mj-system 双向兼容 / dogfood 闭环）+ 负面 3（70% 主观 / 4 类不穷尽 / ADR 治理复杂度）+ 中性 3（self-loop / ADR-011 不动 / §10.2 留 ADR-019）
- §Alternatives considered — A 改 ADR-011 amendment / B 仅 STANDARD 不起 ADR / C 等 C-1a 合并 / D 一并引入 §10.2 — 4 拒
- §References — mj-system §10.1 + ADR-011 cross-ref + Meta v2.1 §5.9 落地 + Issue #76 + 后续 ADR-018/019

## 5. Meta v2.1 §5.9 内容（已落盘）

落盘位置：`docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` §5.8 后、§6 前

```markdown
### 5.9 归档触发判定（v2.1 in-place 加；ADR-017 决议）

> **派生自** mj-system v5.2 §10.1。ADR-011 §5.6.1 仅给文字描述，本节落显式判定。

| 触发归档？ | 场景 | 说明 |
|---|---|---|
| ✅ 是 | 框架大版本升级 | Meta v2.x → v3.0 |
| ✅ 是 | STANDARD 结构性重构 | 12 章 → 5 章；归档名加 _pre_<新版本> |
| ✅ 是 | 70%+ 内容改写 | 量化阈值 |
| ✅ 是 | 拆分/合并/改名 | filename / scope 重定义 |
| ❌ 否 | 小修小补、patch、字段补充、typo/链接 | → git 历史 |

判定优先级 / 反例边界 / HITL 入口 / Cross-ref ADR-017 + ADR-011 §5.6
```

## 6. CLAUDE.md sync（已落盘）

落盘位置：`CLAUDE.md` "## Documentation" 元规则段，紧接 "Versioning rule" 段末（ADR-014 §决策点 3 之后）：

> ADR-017 (Phase C-2) 细化 ADR-011 §5.6.1 HITL trigger，落 Meta v2.1 §5.9 4 类必触发 + 1 类反例归档判定表（mj-system v5.2 §10.1 派生，不 supersede ADR-011，仅补充量化条款）。

## 7. 风险控制

| 风险 | 缓解 |
|---|---|
| Meta v2.1 §5.9 加段触发 §5.9 自身（递归）？ | 显式在 §5.9 反例段标注："单段加新内容属字段补充 → 不触发归档"；自洽闭环 |
| 70% 阈值主观 | mj-system 实践 1 个月未失效；ADR-017 §Consequences 显式承认；Phase 1 末复盘窗口可调整 |
| ADR-017 与 ADR-018（Phase C-1a 起）/ ADR-019（Phase C-1b 起）冲突 | ADR-017 仅治触发判定；ADR-018 治 filename / Meta v2.2 archive ceremony；ADR-019 治 archive 命名 + frontmatter；scope 三段不重叠 |
| .claude/skills/ 不更新 SKILL workflow 引用 | C-1a 顺手修；C-2 此 PR 故意 out-of-scope，单 PR 最小 |
| ADR 编号失配（最初 plan 写为 ADR-018，已修正为 ADR-017） | 起 PR 前 grep 全文确认 0 处 "ADR-018" 错引；Issue #76 body 已 gh edit 修正 |

## 8. 验证计划

### 本地验证（在 worktree 内执行）

```powershell
cd D:/workspace/10-software-project/projects/mj-agent/documentation/doc-governance-phase-c-2

uv run python scripts/check_frontmatter.py        # ADR-017 frontmatter schema 通过
uv run python scripts/check_wikilinks.py          # 0 violations
python -m compileall scripts/ src/                # 0 errors
uv run ruff check                                 # clean
uv run mypy src/mj_agent                          # clean
uv run pytest                                     # default selection green
```

### AI 自检

- ADR-017 §References 含 mj-system §10.1 + Meta v2.1 §5.9 + ADR-011 cross-ref
- Meta v2.1 §5.9 末段含 [[../adr/[ADR]_017_*]] cross-ref
- docs/INDEX.md ADR 表新增 ADR-017 行（按编号顺序）
- CLAUDE.md "## Documentation" 段含 ADR-017 mention
- CHANGELOG.md "Unreleased" 段含 Phase C-2 入条
- grep `ADR_017|ADR-017` 在仓内出现 ≥ 5 处（ADR-017 自身文件 + Meta §5.9 + docs/INDEX + CLAUDE + CHANGELOG）
- grep `ADR-018` 全仓出现位置仅在 §10 后续 / ADR-017 §Decision §References 等"前瞻引用"段（C-1a 未来 ADR）

## 9. 完成标准

- [ ] ADR-017 创建（state: active；decision: accepted；track: shared）
- [ ] Meta v2.1 §5.9 加段（无 version bump，updated 字段刷至 2026-05-09）
- [ ] docs/INDEX.md ADR 表收录 ADR-017
- [ ] CLAUDE.md "## Documentation" "Versioning rule" 段同步 ADR-017
- [ ] CHANGELOG.md 入条
- [ ] 6 项本地验证全绿
- [ ] PR 创建并通过 CI
- [ ] HITL Gate 5 (Stage 5) ✅ / Gate 7 (Stage 7) / Gate 9 (Stage 9) / Gate 11 (Stage 11) / Gate 13 (Stage 13) 全部经过 user 确认
- [ ] Issue #76 closed via PR merge

## 10. 后续（不在本 PR）

- **Phase C-1a**（PR-2，3-PR 序列第 2 步）：active 路径稳定化（去 _vX.Y 后缀）+ PR_TEMPLATE 漂移修 + Meta v2.2 archive ceremony + **ADR-018**（取代 ADR-011 §4.2 filename rule + §5.6.2 file move step）
- **Phase C-1b**（PR-3，3-PR 序列第 3 步）：archive `[DEPRECATED]_` 前缀 + frontmatter（`archived` / `replaced-by`）+ ~50 wikilink 级联 + **ADR-019**（细化 ADR-011 §5.6.2 archive 命名规则）
- Phase C-1a 时 SKILL.md（mj-agent-doc-author / mj-agent-doc-validate）workflow 引用本 §5.9（顺手）
