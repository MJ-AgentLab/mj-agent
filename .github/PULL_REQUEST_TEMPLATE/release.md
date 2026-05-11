---
name: Release PR
about: 版本发布 (develop → main) 的 Pull Request
---

## Release vX.Y.Z — <版本主题>

### Highlights
<!-- 核心变更列表 -->

### 审核要点
- [ ] CHANGELOG.md 完整性（`[Unreleased]` 已转为正式版本节，如 CHANGELOG.md 存在）
- [ ] 版本号一致（`pyproject.toml` 与 README 中的版本声明）
- [ ] 无残留调试代码
- [ ] 无未关闭的阻塞性 Issue

### 文档自检（按 track 选填，详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side §7.1]]</summary>

- [ ] 所有 `state: draft` 的 canonical 文档已升级到 `active` 或留到下一个 release（A2-A3 快速扫描）
- [ ] 本 release 周期内 allowlist 文档（框架 / 架构 / 运行入口）变更同步反映在 `CLAUDE.md`（A6）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A10) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side §7.1]]</summary>

- [ ] 本 release 周期内引入/修改的 `[SKILL]` / `[PROMPT]` / `[CONTRACT]` 在 `docs/INDEX.md` 中已反映
- [ ] 所有 `state: active` 的 `[PROMPT]` `eval_references` 非空（A8，Phase 2 起强制）

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1 §7.7]]</summary>

- [ ] **A12** 本 release 周期内新增/修改的 `.claude/skills/<name>/SKILL.md` 全部用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正反 trigger；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` 在本 release 周期内的累计 diff 评审：无裸 `Bash` 残留、secret patterns 完整在 `permissions.deny`、`enabledPlugins` 变更与对应 PR body 理由一一对应
- [ ] **A14** `.mcp.json` 在本 release 周期内的 server 增删与 trust posture / credential mode 声明在对应 PR body 一一对应
- [ ] **release 风险面**：把 `.claude/{settings.json,skills/}` 与 `.mcp.json` 的本周期增删与对应 maintain/* / feature/* PR 的 A12-A14 自检记录交叉核对，确认无遗漏；hotfix/* 紧急通道临时跳过的 A13/A14 已补 documentation/* PR

</details>

### Details
See [CHANGELOG.md](CHANGELOG.md) for full release notes.
