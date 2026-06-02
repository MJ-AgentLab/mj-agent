---
type: plan
slug: m3-fu-skill-5segment-normalize
summary: M3 follow-up plan — decide whether to normalize in-source SKILL.md to Agent_Side §2.1 canonical 5-段式 OR extend canonical to 6 sections (## Related); M2 Stage C batch 1 #1 spot-check 发现 3/3 active SKILL 均含 ## Related 第 6 段
state: active
version: 0.1
owner: ranzuozhou
created: 2026-05-21
updated: 2026-06-02
track: shared
disposition: M4-FU deferred (新增 disposition 枚举 D-3e; per Stage D Gate-1 2026-05-21; 必停 surface impact + bundle with V4-SKILLS-COMPLETE)
deferred_at: 2026-05-21
refines:
  - plans/[PLAN]_spec_anchored_refactor.md
supersedes: []
related_adrs: []
---

# [PLAN] M3-FU-SKILL-5SEGMENT-NORMALIZE — SKILL.md 5-段式 vs 6-段式 Canonical Decision

> M3 follow-up plan；M3 startup 后独立 ADR + 可能的 SKILL.md 平移 PR；不混入 M3 main work；
> refines `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown；与
> `M3-FU-CLAUDE-SKILL-ADR`（markdown-body-only convention 决议）同 family pattern.

> **⏳ STILL ACTIVE — retargeted 2026-06-02 (E-4-PR3 triage)**. Verified on develop @ `a457cd2`:
> - In-source SKILLs still carry `## Related` (6-section): 9/9 `src/mj_agent/skills/*/SKILL.md`; not normalized to 5 (option A not done) and no deciding ADR (A/B/C) exists.
> - The runtime-skill **contracts** freeze 6 sections incl. `## Related` (`capabilities/*/contracts/runtime-skill.contract.yml` `body_section_heads`), **but** the new `sdd/adapters/runtime-skill.md` L70-71 still says "body 5 段式" (Agent_Side §2.1 wording, no `## Related`) → **contract-vs-adapter-doc inconsistency carried forward into SDD governance**.
> - **Retarget**: the 5-vs-6 decision now applies to `sdd/adapters/runtime-skill.md` (active), NOT the M5-archive-bound Agent_Side §2.1.
> - **Minimal follow-up PR** (recommended option B at adapter level): amend `sdd/adapters/runtime-skill.md` L70-71 to document `## Related` as an allowed 6th section, aligning the adapter doc with the frozen contracts. Owner review required (canonical adapter-text decision). Does **not** touch `src/mj_agent/skills/*/SKILL.md` (no 必停 surface); old Agent_Side §2.1 needs no separate fix (archived in M5).

## §1 Background

M2 Stage C batch 1 #1 撰写时 spot-check 发现：

- 3/3 active in-source SKILL.md 均含 **6 body sections**：
  `## Purpose / ## When to use / ## Planning workflow / ## Common patterns / ## Anti-patterns / ## Related`
- Agent_Side §2.1 canonical 是 **5-段式**（前 5 段；NOT 含 ## Related）
- 3 SKILL.md：`safe-sql-analysis` / `biz-domain-context` / `qcm-analysis`
- M2 Stage C 4 contract（其中 2 个 runtime-skill 各 freeze 这 3 SKILL 之一或全部）已 freeze
  body_section_heads[] = 6 items；本 contract 仅 freeze current state，不取 normalize 决定

## §2 Decision options (M3+ ADR scope)

| Option | Description | SKILL.md PR scope | Agent_Side standard PR | Risk |
|---|---|---|---|---|
| **A — normalize SKILL.md to 5 sections** | 删除或合并 ## Related 段（内容并入 other 段或 frontmatter） | 3 PRs（per SKILL 独立）；触发 content_hash drift → HITL #runtime-skill-content-change → 2 runtime-skill contract `version` bump + `content_hash` 更新 | 不动 | content_hash drift 是必然；流程 well-defined（contract → SKILL → contract 闭环） |
| **B — extend canonical to 6 sections (## Related allowed)** | 更新 Agent_Side §2.1 文本；6 段 canonical；现有 SKILL 不动 | 不动 | Agent_Side v1.3 minor bump；§2.1 + frontmatter strip 契约保留 | 与 v1.2 草案断代；需 archive ceremony per Meta §4.2 |
| **C — keep advisory** | ## Related 是 non-canonical 但 acceptable convention；validator 不 enforce 5-段式严格 | 不动 | 加 §2.1 note 段说明 advisory | weakest option；spec-anchored governance 内"advisory section"模糊空间扩大 |

**推荐**：B（extend canonical）— 现有 3 SKILL `## Related` 都含有用的 cross-skill / tool / EVAL
ref 信息，删之可惜（option A）；advisory（option C）会让 future SKILL drift 难判定.

## §3 Coordination with M3-FU-CLAUDE-SKILL-ADR

- M3-FU-CLAUDE-SKILL-ADR：`.claude/skills/` 34/34 SKILL "markdown-body-only convention" vs
  ADR-013 2-field schema baseline deviation
- 两 ADR 都是 "current convention vs canonical spec" decision pattern；可考虑 unified ADR
- 若 unified：M3-FU-CLAUDE-SKILL-ADR 推荐 option A advisory；本 plan 推荐 B extend
  canonical；不冲突（两 SKILL family schema 独立）
- M3 startup 时若决定 unified handling → 合并为 ADR-NNN "SKILL canonical schema reconciliation"

## §4 Scope

**Included**:
- M3+ 起独立 ADR draft 决定 option A/B/C
- 若 option A → 3 SKILL.md 平移 PR（每 SKILL 独立 PR）+ 2 runtime-skill contract `version`
  bump + `content_hash` 更新 PR
- 若 option B → Agent_Side v1.2 → v1.3 minor bump PR
- 若 option C → Agent_Side v1.2 §2.1 note 段更新 PR

**Excluded**:
- 不修改 Stage C 落地的 2 runtime-skill contract（待 ADR 决定后再 PR）
- 不强行 normalize 现有 SKILL.md（必须先 ADR 决定）
- 不触达 4 项专属必停 surface 修改（任何 SKILL body change 必走 HITL
  #runtime-skill-content-change + version bump 闭环）

## §5 Verification

```bash
# 决议后跑统一 schema 校验
uv run python scripts/sdd/check_runtime_skill_contracts.py --all   # M3-FU-RUNTIME-SKILL-VALIDATOR 落地后
# 或人工 spot-check 3 SKILL.md body section heads

# 若 option A executed
grep -c "^## Related" src/mj_agent/skills/*/SKILL.md   # 期望 0
# 若 option B/C executed
# Agent_Side §2.1 文本更新到位
```

## §6 AC

- [ ] 独立 ADR draft 落地 with chosen option (A/B/C)
- [ ] 若 option A → 3 SKILL.md 平移完成；2 runtime-skill contract `content_hash` + `version`
      重签
- [ ] 若 option B → Agent_Side v1.3 frontmatter `state: active`；archive v1.2 to
      `docs/archive/rule/`
- [ ] 若 option C → Agent_Side §2.1 advisory note 段落地
- [ ] 全程触发 HITL #runtime-skill-content-change（contract YAML version bump 与 SKILL.md body
      change 同 PR 或紧邻 PR）

## §7 估时 / 依赖

- 估时：ADR draft ~2h；若 option A 实施 ~30min/SKILL × 3 + contract 重签 ~1h = ~2.5h；若
  option B/C 实施 ~1h
- 依赖：M3 startup；可与 M3-FU-CLAUDE-SKILL-ADR 协调（同决策 family）

## §8 严格守约

- 不在 M2 Stage C 改 SKILL.md body（4 项专属必停 surface READ-ONLY）
- 不预判 ADR option（A/B/C 留 M3 reviewer 决定）
- 不修改 M2 落地的 runtime-skill contract（freeze current state）
- 不创建多 ADR（unified ADR 与 M3-FU-CLAUDE-SKILL-ADR 同一 family）

---

> *M3 follow-up plan — `state: active`；M2 Stage C 后置；M3 startup 后处理；独立 ADR + 后续
> PR.*
