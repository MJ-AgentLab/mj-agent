---
type: standard
domain: SYS
summary: mj-agent canonical 文档层的人工入口，Phase 2 接入自动生成
owner: 项目负责人
created: 2026-04-24
updated: 2026-05-18
state: draft
track: shared
---

# mj-agent 文档索引

> **A4（per ADR-031 Phase M0）**：本 INDEX 承担 **codebase map** 角色 — 当 Claude Code 不
> 确定路径时优先读此文件，再下钻具体子目录 `INDEX.md` / `CLAUDE.md`.
>
> **互引（per spec-anchored-refactor）**：
> - 治理元规则：[../sdd/constitution.md](../sdd/constitution.md) +
>   [../sdd/lifecycle.md](../sdd/lifecycle.md) + [../sdd/gates.md](../sdd/gates.md)
> - Capability：[../capabilities/INDEX.md](../capabilities/INDEX.md)（Phase M1 起 5 pilot）
> - Business Policy：[../policies/](../policies/)（9 native 文件）
> - ADR 新址：[../decisions/INDEX.md](../decisions/INDEX.md)（Phase M5 平移；当前 ADR-031 draft）
> - Codex 边界：[../AGENTS.md](../AGENTS.md)
> - 术语表：[../GLOSSARY.md](../GLOSSARY.md)

> 本索引（旧版区段）是 **手写初版**。按 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework|mj-agent 文档治理元框架 v2.0]] §6.2，
> 进入 Phase 2 后将改为从各文档 frontmatter `summary` 字段扫描生成。

---

## 规则（docs/rule/）

| 文档 | 摘要 |
|------|------|
| [[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|mj-agent 文档治理元框架 v2.2]] (active；stable path) | 元框架 v2.2 — 引入 §4.4 active canonical 路径稳定原则（ADR-018；上游业务系统 v5.2 §4.1 派生；partial supersede ADR-011 §4.2 + §5.6.2）；v2.1 sustained §3.10 + §7.6 + §5.9；v2.1/v2.0 已 archive |
| [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|mj-agent 代码侧文档治理框架 v1.1（Track A）]] (active) | Track A minor bump（v1.0 → v1.1）— §0/§3.9/§7.3 加注 Track C engineering-workflow 共享 A1-A6 + cross-ref 工程流程 STANDARDs；与 Meta v2.1 同期 promote；v1.0 已 archive |
| [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework\|mj-agent 智能体侧文档治理框架 v1.2（Track B）]] (active；stable path) | Track B v1.2 — §4 EVAL Authoring 完整规范（4 子类 outcome/trajectory/component/integration + body 八段 + frontmatter schema；ADR-024 决议）；A8/A11 transitional waiver 延续 Phase E；v1.1 已 archive；§5/§6/§7.x sustained from v1.1 |
| [[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt\|mj-agent AI 工程执行闭环与 HITL Prompt 规范 v1.0]] (active) | Track C 主 STANDARD（engineering-workflow）；规范 AI 在 mj-agent 17 阶段执行闭环（Intake → Post-merge）的 prompt 结构、引用规则与 HITL 触发条件；§3.1 通用 + 4 项 mj-agent 专属必停规则（runtime-skill / prompt-version / biz-catalog / sql-guardrail）；§4 含 3 风味 Implementation（A 纯代码 / B in-source canonical 永远 HITL / C infra）+ EVAL backlog ticket 自动开单 |
| [[STANDARD]_GitHub_Markdown\|GitHub-Flavored Markdown 编写规范 v1.0]] | 定义 mj-agent 文档在 GitHub 渲染的 Markdown + YAML 语法规范，覆盖 GFM 13 节排版规则，与 Meta_Framework v2.1 §4 字段语义互补 |
| [[STANDARD]_MJ_Agent_Commit_Message_Convention\|MJ-Agent Commit Message 规范 v1.0]] | mj-agent 的 Conventional Commits 规范，定义 type、mj-agent 专属 scope、分支对齐矩阵与示例（draft） |

## 架构决策（docs/adr/）

