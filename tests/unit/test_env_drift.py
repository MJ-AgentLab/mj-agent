"""Unit tests for `mj_agent.env_drift.find_env_drift`."""

from __future__ import annotations

from pathlib import Path

from mj_agent.env_drift import find_env_drift


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_find_env_drift_in_sync(tmp_path: Path) -> None:
    """No drift when both files declare the same key set."""
    _write(tmp_path / ".env", "FOO=1\nBAR=2\n")
    _write(tmp_path / ".env.example", "FOO=\nBAR=\n")
    assert find_env_drift(tmp_path / ".env", tmp_path / ".env.example") == []


def test_find_env_drift_missing_keys_in_env(tmp_path: Path) -> None:
    """Keys declared in .env.example but missing from .env are reported."""
    _write(tmp_path / ".env", "FOO=1\n")
    _write(tmp_path / ".env.example", "FOO=\nBAR=\nBAZ=\n")
    assert find_env_drift(tmp_path / ".env", tmp_path / ".env.example") == [
        "BAR",
        "BAZ",
    ]


def test_find_env_drift_extra_keys_in_env_not_reported(tmp_path: Path) -> None:
    """Extra keys in .env (not in template) are not drift — direction is template→env."""
    _write(tmp_path / ".env", "FOO=1\nBAR=2\nLOCAL_OVERRIDE=x\n")
    _write(tmp_path / ".env.example", "FOO=\nBAR=\n")
    assert find_env_drift(tmp_path / ".env", tmp_path / ".env.example") == []


def test_find_env_drift_skips_comments_and_blank_lines(tmp_path: Path) -> None:
    """`#`-prefixed and blank lines must not yield phantom keys."""
    _write(tmp_path / ".env", "FOO=1\n")
    _write(
        tmp_path / ".env.example",
        "# header comment\n\nFOO=\n# inline section\n\nBAR=\n",
    )
    assert find_env_drift(tmp_path / ".env", tmp_path / ".env.example") == ["BAR"]


def test_find_env_drift_handles_values_with_equals_signs(tmp_path: Path) -> None:
    """KEY extraction must split on the FIRST `=` only; values may contain `=`."""
    _write(tmp_path / ".env", "URL=postgresql://u:p@h:5432/d\n")
    _write(
        tmp_path / ".env.example",
        "URL=\nNESTED_KEY=k=v&x=y\n",
    )
    assert find_env_drift(tmp_path / ".env", tmp_path / ".env.example") == [
        "NESTED_KEY"
    ]


def test_find_env_drift_returns_empty_when_files_missing(tmp_path: Path) -> None:
    """CI runners typically have no `.env` — that is not a drift condition."""
    _write(tmp_path / ".env.example", "FOO=\nBAR=\n")
    # .env intentionally not created
    assert find_env_drift(tmp_path / ".env", tmp_path / ".env.example") == []
    # .env.example also missing — still returns empty rather than raising
    assert find_env_drift(tmp_path / ".env", tmp_path / "missing.example") == []
