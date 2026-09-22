"""Read-only per-command project diagnosis; neither approval nor host execution proof."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

if __package__:
    from scripts.sdd.check_codex_native import (
        ENFORCEMENT,
        RULES,
        approval_status,
        check_enforcement,
    )
    from scripts.sdd.codex_hook_guard import classify
    from scripts.sdd.git_command_review import tokenize
else:
    from sdd.check_codex_native import (  # type: ignore[no-redef]
        ENFORCEMENT,
        RULES,
        approval_status,
        check_enforcement,
    )
    from sdd.codex_hook_guard import classify  # type: ignore[no-redef]
    from sdd.git_command_review import tokenize  # type: ignore[no-redef]

COMMANDS = (
    ('local_delete', ('Remove-Item', '-LiteralPath', 'temporary-item')),
    ('local_delete', ('git', 'branch', '-d', 'maintain/example')),
    ('local_delete', ('git', 'worktree', 'remove', 'temporary-worktree')),
    ('commit', ('git', 'commit')),
    ('push', ('git', 'push', '-u', 'gitee', 'maintain/example')),
    ('push', ('git', 'push', '-u', 'origin', 'maintain/example')),
    ('pr_create', ('gh', 'pr', 'create', '--repo', 'synthetic/repo', '--head', 'maintain/example',
                   '--base', 'develop', '--title', 'Example', '--body-file', 'body.md')),
    ('remote_delete', ('git', 'push', 'gitee', '--delete', 'maintain/example')),
    ('remote_delete', ('git', 'push', 'origin', '--delete', 'maintain/example')),
)
ACTIONS = {kind for kind, _ in COMMANDS}


def diagnose(root: Path, mode: str | None = None, *, actions: set[str] | None = None,
             commands: list[Any] | None = None) -> dict[str, Any]:
    """Observe project files only; missing rules never become NO_MATCH.

    Hook results use this checker's recognizer, not proof that the target host
    loaded or ran that implementation. No arbitrary root code is executed.
    """
    paths = [*root.parents, root]
    for relative in ENFORCEMENT:
        path = root
        for part in Path(relative).parts:
            path = path / part
            paths.append(path)
    digest = None
    try:
        if any(path.is_symlink() or path.is_junction() for path in paths):
            errors = ['indirect enforcement path; no files read']
        else:
            errors = check_enforcement(root)
            if not errors:
                digest = hashlib.sha256((root / '.codex/rules/mj-agent.rules').read_bytes()).hexdigest()
    except OSError:
        errors = ['unreadable enforcement path']
    effective_mode = mode if mode in ('never', 'on-request') else 'unknown'
    selected = [(kind, list(command)) for kind, command in COMMANDS
                if actions is None or kind in actions]
    if commands is not None:
        selected = [('explicit', command) for command in commands]
    rows = []
    for kind, command in selected:
        try:
            argv = tokenize(command)
        except ValueError:
            argv = []
        matches = [decision for prefix, decision in RULES.items()
                   if tuple(argv[:len(prefix)]) == prefix]
        decision = 'UNKNOWN' if errors or not argv else (matches[0] if matches else 'NO_MATCH')
        hook, reason = classify({'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
                                 'tool_input': {'cmd': command}}) if not errors else ('UNKNOWN', 'invalid enforcement files')
        rows.append({'action': kind, 'command': command,
                     'rule_source': '.codex/rules/mj-agent.rules', 'rule_decision': decision,
                     'status': approval_status(effective_mode, decision),
                     'hook_result': hook, 'hook_reason': reason,
                     'hook_source': 'RUNNING_CHECKER_STATIC_ANALYSIS'})
    return {
        'rule_scope': 'PROJECT_FILES_ONLY', 'rules_sha256': digest, 'rule_loading': 'UNKNOWN',
        'effective_approval_policy': effective_mode,
        'mode_source': 'CALLER_OBSERVATION' if effective_mode != 'unknown' else 'UNKNOWN',
        'session_approval': 'PER_COMMAND', 'errors': errors, 'commands': rows,
        'owner_approval': 'NOT_ASSESSED', 'host_enforcement': 'NOT_TESTED',
        'remote_authentication': 'NOT_TESTED',
        'execution_boundary': 'Verify exact task authorization, effective mode and loaded rules/hook. '
                              'NO_MATCH is not host permission. Preserve actual refusals; '
                              'reconcile partial/unknown results before any recovery.',
    }


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=repo_root or Path(__file__).resolve().parents[1])
    parser.add_argument('--effective-approval-policy', choices=('never', 'on-request', 'unknown'),
                        help='Observed target-session mode, never inferred from project config.')
    parser.add_argument('--action', choices=sorted(ACTIONS), action='append',
                        help='Repeat to select actions; omitted means all example commands.')
    parser.add_argument('--command-json', help='One literal argv array for command-specific diagnosis.')
    args = parser.parse_args(argv)
    commands = None
    if args.command_json:
        if args.action:
            parser.error('--action and --command-json are mutually exclusive')
        try:
            command = json.loads(args.command_json)
            if not isinstance(command, list):
                raise ValueError
            tokenize(command)
        except (ValueError, TypeError):
            parser.error('--command-json requires a nonempty string argv array')
        commands = [command]
    report = diagnose(args.root, args.effective_approval_policy,
                      actions=set(args.action) if args.action else None, commands=commands)
    print(json.dumps(report))
    if report['errors'] or any(row['status'] == 'UNKNOWN' for row in report['commands']):
        return 2
    if any(row['status'] in {'INCOMPATIBLE', 'FORBIDDEN'}
           or row['hook_result'] not in {'ALLOW', 'TASK_AUTHORIZATION_CONTEXT'}
           for row in report['commands']):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
