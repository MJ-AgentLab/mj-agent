"""Guard-hook contract fixtures (issue #313, PR-2; plan §4 8g).

Exercises ``.claude/scripts/guard-git-workflow.ps1`` end-to-end via subprocess
(precedent: ``test_g24_live_exercise.py``): G1/G2 positive pins, G1 bypass
closures, false-positive guards, and the v5 §5.4 fail-closed input protocol
(non-JSON / empty / missing-field / unknown-schema stdin must exit non-zero).

Skips when no PowerShell is available (tests/CLAUDE.md anti-pattern rule:
skip, don't fail, on missing host deps). GitHub ubuntu runners ship ``pwsh``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".claude" / "scripts" / "guard-git-workflow.ps1"

PWSH = shutil.which("pwsh") or shutil.which("powershell")

pytestmark = pytest.mark.skipif(PWSH is None, reason="no pwsh/powershell on host")


def run_hook(stdin_text: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(PWSH), "-NoProfile", "-File", str(HOOK)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=120,
    )


def payload(command: str) -> str:
    return json.dumps(
        {
            "tool_name": "Bash",
            "hook_event_name": "PreToolUse",
            "tool_input": {"command": command},
        }
    )


BLOCKED_COMMANDS = [
    # G1/G2 positive pins (pre-existing behavior, must stay blocked)
    "git checkout -b feature/x",
    "git switch -c feature/x",
    "gh pr create --title t --body-file b.md",
    # G1 bypass closures (Owner decision 5, 2026-07-13: tighten in PR-2)
    "git checkout -q -b feature/x",
    "git -C ../elsewhere checkout -b feature/x",
    "git checkout main -b feature/x",
    "cd sub && git checkout -b feature/x",
]

ALLOWED_COMMANDS = [
    "git status",
    "git checkout main",
    "gh pr create --base develop --title t",
    "gh pr create --base=main --title t",
    # false-positive guards: G1 tokens inside another subcommand / non-git segment
    'git commit -m "docs: mention checkout -b in guide"',
    "echo git checkout -b nope",
]


@pytest.mark.parametrize("command", BLOCKED_COMMANDS)
def test_guard_blocks(command: str) -> None:
    result = run_hook(payload(command))
    assert result.returncode == 2, (
        f"expected exit 2 for {command!r}, got {result.returncode}; "
        f"stderr={result.stderr.decode('utf-8', 'replace')!r}"
    )


@pytest.mark.parametrize("command", ALLOWED_COMMANDS)
def test_guard_allows(command: str) -> None:
    result = run_hook(payload(command))
    assert result.returncode == 0, (
        f"expected exit 0 for {command!r}, got {result.returncode}; "
        f"stderr={result.stderr.decode('utf-8', 'replace')!r}"
    )


MALFORMED_STDIN = [
    pytest.param("this is not json", id="non-json"),
    pytest.param("", id="empty"),
    pytest.param(
        json.dumps({"tool_name": "Bash", "hook_event_name": "PreToolUse"}),
        id="missing-tool-input-command",
    ),
    pytest.param(json.dumps({"foo": "bar"}), id="unknown-schema"),
    pytest.param(
        json.dumps(
            {
                "tool_name": "Edit",
                "hook_event_name": "PreToolUse",
                "tool_input": {"command": "git status"},
            }
        ),
        id="wrong-tool-name",
    ),
]


@pytest.mark.parametrize("stdin_text", MALFORMED_STDIN)
def test_fail_closed_input_protocol(stdin_text: str) -> None:
    """v5 §5.4: malformed hook payloads are rejected, never silently allowed."""
    result = run_hook(stdin_text)
    assert result.returncode == 2, (
        f"expected fail-closed exit 2 for stdin {stdin_text!r}, "
        f"got {result.returncode}"
    )
