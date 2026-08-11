---
type: sdd-kernel
artifact: lifecycle
state: active
version: 1.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: shared
ai_visibility: source-of-truth
---

# SDD Lifecycle

> **Kernel home note (M6 PR4a-3)**: 本 doc 是状态机真相源。它定义三套**正交**生命周期：
> §1 capability package 9 态（SDD 主轴）、§2 working 文档 4 态（`plans/**` 任务语义；M6 PR4a-3
> 收纳 Meta §5.11 / ADR-021 决议）、§4 canonical 文档 archive 5 态（**§4.1 补该链条之前的 `draft`
> 入口态 + 翻 `active` 的判据**）。§3 给 capability 态转移触发 +
> gate 联动。归档侧实施细节（ceremony / manifest / 物理归档）在 [[policies/archive|policies/archive]]；
> 本 doc 只定义状态与触发，不重复 ceremony 流程。

## §1 Capability Lifecycle（9 态）

```
idea ─► specified ─► contracted ─► planned ─► implementing ─► verifying ─► active ─► evolving
                                                                              ▲          │
                                                                              └──────────┘
                                                                                 │
                                                                                 ▼
                                                                            deprecated
```

| 状态 | 含义 | 进入条件 | 退出条件 |
|---|---|---|---|
| idea | 新需求未规格化 | 用户/SDR 提出 | spec.yml 起草 |
| specified | spec.yml + requirements.md 起草 | spec.yml schema 通过 | contracts/ 起草 |
| contracted | contracts/ 至少 1 件 + behavior.feature（高风险） | check_contracts.py PASS | tasks.md 拆分 |
| planned | tasks.md 任务清单完整（含 tdd.test_list 高风险） | HITL Gate-1 plan-vs-spec 对齐 | 实施开工 |
| implementing | 代码实施中 | 单 PR open | 单 PR ready-to-merge |
| verifying | contract test + bdd + tdd 跑 | 测试 PASS | evidence/ 写入 |
| active | 全套 artifact 就绪 | trace.yml 完整链路 | HITL 触发 evolve / deprecate |
| evolving | REQ 变更 / contract 扩展 / 依赖升级 | evolve-capability workflow | 回到 active |
| deprecated | 弃用宣告（不再演进） | HITL + ADR | archive ceremony（[[sdd/workflows/archive-capability|sdd/workflows/archive-capability]]） |

> 每态的 evidence 要求 + CI gate 联动见 §3 转移表 + [[sdd/gates|sdd/gates]]（G8 evidence-required
> 是 `verifying → active` 的 active-conditional 门；其余按转移触发）。

## §2 Working-doc Lifecycle（4 态；`plans/**`）

> 源：Meta §5.11（ADR-021 决议；归档侧物理实施在 [[policies/archive|policies/archive]] §8）。
> 与 §1 capability 生命周期**正交**——working 文档语义是"任务完成"（`completed`），**不是**
> canonical 文档的"被新版本替代"（`deprecated`）。[[policies/archive|policies/archive]] §2 反向指入本节。

### §2.1 4 态机

| state | 含义 | 触发 |
|---|---|---|
| `draft` | 仍在拟订；未对齐 | 新建文档默认 |
| `active` | 已采纳；任务执行期 | 关联 issue/PR open |
| `completed` | 任务自然完成 | 关联 PR merged / Issue closed / Release deployed |
| `archived` | 物理归档（GC；见 §2.4） | `completed` ≥ 6 月 + 引用 0 时 |

### §2.2 Stage 17 Post-merge 自动化

`mj-agent-flow-post-merge` SKILL Step 9 自动识别 PR/Issue 关联的 `[PLAN]_*.md` / `[INTAKE]_*.md`，
state 由 `active` 改 `completed` 并刷 `updated` 字段；**不移动文件位置**；保留所有跨文档 reference
（Step 9 是 diff 草案 + user Edit 确认，非自动落盘）。

### §2.3 边界

