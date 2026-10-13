"""Isolated public input fixture for actual GitHub CI protection testing."""

from pathlib import Path


def test_platform_ci_gate_canary() -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures/agent_first_platform_canary/state.txt"
    assert fixture.read_text(encoding="utf-8").strip() == "green"
