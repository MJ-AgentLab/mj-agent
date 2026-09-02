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
- [ ] Commit message 符合 `<type>(<scope>): <summary>` 规范（允许类型：`feat` / `perf` / `refactor` / `test` / `docs`）
- [ ] 如引入新依赖，已通过 `uv add` 写入 `pyproject.toml` 并提交 `uv.lock`
- [ ] CHANGELOG.md `[Unreleased]` 区块已更新（如 CHANGELOG.md 存在）

## 文档自检（按 track 选填，详见 [[../../policies/documentation|documentation policy]] §5）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../policies/documentation|documentation policy]] §5.1</summary>

- [ ] 新功能涉及的 `[ADR]` / `[SPEC]` 已同 PR 落地或更新
- [ ] frontmatter 完整且 `state`、`domain`、`version` 合法（A2-A3）
- [ ] 触发 allowlist 时 `CLAUDE.md` 已同步检查（A6）
- [ ] 相关 `docs/**/INDEX.md` 已同步或可重建（A5）
- [ ] OB1-OB5：非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A11) — cite [[../../policies/documentation|documentation policy]] §5.3 + [[../../sdd/adapters/runtime-skill|runtime-skill adapter]] / [[../../sdd/adapters/prompt|prompt adapter]] / [[../../sdd/adapters/contract|contract adapter]]</summary>

- [ ] 新功能涉及的 `[SKILL]` / `[PROMPT]` / `[CONTRACT]` 已同 PR 落地或更新
- [ ] 新增/修改 `[SKILL]` 时对应 `src/mj_agent/skills/<name>/` 目录存在（A7）
- [ ] 新增/修改 `[PROMPT]` state=active 时 `eval_references` 非空（A8，Phase 2 起强制）
- [ ] 新增/修改 `[CONTRACT]` state=active 时 `schema_ref` 存在（A10）
- [ ] **A11** SKILL `state: active` 时 `eval_references` 非空（Phase D 起强制；transitional waiver 期内允许注释 TODO）

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite A12 → [[../../sdd/adapters/claude-code-skill|claude-code-skill adapter]] §Standards / §CI Gate; A13 → [[../../policies/ci-gates|ci-gates policy]] §5.1; A14 → [[../../policies/ai-agent|ai-agent policy]] §4</summary>

- [ ] **A12** `.claude/skills/<name>/SKILL.md` 用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正向触发 + `Do not use for:` 反向块；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` allowlist diff 评审：无裸 `Bash`、secret patterns 在 `permissions.deny`、`enabledPlugins` 变更附 PR body 理由
- [ ] **A14** `.mcp.json` server 增删声明 trust posture（first-party / third-party / community）+ credential mode（none / OAuth / API key / wrapped script）
- [ ] **feature 风险面**：新增 `.claude/skills/` 时 description ≥ 200 chars + 正反 trigger 双段是命中率刚需（A12）；新功能引入 MCP server / 调整 settings.json `enabledPlugins` 必走 A13/A14 评审

</details>
