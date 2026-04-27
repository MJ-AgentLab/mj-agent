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
- [ ] 所有 `state: draft` 的 canonical 文档已升级到 `active` 或留到下一个 release（A2-A3 快速扫描）
- [ ] 本 release 周期内引入/修改的 `[SKILL]` / `[PROMPT]` / `[CONTRACT]` 在 `docs/INDEX.md` 中已反映

### Details
See [CHANGELOG.md](CHANGELOG.md) for full release notes.
