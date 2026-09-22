"""Small native candidate check, stdlib only. Diagnostics never echo config values."""
from __future__ import annotations

import argparse
import ast
import base64
import json
import tomllib
from pathlib import Path

MEMORY = {
    f"pg-mj-agent-memory-{suffix}": f"MJ_AGENT_PG_MEMORY_{suffix.upper().replace('-', '_')}_URL"
    for suffix in ("dev", "test-lan", "test-wan", "prod-lan", "prod-wan")
}
REQUIRED = (
    ".codex/config.toml", ".codex/hooks.json", ".codex/rules/mj-agent.rules",
    "scripts/mcp/pg-server-start.ps1", "scripts/mcp/pg-server-wrapper.mjs",
    "scripts/mcp/setup-mcp-secrets.ps1", "scripts/sdd/codex_hook_guard.py",
    "scripts/sdd/run_codex_hook.ps1", "scripts/sdd/check_codex_native.py",
)
RULES = {
    ("Remove-Item",): "prompt",
    ("git", "checkout", "-b"): "forbidden", ("git", "switch", "-c"): "forbidden",
    ("gh", "pr", "merge"): "forbidden", ("psql",): "forbidden",
    ("pg_dump",): "forbidden", ("pg_restore",): "forbidden",
    ("git", "commit"): "prompt", ("git", "push"): "prompt", ("gh", "pr", "create"): "prompt",
}
# Plaintext of the tiny Windows quoting bootstrap in hooks.json. EncodedCommand
# avoids expansion by an outer PowerShell/cmd; it contains no credentials.
HOOK_BOOTSTRAP = (
    "$ErrorActionPreference = 'Stop'; try { $r = & git rev-parse --show-toplevel 2>$null; "
    "if ($LASTEXITCODE -ne 0 -or -not $r) { throw 'root' }; "
    "$p = Join-Path $r 'scripts/sdd/run_codex_hook.ps1'; "
    "if (-not (Test-Path -LiteralPath $p)) { throw 'handler' }; & $p } catch { "
    "[Console]::Out.WriteLine('{\"decision\":\"block\",\"reason\":\"UNKNOWN: project hook unavailable\"}') }"
)


def approval_status(mode: str | None) -> str:
    return {"never": "INCOMPATIBLE", "on-request": "APPROVAL_REQUIRED"}.get(mode or "", "UNKNOWN")


def check_mcp(root: Path) -> list[str]:
    errors = []
    for relative in (x for x in REQUIRED if x not in ENFORCEMENT):
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing or indirect required file: {relative}")
    try:
        config = tomllib.loads((root / ".codex/config.toml").read_text("utf-8"))
        if set(config) != {"approval_policy", "sandbox_mode", "project_doc_max_bytes", "mcp_servers"}:
            errors.append("unexpected project config fields")
        if (config.get("approval_policy") != "on-request" or config.get("sandbox_mode") != "workspace-write"
                or config.get("project_doc_max_bytes") != 65536):
            errors.append("project posture mismatch")
        servers = config.get("mcp_servers", {})
        if set(servers) != {"github", "playwright", "serena", *MEMORY}:
            errors.append("project MCP service set mismatch (foreign or missing service)")
        for name, server in servers.items():
            if not isinstance(server, dict) or set(server) - {"command", "args", "env_vars"}:
                errors.append("MCP inline environment or unknown fields rejected")
                continue
            args = server.get("args")
            if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
                errors.append("invalid MCP arguments")
                continue
            if name in MEMORY:
                variable = MEMORY[name]
                bootstrap = ("$r = & git rev-parse --show-toplevel 2>$null; "
                             "if ($LASTEXITCODE -ne 0 -or -not $r) { exit 2 }; "
                             "& (Join-Path $r 'scripts/mcp/pg-server-start.ps1') '" + variable + "'; exit $LASTEXITCODE")
                valid = (server.get("command") == "pwsh" and args == ["-NoProfile", "-Command", bootstrap]
                         and server.get("env_vars") == [variable])
            else:
                expected = {
                    "github": (["/c", "npx", "-y", "@modelcontextprotocol/server-github"], ["GITHUB_PERSONAL_ACCESS_TOKEN"]),
                    "playwright": (["/c", "npx", "-y", "@playwright/mcp@latest"], []),
                    "serena": (["/c", "uv", "tool", "run", "--from", "git+https://github.com/oraios/serena",
                                "serena", "start-mcp-server", "--context", "codex", "--enable-web-dashboard",
                                "false", "--project-from-cwd"], []),
                }.get(name)
                valid = (expected is not None and server.get("command") == "cmd"
                         and args == expected[0] and server.get("env_vars", []) == expected[1])
            if not valid:
                errors.append("MCP command or by-name injection mismatch")
    except (OSError, ValueError, TypeError, AttributeError):
        errors.append("unreadable or invalid project TOML")
    return errors


ENFORCEMENT = (".codex/hooks.json", ".codex/rules/mj-agent.rules",
               "scripts/sdd/codex_hook_guard.py", "scripts/sdd/run_codex_hook.ps1")


def check_enforcement(root: Path) -> list[str]:
    errors = []
    for relative in ENFORCEMENT:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing or indirect required file: {relative}")
    try:
        hooks = json.loads((root / ".codex/hooks.json").read_text("utf-8"))
        entries = hooks["hooks"]["PreToolUse"]
        expected_command = "pwsh -NoProfile -EncodedCommand " + base64.b64encode(HOOK_BOOTSTRAP.encode("utf-16le")).decode("ascii")
        expected_hooks = {"hooks": {"PreToolUse": [{"matcher": "Bash|shell|exec_command|apply_patch|Edit|Write",
                          "hooks": [{"type": "command", "command": expected_command, "timeout": 30}]}]}}
        if hooks != expected_hooks or not entries:
            errors.append("native hook shape mismatch")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError):
        errors.append("unreadable or invalid hooks")
    try:
        tree = ast.parse((root / ".codex/rules/mj-agent.rules").read_text("utf-8"))
        found = {}
        for stmt in tree.body:
            if (not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call)
                    or not isinstance(stmt.value.func, ast.Name) or stmt.value.func.id != "prefix_rule"
                    or stmt.value.args):
                raise ValueError
            options = {kw.arg: ast.literal_eval(kw.value) for kw in stmt.value.keywords}
            if set(options) != {"pattern", "decision"}:
                raise ValueError
            pattern = tuple(options["pattern"])
            if pattern in found:
                raise ValueError
            found[pattern] = options["decision"]
        if found != RULES:
            errors.append("native rule decisions mismatch")
    except (OSError, SyntaxError, ValueError, TypeError):
        errors.append("unreadable or invalid native rules")
    return errors


def check(root: Path) -> list[str]:
    return check_mcp(root) + check_enforcement(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--effective-approval-policy", choices=("never", "on-request", "unknown"))
    parser.add_argument("--surface", choices=("all", "mcp", "enforcement"), default="all")
    args = parser.parse_args()
    errors = {"all": check, "mcp": check_mcp, "enforcement": check_enforcement}[args.surface](args.root)
    print(json.dumps({"config": "FAIL" if errors else "STATIC_PASS", "errors": errors,
                      "session_approval": approval_status(args.effective_approval_policy),
                      "owner_approval": "NOT_ASSESSED", "host_enforcement": "NOT_TESTED"}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
