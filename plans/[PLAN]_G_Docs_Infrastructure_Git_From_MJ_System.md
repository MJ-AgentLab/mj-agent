---
type: plan
summary: 把 mj-system 4 份 git 基础设施 GUIDE + INDEX 镜像到 mj-agent docs/infrastructure/git/，按 mj-agent 12 scope / Phase 0 状态 / v2.0 双轨 frontmatter 改造
owner: 项目负责人
created: 2026-04-30
updated: 2026-04-30
state: completed
track: code
tags:
  - plan
  - documentation
  - infrastructure
  - git
  - track-a
---

# PLAN G — `docs/infrastructure/git/` for mj-agent

## Context

`mj-system` 在 `docs/infrastructure/git/` 维护 4 份 GUIDE + 1 份 INDEX，把 commit / 分支 / 推送 / PR 规范操作化。mj-agent 已经有**基础层**（`[STANDARD]_MJ_Agent_Commit_Message_Convention` + `ADR-010` + `[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0`），但**没有操作侧 GUIDE** —— 开发者目前只能靠 `CLAUDE.md` 摘要 + 直接读 STANDARD 来上手 git 流程。

本次工作把 mj-system 的 4 份 GUIDE 一次性镜像到 mj-agent 并按实际情况改造：
- 12 个 mj-agent 专属 scope（替换 mj-system 的 ETL 服务名 scope）
- 仓库 URL 改为 `MJ-AgentLab/mj-agent` + `gitee.com/ranzuozhou/mj-agent`（双推 remote 已配置，无需改流程）
- mj-agent 暂无 `bump-version.ps1` / `CHANGELOG.md` / Docker，相关章节标注为"Phase 1+ 待引入"
- v2.0 文档框架 frontmatter：补 `track: code` 与 `derives_from`；`domain` 改 `SYS`（mj-agent 枚举无 `GIT`，与 ADR-010 一致）

副作用：激活 `docs/infrastructure/`（`docs/INDEX.md` line 99 已预留为"有独立基础设施内容时"）。

## Files to create

```
docs/infrastructure/git/
├── INDEX.md
├── [GUIDE]_GitHub_Setup_And_Versioning.md
├── [GUIDE]_Git_Branch_Strategy.md
├── [GUIDE]_Git_Push_Workflow.md
└── [GUIDE]_PR_Description_Convention.md
```

**拷贝起点**：`D:\workspace\10-software-project\projects\mj-system\develop\docs\infrastructure\git\<file>`（本地 sibling clone 已验证存在；4 份 GUIDE 全部 `state: draft, version: v1.0, owner: PM, domain: GIT`）。

## Files to modify

- `docs/INDEX.md`
  - 把 `docs/infrastructure/` 行从 `## 尚未建立的 canonical 子目录`（line 99）移除
  - 新增 `## 基础设施（docs/infrastructure/）` 章节，列 `infrastructure/git/INDEX.md` 一行
- `CLAUDE.md`
  - `## Code-Side Documentation` → "Repo conventions (code-side, all governed by Track A standards)" bullet 列下方补一行（紧跟现有 STANDARD/ADR-010/ASSESSMENT 引用）：
    ```
    - 操作性 git 指南（分支、推送、PR 描述、初始化与版本管理）见
      `docs/infrastructure/git/INDEX.md`（4 份 GUIDE，派生自 mj-system v5.0
      `docs/infrastructure/git/`，按 mj-agent scope 与 Phase 0 状态改造）。
    ```

## Per-file 改造矩阵（从 mj-system 原文件起步）

### Frontmatter（每份 GUIDE 统一）

mj-system 原 frontmatter 为单轨 v5.0 风格，mj-agent v2.0 需替换为：

