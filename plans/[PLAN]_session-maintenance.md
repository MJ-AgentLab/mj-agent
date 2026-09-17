---
type: plan
summary: 迁移 mj-system 会话维护机制，接入 mj-agent 共享入口并验证生成一致性
owner: 项目负责人
created: 2026-09-17
updated: 2026-09-17
state: active
track: engineering-workflow
---

# [PLAN] 会话维护机制

## 1 背景与授权

2026-09-17，Owner 要求参照 mj-system 的对话归档机制先评估，随后回复“执行”，确认本次对话中提出的五文件方案及验证范围。该授权覆盖规则、入口、索引、计划和生成记录同步；不包含 commit、push、PR、merge 或客户端任务改名、归档实测。

只读扫描基线：mj-agent `develop` 为 `20e2f24`，工作区干净；mj-system 规则参考提交为 `3e55613`，源文件为 `.agents/references/session-maintenance.md`。上游路径只作来源记录，本项目运行不依赖跨仓文件。

## 2 目标与范围

建立由根 AGENTS 按需读取、Claude Code 经 `@AGENTS.md` 共同消费的会话维护规则，区分归档摘要、推荐标题、明确重命名和额外客户端动作。正文唯一归属 `sdd/workflows/session-maintenance.md`；这是开发协作流程，不修改运行时 agent、数据库、依赖、技能清单或客户端工具实现。

| 文件 | 动作 |
|---|---|
| `sdd/workflows/session-maintenance.md` | 新增共享规则，适配上游执行约定引用 |
| `AGENTS.md` | 增加会话维护触发入口 |
| `docs/INDEX.md` | 登记 workflow 并更新实质修改日期 |
| `.agents.lock.json` | 仅通过 `agents_sync.py sync` 更新生成输入摘要 |
| 本计划 | 记录范围、验证和后续状态 |

不手改 `.agents/` 或 `.codex/`；同步若产生范围外内容差异，先核实原因，不顺带纳入。`CLAUDE.md` 已导入根 AGENTS，不重复维护规则正文。

## 3 任务拆解与执行顺序

1. 从 develop 创建 `documentation/session-maintenance` 工作树，保存已确认方案。
2. 移植上游六节规则，补充共享入口、来源说明及本项目执行流程/授权边界引用。
3. 同步根入口和文档索引；运行生成器同步已有生成产物及 lock。
4. 执行文档、入口与投影校验，逐项静态审阅意图识别场景，记录实际覆盖范围。

改动属于文档与生成元数据，不进入 A/B/C 运行时实现路径；无程序行为实现或新测试缝，不新增模拟规则正文的单元测试。

## 4 Documentation Decision

| 类型 | 动作 | 路径 | 现有目标 | 原因 | 证据 | 模板要点 | 完成阶段 |
|---|---|---|---|---|---|---|---|
| Plan | Create | 本文件 | 无 | 固定范围与验收 | 评估后的“执行”授权 | working 字段、范围、风险、验证 | 实施前 |
| SPEC | None | — | 无 | 行为由 workflow 承载 | 无应用接口变化 | — | — |
| ADR | None | — | 无 | 沿用共享 kernel 架构 | AGENTS 及 CLAUDE 导入关系 | — | — |
| RUNBOOK | None | — | 无 | 无运维变化 | 五文件范围 | — | — |
| GUIDE | None | — | 无 | 根入口已可发现 | AGENTS 按需读取 | — | — |
| STANDARD | None | — | 无 | 不另建重复规则 | 正文在 sdd/workflows | — | — |
| Local ISSUE | None | — | 无 | 无独立长期问题 | 需求和范围已明确 | — | — |
| ASSESSMENT | None | — | 无 | 评估保留在对话 | 本计划记录实施证据 | — | — |
| CHANGELOG | None | — | CHANGELOG.md | 不改变应用发布行为 | 仅开发协作约定 | — | — |
| INDEX | Update | docs/INDEX.md | kernel 索引 | 新增 workflow 入口 | 新规则路径 | 单行索引与 updated | 验证前 |

## 5 风险与控制

总体风险 Medium。HITL 命中 `mcp-server-trust-posture-change` 的 D-017 生成记录邻接面，仅重新计算已有生成输入摘要，不修改信任策略或生成器；Owner 的“执行”覆盖评估中已明确的同步动作。四项 in-source 专属必停面均不涉及。