> 2026-05-11 cross-repo decoupling cleanup（PR-Γ）后：9 个"记录从早期内部上游系统继承设计决策"的 ADR（010/015/017/018/019/021/022/023/025）已批量 archive 到 [[archive/adr/INDEX|docs/archive/adr/]]；其内容已沉淀为对应 framework STANDARD 段。ADR-025 拆分为 mj-agent 原生 ADR-026/027/028。

| 文档 | domain | decision | 摘要 |
|------|--------|----------|------|
| [[ADR]_000_Data_LLM_Boundary_Principles\|ADR-000 Data-LLM Boundary Principles]] | DATA | accepted | 最小必要出网、通道隔离、工具中介——后续所有安全相关决策的理论基础 |
| [[ADR]_001_Python_Only_Agent_Runtime\|ADR-001 Python-Only Agent Runtime]] | SYS | accepted | Agent 逻辑、tools、skills、memory 全部留在 Python；前端仅作通信与渲染 |
| [[ADR]_002_Skills_As_First_Class_Citizens\|ADR-002 Skills as First-Class Citizens]] | SKILL | accepted | 所有专业能力以 `skills/{name}/SKILL.md` 格式封装，对齐 Claude Code skills 约定 |
| [[ADR]_003_Progressive_Disclosure\|ADR-003 Progressive Disclosure]] | PROMPT | accepted | 全局 system prompt 只含身份与原则；具体能力按需加载 |
| [[ADR]_006_Fail_Safe_Reads\|ADR-006 Fail-Safe Reads]] | GUARDRAIL | accepted | biz 库访问用只读账号 + SQL guardrail middleware 双层保护；4 层防御（L1-L4） |
| [[ADR]_008_Co_Deployment_With_Upstream_Warehouse\|ADR-008 Co-Deployment with Upstream Business Warehouse]] | OPS | accepted | mj-agent 是独立 compose project（自带 postgres + redis），通过 `mj-system-backend-network` (external) Docker network 仅以 consumer 身份访问上游业务系统 biz pg；环境矩阵与上游时间表对齐但 lifecycle 解耦 |
| [[ADR]_009_Biz_Domain_As_Primary_Data_Source\|ADR-009 Biz Domain as Primary Data Source]] | INTEGRATION | accepted | mj-agent 仅通过只读账号访问 biz 域，不访问 ODS/DWD 原始层 |
| [[ADR]_011_Doc_Versioning_And_Archive_Convention\|ADR-011 Document Versioning and Archive Convention]] | SYS | accepted | 文档治理新增 Major.Minor 版本演进与 docs/archive/ 归档机制（HITL 触发，A3 模式 = git branch + PR review） |
| [[ADR]_012_Two_Track_Documentation_Governance\|ADR-012 Two-Track Documentation Governance]] | SYS | accepted (state: draft) | 决议引入双轨文档治理（Code_Side + Agent_Side + Meta 元层）+ skeleton-first 演进 + 双 plugin 骨架 |
| [[ADR]_013_Plugin_SKILL_md_Schema_Separation\|ADR-013 Plugin SKILL.md Schema Separation]] | SYS | accepted (state: draft) | marketplace plugin SKILL.md 使用 Claude Code 原生 schema（name + description 两字段），与 mj-agent in-source SKILL.md 的 13 字段 schema 独立 |
| [[ADR]_014_Tri_Track_Documentation_Governance\|ADR-014 Tri-Track Documentation Governance v2.1]] | SYS | accepted | 决议引入第三轨 engineering-workflow（治理 .claude/ + HITL_Prompt + 工程流程 STANDARD）+ A12-A14 PR 门禁加入；mj-agent-* 命名空间；skeleton-first 落地 |
| [[ADR]_016_In_Tree_Claude_Skills_Ecosystem\|ADR-016 In-Tree .claude/skills/ Ecosystem]] | WORKFLOW | accepted | mj-agent .claude/skills/ in-tree 工程编排技能命名空间 mj-agent-<group>-<verb>（5 family：flow 9 / git 9 / doc 6 / runtime 4 / infra 4 = 32）+ lifecycle (P0/P1/P2 + sunset 规则) |
| [[ADR]_020_Archive_Auto_Discovery\|ADR-020 Archive Auto-Discovery]] | SYS | accepted | scripts/check_wikilinks.py 改为 auto-discover NEEDLES from `docs/archive/rule/[DEPRECATED]_*.md` glob；零维护 archive 引用校验 |
| [[ADR]_024_Eval_Framework_Spec\|ADR-024 EVAL Framework Spec]] | AGENT | accepted | Agent_Side v1.2 §4 EVAL Authoring 完整规范（4 子类 outcome/trajectory/component/integration + body 八段 + frontmatter schema）；mj-agent 原生 |
| [[ADR]_026_Multi_Environment_Compose_Profile\|ADR-026 Multi-Environment Compose Profile]] (PR-Γ；ADR-025 拆分) | OPS | accepted | docker-compose 4-file 分层（base + override + test + prod）；compose project name 跨 profile 不变；dev 也用显式 -f 链（auto-load 不生效 quirk） |
| [[ADR]_027_LLM_Provider_Abstraction\|ADR-027 LLM Provider Abstraction]] (PR-Γ；ADR-025 拆分) | AGENT | accepted | `make_llm()` 抽象为 provider 分支 factory（ark + local-openai-compat 支持 DGX-Spark vLLM/SGLang/Ollama）；Profile enum 不扩 dgx |
| [[ADR]_028_MCP_Server_Inventory_And_Governance\|ADR-028 MCP Server Inventory + Governance]] (PR-Γ；ADR-025 拆分) | WORKFLOW | accepted | `.mcp.json` 13 servers + 新建 `docs/infrastructure/mcp/` STANDARD（领域专属 placement）+ A14 PR gate 实施细则；独立 secrets pipeline |
| [[ADR]_029_Tool_Error_Surfacing_To_LLM\|ADR-029 Tool Error Surfacing to LLM via Middleware]] | AGENT | accepted | `src/mj_agent/middleware/tool_errors.py` 用 `@wrap_tool_call` 把 SQL 工具 ValueError/RuntimeError 转为 ToolMessage；工具函数本身保留 raise 行为；修掉 2026-05-12 frontend hang 根因 |
| [[ADR]_030_Secrets_Bundle_Split_For_MCP_Isolation\|ADR-030 Secrets Bundle Split for MCP Isolation]] | OPS | accepted | 把 MCP 基础设施 secrets（5 SSH + 10 PG URL = 15 keys）从 `config/secrets.enc` 拆出到独立的 `config/secrets-mcp.enc`，解密后直接写 OS User-level env（不入 `.env`）；对齐 mj-system v2.3 `secrets-sys-ops.enc` 范式；新增 `setup-mcp-secrets.ps1` + `encrypt-secrets-mcp.ps1` + `migrate-secrets-bundle-split.ps1`；删除旧 `setup-mcp-env.ps1` |

