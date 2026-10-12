# Offline core fixtures

Every observation, target identity, model identity and role record here is synthetic.
Nothing was sampled from an LLM, database or running application. The 22 dataset
cases reproduce the existing first-turn-time-predicate fixture; the original is unchanged.

`expected.json` contains fixed labels authored before implementation. Domain/Prompt
labels were prepared by Codex, then checked in a separate SWE pass from the SQL,
trajectory, reply and frozen rules. This is same-agent role simulation, not separate
human or agent signatures. `reviews.jsonl` holds the 34 final, hash-bound records.

The fixture time is 2026-10-12 in Asia/Taipei. Daily default lower bound is
2026-09-12; monthly default lower bound is 2026-07-01. HP-03 permits only
daily/30d or monthly/3m. Explicit windows are in `reference.json`.
Eight explicit-window/signal reply descriptions were corrected during review;
observation hashes were rebound and fixed expected labels were retained.

Negative labels in the tests are fixed assertions: projection-only and OR TRUE
fail, fact-side filtering cannot be replaced by dimension filtering, unknown SQL
expressions require review, and a first failure cannot be hidden by repair.
Bound negative role verdicts fail even if AST checks pass.

Tests also construct fictional `runtime_observation` conditions solely to exercise
measured, zero-value, regression and hard-failure branches. Their source/approval
references explicitly say unit-condition-only. Those actual/baseline branches stay
in core tests; the CLI refuses runtime_observation after reading only manifest
and has no baseline option. CLI outputs remain synthetic software-test reports.
The delivered replay report uses
`synthetic_fixture`, official metrics null and `baseline_eligible=false`.

JSONL is pinned to LF locally because manifest hashes bind raw bytes. The core
accepts explicit bytes and performs no file or network access. The separate CLI
now implements local-path, secret-file, output-collision and reparse-point checks,
including rejection of Windows trailing-dot/space aliases before reading.
The CLI requires --synthetic-fixture, an absolute injectable repo_root (default cwd),
and a new output directory whose parent exists. Aliases, traversal, devices, networks,
reparse points, multi-link inputs and path replacement cannot bypass handle guards.
Windows fixed NTFS is locally tested; Linux/macOS native IO is explicitly deferred, unsupported guards
fail closed. ../eval_cli/expected.json is a fixed, manually authored CLI expectation.
Actual file entry, baseline CLI inputs, sampling, provenance authenticity and live
runtime acceptance remain deferred/unverified. Historical core reports retain their
CLI_ENTRY_DEFERRED labels; current core uses CORE_API_NO_FILE_IO (bytes change).
