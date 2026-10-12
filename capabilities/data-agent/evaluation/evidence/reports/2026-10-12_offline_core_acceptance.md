---
type: evidence
subtype: report
capability: data-agent.evaluation
covered_reqs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006]
created: 2026-10-12
owner: ranzuozhou
source_kind: synthetic_fixture
---

# Evidence: #582 offline core delivery and synthetic acceptance

## §1 Context

Owner explicitly selected “授权离线核心编码（推荐）”: independent evaluation
core, necessary offline tests, Agent synthetic role acceptance and regression report.
CLI and actual entry remain deferred. Existing runtime, original dataset, live EVAL,
commit, push, PR and Issue states are outside this delivery.

Codex implemented on feature/582-offline-eval-core from
develop@c91d3151d14388f3caab689e5045344c6a134196. This report initially captured the
uncommitted core-delivery phase; subsequent publication preparation committed the
core/tests as 007820e77e0e22ec36ee8d1f99d70de95f4595c8 under explicit Owner authorization.
No subagents were dispatched. The earlier develop drafts and other local contents
were preserved. The capability stays idea, last_verified=null until its full
declared interface and acceptance are complete.

## §2 Method

New [core](../../../../../src/mj_agent/evaluation/core.py), schema, judges and
report modules consume explicit in-memory bytes. They depend only on standard
library and already locked pydantic/sqlglot, with no application settings, tools,
LLM/DB clients or file/network IO. The private API is not a new frozen public contract.

The 22 [fixed fixtures](../../../../../tests/unit/fixtures/eval_core/README.md)
and expected labels preceded implementation. Codex simulated Domain/Prompt labels
and then independently checked raw SQL, trajectory, reply and rules in a separate
SWE pass. This is same-agent role simulation, not independent human/subagent signatures.
Thirty-four final review records bind observation/config/reference hashes and rule
revision. Eight explicit-window/signal reply descriptions were corrected; fixed
expected labels were retained and review digests rebound.

Initial RED: ModuleNotFoundError for mj_agent.evaluation. Subsequent fixed negative
expectations exposed date overflow, a single blocked call misclassified as repair,
inconsistent baseline acceptance, malformed check types bypassed when observations
were absent, and a missing error code mistaken for proof of a specific error being absent. Final negatives also reproduced date-range overflow, exponent-form
non-finite JSON and default source incorrectly using a user-window reference; all
were corrected before the final 69-test run. Each was reproduced before correction. Refactoring consolidated check
type validation and manifest compatibility-key construction, then reran all tests.

BDD plugin binding was rejected by the existing offline boundary checker. The tests
were corrected to the repository's existing per-capability test-module layout;
no boundary checker, runner, permissions or CI configuration was changed.

## §3 Result

| Verification | Observed result | Meaning |
|---|---|---|
| Hardened offline pytest, two new test files | 69 passed: 63 unit + 6 BDD | Core acceptance on synthetic inputs |
| Whole-repository ruff | PASS | No lint findings |
| mypy src/mj_agent | PASS, 53 source files | Existing and new source type checks |
| Synthetic replay, repeated canonical bytes | Identical; 22/22 complete and PASS | Judge selftest only |
| Runtime metric / latency | null / NOT_MEASURED | No actual measurement |
| Baseline eligibility / regression | false / NOT_EVALUATED | No runtime baseline produced |
| Classification | 3, SELFTEST_ONLY | A returned report value; CLI process exit is deferred |

[Verbose test output](../bdd/2026-10-12_core_pytest.txt) records the actual test run;
[BDD evidence](../bdd/2026-10-12_core_scenarios_pass.md) binds the frozen six scenarios.
Dependency warnings: 12 existing gherkin deprecation warnings; no failing tests or skips.

Independent synthetic counterchecks include:

| Condition | Fixed conclusion |
|---|---|
| Daily30d / monthly3m | Exact lower anchors; HP-03 must preserve the period/window pair |
| Projection-only date, OR TRUE, dimension-only filtering | FAIL |
| Unknown scope, date overflow or stale semantic review | REVIEW_REQUIRED |
| First failure followed by repair | First failure and both attempts preserved; FAIL |
| Single rejected SQL without later SQL | Not labelled a repair loop; separate required checks still apply |
| COUNT(*) / t.* | COUNT(*) exempt; t.* rejected |
| Known FAIL with missing review | FAIL with judgment_complete=false |
| Missing one/all observations | Keep all22 cases; metrics null, no smaller denominator |
| Bound negative role verdict / reply keyword alone | FAIL / REVIEW_REQUIRED |
| Red-line failure without baseline | Hard-failure branch preserved even with suite gaps |
| Complete fictional zero-value condition | 0/22 is representable; not confused with a placeholder |
| 21/22 versus22/22, drop exactly0.03 | Hard regression; exact Fraction comparison |
| Hash/model/time/target/commit/sanitization differences | INCOMPATIBLE_BASELINE, no delta |
| Missing checks, contradictory counts/status/binding | Invalid baseline rejected |

