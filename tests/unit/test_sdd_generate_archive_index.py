"""Unit tests for generate_archive_index (M5-PR0 gate-prep).

Mirrors test_sdd_g1g2g9_validators.py G9 tests: synthetic archive.yml
manifests under tmp_path, exercise _build_index_content + drift detection.
M5-PR0 wires the --check step WARNING-mode only.

Synthetic-fixture tests (tmp_path) prove:
- (a) no archive/ → main() exit 0 / clean no-op
- valid manifests → INDEX rows emitted
- idempotent regeneration (byte-identical)
- (f) --check drift detection (committed bytes != regenerated) → WARN
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd.generate_archive_index import _build_index_content, main


def _write_unit(archive_dir: Path, rel: str, manifest: dict) -> Path:
    unit_dir = archive_dir / rel
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / "archive.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return unit_dir


def _manifest(original_path: str, ai_visibility: str = "hidden") -> dict:
    return {
        "archived_at": "2026-06-01",
        "reason": "superseded by sdd/constitution.md",
        "original_path": original_path,
        "ai_visibility": ai_visibility,
        "retention_class": "permanent",
        "superseded_by": ["sdd/constitution.md", "policies/data-boundary.md"],
    }


# -------- (a) no archive/ → main() no-op --------


def test_no_archive_dir_is_noop(capsys, tmp_path: Path) -> None:
    """No archive/ under repo_root → main() returns 0 with a clean no-op line.

    Isolated against an empty tmp repo_root (the real tree has a populated
    archive/ since M5-PR3b).
    """
    assert main(["--check"], repo_root=tmp_path) == 0
    out = capsys.readouterr().out
    assert "no archive/ yet" in out


# -------- build content --------


def test_build_emits_header_and_row(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/old-std", _manifest("docs/rule/[STANDARD]_Old_v1.0.md"))
    content = _build_index_content(archive_dir)
    assert "# archive/ INDEX (auto-generated)" in content
    assert "docs/rule/[STANDARD]_Old_v1.0.md" in content
    assert "hidden" in content
    assert "sdd/constitution.md, policies/data-boundary.md" in content


def test_build_empty_emits_placeholder(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)
    content = _build_index_content(archive_dir)
    assert "_(none)_" in content


def test_build_pipe_escaped_in_cells(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    m = _manifest("docs/a|b.md")
    m["reason"] = "reason with | pipe"
    _write_unit(archive_dir, "rule/x", m)
    content = _build_index_content(archive_dir)
    assert "docs/a\\|b.md" in content
    assert "reason with \\| pipe" in content


# -------- idempotency --------


def test_idempotent_regeneration(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/a", _manifest("docs/rule/a.md"))
    _write_unit(archive_dir, "decisions/b", _manifest("decisions/b.md", "reference"))
    first = _build_index_content(archive_dir)
    second = _build_index_content(archive_dir)
    assert first == second


# -------- (f) --check drift detection --------


def test_check_matches_committed_passes(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/a", _manifest("docs/rule/a.md"))
    generated = _build_index_content(archive_dir)
    # Write committed INDEX.md matching generated content.
    (archive_dir / "INDEX.md").write_text(generated, encoding="utf-8")
    committed = (archive_dir / "INDEX.md").read_text(encoding="utf-8")
    assert committed == generated  # no drift


def test_check_detects_drift(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_unit(archive_dir, "rule/a", _manifest("docs/rule/a.md"))
    generated = _build_index_content(archive_dir)
    # Committed file is stale (extra line) → drift.
    (archive_dir / "INDEX.md").write_text(generated + "STALE EXTRA LINE\n", encoding="utf-8")
    committed = (archive_dir / "INDEX.md").read_text(encoding="utf-8")
    assert committed != generated  # drift present
