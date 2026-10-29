---
name: mj-agent-doc-author
description: 适用于 mj-agent 的已确定类型与scope的一份文档。输入：类型、主题、路径、真实代码、模板。流程：前置ADR/SPEC判定→track→目录→模板→同名冲突→正文→B停点→校验→索引。输出：类型/track/命名/引用/校验逐项有结论。Use when：为已定scope写GUIDE，含现有函数用法。Do not use for：只问哪些文档缺失，不写正文；建议doc-plan，仅评估缺口。授权：按任务范围复用，普通实现自主；安全/业务/权限/breaking/接受标准及门禁实质变化先Owner；技术拒绝不绕过。独立调用完成后结束，委派返回调用者；完整闭环已有授权时按检查点继续，不新增外部授权。
---

# mj-agent Doc Author

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。本技能起草已明确类型与 scope 的一份文档；缺口评估交 doc-plan，完整实施 Plan 交 flow-plan。保存原意时先用本技能，再由 flow-intake 适配任务、flow-plan 编排实施，不新增 flow-intent。

## 1. 判定来源权威与文档责任

读取真实来源、现有文档、代码/配置与对应决定。原始提出者/INTENT/Issue 原意区说明目标与成功判断；SPEC/契约说明应有行为、接口和业务口径；代码/运行证据说明现状；Plan 说明实施；Report/Assessment 说明真实结论和限制。代码是实现事实依据，不能覆盖原意或把错误实现变成接受标准。逐项列冲突和未知，再按实际影响自主修复或提交 Owner 实质决定。

核目标/范围/基线/授权及文件归属。只问影响产物的真歧义；真实业务原意给中性选项，工程/机制/授权取舍给推荐。预选、沉默、超时都不是决定，真实未决项保持待答。

## 2. 选择类型、目录、模板与 schema

先读 `policies/documentation.md` 的当前类型/track/正文深度，再核已有正本，优先更新。跨边界决策先检查是否需要 ADR；新增或改变行为/接口/业务口径先检查现有 SPEC/契约覆盖。

| 分支 | 目录/模板与操作 |
|---|---|
| INTENT | 读下节及 [创作与引用说明](../../references/working-docs-and-intent.md)，用 TEMPLATE_INTENT.md |
| working Intake/Report/Assessment | `plans/<topic>/`，用 TEMPLATE_INTAKE/REPORT/ASSESSMENT.md 的 working 分支；目录可永无 Plan，报告按用途命名 |
| 完整 Plan | 交 flow-plan，用 TEMPLATE_PLAN.md |
| SPEC/ADR/GUIDE/RUNBOOK 等 canonical | 按政策归属，在 `docs/_templates/` 选真实类型模板；ADR 在 `decisions/`，分配前同时查活动/归档编号 |
| 长期 Assessment | 走 canonical 完整 schema；与任务 working 轻量分支区分 |
| 原生开发技能 | `.agents/skills/` 与 TEMPLATE_WORKFLOW_SKILL.md，保持 name/description 原生 schema |
| runtime SKILL/PROMPT/CONTRACT | 读对应 `sdd/adapters/` 与冻结契约，按实际语义走 runtime 领域技能及 EVAL/版本规则 |

按路径与主题选 code/agent/engineering-workflow/shared。working 七字段必须含 track，domain/version 可选。项目根入口、kernel、capability package 和 adapter 各自 schema 依政策执行，不强套通用字段。新文档从 draft 起步；是否生效/采纳及接受按对应类型真实决定判断。

检查准确目标路径与同名冲突。active canonical 默认不加版本后缀，版本号在 frontmatter；只有明确多 active 主版本并存等政策例外才加。模板可合并/改标题，但必需元数据、内容和关联信息保持。

## 3. 保存 INTENT 或 Issue 原意正本

简单单任务可用真实 Issue 原意区为唯一正本，避免重复建文件/ID。跨任务需要稳定原意时正式正本为 `docs/intent/[INTENT]_INT-YYYY-NNN_<English_Topic>.md`，独立于任何 Plan；来源或维护责任不明，先保存在真实类型 working 草稿并写恢复条件。

分配前读取全量现存/保留 ID 与共享变更，包含 draft/active/deprecated 及撤销决定；创建和合并前均查重。首次年度配 001–999；跨年、修改标题、修订、重新接受或拆任务保留 ID；删除/撤销不释放。读取失败标 UNKNOWN，冲突/耗尽交 Owner，不自动改号或扩位。

填写九项 `type/domain/summary/owner/created/updated/state/intent-id/track`（type=intent，version 可选）。五正文逐项明确：问题现状、期望结果、成功判断、范围约束、未决项。前置可读区保存提出者/代表、原始来源准确位置、维护责任、原意核对、内容接受、当前位置与完整适用基线、真实主 Issue、AI 整理说明；owner 不自动等于提出者或接受人。

分别记录原意核对、内容接受、执行授权与交付接受的实际人/动作/范围/位置。接受必须能恢复固定提交文件或完整快照的准确内容；摘要/日期/版本/hash 单独不足。实质变动保留旧决定、来源/原因/影响，旧接受仅覆盖旧基线；纯改路径不自动重置业务接受。

INTENT 只用 draft/active/deprecated，机器 PASS/active/AI 自检不替代真实决定。退役保留原路径 ID、旧决定、原因与后继；Plan/Issue 完成不改变它。一个 INTENT 支持多个 Plan，一个 Plan 承担多个 INTENT 时区分实际交付/依赖/背景。Issue 汇总进度依赖，Intent/INDEX 只维护稳定入口。

## 4. 起草正文与修复引用

按真实类型填写足够可用的内容：操作文档给输入、顺序、可观察结果与恢复点；SPEC 给行为/接口/负例；ADR 给决策与备选；Report 给版本/环境/方法/结果/限制，不能用未来计划冒充实测。未知明确标记，不虚填链接、字段或 Owner 接受。

working 保存与补号改名先按共享说明核目录、源目标、Git 状态、引用/路由，后验证完整性；task_id、历史基线和 INTENT ID 保持。共享报告唯一主归属，子 Plan 独立目录，完成原地保留，working 不走物理归档/GC。

runtime prompt/skill/catalog/SQL 面先读真实装配/loader/契约，分类实际安全/业务/权限/breaking/AC/门禁影响；既有基线内维护自主，实质边界变化才等待 Owner 决定，技术拒绝保持原错与 `BLOCKED_EXECUTION_ROUTE`。

## 5. 校验并返回

调用 doc-validate：frontmatter、wikilinks、working 的实际深相对链接及人工语义检查分开报告。原生技能另跑 native 检查；它们只证明覆盖到的静态结构，不证明宿主加载、服务可用、原意忠实或 Owner 接受。

新 canonical 更新 docs/INDEX 与实际高频入口；working 不强制局部 INDEX，也不把所有对话输出落盘。更新活动引用，冻结提交/快照/旧决定保持可恢复；文档版本、日期按类型政策更新。返回类型/track、准确路径、真实来源、决定与基线、校验命令/结果、未知/延期/恢复条件及下一步。提交/推送/PR 在各 Git 技能和已有任务授权范围处理。

政策依据：`repo:policies/documentation.md`、`repo:policies/archive.md`、`repo:sdd/lifecycle.md`、`repo:sdd/adapters/runtime-skill.md`、`repo:sdd/adapters/prompt.md`、`repo:sdd/adapters/contract.md`。
