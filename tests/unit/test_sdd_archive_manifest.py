"""Unit tests for G11/G12 check_archive_manifest validator (M5-PR0 gate-prep).

Per sdd/gates.md G11/G12 + sdd/archive.schema.json (5 required fields +
ai_visibility / retention_class / original_state enums). M5-PR0 wires the
gate WARNING-mode only; the blocking flip is deferred to the M5 move PRs.

Synthetic-fixture tests (tmp_path) prove:
- (a) no archive/ → main() exit 0 / clean no-op
- (b) valid archive.yml unit → PASS
- (c) missing required field → FAIL
- (d) bad enum value → FAIL
- (e) missing archive.yml for a content dir → FAIL (manifest)

Mirrors test_sdd_g8_evidence_required.py: synthetic fixtures + tmp_path,
exercise the per-unit helpers directly (they accept the repo_root arg).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd.check_archive_manifest import (
    _find_missing_manifest_dirs,
    _validate_manifest,
    main,
)


def _valid_manifest() -> dict:
    """Synthetic valid archive.yml mapping (5 required + valid enums)."""
    return {
        "archived_at": "2026-06-01",
        "reason": "superseded by sdd/constitution.md",
        "original_path": "docs/rule/[STANDARD]_Old_Framework_v1.0.md",
        "ai_visibility": "hidden",
        "retention_class": "permanent",
        "original_state": "deprecated",
        "superseded_by": ["sdd/constitution.md"],
    }


def _write_unit(archive_dir: Path, rel: str, manifest: dict | None, *, content: bool = True) -> Path:
    """Create an archive unit dir under archive_dir/rel with optional manifest + content."""
    unit_dir = archive_dir / rel
    unit_dir.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        (unit_dir / "archive.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    if content:
        (unit_dir / "doc.md").write_text("# archived content", encoding="utf-8")
    return unit_dir


# -------- (a) no archive/ → main() no-op --------


def test_no_archive_dir_is_noop(capsys, tmp_path: Path) -> None:
    """No archive/ under repo_root → main() returns 0 with a clean no-op line.

    Isolated against an empty tmp repo_root: since M5-PR3b the real tree has a
    populated top-level archive/, so we pass an empty repo_root to exercise the
    genuine no-op path rather than depending on repo state.
    """
    assert main(["--all"], repo_root=tmp_path) == 0
    out = capsys.readouterr().out
    assert "no archive/ yet" in out


# -------- (b) valid unit → PASS --------


def test_valid_manifest_passes(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    unit = _write_unit(archive_dir, "rule/old-std", _valid_manifest())
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.pass_count == 1
    assert summary.fail_count == 0
    assert summary.warn_count == 0


def test_reference_visibility_passes(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    manifest = _valid_manifest()
    manifest["ai_visibility"] = "reference"
    manifest["retention_class"] = "5-year"
    unit = _write_unit(archive_dir, "decisions/adr-010", manifest)
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.pass_count == 1
    assert summary.fail_count == 0


# -------- (c) missing required field → FAIL --------


def test_missing_required_field_fails(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    manifest = _valid_manifest()
    del manifest["ai_visibility"]
    unit = _write_unit(archive_dir, "rule/old-std", manifest)
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.fail_count >= 1
    assert summary.pass_count == 0
    assert any("missing required field" in m and "ai_visibility" in m for m in summary.messages)


# -------- (d) bad enum → FAIL --------


def test_bad_ai_visibility_enum_fails(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    manifest = _valid_manifest()
    manifest["ai_visibility"] = "public"  # not in {hidden, reference}
    unit = _write_unit(archive_dir, "rule/old-std", manifest)
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.fail_count >= 1
    assert summary.pass_count == 0
    assert any("ai_visibility 'public' not in" in m for m in summary.messages)


def test_bad_retention_class_enum_fails(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    manifest = _valid_manifest()
    manifest["retention_class"] = "forever"  # not in {permanent, 5-year, 1-year}
    unit = _write_unit(archive_dir, "rule/old-std", manifest)
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.fail_count >= 1
    assert any("retention_class 'forever' not in" in m for m in summary.messages)


def test_bad_original_state_enum_fails(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    manifest = _valid_manifest()
    manifest["original_state"] = "retired"  # not in 4-state enum
    unit = _write_unit(archive_dir, "rule/old-std", manifest)
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.fail_count >= 1
    assert any("original_state 'retired' not in" in m for m in summary.messages)


def test_non_mapping_root_fails(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    unit = archive_dir / "rule" / "bad"
    unit.mkdir(parents=True)
    (unit / "archive.yml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    summary = _validate_manifest(unit / "archive.yml", tmp_path)
    assert summary.fail_count == 1
    assert any("not a mapping" in m for m in summary.messages)


# -------- (e) missing archive.yml for a content dir → FAIL --------


def test_content_dir_without_manifest_fails(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    # Content present, NO archive.yml.
    _write_unit(archive_dir, "rule/orphan", manifest=None, content=True)
    summary = _find_missing_manifest_dirs(archive_dir, tmp_path)
    assert summary.fail_count == 1
    assert any("missing manifest" in m for m in summary.messages)


def test_content_dir_with_manifest_no_missing(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/ok", _valid_manifest(), content=True)
    summary = _find_missing_manifest_dirs(archive_dir, tmp_path)
    assert summary.fail_count == 0


def test_index_and_gitkeep_not_flagged(tmp_path: Path) -> None:
    """INDEX.md / .gitkeep in archive/ do not require a sibling archive.yml."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "INDEX.md").write_text("# archive index", encoding="utf-8")
    (archive_dir / ".gitkeep").write_text("", encoding="utf-8")
    summary = _find_missing_manifest_dirs(archive_dir, tmp_path)
    assert summary.fail_count == 0
