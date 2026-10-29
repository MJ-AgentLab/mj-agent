---
name: mj-agent-flow-plan
description: 适用于 mj-agent 的Stage4完整working-plan正文。输入：Issue、repo-scan事实、SPEC、AC。流程：context→任务拆分→doc-plan→风险→验证→完成标准关联。输出：任务/顺序/风险/验证/AC/文档矩阵完整。Use when：为已核验Issue起草完整实施Plan。Do not use for：只评估文档需求；建议doc-plan，不生成开发Plan正文。授权：按任务范围复用，普通实现自主；安全/业务/权限/breaking/接受标准及门禁实质变化先Owner；技术拒绝不绕过。独立调用完成后结束，委派返回调用者；完整闭环已有授权时按检查点继续，不新增外部授权。
---

# mj-agent Flow — 实施 Plan

执行前读取 [共用执行边界](../../references/execution-boundaries.md) 与 [working/INTENT 创作和引用说明](../../references/working-docs-and-intent.md)。本技能编写完整实施计划；doc-plan 只提供文档缺口矩阵，doc-author 保存单份原意/规范，flow-intake 把原意适配为任务。

## 1. 核实际任务与权威预期

固定 workspace/ref/SHA、真实主 Issue、原意正本、已有 SPEC/ADR/契约、Repo Scan 的事实与未测项。按任务明确路径定位，再用 `rg --files plans` 检查新旧布局；不从分支数字推 Issue，不以不存在本地 Plan 推定任务未授权。没有 Repo Scan 时先核实现依赖与引用事实，结论默认在对话返回，必要持久化才保存对应 working。

目标已确认时复用现决定；把冲突拆成原意/预期/当前实现/证据分别处理。简单任务可使用 Issue 原意区唯一正本；Plan 不代替 INTENT，也不把来源不明的总结升级为已接受需求。

## 2. 选择目录、状态与承担范围

采用 `plans/<topic>/[PLAN]_<topic>.md` 和 `TEMPLATE_PLAN.md`；四种 topic、真实主要关联、稳定主题与受控改名按共享说明执行。多 PR 优先整体集成 PR，无明确主要 PR 则省 P。子 Plan 各有独立目录，共享报告唯一主归属。Intake/报告目录可始终无主 Plan；需要实施计划时才建立它，不为目录形式补造 Plan。

新 Plan 必填 type=plan/summary/owner/created/updated/state=draft/track。有明确采纳依据后在正文记录来源并转 active；阶段是检查点，普通计划安排自主，不加固定人工停点。topic 不推导 task_id；补号保持任务身份、INTENT ID、历史基线。

逐个关联 INTENT/Issue 标明本 Plan 的实际交付范围、依赖和背景；完整接受基线有准确位置，不能只留摘要或 hash。

## 3. 编排任务、文档与风险

按依赖拆成可独立验证的纵切任务，每项注明输入、文件入口、输出、AC、方法及恢复点；原有业务/runtime/秘密边界保持。标明适用 A纯代码/B runtime canonical/C infra 风味和真实影响，行为变化先写负例观察 RED 再实现到 GREEN，bug 先复现并定位根因。纯格式修改不机械增加测试。

调用 doc-plan 按本次实际类型列 Create/Update/None、准确目标、来源、依赖和验证；不固定十行、不漏 INTENT/Report/Intake，也不把矩阵扩成第二份实施计划。必要 SPEC 写行为/接口/口径，Report 写真实证据和限制，Issue 管总体覆盖与进度。

风险逐项说明影响、缓解、回退/恢复和监控信号。未知核心依赖写可恢复入口与停止条件；非核心缺项列延期、原因/影响/恢复条件，继续可验核心，延期不计 PASS。

## 4. Plan 正文必有内容

使用模板组织以下内容，可按任务规模合并标题，但独立执行者必须能找到每项：

1. 目标/使用者、范围、排除及延期；原意来源、完整接受基线和本次承担范围。
2. 执行授权：允许动作、精确对象、环境、权限、副作用、资源、停止/失效条件；结果接受与动作授权分记。
3. 输入文件、入口顺序、依赖与工具身份；实际 workspace/ref/SHA、真实主 Issue/PR 及关联 Intent/SPEC/ADR。
4. 可验证任务与依赖顺序；Documentation Decision、产物与负责人/委派返回点。
5. 风险、恢复与监控；在途副作用、失败、未知、延期与下一步。
6. 逐 AC 验证：期望、方法/命令、版本、环境、时点/批次、结果与完整证据位置；结构 PASS 的覆盖界限。
7. 检查点、候选完成、正式生效、交付与 Owner 接受条件；平台批准/集成/运行/交付/接受分别记录。

## 5. 独立使用七题

写完由未参与计划推导的视角检查：

| 独立执行者要知道什么 | Plan 应给出的答案 |
|---|---|
| 解决什么问题，边界在哪里 | 目标、使用者、范围/排除/延期 |
| 权威预期是什么，冲突如何处理 | 原意/SPEC/契约的准确位置和决定规则 |
| 从哪个文件开始，顺序与依赖是什么 | 文件入口、任务依赖和产物 |
| 用什么工具、身份、输入 | 实际工具、身份/对象、环境和必要输入 |
| 可以做什么，何时停止 | 授权、风险边界、停止/恢复条件 |
| 怎样验证，针对哪个版本环境批次 | 逐 AC 方法、SHA/完整快照、环境/时点与证据 |
| 何时只是候选完成，何时正式生效 | 必要门禁、交付及 Owner 准确版本接受 |

关键缺项保留具体未决项和恢复点，不能让后续实施者猜。语义/来源忠实和实际接受由真实证据核验，正则或模板齐全不能代替。

## 6. 验证与返回

适用命令从根 AGENTS 和真实修改选择：ruff、mypy、`uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit -q`、frontmatter/wikilinks/working 及 native 检查。优先既有锁定环境，外部依赖始终 `SKIP_POLICY_EXTERNAL_DEPENDENCY`，live/容器/生产另按真实授权，不机械 uv sync 或裸 pytest。

核模板与政策一致、链接按文档位置可解析、路由保持 task_id/head/base 及安全拒绝。返回准确 Plan 路径、采纳依据、逐 AC/任务映射、当前检查点、未决/延期/停止条件。已有完整闭环授权就继续实施；独立调用按本技能范围返回。

仅主 Plan completed 需要 AC 满足、成果可用及 Owner 明确接受准确版本；报告 completed 不代表 Plan/整体任务接受。主 Plan 一次接受可以明确同时覆盖整体任务，避免重复确认。完成文件原地保留，废弃 draft 保留原因与恢复条件，INTENT 状态保持独立。

政策与模板：`repo:policies/documentation.md`、`repo:sdd/lifecycle.md`、`repo:sdd/workflows/execution-loop.md`、`repo:docs/_templates/TEMPLATE_PLAN.md`。
