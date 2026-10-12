---
type: evidence
subtype: report
capability: data-agent.evaluation
covered_reqs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006]
created: 2026-10-12
owner: ranzuozhou
source_kind: synthetic_fixture
---

# Evidence: #582 local CLI software acceptance

## Version and authority

Owner requested implementation of the Agent-first plan, including the local CLI,
its declared `main` contract, file-boundary tests and offline validation. Codex
implemented this delegated unit in `feature/582-offline-eval-cli`, based on
`develop@5b8833c523f4401de7b70deb5a82b908f3a9c763`. The candidate is uncommitted;
that base SHA alone does not identify the tested changes. Implementation-side
verification here does not substitute for the coordinator's independent review,
Owner acceptance, repository approval or publish authorization.

The tested source/test/fixture digest is
`2db977bbfe6ae39399106e323354129fc6434e66c27b3b68f781f928803cbfe0`.
Compute SHA-256 of each of the six `src/mj_agent/evaluation/*.py` files, three
evaluation test modules, seven `tests/unit/fixtures/eval_core/*.json*` inputs,
and the three files under `capabilities/data-agent/evaluation/contracts/`.
Sort repository-relative paths, use `/`, concatenate `path:sha256\n`, then
SHA-256 those UTF-8 bytes. Other documentation is outside this behavioral artifact
digest; CI must bind its actual candidate/head/base separately after publication.

Windows local environment: Python 3.13.5, pytest 9.0.3, pytest-bdd 8.1.0,
pydantic 2.13.3 and sqlglot 30.7.0, from this worktree's frozen environment.
No dependency declarations or lockfile were changed.

## Red / green and acceptance mapping

Initial hardened test collection was rejected because a top-level parameterized
rejection example literally named `.env`. The original diagnostic was
`automatic pytest input may not read a .env file`; no secret was read. The
rejection-only exact-name case was moved into its deferred test function, before
any file open, which satisfies the existing import-time boundary. Neither the
checker, runner, permissions nor execution command was bypassed or changed.

RED then observed `ModuleNotFoundError: No module named 'mj_agent.evaluation.runner'`
in `test_public_cli_signature`. After implementing the file adapter, GREEN was
145 passing tests: 64 existing core units, 72 CLI units and 9 BDD scenarios.
The original six BDD scenarios remain; three new scenarios cover stable reports,
secret rejection before reading, and preservation of existing output.

Independent review then found Windows trailing-dot/space aliases accepted by
the raw name matcher. No secret was created or read. A before-metadata regression
for `credentials.json ` observed RED because `_inspect` reached the alias;
the root fix rejects every such Windows component before metadata/secret matching,
while preserving ordinary `.`/`..` syntax. Fourteen alias cases and one positive
parent-syntax case passed; the final complete run is 145 PASS. The earlier
130-test console is retained as historical pre-fix evidence, not the final claim.

| Acceptance | Observed result |
|---|---|
| AC-1 identity and complete suite | CLI/core equality, fixed 22-case expected labels, planned=judged=22; missing reviews preserve gaps |
| AC-2 supported checks | Original 32-class AST/trajectory/semantic coverage retained and rerun; judges.py unchanged |
| AC-3 first attempt and repair | Original first-failure/repair evidence tests rerun; no rule changes |
| AC-4 report and regression | UTF-8/LF, sorted JSON keys, Markdown equality, byte-identical repeated outputs; exact threshold and compatibility tests retained |
| AC-5 incomplete/unmeasured | Synthetic report remains SELFTEST_ONLY, metric=null, baseline_eligible=false; no missing-item denominator reduction |
| AC-6 baseline validity | Existing fixed baseline/self-consistency coverage retained; actual-branch CLI conditions are explicitly fictional |
| AC-7 offline file boundary | URL/UNC/Windows mapped-drive, secret, symbolic/reparse ancestor, nonregular/missing/oversize input and output-collision rejection; IO errors are safe code 2 |
| AC-8 use and evidence | Implemented main signature/module entry, declared contracts, RUNBOOK/trace/Plan/INDEX synchronized; no Owner final acceptance recorded |

