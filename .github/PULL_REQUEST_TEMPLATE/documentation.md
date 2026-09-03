---
name: Documentation PR
about: 纯文档变更 (documentation/*) 的 Pull Request
---

## 文档变更内容
<!-- 列出新增或修改的文档及变更摘要 -->

## 变更原因
<!-- 为什么需要这次文档更新 -->

## 自检结果（按 track 选填，详见 [[../../policies/documentation|documentation policy]] §5）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../policies/documentation|documentation policy]] §5.1</summary>

- [ ] **A1** 路径与文件名符合命名约定（`[TYPE][_Subject]_Description[_vX.Y].md` 或类型专属格式）
- [ ] **A2** Canonical 文档 frontmatter schema 完整（`type` / `domain` / `summary` / `owner` / `created` / `updated` / `state`；`[STANDARD]`/`[SPEC]`/`[SKILL]`/`[PROMPT]`/`[EVAL]`/`[CONTRACT]` 还需 `version`）
- [ ] **A3** `state` 取值在 `draft / active / deprecated`；类型专属字段枚举合法（`decision` / `resolution` / `eval_kind` / `contract_kind`）
- [ ] **A4** 所有 Wikilink `[[...]]` 目标存在于仓库中
- [ ] **A5** 必要的 `docs/INDEX.md` 或 `docs/**/INDEX.md` 已同步或可重建
- [ ] **A6** 若变更属于 allowlist（框架/架构/核心运行入口），`CLAUDE.md` 已同步检查
- [ ] **OB1-OB5** 非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A11) — cite [[../../policies/documentation|documentation policy]] §5.3 + [[../../sdd/adapters/runtime-skill|runtime-skill adapter]] / [[../../sdd/adapters/prompt|prompt adapter]] / [[../../sdd/adapters/contract|contract adapter]]</summary>

- [ ] **A7** 若新增/修改 `[SKILL]`，`src/mj_agent/skills/<name>/` 目录存在且名称一致
- [ ] **A8** 若新增/修改 `[PROMPT]` 且 `state: active`，`eval_references` 非空（Phase 2 起强制）
- [ ] **A9** 若新增/修改 `[EVAL]` 且 `state: active`，`dataset_path` 指向存在文件，`baseline_metric`/`baseline_value` 填写
- [ ] **A10** 若新增/修改 `[CONTRACT]` 且 `state: active`，`schema_ref` 指向存在 schema 文件
- [ ] **A11** SKILL `state: active` 时 `eval_references` 非空（Phase D 起强制；transitional waiver 期内允许注释 TODO）

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite A12 → [[../../sdd/adapters/claude-code-skill|claude-code-skill adapter]] §Standards / §CI Gate; A13 → [[../../policies/ci-gates|ci-gates policy]] §5.1; A14 → [[../../policies/ai-agent|ai-agent policy]] §4</summary>

- [ ] **A12** `.claude/skills/<name>/SKILL.md` 用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正向触发 + `Do not use for:` 反向块；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` allowlist diff 评审：无裸 `Bash`、secret patterns 在 `permissions.deny`、`enabledPlugins` 变更附 PR body 理由
- [ ] **A14** `.mcp.json` server 增删声明 trust posture（first-party / third-party / community）+ credential mode（none / OAuth / API key / wrapped script）
- [ ] **documentation 风险面**：改 `.claude/skills/**/SKILL.md` body 时 frontmatter `name` + `description` 不漂（A12）；修订 [[../../sdd/adapters/claude-code-skill|claude-code-skill adapter]] / [[../../policies/ci-gates|ci-gates policy]] / [[../../policies/ai-agent|ai-agent policy]] 等 A12-A14 kernel home 时条文与本 template 同步检查

</details>

- [ ] Commit message 仅含 `docs` 类型

## AI Self-Check Checklist（per [[../../policies/ai-agent|ai-agent policy]] §6.1）

- [ ] **Codex 参与情况**：`NONE` 或描述其具体贡献（§1；standalone Codex 已开 ⇒ 可为 non-NONE，non-NONE 须 Owner 拍板）
- [ ] **HITL scenario hit**：`NONE` 或逐项列出（§4 canonical 10-enum）
- [ ] **BDD/TDD impact**：`NONE` 或逐项列出（[[../../sdd/adapters/bdd-tdd|bdd-tdd adapter]]）
- [ ] **Subagent dispatched**：`NONE` 或逐项列出（§2 A3 subagent split 准则）

> **PR 面另附 `HITL Trigger Inventory`**（canonical 10-enum 逐条勾选，与 §4 一一对应）。本模板
> **不复制那张表** —— 10-enum 的唯一 home 是 [[../../policies/ai-agent|ai-agent policy]] §4
> （同一枚举出现两次必然漂移，per §5.2）；直接取用 root 模板
> `.github/PULL_REQUEST_TEMPLATE.md` 的同名小节整段即可。它与上列第 2 条是**不同粒度**：
> 第 2 条是「本次是否命中」的摘要，Inventory 是逐 enum 的可查证据。
> **不适用的行标 `— No`，不要删行。**
