"""Integration test for G24 BLOCKING gate live-exercise (3-state subprocess sim).

Per Stage E α' E-3 M-FU#8 G24 bugfix workflow readiness + R-12-9 fire-path
extended to integration layer. D-5 unit tests cover function-level DI (3
cases); E-3 integration adds subprocess invocation simulating CI bugfix/*
PR context.

3-state coverage:
- Compliant bugfix (tests/ in diff OR G24-Exempt trailer) → PASS exit 0
- Non-compliant bugfix (no tests/, no trailer) → FAIL exit 1
- Non-bugfix branch → SKIP exit 0

Per R-16-3 Option (d) commit trailer + R-16-4 subprocess git diff + R-16-9
HEAD commit only. Validator invoked via CLI; --branch + --changed-files +
--commit-message flags inject test context (production uses env + git
log + git diff;test path bypasses for hermetic execution).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_validator(
    branch: str,
    changed_files: list[str],
    commit_message: str | None = None,
) -> tuple[int, str]:
    """Invoke check_tdd_test_list.py --check g24 via subprocess.

    Returns (exit_code, stdout). Uses CLI flags for test injection
    (production reads env GITHUB_HEAD_REF + git log + git diff).
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    script = repo_root / "scripts" / "sdd" / "check_tdd_test_list.py"

    args = [
        sys.executable,
        str(script),
        "--check",
        "g24",
        "--branch",
        branch,
        "--changed-files",
        ",".join(changed_files),
    ]
    if commit_message is not None:
        args.extend(["--commit-message", commit_message])

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    return result.returncode, result.stdout


class TestG24LiveExerciseIntegration:
    """R-12-9 extended: 3-state live-exercise subprocess sim."""

    def test_compliant_bugfix_passes_exit_0(self) -> None:
        # bugfix/* + tests/ in diff → PASS exit 0
        exit_code, stdout = _run_validator(
            branch="bugfix/123-fix-foo",
            changed_files=["src/mj_agent/foo.py", "tests/unit/test_foo.py"],
        )
        assert exit_code == 0
        assert "1P" in stdout or "PASS" in stdout

    def test_non_compliant_bugfix_fails_exit_1(self) -> None:
        # bugfix/* + no tests/ + no trailer → FAIL exit 1 (BLOCKING per R-12-3)
        exit_code, stdout = _run_validator(
            branch="bugfix/123-fix-foo",
            changed_files=["src/mj_agent/foo.py"],
            commit_message="fix(foo): bug fix without test\n",
        )
        assert exit_code == 1
        assert "1F" in stdout or "FAIL" in stdout

    def test_non_bugfix_branch_skips_exit_0(self) -> None:
        # feature/* → SKIP exit 0 (branch-conditional per R-12-4)
        exit_code, stdout = _run_validator(
            branch="feature/add-x",
            changed_files=["src/mj_agent/x.py"],
        )
        assert exit_code == 0
        assert "0P / 0W / 0F" in stdout

    def test_escape_hatch_trailer_passes_exit_0(self) -> None:
        # bugfix/* + no tests/ + G24-Exempt trailer → PASS exit 0 (R-16-3)
        exit_code, stdout = _run_validator(
            branch="bugfix/typo-claude-md",
            changed_files=["CLAUDE.md"],
            commit_message=(
                "fix(docs): typo\n\nG24-Exempt: doc-only fix\n"
            ),
        )
        assert exit_code == 0
        assert "1P" in stdout or "exempt" in stdout.lower()
