---
name: Hotfix PR
about: 生产环境紧急修复 (hotfix/*) 的 Pull Request，目标分支为 main
---

> [!warning] Hotfix PR 目标分支为 `main`，合并后需同步到 `develop`

## 事故描述
<!-- 一句话描述生产环境的问题现象 -->

## 影响范围
<!-- 受影响的用户 / 功能 / 服务 -->

## 根因分析
<!-- 简述问题的根本原因 -->

## 修复方案
<!-- 描述修复方法和关键改动 -->

## 回滚预案
<!-- 如修复引入新问题，如何快速回滚 -->

## 自检结果
- [ ] Bug 已复现并验证修复
- [ ] 无引入新的回归问题
- [ ] 仅包含 `fix` 类型 commit
- [ ] 合并后已计划同步到 develop（`git checkout develop && git merge main`）

## 文档自检（hotfix 紧急通道，最小化要求；按 track 选填，详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|Code_Side §7.1]]</summary>

- [ ] 事故根因值得沉淀时，Release 后补 `[POSTMORTEM]`（本次 PR 不强制）
- [ ] 若 hotfix 触发 allowlist（运行入口/关键依赖），`CLAUDE.md` 已同步检查（A6）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A10) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side §7.1]]</summary>

- [ ] 若触及 `[SKILL]` / `[PROMPT]` / `[CONTRACT]` 的行为，frontmatter 的 `updated` 字段已同步修改

</details>