```yaml
---
type: guide
domain: SYS                      # mj-agent allowlist 无 GIT；与 ADR-010、Commit STANDARD 同 SYS
summary: <原 summary 直译/沿用>
owner: 项目负责人                 # mj-agent 用此称呼；mj-system 用 PM
created: 2026-04-30
updated: 2026-04-30
state: draft
version: v1.0
track: code                      # v2.0 新字段；git ops 属代码侧
derives_from: mj-system/develop@<source-filename>   # mj-agent 现存 6 处 derives_from 均用 filename-only，无目录前缀
tags:
  - guide
  - git
  - <topic-specific>
aliases:
  - <English title>
  - <中文 title>
---
```

### 通用 body 替换（4 份 GUIDE 共用）

| 原内容 | mj-agent 改造 |
| --- | --- |
| `MJ-AgentLab/mj-system` 仓库 URL（含克隆/PR/Issue 链接） | `MJ-AgentLab/mj-agent` |
| `gitee.com/ranzuozhou/mj-system` | `gitee.com/ranzuozhou/mj-agent` |
| commit scope 例（`aec/dqv/qcm/sac/fc/qvl`） | mj-agent 12 scope（`agent/llm/prompt/skill/sql/db/config/tests/eval/ci/deps/infra`）— 引自 `[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §4 |
| `[[STANDARD]_Commit_Message_Convention\|...]]` 反链 | `[[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention\|mj-agent Commit Message 规范 v1.0]]` |
| `[[STANDARD]_Documentation_Management_Framework_v5.0]]` 反链 | `[[../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework\|mj-agent 文档治理元框架 v2.0]]` |
| `[[STANDARD]_Obsidian_Markdown]]` | `[[../../rule/[STANDARD]_GitHub_Markdown\|GitHub-Flavored Markdown 编写规范 v1.0]]` |
| `[[RUNBOOK]_CICD_Release_Process]]` 反链（多处） | 改为纯文本 `CI/CD 发布流程手册（待 docs/runbook/ 在 Phase 0.5 启用，参见 [[ADR-010]] §Defer）` —— 避免 A4 wikilink 校验失败 |
| `[[GUIDE]_Developer_Onboarding]]` 反链 | 同上，纯文本占位 |
| `[[GUIDE]_Local_Development_Testing]]` 反链 | 同上，纯文本占位 |
| Docker / SQL 自检/biz_ads 案例 | 替换为 mj-agent 工具链：`uv sync`、`uv run pytest tests/unit`、`uv run ruff check`、`uv run mypy src/mj_agent` |

### Per-file deltas

**`[GUIDE]_GitHub_Setup_And_Versioning.md`**（mj-system 约 390 行 → mj-agent 约 250 行）

- §1.2 推送命令：保留（双推已配置）；改 `mj-system` → `mj-agent`
- §1.3 分支保护规则：保留（普适）
- §3 SemVer 规则：保留（前瞻性指南，对应 STANDARD §9 促活条件 Phase 1+）
- §4.1 文件位置表：仅留 `pyproject.toml` + `README.md` + `CLAUDE.md`；删除 `main.py` / `Dockerfile` / `docker-compose*.yml` / `QUICK_STATUS_SUMMARY.txt` / `CHANGELOG.md` 行（mj-agent 暂无）；首行加注："mj-agent 当前 `pyproject.toml` 为唯一权威；其他文件待 Phase 1+ 引入"
- §4.2 发布流程概览：改为"mj-agent Phase 0 暂未引入版本发布流程；待 Phase 1+ 与 `docs/runbook/[RUNBOOK]_Release_Process.md` 共同落地"
- **§5 「版本号批量更新脚本」整段删除**（mj-agent 无 `bump-version.ps1`），代之以一段："mj-agent 暂未引入批量更新脚本；版本号集中存于 `pyproject.toml`，发布时手工更新即可。Phase 1+ 引入更多版本承载文件后会同步建立脚本（参见 ADR-010 §Defer）。"
- §6 验证清单：删除涉及 `.env` / Docker / 服务启动的检查项；保留 `git remote -v` / `git branch -r` / GitHub 分支保护检查
- §7 速查表：保留 git 操作行；删除 `mj-system` → `mj-agent` URL

**`[GUIDE]_Git_Branch_Strategy.md`**（mj-system 约 566 行 → mj-agent 约 500 行）

- §0 「获取项目代码」：URL 改 mj-agent；bare-repo worktree 步骤逐字保留（`cwd = .../mj-agent/develop` 即印证）
- §1 「分支模型」：保留（5 永久/临时分支与 mj-agent 完全一致）
- §2 「分支命名」：保留；§2.3 命名示例改为 mj-agent 场景（`feature/12-metrics-glossary-skill`、`bugfix/25-guardrail-regex-fix`、`maintain/8-add-pr-template`）
- §3 「分支类型与 Commit 类型」：表格保留（与 mj-agent STANDARD §5 一致）；§3.1 反链改 mj-agent commit STANDARD
- §4 各分支操作流程：所有 `git commit -m "feat(aec): ..."` 等示例 scope 改 mj-agent scope（`feat(skill): 新增 metrics-glossary skill`、`fix(sql): 修正 guardrail regex`、`docs: 更新 SKILL.md`、`infra: 新增 PR 模板`）
- §4.5 hotfix 流程：保留（结构性，无 mj-agent 差异）
- §6 worktree 用法：保留
- §7 速查表：scope 列调整

**`[GUIDE]_Git_Push_Workflow.md`**（mj-system 约 667 行 → mj-agent 约 480 行）

- §0 「适用场景」：保留；前置步骤表删除"Local_Development_Testing"列改 mj-agent 工具链
- §1 commit 质量检查：保留；§1.2 表格保留（与 mj-agent STANDARD §5 一致）
- §2 「CHANGELOG 更新确认」：**整段加注**："本节描述 Phase 0.5+ 目标态。mj-agent 当前 `CHANGELOG.md` 尚未引入（见 ADR-010 §Defer 与 Commit STANDARD §9 促活条件）。在 CHANGELOG 引入前，可跳过本节。"。表格保留作为前瞻性指引
- §3 工作目录干净检查：保留；§3.5 `.gitignore` 排除项保留 `.claude/settings.local.json`（mj-agent gitStatus 显示该文件即为修改状态）
- §4 分支命名验证：保留
- §5 远程分支同步：保留
- §6 执行推送：保留双推（mj-agent 已配置）；§6.3 worktree 注意事项保留；§6.4 错误表删除"`upload-pack: not our ref`"行（mj-agent CI 不复现）；§6.5 双推保留（含 alias）
- §7 推送后验证：保留
- §8 下一步 — 创建 PR：保留
- §9 速查清单：保留
- §10 常见问题：**删除 Q6（Gitee shallow fetch / `upload-pack: not our ref`）** —— mj-agent CI 仅 `python -m compileall`，不会触发该问题，留之误导；保留 Q1-Q5、Q7（pre-push hook，通用 git 自动化）

**`[GUIDE]_PR_Description_Convention.md`**（mj-system 约 396 行 → mj-agent 约 330 行）

- §1 为什么需要区分 PR 模板：保留
- §2.1 模板 × 分支类型 × 目标分支表：6 行保留（`.github/PULL_REQUEST_TEMPLATE/{bugfix,documentation,feature,hotfix,maintain,release}.md` 已验证存在于 mj-agent）
- §2.2 commit 类型矩阵：保留（与 mj-agent STANDARD §5 一致）
- §3 各模板详解：保留 6 个 §3.x；mj-system 「QCM DWS 迁移实际案例」（§3.1 中段，约 30 行）替换为占位："首份案例待 mj-agent 完成首个完整 PR 流程后回填。字段填法可参考 mj-system 同名 GUIDE 历史案例。" 或简化为字段说明（不带具体案例）
- §4.1 `gh` CLI 命令：保留（普适）
- §4.3 Code Review ↔ 自检对齐表：删除「Docker 自测」「SQL 脚本：命名规范、schema 正确」「无硬编码 IP/密码/路径」三行（mj-agent 暂不适用）；新增三行：
  - `uv run ruff check` 无 lint 错误 → feature/bugfix/maintain
  - `uv run mypy src/mj_agent` 通过 → feature/bugfix
  - `uv run pytest tests/unit` 通过 → feature/bugfix
  - skill loader frontmatter strip 行为不被绕过（如触及 `src/mj_agent/skills/` 或 `src/mj_agent/prompts/`）→ feature
- §5 速查表：保留

### `INDEX.md`（新建，约 30 行）

```markdown
# Git 基础设施索引

