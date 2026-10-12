---
type: evidence
subtype: report
capability: data-agent.evaluation
covered_reqs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006]
created: 2026-10-12
owner: ranzuozhou
source_kind: synthetic_fixture
---

# Evidence: #587 public offline core contract alignment

## §1 Context

Owner explicitly approved the reviewed proposal based on
3dd6b6b3122858eb9abd24c1bc9e7ae13442f684: publish ReplayInputs and replay(inputs),
bind the declared Python contract to their implemented source, retain CLI/actual
deferral, migrate and verify existing tests, synchronize docs, commit and ordinary
dual push, update #587 and mark Ready only after CI passes. No runtime, gate,
ruleset, live, merge or Issue-state change is authorized.

The reviewer answer was “不指定”. No review request is sent; no approval is fabricated.
Repository rules still require a real effective Approve after the last push.
Codex implements and verifies this change; no subagents or human synthetic labels.

## §2 Method

The public dataclass preserves seven bytes fields, two b'' defaults and frozen
behavior. _Inputs remains a compatibility alias. replay delegates to the existing
private implementation; judges, schema rules, compatibility/thresholds, fixtures
and the report format are unchanged. The declared surface now has two real source
anchors, with all six behavioral/safety invariants retained. main remains solely
a SPEC/task candidate, not an implemented public export.

Both tests migrated to the public API first. The existing hardened runner returned
RED with two ImportErrors for missing replay. After implementation, the original
69 tests passed. One additional public-contract test verifies fixed field names,
types/defaults, immutability and the published signature, for 70 total tests.
Import sorting and the test's mutation syntax were corrected according to ruff.

## §3 Result

| Command / condition | Actual result | Scope |
|---|---|---|
| Hardened pytest, two evaluation files | 70 passed, 12 dependency warnings | 64 unit + 6 BDD, synthetic only |
| Ruff whole repository | PASS | No source/test lint findings |
| mypy src/mj_agent | PASS, 53 files | New API and existing sources |
| check_python_contracts.py --all | exit0; 11P/12W/0F | Same default mode as blocking CI V1 |
| public_invariants warning | Retained | Informational checker warning; strict mode is not claimed green |
| Current canonical public replay | Matches saved JSON exactly | Official metrics null, baseline_eligible=false |

The old runner-file-not-found failure is resolved by the Owner-approved real API
contract. No checker suppression, empty module, removed safety invariant or CI
configuration change is used. Prior reports are retained as historical evidence.

The full remote workflow result belongs to the new PR head and must be observed
after push; local PASS is not a substitute. CLI paths/output protection/process
exits, actual sampling/source authenticity, latency and live services remain untested.
This change does not complete all #582 acceptance or remove the approval requirement.

## §4 Related Artifacts

- [Python contract](../../contracts/python.contract.yml)
- [Public API implementation](../../../../../src/mj_agent/evaluation/core.py)
- [Input dataclass](../../../../../src/mj_agent/evaluation/schema.py)
- [Unit/public contract tests](../../../../../tests/unit/test_eval_core.py)
- [BDD bindings](../../../../../tests/bdd/data_agent/evaluation/test_evaluation_bdd.py)
- [Public API console evidence](../bdd/2026-10-12_public_core_pytest.txt)
- [Design and decision](../../design.md), [tasks](../../tasks.md), [runbook](../../runbook.md)
- [PR #587](https://github.com/MJ-AgentLab/mj-agent/pull/587)
