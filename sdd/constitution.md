---
type: sdd-kernel
artifact: constitution
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-01
track: shared
ai_visibility: source-of-truth
---

# SDD Constitution

> Phase M0 skeleton — body 在 Phase M2 内容填充阶段（spec-anchored-refactor PR-M2-1）完成.
> 本文件位于 `sdd/**`，**与 `state` 取值无关**即属 `policies/ai-agent.md` §5
> 「`policies/**` + `sdd/**`（kernel 元规则本身）」行的 **HITL required** 面——**不在** canonical
> 10-enum 内，兜底是 merge review。

## §1 Purpose

SDD（Spec-Driven Development）治理 mj-agent 的开发与变更：**所有变更先有规格（capability spec
+ contract），后有实现**。本文件是 mj-agent SDD Kernel 的元规则入口；细化规则下沉到
`sdd/lifecycle.md` / `sdd/gates.md` / `policies/`.

> TBD: Phase M2 内容填充 — 引用《通用 Spec-Anchored 手册 v1.1》§1-§3 三柱原则，并用 mj-agent
> native 语言重写（不复制原文）.

## §2 三柱原则（Three Pillars）

1. **Strong Specification** — capability spec.yml + requirements.md 是 source of truth.
2. **Local Specification = Source** — 每 capability 自包含；不跨目录隐式依赖.
3. **Adapter-based Verification** — 由 sdd/adapters/ 定义的 contract 校验 + CI gate 兜底.

> TBD: Phase M2 — 三柱原则在 mj-agent 4 项专属必停场景下的具体落地展开.

## §3 mj-agent native 补充

### §3.1 数据-LLM 边界三原则（ADR-000）

1. **最小必要出网** — 仅在响应用户问题时调用 LLM；不在数据加载/ETL 阶段触发.
2. **通道隔离** — biz 数据（read-only analyst grant）与 LLM 出网走不同连接池.
3. **工具中介** — LLM 不直接握 SQL，所有数据访问经 `tools/sql/{guardrail,precheck,execute}`.

详见 `policies/data-boundary.md` + `decisions/ADR-000_Data_LLM_Boundary_Principles.md`（Phase M5
平移自 `docs/adr/`）.

### §3.2 4 项 mj-agent 专属必停（hard stops）

任一修改触发以下文件必须 HITL（不可绕过；写入 `sdd/gates.md` §"mj-agent specific hard stops"）：

| ID | 路径 | 触发原因 |
|---|---|---|
| sql-guardrail-relax | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | L1/L1b 防御层；放宽 = 安全主线动摇 |
| runtime-skill-content-change | `src/mj_agent/skills/*/SKILL.md` body | LLM 行为契约 |
| prompt-version-bump | `src/mj_agent/prompts/system.md` version 字段 + body | 系统提示词行为边界 |
| biz-catalog-sync | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | mirror 上游业务系统数据字典 |

### §3.3 3 SKILL 来源严格区分

| Source | Path | Schema | Loader | Governance |
|---|---|---|---|---|
| in-source（runtime） | `src/mj_agent/skills/<name>/SKILL.md` | 13-field Agent_Side | `load_skill()` strip frontmatter | Track B —— kernel home **现为** `sdd/adapters/runtime-skill.md`（并入**已完成**；Agent_Side v1.2 于 M6 PR4 归档，per ADR-031） |
| in-tree（workflow） | `.claude/skills/mj-agent-*/SKILL.md` | 2-field ADR-013 native | Claude Code main process | Track C —— kernel home **现为** `sdd/adapters/claude-code-skill.md`（并入**已完成**；Meta v2.2 于 M6 PR4 归档，per ADR-031） |
| marketplace plugin | `mj-agentlab-marketplace/plugins/*` | 2-field ADR-013 native | Claude Code plugin loader | out of mj-agent governance |

## §4 与其他 SDD Kernel 文件关系

- `sdd/lifecycle.md` — Capability + Archive 状态机
- `sdd/gates.md` — G1-G17 全局 gate + 8 stack-specific + G19-G28 BDD/TDD + §"mj-agent specific
  hard stops"
- `sdd/traceability.schema.json` — `trace.yml` 机器可读 schema
- `sdd/archive.schema.json` — `archive.yml` 机器可读 schema
- `sdd/workflows/` — 6 工作流（new / evolve / bugfix-drift / cross-cap / hotfix / archive）
- `sdd/adapters/` — 7 启用 adapter（python / langchain-agent / prompt / runtime-skill /
  claude-code-skill / docker-container / bdd-tdd）
- `sdd/templates/` — 标准模板套件（spec / requirements / design / tasks / runbook / trace /
  evidence / archive / tombstone / behavior.feature / bdd-scenarios / tdd-test-list +
  contracts/）

## §5 Phase 推进里程碑

| Phase | 期望本 constitution 状态 |
|---|---|
| M0 | draft（本文件创建） |
| M1 | draft（5 pilot capability 落地后 lessons-learned 回填 §3） |
| M2 | draft → active 候选（adapter 全集就绪；PR-M2-1 promote） |
| M5 | active（旧 STANDARD 整体 archive ceremony 完成；SDD Kernel 成为唯一治理入口） |
| M6 | active（每 3-6 月或 model release 后审计，per `policies/documentation.md` §Review Cadence） |

---

> *Phase M0 skeleton — `state: draft`. 内容填充见 `plans/[PLAN]_spec_anchored_refactor.md` Phase
> M2 §"Content Backfill".*
>
> *v0.2（2026-09-01）：#497 ⑤ —— 两处失效引用真值化。(1) 文首横幅原引 root `CLAUDE.md` 的一个
> **已不存在**的段名（对位段 = §「必停 surfaces」）。⚠ **该段名在此有意不复述** —— 复述会在本仓
> 再造一处 grep 命中，而「全仓不再有活体指针指向那个段名」正是本次修复的验收判据（issue #497
> AC-5）。原句还把 HITL 义务写成「promote 为 `active` 后**才**落入」的条件式 —— 实况是 `sdd/**`
> 无论 `state` 取值都属 `policies/ai-agent.md` §5 的 HITL required 面，故连指针带条件一并更正。
> ⚠ 该短语另以**跨行折断**形式存在于 `policies/ai-agent.md` §5 导言（`…Must Not Edit` 换行
> `Without Approval"`，单行 grep 命不中），那是**正确的历史引述**、不得改；且该文件是 enforcement
> `policy_ref`，改它会重置 V13 观察期。(2) §3.3 三源表 Governance 列**两行**（`in-source（runtime）`
> 与 `in-tree（workflow）`）都用未来时写「Phase M5 后并入 `sdd/adapters/…`」，而两个 adapter 早已是
> kernel home、Meta v2.2 / Agent_Side v1.2 已于 M6 PR4 归档（ADR-031）—— 改现在时。⚠ 两行是同一
> 缺陷的双胞胎，只修其一会让同一张表自相矛盾，故一并修（**按行名指认、不用行号** —— 本次改动
> 自身就会推移行号）。**本单不动**同文件其余已知过期项：§3.2 的退役 enum ID
> `prompt-version-bump`、§4 的 `8 stack-specific` / `7 启用 adapter` / `6 工作流` 三处计数、
> 文末 `Content Backfill` 死指针。⚠ 它们是**既存独立缺陷、非本单诱发**，且截至本次落盘**尚无
> GitHub issue 登记** —— 不要据本条以为已有载体。*
