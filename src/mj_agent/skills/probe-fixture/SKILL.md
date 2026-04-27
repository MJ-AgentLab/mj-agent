---
type: skill
domain: SKILL
summary: 治理框架 v1.1 端到端验收用 dummy skill：仅用于走 PR 模板 A1-A10 自检，不在 agent 运行期被加载
owner: 项目负责人
created: 2026-04-27
updated: 2026-04-27
state: draft
version: v0.1
activation:
  when_to_use: 永远不应在生产路径触发。本 skill 只为 [PLAN]_E V11 的治理框架自检存在
  when_not_to_use: 任何业务查询、任何用户交互、任何被 agent.py 显式加载的场景
tool_dependencies: []
related_prompts: []
---

# Skill: probe-fixture

> **本 skill 是治理框架的 fixture，不是运行期组件。**
> 命名后缀 `-fixture` 表明其用途；`agent.py:_build_system_prompt()` 当前按名字硬编码
> 加载 `query-writing`，本目录仅在文件系统层面存在，用于验证 v1.1 文档治理框架的
> A1-A10 PR 校验项是否在新增 SKILL 时形成端到端闭环。
>
> 目录命名遵守 v1.1 §"SKILL 目录名全小写带连字符"（line 272）。

## Purpose

完成 [PLAN]_E §V11 的"dummy skill 走 PR 模板 A1-A10 自检全绿"——
本 skill 的存在本身就是一次"先治后码"的演练：在没有任何业务诉求的情况下，
把 v1.1 治理框架（[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1）
的 PR 检查清单跑一遍，暴露任何文档级缺口。

## When to use

**从不主动激活。** 本 skill 不会被 `_build_system_prompt()` 加载，
也不应被未来任何动态 skill selector（ADR-003）选中。它只在两种场景被触达：

1. 单元测试 / loader 调试时显式 `load_skill("_probe")` 验证 frontmatter 解析；
2. 作为治理框架自检的"已知良好样例"。

## Planning workflow

不适用——本 skill 没有 agent 工作流。它的"workflow"是文档侧的：

1. 复制 `docs/_templates/TEMPLATE_SKILL.md` 到本路径；
2. 填齐 frontmatter 八字段 + activation 双子段；
3. 提交 PR 时按 `documentation.md` 模板逐项核对 A1-A10；
4. 把核对结果作为 PR 评论贴出（见本 PR #4 评论）。

## Related

- Prompts: 无（`related_prompts: []`）
- Tools: 无（`tool_dependencies: []`）
- Evals: Phase 2 起若 `state: active`，则需关联 `[EVAL]`；当前 `state: draft`，A11 不触发
- 上游: [PLAN]_E §V11、[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1 §7.1
