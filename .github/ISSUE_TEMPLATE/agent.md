---
name: Agent
about: Agent 行为 / Tool / SKILL / Prompt / Eval 相关
title: "[Agent] <one-line summary>"
labels: ["track:agent"]
assignees: []
---

## TL;DR

<一句话：agent 行为 / tool 调用 / SKILL / prompt 在什么场景下如何？>

## Scope

- Agent graph（`src/mj_agent/agent.py`）
- Tool（`src/mj_agent/tools/`）— 4 工具族：biz_context / sql / analysis / charts / excel
- In-source SKILL（`src/mj_agent/skills/*/SKILL.md`）— 9 skill
- System prompt（`src/mj_agent/prompts/system.md`）
- Middleware（`src/mj_agent/middleware/` — ADR-029）
- Memory checkpointer（`src/mj_agent/memory/`）
- EVAL framework（ADR-024；Phase 2+）

## Capability 影响

- `data-agent.safe-sql`
- `data-agent.biz-catalog`
- `data-agent.llm-provider`
- `data-agent.tool-chain`（Phase 2+）
- `data-agent.memory-checkpointer`（Phase 2+）
- `data-agent.entry-points`（Phase 4+）

## Runtime 风险影响 Pre-Check（必填）

- [ ] SQL 防御修改：是否改变安全不变量或可见数据范围？
- [ ] Runtime SKILL 正文修改：是否改变业务口径、数据范围或外发边界？
- [ ] System prompt 修改：是否改变安全/业务/外发承诺或模型选择？
- [ ] Catalog 修改：是否改变指标口径、可见数据范围或上游规范选择？

按 `policies/ai-agent.md` §4 与 ADR-042 判断实际影响。保持接受基线的维护在任务授权内自主执行，提供适用行为、负例及独立核验；实质变化先准备具体方案，由 Owner 决定。路径标签、技术权限和静态检查不产生授权，实际技术拒绝不得绕过。

## Acceptance Criteria

- [ ] AC-1 <可验证陈述>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] Agent tool/schema 是否改变 breaking 承诺、数据/权限或接受标准？
- [ ] Prompt 行为边界变更（不仅 version bump）？
- [ ] middleware 是否改变安全/权限或必要错误暴露承诺？
- [ ] checkpointer 迁移是否超出具名可逆 dev 授权或具有不可逆风险？

## EVAL References

- 关联 EVAL：`tests/eval/<subtype>/<name>.py`（per ADR-024 4 子类）
