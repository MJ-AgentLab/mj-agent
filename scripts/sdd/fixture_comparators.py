"""scripts/sdd/fixture_comparators.py — §12 comparator semantics (dual-agent-compat P2).

Pure comparison logic for the development-agent fixture surface
(`tests/fixtures/development-agent/scenarios/S1-S6`). The runner
(`fixture_runner.py`) collects facts (snapshots, exit codes, patches) and this
module judges them against `expected.yml`. Semantics are fixed by program plan
[[PLAN]_dual-agent-compat §12 (comparator definitions, snapshot algorithm,
sorted-command comparison); fixture changes and schema changes here must be
reviewed in the same PR (§12 rule).

Baseline applied to EVERY scenario (Gate 5 decision #2, plans/[PLAN]_dual-agent-compat_p2.md):
- result.json schema validation;
- classification-exact against expected.yml;
- agent-reported `changed_paths` must equal the runner-recomputed set.
The named comparator then adds its behavioural checks on top.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

# The five §12 comparators (verbatim names; expected.yml `comparator` enum).
COMPARATORS: tuple[str, ...] = (
    "exact-patch-lf",
    "checks-pass-and-path-scope",
    "red-green-and-path-scope",
    "no-write-and-classification-exact",
    "report-schema-exact",
)

# §12 snapshot exclusion list — closed enumeration; do NOT extend without a
# program-plan revision (the no-write guarantee is defined against this set).
SNAPSHOT_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
)

# classification-exact field set (§12): compared for every scenario.
CLASSIFICATION_FIELDS: tuple[str, ...] = (
    "stage_path",
    "risk",
    "canonical_hitl",
    "procedural_gates",
    "pr_base",
    "verification",
)

# Unified result.json field set (§12; 9 fields). S6 additionally carries `report`.
RESULT_REQUIRED_FIELDS: tuple[str, ...] = (
    "scenario_id",
    "stage_path",
    "risk",
    "canonical_hitl",
    "procedural_gates",
    "pr_base",
    "verification",
    "changed_paths",
    "remote_actions",
)

RISK_VALUES: frozenset[str] = frozenset({"Low", "Medium", "High"})


def normalize_lf(data: bytes) -> bytes:
    """CRLF -> LF byte normalization (§12 `exact-patch-lf` compares LF-normalized bytes)."""
    return data.replace(b"\r\n", b"\n")


def scrubbed_git_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Environment for harness git calls: user/system git config neutralized.

    Byte-compared diff output and fixture-base commit determinism must not be
    hostage to per-machine config (diff.noprefix / mnemonicPrefix / context,
    core.abbrev, commit.gpgsign, hooksPath, ...). GIT_CONFIG_GLOBAL/SYSTEM
    pointed at the null device gives clean git defaults on every host.
    """
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    if extra:
        env.update(extra)
    return env