| 风险 | 缓解与回退 |
|---|---|
| 把机制讨论、普通摘要或命名建议当成客户端操作 | 保留正反例和动作边界，分别静态审阅 |
| 双工具规则分叉或误报工具成功 | 只维护一份正文；按当前能力调用，确认结果后才报告成功 |
| AGENTS 改动未同步生成摘要 | sync 后检查全表及 enforcement；不手改 lock |
| 静态检查被误报为客户端验证 | 单列实测状态，未授权目标则不调用客户端写操作 |

回退时撤回本任务源文档差异，并由生成器重建 lock；保留用户其他修改。没有数据或服务恢复步骤。

## 6 验证计划

使用已有 Python 环境执行工作树内脚本，不安装依赖、不加载应用环境：

- `git diff --check`，并核对已跟踪与未跟踪文件的完整范围。
- `scripts/check_frontmatter.py`、`scripts/check_wikilinks.py`、`scripts/check_loop_section_refs.py`。
- `scripts/sdd/check_development_agent.py --all --fail-on warning`。
- `scripts/sdd/check_agents_projection.py --all --fail-on warning`。
- `scripts/sdd/agents_sync.py --check --surface all` 和 `--surface enforcement`，核对实际结果码，SKIP 不算通过。
- 补充核对 workflow 元数据及新增相对链接：通用 frontmatter 扫描不覆盖 `sdd/`，根 AGENTS 的新 Markdown 链接也需独立验证。
- AI 静态审阅：归档/推荐/显式改名/规范改名，四种编号组合，多编号、指定日期/时区、完整标题、工具缺失/失败/结果未知，以及否定/引用/机制讨论/文件归档/PR 收尾。

客户端改名或客户端归档实测仅在 Owner 明确指定获授权目标和动作后执行，本次不作为实施完成条件。无业务代码改动，不运行应用、数据库、Docker、LLM 或业务测试。

## 7 验收标准

- [x] 一份共享规则覆盖上游六节语义，并正确引用本项目执行流程与授权边界。
- [x] 根入口和索引可达；CLAUDE 经现有导入消费，不复制正文。
- [x] 五文件范围内完成，生成记录仅由同步脚本维护。
- [x] 文档与投影校验结果有本次证据，新增链接及 workflow 元数据补检通过。
- [x] 静态场景审阅与客户端实测状态分别记录，不以工具存在或静态 PASS 代替执行成功。

## 8 关联与执行记录

关联：[会话维护规则](../sdd/workflows/session-maintenance.md)、[执行闭环](../sdd/workflows/execution-loop.md)、[AI 协作边界](../policies/ai-agent.md)、[根协作契约](../AGENTS.md)。实施记录时本任务无已确认 Issue 或 PR。

### 本地验证

2026-09-17 在 `documentation/session-maintenance` 工作树执行，基线为 `20e2f24c352cf640d9dd33234b128ca897804b99`。使用 develop 工作树已有 `.venv/Scripts/python.exe`（`-B -X utf8`）执行本工作树内脚本；没有安装依赖。规则文件 SHA256：`655656e27755efe5c4418fddf7b5b8ed52a14460a0f97229bebac050563be034`。

| 检查 | 实际结果 |
|---|---|
| `agents_sync.py sync` | PASS，仅写 `.agents.lock.json`，1 项变更 |
| `check_frontmatter.py` | PASS，140 份扫描范围内文档 |
| `check_wikilinks.py`，`MJ_AGENT_A4_STRICT=1` | PASS，0 archive-ref violations、5 个根文件 0 unresolved targets |
| `check_loop_section_refs.py` | PASS，20 个 live sections、0 violations |
| V8 `check_development_agent.py --all --fail-on warning` | PASS，0 errors / 0 warnings |
| V9 `check_agents_projection.py --all --fail-on warning` | PASS，0 errors / 0 warnings |
| `agents_sync.py --check --surface all` | PASS，18 skills，lock consistent |
| `agents_sync.py --check --surface enforcement` | PASS，结果码 `EXECUTED_CLEAN`，不是 SKIP |
| 补充链接与元数据检查 | PASS，新 workflow 字段、8 个正文相对链接、根入口及索引目标有效；新文件无行末空白 |
| 补充生成差异检查 | PASS，JSON 结构比较确认仅两个 entry 的 `policy_refs_sha256` 改变；hooks/rules 正文不变 |
| 原文与范围检查 | PASS，根 AGENTS 除新增段落外与 HEAD 一致；完整修改及未跟踪集合恰为五文件，暂存区为空 |
| `git diff --check` | PASS；Git 的 LF/CRLF 提示为既有文本转换策略，生成输入摘要已按现有实现归一化 |

