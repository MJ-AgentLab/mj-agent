"""Native cooperative guard. No adapter, transcript, credential or user-config reads.

This is a bounded recognizer, not a shell sandbox. Unrecognized payloads fail
closed. Owner-gated edits block here: this hook cannot authenticate an approval.
"""
from __future__ import annotations

import json
import posixpath
import re
import shlex
import sys
from typing import Any


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
        "scripts/sdd/codex_hook_guard.py", "scripts/sdd/run_codex_hook.ps1",
        "scripts/sdd/check_codex_native.py", "scripts/sdd/check_native_skills.py",
        "scripts/sdd/check_native_governance.py", "scripts/sdd/_common/native_assets.py",
    )
    return (any(_has(path, p) for p in exact + (".codex", ".claude", "policies", "sdd", "scripts/mcp", ".github/workflows"))
            or _has(path, "agents.md")
            or bool(re.search(r"(?:^|/)capabilities/[^/]+/[^/]+/contracts/", path))
            or bool(re.search(r"(?:^|/)src/mj_agent/skills/[^/]+/skill.md$", path))
            or bool(re.search(r"(?:^|/)\.agents/skills/mj-agent-infra-[^/]+/", path)))


def _branch_token(value: str) -> bool:
    return (bool(re.fullmatch(r"(?:refs/heads/)?[A-Za-z0-9][A-Za-z0-9._/-]*", value))
            and value != "HEAD" and not value.endswith(("/", ".", ".lock"))
            and ".." not in value and "//" not in value)


def _host_review(tokens: list[str]) -> tuple[str, str]:
    """Bounded canonical spellings covered by native prompt rules; no approval claim."""
    if tokens[:2] == ["git", "commit"]:
        args = tokens[2:]
        if not args or (len(args) == 2 and args[0] in {"-m", "--message", "-F", "--file"}
                        and args[1].strip("\"'") and not args[1].startswith("-")):
            return "HOST_APPROVAL_REQUIRED", "commit; task authorization remains separate"
    elif tokens[:2] == ["git", "push"]:
        args = tokens[2:]
        if args and args[0] in {"-u", "--set-upstream"}:
            args = args[1:]
        if len(args) == 3 and args[0] in {"gitee", "origin"} and args[1] == "--delete":
            branch = args[2].removeprefix("refs/heads/")
            if branch in {"main", "develop"}:
                return "FORBIDDEN", "protected remote branch"
            if _branch_token(args[2]):
                return "HOST_APPROVAL_REQUIRED", "remote deletion; independent task authorization required"
        if len(args) == 2 and args[0] in {"gitee", "origin"} and _branch_token(args[1]):
            return "HOST_APPROVAL_REQUIRED", "push; task authorization remains separate"
    elif tokens[:3] == ["gh", "pr", "create"]:
        args = tokens[3:]
        values: dict[str, str] = {}
        while args:
            flag, *args = args
            if flag == "--draft" and flag not in values:
                values[flag] = "true"
                continue
            if flag == "-B":
                flag = "--base"
            if flag not in {"--repo", "--head", "--base", "--title", "--body-file"} or flag in values:
                return "UNKNOWN", "unrecognized PR invocation"
            if not args or args[0].startswith("-") or not args[0].strip("\"'"):
                return "UNKNOWN", "missing PR option value"
            values[flag], *args = args
        if values.get("--base") not in {"develop", "main"}:
            return "UNKNOWN", "review explicit PR base"
        head = values.get("--head")
        if head and (not _branch_token(head) or values["--base"] != (
                "main" if head.startswith("hotfix/") else "develop")):
            return "FORBIDDEN", "G2 base does not match head type"
        return "HOST_APPROVAL_REQUIRED", "PR creation; task authorization remains separate"
    return "UNKNOWN", "publication spelling needs explicit review"


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
        tokens = shlex.split(command, posix=False) if isinstance(command, str) else command
    except ValueError:
        return "UNKNOWN", "unrecognized command syntax"
    if not isinstance(tokens, list) or not tokens or not all(isinstance(t, str) for t in tokens):
        return "UNKNOWN", "missing command"
    words = [_path(t) for t in tokens]
    # Global Git options may redirect repository/config state before the verb.
    # Do not attempt a new general command parser: fail closed for this spelling.
    if words[0] == "git" and len(tokens) > 1 and tokens[1].startswith("-"):
        return "UNKNOWN", "Git global options require reviewed execution route"
    docker_carrier = words[:2] == ["docker", "compose"]
    if any(_sensitive(t) for t in words) and not docker_carrier:
        return "FORBIDDEN", "secret surface"
    if any(t.rsplit("/", 1)[-1].removesuffix(".exe") in {"psql", "pg_dump", "pg_restore"} for t in words):
        return "FORBIDDEN", "direct database route"
    if words[:2] == ["git", "checkout"] and any(t in {"-b", "-B"} for t in tokens[2:]):
        return "FORBIDDEN", "G1 worktree required"
    if words[:2] == ["git", "switch"] and any(t in {"-c", "-C", "--create", "--force-create"} for t in tokens[2:]):
        return "FORBIDDEN", "G1 worktree required"
    if words[:3] == ["gh", "pr", "merge"]:
        return "FORBIDDEN", "human merge only"
    if any(re.search(r"[;|&<>`\n\r$]", token) for token in tokens) or any(
            token.startswith("(") or token.endswith(")") for token in tokens if not token.startswith(("'", '"'))):
        return "UNKNOWN", "compound or expanding command needs explicit review"
    if words[:3] == ["gh", "pr", "create"]:
        has_base = any(t.startswith("--base=") and len(t) > 7 for t in tokens[3:])
        has_base |= any(t in {"--base", "-B"} and i + 1 < len(tokens) and not tokens[i + 1].startswith("-")
                        for i, t in enumerate(tokens) if i >= 3)
        if not has_base:
            return "FORBIDDEN", "G2 explicit base required"
        return _host_review(tokens)
    if words[:2] in (["git", "commit"], ["git", "push"]):
        return _host_review(tokens)
    # Do not pretend to parse compound commands, interpreters or arbitrary writes.
    if isinstance(command, str) and re.search(r"[;|&<>`\n]", command):
        return "UNKNOWN", "compound command needs explicit review"
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
    if state == "HOST_APPROVAL_REQUIRED":
        # No allow/ask or updatedInput: leave existing native prompt rules in charge.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "additionalContext": f"{state}: {reason}. Normal host approval is still required; "
                                   "this hook does not authenticate Owner authorization."}}))
    elif state != "ALLOW":
        # Legacy block is supported by the current host; never emit unsupported ask.
        print(json.dumps({"decision": "block", "reason": f"{state}: {reason}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