> **所属目录**：`docs/infrastructure/git/`
> **说明**：4 份 GUIDE 派生自 mj-system v5.0 同名目录，按 mj-agent scope、Phase 0 状态与 v2.0 framework 改造。摘要取自每份文档 frontmatter `summary`。

---

## 文档列表

| 文档 | 类型 | 摘要 |
|------|------|------|
| [GitHub 设置与版本管理]([GUIDE]_GitHub_Setup_And_Versioning.md) | GUIDE | GitHub 设置与版本管理（mj-agent 适配版） |
| [Git 分支策略指南]([GUIDE]_Git_Branch_Strategy.md) | GUIDE | Git 分支策略指南（mj-agent 5 分支模型） |
| [Git 推送工作流]([GUIDE]_Git_Push_Workflow.md) | GUIDE | Git 推送工作流（含双推 Gitee + GitHub） |
| [PR 描述规范指南]([GUIDE]_PR_Description_Convention.md) | GUIDE | PR 描述规范指南(6 模板 × `gh` CLI) |

---

## 关联入口

- [返回上级索引](../../INDEX.md)
- [[../../rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|mj-agent 文档治理元框架 v2.0]]
- [[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention|mj-agent Commit Message 规范 v1.0]]
- [[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System|ADR-010 Git and Commit Conventions Adopted from mj-system]]
- [[../../assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0|mj-system Git 规范在 mj-agent 的适配评估 v1.0]]

