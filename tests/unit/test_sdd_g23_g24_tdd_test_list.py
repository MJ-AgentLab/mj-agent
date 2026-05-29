"""Unit tests for G23 + G24 TDD validator (R-N v12 R-12-1..R-12-9).

Per Stage D D-5 (FINAL unit) + sdd/gates.md L62-L63 + L96 +
sdd/adapters/bdd-tdd.md L197-199:

> L62 G23 | check_tdd_test_list.py | 高风险 task 有 tdd.test_list | M4 warning / M6 blocking
> L63 G24 | 同 G23（bugfix-regression）| bugfix PR 必有 regression test | M4 blocking
> L197-199: bugfix-regression — 仅 bugfix/* 分支触发；M3 warning / M4 blocking.

R-N v12 increments:
- R-12-1: single script + subflag dispatch (--check g23|g24|both)
- R-12-2: G23 mode = WARNING (per L62 designed M4→M6 phased)
- R-12-3: G24 mode = BLOCKING immediate (per L63+L198 most-specific;NOT R-10-8 transplant)
- R-12-4: G24 branch-conditional (bugfix/* fires; else SKIP)
- R-12-6: G23 WARN-on-missing / G24 FAIL-on-bugfix-missing / SKIP non-bugfix or non-target priority
- R-12-9: G24 fire-path unit-test 强制 (avoid landing untested dormant BLOCKING)

Test coverage (8 cases):
- TestG23TaskListPresence (3): critical+test_list PASS / critical-no-test_list WARN /
  medium excluded.
- TestG24BugfixRegression (3 ★ R-12-9 MANDATORY): bugfix+regression PASS /
  bugfix-missing FAIL / non-bugfix SKIP.
- TestSubflagDispatch (2): --check g23 only G23 fires / --check g24 only G24 fires.

N-1 inline: G24 cases use injected ``changed_files`` list (DI; no real git);
validator-local ``_check_g24`` accepts ``branch`` + ``changed_files`` params.
"""

from __future__ import annotations

from pathlib import Path

from scripts.sdd.check_tdd_test_list import (
    _check_g23_capability,
    _check_g24,
    main,
)


def _write_tasks_md(tmp_path: Path, content: str) -> Path:
    """Helper: write tasks.md at capability root."""
    cap_dir = tmp_path / "cap1"
    cap_dir.mkdir()
    (cap_dir / "tasks.md").write_text(content, encoding="utf-8")
    return cap_dir


class TestG23TaskListPresence:
    """R-12-6 G23: high/critical priority tasks have TDD test_list section."""

    def test_critical_task_with_test_list_passes(self, tmp_path: Path) -> None:
        content = (
            "# Tasks\n\n"
            "### T-001 — Critical task\n"
            "- **Priority**：critical\n"
            "- **Status**：done\n"
            "- **TDD test_list**：\n"
            "  - `tests/unit/test_foo.py::test_bar`\n"
        )
        cap_dir = _write_tasks_md(tmp_path, content)
        summary = _check_g23_capability(cap_dir, tmp_path)
        assert summary.pass_count == 1
        assert summary.warn_count == 0

    def test_critical_task_without_test_list_warns(self, tmp_path: Path) -> None:
        content = (
            "# Tasks\n\n"
            "### T-002 — Critical task missing test_list\n"
            "- **Priority**：critical\n"
            "- **Status**：in-progress\n"
        )
        cap_dir = _write_tasks_md(tmp_path, content)
        summary = _check_g23_capability(cap_dir, tmp_path)
        assert summary.warn_count >= 1
        assert any("test_list" in m for m in summary.messages)

    def test_medium_task_excluded(self, tmp_path: Path) -> None:
        content = (
            "# Tasks\n\n"
            "### T-003 — Medium task\n"
            "- **Priority**：medium\n"
            "- **Status**：done\n"
        )
        cap_dir = _write_tasks_md(tmp_path, content)
        summary = _check_g23_capability(cap_dir, tmp_path)
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)


