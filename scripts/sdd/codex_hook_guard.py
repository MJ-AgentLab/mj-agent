"""Native cooperative guard. No adapter, transcript, credential or user-config reads.

This is a bounded recognizer, not a shell sandbox. Unrecognized payloads fail
closed. Owner-gated edits block here: this hook cannot authenticate an approval.
"""
from __future__ import annotations

import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .git_command_review import CONTEXT, publication, tokenize
else:
    # The reviewed launcher uses Python -I; load only the adjacent project helper.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from git_command_review import CONTEXT, publication, tokenize  # type: ignore[no-redef]


def project_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in ("hook_event_name", "tool_name", "tool_input") if key in payload}


def _path(value: str) -> str:
    return posixpath.normpath(value.strip("\"'").replace("\\", "/")).lower()


def _has(path: str, part: str) -> bool:
    return path == part or path.endswith("/" + part) or ("/" + part + "/") in ("/" + path + "/")


def _sensitive(path: str) -> bool:
    return _has(path, ".env") or bool(re.search(r"(?:^|/)config/secrets[^/]*(?:$|/)", path))


def _owner(path: str) -> bool:
    exact = (
        ".mcp.json", "src/mj_agent/tools/sql/guardrail.py", "src/mj_agent/tools/sql/precheck.py",
        "src/mj_agent/prompts/system.md", "src/mj_agent/biz_catalog/qcm_catalog.yaml",
        "docker/compose.prod.yml", "docker/dockerfile",
        "scripts/sdd/codex_hook_guard.py", "scripts/sdd/git_command_review.py", "scripts/sdd/run_codex_hook.ps1",
        "scripts/sdd/check_codex_native.py", "scripts/sdd/check_native_skills.py",
        "scripts/sdd/check_native_governance.py", "scripts/sdd/_common/native_assets.py",
    )
    return (any(_has(path, p) for p in exact + (".codex", ".claude", "policies", "sdd", "scripts/mcp", ".github/workflows"))
            or _has(path, "agents.md")
            or bool(re.search(r"(?:^|/)capabilities/[^/]+/[^/]+/contracts/", path))
            or bool(re.search(r"(?:^|/)src/mj_agent/skills/[^/]+/skill.md$", path))
            or bool(re.search(r"(?:^|/)\.agents/skills/mj-agent-infra-[^/]+/", path)))


def classify(payload: dict[str, Any]) -> tuple[str, str]:
    if payload.get("hook_event_name") != "PreToolUse":
        return "UNKNOWN", "unsupported event"
    tool = payload.get("tool_name")
    data = payload.get("tool_input")
    if tool in {"apply_patch", "Edit", "Write"}:
        if tool == "apply_patch" and isinstance(data, dict) and "command" in data:
            if set(data) != {"command"} or not isinstance(data["command"], str):
                return "UNKNOWN", "unrecognized patch payload"
            data = data["command"]
        if isinstance(data, str):
            paths = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", data, re.M)
        elif isinstance(data, dict):
            paths = [data[k] for k in ("file_path", "path") if isinstance(data.get(k), str)]
        else:
            paths = []
        if not paths:
            return "UNKNOWN", "no recognized edit target"
        if any(_sensitive(_path(p)) for p in paths):
            return "FORBIDDEN", "secret surface"
        if any(_owner(_path(p)) for p in paths):
            return "OWNER_APPROVAL_REQUIRED", "protected edit; human decision required"
        return "ALLOW", "ordinary edit; other project obligations still apply"
    if tool not in {"Bash", "shell", "exec_command"} or not isinstance(data, dict):
        return "UNKNOWN", "unsupported tool payload"
    command = data.get("command", data.get("cmd"))
    try:
        tokens = tokenize(command)
    except ValueError:
        return "UNKNOWN", "unrecognized command syntax"
    if not isinstance(tokens, list) or not tokens or not all(isinstance(t, str) for t in tokens):
        return "UNKNOWN", "missing command"
    words = [_path(t) for t in tokens]
    # Global Git options may redirect repository/config state before the verb.
    # Do not attempt a new general command parser: fail closed for this spelling.
    if words[0] == "git" and len(tokens) > 1 and tokens[1].startswith("-"):
        return "UNKNOWN", "Git global options require reviewed execution route"
    if words[:2] == ["git", "checkout"] and any(
            t.startswith(("-b", "-B", "--orphan")) for t in tokens[2:]):
        return "FORBIDDEN", "G1 worktree required"
    if words[:2] == ["git", "switch"] and any(
            t.startswith(("-c", "-C", "--create", "--force-create", "--orphan")) for t in tokens[2:]):
        return "FORBIDDEN", "G1 worktree required"
    if words[:3] == ["gh", "pr", "merge"]:
        return "FORBIDDEN", "human merge only"
    if words[:3] == ["gh", "pr", "create"] or words[:2] in (["git", "commit"], ["git", "push"]):
        review = publication(tokens)
        scope = review['scope']
        for key in ('message_file', 'body_file'):
            if scope.get(key) and _sensitive(_path(scope[key])):
                return "FORBIDDEN", "secret surface"
        return review['status'], review['reason']
    docker_carrier = words[:2] == ["docker", "compose"]
    if any(_sensitive(t) for t in words) and not docker_carrier:
        return "FORBIDDEN", "secret surface"
    if any(t.rsplit("/", 1)[-1].removesuffix(".exe") in {"psql", "pg_dump", "pg_restore"} for t in words):
        return "FORBIDDEN", "direct database route"
    if (words[:2] == ["git", "branch"] and "-d" in tokens
            and any(t.removeprefix('refs/heads/') in {'main', 'develop'} for t in tokens[2:])):
        return "FORBIDDEN", "protected local branch"
    if words[:3] == ["git", "worktree", "remove"] and any(
            word.rstrip('/').rsplit('/', 1)[-1] in {'main', 'develop'} for word in words[3:]):
        return "FORBIDDEN", "protected worktree"
    # Literal argv is not shell-evaluated. Unknown command carriers retain the
    # conservative compound check; publication values were parsed above.
    if any(re.search(r"[;|&<>`\n\r$]", token) for token in tokens):
        return "UNKNOWN", "compound or expanding command needs explicit review"
    if words[:2] in (["git", "status"], ["git", "diff"], ["git", "log"]):
        return "ALLOW", "read-only Git inspection"
    if words[0] in {"get-content", "cat", "rg"}:
        return "ALLOW", "recognized read; caller still enforces data boundary"
    return "ALLOW", "no recognized stop point; not a shell safety certification"


def main() -> int:
    try:
        raw = json.load(sys.stdin)
        state, reason = classify(project_payload(raw)) if isinstance(raw, dict) else ("UNKNOWN", "invalid payload")
    except (ValueError, TypeError):
        state, reason = "UNKNOWN", "invalid payload"
    if state == CONTEXT:
        # Context only: neither project authorization nor a host approval result.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "additionalContext": f"{state}: {reason}. This hook does not authenticate Owner authorization; "
                                   "host execution restrictions are assessed separately."}}))
    elif state != "ALLOW":
        # Legacy block is supported by the current host; never emit unsupported ask.
        print(json.dumps({"decision": "block", "reason": f"{state}: {reason}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
