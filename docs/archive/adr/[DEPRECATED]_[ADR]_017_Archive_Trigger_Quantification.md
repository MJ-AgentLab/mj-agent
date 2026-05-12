---
type: adr
domain: SYS
summary: 引入 4 类必触发 + 1 类反例的归档量化判定（mj-system v5.2 §10.1 派生），落 Meta v2.1 §5.9，消除 ADR-011 §5.6.1 HITL 判断模糊
owner: 项目负责人
created: 2026-05-09
updated: 2026-05-09
state: deprecated
archived: 2026-05-11
replaced-by: docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md
decision: accepted
track: shared
tags:
  - adr
  - documentation
  - archive
  - lifecycle
  - mj-system-derivation
---

# ADR 017: Archive Trigger Quantification (4 必触发 + 1 反例)

## Context

[[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] §5.6.1 仅以文字描述 HITL trigger："正式版本演进时 reviewer 在 PR review 阶段判定"，缺量化标准。ADR-011 §Consequences "负面"第二条已明确承认此痛点：

> Living vs Frozen 引用判断依赖作者+reviewer 共识——新外部贡献者需要 onboarding 培训（应包含 Framework v1.1 §5.6 + 本 ADR）

mj-agent 当前已积累 5 份 archived 文件（v1.0/v1.1 + v2.0 trio）+ 1 次 promote 经验（v2.0 → v2.1）。每次归档判定都依赖 reviewer 个人经验，无可 cite 规则。

mj-system 在 v5.0 → v5.1 → v5.2 共 3 次大版本归档（11 份 legacy 文件可见）经验中沉淀出 v5.2 §10.1 显式判定表（4 类必触发 + 1 类反例），实测 1 个月（2026-04 → 2026-05）未见漏触发或误触发。

mj-agent 私有评估（用户 2026-05-08 brainstorming，私有计划 `glistening-shannon` §C.1.3 / §D.3）将此作为 P0 强烈推荐借鉴项之一。Issue [#76](https://github.com/MJ-AgentLab/mj-agent/issues/76) 是 3-PR 序列（C → A → B）的第 1 步。

## Decision

引入 4 类必触发 + 1 类反例归档判定（mj-system v5.2 §10.1 派生），双轨落地：

**(A) ADR-017（本文件）**：记录决策、派生论证、Alternatives；ADR 不可变（mj-system §3.2 line 184）。

**(B) Meta v2.1 §5.9**（in-place edit，无 version bump）：落规则文本本身，供 reviewer / 作者直接 cite。

**判定表（4+1）**：

| 触发归档？ | 场景 |
|---|---|
| ✅ 是 | 框架大版本升级（如 Meta v2.x → v3.0；trio 整体演进） |
| ✅ 是 | STANDARD 结构性重构（如 12 章 → 5 章模板换代；归档名加 `_pre_<新版本>`） |
| ✅ 是 | 70%+ 内容改写（量化阈值） |
| ✅ 是 | 拆分 / 合并 / 改名（filename / scope 重定义） |
| ❌ 否 | 小修小补、patch 升级、字段补充、typo / 链接修 → git 历史 |

**判定优先级**：4 类必触发条件按列表顺序短路判定（满足任一即触发）。

**与 ADR-011 关系**：本 ADR **不 supersede** ADR-011；仅细化其 §5.6.1 trigger 条款的可执行性。ADR-011 §5.6.2 文件操作步骤、§5.6.3 archive 目录语义、§5.6.4 Living/Frozen 引用判断均保留有效。

**与未来 ADR 关系**：

- ADR-018（待 Phase C-1a 起）将反转 ADR-011 §4.2 filename rule（active 路径稳定化）+ §5.6.2 file move step；本 ADR-017 与之 scope 不重叠（触发 vs filename）
- ADR-019（待 Phase C-1b 起）将引入 archive `[DEPRECATED]_` 前缀 + `archived` / `replaced-by` frontmatter；本 ADR-017 与之 scope 不重叠

## Consequences

**正面**

- 消除 ADR-011 §Consequences "负面"第二条 onboarding 痛点 — 新贡献者直接读 Meta v2.1 §5.9 即可判定
- PR reviewer 可直接 cite §5.9 而非依赖个人经验，降低 review 心智负担
- 4 触发条件可被 PR 模板 A2 自检列表收敛（待 Phase C-1a 时同步 PR_TEMPLATE.md）
- 与 mj-system 文档治理双向兼容（同一规则集，未来 cross-project 协作降摩擦）
- 形成 dogfood 闭环：本 ADR 的落地行为本身（Meta v2.1 in-place 加 §5.9）可对照 §5.9 反例段验证（属字段补充 → 不触发归档）—— 自洽

**负面**

- 70% 阈值仍含主观判断（mj-system 实践证明可工作；Phase 1 末复盘窗口可调整）
- 4 类触发未必穷尽（边界场景仍需 reviewer judgment；mj-system 1 个月使用未发现额外类目）
- 引入新 ADR 增加治理复杂度（边际成本低；同期已有 ADR-014/015/016 落地节奏）

**中性**

- 本 PR 自身**不**触发 §5.9 任一类目（属字段补充 → 反例匹配）—— 自洽 dogfood
- ADR-011 状态不变（active；仅被 cross-ref，不被 supersede）
- mj-system §10.1 同时含 §10.1 触发表 + §10.2 7 步动作清单；本 ADR / Meta v2.1 §5.9 仅借鉴 §10.1 部分；§10.2 动作清单已由 ADR-011 §5.6.2 覆盖（虽未量化），可在 Phase C-1a / C-1b 进一步细化

## Alternatives considered

**A. 改 ADR-011 amendment 段（不起新 ADR）**

内容：在 ADR-011 文末加 "Amendment 2026-05-09" 段引入 4+1 触发表。

拒绝原因：ADRs are "basically immutable" per mj-system §3.2 line 184；mj-agent 沿用此约定。改 ADR-011 违反治理纯度，且 git diff 让历史 ADR 决策点变化与新决策混杂，未来读者难以分清。

**B. 仅在 Meta v2.x 加触发表，不起 ADR**

内容：直接在 Meta v2.1 §5.9 加触发表，无 ADR 决策记录。

拒绝原因：(a) 决策叙述（mj-system 派生 / 70% 阈值合理性 / Alternatives）无落点；(b) 未来读者无法快速理解为什么是 4 而非 3 或 5 个触发；(c) 与 mj-agent ADR governance pattern 不一致（每个治理决策都有 ADR 记录）。

**C. 等 Phase C-1a 时合并落地**

内容：把触发表与 active 路径稳定化、archive 命名规范化合并到一个大 PR。

拒绝原因：用户 2026-05-09 brainstorming 选定 "C → A → B 三步序列"，C-2 先行验证规则后续 PR-2 / PR-3 复用其条款（Phase C-1a archive ceremony 时直接 cite §5.9 trigger #2 "STANDARD 结构性重构"判定 Meta v2.1 → v2.2 是否触发归档）。提前独立落地小 PR 也降低 reviewer 负担。

**D. 把 §10.2 7 步动作清单一并引入 mj-agent**

内容：除 §10.1 触发表外，把 mj-system §10.2 的归档操作 7 步（移位 / 前缀 / frontmatter / banner / INDEX / 反向指针 / docs/rule/INDEX.md 同步）一并落 Meta v2.x。

拒绝原因：scope 扩大 — §10.2 步骤涉及 `[DEPRECATED]_` 前缀 + `archived` / `replaced-by` frontmatter，属 Phase C-1b 范畴。本 ADR 严格限定 §10.1 "什么情况下触发"判定；§10.2 "怎么操作"留 ADR-019 处理。

## References

- 派生源：[mj-system@docs/rule/[STANDARD]_Documentation_Management_Framework.md §10.1](https://github.com/MJ-AgentLab/mj-system/blob/develop/docs/rule/%5BSTANDARD%5D_Documentation_Management_Framework.md) lines 633-641
- 关联 ADR：[[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]（保留 active；本 ADR 不 supersede，仅 cross-ref + 细化 §5.6.1 trigger 可执行性）
- 落地：[[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] §5.9（本 ADR 同步落 STANDARD 文）
- 关联 GitHub Issue：[#76](https://github.com/MJ-AgentLab/mj-agent/issues/76)
- 后续相关 ADR（待 Phase C-1a / C-1b 起）：
  - ADR-018（Phase C-1a，C.1.1）— active 路径稳定化 + filename rule 反转（部分 supersede ADR-011 §4.2）
  - ADR-019（Phase C-1b，C.1.2 + C.2.1）— archive `[DEPRECATED]_` 前缀 + `archived` / `replaced-by` frontmatter（细化 ADR-011 §5.6.2 file move step）
- 用户互动证据：2026-05-08 brainstorming session（plan §C.1.3 / §D.3）+ 2026-05-09 三步序列选定（C → A → B）+ HITL Gate 1 批准（Stage 5）
