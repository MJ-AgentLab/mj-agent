---
type: sdd-kernel
artifact: lifecycle
state: active
version: "1.5"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-29
track: shared
ai_visibility: source-of-truth
---

# SDD Lifecycle

> **Kernel home note (M6 PR4a-3)**: 本 doc 是状态机真相源。它定义三套**正交**生命周期：
> §1 capability package 9 态（SDD 主轴）、§2 working 文档 3 态及 archived 历史兼容（`plans/**` 任务语义；M6 PR4a-3
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
| planned | tasks.md 任务清单完整（含 tdd.test_list 高风险） | 接受基线/授权与 plan-vs-spec 对齐 | 实施开工 |
| implementing | 代码实施中 | 单 PR open | 单 PR ready-to-merge |
| verifying | contract test + bdd + tdd 跑 | 测试 PASS | evidence/ 写入 |
| active | 全套 artifact 就绪 | trace.yml 完整链路 | HITL 触发 evolve / deprecate |
| evolving | REQ 变更 / contract 扩展 / 依赖升级 | evolve-capability workflow | 回到 active |
| deprecated | 弃用宣告（不再演进） | HITL + ADR | archive ceremony（[[sdd/workflows/archive-capability|sdd/workflows/archive-capability]]） |

> 每态的 evidence 要求 + CI gate 联动见 §3 转移表 + [[sdd/gates|sdd/gates]]（G8 evidence-required
> 是 `verifying → active` 的 active-conditional 门；其余按转移触发）。

## §2 Working-doc Lifecycle（3 态；`plans/**`）

working 与 capability / canonical 生命周期正交。新文件按 [[policies/documentation|documentation]] §2.7 进入任务目录；旧根文件兼容，历史不批量迁移。独立任务可仅有 Intake/Report/Assessment，不为了状态或整体接受补造 Plan。

### §2.1 状态与完成条件

| state | 含义 | 触发 |
|---|---|---|
| `draft` | 拟订或尚未采纳 | 新文档默认；废弃 draft 保持 draft，正文记原因/恢复条件 |
| `active` | 已明确采纳且正在交付 | 记录真实采纳依据；关联 Issue/PR open 本身不代替采纳 |
| `completed` | 本文档交付条件已满足 | 主 Plan：AC 满足、成果可用、Owner 明确接受准确版本；其他 working：Agent 核实自身已确定交付条件后记录证据 |

`archived` 仅兼容历史，不再是活动状态转移目标。非主 Plan working 如果自身交付条件明确包括 Owner 接受，仍须满足该条件。报告 completed 仅表示报告交付完成，不表示 Plan 或整个任务完成。

### §2.2 结果核实与整体接受

Agent 分别记录候选集成、验证、交付、待接受、已接受、部分完成、延期、失败和未知；merged、closed、deployed、机器 PASS 不能替代 Owner 接受。主 Plan 仅在其完整基线满足、成果可用及 Owner 明确接受准确版本后改 completed 并刷 updated。一份报告完成不推导整个 Plan 完成。

独立报告任务的整体接受仍由 Owner 在既有 Issue/会话/任务记录中表达，不另造接受系统，也不补主 Plan。主 Plan 的一次明确接受可以同时覆盖所列范围的整体任务接受，无须重复确认。非核心延期独立登记原因、影响与恢复条件；影响完整接受基线时须 Owner 决定调整。

接受记录绑定固定提交完整文件或完整可恢复快照的准确位置，保留旧决定；内容实质变化后旧接受仅覆盖旧基线，路径变化不自动重置接受。检查点保存实际 workspace/ref/SHA、验证环境/时点、证据、在途副作用和下一步，重入先核现实。

### §2.3 原位保留与稳定引用

完成文件原地保留，不运行 working 物理归档、180 天 GC、候选检测或相关 CI；不强制局部 INDEX。命名修正仍按受控改名规则同步目录/主文件、活动引用和交付路由；task_id、INTENT ID、固定提交/旧快照和旧决定不变。新 HEAD 仍核平台审核。

