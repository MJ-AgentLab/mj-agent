---
type: standard
domain: WORKFLOW
summary: 规范 AI 在 mj-agent 17 阶段执行闭环（Intake → Post-merge）的 prompt 结构、引用规则与 HITL 触发条件，是 Track C engineering-workflow 主 STANDARD
owner: 项目负责人
created: 2026-05-08
updated: 2026-05-11
state: active
version: v1.0
track: engineering-workflow
tags:
  - standard
  - ai-engineering
  - execution
  - hitl
  - prompt
  - engineering-workflow
aliases:
  - MJ-Agent AI Engineering Execution HITL Prompt Standard
  - mj-agent AI 工程执行闭环与 HITL Prompt 规范
  - HITL_Prompt v1.0
---

# mj-agent AI 工程执行闭环与 HITL Prompt 规范 v1.0

> **状态（Phase B PR-B3c-promote 完成后）**：`state: active`，`track: engineering-workflow`（reclassify 完成；与 [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]] §决策点 4 边界表一致）。`scripts/check_frontmatter.py` 同期已加 `engineering-workflow` 到 TRACK_VALUES 允许值集合。
> **适用范围**：mj-agent 仓中 AI Agent / Claude Code 从任务准入到合并收尾的全流程
> **目标受众**：开发者 / 项目负责人 / Claude Code AI Agent

> **目的**：规范 AI 从任务进入执行、验证、PR、合并与收尾的完整闭环，并明确何时必须引入 HITL（Human-in-the-loop）确认。
>
> **核心原则**：AI 自主推进低风险、可逆、符合既有模式的事项；凡影响数据、API、权限、安全、生产、发布、兼容性、in-source SKILL/PROMPT body、qcm_catalog 镜像或任务边界的事项，必须暂停并请求人工确认。

> **mj-agent 关键设计约束**（影响 §4 内容）：
> - mj-agent 是 **Python 3.13 + uv + LangChain 1.x + LangGraph** 项目（无 ETL pipeline / DB migration 工具链）
> - mj-agent **运行时 SKILL.md / system.md body 直接进 LLM 上下文**（in-source canonical；ADR-013 + Agent_Side §2 / §7.5 frontmatter strip 契约）—— 任何 in-source SKILL/PROMPT body 修改是 §3.1 必停 HITL 项
> - mj-agent **biz catalog**（`src/mj_agent/biz_catalog/qcm_catalog.yaml`）镜像上游业务系统数据字典 STANDARD ——任何镜像漂移检测见 §4.4
> - mj-agent **数据边界严格只读**（ADR-006 + ADR-009 + analyst-RO PostgreSQL role）—— DB schema 修改无 mj-agent 侧动作；`statement_timeout` 60s 由上游业务系统 GRANT 兜底
> - mj-agent **3 种 SKILL 实体共存**（in-source v.s. in-tree workflow v.s. marketplace plugin；详见 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.10 的边界表）

---

## 1. 总体流程

```text
0. Intake：任务准入评估
1. Issue Draft / Issue 创建
2. Branch / Worktree 创建
3. Repo Scan：仓库事实核查
4. Plan 编写或更新
5. HITL Gate 1：确认 Plan / 风险 / 文档决策
6. SPEC / ADR / RUNBOOK 编写或更新
7. HITL Gate 2：确认设计与关键决策
8. Implementation：按已确认文档实现（**3 风味**：纯代码 / in-source canonical / infra）
9. Scope Drift Gate：实现中发现偏离时暂停
10. Local Verification：本地验证（**Level A 只读** + **Level B HITL-confirm**）
11. AI Self-review：提交前自检（含 §4.9 5a/5b/5c/5d 反向扫描）
12. Commit
13. Push
14. PR 创建
15. CI / Review 处理
16. Merge Gate
17. Post-merge 收尾（含 EVAL backlog ticket 自动开单 / SPEC-* 漏项沉淀）
```

> **HITL gates 集中于 stages 5 / 7 / 9 / 11 / 13**：每次 AI 自主推进抵达这些阶段时，强制暂停等待人工确认。其他阶段按 §3.1-§3.3 规则按需 HITL。

---

## 2. Prompt 通用结构

> **每个阶段 Prompt 推荐使用以下通用结构**：

```markdown
## Task

说明当前阶段要完成什么。

## Reference Docs

### Must Follow
- `必须遵守的规范文档`

### Use As Template
- `输出结构模板`

### Consult If Affected
- `仅当涉及对应领域时参考的文档`

## Skill Hint

Preferred Skill:
- `/mj-agent-<group>-<verb>`

Use When:
- 说明何时使用该 skill

Fallback:
- 如果 skill 不可用，按哪些规则手动执行

## Rules

列出本阶段禁止事项、必须事项、HITL 触发条件。

## Output

说明期望输出格式。
```

### 2.1 Reference Docs 规则

- 标准文档用于约束行为
- 模板文档用于约束输出结构
- Plan / SPEC / ADR 用于约束任务边界
- 代码与真实数据流用于校验文档是否仍然成立
- **不要写"参考所有 docs/**"**
- 如果参考文档、Issue、Plan、代码现状冲突，必须触发 HITL

### 2.2 Skill Hint 规则

若某阶段已有对应技能（mj-agent-* 命名空间），应在 Prompt 中标记推荐 slash command，但不把它作为唯一执行路径。

推荐格式：

```markdown
## Skill Hint

Preferred Skill:
- `/mj-agent-git-pr`

Use When:
- 当前阶段是创建 PR
- in-tree skill 已 commit 且 Claude Code 已发现

Fallback:
- 如果 skill 不可用，按本 prompt 的 PR 流程手动执行
```

