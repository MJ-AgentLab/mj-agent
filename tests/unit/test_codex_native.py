"""P1 native candidates: synthetic fixtures only; no services or user config."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from scripts.sdd.check_codex_native import approval_status, check
from scripts.sdd.codex_hook_guard import classify, project_payload

ROOT = Path(__file__).resolve().parents[2]


def candidate(tmp_path: Path) -> Path:
    root = tmp_path / "project with spaces"
    for rel in (".codex", "scripts/mcp"):
        shutil.copytree(ROOT / rel, root / rel)
    (root / "scripts/sdd").mkdir(parents=True)
    for name in ("codex_hook_guard.py", "check_codex_native.py", "run_codex_hook.ps1"):
        shutil.copyfile(ROOT / "scripts/sdd" / name, root / "scripts/sdd" / name)
    return root


def test_project_only_config_and_independent_checks(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    assert not (root / ".claude").exists()
    assert not (root / "sdd").exists()
    assert check(root) == []


@pytest.mark.parametrize("relative", [
    ".codex/config.toml", ".codex/hooks.json", ".codex/rules/mj-agent.rules",
    "scripts/mcp/pg-server-start.ps1", "scripts/mcp/pg-server-wrapper.mjs",
    "scripts/mcp/setup-mcp-secrets.ps1", "scripts/sdd/codex_hook_guard.py",
    "scripts/sdd/run_codex_hook.ps1",
])
def test_missing_required_file_fails(tmp_path: Path, relative: str) -> None:
    root = candidate(tmp_path)
    (root / relative).unlink()
    assert check(root)


@pytest.mark.parametrize("text", [
    "not = [valid", "[mcp_servers.unknown]\ncommand='ignored'\n",
    "[mcp_servers.ssh-manager]\ncommand='ignored'\n",
    "[mcp_servers.pg-mj-system-biz-dev]\ncommand='ignored'\n",
])
def test_invalid_or_foreign_mcp_is_rejected(tmp_path: Path, text: str) -> None:
    root = candidate(tmp_path)
    (root / ".codex/config.toml").write_text(text, encoding="utf-8")
    assert check(root)


def test_no_secret_echo_and_repair(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    path = root / ".codex/config.toml"
    original = path.read_text("utf-8")
    sentinel = "synthetic-secret-do-not-echo"
    path.write_text(original + '\n[mcp_servers.github.env]\nTOKEN="' + sentinel + '"\n', encoding="utf-8")
    errors = check(root)
    assert errors and sentinel not in repr(errors)
    path.write_text(original, encoding="utf-8")
    assert check(root) == []


def test_rules_and_hooks_malformed_fail(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    (root / ".codex/hooks.json").write_text("{", encoding="utf-8")
    assert check(root)
    root2 = candidate(tmp_path / "other")
    (root2 / ".codex/rules/mj-agent.rules").write_text("exec('not permitted')", encoding="utf-8")
    assert check(root2)


@pytest.mark.parametrize(("mode", "expected"), [
    (None, "UNKNOWN"), ("unknown", "UNKNOWN"), ("never", "INCOMPATIBLE"),
    ("on-request", "APPROVAL_REQUIRED"),
])
def test_approval_layers_remain_separate(mode: str | None, expected: str) -> None:
    assert approval_status(mode) == expected


@pytest.mark.parametrize(("command", "expected"), [
    ("git status", "ALLOW"), ("git checkout -b trial", "FORBIDDEN"),
    ("git switch -c trial", "FORBIDDEN"), ("psql", "FORBIDDEN"),
    ("pg_dump", "FORBIDDEN"), ("gh pr merge 1", "FORBIDDEN"),
    ("gh pr create", "FORBIDDEN"), ("gh pr create --base develop", "OWNER_APPROVAL_REQUIRED"),
    ("git push origin example", "OWNER_APPROVAL_REQUIRED"),
    ("Get-Content .env", "FORBIDDEN"), ("Get-Content .env.example", "ALLOW"),
])
def test_native_command_boundaries(command: str, expected: str) -> None:
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}
    assert classify(project_payload(payload))[0] == expected


@pytest.mark.parametrize(("path", "expected"), [
    (".agents/skills/mj-agent-flow-verify/SKILL.md", "ALLOW"),
    (".codex/config.toml", "OWNER_APPROVAL_REQUIRED"),
    ("src/mj_agent/skills/example/SKILL.md", "OWNER_APPROVAL_REQUIRED"),
    ("D:/project/src/mj_agent/prompts/system.md", "OWNER_APPROVAL_REQUIRED"),
    (".agents/skills/mj-agent-infra-app-start/SKILL.md", "OWNER_APPROVAL_REQUIRED"),
    ("config/secrets-mcp.enc", "FORBIDDEN"),
])
def test_native_edit_ownership(path: str, expected: str) -> None:
    patch = f"*** Begin Patch\n*** Update File: {path}\n@@\n-a\n+b\n*** End Patch"
    payload = {"tool_name": "apply_patch", "tool_input": patch, "hook_event_name": "PreToolUse"}
    assert classify(project_payload(payload))[0] == expected


def test_payload_projection_never_reads_private_fields() -> None:
    class Spy(dict):
        def __getitem__(self, key):
            assert key not in {"transcript_path", "session_id", "last_assistant_message", "cwd"}
            return super().__getitem__(key)
    payload = Spy(tool_name="Bash", hook_event_name="PreToolUse", tool_input={"command": "git status"},
                  transcript_path="never-read", session_id="never-read", cwd="never-read")
    assert classify(project_payload(payload))[0] == "ALLOW"
    assert classify({})[0] == "UNKNOWN"


def clean_env(tmp_path: Path) -> dict[str, str]:
    # Explicit platform carrier only, never inherit credential variables.
    env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT") if k in os.environ}
    for key in ("USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        folder = tmp_path / key
        folder.mkdir(parents=True, exist_ok=True)
        env[key] = str(folder)
    return env


@pytest.mark.skipif(os.name != "nt", reason="Windows launcher; Linux MCP not in scope")
def test_missing_connection_fails_before_npx_from_subdirectory(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    sub = root / "nested child"
    sub.mkdir()
    proc = subprocess.run(["pwsh", "-NoProfile", "-File", str(root / "scripts/mcp/pg-server-start.ps1"),
                           "MJ_AGENT_PG_MEMORY_DEV_URL"], cwd=sub, env=clean_env(tmp_path / "env"),
                          capture_output=True, text=True, check=False, timeout=20)
    assert proc.returncode == 3
    assert "MISSING" in proc.stderr
    assert "MJ_AGENT_PG_MEMORY_DEV_URL" in proc.stderr


def test_wrapper_error_never_echoes_connection(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    env = clean_env(tmp_path / "env")
    sentinel = "synthetic-connection-must-not-be-logged"
    env["MJ_AGENT_PG_MEMORY_DEV_URL"] = sentinel
    env["NODE_PATH"] = str(tmp_path / "missing modules")
    proc = subprocess.run(["node", str(root / "scripts/mcp/pg-server-wrapper.mjs"),
                           "MJ_AGENT_PG_MEMORY_DEV_URL"], env=env,
                          capture_output=True, text=True, check=False, timeout=20)
    assert proc.returncode != 0
    assert sentinel not in proc.stdout + proc.stderr


def test_hook_cli_reports_unknown_instead_of_success(tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/sdd/codex_hook_guard.py")],
                          input="{", env=clean_env(tmp_path), text=True, capture_output=True,
                          check=False, timeout=20)
    assert json.loads(proc.stdout)["decision"] == "block"
    assert "UNKNOWN" in proc.stdout


def fake_pg_modules(tmp_path: Path) -> Path:
    modules = tmp_path / 'node_modules'
    pg = modules / 'pg'
    pg.mkdir(parents=True)
    (pg / 'package.json').write_text('{"main":"index.js"}', encoding='utf-8')
    (pg / 'index.js').write_text('exports.parsers={};exports.types={setTypeParser:(oid,fn)=>exports.parsers[oid]=fn};', encoding='utf-8')
    server = modules / '@modelcontextprotocol/server-postgres/dist'
    server.mkdir(parents=True)
    (server / 'index.js').write_text("""
