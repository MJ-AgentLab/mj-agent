"""Unit tests for G7 secret exposure validator (completion-audit PR2 + S2 #330).

All four checks are exercised via DI-injected inputs (file lists / text) —
no real `git ls-files` or filesystem reads, mirroring the G24 N-1 DI pattern.
Check (4) covers the generated .codex/config.toml content scan (env tables,
URL userinfo shapes, PREFIXED credential-key assignments, no-echo discipline).
"""

from __future__ import annotations

from scripts.sdd.check_secret_exposure import (
    _check_build_context,
    _check_codex_config,
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
    _DOCKERIGNORE_COVERING = "# comment\n.env\nconfig/secrets*.conf\n.git\n"
    _DOCKERIGNORE_UNRELATED = "# only hygiene, no secrets coverage\n.git\n.venv\n"

    def test_copy_config_repo_root_context_no_dockerignore_warns(self) -> None:
        summary = _check_build_context(
            self._DOCKERFILE_WITH_COPY, self._OVERRIDE_REPO_ROOT, None
        )
        assert summary.warn_count == 1
        assert any("NO root" in m for m in summary.messages)

    def test_root_dockerignore_with_secrets_coverage_passes(self) -> None:
        summary = _check_build_context(
            self._DOCKERFILE_WITH_COPY, self._OVERRIDE_REPO_ROOT, self._DOCKERIGNORE_COVERING
        )
        assert summary.warn_count == 0
        assert summary.pass_count == 1

    def test_root_dockerignore_without_coverage_warns(self) -> None:
        """An empty/unrelated .dockerignore must not satisfy the gate."""
        summary = _check_build_context(
            self._DOCKERFILE_WITH_COPY, self._OVERRIDE_REPO_ROOT, self._DOCKERIGNORE_UNRELATED
        )
        assert summary.warn_count == 1
        assert any("does NOT cover" in m for m in summary.messages)

    def test_explicit_file_pair_counts_as_coverage(self) -> None:
        summary = _check_build_context(
            self._DOCKERFILE_WITH_COPY,
            self._OVERRIDE_REPO_ROOT,
            "config/secrets.conf\nconfig/secrets-mcp.conf\n",
        )
        assert summary.warn_count == 0
        assert summary.pass_count == 1

    def test_no_config_copy_passes(self) -> None:
        summary = _check_build_context(
            "FROM python:3.14-slim\nCOPY src/ ./src/\n", self._OVERRIDE_REPO_ROOT, None
        )
        assert summary.warn_count == 0
        assert summary.pass_count == 1



_CLEAN_CODEX_TOML = """# GENERATED header
approval_policy = "on-request"

[mcp_servers.github]
command = "cmd"
args = ["/c", "npx", "-y", "@modelcontextprotocol/server-github"]
env_vars = ["GITHUB_PERSONAL_ACCESS_TOKEN"]
"""


class TestCodexConfig:
    """Check (4): .codex/config.toml literal-credential scan (S2 #330)."""

    def test_absent_file_passes(self) -> None:
        summary = _check_codex_config(None)
        assert summary.fail_count == 0
        assert summary.pass_count == 1

    def test_clean_generated_shape_passes(self) -> None:
        summary = _check_codex_config(_CLEAN_CODEX_TOML)
        assert summary.fail_count == 0
        assert summary.pass_count == 1

    def test_env_table_fails(self) -> None:
        toml = _CLEAN_CODEX_TOML + '\n[mcp_servers.github.env]\nX = "y"\n'
        summary = _check_codex_config(toml)
        assert summary.fail_count == 1

    def test_url_userinfo_fails_without_echoing_value(self) -> None:
        secret = "postgresql://analyst:hunter2@db:5432/x"
        toml = _CLEAN_CODEX_TOML + f'\n[mcp_servers.pg]\ncommand = "{secret}"\n'
        summary = _check_codex_config(toml)
        assert summary.fail_count == 1
        joined = " ".join(summary.messages)
        assert "hunter2" not in joined  # no-echo discipline (#330-2)

    def test_prefixed_credential_key_fails(self) -> None:
        """Repo-real prefixed shapes (SSH_SERVER_*_PASSWORD=...) must match --
        a leading word boundary would never fire after `_` (#330-1)."""
        toml = _CLEAN_CODEX_TOML + (
            '\n[mcp_servers.ssh]\ncommand = "cmd"\n'
            'args = ["SSH_SERVER_CLOUD_PASSWORD=hunter2"]\n'
        )
        summary = _check_codex_config(toml)
        assert summary.fail_count == 1
        joined = " ".join(summary.messages)
        assert "hunter2" not in joined

    def test_invalid_toml_warns(self) -> None:
        summary = _check_codex_config("not = [valid\n")
        assert summary.warn_count == 1
        assert summary.fail_count == 0
