---
type: standard
domain: SYS
summary: mj-agent canonical 文档层的人工入口，Phase 2 接入自动生成
owner: 项目负责人
created: 2026-04-24
updated: 2026-04-30
state: draft
track: shared
---

# mj-agent 文档索引

> 本索引是 **手写初版**。按 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|mj-agent 文档治理元框架 v2.0]] §6.2，
> 进入 Phase 2 后将改为从各文档 frontmatter `summary` 字段扫描生成。

---

## 规则（docs/rule/）

| 文档 | 摘要 |
|------|------|
| [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0\|mj-agent 文档治理元框架 v2.0]] | 元框架（v1.1 升级）—— 引入 track 字段与双轨子框架，治理 types/layers/lifecycle/archive 跨轨规则；骨架交付 Phase 0.5 |
| [[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0\|mj-agent 代码侧文档治理框架 v1.0（Track A）]] | Track A 代码侧文档治理 — GUIDE/ADR-code/SPEC-code/RUNBOOK/POSTMORTEM-code/STANDARD-code/ISSUE-code/ASSESSMENT-code 的 authoring 深度规则；A1-A6 + OB1-OB5 |
| [[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0\|mj-agent 智能体侧文档治理框架 v1.0（Track B）]] | Track B 智能体侧文档治理 — SKILL/PROMPT/EVAL/agent-facing CONTRACT 的 authoring 深度规则；A7-A10 + A11 + 渐进披露 + EVAL coupling + frontmatter strip §7.5 |
| [[STANDARD]_GitHub_Markdown_v1.0\|GitHub-Flavored Markdown 编写规范 v1.0]] | 定义 mj-agent 文档在 GitHub 渲染的 Markdown + YAML 语法规范，覆盖 GFM 13 节排版规则，与 Meta_Framework v2.0 §4 字段语义互补 |
| [[STANDARD]_MJ_Agent_Commit_Message_Convention_v1.0\|MJ-Agent Commit Message 规范 v1.0]] | mj-agent 的 Conventional Commits 规范，定义 type、mj-agent 专属 scope、分支对齐矩阵与示例（draft；派生自 mj-system v2.0） |

## 架构决策（docs/adr/）

| 文档 | domain | decision | 摘要 |
|------|--------|----------|------|
| [[ADR]_000_Data_LLM_Boundary_Principles\|ADR-000 Data-LLM Boundary Principles]] | DATA | accepted | 最小必要出网、通道隔离、工具中介——后续所有安全相关决策的理论基础 |
| [[ADR]_001_Python_Only_Agent_Runtime\|ADR-001 Python-Only Agent Runtime]] | SYS | accepted | Agent 逻辑、tools、skills、memory 全部留在 Python；前端仅作通信与渲染 |
| [[ADR]_002_Skills_As_First_Class_Citizens\|ADR-002 Skills as First-Class Citizens]] | SKILL | accepted | 所有专业能力以 `skills/{name}/SKILL.md` 格式封装，对齐 Claude Code skills 约定 |
| [[ADR]_003_Progressive_Disclosure\|ADR-003 Progressive Disclosure]] | PROMPT | accepted | 全局 system prompt 只含身份与原则；具体能力按需加载 |
| [[ADR]_006_Fail_Safe_Reads\|ADR-006 Fail-Safe Reads]] | GUARDRAIL | accepted | biz 库访问用只读账号 + SQL guardrail middleware 双层保护 |
| [[ADR]_008_Co_Deployment_With_MJ_System\|ADR-008 Co-Deployment with mj-system]] | OPS | accepted | mj-agent 作为 mj-system 的兄弟服务部署在同一 Docker 环境（DEV/TEST/PROD 三套） |
| [[ADR]_009_Biz_Domain_As_Primary_Data_Source\|ADR-009 Biz Domain as Primary Data Source]] | INTEGRATION | accepted | mj-agent 仅通过只读账号访问 biz 域，不访问 ODS/DWD 原始层 |
| [[ADR]_010_Git_And_Commit_Conventions_From_MJ_System\|ADR-010 Git and Commit Conventions Adopted from mj-system]] | SYS | accepted | mj-agent 从 mj-system 继承 git 工作流与 commit 规范，附 Keep/Adapt/Defer 矩阵与再评估触发器 |
| [[ADR]_011_Doc_Versioning_And_Archive_Convention\|ADR-011 Document Versioning and Archive Convention]] | SYS | accepted | 文档治理新增 Major.Minor 版本演进与 docs/archive/ 归档机制（HITL 触发，A3 模式 = git branch + PR review）；本 PR 同时把 Framework v1.0 升至 v1.1 |
| [[ADR]_012_Two_Track_Documentation_Governance\|ADR-012 Two-Track Documentation Governance]] | SYS | accepted (state: draft) | 决议引入双轨文档治理（Code_Side + Agent_Side + Meta 元层）+ skeleton-first 演进 + 双 plugin 骨架（mj-agent-agent-doc / mj-agent-code-doc） |
| [[ADR]_013_Plugin_SKILL_md_Schema_Separation\|ADR-013 Plugin SKILL.md Schema Separation]] | SYS | accepted (state: draft) | marketplace plugin SKILL.md 使用 Claude Code 原生 schema（name + description 两字段），与 mj-agent in-source SKILL.md 的 Agent_Side v1.0 §2 13 字段 schema 独立；两者通过 sync skill（Phase 1）做内容同步，不做 schema 同步 |

## 评估（docs/assessments/）

| 文档 | 周期 | 摘要 |
|------|------|------|
| [[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0\|mj-system Git 规范在 mj-agent 的适配评估 v1.0]] | Phase 0 | 评估 mj-system git 基础设施与 commit 规范在 mj-agent 的适用性，给出 Keep/Adapt/Defer 矩阵与社区证据 |

