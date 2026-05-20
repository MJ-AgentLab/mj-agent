# tests/CLAUDE.md

> Test matrix conventions for `tests/`. Loaded additively after root CLAUDE.md.
> See root `CLAUDE.md` for repo-wide map + `sdd/adapters/bdd-tdd.md` for cross-cutting BDD/TDD
> rules.

## 11 子目录矩阵（Phase 1-3 落地；Phase M0 当前仅 ≤5 子目录）

| 子目录 | 用途 | 标记 / 默认 select |
|---|---|---|
| `tests/unit/` | 纯 Python 单元测试 | default selected |
| `tests/contracts/` ★ Phase M3 改名 | capability contract 测试（由 `tests/contract/` 改名）| `-m contract`；默认 deselect |
| `tests/bdd/` ★ Phase M3 新增 | BDD scenario 自动化（pytest-bdd） | default selected |
| `tests/integration/` | 跨组件 + 真实依赖 | default selected；缺 .env 时 session-skip |
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
uv run pytest tests/unit -q

# 仅 contract 测试（per-capability）
uv run pytest tests/contracts/data_agent/safe_sql/ -m contract
uv run pytest tests/contracts/infrastructure/docker_compose/ -m contract

# BDD scenario（per-capability）
uv run pytest tests/bdd/data_agent/safe_sql/ -k "<scenario name keyword>"

# Smoke（默认 deselect；需 -m smoke 显式 opt-in）
uv run pytest tests/smoke -m smoke

# EVAL framework baseline（Phase 2+ EVAL framework 落地后）
uv run pytest tests/eval/component
```

`pyproject.toml` pins `addopts = "-m 'not smoke and not contract'"` — plain `pytest` excludes
smoke + contract by default.

## Anti-patterns

- ❌ smoke 测试无 `@pytest.mark.smoke` marker（会进 default selected → CI 误跑）
- ❌ contract 测试无 `@pytest.mark.contract` marker（同上）
- ❌ bdd scenario 不在 `tests/bdd/<capability>/steps/` 写 step definitions（违反 BDD adapter
  规则）
- ❌ integration / smoke 测试硬依赖 .env 而无 session-skip fallback（CI 会 fail 而非 skip）

## See Also

- `sdd/adapters/bdd-tdd.md`（BDD/TDD 横切准则）
- `sdd/adapters/python.md`（Python contract testing）
- `pyproject.toml`（pytest config: addopts / markers）

---

> *Phase M0 skeleton — Phase M3 子目录改名 / 新增时刷新.*
