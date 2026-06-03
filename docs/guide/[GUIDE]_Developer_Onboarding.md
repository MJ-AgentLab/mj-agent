---
type: guide
domain: SYS
summary: mj-agent 新成员（或长假回归者）端到端上手路径——仓库与远端、分支与 worktree、本地环境、测试、双轨道文档、提交推送、Studio 首跑
tags:
  - guide
  - onboarding
  - dev
aliases:
  - mj-agent Developer Onboarding
  - mj-agent 开发者上手指南
created: 2026-05-06
updated: 2026-05-18
state: draft
version: v0.1
track: code
owner: 项目负责人
---

# mj-agent 开发者上手指南

> **适用范围**：mj-agent 新成员（Day-1）与长假回归者刷新场景下的端到端上手路径
> **目标受众**：开发 + 维护者
> **版本**：v0.1
> **最后更新**：2026-05-18
> **派生自**：mj-agent 原生（PR-B 增 4 处段借鉴 mj-system Developer_Onboarding 写法：权限清单 / ASCII 仓库导航 / hook 防护 / Quick Checklist；内容按 mj-agent 自身资产派生）
> **关联文档**：[[../infrastructure/git/INDEX|infrastructure/git/]]（4 份 git
> GUIDE）、[[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]、
> [[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]、
> [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.2]]

---

## TL;DR

- **阅读时间**：~15 分钟
- **涵盖范围**：mj-agent 是什么 → 仓库与远端 → 分支模型 → 本地环境 → 测试 →
  双轨道文档 → 提交推送 → LangGraph Studio 首跑
- **适用场景**：Day-1 新成员（按顺序读完 §1-§7）；长假回归者（直接跳速查表 §8）
- **复用原则**：本 GUIDE 不复述命令注释；命令细节优先 wikilink 到
  `README.md` / `CLAUDE.md` / 现有 GUIDE，本 GUIDE 仅承担"读哪份 / 顺序怎么连"

## Prerequisites

- **目标读者**：项目新成员、长假回归后的开发者
- **必备知识**：
  - Python 3.13 基础
  - Git 基础（worktree、branch、push 概念）
  - GitHub & Gitee 账号（mj-agent 双推镜像）
- **建议了解**：
  - LangChain 1.x / LangGraph 1.1.8 概念（不强求）
  - PostgreSQL 只读权限模型（参见 [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]]）

---

## 目录

- §0 适用场景
- §0.5 权限/账号申请清单（首次入职先跑这张表）
- §1 仓库与远端
- §2 工作目录与分支
- §3 本地环境
- §3.5 仓库结构鸟瞰
- §4 测试运行
- §5 三轨道文档约定
- §6 提交与推送
- §6.5 G1/G2 PreToolUse hook 防护
- §7 LangGraph Studio 首跑
- §8 速查表
- §9 Day-1 打勾清单

---

## §0 适用场景

| 场景 | 顺序 |
| --- | --- |
| Day-1 新成员 | §1 → §2 → §3 → §4 → §5 → §6 → §7（端到端跑通一个查询） |
| 长假回归者 refresh | §8 速查表，按需回到 §3-§7 中具体一节 |
| 仅要做文档贡献 | §1 → §2 → §5 → §6 |
| 仅要本地体验 agent | §3 → §7 |

读完本份后下一站：根据角色 / 兴趣，进入 [[../infrastructure/git/INDEX|git GUIDEs]]
深入或 [[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side §3]]
学认证类型的 authoring 细节。

## §0.5 权限/账号申请清单

首次入职先跑这张表——把账号/凭据全拿齐能避免后续每节回头补卡。

| 资源 | 用途 | 申请方式 |
| --- | --- | --- |
| GitHub `MJ-AgentLab` org 成员 | clone / PR | 项目负责人邀请（飞书工单如适用） |
| Gitee `ranzuozhou/mj-agent` 协作者 | 镜像推送 | 项目负责人邀请（飞书工单如适用） |
| Volcengine Ark API key | LLM 调用（默认 provider） | 团队 Ark 企业账号子 key（合规已确认 ZDR） |
| analyst PG RO 账号 | biz_dws / biz_dwd 读 | 上游业务系统仓库 `R__analyst_permissions.sql` 已 GRANT；问运维要 `POSTGRES_ANALYST_USER/PASSWORD` |
| LangSmith API key | trace 调试（可选） | 团队 LangSmith 工作区 invite |
| 团队 secrets 口令 | `.\scripts\setup-env.ps1` 解密 | 项目负责人发放（口令轮换 2 月一次；详见 [[../../config/README|config/README.md]] §6） |