| 项 | 处理 |
|---|---|
| `completed` 文件位置 | 保留 `plans/` 原路径；不移 `plans/archive/`（避免断跨文档引用） |
| `completed` 文件 INDEX | `plans/` 不维护 INDEX |
| 跨文档引用稳定性 | 仅 state 改变 → 引用路径不变 → 全仓 reference 稳定 |
| 长期 `draft` abandon | 保持 `draft`（留重启余地）；确认废弃可手工标 `archived`（不移文件） |
| `completed` 文件 grep | 仍可命中；state 字段标识其已落地 |

### §2.4 archived 物理归档

`completed` → `archived` 的物理 GC（创建 `plans/archive/` + `git mv` + frozen snapshot）实施指引在
[[policies/archive|policies/archive]] §8（触发：`completed` ≥ 6 月 + grep ref = 0 + HITL；首次 GC 约
2026-11+）。本节只定义 state 语义。

> Cross-ref：ADR-021（working-doc lifecycle 决策；已 archive 至 `archive/decisions/superseded/`，
> 按编号 prose 引用）；ADR-023（plan GC infra）；Stage 17 自动化 [[../.claude/skills/mj-agent-flow-post-merge/SKILL|mj-agent-flow-post-merge]] Step 9。

### §2.5 Retroactive 补落（漏落盘事后补救）

> 源：Meta §5.11.6（ADR-021 follow-up）。区别于 §2.2 Stage 17 自动化（`active → completed`）
> 与 §2.4 archived 物理归档（`completed → archived`）——本节治"实施期漏落盘 `[PLAN]` / `[INTAKE]`，
> 事后审计补救"的路径。

**触发场景**（事后发现漏落盘 + 满足任一）：

1. **多 PR 链 ≥ 3** 且不满足 `sdd/workflows/execution-loop.md §3.2` Stage 4 豁免（即非单文件
   Low-risk bugfix / documentation）；
2. **High 风险**（含 §3.1 mj-agent 专属 4 必停之一：runtime-skill-content-change /
   prompt-version-or-body-change / biz-catalog-sync / sql-guardrail-relax）；
3. **跨 ≥ 5 个 canonical 文档**，或改动 Track C primary 执行闭环治理。

**补落规则**：

- **state 直接置 `completed`**（不走 `draft → active` 中间态）+ 填 `completed: <最后 PR merged ISO 日期>`；
- frontmatter 加 `retroactive: true`（机器可识别；`scripts/check_frontmatter.py` 对未知字段宽容，不破坏 schema）；
- 头部加 `> [!warning]` 声明框：醒目标注"事后回填，非真实 Stage 0/4 输出"，引导读者关注内容 trace；
- **凭证 trace 段必加**：逐段标内容来源（PR description / commit / memory / CLAUDE.md update /
  vault 草稿），避免 time-shift bias；
- 在归档源 Meta §5.11.6.1（历史落地记录）追加 1 行时间序记录。

**不补落判定**（凭证已充分，可跳过补落；满足任一即可不补）：

- `CLAUDE.md` 已有同等深度的 "YYYY-MM-DD update" 段；
- memory feedback / project 文件已完整覆盖决策点；
- commit message + PR body 已含 7 段 PLAN 同等信息。

> Cross-ref：ADR-021（同上，prose 引用）；`sdd/workflows/execution-loop.md §3.2` Stage 4 豁免 +
> §7 post-merge 沉淀；本 doc §2.2 Stage 17 `active → completed` 自动化；
> [[../.claude/skills/mj-agent-flow-intake/SKILL|mj-agent-flow-intake]] §2.1 落盘判定。历史首次
> retroactive 落地记录（2026-05-18 cross-repo decoupling）留在归档源 Meta §5.11.6.1（frozen 历史）。

## §3 Capability 状态转移触发条件

