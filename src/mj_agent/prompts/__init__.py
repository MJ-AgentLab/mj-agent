"""Loader for static prompt fragments packaged alongside the agent.

Prompt files are in-source canonical documentation per the v2.0 trio
(``[STANDARD]_MJ_Agent_Documentation_Meta_Framework_v2.0`` + Track B
``[STANDARD]_MJ_Agent_Agent_Side_Documentation_Framework_v1.0`` §7.5).
They carry YAML frontmatter with documentation governance metadata which
MUST NOT be injected into the LLM system prompt. This module strips
frontmatter on load.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import frontmatter

_PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Read ``prompts/{name}.md`` and return the body only.

    The YAML frontmatter is parsed and discarded; only the markdown body
    (everything after the closing ``---``) is returned. Files without
    frontmatter are supported — the whole text is returned as body.

    Raises ``FileNotFoundError`` if the prompt does not exist.
    """
    path = _PROMPTS_DIR / f"{name}.md"
    return str(frontmatter.load(path).content)


@lru_cache(maxsize=32)
def load_prompt_meta(name: str) -> dict[str, Any]:
    """Return the frontmatter metadata of ``prompts/{name}.md``.

    Used by documentation tooling (index generation, A8 validation).
    Returns an empty dict when the file has no frontmatter.
    """
    path = _PROMPTS_DIR / f"{name}.md"
    return dict(frontmatter.load(path).metadata)