补完后回到 §1 顺序往下读。

## §1 仓库与远端

mj-agent 双远端：
- **GitHub**（origin）：`MJ-AgentLab/mj-agent`（PR 在此开）
- **Gitee**（gitee）：`ranzuozhou/mj-agent`（镜像；PR 不在此开）

完整 setup（首次 clone、双 remote 配置、SemVer 规则）见
[[../infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning|GitHub Setup and Versioning]]。

## §2 工作目录与分支

5 分支模型与 worktree 操作完整说明见
[[../infrastructure/git/[GUIDE]_Git_Branch_Strategy|Git Branch Strategy]]。

简述：mj-agent 是 **bare-repo + 多 worktree** 布局：
- 长期 worktree：`develop`（默认开发线）、`main`（稳定）、`documentation/research-mj-agent`
- 临时 worktree：每条 PR 一个 `feature/<name>` / `documentation/<name>` /
  `bugfix/<name>` / `maintain/<name>` / `hotfix/<name>` 目录

```powershell
# 起新 feature worktree
git -C develop worktree add ../feature/<your-feature> -b feature/<your-feature> develop
```

详见 [[../infrastructure/git/[GUIDE]_Git_Branch_Strategy|Git Branch Strategy]] §3-§4。

## §3 本地环境

最小命令序列（细节见 `README.md` Quick start + `CLAUDE.md` Commands）：

```powershell
# 在你的 worktree 内
uv sync                                # 装依赖、锁版本
.\scripts\setup-env.ps1                # 用团队口令解密 secrets.enc，生成 .env
                                       # （没团队口令 → cp .env.example .env 手填）
uv run langgraph dev                   # 启 LangGraph Studio
```

`.env` 字段说明在 `.env.example`；secrets 治理流程在 `config/README.md`。

## §3.5 仓库结构鸟瞰

```text
src/mj_agent/
├── agent.py             # make_graph() — LangGraph 编译入口（langgraph.json 指向）
├── llm.py               # make_llm() — provider 分支 factory（ADR-027）
├── config.py            # pydantic-settings over .env
├── prompts/system.md    # 全局身份 + ADR-000 三原则
├── skills/              # in-source Track B SKILL.md（业务能力；3 active）
├── tools/               # find_biz_context + sql/{guardrail,precheck,execute,introspect}
├── middleware/          # tool_errors.py @wrap_tool_call（ADR-029）
├── memory/              # AsyncPostgresSaver checkpointer
├── integrations/        # mj_system_db.py 只读 psycopg pool
├── biz_catalog/         # qcm_catalog.yaml 镜像上游业务系统数据字典
├── server/              # cli.py（typer: mj-agent serve / check）
└── ui.py                # Chainlit 入口
```

读这张图先抓三个关键节点：(1) `agent.py` 是 LangGraph 编译入口（`langgraph.json` 指向）；(2) `tools/sql/` 是 4 层数据边界中 L1+L1b+L3 的实现；(3) `skills/` + `prompts/` 是 Track B in-source canonical，由 Python loader 剥 frontmatter 后喂给 LLM。

## §4 测试运行

