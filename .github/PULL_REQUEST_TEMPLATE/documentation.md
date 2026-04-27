---
name: Documentation PR
about: 纯文档变更 (documentation/*) 的 Pull Request
---

## 文档变更内容
<!-- 列出新增或修改的文档及变更摘要 -->

## 变更原因
<!-- 为什么需要这次文档更新 -->

## 自检结果（A1-A10，详见 `docs/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md` §7.1）
- [ ] **A1** 路径与文件名符合命名约定（`[TYPE][_Subject]_Description[_vX.Y].md` 或类型专属格式）
- [ ] **A2** Canonical 文档 frontmatter schema 完整（`type` / `domain` / `summary` / `owner` / `created` / `updated` / `state`；`[STANDARD]`/`[SPEC]`/`[SKILL]`/`[PROMPT]`/`[EVAL]`/`[CONTRACT]` 还需 `version`）
- [ ] **A3** `state` 取值在 `draft / active / deprecated`；类型专属字段枚举合法（`decision` / `resolution` / `eval_kind` / `contract_kind`）
- [ ] **A4** 所有 Wikilink `[[...]]` 目标存在于仓库中
- [ ] **A5** 必要的 `docs/INDEX.md` 或 `docs/**/INDEX.md` 已同步或可重建
- [ ] **A6** 若变更属于 allowlist（框架/架构/核心运行入口），`CLAUDE.md` 已同步检查
- [ ] **A7** 若新增/修改 `[SKILL]`，`src/mj_agent/skills/<name>/` 目录存在且名称一致
- [ ] **A8** 若新增/修改 `[PROMPT]` 且 `state: active`，`eval_references` 非空（Phase 2 起强制）
- [ ] **A9** 若新增/修改 `[EVAL]` 且 `state: active`，`dataset_path` 指向存在文件，`baseline_metric`/`baseline_value` 填写
- [ ] **A10** 若新增/修改 `[CONTRACT]` 且 `state: active`，`schema_ref` 指向存在 schema 文件
- [ ] Commit message 仅含 `docs` 类型
