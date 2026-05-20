# Pull Request

> Replaced by spec-anchored-refactor Phase M0 (per ADR-031).
> 旧 tri-track A1-A14 self-check 在 Phase M5 时整体迁入 `policies/documentation.md` +
> `policies/claude-code-skill.md` 段；过渡期保留 `<details>` block 作 backward-compat.

## Summary

<1-3 句：本 PR 做什么 + 为什么>

## Linked ADR / Plan

- Linked ADR: `decisions/ADR-NNN_<slug>.md` (或 `docs/adr/...` 过渡期)
- Linked Plan: `plans/[PLAN]_<slug>.md`
- Phase Marker: M0 / M1 / M2 / ... (per `[PLAN]_spec_anchored_refactor.md`)

## Plan-vs-Diff Scope Declaration（手册 §9.3）

本 PR 的实际变更范围 vs Plan 声明范围：

- **Plan 声明**：<列出 plan 中明确列入本 PR 的文件 / 目录范围>
- **实际改动**：<列出本 PR 实际改动的文件 / 目录范围>
- **是否偏离**：no / yes（如 yes → 走 `mj-agent-flow-scope-drift` HITL）

## Adapter Coverage（哪些 sdd/adapters/ 被影响）

- [ ] `python`
- [ ] `langchain-agent`
- [ ] `prompt`
- [ ] `runtime-skill`
- [ ] `claude-code-skill`
- [ ] `docker-container`
- [ ] `bdd-tdd`
- [ ] N/A（纯文档 / 元规则）

## Docker Impact

- [ ] no
- [ ] yes — Dockerfile / compose.yaml / override.yml 修改
- [ ] yes — **compose.prod.yml 修改 → 生产红线 HITL（≥ 2 reviewer）**

## Evidence Links

- BDD evidence: `evidence/bdd/...`（如 capability 有 behavior.feature）
- TDD evidence: `evidence/tdd/...`（red / green / refactor 三阶段）
- Verification evidence: `evidence/verification/...`

## Spec Drift

- [ ] no drift（capability spec.yml / requirements.md / contracts/ 与本 PR 实施一致）
- [ ] drift detected（说明并触发 `bugfix-drift.md` 或 `evolve-capability.md`）
- [ ] N/A（无 capability scope；如 Phase M0 元规则 PR）

## AI Self-Check Checklist（per `policies/ai-agent.md` §4 + §6）

- [ ] Codex invocation: **NONE**（如 NONE 显式声明；non-NONE 必须 HITL）
- [ ] HITL scenario hit: **NONE / 列出**（per `policies/ai-agent.md` §4 12 项场景）
- [ ] BDD/TDD impact: **NONE / 列出**（per blueprint §11.6 #11）
- [ ] Subagent dispatched: **NONE / 列出**（per `policies/ai-agent.md` §2 A3）

## HITL Trigger Inventory（4 项专属必停 + cross-cap + DB / Docker prod / secrets）

- [ ] sql-guardrail-relax（`src/mj_agent/tools/sql/{guardrail,precheck}.py`）
- [ ] runtime-skill-content-change（`src/mj_agent/skills/*/SKILL.md` body）
- [ ] prompt-version-bump（`src/mj_agent/prompts/system.md`）
- [ ] biz-catalog-sync（`src/mj_agent/biz_catalog/qcm_catalog.yaml`）
- [ ] cross-capability contract change
- [ ] DB migration（mj_agent_memory schema）
- [ ] secrets / 权限 / GRANT 变更
- [ ] CI blocking gate 启用 / 关闭
- [ ] 大规模目录迁移（≥10 文件）
- [ ] `docker/compose.prod.yml` 变更
- [ ] `.mcp.json` 新增 server（A14 trigger）

## Verification Plan

```bash
# 列出本 PR 跑过的验证命令 + 结果
uv run pytest tests/unit -q
uv run pytest tests/contract -m contract
# ...
```

未跑命令的原因（如 worktree 缺 .env）：<...>

## Reviewer Focus

提示 Reviewer 重点关注：

- ...
- ...

---

<details>
<summary><b>Legacy Code-Side checklist</b> (A1-A6 + OB1-OB5) — Phase M5 末迁入 policies/</summary>

- [ ] A1-A3：新增/修改 canonical 文档（含 `src/mj_agent/skills/**/SKILL.md` 与 `src/mj_agent/prompts/*.md`）路径/命名合法、frontmatter schema 完整、state 与专属字段枚举合法
- [ ] A4-A5：内部 Wikilink 目标存在；必要的 `docs/**/INDEX.md` 已同步
- [ ] A6：allowlist 文档（框架/架构/运行入口）变更已同步检查 `CLAUDE.md`
- [ ] OB1-OB5：非阻塞观察项

</details>

<details>
<summary><b>Legacy Agent-Side checklist</b> (A7-A10) — Phase M5 末迁入 policies/</summary>

- [ ] A7：新增/修改 `[SKILL]` 时，`src/mj_agent/skills/<name>/` 目录与文档身份一致
- [ ] A8：新增/修改 `[PROMPT]` 时 `version` 填写；`state: active` 时 `eval_references` 非空
- [ ] A9：新增/修改 `[EVAL]` 时 `dataset_path` 存在、`baseline_metric`/`baseline_value` 填写
- [ ] A10：新增/修改 `[CONTRACT]` state=active 时 `schema_ref` 存在

</details>

<details>
<summary><b>Legacy Engineering-Workflow checklist</b> (A12-A14) — Phase M5 末迁入 policies/</summary>

- [ ] A12：`.claude/skills/<name>/SKILL.md` 使用 ADR-013 native schema；description ≥ 200 chars + reverse-trigger block
- [ ] A13：`.claude/settings.json` allowlist diffs reviewed；无 bare `Bash` in `permissions.allow`；secrets 在 `permissions.deny`
- [ ] A14：`.mcp.json` server 变更声明 trust posture + credential mode（per `docs/infrastructure/mcp/[STANDARD]_*`）

</details>
