---
name: Bug Report
about: 发现 bug；走 sdd/workflows/bugfix-drift.md
title: "[Bugfix] <one-line summary>"
labels: ["bug"]
assignees: []
---

## TL;DR

<一句话：什么场景下出现什么错误？>

## Capability 影响范围

- Capability: `<domain>.<slug>`（如未识别 capability，写 "unscoped"）
- Related REQ: REQ-NNN（如有）
- Related contract: `contracts/<slug>.contract.yml`（如有）

## Repro Steps

1. ...
2. ...
3. ...

## Expected vs Actual

- **Expected**：<期望行为>
- **Actual**：<实际行为>

## Environment

- mj-agent commit SHA: `<sha>`
- Profile (DEV / TEST / PROD): ...
- LLM provider: ark / local-openai-compat
- Python version: 3.13.x
- 上游 mj-system commit SHA: `<sha>` (如相关)

## Logs / Evidence

```
<paste relevant logs / stack traces>
```

## Workflow Routing

- 单 capability bug → `sdd/workflows/bugfix-drift.md`
- 跨 capability bug → `sdd/workflows/cross-capability-change.md`
- 生产紧急 → `sdd/workflows/hotfix.md`

## Acceptance Criteria

- [ ] AC-1 <可验证陈述；bug 类首条通常是"复现步骤不再复现">
- [ ] AC-2 <回归测试已覆盖该路径>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check（提交前自检）

- [ ] 修复触及 4 项专属必停？（详 `policies/data-boundary.md` §3）
- [ ] 修复触及 cross-capability contract？
- [ ] 修复触及 prod compose / DB migration / secrets？

如有任一勾选 → 必须 HITL.
