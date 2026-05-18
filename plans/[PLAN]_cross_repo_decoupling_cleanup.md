---
type: plan
summary: 5-PR bundle (✅ completed retroactive) — mj-agent 文档治理框架的跨仓引用解耦 cleanup（HITL_Prompt 镜像归档 + STANDARD/ADR prose 中性化 + 9 ADR archive + ADR-025 三拆 026/027/028 + glossary 元文档段建立）；2026-05-11 02:44-04:47 实施期 5 PR 漏落盘 plans/，2026-05-18 retroactive 补救
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-18
completed: 2026-05-11
state: completed
track: shared
retroactive: true
---

# [PLAN] mj-agent Cross-Repo Decoupling Cleanup（5-PR bundle, retroactive）

> [!warning] **Retroactive 落盘说明**
>
> 本 PLAN 文件由 2026-05-18 事后回填，**非真实 Stage 4 输出**。5 PR 实施期间未按 [[../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt]] §3.2 在 `plans/` 落盘 [PLAN]_*.md，事后补救。内容来源：5 PR description + commit log + memory `project_cross_repo_decoupling_completion.md` + vault `~/.claude/plans/mj-agent-derived-from-crispy-marble.md`（plan-mode artifact，不入 git）。
>
> Stage 4 落盘漏的根因 + 长效补落机制见 [[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11.6 Retroactive 补落 working 文档。

## Context

mj-agent 文档治理框架在 bootstrap 阶段曾参考 mj-system 实践沉淀（HITL_Prompt 镜像版本 + Documentation Meta Framework 派生 + 5-branch type 模型 + worktree-per-branch + ADR 系列）。bootstrap 完成后框架已独立成熟，但 **~35 份 canonical docs 仍含 ~65 处 mj-system inline refs**（prose + frontmatter `derives_from`），未来仓库分离/归档 + 新读者独立阅读叙事均有阻力。

**用户决策**（2026-05-10/05-11 brainstorming，vault `~/.claude/plans/mj-agent-derived-from-crispy-marble.md`）：

1. **集中而非散布**：`derives_from` frontmatter 全删；prose attribution 集中到新 glossary `[GLOSSARY] upstream_business_warehouse` 元文档段（"如何引用上游业务系统"，定义唯一 inline URL 例外）
2. **保留 runtime literal**：`mj-system-backend-network` Docker network / `mj-postgres` 容器 / `MJ_SYS_*` env / `pg-mj-system-biz-*` MCP server 名保留作真实部署对象的精确引用（per D2 keep-runtime-fact 决策）
3. **ADR-025 三拆**：multi-env + DGX + MCP bundle 跨 3 主题 → 拆 ADR-026/027/028 单主题
4. **9 ADR batch archive**：决策已沉淀到 framework STANDARD 段（ADR-017/018/019/021/022/023 → Meta v2.2；ADR-010/015 → STANDARD 主体 inline）
5. **forward guard warning-mode**：4 周观察期 → 后切 strict（env switch `MJ_AGENT_CHECK_REFS_STRICT=1`）；剩余 ~10-90 warnings 留 Phase E+

**决策为何在 1 日完成 5 PR**：plan §11 sequence 在 2026-05-11 02:44 启动后顺序推进；中间无 review 阻塞（所有 PR 由 user 即时 approve），形成 02:44 → 04:47 紧凑 2h 03min 5 PR 链。

## Scope（5 PRs sequential）

### PR-A: `documentation/decouple-hitl-prompt-plus-strip-derives-from`（[#118](https://github.com/MJ-AgentLab/mj-agent/pull/118)，merged 2026-05-11 02:44Z）

**首批 / 28 files / +746/-112 lines**。承载两个 commits：

- **HITL_Prompt v1.0 主体重写**（3 files）：frontmatter `derives_from` + summary 末"派生自 mj-system v1.0" 删；§0 prelude block 重写为 "mj-agent 关键设计约束"；§4 占位符 `mj-system@docs/rule/...` → 本规范段引 + in-tree SKILL；§4.6/§4.9/§4.13/§4.15 cross-repo SPEC-authoring 5 处 → `docs/_templates/TEMPLATE_SPEC.md`；§4.8/§5.4 runtime fact prose → "上游业务系统..."；§6 verbatim 标记 + References tail 全清；framework 版本号同步（Meta v2.1 → v2.2，Code_Side v1.0 → v1.1，Agent_Side v1.0 → v1.2）；References 末段加 in-tree SKILL 关联（6 个 active skills）
- **全仓 derives_from strip + forward guard**（22 files）：12 active docs frontmatter `derives_from:` 全删 + 7 templates frontmatter + body `> **派生自**：` 提示文本全删；INDEX.md 3 处机械清理；`scripts/check_frontmatter.py` 加 `FORBIDDEN_FIELDS = {"derives_from"}` forward guard + archive 路径豁免（per ADR-019）
- 同期 commit 加 `docs/_templates/TEMPLATE_REPO_SCAN_RESULT.md` + `TEMPLATE_PLAN.md` + SPEC Authoring inline

### PR-Β: `documentation/neutralize-prose-cross-repo-refs`（[#121](https://github.com/MJ-AgentLab/mj-agent/pull/121)，merged 2026-05-11 03:14Z）

**第 2 批 / 17 files / +160/-172 lines**。中风险 prose 中性化层：

- **ADR rewrites（3 files）**：
  - `git mv [ADR]_008_Co_Deployment_With_MJ_System.md` → `[ADR]_008_Co_Deployment_With_Upstream_Warehouse.md` + body 整体重写
  - ADR-006 / ADR-009 prose 3/4 处中性化（mj-system biz 域 / analyst 角色 / schema 变更 / 治理 / R__analyst_permissions.sql 文件引用）+ §Context cross-ref 新 glossary
- **STANDARD prose softening（3 files）**：Meta v2.2 14 处 / Commit_Convention v1.0 6 处 / MCP_Governance §5/§6/§7 多处
- **Wikilink + display text bulk update（11 dependent files）**：ADR-008 rename 触发 cross-repo wikilink 同步（config/README.md、ADR-010、ADR-025、INDEX.md、ASSESSMENT、glossary self-fix、MCP Governance、HITL_Prompt、3 份 SKILL）

### PR-Γ: `documentation/archive-9-adrs-plus-split-adr-025-plus-forward-guard`（[#122](https://github.com/MJ-AgentLab/mj-agent/pull/122)，merged 2026-05-11 03:38Z）

**核心批 / 18 files / +717/-86 lines**。最高风险的批量 archive + 拆分：

- **9 ADR archive ceremony（per ADR-019）**：`git mv` 到 `docs/archive/adr/[DEPRECATED]_*` + frontmatter `state: deprecated` + `archived: 2026-05-11` + `replaced-by: <stable-path>` + body frozen snapshot
  - ADR-010 / ADR-015 / ADR-017 / ADR-018 / ADR-021 / ADR-022 / ADR-023 / ADR-025 / **ADR-019 (LAST)** — ADR-019 自身最后归档（依赖其约定走完全程）
- **ADR-025 split → 3 new mj-agent-native ADRs**：
  - **ADR-026** Multi-Environment Compose Profile — docker-compose 4-file 分层 + dev quirk
  - **ADR-027** LLM Provider Abstraction — `make_llm()` factory + DGX vLLM 消费侧
  - **ADR-028** MCP Server Inventory + Governance — `.mcp.json` 13 servers + 领域专属 STANDARD + A14
- **Supporting infrastructure**：
  - `docs/archive/adr/INDEX.md` — 9 archived ADR forward gateway
  - `docs/_baselines/pg_server_baseline.md` — wrapper script 内部基线（替代 "vs mj-system upstream"）
  - `scripts/check_no_cross_repo_refs.py` — forward guard（warning-mode；env switch 转 strict）
  - `.github/workflows/ci.yml` — 新 step "No cross-repo refs"
- **INDEX.md restructuring** + **CLAUDE.md cleanup**（项目起源说明 prelude + data boundary 段 + ADR list cleanup）

### PR-Δ: `documentation/tail-cleanup-cross-repo-refs`（[#123](https://github.com/MJ-AgentLab/mj-agent/pull/123)，merged 2026-05-11 03:48Z）

**Tail cleanup / 20 files / +82/-85 lines**。把 forward guard 从 170+ → ~10 warnings：

- Bulk neutralization `mj-system` → `上游业务系统` 在 prose（保留代码层 literal）：5 templates + 2 runbooks + 4 git GUIDEs + 3 INDEX + 4 STANDARDs + README.md + docs/INDEX.md
- 留余 ~10 warnings 留 Phase E+：changelog 历史行 + Agent_Side/Code_Side self-link + Developer_Onboarding/Analyst_Day_One placeholder + ADR-012/014/016 Context heritage + ASSESSMENT_MJ_System_Git_Conventions_Adoption（评估对象精确引用）

### PR-E: `documentation/glossary-meta-doc-plus-adr-020-wikilink`（[#124](https://github.com/MJ-AgentLab/mj-agent/pull/124)，merged 2026-05-11 04:47Z）

**Glossary 元文档段 / 2 files / +50/-7 lines**。Cleanup 收口：

- `docs/glossary/upstream_business_warehouse.md` 加新段 **"§如何引用上游业务系统（mj-system）"**：定义 mj-agent active 文档**唯一允许**含 mj-system inline URL 的位置（元文档例外）；含 仓库定位 / Branch/Ref 选择规则（SHA / develop / main / 不放 URL 4 场景）/ 最小化原则 / 例外 / forward guard 5 子段
- ADR-020 inline URL → wikilink to glossary（7 处改动 — frontmatter tag delete + 5 prose 改写 + 1 URL → wikilink）

设计意图（用户 2026-05-11 brainstorming 校正）：**集中**到元文档（一处定义，wikilink 引用），不是 D1 v1 误读的"散布"；MJ-AgentLab 内同团队无访问障碍；main vs develop 选择规则**显式编码**而非禁令。

## 严格守约（Out-of-Scope）

| 决策 | 范围 | 理由 |
|---|---|---|
| 保留 `mj-system-backend-network` 等 runtime literal | Docker network 名 / 容器名 / `MJ_SYS_*` env / `pg-mj-system-biz-*` MCP server / `R__analyst_permissions.sql` 文件名 | D2 keep-runtime-fact 决策；real deployment object 精确引用 |
| ADR-006/008/009 Context 保留部分 mj-system 引用 | ADR Context 段说明历史动因 | ADR 本质是不可逆决策记录；Context 必然描述启发源 |
| Phase E+ 残留 ~10-90 warnings 不强清 | changelog 历史行 + self-link + ASSESSMENT 评估对象 | warning-mode 容忍；strict 切换 4 周观察后再议 |
| `ASSESSMENT_MJ_System_Git_Conventions_Adoption_v1.0` 保留 mj-system 出现 | source 列表是评估对象 | 评估报告本身就是评估上游 git 规范 |
| 不动 ADR-008 之外的 ADR 文件名 | rename 只做 ADR-008 | 命中"Co_Deployment_With_MJ_System" → "Upstream_Warehouse"；其他 ADR 文件名中性 |

## HITL Gates

**Stage 5 Plan-mode（事后回填）**：3 决策点已答（详见 `[INTAKE]_cross_repo_decoupling_cleanup.md` §6）：
- **Q1 attribution 集中 vs 散布 vs 删除** → 集中到 glossary 元文档（PR-E #124 落地）
- **Q2 ADR-025 单一 vs 三拆** → 三拆为 026/027/028（PR-Γ #122 落地）
- **Q3 forward guard strict vs warning** → warning-mode 4 周观察 + env switch（PR-Γ #122 落地）

**Stage 7 SPEC-design**：N/A（documentation track 无 SPEC）

**Stage 11 Self-review**：每 PR self-check A1-A14 tri-track checklist 已逐 PR 在 PR body 完成

**Stage 13 Push / Review-CI**：5 PR 全部 CI 绿（check_frontmatter + check_wikilinks + check_no_cross_repo_refs warning-mode）

## 关键 ADR / STANDARD 引用

**新增 ADR**（active）：
- [[../docs/adr/[ADR]_026_Multi_Environment_Compose_Profile|ADR-026]]
- [[../docs/adr/[ADR]_027_LLM_Provider_Abstraction|ADR-027]]
- [[../docs/adr/[ADR]_028_MCP_Server_Inventory_And_Governance|ADR-028]]

**重命名 ADR**：
- [[../docs/adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse|ADR-008]]（from `Co_Deployment_With_MJ_System`）

**Archive 9 ADRs**：
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_010_Adopt_MJ_System_Git_Conventions|ADR-010]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_015_AI_Engineering_Execution_HITL_Prompt_Source|ADR-015]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_017_Document_Stale_Risk_And_Re_Promote|ADR-017]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_018_Active_Path_Stability|ADR-018]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_019_Archive_And_Frozen_Snapshot|ADR-019]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_021_Working_Document_Lifecycle|ADR-021]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_022_Canonical_Type_Adoption_Roadmap|ADR-022]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_023_Stale_Doc_And_Plan_GC_Infra|ADR-023]]
- [[../docs/archive/adr/[DEPRECATED]_[ADR]_025_Multi_Env_DGX_MCP_Bundle|ADR-025]]

