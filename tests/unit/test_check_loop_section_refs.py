"""Unit tests for ``scripts/check_loop_section_refs.py`` (#453).

Bands per ``tests/AGENTS.md`` fixture discipline:

- scan-face config pins and pure helpers run against ``tmp_path`` fixtures;
- exit codes run ``main(argv, repo_root=...)`` against a synthetic tree in
  ``tmp_path`` -- never against the live tree;
- two real-tree pins (kernel heading set is non-empty; live tree is clean)
  guard the regression this gate was built for.

The negative tests are the point (AC-3): a detector that cannot be made to
fail is indistinguishable from one that passes vacuously -- the
``check_frontmatter`` fail-open precedent (#429).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.check_loop_section_refs import (
    ARCHIVED_SOURCE_MARKERS,
    KERNEL_REL,
    WALK_DIRS,
    WALK_FILES,
    check_line,
    iter_scanned_files,
    main,
    parse_kernel_sections,
    parse_sections,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

KERNEL_STUB = """---
type: sdd-workflow
---

# Workflow: Execution Loop

## §1 总体流程

## §3 HITL 通用规则

### §3.1 必须暂停确认

## §4 Stage → Skill 映射表

### §4.1 流程编排器

## §6 AI Self-review 检查清单
"""


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_tree(root: Path, extra: dict[str, str] | None = None) -> Path:
    _write(root, str(KERNEL_REL), KERNEL_STUB)
    for rel, text in (extra or {}).items():
        _write(root, rel, text)
    return root


# --------------------------------------------------------------------------
# scan-face config pins
# --------------------------------------------------------------------------


class TestScanFaceConfig:
    def test_claude_skills_are_on_the_face(self) -> None:
        # The defect class lives in .claude/skills/**; a gate that cannot see
        # them is useless.
        assert ".claude" in WALK_DIRS

    def test_kernel_dirs_are_on_the_face(self) -> None:
        for expected in ("sdd", "policies", "docs", "decisions", "capabilities"):
            assert expected in WALK_DIRS

    def test_historical_ledgers_are_off_the_face(self) -> None:
        # Deliberate exclusions (module docstring): these record the numbering
        # in force when written and must not be rewritten. A silent re-add
        # would produce permanent un-fixable noise, so pin it structurally.
        assert "plans" not in WALK_DIRS
        assert "CHANGELOG.md" not in WALK_FILES

    def test_root_instruction_files_are_on_the_face(self) -> None:
        for expected in ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md"):
            assert expected in WALK_FILES


# --------------------------------------------------------------------------
# heading parsing
# --------------------------------------------------------------------------


class TestParseSections:
    def test_parses_numbered_and_section_sign_headings(self, tmp_path: Path) -> None:
        doc = _write(tmp_path, "d.md", "## §3.1 A\n### 4.2 B\n# §1 C\ntext §9 not a heading\n")
        assert parse_sections(doc) == {"3.1", "4.2", "1"}

    def test_ignores_unnumbered_headings(self, tmp_path: Path) -> None:
        doc = _write(tmp_path, "d.md", "## Overview\n## Step 3: things\n")
        # "Step 3: things" does not start with a number, so it contributes none.
        assert parse_sections(doc) == set()

    def test_tolerates_utf8_bom(self, tmp_path: Path) -> None:
        doc = tmp_path / "bom.md"
        doc.write_text("\ufeff## §2 Header\n", encoding="utf-8")
        assert parse_sections(doc) == {"2"}

    def test_kernel_parse_is_fail_closed_on_empty(self, tmp_path: Path) -> None:
        # AC-3: a kernel we cannot parse must HARD FAIL, never pass vacuously.
        empty = _write(tmp_path, "empty.md", "# Title with no numbered sections\n")
        with pytest.raises(ValueError, match="parsed zero section headings"):
            parse_kernel_sections(empty)


# --------------------------------------------------------------------------
# rule: dangling-section
# --------------------------------------------------------------------------


class TestDanglingSection:
    sections = {"1", "3", "3.0", "3.1", "4", "4.1", "6"}

    def test_flags_section_that_does_not_exist(self) -> None:
        found = check_line("see execution-loop §4.7 Rules 1-15", self.sections)
        assert [r for r, _ in found] == ["dangling-section"]

    def test_accepts_section_that_exists(self) -> None:
        assert check_line("see execution-loop §4.1 map", self.sections) == []

    def test_ignores_lines_that_do_not_name_the_kernel(self) -> None:
        # Bare refs without attribution are out of scope for this gate
        # (Class 6, deferred) -- they are ambiguous, not wrong.
        assert check_line("per §4.15 Rule 11 open a ticket", self.sections) == []

    @pytest.mark.parametrize("marker", ARCHIVED_SOURCE_MARKERS)
    def test_archived_source_attribution_is_whitelisted(self, marker: str) -> None:
        # `原 HITL_Prompt §4.7` is a correct historical citation. This is what
        # keeps the 5 frozen infra-* skills out of the report.
        line = f"execution-loop kernel home; 原 {marker} §4.7 Rule 13"
        assert check_line(line, self.sections) == []

    def test_self_reference_is_exempt(self) -> None:
        # `policies/ai-agent.md` saying "详 §9 + execution-loop.md §3.0" means
        # ITS OWN §9.
        line = "> （详 §9 + `sdd/workflows/execution-loop.md §3.0`）。"
        assert check_line(line, self.sections, frozenset({"9"})) == []
        # ...but without that heading it is a genuine dangling reference.
        assert [r for r, _ in check_line(line, self.sections)] == ["dangling-section"]

    def test_reference_attributed_to_another_document_is_skipped(self) -> None:
        # Naming the document is the behaviour we want; do not punish it.
        line = "per execution-loop §3.1 + policies/documentation.md §5.3 A8/A11"
        assert check_line(line, self.sections) == []

    def test_reference_attributed_to_the_kernel_itself_is_still_checked(self) -> None:
        line = "详 `sdd/workflows/execution-loop.md §4.7` Rules"
        assert [r for r, _ in check_line(line, self.sections)] == ["dangling-section"]

    def test_wikilink_form_is_not_mistaken_for_attribution(self) -> None:
        # The wikilink ends in `]]`, not `.md` -- it must stay checked.
        line = "[[../../../sdd/workflows/execution-loop|execution-loop]] §4.7（Stage 8）"
        assert [r for r, _ in check_line(line, self.sections)] == ["dangling-section"]

    def test_reports_every_dangling_ref_on_one_line(self) -> None:
        line = "execution-loop §4.4 / §4.6 both gone"
        assert [r for r, _ in check_line(line, self.sections)] == [
            "dangling-section",
            "dangling-section",
        ]


# --------------------------------------------------------------------------
# rule: positional-hitl-index
# --------------------------------------------------------------------------


class TestPositionalHitlIndex:
    sections = {"3.1"}

    @pytest.mark.parametrize(
        "line",
        [
            "§3.1 必停 10 自动 HITL",
            "违反 §3.1 必停 10/11；ADR-015",
            "§3.1 必停 10/13（runtime-skill-content-change）",
            "guardrail 放宽是 §3.1 必停 13",
        ],
    )
    def test_flags_positional_index(self, line: str) -> None:
        assert "positional-hitl-index" in [r for r, _ in check_line(line, self.sections)]

    @pytest.mark.parametrize(
        "line",
        [
            "§3.1 必停 4 项：runtime-skill-content-change / ...",
            "本豁免范围不包含 §3.1 通用必停 12 项",
            "§3.1 必停 16 项（通用 12 + 专属 4）",
        ],
    )
    def test_does_not_flag_a_count(self, line: str) -> None:
        # REGRESSION PIN: with a backtracking quantifier, `必停 12 项` degraded
        # into a spurious `必停 1` match that slipped past the `项` guard.
        # The possessive `++` is what stops that -- keep it.
        assert [r for r, _ in check_line(line, self.sections)] == []

    def test_named_enum_is_the_accepted_form(self) -> None:
        line = "§3.1 必停面 `runtime-skill-content-change` 触发"
        assert check_line(line, self.sections) == []


# --------------------------------------------------------------------------
# file discovery
# --------------------------------------------------------------------------


class TestIterScannedFiles:
    def test_collects_face_dirs_and_root_files(self, tmp_path: Path) -> None:
        _make_tree(tmp_path, {"policies/p.md": "x", "CLAUDE.md": "y"})
        found = {p.relative_to(tmp_path).as_posix() for p in iter_scanned_files(tmp_path)}
        assert "policies/p.md" in found
        assert "CLAUDE.md" in found
        assert KERNEL_REL.as_posix() in found

    def test_skips_archive_and_generated_projections(self, tmp_path: Path) -> None:
        _make_tree(
            tmp_path,
            {
                "docs/archive/old.md": "x",
                ".claude/skills/s/SKILL.md": "y",
            },
        )
        (tmp_path / ".agents" / "skills").mkdir(parents=True)
        (tmp_path / ".agents" / "skills" / "proj.md").write_text("z", encoding="utf-8")
        found = {p.relative_to(tmp_path).as_posix() for p in iter_scanned_files(tmp_path)}
        assert "docs/archive/old.md" not in found
        assert not any(f.startswith(".agents/") for f in found)
        assert ".claude/skills/s/SKILL.md" in found

    def test_missing_face_dirs_are_tolerated(self, tmp_path: Path) -> None:
        _make_tree(tmp_path)
        assert iter_scanned_files(tmp_path)  # only the kernel exists; no crash


# --------------------------------------------------------------------------
# exit codes (synthetic trees only)
# --------------------------------------------------------------------------


class TestMain:
    def test_clean_tree_exits_zero(self, tmp_path: Path) -> None:
        _make_tree(tmp_path, {"policies/ok.md": "see execution-loop §4.1 map\n"})
        assert main([], repo_root=tmp_path) == 0

    def test_injected_dangling_ref_is_caught(self, tmp_path: Path) -> None:
        # AC-3 negative test: prove the gate can fail.
        _make_tree(tmp_path, {"policies/bad.md": "see execution-loop §4.99 nowhere\n"})
        assert main([], repo_root=tmp_path) == 1

    def test_injected_positional_index_is_caught(self, tmp_path: Path) -> None:
        _make_tree(tmp_path, {"docs/bad.md": "触 §3.1 必停 12 强制 HITL\n"})
        assert main([], repo_root=tmp_path) == 1

    def test_missing_kernel_exits_two(self, tmp_path: Path) -> None:
        (tmp_path / "policies").mkdir()
        assert main([], repo_root=tmp_path) == 2

    def test_unparseable_kernel_exits_two(self, tmp_path: Path) -> None:
        # Fail-closed, not fail-open: a kernel with no numbered headings is a
        # broken input, not a clean result.
        _write(tmp_path, str(KERNEL_REL), "# No numbered sections here\n")
        assert main([], repo_root=tmp_path) == 2


# --------------------------------------------------------------------------
# real-tree pins
# --------------------------------------------------------------------------


class TestLiveTree:
    def test_kernel_heading_set_is_parseable_and_bounded(self) -> None:
        sections = parse_kernel_sections(REPO_ROOT / KERNEL_REL)
        # §4 has exactly two children -- the fact that started #453.
        assert {"4", "4.1", "4.2"} <= sections
        assert not {s for s in sections if s.startswith("4.") and s not in {"4.1", "4.2"}}
        # The kernel stops at §8; §11 / §12 refs are stage numbers, not sections.
        assert "11" not in sections
        assert "12" not in sections

    def test_live_tree_has_no_violations(self) -> None:
        # AC-2 regression pin.
        assert main([], repo_root=REPO_ROOT) == 0
