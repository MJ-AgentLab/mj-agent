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


def parse_native_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    """Split text into `(frontmatter_dict, body)` using permissive native semantics.

    Matches Claude Code's `.claude/skills/*/SKILL.md` parser: each top-level
    `<key>: <value>` line is captured with `<value>` as the literal rest-of-line,
    so embedded `:` characters inside `description` (e.g., a literal
    `Do not use for: ...` anti-trigger phrase) do NOT trigger YAML's "mapping
    values are not allowed here" error that `parse_frontmatter` raises.

    Rules:
      - Top-level keys only (lines with leading whitespace are skipped — no
        nesting or continuation lines supported).
      - Lines starting with `#` are treated as YAML comments and skipped.
      - Lines without `:` are skipped.
      - The value is the rest-of-line after the FIRST `:`, with leading and
        trailing whitespace stripped. Embedded `:` characters are preserved.

    Returns `(None, original_text)` if no `---\\n...\\n---\\n` block at start
    or if the block yielded zero parseable keys.

    Use `parse_frontmatter` (strict yaml.safe_load) for full Agent_Side / PROMPT
    13-field schemas; use `parse_native_frontmatter` for ADR-013 native 2-field
    `.claude/skills/*/SKILL.md` files only.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line[0].isspace() or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key:
            fm[key] = value.strip()
    if not fm:
        return None, text
    return fm, text[match.end():]


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


_HASH_PREFIX_RE = re.compile(r"^sha256:", re.IGNORECASE)


def content_hash_matches(expected: str | None, actual: str | None) -> bool:
    """Compare two content-hash strings with `sha256:` prefix tolerance.

    Stage B adapter doc canonical form is `sha256:<hex>`; Stage A validator
    initial implementation produced bare `<hex>`. Both formats are accepted —
    the prefix is stripped (case-insensitive) before exact hex comparison.

    Either argument may be `None` (e.g., contract missing the field); in that
    case the comparison returns `False`.
    """
    if expected is None or actual is None:
        return False
    return _HASH_PREFIX_RE.sub("", expected).lower() == _HASH_PREFIX_RE.sub("", actual).lower()


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
    "parse_native_frontmatter",
    "strip_frontmatter",
    "body_sha256",
    "content_hash_matches",
    "extract_headings",
]
