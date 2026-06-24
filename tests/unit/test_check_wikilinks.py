"""Unit tests for the #267 item-2 A4 root-file link resolution in
``scripts/check_wikilinks.py``.

Tests exercise the root-parameterized helper functions against ``tmp_path``
fixtures (never ``main()`` against the real repo tree), so building scratch
directories cannot flip a real-tree precondition.
"""
from __future__ import annotations

from pathlib import Path

from scripts.check_wikilinks import (
    ROOT_FILES,
    WALK_FILES,
    clean_target,
    iter_content_lines,
    scan_links,
    scan_root_file_links,
    target_resolves,
)


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestConfig:
    def test_walk_files_now_covers_all_root5(self) -> None:
        # #267 item 1: archive forward-guard extended from CLAUDE.md-only.
        assert set(WALK_FILES) == set(ROOT_FILES)
        assert "GLOSSARY.md" in WALK_FILES  # the M6 sweep gap, now guarded


class TestCleanTarget:
    def test_external_schemes_skipped(self) -> None:
        assert clean_target("https://example.com/x", "md") is None
        assert clean_target("http://example.com", "md") is None
        assert clean_target("mailto:a@b.com", "md") is None
        assert clean_target("//cdn.example.com/x", "md") is None

    def test_same_doc_anchor_skipped(self) -> None:
        assert clean_target("#section", "md") is None
        assert clean_target("#heading", "wiki") is None

    def test_absolute_path_skipped(self) -> None:
        assert clean_target("/etc/passwd", "md") is None

    def test_md_strips_title_and_angle_brackets(self) -> None:
        assert clean_target('docs/x.md "a title"', "md") == "docs/x.md"
        assert clean_target("<docs/x.md>", "md") == "docs/x.md"

    def test_strips_anchor_fragment(self) -> None:
        assert clean_target("docs/x.md#sec", "md") == "docs/x.md"

    def test_wiki_strips_display_text(self) -> None:
        assert clean_target("decisions/ADR-016|ADR-016 Foo", "wiki") == "decisions/ADR-016"

    def test_wiki_strips_escaped_pipe(self) -> None:
        # GFM table cells escape the wikilink pipe as ``\|``.
        assert clean_target(r"decisions/ADR-034\|ADR-034", "wiki") == "decisions/ADR-034"

    def test_placeholder_without_path_content_skipped(self) -> None:
        # Illustrative ``[[...]]`` / ``[](...)`` syntax examples carry no
        # resolvable filename — and ``...`` resolves to the repo root on
        # Windows (trailing-dot strip) but not Linux, so skipping is required
        # for cross-platform parity.
        assert clean_target("...", "wiki") is None
        assert clean_target("...", "md") is None
        assert clean_target("..", "md") is None


class TestTargetResolves:
    def test_existing_relative_path(self, tmp_path: Path) -> None:
        _write(tmp_path, "policies/documentation.md", "x")
        assert target_resolves(tmp_path, "policies/documentation.md") is True
        assert target_resolves(tmp_path, "./policies/documentation.md") is True

    def test_missing_path(self, tmp_path: Path) -> None:
        assert target_resolves(tmp_path, "docs/missing.md") is False

    def test_extensionless_md_target(self, tmp_path: Path) -> None:
        _write(tmp_path, "decisions/ADR-016.md", "x")
        assert target_resolves(tmp_path, "decisions/ADR-016") is True

    def test_bracketed_filename_resolves_literally(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/rule/[STANDARD]_X.md", "x")
        assert target_resolves(tmp_path, "docs/rule/[STANDARD]_X.md") is True

    def test_directory_target(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        assert target_resolves(tmp_path, "docs") is True


class TestScanLinks:
    def test_dangling_markdown_link_flagged(self, tmp_path: Path) -> None:
        result = scan_links(tmp_path, Path("README.md"), "see [x](./docs/missing.md)")
        assert len(result) == 1
        assert result[0][1:] == (1, "md", "./docs/missing.md")

    def test_resolved_link_is_clean(self, tmp_path: Path) -> None:
        _write(tmp_path, "policies/documentation.md", "x")
        text = "文档贡献请按 [policies/documentation.md](./policies/documentation.md)"
        assert scan_links(tmp_path, Path("README.md"), text) == []

    def test_external_and_anchor_not_flagged(self, tmp_path: Path) -> None:
        text = "[a](https://example.com) [b](#anchor) [c](mailto:x@y.com)"
        assert scan_links(tmp_path, Path("README.md"), text) == []

    def test_fenced_code_block_skipped(self, tmp_path: Path) -> None:
        text = "before\n```\n[x](./missing.md)\n```\nafter"
        assert scan_links(tmp_path, Path("CHANGELOG.md"), text) == []

    def test_inline_code_span_skipped(self, tmp_path: Path) -> None:
        text = "example `[x](./missing.md)` not a real link"
        assert scan_links(tmp_path, Path("README.md"), text) == []

    def test_bracketed_link_text_target_still_resolved(self, tmp_path: Path) -> None:
        # mj-agent filenames embed [STANDARD] brackets in the link *text*.
        _write(tmp_path, "policies/documentation.md", "x")
        text = "[docs/rule/[STANDARD]_X.md](./policies/documentation.md)"
        assert scan_links(tmp_path, Path("README.md"), text) == []

    def test_wikilink_escaped_pipe_resolves(self, tmp_path: Path) -> None:
        _write(tmp_path, "decisions/ADR-034.md", "x")
        text = r"| row | [[decisions/ADR-034\|ADR-034 model]] | cell |"
        assert scan_links(tmp_path, Path("CHANGELOG.md"), text) == []

    def test_dangling_wikilink_flagged(self, tmp_path: Path) -> None:
        result = scan_links(tmp_path, Path("CHANGELOG.md"), "[[decisions/ADR-999|gone]]")
        assert len(result) == 1
        assert result[0][2] == "wiki"

    def test_syntax_example_heading_not_flagged(self, tmp_path: Path) -> None:
        # GLOSSARY.md's ``### Wikilink（[[...]] 链接）`` heading is illustrative,
        # not a real link (regression: the blocking flip surfaced this).
        assert scan_links(tmp_path, Path("GLOSSARY.md"), "### Wikilink（[[...]] 链接）") == []


class TestIterContentLines:
    def test_skips_fenced_block_and_markers(self) -> None:
        text = "a\n```python\nb\n```\nc"
        bodies = [line for _, line in iter_content_lines(text)]
        assert "a" in bodies and "c" in bodies
        assert "b" not in bodies
        assert "```python" not in bodies

    def test_tilde_fence(self) -> None:
        text = "x\n~~~\ny\n~~~\nz"
        bodies = [line for _, line in iter_content_lines(text)]
        assert bodies == ["x", "z"]


class TestScanRootFileLinks:
    def test_aggregates_across_root_files(self, tmp_path: Path) -> None:
        _write(tmp_path, "README.md", "[a](./missing-a.md)")
        _write(tmp_path, "GLOSSARY.md", "[b](./missing-b.md)")
        result = scan_root_file_links(tmp_path, ("README.md", "GLOSSARY.md"))
        assert len(result) == 2

    def test_absent_root_file_is_skipped(self, tmp_path: Path) -> None:
        assert scan_root_file_links(tmp_path, ROOT_FILES) == []
