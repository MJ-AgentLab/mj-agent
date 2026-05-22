---
type: plan
slug: m3-fu-rd10c-harmonize
summary: M3 follow-up plan — harmonize RD10=C canonical wording across 5 adapter docs (low severity drift items surfaced during M2 batch 4 cross-check); 独立小 PR；不阻塞 M3 main work
state: completed
version: 0.1
owner: ranzuozhou
created: 2026-05-21
updated: 2026-05-22
track: shared
refines:
  - plans/[PLAN]_spec_anchored_refactor.md
supersedes: []
related_adrs: []
---

# [PLAN] M3-FU-RD10C-HARMONIZE — RD10=C Canonical Wording Alignment

> 长寿命 follow-up plan；M3 startup 后由独立小 PR 处理；不混入 M3 main work；refines
> `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown.

## §1 Background

M2 batch 4（`sdd/adapters/bdd-tdd.md` 撰写）发现 5 个 adapter doc 的 RD10=C 软模式表述与
canonical wording 有 drift。canonical wording 锚定在两处字符级一致：

- `sdd/adapters/bdd-tdd.md` L191（cross-cutting canonical source）
- `sdd/adapters/python.md` L155（mirror reference）

Canonical wording:

> `Red-Green-Refactor 软模式 RD10=C — AI-generated code 允许 "test alongside code"（同一 PR
> 内含 test + 实装；不强制先 commit failing test）`

## §2 5 Drift Items

| # | Adapter file | Line | Current wording | Severity | Target action |
|---|---|---|---|---|---|
| 1 | `langchain-agent.md` | §TDD Rules | 无显式 RD10=C / "test alongside" 提及 | low | 补 1 行 "（RD10=C 软模式同 `python.md` §TDD Rules）" |
| 2 | `docker-container.md` | L201 | "test alongside change"（缺括号 parenthetical） | low | 补全括号 "（同一 PR 内含 test + 实装；不强制先 commit failing test）" |
| 3 | `claude-code-skill.md` | L190 | "test alongside SKILL.md"（缺括号 parenthetical） | low | 同 #2 |
| 4 | `prompt.md` | L167 | "test-first 软模式 per RD10=C"（短形式） | informational | acceptable as-is（prompt scope schema-layer test-first 限定；短形式合适） |
| 5 | `runtime-skill.md` | L175 | "Red-Green-Refactor 软模式 + EVAL 联动"（无 RD10=C 字面） | low | 加 "(RD10=C)" 注 |

## §3 Scope

**Included**:
- 修改 4 个 adapter doc（items #1 / #2 / #3 / #5；item #4 不修改）
- 每改动 ≤ 5 行 diff；不改其他段
- 不修改 `bdd-tdd.md` / `python.md`（canonical sources）

**Excluded**:
- contract YAML / validator script / template — 不在本 plan scope
- 大规模 §TDD Rules 重写 — 仅 wording alignment
- 触达 4 项专属必停 surface — 不涉及（仅文档对齐）

## §4 Verification

```bash
# 改动后 5 adapter 行数仍在 200-280 范围
wc -l sdd/adapters/python.md sdd/adapters/langchain-agent.md sdd/adapters/prompt.md \
       sdd/adapters/runtime-skill.md sdd/adapters/claude-code-skill.md \
       sdd/adapters/docker-container.md sdd/adapters/bdd-tdd.md

# canonical wording 字符级一致（grep "test alongside code" 至少 2 处 = bdd-tdd L191 + python L155）
grep -n "test alongside code" sdd/adapters/*.md

# 4 个修改项各 grep confirm
grep -n "RD10=C" sdd/adapters/langchain-agent.md   # item #1: 至少 1 hit
grep -n "不强制先 commit failing test" sdd/adapters/docker-container.md   # item #2
grep -n "不强制先 commit failing test" sdd/adapters/claude-code-skill.md  # item #3
grep -n "RD10=C" sdd/adapters/runtime-skill.md     # item #5: 至少 1 hit
```

## §5 AC

- [x] 4 adapter doc 修改完成（items #1 / #2 / #3 / #5）；每改动 ≤ 5 行 diff
- [x] 7 adapter doc 行数仍在 200-280 范围（python 206 / langchain 208 / prompt 196 / runtime 223
      / claude-code 231 / docker 265 / bdd-tdd 284）
- [x] `grep "test alongside code"` 仍 = 2 hits（bdd-tdd L191 + python L155 不变；其他不再补
      重复 canonical）
- [x] item #4 (`prompt.md`) 不修改；plan §2 表 "acceptable as-is" 声明保留
- [x] D-3c commit lands in M3 documentation branch（commit message
      `refactor(sdd-adapter): align RD10=C wording across 4 adapter docs`；ε-1 path per Δ-1
      provenance; not split as standalone PR — bundled into Stage D arc per D-3c plan §6
      consolidated commit strategy）
- [x] D-3c commit body cross-refs (a) this plan §2 5-item table (b) §7 6th intercept
      registered for D-3f cluster #4 fill

## §6 估时 / 依赖

- 估时 ~1h（4 adapter wording alignment + verification）
- 依赖：M3 startup（不阻塞 M3 main work）
- PR scope ≤ 5 adapter doc；不触达 src/ / tests/ / infra/

## §7 严格守约

- 不触达 4 项专属必停 surface（本 plan 仅文档对齐；不涉及 SKILL.md / system.md 等）
- 不修改 `bdd-tdd.md` / `python.md`（canonical 双锚点不动）
- 不改 contract YAML / validator script / template
- 不创建新 ADR（wording alignment 不构成 architectural decision）

---

> *M3 follow-up plan — `state: completed` 2026-05-22；executed during M3 Stage D D-3c per ε-1
> path (4-file scope honoring plan §2 verbatim; python.md / bdd-tdd.md / prompt.md read-only per
> Δ-1 canonical source doctrine carried from D-3b).*
