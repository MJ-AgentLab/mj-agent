---
type: sdd-workflow
artifact: execution-loop
state: active
version: 1.3
owner: ranzuozhou
created: 2026-06-04
updated: 2026-06-20
track: shared
ai_visibility: source-of-truth
---

# Workflow: Execution Loop（17-stage AI 工程执行闭环）

> **Kernel home note**：本文件是 17-stage AI 工程执行闭环的 **kernel home**
> （Track C engineering-workflow 执行治理）。它 faithful port 了 HITL_Prompt
> STANDARD 的 §1（总体流程）/ §2（Prompt 通用结构）/ §3（HITL 通用规则）/
> §5（Skill Hint 映射表）+ §4.8（Local Verification）/ §4.9（AI Self-review）的
> **结构性 / 契约性** 内容。
>
> 源 STANDARD（`docs/rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt.md`）
> 在 `docs/rule/` 中保持 `state: active` 作为历史源，直至 M6 PR4 将其归档。
>
> **不在本文件 re-port 的内容（cross-ref，避免重复）**：
> - 每个 stage 的 **detailed prompt**（源 §4.1-§4.15 的完整步骤 + Output 结构）由
>   `.claude/skills/mj-agent-*` SKILL 拥有（active 执行路径）+ HITL_Prompt §4
>   历史源；本文件只持 stage 骨架 + stage→skill 映射。
> - HITL **required-scenarios 10-enum**（canonical 收敛口径）住在
>   [[../../policies/ai-agent|policies/ai-agent]] §4。
> - 文档治理门禁 **A1-A6**（frontmatter / wikilink / INDEX / allowlist）住在
>   [[../../policies/documentation|policies/documentation]]。

---

## §1 总体流程（17-stage loop）

> Port from HITL_Prompt STANDARD §1。stage 0-17 逐字保留。

```text
0.  Intake：任务准入评估
1.  Issue Draft / Issue 创建
2.  Branch / Worktree 创建
3.  Repo Scan：仓库事实核查
4.  Plan 编写或更新
5.  HITL Gate 1：确认 Plan / 风险 / 文档决策
6.  SPEC / ADR / RUNBOOK 编写或更新
7.  HITL Gate 2：确认设计与关键决策
8.  Implementation：按已确认文档实现（3 风味：纯代码 / in-source canonical / infra）
9.  Scope Drift Gate：实现中发现偏离时暂停
10. Local Verification：本地验证（Level A 只读 + Level B HITL-confirm）
11. AI Self-review：提交前自检（含 §6 5a/5b/5c/5d 反向扫描）
12. Commit
13. Push
14. PR 创建
15. CI / Review 处理
16. Merge Gate
17. Post-merge 收尾（含 EVAL backlog ticket 自动开单 / SPEC-* 漏项沉淀）
```

> **HITL gates 集中于 stages 5 / 7 / 9 / 11 / 13**：每次 AI 自主推进抵达这些
> 阶段时，**强制暂停**等待人工确认。其他阶段按 §3 规则按需 HITL。

| Gate | Stage | 确认内容 |
|---|---|---|
| Gate 1 | 5 | Plan / 风险 / 文档决策 |
| Gate 2 | 7 | 设计与关键决策（SPEC / ADR） |
| Gate 3 | 9 | Scope Drift（实现中发现偏离） |
| Gate 4 | 11 | Self-review 结论（commit 前） |
| Gate 5 | 13 | Push（CI / Review 进入前） |

---

## §2 Per-stage Prompt 通用结构

> Port from HITL_Prompt STANDARD §2 + §2.1 + §2.2。

每个阶段 Prompt 推荐使用以下通用结构：

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

### §2.1 Reference Docs 规则

- 标准文档用于约束行为
- 模板文档用于约束输出结构
- Plan / SPEC / ADR 用于约束任务边界
- 代码与真实数据流用于校验文档是否仍然成立
- **不要写"参考所有 docs/\*\*"**
- 如果参考文档、Issue、Plan、代码现状冲突，**必须触发 HITL**

### §2.2 Skill Hint 规则

