---
type: adr
domain: SYS
summary: mj-agent 从 mj-system 继承 git 工作流与 commit 规范，附 Keep/Adapt/Defer 矩阵与再评估触发器
owner: 项目负责人
created: 2026-04-25
updated: 2026-04-25
state: active
decision: accepted
track: code
---

# ADR-010: Git and Commit Conventions Adopted from mj-system

## Context

mj-agent 在 bootstrap 阶段从 mj-system 继承了一整套 git 治理基础设施：

- **Bare-repo Worktree** 布局（`.bare/` + 兄弟工作树）
- **双远端**：`origin` = GitHub `MJ-AgentLab/mj-agent`、`gitee` = `gitee.com/ranzuozhou/mj-agent`
- **6 份 PR 模板**：`.github/PULL_REQUEST_TEMPLATE/{feature,bugfix,documentation,maintain,hotfix,release}.md`
- **声明 Conventional Commits**（`CLAUDE.md` §Repo conventions），但实际首个 commit `b932007 Initial commit: mj-agent Python 3.13 scaffold` 不符合 `type(scope):` 格式
- **派生中的文档治理框架**：[[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|Framework v1.1（archive）]]（draft；本 ADR 撰写时为 v1.0，由 [[ADR]_011_Doc_Versioning_And_Archive_Convention|ADR-011]] 升级至 v1.1；之后由 [[ADR]_012_Two_Track_Documentation_Governance|ADR-012]] 升级至 v2.0 trio）

源规范来自 mj-system：

- `[STANDARD]_Commit_Message_Convention.md`（v2.0），含 7 个 type 与 mj-system 服务专属 scope `aec/dqv/qvl/qcm/sac/fc`
- `[GUIDE]_Git_Branch_Strategy.md`、`[GUIDE]_Git_Push_Workflow.md`、`[GUIDE]_GitHub_Setup_And_Versioning.md`、`[GUIDE]_PR_Description_Convention.md`

需要决策的问题：

1. **scope 列表不可直接用**：mj-system 的 scope 缩写（`aec/dqv/qcm` 等）是 mj-system 的 ETL 微服务名，对 mj-agent 无意义。继续直接套用会让首个 commit 起就漂移
2. **重量级与 Phase 0 规模的张力**：[[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|配套评估文档]] §4 的社区调查显示，8 个数据 Agent OSS 项目（LangChain / LangGraph / Vanna / DB-GPT / WrenAI / AutoGPT / Aider / Open Interpreter）**0/8** 使用 GitFlow `develop`+`main` 双干、**0/8** 使用 6 份 PR 模板、**0/8** 发明自定义 footer 关键字。mj-agent 当前是 1 人团队 + Phase 0，重量级流程缺乏直接收益证据
3. **跨项目运维一致性**：但 mj-agent 与 mj-system 是相邻 consumer 关系（[[ADR]_008_Co_Deployment_With_MJ_System|ADR-008]] 已确定独立 compose project + 环境矩阵对齐），运维与开发者同时面对两个仓库；保持 git 操作肌肉记忆相同有运维收益
4. **首份 commit 不合规**已成事实——再不固化规则，后续提交将继续漂移

## Decision

采用 **务实适配（Pragmatic Adaptation）** 策略：

| mj-system 规则 | mj-agent 决策 | 再评估触发器 |
|---|---|---|
| Bare-repo Worktree 布局 | **KEEP**（已安装、与 mj-system 切换零摩擦） | 团队 < 1 dev 或工作树破坏工具链 |
| 双远端（Gitee + GitHub） | **KEEP**（与 mj-system 环境矩阵对齐 + CI 路径共用） | mj-agent 与 mj-system 完全分离 OR Gitee 镜像连续 90 天未使用 |
| `develop` + `main` 双干模型 | **KEEP**（mj-system 一致性） | 首次 hotfix 暴露混乱 OR Phase 1 review |
| 5 类临时分支（feature/bugfix/documentation/maintain/hotfix） | **KEEP** | 同上 |
| 6 份 PR 模板（每分支类型一份） | **KEEP**（已安装、零边际成本） | 首次贡献者选错模板 |
| 7 步 pre-push 检查清单 | **KEEP** 作为 guidance，**NOT** 强制为 hook | Phase 1：评估 hook 自动化 |
| Conventional Commits `type(scope): summary` | **ADAPT** → [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention\|MJ-Agent Commit Message Convention v1.0]] | 见该规范 §9 promotion criteria |
| 服务 scope `aec/dqv/qvl/qcm/sac/fc` | **DROP**（与 mj-agent 无关） | N/A |
| 7 个 type（`feat/fix/perf/refactor/test/docs/infra` + `merge`） | **KEEP**（一字不改） | 引入新业务领域时评估增加 |
| 分支 × type 对齐矩阵 | **KEEP**（一字不改），仅 scope 列重建 | N/A |
| 自定义 footer 关键字 | **DROP / NEVER ADOPT**（mj-system 也未使用；社区 0/8 使用） | N/A |
| 多文件版本号同步（`pyproject.toml` + `Dockerfile` + `main.py` + ...） | **DEFER** → 集中到 `pyproject.toml` 单一来源 | 首次发版 |
| 角色门禁字段（PM/DBA/SRE 审核者） | **DEFER**（团队规模 < 4） | 团队规模 ≥ 4 |
| CI 强制校验 commit 格式 | **DEFER** → 推荐 Phase 1 引入 `amannn/action-semantic-pull-request` | 配套 commit 规范升至 `state: active` 之后 |

具体落地：

