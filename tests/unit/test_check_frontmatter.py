"""Unit tests for ``scripts/check_frontmatter.py`` — the canonical-doc frontmatter gate.

Regression home for #429. The gate used to define "is canonical" as "has frontmatter":
``find_canonical_docs()`` only collected files whose text began with ``---``, so a canonical
doc that lost — or never had — frontmatter silently dropped out of the gate's scope while the
gate still exited 0. The coverage face is now the filesystem itself (every ``.md`` under
``SCAN_ROOTS``), with ``SKIP_PATH_PARTS`` carrying explicit, reviewable exemptions.

Filesystem tests run against ``tmp_path`` fixtures rather than ``main()`` against the live tree
(per ``tests/AGENTS.md``: "Scripts under test take an injectable repo root ... so fixtures run
against ``tmp_path``, not the live tree"), so building scratch dirs cannot flip a real-tree
precondition. Two real-tree pins at the end assert the committed corpus passes and that the
gate's coverage has no silent gap.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from scripts.check_frontmatter import (
    SCAN_ROOTS,
    check,
    find_scanned_docs,
    is_skipped,
    run,
    validate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

VALID_FM = (
    "---\n"
    "type: standard\n"
    "summary: a valid canonical doc\n"
    "owner: ranzuozhou\n"
    "created: 2026-08-05\n"
    "updated: 2026-08-05\n"
    "state: active\n"
    "track: shared\n"
    "---\n\n# Title\n\nbody\n"
)


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _meta(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "type": "standard",
        "summary": "s",
        "owner": "o",
        "created": "2026-08-05",
        "updated": "2026-08-05",
        "state": "active",
        "track": "shared",
    }
    base.update(overrides)
    return base


class TestFindScannedDocs:
    def test_collects_doc_without_frontmatter(self, tmp_path: Path) -> None:
        """THE #429 regression: a frontmatter-less doc must stay inside the gate's scope."""
        _write(tmp_path, "docs/lost_frontmatter.md", "# Y\n\nbody only\n")
        assert find_scanned_docs(tmp_path) == [Path("docs/lost_frontmatter.md")]

    def test_collects_doc_with_frontmatter(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/kept.md", VALID_FM)
        assert find_scanned_docs(tmp_path) == [Path("docs/kept.md")]

    def test_respects_skip_path_parts(self, tmp_path: Path) -> None:
        """``docs/_templates`` scaffolds stay exempt — the exemption is now the ONLY way out."""
        _write(tmp_path, "docs/_templates/TEMPLATE_X.md", "no frontmatter here\n")
        _write(tmp_path, "docs/real.md", VALID_FM)
        assert find_scanned_docs(tmp_path) == [Path("docs/real.md")]

    def test_absent_scan_root_is_skipped(self, tmp_path: Path) -> None:
        assert find_scanned_docs(tmp_path) == []

    def test_non_md_files_ignored(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/notes.txt", "text")
        _write(tmp_path, "docs/data.yaml", "k: v")
        assert find_scanned_docs(tmp_path) == []

    def test_scans_every_root_and_sorts(self, tmp_path: Path) -> None:
        _write(tmp_path, "plans/b.md", VALID_FM)
        _write(tmp_path, "decisions/a.md", VALID_FM)
        _write(tmp_path, "src/mj_agent/skills/s/SKILL.md", VALID_FM)
        _write(tmp_path, "src/mj_agent/prompts/system.md", VALID_FM)
        _write(tmp_path, "docs/c.md", VALID_FM)
        found = find_scanned_docs(tmp_path)
        assert found == sorted(found)
        assert len(found) == 5

    def test_nested_subdirectories_are_reached(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/infrastructure/cicd/INDEX.md", VALID_FM)
        assert find_scanned_docs(tmp_path) == [Path("docs/infrastructure/cicd/INDEX.md")]


class TestCheckMissingFrontmatter:
    def test_missing_frontmatter_is_a_violation(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/bare.md", "# Y\n\nbody only\n")
        bad = check(tmp_path)
        assert Path("docs/bare.md") in bad
        assert any("frontmatter" in v for v in bad[Path("docs/bare.md")])

    def test_missing_frontmatter_reports_one_message_not_seven(self, tmp_path: Path) -> None:
        """Short-circuit: don't degrade into seven 'missing required field' lines."""
        _write(tmp_path, "docs/bare.md", "body only\n")
        assert len(check(tmp_path)[Path("docs/bare.md")]) == 1

    def test_empty_frontmatter_block_is_a_violation(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/empty.md", "---\n---\n\nbody\n")
        assert Path("docs/empty.md") in check(tmp_path)

    def test_bom_prefixed_frontmatter_is_a_violation(self, tmp_path: Path) -> None:
        """Non-evasion: a UTF-8 BOM used to make a fully-valid doc invisible to the gate."""
        _write(tmp_path, "docs/bom.md", "\ufeff" + VALID_FM)
        bad = check(tmp_path)
        assert Path("docs/bom.md") in bad
        assert any("BOM" in v for v in bad[Path("docs/bom.md")])

    def test_valid_doc_is_clean(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/ok.md", VALID_FM)
        assert check(tmp_path) == {}

    def test_parse_error_is_reported_not_swallowed(self, tmp_path: Path) -> None:
        _write(tmp_path, "docs/broken.md", "---\ntype: [unclosed\n---\n\nbody\n")
        bad = check(tmp_path)
        assert Path("docs/broken.md") in bad


class TestValidate:
    def test_missing_required_fields_reported(self) -> None:
        meta = _meta()
        del meta["owner"]
        del meta["track"]
        violations = validate(meta, Path("docs/x.md"))
        assert any("`owner`" in v for v in violations)
        assert any("`track`" in v for v in violations)

    def test_forbidden_derives_from_rejected(self) -> None:
        violations = validate(_meta(derives_from="mj-system"), Path("docs/x.md"))
        assert any("derives_from" in v for v in violations)

    def test_archive_exempt_from_forbidden_field(self) -> None:
        violations = validate(
            _meta(state="deprecated", derives_from="mj-system"),
            Path("docs/archive/old.md"),
        )
        assert not any("derives_from" in v for v in violations)

    def test_bad_track_enum_rejected(self) -> None:
        assert any("track=" in v for v in validate(_meta(track="nope"), Path("docs/x.md")))

    def test_bad_state_enum_rejected(self) -> None:
        assert any("state=" in v for v in validate(_meta(state="nope"), Path("docs/x.md")))

    def test_type_specific_field_required_when_active(self) -> None:
        violations = validate(_meta(type="runbook"), Path("docs/r.md"))
        assert any("last-verified" in v for v in violations)

    def test_type_specific_field_lenient_when_draft(self) -> None:
        violations = validate(_meta(type="runbook", state="draft"), Path("docs/r.md"))
        assert not any("last-verified" in v for v in violations)


class TestRun:
    """The gate's core promise: exit non-zero when a doc leaves the schema, and name it."""

    def test_clean_tree_exits_zero(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write(tmp_path, "docs/ok.md", VALID_FM)
        assert run(tmp_path) == 0
        assert "OK" in capsys.readouterr().out

    def test_doc_stripped_of_frontmatter_fails_and_is_named(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """AC-2: strip a canonical doc's frontmatter -> gate MUST exit non-zero and name it.

        Before #429 this exited 0 with no output mentioning the file at all.
        """
        _write(tmp_path, "docs/kept.md", VALID_FM)
        target = _write(tmp_path, "docs/victim.md", VALID_FM)

        assert run(tmp_path) == 0  # baseline: both docs valid

        target.write_text("# Victim\n\nframtmatter deleted\n", encoding="utf-8")
        capsys.readouterr()  # drop baseline output

        assert run(tmp_path) == 1
        captured = capsys.readouterr()
        assert "victim.md" in captured.err

    def test_restoring_frontmatter_returns_to_zero(self, tmp_path: Path) -> None:
        """AC-2 second half: the failure is a function of the file, not sticky state."""
        target = _write(tmp_path, "docs/victim.md", "# no frontmatter\n")
        assert run(tmp_path) == 1
        target.write_text(VALID_FM, encoding="utf-8")
        assert run(tmp_path) == 0

    def test_schema_violation_still_fails(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Pre-existing behaviour must survive the refactor."""
        _write(tmp_path, "docs/bad_track.md", VALID_FM.replace("track: shared", "track: nope"))
        assert run(tmp_path) == 1
        assert "bad_track.md" in capsys.readouterr().err

    def test_empty_tree_exits_zero(self, tmp_path: Path) -> None:
        assert run(tmp_path) == 0


class TestRealTree:
    """Pins against the committed corpus — these are what CI actually exercises."""

    def test_live_tree_passes(self) -> None:
        assert run(REPO_ROOT) == 0

    def test_coverage_has_no_silent_gap(self) -> None:
        """AC-3: the gate's scope == every .md under SCAN_ROOTS minus explicit exemptions.

        The census below is deliberately computed WITHOUT the function under test and without
        any content-based predicate — that absence is precisely the property #429 is about.
        """
        census = {
            md.relative_to(REPO_ROOT)
            for scan_root in SCAN_ROOTS
            if (REPO_ROOT / scan_root).exists()
            for md in (REPO_ROOT / scan_root).rglob("*.md")
            if not is_skipped(md.relative_to(REPO_ROOT))
        }
        assert set(find_scanned_docs(REPO_ROOT)) == census
        assert census, "sanity: the live tree must contain canonical docs"
