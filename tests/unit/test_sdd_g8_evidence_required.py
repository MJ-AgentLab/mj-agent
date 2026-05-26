"""Unit tests for G8 check_capability_evidence_required validator.

Per Stage D D-1 + sdd/gates.md L30 + L96 (Phase M4 BLOCKING) +
sdd/lifecycle.md L69 (verifying → active gate):

G8 trigger semantic (per most-specific-SoT sdd/lifecycle.md L69):
- Validator fires when capability `lifecycle_state: active`
- Requires evidence/ subdir ≥1 non-.gitkeep file
- Capabilities with lifecycle_state != active → SKIP (validator dormant)

Stage A test_sdd_g1g2g9_validators.py precedent: synthetic spec.yml +
tmp_path fixture for branch coverage (PASS / FAIL / SKIP).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.sdd.check_capability_evidence_required import (
    _has_evidence,
    _validate_capability,
)


def _baseline_spec(lifecycle_state: str = "active") -> dict:
    """Synthetic baseline spec.yml mapping."""
    return {
        "id": "data-agent.x",
        "name": "X",
        "domain": "data-agent",
        "lifecycle_state": lifecycle_state,
        "archive_state": "active",
        "adapter_coverage": ["python"],
        "last_verified": "2026-05-26",
        "owner": "ranzuozhou",
        "created": "2026-05-26",
        "updated": "2026-05-26",
        "summary": "test capability",
        "requirements": [
            {
                "id": "REQ-001",
                "statement": "test statement",
                "rationale": "test rationale",
                "priority": "critical",
            },
        ],
    }


def _setup_capability(
    tmp_path: Path,
    name: str = "x",
    lifecycle_state: str = "active",
) -> Path:
    """Create synthetic capability dir with spec.yml + empty evidence/."""
    cap_dir = tmp_path / "capabilities" / "data-agent" / name
    cap_dir.mkdir(parents=True, exist_ok=True)
    spec = _baseline_spec(lifecycle_state=lifecycle_state)
    (cap_dir / "spec.yml").write_text(yaml.safe_dump(spec), encoding="utf-8")
    (cap_dir / "evidence").mkdir(exist_ok=True)
    return cap_dir


class TestG8EvidenceRequired:
    """G8 validator branch coverage: PASS / FAIL / SKIP."""

    def test_active_with_evidence_passes(self, tmp_path: Path) -> None:
        """lifecycle_state: active + evidence/<file>.md → PASS."""
        cap = _setup_capability(tmp_path, lifecycle_state="active")
        (cap / "evidence" / "report.md").write_text("# evidence", encoding="utf-8")
        summary = _validate_capability(cap, tmp_path)
        assert summary.pass_count == 1
        assert summary.fail_count == 0
        assert summary.warn_count == 0

    def test_active_without_evidence_fails(self, tmp_path: Path) -> None:
        """lifecycle_state: active + evidence/ empty → FAIL with capability path."""
        cap = _setup_capability(tmp_path, lifecycle_state="active")
        summary = _validate_capability(cap, tmp_path)
        assert summary.fail_count == 1
        assert summary.pass_count == 0
        assert any("evidence/ is empty" in m for m in summary.messages)

    def test_active_only_gitkeep_fails(self, tmp_path: Path) -> None:
        """lifecycle_state: active + evidence/.gitkeep only → FAIL (.gitkeep excluded)."""
        cap = _setup_capability(tmp_path, lifecycle_state="active")
        (cap / "evidence" / ".gitkeep").write_text("", encoding="utf-8")
        summary = _validate_capability(cap, tmp_path)
        assert summary.fail_count == 1
        assert summary.pass_count == 0

    def test_drafting_state_skips(self, tmp_path: Path) -> None:
        """lifecycle_state: drafting → SKIP (no PASS/WARN/FAIL counted)."""
        cap = _setup_capability(tmp_path, lifecycle_state="drafting")
        summary = _validate_capability(cap, tmp_path)
        assert summary.pass_count == 0
        assert summary.fail_count == 0
        assert summary.warn_count == 0
        assert summary.messages == []

    def test_has_evidence_helper(self, tmp_path: Path) -> None:
        """_has_evidence: True iff ≥1 non-.gitkeep file in evidence/."""
        cap_dir = tmp_path / "cap1"
        cap_dir.mkdir()
        evidence = cap_dir / "evidence"
        evidence.mkdir()
        assert _has_evidence(cap_dir) is False  # empty dir

        (evidence / ".gitkeep").write_text("", encoding="utf-8")
        assert _has_evidence(cap_dir) is False  # only .gitkeep

        (evidence / "report.md").write_text("# r", encoding="utf-8")
        assert _has_evidence(cap_dir) is True  # has real file
