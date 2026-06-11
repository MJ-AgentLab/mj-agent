"""Unit tests for G25 changed-code-has-test subflag (completion-audit PR2).

DI-injected changed_files per the G24 N-1 pattern — no real git diff.
4 cases per the audit plan: src+tests PASS / src-only WARN / no-src SKIP /
no-diff-context SKIP.
"""

from __future__ import annotations

from scripts.sdd.check_tdd_test_list import _check_g25


def test_g25_src_change_with_tests_passes() -> None:
    summary = _check_g25(
        changed_files=["src/mj_agent/llm.py", "tests/unit/test_llm.py"]
    )
    assert summary.pass_count == 1
    assert summary.warn_count == 0


def test_g25_src_change_without_tests_warns() -> None:
    summary = _check_g25(changed_files=["src/mj_agent/llm.py", "README.md"])
    assert summary.warn_count == 1
    assert summary.fail_count == 0  # warning mode — M6 blocking flip deferred


def test_g25_no_src_change_skips() -> None:
    summary = _check_g25(changed_files=["docs/INDEX.md", "tests/unit/test_llm.py"])
    assert summary.pass_count == 0
    assert summary.warn_count == 0
    assert summary.fail_count == 0


def test_g25_no_diff_context_skips(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # No injected list + no CI env (GITHUB_BASE_REF/HEAD_REF absent) → graceful SKIP.
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    summary = _check_g25(changed_files=None)
    assert summary.pass_count == 0
    assert summary.warn_count == 0
    assert summary.fail_count == 0
