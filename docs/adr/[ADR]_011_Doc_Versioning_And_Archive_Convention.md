---
type: adr
domain: SYS
summary: 文档治理新增 Major.Minor 版本演进与 docs/archive/ 归档机制（HITL 触发，A3 模式 = git branch + PR review）
owner: 项目负责人
created: 2026-04-25
updated: 2026-04-25
state: active
decision: accepted
---

# ADR-011: Document Versioning and Archive Convention

## Context

Framework v1.0 §4.2 仅在"多主版本并存"时要求 `_vX.Y` filename 后缀。这在 Phase 0 corpus 中造成不一致：3 份 STANDARD 中 2 份带 `_v1.0`（Framework、Commit Message），但 `[STANDARD]_GitHub_Markdown.md` 不带。同时除 PROMPT 外（v1.0 §5.5 已定义 `docs/design/prompts/` 归档目的地），其他 canonical 类型的 deprecated 版本无显式归档约定——git 是唯一历史机制。

2026-04-25 brainstorming session 明确两条动机：

1. **Filename-as-version-signal**：从文件名一眼识别当前版本，无须打开文件查看 frontmatter `version` 字段
2. **Cite-by-vintage**：未来文档应能写 `[[STANDARD]_X_v1.0|...]]` 并把当时的措辞作为 citable, immutable artifact 永久保留（类比学术引用锁定具体版次）

Browse-without-git **未被** 列入动机——deprecated 版本不需要从工作树消失，仅需 (a) 文件名声明版本 (b) 稳定地址供未来引用。

设计空间沿三个轴评估：

- **命名模式**：in-place coexistence（Approach A）vs archive workflow（Approach B）vs status-quo cleanup（Approach C）—— Q2 选 B
- **粒度**：Major.Minor with archive-on-every-bump（B1）vs major-only（B2）vs grandfather-this-PR（B3）—— Q3 选 B1
- **HITL gate 位置**：predict-at-edit-start（A1）vs file-level draft + completion-time HITL（A2）vs git-branch-as-draft + PR-review HITL（A3）—— Q4 选 A3

组合锁定 **B1 + A3**：filename 携带完整 Major.Minor；正式版本演进时执行 archive 工作流；HITL 判断位于 PR review（不在 edit-start），编辑过程在 feature branch 上 in-place 进行。日常 edit merge as-is；只有 reviewer 判定为"正式版本演进"的改动才触发 §5.6.2 文件操作流程。

## Decision

升级 Framework v1.0 → v1.1，包含以下变更：

| Section | 变更 |
|---|---|
| §4.2 | 把条件性规则"多主版本并存保留 `_vX.Y`"替换为对 `version` 必填类型（STANDARD / SPEC / EVAL / CONTRACT / ASSESSMENT）的强制规则 |
| 新增 §5.6 | 定义 Major.Minor 版本演进与 docs/archive/ 工作流：§5.6.1 PR review HITL 触发；§5.6.2 文件操作步骤；§5.6.3 archive 目录语义；§5.6.4 Living vs Frozen 引用判断 |
| §5.5 | 追加 in-source canonical（SKILL / PROMPT）例外说明：loader 锁定固定 filename，不进入 §5.6 流程 |
| §3.6 | 增加 `docs/archive/<subdir>/` 用途行——仅作版本退役搬迁，不作新文档默认落点 |

承载本规则的 PR 自我应用该规则（eats own dogfood）：

- Framework v1.0 移入 `docs/archive/rule/[STANDARD]_..._Framework_v1.0.md`，state 翻转为 deprecated，body 顶部加 banner 指向 v1.1 与本 ADR
- Framework v1.1 创建于 `docs/rule/[STANDARD]_..._Framework_v1.1.md`，应用所有 amendments，frontmatter bump 至 v1.1
- 14 文件 corpus audit 一次性完成（CLAUDE.md / 4 PR 模板 / INDEX / ASSESSMENT / GitHub_Markdown_v1.0 / Commit STANDARD / ADR-010 / PLAN_E / 2 src docstring / Framework v1.1 自引）—— 全部归类为 living references，升级至 `_v1.1`
- Backfill rename：`[STANDARD]_GitHub_Markdown.md → [STANDARD]_GitHub_Markdown_v1.0.md`（首版无后缀的孤例；first-version 不触发 archive）

新命名规则的适用范围明确：仅适用于 frontmatter `version` 必填的类型。ADR / TEMPLATE / INDEX / POSTMORTEM / ISSUE / GUIDE / RUNBOOK 不受影响。`plans/`（working 层）不受影响。

## Consequences

**正面**

- Filename 自描述当前版本——读者无须打开文件即可识别 vX.Y
- 历史版本以 citable filepath 保留——`[[STANDARD]_X_v1.0|...]]` 永远解析至 archive 副本，不会被 v1.1 silently 取代
- HITL 触发避免日常更新引发的 churn——typo 修复仍然 in-place，零 corpus audit
- A3 模式（git branch + PR review HITL）零新机制——复用既有 git/PR 工作流，不引入文件级 draft 状态
- 显式区分 Living vs Frozen 引用让历史 ADR 与历史 assessment 的"事故时规则状态"段落在概念上获得保护
- 修复了 `[STANDARD]_GitHub_Markdown.md` 的单点不一致

