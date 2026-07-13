"""P0 dual-agent-compat wording fixtures (issue #313, PR-1; plan §4 8a).

Pins the v5 §5.1 (biz data boundary) and §5.2 (secrets boundary) teaching-surface
state: workflow skills and templates must not instruct any agent to read biz data
via raw PostgreSQL MCP, nor to read/echo ``.env`` / process-env credentials.
Real-repo-file content assertions follow the precedent of
``test_sdd_g21_evidence_predicate.py::TestTraceYmlMfu1Fix``.

Forbidden literals are built by concatenation so repo-wide drift greps
(e.g. ``rg 'mcp postgres'``) never hit this test file itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# -- forbidden teaching-surface literals (concatenated; see module docstring) --
RAW_BIZ_MCP = "mcp " + "postgres"  # covers "mcp postgres-*" and "mcp postgres"
AGENT_ENV_READ_PS = "Get-Content " + ".env"
AGENT_ENV_READ_SH = "grep -E '^LLM_PROVIDER=' " + ".env"
AGENT_ENV_VALUE_EXTRACT = "cut -d= " + "-f2"
AGENT_PROCESS_ENV_SECRET = "$env:" + "LLM_API_KEY"

CASES: list[tuple[str, list[str], list[str]]] = [
    (
        ".claude/skills/mj-agent-flow-repo-scan/SKILL.md",
        [RAW_BIZ_MCP],
        ["describe_biz_table", "list_biz_tables", "pg-mj-agent-memory"],
    ),
    (
        "docs/_templates/TEMPLATE_REPO_SCAN_RESULT.md",
        [RAW_BIZ_MCP],
        ["describe_biz_table"],
    ),
    (
        ".claude/skills/mj-agent-infra-env-setup/SKILL.md",
        [AGENT_ENV_READ_PS, AGENT_ENV_READ_SH, AGENT_ENV_VALUE_EXTRACT],
        ["check_env_keys.ps1"],
    ),
    (
        ".claude/skills/mj-agent-infra-docker-compose/SKILL.md",
        [AGENT_ENV_READ_PS],
        ["check_env_keys.ps1"],
    ),
    (
        ".claude/skills/mj-agent-infra-llm-endpoint-probe/SKILL.md",
        [AGENT_ENV_READ_PS, AGENT_PROCESS_ENV_SECRET],
        ["probe_llm_endpoint.ps1"],
    ),
]

# PR-2 (plan §4 8i/8j): tool-neutral OWNER_APPROVAL_REQUIRED stop point in the
# runtime family + dual-tool AGENTS.md (v5 §5.3 tool-agnostic HITL & Git guard).
CASES += [
    (
        ".claude/skills/mj-agent-runtime-biz-catalog-sync/SKILL.md",
        [],
        ["OWNER_APPROVAL_REQUIRED"],
    ),
    (
        ".claude/skills/mj-agent-runtime-prompt-version-bump/SKILL.md",
        [],
        ["OWNER_APPROVAL_REQUIRED"],
    ),
    (
        ".claude/skills/mj-agent-runtime-skill-doc-improve/SKILL.md",
        [],
        ["OWNER_APPROVAL_REQUIRED"],
    ),
    (
        ".claude/skills/mj-agent-runtime-eval-baseline/SKILL.md",
        [],
        ["OWNER_APPROVAL_REQUIRED"],
    ),
    (
        "AGENTS.md",
        ["Primary AI developer", "non-Claude-Code agents"],
        ["OWNER_APPROVAL_REQUIRED", "git worktree add"],
    ),
]

CASE_IDS = [path.rsplit("/", 2)[-2] if "skills" in path else Path(path).stem for path, _, _ in CASES]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


@pytest.mark.parametrize(("rel_path", "forbidden", "required"), CASES, ids=CASE_IDS)
def test_teaching_surface_boundary(rel_path: str, forbidden: list[str], required: list[str]) -> None:
    """Boundary fix pinned: forbidden instructions absent, sanitized seams present."""
    text = _read(rel_path)
    for needle in forbidden:
        assert needle not in text, (
            f"{rel_path}: forbidden teaching-surface literal {needle!r} present "
            "(v5 §5.1/§5.2 boundary regression)"
        )
    for needle in required:
        assert needle in text, (
            f"{rel_path}: required sanitized-seam reference {needle!r} missing"
        )


def test_docker_compose_env_file_flag_untouched() -> None:
    """``--env-file .env`` is docker-process env injection, NOT an agent read.

    Guards against over-deleting the compose variable-injection flag while
    removing agent-side ``.env`` parsing (plan §5 risk row 3).
    """
    text = _read(".claude/skills/mj-agent-infra-docker-compose/SKILL.md")
    assert "--env-file .env" in text


@pytest.mark.parametrize(
    "script_rel_path",
    ["scripts/check_env_keys.ps1", "scripts/probe_llm_endpoint.ps1"],
)
def test_sanitized_scripts_exist_and_never_echo_values(script_rel_path: str) -> None:
    """v5 §5.2: scripts return key names / booleans / sanitized diagnostics only."""
    script = REPO_ROOT / script_rel_path
    assert script.is_file(), f"{script_rel_path} missing (sanitized seam for infra skills)"
    text = script.read_text(encoding="utf-8")
    assert "sanitized" in text.lower(), (
        f"{script_rel_path}: must declare its sanitized-output contract in-line"
    )
