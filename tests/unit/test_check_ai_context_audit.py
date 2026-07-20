"""Unit tests for ``scripts/check_ai_context_audit.py`` (A6 durability gate, #359;
ai-context-investigation schema added #362).

Schema-validation tests exercise ``validate_audit_entry()`` /
``validate_investigation_entry()`` on plain dicts (pure — no filesystem). ``run()`` /
``check()`` / ``find_entries()`` tests use ``tmp_path`` fixtures (git-init where the §2.1
derivation needs ``git ls-files``), never against the real tree — so building scratch dirs
cannot flip a real-tree precondition (per the structure-move lesson). ``TestRun`` covers the
gate's core promise (exit 1 on a schema violation) for BOTH entry types, BOM non-evasion,
and the parse-error branch. A real-tree pin confirms the committed Q2/Q3 audit + a2/a3
investigation entries pass and ``derive_face_set`` is well-formed (structural invariants,
not an exact count — the face-set is time-varying).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from scripts.check_ai_context_audit import (
    _ask_glob_md,
    _frozen_infra,
    check,
    derive_face_set,
    find_entries,
    run,
    validate_audit_entry,
    validate_investigation_entry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

VALID_AUDIT_MD = (
    "---\n"
    "type: ai-context-audit\n"
    "cycle: 2026-Q2\n"
    'auditor: "ai-agent (test)"\n'
    "scope:\n"
    "  - root-claude-md\n"
    'findings_summary: "baseline OK"\n'
    "content_hash_snapshot:\n"
    "  CLAUDE.md: 998d8d13c4b5ad9a\n"
    "---\nbody\n"
)


def _valid_meta() -> dict:
    return {
        "type": "ai-context-audit",
        "cycle": "2026-Q2",
        "auditor": "ai-agent (test)",
        "scope": ["root-claude-md", "freeze-surface-hashes"],
        "findings_summary": "baseline OK; no drift detected",
        "content_hash_snapshot": {
            "CLAUDE.md": "998d8d13c4b5ad9a",
            "src/mj_agent/prompts/system.md": "994d4a2d7fd3677f",
        },
    }


VALID_INVESTIGATION_MD = (
    "---\n"
    "type: ai-context-investigation\n"
    "investigation: test-investigation-slug\n"
    'auditor: "ai-agent (test)"\n'
    "scope:\n"
    "  - some-scope\n"
    'findings_summary: "found things"\n'
    "---\nbody\n"
)


def _valid_investigation_meta() -> dict:
    return {
        "type": "ai-context-investigation",
        "investigation": "a2-test-slug",
        "auditor": "ai-agent (test)",
        "scope": ["body-sha256-utility", "hash-algorithm-governance"],
        "findings_summary": "surfaced 2 latent issues; defer M5+",
    }


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestValidateAuditEntry:
    def test_valid_passes(self) -> None:
        assert validate_audit_entry(_valid_meta()) == []

    def test_64_char_hex_ok(self) -> None:
        meta = _valid_meta()
        meta["content_hash_snapshot"]["CLAUDE.md"] = "a" * 64
        assert validate_audit_entry(meta) == []

    def test_all_digit_int_hash_ok(self) -> None:
        # An unquoted 16-digit hash is YAML-coerced to int; the validator coerces it
        # back to str so a legitimately-computed all-digit hex still validates.
        meta = _valid_meta()
        meta["content_hash_snapshot"]["CLAUDE.md"] = 1234567890123456
        assert validate_audit_entry(meta) == []

    @pytest.mark.parametrize(
        "field",
        ["type", "cycle", "auditor", "scope", "findings_summary", "content_hash_snapshot"],
    )
    def test_missing_required_field(self, field: str) -> None:
        meta = _valid_meta()
        del meta[field]
        violations = validate_audit_entry(meta)
        assert any(field in msg for msg in violations), violations

    def test_wrong_type(self) -> None:
        meta = _valid_meta()
        meta["type"] = "ai-context-investigation"
        assert any("type must be" in msg for msg in validate_audit_entry(meta))

    @pytest.mark.parametrize("bad", ["2026-Q9", "2026-13", "foo", "2026-Q", "26-Q2", "2026-q2", "2026-Q0"])
    def test_bad_cycle(self, bad: str) -> None:
        meta = _valid_meta()
        meta["cycle"] = bad
        assert any("cycle=" in msg for msg in validate_audit_entry(meta)), bad

    def test_cycle_non_str(self) -> None:
        meta = _valid_meta()
        meta["cycle"] = 2026
        assert any("cycle=" in msg for msg in validate_audit_entry(meta))

    def test_empty_scope(self) -> None:
        meta = _valid_meta()
        meta["scope"] = []
        assert any("scope must be" in msg for msg in validate_audit_entry(meta))

    def test_scope_not_list(self) -> None:
        meta = _valid_meta()
        meta["scope"] = "root-claude-md"
        assert any("scope must be" in msg for msg in validate_audit_entry(meta))

    def test_scope_empty_string_item(self) -> None:
        meta = _valid_meta()
        meta["scope"] = ["ok", "  "]
        assert any("scope must be" in msg for msg in validate_audit_entry(meta))

    def test_empty_auditor(self) -> None:
        meta = _valid_meta()
        meta["auditor"] = "   "
        assert any("auditor" in msg for msg in validate_audit_entry(meta))

    def test_empty_findings_summary(self) -> None:
        meta = _valid_meta()
        meta["findings_summary"] = ""
        assert any("findings_summary" in msg for msg in validate_audit_entry(meta))

    def test_empty_snapshot(self) -> None:
        meta = _valid_meta()
        meta["content_hash_snapshot"] = {}
        assert any("non-empty mapping" in msg for msg in validate_audit_entry(meta))

    def test_snapshot_not_map(self) -> None:
        meta = _valid_meta()
        meta["content_hash_snapshot"] = ["a", "b"]
        assert any("non-empty mapping" in msg for msg in validate_audit_entry(meta))

    @pytest.mark.parametrize(
        "bad", ["xyz", "998D8D13C4B5AD9A", "998d8d13", "g98d8d13c4b5ad9a", "a" * 32, "a" * 63]
    )
    def test_bad_hex(self, bad: str) -> None:
        meta = _valid_meta()
        meta["content_hash_snapshot"]["CLAUDE.md"] = bad
        assert any("hex" in msg for msg in validate_audit_entry(meta)), bad

    def test_hex_float(self) -> None:
        meta = _valid_meta()
        meta["content_hash_snapshot"]["CLAUDE.md"] = 1.5
        assert any("hex" in msg for msg in validate_audit_entry(meta))


class TestValidateInvestigationEntry:
    def test_valid_passes(self) -> None:
        assert validate_investigation_entry(_valid_investigation_meta()) == []

    def test_valid_with_optionals_passes(self) -> None:
        meta = _valid_investigation_meta()
        meta.update(
            {
                "subtype": "readiness-eval",
                "phase": "M4-Stage-A-unit-A-2",
                "date": "2026-05-22",
                "related_episodes": ["#2-1 first", "#2-9 schema amendment"],
                "parent_artifacts": ["A-1 brief §0"],
                "schema_extension_request": True,
            }
        )
        assert validate_investigation_entry(meta) == []

    def test_no_content_hash_snapshot_required(self) -> None:
        # Key structural difference vs audit: investigations are not hash snapshots.
        meta = _valid_investigation_meta()
        assert "content_hash_snapshot" not in meta
        assert validate_investigation_entry(meta) == []

    @pytest.mark.parametrize(
        "field", ["type", "investigation", "auditor", "scope", "findings_summary"]
    )
    def test_missing_required_field(self, field: str) -> None:
        meta = _valid_investigation_meta()
        del meta[field]
        violations = validate_investigation_entry(meta)
        assert any(field in msg for msg in violations), violations

    def test_wrong_type(self) -> None:
        meta = _valid_investigation_meta()
        meta["type"] = "ai-context-audit"
        assert any("type must be" in msg for msg in validate_investigation_entry(meta))

    def test_empty_investigation(self) -> None:
        meta = _valid_investigation_meta()
        meta["investigation"] = "   "
        assert any("investigation must be" in msg for msg in validate_investigation_entry(meta))

    def test_investigation_non_str(self) -> None:
        meta = _valid_investigation_meta()
        meta["investigation"] = 123
        assert any("investigation must be" in msg for msg in validate_investigation_entry(meta))

    def test_empty_auditor(self) -> None:
        meta = _valid_investigation_meta()
        meta["auditor"] = ""
        assert any("auditor" in msg for msg in validate_investigation_entry(meta))

    def test_empty_scope(self) -> None:
        meta = _valid_investigation_meta()
        meta["scope"] = []
        assert any("scope must be" in msg for msg in validate_investigation_entry(meta))

    def test_scope_not_list(self) -> None:
        meta = _valid_investigation_meta()
        meta["scope"] = "some-scope"
        assert any("scope must be" in msg for msg in validate_investigation_entry(meta))

    def test_empty_findings_summary(self) -> None:
        meta = _valid_investigation_meta()
        meta["findings_summary"] = "   "
        assert any("findings_summary" in msg for msg in validate_investigation_entry(meta))

    def test_bad_related_episodes(self) -> None:
        # Optional list field is validated only when present.
        meta = _valid_investigation_meta()
        meta["related_episodes"] = "not-a-list"
        assert any(
            "related_episodes must be" in msg for msg in validate_investigation_entry(meta)
        )

    def test_bad_parent_artifacts(self) -> None:
        meta = _valid_investigation_meta()
        meta["parent_artifacts"] = ["ok", "  "]
        assert any(
            "parent_artifacts must be" in msg for msg in validate_investigation_entry(meta)
        )

    def test_empty_subtype(self) -> None:
        meta = _valid_investigation_meta()
        meta["subtype"] = ""
        assert any("subtype must be" in msg for msg in validate_investigation_entry(meta))


class TestFindEntries:
    def test_splits_cycle_investigation_other(self, tmp_path: Path) -> None:
        _write(tmp_path, "evidence/ai-context-audit/2026-Q2.md", VALID_AUDIT_MD)
        _write(tmp_path, "evidence/ai-context-audit/2026-Q3.md", VALID_AUDIT_MD)
        _write(
            tmp_path,
            "evidence/ai-context-audit/2026-05-22_a2-investigation.md",
            VALID_INVESTIGATION_MD,
        )
        _write(
            tmp_path,
            "evidence/ai-context-audit/2026-05-22_a3-readiness-eval.md",
            VALID_INVESTIGATION_MD,
        )
        _write(tmp_path, "evidence/ai-context-audit/SCHEMA.md", "# Schema\nno frontmatter")
        cycle, investigation, other = find_entries(tmp_path)
        assert Path("evidence/ai-context-audit/2026-Q2.md") in cycle
        assert Path("evidence/ai-context-audit/2026-Q3.md") in cycle
        assert Path("evidence/ai-context-audit/2026-05-22_a2-investigation.md") in investigation
        assert Path("evidence/ai-context-audit/2026-05-22_a3-readiness-eval.md") in investigation
        assert Path("evidence/ai-context-audit/SCHEMA.md") in other

    def test_absent_dir(self, tmp_path: Path) -> None:
        assert find_entries(tmp_path) == ([], [], [])


class TestRun:
    def test_valid_passes(self, tmp_path: Path) -> None:
        _write(tmp_path, "evidence/ai-context-audit/2026-Q2.md", VALID_AUDIT_MD)
        assert run(tmp_path) == 0

    def test_violating_fails(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "evidence/ai-context-audit/2026-Q3.md",
            "---\ntype: ai-context-audit\ncycle: 2026-Q3\n---\nbody",
        )
        assert run(tmp_path) == 1
        bad = check(tmp_path)
        assert bad[Path("evidence/ai-context-audit/2026-Q3.md")]

    def test_missing_type_cycle_file_caught_not_skipped(self, tmp_path: Path) -> None:
        # A real cycle FILENAME with no `type` must be FAILED (filename selection),
        # not silently skipped — the most basic authoring mistake a gate must catch.
        _write(
            tmp_path,
            "evidence/ai-context-audit/2026-Q4.md",
            "---\ncycle: 2026-Q4\nauditor: x\nscope:\n  - a\n"
            "findings_summary: y\ncontent_hash_snapshot:\n  CLAUDE.md: 998d8d13c4b5ad9a\n---\n",
        )
        assert run(tmp_path) == 1
        bad = check(tmp_path)
        assert any("type" in m for m in bad[Path("evidence/ai-context-audit/2026-Q4.md")])

    def test_bom_cycle_file_not_evaded(self, tmp_path: Path) -> None:
        # A UTF-8-BOM-prefixed malformed cycle file must NOT slip past the gate.
        path = tmp_path / "evidence/ai-context-audit/2026-Q4.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\xef\xbb\xbf---\ntype: ai-context-audit\ncycle: 2026-Q4\n---\nbody")
        assert run(tmp_path) == 1  # missing auditor/scope/findings_summary/content_hash_snapshot

    def test_wellformed_investigation_passes(self, tmp_path: Path) -> None:
        _write(tmp_path, "evidence/ai-context-audit/2026-Q2.md", VALID_AUDIT_MD)
        _write(
            tmp_path,
            "evidence/ai-context-audit/2026-05-22_a2-investigation.md",
            VALID_INVESTIGATION_MD,
        )
        assert run(tmp_path) == 0

    def test_malformed_investigation_fails(self, tmp_path: Path) -> None:
        # An investigation FILENAME with a bare `type` (missing investigation/auditor/
        # scope/findings_summary) must now be FAILED — #362 supersedes the old skip.
        rel = Path("evidence/ai-context-audit/2026-05-22_a2-investigation.md")
        _write(tmp_path, str(rel), "---\ntype: ai-context-investigation\n---\nbody")
        assert run(tmp_path) == 1
        assert check(tmp_path)[rel]

    def test_schema_and_non_entry_md_still_skipped(self, tmp_path: Path) -> None:
        # SCHEMA.md is neither a cycle (YYYY-QN.md) nor investigation (YYYY-MM-DD_*.md)
        # filename → reported as skipped, never validated.
        _write(tmp_path, "evidence/ai-context-audit/2026-Q2.md", VALID_AUDIT_MD)
        _write(tmp_path, "evidence/ai-context-audit/SCHEMA.md", "# Schema\nno frontmatter")
        assert run(tmp_path) == 0
        _cycle, _investigation, other = find_entries(tmp_path)
        assert Path("evidence/ai-context-audit/SCHEMA.md") in other

    def test_parse_error_branch(self, tmp_path: Path) -> None:
        _write(tmp_path, "evidence/ai-context-audit/2026-Q2.md", "---\ntype: [unclosed\n---\nx")
        bad = check(tmp_path)
        assert any(
            "parse error" in m for m in bad.get(Path("evidence/ai-context-audit/2026-Q2.md"), [])
        )


def _mini_repo(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".claude/settings.json",
        json.dumps(
            {
                "permissions": {
                    "ask": [
                        "Edit(./src/mj_agent/skills/**/SKILL.md)",
                        "Edit(./src/mj_agent/prompts/system.md)",
                        "Edit(./src/mj_agent/tools/sql/guardrail.py)",
                        "Edit(./src/mj_agent/biz_catalog/qcm_catalog.yaml)",
                    ]
                }
            }
        ),
    )
    _write(tmp_path, "src/mj_agent/skills/foo/SKILL.md", "x")
    _write(tmp_path, "src/mj_agent/skills/bar/SKILL.md", "x")
    _write(tmp_path, "src/mj_agent/prompts/system.md", "x")
    _write(
        tmp_path,
        "capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml",
        "skills:\n"
        "  - file: .claude/skills/mj-agent-infra-alpha/SKILL.md\n"
        "    name: mj-agent-infra-alpha\n"
        "  - file: .claude/skills/mj-agent-infra-beta/SKILL.md\n"
        "    name: mj-agent-infra-beta\n",
    )
    _write(tmp_path, "CLAUDE.md", "root")
    _write(tmp_path, "src/mj_agent/CLAUDE.md", "sub")


class TestDeriveComponents:
    def test_ask_glob_md_expands_and_excludes_non_md(self, tmp_path: Path) -> None:
        _mini_repo(tmp_path)
        got = _ask_glob_md(tmp_path)
        assert "src/mj_agent/skills/foo/SKILL.md" in got
        assert "src/mj_agent/skills/bar/SKILL.md" in got
        assert "src/mj_agent/prompts/system.md" in got
        assert not any(x.endswith(".py") or x.endswith(".yaml") for x in got)

    def test_frozen_infra_from_contract(self, tmp_path: Path) -> None:
        _mini_repo(tmp_path)
        assert _frozen_infra(tmp_path) == {
            ".claude/skills/mj-agent-infra-alpha/SKILL.md",
            ".claude/skills/mj-agent-infra-beta/SKILL.md",
        }


class TestDeriveFaceSet:
    def test_union_over_git_repo(self, tmp_path: Path) -> None:
        _mini_repo(tmp_path)
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
        faces = derive_face_set(tmp_path)
        assert set(faces) == {
            "CLAUDE.md",
            "src/mj_agent/CLAUDE.md",
            "src/mj_agent/skills/foo/SKILL.md",
            "src/mj_agent/skills/bar/SKILL.md",
            "src/mj_agent/prompts/system.md",
            ".claude/skills/mj-agent-infra-alpha/SKILL.md",
            ".claude/skills/mj-agent-infra-beta/SKILL.md",
        }
        assert faces == sorted(faces)


class TestRealTree:
    def test_committed_entries_pass(self) -> None:
        cycle, investigation, _other = find_entries(REPO_ROOT)
        assert len(cycle) >= 2  # 2026-Q2 + 2026-Q3
        assert len(investigation) >= 2  # 2026-05-22 a2 + a3 (green day-one, #362)
        assert check(REPO_ROOT) == {}

    def test_derive_structural_invariants(self) -> None:
        faces = derive_face_set(REPO_ROOT)
        assert len(faces) > 0
        assert "CLAUDE.md" in faces
        assert "src/mj_agent/prompts/system.md" in faces
        assert any(f.startswith(".claude/skills/mj-agent-infra-") for f in faces)
        claude = [f for f in faces if f.endswith("CLAUDE.md")]
        assert claude and all(c == "CLAUDE.md" or c.endswith("/CLAUDE.md") for c in claude)
