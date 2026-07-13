# tests/AGENTS.md

> Tool-neutral local constraints for `tests/` — binds every AI agent working here (roster in
> root `AGENTS.md`). Codex discovers this file hierarchically (root → cwd); Claude Code
> imports it via the sibling `tests/CLAUDE.md`. Cross-cutting BDD/TDD rules live in
> `sdd/adapters/bdd-tdd.md` — this file only points.

## Band discipline

- Default-selected bands: `tests/unit` + `tests/eval` + `tests/integration` + `tests/bdd`;
  opt-in via markers: `-m smoke` / `-m contract` (`pyproject.toml` pins
  `addopts = "-m 'not smoke and not contract'"`). New smoke/contract tests MUST carry their
  marker, or CI will mis-select them.
- `tests/bdd` runs as its own CI step; the main Tests step runs with `--ignore=tests/bdd`.

## External-dependency rules

- Missing credentials must SKIP, not fail: integration/smoke tests follow the
  `tests/conftest.py` session-skip convention (`POSTGRES_ANALYST_USER` / `ARK_API_KEY`).
- Tests must not read `.env` values or embed secrets/DSNs in fixtures; biz-DB access in tests
  goes through the sanctioned integration fixtures only (root `AGENTS.md` boundaries 1-2).
- No dev-machine coupling: never reference a developer's local branches, absolute paths, or
  user-level plugin caches. Scripts under test take an injectable repo root
  (`main(argv, repo_root=...)`) so fixtures run against `tmp_path`, not the live tree.

## Fixture discipline

- Expected values are fixed files, never generated at runtime by the code under test.
- Real-tree assertion tests (asserting live repo file contents) must enumerate their target
  files explicitly, so structural moves fail loudly rather than silently passing.

## Verification (either tool, from repo root)

```bash
uv run pytest tests/unit -q
uv run pytest tests/eval -q
uv run pytest tests/bdd -q
```

## See also

- Root `AGENTS.md` · `tests/CLAUDE.md` (same layer) · `sdd/adapters/bdd-tdd.md`
- `pyproject.toml` (pytest markers / addopts) · `policies/ai-agent.md` §4 + §7