**STANDARD 主体修改**：
- [[../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.0]]（镜像归档 + §0/§4/§6 大段重写）
- [[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]]（path stability + working doc lifecycle）
- [[../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]
- [[../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.2]]
- [[../docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit_Convention v1.0]]
- [[../docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance|MCP_Server_Governance]]
- [[../docs/rule/[STANDARD]_GitHub_Markdown|GitHub_Markdown]]

**新增 Glossary**：
- [[../docs/glossary/upstream_business_warehouse|GLOSSARY upstream_business_warehouse]]（含 PR-E 加入 §如何引用上游业务系统）

**Scripts 修改**：
- `scripts/check_frontmatter.py`（FORBIDDEN_FIELDS guard）
- `scripts/check_wikilinks.py`（auto-discover NEEDLES per ADR-020）
- `scripts/check_no_cross_repo_refs.py`（新；warning-mode）

## 进度（事后 = 全部 ✅）

| Step | 状态 | 完成时间 |
|---|---|---|
| PR-A #118 HITL_Prompt 解耦 + derives_from strip | ✅ merged | 2026-05-11 02:44Z |
| PR-Β #121 STANDARD/ADR prose 中性化 | ✅ merged | 2026-05-11 03:14Z |
| PR-Γ #122 9 ADR archive + ADR-025 三拆 + forward guard | ✅ merged | 2026-05-11 03:38Z |
| PR-Δ #123 tail cleanup | ✅ merged | 2026-05-11 03:48Z |
| PR-E #124 glossary 元文档段 + ADR-020 wikilink | ✅ merged | 2026-05-11 04:47Z |
| **Bundle 闭环** | ✅ | 2026-05-11 04:47Z（2h 03min total） |
| **Retroactive INTAKE/PLAN 补落** | ✅ | 2026-05-18（本 PR） |

## 累计成果（bundle 收尾）

- ✅ 9 个 ADR archive + 3 个新 ADR 创建（ADR-008 rename）
- ✅ ~65 处 mj-system inline refs 减至 ~10-90 warnings（warning-mode 容忍；Phase E+ 续清）
- ✅ HITL_Prompt v1.0 主体重写为独立 mj-agent native
- ✅ Meta v2.2 + Code_Side v1.1 + Agent_Side v1.2 framework 升级
- ✅ Glossary 元文档段建立（"§如何引用上游业务系统"）
- ✅ Forward guard 部署（check_no_cross_repo_refs.py + CI workflow）
- ✅ check_wikilinks.py auto-discover NEEDLES（ADR-020 落实，零维护 archive 引用校验）
- ✅ CLAUDE.md 重大 cleanup（项目起源说明 prelude + data boundary 段 + ADR list cleanup）

**未来防漏机制**（2026-05-18 retroactive 补落同期）：
- ✅ [[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11.6 Retroactive 补落 working 文档段（触发 3 条件 + 补落规则 + 落地记录区）
- ⚠️ Stage 4 Plan body 落盘 SKILL §4.5 硬性 gate（per HITL_Prompt §3.2 实施时漏；独立 follow-up 评估，参考 PR #163 PreToolUse hook 模式）

---

## Trace 凭证段（retroactive 必备）

| 段 | 凭证来源 |
|---|---|
| Context | vault `~/.claude/plans/mj-agent-derived-from-crispy-marble.md` §决策点 + memory `project_cross_repo_decoupling_completion.md` + `CLAUDE.md "项目起源说明（2026-05-11 update）"` 段 |
| Scope（5 PR sub-sections） | 5 PR description 全文 + commit log + `gh pr view` 输出 |
| 严格守约 | 5 PR PR body "保留代码层 literal" 段 + "留余 warnings" 段 |
| HITL Gates | vault plan §决策点 Q1/Q2/Q3 原文 + [[[INTAKE]_cross_repo_decoupling_cleanup|INTAKE]] §6 |
| 关键引用 | 当前 develop branch 状态 `ls docs/adr/` + `ls docs/archive/adr/` 实测 |
| 进度 | `gh pr list --state merged --search "#118 OR ..."` 时间戳 |
| 累计成果 | 5 PR body §验证 段 + 当前 `scripts/check_*.py` 实测结果 |

## Cross-ref

- [[[INTAKE]_cross_repo_decoupling_cleanup|[INTAKE] 同任务 Intake 文件]]（同期 retroactive 落盘）
- [[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11.6（retroactive 补落条款 + 首次落地记录）
- [[../docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt]] §3.2 Stage 4 豁免 / §4.15 Rule 12 PR-state 联动
- [[[PLAN]_multi_env_dgx_mcp_bundle|[PLAN]_multi_env_dgx_mcp_bundle]]（mj-agent native 4-PR bundle 范本；本 PLAN 结构 mirror 此先例）
- [[[PLAN]_g1_g2_workflow_enforcement|[PLAN]_g1_g2_workflow_enforcement]]（PreToolUse hook 防漏先例；本 retroactive §累计成果"未来防漏机制" 参考其模式）
