"""Unit tests for V5 sub-flags (M3-FU-V5-SUBFLAGS).

Covers --bdd / --tdd / --compose-config additive sub-mode checks beyond
V5 5.1 core lint.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from scripts.sdd._common import Summary
from scripts.sdd.check_docker_contracts import (
    _check_compose_bdd,
    _check_compose_config,
    _check_compose_tdd,
    _check_docker_bdd,
    _check_docker_tdd,
)

# -------- --bdd --------


def test_bdd_docker_missing_healthcheck_warns() -> None:
    summary = Summary()
    _check_docker_bdd({}, summary)
    assert summary.warn_count >= 1
    assert any("healthcheck" in m for m in summary.messages)


def test_bdd_docker_healthcheck_missing_cmd_warns() -> None:
    summary = Summary()
    _check_docker_bdd({"healthcheck": {"interval": "30s"}}, summary)
    assert summary.warn_count >= 1
    assert any("healthcheck.cmd missing" in m for m in summary.messages)


def test_bdd_docker_healthcheck_present_passes() -> None:
    summary = Summary()
    _check_docker_bdd({"healthcheck": {"cmd": "mj-agent check"}}, summary)
    assert summary.warn_count == 0


def test_bdd_compose_service_missing_healthcheck_warns() -> None:
    summary = Summary()
    _check_compose_bdd({"services": {"svc1": {"image": "x"}}}, summary)
    assert summary.warn_count >= 1
    assert any("'svc1'" in m and "healthcheck" in m for m in summary.messages)


def test_bdd_compose_all_services_have_healthcheck_passes() -> None:
    summary = Summary()
    _check_compose_bdd(
        {"services": {"svc1": {"healthcheck": {"cmd": "ping"}}}}, summary
    )
    assert summary.warn_count == 0


# -------- --tdd --------


def test_tdd_docker_missing_runtime_stage_warns() -> None:
    summary = Summary()
    _check_docker_tdd({}, summary)
    assert summary.warn_count >= 1
    assert any("runtime_stage_contract" in m for m in summary.messages)


def test_tdd_docker_runtime_stage_missing_subfields_warns() -> None:
    summary = Summary()
    _check_docker_tdd({"runtime_stage_contract": {"user": {}}}, summary)
    assert summary.warn_count >= 2  # forbidden_in_image + entrypoint missing
    assert any("'forbidden_in_image'" in m for m in summary.messages)
    assert any("'entrypoint'" in m for m in summary.messages)


def test_tdd_compose_missing_invocation_contract_warns() -> None:
    summary = Summary()
    _check_compose_tdd({}, summary)
    assert summary.warn_count >= 1
    assert any("invocation_contract" in m for m in summary.messages)


def test_tdd_compose_invocation_missing_one_profile_warns() -> None:
    summary = Summary()
    _check_compose_tdd(
        {"invocation_contract": {"dev_command": "x", "test_command": "y"}},
        summary,
    )
    assert summary.warn_count >= 1
    assert any("prod_command" in m for m in summary.messages)


def test_tdd_compose_all_three_profiles_passes() -> None:
    summary = Summary()
    _check_compose_tdd(
        {
            "invocation_contract": {
                "dev_command": "x",
                "test_command": "y",
                "prod_command": "z",
            }
        },
        summary,
    )
    assert summary.warn_count == 0


# -------- --compose-config --------


def test_compose_config_base_missing_services_warns(tmp_path: Path) -> None:
    base = tmp_path / "base.yml"
    base.write_text(yaml.safe_dump({"networks": {}}), encoding="utf-8")
    summary = Summary()
    _check_compose_config(["base.yml"], tmp_path, summary)
    assert summary.warn_count >= 1
    assert any("missing top-level 'services' key" in m for m in summary.messages)


def test_compose_config_overlay_inherits_image_passes(tmp_path: Path) -> None:
    """Base declares image; overlay only adds env — no WARN per merge semantics."""
    base = tmp_path / "base.yml"
    base.write_text(
        yaml.safe_dump({"services": {"svc1": {"image": "alpine:3"}}}),
        encoding="utf-8",
    )
    overlay = tmp_path / "overlay.yml"
    overlay.write_text(
        yaml.safe_dump({"services": {"svc1": {"environment": {"X": "1"}}}}),
        encoding="utf-8",
    )
    summary = Summary()
    _check_compose_config(["base.yml", "overlay.yml"], tmp_path, summary)
    assert summary.warn_count == 0


def test_compose_config_service_missing_image_anywhere_warns(tmp_path: Path) -> None:
    base = tmp_path / "base.yml"
    base.write_text(
        yaml.safe_dump({"services": {"orphan_svc": {"environment": {"X": "1"}}}}),
        encoding="utf-8",
    )
    summary = Summary()
    _check_compose_config(["base.yml"], tmp_path, summary)
    assert summary.warn_count >= 1
    assert any("'orphan_svc'" in m and "neither 'image' nor 'build'" in m for m in summary.messages)


def test_compose_config_yaml_load_failure_warns(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text("not a mapping", encoding="utf-8")
    summary = Summary()
    _check_compose_config(["bad.yml"], tmp_path, summary)
    assert summary.warn_count >= 1
    assert any("YAML root is not a mapping" in m for m in summary.messages)


def test_compose_config_missing_file_skipped_silently(tmp_path: Path) -> None:
    """Missing file already FAILed by core lint; --compose-config skips to avoid dup."""
    summary = Summary()
    _check_compose_config(["nonexistent.yml"], tmp_path, summary)
    assert summary.warn_count == 0