---

## 派生说明

| 本文件 | mj-system 源 | 主要改造 |
|--------|------------|---------|
| `[GUIDE]_GitHub_Setup_And_Versioning.md` | 同名 | 删除 bump-version.ps1 §5；缩减 §4.1 文件表至 mj-agent 实际 |
| `[GUIDE]_Git_Branch_Strategy.md` | 同名 | scope/URL 替换 |
| `[GUIDE]_Git_Push_Workflow.md` | 同名 | 删除 §10 Q6（Gitee shallow fetch）；CHANGELOG §2 标注 Phase 0.5+ |
| `[GUIDE]_PR_Description_Convention.md` | 同名 | §4.3 Code Review 自检表换成 ruff/mypy/pytest 行 |
```

## A1-A6 PR gate 合规清单

| 门 | 满足方式 |
| --- | --- |
| **A1 路径** | `[GUIDE]_<Subject>.md`（GUIDE 类型不需 `_vX.Y` 文件名后缀，但 frontmatter `version: v1.0`）；INDEX.md 命名合法 |
| **A2 frontmatter** | 含 `type/domain/summary/owner/created/updated/state/version/track`；附 `derives_from/tags/aliases` |
| **A3 state** | `draft`（首版） |
| **A4 wikilinks** | 所有跨仓引用（mj-system docs）改外部相对 URL 或纯文本；前向引用（runbook / onboarding 暂未建）一律改纯文本 + TODO，避免内部 wikilink 指向不存在文件。**Phase 0 阶段 A4 为人工 review，无 CI 自动校验**（Code_Side §7.1 列为 Phase 2 CI 自动化项；mj-agent 当前的 `scripts/check_wikilinks.py` 仅是 ADR-011 §5.6.2 v1.1 archive 守卫，**不**校验通用 wikilink 解析） |
| **A5 INDEX** | 修改 `docs/INDEX.md` + 新建 `docs/infrastructure/git/INDEX.md` |
| **A6 CLAUDE.md** | 在 `## Code-Side Documentation` "Repo conventions" 列表补一行链 `docs/infrastructure/git/INDEX.md` |

