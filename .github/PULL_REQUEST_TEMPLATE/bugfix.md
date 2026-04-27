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

## 文档自检（A1-A10，仅在触及文档时勾选）
- [ ] 如修复涉及 `[SKILL]` / `[PROMPT]` 的行为变更，对应 SKILL.md / prompt.md 已同步更新（`updated` 字段、Change log）
- [ ] 如修复源于某个 `[ADR]` 的假设变化，对应 ADR 已追加变更说明或新增 superseding ADR
- [ ] `src/mj_agent/skills/**/SKILL.md` 与 `src/mj_agent/prompts/*.md` 的 frontmatter 仍然合法
