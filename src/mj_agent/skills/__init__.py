"""Loader for packaged skill definitions (SKILL.md)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_SKILLS_DIR = Path(__file__).parent


@lru_cache(maxsize=32)
def load_skill(name: str) -> str:
    """Read `skills/{name}/SKILL.md` and return its text.

    Raises FileNotFoundError if the skill is not present.
    """
    path = _SKILLS_DIR / name / "SKILL.md"
    return path.read_text(encoding="utf-8")
