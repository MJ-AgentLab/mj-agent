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
SSH_ENV = [f'MJ_SYS_SSH_SERVER_{name}_PASSWORD' for name in ('CLOUD', 'RUNNER', 'TEST', 'PROD', 'DGX')]
SSH_FILES = tuple('.codex/mcp/' + name for name in (
    'package.json', 'package-lock.json', 'ssh-start.mjs', 'ssh-runtime.mjs',
    'ssh-server.mjs', 'ssh-servers.json',
))
REQUIRED = (
    ".codex/config.toml", ".codex/hooks.json", ".codex/rules/mj-agent.rules",
    "scripts/mcp/pg-server-start.ps1", "scripts/mcp/pg-server-wrapper.mjs",
    "scripts/mcp/setup-mcp-secrets.ps1", "scripts/sdd/codex_hook_guard.py",
    "scripts/sdd/run_codex_hook.ps1", "scripts/sdd/check_codex_native.py",
    "scripts/sdd/git_command_review.py",
    "scripts/sdd/task_delivery.py",
) + SSH_FILES
RULES = {
    ("Remove-Item",): "prompt",
    ("psql",): "forbidden",
    ("pg_dump",): "forbidden", ("pg_restore",): "forbidden",
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


def approval_status(mode: str | None, decision: str = "UNKNOWN") -> str:
    """A mode alone is never a session-wide compatibility verdict."""
    if decision == "NO_MATCH":
        return "NO_PROJECT_RULE_REQUIREMENT"
    if decision == "forbidden":
        return "FORBIDDEN"
    if decision != "prompt":
        return "UNKNOWN"
    return {"never": "INCOMPATIBLE", "on-request": "APPROVAL_REQUIRED"}.get(mode or "", "UNKNOWN")


def check_mcp(root: Path) -> list[str]:
    errors = []
    for relative in (x for x in REQUIRED if x not in ENFORCEMENT):
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing or indirect required file: {relative}")
    try:
        config = tomllib.loads((root / ".codex/config.toml").read_text("utf-8"))
        if set(config) != {"mcp_servers"}:
            errors.append("unexpected project config fields")
        servers = config.get("mcp_servers", {})
        if set(servers) != {"github", "playwright", "serena", "ssh-manager", *MEMORY}:
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
            elif name == 'ssh-manager':
                bootstrap = ("$r = & git rev-parse --show-toplevel 2>$null; "
                             "if ($LASTEXITCODE -ne 0 -or -not $r) { exit 2 }; "
                             "& node (Join-Path $r '.codex/mcp/ssh-start.mjs'); exit $LASTEXITCODE")
                valid = (server.get('command') == 'pwsh' and args == ['-NoProfile', '-Command', bootstrap]
                         and server.get('env_vars') == SSH_ENV)
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
    errors.extend(check_ssh_assets(root))
    return errors


def check_ssh_assets(root: Path) -> list[str]:
    """Public metadata only; never load dependencies or credential sources."""
    try:
        folder = root / '.codex/mcp'
        # Refuse indirect parents before reading any asset.
        if folder.is_symlink() or folder.is_junction() or any((root / p).is_symlink() for p in SSH_FILES):
            return ['indirect SSH MCP assets; no files read']
        roster = json.loads((folder / 'ssh-servers.json').read_text('utf-8'))
        expected = [
            ('CLOUD', '8.135.38.175', 22, 'root', 0),
            ('RUNNER_LAN', '192.168.0.126', 22, 'mingjian', 1),
            ('RUNNER_WAN', '8.135.38.175', 2201, 'mingjian', 1),
            ('TEST_LAN', '192.168.0.179', 22, 'mingjian02', 2),
            ('TEST_WAN', '8.135.38.175', 2202, 'mingjian02', 2),
            ('PROD_LAN', '192.168.0.106', 22, 'mingjian03', 3),
            ('PROD_WAN', '8.135.38.175', 2203, 'mingjian03', 3),
            ('DGX_LAN', '192.168.0.189', 22, 'ranzuozhou', 4),
            ('DGX_WAN', '8.135.38.175', 2204, 'ranzuozhou', 4),
        ]
        if not isinstance(roster, list) or len(roster) != 9:
            return ['SSH roster mismatch']
        for entry, (sid, host, port, user, index) in zip(roster, expected, strict=True):
            if (not isinstance(entry, dict) or set(entry) != {'id', 'host', 'port', 'user', 'description', 'passwordEnv'}
                    or [entry['id'], entry['host'], entry['port'], entry['user'], entry['passwordEnv']]
                    != [sid, host, port, user, SSH_ENV[index]]):
                return ['SSH roster mismatch']
        package = json.loads((folder / 'package.json').read_text('utf-8'))
        lock = json.loads((folder / 'package-lock.json').read_text('utf-8'))
        pins = {'@modelcontextprotocol/sdk': '1.32.2', 'ssh2': '1.17.0'}
        if (package.get('dependencies') != pins or package.get('private') is not True
                or lock.get('lockfileVersion') != 3 or lock['packages']['']['dependencies'] != pins):
            return ['SSH dependency pins or lock mismatch']
        return []
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return ['unreadable or invalid SSH public assets']


ENFORCEMENT = (".codex/hooks.json", ".codex/rules/mj-agent.rules",
               "scripts/sdd/codex_hook_guard.py", "scripts/sdd/git_command_review.py",
               "scripts/sdd/task_delivery.py",
               "scripts/sdd/run_codex_hook.ps1")


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
            if set(options) != {"pattern", "decision"} or len(stmt.value.keywords) != 2:
                raise ValueError
            if not isinstance(options['pattern'], list) or not all(isinstance(x, str) for x in options['pattern']):
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


def legacy_check(root: Path) -> list[str]:
    """Historical synthetic fixtures only; not a current host activation check."""
    return check_mcp(root) + check_enforcement(root)


def check_project_profile(root: Path) -> list[str]:
    """Current profile deliberately has no project hook/rule execution layer."""
    paths = (root / '.codex', root / '.codex/mcp', root / '.codex/rules', root / '.codex/hooks.json')
    if any(p.is_symlink() or p.is_junction() for p in (*root.parents, root, *paths)):
        return ['indirect project configuration path; no files read']
    if (root / '.codex/hooks.json').exists() or list((root / '.codex/rules').glob('*.rules')):
        return ['project hooks/rules are not part of the MCP-only profile']
    return []


def check(root: Path) -> list[str]:
    errors = check_project_profile(root)
    return errors if errors else check_mcp(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--effective-approval-policy", choices=("never", "on-request", "unknown"))
    parser.add_argument("--surface", choices=("all", "mcp", "enforcement"), default="all")
    args = parser.parse_args()
    errors = {"all": check, "mcp": check, "enforcement": check_project_profile}[args.surface](args.root)
    print(json.dumps({"config": "FAIL" if errors else "STATIC_PASS", "errors": errors,
                      "profile": "INVALID" if errors else "MCP_ONLY",
                      "project_hooks": "UNVERIFIED" if errors else "NOT_CONFIGURED",
                      "project_rules": "UNVERIFIED" if errors else "NOT_CONFIGURED",
                      "effective_approval_policy": args.effective_approval_policy or "unknown",
                      "mcp_runtime": "NOT_TESTED",
                      "owner_approval": "NOT_ASSESSED"}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
