---
type: sdd-workflow
artifact: execution-loop
state: active
version: "1.6"
owner: ranzuozhou
created: 2026-06-04
updated: 2026-10-12
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
> 源 STANDARD 已由 M6 PR4 归档 →
> `archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt_v1_1.md`
> （原居 `docs/rule/`，归档后该目录不再持有此 STANDARD；下文以 HITL_Prompt 为「历史源」的
> 提法均指该归档件）。
>
> **不在本文件 re-port 的内容（cross-ref，避免重复）**：
> - 每个 stage 的 **detailed prompt**（源 §4.1-§4.15 的完整步骤 + Output 结构）由
>   `.agents/skills/mj-agent-*` SKILL 拥有（active 执行路径）+ HITL_Prompt §4
>   历史源；本文件只持 stage 骨架 + stage→skill 映射。
> - HITL **required-scenarios 10-enum**（canonical 收敛口径）住在
>   [[../../policies/ai-agent|policies/ai-agent]] §4。
> - 文档治理门禁 **A1-A6**（frontmatter / wikilink / INDEX / allowlist）住在
>   [[../../policies/documentation|policies/documentation]]。

---

## §1 交付闭环与阶段检查点

阶段保留身份和记录位置，不产生固定人工等待；stages 5/7/9/11/13 是对齐、核验和授权检查点。Agent 在已有任务授权内自主完成常规设计、实现、验证、文档及修复；实质决定与技术边界按 `policies/ai-agent.md` §4 判断。

0. Intake：目标、接受基线、授权、风险与实际前置。
1. Issue：复用任务系统，必要发布核对授权。
2. Branch：核对真实工作区，新增分支通过 worktree。
3. Repo Scan：核实规格、实现、依赖与文档。
4. Plan：按依赖与风险自主拆解，明确 AC 和证据。
5. 基线检查点：核对 Plan/风险/文档；未决实质选择交 Owner。
6. SPEC/ADR/必要文档：按真实行为同步。
7. 设计检查点：普通技术选择自主，实质取舍取得决定。
8. Implementation：实现、适用 TDD/根因诊断、文档和局部修复。
9. Scope Drift：对真实 diff 反扫，边界越界只停受影响项。
10. Verification：离线验证及已授权适用运行行为。
11. Self-review + 独立核验：真实成果、独立期望和可复现证据。
12. Commit：任务授权内核对 staged 内容与来源。
13. Push：核对版本、目标与风险，失败先对账。
14. PR：选择单 PR、独立多 PR 或精确登记的分层结构。
15. Review/CI：自主修复，接受条件变化交 Owner。
16. Delivery/Merge：门禁及平台有效审核满足后在授权内执行。
17. 收尾与接受：核实集成/运行成果、验收包、延期与恢复；Owner 明确接受后才标任务 completed。

成果可见性决定接受与发布顺序，仓库批准、部署授权、运行验收与业务接受分记。子 PR 已合并仅表示候选集成。独立可信核验、actual 采样、部署自动化及实际恢复演练首期延期，未测与延期不计 PASS。

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
- 如果参考文档、Issue、Plan、代码现状冲突，先核实事实并自主修复基线内差异；实质目标、接受标准或风险冲突再请求 Owner 决定

### §2.2 Skill Hint 规则

若某阶段已有对应技能（`mj-agent-*` 命名空间），应在 Prompt 中标记推荐 slash
command，但**不**把它作为唯一执行路径——同时给出 `Use When` + `Fallback`（skill
不可用时按本 prompt 手动执行）。

> **mj-agent 命名空间约定**：所有 in-tree workflow skill 强制使用
> `mj-agent-<group>-<verb>` 三段式（`<group>` ∈ {flow, git, doc, runtime,
> infra}）；slash command 为 `/mj-agent-<group>-<verb>`。命名空间 + lifecycle
> 由 [[../../decisions/ADR-016_In_Tree_Claude_Skills_Ecosystem|ADR-016]] 治理。

---

## §3 决定、授权与检查点

### §3.0 决定与实际执行路线

先完成具体可审阅差异、影响、证据与恢复方案。对实质变化由 Owner 决定；已有明确任务授权覆盖的普通实现与已批准方案由 Agent 正常工具执行。成组治理改造不部分切换；独立Agent先读取真实原生配置/守卫并复现负例，执行Agent随后仅经宿主正常机制启用本项目信任、核实际加载/canary；不改个人config、不扩大权限、不绕技术拒绝。不支持的步骤如实未验证。授权不解锁实际拒绝，受阻步骤保留原错并返回 `BLOCKED_EXECUTION_ROUTE`，不绕过。

### §3.1 按语义影响停止

