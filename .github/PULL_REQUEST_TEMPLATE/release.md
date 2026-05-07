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

### 文档自检（按 track 选填，详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0|Meta_Framework v2.0]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework_v1.0|Code_Side §7.1]]</summary>

- [ ] 所有 `state: draft` 的 canonical 文档已升级到 `active` 或留到下一个 release（A2-A3 快速扫描）
- [ ] 本 release 周期内 allowlist 文档（框架 / 架构 / 运行入口）变更同步反映在 `CLAUDE.md`（A6）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A10) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0|Agent_Side §7.1]]</summary>

- [ ] 本 release 周期内引入/修改的 `[SKILL]` / `[PROMPT]` / `[CONTRACT]` 在 `docs/INDEX.md` 中已反映
- [ ] 所有 `state: active` 的 `[PROMPT]` `eval_references` 非空（A8，Phase 2 起强制）

</details>

### Details
See [CHANGELOG.md](CHANGELOG.md) for full release notes.
