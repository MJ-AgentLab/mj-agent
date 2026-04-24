---
name: Feature PR
about: 新功能、重构等功能开发 (feature/*) 的 Pull Request
---

## 变更摘要
<!-- 简述本次变更的内容和目的 -->

## 影响范围
<!-- 列出受影响的模块 / 文件 / 外部接口 -->

## 审核要点
<!-- 提示审核者重点关注的内容 -->

## 自检结果
- [ ] 本地自测通过（`uv sync` 成功；目标脚本可运行）
- [ ] 无硬编码（IP、密码、令牌、绝对路径）
- [ ] 无残留调试代码（print / TODO hack）
- [ ] Commit message 符合 `<type>(<scope>): <summary>` 规范（允许类型：`feat` / `refactor` / `test` / `docs`）
- [ ] 如引入新依赖，已通过 `uv add` 写入 `pyproject.toml` 并提交 `uv.lock`
- [ ] CHANGELOG.md `[Unreleased]` 区块已更新（如 CHANGELOG.md 存在）
