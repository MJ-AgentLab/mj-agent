---
type: plan
summary: Issue 538 原生开发技能、PR 描述指南与政策的模板字段同步
owner: ranzuozhou
created: 2026-10-10
updated: 2026-10-10
state: completed
completed: 2026-10-10
track: engineering-workflow
---

# Issue #538 PR 模板字段同步

## 追踪与批准

- Issue：[GitHub #538](https://github.com/MJ-AgentLab/mj-agent/issues/538)。
- 基线：`develop@9b36f2d2b099568437732eea4953dce1d9e6c9b5`；独立工作树分支 `documentation/538-pr-template-field-sync`。
- Owner 在当前会话明确要求实施本计划，包括以下六份修复文件、必要的 working PLAN、Issue 范围同步，以及 `policies/ai-agent.md` §6.2 的具体修订与版本更新。
- Owner 随后明确批准本分支七份文件的 commit（`docs: sync PR template field references`）、按 Gitee → origin 普通双推及以 develop 为 base 创建 PR；各步骤按实际结果留证。merge 与最终验收由 Owner 执行。合并及验收前 Issue 保持 open，本计划保持 active。

## 范围与实施顺序

| 文件 | 变更 |
|---|---|
| `.agents/skills/mj-agent-git-pr/SKILL.md` | 按实际模板目录选择；补齐 release、文档自检与每行 AI Self-Check；明确四项报告及根模板两段完整取用 |
| `.agents/skills/mj-agent-doc-review/SKILL.md` | 移除失实计数，逐项对照选定类型模板及根模板取用项 |
| `.agents/skills/mj-agent-flow-self-review/SKILL.md` | 修正模板依据与漏 release 的路径枚举 |
| `.agents/skills/mj-agent-git-check-merge/SKILL.md` | 移除失实计数及枚举，以实际模板核对完整性，覆盖 release |
| `docs/infrastructure/git/[GUIDE]_PR_Description_Convention.md` | 补齐速查与共用要求，保留类型结构与历史；更新为 v1.1 |
| `policies/ai-agent.md` | §6.2 改为准确的载体、同步责任及 CI 证据边界；更新为 0.9，保留 state、审批边界与历史 |
| `plans/[PLAN]_538_pr_template_field_sync.md` | 记录批准范围、验证、AC 与交付状态 |

先核对实际模板与缺项，再维护上述说明，最后运行现有检查、逐文件审阅、同步 Issue 并准备 PR 正文草案。四份技能 frontmatter 不变。

## 文档决策

| 类型 | 决策 |
|---|---|
| PLAN | 新增本 working PLAN；多文件变更不适用单文件落盘豁免 |
| SPEC | 无公共 API、运行时接口或类型变化，无需新增 |
| ADR | 无架构或批准边界决策变化，无需新增 |
| RUNBOOK | 无操作流程变化，无需新增 |
| GUIDE | 更新既有 PR 描述指南 |
| STANDARD | 无；政策说明在既有文件修正 |
| Local ISSUE | 无；使用 GitHub #538 |
| ASSESSMENT | 无；核查结果记在本计划与 PR 草案 |
| CHANGELOG | 无用户可见运行时变化，无需更新 |
| INDEX | 无既有路径、名称或入口变化；working PLAN 使用 `plans/` 追踪，无需新增索引条目 |

## 验证方法与风险

1. 实施前后枚举 `.github/PULL_REQUEST_TEMPLATE/`，核对选择矩阵、必填表与 GUIDE 文件名集合。
2. 逐模板对照全部标题、折叠检查及必答项；release 保留标题层级与发布字段，documentation 检查嵌入自检结果，hotfix 回滚必填。
3. 对四份技能反扫旧计数与漏 release 的枚举，逐行确认 AI Self-Check。根模板 Inventory、Docker Impact 均完整取用并逐项作答。
4. 运行下表现有检查，记录真实退出码；额外核对新增引用及技能 frontmatter 与基线一致。
5. 审查最终 diff，仅含范围内七份文件；不触及 develop 工作树其他任务的未提交内容。

结构检查不核验模板字段语义；逐模板对照用于补足此证据。静态通过不能证明实际 LLM 装配 PR 的行为。政策编辑仅限获批说明，不改变 Owner 权限。无需新增测试、脚本或 CI gate，也不运行 live probe、容器或外部依赖测试。

## 检查记录

运行日期：2026-10-10。复用 develop 的现有 `.venv`，设置进程级 `UV_PROJECT_ENVIRONMENT`；全部 `uv run` 使用 `--frozen --no-sync`，未安装或同步依赖。

| 检查命令（工作树根） | 实施前 | 实施后 |
|---|---|---|
| `uv run --frozen --no-sync python scripts/sdd/check_native_skills.py --surface skills` | exit 0 / STATIC_PASS | exit 0 / STATIC_PASS，errors 空；host/services NOT_TESTED |
| `uv run --frozen --no-sync python scripts/sdd/check_native_skills.py --surface resources` | exit 0 / STATIC_PASS | exit 0 / STATIC_PASS，errors 空；host/services NOT_TESTED |
| `uv run --frozen --no-sync python scripts/sdd/check_native_governance.py --surface entries` | exit 0 / STATIC_PASS | exit 0 / STATIC_PASS，errors 空；host NOT_TESTED |
| `uv run --frozen --no-sync python scripts/sdd/check_native_governance.py --surface consumers` | exit 0 / STATIC_PASS | exit 0 / STATIC_PASS，errors 空；host NOT_TESTED |
| `uv run --frozen --no-sync python scripts/check_frontmatter.py` | exit 0 / 147 canonical docs 合法 | exit 0 / 148 canonical docs 合法 |
| `uv run --frozen --no-sync python scripts/check_wikilinks.py` | exit 0 / archive-ref 与根文件 A4 均 0 violations | exit 0 / 13 archived files 的 archive-ref 0 violations；5 root files 的 A4 0 unresolved targets |

实施后第一次运行漏设验证环境：skills/resources/frontmatter/wikilink 因 `yaml` 或 `frontmatter` 缺失 exit 1，entries/consumers exit 0；明确指定 develop 既有环境后，上表全部重跑 exit 0。未安装依赖；新工作树中自动创建的空 `.venv` 是忽略内容，未纳入 diff。

一次性内存字段对照在实施前 exit 1，检出 release 缺行、文档与 AI 字段遗漏、失实计数及政策旧说明；实施后 exit 0 / PASS，problems 空。未向仓库新增脚本或测试。实际目录、选择矩阵、技能必填表与 GUIDE 速查集合均为 `bugfix.md / documentation.md / feature.md / hotfix.md / maintain.md / release.md`。

逐模板读取全部标题、三个 track 折叠块、四项 AI 报告及根模板两项取用指针，结果如下（仅为本基线观测）：

| 模板 | 标题数 | 折叠块 | 结构核对 |
|---|---|---|---|
| bugfix | 7 | Code / Agent / Engineering | 文档与 AI 自检均列入 |
| documentation | 4 | Code / Agent / Engineering | 文档检查嵌在自检结果，没有虚构独立小节 |
| feature | 6 | Code / Agent / Engineering | 文档与 AI 自检均列入 |
| hotfix | 8 | Code / Agent / Engineering | 回滚预案必填，紧急通道检查保留 |
| maintain | 6 | Code / Agent / Engineering | 文档与 AI 自检均列入 |
| release | 6 | Code / Agent / Engineering | Release 标题为二级，其余五项为三级；含 Details |

额外范围与引用核查 exit 0 / PASS：四份技能 frontmatter 与基线一致；新增根模板 / 目录引用目标存在；政策仅改变批准的 §6.2、version/updated 与追加修订记录；GUIDE 历史记录保留。`git diff --check` exit 0，`git diff --name-only` 与未跟踪 PLAN 合并后恰为七份范围文件。模板本身未改，develop 工作树的其他任务文件原位保留。

## AC 证据映射与交付

| AC | 验证对象与证据 | 状态 |
|---|---|---|
| AC-1 | git-pr 必填表逐行含 AI Self-Check；共用说明含 §6.1 四项及完整根模板取用；内存字段对照 PASS | 本地 PASS |
| AC-2 | 实际目录、选择矩阵、必填表与 GUIDE 文件名集合一致；目标技能旧计数反扫无命中 | 本地 PASS |
| AC-3 | 三份关联技能引用实际目录及根模板，显式覆盖 release；merge 选择表逐模板核对 | 本地 PASS |
| AC-4 | 上表语义对照；GUIDE v1.1 与政策 0.9，历史保留，§6.2 无失实活体断言 | 本地 PASS |
| AC-5 | skills/resources/entries/consumers 各 exit 0 / STATIC_PASS，输出见检查记录 | 本地 PASS（结构） |
| AC-6 | frontmatter/wikilink exit 0；新增引用目标存在，技能 frontmatter 不变，七文件 diff 检查通过 | 本地 PASS |
| AC-7 | 按实际 documentation 模板准备 PR 草案，含语义结论、四项报告、完整 Inventory / Docker Impact、双段与未验证项 | 本地草案完成；CI/人工 merge review 待发布后执行 |

## AI 自检与后续

按实际未暂存 diff 审阅：12 项中边界、敏感信息、文档同步、分支与 `docs` 类型、scope、双段、模板字段、反扫均符合；业务数据源、CHANGELOG、system prompt / EVAL 检查不适用，commit message 尚为建议 `docs: sync PR template field references`。5a 反扫覆盖四份技能与 GUIDE/政策说明；5b 新 PLAN 已落盘；5c INDEX/AGENTS/CHANGELOG 无同步变更；5d 无 SPEC。Scope drift = None；政策多文件语义修订需 reviewer 重点核对，已有具体 Owner 批准。

Issue 已同步计划记录范围并保持 open。交付为修复 diff、本计划 AC 映射及 PR 正文；Owner 已分别批准本分支七份文件的 commit、普通双推与 PR 创建。提交及两端推送 SHA、PR URL 由实际执行后的会话和 PR 留证；本计划不预先声明执行成功。merge 与最终验收仍待 Owner 人工处理，未授权删除或清理。

实施来源：Codex；canonical 10-enum 命中 NONE，另有 §5 政策受保护编辑批准（上文）；BDD/TDD impact NONE（文档语义修复）；Subagent dispatched NONE。无运行时行为变更。PR 草案按模板逐项装配并核对，未做独立调用技能的 LLM 行为回归，未验证 host/services、远端 CI 或 merge。
