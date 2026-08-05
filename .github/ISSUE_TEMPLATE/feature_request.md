---
name: Feature Request
about: 新功能 / 新 capability / 演进；走 sdd/workflows/new-capability.md 或 evolve-capability.md
title: "[Feature] <one-line summary>"
labels: ["enhancement"]
assignees: []
---

## TL;DR

<一句话：要做什么 + 业务价值>

## Capability Scope

- **新 capability**：`<domain>.<slug>`（提议名）→ `sdd/workflows/new-capability.md`
- **演进现有 capability**：`<domain>.<slug>`（已存在）→ `sdd/workflows/evolve-capability.md`
- **跨 capability**：列出涉及的 capability → `sdd/workflows/cross-capability-change.md`

## Business Rationale

<为什么要做？业务驱动 / 合规驱动 / 性能驱动 / 用户体验？>

## High-Level REQ Sketch

- REQ-001: <statement> (priority: critical / high / medium / low)
- REQ-002: <statement>
- ...

## Adapter Coverage 预估

- python / langchain-agent / prompt / runtime-skill / claude-skill / docker-container /
  tdd-bdd（多选；详 `sdd/adapters/`）

## Acceptance Criteria

- [ ] AC-1 <可验证陈述；逐条对位上面的 REQ>
- [ ] AC-2 <可验证陈述>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check（提议前自检）

- [ ] 触及 4 项专属必停？
- [ ] 触及 cross-capability contract / qcm_catalog / system.md？
- [ ] 触及 prod compose / DB migration / secrets？
- [ ] 引入新 LangChain tool / Agent middleware？

## Related ADR

<引用支撑本 feature 的 ADR；如需新 ADR，标注 "ADR needed" 并 link 草案>
