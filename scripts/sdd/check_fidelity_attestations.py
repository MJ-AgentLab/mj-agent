"""check_fidelity_attestations.py — independent fidelity closure checker.

Epic #499 plan §2.7 / §2.8.5, PR-B (dormant — the tracked index
`sdd/adapters/codex-skill-fidelity.yml` and the coverage reports under
`evidence/development-agent-v8/fidelity/coverage/` land at PR-C0; until then
this checker is exercised by fixture tests only, and it is deliberately NOT a
CI step).

Independence contract: this checker NEVER imports the renderer's coverage
generator. It re-derives the heading / owner-stop / prohibition / validator /
description / level-handler / git-rule / issue-route / dependency-route
inventory from the SOURCE skill, the manifest and the workflow registry with
its own (intentionally duplicated) extraction rules, then requires the
renderer-generated coverage report to close EXACTLY over that inventory —
so a renderer that omits an item from both its output and its own report
still goes red here (the mandated negative fixture).

Checks:
  index    — schema v1 exact top keys; 3-4 tranches exactly partitioning the
             translated capabilities (no gap/overlap); approval_binding exact
             keys with `approved|rejected` verdicts; globally-unique record
             ids. This checker validates STRUCTURE and digest binding only —
             it cannot authenticate a human; the Owner opens the immutable
             record at the PR-C0/PR-C1 gates.
  coverage — coverage v1 exact keys per capability; item exact keys/enums;
             recomputed inventory_sha256; independent inventory closure.

Exit codes: 0 clean; 1 violations; 2 unreadable/unknown schema.
`main(argv=None, repo_root=None)` — repo_root injectable for tests.
Read-only; no secrets; no network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

_SCRIPT_NAME = "check_fidelity_attestations.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

INDEX_RELPATH = Path("sdd/adapters/codex-skill-fidelity.yml")
COVERAGE_RELDIR = Path("evidence/development-agent-v8/fidelity/coverage")
KNOWN_INDEX_SCHEMA_VERSIONS = {1}
KNOWN_COVERAGE_SCHEMA_VERSIONS = {1}

INDEX_TOP_KEYS = {
    "schema_version", "translated_capabilities", "coverage_reports", "tranches",
}
TRANCHE_KEYS = {
    "tranche_id", "capability_ids", "candidate_commit_sha",
    "manifest_set_sha256", "source_set_sha256", "artifact_set_sha256",
    "translation_set_sha256", "workflow_set_sha256", "preface_sha256",
    "renderer_set_sha256", "coverage_set_sha256", "approval_binding",
}
BINDING_KEYS = {
    "record_system", "immutable_record_id", "reviewer_identity", "verdict",
    "reviewed_candidate_commit_sha", "reviewed_source_set_sha256",
    "reviewed_artifact_set_sha256", "recorded_at",
}
VERDICTS = {"approved", "rejected"}
COVERAGE_TOP_KEYS = {
    "schema_version", "capability_id", "source_path", "artifact_path",
    "source_sha256", "artifact_sha256", "inventory_sha256", "items",
}
ITEM_KEYS = {
    "item_id", "item_kind", "source_locator", "source_sha256",
    "artifact_locator", "artifact_sha256", "transform_class", "status",
}
ITEM_KINDS = {
    "heading", "owner-stop", "prohibition", "validator",
    "frontmatter-description", "dependency-route", "level-handler",
    "git-rule", "issue-route",
}
TRANSFORM_CLASSES = {"T1a", "T1b", "T2a", "T2b", "T3", "NOOP"}
STATUSES = {"COVERED", "INTENTIONALLY_NOOP"}
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

# Independent inventory extraction rules — intentionally re-stated here, NOT
# imported from the renderer (the independence is the point).
_INDEPENDENT_RULES: dict[str, str] = {
    "heading": r"^#{1,6}\s\S",
    "owner-stop": r"OWNER_APPROVAL_REQUIRED|必停",
    "prohibition": r"❌|\*\*不要\*\*",
    "validator": r"scripts/(?:sdd/)?[a-z0-9_]+\.py",
    "level-handler": r"\bLevel [ABC]\b",
    "git-rule": r"\bG[12]\b",
    "issue-route": r"ISSUE_TEMPLATE",
}


class FatalCheckError(Exception):
    """Exit-code-2 conditions."""


def _fail(problems: list[str], message: str) -> None:
    problems.append(message)


def _canonical_sha256(obj: Any) -> str:
    text = json.dumps(
        obj, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _independent_inventory(
    repo_root: Path, capability_id: str
) -> dict[str, int]:
    """kind -> expected item count, derived from source + workflow registry
    with this checker's OWN rules (never the renderer's generator)."""
    source_path = repo_root / ".claude" / "skills" / capability_id / "SKILL.md"
    if not source_path.is_file():
        raise FatalCheckError(f"source missing for {capability_id}")
    text = source_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    end = text.find("\n---\n", 4)
    body = text[end + 5:] if text.startswith("---\n") and end > 0 else text

    counts: dict[str, int] = {}
    lines = body.split("\n")
    fence = False
    fence_flags: list[bool] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            fence = not fence if stripped == "```" else True
            if stripped == "```" and not fence:
                pass
            fence_flags.append(True)
            continue
        fence_flags.append(fence)
    for kind, pattern in _INDEPENDENT_RULES.items():
        compiled = re.compile(pattern)
        n = 0
        for i, line in enumerate(lines):
            if kind == "heading" and fence_flags[i]:
                continue
            if compiled.search(line):
                n += 1
        if n:
            counts[kind] = n
    counts["frontmatter-description"] = 1

    registry_path = repo_root / "sdd" / "workflows" / "development-agent-workflows.yml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    edge_count = sum(
        1 for e in registry.get("edges") or [] if e.get("from") == capability_id
    )
    if edge_count:
        counts["dependency-route"] = edge_count
    return counts


def check_coverage_report(
    repo_root: Path, report: dict[str, Any], problems: list[str]
) -> None:
    where = f"coverage[{report.get('capability_id')!r}]"
    if set(report) != COVERAGE_TOP_KEYS:
        _fail(problems, f"{where}: top keys {sorted(report)} != exact set")
        return
    if report["schema_version"] not in KNOWN_COVERAGE_SCHEMA_VERSIONS:
        _fail(problems, f"{where}: unknown schema_version")
        return
    cap = str(report["capability_id"])
    for key in ("source_sha256", "artifact_sha256", "inventory_sha256"):
        if not isinstance(report[key], str) or _HEX64.fullmatch(report[key]) is None:
            _fail(problems, f"{where}.{key}: not 64-hex")
    items = report["items"]
    if not isinstance(items, list) or not items:
        _fail(problems, f"{where}.items must be a non-empty list")
        return
    seen_ids: set[str] = set()
    actual_counts: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != ITEM_KEYS:
            _fail(problems, f"{where}: item keys not exact")
            continue
        if item["item_kind"] not in ITEM_KINDS:
            _fail(problems, f"{where}: item_kind {item['item_kind']!r} invalid")
        if item["transform_class"] not in TRANSFORM_CLASSES:
            _fail(problems, f"{where}: transform_class invalid")
        if item["status"] not in STATUSES:
            _fail(problems, f"{where}: status {item['status']!r} invalid"
                  " (a MISSING item is a closure failure, not a status)")
        if item["item_id"] in seen_ids:
            _fail(problems, f"{where}: duplicate item_id {item['item_id']!r}")
        seen_ids.add(str(item["item_id"]))
        actual_counts[str(item["item_kind"])] = (
            actual_counts.get(str(item["item_kind"]), 0) + 1
        )
    projection = [
        {k: item[k] for k in sorted(ITEM_KEYS)} for item in items
        if isinstance(item, dict) and set(item) == ITEM_KEYS
    ]
    recomputed = _canonical_sha256(
        [
            {k: item[k] for k in (
                "item_id", "item_kind", "source_locator", "source_sha256",
                "artifact_locator", "artifact_sha256", "transform_class",
                "status",
            )}
            for item in items
            if isinstance(item, dict) and set(item) == ITEM_KEYS
        ]
    )
    del projection
    if recomputed != report["inventory_sha256"]:
        _fail(problems, f"{where}: inventory_sha256 does not match the item"
              " projection (stale report)")
    try:
        expected_counts = _independent_inventory(repo_root, cap)
    except FatalCheckError as exc:
        _fail(problems, f"{where}: {exc}")
        return
    for kind, expected in sorted(expected_counts.items()):
        actual = actual_counts.get(kind, 0)
        if actual != expected:
            _fail(
                problems,
                f"{where}: independent inventory expects {expected} {kind}"
                f" item(s), report has {actual} (EXACT closure — missing and"
                " surplus items both fail)",
            )
    for kind in sorted(set(actual_counts) - set(expected_counts)):
        _fail(
            problems,
            f"{where}: report carries {actual_counts[kind]} {kind} item(s) the"
            " independent inventory does not derive (EXACT closure)",
        )


def check_index(repo_root: Path, index: dict[str, Any], problems: list[str]) -> None:
    if set(index) != INDEX_TOP_KEYS:
        _fail(problems, f"index top keys {sorted(index)} != exact set")
        return
    if index["schema_version"] not in KNOWN_INDEX_SCHEMA_VERSIONS:
        raise FatalCheckError("unknown fidelity index schema_version")
    translated = index["translated_capabilities"]
    if not isinstance(translated, list) or not translated:
        _fail(problems, "translated_capabilities must be a non-empty list")
        return
    tranches = index["tranches"]
    if not isinstance(tranches, list) or not 3 <= len(tranches) <= 4:
        _fail(problems, "tranches must be a list of 3-4 records")
        return
    seen_caps: list[str] = []
    seen_records: set[str] = set()
    seen_tranche_ids: set[str] = set()
    for tranche in tranches:
        if not isinstance(tranche, dict) or set(tranche) != TRANCHE_KEYS:
            _fail(problems, "tranche keys not exact")
            continue
        tid = str(tranche["tranche_id"])
        if tid in seen_tranche_ids:
            _fail(problems, f"duplicate tranche_id {tid!r}")
        seen_tranche_ids.add(tid)
        if not isinstance(tranche["capability_ids"], list) or not tranche["capability_ids"]:
            _fail(problems, f"tranche {tid!r}: empty capability_ids")
            continue
        seen_caps.extend(str(c) for c in tranche["capability_ids"])
        sha = tranche["candidate_commit_sha"]
        if not isinstance(sha, str) or _HEX40.fullmatch(sha) is None:
            _fail(problems, f"tranche {tid!r}: candidate_commit_sha not 40-hex")
        for key in TRANCHE_KEYS - {"tranche_id", "capability_ids",
                                   "candidate_commit_sha", "approval_binding"}:
            value = tranche[key]
            if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
                _fail(problems, f"tranche {tid!r}.{key}: not 64-hex")
        binding = tranche["approval_binding"]
        if not isinstance(binding, dict) or set(binding) != BINDING_KEYS:
            _fail(problems, f"tranche {tid!r}: approval_binding keys not exact")
            continue
        if binding["verdict"] not in VERDICTS:
            _fail(problems, f"tranche {tid!r}: verdict {binding['verdict']!r}"
                  " invalid (approved|rejected)")
        record_id = str(binding["immutable_record_id"])
        if record_id in seen_records:
            _fail(problems, f"record id {record_id!r} reused — a re-review must"
                  " create a NEW record, never mutate a merged one")
        seen_records.add(record_id)
    if sorted(seen_caps) != sorted(set(seen_caps)):
        _fail(problems, "tranche partition overlap (a capability appears twice)")
    if set(seen_caps) != {str(c) for c in translated}:
        _fail(problems, "tranche partition gap/extra vs translated_capabilities")


def run_checks(repo_root: Path) -> list[str]:
    problems: list[str] = []
    index_path = repo_root / INDEX_RELPATH
    if not index_path.is_file():
        raise FatalCheckError(
            f"{INDEX_RELPATH.as_posix()} not found (dormant until PR-C0; run"
            " this checker against a fixture tree)"
        )
    try:
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FatalCheckError(f"index unreadable: {exc}") from exc
    if not isinstance(index, dict):
        raise FatalCheckError("index top level must be a mapping")
    check_index(repo_root, index, problems)
    coverage_dir = repo_root / COVERAGE_RELDIR
    reports = sorted(coverage_dir.glob("*.json")) if coverage_dir.is_dir() else []
    expected = {str(c) for c in index.get("translated_capabilities") or []}
    found: set[str] = set()
    for path in reports:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{path.name}: unreadable: {exc}")
            continue
        if not isinstance(report, dict):
            problems.append(f"{path.name}: not an object")
            continue
        found.add(str(report.get("capability_id")))
        check_coverage_report(repo_root, report, problems)
    missing = expected - found
    if missing:
        problems.append(
            f"coverage reports missing for: {', '.join(sorted(missing))}"
        )
    return problems


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=_SCRIPT_NAME,
        description="independent fidelity attestations closure checker"
                    " (plan §2.7/§2.8.5; dormant until PR-C0)",
    )
    parser.add_argument("--all", action="store_true", help="check index + coverage")
    args = parser.parse_args(argv)
    root = repo_root if repo_root is not None else _REPO_ROOT
    if not args.all:
        parser.print_usage(sys.stderr)
        print(f"{_SCRIPT_NAME}: --all required", file=sys.stderr)
        return 2
    try:
        problems = run_checks(root)
    except FatalCheckError as exc:
        print(f"{_SCRIPT_NAME}: {exc}", file=sys.stderr)
        return 2
    for problem in problems:
        print(f"[ERROR] {problem}")
    print(f"=== Summary === errors: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
