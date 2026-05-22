# Stage B Closure — BDD Step Definitions Landing

**Stage:** Phase M3 Stage B (M3-FU-BDD-TDD-RESTORE work)
**Branch:** `documentation/spec-anchored-refactor-m3`
**Outcome:** pytest-bdd framework + 16 scenario bindings across 5 capabilities + dedicated CI gate (warning mode at M3, M4 strict per blueprint).

## Stage B atomic commits

| # | Commit | Scope | Tests |
|---|---|---|---|
| B-1 | `9464e5c` | pytest-bdd 8.1 framework + tests/bdd/ scaffolding + safe-sql 3 offline scenarios (REQ-001/002/006) | 3 PASS |
| B-2 | `0e3eb96` | safe-sql REQ-003/005 live-DB gated; REQ-004 documented unbound | 2 SKIP (live-DB) |
| B-3 | `8ad6f17` | biz-catalog 3 scenarios (1 offline + 2 live-DB) | 1 PASS + 2 SKIP |
| B-4 | `517a7ef` | llm-provider 3 offline scenarios (config-only) | 3 PASS |
| B-5 | `121719c` | docker-compose 3 scenarios with `docker_available` skip gate (CI always skips) | 3 SKIP |
| B-6 | `9af7fde` | mcp-server-governance 2 offline scenarios + feature file Gherkin fix | 2 PASS |
| B-7 | (this) | CI integration + Stage B closure evidence | (CI gate added) |

**Total bound: 16 scenarios** (5 + 3 + 3 + 3 + 2). **CI run state: 9 PASS + 7 SKIP + 0 FAIL.**

REQ-004 (safe-sql L4 statement_timeout) intentionally unbound — requires deterministic 60s+ query provocation infeasible in CI; documented in B-2 evidence as M4+ future work.

## Framework architecture

```
tests/bdd/
├── __init__.py
├── conftest.py                              # shared Background steps + assertion helpers + docker_available fixture
├── _shared/
│   ├── __init__.py
│   └── steps.py                             # placeholder for cross-capability Python utility helpers (non-step)
├── data_agent/
│   ├── safe_sql/                            # 5 scenarios bound (3 offline + 2 live-DB)
│   ├── biz_catalog/                         # 3 scenarios (1 offline + 2 live-DB)
│   └── llm_provider/                        # 3 offline scenarios
└── infrastructure/
    ├── docker_compose/                      # 3 scenarios (all docker_available gated)
    └── mcp_governance/                      # 2 offline scenarios
```

## Key design decisions (locked at Stage B kickoff Gate-1)

| Decision | Choice | Notes |
|---|---|---|
| BDD library | `pytest-bdd 8.1` | Shares pytest fixtures/CI w/ tests/unit/ — chosen over `behave` for fixture interop. |
| Subdir layout | `tests/bdd/<domain>/<capability>/` | Mirrors `capabilities/<domain>/<capability>/`. |
| Step sharing | `tests/bdd/conftest.py` (canonical pytest-bdd discovery) | `_shared/steps.py` reserved for ordinary Python utilities (non-step). |
| Gherkin literal `{` `}` `[` `]` | `parsers.re(re.escape(text))` | Default parser treats `{name}` as placeholder; literal braces (e.g. `biz_dwd.{dwd_dim_product_interface, ...}`) require regex matching. |
| Tag warnings | `filterwarnings = ["ignore::pytest.PytestUnknownMarkWarning"]` in pyproject | `@REQ-NNN` / `@risk:critical` / `@adapter:python` are informational, not pytest markers. |
| Stateless `@then` | Re-invoke SUT when scenario `@when` differs (e.g., REQ-002 `@when` is `precheck_sql` but `@then` asserts about `execute_sql`) | `execute_sql` is idempotent in rejection path. |
| Live-DB scenarios | Use existing `live_db` session fixture in `tests/conftest.py` | Skip-clean when `POSTGRES_ANALYST_USER` unset. |
| Docker scenarios | New `docker_available` session fixture in `tests/bdd/conftest.py` | Always skips in CI; M4+ may add probe. |
| Single duplicate `@when` text | Consolidate into one decorator with branching | pytest-bdd matches step text only; duplicate decorators conflict. |

## CI integration

New `ci.yml` step structure:

```yaml
- name: Tests (unit + eval + integration; smoke + contract + bdd excluded by default)
  run: uv run pytest --ignore=tests/bdd

- name: 'BDD scenarios (warning mode at M3; M4 strict per blueprint)'
  continue-on-error: true
  run: uv run pytest tests/bdd -q
```

- **Main "Tests" step**: explicit `--ignore=tests/bdd` so the BDD step is the sole BDD runner.
- **BDD step**: `continue-on-error: true` (warning mode per Stage B kickoff outline + plan §6 严格守约). Phase M4 will flip to strict per blueprint §6 gate matrix.

## Minor SUT + contract drift fixes surfaced during Stage B

| Surface | Fix | Commit |
|---|---|---|
| `src/mj_agent/tools/sql/guardrail.py` rejection message | Surface blocked keyword name (`"blocked keyword DROP detected"`) when `_BLOCKED.search` matches a non-SELECT statement | B-1 (`9464e5c`) |
| `capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature` line 35-36 | Malformed Gherkin step split across two lines without continuation syntax — joined to single line | B-6 (`9af7fde`) |

These are precisely the contract-vs-implementation drift findings BDD landing exists to surface.

## Regression checks (final)

- `uv run pytest --ignore=tests/bdd -q` → 329 passed / 5 skipped / 22 deselected
- `uv run pytest tests/bdd -q` → 9 passed / 7 skipped (4 live-DB + 3 docker)
- `uv run ruff check` → clean
- `uv run mypy src/mj_agent` → clean (44 files)
- pre-Stage-B baseline 236 passed → post-Stage-B 329 + 9 = 338 (delta +102, includes earlier Stage A test additions + 16 BDD scenarios)

## Stage A + Stage B accumulated state on `documentation/spec-anchored-refactor-m3`

12 atomic commits ahead of `origin/develop` (`658b590`):

```
Stage A (5 commits):
  a5614c4 fix(sdd): V4 parser bug
  e6ac9e1 fix(sdd): V3 canonical drift
  f3c9852 feat(sdd): V7 runtime-skill validator
  5cd68a6 feat(sdd): G1/G2/G9 real impl
  d31371d feat(sdd): V5 sub-flags

Stage B (7 commits):
  9464e5c test(bdd): pytest-bdd framework + safe-sql POC
  0e3eb96 test(bdd): safe-sql REQ-003/005 live-DB
  8ad6f17 test(bdd): biz-catalog 3 scenarios
  517a7ef test(bdd): llm-provider 3 scenarios
  121719c test(bdd): docker-compose 3 docker-gated
  9af7fde test(bdd): mcp-governance 2 + Gherkin fix
  (B-7)   test(bdd): CI BDD gate + Stage B closure
```

## Files added in B-7

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | Main Tests step explicit `--ignore=tests/bdd`; new BDD-specific warning-mode step added after it |
| `capabilities/data-agent/safe-sql/evidence/bdd/stage-b-closure.md` | this file |

## Forward to Stage C (blocking gate switches)

Stage C scope per Phase M3 kickoff outline:
- Toggle V3 / V5 / V6 / V7 / G1 / G2 / G9 / BDD from `continue-on-error: true → false`
- Each flip preceded by HITL Gate-1 authorization (per kickoff Gate-1 cadence)
- Estimate ~3-5h focused / 0.5-1 day
- Entry: Stage A + Stage B clean ✓ (now satisfied)
- HITL Gate-1 per gate flip (3-4 expected toggles)
