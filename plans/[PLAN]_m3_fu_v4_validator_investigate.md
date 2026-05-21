---
type: plan
slug: m3-fu-v4-validator-investigate
summary: M3 follow-up plan — investigate Stage A V4 validator (scripts/sdd/check_claude_skill_contracts.py) root cause for false "34/34 markdown-body-only" report; M2 Stage C batch 2 pre-outline reverify 证实 34/34 SKILL 实际有 ADR-013 native 2-field frontmatter（0 deviation）
state: active
version: 0.1
owner: ranzuozhou
created: 2026-05-21
updated: 2026-05-21
track: shared
refines:
  - plans/[PLAN]_spec_anchored_refactor.md
supersedes: []
related_adrs: []
---

# [PLAN] M3-FU-V4-VALIDATOR-INVESTIGATE — V4 Validator False-Claim Root Cause Investigation

> M3 follow-up plan；M3 startup 后独立 PR；不混入 M3 main work；refines
> `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown.

## §1 Background

M2 Stage C batch 2 启动前 reverify（per `confirm reverify` HITL Gate）对 34/34 SKILL 做
full deep scan，结果**与 Stage A V4 prior claim 直接矛盾**：

| Aspect | Q-A3 prior claim (Stage A V4) | Empirical reverify (Stage C batch 2 pre-outline) |
|---|---|---|
| HasFrontmatter | "34/34 markdown-body-only — body 富文本无 frontmatter" | **34/34 WITH frontmatter** ✓ |
| ADR-013 2-field schema | "baseline deviation" | **34/34 compliant** ✓（仅 `name` + `description`）|
| 跨 family 一致性 | (未声明) | **5/5 family** 一致（doc 6 / flow 9 / git 9 / infra 6 / runtime 4） |

Q-A3 prior claim 是**categorically false** — 不是部分错；是 100% 反真.

## §2 Suspected root causes

3 个 hypothesis 全部需要 V4 实际重跑 + code inspection 才能 confirm:

1. **H1 — V4 looking at wrong file extension / wrong directory**：V4 可能扫的是
   `src/mj_agent/skills/` (in-source canonical) 而非 `.claude/skills/` (in-tree workflow)；
   两个 family schema 不同（in-source 13-field Agent_Side schema；in-tree 2-field ADR-013）；
   命名混淆可能让 V4 报告"in-source SKILL 不符合 2-field schema"被 Q-A3 brief 误读为
   "claude SKILL markdown-body-only"
2. **H2 — V4 schema parser bug**：YAML frontmatter delimiter `---` 解析失败（如 LF/CRLF 混
   合 / BOM / regex multiline flag 缺失）；V4 把全 SKILL 都判为 "no frontmatter detected"
3. **H3 — Q-A3 brief misinterpretation**：V4 实际 report 是另一意义（如 "34/34 SKILL body 内
   没有 schema-additional fields beyond name+description"，i.e., 全是合规的 2-field 而非
   bloated 13-field），但 Q-A3 brief 把 "no additional schema fields beyond name+description"
   错读为 "no frontmatter at all"

不排除多个 root cause 共栖.

## §3 Scope

**Included**:
- 重跑 `scripts/sdd/check_claude_skill_contracts.py` against `.claude/skills/mj-agent-*/SKILL.md`
- Code inspection of `check_claude_skill_contracts.py` to identify scanning logic / schema
  parser / output report wording
- 比对 V4 output 与 reverify table（detail in M3-FU-V4-VALIDATOR-INVESTIGATE evidence）
- Identify root cause (1-3 hypothesis or other)
- Fix V4 bug if applicable OR clarify scope if V4 output is correct but Q-A3 misread
- Document findings in evidence/

**Excluded**:
- 不修改 V4 之外的其他 validator（python / agent / prompt / runtime / docker）
- 不触达 4 项专属必停 surface
- 不重新设计 ADR-013 schema（schema 是 canonical；本 plan 仅验证 V4 vs schema 的一致性）

## §4 Verification

```bash
# 重跑 V4 validator
uv run python scripts/sdd/check_claude_skill_contracts.py --dry-run
uv run python scripts/sdd/check_claude_skill_contracts.py --capability \
  capabilities/infrastructure/mcp-server-governance/
uv run python scripts/sdd/check_claude_skill_contracts.py --all

# 比对 V4 output 与 reverify table
# (reverify table 保存在 M2 Stage C batch 2 pre-outline brief 内；evidence PR copy)

# Code inspection
grep -nE "markdown.*body|no.*frontmatter|body.*only" scripts/sdd/check_claude_skill_contracts.py
```

## §5 AC

- [ ] V4 重跑 + output 与 reverify table 对照表 written to evidence/
- [ ] root cause confirmed（H1 / H2 / H3 / other；可多选）
- [ ] 若 V4 bug → fix PR；新增单元测试覆盖 root cause case；CI 接入
- [ ] 若 Q-A3 brief misinterpretation → 文档化 clarification（在 Stage A 评估材料内补 NOTE）
- [ ] 独立小 PR；commit type `fix(sdd)` or `docs(plan)` per 实际结果

## §6 估时 / 依赖

- 估时 ~2-3h（reproduce + investigate + fix + test）
- 依赖：M3 startup；reverify table（M2 Stage C 内 evidence；不入 Stage C scope）
- PR scope ≤ `scripts/sdd/check_claude_skill_contracts.py` + `tests/unit/` + `evidence/`

## §7 严格守约

- 不在 M2 Stage C 内重跑 V4（保 Stage C 节奏；root cause investigation 是 M3 work）
- 不修改 4 项专属必停 surface（仅 read V4 output + V4 code）
- 不删除 / 不重写 V4 validator（仅 fix or clarify）
- 不创建新 ADR（V4 fix 不构成 architectural decision）

---

> *M3 follow-up plan — `state: active`；M2 Stage C batch 2 pre-outline reverify 后置；M3 startup
> 后处理；独立小 PR.*