`policies/ai-agent.md` §4 canonical 10-enum 是风险定位标签，四类 runtime 路径及兼容契约命中本身不审批。SQL 安全不变量、数据范围、业务口径、外发边界、breaking 承诺、目标/AC、必要门禁、信任/权限、生产策略或供应链信任来源变化需要 Owner 决定。未授权删除/迁移、不可逆操作、资源越界或未知风险只停受影响项。

基线内实现、重构、局部修复、普通 Plan 和文档自主完成，提供行为及负例证据。失败先定位与修复，不能删除断言、忽略红灯或降低 AC 获得通过；决定改变 AC 交 Owner。技术权限、CI 全绿及模型 effort 均不产生授权。

### §3.2 按规模裁剪与状态恢复

单文件低风险改动可用已有 Issue/PR 记录替代单独 Plan，明确复用载体及验证即可。复杂、多单元或治理任务使用 Plan/任务清单，不机械新增材料。阶段结束、集成前/交接形成检查点：目标/AC/授权、版本/工作区/集成、证据、在途/失败/未知/延期、下一步及停止条件。重入核事实与副作用，成功项不重复。

普通授权在目标、对象、环境、权限和风险未实质变化且未撤销时复用，实际 diff/SHA 仍核验。任务可列 stage/commit、普通 push、PR/merge，删除与权限变更独立列明。Plan completed 须基线满足、成果可用且 Owner 明确接受版本；merge 不自动完成。

### §3.3 实质决定提问格式

一次聚焦一项真实取舍，先探索可自取事实；提供当前观察、为何影响结果、互斥可行选项、推荐项与理由/影响、必须等待的原因。没有新增实质决定就继续授权内工作。先自取可用公开事实；既有秘密不读取、不索取值。新单仓App材料仅受控后台处理；独立Agent技术审阅后，执行Agent按授权与正常宿主机制实施项目范围启用。不支持或拒绝如实未验证。

## §4 Stage → Skill 映射表

> Port from HITL_Prompt STANDARD §5。目标态覆盖 `.agents/skills/` 内 **37 个** mj-agent-*
> in-tree skills——flow family 10（9 流程编排器 + 1 邻接子纪律 flow-diagnose）+ 27 域工具
> skills（git 9 / doc 6 / runtime 4 / infra 8）。**on-disk 实装计数以
> `scripts/sdd/check_native_skills.py` 为准**（ADR-016 设计态目标 32 与实装
> 存在既有 drift；跨文档计数全量刷新 / 去硬写 = M-FU，tracked #267 + `docs/INDEX.md`
> §技能清单合计行）。各 skill 详细描述见对应 `.agents/skills/<skill-name>/SKILL.md`。

### §4.1 流程编排器（mj-agent-flow family，9 个 + 1 邻接子纪律 flow-diagnose）

| Stage | 推荐 Skill |
|---|---|
| 0 Intake | [[../../.agents/skills/mj-agent-flow-intake/SKILL\|mj-agent-flow-intake]] |
| 3 Repo Scan | [[../../.agents/skills/mj-agent-flow-repo-scan/SKILL\|mj-agent-flow-repo-scan]] |
| 4 Plan body 编写 | [[../../.agents/skills/mj-agent-flow-plan/SKILL\|mj-agent-flow-plan]] |
| 8 Implementation 编码段 | [[../../.agents/skills/mj-agent-flow-implement/SKILL\|mj-agent-flow-implement]] |
| 8/10 邻接 · 诊断（非新 stage） | [[../../.agents/skills/mj-agent-flow-diagnose/SKILL\|mj-agent-flow-diagnose]]（硬/flaky/perf bug；flow-implement Step 3b 委派） |
| 9 Scope Drift Gate | [[../../.agents/skills/mj-agent-flow-scope-drift/SKILL\|mj-agent-flow-scope-drift]] |
| 10 Local Verification | [[../../.agents/skills/mj-agent-flow-verify/SKILL\|mj-agent-flow-verify]] |
| 11 AI Self-review | [[../../.agents/skills/mj-agent-flow-self-review/SKILL\|mj-agent-flow-self-review]] |
| 13/15 Review/CI 处理 | [[../../.agents/skills/mj-agent-flow-review-respond/SKILL\|mj-agent-flow-review-respond]] |
| 17 Post-merge | [[../../.agents/skills/mj-agent-flow-post-merge/SKILL\|mj-agent-flow-post-merge]] |

### §4.2 域工具 family（git 9 / doc 6 / runtime 4 / infra 8）

