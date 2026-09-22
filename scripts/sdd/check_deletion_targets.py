"""Read-only deletion review. Snapshots are comparison data, never authorization.

No deletion, backup creation, process termination, permission changes or hook calls.
READY_FOR_REVIEW requires separate task authorization and normal host approval.
Reinspect immediately before acting; a snapshot cannot eliminate filesystem races.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO


class ReviewStop(Exception):
    """A bounded, value-free diagnostic safe to include in the review."""


def _absolute(path: Path) -> Path:
    if (not path.is_absolute() or any(p in {'.', '..'} for p in path.parts)
            or str(path).startswith(('\\\\', '//'))
            or any(c in str(path) for c in '*?\x00')
            or any(':' in p or p.endswith((' ', '.'))
                   or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', p, re.I)
                   for p in path.parts[1:])):
        raise ReviewStop('OUT_OF_SCOPE')
    return path


def _secret(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    return any(
        (p.startswith('.env') and p != '.env.example')
        or p in {'.ssh', '.aws', '.azure', 'credentials', 'credentials.json', 'id_rsa', 'id_ed25519'}
        or p.endswith(('.pem', '.key', '.pfx', '.p12'))
        or (p.startswith('secrets') and i > 0 and parts[i - 1] == 'config')
        for i, p in enumerate(parts)
    )


def _chain(path: Path) -> None:
    """Check lexically, before resolving/opening anything through a link."""
    for node in (*reversed(path.parents), path):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ReviewStop('REPARSE_POINT')


def _identity(info: os.stat_result) -> list[int]:
    # Windows path-stat and fd-stat can disagree on deprecated st_ctime semantics.
    # Birth time is consistent across both; keep mtime, file ID and content digest.
    return [info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, getattr(info, 'st_birthtime_ns', info.st_ctime_ns)]


def _windows_open(path: Path, access: int) -> tuple[Any, Any]:
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # OPEN_EXISTING, BACKUP_SEMANTICS | OPEN_REPARSE_POINT; never DELETE_ON_CLOSE.
    handle = kernel.CreateFileW(str(path), access, 7, None, 3, 0x02200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    return kernel, handle


def probe_delete_access(path: Path) -> str:
    """Test Windows DELETE access/sharing without deleting or changing the file."""
    if os.name != 'nt':
        return 'UNKNOWN'
    try:
        _chain(path)
        before = path.lstat()
        if stat.S_ISREG(before.st_mode) and getattr(before, 'st_file_attributes', 0) & 1:
            return 'UNKNOWN'
        kernel, handle = _windows_open(path, 0x00010000)  # DELETE access only
        kernel.CloseHandle(handle)
        return 'AVAILABLE' if _identity(path.lstat()) == _identity(before) else 'CHANGED'
    except OSError as exc:
        return 'IN_USE' if getattr(exc, 'winerror', None) in {32, 33} else 'UNKNOWN'
    except ReviewStop:
        return 'UNKNOWN'


@contextmanager
def _checked_reader(path: Path, expected: os.stat_result) -> Iterator[BinaryIO]:
    _chain(path)
    if _secret(path) or not stat.S_ISREG(expected.st_mode):
        raise ReviewStop('SECRET_BOUNDARY' if _secret(path) else 'UNKNOWN')
    if os.name == 'nt':
        import msvcrt
        kernel, handle = _windows_open(path, 0x80000000)  # GENERIC_READ
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except OSError:
            kernel.CloseHandle(handle)
            raise
    else:
        no_follow = getattr(os, 'O_NOFOLLOW', None)
        if not isinstance(no_follow, int):
            raise ReviewStop('UNKNOWN')
        fd = os.open(path, os.O_RDONLY | no_follow)
    with os.fdopen(fd, 'rb') as stream:
        actual = os.fstat(stream.fileno())
        if (_identity(actual) != _identity(expected)
                or getattr(actual, 'st_file_attributes', 0) & 0x400):
            raise ReviewStop('CHANGED')
        yield stream
        if _identity(os.fstat(stream.fileno())) != _identity(expected):
            raise ReviewStop('CHANGED')
    _chain(path)
    if _identity(path.lstat()) != _identity(expected):
        raise ReviewStop('CHANGED')


def _digest(path: Path, expected: os.stat_result) -> str:
    with _checked_reader(path, expected) as stream:
        digest = hashlib.sha256()
        while chunk := stream.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _tree(target: Path) -> dict[str, Any]:
    members: dict[str, Any] = {}
    pending = [target]
    while pending:
        path = pending.pop()
        if _secret(path):
            raise ReviewStop('SECRET_BOUNDARY')
        if path.name.lower() == '.git':
            raise ReviewStop('OUT_OF_SCOPE')
        _chain(path)
        info = path.lstat()
        key = path.relative_to(target).as_posix()
        if stat.S_ISDIR(info.st_mode):
            members[key] = {'kind': 'directory', 'identity': _identity(info)}
            pending.extend(sorted(path.iterdir(), reverse=True))
        elif stat.S_ISREG(info.st_mode):
            if info.st_nlink != 1:
                raise ReviewStop('UNKNOWN')  # shared content is not an independent copy
            members[key] = {'kind': 'file', 'identity': _identity(info),
                            'sha256': _digest(path, info)}
        else:
            raise ReviewStop('UNKNOWN')
    # Detect directory/member replacement during enumeration, including empty dirs.
    for key, member in members.items():
        path = target if key == '.' else target / key
        _chain(path)
        if _identity(path.lstat()) != member['identity']:
            raise ReviewStop('CHANGED')
    return members


def _git(root: Path, *args: str) -> str:
    env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT')
           if k in os.environ}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS='0')
    try:
        proc = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args],
                              env=env, capture_output=True, check=False, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewStop('UNKNOWN') from exc
    if proc.returncode:
        raise ReviewStop('UNKNOWN')
    return proc.stdout.decode('utf-8', errors='strict')


def _git_state(root: Path, target: Path, members: dict[str, Any]) -> dict[str, str]:
    rel = target.relative_to(root).as_posix()
    # Literal pathspec also prevents magic in filenames from expanding the review scope.
    pathspec = ':(literal)' + rel
    tracked: dict[str, list[str]] = {}
    for record in _git(root, 'ls-files', '--stage', '-z', '--', pathspec).split('\0'):
        if record:
            metadata, name = record.split('\t', 1)
            tracked.setdefault(name, []).append(metadata)
    flags = {record[2:]: record[0] for record in
             _git(root, 'ls-files', '-v', '-z', '--', pathspec).split('\0') if record}
    changes: dict[str, str] = {}
    records = iter(_git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all',
                        '--ignored', '--', pathspec).split('\0'))
    for record in records:
        if not record:
            continue
        status, name = record[:2], record[3:]
        changes[name] = status
        if 'R' in status or 'C' in status:
            next(records)  # original name in porcelain -z format
    for key, member in members.items():
        name = rel if key == '.' else rel + '/' + key
        status = changes.get(name, '')
        if not status:
            status = next((value for changed, value in changes.items()
                           if changed.endswith('/') and name.startswith(changed)), '')
        member['git'] = {'tracked': name in tracked, 'index': tracked.get(name, []),
                         'status': status, 'flag': flags.get(name, '')}
    return changes


def _content(members: dict[str, Any]) -> dict[str, Any]:
    return {key: (value['kind'], value.get('sha256')) for key, value in members.items()}


def _backup_matches(target: Path, members: dict[str, Any], backup: Path | None) -> bool:
    if backup is None:
        return False
    try:
        _absolute(backup)
        if backup.is_relative_to(target) or target.is_relative_to(backup):
            return False
        other = _tree(backup)
        source_ids = {tuple(m['identity'][:2]) for m in members.values()}
        return (_content(other) == _content(members)
                and not any(tuple(m['identity'][:2]) in source_ids for m in other.values()))
    except (OSError, ReviewStop):
        return False


def _needs_backup(members: dict[str, Any]) -> bool:
    files = [m for m in members.values() if m['kind'] == 'file']
    return not files or any(not m['git']['tracked'] or m['git']['status']
                            or m['git']['flag'] != 'H' for m in files)


def _differences(before: Any, after: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(before, dict) or not isinstance(before.get('members'), dict):
        return {'reason': 'NO_COMPARABLE_SNAPSHOT'}
    old, new = before['members'], after['members']
    if not all(isinstance(key, str) for key in old):
        return {'reason': 'NO_COMPARABLE_SNAPSHOT'}
    return {'added': sorted(new.keys() - old.keys()),
            'removed': sorted(old.keys() - new.keys()),
            'modified': sorted(k for k in new.keys() & old.keys() if old[k] != new[k]),
            'git_status_changed': before.get('git_changes') != after['git_changes']}


def _scope(root: Path, target: Path) -> None:
    _absolute(target)
    if target == root or not target.is_relative_to(root) or '.git' in (
            p.lower() for p in target.relative_to(root).parts):
        raise ReviewStop('OUT_OF_SCOPE')
    if _secret(target):
        raise ReviewStop('SECRET_BOUNDARY')
    _chain(target)
    # A nested repository/worktree is a different deletion scope, even if under root.
    for node in (target, *target.parents):
        if node == root:
            break
        if (node / '.git').exists():
            raise ReviewStop('OUT_OF_SCOPE')


def inspect_targets(
    root: Path, targets: list[Path], *, baseline: dict[str, Any] | None = None,
    backups: dict[str, Path] | None = None,
    access_probe: Callable[[Path], str] = probe_delete_access,
) -> dict[str, Any]:
    """Inspect items independently. A passed comparison never supplies approval."""
    result: dict[str, Any] = {'schema': 1, 'owner_approval': 'NOT_ASSESSED',
                              'execution': 'NOT_ATTEMPTED', 'items': []}
    try:
        _absolute(root)
        _chain(root)
        if Path(_git(root, 'rev-parse', '--show-toplevel').strip()) != root:
            raise ReviewStop('OUT_OF_SCOPE')
        context = {'root': str(root), 'root_identity': _identity(root.stat())[:2],
                   'head': _git(root, 'rev-parse', 'HEAD').strip()}
        result['context'] = context
        previous = {}
        if baseline is not None:
            if (not isinstance(baseline, dict) or baseline.get('schema') != 1
                    or not isinstance(baseline.get('context'), dict)
                    or not isinstance(baseline.get('items'), list)):
                raise ReviewStop('UNKNOWN')
            for previous_item in baseline['items']:
                if (not isinstance(previous_item, dict)
                        or not isinstance(previous_item.get('target'), str)
                        or previous_item['target'] in previous):
                    raise ReviewStop('UNKNOWN')
                previous[previous_item['target']] = previous_item
    except (OSError, ValueError, ReviewStop) as exc:
        status = str(exc) if isinstance(exc, ReviewStop) else 'UNKNOWN'
        result['items'] = [{'target': str(p), 'status': status} for p in targets]
        return result

    for target in targets:
        item: dict[str, Any] = {'target': str(target), 'status': 'UNKNOWN'}
        result['items'].append(item)
        try:
            _scope(root, target)
            if baseline is not None:
                if str(target) not in previous or baseline['context'].get('root') != str(root):
                    item['differences'] = {'reason': 'TARGET_OR_WORKTREE_NOT_IN_BASELINE'}
                    raise ReviewStop('OUT_OF_SCOPE')
                if baseline['context'] != context:
                    item['differences'] = {'reason': 'WORKTREE_IDENTITY_OR_HEAD_CHANGED'}
                    raise ReviewStop('CHANGED')
            if not target.exists():
                item['status'] = 'ALREADY_ABSENT'
                continue
            members = _tree(target)
            changes = _git_state(root, target, members)
            snapshot = {'members': members, 'git_changes': changes}
            item['snapshot'] = snapshot
            if baseline is not None and previous[str(target)].get('snapshot') != snapshot:
                item['differences'] = _differences(previous[str(target)].get('snapshot'), snapshot)
                raise ReviewStop('CHANGED')
            for key in members:
                state = access_probe(target if key == '.' else target / key)
                if state != 'AVAILABLE':
                    raise ReviewStop(state if state in {'IN_USE', 'CHANGED'} else 'UNKNOWN')
            needs_backup = bool(changes) or _needs_backup(members)
            backup_ok = _backup_matches(target, members, (backups or {}).get(str(target)))
            # A successful probe/backup comparison must not hide a concurrent mutation.
            fresh = _tree(target)
            fresh_changes = _git_state(root, target, fresh)
            if ({'members': fresh, 'git_changes': fresh_changes} != snapshot
                    or _git(root, 'rev-parse', 'HEAD').strip() != context['head']):
                item['differences'] = {'reason': 'CHANGED_DURING_INSPECTION'}
                raise ReviewStop('CHANGED')
            item['backup'] = 'VERIFIED' if backup_ok else 'REQUIRED' if needs_backup else 'GIT_CLEAN'
            if needs_backup and not backup_ok:
                raise ReviewStop('BACKUP_REQUIRED')
            item['status'] = 'READY_FOR_REVIEW'
        except (OSError, ValueError, StopIteration, ReviewStop) as exc:
            item['status'] = str(exc) if isinstance(exc, ReviewStop) else 'UNKNOWN'
    return result


def diagnose_rejection(error: str, mode: str | None = None) -> dict[str, str]:
    """Accept an already sanitized tool error, preserve it, never suggest a retry route."""
    layer = 'UNKNOWN_LAYER'
    if ('askforapproval is set to never' in error.lower()
            or ('approval required by policy' in error.lower() and 'never' in error.lower())):
        layer = 'APPROVAL_MODE'
    elif re.search(r'exec[-_ ]policy.*(?:forbidden|denied|rejected)|dangerous command.*(?:denied|rejected)', error, re.I):
        layer = 'EXEC_POLICY'
    elif re.search(r'winerror\s*(32|33)|sharing violation', error, re.I):
        layer = 'FILE_IN_USE'
    elif re.search(r'PermissionError|access denied|WinError\s*5\b|index\.lock.*permission denied', error, re.I):
        layer = 'FILESYSTEM_PERMISSION'
    elif re.search(r'connection refused|could not resolve host|failed to connect|network is unreachable', error, re.I):
        layer = 'NETWORK'
    else:
        try:
            payload = json.loads(error)
            if (isinstance(payload, dict) and payload.get('decision') == 'block'
                    and re.match(r'^(UNKNOWN|FORBIDDEN|OWNER_APPROVAL_REQUIRED):',
                                 str(payload.get('reason', '')))):
                layer = 'PROJECT_HOOK'
        except (ValueError, TypeError):
            pass  # a generic host error is not evidence of a particular guard
    return {'layer': layer, 'original_error': error, 'retry': 'STOP_AFFECTED_ACTION',
            'effective_mode': mode if mode in {'never', 'on-request'} else 'UNKNOWN'}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--target', action='append', type=Path)
    parser.add_argument('--baseline', type=Path, help='comparison JSON; never an approval receipt')
    parser.add_argument('--backup', nargs=2, action='append', default=[], metavar=('TARGET', 'BACKUP'))
    parser.add_argument('--diagnose-error', help='already sanitized original tool error; no retry')
    parser.add_argument('--effective-approval-policy', choices=('never', 'on-request', 'unknown'))
    args = parser.parse_args(argv)
    if args.diagnose_error is not None:
        if args.root or args.target or args.baseline or args.backup:
            parser.error('diagnosis cannot be combined with file inspection')
        print(json.dumps(diagnose_rejection(args.diagnose_error, args.effective_approval_policy),
                         ensure_ascii=False, indent=2))
        return 1  # diagnosis is not a successful execution or recovery
    if not args.root or not args.target:
        parser.error('--root and --target are required for inspection')
    if len({target for target, _ in args.backup}) != len(args.backup):
        parser.error('duplicate backup target')
    baseline = None
    try:
        if args.baseline:
            _absolute(args.baseline)
            if _secret(args.baseline):
                raise ReviewStop('SECRET_BOUNDARY')
            _chain(args.baseline)
            # Read the validated handle itself; do not reopen a path after validation.
            with _checked_reader(args.baseline, args.baseline.lstat()) as stream:
                data = stream.read(16 * 1024 * 1024 + 1)
            if len(data) > 16 * 1024 * 1024:
                raise ReviewStop('UNKNOWN')
            baseline = json.loads(data.decode('utf-8'))
        report = inspect_targets(args.root, args.target, baseline=baseline,
                                 backups={target: Path(backup) for target, backup in args.backup})
    except (OSError, ValueError, ReviewStop):
        print(json.dumps({'error': 'INVALID_BASELINE', 'execution': 'NOT_ATTEMPTED'}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(any(i['status'] not in {'READY_FOR_REVIEW', 'ALREADY_ABSENT'} for i in report['items']))


if __name__ == '__main__':
    raise SystemExit(main())