class TestG24BugfixRegression:
    """R-12-9 G24 fire-path MANDATORY: bugfix/* branch regression test check."""

    def test_bugfix_branch_with_regression_passes(self) -> None:
        summary = _check_g24(
            branch="bugfix/123-fix-foo",
            changed_files=["src/mj_agent/foo.py", "tests/unit/test_foo.py"],
        )
        assert summary.pass_count >= 1
        assert summary.fail_count == 0

    def test_bugfix_branch_missing_regression_fails(self) -> None:
        summary = _check_g24(
            branch="bugfix/123-fix-foo",
            changed_files=["src/mj_agent/foo.py"],
        )
        assert summary.fail_count >= 1
        assert any("regression" in m.lower() for m in summary.messages)

    def test_non_bugfix_branch_skips(self) -> None:
        summary = _check_g24(
            branch="feature/add-x",
            changed_files=["src/mj_agent/x.py"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)


class TestG24BoundaryBranchMatrix:
    """R-16-2 boundary branch precision: only ^bugfix/ fires (6 boundary cases)."""

    def test_hotfix_branch_skips(self) -> None:
        # hotfix is different urgency tier (per Git Branch Strategy guide)
        summary = _check_g24(
            branch="hotfix/123-emergency",
            changed_files=["src/mj_agent/x.py"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)

    def test_fix_branch_skips(self) -> None:
        # 'fix' is not a canonical mj-agent branch type
        summary = _check_g24(
            branch="fix/typo",
            changed_files=["src/mj_agent/x.py"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)

    def test_bugfix_no_slash_skips(self) -> None:
        # 'bugfix-something' (no slash) is malformed
        summary = _check_g24(
            branch="bugfix-something",
            changed_files=["src/mj_agent/x.py"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)

    def test_feature_bugfix_suggestion_skips(self) -> None:
        # 'feature/bugfix-suggestion' is feature family
        summary = _check_g24(
            branch="feature/bugfix-suggestion",
            changed_files=["src/mj_agent/x.py"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)

    def test_documentation_branch_skips(self) -> None:
        summary = _check_g24(
            branch="documentation/some-doc-fix",
            changed_files=["docs/some.md"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)

    def test_maintain_branch_skips(self) -> None:
        summary = _check_g24(
            branch="maintain/dep-bump",
            changed_files=["pyproject.toml"],
        )
        assert (summary.pass_count, summary.warn_count, summary.fail_count) == (0, 0, 0)


class TestG24EscapeHatchTrailer:
    """R-16-3 Option (d) commit trailer ``G24-Exempt: <reason>`` escape hatch.

    Anti-gate-defeat (R-16-6): explicit + reviewable; HEAD commit only (R-16-9);
    presence + non-empty reason hard check (reviewer culture handles reason quality).
    """

    def test_trailer_present_with_reason_skips_with_note(self) -> None:
        # Doc-only bugfix legit case: trailer present + reason → PASS+note (not FAIL)
        summary = _check_g24(
            branch="bugfix/typo-claude-md",
            changed_files=["CLAUDE.md"],
            commit_message=(
                "fix(docs): typo in CLAUDE.md\n\n"
                "Trivial typo fix; no functional change.\n\n"
                "G24-Exempt: doc-only fix; no behavior change to test\n"
            ),
        )
        # Trailer present → bypass FAIL; record as PASS with trailer-exempt note
        assert summary.fail_count == 0
        assert summary.pass_count >= 1
        assert any("exempt" in m.lower() or "G24-Exempt" in m for m in summary.messages)

    def test_trailer_empty_reason_fails(self) -> None:
        # Presence requires non-empty reason (per R-16-3 hard check)
        summary = _check_g24(
            branch="bugfix/typo-claude-md",
            changed_files=["CLAUDE.md"],
            commit_message="fix(docs): typo\n\nG24-Exempt:\n",  # empty reason
        )
        # Empty reason = treat as absent trailer → FAIL on no tests/
        assert summary.fail_count >= 1

    def test_trailer_absent_fails_on_no_tests(self) -> None:
        # Doc-only bugfix WITHOUT trailer → FAIL (anti-gate-defeat;forces explicit)
        summary = _check_g24(
            branch="bugfix/typo-claude-md",
            changed_files=["CLAUDE.md"],
            commit_message="fix(docs): typo in CLAUDE.md\n",  # no trailer
        )
        assert summary.fail_count >= 1
        assert any("regression" in m.lower() or "missing" in m.lower() for m in summary.messages)

    def test_trailer_present_but_with_tests_passes_normally(self) -> None:
        # Trailer + tests/ change → still PASS via normal path (trailer not needed)
        summary = _check_g24(
            branch="bugfix/foo",
            changed_files=["src/mj_agent/foo.py", "tests/unit/test_foo.py"],
            commit_message=(
                "fix(foo): handle edge case\n\nG24-Exempt: extra precaution\n"
            ),
        )
        # Normal path PASS (tests/ present);trailer extra is harmless
        assert summary.pass_count >= 1
        assert summary.fail_count == 0


class TestSubflagDispatch:
    """R-12-1 subflag dispatch correctness."""

    def test_check_g23_only_skips_g24(self, tmp_path: Path, monkeypatch) -> None:
        # Ensure no GITHUB_HEAD_REF leaks G24 fire when --check g23
        monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
        # Use --capability path to scope discovery
        content = (
            "# Tasks\n\n"
            "### T-001 — Critical task\n"
            "- **Priority**：critical\n"
            "- **TDD test_list**：\n"
            "  - `tests/unit/test_x.py::test_x`\n"
        )
        cap_dir = _write_tasks_md(tmp_path, content)
        # When --check g23 is selected, G24 logic NOT invoked
        exit_code = main(["--check", "g23", "--capability", str(cap_dir)])
        assert exit_code == 0

    def test_check_g24_only_skips_g23(self, tmp_path: Path, monkeypatch) -> None:
        # G24 invoked, but no PR context (no env) → SKIP
        monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
        content = (
            "# Tasks\n\n"
            "### T-002 — Critical missing test_list\n"
            "- **Priority**：critical\n"
        )
        cap_dir = _write_tasks_md(tmp_path, content)
        # --check g24 → G23 NOT invoked → 0 WARN regardless of tasks.md content
        exit_code = main(["--check", "g24", "--capability", str(cap_dir)])
        assert exit_code == 0