## 评估（docs/assessments/）

| 文档 | 周期 | 摘要 |
|------|------|------|
| [[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0\|上游业务系统 Git 规范在 mj-agent 的适配评估 v1.0]] | Phase 0 | 评估 上游业务系统 git 基础设施与 commit 规范在 mj-agent 的适用性，给出 Keep/Adapt/Defer 矩阵与社区证据 |

## 归档（docs/archive/）

> Archive 由 Meta_Framework §5 流程触发的版本退役搬迁。详见 [[adr/[ADR]_011_Doc_Versioning_And_Archive_Convention\|ADR-011]] + [[archive/adr/INDEX\|archive/adr/INDEX]]（9 个 cross-repo decoupling 归档 ADR forward gateway）。

### 归档 STANDARDs

| 归档文档 | 取代者 | 归档原因 |
|---|---|---|
| [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.0\|Framework v1.0（archive）]] | [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1\|Framework v1.1（archive）]] | v1.1 引入 §5.6（Major.Minor 版本演进与归档机制）和 §4.2 filename `_vX.Y` 强制规则 |
| [[archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1\|Framework v1.1（archive）]] | v2.0 trio：Meta_Framework v2.0 + Code_Side v1.0 + Agent_Side v1.0 (all archive) | v2.0 引入 `track` frontmatter 字段与双轨子框架；详见 [[adr/[ADR]_012_Two_Track_Documentation_Governance\|ADR-012]] |
| Meta_Framework v2.0 + Code_Side v1.0 + Agent_Side v1.0 (all archive) | v2.1 trio (现 v2.2 stable) + HITL_Prompt v1.0 | v2.1 引入第三轨 engineering-workflow（治理 .claude/ + HITL_Prompt + 工程流程 STANDARD）+ A12-A14 PR 门禁 + §3.10 in-tree workflow SKILL 治理；详见 [[adr/[ADR]_014_Tri_Track_Documentation_Governance\|ADR-014]] |
| Meta_Framework v2.1 (archive) | [[rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.2（stable path）]] | v2.2 引入 §4.4 active canonical 路径稳定原则（已归档 ADR-018 决议；filename rename 触发已归档 ADR-017 §5.9 trigger #4） |

