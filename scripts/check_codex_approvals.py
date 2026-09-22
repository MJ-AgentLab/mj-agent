"""Read-only delivery preflight; exit 0 means approval is still required, not granted."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__:
    from scripts.sdd.check_codex_native import ENFORCEMENT, approval_status, check_enforcement
else:
    from sdd.check_codex_native import (  # type: ignore[no-redef]
        ENFORCEMENT,
        approval_status,
        check_enforcement,
    )

COMMANDS = (
    (("Remove-Item",), ("Remove-Item", "-LiteralPath", "<absolute-target>")),
    (("git", "commit"), ("git", "commit")),
    (("git", "push"), ("git", "push", "-u", "gitee", "<branch>")),
    (("git", "push"), ("git", "push", "-u", "origin", "<branch>")),
    (("gh", "pr", "create"), ("gh", "pr", "create", "--base", "develop")),
    (("git", "push"), ("git", "push", "gitee", "--delete", "<branch>")),
    (("git", "push"), ("git", "push", "origin", "--delete", "<branch>")),
)
RECOVERY = {
    "UNKNOWN": "Verify the effective session mode and project rules; do not infer them from static config.",
    "INCOMPATIBLE": "Have the Owner enter an approval-capable session, verify its effective mode, then rerun.",
    "APPROVAL_REQUIRED": "Verify action-specific Owner approval, reusing an existing exact approval, "
                         "and verify the host execution route before delivery.",
}


def diagnose(root: Path, mode: str | None = None) -> dict[str, Any]:
    """Combine existing native checks with an explicitly observed mode; never execute delivery."""
    # Refuse indirect inputs before the existing checker reads any file.
    paths = [root]
    for relative in ENFORCEMENT:
        path = root
        for part in Path(relative).parts:
            path = path / part
            paths.append(path)
    try:
        if any(path.is_symlink() or path.is_junction() for path in paths):
            errors = ["indirect enforcement path; no files read"]
        else:
            errors = check_enforcement(root)
    except OSError:
        errors = ["unreadable enforcement path"]
    effective_mode = mode if mode in ("never", "on-request") else "unknown"
    status = "UNKNOWN" if errors else approval_status(effective_mode)
    return {
        "rule_scope": "PROJECT_FILES_ONLY",
        "effective_approval_policy": effective_mode,
        "mode_source": "CALLER_OBSERVATION" if effective_mode != "unknown" else "UNKNOWN",
        "session_approval": status,
        "errors": errors,
        "commands": [
            {
                "command_family": list(family), "command": list(command),
                "rule_source": ".codex/rules/mj-agent.rules",
                "rule_decision": "UNKNOWN" if errors else "prompt", "status": status,
            }
            for family, command in COMMANDS
        ],
        "owner_approval": "NOT_ASSESSED",
        "host_enforcement": "NOT_TESTED",
        "remote_authentication": "NOT_TESTED",
        "recovery": RECOVERY[status],
        "execution_boundary": "Owner approval and on-request do not unlock a blocking hook; "
                              "report BLOCKED_EXECUTION_ROUTE without bypassing it.",
    }


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root or Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--effective-approval-policy", choices=("never", "on-request", "unknown"),
        help="Actual mode observed in the target session; omit if unknown. Static config is not evidence.",
    )
    args = parser.parse_args(argv)
    report = diagnose(args.root, args.effective_approval_policy)
    print(json.dumps(report))
    return {"APPROVAL_REQUIRED": 0, "INCOMPATIBLE": 1, "UNKNOWN": 2}[report["session_approval"]]


if __name__ == "__main__":
    raise SystemExit(main())
