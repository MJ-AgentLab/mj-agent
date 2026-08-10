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

## 4 项专属必停 Pre-Check（必填）

- [ ] `src/mj_agent/tools/sql/{guardrail,precheck}.py` 修改？→ **sql-guardrail-relax** HITL
- [ ] `src/mj_agent/skills/*/SKILL.md` body 修改？→ **runtime-skill-content-change** HITL
- [ ] `src/mj_agent/prompts/system.md` version + body 修改？→ **prompt-version-or-body-change** HITL
- [ ] `src/mj_agent/biz_catalog/qcm_catalog.yaml` 修改？→ **biz-catalog-sync** HITL

→ 任一勾选必须走 `mj-agent-runtime-*` skill 提议 diff，停在 `OWNER_APPROVAL_REQUIRED`；拍板后由 skill 经 `ask` 门落盘，**不未经拍板直接 Edit**.

## Acceptance Criteria

- [ ] AC-1 <可验证陈述>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] Agent tool 列表 / schema 变更？（per `policies/ai-agent.md` §HITL Required Scenarios #7）
- [ ] Prompt 行为边界变更（不仅 version bump）？
- [ ] middleware 链变更（影响 HITL config / error surfacing）？
- [ ] checkpointer schema 变更？（DB migration HITL）

## EVAL References

- 关联 EVAL：`tests/eval/<subtype>/<name>.py`（per ADR-024 4 子类）
