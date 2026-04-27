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

## 文档自检（A1-A10，详见 `docs/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md` §7.1）
- [ ] 新功能涉及的 `[SKILL]` / `[PROMPT]` / `[CONTRACT]` / `[ADR]` / `[SPEC]` 已同 PR 落地或更新
- [ ] frontmatter 完整且 `state`、`domain`、`version` 合法
- [ ] 新增/修改 `[SKILL]` 时对应 `src/mj_agent/skills/<name>/` 目录存在（A7）
- [ ] 新增/修改 `[PROMPT]` state=active 时 `eval_references` 非空（A8，Phase 2 起强制）
- [ ] 新增/修改 `[CONTRACT]` state=active 时 `schema_ref` 存在（A10）
- [ ] 触发 allowlist 时 `CLAUDE.md` 已同步检查（A6）
- [ ] 相关 `docs/**/INDEX.md` 已同步或可重建（A5）