### §2.4 历史兼容与 GC 退出

Issue #608 / ADR-043 取消 working 的 `completed → archived` 物理 GC。旧 archived 文件仍可读取，原脚本退出活动流程，不以此授权删除历史资料。canonical 归档仍按 [[policies/archive|archive]] 的独立规则执行；INTENT 退役例外见 §4.2。

### §2.5 Retroactive 补落（漏落盘事后补救）

> 源：Meta §5.11.6（ADR-021 follow-up）。区别于 §2.2 Stage 17 自动化（`active → completed`）
> 与已退出活动链的历史 §2.4 GC——本节治"实施期漏落盘 `[PLAN]` / `[INTAKE]`，
> 事后审计补救"的路径。

**触发场景**（事后发现漏落盘 + 满足任一）：

1. **多 PR 链 ≥ 3** 且不满足 `sdd/workflows/execution-loop.md §3.2` Stage 4 豁免（即非单文件
   Low-risk bugfix / documentation）；
2. **High 风险**（含 §3.1 mj-agent 专属 4 必停之一：runtime-skill-content-change /
   prompt-version-or-body-change / biz-catalog-sync / sql-guardrail-relax）；
3. **跨 ≥ 5 个 canonical 文档**，或改动 Track C primary 执行闭环治理。

**补落规则**：

- **state 按本文档真实交付条件置 draft / active / completed**；主 Plan 的 completed 必须 AC 满足、成果可用且 Owner 明确接受，其他 working 按 §2.1；禁止用最后 merge 日期推定接受；
- frontmatter 加 `retroactive: true`（机器可识别；`scripts/check_frontmatter.py` 对未知字段宽容，不破坏 schema）；
- 头部加 `> [!warning]` 声明框：醒目标注"事后回填，非真实 Stage 0/4 输出"，引导读者关注内容 trace；
- **凭证 trace 段必加**：逐段标内容来源（PR description / commit / memory / AGENTS.md update /
  vault 草稿），避免 time-shift bias；
- 在当前任务记录追加来源与补落时间；冻结归档源不回写。

**不补落判定**（凭证已充分，可跳过补落；满足任一即可不补）：

- `AGENTS.md` 已有同等深度的 "YYYY-MM-DD update" 段；
- memory feedback / project 文件已完整覆盖决策点；
- commit message + PR body 已含 7 段 PLAN 同等信息。

> Cross-ref：ADR-021（同上，prose 引用）；`sdd/workflows/execution-loop.md §3.2` Stage 4 豁免 +
> §7 post-merge 沉淀；本 doc §2.2 Stage 17 `active → completed` 自动化；
> [[../.agents/skills/mj-agent-flow-intake/SKILL|mj-agent-flow-intake]] §2.1 落盘判定。历史首次
> retroactive 落地记录（2026-05-18 cross-repo decoupling）留在归档源 Meta §5.11.6.1（frozen 历史）。

## §3 Capability 状态转移触发条件

| Transition | 触发 | 必经 gate |
|---|---|---|
| idea → specified | spec.yml 起草 + schema 校验 | G1 check_capability_schema |
| specified → contracted | contracts/ 文件 ≥ 1 + 高风险加 behavior.feature | G3 check_contracts |
| contracted → planned | tasks.md `tdd.test_list[]` 完整（高风险）| G23 check_tdd_test_list（Phase M3 起 warning；M6 blocking） |
| planned → implementing | PR open + 基线/授权对齐 | — |
| implementing → verifying | contract test + bdd-step + tdd green | G2/G5/G19-G28 |
| verifying → active | evidence 写入 + trace.yml 链路完整 | G8 evidence required（Phase M4 起 blocking） |
| active → deprecated | ADR + HITL | A12-A14 PR gate（[[policies/documentation|policies/documentation]] §5.3；历史源 Meta §7.7） |
| deprecated → archived | archive ceremony + archive.yml | G11/G12 check_archive_manifest（[[policies/archive|policies/archive]] §3/§4） |