补充检查通过临时内存脚本执行，未新增测试文件。`check_frontmatter.py` 不覆盖新 workflow，`check_wikilinks.py` 的五个根文件不含 AGENTS，因此显式补检两项覆盖缺口。客户端改名/归档实测为 **未执行**：本次没有获授权的测试目标；静态审查不证明模型实际触发率或客户端操作成功。无应用改动，业务测试、数据库、Docker、LLM 探针均不适用。

### AI 自检

审阅对象为未暂存差异及两个新文件，非 staged diff；后续提交前仍须确认实际暂存范围。Scope drift = None：五文件逐一对应 §2，生成联动符合已确认评估。上游六节正文对照仅有示例对象、本项目执行引用、文字摘要落盘语义和客户端归档边界说明四处适配。

以下结果是对最终文本的静态语义审阅，不是客户端执行记录；日期与编号均为合成场景。

| 场景 | 预期与静态结论 |
|---|---|
| 归档本次对话 | PASS，标题、日期、成果、结论、待办；不自动保存、改名或客户端归档 |
| 推荐标题／给本次对话命名 | PASS，仅一个标题，不附解释或调用客户端 |
| 指定完整标题改名 | PASS，逐字使用；不加日期编号，不按长度截断 |
| 按规范改名 | PASS，使用当前能力调用，确认结果后才能报告成功 |
| 无编号／仅 Issue／仅 PR／双编号 | PASS，分别为 `0917-对象任务`、`0917-I123-对象任务`、`0917-P456-对象任务`、`0917-I123-P456-对象任务` |
| 多编号／关联不明 | PASS，最多保留一个主要 Issue 和 PR，不明则省略，不搜索补齐 |
| 指定日期/时区、跨日 | PASS，用户指定优先，否则会话时区的命名当天，缺失时 Asia/Taipei |
| 缩写与长对象名 | PASS，保留辨识信息；长度建议只约束生成的对象描述，不作硬门槛 |
| 否定、引用、示例、机制评估/实施 | PASS，不触发实际归档或改名，本次“执行”属于机制实施 |
| PR 收尾／文件归档 | PASS，按对象走既有流程，不误作会话动作 |
| 工具缺失／执行失败／结果未知 | PASS，如实区分状态，未知先只读核实，不盲重试或报成功 |
| 明确要求保存／客户端归档 | PASS，仅处理明确授权范围并分别核实结果 |
| 计划未执行／静态检查通过 | PASS，不计为完成成果或业务成功 |
| 上下文不全／继续工作有条件 | PASS，说明覆盖范围，保留必要工作树、授权、待办与恢复条件 |

12 项自检：模块边界、敏感信息、文档同步、提交说明格式、分支类型、范围、验证/自检分段及引用审阅通过；业务数据、应用 CHANGELOG、PR 正文和 system prompt/EVAL 项不适用。`CLAUDE.md` 的现有 `@AGENTS.md` 已覆盖新增入口，无需复制正文。不涉及符号重命名、文件移动、SQL/DDD 重组、runtime canonical 或 biz catalog 漂移；SPEC Delta 不适用。

Codex 负责本次评估与实施；HITL scenario hit = `mcp-server-trust-posture-change` 的生成记录邻接面（本次“执行”已授权）；Subagent dispatched = NONE；BDD/TDD impact = NONE（文档及生成摘要）。自检结论 GO（可交付审阅），风险保持 Medium。建议单次提交，草案为 `docs: 新增会话归档与任务命名规则`，跨治理目录省略 scope；没有执行暂存、提交、推送、PR 或合并。

实施与本地验证已完成，改动保留在独立工作树，尚未进入 develop。计划保持 active，等待 PR 审阅及合并验收。

### 提交与 PR 授权

2026-09-17，Owner 在实施交付后明确要求“提交PR”，补充授权本任务的暂存、提交、Gitee/GitHub 双推和创建目标为 develop 的 PR；不包含合并。上文的未提交状态是实施交付时点记录，后续提交和 PR 结果以 Git 历史与 PR 页面为准。

提交前 fetch 确认 origin/develop 与任务基线相同，无需合并上游差异。五个文件作为同一文档主题提交，保持跨治理目录省略 scope 的 `docs` 格式，并记录 Codex 协作来源。PR 按 documentation 模板填写本地验证、AI 自检、HITL Trigger Inventory 和 Docker Impact；客户端实测仍为未执行。

本轮补充本地验证：`ruff check` 通过；`mypy src/mj_agent` 为 48 个源文件无问题；frontmatter、execution-loop 节号引用及 all/enforcement 生成一致性复查通过（enforcement = `EXECUTED_CLEAN`）。
