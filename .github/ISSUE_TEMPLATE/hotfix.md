---
name: Hotfix
about: 生产紧急修复；走 sdd/workflows/hotfix.md (base = main)
title: "[Hotfix] <one-line summary>"
labels: ["bug"]
assignees: []
---

## ⚠ Hotfix 启动检查清单

- [ ] 确认此变更**真的需要走 hotfix 单线**（绕过 develop 标准流程）
- [ ] base = `main`（不是 `develop`）
- [ ] 走 `sdd/workflows/hotfix.md` 6 步
- [ ] PR target = `main`
- [ ] commit type 必含 `fix(`；不夹带 refactor / feature
- [ ] merge 后 main 打 patch 版本 tag
- [ ] merge 后 sync develop ← main（用 `mj-agent-git-sync` skill）

## TL;DR

<一句话：什么生产事故 / 高危漏洞？>

## Impact

- **Affected production**: TEST / PROD / 上游业务系统集成
- **User-facing symptom**: <symptom>
- **Severity**: critical / high

## Root Cause Hypothesis

<初步根因；可后续在 postmortem 中修订>

## Minimal Fix Scope

<最小变更面 — 仅这些文件需改>

## Acceptance Criteria

- [ ] AC-1 <可验证陈述；hotfix 类首条通常是"生产症状消失">
- [ ] AC-2 <回归测试已覆盖，防止再犯>

> 每条 AC 须落到一种验证手段（pytest / ruff / mypy / `mj-agent check` / Studio 探针 /
> `scripts/**` 校验脚本 / 文档 grep）。写不出验证手段的 AC 应回 Stage 0 重新拆解，而不是照写。

## HITL Trigger Check

- [ ] 触及 prod compose？（必 ≥ 2 reviewer）
- [ ] 触及 4 项专属必停？（必 ≥ 2 reviewer + 1 domain expert）
- [ ] 数据-LLM 边界相关？（不应走 hotfix 单线 — 走 cross-capability workflow）

## Spec Debt Plan

merge 后 N 工作日内（默认 5；critical hotfix 3）补齐：

- [ ] capability `requirements.md` / `contracts/` 演进（走 `sdd/workflows/evolve-capability.md`）
- [ ] `evidence/postmortems/<YYYY-MM-DD>_<incident-slug>.md` 写入
- [ ] trace.yml 关联 hotfix PR + postmortem