Tests for measured/actual-source branches use fictional unit conditions whose source
and approval strings explicitly state that they are not runtime evidence or authorization.
No such report is saved or accepted as an actual baseline. The core checks provenance
structure and supplied review binding; it cannot establish source authenticity or
authorization validity from a reference string.

The delivered [JSON](2026-10-12_synthetic_replay.json) and
[Markdown](2026-10-12_synthetic_replay.md) report use synthetic_fixture.
JSON SHA-256: 7c5047a7520ba216aef1d31dd2dcc742718baee2d1c7d1fb93aa863db501e999.
Markdown SHA-256: 9b8206952feb56ac65a21cee2433345331ff6360de61f1c799f3143daa7350dd.

Original dataset SHA-256 remains
01703f365dec13b091f00070ffafdcd93a4a8c269089fce8ab2483f4570b58a3;
catalog remains29f93fd5362884c84745f965b8863c8d964fa6fceae7fcae437b28304810342e.
No existing source, runtime skill/prompt, catalog, policy, native guard or CI file was edited.

### Deferred acceptance

runner.py/main remains absent, so Python public-contract checking still fails at
that declared anchor. No shim or contract relaxation was added. File paths, URL/UNC,
secret-file/reparse rejection, output collision protection, file emission and CLI
process exits have no implementation or end-to-end evidence. Actual sampling,
provenance authenticity, real semantic audits, latency, live services and remote CI
were not run. This is core delivery, not full #582 acceptance or Issue closure.

## §4 Related Artifacts

[Plan](../../../../../plans/[PLAN]_582_offline_eval_runner.md),
[design](../../design.md), [requirements](../../requirements.md),
[tasks](../../tasks.md), [runbook](../../runbook.md), [trace](../../trace.yml).
All related Issue states and scopes are preserved; no external update was published.

### Final structural and documentation verification

Executed from this worktree with the existing Python3.13.5 environment,
UTF-8 and bytecode disabled; no dependency installation or synchronization.

| Command | Exit and observed result |
|---|---|
| scripts/sdd/check_capability_schema.py --capability capabilities/data-agent/evaluation --strict | 0; 1P/0W/0F |
| scripts/sdd/check_traceability.py --capability <absolute capability> --strict | 0; 1P/0W/0F |
| scripts/sdd/check_contracts.py --capability <absolute capability> --strict | 0; 1P/0W/0F |
| scripts/sdd/check_bdd_scenario_trace.py --capability capabilities/data-agent/evaluation --scope full --strict | 0; 6P/0W/0F |
| scripts/sdd/check_bdd_acceptance.py --capability capabilities/data-agent/evaluation --strict | 0; 6P/0W/0F, executed BDD evidence primary path |
| scripts/sdd/check_python_contracts.py --capability capabilities/data-agent/evaluation --strict | 1; runner module not found, deferred public CLI anchor |
| scripts/check_frontmatter.py | 0; 151 canonical docs |
| scripts/check_wikilinks.py | 0; archive scope and five root files |

G1/G2/G3/G19 validate structure; the six BDD scenario executions are separately
recorded. Capability-package metadata and explicit links require their own static
check because the canonical frontmatter scan excludes capabilities/.

Final ruff and mypy checks were rerun after these corrections and passed. G9 index check passed (7 specs). Package metadata and explicit links passed for11 Markdown files; 35 tracked/untracked files all belong to the authorized scope. Link extraction reused the existing checker with document-relative Markdown/root-or-document wikilink resolution; its default root-file-only resolver cannot directly validate nested documents. Current canonical replay exactly matches the delivered JSON, and both declared contracts match the approved develop drafts. CLI main remains absent.

Publication preparation: console evidence retains actual test names/results and warnings, with only local worktree/venv paths redacted. Core/report input hashes and outputs are unchanged. Owner subsequently authorized commit, ordinary dual push and Draft PR; earlier no-PR statements describe the core-delivery phase.
