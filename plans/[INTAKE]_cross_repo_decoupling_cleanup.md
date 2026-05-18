---
type: intake
summary: 2026-05-11 cross-repo decoupling cleanup（PR-A/-Β/-Γ/-Δ/-E 共 5 PR / 2h 03min / 85 文件 / +1755/-462 lines）的 retroactive Stage 0 Intake；首份 mj-agent [INTAKE]_* 范本
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-18
completed: 2026-05-11
state: completed
track: shared
retroactive: true
---

# [INTAKE] Cross-Repo Decoupling Cleanup (retroactive)

> [!warning] **Retroactive 落盘说明**
>
> 本 INTAKE 文件由 2026-05-18 事后回填，**非真实 Stage 0 输出**。时间线、HITL Questions、Documentation Decision 等内容均按 5 PR description（#118/#121/#122/#123/#124）+ memory `project_cross_repo_decoupling_completion.md` + `CLAUDE.md "2026-05-11 update"` 段重建。
>
> 本文件用作 mj-agent `plans/[INTAKE]_*` 的首个落地范本（项目历史 0 个 [INTAKE] 文件）；建议**未来同类任务的 Stage 0 落盘参考其结构**，但**不**作为"标准模板"使用——标准模板见 `.claude/skills/mj-agent-flow-intake/SKILL.md` §Output Format。
>
> 详见 [[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11.6 Retroactive 补落 working 文档。

---

## 1 Task Classification

- **Type**: documentation
- **Base branch**: develop
- **估计影响范围**：
  - 5 个 framework 类 STANDARD（HITL_Prompt / Meta / Code_Side / Agent_Side / Commit_Convention / MCP_Governance / GitHub_Markdown）
  - 9 个 ADR archive ceremony（010/015/017/018/019/021/022/023/025）+ 3 个新 ADR 创建（026/027/028）
  - ADR-008 rename（Co_Deployment_With_MJ_System → Upstream_Warehouse）
  - 1 个新 glossary（upstream_business_warehouse.md + 元文档段）
  - 7 个 templates + 12 个 active docs frontmatter `derives_from` strip
  - 4 git GUIDEs + 2 onboarding GUIDEs + 1 RUNBOOK + GitHub_Markdown prose 中性化
  - scripts/check_frontmatter.py (FORBIDDEN_FIELDS guard) + scripts/check_no_cross_repo_refs.py (新 forward guard) + scripts/check_wikilinks.py (auto-discover NEEDLES)
  - CLAUDE.md 重大 cleanup（"项目起源说明" prelude + data boundary 段 + ADR list cleanup）
  - .github/workflows/ci.yml 加 "No cross-repo refs" step

## 2 Risk Assessment

- **Level**: **High**
- **触发 §3.1 必停项**（通用 9 + mj-agent 专属 4）：
  - **#6 生产配置/CI-CD/部署**（命中：`scripts/check_no_cross_repo_refs.py` + `.github/workflows/ci.yml` 新 CI step；warning-mode → 4 周后 strict-mode env switch）
  - **#7 公共 API / 用户可见行为** — 弱命中（active path stability 影响 wikilink 解析；ADR-008 rename 影响外部 reference）
  - **#10 runtime-skill-content-change** — 弱命中（仅修改 `.claude/skills/mj-agent-infra-{storage-stack,env-teardown,docker-compose}/SKILL.md` 内 wikilink display；不动 description / 反向触发段；A12 description quality gate 未触发）
- **升档原因**：
  - 跨 9 ADR archive + 3 新 ADR 创建（archive ceremony 是 ADR-019 governed 不可逆操作）
  - 改 Track C primary STANDARD HITL_Prompt 主体（含 §0/§4/§6/References 大段重写）
  - Meta v2.1 → v2.2 framework 升级（active path stability）
  - CLAUDE.md 是 LLM 高频上下文，跨段重写影响所有后续 session

## 3 Documentation Decision（粗评，事后回填）

| 类型 | 操作 | 落地文件 |
|---|---|---|
| Plan | Create | **未落盘**（本 retroactive 即是补救；plan-mode artifact 在 `~/.claude/plans/mj-agent-derived-from-crispy-marble.md` 内部 trace 充分，但 mj-agent repo `plans/` 漏落） |
| SPEC | None | — |
| ADR | Archive 9 + Create 3 | ADR-026/027/028 from ADR-025 split；ADR-010/015/017/018/019/021/022/023/025 archive |
| RUNBOOK | None | — |
| GUIDE | Update | dev_studio_walkthrough / dev_deployment / Git_*（4 个） |
| STANDARD | Update | HITL_Prompt（主体重写）/ Meta v2.1→v2.2 / Code_Side v1.0→v1.1 / Agent_Side v1.0→v1.2 / Commit_Convention v1.0 / GitHub_Markdown / MCP_Governance |
| Local ISSUE | None | — |
| ASSESSMENT | None | — |
| CHANGELOG | None | mj-agent 无 CHANGELOG.md 治理（per Code_Side §0） |
| INDEX | Update | `docs/INDEX.md` 多处 + 新建 `docs/archive/adr/INDEX.md` |
| Glossary | Create | `docs/glossary/upstream_business_warehouse.md`（含 PR-E 加入的 §如何引用上游业务系统 元文档段） |
| Scripts | Update | `check_frontmatter.py` + `check_wikilinks.py` + 新建 `check_no_cross_repo_refs.py` + 新建 `pg_server_baseline.md` |
| CLAUDE.md | Update | "项目起源说明" prelude + data boundary 段 + ADR list cleanup |

## 4 Issue Draft

**N/A** — 任务从用户 2026-05-10 brainstorming 直接发起（外部 vault plan `mj-agent-derived-from-crispy-marble.md`），**未创建 GitHub Issue**。

按 `[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §5，documentation track 允许无 issue 直接走 PR；本任务 5 PR 均无 `Closes #N` 行（commit message + PR body 已含完整 motivation + scope + verification）。

## 5 Verification Plan（事后 = git/grep 重建）

| Level | 检查 | 命令 | 期望（事后） |
|---|---|---|---|
| A read-only | 5 PR 全部 merged | `gh pr list --state merged --search "#118 OR #121 OR #122 OR #123 OR #124"` | 5 PR all merged 2026-05-11 |
| A read-only | 9 ADR archived | `ls docs/archive/adr/[DEPRECATED]_*.md` | 9 个 `[DEPRECATED]_*` 文件（含 ADR-019 self-archive） |
| A read-only | 3 新 ADR active | `ls docs/adr/[ADR]_02{6,7,8}_*.md` | 3 文件存在，state=active |
| A read-only | ADR-008 rename 完成 | `ls docs/adr/[ADR]_008_*.md` | 命中 `Co_Deployment_With_Upstream_Warehouse`，非 `Co_Deployment_With_MJ_System` |
| A read-only | `derives_from` 仅在 archive | `grep -r "^derives_from:" docs/` | 仅命中 `docs/archive/` 内 |
| A read-only | check_frontmatter.py | `uv run python scripts/check_frontmatter.py` | OK 89 canonical docs |
| A read-only | check_wikilinks.py | `uv run python scripts/check_wikilinks.py` | 0 violations（16 archived files auto-discovered） |
| A read-only | check_no_cross_repo_refs.py | `uv run python scripts/check_no_cross_repo_refs.py` | warning-mode active；~90 warnings 计数稳定（Phase E+ 容忍） |
| A read-only | glossary 元文档段 | `grep "§如何引用上游业务系统" docs/glossary/upstream_business_warehouse.md` | 命中 |

## 6 HITL Questions（3 个，事后回填）

> 以下 3 个 HITL Questions 在实际 brainstorming 中已答（2026-05-10/05-11），凭证来源：vault plan `mj-agent-derived-from-crispy-marble.md` §决策点 + memory `project_cross_repo_decoupling_completion.md`。

### Q1：是否保留 mj-system attribution？

- **当前观察**：mj-agent 文档治理框架在 bootstrap 时参考 mj-system 实践；35 份 canonical docs 含 ~65 处 mj-system inline refs（prose + frontmatter `derives_from`）
- **不确定点**：完全删除引用 vs 集中到元文档 vs 保留原状
- **为什么重要**：影响学术诚信 + 跨仓引用风险 + 未来仓库分离/归档准备
- **可选方案**：
  - A. 完全删除（去除所有 mj-system literal + derives_from）
  - B. 集中到 glossary 元文档（active docs 不允许 inline URL；元文档定义唯一例外）
  - C. 保留 status quo
- **我的建议**：B
- **默认假设**：B（学术诚信 + 强化独立叙事 双赢）
- **是否必须等待人工确认**：是
- **答**：**B — 集中到 glossary `[GLOSSARY] upstream_business_warehouse` 元文档，prose 用 "上游业务系统" 中性术语；代码层 literal（`mj-system-backend-network` Docker network / `mj-postgres` 容器 / `MJ_SYS_*` env / `pg-mj-system-biz-*` MCP server）保留作真实部署对象的精确引用**（PR-E #124 完成元文档段 + Branch 选择规则）

### Q2：ADR-025（多环境 + DGX + MCP bundle）是否拆？

- **当前观察**：ADR-025 一个 ADR 承载 3 主题（multi-env compose / LLM provider / MCP governance）
- **不确定点**：单 ADR 跨主题 vs 三 ADR 单主题
- **为什么重要**：ADR 是不可逆决策记录；单 ADR 跨主题不利于事后追溯
- **可选方案**：
  - A. ADR-025 拆为 026/027/028 三个单主题 ADR
  - B. 保留 ADR-025 单一
- **我的建议**：A
- **默认假设**：A
- **是否必须等待人工确认**：是
- **答**：**A — 拆为 ADR-026 (multi-env compose) / ADR-027 (LLM provider) / ADR-028 (MCP governance)；ADR-025 archive 到 `docs/archive/adr/[DEPRECATED]_[ADR]_025_*`**（PR-Γ #122 完成）

### Q3：forward guard 用 strict vs warning？

- **当前观察**：本次 cleanup 后仍有 ~10-90 残留 warning（changelog 历史行 + intra-mj-agent self-link）
- **不确定点**：是否阻塞性 strict CI
- **为什么重要**：strict 模式会让历史 warning 阻塞所有未来 PR；warning 模式延迟收口
- **可选方案**：
  - A. strict 模式立即生效
  - B. warning-mode 4 周观察期 → 后切 strict（env switch `MJ_AGENT_CHECK_REFS_STRICT=1`）
  - C. 永久 warning-mode
- **我的建议**：B
- **默认假设**：B（mirror `find_stale_docs.py` 4 周观察 pattern）
- **是否必须等待人工确认**：是
- **答**：**B — warning-mode 默认 + env switch 转 strict；4 周观察期；剩余 warnings 留 Phase E+**（PR-Γ #122 落地 warning-mode；strict 切换计划见 §2 PR-Γ verification）

## 7 §2.1 落盘判定（retroactive 标注）

- **是否落盘 plans/[INTAKE]_*.md**：**是**（本文件即落盘产物，但 retroactive=true）
- **触发条件**（事后判定，按 SKILL §2.1 6 项）：
  - ✅ Risk Level = **High**（§2 评估）
  - ✅ 涉及多模块（>2 个 7 模块 — STANDARD / ADR / GUIDE / glossary / scripts / CLAUDE.md / .github CI）
  - ✅ 涉及多迭代周期（5 PR sequential 跨 2h）
  - ❌ in-source canonical（未触 `src/mj_agent/skills/**/SKILL.md` 或 `prompts/system.md` body）
  - ❌ biz catalog（未触 `qcm_catalog.yaml`）
  - ❌ HITL 触发点 ≥3 个（虽然 §6 有 3 Q，但属信息确认型 HITL，未到必停级别）
- **落盘原因**：3 项触发条件足够（Risk=High + 多模块 + 多 PR）；按 SKILL §2.1 应在 Stage 0 落盘 — **实施时漏，本 retroactive 即补救**
- **建议路径**：`plans/[INTAKE]_cross_repo_decoupling_cleanup.md`（即本文件）

### Next Step（已完成历史）

- ✅ Stage 1 GitHub Issue Draft — **跳过**（documentation track + 无 Issue 模板，per CommitConvention §5）
- ✅ Stage 2 Branch / Worktree — 5 个 worktree 各承载 1 PR
- ✅ Stage 3 Repo Scan — vault plan §3 已完成
- ✅ Stage 4 Plan body 落盘 — **漏**（同时 retroactive 补救 `plans/[PLAN]_cross_repo_decoupling_cleanup.md`）
- ✅ Stage 5-17 — 5 PR 已按 G1/G2 流程实施 + merged

---

## 8 凭证 trace（retroactive 必备段）

| 段 | 凭证来源 |
|---|---|
| §1 Task Classification | 5 PR title + diff stat + memory `project_cross_repo_decoupling_completion.md` |
| §2 Risk Assessment | 5 PR body Self-check sections（A1-A14 checklist） + memory + vault plan §决策点 |
| §3 Documentation Decision | 5 PR diff stat + `git log --name-status PR_SHA` 重建 |
| §4 Issue Draft N/A | `gh pr list --search` 确认 5 PR 均无 `Closes #N`（仅 PR-Β #121 / PR-Γ #122 / PR-Δ #123 PR-body 提及"承接 PR #118" sequential reference） |
| §5 Verification Plan | 5 PR body §Verification 段 + 当前 develop branch 状态实测 |
| §6 HITL Questions | vault plan `mj-agent-derived-from-crispy-marble.md` §决策点（Q1/Q2/Q3 决策原文）+ memory |
| §7 §2.1 落盘判定 | SKILL.md §2.1 6 项触发条件对照本次 scope 重判 |

---

## 9 Cross-ref

- [[[PLAN]_cross_repo_decoupling_cleanup|[PLAN] 同任务 PLAN 文件]]（同期 retroactive 落盘）
- [[../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11.6 Retroactive 补落 working 文档
- [[../.claude/skills/mj-agent-flow-intake/SKILL]] §2.1 落盘判定（6 项触发条件）
- [[../docs/glossary/upstream_business_warehouse|GLOSSARY upstream_business_warehouse]]（PR-E 加入 §如何引用上游业务系统 元文档段）
- [[../docs/adr/[ADR]_019_Archive_And_Frozen_Snapshot|ADR-019]]（archive 文件 frozen snapshot 原则）
- [[../docs/adr/[ADR]_020_Archive_Auto_Discovery|ADR-020]]（check_wikilinks.py auto-discover NEEDLES）

---

## 10 关联 PR

| PR | merged | 标题 | 文件 / lines |
|---|---|---|---|
| [#118](https://github.com/MJ-AgentLab/mj-agent/pull/118) | 2026-05-11 02:44Z | PR-A: decouple HITL_Prompt + strip derives_from frontmatter | 28f / +746/-112 |
| [#121](https://github.com/MJ-AgentLab/mj-agent/pull/121) | 2026-05-11 03:14Z | PR-Β: neutralize STANDARD/ADR prose mj-system refs | 17f / +160/-172 |
| [#122](https://github.com/MJ-AgentLab/mj-agent/pull/122) | 2026-05-11 03:38Z | PR-Γ: archive 9 ADRs + split ADR-025 into 026/027/028 + forward guard | 18f / +717/-86 |
| [#123](https://github.com/MJ-AgentLab/mj-agent/pull/123) | 2026-05-11 03:48Z | PR-Δ: tail cleanup of cross-repo refs | 20f / +82/-85 |
| [#124](https://github.com/MJ-AgentLab/mj-agent/pull/124) | 2026-05-11 04:47Z | PR-E: 加 §如何引用上游业务系统 元文档段 + ADR-020 URL → wikilink | 2f / +50/-7 |

**总计**：5 PR / 2h 03min / 85 文件 / +1755/-462 lines。