1. 本 PR 同时落地 [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|MJ-Agent Commit Message Convention v1.0]]（`state: draft`）作为对前述 ADAPT 决策的执行
2. 配套评估文档 [[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|本决策的依据]] 记录证据来源
3. **本 PR 故意不更新 `CLAUDE.md` §Repo conventions**——属于 Framework v1.0 §6.4 allowlist 触发的 A6 同步检查，但用户决策范围（评估 + 规范 + ADR 三件套）不含 CLAUDE.md 编辑。承诺紧接的下一个 PR 修复（见 §Consequences "中性"）

## Consequences

**正面**

- Phase 0 后续 commit 起立即有可对照的规范文档；首次贡献者只需读一份 STANDARD
- `type / scope / 分支对齐` 与 mj-system 完全相同，运维同时操作两仓零切换成本
- scope 列表针对 mj-agent 模块（`agent / llm / prompt / skill / sql / db / config / tests / eval / ci / deps / infra`），首日即可用
- 配套评估文档为后续每一项 DEFER 决策提供再评估触发器，避免"忘记 revisit"的治理债务
- 显式拒绝自定义 footer 关键字（社区 0/8 使用），堵住未来 prompt-version / eval-score 等"看似聪明"的发明

**负面**

- 继续承担"已安装但未被 Phase 0 规模用满"的重量（6 PR 模板、`develop`/`main` 双干、双远端）。社区 0/8 使用此组合，新外部贡献者需要额外定向
- ADR-010 将 KEEP 与 DEFER 混用，未来某项触发器命中时需同时改 STANDARD + ADR + INDEX，治理回路较长
- DEFER `amannn/action-semantic-pull-request` 意味着 Phase 0 阶段无 CI 强制；规范是否被遵守完全靠 PR review 和 promotion criteria（`MJ-Agent Commit Message Convention v1.0` §9）人工把关

**中性**

- **本 PR 通过 A6**（Framework v1.0 §6.4 + §7.1 A6）：commit 规范是"全局高频标准"，按 allowlist 触发 `CLAUDE.md` 同步检查。本 PR 同时编辑 `CLAUDE.md` §Repo conventions：把 "Commits follow Conventional Commits" 一行扩写为指向新 STANDARD（路径 + 类型清单 + scope 来源说明），同步把分支说明扩到 5 种、把 ADR 清单从 `000/001/002/003/006/008/009` 更新为 `000/001/002/003/006/008/009/010`，并加一行指向本 ADR + 配套 ASSESSMENT。剩余 follow-up（6 份 PR 模板的"自检结果"段引用新 STANDARD）属配套评估文档 §6.2 计划，不阻塞 A6
- 配套 STANDARD 进入 `state: draft`；按其 §9 promotion criteria 至少 20 次合规提交或引入 PR 标题 lint 后才会升至 `active`。Phase 0 期间 STANDARD 与现实之间存在受控 drift 是设计预期，不是疏漏

## Alternatives considered

**A. 严格社区对齐简化**：把 6 PR 模板压成 1 份（LangGraph 风格 ~40 行），废弃 `develop` 改用 trunk-on-`main`，废弃双远端。

拒绝原因：当前阶段没有任何具体痛点，强行对齐社区只制造迁移成本。重量级元素已安装，留它"备用"的成本只是 review 注解噪声；但移除它的成本是切换跨项目运维流程 + 重训肌肉记忆。社区证据的价值是**告诉未来的我们何时简化**，而不是**强制此刻就简化**。

**C. 验证现状（不动 scope 列表）**：保留 mj-system 的 `aec/dqv/qcm` scope 列表不动，理由是"反正不用就是"。

拒绝原因：会让 Phase 0 的 commit 处于"声称遵守规范但实际无法填合法 scope"的尴尬态——首位贡献者就会把 scope 留空，从此规范名存实亡。规范要么实际可用，要么不写；中间态最差。

## References

- [[../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|mj-system Git 规范在 mj-agent 的适配评估 v1.0]] —— 本决策的证据
- [[../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|MJ-Agent Commit Message Convention v1.0]] —— 本决策的执行
- [[ADR]_008_Co_Deployment_With_MJ_System|ADR-008 Cross-System Boundary with mj-system]] —— 跨项目边界（独立 compose project + consumer 关系）上下文
- [[../archive/rule/[DEPRECATED]_[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1|MJ-Agent 文档管理框架 v1.1（archive）]] §6.4 / §7.1 A6 —— CLAUDE.md 同步约束（本 PR 故意不过的门禁；v1.1 已归档，等价语义见 v2.0 trio Meta + Code_Side §7.1 A6）
- mj-system 源文档：
  - `mj-system/develop/docs/rule/[STANDARD]_Commit_Message_Convention.md`
  - `mj-system/develop/docs/infrastructure/git/[GUIDE]_Git_Branch_Strategy.md`
  - `mj-system/develop/docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md`
  - `mj-system/develop/docs/infrastructure/git/[GUIDE]_GitHub_Setup_And_Versioning.md`
  - `mj-system/develop/docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md`
- 社区证据（评估 §4 引用，URL 验证日 2026-04-25）：
  - [LangChain pr_lint.yml](https://github.com/langchain-ai/langchain/blob/master/.github/workflows/pr_lint.yml)
  - [LangGraph pr_lint.yml](https://github.com/langchain-ai/langgraph/blob/main/.github/workflows/pr_lint.yml)
  - [DB-GPT release-drafter.yml](https://github.com/eosphoros-ai/DB-GPT/blob/main/.github/release-drafter.yml)
  - [WrenAI wren-ai-service/CONTRIBUTING.md](https://github.com/Canner/WrenAI/blob/main/wren-ai-service/CONTRIBUTING.md)
  - [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- `plans/mj-agent-roadmap-v1.6.md` —— Phase 0 范围与退出条件
- `CLAUDE.md` §Repo conventions —— 当前仓库级声明（待下一 PR 同步至本规范）
