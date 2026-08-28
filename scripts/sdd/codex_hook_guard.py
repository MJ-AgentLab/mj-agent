"""codex_hook_guard.py — runtime PreToolUse guard for the Codex cooperative carrier.

Epic #499 PR-D1a (plan §5.9). `.codex/hooks.json` wires codex's PreToolUse event
to this script; it evaluates the `hooks.guards` declared in the typed source
`sdd/adapters/codex-enforcement.yml` and returns a BLOCK decision before the
tool call runs.

WHY THIS BLOCKS BEFORE THE SIDE EFFECT: codex evaluates PreToolUse hooks BEFORE
executing the tool call and reports "Tool call blocked by PreToolUse hook: " /
"Command blocked by PreToolUse hook: ". Nothing here undoes a completed action —
there is no rollback path, by design (plan §5.9).

INPUT DISCIPLINE (plan §5.9, hard — this is the whole point of the module):
the payload codex sends carries `transcript_path`, `agent_transcript_path`,
`last_assistant_message`, `session_id`, `turn_id`, `cwd`, `model` and more.
This guard reads NONE of them. It projects the payload down to
`ALLOWED_INPUT_KEYS` as its FIRST action and every later line reads only that
projection, so "never an input" is a structural property, not a promise. It
also never reads Secrets, the environment, the network, or any file other than
the typed source.

COOPERATIVE, NOT AUTHORITATIVE: a guard that fails to fire is not permission to
proceed. The binding rules live in AGENTS.md; this only surfaces them earlier.
Consistent with that, an unparseable or unrecognized payload does NOT block —
a cooperative aid must not wedge a Codex session on a payload shape it does not
understand. Fail-open here is a deliberate decision, recorded in the PR-D1a
evidence, and it is why AGENTS.md prose remains the real boundary.

Wire (codex-cli 0.147.0, `PreToolUseDecisionWire`): `{"decision": "block",
"reason": "<non-empty>"}` is the supported deny form. `decision: approve` and
`permissionDecision: allow|ask` are explicitly UNSUPPORTED, so the allow path
emits nothing at all and exits 0.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:  # pragma: no cover - import bootstrap
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common.enforcement_source import (  # noqa: E402
    ENFORCEMENT_SOURCE_RELPATH,
    EnforcementSource,
    EnforcementSourceError,
    Guard,
    load_enforcement_source,
)

# The ONLY payload keys this guard may read. Anything else codex sends —
# notably transcript_path / agent_transcript_path / last_assistant_message /
# session_id — is dropped before evaluation and is never referenced again.
ALLOWED_INPUT_KEYS = ("hook_event_name", "tool_name", "tool_input")
# Explicitly enumerated so a test can assert none of them is ever touched
# (AC-12 "no-read spies cover forbidden inputs").
FORBIDDEN_INPUT_KEYS = (
    "agent_transcript_path",
    "last_assistant_message",
    "session_id",
    "stop_hook_active",
    "transcript_path",
    "turn_id",
)

# apply_patch envelope headers (codex-cli 0.147.0): the only valid hunk headers
# are '*** Add File: {path}', '*** Delete File: {path}', '*** Update File:
# {path}'; a rename adds '*** Move to: {path}'.
_PATCH_PATH = re.compile(
    r"^\*\*\* (?:Add File|Delete File|Update File|Move to):\s*(.+?)\s*$",
    re.MULTILINE,
)
_APPLY_PATCH = "apply_patch"


def project_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Reduce the hook payload to the allowlisted keys. FIRST thing we do."""
    return {k: payload[k] for k in ALLOWED_INPUT_KEYS if k in payload}


def _command_tokens(tool_input: Any) -> list[str]:
    if not isinstance(tool_input, dict):
        return []
    command = tool_input.get("command")
    if isinstance(command, str):
        return command.split()
    if isinstance(command, list):
        return [c for c in command if isinstance(c, str)]
    return []


def _normalized_command(tokens: list[str]) -> str:
    return " ".join(tokens).strip()


