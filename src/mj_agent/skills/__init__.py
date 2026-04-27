"""Loader for packaged skill definitions (SKILL.md).

SKILL.md files are in-source canonical documentation per
``[STANDARD]_MJ_Agent_Documentation_Management_Framework_v1.1``. They carry
YAML frontmatter with documentation governance metadata which MUST NOT be
injected into the LLM system prompt. This module strips frontmatter on load.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import frontmatter

_SKILLS_DIR = Path(__file__).parent


@lru_cache(maxsize=32)
def load_skill(name: str) -> str:
    """Read ``skills/{name}/SKILL.md`` and return the body only.

    The YAML frontmatter is parsed and discarded; only the markdown body
    (everything after the closing ``---``) is returned. Files without
    frontmatter are supported — the whole text is returned as body.

    Raises ``FileNotFoundError`` if the skill is not present.
    """
    path = _SKILLS_DIR / name / "SKILL.md"
    return frontmatter.load(path).content


@lru_cache(maxsize=32)
def load_skill_meta(name: str) -> dict[str, Any]:
    """Return the frontmatter metadata of ``skills/{name}/SKILL.md``.

    Used by documentation tooling (index generation, A7 validation).
    Returns an empty dict when the file has no frontmatter.
    """
    path = _SKILLS_DIR / name / "SKILL.md"
    return dict(frontmatter.load(path).metadata)
