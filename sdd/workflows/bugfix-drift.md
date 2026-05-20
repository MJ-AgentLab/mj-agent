---
type: sdd-workflow
artifact: bugfix-drift
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Workflow: Bug Fix + Spec Drift

> Phase M0 skeleton — bug 修复 + spec 漂移修正. 替代 HITL_Prompt v1.x bugfix flavor.

## Purpose

Bug 修复时检测 contract / spec / 实现间漂移；修代码（实现），保 spec 为 source of truth.

## Trigger

- Active capability 内出现 bug
- 代码 vs `contracts/` 不一致（drift detected by `check_python_contracts.py`）
- bugfix PR open

## High-Level Steps

1. **Repro** — bugfix 必有 regression test（先写 failing test）.
2. **Drift detect** — 判断本 bug 是否因 contract / spec 已说明但实现遗漏，还是实现已合理但
   contract 过时.
   - 实现遗漏 → 修代码使其匹配 contract
   - contract 过时 → 触发 `evolve-capability.md`（spec 优先）
3. **Fix** — `tasks.md` 加 task；tdd.test_list red → green → refactor evidence.
4. **HITL Gate-2** — PR review，特别看 regression test 与 root-cause 对齐.
5. **trace.yml** — 关联 PR + 新 test + evidence.

## HITL Triggers

- bugfix 触及 4 项专属必停 → 永久 HITL（per `sdd/gates.md` §4）
- bugfix 跨 capability → 触发 `cross-capability-change.md`
- 紧急修复 → 走 `hotfix.md`（base = main）

## TBD: Phase M2 内容填充

- bugfix-regression test 强制条件（G24 blocking from M4）
- contract-test-first 在 bugfix 场景下的应用细则（G28）

---

> *Phase M0 skeleton — `state: draft`.*