def _normalize_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _written_paths(tool_input: Any, tokens: list[str]) -> list[str]:
    """Paths this call would WRITE: declared file_path/path inputs + every
    apply_patch hunk header. Read-only mentions are deliberately excluded.

    The documented apply_patch tool call is
    `{"command": ["apply_patch", "*** Begin Patch\\n..."]}` (codex 0.147.0 also
    refuses anything else with `CommandDidNotStartWithApplyPatch`), but the
    envelope is scanned for in EVERY string value of `tool_input` rather than
    only in that position, so a differently-keyed payload (`input`, `patch`, ...)
    still yields its write targets instead of silently yielding none.
    """
    paths: list[str] = []
    if isinstance(tool_input, dict):
        for key in ("file_path", "path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value)
        for value in tool_input.values():
            for chunk in value if isinstance(value, list) else [value]:
                if isinstance(chunk, str) and "*** " in chunk:
                    paths.extend(_PATCH_PATH.findall(chunk))
    return [_normalize_path(p) for p in paths]


def _command_args(tokens: list[str]) -> list[str]:
    """Every argument of a shell command, as a path candidate. Used ONLY by
    `command_arg` guards (secrets), where READING is itself the violation — a
    path guard must not be widened to arguments or a harmless
    `--rules .codex/rules/mj-agent.rules` read would be blocked."""
    if not tokens or tokens[0] == _APPLY_PATCH:
        return []
    return [_normalize_path(t) for t in tokens[1:] if t and not t.startswith("-")]


def _command_hit(pattern: str, command: str) -> bool:
    """Whitespace-normalized token-PREFIX match, never a bare substring test.

    "git checkout -b" matches `git checkout -b x` but not `git checkout --benign`.
    """
    pat_tokens = pattern.split()
    cmd_tokens = command.split()
    if not pat_tokens or len(pat_tokens) > len(cmd_tokens):
        return False
    return cmd_tokens[: len(pat_tokens)] == pat_tokens


def _path_hit(pattern: str, path: str) -> bool:
    """Directory prefix (`dir/`), string prefix (`pre*`), else exact full path
    OR exact basename. Never a bare substring: `.env` must not match `.venv/x`.

    A multi-segment pattern also matches as a path SUFFIX on a segment boundary,
    so an absolute or otherwise-prefixed spelling of the same file still hits
    (`D:/repo/src/mj_agent/prompts/system.md` vs the declared repo-relative
    `src/mj_agent/prompts/system.md`). Without this the multi-segment 必停
    patterns degraded to exact repo-relative string equality.
    """
    if pattern.endswith("/"):
        return (
            path == pattern.rstrip("/")
            or path.startswith(pattern)
            or ("/" + pattern) in ("/" + path)
        )
    if pattern.endswith("*"):
        stem = pattern[:-1]
        return path.startswith(stem) or ("/" + stem) in ("/" + path)
    if path == pattern or path.rsplit("/", 1)[-1] == pattern:
        return True
    return "/" in pattern and path.endswith("/" + pattern)


def evaluate(source: EnforcementSource, projected: dict[str, Any]) -> Guard | None:
    """Return the first guard that denies this call, or None. Reads ONLY `projected`."""
    tool_input = projected.get("tool_input")
    tokens = _command_tokens(tool_input)
    command = _normalized_command(tokens)
    written = _written_paths(tool_input, tokens)
    args = _command_args(tokens)
    is_patch = bool(tokens) and tokens[0] == _APPLY_PATCH

    for guard in source.guards:
        if command and any(
            _command_hit(prefix, command) for prefix in guard.exempt_command_prefixes
        ):
            continue
        for surface in guard.applies_to:
            if surface == "command":
                # An apply_patch call is not a shell command; its first token is
                # the tool name, so command guards must not fire on it.
                if is_patch or not command:
                    continue
                if any(_command_hit(p, command) for p in guard.deny_patterns):
                    return guard
            elif surface == "path":
                if any(
                    _path_hit(p, path)
                    for path in written
                    for p in guard.deny_patterns
                ):
                    return guard
            elif surface == "command_arg":
                if any(
                    _path_hit(p, arg)
                    for arg in args
                    for p in guard.deny_patterns
                ):
                    return guard
    return None


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    root = repo_root or _REPO_ROOT
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return 0  # cooperative: unknown payload never wedges the session
    if not isinstance(payload, dict):
        return 0
    projected = project_payload(payload)
    if projected.get("hook_event_name") != "PreToolUse":
        return 0

    try:
        source = load_enforcement_source(
            (root / ENFORCEMENT_SOURCE_RELPATH).read_text(encoding="utf-8")
        )
    except (OSError, EnforcementSourceError):
        return 0  # no declared enforcement -> nothing to surface

    guard = evaluate(source, projected)
    if guard is None:
        # `decision: approve` is unsupported by codex; emit nothing.
        return 0
    reason = " ".join(guard.reason.split())
    # codex refuses "decision:block without a non-empty reason".
    json.dump({"decision": "block", "reason": f"[{guard.guard_id}] {reason}"}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
