---
type: assessment
domain: SYS
summary: 评估 mj-system git 基础设施与 commit 规范在 mj-agent 的适用性，给出 Keep/Adapt/Defer 矩阵与社区证据
owner: 项目负责人
created: 2026-04-25
updated: 2026-04-27
state: active
version: v1.0
track: code
dimensions:
  - fit-for-mj-agent
  - community-precedent
  - implementation-cost
  - deferral-risk
period: Phase 0
tags:
  - assessment
  - git
  - commit-convention
  - governance
aliases:
  - MJ System Git Conventions Adoption Assessment
  - mj-system git 规范适配评估
---

# mj-system Git 规范在 mj-agent 的适配评估

> **适用范围**：评估 mj-system 5 份 git 治理文档（4 GUIDE + 1 STANDARD）在 mj-agent 的适用性
> **目标受众**：项目负责人、未来贡献者、再评估触发器命中时的 reviewer
> **版本**：v1.0
> **最后更新**：2026-04-25
> **关联文档**：[[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from mj-system]]、[[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|MJ-Agent Commit Message Convention v1.0]]

---

## 目录

1. [背景](#1-背景)
2. [方法与评估维度](#2-方法与评估维度)
3. [源文档一览](#3-源文档一览)
4. [社区实践对照](#4-社区实践对照)
5. [规则打分](#5-规则打分)
6. [建议](#6-建议)
7. [风险登记](#7-风险登记)
8. [参考](#8-参考)
9. [附录 A：社区项目档案](#附录-a社区项目档案)
10. [附录 B：引用清单](#附录-b引用清单)

---

## 1 背景

mj-agent 在 bootstrap 阶段从 [[ADR]_008_Co_Deployment_With_MJ_System|ADR-008 Cross-System Boundary with mj-system]] 决定的跨项目运维一致性出发（注：ADR-008 早期形态为"兄弟服务"，PR #42-#46 后演进为独立 compose project + consumer 关系；本评估以早期 framing 为背景），把 mj-system 已经成熟的一整套 git 治理文档**几乎原封不动地继承下来**。继承的可观察痕迹：

- `.bare/` 与兄弟工作树（Bare-repo Worktree）— 与 mj-system [[GUIDE]_Git_Branch_Strategy|分支策略指南]] §6 描述的结构完全一致
- 双远端：`origin` (GitHub `MJ-AgentLab/mj-agent`) + `gitee` (`gitee.com/ranzuozhou/mj-agent`)
- `.github/PULL_REQUEST_TEMPLATE/` 下 6 份模板（feature / bugfix / documentation / maintain / hotfix / release），每份对应一种分支类型
- `CLAUDE.md` §Repo conventions 声明 "Commits follow Conventional Commits"，但**首个 commit `b932007` 不符合 `type(scope):` 格式**
- 文档治理框架 [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|Framework v1.1（archive）]] 自身也声明 `derives_from: mj-system/develop@[STANDARD]_Documentation_Management_Framework_v5.0`

继承本身合理（[[ADR]_008_Co_Deployment_With_MJ_System|ADR-008]] 已论证跨项目运维一致性路径），但 mj-system 的规则是为：

- 多服务平台（aec / dqv / qvl / qcm / sac / fc 共 6 个 ETL 服务）
- 含 PM / DBA / SRE 角色的团队
- 三套环境（DEV / TEST / PROD）
- CI runner 无法访问 GitHub（被迫走 Gitee 镜像）

而设计的。mj-agent 当前是：

- 单服务 LangChain + LangGraph Python 3.13 Agent
- Phase 0 Foundation，1 名开发者
- 无独立 PROD 环境（与 mj-system 共部署）
- 直接访问 GitHub

直接套用规则的两个具体后果已经显现：

1. **scope 列表不可用**：mj-system 的 `aec/dqv/qcm` 服务缩写对 mj-agent 无意义，导致首位贡献者无法填出合法 scope，规范实际未生效
2. **首份 commit 不合规**：`b932007 Initial commit: mj-agent Python 3.13 scaffold` 未带 type，反映出"声明遵守、实际无规可依"的状态

本评估的目的：在 Phase 0 commit 持续累积之前，对 mj-system 5 份治理文档的每一条规则做出明确的 **KEEP / ADAPT / DEFER / DROP** 判定，给后续每个被推迟的项目一个明确的再评估触发器。

---

## 2 方法与评估维度

### 2.1 评估维度

frontmatter `dimensions` 列出的 4 个维度，每条规则按这 4 维打分后得出 verdict：

| 维度 | 含义 | 打分线索 |
|---|---|---|
| **fit-for-mj-agent** | 规则是否解决 mj-agent 实际场景的问题 | mj-agent 模块结构 / 团队规模 / 部署形态 |
| **community-precedent** | 数据 Agent OSS 社区是否采用此模式 | §4 表格 8/8 计数 |
| **implementation-cost** | 引入或维护此规则的边际成本 | "已安装" 接近 0 / "需要新建" 较高 |
| **deferral-risk** | 推迟的代价（如果不引入会失去什么） | 缺失会引发什么具体痛点 |

### 2.2 verdict 取值

| verdict | 含义 | 适用条件 |
|---|---|---|
| **KEEP** | 完整保留 mj-system 规则，无修改 | 4 维总体正向，已安装或边际成本接近 0 |
| **ADAPT** | 保留结构，但内容需重写以匹配 mj-agent | 结构正向但具体内容（如 scope 列表）不适用 |
| **DEFER** | 暂不引入；记录再评估触发器 | 有价值但 deferral-risk 当前低 |
| **DROP** | 不引入且无再评估计划 | mj-agent 永远不需要（如 mj-system 的服务名 scope） |

### 2.3 数据来源

- **mj-system 源文档**：5 份完整阅读（详见 §3）
- **mj-agent 现状**：仓库扫描（PR 模板、CI workflow、git 远端、commit 历史、INDEX、ADR、roadmap）
- **社区证据**：8 个数据 Agent OSS 项目的 `.github/`、`CONTRIBUTING.md`、近期 commits，以及 2 份权威规范（详见 §4 与 附录 A）

---

## 3 源文档一览

| # | 文件 | 类型 | 行数（约） | 核心规则 | mj-agent 当前状态 |
|---|---|---|---|---|---|
| 1 | `[GUIDE]_Git_Branch_Strategy.md` | GUIDE | ~550 | 5 类临时分支（feature/bugfix/documentation/maintain/hotfix）+ Bare-repo Worktree 结构 + 命名规范 | 工作树结构已安装 |
| 2 | `[GUIDE]_Git_Push_Workflow.md` | GUIDE | ~660 | 7 步 pre-push 检查 + 双远端推送 + .gitignore 策略 + 可选 pre-push hook | 双远端已配置；7 步检查未自动化 |
| 3 | `[GUIDE]_GitHub_Setup_And_Versioning.md` | GUIDE | ~390 | SemVer 规则 + 版本号在 8 个文件分布 + 分支保护 + dual-push alias | 仅 `pyproject.toml` 持有版本号 |
| 4 | `[GUIDE]_PR_Description_Convention.md` | GUIDE | ~395 | 6 份 PR 模板键控分支类型 + 自检字段对齐 PM Code Review | 6 份模板已安装于 `.github/PULL_REQUEST_TEMPLATE/` |
| 5 | `[STANDARD]_Commit_Message_Convention.md` | STANDARD | ~250 | Conventional Commits + 服务 scope (`aec/dqv/qvl/qcm/sac/fc`) + infra scope (`db/docker/ci/deps/n8n`) + 分支×type 矩阵 | 仅 CLAUDE.md 一行声明 "follow Conventional Commits"，无具体 scope 表 |

---

## 4 社区实践对照

8 个数据 Agent / LLM-Agent OSS 项目 + 2 份权威规范的横切对比（数据来源：见 附录 A 与 附录 B）：

| 模式 | 8 项目采纳数 | 谁采纳 | 谁不采纳 | mj-agent 含义 |
|---|---|---|---|---|
| trunk-on-`main`（无 develop/main 双干） | **8 / 8** | 全员 | — | mj-agent 的 `develop` 分支是社区异常项；保留属 mj-system 一致性而非社区惯例 |
| 单 PR 模板（~20-50 行） | **8 / 8** | 全员 | — | mj-agent 的 6 份 PR 模板是社区异常项；保留属"已安装零成本"非最佳实践 |
| Conventional Commits `type(scope): summary` | **6 / 8** | LangChain / LangGraph / DB-GPT / WrenAI / AutoGPT / Aider | Vanna / Open Interpreter（自由文本） | mj-agent 应采纳；与 mj-system 一致 |
| CI 强制校验 PR 标题（`amannn/action-semantic-pull-request`） | **2 / 8** 显式 | LangChain / LangGraph | 其他 6 个无强制 | **mj-agent 直接依赖** LangChain + LangGraph，跟随它们的实践有强对齐价值 |
| scope = subpackage / ship-unit | **5 / 8** | LangChain / LangGraph / WrenAI / DB-GPT / Angular | AutoGPT 用 path / Aider 不用 scope / Vanna 不用 | 应采纳；mj-agent scope = `src/mj_agent/` 模块名 |
| 自定义 footer 关键字（`Eval-Score:`、`Prompt-Version:`） | **0 / 8** | — | 全员 | **不要发明**；prompt 版本在 frontmatter，eval 分数在 PR 描述 |
| 数据 Agent 专属 scope (`prompt`/`agent`/`rag`/`model`/`eval`) | DB-GPT release-drafter labels / WrenAI eval branches / LangChain `model-profiles` | DB-GPT / WrenAI / LangChain | — | 借鉴子集：`prompt / agent / skill / sql / eval` |
| 双远端 / 镜像（Gitee + GitHub） | **0 / 8** | — | 全员 | 视为 mj-agent ↔ mj-system 跨项目运维一致性细节（ADR-008），不是 git 工作流 |
| 角色门禁字段（PM / DBA / SRE 必审） | **0 / 8** | — | 全员（只用 CODEOWNERS，不在 PR 模板里写角色） | mj-agent 团队规模 < 4，DEFER 直至触发 |
| Release commit `release(scope): x.y.z` | **2 / 8** | LangChain / LangGraph | 其他 | Phase 1 follow-up，非 Phase 0 关切 |

> [!IMPORTANT]
> 最具决策力的发现是 **0/8 GitFlow + 0/8 6 PR 模板 + 0/8 自定义 footer** 三项一致性。前两项的 KEEP 是对 mj-system 一致性的妥协，不是社区背书；自定义 footer 的 DROP 是直接遵循社区共识。

---

## 5 规则打分

主表 — 每行为一条来自 §3 五份文档的具体规则。打分顺序：fit / precedent / cost / deferral，verdict 综合 4 维。

### 5.1 来自 GUIDE 的规则

| 来源文件 | 规则 | mj-system 原意 | mj-agent verdict | 理由 | 再评估触发器 |
|---|---|---|---|---|---|
| Branch Strategy §0.4 | Bare-repo Worktree 布局 | 多分支并行开发，bare repo 在根，worktree 是兄弟目录 | **KEEP** | 已安装、与 mj-system 切换零摩擦；fit OK / precedent N/A / cost ~0 / deferral OK | 工作树破坏工具链 OR 团队 < 1 dev |
| Branch Strategy §1-§2 | 5 类临时分支命名 (feature/bugfix/documentation/maintain/hotfix) | 分支 type 与 commit type 不混淆，清晰角色 | **KEEP** | mj-system 一致；6 PR 模板与之绑定；社区虽简单但 mj-agent 已配套 | Phase 1 review 决定是否简化 |
| Branch Strategy §3 | 分支 × commit type 对齐矩阵 | feature/* 只允许 feat/perf/refactor/test/docs；hotfix/* 只允许 fix | **KEEP**（写入 STANDARD §5.2） | 干净的提交分类，PR review 可直接照表 | N/A |
| Push Workflow §1-§7 | 7 步 pre-push 检查清单 | 1.commit 格式 2.类型/分支匹配 3.CHANGELOG 4.工作目录干净 5.分支命名 6.同步基线 7.推送验证 | **KEEP** as guidance, **NOT** as hook | Phase 0 用人工自检；hook 自动化推迟到 Phase 1 | 重复的 push-time 错误超 3 次 |
| Push Workflow §6 | 双远端 dual-push alias | `git pushall = git push gitee && git push origin` | **KEEP** | 跨项目运维一致性（ADR-008）；CI 走 Gitee 镜像；mj-agent 后续若进入同一 CI 也需要 | mj-agent 与 mj-system 完全分离，或 Gitee 90 天未用 |
| GitHub Setup §1-§2 | GitHub + Gitee 镜像配置 | 两个仓库为同一真相源，GitHub 主，Gitee 镜像供 CI | **KEEP** | 已配置；ADR-008 跨项目运维一致性决策 | 同上 |
| GitHub Setup §3-§4 | SemVer + 多文件版本号同步（`pyproject.toml` + `Dockerfile` + `main.py` + 4 处） | mj-system 的发版要在 8 个文件改版本号 | **DEFER**，集中到单一 `pyproject.toml` | mj-agent Phase 0 仅 `pyproject.toml` 持有 version；Docker 与 CHANGELOG 尚不存在 | 首次发版时配套写入 RUNBOOK |
| GitHub Setup §5 | PowerShell 版本号批量更新脚本 | 在 8 个文件上 sed | **DROP** | mj-agent 单一 source 不需要批量 | N/A |
| PR Description §1-§3 | 6 份 PR 模板（feature/bugfix/doc/maintain/hotfix/release） | 不同分支类型审核关注点不同 | **KEEP** | 已安装；社区 0/8 但移除成本 > 维持成本 | 首位外部贡献者选错模板 |
| PR Description §3 | 自检字段对齐 PM Code Review 清单 | 开发者自检 = PM 复核 | **KEEP** as structure, **DEFER** PM 角色映射 | mj-agent Phase 0 无 PM 角色；自检表保留，"PM 复核"含义留待团队规模到位 | 团队规模 ≥ 4 |

### 5.2 来自 STANDARD（commit 规范）的规则

| 规则 | mj-system 原意 | mj-agent verdict | 理由 |
|---|---|---|---|
| 格式 `<type>(<scope>): <summary>` + body + footer | Conventional Commits 1.0.0 | **KEEP** 一字不改 | 行业标准；零适配成本 |
| 7 个 type (`feat/fix/perf/refactor/test/docs/infra` + `merge`) | 表达变更性质 | **KEEP** 一字不改 | 覆盖 mj-agent 全部场景 |
| 服务 scope 表 (`aec/dqv/qvl/qcm/sac/fc`) | mj-system ETL 微服务 | **DROP** | mj-agent 无这些服务；保留就是垃圾 scope |
| 基础设施 scope 表 (`db/docker/ci/deps/n8n`) | mj-system 跨 ETL 共享层 | **ADAPT** → mj-agent 版本（保留 `db/ci/deps/infra`，删 `docker/n8n`） | mj-agent 无 docker / n8n |
| **新增** mj-agent 代码 scope (`agent/llm/prompt/skill/sql/config`) | — | **ADAPT**（[[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention\|新 STANDARD]] §4.1） | 来自 `src/mj_agent/` 真实模块 |
| **新增** mj-agent 跨代码 scope (`tests/eval`) | — | **ADAPT**（同上 §4.2） | `tests/` 已存在；`eval/` Phase 2 |
| `docs` 仅作 type 不作 scope | mj-system §4.3 | **KEEP** | 干净的语义；继承到新 STANDARD §4.3 |
| 分支 × type 对齐矩阵 | mj-system §5.2 | **KEEP** 一字不改 | 与 GUIDE 的分支模型联动 |
| 提交拆分指南（§6） | 拆分原则 + 应拆分信号 + 推荐顺序 | **KEEP**（mj-agent 示例替换） | 通用工程纪律 |
| 自定义 footer 关键字 | 未使用 | **DROP / NEVER ADOPT** | 0/8 社区项目使用；prompt 版本在 frontmatter / eval 在 PR 描述 / trace 在 [POSTMORTEM] |

---

## 6 建议

### 6.1 本次随附 PR（已同时落地）

- 本评估文档（[ASSESSMENT]）
- [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|MJ-Agent Commit Message Convention v1.0]]（state: draft）
- [[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010]]（state: active）
- `docs/INDEX.md` 同步（A5 硬门禁）
- `CLAUDE.md` §Repo conventions 同步（A6 硬门禁）：扩写 commit 与分支两行、把新 STANDARD 路径写入、把 ADR 清单加入 010、加一行指向 ADR-010 + 本评估文档

### 6.2 紧接的下一个 PR（PR 模板对齐）

A5 / A6 在本 PR 内已同步落地。剩余对齐项不阻塞门禁，但建议作为下一 PR 单独提交以保持纯文档纪律：

- 修订 6 份 `.github/PULL_REQUEST_TEMPLATE/*.md` 的"自检结果"段，把通用 "Commits follow Conventional Commits" 改为引用新 STANDARD §2-§5；让 PR 提交者直接看到分支 ↔ commit type 矩阵
- 在 `documentation.md` PR 模板里新增一行检查项："如修改 `docs/rule/`、`docs/adr/`、`docs/assessments/`，已确认 `docs/INDEX.md` 已同步（A5）"
- 视情形把"如触发 allowlist，CLAUDE.md 已同步检查"一行（Framework v1.0 §7.3 模板检查项）从可选改为强制 checkbox

### 6.3 Phase 1 follow-ups

- **CI lint**：引入 `amannn/action-semantic-pull-request` 校验 PR 标题（参 LangChain `pr_lint.yml`）。这是 STANDARD §9 promotion 的触发条件之一
- **6 → 1 PR 模板收敛评估**：若 Phase 1 内出现首位外部贡献者选错模板的事件，把 6 份折叠为 1 份 + 条件化章节（参 AutoGPT 模板）
- **`develop` 收敛评估**：若 Phase 1 内出现首次 hotfix 暴露双干混乱，评估收敛到 trunk-on-`main`
- **角色门禁评估**：团队规模到 4 时引入 CODEOWNERS（不进 PR 模板正文，参社区惯例）

### 6.4 Phase 2+ 延期项

- 多文件版本号同步策略 → 写 `[RUNBOOK]_Release_Process.md`（届时若 mj-agent 引入 Dockerfile）
- pre-push hook 自动化 → 写 `scripts/pre-push.ps1` + `[GUIDE]_Local_Git_Hooks.md`
- Release commit 约定 (`release(scope): x.y.z`) → 写入新 STANDARD §10（v2.0 升级）

---

## 7 风险登记

每个 KEEP-but-未-用-满 决策的潜在治理债务：

| 风险 | 触发条件 | 影响 | 缓解 |
|---|---|---|---|
| `develop` 分支沦为 `main` 的别名 | mj-agent 永远 trunk 化操作而无 release-train 节奏 | 新外部贡献者无法理解为何要 PR `develop` 而不是 `main` | ADR-010 触发器 "Phase 1 review" 强制 revisit |
| 6 份 PR 模板成为 cargo cult | 全部 PR 都用 feature.md，其他模板从未被选 | 5 份模板成为腐烂 fixture，review 注解噪声 | ADR-010 触发器 "首位贡献者选错模板" 命中后立即收敛 |
| 双远端 Gitee 镜像静默失活 | mj-agent CI 实际只用 GitHub | Gitee 镜像 push 失败无人发现，与 mj-system 协同时镜像滞后 | "Gitee 90 天未用" 触发器；建立月度健康检查 |
| `MJ-Agent Commit Message Convention v1.0` 长期 `state: draft` | promotion criteria 永远不满足（无 CI lint、无 20 commit 阈值） | 规范文档化但实际不被遵守 | Phase 1 启动时优先引入 `amannn/action-semantic-pull-request` |
| 7 步 pre-push 检查"建议但不强制" | 实际无人执行 | 推送质量退化 | Phase 0.5 评估自动化 hook |

---

## 8 参考

### 8.1 项目内部

- [[../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from mj-system]] —— 本评估的决策落地
- [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|MJ-Agent Commit Message Convention v1.0]] —— 本评估的规范产出
- [[../archive/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|MJ-Agent 文档管理框架 v1.1（archive）]] —— 本评估自身遵循的治理框架（§3.2 ASSESSMENT 类型 / §4.4 ASSESSMENT 专属字段；本 PR 同时把 Framework 升至 v1.1，详见 [[../adr/[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]]；后续 v2.0 trio 演进见 [[../adr/[ADR]_012_Two_Track_Documentation_Governance|ADR-012]]）
- [[ADR]_008_Co_Deployment_With_MJ_System|ADR-008 Cross-System Boundary with mj-system]] —— 继承 mj-system 治理的跨项目运维上下文
- `plans/mj-agent-roadmap-v1.6.md` —— Phase 0 范围与退出条件

### 8.2 mj-system 源文档（被评估对象）

- `mj-system/develop/docs/rule/[STANDARD]_Commit_Message_Convention.md`（v2.0）
- `mj-system/develop/docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`（v1.0）
- `mj-system/develop/docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md`（v1.0）
- `mj-system/develop/docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning.md`（v1.0）
- `mj-system/develop/docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`（v1.0）

### 8.3 行业规范

- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Angular commit-message-guidelines.md](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md)
- [amannn/action-semantic-pull-request](https://github.com/amannn/action-semantic-pull-request)

---

## 附录 A：社区项目档案

8 个数据 Agent / LLM-Agent OSS 项目的 1-段简介。数据采集日 2026-04-25。

### A.1 LangChain (`langchain-ai/langchain`)

- 默认分支：`master`（trunk）
- 命令式 Conventional Commits 强制于 PR 标题：`.github/workflows/pr_lint.yml` 用 `amannn/action-semantic-pull-request@v6`，types 列表 13 项 (`feat / fix / docs / style / refactor / perf / test / build / ci / chore / revert / release / hotfix`)，scope 是 packages 显式 allowlist (`core / langchain / openai / anthropic / chroma / ...`)
- 单 PR 模板 ~50 行，无角色字段
- 发版 commit `release(<scope>): x.y.z`（如 `release(openai): 1.2.1`）

### A.2 LangGraph (`langchain-ai/langgraph`)

- 默认分支：`main`（trunk）
- 同 LangChain 家族 `pr_lint.yml`，types 11 项，scope 11 项
- 单 PR 模板 ~45 行
- mj-agent 直接依赖 → 跟随其 CI 实践对齐价值最高

### A.3 Vanna.AI (`vanna-ai/vanna`)

- 默认分支：`main`（trunk）
- CONTRIBUTING.md 仅说 "Use clear, descriptive commit messages"，**无** Conventional Commits
- **无** PR 模板
- 发版 commit `Bump version from X to Y`

### A.4 DB-GPT (`eosphoros-ai/DB-GPT`)

- 默认分支：`main`（trunk）
- Conventional Commits 实操但 CI 不强制；`.github/release-drafter.yml` 把 PR title regex 映射到 label（domain-specific labels 含 `prompt / agent / model / connection / ChatData / ChatExcel / ChatDB`）
- 单 PR 模板 ~25 行：Description / Test / Snapshots / 6 项 checklist

### A.5 WrenAI (`Canner/WrenAI`)

- 默认分支：`main`（trunk）
- 分支命名 `chore/<service>/<desc>`（如 `chore/ai-service/dspy`）
- `wren-ai-service/CONTRIBUTING.md` **显式要求**：PR title 用 `feat(wren-ai-service)` / `chore(wren-ai-service)`；scope = service name
- **无** PR 模板

### A.6 AutoGPT (`Significant-Gravitas/AutoGPT`)

- 默认分支：`master`（trunk）
- Conventional Commits 实操，scope 可为 path（如 `fix(backend/copilot): ...`），CI 不强制
- **单** PR 模板，含两个条件化 section ("For code changes" / "For configuration changes")
- 200+ 活跃分支，证明单模板可承载大流量

### A.7 Aider (`Aider-AI/aider`)

- 默认分支：`main`（trunk）
- 仅 2 条本地分支
- 松散 Conventional Commits（`feat: ...` / `fix: ...`），**无** scope，CI 不强制
- **无** PR 模板；CONTRIBUTING.md 鼓励直接提交小 PR

### A.8 Open Interpreter (`OpenInterpreter/open-interpreter`)

- 默认分支：`main`（trunk）
- 自由文本 commit，**非** Conventional Commits
- **单** PR 模板 ~14 行（Describe / Reference issues / 3 项 pre-submission checklist / OS test checkbox）

### A.9 / A.10 权威规范

- **Conventional Commits 1.0.0**：仅强制 `feat` 与 `fix` 两个 type；其他 (`build/chore/ci/docs/style/refactor/perf/test`) 为推荐而非规范；scope 显式 optional；唯一 normative footer 是 `BREAKING CHANGE:`
- **Angular commit-message-guidelines**：8 type (`build/ci/docs/feat/fix/perf/refactor/test`)，scope = npm package name (`animations / common / compiler / core / forms / http / router / platform-browser / ...`)，**无** `chore`

---

## 附录 B：引用清单

- [LangChain pr_lint.yml](https://github.com/langchain-ai/langchain/blob/master/.github/workflows/pr_lint.yml)
- [LangChain PR template](https://github.com/langchain-ai/langchain/blob/master/.github/PULL_REQUEST_TEMPLATE.md)
- [LangGraph pr_lint.yml](https://github.com/langchain-ai/langgraph/blob/main/.github/workflows/pr_lint.yml)
- [LangGraph PR template](https://github.com/langchain-ai/langgraph/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
- [Vanna CONTRIBUTING.md](https://github.com/vanna-ai/vanna/blob/main/CONTRIBUTING.md)
- [DB-GPT pull_request_template.md](https://github.com/eosphoros-ai/DB-GPT/blob/main/.github/pull_request_template.md)
- [DB-GPT release-drafter.yml](https://github.com/eosphoros-ai/DB-GPT/blob/main/.github/release-drafter.yml)
- [WrenAI ai-service CONTRIBUTING.md](https://github.com/Canner/WrenAI/blob/main/wren-ai-service/CONTRIBUTING.md)
- [AutoGPT PR template](https://github.com/Significant-Gravitas/AutoGPT/blob/master/.github/PULL_REQUEST_TEMPLATE.md)
- [Aider CONTRIBUTING.md](https://github.com/Aider-AI/aider/blob/main/CONTRIBUTING.md)
- [Open Interpreter PR template](https://github.com/openinterpreter/open-interpreter/blob/main/.github/pull_request_template.md)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Angular commit-message-guidelines.md](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md)
- [amannn/action-semantic-pull-request](https://github.com/amannn/action-semantic-pull-request)

URL 验证日：**2026-04-25**。