| Family | 数量 | Stage / 用途 | 代表 skill |
|---|---|---|---|
| **git** | 9 | 1 Issue / 2 Branch / 12 Commit / 13 Push / 14 PR / 15 Review-others-PR / 16 Merge-check / 17 Delete / 17 Sync | `/mj-agent-git-issue` `/mj-agent-git-branch` `/mj-agent-git-commit` `/mj-agent-git-push` `/mj-agent-git-pr` `/mj-agent-git-review-pr` `/mj-agent-git-check-merge` `/mj-agent-git-delete` `/mj-agent-git-sync` |
| **doc** | 6 | 4 sub Plan / 6 Author / 11 sub Validate / 8 sub Sync / 15 sub Review / archive Migrate | `/mj-agent-doc-plan` `/mj-agent-doc-author` `/mj-agent-doc-validate` `/mj-agent-doc-sync` `/mj-agent-doc-review` `/mj-agent-doc-migrate` |
| **runtime** | 4 | 8 (B-flavor) sub；**分析 → 影响分类 → 实施/决定** | `/mj-agent-runtime-skill-doc-improve` `/mj-agent-runtime-prompt-version-bump` `/mj-agent-runtime-biz-catalog-sync` `/mj-agent-runtime-eval-baseline` |
| **infra** | 8 | 8 (C-flavor) / 10 sub / env teardown / LLM endpoint probe / 10 sub app-start · 17 sub app-stop | `/mj-agent-infra-env-setup` `/mj-agent-infra-env-teardown` `/mj-agent-infra-studio-probe` `/mj-agent-infra-docker-compose` `/mj-agent-infra-storage-stack` `/mj-agent-infra-llm-endpoint-probe` `/mj-agent-infra-app-start` `/mj-agent-infra-app-stop` |

> **Runtime family**：先分析、差异及 impact 反扫；基线内保持安全/业务/外发边界的改善自主 apply，语义越界按 §3.1 作实质决定。保持 frontmatter/版本/EVAL/冻结契约与独立角色核验，实际拒绝不绕过。

---

## §5 Local Verification 矩阵 [GAP #10]

> Port from HITL_Prompt STANDARD §4.8。**Level A 只读 / 无副作用 / 无 HITL**（必跑）
> 与 **Level B DB/LLM 依赖 / 副作用 / 具名授权** 分别执行。
> 完整编排步骤见 [[../../.agents/skills/mj-agent-flow-verify/SKILL\|mj-agent-flow-verify]]。

### Level A：只读 / 无副作用 / 无 HITL（必跑）

| 命令 | 用途 |
|---|---|
| `uv run ruff check` | lint（CI 必跑，本地等价） |
| `uv run mypy src/mj_agent` | 类型检查 strict（CI 必跑，本地等价） |
| `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit` | unit tests（无外部依赖） |
| `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/eval` | eval tests（seed schema + Component check，无 DB） |
| `python -m compileall src` | 编译可解析 |
| `python scripts/check_wikilinks.py` | 文档 wikilinks（docs/ 改动时） |
| `python scripts/check_frontmatter.py` | 文档 frontmatter（docs/ 改动时） |

### Offline pytest external bands（只验证 structured skip）

Agent/CI 发起的 pytest 始终走 hardened runner。凭据存在不会启用 live route；biz live pytest
永久不可用，non-biz external 需未来独立 Owner-approved profile。当前这些命令只验证
`SKIP_POLICY_EXTERNAL_DEPENDENCY`，不算 live integration 证据。

| 命令 | 用途 |
|---|---|
| `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/integration` | integration collection + biz-live policy skip |
| `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/smoke -m smoke` | smoke collection + external policy skip |
| `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/contract -m contract` | contract collection + biz-live policy skip |

### Level B：DB / LLM 依赖 / 副作用 / **具名授权**

| 命令 | 用途 | HITL 触发条件 |
|---|---|---|
| `uv run mj-agent check` | DB + LLM creds 健康探针 | 需 `.env` 充实 |
| `uv run langgraph dev` | LangGraph Studio 起服务 | 需 `.env` + Ark；交互式探针 H1/H2/H3/R1/R2 |
| `docker compose ... up -d` | mj-agent compose 启动 | 需上游业务系统栈先 up；本地 docker daemon |
| `docker compose ... down` | compose 清理 | 同上 |

按影响范围（实现 3 风味）检查：

- **风味 A 纯代码**：Level A 与 offline pytest external bands 全跑；Level B 按改动域选
  （碰 SQL/biz 时，live 证据走 sanctioned probe / Studio，不以 pytest 代替）。
- **风味 B in-source canonical**：Level A + 对是否运行 Studio / sanctioned live probe 的
  显式 Owner 决策；pytest smoke 仅证明结构化 policy skip，不作为业务样本 live 证据。
- **风味 C infra**：Level A；健康探针、compose 排练及 Studio 按任务需要与具名运行授权执行，缺运行条件明确未验证。

关键测试失败由 Agent 自主定位修复；未知风险影响资源、安全或 AC 时暂停受影响项并请 Owner 决定。