## 归档（docs/archive/）

> 由 Meta_Framework §5 / 历史 Framework v1.1 §5.6.2 流程触发的版本退役搬迁。详见 [[adr/[ADR]_011_Doc_Versioning_And_Archive_Convention\|ADR-011]]。

| 归档文档 | 取代者 | 归档原因 |
|---|---|---|
| [[archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.0\|Framework v1.0（archive）]] | [[archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1\|Framework v1.1（archive）]] | v1.1 引入 §5.6（Major.Minor 版本演进与归档机制）和 §4.2 filename `_vX.Y` 强制规则 |
| [[archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1\|Framework v1.1（archive）]] | v2.0 trio：[[rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0\|Meta_Framework v2.0]] + [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0\|Code_Side v1.0]] + [[rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0\|Agent_Side v1.0]] | v2.0 引入 `track` frontmatter 字段与双轨子框架（Code_Side / Agent_Side），把 authoring 深度规则与 PR 校验门禁按轨拆分；详见 [[adr/[ADR]_012_Two_Track_Documentation_Governance\|ADR-012]] |

## 模板（docs/\_templates/）

| 模板 | 用途 |
|------|------|
| `TEMPLATE_ADR.md` | 架构决策记录骨架 |
| `TEMPLATE_GUIDE.md` | GUIDE 骨架（CN-numbered 详规，codified 自 4 份 reference GUIDE）；规格见 [[rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0\|Code_Side]] §3.1 |
| `TEMPLATE_SKILL.md` | skill 骨架（复制到 `src/mj_agent/skills/<name>/SKILL.md`） |
| `TEMPLATE_PROMPT.md` | prompt 骨架（复制到 `src/mj_agent/prompts/<name>.md`） |
| `TEMPLATE_CONTRACT.md` | 工具/服务契约骨架 |

*Phase 0.5 将补 `TEMPLATE_RUNBOOK.md`；Phase 2 将补 `TEMPLATE_EVAL.md` / `TEMPLATE_POSTMORTEM.md` / `TEMPLATE_ASSESSMENT.md`。*

---

## 运行时 canonical（in-source）

按 [[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0\|Meta_Framework v2.0]] §2.3 / §4.6（沿用 v1.1 §2.3、§4.6 不变），以下文件虽位于 `src/` 但属于 canonical 治理范围：

| 文件 | 类型 | 运行时作用 |
|------|------|-----------|
| `src/mj_agent/prompts/system.md` | `[PROMPT]` v1.2 | agent 基础 system prompt（身份 + ADR-000 P1/P2/P3 + 工具清单 + envelope 字段说明 + 硬规则） |
| `src/mj_agent/skills/biz-domain-context/SKILL.md` | `[SKILL]` v0.1 | 用 `find_biz_context` 把自然语言映射到 catalog（metric / period / dimension / 时间列 / 同环比列 / 信号表 / 维表 join key），产出"目标表+目标列"提案 |
| `src/mj_agent/skills/qcm-analysis/SKILL.md` | `[SKILL]` v0.1 | QCM 五类高频分析模板（趋势 / Top-N / 同环比 / ETL 健康度 / Ready 信号），含 curated NL→SQL 示例（源头：`tests/eval/golden_seed.jsonl` 的 reference_sql） |
| `src/mj_agent/skills/safe-sql-analysis/SKILL.md` | `[SKILL]` v0.1 | SQL 撰写守则与执行 envelope（时间谓词必填 / `SELECT *` 禁用 / LIMIT 策略），失败 → 修正回路 |
| `src/mj_agent/skills/query-writing/SKILL.md` | `[SKILL]` v0.2 (`state: deprecated`) | MVP PR3 拆分为上述 3 个 skill；保留作历史参考，`agent.py` 不加载 |
| `src/mj_agent/skills/probe-fixture/SKILL.md` | `[SKILL]` (fixture) | 治理框架 v1.1 自检用 dummy skill；`state: draft`，**不被** `agent.py` 加载 |
| `src/mj_agent/biz_catalog/qcm_catalog.yaml` | catalog data | 静态镜像 mj-system `[STANDARD]_Biz_DWS_Naming_Stability.md` §2-§4：metric / period / dimension / 同环比列 / 信号表 / 维表 join key；由 `find_biz_context` 召回 |

*MVP 阶段 3 个 skill 静态全载（`agent.py:_ACTIVE_SKILLS`）。Phase 1+ 新增 skill 由 `docs/design/skills/INDEX.md` 补充详细目录；dynamic skill selector 推迟到 1.5。*

---

## 基础设施（docs/infrastructure/）

| 子目录 | 摘要 |
|---|---|
| [[infrastructure/git/INDEX\|infrastructure/git/]] | 4 份 GUIDE 操作化 commit / 分支 / 推送 / PR 规范，派生自 mj-system v5.0 同名目录 |
| [[infrastructure/cicd/INDEX\|infrastructure/cicd/]] | CI/CD 与发布运维 RUNBOOK 入口；首份为 Release Process（Phase 0.5 Minimal 起步版） |

---

## 上手指南（docs/guide/）

| 子目录 | 摘要 |
|---|---|
| [[guide/INDEX\|guide/]] | 面向开发者与运维的上手 / 操作 GUIDE；首份为 `[GUIDE]_Developer_Onboarding.md`（mj-agent 新成员端到端上手路径） |

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

- 派生来源：[[STANDARD]_Documentation_Management_Framework_v5.0\|mj-system 文档管理框架 v5.0]]
- Claude Code 工作区配置：`.claude/`（不受本框架治理）
- Roadmap：`../mj-agent-design/mj-agent-roadmap-v1.6.md`（本仓库外）
