"""scripts/sdd/_common/frontmatter.py — frontmatter + body helpers.

Used by prompt / runtime-skill / claude-skill validators to:
- Parse YAML frontmatter block.
- Strip frontmatter and hash body bytes for `freeze_anchor.content_hash`.
- Extract markdown headings while skipping fenced code blocks (critical per
  M2 Subagent B findings: system.md and SKILL.md `description` blocks may
  embed example markdown with `##`/`#` that are NOT real document headings).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import yaml

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split text into `(frontmatter_dict, body)`.

    Returns `(None, original_text)` if no frontmatter block at start, or if the
    block fails YAML parse, or if the parsed result is not a mapping.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    body = text[match.end():]
    return fm, body


def strip_frontmatter(text: str) -> str:
    """Return body only (frontmatter block removed if present)."""
    _, body = parse_frontmatter(text)
    return body


def body_sha256(text: str) -> str:
    """Return sha256 hex of body bytes (frontmatter stripped, UTF-8 encoded).

    Used by claude-skill / runtime-skill / prompt contracts to lock down
    `freeze_anchor.content_hash` against the 4 项必停 source files.
    """
    body = strip_frontmatter(text)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def extract_headings(text: str, level: int = 1, skip_fenced: bool = True) -> list[str]:
    """Extract markdown headings of given level, optionally skipping fenced code blocks.

    Critical for system.md (single-hash) and SKILL.md (double-hash) which may contain
    fenced markdown blocks with their own ## / # that are NOT real headings.

    >>> txt = "# Real one\\n```markdown\\n## Trap inside fence\\n```\\n# Real two"
    >>> extract_headings(txt, level=1)
    ['Real one', 'Real two']
    >>> extract_headings(txt, level=2)
    []
    >>> extract_headings(txt, level=2, skip_fenced=False)
    ['Trap inside fence']
    """
    headings: list[str] = []
    in_fenced = False
    prefix = "#" * level + " "
    for line in text.splitlines():
        if line.startswith("```"):
            if skip_fenced:
                in_fenced = not in_fenced
            continue
        if skip_fenced and in_fenced:
            continue
        if line.startswith(prefix):
            heading_text = line[len(prefix):].rstrip().rstrip("#").rstrip()
            headings.append(heading_text)
    return headings


__all__ = [
    "parse_frontmatter",
    "strip_frontmatter",
    "body_sha256",
    "extract_headings",
]
