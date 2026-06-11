"""Unit tests for G7 secret exposure validator (completion-audit PR2).

All three checks are exercised via DI-injected inputs (file lists / text) —
no real `git ls-files` or filesystem reads, mirroring the G24 N-1 DI pattern.
"""

from __future__ import annotations

from scripts.sdd.check_secret_exposure import (
    _check_build_context,
    _check_gitignore_pins,
    _check_tracked_files,
)

_CLEAN_TRACKED = [
    ".env.example",
    "config/secrets.enc",
    "config/secrets-mcp.enc",
    "src/mj_agent/config.py",
    "docker/Dockerfile",
]


class TestTrackedFiles:
    def test_clean_tree_passes_and_allows_enc_ciphertext(self) -> None:
        summary = _check_tracked_files(_CLEAN_TRACKED)
        assert summary.fail_count == 0
        assert summary.pass_count == 1

    def test_tracked_env_fails(self) -> None:
        summary = _check_tracked_files([*_CLEAN_TRACKED, ".env"])
        assert summary.fail_count == 1

    def test_tracked_decrypted_conf_and_key_material_fail(self) -> None:
        summary = _check_tracked_files(
            [*_CLEAN_TRACKED, "config/secrets.conf", "deploy/server.pem", "id_rsa.key"]
        )
        assert summary.fail_count == 3

    def test_env_example_is_allowed(self) -> None:
        summary = _check_tracked_files([".env.example"])
        assert summary.fail_count == 0


class TestGitignorePins:
    def test_all_pins_present_passes(self) -> None:
        text = ".env\nconfig/secrets.conf\nconfig/secrets-mcp.conf\n*.log\n"
        summary = _check_gitignore_pins(text)
        assert summary.warn_count == 0
        assert summary.pass_count == 1

    def test_missing_pin_warns(self) -> None:
        summary = _check_gitignore_pins(".env\n*.log\n")
        assert summary.warn_count == 1
        assert any("config/secrets.conf" in m for m in summary.messages)

    def test_missing_gitignore_warns(self) -> None:
        summary = _check_gitignore_pins(None)
        assert summary.warn_count == 1


class TestBuildContext:
    _DOCKERFILE_WITH_COPY = "FROM python:3.14-slim\nCOPY config/ ./config/\n"
    _OVERRIDE_REPO_ROOT = "services:\n  mj-agent:\n    build:\n      context: ../\n"

    def test_copy_config_repo_root_context_no_dockerignore_warns(self) -> None:
        summary = _check_build_context(
            self._DOCKERFILE_WITH_COPY, self._OVERRIDE_REPO_ROOT, False
        )
        assert summary.warn_count == 1
        assert any(".dockerignore" in m for m in summary.messages)

    def test_root_dockerignore_present_passes(self) -> None:
        summary = _check_build_context(
            self._DOCKERFILE_WITH_COPY, self._OVERRIDE_REPO_ROOT, True
        )
        assert summary.warn_count == 0
        assert summary.pass_count == 1

    def test_no_config_copy_passes(self) -> None:
        summary = _check_build_context(
            "FROM python:3.14-slim\nCOPY src/ ./src/\n", self._OVERRIDE_REPO_ROOT, False
        )
        assert summary.warn_count == 0
        assert summary.pass_count == 1