---

## §6 AI Self-review 检查清单 [GAP #10]

> Port from HITL_Prompt STANDARD §4.9。commit 前逐项自检，并由独立核验者从 AC 建立期望读取真实成果。
> 完整编排见 [[../../.agents/skills/mj-agent-flow-self-review/SKILL\|mj-agent-flow-self-review]]。

11-item checklist：

1. 改动是否完全对应 Plan / SPEC。
2. 是否超出 scope（含 in-source canonical / biz catalog 触及但 Plan 未声明）。
3. 是否改变 API、schema、权限、配置、依赖、用户可见行为。
4. 是否有 hardcode、secret、绝对路径、调试代码（特别检查 `.env` /
   `secrets.enc` / Ark API key）。
5. **文档同步检查（5a/5b/5c/5d 反向扫描）**：
   - **5a 既有文档失真扫描**：基于本次 diff 中 rename / move / delete 的函数 /
     类 / 文件 / SQL 对象 / 列，反向 grep `docs/**/*.md` + `AGENTS.md` +
     **`src/mj_agent/skills/**/SKILL.md` + `src/mj_agent/prompts/*.md`**（runtime
     canonical 是反向扫描目标）中 backtick 包裹的引用，列出命中并在 PR
     description 说明已更新或决定不更新（含理由）；不涉及上述 5 类改动时须显式
     记录"不涉及反向扫描"。
   - **5b 新文档创建确认**：比对 Repo Scan Documentation Decision 表中
     Action=Create 的所有行，确认对应 Plan / SPEC / ADR / RUNBOOK / GUIDE /
     STANDARD / 本地 ISSUE / ASSESSMENT 已创建并填入 frontmatter。
   - **5c INDEX / AGENTS.md / CHANGELOG.md 同步**：按文档框架 allowlist 检查
     `AGENTS.md`；按 A5 检查 `INDEX.md`；按 PR template CHANGELOG 字段判断。
   - **5d SPEC Delta Check**：若本任务创建/更新了 SPEC，对比最终 diff、验证
     结果与 review/CI 发现，判断 SPEC 是否遗漏关键契约 / 配置 / 错误处理 /
     幂等 / 回滚 / 验证 / 可观测性。无漏项输出 `SPEC Delta: None`；不涉及 SPEC
     时显式输出"不涉及 SPEC Delta"。
6. acceptance criteria 是否都有验证证据。
7. 是否有不应提交的文件（`.env` / `*.pyc` / `.venv/` / log files）。
8. **biz catalog drift**：若 `qcm_catalog.yaml` 改动，与上游业务系统数据字典 STANDARD
   是否一致。检测器 = `scripts/diff_biz_schema.py`，**只读**
   `.mj-agent-local/biz-schema-snapshots/`（gitignored）下 Owner 背书的 sanitized 快照，
   不连任何数据库。无快照 / 快照超 7 天 → `SKIP_NO_SNAPSHOT` / `SKIP_STALE_SNAPSHOT`
   （均 exit 0）：**SKIP 不是 PASS**，须如实记为「未验证」，不得据此声称 catalog 与当前
   数据库一致。
9. **runtime canonical 改动审查**：若 `src/mj_agent/skills/**/SKILL.md` 或
   `src/mj_agent/prompts/*.md` 改动，A11 / A8 EVAL 同步审查 + frontmatter
   `version` bump + 独立领域视角核验记录（不要求真人或固定人数）。
10. **system.md `version` bump 检查**：若 system.md `version` 字段改变，必须
    同步 `eval_references` 字段（transitional waiver 期内可注释 TODO）。
11. commit type 是否匹配 branch type（`documentation/*` 仅 `docs`；`feature/*`
    ∈ {feat, perf, refactor, test, docs}）+ commit scope 是否在闭合 allowlist 内。

> 发现 secret 或安全边界风险暂停受影响项；范围内失败自主修复。实质变化、未授权操作或接受风险越界才请求 Owner 决定。

---

## §7 Post-merge sedimentation policy（Stage 17）

> Port from HITL_Prompt STANDARD §4.15（post-merge prompt Rules 9/10/11）。Stage 17 收尾阶段的
> 沉淀闸；§1 stage 17 列出的 "EVAL backlog ticket 自动开单 / SPEC-* 漏项沉淀" 即指本节。完整收尾
> 编排见 [[../../.agents/skills/mj-agent-flow-post-merge/SKILL\|mj-agent-flow-post-merge]]。

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
  `.agents/skills/mj-agent-*` SKILL 拥有（active 执行路径）——`mj-agent-flow-*`
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
> 源 STANDARD 归档已由 M6 PR4 执行完毕（归档件路径见文首 kernel home note）。*
