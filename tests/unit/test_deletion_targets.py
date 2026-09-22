"""Deletion review uses synthetic repositories, never real data or approval receipts."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.sdd.check_deletion_targets import (
    diagnose_rejection,
    inspect_targets,
    probe_delete_access,
)


def test_windows_identity_uses_birth_time_not_ambiguous_ctime() -> None:
    from scripts.sdd.check_deletion_targets import _identity
    common = dict(st_dev=1, st_ino=2, st_mode=0o100666, st_size=7, st_mtime_ns=200,
                  st_birthtime_ns=100)
    assert _identity(SimpleNamespace(**common, st_ctime_ns=100)) == [1, 2, 0o100666, 7, 200, 100]
    assert _identity(SimpleNamespace(**common, st_ctime_ns=200)) == [1, 2, 0o100666, 7, 200, 100]


def git(root: Path, *args: str) -> None:
    subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / 'repo with spaces'
    root.mkdir()
    git(root, 'init')
    (root / 'tracked.txt').write_text('original', encoding='utf-8')
    (root / '.gitignore').write_text('ignored/\n', encoding='utf-8')
    git(root, 'add', 'tracked.txt', '.gitignore')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fixture')
    return root


def inspect(root: Path, targets: list[Path], **kwargs):
    return inspect_targets(root, targets, access_probe=lambda path: 'AVAILABLE', **kwargs)


def test_clean_tracked_is_reviewable_but_not_authorized(repo: Path) -> None:
    result = inspect(repo, [repo / 'tracked.txt'])
    assert result['items'][0]['status'] == 'READY_FOR_REVIEW'
    assert result['owner_approval'] == 'NOT_ASSESSED'
    assert result['execution'] == 'NOT_ATTEMPTED'
    assert (repo / 'tracked.txt').read_text() == 'original'


@pytest.mark.parametrize('kind', ['untracked', 'ignored', 'dirty', 'staged'])
def test_valuable_content_requires_verified_backup(repo: Path, tmp_path: Path, kind: str) -> None:
    target = repo / ('ignored/item.txt' if kind == 'ignored' else
                     'tracked.txt' if kind in {'dirty', 'staged'} else 'new.txt')
    target.parent.mkdir(exist_ok=True)
    target.write_text('valuable', encoding='utf-8')
    if kind == 'staged':
        git(repo, 'add', 'tracked.txt')
    result = inspect(repo, [target])
    assert result['items'][0]['status'] == 'BACKUP_REQUIRED'
    backup = tmp_path / 'backup.txt'
    backup.write_text('wrong', encoding='utf-8')
    assert inspect(repo, [target], backups={str(target): backup})['items'][0]['status'] == 'BACKUP_REQUIRED'
    backup.write_text('valuable', encoding='utf-8')
    assert inspect(repo, [target], backups={str(target): backup})['items'][0]['status'] == 'READY_FOR_REVIEW'


def test_directory_members_and_git_state_are_captured(repo: Path) -> None:
    target = repo / 'folder'
    target.mkdir()
    (target / 'file.txt').write_text('first')
    git(repo, 'add', 'folder')
    result = inspect(repo, [target])
    assert result['items'][0]['status'] == 'BACKUP_REQUIRED'
    member = result['items'][0]['snapshot']['members']['file.txt']
    assert member['git']['tracked'] is True
    assert member['git']['status'] == 'A '


@pytest.mark.parametrize('flag', ['--skip-worktree', '--assume-unchanged'])
def test_git_hidden_modifications_require_backup(repo: Path, flag: str) -> None:
    target = repo / 'tracked.txt'
    git(repo, 'update-index', flag, 'tracked.txt')
    target.write_text('valuable hidden modification')
    assert inspect(repo, [target])['items'][0]['status'] == 'BACKUP_REQUIRED'


def test_change_during_access_probe_is_not_reviewable(repo: Path) -> None:
    target = repo / 'tracked.txt'
    def mutate(path):
        path.write_text('changed during inspection')
        return 'AVAILABLE'
    result = inspect_targets(repo, [target], access_probe=mutate)
    assert result['items'][0]['status'] == 'CHANGED'


def test_git_failure_and_non_repository_are_unknown(tmp_path: Path) -> None:
    target = tmp_path / 'item'
    target.write_text('valuable')
    assert inspect(tmp_path, [target])['items'][0]['status'] == 'UNKNOWN'


def test_nested_repository_is_out_of_scope(repo: Path) -> None:
    nested = repo / 'nested'
    nested.mkdir()
    git(nested, 'init')
    target = nested / 'file.txt'
    target.write_text('nested')
    assert inspect(repo, [target])['items'][0]['status'] == 'OUT_OF_SCOPE'


@pytest.mark.parametrize('change', ['content', 'replacement', 'new-member', 'git-index'])
def test_changes_pause_only_the_affected_item(repo: Path, change: str) -> None:
    folder = repo / 'folder'
    folder.mkdir()
    item = folder / 'item.txt'
    item.write_text('before')
    baseline = inspect(repo, [folder, repo / 'tracked.txt'])
    if change == 'content':
        item.write_text('after')
    elif change == 'replacement':
        replacement = repo / 'replacement'
        replacement.write_text('before')
        replacement.replace(item)
    elif change == 'new-member':
        (folder / 'new.txt').write_text('new')
    else:
        git(repo, 'add', 'folder')
    result = inspect(repo, [folder, repo / 'tracked.txt'], baseline=baseline)
    assert [i['status'] for i in result['items']] == ['CHANGED', 'READY_FOR_REVIEW']
    differences = result['items'][0]['differences']
    assert 'new.txt' in differences['added'] if change == 'new-member' else 'item.txt' in differences['modified']


def test_scope_cannot_expand_and_absent_items_are_reported(repo: Path) -> None:
    target = repo / 'tracked.txt'
    baseline = inspect(repo, [target])
    target.unlink()
    result = inspect(repo, [target, repo / 'new'], baseline=baseline)
    assert [i['status'] for i in result['items']] == ['ALREADY_ABSENT', 'OUT_OF_SCOPE']


def test_other_worktree_and_head_changes_invalidate_baseline(repo: Path, tmp_path: Path) -> None:
    baseline = inspect(repo, [repo / 'tracked.txt'])
    other = tmp_path / 'other'
    git(repo, 'worktree', 'add', '--detach', str(other))
    assert inspect(other, [other / 'tracked.txt'], baseline=baseline)['items'][0]['status'] == 'OUT_OF_SCOPE'
    git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        '-c', 'core.hooksPath=/dev/null', 'commit', '--allow-empty', '-m', 'next')
    assert inspect(repo, [repo / 'tracked.txt'], baseline=baseline)['items'][0]['status'] == 'CHANGED'


@pytest.mark.parametrize('relative', ['.', '.git', '.git/config', '../outside', 'folder/../tracked.txt'])
def test_unsafe_targets_fail_closed(repo: Path, relative: str) -> None:
    assert inspect(repo, [repo / relative])['items'][0]['status'] == 'OUT_OF_SCOPE'


def test_relative_target_is_not_resolved_against_cwd(repo: Path) -> None:
    assert inspect(repo, [Path('tracked.txt')])['items'][0]['status'] == 'OUT_OF_SCOPE'


def test_secret_descendant_is_never_opened(repo: Path, monkeypatch) -> None:
    from scripts.sdd import check_deletion_targets as checker
    folder = repo / 'folder'
    folder.mkdir()
    (folder / '.env').write_text('SYNTHETIC_ONLY')
    original = checker._digest
    def checked_digest(path, *args, **kwargs):
        assert Path(path).name != '.env'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(checker, '_digest', checked_digest)
    result = inspect(repo, [folder])
    assert result['items'][0]['status'] == 'SECRET_BOUNDARY'
    assert 'SYNTHETIC_ONLY' not in json.dumps(result)


def test_hardlink_is_not_an_independent_backup(repo: Path, tmp_path: Path) -> None:
    target = repo / 'new.txt'
    target.write_text('valuable')
    backup = tmp_path / 'backup'
    os.link(target, backup)
    assert inspect(repo, [target], backups={str(target): backup})['items'][0]['status'] != 'READY_FOR_REVIEW'


@pytest.mark.parametrize('state', ['IN_USE', 'UNKNOWN'])
def test_occupancy_unknown_and_git_failure_never_pass(repo: Path, state: str) -> None:
    result = inspect_targets(repo, [repo / 'tracked.txt'], access_probe=lambda path: state)
    assert result['items'][0]['status'] == state


def test_malformed_baseline_does_not_grant_scope(repo: Path) -> None:
    assert inspect(repo, [repo / 'tracked.txt'], baseline={'items': 'bad'})['items'][0]['status'] == 'UNKNOWN'


def test_reparse_ancestor_and_descendant_are_rejected(repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'file.txt').write_text('outside')
    link = repo / 'link'
    if os.name == 'nt':
        # Fixed synthetic paths only; no deletion or cross-shell filesystem cleanup.
        proc = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
        assert proc.returncode == 0
    else:
        link.symlink_to(outside, target_is_directory=True)
    assert inspect(repo, [link])['items'][0]['status'] == 'REPARSE_POINT'
    assert inspect(repo, [link / 'file.txt'])['items'][0]['status'] == 'REPARSE_POINT'


@pytest.mark.skipif(os.name != 'nt', reason='Windows delete-sharing semantics')
def test_native_probe_detects_handle_without_delete_sharing(repo: Path) -> None:
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    target = repo / 'tracked.txt'
    handle = kernel.CreateFileW(str(target), 0x80000000, 1, None, 3, 0, None)
    assert handle != wintypes.HANDLE(-1).value
    try:
        assert probe_delete_access(target) == 'IN_USE'
    finally:
        kernel.CloseHandle(handle)
    assert probe_delete_access(target) == 'AVAILABLE'
    assert target.read_text() == 'original'


@pytest.mark.parametrize(('error', 'mode', 'expected'), [
    ('CreateProcess rejected: blocked by policy', None, 'UNKNOWN_LAYER'),
    ('approval required by policy, but AskForApproval is set to Never', 'never', 'APPROVAL_MODE'),
    ('{"decision":"block","reason":"UNKNOWN: compound command"}', None, 'PROJECT_HOOK'),
    ('PermissionError: access denied', 'on-request', 'FILESYSTEM_PERMISSION'),
    ('WinError 32: sharing violation', None, 'FILE_IN_USE'),
    ('unrecognized failure', 'on-request', 'UNKNOWN_LAYER'),
    ('exec-policy: forbidden command', 'on-request', 'EXEC_POLICY'),
    ("fatal: Unable to create 'index.lock': Permission denied", None, 'FILESYSTEM_PERMISSION'),
    ('fatal: unable to access remote: Failed to connect: Connection refused', None, 'NETWORK'),
    ('AskForApproval is set to Never', 'never', 'APPROVAL_MODE'),
])
def test_rejection_diagnosis_preserves_evidence_without_guessing(error, mode, expected) -> None:
    result = diagnose_rejection(error, mode)
    assert result['layer'] == expected
    assert result['original_error'] == error
    assert result['retry'] == 'STOP_AFFECTED_ACTION'


def test_cli_baseline_backup_and_recheck(repo: Path, tmp_path: Path, capsys) -> None:
    from scripts.sdd.check_deletion_targets import main
    target = repo / 'tracked.txt'
    args = ['--root', str(repo), '--target', str(target)]
    status = main(args)
    baseline = tmp_path / 'baseline.json'
    first = capsys.readouterr().out
    baseline.write_text(first, encoding='utf-8')
    assert status == (0 if os.name == 'nt' else 1)
    result = main([*args, '--baseline', str(baseline)])
    assert result == status
    report = json.loads(capsys.readouterr().out)
    assert report['owner_approval'] == 'NOT_ASSESSED'
    target.write_text('changed')
    assert main([*args, '--baseline', str(baseline)]) == 1
    assert json.loads(capsys.readouterr().out)['items'][0]['status'] == 'CHANGED'


def test_cli_rejects_secret_baseline_without_opening(repo: Path, capsys) -> None:
    from scripts.sdd.check_deletion_targets import main
    secret = repo / '.env'
    secret.write_text('SYNTHETIC_ONLY')
    assert main(['--root', str(repo), '--target', str(repo / 'tracked.txt'),
                 '--baseline', str(secret)]) == 2
    output = capsys.readouterr().out
    assert 'INVALID_BASELINE' in output and 'SYNTHETIC_ONLY' not in output


def test_cli_diagnosis_is_not_success(capsys) -> None:
    from scripts.sdd.check_deletion_targets import main
    assert main(['--diagnose-error', 'blocked by policy',
                 '--effective-approval-policy', 'never']) == 1
    assert json.loads(capsys.readouterr().out)['layer'] == 'UNKNOWN_LAYER'


def test_backup_directory_must_match_all_members(repo: Path, tmp_path: Path) -> None:
    folder = repo / 'folder'
    folder.mkdir()
    (folder / 'one.txt').write_text('one')
    (folder / 'two.txt').write_text('two')
    backup = tmp_path / 'backup'
    backup.mkdir()
    (backup / 'one.txt').write_text('one')
    assert inspect(repo, [folder], backups={str(folder): backup})['items'][0]['status'] == 'BACKUP_REQUIRED'
    (backup / 'two.txt').write_text('two')
    assert inspect(repo, [folder], backups={str(folder): backup})['items'][0]['status'] == 'READY_FOR_REVIEW'
