---
type: standard
domain: SYS
summary: archive/decisions/superseded/ 归档 ADR 索引 + forward gateway；列出 9 个由 cross-repo decoupling cleanup 批量归档的 ADR + 各自 replaced-by 指向
owner: 项目负责人
created: 2026-05-11
updated: 2026-06-03
state: active
track: shared
note: 2026-06-03 (M5-PR3b) 由 docs/archive/adr/ 平移至 archive/decisions/superseded/；相对链接已按新深度重算
---

# Archived ADRs Index

> 本目录归档了 9 个 "记录从早期内部上游系统继承设计决策" 的 ADR。当前 active framework STANDARD 已独立维护决策本体；如需追溯设计起源（"为什么继承了某条规则"），见各 archived ADR 的 Context/Decision 段。
>
> Archive 操作于 2026-05-11 由 PR-Γ（cross-repo cleanup 收尾批次）一次性完成；archive 命名 + frontmatter 规则按 ADR-019 主条款（本 ADR 自身在序列最后 archive）。Body 内部 wikilinks **不更新**（frozen snapshot 原则）。

## 归档清单

| Archived ADR | Replaced-by | 归档原因 |
|---|---|---|
| [[[DEPRECATED]_[ADR]_010_Git_And_Commit_Conventions_From_MJ_System\|ADR-010 Git and Commit Conventions]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention\|Commit Message Convention v1.0]] | git/commit 规则已独立 STANDARD 化；Keep/Adapt/Defer 矩阵决策已落地 |
| [[[DEPRECATED]_[ADR]_015_HITL_Prompt_v1_0_Derivation\|ADR-015 HITL_Prompt v1.0 Derivation]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt\|HITL_Prompt v1.0]] | HITL 17-stage 闭环规则已独立 STANDARD 化；§4.1/§4.4 内联完成（PR #118） |
| [[[DEPRECATED]_[ADR]_017_Archive_Trigger_Quantification\|ADR-017 Archive Trigger Quantification]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.2]] §5.9 | 4 必触发判定条款已并入 Meta v2.2 §5.9 |
| [[[DEPRECATED]_[ADR]_018_Active_Path_Stability\|ADR-018 Active Path Stability]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.2]] §4.4 | active 文件名稳定原则已并入 Meta v2.2 §4.4 |
| [[[DEPRECATED]_[ADR]_019_Archive_Naming_Convention\|ADR-019 Archive Naming Convention]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.2]] §5.11 + 本 INDEX | 归档命名 [DEPRECATED]_ 前缀 + frontmatter 规则已落地为日常实践；本 PR-Γ 全程依赖该约定（最后 archive） |
| [[[DEPRECATED]_[ADR]_021_Working_Doc_Lifecycle\|ADR-021 Working Doc Lifecycle]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.2]] §5.11 | plans/ 4 态机已并入 Meta v2.2 §5.11；mj-agent-flow-post-merge SKILL Step 9 自动 active → completed |
| [[[DEPRECATED]_[ADR]_022_P2_Framework_Enhancements\|ADR-022 P2 Framework Enhancements]] | [[../../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.4-§3.8 + [[../../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta v2.2]] §3.7/§3.8/§4.5/§4.6 | 5 项 framework 增强已并入对应 STANDARD 章节 |
| [[[DEPRECATED]_[ADR]_023_Stale_Doc_And_Plan_GC_Infra\|ADR-023 Stale Doc + Plan GC Infrastructure]] | `scripts/find_stale_docs.py` + `scripts/find_old_completed_plans.py` 注释 | 实际 scripts 已落地；ADR 决策叙事归档 |
| [[[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction\|ADR-025 Multi-Env + DGX + MCP Bundle]] | [[../ADR-026_Multi_Environment_Compose_Profile\|ADR-026]] + [[../ADR-027_LLM_Provider_Abstraction\|ADR-027]] + [[../ADR-028_MCP_Server_Inventory_And_Governance\|ADR-028]] | 多 domain bundle ADR 拆分为 3 个 mj-agent 原生焦点 ADR |

## 阅读注意

- 归档文件 frontmatter 含 `state: deprecated` + `archived: 2026-05-11` + `replaced-by`
- 文件名加 `[DEPRECATED]_` 前缀 + 保留原 ADR 编号（cite-by-vintage）
- Body 是 frozen snapshot：不更新内部 wikilinks（archive 内对其他 archived / active 文件的 wikilinks 可能 404；属预期）
- 为追溯当前活跃决策，按本表 `Replaced-by` 列直接跳转

## 关联

- [[../../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.2]] §5.11.5（archived 物理归档实施指引）
- `scripts/check_wikilinks.py`（auto-discover archived 文件名 + 验证 living/frozen 引用规则）
- `scripts/check_no_cross_repo_refs.py`（forward guard；本目录豁免）
