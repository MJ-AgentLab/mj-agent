---
name: mj-agent-doc-validate
description: 适用于 mj-agent 的既有文档格式/元数据/链接审核。输入：文件集合、track、当前规范。流程：frontmatter→wikilinks→半自动OB→track分组→根例外→报告。输出：每项PASS/FAIL/WARN/SKIP及来源；静态审阅明确标记。Use when：检查某GUIDE frontmatter和wikilinks。Do not use for：跑完整lint/types/pytest矩阵；建议flow-verify，不用文档校验替代全验证。授权：按任务范围复用，普通实现自主；安全/业务/权限/breaking/接受标准及门禁实质变化先Owner；技术拒绝不绕过。独立调用完成后结束，委派返回调用者；完整闭环已有授权时按检查点继续，不新增外部授权。
---

# mj-agent Doc Validator

执行前读取 [共用执行边界](../../references/execution-boundaries.md)。输入为既有文件集合/任务目录与当前政策，输出每项 PASS/FAIL/WARN/SKIP、命令/版本/环境和覆盖限制。只做审核与修复指引；完整 lint/type/offline test 矩阵交 flow-verify，正文创作交 doc-author/flow-plan。

## 1. 固定范围与适用 schema

核实际 workspace/ref/SHA、被检文件、引用它们的活动入口和历史基线，读取 `policies/documentation.md`。按真实归属区分 canonical、working、kernel、capability package、原生开发技能和 runtime adapter；不能用一种 schema 代替全部。

working/INTENT/改名时先读 [创作与引用说明](../../references/working-docs-and-intent.md)：核四式 topic、真实主要关联与稳定主题、主 Plan 和目录一致/至多一个主 Plan、无 Plan 独立目录与共享报告归属。编号真实性/主要性、原意忠实和接受均须实际证据，checker 仅能验证它所覆盖的结构。

## 2. 运行实际入口

从当前仓根显式运行，优先既有锁定环境，不机械 uv sync；每条保存命令、退出码和新输出：

```text
python scripts/check_frontmatter.py
python scripts/check_wikilinks.py
python scripts/check_working_docs.py
```

这些 CLI 无必需参数；全量范围/兼容行为由真实脚本决定。check_frontmatter 校验通用元数据及 working/INTENT 专属字段、路径/ID/状态/日期和 ID 集合唯一性；check_wikilinks 校验其实际扫描面，按文档位置解析显式相对目标；check_working_docs 对新嵌套 working 执行目录/归属和真实深层 Markdown 相对链接校验。旧根布局兼容读取，不能声称深链接已全量重新验证。

`.agents/skills/` 变更另运行 `python scripts/sdd/check_native_skills.py`，资源引用用其 `--surface resources`；涉及原生配置再按真实范围运行 `python scripts/sdd/check_codex_native.py`。STATIC_PASS 不证明宿主加载、项目使能或服务可用。infra 冻结摘要只在实际对应技能改变时成组维护，不为 flow/doc 修改刷新冻结内容。

## 3. 分类型核结构和状态

| 对象 | 必须核验 |
|---|---|
| 通用 canonical | 政策通用字段和类型专属条件、当前状态/日期/track、准确目录/命名、版本与引用 |
| working | type=plan/intake/report/assessment；七字段 type/summary/owner/created/updated/state/track，domain/version 不强制 |
| 新主 Plan | 新建 draft；active 有明确采纳依据，completed 有逐 AC 满足、成果可用和 Owner 准确版本接受 |
| 其他 working | 按已确定自身交付条件完成；若条件包含 Owner 接受仍须满足；报告 completed 不代表整体任务接受 |
| INTENT | docs/intent 正式路径；九字段 type/domain/summary/owner/created/updated/state/intent-id/track，type=intent，version 可选；有效日期，ID与文件名一致，状态仅 draft/active/deprecated，含deprecated全量查重 |
| 已退役/历史对象 | INTENT 原路径/ID/旧决定/原因/后继保留；working archived 仅历史兼容，废弃 draft 保持 draft，完成原地保留；canonical 归档按原政策 |

INTENT ID 分配还须人工核保留/撤销历史及共享变更；集合读取失败标 UNKNOWN，不当空集合。跨年/修订/重新接受/拆任务保持 ID，删除撤销不释放；冲突/999耗尽留 Owner 决定。Plan/Issue完成不传播INTENT状态。

## 4. 人工内容与接受核验

INTENT 五正文（问题现状、期望结果、成功判断、范围约束、未决项）及前置可读区完整：提出者/代表、来源准确位置、维护责任、原意核对、内容接受、当前位置与完整适用基线、真实主Issue、AI整理说明。来源/维护责任不明应为真实类型 working 草稿；简单任务 Issue 原意区可作唯一正本。

Plan 对目标范围、完整接受基线/承担范围、动作授权、文件入口顺序/依赖、工具身份/输入、停止/恢复、逐AC版本环境批次证据、候选完成/正式生效均有答案。缺关键内容具体列未决与恢复点，结构齐全不算语义可用。

原意核对、内容接受、执行授权、交付接受分记。接受绑定固定提交文件或完整可恢复快照准确位置；摘要/日期/版本/hash 单独不足。实质变动旧接受只覆盖旧内容，保旧决定及原因/影响；纯路径调整不自动重置业务接受。活动链接按新路径修，历史证据保持可恢复，task_id/INTENT ID不由目录重算。

## 5. A1–A14 与 OB 报告

| 项 | 检查边界 |
|---|---|
| A1–A3 | 路径命名、适用schema、日期与两套状态；机器结果与人工真实性判断分列 |
| A4 | 实际扫描面的链接可解析；迁移区分活动引用与固定提交/快照/旧决定 |
| A5 | 新canonical更新导航；working不强制局部INDEX，不复制实时进度 |
| A6 | 按policy allowlist核高频规则/运行/目录/runtime语义的入口同步与主题落位 |
| A7–A11 | 仅实际agent adapter类型：实现路径、eval_references/dataset/schema等当前契约与过渡规则；不能对无关working硬套 |
| A12 | 原生技能name/description schema、正反向触发及资源引用；调用实际native checker |
| A13–A14 | 原生hooks/rules与MCP实际保护/信任/凭据模式，依共享边界；不扩权限、不绕技术拒绝 |

项目根 README/CONTRIBUTING/CHANGELOG/GLOSSARY/AGENTS 无通用 frontmatter，A1–A3 对对应schema标 SKIP；仍核适用链接/导航/入口。kernel/capability/adapter按各自规则，不能泛化豁免。

OB1–OB5 为长度、时态、内容边界、summary质量和内部一致性，按当前政策阈值区分 WARN/FAIL；不能把建议阈值变成新必要门禁。Report 给真实结论/证据/限制，SPEC给行为/接口/口径，Issue给覆盖进度，类型边界逐项核。

## 返回

每项给 PASS/FAIL/WARN/SKIP/UNKNOWN、文件位置、命令或人工来源、当前版本环境/时点和限制。只静态审阅就写 STATIC_REVIEW，未运行不能写 PASS。机器 PASS 不证明来源忠实、实际授权、真实运行或 Owner接受；把问题交回对应作者在原授权内修，实质未决保持待答，复核受影响项。

依据：`repo:policies/documentation.md`、`repo:sdd/lifecycle.md`、`repo:policies/archive.md`、`repo:scripts/check_frontmatter.py`、`repo:scripts/check_wikilinks.py`、`repo:scripts/sdd/check_native_skills.py`。