| Transition | 触发 | 必经 gate |
|---|---|---|
| idea → specified | spec.yml 起草 + schema 校验 | G1 check_capability_schema |
| specified → contracted | contracts/ 文件 ≥ 1 + 高风险加 behavior.feature | G3 check_contracts |
| contracted → planned | tasks.md `tdd.test_list[]` 完整（高风险）| G23 check_tdd_test_list（Phase M3 起 warning；M6 blocking） |
| planned → implementing | PR open + HITL Gate-1 | — |
| implementing → verifying | contract test + bdd-step + tdd green | G2/G5/G19-G28 |
| verifying → active | evidence 写入 + trace.yml 链路完整 | G8 evidence required（Phase M4 起 blocking） |
| active → deprecated | ADR + HITL | A12-A14 PR gate（[[policies/documentation|policies/documentation]] §5.3；历史源 Meta §7.7） |
| deprecated → archived | archive ceremony + archive.yml | G11/G12 check_archive_manifest（[[policies/archive|policies/archive]] §3/§4） |

> 表中 "HITL Gate-1" / "HITL + ADR" trigger 完整 enum 见
> `policies/ai-agent.md §4 HITL Required Scenarios — Canonical 10-Enum`；本表仅列 state-
> machine transition 触发条件，不重复 enum 完整定义.

## §4 Canonical 文档 Archive State（5 态；archive.yml `original_state` / `ai_visibility`）

```
active ─► deprecated ─► frozen ─► archived ─► purge-eligible
```

| 状态 | 含义 | AI 可读性（archive.yml `ai_visibility`） |
|---|---|---|
| active | 在用 | source-of-truth |
| deprecated | 弃用宣告，仍有引用 | reference |
| frozen | 不再修改，仅作历史 | reference |
| archived | 已迁入 `archive/` 目录 | hidden（默认） / reference（按需） |
| purge-eligible | 保留期满，可物理删除（per [[policies/archive|policies/archive]] §6 retention_class） | hidden |

> `frozen → archived` transition（ceremony / `[DEPRECATED]_` 命名 / manifest 写入）详见
> [[policies/archive|policies/archive]] §4 ceremony playbook + [[sdd/workflows/archive-capability|sdd/workflows/archive-capability]]（capability 包）。
> `ai_visibility` 枚举 `{hidden, reference}` 与 G14/G15 引用规则见 [[policies/archive|policies/archive]] §3/§5。

### §4.1 `draft` —— §4 链条之前的入口态（#480）

§4 的 5 态从 `active` 起算，**不含 `draft`**；§2 的 4 态含 `draft` 但只治 `plans/**`。于是 canonical
与 kernel 文档（`policies/**` / `sdd/**`）用的 `draft` 长期没有 kernel 级定义，只散落在各文件脚注里。
本节补上，**语义与既有落盘实况一致，不改任何一份文件的现值**。

**定义**：`draft` = **正文尚未 authoring 到该文档在其 canonical home 应有的深度**——骨架、留有未填的
`> TBD` 块、或内容已成型但沿用了当初的 phase 标签。

**`draft` 不等于「未生效」。** 一份 `draft` 文档完全可以是活体规则的唯一真相源，且仓内确有此例
（`policies/docker-runtime.md` 的头注即自陈「§4 已是 live SoT；§1-§3 待内容填充」）。判断一份文档
对 AI 是否权威，看 **`ai_visibility`** 而不是 `state`——这就是 kernel 文档同时写着 `state: draft` 与
`ai_visibility: source-of-truth` 却不矛盾的原因：前者说"写完了没"，后者说"算不算数"。

**翻 `active` 的判据 = 操作必要性**（"live-kernel-home"）：当某个下游动作要求该文档必须是 LIVE 时才翻，
而不是定期普查或图整齐。判据取自首次 kernel 晋级 commit `13605c8`（M6 PR4a-1）的自述——它为了让 PR4
能把 STANDARD 归档**进**该 policy 才把它转 active，并在同一段里明确决定让姊妹 policy 继续留在 draft。
后续 `d1a077a` / `c5b3ac8` / `1348776` 沿用同一判据。推论：**长期停在 `draft` 本身不构成漂移**，
它是"尚无下游动作需要它 LIVE"的如实记录；真正该追的是内容债务本身（登记在
`plans/[PLAN]_spec_anchored_refactor.md` 的 `M6-FU-*-TBD-SWEEP` 条目），不是 `state` 字段的外观。

