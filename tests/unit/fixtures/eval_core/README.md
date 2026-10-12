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
references explicitly say unit-condition-only. They are never saved as actual
runtime reports or used as baselines. The delivered replay report uses
`synthetic_fixture`, official metrics null and `baseline_eligible=false`.

JSONL is pinned to LF locally because manifest hashes bind raw bytes. The core
accepts explicit bytes and performs no file or network access. Future CLI path,
secret-file, output-collision and reparse-point protections remain deferred.
