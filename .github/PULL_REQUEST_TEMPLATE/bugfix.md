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

## 文档自检（按 track 选填，仅在触及文档时勾选；详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side §7.1]]</summary>

- [ ] 如修复源于某个 `[ADR]` 的假设变化，对应 ADR 已追加变更说明或新增 superseding ADR
- [ ] OB1-OB5：非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A10) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side §7.1]]</summary>

- [ ] 如修复涉及 `[SKILL]` / `[PROMPT]` 的行为变更，对应 SKILL.md / prompt.md 已同步更新（`updated` 字段、Change log）
- [ ] `src/mj_agent/skills/**/SKILL.md` 与 `src/mj_agent/prompts/*.md` 的 frontmatter 仍然合法

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1 §7.7]]</summary>

- [ ] **A12** `.claude/skills/<name>/SKILL.md` 用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正向触发 + `Do not use for:` 反向块；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` allowlist diff 评审：无裸 `Bash`、secret patterns 在 `permissions.deny`、`enabledPlugins` 变更附 PR body 理由
- [ ] **A14** `.mcp.json` server 增删声明 trust posture（first-party / third-party / community）+ credential mode（none / OAuth / API key / wrapped script）
- [ ] **bugfix 风险面**：修 `.claude/skills/` 内 SKILL 行为时 description 文案变化不能破坏正向 trigger 命中率（A12）；description 修剪过头会让 user 输入触发不到 skill — fix 类语义修改要保留主 trigger 词

</details>