> 表中治理决定与授权分类完整定义见
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

§4 的 5 态从 `active` 起算，**不含 `draft`**；§2 的 3 态含 `draft` 但只治 `plans/**`。于是 canonical
与 kernel 文档（`policies/**` / `sdd/**`）用的 `draft` 长期没有 kernel 级定义，只散落在各文件脚注里。
本节补上，**语义与既有落盘实况一致，不改任何一份文件的现值**。

**定义**：`draft` = **正文尚未 authoring 到该文档在其 canonical home 应有的深度**——骨架、留有未填的
`> TBD` 块、或内容已成型但沿用了当初的 phase 标签。

**`draft` 不等于「未生效」。** 一份 `draft` 文档完全可以是活体规则的唯一真相源，且仓内确有此例：
`policies/docker-runtime.md` 长期是 `docker/` 下审批级别的 kernel SoT——其 §4 被 `docker/AGENTS.md`
与 `docker/AGENTS.md` 两个 entry adapter 回指取级别——却始终是 `state: draft`。判断一份文档
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
| `SCAN_ROOTS` 内的文档 | 有，按类型/路径 | `scripts/check_frontmatter.py` 对 RUNBOOK / POSTMORTEM / canonical ASSESSMENT / ISSUE / EVAL 按 active/completed 校专属字段；INTENT 始终校九字段和三态；新 working 校七字段与独立状态，历史根布局兼容 |
| `policies/**` · `sdd/**` · `capabilities/**` | **无** | 三者都不在 `SCAN_ROOTS` 内（门禁事实的 canonical 记载见 [[policies/documentation|policies/documentation]] §3.1），且无任何脚本读它们的 frontmatter `state`。故此处的 `state` 是**给人读的**，靠 merge review 兜底 |

> 本节只定义 canonical / kernel 侧的 `draft`。`plans/**` 的 `draft` 按 §2.1（3 态，语义是"任务未对齐"）；
> `capabilities/**` 用的是 §1 的 9 态词表（`drafting` 等），与本节正交——per
> [[policies/documentation|policies/documentation]] §3.1 规则 9 的 `capabilities/**` 豁免条款。

### §4.2 INTENT 专属生命周期

INTENT 为独立 canonical 原意正本，状态仅 `draft → active → deprecated`。draft 是尚在整理/核对；active 须记录原意核对和内容接受的真实情况、完整适用基线与责任，不把该状态当作执行授权或交付接受。deprecated 在原路径保留 ID、旧决定、退役原因和后继；不进入 §4 的物理归档或释放编号。Plan/Issue 完成、修订、跨年、标题或路径变化不传播状态或换 ID。实质变化保留旧内容接受，仅对新基线重新取得所需决定。专属字段、ID 查重和集合读取失败处理见 [[policies/documentation|documentation]] §2.8。

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
>
> *v1.3（2026-08-11）：#482 — §4.1 的「`draft` 不等于未生效」举例改为**耐久措辞**。原句逐字引用
> `policies/docker-runtime.md` 的头注（「§4 已是 live SoT；§1-§3 待内容填充」），而该头注在同批
> PR 里随三个 TBD 块填充而改写，引用当场失真。改为引「该文件长期是 `docker/` 审批级别的 kernel
> SoT（§4 被两个 entry adapter 回指）却始终 `state: draft`」——同一论点，但不依赖任何会变的
> 措辞。**本次零 state 变更、零定义变更**，只修这一处诱发性陈旧。判例：引用他文时引**结构事实**
> 不引**当期措辞**——后者没有任何 gate 兜底（`check-stale-docs` 只匹配完整 backtick 路径字面量）。*

> *v1.5（2026-10-29）：#608 / ADR-043 — working 三态、按文档交付条件完成与整体接受分离；GC 退出；加入 INTENT 原位退役独立生命周期，冻结历史不回写。*