### 归档 ADRs（cross-repo decoupling cleanup，2026-05-11）

详细 forward gateway 见 [[archive/adr/INDEX\|docs/archive/adr/INDEX.md]]。

| 归档 ADR | 替代位置 | 归档原因 |
|---|---|---|
| [[archive/adr/[DEPRECATED]_[ADR]_010_Git_And_Commit_Conventions_From_MJ_System\|ADR-010]] | [[rule/[STANDARD]_MJ_Agent_Commit_Message_Convention\|Commit Message Convention v1.0]] | git/commit 规则已独立 STANDARD 化 |
| [[archive/adr/[DEPRECATED]_[ADR]_015_HITL_Prompt_v1_0_Derivation\|ADR-015]] | [[rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt\|HITL_Prompt v1.1]] | 17-stage 闭环规则已独立 STANDARD 化（§4.1/§4.4 已 inline） |
| [[archive/adr/[DEPRECATED]_[ADR]_017_Archive_Trigger_Quantification\|ADR-017]] | Meta v2.2 §5.9 | 4 必触发判定条款已并入 Meta v2.2 §5.9 |
| [[archive/adr/[DEPRECATED]_[ADR]_018_Active_Path_Stability\|ADR-018]] | Meta v2.2 §4.4 | active 文件名稳定原则已并入 Meta v2.2 §4.4 |
| [[archive/adr/[DEPRECATED]_[ADR]_019_Archive_Naming_Convention\|ADR-019]] | Meta v2.2 §5.11 + [[archive/adr/INDEX\|archive INDEX]] | 归档命名 [DEPRECATED]_ 前缀 + frontmatter 规则已落地为日常实践 |
| [[archive/adr/[DEPRECATED]_[ADR]_021_Working_Doc_Lifecycle\|ADR-021]] | Meta v2.2 §5.11 | plans/ 4 态机已并入 Meta v2.2 §5.11；mj-agent-flow-post-merge SKILL Step 9 自动 active → completed |
| [[archive/adr/[DEPRECATED]_[ADR]_022_P2_Framework_Enhancements\|ADR-022]] | Code_Side v1.1 §3.4-§3.8 + Meta v2.2 §3.7/§3.8/§4.5/§4.6 | 5 项 framework 增强已并入对应 STANDARD 章节 |
| [[archive/adr/[DEPRECATED]_[ADR]_023_Stale_Doc_And_Plan_GC_Infra\|ADR-023]] | `scripts/find_stale_docs.py` + `scripts/find_old_completed_plans.py` 注释 | 实际 scripts 已落地 |
| [[archive/adr/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction\|ADR-025]] | [[adr/[ADR]_026_Multi_Environment_Compose_Profile\|ADR-026]] + [[adr/[ADR]_027_LLM_Provider_Abstraction\|ADR-027]] + [[adr/[ADR]_028_MCP_Server_Inventory_And_Governance\|ADR-028]] | 多 domain bundle ADR 拆分为 3 个焦点 ADR |

## 模板（docs/\_templates/）

