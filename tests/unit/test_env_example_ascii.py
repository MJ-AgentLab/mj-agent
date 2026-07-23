"""Repo-invariant guard: ``.env.example`` must be pure ASCII (issue #119).

``python-dotenv`` (invoked inside ``langgraph_api.cli.run_server`` via
``DotEnv(dotenv_path=...).dict()``) opens the file with the OS *default*
encoding. On Chinese Windows that codec is GBK/CP936, so any non-ASCII byte
in ``.env.example`` -- an em-dash, a Chinese comment, a section sign -- raises
``UnicodeDecodeError`` and ``uv run langgraph dev`` fails to start before
Studio ever loads.

CLAUDE.md "Environment variables & secrets" declares ``.env.example``
ASCII-only. This test makes that invariant CI-enforced so a future edit cannot
silently reintroduce non-ASCII the way ADR-025 PR-2/PR-3 did.
"""

from __future__ import annotations

from pathlib import Path

_ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"


def test_env_example_is_ascii_only() -> None:
    """Every byte of the committed ``.env.example`` must be < 0x80."""
    assert _ENV_EXAMPLE.is_file(), f"expected {_ENV_EXAMPLE} to exist"
    data = _ENV_EXAMPLE.read_bytes()

    offenders: list[str] = []
    line = 1
    col = 1
    for byte in data:
        if byte == 0x0A:  # newline resets the column counter
            line += 1
            col = 1
            continue
        if byte > 0x7F:
            offenders.append(f"line {line} col {col}: byte {byte:#04x}")
        col += 1

    assert not offenders, (
        f"{_ENV_EXAMPLE.name} must be ASCII-only (issue #119) -- python-dotenv "
        "decodes it with the OS default codec (GBK on Chinese Windows) and any "
        f"non-ASCII byte crashes `langgraph dev`. Found {len(offenders)} "
        "non-ASCII byte(s): " + "; ".join(offenders[:20])
    )
