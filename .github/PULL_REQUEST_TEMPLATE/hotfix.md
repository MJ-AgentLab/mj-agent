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