| 模板 | 用途 |
|------|------|
| `TEMPLATE_ADR.md` | 架构决策记录骨架 |
| `TEMPLATE_GUIDE.md` | GUIDE 骨架（CN-numbered 详规，codified 自 4 份 reference GUIDE）；规格见 [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.1 |
| `TEMPLATE_SKILL.md` | in-source SKILL 骨架（复制到 `src/mj_agent/skills/<name>/SKILL.md`；13 字段 + 五段式） |
| `TEMPLATE_PROMPT.md` | in-source PROMPT 骨架（复制到 `src/mj_agent/prompts/<name>.md`） |
| `TEMPLATE_CONTRACT.md` | 工具/服务契约骨架 |
| `TEMPLATE_RUNBOOK.md` (Phase A PR-A3；Phase D-1 加 last-verified 字段) | RUNBOOK 骨架；body 七段（TL;DR / Trigger / Pre-checks / Steps / Verification / Rollback / Post-mortem trigger）；frontmatter 含 ADR-022 C.3.1 `last-verified`（state: active 时强制）；规格见 [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.4 |
| `TEMPLATE_SPEC.md` (Phase A PR-A3；PR-118 加 §0 Task Type Identification) | SPEC 骨架；body §0 + 九段（Context / Scope / Contract / Configuration / Error handling / Rollback / Verification / Observability / Open questions）；§0 任务类型识别按 [[guide/[GUIDE]_MJ_Agent_SPEC_Authoring\|SPEC Authoring GUIDE]] §3 决策树 + §4 8 类裁剪规则 |
| `TEMPLATE_REPO_SCAN_RESULT.md` (PR-118 commit-3) | HITL Stage 3 Repo Scan Result 输出结构（对话输出，**不**写文件）；与 `mj-agent-flow-repo-scan` SKILL Output Format 一致；含 8-dim Evidence Map + 10 行 Documentation Decision + Stale Doc Reverse Scan + Plan Verdict + HITL Questions |
| `TEMPLATE_PLAN.md` (PR-118 commit-3) | HITL Stage 4 Plan body 模板（写到 `plans/[PLAN]_*.md`）；轻量 5-6 段（Scope / Task Breakdown / Risk Control / Verification / AC + 可选 Phase 子包 / 严格守约）；从 plans/ 既有 18 份范例综合 |
| `TEMPLATE_HITL_STAGE.md` (Phase A PR-A3) | HITL_Prompt §4 单 stage prompt 模板；匹配 §2 通用结构（Task / Reference Docs / Skill Hint / Rules / Output）；与 [[rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt\|HITL_Prompt v1.1]] 配套 |
| `TEMPLATE_WORKFLOW_SKILL.md` (Phase B PR-B1) | engineering-workflow track 专用 SKILL.md 模板；ADR-013 native 2 字段 schema + body 风格（Overview / Workflow / 等灵活段名）；用于 `.claude/skills/mj-agent-<group>-<verb>/SKILL.md` 起草；规格见 [[adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem\|ADR-016]] |
| `TEMPLATE_POSTMORTEM.md` (Phase D-1) | POSTMORTEM 骨架；事件 / 异常 / 失败复盘；body 八段（TL;DR / 事件摘要 / 影响范围 / 时间线 / 根因 5-Whys / 行动项 / 检测响应评估 / 经验教训 / 数据边界专属审计）；mj-agent 扩展含 §8 ADR-006/009 4 层 + biz_dwd allowlist 审计；frontmatter 含 ADR-022 C.3.1 字段（severity/incident-date/resolved-at）；规格见 [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.5 |
| `TEMPLATE_ISSUE.md` (Phase D-1) | local [ISSUE] 骨架；延后处理问题 / bug 待修 / 优化候选；body 八段（TL;DR / 问题摘要 / 发现上下文证据 / 问题分析 / 影响评估 / 修复方向 / 验收标准 / 验证计划 双段 / 待确认问题）；含风味识别（A/B/C） + §3.1 必停 4 项 mj-agent 专属 trigger 字段；frontmatter 含 ADR-022 C.3.1 字段（priority/risk-level/resolution）；规格见 [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.7 |
| `TEMPLATE_ASSESSMENT.md` (Phase D-1) | ASSESSMENT 骨架；优化 / 改造后评估对比；body 八维度（D1 架构 / D2 性能 / D3 质量与流程 / D4 数据一致性 / D5 资源 / D6 in-source canonical 行为变化 mj-agent 专属 / D7 数据边界合规 mj-agent 专属 / D8 工程编排技能体系覆盖 mj-agent 专属）；frontmatter 含 ADR-022 C.3.1 字段（dimensions/period）；规格见 [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework\|Code_Side v1.1]] §3.8 |
| `TEMPLATE_EVAL.md` (Phase D PR-D1; mj-agent 原生) | EVAL 骨架（Track B 自有；上游业务系统 无对位）；body 八段（Purpose / Eval Design / Dataset / Judges / Baseline / Regression Criteria / Run History / Open Questions）+ 4 子类（outcome/trajectory/component/integration）+ frontmatter 含 eval_kind / target_skill / dataset_path / baseline_metric+value / regression_threshold / judges；规格见 [[rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework\|Agent_Side v1.1]] §4（Phase 2 EVAL framework 落地后 A8/A11 强制） |

---

## 运行时 canonical（in-source）

按 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta_Framework v2.1]] §2.3 / §4.6（沿用 v2.0 不变），以下文件虽位于 `src/` 但属于 canonical 治理范围：

| 文件 | 类型 | 运行时作用 |
|------|------|-----------|
| `src/mj_agent/prompts/system.md` | `[PROMPT]` v1.2 | agent 基础 system prompt（身份 + ADR-000 P1/P2/P3 + 工具清单 + envelope 字段说明 + 硬规则） |
| `src/mj_agent/skills/biz-domain-context/SKILL.md` | `[SKILL]` v0.1 | 用 `find_biz_context` 把自然语言映射到 catalog（metric / period / dimension / 时间列 / 同环比列 / 信号表 / 维表 join key），产出"目标表+目标列"提案 |
| `src/mj_agent/skills/qcm-analysis/SKILL.md` | `[SKILL]` v0.1 | QCM 五类高频分析模板（趋势 / Top-N / 同环比 / ETL 健康度 / Ready 信号），含 curated NL→SQL 示例（源头：`tests/eval/golden_seed.jsonl` 的 reference_sql） |
| `src/mj_agent/skills/safe-sql-analysis/SKILL.md` | `[SKILL]` v0.1 | SQL 撰写守则与执行 envelope（时间谓词必填 / `SELECT *` 禁用 / LIMIT 策略），失败 → 修正回路 |
| `src/mj_agent/skills/query-writing/SKILL.md` | `[SKILL]` v0.2 (`state: deprecated`) | MVP PR3 拆分为上述 3 个 skill；保留作历史参考，`agent.py` 不加载 |
| `src/mj_agent/skills/probe-fixture/SKILL.md` | `[SKILL]` (fixture) | 治理框架 v1.1 自检用 dummy skill；`state: draft`，**不被** `agent.py` 加载 |
| `src/mj_agent/biz_catalog/qcm_catalog.yaml` | catalog data | 静态镜像 上游业务系统 `[STANDARD]_Biz_DWS_Naming_Stability.md` §2-§4：metric / period / dimension / 同环比列 / 信号表 / 维表 join key；由 `find_biz_context` 召回 |

*MVP 阶段 3 个 skill 静态全载（`agent.py:_ACTIVE_SKILLS`）。Phase 1+ 新增 skill 由 `docs/design/skills/INDEX.md` 补充详细目录；dynamic skill selector 推迟到 1.5。*

---

## 基础设施（docs/infrastructure/）

| 子目录 | 摘要 |
|---|---|
| [[infrastructure/git/INDEX\|infrastructure/git/]] | 4 份 GUIDE 操作化 commit / 分支 / 推送 / PR 规范 |
| [[infrastructure/cicd/INDEX\|infrastructure/cicd/]] | CI/CD 与发布运维 RUNBOOK 入口；首份为 Release Process（Phase 0.5 Minimal 起步版） |

---

## 上手指南（docs/guide/）

| 子目录 | 摘要 |
|---|---|
| [[guide/INDEX\|guide/]] | 面向开发者与运维的上手 / 操作 GUIDE；含 `[GUIDE]_Quick_Start_Setup.md`（5 分钟赶时间版）+ `[GUIDE]_Developer_Onboarding.md`（mj-agent 新成员端到端上手路径）+ `[GUIDE]_Analyst_Day_One.md`（分析师 Day-1 试用闭环） |
| [[guide/[GUIDE]_MJ_Agent_SPEC_Authoring\|MJ-Agent SPEC Authoring Guide v0.1]] (PR-118 commit-3) | mj-agent SPEC 撰写指南；§3 任务类型识别决策树 + §4 8 类任务详解（Python 应用 / SQL guardrail / In-source canonical / Docker compose / CI/CD scripts / Config secrets / Engineering-workflow infra / 文档治理）+ §5 与 HITL_Prompt 短码映射 + §6 与 §3.1 必停规则关系；HITL Stage 6 SPEC 起草必读 |

---

## 术语表

| 术语来源 | 摘要 |
|---|---|
| [项目根 GLOSSARY](../GLOSSARY.md) | mj-agent 全项目术语索引；A-W 字母分段；约 40 术语 + 「定义 + 相关术语」二字段；专题深度词典在 `docs/glossary/` |
| [[glossary/upstream_business_warehouse\|上游业务系统 / Upstream Business Warehouse]] (PR-118 commit-3) | docs/glossary/ 专题词典之一；mj-agent prose 中描述外部业务库的中性术语；PR-118 D2 决策；与代码层 literal `mj-system-backend-network` / `MJ_AGENT_PG_BIZ_*` env var 等的边界 |

---

## 工程编排技能（`.claude/skills/`，Track C engineering-workflow）

按 [[adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem\|ADR-016]] 锁定的 5 family / 命名空间 `mj-agent-<group>-<verb>`，目标态 32 skills；落地状态随 PR-B1...D 推进：

### git family（PR-B1 落地 5 P0；剩 4 个 P1 PR-B3 落地）

| Skill | Stage | Status |
|---|---|---|
| `/mj-agent-git-issue` | 1 Issue Draft | **active**（PR-B1） |
| `/mj-agent-git-branch` | 2 Branch / Worktree | **active**（PR-B1） |
| `/mj-agent-git-commit` | 12 Commit | **active**（PR-B1） |
| `/mj-agent-git-push` | 13 Push | **active**（PR-B1） |
| `/mj-agent-git-pr` | 14 PR | **active**（PR-B1） |
| `/mj-agent-git-review-pr` | 15 review 别人 PR（架构审查方向） | **active**（PR-B3b） |
| `/mj-agent-git-check-merge` | 16 Merge Gate | **active**（PR-B3b） |
| `/mj-agent-git-delete` | 17 sub Branch Cleanup | **active**（PR-B3b） |
| `/mj-agent-git-sync` | 17 sub / hotfix 同步 | **active**（PR-B3b） |

### flow family（PR-B2 + PR-B3 落地共 9）

| Skill | Stage | Status |
|---|---|---|
| `/mj-agent-flow-intake` | 0 Intake | **active**（PR-B2） |
| `/mj-agent-flow-repo-scan` | 3 Repo Scan | **active**（PR-B2） |
| `/mj-agent-flow-plan` | 4 Plan body | **active**（PR-B2） |
| `/mj-agent-flow-implement` | 8 Implementation 编码 | **active**（PR-B2） |
| `/mj-agent-flow-verify` | 10 Local Verification | **active**（PR-B3a） |
| `/mj-agent-flow-self-review` | 11 AI Self-review | **active**（PR-B3a） |
| `/mj-agent-flow-scope-drift` | 9 Scope Drift Gate | **active**（PR-B3a） |
| `/mj-agent-flow-review-respond` | 15 Review/CI（own PR） | **active**（PR-B3a） |
| `/mj-agent-flow-post-merge` | 17 Post-merge | **active**（PR-B3a） |

### doc family（PR-B4 + PR-C1 落地共 6）

| Skill | Stage | Status |
|---|---|---|
| `/mj-agent-doc-plan` | 4 sub Documentation Decision | **active**（PR-B4） |
| `/mj-agent-doc-author` | 6 SPEC/ADR/RUNBOOK | **active**（PR-B4） |
| `/mj-agent-doc-validate` | 11 sub wikilinks/frontmatter/INDEX | **active**（PR-B4） |
| `/mj-agent-doc-sync` | 8 sub code→doc | **active**（PR-C1） |
| `/mj-agent-doc-review` | 15 sub PR-scope 评审 | **active**（PR-C1） |
| `/mj-agent-doc-migrate` | archive workflow | **active**（PR-C1） |

### runtime family（PR-C2 落地 3 P1 + PR-D2-skill 1 P2；**全部 read-only by design**）

| Skill | Stage | Status |
|---|---|---|
| `/mj-agent-runtime-skill-doc-improve` | 8 (B-flavor) sub | **active**（PR-C2） |
| `/mj-agent-runtime-prompt-version-bump` | 8 (B-flavor) sub | **active**（PR-C2） |
| `/mj-agent-runtime-biz-catalog-sync` | 8 (B-flavor) sub | **active**（PR-C2） |
| `/mj-agent-runtime-eval-baseline` | 8 sub / EVAL framework | **active**（PR-D2-skill；framework-independent 设计阶段产物 = 填好的 TEMPLATE_EVAL.md 草稿；Phase 2 EVAL framework 落地由 PR-D2-enforcement 跑 baseline_value 实测） |

### infra family（PR-C3 落地共 4）

| Skill | Stage | Status |
|---|---|---|
| `/mj-agent-infra-env-setup` | 8 (C-flavor) | **active**（PR-B3b） |
| `/mj-agent-infra-studio-probe` | 10 sub Studio H1/H2/H3/R1/R2 | **active**（PR-B3b） |
| `/mj-agent-infra-docker-compose` | 8 (C-flavor) compose lifecycle | **active**（PR-C3） |
| `/mj-agent-infra-storage-stack` | 8 (C-flavor) postgres+redis | **active**（PR-C3） |

合计 32 skills（9/9 + 9/9 + 6/6 + **4/4** + 4/4 = **32/32 全部落地**；flow + git + doc + runtime + infra 五 family 完成；runtime 4 个全部 read-only by design；其中 eval-baseline 是 framework-independent 设计阶段，Phase 2 EVAL framework 落地后由 PR-D2-enforcement 跑 baseline 实测）；详细命名 + lifecycle 见 [[adr/[ADR]_016_In_Tree_Claude_Skills_Ecosystem\|ADR-016]]。

---

## 运维手册（docs/runbook/）

| 文档 | 摘要 |
|---|---|
| `docs/runbook/dev_studio_walkthrough.md` | MVP 开发态 LangGraph Studio 试用与诊断 walkthrough：前置依赖、`.env` 配置、Studio 启动、H1/H2/H3/R1/R2 验证矩阵（引用 Plan A）、LangSmith trace 开关、常见诊断、测试与回归命令矩阵 |

---

## 尚未建立的 canonical 子目录

以下目录将在相应阶段启用：

| 目录 | 用途 | 启用阶段 |
|------|------|---------|
| `docs/contracts/` | `[CONTRACT]` 文档 | Phase 0.5 起首份 SQL 工具契约 |
| `docs/design/` | 子系统设计文档（agent/gateway/memory/prompts/skills/ui） | Phase 1+ 按子系统启用 |
| `docs/evaluation/` | `[EVAL]` 文档 | Phase 2 |
| `docs/postmortem/` | 事故复盘 | 首次事故发生时 |
| `docs/issues/` | 延后问题 | 首次需要时 |
| `docs/api/` | 对外 API 规范 | 如有外部调用方出现 |
| `docs/archive/legacy/` | 历史归档 | 首次需要归档时 |

---

## 快速链接

- Claude Code 工作区配置：`.claude/`（项目级 `.claude/{settings.json,skills/**,scripts/**,hooks/**}` + `.mcp.json` 纳入 engineering-workflow track；详见 [[rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|Meta v2.2]] §7.6 + [[adr/[ADR]_014_Tri_Track_Documentation_Governance\|ADR-014]]）
- Roadmap：`../mj-agent-design/mj-agent-roadmap-v1.6.md`（本仓库外）
