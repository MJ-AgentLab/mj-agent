---
name: Maintain PR
about: CI/CD、依赖、脚本等基础设施维护 (maintain/*) 的 Pull Request
---

## 变更摘要
<!-- 简述本次维护变更的内容和目的 -->

## 影响评估
<!-- 列出受影响的环境（开发/CI）、工具链或依赖 -->

## 审核要点
<!-- 提示审核者重点关注的内容 -->

## 自检结果
- [ ] 配置文件语法正确（YAML / TOML / JSON）
- [ ] GitHub Actions 工作流不受影响（或已同步更新）
- [ ] 无硬编码敏感信息（密钥、令牌、IP、密码）
- [ ] Commit message 符合规范（仅含 `infra` / `docs` 类型）

## 文档自检（按 track 选填，详见 [[../../policies/documentation|documentation policy]] §5）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../policies/documentation|documentation policy]] §5.1</summary>

- [ ] 若变更影响运行入口、关键环境变量、依赖版本，`CLAUDE.md` 已同步检查（A6）
- [ ] 若新增/修改 PR 模板或 CI 工作流涉及 A1-A11 校验，文档治理 kernel home（[[../../policies/documentation|documentation policy]] §5 门禁 + [[../../sdd/adapters/runtime-skill|runtime-skill adapter]] / [[../../sdd/adapters/prompt|prompt adapter]] / [[../../sdd/adapters/contract|contract adapter]]）已同步
- [ ] OB1-OB5：非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A11) — cite [[../../policies/documentation|documentation policy]] §5.3 + [[../../sdd/adapters/runtime-skill|runtime-skill adapter]] / [[../../sdd/adapters/prompt|prompt adapter]] / [[../../sdd/adapters/contract|contract adapter]]</summary>

- [ ] 若维护脚本触及 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/*.md` 的 loader 路径/契约，A7-A11 + [[../../sdd/adapters/runtime-skill|runtime-skill adapter]] frontmatter strip 契约仍然成立
- [ ] **A11** SKILL `state: active` 时 `eval_references` 非空（Phase D 起强制；transitional waiver 期内允许注释 TODO）

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite A12 → [[../../sdd/adapters/claude-code-skill|claude-code-skill adapter]] §Standards / §CI Gate; A13 → [[../../policies/ci-gates|ci-gates policy]] §5.1; A14 → [[../../policies/ai-agent|ai-agent policy]] §4</summary>

- [ ] **A12** `.claude/skills/<name>/SKILL.md` 用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正向触发 + `Do not use for:` 反向块；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` allowlist diff 评审：无裸 `Bash`、secret patterns 在 `permissions.deny`、`enabledPlugins` 变更附 PR body 理由
- [ ] **A14** `.mcp.json` server 增删声明 trust posture（first-party / third-party / community）+ credential mode（none / OAuth / API key / wrapped script）
- [ ] **maintain 风险面**：`scripts/` / CI / `setup-env.ps1` / `setup-mcp-secrets.ps1` (ADR-030) / `secrets.enc` + `secrets-mcp.enc` 改动常触 A13/A14 双查；CI workflow 涉及 secret 注入路径要复核 `permissions.deny`

</details>

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
