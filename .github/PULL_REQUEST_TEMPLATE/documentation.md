---
name: Documentation PR
about: 纯文档变更 (documentation/*) 的 Pull Request
---

## 文档变更内容
<!-- 列出新增或修改的文档及变更摘要 -->

## 变更原因
<!-- 为什么需要这次文档更新 -->

## 自检结果（按 track 选填，详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side §7.1]]</summary>

- [ ] **A1** 路径与文件名符合命名约定（`[TYPE][_Subject]_Description[_vX.Y].md` 或类型专属格式）
- [ ] **A2** Canonical 文档 frontmatter schema 完整（`type` / `domain` / `summary` / `owner` / `created` / `updated` / `state`；`[STANDARD]`/`[SPEC]`/`[SKILL]`/`[PROMPT]`/`[EVAL]`/`[CONTRACT]` 还需 `version`）
- [ ] **A3** `state` 取值在 `draft / active / deprecated`；类型专属字段枚举合法（`decision` / `resolution` / `eval_kind` / `contract_kind`）
- [ ] **A4** 所有 Wikilink `[[...]]` 目标存在于仓库中
- [ ] **A5** 必要的 `docs/INDEX.md` 或 `docs/**/INDEX.md` 已同步或可重建
- [ ] **A6** 若变更属于 allowlist（框架/架构/核心运行入口），`CLAUDE.md` 已同步检查
- [ ] **OB1-OB5** 非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A11) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side §7.1]]</summary>

- [ ] **A7** 若新增/修改 `[SKILL]`，`src/mj_agent/skills/<name>/` 目录存在且名称一致
- [ ] **A8** 若新增/修改 `[PROMPT]` 且 `state: active`，`eval_references` 非空（Phase 2 起强制）
- [ ] **A9** 若新增/修改 `[EVAL]` 且 `state: active`，`dataset_path` 指向存在文件，`baseline_metric`/`baseline_value` 填写
- [ ] **A10** 若新增/修改 `[CONTRACT]` 且 `state: active`，`schema_ref` 指向存在 schema 文件
- [ ] **A11** SKILL `state: active` 时 `eval_references` 非空（Phase D 起强制；transitional waiver 期内允许注释 TODO）

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1 §7.7]]</summary>

- [ ] **A12** `.claude/skills/<name>/SKILL.md` 用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正向触发 + `Do not use for:` 反向块；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` allowlist diff 评审：无裸 `Bash`、secret patterns 在 `permissions.deny`、`enabledPlugins` 变更附 PR body 理由
- [ ] **A14** `.mcp.json` server 增删声明 trust posture（first-party / third-party / community）+ credential mode（none / OAuth / API key / wrapped script）
- [ ] **documentation 风险面**：改 `.claude/skills/**/SKILL.md` body 时 frontmatter `name` + `description` 不漂（A12）；修订 Meta v2.1 / Code_Side / Agent_Side / HITL_Prompt 等 STANDARD 时 A12-A14 条文与本 template 同步检查

</details>

- [ ] Commit message 仅含 `docs` 类型
