## 变更摘要
简述本次变更内容和目的。

## 关联 Issue
Closes #<issue-id>

## 影响范围
受影响的模块 / 接口 / 文件。

## 自检结果
- [ ] 本地自测通过（`uv sync` + 目标脚本运行）
- [ ] 无调试代码残留（print / TODO hack）
- [ ] 无硬编码（密钥、令牌、绝对路径）
- [ ] Commit message 符合 `<type>(<scope>): <summary>` 规范

## 文档自检（A1-A10，详见 `docs/rule/[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1.md` §7.1）
- [ ] A1-A3：新增/修改 canonical 文档（含 `src/mj_agent/skills/**/SKILL.md` 与 `src/mj_agent/prompts/*.md`）路径/命名合法、frontmatter schema 完整、state 与专属字段枚举合法
- [ ] A4-A5：内部 Wikilink 目标存在；必要的 `docs/**/INDEX.md` 已同步
- [ ] A6：allowlist 文档（框架/架构/运行入口）变更已同步检查 `CLAUDE.md`
- [ ] A7：新增/修改 `[SKILL]` 时，`src/mj_agent/skills/<name>/` 目录与文档身份一致
- [ ] A8：新增/修改 `[PROMPT]` 时 `version` 填写；`state: active` 时 `eval_references` 非空（Phase 2 起强制）
- [ ] A9：新增/修改 `[EVAL]` 时 `dataset_path` 存在、`baseline_metric`/`baseline_value` 填写（Phase 2 起）
- [ ] A10：新增/修改 `[CONTRACT]` state=active 时 `schema_ref` 存在

## 审核要点
提示 Reviewer 重点关注的内容。
