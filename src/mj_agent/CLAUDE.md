# src/mj_agent/CLAUDE.md

> Runtime code conventions for `src/mj_agent/`. Loaded additively after root CLAUDE.md when
> Claude Code works in this subdirectory.
> See root `CLAUDE.md` for repo-wide map, HITL scenarios, and Codex Status.

## 4 项专属必停文件路径（最高优先级；详 `policies/data-boundary.md` §3）

| Hard Stop | 路径 | 触发动作 |
|---|---|---|
| sql-guardrail-relax | `src/mj_agent/tools/sql/{guardrail,precheck}.py` | **HITL required**；不直接 Edit；走 cross-capability workflow |
| runtime-skill-content-change | `src/mj_agent/skills/*/SKILL.md` body | **HITL required**；用 `mj-agent-runtime-skill-doc-improve` skill（read-only diff） |
| prompt-version-or-body-change | `src/mj_agent/prompts/system.md` body 或 version | **HITL required**；用 `mj-agent-runtime-prompt-version-bump` skill（含义吸收原 `prompt-version-bump`；per D-3d canonical 10-enum）|
| biz-catalog-sync | `src/mj_agent/biz_catalog/qcm_catalog.yaml` | **HITL required**；用 `mj-agent-runtime-biz-catalog-sync` skill |

## 工具加载顺序（per `prompts/system.md`）

`find_biz_context → list_biz_tables → describe_biz_table → execute_sql`.

详 `tools/__init__.py:ALL_TOOLS` 注册中心.

## Middleware 链

`agent.py:make_graph()` 当前 middleware：

- `handle_sql_tool_errors`（ADR-029；`middleware/tool_errors.py`）

新增 middleware 走 `sdd/workflows/cross-capability-change.md`（影响 agent.py / middleware/ 即
跨 tool-chain capability）.

## SKILL 加载（in-source canonical）

- 启用列表：`agent.py:_ACTIVE_SKILLS`（当前 MVP 3 个：biz-domain-context / qcm-analysis /
  safe-sql-analysis）
- Loader：`load_skill()` 必须 strip frontmatter（详 `sdd/adapters/runtime-skill.md` §
  Frontmatter Strip 契约；A11 PR gate from Phase M3 blocking）

## 本子目录最小可执行命令集（B1 大型代码库最佳实践）

```bash
uv run mypy src/mj_agent              # strict type check (CI gate)
uv run ruff check src/mj_agent        # lint (CI gate)
```

不要在本子目录工作时跑全套测试 — 走对应 `tests/` 子目录的命令（详 `tests/CLAUDE.md`）.

## CI Gates 触及（本 subdir 路径）

- **V1 python contracts** — BLOCKING (Stage C C-a; commit `02b1cc8`); covers `src/mj_agent/**/*.py` schema
- **V3 prompt contracts** — BLOCKING; freeze anchor `src/mj_agent/prompts/system.md`
- **V7 runtime-skill contracts** — BLOCKING; freeze anchor `src/mj_agent/skills/*/SKILL.md`
- **V2 agent contracts** — warning (Phase 2+ activation when `agent.contract.yml` lands)
- Truth source: `.github/workflows/ci.yml` (per-job `continue-on-error` 状态)

## Freeze surface 警示

本 subdir 含 4 项 §M2 freeze surface（3 in-source SKILL + `prompts/system.md`）。任何 body
变更触发 `content_hash` drift → HITL gate（per `policies/ai-agent.md §4` canonical 10-enum
+ `claude-skill.contract.yml` / `runtime-skill.contract.yml` / `prompt.contract.yml`
`frozen_at`）。修改前先看 `policies/ai-agent.md §7` Pre-flight Verification Discipline.

## Anti-patterns

- ❌ 直接 Edit `tools/sql/guardrail.py` 或 `precheck.py`（触发 sql-guardrail-relax；必先 HITL）
- ❌ 直接 Edit `skills/*/SKILL.md` body（触发 runtime-skill-content-change；用 read-only skill）
- ❌ 修改 `prompts/system.md` 不 bump version（违反 prompt-version-bump 约束）
- ❌ 修改 `biz_catalog/qcm_catalog.yaml` 不对照上游 DB schema（biz-catalog-sync 触发）
- ❌ 绕过 `load_skill()` 直接 `open(SKILL.md).read()`（违反 A11 frontmatter strip 契约）

## See Also

- 根级：`CLAUDE.md`（repo-wide map） + `AGENTS.md`（Codex 边界）
- HITL canonical: `policies/ai-agent.md §4` (Canonical 10-Enum) + `§7` (Pre-flight
  Verification Discipline)
- A2 hook: `.claude/hooks/stop-claude-md-improver/` (Stop event; allowlist denies 本 subdir
  freeze surface — per commit `0d086c2`)
- Adapter: `sdd/adapters/python.md` (V1) + `sdd/adapters/runtime-skill.md` (V7) +
  `sdd/adapters/prompt.md` (V3)
- 同目录：`src/mj_agent/agent.py`（wired tool registry + middleware list + skill loader）

---

> *Phase M0 skeleton — Phase M6 末根据 capability 落地经验校准.*