**晋级动作**：翻 `state` 的同批必须做完该文档的 kernel 改动纪律（`version` + `updated` + 文末脚注条目），
并清理正文里已失效的 phase 自述。翻转本身**不需**单独 ceremony，也**不要求** `version` 跳到 1.0
（`sdd/gates.md` 是在 v0.2 上转的 active）。

**`state` 在哪些面有机器后果**——写在这里是因为"kernel 的 state 无 gate"容易被推广成"state 到处都无所谓"，
而那是错的：

| 面 | `state` 有无机器后果 | 载体 |
|---|---|---|
| `src/mj_agent/skills/**/SKILL.md` | **有，且 blocking** | `scripts/sdd/check_runtime_skill_contracts.py` 把 frontmatter `state` 与契约 `skills[].state`（frozen）逐字比对，不等即 FAIL。**改这类文件的 `state` 必须同批改契约**，否则 CI 红 |
| `SCAN_ROOTS` 内的 canonical 文档 | 有，但只限 5 个类型 | `scripts/check_frontmatter.py` 在 `state ∈ {active, completed}` 时强制 RUNBOOK / POSTMORTEM / ASSESSMENT / ISSUE / EVAL 的类型专属字段；其余类型无差别 |
| `policies/**` · `sdd/**` · `capabilities/**` | **无** | 三者都不在 `SCAN_ROOTS` 内（门禁事实的 canonical 记载见 [[policies/documentation|policies/documentation]] §3.1），且无任何脚本读它们的 frontmatter `state`。故此处的 `state` 是**给人读的**，靠 merge review 兜底 |

> 本节只定义 canonical / kernel 侧的 `draft`。`plans/**` 的 `draft` 按 §2.1（4 态，语义是"任务未对齐"）；
> `capabilities/**` 用的是 §1 的 9 态词表（`drafting` 等），与本节正交——per
> [[policies/documentation|policies/documentation]] §3.1 规则 9 的 `capabilities/**` 豁免条款。

## §5 与 sdd/workflows/ 联动

每个状态转移对应一个或多个 workflow：

| Transition 起点 | Workflow |
|---|---|
| idea / specified | `sdd/workflows/new-capability.md` |
| active → evolving | `sdd/workflows/evolve-capability.md` |
| 任意态触发 bugfix | `sdd/workflows/bugfix-drift.md` |
| 跨 capability 共享 contract 变更 | `sdd/workflows/cross-capability-change.md` |
| 生产紧急 | `sdd/workflows/hotfix.md` |
| deprecated → archived | `sdd/workflows/archive-capability.md` |

---

> *M6 PR4a-3 — kernel home for the three state machines（§1 capability 9 态 / §2 working-doc 4 态
> [GAP #9；Meta §5.11] / §4 archive 5 态）+ §3 转移触发。归档 ceremony / manifest / 物理归档实施在
> policies/archive；HITL trigger enum 在 policies/ai-agent §4。*
>
> *v1.2（2026-08-11）：#480 — 新增 §4.1，补上 canonical / kernel 文档的 `draft` 入口态定义。此前
> §4 的 5 态自 `active` 起算、不含 `draft`，§2 的 4 态含但只治 `plans/**`，于是仓内大量在用的
> `state: draft` 在 kernel 层面无定义，含义只散落在各文件脚注里——读起来像治理漂移，实则不是。
> §4.1 写下三件事：(a) `draft` = 正文未 authoring 到应有深度，**不等于「未生效」**（权威性由
> `ai_visibility` 承载，这正是 kernel 文档 `state: draft` + `ai_visibility: source-of-truth`
> 并存不矛盾的原因）；(b) 翻 `active` 的判据 = **操作必要性**，取自首次 kernel 晋级 commit
> `13605c8` 的自述（它同段明确决定让姊妹 policy 继续留 draft），故长期停在 `draft` 本身不构成漂移，
> 该追的是登记在 `M6-FU-*-TBD-SWEEP` 的内容债务；(c) `state` 在哪些面**有**机器后果——runtime SKILL
> 的契约冻结是 blocking 的，`SCAN_ROOTS` 内只对 5 个类型生效，而 `policies/` `sdd/` `capabilities/`
> 三处完全无 gate。**本次零 state 变更**：不翻任何一份文档，只补定义。*
