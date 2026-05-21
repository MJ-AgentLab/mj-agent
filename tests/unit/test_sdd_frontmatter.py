"""Unit tests for `scripts.sdd._common.frontmatter` — covers both parsers.

`parse_native_frontmatter` was introduced in Phase M3 Stage A (M3-FU-V4-
VALIDATOR-INVESTIGATE) to fix the V4 validator's 34/34 spurious WARN: standard
`yaml.safe_load()` rejects `.claude/skills/*/SKILL.md` descriptions that
contain a literal `Do not use for: ...` anti-trigger phrase (a colon followed
by space inside an unquoted scalar value is interpreted as a nested mapping
start). The native parser matches Claude Code's own SKILL.md loader semantics
by taking the literal rest-of-line as the value.
"""

from __future__ import annotations

from scripts.sdd._common.frontmatter import (
    parse_frontmatter,
    parse_native_frontmatter,
)


def test_native_parses_simple_2_field_block() -> None:
    text = "---\nname: mj-agent-doc-author\ndescription: A short skill.\n---\nbody\n"
    fm, body = parse_native_frontmatter(text)
    assert fm == {"name": "mj-agent-doc-author", "description": "A short skill."}
    assert body == "body\n"


def test_native_parses_description_with_embedded_colon_space() -> None:
    """Regression: this case made `yaml.safe_load()` raise YAMLError."""
    text = (
        "---\n"
        "name: mj-agent-doc-author\n"
        "description: A skill ... Do not use for: gap analysis (use other).\n"
        "---\nbody\n"
    )
    fm, _ = parse_native_frontmatter(text)
    assert fm is not None
    assert fm["name"] == "mj-agent-doc-author"
    assert fm["description"] == (
        "A skill ... Do not use for: gap analysis (use other)."
    )


def test_native_returns_none_when_no_frontmatter_block() -> None:
    text = "# Plain markdown, no frontmatter\nbody\n"
    fm, body = parse_native_frontmatter(text)
    assert fm is None
    assert body == text


def test_native_returns_none_when_empty_block() -> None:
    """An empty `---\\n---\\n` block has no `(.*?)` interior — regex fails to match."""
    text = "---\n---\nbody\n"
    fm, _ = parse_native_frontmatter(text)
    assert fm is None


def test_native_skips_comment_lines() -> None:
    text = "---\n# a YAML comment\nname: x\ndescription: y\n---\nb\n"
    fm, _ = parse_native_frontmatter(text)
    assert fm == {"name": "x", "description": "y"}


def test_native_returns_extra_keys_for_deviation_detection() -> None:
    """Extra keys beyond ADR-013 native 2-field schema must be exposed to caller."""
    text = "---\nname: x\ndescription: y\nversion: 1.0\n---\nb\n"
    fm, _ = parse_native_frontmatter(text)
    assert fm is not None
    assert set(fm.keys()) == {"name", "description", "version"}


def test_native_returns_partial_when_required_key_missing() -> None:
    """Caller (V4 validator) detects missing keys; parser returns what's present."""
    text = "---\ndescription: only description here\n---\nb\n"
    fm, _ = parse_native_frontmatter(text)
    assert fm == {"description": "only description here"}


def test_native_skips_indented_continuation_lines() -> None:
    """Multi-line / indented values are out of scope for ADR-013 native schema."""
    text = "---\nname: x\ndescription: first line\n  continuation\n---\nb\n"
    fm, _ = parse_native_frontmatter(text)
    assert fm is not None
    assert fm["name"] == "x"
    assert fm["description"] == "first line"


def test_native_takes_first_colon_as_separator() -> None:
    """Description with multiple `: ` runs — only the FIRST colon is the separator."""
    text = "---\nname: x\ndescription: foo: bar: baz\n---\nb\n"
    fm, _ = parse_native_frontmatter(text)
    assert fm is not None
    assert fm["description"] == "foo: bar: baz"


def test_strict_parse_frontmatter_still_works_for_full_yaml() -> None:
    """Confirm `parse_frontmatter` (strict YAML) is unchanged for full schemas."""
    text = (
        "---\n"
        "name: foo\n"
        "version: 1.0\n"
        "tags:\n"
        "  - alpha\n"
        "  - beta\n"
        "---\nbody\n"
    )
    fm, body = parse_frontmatter(text)
    assert fm == {"name": "foo", "version": 1.0, "tags": ["alpha", "beta"]}
    assert body == "body\n"


def test_strict_parse_frontmatter_returns_none_on_embedded_colon() -> None:
    """Confirm the bug case still breaks strict parser (justifies native variant)."""
    text = (
        "---\n"
        "name: x\n"
        "description: A skill ... Do not use for: gap analysis.\n"
        "---\nbody\n"
    )
    fm, _ = parse_frontmatter(text)
    assert fm is None
