---
type: sdd-workflow
artifact: bugfix-drift
state: draft
version: "0.2"
owner: ranzuozhou
created: 2026-05-20
updated: 2026-10-12
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
4. **独立核验/平台审核** — PR review，特别看 regression test 与 root-cause 对齐.
5. **trace.yml** — 关联 PR + 新 test + evidence.

## 决定与授权

已有接受基线内根因修复/回归自主，包括runtime安全保持；跨capability按影响协调，改变安全/业务/breaking或AC才先Owner决定。

## TBD: Phase M2 内容填充

- bugfix-regression test 强制条件（G24 blocking from M4）
- contract-test-first 在 bugfix 场景下的应用细则（G28）

---

> *Phase M0 skeleton — `state: draft`.*