const pg = require('pg');
const value = '2026-09-18 12:34:56.123+08';
if (pg.parsers[1114](value) !== value || pg.parsers[1184](value) !== value) throw Error('timestamp');
if (process.argv[2] !== 'synthetic-memory-input') throw Error('argument');
console.log('WRAPPER_PASS');
""", encoding='utf-8')
    return modules


def test_wrapper_preserves_timestamp_and_consumes_name(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    env = clean_env(tmp_path / 'env')
    env['NODE_PATH'] = str(fake_pg_modules(tmp_path))
    env['MJ_AGENT_PG_MEMORY_DEV_URL'] = 'synthetic-memory-input'
    result = subprocess.run(['node', str(root / 'scripts/mcp/pg-server-wrapper.mjs'),
                             'MJ_AGENT_PG_MEMORY_DEV_URL'], env=env, capture_output=True, text=True,
                            check=False, timeout=20)
    assert result.returncode == 0 and result.stdout.strip() == 'WRAPPER_PASS'
    assert not result.stderr


@pytest.mark.skipif(os.name != 'nt', reason='Windows launcher')
def test_launcher_with_stub_package_from_space_subdirectory(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    modules = fake_pg_modules(tmp_path)
    binaries = tmp_path / 'stub bin'
    binaries.mkdir()
    # npx is a process double: no download, no service and no real environment.
    (binaries / 'npx.cmd').write_text('@echo off\r\necho ' + str(modules) + '\r\n', encoding='utf-8')
    env = clean_env(tmp_path / 'env')
    env['PATH'] = str(binaries) + os.pathsep + env['PATH']
    env['MJ_AGENT_PG_MEMORY_DEV_URL'] = 'synthetic-memory-input'
    child = root / 'child with spaces'
    child.mkdir()
    result = subprocess.run(['pwsh', '-NoProfile', '-File', str(root / 'scripts/mcp/pg-server-start.ps1'),
                             'MJ_AGENT_PG_MEMORY_DEV_URL'], cwd=child, env=env, capture_output=True,
                            text=True, check=False, timeout=20)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'WRAPPER_PASS'
    assert 'synthetic-memory-input' not in result.stdout + result.stderr


@pytest.mark.skipif(os.name != 'nt', reason='Windows PowerShell helpers')
def test_secret_helpers_only_synthetic_no_script_execution(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    # Parse definitions, then execute only two pure helper functions with synthetic text.
    # Do not dot-source the maintenance script: that would read/write User credentials.
    script = r"""
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$tokens,[ref]$errors)
if ($errors.Count) { exit 2 }
$AllowedKeys=@('GITHUB_PERSONAL_ACCESS_TOKEN','MJ_AGENT_PG_MEMORY_DEV_URL')
$ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -in @('ConvertFrom-McpEnv','Format-MaskedValue')},$false) | ForEach-Object { . ([scriptblock]::Create($_.Extent.Text)) }
$v=ConvertFrom-McpEnv @('GITHUB_PERSONAL_ACCESS_TOKEN=synthetic-value','UNRELATED_PLUGIN_TOKEN=discard','APP_PASSWORD=discard')
if ($v.Count -ne 1 -or $v['GITHUB_PERSONAL_ACCESS_TOKEN'] -ne 'synthetic-value') { exit 3 }
if ((Format-MaskedValue 'synthetic-value') -ne '[REDACTED]') { exit 4 }
Write-Output 'HELPERS_PASS'
"""
    helper = tmp_path / 'helper-test.ps1'
    helper.write_text(script, encoding='utf-8')
    result = subprocess.run(['pwsh', '-NoProfile', '-File', str(helper),
                             str(root / 'scripts/mcp/setup-mcp-secrets.ps1')],
                            env=clean_env(tmp_path / 'env'), capture_output=True, text=True,
                            check=False, timeout=20)
    assert result.returncode == 0 and result.stdout.strip() == 'HELPERS_PASS', result.stderr


@pytest.mark.skipif(os.name != 'nt', reason='Windows project command')
def test_config_command_resolves_git_root_from_child(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    env = clean_env(tmp_path / 'env')
    subprocess.run(['git', 'init', '--quiet', str(root)], env=env, check=True, capture_output=True)
    child = root / 'nested space'
    child.mkdir()
    config = tomllib.loads((root / '.codex/config.toml').read_text('utf-8'))
    server = config['mcp_servers']['pg-mj-agent-memory-dev']
    result = subprocess.run([server['command'], *server['args']], cwd=child, env=env,
                            capture_output=True, text=True, check=False, timeout=20)
    assert result.returncode == 3 and '[MISSING]' in result.stderr


@pytest.mark.skipif(os.name != 'nt', reason='Windows project hook command')
@pytest.mark.parametrize('shell', ['cmd', 'pwsh'])
def test_hook_command_resolves_root_and_preserves_payload(tmp_path: Path, shell: str) -> None:
    root = candidate(tmp_path)
    env = clean_env(tmp_path / 'env')
    subprocess.run(['git', 'init', '--quiet', str(root)], env=env, check=True, capture_output=True)
    binaries = tmp_path / 'stub bin'
    binaries.mkdir()
    # Stub uv emits fixed protocol output; no venv or network access.
    probe = binaries / 'uv-probe.py'
    probe.write_text("import json,sys\nassert json.load(sys.stdin)=={'synthetic': True}\nprint(json.dumps({'decision':'block','reason':'SYNTHETIC_STOP'}))\n", encoding='utf-8')
    (binaries / 'uv.cmd').write_text(f'@echo off\r\n"{sys.executable}" -B "{probe}"\r\n', encoding='utf-8')
    env['PATH'] = str(binaries) + os.pathsep + env['PATH']
    child = root / 'nested space'
    child.mkdir()
    command = json.loads((root / '.codex/hooks.json').read_text('utf-8'))['hooks']['PreToolUse'][0]['hooks'][0]['command']
    args = ['cmd', '/d', '/c', command] if shell == 'cmd' else ['pwsh', '-NoProfile', '-Command', command]
    result = subprocess.run(args, cwd=child, env=env, input='{"synthetic":true}', capture_output=True,
                            text=True, check=False, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['reason'] == 'SYNTHETIC_STOP'


@pytest.mark.skipif(os.name != 'nt', reason='Windows project commands')
def test_wrong_git_root_never_falls_back_to_parent_assets(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    env = clean_env(tmp_path / 'env')
    unrelated = tmp_path / 'unrelated project'
    subprocess.run(['git', 'init', '--quiet', str(unrelated)], env=env, capture_output=True, check=True)
    hooks = json.loads((root / '.codex/hooks.json').read_text('utf-8'))
    command = hooks['hooks']['PreToolUse'][0]['hooks'][0]['command']
    result = subprocess.run(['pwsh', '-NoProfile', '-Command', command], cwd=unrelated, env=env,
                            capture_output=True, text=True, check=False, timeout=20)
    assert result.returncode == 0
    assert json.loads(result.stdout)['decision'] == 'block'
    assert 'UNKNOWN' in json.loads(result.stdout)['reason']


def test_hook_command_injection_is_not_a_valid_configuration(tmp_path: Path) -> None:
    root = candidate(tmp_path)
    path = root / '.codex/hooks.json'
    hooks = json.loads(path.read_text('utf-8'))
    hooks['hooks']['PreToolUse'][0]['hooks'][0]['command'] += ' synthetic-secret-do-not-echo'
    path.write_text(json.dumps(hooks), encoding='utf-8')
    errors = check(root)
    assert errors and 'synthetic-secret-do-not-echo' not in repr(errors)
