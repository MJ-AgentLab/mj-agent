# tests/CLAUDE.md

> Test matrix conventions for `tests/`. Loaded additively after root CLAUDE.md.
> See root `CLAUDE.md` for repo-wide map + `sdd/adapters/bdd-tdd.md` for cross-cutting BDD/TDD
> rules.

@AGENTS.md

> ↑ 同层工具中立约束（binds Claude Code + Codex；per dual-agent-compat v5 P1）。

## 11 子目录矩阵（Phase 1-3 落地；Phase M0 当前仅 ≤5 子目录）

| 子目录 | 用途 | 标记 / 默认 select |
|---|---|---|
| `tests/unit/` | 纯 Python 单元测试 | default selected |
| `tests/contracts/` ★ Phase M3 改名 | capability contract 测试（由 `tests/contract/` 改名）| `-m contract`；默认 deselect |
| `tests/bdd/` | BDD scenario 自动化（pytest-bdd; active per Stage B B-1..B-6 + B-7 CI gate `c60aaa3`） | default selected |
| `tests/integration/` | 跨组件 + 真实依赖 | default selected；始终 structured policy skip |
| `tests/smoke/` | 端到端 + LLM | `-m smoke`；默认 deselect |
| `tests/eval/` | EVAL framework（ADR-024 联动）| default selected；4 子类 outcome / trajectory / component / integration |
| `tests/agents/` ★ Phase 2+ | LangChain Agent schema 测试 | TBD |
| `tests/prompts/` ★ Phase 2+ | Prompt regression（ADR-024 联动） | TBD |
| `tests/docker/` ★ Phase 3+ | docker compose config + image lint | TBD |
| `tests/db/` ★ Phase 2+ | DB schema + migration test | TBD |
| `tests/data_quality/` ★ Phase 2+ | catalog freshness / data alignment | TBD |

## 本子目录最小可执行命令集

```bash
# 单元测试（默认 default selected）
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit -q

# 仅 contract 测试（per-capability）
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/contract -m contract

# BDD scenario（per-capability）
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/bdd/data_agent/safe_sql -k "<scenario name keyword>"

# Smoke（默认 deselect；需 -m smoke 显式 opt-in）
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/smoke -m smoke

# EVAL framework baseline（Phase 2+ EVAL framework 落地后）
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/eval/component
```

`pyproject.toml` pins `addopts = "-m 'not smoke and not contract'"` — plain `pytest` excludes
smoke + contract by default.

## CI Gates 触及（本 subdir 路径）

- **BDD scenarios** — BLOCKING (Stage C C-a; commit `02b1cc8`); runs `tests/bdd/` via dedicated CI step
- **Main Tests step** — strict (no `continue-on-error`); runs `tests/unit + tests/eval + tests/integration` with `--ignore=tests/bdd`
- **Contract tests step** — gated (`tests/contract -m contract`; live legs always policy-skip)
- Smoke (`-m smoke`) — never in CI; manual only
- Truth source: `.github/workflows/ci.yml` (per-job `continue-on-error` 状态)

## Anti-patterns

- ❌ smoke 测试无 `@pytest.mark.smoke` marker（会进 default selected → CI 误跑）
- ❌ contract 测试无 `@pytest.mark.contract` marker（同上）
- ❌ bdd scenario 不在 `tests/bdd/<capability>/steps/` 写 step definitions（违反 BDD adapter
  规则）
- ❌ integration / smoke 测试读取 `.env`、以 credential presence 控制 session skip、或据此
  启用 external route；external bands 必须无条件使用 canonical
  `SKIP_POLICY_EXTERNAL_DEPENDENCY`

## See Also

- 根级：`CLAUDE.md` + `capabilities/CLAUDE.md`（contract authoring → contracts/ files
  consumed by `tests/contracts/` + `tests/bdd/`）
- `sdd/adapters/bdd-tdd.md`（BDD/TDD 横切准则）
- `sdd/adapters/python.md`（Python contract testing）
- `pyproject.toml`（pytest config: addopts / markers）
- HITL canonical: `policies/ai-agent.md §4` + `§7` (Pre-flight Verification Discipline)
- A2 hook: `.claude/hooks/stop-claude-md-improver/`

---

> *Phase M0 skeleton — Phase M3 子目录改名 / 新增时刷新.*