四档测试；命令矩阵见 [[../../CLAUDE.md#Commands|CLAUDE.md Commands]]：

```powershell
uv run pytest tests/unit          # 快；无外部依赖
uv run pytest tests/eval          # seed schema + Component 检查；无 DB
uv run pytest tests/integration   # 需 live biz DB（无 .env 凭据时 skip）
uv run pytest tests/smoke -m smoke   # 需 DB + LLM（无凭据时 skip）
```

`tests/conftest.py` 在凭据缺失时**自动 skip**（不 fail），所以空 env 也能跑出绿。

## §5 三轨道文档约定

mj-agent 文档治理走**三轨**（Phase B PR-B3c-promote 后由双轨升级；
[[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.2]] §3.10）：
- **Track A 代码侧**（GUIDE / ADR-code / SPEC-code / RUNBOOK / POSTMORTEM-code
  / STANDARD-code / ISSUE-code / ASSESSMENT-code）——
  [[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]
- **Track B 智能体侧**（in-source SKILL / PROMPT / EVAL / agent-facing CONTRACT）——
  [[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]
- **Track C 工程编排侧**（`.claude/skills/mj-agent-*/SKILL.md` / `.claude/settings.json`
  / HITL_Prompt 等）—— [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]]
  + Meta v2.2 §3.10 / §7.7
- **Meta 元层**（types / layers / lifecycle / archive / `track`）——
  Meta_Framework v2.2

> **⚠️ 两类 "skill" 严格区分**（误判事故防护）：
> - **Track B 业务 skill**：`src/mj_agent/skills/<name>/SKILL.md` —— 运行时 LLM 输入；
>   驱动 data agent 业务回答（biz-domain-context / qcm-analysis / safe-sql-analysis 等）；
>   13 字段 schema + 五段式 body；由 `load_skill()` Python loader 加载剥 frontmatter
> - **Track C 工程 skill**：`.claude/skills/mj-agent-<group>-<verb>/SKILL.md` —— 开发流程
>   编排（17-stage HITL 闭环；32 个，5 family：flow / git / doc / runtime / infra）；
>   ADR-013 native 2 字段 schema；由 Claude Code 主进程发现 + slash command 触发
>
> 二者**同名同形不同义**，必须严格区分；混淆会导致施加错误约束 / 套错 schema。
> 三类完整速查表（含第三类 marketplace plugin SKILL）见
> [[../../CLAUDE|CLAUDE.md]] §"Three-source SKILL distinction"。

撰写新文档时复制 `docs/_templates/TEMPLATE_*.md` 起步：

| 类型 | 模板 | Authoring 规格章节 |
| --- | --- | --- |
| GUIDE | [[../_templates/TEMPLATE_GUIDE|TEMPLATE_GUIDE]] | Code_Side §3.1 |
| ADR | [[../_templates/TEMPLATE_ADR|TEMPLATE_ADR]] | Code_Side §3.2 |
| CONTRACT | [[../_templates/TEMPLATE_CONTRACT|TEMPLATE_CONTRACT]] | Code_Side §3.x |
| SKILL（Track B；in-source 业务）| [[../_templates/TEMPLATE_SKILL|TEMPLATE_SKILL]] | Agent_Side §2 |
| WORKFLOW_SKILL（Track C；in-tree 工程）| [[../_templates/TEMPLATE_WORKFLOW_SKILL|TEMPLATE_WORKFLOW_SKILL]] | ADR-013 + ADR-016 |
| PROMPT | [[../_templates/TEMPLATE_PROMPT|TEMPLATE_PROMPT]] | Agent_Side §3 |

## §6 提交与推送

- Commit 格式：`<type>(<scope>): <summary>`，详见
  [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Message 规范]]
- 推送前 7 步检查：[[../infrastructure/git/[GUIDE]_Git_Push_Workflow|Git Push Workflow]]
- PR 描述模板：[[../infrastructure/git/[GUIDE]_PR_Description_Convention|PR Description Convention]]

## §6.5 G1/G2 PreToolUse hook 防护

`.claude/scripts/guard-git-workflow.ps1` 是 PreToolUse hook（在 `.claude/settings.json`
`hooks.PreToolUse[matcher="Bash"]` 注册；通过 `pwsh -NoProfile -File` 调用），
对每条 Bash 命令做正则检查，拦截两类高频误操作：

- **G1 worktree-required**：拦 `git checkout -b/-B` 与 `git switch -c/-C`，引导用
  `git -C develop worktree add ../<branch> -b <branch> develop`
- **G2 base=develop-except-hotfix**：拦 `gh pr create` 不带 `--base` / `-B`，
  引导 non-hotfix 用 `--base develop`（仅 hotfix 允许 `--base main`）

Hook 命令 exit code 2 让 Claude Code 把 stderr 经 agent 视图喂回，AI 立即看到违例
并自动修复。事故起源：PR #158（缺 `--base` 误合到 main）+ PR #154（`git checkout -b`
而非 worktree-add）于 2026-05-12；恢复闭环 PR #159 + 3 层防御设计见
[[../../plans/[PLAN]_g1_g2_workflow_enforcement|PLAN_g1_g2_workflow_enforcement]]。

## §7 LangGraph Studio 首跑

启动后浏览器会打开 Studio URL（默认 `http://127.0.0.1:2024`）；选 graph
`mj_agent`。完整 walkthrough（含 H1/H2/H3 happy path 与 R1/R2 red line 验证矩阵
+ LangSmith trace 开关 + 8 条诊断）见
[[../runbook/dev_studio_walkthrough|dev_studio_walkthrough]]。

最简首跑：在 Studio 输入框问"biz_dws 里有哪些日度总量表？"，agent 应该
依序调 `find_biz_context → list_biz_tables`，回复中含 `dws_qcm_*_daily_total`
表名清单。

## §8 速查表

| 任务 | 命令 / 路径 |
| --- | --- |
| 装依赖 | `uv sync` |
| 启 Studio | `uv run langgraph dev` |
| 单元测试 | `uv run pytest tests/unit` |
| 完整测试 | `uv run pytest`（默认排除 smoke） |
| Lint | `uv run ruff check` |
| 类型检查 | `uv run mypy src/mj_agent` |
| 起 worktree | `git -C develop worktree add ../<dir> -b <branch> develop` |
| 解密 secrets | `.\scripts\setup-env.ps1` |
| 文档 INDEX | `docs/INDEX.md` |
| 双轨道 STANDARD | `docs/rule/[STANDARD]_MJ_Agent_*.md` × 3 |
| 模板 | `docs/_templates/TEMPLATE_*.md` × 5 |
| 路线图 | `plans/mj-agent-roadmap-v1.6.md` |
| MVP plan | `plans/[PLAN]_mj-agent-data-agent-mvp-framework.md` |

## §9 Day-1 打勾清单

逐项跑完即完成 Day-1 上手；按段顺序对应 §0.5/§1-§7。

**账号准备**（先跑 §0.5）

- [ ] GitHub `MJ-AgentLab` org 成员邀请收到并接受
- [ ] Gitee `ranzuozhou/mj-agent` 协作者权限拿到
- [ ] Ark API key + analyst PG RO + 团队 secrets 口令收到

**环境就绪**（§3）

- [ ] `git -C develop worktree add ../feature/<my-first> -b feature/<my-first> develop` 起首条 PR worktree
- [ ] `uv sync` 成功（首次约 1-3 分钟）
- [ ] `.\scripts\setup-env.ps1` 解密 `.env`（或 fallback `cp .env.example .env`）
- [ ] `uv run mj-agent check` 输出 `db: ok` + `llm provider = ark (endpoint=...)`

**跑通 hello**（§4 + §7）

- [ ] `uv run pytest tests/unit` 全绿
- [ ] `uv run langgraph dev` 启 Studio，浏览器自动打开 `http://127.0.0.1:2024`
- [ ] Studio 选 `mj_agent` graph，首问"biz_dws 里有哪些日度总量表？"
- [ ] 回复含 `dws_qcm_*_daily_total` 表名清单（说明 `find_biz_context + list_biz_tables` 调通）

**文档第一眼**（§5）

- [ ] 已读 [[../INDEX|docs/INDEX.md]]
- [ ] 已读 [[../../CLAUDE|CLAUDE.md]] §Documentation 三轨段
- [ ] 已记住三类 SKILL 区分（in-source / in-tree workflow / marketplace plugin）

**提交链路**（§6 + §6.5）

- [ ] 已配 `.claude/settings.json` PreToolUse hook（自动从仓库继承；首次 Claude Code 启动时加载）
- [ ] 已读 [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Message 规范]] §4 scope 派生规则

**学习包**

- [ ] 已读 [[decisions/ADR-006_Fail_Safe_Reads|ADR-006]] 数据边界 4 层
- [ ] 已读 [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] LLM provider 二分

---

## 关联文档

- [[../infrastructure/git/INDEX|git GUIDEs]]（4 份）
- [[[GUIDE]_Quick_Start_Setup|Quick Start Setup（5 分钟赶时间版）]]
- [[../rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.1]]
- [[../rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.1]]
- [[../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.2]]
- [[../rule/[STANDARD]_MJ_Agent_AI_Engineering_Execution_HITL_Prompt|HITL_Prompt v1.1]]
- [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|Commit Message Convention]]
- [[../runbook/dev_studio_walkthrough|Dev Studio Walkthrough]]
- [[../INDEX|docs/INDEX]]

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-06 | v0.1 | 初稿（PLAN G PR2 落地） |
| 2026-05-18 | v0.1（in-place） | 4 处增强（§0.5 权限清单 / §3.5 仓库结构鸟瞰 / §6.5 G1/G2 hook 防护 / §9 Day-1 打勾清单）+ 关联文档 + §5 文档版本号刷新到 v2.2 / v1.1；借鉴 mj-system Developer_Onboarding 写法，内容按 mj-agent 自身资产派生 |
