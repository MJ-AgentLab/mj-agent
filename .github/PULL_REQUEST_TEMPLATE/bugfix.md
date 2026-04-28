---
name: Bugfix PR
about: 常规 Bug 修复 (bugfix/*) 的 Pull Request
---

## Bug 描述
<!-- 一句话描述 Bug 现象 -->

## 根因分析
<!-- 简述问题的根本原因 -->

## 修复方案
<!-- 描述修复方法和关键改动 -->

## 影响范围
<!-- 列出受影响的模块 / 文件 -->

## 自检结果
- [ ] Bug 已在本地复现并验证修复
- [ ] 无引入新的回归问题
- [ ] 无残留调试代码
- [ ] Commit message 符合规范（仅含 `fix` / `test` / `docs` 类型）
- [ ] CHANGELOG.md `[Unreleased]` 区块已更新（如 CHANGELOG.md 存在）

## 文档自检（按 track 选填，仅在触及文档时勾选；详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|Code_Side §7.1]]</summary>

- [ ] 如修复源于某个 `[ADR]` 的假设变化，对应 ADR 已追加变更说明或新增 superseding ADR
- [ ] OB1-OB5：非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A10) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side §7.1]]</summary>

- [ ] 如修复涉及 `[SKILL]` / `[PROMPT]` 的行为变更，对应 SKILL.md / prompt.md 已同步更新（`updated` 字段、Change log）
- [ ] `src/mj_agent/skills/**/SKILL.md` 与 `src/mj_agent/prompts/*.md` 的 frontmatter 仍然合法

</details>