Real child processes exercised codes 0, 2, 3, 4, 5 and 6. Codes 0/4/5 and
actual red-line code 6 used fictional, named unit conditions, not sampled actual
observations. The fixed synthetic process returned 3, as expected. The adapter
returns the core's unchanged classification; no new soft-regression or latency
sampling was invented to produce 7.

## Fresh verification and reproduction

| Command | Actual result |
|---|---|
| `uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_runner.py tests/unit/test_eval_core.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -v` | exit 0, 145 passed; 18 third-party Gherkin deprecation warnings; [actual console](../bdd/2026-10-12_cli_windows_alias_pytest.txt) |
| `uv run --frozen --no-sync ruff check src/mj_agent/evaluation tests/unit/test_eval_runner.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py` | exit 0, all checks passed |
| `uv run --frozen --no-sync mypy src/mj_agent` | exit 0, 54 source files, no issues |
| capability schema / trace / generic contracts / Python public contract | G1 1P, G2 1P, G3 1P, V1 3P/2 informational WARN/0F; main has a real source/signature anchor |
| BDD scenario trace / BDD acceptance / capability index | G19 9P/0W/0F, G21 9P/0W/0F, index matches 7 specs; structure checks do not substitute for console execution |
| canonical frontmatter / whitespace | 151 canonical docs PASS (capability-package outside that scan); git diff --check PASS |

The generic contract check initially raised its existing `relative_to` ValueError
when given a relative capability path; the documented absolute capability path
passed without checker edits. An initial wrong frontmatter script path returned
file-not-found; the discovered `scripts/check_frontmatter.py` passed. These were
command/path errors, not permission refusals. Python public-invariant WARNs remain
informational in default mode; no strict zero-warning claim is made.

For a fixed synthetic replay, use a fresh ordinary output directory:

```text
uv run --frozen --no-sync python -m mj_agent.evaluation.runner --eval-config tests/unit/fixtures/eval_core/config.json --dataset tests/unit/fixtures/eval_core/dataset.jsonl --observations tests/unit/fixtures/eval_core/observations.jsonl --manifest tests/unit/fixtures/eval_core/manifest.json --reference tests/unit/fixtures/eval_core/reference.json --reviews tests/unit/fixtures/eval_core/reviews.jsonl --output-dir <new-local-directory>
```

Expect process exit 3, `report.json` and `report.md`, planned=judged=22,
SELFTEST_ONLY, metrics=null and baseline_eligible=false. Repeating with identical
inputs in another new directory yields identical bytes. Existing report names,
including directories or links, are never overwritten.

## Limits, recovery and state

The ordinary input/output directories must be under the caller's exclusive
control. Ancestor checks, descriptor identity checks, bounded reads and exclusive
report creation are not a hostile concurrent-filesystem sandbox. POSIX mount
locality and malicious concurrent ancestor replacement are not verified.

A write failure can leave a partial report pair. The actual process returns 2,
which takes precedence over the report's evaluation classification. Preserve
those files, inspect the completed side effects, and retry in a new directory;
the adapter never auto-deletes or overwrites. It does not claim an atomic
two-file transaction or durability after a power failure.

No runtime imports/settings, secret access, SQL execution, network, LLM, database,
actual sampling, real provenance/sanitization assurance, deployed behavior or
recovery exercise was performed. Synthetic and fictional actual-branch tests
are software evidence only. Historical core reports retain their historical
CLI deferral text; current generated reports remove that stale limitation.
No commit/push/PR/merge or Issue-state change was made by this delegate.
The capability remains idea, last_verified=null and Plan active.

Related: [design](../../design.md), [CLI contract](../../contracts/cli.contract.yml),
[core/public API contract](../../contracts/python.contract.yml),
[RUNBOOK](../../runbook.md), [tasks](../../tasks.md).
