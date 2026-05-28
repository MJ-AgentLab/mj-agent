"""scripts/sdd/check_tdd_test_list.py — G23 + G24 TDD validator (Stage D D-5 FINAL).

Dual-gate single script + subflag dispatch (R-N v12 R-12-1; V5 precedent
``check_docker_contracts.py --bdd --tdd --compose-config``):

Per sdd/gates.md L62-L63 + L96 + sdd/adapters/bdd-tdd.md L197-199:

> L62 G23 | check_tdd_test_list.py | 高风险 task 有 tdd.test_list | M4 warning / M6 blocking
> L63 G24 | 同 G23（bugfix-regression）| bugfix PR 必有 regression test | M4 blocking
> L197-199: bugfix-regression — bugfix 修复前必先有 failing test reproducing the bug；
> M3 warning / M4 blocking；仅 bugfix/* 分支触发.

R-N v12 mode lock-in:

- R-12-2: G23 mode = **WARNING** (per L62 M4 warning → M6 blocking phased designed)
- R-12-3: G24 mode = **BLOCKING immediate** (per L63+L198 most-specific-SoT;NOT
  R-10-8 phased-rollout transplant — outline §4 R-1'' covers G21/G22 only, NOT G23/G24)
- R-12-4: G24 branch-conditional — only ``bugfix/*`` branches fire;else SKIP (per L198).
  CI mode reads ``GITHUB_HEAD_REF`` env;local CLI accepts ``--branch`` override
  (per N-1 diff-source DI abstraction for testability).

R-N v12 R-12-6 FAIL/WARN/PASS policy (R-N v8 R-1 dichotomy adapted):

- G23: critical|high priority task w/o TDD test_list section → **WARN**
       (M-FU#9 conditional curation register if surface)
- G24: bugfix/* branch + missing regression test → **FAIL** (BLOCKING)
- G24: non-bugfix branch OR no PR context → **SKIP** (exit 0)
- G23: medium|low priority task → not filtered (SKIP)

R-N v12 R-12-7 Section 5 stability 守: ``_common.frontmatter.extract_headings``
reuse for tasks.md ``### T-NNN`` parsing;NO extension;``bdd_helpers`` UNTOUCHED.

R-N v12 R-12-9 G24 fire-path 强制 unit-test coverage: bugfix context PASS +
missing FAIL + non-bugfix SKIP (3 cases mandatory). Avoid landing untested
dormant BLOCKING gate that first fires on real bugfix PR uncovered.

N-2 inline: G24 predicate is **MVP-heuristic** (bugfix branch + any tests/ file
in changed files → PASS;else FAIL). Precision refinement → M-FU#8 scope expanded
to include predicate false-positive review + bugfix-exempt edge cases (config-only
fix / doc-only fix on bugfix branch) + possible PR label override.

M-FU registry post-D-5 (Action-N batch propagate post-Stage-E):

- M-FU#8 NEW ``M4-FU-G24-BUGFIX-BRANCH-WORKFLOW-READINESS``: pre-first-bugfix-PR
  validate G24 predicate + workflow docs + precision review (N-3 scope expansion).
- M-FU#9 NEW conditional ``M4-FU-G23-TASKS-CURATION-SURFACE``: if D-5 Step 5(d)
  dry-run surfaces tasks.md test_list curation gap.
- M-FU PHASE-MAP-RECONCILE existing AMEND: G23 L62 "M4 warning/M6 blocking" +
  G24 L63 "M4 blocking" added as phase-map reconciliation examples.
- M-FU#3 existing AMEND: TDD Solo first data point (n=1; sub-taxonomy lock-progress).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.cli import Severity, Summary, build_argparser  # noqa: E402
from scripts.sdd._common.discovery import (  # noqa: E402
    discover_capabilities,
    resolve_display_path,
)
from scripts.sdd._common.frontmatter import extract_headings  # noqa: E402

_SCRIPT_NAME = "check_tdd_test_list"
_TARGET_PRIORITIES = frozenset({"critical", "high"})
_PRIORITY_PATTERN = re.compile(r"\*\*Priority\*\*[:：]\s*(\w+)", re.IGNORECASE)
_TEST_LIST_PATTERN = re.compile(r"\*\*TDD test_list\*\*", re.IGNORECASE)
_BUGFIX_BRANCH_PATTERN = re.compile(r"^bugfix/")
_TESTS_PATH_PATTERN = re.compile(r"(^|/)tests/")


def _split_into_task_sections(tasks_md_text: str) -> list[str]:
    """Split tasks.md body into per-task sections by ``### T-NNN`` boundaries.

    Returns list of section bodies (between ### headers). Empty if no tasks.
    """
    sections: list[str] = []
    current_lines: list[str] = []
    in_section = False

    for line in tasks_md_text.splitlines():
        if line.startswith("### "):
            if in_section:
                sections.append("\n".join(current_lines))
            current_lines = [line]
            in_section = True
        elif in_section:
            current_lines.append(line)

    if in_section:
        sections.append("\n".join(current_lines))

    return sections


def _extract_task_priority(section: str) -> str | None:
    """Extract priority value from task section. Returns None if no Priority field."""
    m = _PRIORITY_PATTERN.search(section)
    if not m:
        return None
    return m.group(1).lower()


def _section_has_test_list(section: str) -> bool:
    """True if section contains a ``**TDD test_list**`` marker (R-12-6)."""
    return bool(_TEST_LIST_PATTERN.search(section))


def _check_g23_capability(capability_dir: Path, repo_root: Path) -> Summary:
    """G23 per-capability: high/critical tasks have TDD test_list section.

    SKIP: tasks.md missing.
    WARN: filtered task missing test_list (R-12-6).
    PASS: filtered task with test_list section.
    """
    summary = Summary()
    tasks_path = capability_dir / "tasks.md"
    display = resolve_display_path(capability_dir, repo_root)

    if not tasks_path.exists():
        return summary

    try:
        text = tasks_path.read_text(encoding="utf-8")
    except OSError as exc:
        summary.add(Severity.WARN, f"{display}: tasks.md unreadable ({exc})")
        return summary

    sections = _split_into_task_sections(text)
    headings = extract_headings(text, level=3)

    for section, heading in zip(sections, headings, strict=False):
        priority = _extract_task_priority(section)
        if priority not in _TARGET_PRIORITIES:
            continue

        if _section_has_test_list(section):
            summary.add(
                Severity.PASS,
                f"{display}: task '{heading}' (priority={priority}) has TDD test_list",
            )
        else:
            summary.add(
                Severity.WARN,
                f"{display}: task '{heading}' (priority={priority}) missing TDD test_list "
                "(R-12-6 CURATION WARN; M-FU#9 maintenance)",
            )

    return summary


def _check_g24(
    branch: str | None = None, changed_files: list[str] | None = None
) -> Summary:
    """G24: bugfix/* branch must have regression test in PR diff (R-12-3 BLOCKING).

    R-12-4 branch-conditional: non-bugfix branch OR no context → SKIP.
    R-12-9 fire-path: bugfix + tests/ file in diff → PASS;else FAIL.

    N-1 DI: branch + changed_files accept injected values for testing; in CI mode,
    fallback to GITHUB_HEAD_REF env + git diff (NOT implemented here — placeholder
    for M-FU#8 readiness work; current dry-run on non-bugfix branch SKIPs cleanly).

    N-2 MVP-lenient: predicate = "any tests/ file modified on bugfix branch".
    Precision refinement (config-only fix / doc-only fix exemption / PR label
    override) → M-FU#8 expanded scope.
    """
    summary = Summary()
    if branch is None:
        branch = os.environ.get("GITHUB_HEAD_REF") or ""

    if not _BUGFIX_BRANCH_PATTERN.match(branch):
        return summary  # SKIP: non-bugfix branch OR no PR context

    if changed_files is None:
        return summary  # SKIP: no PR diff context (local dry-run; M-FU#8 CI fill-in)

    has_test_file = any(_TESTS_PATH_PATTERN.search(p) for p in changed_files)
    if has_test_file:
        summary.add(
            Severity.PASS,
            f"G24: bugfix branch '{branch}' includes tests/ file in diff "
            "(R-12-9 fire-path PASS; MVP-lenient predicate per N-2)",
        )
    else:
        summary.add(
            Severity.FAIL,
            f"G24: bugfix branch '{branch}' MISSING regression test in diff "
            f"(no tests/ file in changed_files; per L63+L198 BLOCKING; "
            "regression test must reproduce the bug per bdd-tdd.md L197-199)",
        )

    return summary


def main(argv: list[str] | None = None) -> int:
    """G23 + G24 validator entry point per R-12-1 subflag dispatch."""
    parser = build_argparser(
        _SCRIPT_NAME,
        "G23/G24 TDD test_list + bugfix-regression validator (per gates.md L62-L63 + L96; "
        "bdd-tdd.md L197-199; R-N v12 R-12-1 single+subflag dispatch)",
        "tasks.md",
    )
    parser.add_argument(
        "--check",
        choices=["g23", "g24", "both"],
        default="both",
        help="Which gate(s) to run: g23 (warning) / g24 (blocking) / both",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Override branch detection for G24 (local testing only; CI uses GITHUB_HEAD_REF)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent

    if args.dry_run:
        capabilities = discover_capabilities(repo_root, args.capability)
        print(
            f"{_SCRIPT_NAME}: {len(capabilities)} capability(ies) discovered "
            f"(no validation in dry-run mode; --check {args.check})"
        )
        return 0

    aggregate = Summary()

    if args.check in ("g23", "both"):
        capabilities = discover_capabilities(repo_root, args.capability)
        for cap_dir in capabilities:
            per_cap = _check_g23_capability(cap_dir, repo_root)
            aggregate.merge(per_cap)
            per_cap.print_messages()

    if args.check in ("g24", "both"):
        g24_summary = _check_g24(branch=args.branch)
        aggregate.merge(g24_summary)
        g24_summary.print_messages()

    print(
        f"{_SCRIPT_NAME}: "
        f"{aggregate.pass_count}P / {aggregate.warn_count}W / {aggregate.fail_count}F "
        f"(--check={args.check}; G23 WARN per L62 / G24 BLOCKING per L63+L198 / "
        "branch-conditional SKIP)"
    )
    return aggregate.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
