"""Unit tests for scripts/sdd/check_runtime_skill_contracts.py.

Covers M3-FU-RUNTIME-SKILL-VALIDATOR AC §4: happy path + content_hash drift +
frontmatter_strip_contract violation + missing skills[] + version string-exact
drift. Tests use tmp_path fixtures with synthetic SKILL.md + contract YAML so
they run without touching the real `capabilities/` tree.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml
from scripts.sdd.check_runtime_skill_contracts import _validate_contract


def _skill_md_body() -> str:
    return (
        "# Skill: test-skill\n"
        "\n"
        "## Purpose\n"
        "Test purpose.\n"
        "\n"
        "## When to use\n"
        "When testing.\n"
    )


def _skill_md_full() -> str:
    return (
        "---\n"
        "type: skill\n"
        "version: v0.1\n"
        "state: active\n"
        "---\n"
    ) + _skill_md_body()


def _expected_body_hash() -> str:
    body = _skill_md_body()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _write_skill_and_contract(
    tmp_path: Path,
    *,
    skill_text: str | None = None,
    contract_overrides: dict | None = None,
    skill_entry_overrides: dict | None = None,
) -> Path:
    """Write SKILL.md + contract.yml under tmp_path; return contract path."""
    skill_dir = tmp_path / "src" / "mj_agent" / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        skill_text if skill_text is not None else _skill_md_full(),
        encoding="utf-8",
    )

    contract_dir = tmp_path / "capabilities" / "domain" / "cap" / "contracts"
    contract_dir.mkdir(parents=True)
    skill_entry = {
        "file": "src/mj_agent/skills/test-skill/SKILL.md",
        "version": "v0.1",
        "state": "active",
        "body_section_heads": ["## Purpose", "## When to use"],
        "content_hash": f"sha256:{_expected_body_hash()}",
    }
    if skill_entry_overrides:
        skill_entry.update(skill_entry_overrides)

    contract = {
        "contract_id": "runtime-skill",
        "adapter": "runtime-skill",
        "frontmatter_strip_contract": True,
        "loader": "load_skill",
        "skills": [skill_entry],
    }
    if contract_overrides:
        contract.update(contract_overrides)

    contract_path = contract_dir / "runtime-skill.contract.yml"
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    return contract_path


def test_happy_path_passes(tmp_path: Path) -> None:
    contract_path = _write_skill_and_contract(tmp_path)
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count == 0
    assert summary.warn_count == 0
    assert summary.pass_count == 1


def test_content_hash_drift_fails(tmp_path: Path) -> None:
    """Body modified after contract anchor → FAIL on hash drift."""
    drifted_skill = (
        "---\nversion: v0.1\nstate: active\n---\n"
        "# Skill: test-skill\n\n## Purpose\nDRIFTED BODY.\n"
    )
    contract_path = _write_skill_and_contract(tmp_path, skill_text=drifted_skill)
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("BODY CONTENT HASH DRIFT" in m for m in summary.messages)


def test_frontmatter_strip_contract_must_be_true(tmp_path: Path) -> None:
    contract_path = _write_skill_and_contract(
        tmp_path,
        contract_overrides={"frontmatter_strip_contract": False},
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("frontmatter_strip_contract MUST be true" in m for m in summary.messages)


def test_empty_skills_list_fails(tmp_path: Path) -> None:
    contract_path = _write_skill_and_contract(
        tmp_path,
        contract_overrides={"skills": []},
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("skills list is empty" in m for m in summary.messages)


def test_version_string_exact_v_prefix_drift_fails(tmp_path: Path) -> None:
    """`v0.1` in frontmatter vs `0.1` in contract → FAIL (string-exact required).

    Per M3-FU accumulated AC: no v-prefix strip / no normalize — any v-prefix
    diff is treated as explicit semantic change.
    """
    contract_path = _write_skill_and_contract(
        tmp_path,
        skill_entry_overrides={"version": "0.1"},
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("version mismatch" in m for m in summary.messages)


def test_state_string_exact_drift_fails(tmp_path: Path) -> None:
    contract_path = _write_skill_and_contract(
        tmp_path,
        skill_entry_overrides={"state": "deprecated"},
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("state mismatch" in m for m in summary.messages)


def test_missing_required_skill_field_fails(tmp_path: Path) -> None:
    """Removing 'content_hash' from a skill entry → FAIL."""
    skill_dir = tmp_path / "src" / "mj_agent" / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(_skill_md_full(), encoding="utf-8")

    contract_dir = tmp_path / "capabilities" / "domain" / "cap" / "contracts"
    contract_dir.mkdir(parents=True)
    contract = {
        "contract_id": "runtime-skill",
        "adapter": "runtime-skill",
        "frontmatter_strip_contract": True,
        "loader": "load_skill",
        "skills": [
            {
                "file": "src/mj_agent/skills/test-skill/SKILL.md",
                "version": "v0.1",
                "state": "active",
                "body_section_heads": ["## Purpose"],
                # content_hash deliberately omitted
            }
        ],
    }
    contract_path = contract_dir / "runtime-skill.contract.yml"
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")

    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("missing required field 'content_hash'" in m for m in summary.messages)


def test_skill_file_missing_fails(tmp_path: Path) -> None:
    contract_path = _write_skill_and_contract(
        tmp_path,
        skill_entry_overrides={"file": "src/mj_agent/skills/nonexistent/SKILL.md"},
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("skill file does not exist" in m for m in summary.messages)


def test_body_section_heads_mismatch_emits_warn_not_fail(tmp_path: Path) -> None:
    """Section name mismatch → WARN (not FAIL); content_hash is the strict gate."""
    contract_path = _write_skill_and_contract(
        tmp_path,
        skill_entry_overrides={
            "body_section_heads": ["## Purpose", "## NonexistentHeading"],
        },
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count == 0
    assert summary.warn_count >= 1
    assert any("not found in actual level-2 headings" in m for m in summary.messages)


def test_wrong_contract_id_fails(tmp_path: Path) -> None:
    contract_path = _write_skill_and_contract(
        tmp_path,
        contract_overrides={"contract_id": "wrong-adapter"},
    )
    summary = _validate_contract(contract_path, tmp_path)
    assert summary.fail_count >= 1
    assert any("contract_id is not 'runtime-skill'" in m for m in summary.messages)
