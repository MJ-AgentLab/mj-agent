"""Retained data/secrets prose pins; host enforcement needs separate evidence."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def _agents_md() -> str:
    return (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_agents_md_pins_biz_data_boundary_prose() -> None:
    """§12 L442 committed proxy: AGENTS.md self-enforced biz boundary (Codex's ONLY enforcement —
    it runs under no harness gate) must forbid raw DB connections. Static proxy for the RULE TEXT;
    the runtime refusal itself is harness-reproducible-only (see module docstring)."""
    text = _agents_md()
    assert "Do NOT connect to any database directly" in text
    assert "never bypass it" in text


def test_agents_md_pins_secrets_boundary_prose() -> None:
    """§12 L443 committed proxy: AGENTS.md self-enforced secrets boundary must forbid reading /
    exfiltrating credentials. Static proxy for the rule text (see module docstring)."""
    assert "never read or exfiltrate" in _agents_md()