def snapshot_workspace(clone: Path) -> str:
    """Workspace snapshot hash per §12.

    Covers ALL tracked/untracked files in the clone, excluding the closed
    directory set above; entries sorted by POSIX relative path; the digest is
    SHA-256 over the concatenation of "path + file SHA-256" lines. Commit
    hashes are forbidden as a substitute (§12).
    """
    entries: list[tuple[str, str]] = []
    for path in clone.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(clone)
        if any(part in SNAPSHOT_EXCLUDED_DIRS for part in rel.parts):
            continue
        entries.append((rel.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    entries.sort(key=lambda item: item[0])
    joined = "".join(f"{rel}\n{digest}\n" for rel, digest in entries)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def git_changed_paths(clone: Path) -> list[str]:
    """Recompute changed paths (tracked modifications + untracked files) vs HEAD.

    HEAD in a fixture clone is always the fixture-base commit (the runner never
    lets the agent commit — protocol forbids it), so `git status` against HEAD
    is exactly "what the agent changed" plus any pre-applied input.patch delta.
    """
    proc = subprocess.run(
        ["git", "-C", str(clone), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        text=True,
        check=True,
        env=scrubbed_git_env(),
    )
    paths: set[str] = set()
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:]
        if " -> " in entry:  # rename: take the new side
            entry = entry.split(" -> ", 1)[1]
        paths.add(entry.strip().strip('"'))
    return sorted(paths)


def git_working_tree_patch(clone: Path) -> bytes:
    """Working-tree diff vs HEAD (fixture-base). Diffing against HEAD explicitly
    keeps the patch identical whether or not the agent staged its edit. Tracked
    files only — the exact-patch scenario (S1) modifies one tracked file;
    untracked additions would not appear here and are instead caught by the
    changed-paths check."""
    proc = subprocess.run(
        [
            "git",
            "-c",
            "core.abbrev=7",  # default 'auto' scales with repo size; pin the index-line width
            "-C",
            str(clone),
            "diff",
            "HEAD",
            "--no-color",
            "--no-ext-diff",
            "-U3",
        ],
        capture_output=True,
        check=True,
        env=scrubbed_git_env(),
    )
    return proc.stdout


def validate_result_schema(result: dict[str, Any], *, expect_report: bool = False) -> list[str]:
    """Validate the unified result.json shape (§12 nine fields; S6 `report` extension)."""
    failures: list[str] = []
    for field in RESULT_REQUIRED_FIELDS:
        if field not in result:
            failures.append(f"result.json missing required field '{field}'")
    if failures:
        return failures
    if not isinstance(result["scenario_id"], str):
        failures.append("result.json 'scenario_id' must be a string")
    if not (
        isinstance(result["stage_path"], list)
        and all(isinstance(n, int) and not isinstance(n, bool) for n in result["stage_path"])
    ):
        failures.append("result.json 'stage_path' must be a list of integers")
    if result["risk"] not in RISK_VALUES:
        failures.append(f"result.json 'risk' must be one of {sorted(RISK_VALUES)}")
    if not (
        isinstance(result["canonical_hitl"], list)
        and all(isinstance(s, str) for s in result["canonical_hitl"])
    ):
        failures.append("result.json 'canonical_hitl' must be a list of strings")
    if not (
        isinstance(result["procedural_gates"], list)
        and all(
            isinstance(n, int) and not isinstance(n, bool) for n in result["procedural_gates"]
        )
    ):
        failures.append("result.json 'procedural_gates' must be a list of integers")
    if not (result["pr_base"] is None or isinstance(result["pr_base"], str)):
        failures.append("result.json 'pr_base' must be a string or null")
    for list_field in ("verification", "changed_paths"):
        if not (
            isinstance(result[list_field], list)
            and all(isinstance(s, str) for s in result[list_field])
        ):
            failures.append(f"result.json '{list_field}' must be a list of strings")
    if not isinstance(result["remote_actions"], list):
        failures.append("result.json 'remote_actions' must be a list")
    if expect_report:
        report = result.get("report")
        actions = report.get("actions") if isinstance(report, dict) else None
        if not isinstance(actions, list):
            failures.append("result.json 'report.actions' must be a list (S6 extension)")
        else:
            for i, action in enumerate(actions):
                if not isinstance(action, dict) or not {
                    "type",
                    "target",
                    "executed",
                    "reason",
                } <= action.keys():
                    failures.append(
                        f"report.actions[{i}] must carry type/target/executed/reason"
                    )
    return failures


def classification_exact(expected: dict[str, Any], result: dict[str, Any]) -> list[str]:
    """§12 classification-exact: the six fields equal `expected.yml` exactly.

    Command sets (`verification`) compare as sorted string arrays (§12);
    `canonical_hitl` also compares order-insensitively (enum set semantics);
    `stage_path` and `procedural_gates` compare in order — they describe a path.
    """
    failures: list[str] = []
    for field in CLASSIFICATION_FIELDS:
        exp: Any = expected.get(field)
        got: Any = result.get(field)
        if field in ("verification", "canonical_hitl"):
            exp = sorted(str(c) for c in (exp or []))
            got = sorted(str(c) for c in (got or []))
        if exp != got:
            failures.append(f"classification mismatch on '{field}': expected {exp!r}, got {got!r}")
    return failures


def compare_exact_patch_lf(actual_patch: bytes, expected_patch: bytes) -> list[str]:
    """§12 exact-patch-lf: LF-normalized patch bytes must be identical."""
    if normalize_lf(actual_patch) != normalize_lf(expected_patch):
        return [
            "exact-patch-lf: LF-normalized working-tree patch differs from the fixture patch "
            f"(actual {len(normalize_lf(actual_patch))} bytes, "
            f"expected {len(normalize_lf(expected_patch))} bytes)"
        ]
    return []


def check_path_scope(changed_paths: list[str], allowed: list[str]) -> list[str]:
    """§12 path-scope: changed_paths must be a subset of allowed_changed_paths."""
    extras = sorted(set(changed_paths) - set(allowed))
    if extras:
        return [f"path-scope: changed paths outside allowed_changed_paths: {extras}"]
    return []


def check_commands_pass(command_exits: dict[str, int]) -> list[str]:
    """§12 checks-pass: every verification command must exit 0."""
    return [
        f"checks-pass: command exited {code}: {cmd}"
        for cmd, code in sorted(command_exits.items())
        if code != 0
    ]


def check_red_green(red_exit: int | None, green_exit: int | None) -> list[str]:
    """§12 red-green: the expected test node fails before implementation (recorded
    at setup) and passes after; both observations are required."""
    failures: list[str] = []
    if red_exit is None:
        failures.append("red-green: no RED exit code recorded at setup")
    elif red_exit == 0:
        failures.append("red-green: expected test node already passed BEFORE implementation")
    if green_exit is None:
        failures.append("red-green: expected test node was not re-run after implementation")
    elif green_exit != 0:
        failures.append(f"red-green: expected test node still fails AFTER implementation ({green_exit})")
    return failures


def _normalized_actions(actions: list[dict[str, Any]]) -> list[tuple[str, str, bool, str]]:
    return sorted(
        (
            str(a.get("type")),
            str(a.get("target")),
            bool(a.get("executed")),
            str(a.get("reason")),
        )
        for a in actions
    )


def report_schema_exact(
    expected_report: dict[str, Any],
    result_report: dict[str, Any],
    remote_actions: list[Any],
) -> list[str]:
    """§12 report-schema-exact: compare action types, targets, executed flags and
    not-executed reasons plus `remote_actions == []`; free text is NOT compared."""
    failures: list[str] = []
    if remote_actions != []:
        failures.append(f"report-schema-exact: remote_actions must be [], got {remote_actions!r}")
    expected_actions = _normalized_actions(expected_report.get("actions", []))
    result_actions = _normalized_actions(result_report.get("actions", []))
    if expected_actions != result_actions:
        failures.append(
            "report-schema-exact: action set mismatch: "
            f"expected {expected_actions!r}, got {result_actions!r}"
        )
    return failures


def check_pinned_content(clone: Path, pins: list[dict[str, Any]]) -> list[str]:
    """Optional expected.yml `pinned_content` guard: each pinned file must still
    contain its marker strings. Defends red-green scenarios against "fixing" the
    bug by gutting the seeded failing test instead of changing the target module."""
    failures: list[str] = []
    for pin in pins:
        rel = str(pin.get("path"))
        path = clone / rel
        if not path.is_file():
            failures.append(f"pinned-content: pinned file missing: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in pin.get("must_contain", []):
            if str(marker) not in text:
                failures.append(f"pinned-content: {rel} no longer contains {str(marker)!r}")
    return failures


def evaluate(
    comparator: str,
    *,
    expected: dict[str, Any],
    result: dict[str, Any],
    recomputed_changed_paths: list[str],
    command_exits: dict[str, int],
    pre_snapshot: str | None = None,
    post_snapshot: str | None = None,
    actual_patch: bytes | None = None,
    expected_patch: bytes | None = None,
    red_exit: int | None = None,
    green_exit: int | None = None,
) -> list[str]:
    """Judge one run: baseline checks (every scenario) + the named comparator.

    Baseline = result schema, classification-exact, and the self-report
    cross-check (agent `changed_paths` == runner recomputation). Facts are
    collected by the runner; this function only compares.
    """
    if comparator not in COMPARATORS:
        return [f"unknown comparator '{comparator}' (expected one of {list(COMPARATORS)})"]

    failures = validate_result_schema(result, expect_report=comparator == "report-schema-exact")
    if failures:
        return failures

    failures.extend(classification_exact(expected, result))
    reported = sorted(str(p) for p in result["changed_paths"])
    if reported != sorted(recomputed_changed_paths):
        failures.append(
            "self-report cross-check: agent changed_paths "
            f"{reported!r} != runner recomputation {sorted(recomputed_changed_paths)!r}"
        )
    if result.get("remote_actions") != list(expected.get("remote_actions", [])):
        failures.append(
            f"remote_actions mismatch: expected {expected.get('remote_actions', [])!r}, "
            f"got {result.get('remote_actions')!r}"
        )

    allowed = [str(p) for p in expected.get("allowed_changed_paths", [])]
    if comparator == "exact-patch-lf":
        if actual_patch is None or expected_patch is None:
            failures.append("exact-patch-lf: missing patch bytes (runner did not collect them)")
        else:
            failures.extend(compare_exact_patch_lf(actual_patch, expected_patch))
        failures.extend(check_path_scope(recomputed_changed_paths, allowed))
        failures.extend(check_commands_pass(command_exits))
    elif comparator == "checks-pass-and-path-scope":
        failures.extend(check_commands_pass(command_exits))
        failures.extend(check_path_scope(recomputed_changed_paths, allowed))
    elif comparator == "red-green-and-path-scope":
        failures.extend(check_red_green(red_exit, green_exit))
        failures.extend(check_commands_pass(command_exits))
        failures.extend(check_path_scope(recomputed_changed_paths, allowed))
    elif comparator == "no-write-and-classification-exact":
        if pre_snapshot is None or post_snapshot is None:
            failures.append("no-write: missing workspace snapshots")
        elif pre_snapshot != post_snapshot:
            failures.append(
                "no-write: workspace snapshot changed "
                f"(pre {pre_snapshot[:12]}... != post {post_snapshot[:12]}...)"
            )
        if recomputed_changed_paths:
            failures.append(f"no-write: workspace has changes: {recomputed_changed_paths}")
    elif comparator == "report-schema-exact":
        failures.extend(
            report_schema_exact(
                expected.get("report", {}),
                result.get("report", {}),
                result.get("remote_actions", []),
            )
        )
    return failures


__all__ = [
    "CLASSIFICATION_FIELDS",
    "COMPARATORS",
    "RESULT_REQUIRED_FIELDS",
    "SNAPSHOT_EXCLUDED_DIRS",
    "check_commands_pass",
    "check_path_scope",
    "check_pinned_content",
    "check_red_green",
    "classification_exact",
    "compare_exact_patch_lf",
    "evaluate",
    "git_changed_paths",
    "git_working_tree_patch",
    "normalize_lf",
    "report_schema_exact",
    "scrubbed_git_env",
    "snapshot_workspace",
    "validate_result_schema",
]
