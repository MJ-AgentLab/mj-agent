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

## 文档自检（按 track 选填，详见 [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] §7.1）

<details>
<summary><b>Code-Side checklist</b> (A1-A6 + OB1-OB5) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side §7.1]]</summary>

- [ ] 若变更影响运行入口、关键环境变量、依赖版本，`CLAUDE.md` 已同步检查（A6）
- [ ] 若新增/修改 PR 模板或 CI 工作流涉及 A1-A10 校验，v2.0 trio ([[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta_Framework v2.0]] + [[../../docs/rule/[STANDARD]_MJ_Agent_Code_Side_Documentation_Framework|Code_Side v1.0]] + [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side v1.0]]) 已同步
- [ ] OB1-OB5：非阻塞观察项（Code_Side §7.2；Phase 1 填充阈值）

</details>

<details>
<summary><b>Agent-Side checklist</b> (A7-A10) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework|Agent_Side §7.1]]</summary>

- [ ] 若维护脚本触及 `src/mj_agent/skills/**/SKILL.md` 或 `src/mj_agent/prompts/*.md` 的 loader 路径/契约，A7-A10 + §7.5 frontmatter strip 仍然成立

</details>

<details>
<summary><b>Engineering-Workflow checklist</b> (A12-A14) — cite [[../../docs/rule/[STANDARD]_MJ_Agent_Documentation_Meta_Framework|Meta v2.1 §7.7]]</summary>

- [ ] **A12** `.claude/skills/<name>/SKILL.md` 用 ADR-013 native schema（`name` + `description`）；`description` ≥ 200 chars 含正向触发 + `Do not use for:` 反向块；`name` 符合 `mj-agent-<group>-<verb>` namespace
- [ ] **A13** `.claude/settings.json` allowlist diff 评审：无裸 `Bash`、secret patterns 在 `permissions.deny`、`enabledPlugins` 变更附 PR body 理由
- [ ] **A14** `.mcp.json` server 增删声明 trust posture（first-party / third-party / community）+ credential mode（none / OAuth / API key / wrapped script）
- [ ] **maintain 风险面**：`scripts/` / CI / `setup-env.ps1` / `setup-mcp-env.ps1` / `secrets.enc` 改动常触 A13/A14 双查；CI workflow 涉及 secret 注入路径要复核 `permissions.deny`

</details>