若某阶段已有对应技能（`mj-agent-*` 命名空间），应在 Prompt 中标记推荐 slash
command，但**不**把它作为唯一执行路径——同时给出 `Use When` + `Fallback`（skill
不可用时按本 prompt 手动执行）。

> **mj-agent 命名空间约定**：所有 in-tree workflow skill 强制使用
> `mj-agent-<group>-<verb>` 三段式（`<group>` ∈ {flow, git, doc, runtime,
> infra}）；slash command 为 `/mj-agent-<group>-<verb>`。命名空间 + lifecycle
> 由 [[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] 治理。

---

## §3 HITL 通用规则

> Port from HITL_Prompt STANDARD §3.1 / §3.2 / §3.3。
> **核心原则**：AI 自主推进低风险、可逆、符合既有模式的事项；凡影响数据、API、
> 权限、安全、生产、发布、兼容性、in-source SKILL/PROMPT body、qcm_catalog 镜像或
> 任务边界的事项，必须暂停并请求人工确认。

### §3.0 HITL 执行模型（拍板即落盘；v1.3）

> **暂停 ≠ 让 Owner 手动转写。** HITL = **AI 呈现方案/选项/diff + impact 分析 →
> Owner 拍板（决策）→ AI 直接落盘并执行**。Owner 的职责是**决策**，不是粘贴/复制/
> 编写内容；AI 不得把落盘动作甩回给 Owner 手动完成。

拍板有两种形态：

1. **内容多选 / 方案选择** → `AskUserQuestion`（结构见 §3.3）；Owner 选定后 AI 落盘。
2. **权限门（逐写确认）** → 对 `ask` 列表面（4 项 in-source 专属必停，见 §3.1）与
   **protected paths**（`.claude/**`、`.mcp.json`、`.claude.json`）的 Edit/Write，
   harness 在交互模式**强制弹权限 prompt**（`permissions.allow` 不可抑制）——该 prompt
   **就是拍板**；Owner 批准后 AI 写入。落盘后由 **merge review（A13 settings allowlist /
   A14 .mcp.json trust posture 等 PR gate）兜底**。

> **enforce 机制变更（ADR-034）**：4 项 in-source 专属必停由"`settings.json` 物理
> `deny`（AI 完全不能写）"改为"`ask` 列表逐写拍板（AI 可在 Owner 批准后落盘）"；
> 物理硬锁兜底转为"拍板 prompt + 合并审查"。**仅在交互模式成立**——`auto` / `bypass`
> 模式下 `ask` 会被自动放行且 protected-path privilege-escalation 被 classifier 硬拦，
> 故放宽类 / privilege 文件改动必须在交互模式执行。`git commit/push/PR/merge` 与
> "是否变更必停面"的判断仍是独立拍板点，只是拍板后由 AI 执行而非 Owner 手动。

### §3.1 必须暂停确认

通用项（出现以下任一即暂停）：

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

mj-agent 专属新增（4 项硬必停）：

- **in-source SKILL.md body 修改**（`src/mj_agent/skills/**/SKILL.md`）—— 字面
  修改即 LLM runtime 行为修改，必须 Domain Expert + Prompt Engineer 评审；A11
  EVAL 门禁（transitional waiver 期内可暂时 `eval_references` 注释 TODO）。
- **system prompt 修改**（`src/mj_agent/prompts/system.md`）—— `version` bump
  必触发 HITL；`eval_references` 同步审查。
- **qcm_catalog.yaml 镜像变更**（`src/mj_agent/biz_catalog/qcm_catalog.yaml`）——
  与上游业务系统数据字典 STANDARD 同步；漂移可能导致 `find_biz_context` 返回
  错误业务语义。
- **SQL guardrail / precheck 规则修改**（`src/mj_agent/tools/sql/{guardrail,precheck}.py`）——
  改动放宽即扩 mj-agent 数据边界（ADR-006 / ADR-009 红线）。

> canonical 的 HITL required-scenarios 10-enum 收敛口径见
> [[../../policies/ai-agent|policies/ai-agent]] §4；本节是其在执行闭环里的展开。
>
> **enforce（per §3.0）**：上述 4 项 in-source 专属必停由 `.claude/settings.json`
> `ask` 列表逐写拍板门 enforce（不再是 `deny` 物理硬锁）——AI 可在 Owner 权限 prompt
> 批准后落盘，合并审查（A13/A14）兜底。"暂停"= 呈现方案 + 等拍板 + 拍板后 AI 落盘，
> **不要求 Owner 手动转写**。

### §3.2 可以默认处理

以下情况 AI 可以自主处理，但需**记录假设**：

- 低风险格式修正
- 拼写、链接、frontmatter 小修
- 明显符合现有模式的重复性代码
- 补充局部测试
- 修复 lint
- 更新与代码变更直接对应的文档
- 根据既有规则选择模板或文档落点

#### Stage 4 豁免（PLAN 落盘）

满足以下**全部 4 项 AND 条件**时，AI 可在 Intake 阶段直接判定 `Plan: 不需要`，
跳过 Stage 4 PLAN 落盘 + Stage 5 HITL Gate 1：

1. **任务性质**：单文件 bugfix / 拼写 / 链接修正 / dependency 版本 patch / 文案微调。
2. **风险等级**：Intake risk-level = `Low`（task-type ∈ `{bugfix, documentation}`）。
3. **Affected areas 不触发 §3.1 mj-agent 专属 4 项必停**：
   - `src/mj_agent/skills/**/SKILL.md` body（runtime-skill-content-change）
   - `src/mj_agent/prompts/system.md` body（prompt-version-bump）
   - `src/mj_agent/biz_catalog/qcm_catalog.yaml`（biz-catalog-sync）
   - `src/mj_agent/tools/sql/{guardrail,precheck}.py`（sql-guardrail-relax）
4. **不涉及** `.env` / `.env.example` / `infra/docker/` / CI workflow /
   `pyproject.toml` `[project.dependencies]` 主条目（version patch 除外）。

豁免必须在 **Intake Result 显式声明** `Plan: 不需要 / 豁免依据=§3.2`；否则
Stage 4 仍为必经阶段。**审计依据**：`grep "Plan: skipped\|Plan: 不需要"
intake-result.md` 用作留痕。

> **豁免边界（明确不覆盖）**：本豁免范围**不包含** §3.1 通用必停 12 项，
> 亦**不包含** in-source canonical / biz catalog / SQL guardrail / Docker
> compose / CI/CD 类变更。

### §3.3 HITL 提问格式

```text
问题 N：
- 当前观察：
- 不确定点：
- 为什么重要：
- 可选方案：
  A.
  B.
  C.
- Owner 执行步骤（仅当需 AI 无法自取的外部信息：ip / port / key / token / endpoint
  等 → 给精确命令 + env 变量名 + 失败现象；详 policies/ai-agent §8）：
- 我的建议：
- 默认假设：
- 是否必须等待人工确认：是 / 否
```

每次最多提出 **3-5 个**关键问题。格式定位 = **选项 + （必要时）可执行步骤**，让 Owner
能"拍板选择"或"照步骤执行"，而非自行编写内容。当 AI 需要无法自取的外部信息时，
`Owner 执行步骤` 字段必填具体命令（见 [[../../policies/ai-agent|policies/ai-agent]] §8
External-Info Handoff Discipline）。

---

## §4 Stage → Skill 映射表

> Port from HITL_Prompt STANDARD §5。目标态与 `.claude/skills/` 内 **32 个**
> mj-agent-* in-tree skills 完全对齐——9 流程编排器（flow family）+ 23 域工具
> skills（git 9 / doc 6 / runtime 4 / infra 4）。各 skill 详细描述见对应
> `.claude/skills/<skill-name>/SKILL.md`。

### §4.1 流程编排器（mj-agent-flow family，9 个 + 1 邻接子纪律 flow-diagnose）

| Stage | 推荐 Skill |
|---|---|
| 0 Intake | [[../../.claude/skills/mj-agent-flow-intake/SKILL\|mj-agent-flow-intake]] |
| 3 Repo Scan | [[../../.claude/skills/mj-agent-flow-repo-scan/SKILL\|mj-agent-flow-repo-scan]] |
| 4 Plan body 编写 | [[../../.claude/skills/mj-agent-flow-plan/SKILL\|mj-agent-flow-plan]] |
| 8 Implementation 编码段 | [[../../.claude/skills/mj-agent-flow-implement/SKILL\|mj-agent-flow-implement]] |
| 8/10 邻接 · 诊断（非新 stage） | [[../../.claude/skills/mj-agent-flow-diagnose/SKILL\|mj-agent-flow-diagnose]]（硬/flaky/perf bug；flow-implement Step 3b 委派） |
| 9 Scope Drift Gate | [[../../.claude/skills/mj-agent-flow-scope-drift/SKILL\|mj-agent-flow-scope-drift]] |
| 10 Local Verification | [[../../.claude/skills/mj-agent-flow-verify/SKILL\|mj-agent-flow-verify]] |
| 11 AI Self-review | [[../../.claude/skills/mj-agent-flow-self-review/SKILL\|mj-agent-flow-self-review]] |
| 13/15 Review/CI 处理 | [[../../.claude/skills/mj-agent-flow-review-respond/SKILL\|mj-agent-flow-review-respond]] |
| 17 Post-merge | [[../../.claude/skills/mj-agent-flow-post-merge/SKILL\|mj-agent-flow-post-merge]] |

### §4.2 域工具 family（git 9 / doc 6 / runtime 4 / infra 4）

| Family | 数量 | Stage / 用途 | 代表 skill |
|---|---|---|---|
| **git** | 9 | 1 Issue / 2 Branch / 12 Commit / 13 Push / 14 PR / 15 Review-others-PR / 16 Merge-check / 17 Delete / 17 Sync | `/mj-agent-git-issue` `/mj-agent-git-branch` `/mj-agent-git-commit` `/mj-agent-git-push` `/mj-agent-git-pr` `/mj-agent-git-review-pr` `/mj-agent-git-check-merge` `/mj-agent-git-delete` `/mj-agent-git-sync` |
| **doc** | 6 | 4 sub Plan / 6 Author / 11 sub Validate / 8 sub Sync / 15 sub Review / archive Migrate | `/mj-agent-doc-plan` `/mj-agent-doc-author` `/mj-agent-doc-validate` `/mj-agent-doc-sync` `/mj-agent-doc-review` `/mj-agent-doc-migrate` |
| **runtime** | 4 | 8 (B-flavor) sub；**propose → 拍板 → apply** | `/mj-agent-runtime-skill-doc-improve` `/mj-agent-runtime-prompt-version-bump` `/mj-agent-runtime-biz-catalog-sync` `/mj-agent-runtime-eval-baseline` |
| **infra** | 4 | 8 (C-flavor) / 10 sub | `/mj-agent-infra-env-setup` `/mj-agent-infra-studio-probe` `/mj-agent-infra-docker-compose` `/mj-agent-infra-storage-stack` |

> **Runtime family 约束（v1.3 / ADR-034）**：所有 `mj-agent-runtime-*` 先做
> **分析 + propose diff + impact 反扫**（列出影响清单），**但落盘前必须 Owner 拍板**——
> 拍板后由 skill 经 `ask` 权限门直接 Edit/Write `src/mj_agent/{skills,prompts,
> biz_catalog,tools}/`（不再"read-only 永不写"、不再甩回 Owner 手动粘贴）。SKILL.md
> `## Anti-patterns` 段明文写 "❌ 未经 Owner 拍板就落盘 / ❌ 跳过 impact 分析直接改"；
> A12 描述质量门禁校验此约束。

---

## §5 Local Verification 矩阵 [GAP #10]

> Port from HITL_Prompt STANDARD §4.8。**Level A 只读 / 无副作用 / 无 HITL**（必跑）
> 与 **Level B DB/LLM 依赖 / 副作用 / HITL-confirm** 分别执行。
> 完整编排步骤见 [[../../.claude/skills/mj-agent-flow-verify/SKILL\|mj-agent-flow-verify]]。

### Level A：只读 / 无副作用 / 无 HITL（必跑）

| 命令 | 用途 |
|---|---|
| `uv run ruff check` | lint（CI 必跑，本地等价） |
| `uv run mypy src/mj_agent` | 类型检查 strict（CI 必跑，本地等价） |
| `uv run pytest tests/unit` | unit tests（无外部依赖） |
| `uv run pytest tests/eval` | eval tests（seed schema + Component check，无 DB） |
| `python -m compileall src` | 编译可解析 |
| `python scripts/check_wikilinks.py` | 文档 wikilinks（docs/ 改动时） |
| `python scripts/check_frontmatter.py` | 文档 frontmatter（docs/ 改动时） |

### Level B：DB / LLM 依赖 / 副作用 / **HITL-confirm**

| 命令 | 用途 | HITL 触发条件 |
|---|---|---|
| `uv run pytest tests/integration` | integration（需 live biz DB） | 需 `POSTGRES_ANALYST_USER` |
| `uv run pytest tests/smoke -m smoke` | smoke（需 live biz DB + Ark API） | 需 `ARK_API_KEY`；CI 不跑 |
| `uv run pytest tests/contract -m contract` | contract | 需 DB creds |
| `uv run mj-agent check` | DB + LLM creds 健康探针 | 需 `.env` 充实 |
| `uv run langgraph dev` | LangGraph Studio 起服务 | 需 `.env` + Ark；交互式探针 H1/H2/H3/R1/R2 |
| `docker compose ... up -d` | mj-agent compose 启动 | 需上游业务系统栈先 up；本地 docker daemon |
| `docker compose ... down` | compose 清理 | 同上 |

按影响范围（实现 3 风味）检查：

- **风味 A 纯代码**：Level A 全跑；Level B 按改动域选（碰 SQL/biz 必跑
  integration + Studio 探针）。
- **风味 B in-source canonical**：Level A + Studio 探针（手动看 LLM 行为差异）
  + smoke（业务样本对比）。
- **风味 C infra**：Level A + 必跑 `mj-agent check` + compose up/down 排练 +
  Studio 探针。

关键测试失败且原因不明时**必须 HITL**。

---

## §6 AI Self-review 检查清单 [GAP #10]

> Port from HITL_Prompt STANDARD §4.9。commit 前（HITL Stage 11）逐项自检。
> 完整编排见 [[../../.claude/skills/mj-agent-flow-self-review/SKILL\|mj-agent-flow-self-review]]。

11-item checklist：

1. 改动是否完全对应 Plan / SPEC。
2. 是否超出 scope（含 in-source canonical / biz catalog 触及但 Plan 未声明）。
3. 是否改变 API、schema、权限、配置、依赖、用户可见行为。
4. 是否有 hardcode、secret、绝对路径、调试代码（特别检查 `.env` /
   `secrets.enc` / Ark API key）。
5. **文档同步检查（5a/5b/5c/5d 反向扫描）**：
   - **5a 既有文档失真扫描**：基于本次 diff 中 rename / move / delete 的函数 /
     类 / 文件 / SQL 对象 / 列，反向 grep `docs/**/*.md` + `CLAUDE.md` +
     **`src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md`**（runtime
     canonical 是反向扫描目标）中 backtick 包裹的引用，列出命中并在 PR
     description 说明已更新或决定不更新（含理由）；不涉及上述 5 类改动时须显式
     记录"不涉及反向扫描"。
   - **5b 新文档创建确认**：比对 Repo Scan Documentation Decision 表中
     Action=Create 的所有行，确认对应 Plan / SPEC / ADR / RUNBOOK / GUIDE /
     STANDARD / 本地 ISSUE / ASSESSMENT 已创建并填入 frontmatter。
   - **5c INDEX / CLAUDE.md / CHANGELOG.md 同步**：按文档框架 allowlist 检查
     `CLAUDE.md`；按 A5 检查 `INDEX.md`；按 PR template CHANGELOG 字段判断。
   - **5d SPEC Delta Check**：若本任务创建/更新了 SPEC，对比最终 diff、验证
     结果与 review/CI 发现，判断 SPEC 是否遗漏关键契约 / 配置 / 错误处理 /
     幂等 / 回滚 / 验证 / 可观测性。无漏项输出 `SPEC Delta: None`；不涉及 SPEC
     时显式输出"不涉及 SPEC Delta"。
6. acceptance criteria 是否都有验证证据。
7. 是否有不应提交的文件（`.env` / `*.pyc` / `.venv/` / log files）。
8. **biz catalog drift**：若 `qcm_catalog.yaml` 改动，与上游业务系统数据字典
   STANDARD 是否一致（`scripts/diff_biz_schema.py`）。
9. **runtime canonical 改动审查**：若 `src/mj_agent/skills/**/SKILL.md` 或
   `src/mj_agent/prompts/*.md` 改动，A11 / A8 EVAL 同步审查 + frontmatter
   `version` bump + Domain Expert 评审签字。
10. **system.md `version` bump 检查**：若 system.md `version` 字段改变，必须
    同步 `eval_references` 字段（transitional waiver 期内可注释 TODO）。
11. commit type 是否匹配 branch type（`documentation/*` 仅 `docs`；`feature/*`
    ∈ {feat, perf, refactor, test, docs}）+ commit scope 是否在闭合 allowlist 内。

> 发现 secret、无关改动、关键测试失败、in-source canonical 未 HITL、中高风险
> 残留时**必须 HITL**。

---

## §7 Post-merge sedimentation policy（Stage 17）

> Port from HITL_Prompt STANDARD §4.15（post-merge prompt Rules 9/10/11）。Stage 17 收尾阶段的
> 沉淀闸；§1 stage 17 列出的 "EVAL backlog ticket 自动开单 / SPEC-* 漏项沉淀" 即指本节。完整收尾
> 编排见 [[../../.claude/skills/mj-agent-flow-post-merge/SKILL\|mj-agent-flow-post-merge]]。

### §7.1 ASSESSMENT-on-optimization 闸（Rule 9）

任务类型为 **optimization**，或 feature **含重构 / 性能改造** 时：必须判定是否建 ASSESSMENT 对比
改造效果。pre-change 阶段未识别 ASSESSMENT 需求时，**post-merge 是最后一道闸**——决定**不**建
ASSESSMENT 必须在 post-merge checklist **显式记录原因**（如"优化未达预期 measurable improvement"）。

### §7.2 SPEC-miss 沉淀阶梯（Rule 10）

若本任务在 self-review / Review / CI 阶段产生 `SPEC-*` 漏项（按 `docs/_templates/TEMPLATE_SPEC.md`
§3 Contract 子项命名 + SPEC Authoring GUIDE §5 短码映射），按层级沉淀：

1. **默认**：PR description「AI 自检」段累计 `SPEC Delta: <code> @ <section>`；
2. **触发达标后**（≥ 3 真实漏项跨 ≥ 2 任务）：新建 / 追加 `plans/[PLAN]_SPEC_Authoring_Miss_Ledger.md`；
3. **升级 POSTMORTEM**：仅当漏项导致 merge 后事故 / 生产影响 / 数据错误 / CI-CD 发布失败 / P1-P2
   级返工时，才写 `docs/postmortem/[POSTMORTEM]_*.md`。

### §7.3 EVAL-backlog 自动开单（Rule 11；A11 transitional-waiver 兜底）

若本 PR 触及 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/system.md` body 修改，
**无论本 PR 是否带 EVAL 引用**，均开 follow-up Issue：`[EVAL backlog] <skill_name | prompt_name>
@ <commit_sha>`，归 Phase D（Phase 2）EVAL framework 时一并完成。这是 A11 transitional-waiver 期内
的兜底机制；触发面对应 [[../../policies/ai-agent|policies/ai-agent]] §4 canonical 10-enum 的
`runtime-skill-content-change` / `prompt-version-or-body-change`。

### §7.4 Milestone / Phase closure 收幕清单（v1.2；completion-audit PR4）

> 背景：M6 closure 后的完成度评估发现 6 项"登记外"债务（既不在 Phase-2 defer 也不在 M6-FU
> register）——逃逸根因是 closure 只对账了 register 内条目，没有全仓扫尾。任何 Milestone /
> Phase 宣布 closure 的 PR，post-merge（Stage 17）必须执行下列三项收幕检查，结果写进
> closure PR body 或 plan 的 phase_progress 块：

1. **TBD-M\<N\> 大扫除**：`grep -rn "TBD-M<N>\|TBD: Phase M<N>" --include="*.md" --include="*.yml"`
   全仓扫描本阶段到期占位；逐条处置（实装 / 改指真实物 / ceremony 登记 defer / decline），
   零静默滚动——滚动必须在 M-FU registry 留行。
2. **M-FU registry 对账批处理**：沿 Action-N-2 批次表格式核对本阶段全部 M-FU 条目
   disposition（completed / deferred→slug / WITHDRAWN+理由 / active+owner）；登记外发现项
   一律补行。
3. **gates.md 阻塞模式 vs ci.yml 真值抽查**：逐 gate 比对 `sdd/gates.md` 真值列与
   `.github/workflows/ci.yml` per-step `continue-on-error` 实况（含 step 名内嵌基线计数是否
   陈旧）；偏差要么修文档要么走 `ci-blocking-gate-toggle` HITL 修 CI——不允许带偏差 closure。

> **Rule 12（PR 关联 plan state 标记）不在本节**——其 `active → completed` 落地在
> [[../lifecycle|sdd/lifecycle]] §2.2（Stage 17 自动化），漏落盘事后补救在 §2.5。

---

## §8 Cross-refs

- **每个 stage 的 detailed prompt**（源 §4.1-§4.15 完整步骤 + Output 结构）：由
  `.claude/skills/mj-agent-*` SKILL 拥有（active 执行路径）——`mj-agent-flow-*`
  编排器是入口，git / doc / runtime / infra 域工具承载具体步骤；本文件只持
  骨架 + 映射，不复制 prompt body。
- **HITL required-scenarios 10-enum**（canonical 收敛口径）：
  [[../../policies/ai-agent|policies/ai-agent]] §4。
- **文档治理门禁 A1-A6**（frontmatter / wikilink / INDEX / allowlist）：
  [[../../policies/documentation|policies/documentation]]。
- **capability 状态迁移工作流**（本闭环的 capability-scoped 投影）：
  [[new-capability|new-capability]]（idea → active）/
  [[evolve-capability|evolve-capability]]（spec 演进）/
  [[bugfix-drift|bugfix-drift]]（缺陷与漂移修复）/
  [[cross-capability-change|cross-capability-change]] /
  [[hotfix|hotfix]] / [[archive-capability|archive-capability]]。
- **capability lifecycle**（本闭环与状态机的关系）：
  [[../lifecycle|sdd/lifecycle]]。
- **关联 ADR**：[[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]]
  （in-tree skills 命名空间 + lifecycle）/
  [[../../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]
  （in-tree vs marketplace SKILL schema 边界）/
  [[../../decisions/ADR-006_Fail_Safe_Reads|ADR-006]] +
  [[../../decisions/ADR-009_Biz_Domain_As_Primary_Data_Source|ADR-009]]
  （数据边界红线，对应 §3.1 SQL guardrail 必停）/
  [[../../decisions/ADR-014_Tri_Track_Documentation_Governance|ADR-014]]
  （tri-track 边界）。
- **历史源 STANDARD 的派生缘起** 由 deprecated ADR-015（HITL_Prompt v1.0
  Derivation）记录；该 ADR 已 superseded，本文件不持其 wikilink，仅以编号在
  prose 中引用。

---

> *M6-PR4a kernel-authoring 收尾件；本文件为 17-stage 执行闭环 kernel home。
> 源 STANDARD 归档由 M6 PR4 执行。*
