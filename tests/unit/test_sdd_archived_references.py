"""Unit tests for G14/G15 check_archived_references validator (M5-PR0 gate-prep).

Per sdd/gates.md G14/G15: active (non-archive) files must not reference
archive/ paths UNLESS the referenced unit's archive.yml has
ai_visibility: reference, OR the file is allowlisted (CHANGELOG.md), OR the
line carries an explicit ai_visibility=reference marker. M5-PR0 wires the
gate WARNING-mode only.

Synthetic-fixture tests (tmp_path) prove:
- (a) no archive/ → main() exit 0 / clean no-op
- (e) archived ref with ai_visibility=reference → OK (PASS) vs hidden → WARN
- file allowlist (CHANGELOG.md) → PASS
- line-level ai_visibility=reference marker → PASS
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd.check_archived_references import (
    _resolve_unit_visibility,
    _scan_file,
    main,
)


def _write_unit(archive_dir: Path, rel: str, ai_visibility: str) -> Path:
    """Create an archive unit with a minimal archive.yml at archive_dir/rel."""
    unit_dir = archive_dir / rel
    unit_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "archived_at": "2026-06-01",
        "reason": "superseded for test purposes",
        "original_path": f"docs/rule/{rel}.md",
        "ai_visibility": ai_visibility,
        "retention_class": "permanent",
    }
    (unit_dir / "archive.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (unit_dir / "doc.md").write_text("# archived content", encoding="utf-8")
    return unit_dir


# -------- (a) no archive/ → main() no-op --------


def test_no_archive_dir_is_noop(capsys) -> None:
    """No top-level archive/ → main() returns 0 with a clean no-op line."""
    assert main(["--all"]) == 0
    out = capsys.readouterr().out
    assert "no archive/ yet" in out


# -------- ai_visibility resolution --------


def test_resolve_visibility_reference(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", "reference")
    assert _resolve_unit_visibility(archive_dir, "rule/old-std/doc.md") == "reference"


def test_resolve_visibility_hidden(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", "hidden")
    assert _resolve_unit_visibility(archive_dir, "rule/old-std/doc.md") == "hidden"


def test_resolve_visibility_no_manifest(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)
    assert _resolve_unit_visibility(archive_dir, "rule/nonexistent/doc.md") is None


# -------- (e) reference → OK vs hidden → WARN --------


def test_reference_unit_is_ok(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", "reference")
    active = tmp_path / "docs" / "note.md"
    active.parent.mkdir(parents=True)
    active.write_text("See archive/rule/old-std/doc.md for history.\n", encoding="utf-8")
    summary = _scan_file(active, active.relative_to(tmp_path), archive_dir, tmp_path)
    assert summary.pass_count == 1
    assert summary.warn_count == 0


def test_hidden_unit_warns(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", "hidden")
    active = tmp_path / "docs" / "note.md"
    active.parent.mkdir(parents=True)
    active.write_text("See archive/rule/old-std/doc.md for history.\n", encoding="utf-8")
    summary = _scan_file(active, active.relative_to(tmp_path), archive_dir, tmp_path)
    assert summary.warn_count == 1
    assert summary.pass_count == 0
    assert any("not permitted" in m for m in summary.messages)


def test_unresolvable_ref_warns(tmp_path: Path) -> None:
    """archive/ ref with no resolvable archive.yml → WARN."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)
    active = tmp_path / "docs" / "note.md"
    active.parent.mkdir(parents=True)
    active.write_text("Broken: archive/rule/ghost/doc.md\n", encoding="utf-8")
    summary = _scan_file(active, active.relative_to(tmp_path), archive_dir, tmp_path)
    assert summary.warn_count == 1
    assert any("no resolvable archive.yml" in m for m in summary.messages)


# -------- allowlist + line marker --------


def test_changelog_file_allowlisted(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", "hidden")  # hidden, but file allowlisted
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("- moved to archive/rule/old-std/doc.md\n", encoding="utf-8")
    summary = _scan_file(changelog, changelog.relative_to(tmp_path), archive_dir, tmp_path)
    assert summary.pass_count == 1
    assert summary.warn_count == 0


def test_line_reference_marker_permits(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", "hidden")  # hidden, but line marker overrides
    active = tmp_path / "docs" / "note.md"
    active.parent.mkdir(parents=True)
    active.write_text(
        "Cite archive/rule/old-std/doc.md (ai_visibility=reference)\n", encoding="utf-8"
    )
    summary = _scan_file(active, active.relative_to(tmp_path), archive_dir, tmp_path)
    assert summary.pass_count == 1
    assert summary.warn_count == 0


def test_no_archive_ref_no_findings(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)
    active = tmp_path / "docs" / "note.md"
    active.parent.mkdir(parents=True)
    active.write_text("No archive references here, just src/foo.py.\n", encoding="utf-8")
    summary = _scan_file(active, active.relative_to(tmp_path), archive_dir, tmp_path)
    assert summary.pass_count == 0
    assert summary.warn_count == 0
    assert summary.fail_count == 0