> **mj-agent 命名空间约定**：所有 in-tree workflow skill 强制使用 `mj-agent-<group>-<verb>` 三段式（`<group>` ∈ {flow, git, doc, runtime, infra}；详见 [[../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]，PR-B1 落地）；slash command 为 `/mj-agent-<group>-<verb>`。

---

## 3. HITL 通用规则

### 3.1 必须暂停确认

出现以下情况时，AI 必须暂停。规则分为通用项 + mj-agent 专属项两段：

通用项：

- 任务目标、范围、验收标准不清楚
- Issue / Plan / SPEC 与代码现状冲突
- 涉及数据库 schema、migration、回滚脚本（mj-agent 是只读消费者，仍可触发上游业务系统调整诉求）
- 涉及真实字段、列名、数据流但尚未验证
- 涉及权限、认证、安全、secret
- 涉及生产配置、CI/CD 发布链路、部署流程
- 涉及公共 API 或用户可见行为变化
- 需要删除数据、删除文件或执行不可逆操作
- 需要引入新依赖（影响 `pyproject.toml` / `uv.lock`）
- 实现中 scope 明显扩大
- 测试失败且原因不明确
- Review comment 会改变需求、API、schema、权限或用户行为

mj-agent 专属新增：

- **涉及 in-source SKILL.md body 修改**（`src/mj_agent/skills/**/SKILL.md`）—— 字面修改即 LLM runtime 行为修改，必须 Domain Expert + Prompt Engineer 评审；A11 EVAL 门禁（transitional waiver 期内可暂时 `eval_references` 注释 TODO）
- **涉及 system prompt 修改**（`src/mj_agent/prompts/system.md`）—— `version` bump 必触发 HITL；`eval_references` 同步审查
- **涉及 qcm_catalog.yaml 镜像变更**（`src/mj_agent/biz_catalog/qcm_catalog.yaml`）—— 与上游业务系统数据字典 STANDARD 同步；漂移可能导致 `find_biz_context` 返回错误业务语义
- **涉及 SQL guardrail / precheck 规则修改**（`src/mj_agent/tools/sql/{guardrail.py, precheck.py}`）—— 改动放宽即扩 mj-agent 数据边界（ADR-006 / ADR-009 红线）

### 3.2 可以默认处理

以下情况 AI 可以自主处理，但需记录假设：

- 低风险格式修正
- 拼写、链接、frontmatter 小修
- 明显符合现有模式的重复性代码
- 补充局部测试
- 修复 lint
- 更新与代码变更直接对应的文档
- 根据既有规则选择模板或文档落点

#### Stage 4 豁免（PLAN 落盘）

满足以下**全部**条件时，AI 可在 Intake 阶段直接判定 `Plan: 不需要`，跳过 Stage 4 PLAN 落盘 + Stage 5 HITL Gate 1：

1. **任务性质**：单文件 bugfix / 拼写 / 链接修正 / dependency 版本 patch / 文案微调
2. **风险等级**：Intake §6 risk-level = `Low`（task-type ∈ `{bugfix, documentation}`）
3. **Affected areas 不触发 §3.1 mj-agent 专属 4 项必停**：
   - `src/mj_agent/skills/**/SKILL.md` body（runtime-skill-content-change）
   - `src/mj_agent/prompts/system.md` body（prompt-version-bump）
   - `src/mj_agent/biz_catalog/qcm_catalog.yaml`（biz-catalog-sync）
   - `src/mj_agent/tools/sql/{guardrail,precheck}.py`（sql-guardrail-relax）
4. **不涉及** `.env` / `.env.example` / `infra/docker/` / CI workflow / `pyproject.toml` `[project.dependencies]` 主条目（version patch 除外）

豁免必须在 **Intake Result 显式声明** `Plan: 不需要 / 豁免依据=§3.2`；否则 Stage 4 仍为必经阶段（`grep "Plan: skipped\|Plan: 不需要" intake-result.md` 用作审计依据）。豁免范围**不包含** §3.1 通用必停 12 项，亦不包含 in-source canonical / biz catalog / SQL guardrail / Docker compose / CI/CD 类变更。

### 3.3 HITL 提问格式

```text
问题 N：
- 当前观察：
- 不确定点：
- 为什么重要：
- 可选方案：
  A.
  B.
  C.
- 我的建议：
- 默认假设：
- 是否必须等待人工确认：是 / 否
```

每次最多提出 3-5 个关键问题。

---

## 4. 分阶段 Prompt

> 各 stage 的 Preferred Skill 已在 `.claude/skills/mj-agent-*/` 下实装并 active；Fallback 段保留供 skill 临时不可用时手工执行参照。Stage 0 Intake 与 Stage 3 Repo Scan 的完整步骤由对应 in-tree SKILL（`mj-agent-flow-intake` / `mj-agent-flow-repo-scan`）承载，本规范只列 prompt 骨架与 Rules / Output 契约。

### 4.1 Intake Prompt

```markdown
## Task

请先做 mj-agent 任务 Intake。不要创建 Issue，不要创建 branch，不要创建 worktree，不要写文件，不要修改代码（特别是 src/mj_agent/skills/、src/mj_agent/prompts/、src/mj_agent/agent.py、src/mj_agent/tools/）。

## Reference Docs

### Must Follow
- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`（v2.2 active；§3.10 in-tree workflow SKILL 治理 + §4.3.1 track 字段）
- 本规范 §3.1 必停规则（含 mj-agent 专属 4 项：runtime-skill-content-change / prompt-version-bump / biz-catalog-sync / sql-guardrail-relax）

### Consult If Affected
- `docs/adr/[ADR]_006_Fail_Safe_Reads.md`（数据边界 4 层 guardrail）
- `docs/adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse.md`（mj-agent 独立 compose / 上游业务系统 consumer 边界）
- `docs/adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source.md`（biz 域 only / 不访问 ODS/DWD）
- `docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`
- `CLAUDE.md`（项目根 AI 高频上下文）

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-intake`（首位编排器；active；覆盖 risk-level / scope / 文档需求 / HITL 决策点完整 Intake 流程；含 mj-agent 专属 risk 类目：runtime-skill-content-change / prompt-version-bump / biz-catalog-sync）
- `/mj-agent-git-issue`（下游：Intake 完成后落地 Issue Draft 时调用；active）

Use When:
- 用户请求"评估任务" / "intake" / "Issue 创建前" / "需求收口"
- 需要把 vague description / chat / spec 转为可执行工程任务

Fallback:
- 若 skill 不可用，按本 prompt Rules 手动评估 risk-level / scope / 文档需求；再按 `.github/ISSUE_TEMPLATE/` 中对应模板生成 Issue Draft
- 或回落到下位子 skill：直接用 `mj-agent-git-issue` 跳过 Intake 评估（不推荐，仅简单任务）

## Rules

请判断：
1. 任务类型：feature / bugfix / documentation / maintain / hotfix（mj-agent 5 类，**不**含 optimization；详见 [[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Convention]] §5）
2. base branch：develop / main
3. scope 与 out-of-scope 是否清楚
4. acceptance criteria 是否可验证
5. 是否涉及：mj-agent 服务、API、SQL guardrail、biz catalog、mj-agent-postgres / mj-agent-redis、上游业务系统 biz pg consumer 边界、analyst RO 角色、`.env`、secrets.enc、Docker compose、CI/CD、文档
6. 风险等级：Low / Medium / High
7. 是否需要拆分 Issue
8. 是否需要 Plan / SPEC / ADR / RUNBOOK / Local ISSUE / ASSESSMENT / CHANGELOG / INDEX
9. 是否存在必须 HITL 的问题（**含 mj-agent 专属 §3.1 4 项 trigger**：runtime SKILL/PROMPT body / qcm_catalog 镜像 / SQL guardrail / system prompt version bump）
10. 是否触及 mj-agent 数据边界（ADR-006 / ADR-009）—— 触及必 HITL

## Output

输出：
- Intake Result
- Issue Draft
- Affected Areas（区分：纯代码 / in-source canonical / infra / 文档）
- Documentation Needed
- Verification Plan（含 `uv run pytest tests/{unit,eval,integration,smoke}` 选用 + `mj-agent check` healthcheck + Studio 探针）
- HITL Questions
```

---

### 4.2 Issue Prompt

```markdown
## Task

请基于已确认的 Intake Result 生成 GitHub Issue 内容。

## Reference Docs

### Must Follow
- `.github/ISSUE_TEMPLATE/`（mj-agent 5 类临时分支对应 5 份模板；hotfix 走 main）
- 本规范 §4.1 Intake Result Output（Issue Draft 必须基于已确认的 Intake Result 生成，不要在 Issue Prompt 阶段做 risk 重评估）

### Consult If Affected
- `docs/_templates/TEMPLATE_ISSUE.md`（Phase D 落地）

## Skill Hint

Preferred Skill:
- `/mj-agent-git-issue`（PR-B1 落地）

Use When:
- 创建、补全或发布 GitHub Issue

Fallback:
- 若 skill 不可用，手动选择对应 Issue 模板生成正文。

## Rules

Issue body 必须包含：
- 做什么 / 现象 / 变更内容
- 为什么
- scope / out-of-scope
- 影响范围（含 in-source canonical 影响标识 + biz catalog 影响标识）
- 完成标准
- 风险等级与来源
- 验证计划（含 mj-agent 专属验证项：Studio 探针 / mj-agent check）
- 相关文档

不要把完整设计、详细实现计划或 Repo Scan Result 原样塞进 Issue。

## Output

输出：
- 推荐 Issue 标题
- 推荐 Issue 模板
- Issue body
- 是否需要 Local ISSUE
- 是否需要 HITL
```

---

### 4.3 Branch / Worktree Prompt

```markdown
## Task

请在创建 branch / worktree 前完成检查并给出推荐命令。

## Reference Docs

### Must Follow
- `docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`
- `CLAUDE.md`（项目根 AI 高频上下文）
- `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §5（branch ↔ commit type 对齐矩阵）

## Skill Hint

Preferred Skill:
- `/mj-agent-git-branch`（PR-B1 落地）

Use When:
- 需要创建 feature / bugfix / documentation / maintain / hotfix worktree

Fallback:
- 若 skill 不可用，按 mj-agent bare repo + worktree 规则手动创建（参考现有 18 个 worktree 命名实践）；禁止使用 `git checkout` 切分支。

## Rules

检查：
1. 当前是否在 worktree 内（GIT_DIR != GIT_COMMON）
2. base branch 是否正确（feature/bugfix/documentation/maintain 从 develop；hotfix 从 main）
3. branch 类型是否匹配 Issue 类型
4. branch name 是否包含 issue id 和简述（kebab-case）
5. 是否应创建独立 worktree（mj-agent 默认每 PR 一个 worktree）
6. 是否存在分支冲突风险

规则：
- feature / bugfix / documentation / maintain 从 develop 创建
- hotfix 从 main 创建
- 不在 bare repo 根目录执行 git 工作流
- 不使用 git checkout 切换分支
- 一次只工作在一个 worktree 内（避免误改其他分支）

## Output

输出：
- 推荐 base branch
- 推荐 branch name
- 推荐 worktree 路径（`D:/workspace/10-software-project/projects/mj-agent/<branch-type>/<branch-name>`）
- 推荐命令
- HITL Questions
```

---

### 4.4 Repo Scan Prompt

```markdown
## Task

请基于 Issue、branch、plan 和当前仓库状态执行 Repo Scan。不要修改代码、SQL、配置、in-source SKILL/PROMPT、biz catalog，也不要把 Repo Scan Result 写成独立文档。

## Reference Docs

### Must Follow
- 本规范 §4.4 Repo Scan Rules（8-dim 扫描 + §7.2.1 反向扫描 + §7.1 Documentation Decision 矩阵 + Plan Verdict）
- `.claude/skills/mj-agent-flow-repo-scan/SKILL.md`（in-tree active SKILL；含 8-dim 扫描具体步骤、命令模板、HITL gate 触发条件）

### Use As Template
- `docs/_templates/TEMPLATE_REPO_SCAN_RESULT.md`（Phase B+ 待落地；模板未存在前对话输出 Repo Scan Result，结构参考下方 Output 段）

### Consult If Affected
- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`（v2.0 active）
- `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md`
- `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md`
- `docs/adr/[ADR]_006_Fail_Safe_Reads.md`
- `docs/adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source.md`

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-repo-scan`（首位编排器；PR-B2 落地后激活，覆盖 §6 八维扫描 + §7.2.1 反向扫描 + §7.1 Documentation Decision 矩阵 + Plan Verdict）
- `/mj-agent-doc-plan`（仅文档子集时降级使用；PR-B4 落地）

Use When:
- 用户已有 Issue + branch，准备进 Plan / SPEC / 实现
- 需要"事实核查" / "repo scan" / "Plan 是否成立" / "Documentation Decision" / "反向扫描"

Fallback:
- 若 skill 不可用，按本 prompt Rules 手动逐项扫描；输出 Repo Scan Result（不写文件）。
- 或回落到下位子 skill：当任务仅涉及文档需求评估时，用 `mj-agent-doc-plan`（覆盖 §7.1 Documentation Decision 子集）。

## Rules

请检查：
1. 当前 branch / worktree / diff / 未跟踪文件
2. 受影响 mj-agent 模块（agent.py / skills / prompts / tools / memory / integrations / biz_catalog / config / server / ui）+ 跨服务边界（上游业务系统 biz pg consumer / mj-agent-postgres / mj-agent-redis）
3. 真实数据来源、真实列名、真实数据流（biz_dws / biz_dwd allowlist；qcm_catalog 镜像）
4. **biz catalog drift 检测**（`scripts/diff_biz_schema.py`）—— 与上游业务系统数据字典 STANDARD 比对，若漂移触发 §3.1 必停 HITL
5. 配置、secret、Docker、CI/CD、`.env.example` 与 `secrets.enc` 一致性
6. **runtime SKILL.md / system.md drift 反向扫描**：基于本次 git diff 中 rename / move / delete 的函数 / 类 / 列 / SQL 对象，grep `src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md` + `CLAUDE.md` + `docs/**/*.md` 中的 backtick 引用，列出所有命中点；命中后须在 Output 标记需要更新的 in-source canonical（HITL 必停）
7. 测试文件和验证命令（unit / eval / integration / smoke / contract）
8. docs、plans、INDEX、CLAUDE、CHANGELOG 影响
9. Documentation Decision（10 类 × Create/Update/None 矩阵）
10. 若 Documentation Decision 判断需要 Create / Update SPEC，识别 SPEC 任务类型并按 `docs/_templates/TEMPLATE_SPEC.md` §3 Contract 列出关键检查项（输入 schema / 输出 schema / 行为不变量 / 幂等与重试 / 配置 / 错误处理 / 回滚 / 验证 / 可观测性 共 9 大子项）
11. Plan 是否仍然成立

涉及数据字段时，不得仅凭命名推断，必须读取真实来源（`src/mj_agent/biz_catalog/qcm_catalog.yaml` + `find_biz_context` 真实返回）。

## Output

输出：
- Repo Scan Result
- Current State
- Evidence Map
- Affected Areas（区分：纯代码 / in-source canonical / infra / 文档）
- biz catalog drift 状态
- runtime SKILL/PROMPT/CLAUDE.md 反向扫描命中清单
- Documentation Decision
- SPEC Type & Checklist（仅当需 Create / Update SPEC）
- Plan Verdict
- Verification Plan
- HITL Questions
- Next Step Context
```

---

### 4.5 Plan Prompt

```markdown
## Task

请基于 Repo Scan Result 编写或更新执行 Plan。

## Reference Docs

### Must Follow
- 本规范 §4.4 Repo Scan Output（Plan body 必须基于已确认的 Repo Scan Result 编写）
- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`

### Use As Template
- `docs/_templates/TEMPLATE_PLAN.md`（Phase B+ 落地；当前 plans/ 目录已有多份范例可参考）

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-plan`（首位编排器；PR-B2 落地后激活，覆盖 Plan body 6 步：context capture / 任务拆解 / 文档决策 / 风险控制 / 验证计划 / 完成标准 + 关联；sub-call mj-agent-doc-plan 处理 §7.1 Documentation Decision matrix；不直接落盘 Plan 文件）
- `/mj-agent-doc-plan`（仅文档需求评估子集时降级使用；PR-B4 落地）

Use When:
- Stage 4 Plan body 编写或更新（基于 Stage 3 Repo Scan Result 之后）
- 用户请求"写 plan" / "执行计划" / "任务拆解" / "怎么推进" / "Plan §X 步骤"
- ⚠ **方向区分**：`mj-agent-doc-plan` 仅评估"需要哪些文档"（§7.1 子集），是本 skill Step 3 的子例程；不要直接用 doc-plan 写完整 Plan

Fallback:
- 若 skill 不可用，按 plans/ 既有 PLAN 范例 + 本 prompt Rules 手工组织 Plan body。
- 或回落到下位子 skill：当任务**仅**涉及文档需求评估时，用 `mj-agent-doc-plan`。

## Rules

Plan 必须写入：
- `plans/[PLAN]_*.md`

禁止写入：
- `docs/plans/`

Plan 只写：
- 怎么推进
- 步骤顺序
- 风险控制
- 文档决策（含 in-source canonical 影响 + biz catalog 影响）
- 验证计划
- 完成标准

Plan 不写：
- 详细接口契约（归 SPEC）
- 长期架构决策（归 ADR）
- 完整实现代码

豁免（Stage 4 可跳过）：
- 满足 §3.2 「Stage 4 豁免」**全部 4 项**条件时，Stage 4 + Stage 5 可跳
- 豁免必须在 Intake Result 显式声明 `Plan: 不需要 / 豁免依据=§3.2`，否则 Stage 4 仍为必经阶段
- 豁免范围**不包含** §3.1 mj-agent 专属 4 项 trigger 与通用必停 12 项

## Output

输出（普通情况）：
- Plan 摘要
- Plan 正文草案
- 需要写入的路径
- HITL Questions

输出（豁免情况，per §3.2）：
- `Plan: skipped (per §3.2 / 豁免触发原因=<bugfix|拼写|dependency-patch|文案>)`
- 豁免凭证（写入 Intake Result + PR description「AI 自检」段；用作 §3.1 审计）
```

---

### 4.6 SPEC / ADR / RUNBOOK Prompt

```markdown
## Task

请根据已确认的 Plan 编写或更新 SPEC / ADR / RUNBOOK。

## Reference Docs

### Must Follow
- `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md`
- `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md`（code-track ADR/SPEC/RUNBOOK 时）
- `docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md`（agent-track ADR/SPEC 时）

### Use As Template
- `docs/_templates/TEMPLATE_SPEC.md`（含 §0 Task Type Identification；按任务类型裁剪）
- `docs/guide/[GUIDE]_MJ_Agent_SPEC_Authoring.md`（**SPEC 起草前必读**；§3 决策树识别 8 类任务 + §4 各类必填 / 可选段裁剪规则）
- `docs/_templates/TEMPLATE_ADR.md`
- `docs/_templates/TEMPLATE_RUNBOOK.md`（Phase A PR-A3 落地）

### Consult If Affected
- `docs/adr/[ADR]_006_Fail_Safe_Reads.md`
- `docs/adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source.md`
- `docs/adr/[ADR]_011_Doc_Versioning_And_Archive_Convention.md`（涉及 STANDARD/SPEC/EVAL/CONTRACT/ASSESSMENT 版本演进时）

## Skill Hint

Preferred Skill:
- `/mj-agent-doc-author`（PR-B4 落地；track-aware：根据 frontmatter `track` 字段 dispatch）
- `mj-agent-code-doc-author`（marketplace plugin，已存在；通用 author 能力）

Use When:
- 编写 canonical 文档，如 SPEC / ADR / RUNBOOK / GUIDE / STANDARD
- 与 HITL_Prompt §4.6 stage 上下文紧耦合时优先 in-tree `/mj-agent-doc-author`

Fallback:
- 若 skill 不可用，按对应模板和文档治理规则手动编写。

## Rules

判断：
- 新功能 / 新接口 / 新表 / 新能力：新建或更新 SPEC
- 架构 / 跨服务边界 / DB schema 影响 / CI/CD / 部署策略：新建或更新 ADR
- 运维操作 / 回滚 / 排障：新建或更新 RUNBOOK
- Bug fix / 小改动：优先更新现有 SPEC
- **代码优化 / 内部重构 / 性能改造（接口不变）**：先按本规范 §4.4 Repo Scan §7.2.1 反向扫描既有 SPEC / GUIDE / RUNBOOK 的命中段；事后按 §4.15 Rule 9 决策建 ASSESSMENT
- 编写或更新 SPEC 时，必须按 `docs/_templates/TEMPLATE_SPEC.md` 九段（Context / Scope / Contract / Configuration / Error handling / Rollback / Verification / Observability / Open questions）覆盖契约、配置、错误处理、幂等、回滚、验证、可观测性等关键项；按 [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §3 决策树先识别任务类型（8 类），再按 §4.X 裁剪必填 / 可选段

如涉及 mj-agent 数据边界（biz_dws/biz_dwd allowlist 修改）、SQL guardrail 放宽、in-source SKILL/PROMPT body 重写、biz catalog 镜像规则变更，必须 HITL。

## Output

输出：
- 文档类型
- 目标路径
- 文档正文草案
- 与 Plan 的对应关系
- frontmatter（含 `track` 字段）
- HITL Questions
```

---

### 4.7 Implementation Prompt

```markdown
## Task

请严格按已确认的 SPEC / Plan 实现。本 stage 区分 **3 种实现风味**，每种 HITL 强度不同：

- **A. 纯代码**（`src/mj_agent/{config,server,memory,integrations,...}/` + `tests/` + `infra/docker/`）—— TDD red-green；ruff/mypy strict；不触 in-source canonical
- **B. in-source canonical**（`src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md`）—— **永远 HITL**；A11 EVAL 门禁（Phase D 起强制；transitional waiver 期间允许 `eval_references` 注释 TODO）
- **C. infra**（`infra/docker/` + `pyproject.toml` + `langgraph.json` + `qcm_catalog.yaml` + `.env.example` + `scripts/`）—— `mj-agent check` healthcheck 必过；compose 改动需手动 `up -d`/`down` 排练记录到 PR

## Reference Docs

### Must Follow
- 已确认的 Plan
- 已确认的 SPEC / ADR / RUNBOOK
- 风味 A 时：`docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md`
- 风味 B 时：`docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework.md` §2 + §7.5（frontmatter strip 契约）
- 风味 C 时：相关 RUNBOOK + `docs/runbook/dev_studio_walkthrough.md`

### Consult If Affected
- `docs/adr/[ADR]_006_Fail_Safe_Reads.md`（SQL guardrail 涉及时）
- `docs/adr/[ADR]_008_Co_Deployment_With_Upstream_Warehouse.md`（compose / network 涉及时）

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-implement`（首位编排器；PR-B2 落地后激活，覆盖 3 风味判定 + red-green / root-cause-first / fresh evidence + 衔接 §4.8 Local Verification）

Use When:
- 风味 A 编码涉及 SQL guardrail / precheck：补用 `/mj-agent-runtime-biz-catalog-sync`（PR-C2，read-only inspect）
- 风味 B in-source canonical 修改：补用 `/mj-agent-runtime-skill-doc-improve` 或 `/mj-agent-runtime-prompt-version-bump`（PR-C2）
- 风味 C infra：补用 `/mj-agent-infra-docker-compose` / `/mj-agent-infra-storage-stack` / `/mj-agent-infra-studio-probe`（PR-C3）

Fallback（`/mj-agent-flow-implement` 不可用时降级路径）：
- 用户全局可选增强 skill（来自 `~/.claude/`，非 in-tree、不进入 §5 矩阵）：
  - `superpowers:test-driven-development` —— feature / bugfix / refactor / 行为变更（red-green）
  - `superpowers:systematic-debugging` —— bug 复现 / 测试失败 / 异常行为（root-cause-first）
  - `superpowers:verification-before-completion` —— 声称完成前 / 进入 §4.8 Local Verification 前（fresh evidence）
  - `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` —— 已确认 Plan 且任务可拆分
- 上述均不可用时，手动执行本节 Rules 6-8 等价动作

## Rules

必须：
1. 保持改动范围最小
2. 遵循既有 mj-agent 模块分层（CLAUDE.md "Architecture" 段）
3. 涉及数据字段时读取真实列名和数据流（`qcm_catalog.yaml` + `find_biz_context` 真实返回；不得仅凭命名推断）
4. 未明确要求时，不新增 groupby、类型转换、schema 变更或预处理
5. 不混入无关重构
6. 行为变更（feature / bugfix / refactor）先写或先调整失败测试，再写实现使其通过（red-green；TDD）
7. 修 bug 前先稳定复现路径并定位 root cause，不可用绕过 / 关闭测试 / 加 try-except 吞错替代修复
8. 声称"实现完成"前必须运行新证据（本次会话新输出），不可复用旧测试结果或旧 log 截图

风味 B（in-source canonical）专属硬约束：

9. **永远 HITL**：每次 SKILL.md / system.md body 修改提交前必先把 diff 显式给项目负责人审
10. EVAL 引用同步审查（A8 PROMPT / A11 SKILL；Phase D 起强制；当前 transitional waiver 允许注释 TODO）
11. frontmatter strip 契约不破坏：loader 行为不变；不允许把 frontmatter 字段塞进 body 文本
12. 五段式 body 结构（Agent_Side §2.1 Purpose / When to use / Planning workflow / Common patterns / Anti-patterns）保持

风味 C（infra）专属硬约束：

13. compose 改动后必须手动 `docker compose -f infra/docker/docker-compose.mj-agent.yml up -d` + `down` 排练，记录在 PR description
14. `pyproject.toml` 增依赖必须运行 `uv lock` + `uv sync`，确认 lock 文件 commit 同 PR
15. `.env.example` 改动需在 `secrets.enc` 同步加密（如涉及 secret），并更新 `config/README.md`

以下情况暂停（任意风味）：

- 需要越过 SPEC
- 需要删除或替换已有逻辑
- 需要新增依赖
- 需要改变 API / DB / 权限 / 生产配置
- 发现原方案测试无法通过
- 发现 mj-agent 数据边界（ADR-006 / ADR-009）需要修改

## Output

输出：
- 计划修改文件
- 每个文件修改目的
- 风味判定（A / B / C）
- 是否发现 scope drift
- HITL Questions（特别 B 风味必出至少 1 条 HITL Question）
```

---

### 4.8 Local Verification Prompt

```markdown
## Task

请根据本次影响范围运行或列出验证计划。**Level A 只读** 与 **Level B HITL-confirm 副作用** 分别执行。

## Reference Docs

### Must Follow
- 已确认的 Plan / SPEC
- `CLAUDE.md` "Commands" 段（uv-based 命令矩阵）
- `docs/runbook/dev_studio_walkthrough.md`（Studio 探针 H1/H2/H3/R1/R2 矩阵）

### Consult If Affected
- `.github/PULL_REQUEST_TEMPLATE/`
- 风味 C 时：`infra/docker/README.md`

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-verify`（首位编排器；PR-B3 落地后激活，按改动 scope 自动 dispatch Level A / Level B）
- `/mj-agent-doc-validate`（下位：文档验证；PR-B4 落地）
- `/mj-agent-infra-studio-probe`（下位：Studio 探针；PR-C3 落地）

Use When:
- 编码完成 / lint 后 / commit 前的本地验证（HITL Stage 10）
- 用户请求"本地验证" / "测试编排" / "verify changes" / "跑测试" / "Studio 验证"

Fallback:
- 若 skill 不可用，按下表 Rules 手动运行；Level B 命令需 HITL 确认后执行。

## Rules

### Level A：只读 / 无副作用 / 无 HITL（必跑）

| 命令 | 用途 |
|---|---|
| `uv run ruff check` | lint（CI 必跑，本地等价） |
| `uv run mypy src/mj_agent` | 类型检查 strict（CI 必跑，本地等价） |
| `uv run pytest tests/unit` | unit tests（无外部依赖） |
| `uv run pytest tests/eval` | eval tests（seed schema + Component check，无 DB） |
| `python -m compileall src` | 编译可解析 |
| `python scripts/check_wikilinks.py` | 文档 wikilinks（如 docs/ 改动） |
| `python scripts/check_frontmatter.py` | 文档 frontmatter（如 docs/ 改动） |

### Level B：DB / LLM 依赖 / 副作用 / **HITL-confirm**

| 命令 | 用途 | HITL 触发条件 |
|---|---|---|
| `uv run pytest tests/integration` | integration tests（需 live biz DB） | 需 `POSTGRES_ANALYST_USER` |
| `uv run pytest tests/smoke -m smoke` | smoke tests（需 live biz DB + Ark API） | 需 `ARK_API_KEY`；CI 不跑 |
| `uv run pytest tests/contract -m contract` | contract tests | 需 DB creds |
| `uv run mj-agent check` | DB + LLM creds 健康探针（Docker healthcheck 等价） | 需 `.env` 充实 |
| `uv run langgraph dev` | LangGraph Studio 起服务 | 需 `.env` + Ark；交互式探针 H1/H2/H3/R1/R2 |
| `docker compose -f infra/docker/docker-compose.mj-agent.yml up -d` | mj-agent compose 启动（含 mj-agent-postgres + mj-agent-redis） | 需上游业务系统栈先 up（含 `mj-system-backend-network` bridge）；本地 docker daemon |
| `docker compose -f infra/docker/docker-compose.mj-agent.yml down` | compose 清理 | 同上 |

按影响范围检查：

- 风味 A 纯代码：Level A 全跑；Level B 按改动域选（碰 SQL/biz 必跑 integration + Studio 探针）
- 风味 B in-source canonical：Level A + Studio 探针（手动看 LLM 行为差异）+ smoke（业务样本对比）
- 风味 C infra：Level A + 必跑 `mj-agent check` + compose up/down 排练 + Studio 探针

关键测试失败且原因不明时必须 HITL。

## Output

输出：
- 已运行 Level A 检查及结果
- 已运行 Level B 检查及结果（注明 HITL 已确认）
- 未运行检查及原因（环境缺 creds / 改动不涉及 / HITL 未批）
- 失败项
- 风险判断
- 是否可进入 self-review
```

---

### 4.9 AI Self-review Prompt

```markdown
## Task

请在 commit 前做 AI self-review。

## Reference Docs

### Must Follow
- 已确认的 Plan / SPEC
- `.github/PULL_REQUEST_TEMPLATE/`
- `docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`
- `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-self-review`（首位编排器；PR-B3 落地后激活，覆盖 11-item checklist + 5a/5b/5c/5d 反向扫描 + scope-drift 检查 + commit message 起草）

Use When:
- 本地验证完成、commit 前的最终自审（HITL Stage 11）
- 用户请求"AI 自检" / "self review" / "commit 前检查" / "diff 自审"

Fallback:
- 若 skill 不可用，按本 prompt Rules 手动逐项检查 12 项 checklist。

## Rules

检查：

1. 改动是否完全对应 Plan / SPEC
2. 是否超出 scope（含 in-source canonical / biz catalog 触及但 Plan 未声明）
3. 是否改变 API、schema、权限、配置、依赖、用户可见行为
4. 是否有 hardcode、secret、绝对路径、调试代码（特别检查 `.env` / `secrets.enc` / Ark API key）
5. 文档同步检查（拆为四段 5a/5b/5c/5d）：
   - **5a. 既有文档失真扫描**：基于本次 git diff 中 rename / move / delete 的函数 / 类 / 文件 / SQL 对象 / 列 列表，按本规范 §4.4 Repo Scan §7.2.1 反向扫描动作 grep `docs/**/*.md` + `CLAUDE.md` + **`src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md`**（runtime canonical 是反向扫描目标）中 backtick 包裹的引用，列出所有命中文档；命中后须在 PR description 说明已更新或决定不更新（含理由）。本次任务不涉及上述 5 类改动时，须显式记录"不涉及反向扫描"
   - **5b. 新文档创建确认**：比对 Repo Scan §7.1 Documentation Decision 表中 Action=Create 的所有行，确认对应 Plan / SPEC / ADR / RUNBOOK / GUIDE / STANDARD / 本地 ISSUE / ASSESSMENT 已创建并填入 frontmatter（schema 按 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|文档管理框架]] §4.3 / §4.4）
   - **5c. INDEX / CLAUDE.md / CHANGELOG.md 同步**：按 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|框架]] §6.4 的 allowlist 检查 `CLAUDE.md`；按 §7.1 A5 检查 `INDEX.md`；按 PR template `.github/PULL_REQUEST_TEMPLATE/<type>.md` 的 CHANGELOG 字段判断
   - **5d. SPEC Delta Check**：若本任务创建或更新了 SPEC，对比最终 diff、验证结果与 review/CI 发现，判断 SPEC 是否遗漏关键契约、配置、错误处理、幂等、回滚、验证或可观测性。无漏项时输出 `SPEC Delta: None`；有漏项时按 `docs/_templates/TEMPLATE_SPEC.md` §3 Contract 各子项命名（如 `Contract.Input` / `Configuration` / `Error handling` / `Rollback` / `Verification` / `Observability`）记录漏项；按 [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §5 短码映射表对照本任务类型的必填段 cross-check。若本任务不涉及 SPEC，显式输出"不涉及 SPEC Delta"
6. acceptance criteria 是否都有验证证据
7. 是否有不应提交的文件（`.env` / `*.pyc` / `.venv/` / log files）
8. **biz catalog drift**：若 `qcm_catalog.yaml` 改动，与上游业务系统数据字典 STANDARD 是否一致（`scripts/diff_biz_schema.py`）
9. **runtime canonical 改动审查**：若 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/*.md` 改动，A11 / A8 EVAL 同步审查 + frontmatter `version` bump + Domain Expert 评审签字
10. **system.md `version` bump 检查**：若 system.md `version` 字段改变，必须同步 `eval_references` 字段（transitional waiver 期内可注释 TODO）
11. commit type 是否匹配 branch type（`documentation/*` 仅 `docs`；`feature/*` ∈ {feat, perf, refactor, test, docs}；详见 STANDARD §5.2）
12. commit scope 是否在闭合 allowlist 内（详见 STANDARD §4 + 12 个允许 scope）

发现 secret、无关改动、关键测试失败、in-source canonical 未 HITL、中高风险残留时必须 HITL。

## Output

输出：
- 文件清单
- 改动理由
- AC 映射
- 测试结果
- 风险清单
- SPEC Delta
- biz catalog drift 状态
- in-source canonical 改动 HITL 状态
- 是否建议提交
```

---

### 4.10 Commit Prompt

```markdown
## Task

请基于当前 diff 生成 commit 方案。

## Reference Docs

### Must Follow
- `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md`
- `docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`

## Skill Hint

Preferred Skill:
- `/mj-agent-git-commit`（PR-B1 落地）

Use When:
- 需要暂存文件并创建规范 commit

Fallback:
- 若 skill 不可用，手动筛选文件、拆分提交、生成 commit message。

## Rules

检查：

1. 是否单 commit 或多 commit
2. commit type 是否匹配 branch type（STANDARD §5.2 矩阵）
3. commit scope 是否在闭合 allowlist 内（STANDARD §4 12 项）
4. 是否包含无关文件
5. 是否包含敏感信息（secret / token / `.env` / `secrets.enc`）
6. 是否需要拆分提交
7. commit message 格式：`<type>(<scope>): <summary>`（小写）

mj-agent 专属 scope 提醒（STANDARD §4 闭合 allowlist）：
- 代码：`agent` / `llm` / `prompt` / `skill` / `sql` / `db` / `config`
- 跨代码：`tests` / `eval` / `ci` / `deps` / `infra`

## Output

输出：
- 推荐提交拆分
- 每个 commit 包含文件
- commit message（heredoc 格式 + Co-Authored-By: Claude）
- 不应提交文件
- HITL Questions
```

---

### 4.11 Push Prompt

```markdown
## Task

请在 push 前做最终检查。

## Reference Docs

### Must Follow
- `docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md`
- `docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`

## Skill Hint

Preferred Skill:
- `/mj-agent-git-push`（PR-B1 落地）

Use When:
- 需要推送分支到远程仓库

Fallback:
- 若 skill 不可用，手动确认分支、提交、远程、secret 和测试结果后再 push。

## Rules

检查：

1. 当前 branch 是否正确（feature/bugfix/documentation/maintain/hotfix 之一）
2. base branch 是否正确（develop 或 main）
3. 是否有未提交文件
4. 是否有不应提交文件（`.env` / `secrets.enc` 解密产物 / `*.log` / `.venv/`）
5. 是否包含 secret、token、个人信息或本地配置
6. 是否已运行必要测试（Level A 全过；Level B 按需）
7. 是否存在需要先确认的风险（in-source canonical 改动 HITL、biz catalog drift 未确认）
8. branch 是否需要先 rebase / merge develop 同步

## Output

输出：
- 当前 branch
- 即将 push 的 commits
- 检查结果
- 风险判断
- 是否可以 push
```

---

### 4.12 PR Prompt

```markdown
## Task

请基于 Issue、Plan、SPEC、commit history 和当前 diff 生成 PR 内容。

## Reference Docs

### Must Follow
- `docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`
- `.github/PULL_REQUEST_TEMPLATE/`

## Skill Hint

Preferred Skill:
- `/mj-agent-git-pr`（PR-B1 落地）

Use When:
- 创建 Pull Request 或生成 PR body

Fallback:
- 若 skill 不可用，读取对应 PR 模板，填充后使用 `--body-file` 创建 PR。

## Rules

按 branch type 选择模板：
- `feature.md`
- `bugfix.md`
- `documentation.md`
- `maintain.md`
- `hotfix.md`
- `release.md`

非交互模式必须使用 `--body-file`，不要依赖 `gh pr create --template` 打开编辑器。

PR 内容必须包含：

- 变更摘要
- 影响范围（区分：纯代码 / in-source canonical / infra / 文档）
- 审核要点
- 本地验证（Level A + Level B 已跑哪些）
- AI 自检（11-item checklist + 5a/5b/5c/5d）
- 风险（含 in-source canonical 改动声明 + biz catalog drift 声明）
- 回滚方式
- 关联 Issue / Plan / SPEC / ADR
- **dual-track / tri-track 反检 checklist**（v2.0 → v2.1 promote 后切到 tri-track）：
  - Code-Side `<details>` block A1-A6 + OB1-OB5
  - Agent-Side `<details>` block A7-A10 + A11
  - Engineering-Workflow `<details>` block A12-A14（v2.1 promote 后激活）

## Output

输出：
- PR 标题
- PR body
- 推荐 reviewer
- 是否 draft
- 是否需要 HITL
```

---

### 4.13 Review / CI Prompt

```markdown
## Task

请处理 PR review comments 和 CI failures。

## Reference Docs

### Must Follow
- `.github/PULL_REQUEST_TEMPLATE/`
- 已确认的 Plan / SPEC / ADR

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-review-respond`（首位编排器；PR-B3 落地后激活，覆盖 reviewer comments 6 类分类 + 每条影响评估 + 修改计划 + 回复起草 + Risk 判断）

Use When:
- 收到 PR review comments 或 CI failures，需分类、影响评估、起草回复
- ⚠ **方向区分**：`mj-agent-git-review-pr` 是"架构审查方向"（review **别人的** PR），与本阶段方向相反；不要误用

Fallback:
- 若 skill 不可用，按本 prompt Rules 手工处理。

## Rules

逐条判断：

1. reviewer 说了什么
2. 是 bug、建议、风格、架构、需求、测试问题，还是 SPEC gap（按 `docs/_templates/TEMPLATE_SPEC.md` §3 Contract 各子项命名 + [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §5 短码映射表）
3. 是否必须修改
4. 是否影响 Plan / SPEC / ADR
5. 建议如何回应
6. 需要修改哪些文件
7. 修改后需要重新运行哪些测试

如果 review 改变需求、API、schema、权限、用户行为、in-source canonical body、biz catalog 镜像规则，必须 HITL。

## Output

输出：
- comment 分类
- 处理优先级
- 修改计划
- 建议回复
- 是否需要更新文档
- HITL Questions
```

---

### 4.14 Merge Gate Prompt

```markdown
## Task

请在 merge 前做最终 gate 检查。

## Reference Docs

### Must Follow
- `docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`
- `docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`

## Skill Hint

Preferred Skill:
- `/mj-agent-git-check-merge`（PR-B1 落地）

Use When:
- 检查 PR 是否可以合并

Fallback:
- 若 skill 不可用，手动检查 CI、review、conflict、风险、回滚和发布动作。

## Rules

检查：

1. PR 是否链接正确 Issue
2. acceptance criteria 是否全部满足
3. required checks 是否通过（CI ruff + mypy + pytest unit/eval/integration + contract）
4. review comments 是否全部处理
5. 是否存在 unresolved conversation
6. 是否存在 merge conflict
7. 是否需要 rebase 或同步 base
8. 是否有发布、部署或迁移步骤
9. 是否有 rollback plan
10. 是否需要 post-merge 验证（特别 in-source canonical / biz catalog 改动）

CI 未通过、review 未完成、风险未确认，不得 merge。

## Output

输出：
- Merge readiness: Ready / Not Ready
- 未完成事项
- 风险
- 推荐 merge 方式（squash / merge commit / rebase）
- merge 后动作
```

---

### 4.15 Post-merge Prompt

```markdown
## Task

请在 PR merge 后完成收尾检查。

## Reference Docs

### Must Follow
- `docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`

### Consult If Affected
- `docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`
- `CHANGELOG.md`
- 相关 RUNBOOK / RELEASE 文档

## Skill Hint

Preferred Skill:
- `/mj-agent-flow-post-merge`（首位编排器；PR-B3 落地后激活，覆盖 Issue 关闭 / CHANGELOG / follow-up issue / 分支清理 / hotfix 同步 / smoke test / 复盘 / ASSESSMENT 决策 / EVAL backlog ticket）
- `/mj-agent-git-delete`（下位：分支 / worktree 删除；PR-B3 落地）
- `/mj-agent-git-sync`（下位：hotfix 后 sync main → develop；PR-B3 落地）

Use When:
- PR 合并后的收尾（HITL Stage 17）
- 用户请求"PR 合并后" / "post-merge" / "Issue 关闭" / "release notes" / "follow-up"

Fallback:
- 若 skill 不可用，按本 prompt Rules 手动逐项执行 Post-merge checklist。

## Rules

执行或生成：

1. 确认 Issue 是否关闭
2. 确认 branch / worktree 是否需要删除
3. hotfix 是否已同步 develop
4. 是否需要发布或部署
5. 是否需要 smoke test
6. 是否需要更新 CHANGELOG / release note
7. 是否有 follow-up issue
8. 是否需要复盘
9. **任务类型为 optimization，或 feature 含重构 / 性能改造**：是否建 ASSESSMENT 对比改造效果。pre-change 阶段未识别 ASSESSMENT 需求时，post-merge 是最后一道闸——不建 ASSESSMENT 必须在 post-merge checklist 显式记录原因（如"优化未达预期 measurable improvement"）
10. 若本任务在 self-review / Review / CI 阶段产生 `SPEC-*` 漏项（按 `docs/_templates/TEMPLATE_SPEC.md` §3 Contract 各子项命名 + [[../guide/[GUIDE]_MJ_Agent_SPEC_Authoring|SPEC Authoring GUIDE]] §5 短码映射表），按以下层级沉淀：
    - **默认**：在 PR description「AI 自检」段累计 `SPEC Delta: <code> @ <section>`
    - **触发条件达标后**（≥3 真实漏项跨 ≥2 任务）：新建或追加 `plans/[PLAN]_SPEC_Authoring_Miss_Ledger.md`
    - **升级 POSTMORTEM 边界**：仅当漏项导致 merge 后事故、生产影响、数据错误、CI/CD 发布失败或 P1/P2 级返工时，才写入 `docs/postmortem/[POSTMORTEM]_*.md`
11. **EVAL backlog ticket 自动开单**（mj-agent 专属，v1.0 引入；transitional waiver 衰减机制）：若本 PR 触及 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/system.md` body 修改，无论本 PR 是否带 EVAL 引用，均开 follow-up Issue：`[EVAL backlog] <skill_name or prompt_name> @ <commit_sha>`，归 Phase D（Phase 2）EVAL framework 时一并完成；这是 A11 transitional waiver 期内的兜底机制
12. **PR 关联 plan state 标记**（v1.0 引入；闭合 STANDARD ↔ skill 引用链）：若本 PR 关联 `plans/[PLAN]_*.md` 或 `plans/[INTAKE]_*.md` 且当前 `state: active`，post-merge 阶段必须把 frontmatter `state` 改为 `completed` + 填 `completed: <ISO date>` 字段。覆盖场景：
    - **(a) 单 PR 单 plan**：PR merge 即直改 `completed`
    - **(b) 多 PR 同一 plan**：仅当 plan 内显式标"本 PR 是最后阶段"才改 `completed`；否则保 `active` + 在 post-merge checklist 提示
    - **(c) plan 当前 `state: draft`**：**不**自动跨态跳 `completed`（draft 不应跳过 active 直达终止态）；输出建议"先评估转 active 或人工处理"
    - 引用 [[../../.claude/skills/mj-agent-flow-post-merge/SKILL|.claude/skills/mj-agent-flow-post-merge/SKILL.md]] Step 9 为执行子例程；引用 [[./[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §5.11 4 态机定义（draft / active / completed / archived）

## Output

输出：
- Post-merge checklist
- 验证结果
- 清理动作
- follow-up issue（含 EVAL backlog ticket 如有）
- SPEC-* 漏项沉淀动作
- 复盘摘要
```

---

## 5. Skill Hint 映射表

> **覆盖矩阵（目标态）**：与 `.claude/skills/` 内 32 个 mj-agent-* in-tree skills 完全对齐——9 流程编排器（mj-agent-flow plugin family）+ 23 域工具 skills（git 9 / doc 6 / runtime 4 / infra 4）。
>
> **当前状态（Phase A）**：`.claude/skills/` 为空白，本节作为占位指引；Phase B PR-B1...B3 起 13 P0 skills 落地后渐次激活；§5 各表"Status"列展示当前可用性。
>
> 各 skill 详细描述见 `.claude/skills/<skill-name>/SKILL.md`（落地后）；`CLAUDE.md` "Engineering-Workflow Documentation" 段提供高频上下文索引。

### 5.1 流程编排器（mj-agent-flow plugin family，9 个）

| 阶段 | 推荐 Skill | Status |
|---|---|---|
| 0 Intake | `/mj-agent-flow-intake` | P0；PR-B2 落地 |
| 3 Repo Scan | `/mj-agent-flow-repo-scan` | P0；PR-B2 落地 |
| 4 Plan body 编写 | `/mj-agent-flow-plan` | P0；PR-B2 落地 |
| 8 Implementation 编码段 | `/mj-agent-flow-implement` | P0；PR-B2 落地 |
| 9 Scope Drift Gate | `/mj-agent-flow-scope-drift` | P1；PR-B3 落地 |
| 10 Local Verification | `/mj-agent-flow-verify` | P0；PR-B3 落地 |
| 11 AI Self-review | `/mj-agent-flow-self-review` | P0；PR-B3 落地 |
| 13 Review/CI（处理 own PR comments / CI failure） | `/mj-agent-flow-review-respond` | P1；PR-B3 落地 |
| 17 Post-merge | `/mj-agent-flow-post-merge` | P1；PR-B3 落地 |

### 5.2 Git 域（mj-agent-git，9 个）

| 阶段 | 推荐 Skill | Status |
|---|---|---|
| 1 Issue | `/mj-agent-git-issue` | P0；PR-B1 落地 |
| 2 Branch / Worktree | `/mj-agent-git-branch` | P0；PR-B1 落地 |
| 12 Commit | `/mj-agent-git-commit` | P0；PR-B1 落地 |
| 13 Push | `/mj-agent-git-push` | P0；PR-B1 落地 |
| 14 PR | `/mj-agent-git-pr` | P0；PR-B1 落地 |
| 15 PR Review（架构审查方向：review **别人的** PR） | `/mj-agent-git-review-pr` | P1；PR-B3 落地 |
| 16 Merge Check | `/mj-agent-git-check-merge` | P1；PR-B3 落地 |
| 17 Branch Cleanup（post-merge 子动作） | `/mj-agent-git-delete` | P1；PR-B3 落地 |
| 17 Branch Sync（post-merge 子动作 / hotfix 同步） | `/mj-agent-git-sync` | P1；PR-B3 落地 |

### 5.3 文档域（mj-agent-doc，6 个）

| 用途 | 推荐 Skill | Status |
|---|---|---|
| Plan / 文档需求评估 | `/mj-agent-doc-plan` | P0；PR-B4 落地 |
| 文档编写（track-aware，与 stage 6 紧耦合） | `/mj-agent-doc-author` | P0；PR-B4 落地 |
| 文档验证（wikilinks + frontmatter + INDEX） | `/mj-agent-doc-validate` | P0；PR-B4 落地 |
| 文档同步（代码改动 → 文档更新） | `/mj-agent-doc-sync` | P1；PR-C1 落地 |
| 文档审查（PR 范围） | `/mj-agent-doc-review` | P1；PR-C1 落地 |
| 文档迁移（archive 工作流） | `/mj-agent-doc-migrate` | P2；PR-C1 落地 |

> 注：marketplace plugin `mj-agent-code-doc-author` / `mj-agent-code-doc-plan` 与本表共存（详见 [[../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]）；本表 in-tree skills 与 stage 6 / stage 11 紧耦合。

### 5.4 Runtime 域（mj-agent-runtime，4 个；**read-only by design**）

| 用途 | 推荐 Skill | Status |
|---|---|---|
| 运行时 SKILL.md body 改进（**propose diff，不写 src/**） | `/mj-agent-runtime-skill-doc-improve` | P1；PR-C2 落地 |
| system.md `version` bump walkthrough | `/mj-agent-runtime-prompt-version-bump` | P1；PR-C2 落地 |
| qcm_catalog.yaml 镜像同步（与上游业务系统数据字典 STANDARD 比对） | `/mj-agent-runtime-biz-catalog-sync` | P1；PR-C2 落地 |
| EVAL baseline 设定（A11 强制后） | `/mj-agent-runtime-eval-baseline` | P1；PR-D2-skill 落地（framework-independent；baseline 实测延 Phase 2 PR-D2-enforcement） |

> **Runtime 类目硬约束**（v1.0 引入）：所有 `mj-agent-runtime-*` 是 **read-only inspect** 设计——它们 propose diff、跑反向扫描、列出影响清单，但**不**直接修改 `src/mj_agent/{skills,prompts,agent.py,tools}/`。SKILL.md "Anti-patterns" 段必须明文写"Do NOT modify src/mj_agent/...";A12 描述质量门禁校验此约束。

### 5.5 Infra 域（mj-agent-infra，4 个）

| 用途 | 推荐 Skill | Status |
|---|---|---|
| 环境搭建（`scripts/setup-env.ps1` walkthrough） | `/mj-agent-infra-env-setup` | P0；PR-C3 落地 |
| Studio 探针（`uv run langgraph dev` H1/H2/H3/R1/R2 矩阵） | `/mj-agent-infra-studio-probe` | P0；PR-C3 落地 |
| Docker compose lifecycle（mj-agent compose stack） | `/mj-agent-infra-docker-compose` | P1；PR-C3 落地 |
| Storage stack（mj-agent-postgres + mj-agent-redis 容器编排） | `/mj-agent-infra-storage-stack` | P1；PR-C3 落地 |

---

## 6. 最终推荐原则

```text
Intake 解决能不能立项。
Issue 解决如何追踪。
Repo Scan 解决仓库事实是否支持原计划。
Plan 解决怎么推进。
SPEC / ADR 解决要实现什么和为什么这样设计。
Implementation 只执行已确认方案。
Verification 和 Self-review 负责防止局部正确但整体失控。
PR / Review / Merge Gate 负责团队协作和发布风险控制。
Post-merge 负责闭环。
```

Reference Docs 与 Skill Hint 的定位：

```text
Reference Docs 是知识与规则锚点。
Skill Hint 是工具与流程入口。
HITL 是风险与决策边界。
```

最终规则：

```text
低风险事项：AI 自主推进并记录假设。
中风险事项：AI 给出推荐方案，必要时 HITL。
高风险事项：AI 必须暂停，等待人工确认。
```

---

## 参考

- 上层框架：
  - [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.2]]（active）
  - [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]（active）
  - [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.2]]（active）
- 实施 ADR：
  - [[../adr/[ADR]_014_Tri_Track_Documentation_Governance|ADR-014]]（v2.1 tri-track 升级）
  - [[../adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]（mj-agent-* in-tree skills 命名空间 + lifecycle）
- 关联 ADR：
  - [[../adr/[ADR]_006_Fail_Safe_Reads|ADR-006]]（数据边界 4 层 guardrail）
  - [[../adr/[ADR]_009_Biz_Domain_As_Primary_Data_Source|ADR-009]]（biz 域 only / 不访问 ODS/DWD）
  - [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]（archive 工作流）
  - [[../adr/[ADR]_013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（in-tree vs marketplace SKILL schema 边界）
- mj-agent 关联 STANDARD（cross-ref）：
  - [[STANDARD]_MJ_Agent_Commit_Message_Convention]]（§4.10 / §4.12 引用）
- mj-agent 关联 GUIDE（cross-ref）：
  - [[../infrastructure/git/[GUIDE]_Git_Branch_Strategy|Git_Branch_Strategy]]（§4.3 引用）
  - [[../infrastructure/git/[GUIDE]_Git_Push_Workflow|Git_Push_Workflow]]（§4.11 引用）
  - [[../infrastructure/git/[GUIDE]_PR_Description_Convention|PR_Description_Convention]]（§4.12 / §4.15 引用）
- mj-agent 关联 RUNBOOK（cross-ref）：
  - `docs/runbook/dev_studio_walkthrough.md`（§4.8 Level B 探针）
- 关联 in-tree SKILL（承载本规范各 stage 完整步骤）：
  - `.claude/skills/mj-agent-flow-intake/SKILL.md`（§4.1 完整步骤 + Output 结构）
  - `.claude/skills/mj-agent-flow-repo-scan/SKILL.md`（§4.4 完整步骤 + 8-dim 扫描表 + §7.1 Documentation Decision 模板）
  - `.claude/skills/mj-agent-flow-plan/SKILL.md`（§4.5 Plan body 编排）
  - `.claude/skills/mj-agent-flow-implement/SKILL.md`（§4.7 3 风味实现编排）
  - `.claude/skills/mj-agent-flow-self-review/SKILL.md`（§4.9 11-item checklist + 5a/5b/5c/5d 反向扫描）
  - `.claude/skills/mj-agent-flow-post-merge/SKILL.md`（§4.15 收尾 + EVAL backlog ticket 自动开单）
- 行业精度：
  - HITL（Human-in-the-Loop）：MLOps Level 2 + AI Safety 标准做法
  - Anthropic Skills 仓 in-tree pattern：[anthropics/skills](https://github.com/anthropics/skills)
  - Claude Code plugin marketplace 与 in-tree 二元生态：[Claude Code docs](https://docs.claude.com/en/docs/claude-code/plugins)
- 用户互动证据：
  - 2026-05-08 brainstorming session：4 决策（建设侧 / skill 放置 / HITL 深度 / 框架重构）+ skeleton-first follow-up
  - 外部 plan 文件：`C:/Users/Admin/.claude/plans/d-workspace-10-software-project-projects-golden-shannon.md`