**负面**

- 每次正式版本演进需要 corpus-wide reference audit——本 PR 落地时审计 14 个文件 / 24 处引用
- Living vs Frozen 引用判断依赖作者+reviewer 共识——新外部贡献者需要 onboarding 培训（应包含 Framework v1.1 §5.6 + 本 ADR）
- archive 副本与 git 历史并行存在——存在轻度信息冗余，但符合 cite-by-vintage 显式动机
- §5.6 流程对 mj-agent Phase 0（1 contributor）规模稍重——风险是日常版本演进被规避，长期演进债累积。Mitigation：Framework v1.1 promotion criteria 要求"在第一次非自身正式演进成功执行 §5.6 后"才升至 `state: active`

**中性**

- 本 PR 同时承担了规则的"安装"和"首次执行"——v1.0 → v1.1 自身按 §5.6.2 执行，是规则有效性的端到端演示
- 触发 A6 同步检查：CLAUDE.md §Documentation 段落需更新 Framework 路径与新增 §5.6 说明（本 PR 内一并完成，不留遗留）
- Framework v1.1 初始 state 为 `draft`（与 v1.0 入场一致），promotion 路径见上
- ADR-011 自身是正常 ADR，state: active；ADR 类型不在 §4.2 新规适用范围（无 `version` 字段），filename 沿用 `[ADR]_NNN_Title.md` 模式

## Alternatives considered

**Approach A — Minimal codification + in-place coexistence**

内容：filename `_vX.Y` 强制，但 deprecated 版本与 active 版本同目录共存（仅 `state: deprecated` 区分），不引入 archive workflow。

拒绝原因：用户在 Q2 明确选择 archive workflow（B），并表示对"docs/ 浏览时只显示 latest"无强烈需求但接受 archive 带来的显式归档语义。Approach A 虽然成本更低（无文件移动、无 §3.6 改动），但不满足"versioned old artifacts 应被结构化保留在 docs/archive/"的显式动机表达。

**B2 — Major-only filename granularity**

内容：filename 只带 `_v1`（major），minor 演进 in-place 编辑而不 rename；archive 仅在 v1 → v2 时触发。

拒绝原因：用户在 Q3 明确要求 Major.Minor 完整粒度。B2 节省 ongoing audit 成本但损失 minor 版本的 cite-by-vintage 精度——cite by `[[STANDARD]_X_v1.3]]` 在 B2 下解析不到独立文件，必须 fallback 到 git。

**B3 — Grandfather this PR**

内容：规则安装时 v1.0 → v1.1 在原位置 in-place 编辑（不 rename、不 archive），未来 bump 才执行完整 §5.6.2。

拒绝原因：用户隐式选择"安装时即自我演示"。Q4 答案"B1；但是该操作需要 HITL 进行判断是否执行该正式机制；日常更新不会触发"已经判定本次安装属于"正式机制"。B3 的"豁免本次"会让规则首次落地时缺少端到端验证。

**A1 — Predict-at-edit-start HITL**

内容：作者在编辑前预测此次改动是否为正式版本演进；预测错误则需要中途切换流程。

拒绝原因：用户在 Q4 指出"边界模糊"——预测在编辑过程开始时极难准确（一个 typo 修复可能演化为措辞重写或语义调整）。A3 通过把 HITL 移到 PR review 解决这个问题。

**A2 — File-level draft + completion-time HITL**

内容：始终创建 `[TYPE]_X_v<next>.md` 作为草稿文件，编辑完成时 HITL 决定 promote 或 merge-back-and-delete。

拒绝原因：在 mj-agent Phase 0（1 contributor / 单日 PR）规模下，per-file draft visibility 的收益不抵 per-file overhead；git branch 已经天然提供 draft 语义。Long-form RFC（multi-week 提案）出现时可在 ADR 后续修订中重新评估。

## References

- [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|Framework v1.1（archive）]] §4.2 / §5.5 / §5.6 / §3.6 —— 本决策的执行（v1.1 已归档；后续由 ADR-012 升级至 v2.0 trio）
- [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.0|Framework v1.0（archive）]] —— 被本决策归档的前版本
- [[[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions]] —— Phase 0 governance KEEP/ADAPT/DEFER 模式先例
- [[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|MJ System Git Conventions Adoption Assessment v1.0]] —— 同期 governance 评估文档
- [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0|MJ-Agent Commit Message Convention v1.0]] —— Phase 0 governance peer
- 用户互动证据（2026-04-25 brainstorming session）：Q1 motivations（filename-signal + cite-by-vintage，NOT browse-without-git）/ Q2 approach（B）/ Q3 granularity（B1 + HITL）/ Q4 HITL gate（A3 = git branch + PR review）；ExitPlanMode 批准
