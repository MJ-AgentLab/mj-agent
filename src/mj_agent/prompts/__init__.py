"""Loader for static prompt fragments packaged alongside the agent."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Read a packaged prompt file (`prompts/{name}.md`) and return its text.

    Raises FileNotFoundError if the prompt does not exist.
    """
    path = _PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")