## 已存在可直接复用的工件

- `[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §4 scope 列表 + §5 分支矩阵 → GUIDE 反链不重复
- `.github/PULL_REQUEST_TEMPLATE/{bugfix,documentation,feature,hotfix,maintain,release}.md` → PR_Description GUIDE 直接引用
- `.github/PULL_REQUEST_TEMPLATE.md` → 默认模板，留作兜底
- bare-repo worktree 当前布局（`cwd = .../mj-agent/develop`，sibling `main`/`feature/*`/`hotfix/*` 子目录） → Branch_Strategy GUIDE §0 + §6 不需结构性修改
- 双推 remote（`origin = MJ-AgentLab/mj-agent`，`gitee = ranzuozhou/mj-agent`） → Push_Workflow GUIDE §6.5 直接套用
- `scripts/check_wikilinks.py`（CLAUDE.md §Documentation 引用）→ 仅守 v1.1 living/frozen 引用，不参与 A4 通用校验

## Sequencing within the PR

1. 创建 `documentation/infrastructure-git-docs` 分支（per STANDARD §5 — 纯文档分支）
2. 拷贝 4 份 mj-system 文件到 `docs/infrastructure/git/`
3. 替换 frontmatter（每份）
4. 应用 "通用 body 替换" + "Per-file deltas"
5. 新建 `docs/infrastructure/git/INDEX.md`
6. 修改 `docs/INDEX.md`：移除 `docs/infrastructure/` 在"尚未建立"表的行，新增 `## 基础设施（docs/infrastructure/）` 章节
7. 修改 `CLAUDE.md`：`## Code-Side Documentation` "Repo conventions" 列表补一行
8. 跑 v1.1 archive guard：`uv run python scripts/check_wikilinks.py`（确认未引入 v1.1 living 引用，0 violations）；A4 普通 wikilink 由 reviewer 人工 audit
9. 提交：`docs(governance): seed docs/infrastructure/git/ with 4 GUIDE + INDEX (derives mj-system)`（沿用近期 `docs(governance)` scope 风格 — `7ba760b` `dae617b` `c27ce02`）

## Verification（落地后）

1. `uv run python scripts/check_wikilinks.py` — 0 violations（仅确认未引入对 v1.1 archive 的 living 引用；该脚本是 ADR-011 §5.6.2 living/frozen 守卫，**不**校验通用 wikilink 解析）
2. IDE markdown 预览：每份文档的 H1/H2 锚点链接、表格渲染、代码块语言标记正常
3. `git status --short` 仅含本次改动文件（无遗留）
4. `docs/INDEX.md` 中 `docs/infrastructure/` 已从 reserved 表迁移到正式章节
5. `CLAUDE.md` "Repo conventions" 子节包含新链
6. 抽查反链解析（人工，A4 ad-hoc check）：在 IDE 中点击 `[[../../rule/[STANDARD]_MJ_Agent_Commit_Message_Convention]]`、`[[../../adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System]]` 跳转正常
7. 渲染对照：本地 GitHub markdown 预览（VS Code Markdown Preview Github Styling 扩展）与 mj-system 原文档对比，结构一致
8. grep 残留：每份 GUIDE 跑 `grep -E 'mj-system|aec|dqv|qcm|sac|fc|qvl' <file>` 应 0 命中（mj-system 旧 scope 全部替换；mj-system 仓名仅在 derives_from 出现）

## Out of scope

- `docs/_templates/TEMPLATE_GUIDE.md`：Phase 0.5 单独 PR（按 `docs/INDEX.md` line 67 规划；本 PR 4 份 GUIDE 可作为该模板的现成范式）
- `docs/runbook/[RUNBOOK]_Release_Process.md` / `[RUNBOOK]_CICD_Release_Process.md`：Phase 0.5/1，依赖 mj-agent 发布流程成型
- `docs/guide/[GUIDE]_Developer_Onboarding.md`：Phase 0.5
- CI lint adoption（`amannn/action-semantic-pull-request` PR title 校验）：Phase 1+ 按 ADR-010 §Defer
- `bump-version.ps1`：Phase 1+，待 mj-agent 引入版本发布流程
- `CHANGELOG.md` 引入：Phase 0.5/1 按 STANDARD §9 促活条件
- `domain: GIT` 加入 mj-agent 枚举：本 PR 不修改 Meta_Framework v2.0 §9；如未来希望专列 GIT domain，单独 PR
- 通用 wikilink 校验脚本：本 PR 不修 `scripts/check_wikilinks.py`；Phase 1+ 引入独立通用 wikilink 校验时另开 PR

## 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| mj-system 源文件在本 PR 起草到合入期间漂移（mj-system 仓上游修订） | 拷贝时 `derives_from` 用 filename-only（不绑定 sha）；下次 mj-system 同名文档显著修订时由 reviewer 决定是否回流；本 PR 不追同步 |
| Phase 0 阶段 A4 内部 wikilink 无 CI 校验，依赖人工 review | reviewer 自检清单纳入「点击全部 `[[...]]` 跳转正常」；Phase 2 CI 自动化项落地后会兜底（Code_Side §7.1） |
| 12 scope / URL 替换逐处人工修改可能漏改 | sequencing §3-§4 完成 frontmatter + body 替换后，逐 GUIDE 跑 grep `mj-system\|aec\|dqv\|qcm\|sac\|fc\|qvl` 确认 0 残留（Verification §8）；mj-system 旧 scope 命中即排查 |
| `[[../../rule/...|...]]` 路径式 wikilink 在不同渲染器（Obsidian vs GitHub）兼容性不一 | 4 GUIDE 均按 GitHub-Flavored Markdown v1.0 编写正文；wikilink 仅作为附属反链；GitHub 原生不渲染 `[[...]]` 但作为纯文本不破坏阅读；Obsidian 端正常解析 |
| 「v1.1 archive 守卫脚本」名字（`check_wikilinks.py`）易被误读为通用校验 | 本 PR 在 A1-A6 §A4 与 Verification §1 段落均显式标注其实际作用范围；Phase 1+ 引入独立通用 wikilink 校验时另开 PR |
| 4 份 GUIDE 总修订工作量大，单 PR review 负担重 | Sequencing 9 步分步执行；commit 仍合并为一个，但本 PLAN 文件可作为 reviewer 的 per-file 改造矩阵索引（A1-A6 / Verification 自检条款逐条对照） |

## Source-of-truth references

| Item | Path |
| --- | --- |
| mj-system git docs（拷贝源） | `D:\workspace\10-software-project\projects\mj-system\develop\docs\infrastructure\git\` |
| Frontmatter 规范 | `docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework.md` §4 |
| Track A 门禁 | `docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework.md` §7.1 |
| Markdown 语法 | `docs/rule/[STANDARD]_GitHub_Markdown.md` |
| commit type/scope | `docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md` §3 §4 |
| 决策依据 | `docs/adr/[ADR]_010_Git_And_Commit_Conventions_From_MJ_System.md` |
| 适配评估证据 | `docs/assessments/[ASSESSMENT]_MJ_System_Git_Conventions_Adoption_v1.0.md` |
| Wikilink 校验脚本（v1.1 archive 守卫） | `scripts/check_wikilinks.py` |
| INDEX 入口 | `docs/INDEX.md` |
| Claude 指引 | `CLAUDE.md` §Code-Side Documentation |
