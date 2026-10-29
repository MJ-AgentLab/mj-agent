"""Current project profile: MCP only; fixture tests never start a service."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.sdd.check_codex_native import SSH_FILES, check

ROOT = Path(__file__).resolve().parents[2]


def fixture(tmp_path: Path) -> Path:
    root = tmp_path / 'project'
    for rel in ('.codex/config.toml', 'scripts/mcp/pg-server-start.ps1',
                'scripts/mcp/pg-server-wrapper.mjs', 'scripts/mcp/setup-mcp-secrets.ps1',
                'scripts/sdd/check_codex_native.py', *SSH_FILES):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    config = root / '.codex/config.toml'
    content = config.read_text('utf-8')
    content = '\n'.join(line for line in content.splitlines()
                        if not line.startswith(('approval_policy =', 'sandbox_mode =',
                                                'project_doc_max_bytes ='))) + '\n'
    config.write_text(content, encoding='utf-8')
    return root


def test_mcp_only_profile_needs_no_project_hook_or_permission_override(tmp_path: Path) -> None:
    assert check(fixture(tmp_path)) == []


def test_reintroduced_project_hook_is_not_silently_admitted(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    (root / '.codex/hooks.json').write_text('{"hooks": {}}', encoding='utf-8')
    assert check(root)


def test_ssh_choice_does_not_admit_unapproved_service(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    path = root / '.codex/config.toml'
    path.write_text(path.read_text('utf-8') + '\n[mcp_servers.unapproved]\ncommand="ignored"\n',
                    encoding='utf-8')
    assert check(root)


def test_ssh_password_inline_and_foreign_host_are_rejected_without_echo(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    path = root / '.codex/mcp/ssh-servers.json'
    roster = json.loads(path.read_text('utf-8'))
    roster[0]['password'] = 'SYNTHETIC_SECRET'
    path.write_text(json.dumps(roster), encoding='utf-8')
    errors = check(root)
    assert errors and 'SYNTHETIC_SECRET' not in repr(errors)
    del roster[0]['password']
    roster[0]['host'] = 'foreign.invalid'
    path.write_text(json.dumps(roster), encoding='utf-8')
    assert check(root)


def test_ssh_by_name_scope_cannot_import_another_service_token(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    path = root / '.codex/config.toml'
    path.write_text(path.read_text('utf-8').replace('MJ_SYS_SSH_SERVER_PROD_PASSWORD',
                                                  'DATABASE_PASSWORD'), encoding='utf-8')
    assert check(root)
