"""Issue 555: command-specific project policy, never an authorization receipt."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from scripts.check_codex_approvals import diagnose
from scripts.sdd import codex_hook_guard as guard
from scripts.sdd.check_git_actions import review_actions

ROOT = Path(__file__).resolve().parents[2]
PR = ['gh', 'pr', 'create', '-R', 'synthetic/repo', '-H', 'maintain/example',
      '-B', 'develop', '-t', 'Title ; | & normal text', '-F', 'body with spaces.md', '-d']


def state(command):
    return guard.classify({'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
                           'tool_input': {'cmd': command}})[0]


@pytest.mark.parametrize('command', [
    'git commit -m "Title; normal | prose & punctuation" -m "Second paragraph"',
    'git commit --message="A title" --message="A body"',
    "git commit -m 'literal $(example) and `example`'",
    'git commit --file="C:\\public docs\\message.txt"',
    ['git', 'commit', '-m', 'title', '--message', 'body; psql is prose'],
    ['git', 'commit', '--file=message with spaces.txt'],
    'git push origin --set-upstream maintain/example',
    'git push origin maintain/example -u',
    'git push --set-upstream origin HEAD:refs/heads/maintain/example',
    'git push gitee refs/heads/maintain/source:refs/heads/maintain/target',
    'git push --delete origin maintain/one refs/heads/maintain/two',
    'git push gitee maintain/one maintain/two --delete',
    PR,
    'gh pr create --repo=synthetic/repo --head=maintain/example --base=develop '
    '--title="A title with ; punctuation" --body-file="body with spaces.md" --draft',
])
def test_common_publication_forms_provide_task_context(command):
    assert state(command) == 'TASK_AUTHORIZATION_CONTEXT'


@pytest.mark.parametrize('command', [
    'git commit -m title -F body.md', 'git commit --file=a --file=b',
    'git commit --message=', 'git commit --amend', 'git commit --message',
    'git commit -m "expand $env:HOME"', 'git commit -m "$(Get-Content x)"',
    'git commit -m title; git status', 'git commit -m title | git log',
    'git push origin +HEAD:maintain/example', 'git push origin :maintain/example',
    'git push origin HEAD:refs/tags/example', 'git push origin maintain/*',
    'git push origin --force-with-lease maintain/example', 'git push origin HEAD',
    'git push origin --delete -u maintain/example', 'git push origin --delete',
    'git push origin --delete maintain/one refs/heads/maintain/one',
    [*PR, '--title', 'conflict'], [*PR, '--body-file'], [*PR, '--unknown'],
    'gh pr create --base=develop',
])
def test_unknown_or_ambiguous_forms_still_stop(command):
    assert state(command) == 'UNKNOWN'


@pytest.mark.parametrize('command', [
    'git push origin --delete maintain/one develop',
    'git push gitee --delete refs/heads/main maintain/two',
    'git checkout -bnew', 'git switch --create=new', 'gh pr merge 1',
    ['gh', 'pr', 'create', '-R', 'synthetic/repo', '-H', 'hotfix/example', '-B', 'develop',
     '-t', 'title', '-F', 'body.md'],
    'git commit -F config/secrets.enc',
])
def test_guard_boundaries_survive_rule_removal(command):
    assert state(command) == 'FORBIDDEN'


@pytest.mark.parametrize('mode', ['never', 'on-request', None])
def test_diagnostics_are_per_command_and_filterable(mode):
    report = diagnose(ROOT, mode, actions={'commit', 'push', 'pr_create', 'remote_delete'})
    assert report['session_approval'] == 'PER_COMMAND'
    assert all(row['rule_decision'] == 'NO_MATCH' for row in report['commands'])
    assert all(row['status'] == 'NO_PROJECT_RULE_REQUIREMENT' for row in report['commands'])
    assert report['host_enforcement'] == 'NOT_TESTED'
    assert report['rule_loading'] == 'UNKNOWN'
    local = diagnose(ROOT, mode, actions={'local_delete'})['commands']
    assert len(local) == 3
    assert local[0]['status'] == {'never': 'INCOMPATIBLE', 'on-request': 'APPROVAL_REQUIRED',
                                 None: 'UNKNOWN'}[mode]
    assert all(row['status'] == 'NO_PROJECT_RULE_REQUIREMENT' for row in local[1:])


def item(command, kind='local_delete'):
    return {'id': 'one', 'kind': kind, 'command': command,
            'scope': {'root': 'synthetic-root', 'target': 'maintain/example',
                      'snapshot_sha256': 'a' * 64}}


@pytest.mark.parametrize('command,expected', [
    (['Remove-Item', '-LiteralPath', 'maintain/example'], 'BLOCKED_EXECUTION_ROUTE'),
    (['git', 'branch', '-d', 'maintain/example'], 'READY_FOR_REVIEW'),
    (['git', 'worktree', 'remove', 'maintain/example'], 'READY_FOR_REVIEW'),
])
def test_local_delete_uses_actual_command(command, expected):
    entries = [item(command)]
    result = review_actions(entries, entries, mode='never')
    assert result['items'][0]['status'] == expected
    assert result['owner_approval'] == 'NOT_ASSESSED'


def test_missing_command_and_known_block_cannot_be_cleared_by_mode_alone():
    entry = item(['git', 'branch', '-d', 'maintain/example'])
    missing = copy.deepcopy(entry)
    missing.pop('command')
    assert review_actions([missing], [missing], mode='never')['items'][0]['status'] == 'UNKNOWN_COMMAND'
    for mode in ('never', 'on-request', None):
        report = review_actions([entry], [entry], mode=mode, known_approval_block=True)
        assert report['items'][0]['status'] == 'BLOCKED_EXECUTION_ROUTE'


def test_wire_context_does_not_claim_host_approval(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', __import__('io').StringIO(json.dumps({
        'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
        'tool_input': {'cmd': PR}, 'owner_approved': True})))
    guard.main()
    result = json.loads(capsys.readouterr().out)
    assert set(result) == {'hookSpecificOutput'}
    context = result['hookSpecificOutput']['additionalContext']
    assert 'TASK_AUTHORIZATION_CONTEXT' in context
    assert 'HOST_APPROVAL_REQUIRED' not in context
    assert 'Normal host approval is still required' not in context


@pytest.mark.parametrize('source', ['PROJECT_PROMPT', 'HOST_POLICY', 'UNKNOWN'])
@pytest.mark.parametrize('loaded', [False, True])
def test_only_observed_loaded_rule_change_reassesses_project_refusal(source, loaded):
    entry = item(['git', 'branch', '-d', 'maintain/example'])
    digest = diagnose(ROOT, 'never')['rules_sha256']
    previous = {'one': {'source': source, 'mode': 'never', 'rules_sha256': '0' * 64,
                        'raw_error': 'synthetic prior policy refusal', 'command': entry['command']}}
    result = review_actions([entry], [entry], mode='never', known_approval_block=True,
                            prior_blocks=previous, loaded_rules_sha256=digest if loaded else None)
    assert result['items'][0]['status'] == (
        'READY_FOR_REVIEW' if source == 'PROJECT_PROMPT' and loaded else 'BLOCKED_EXECUTION_ROUTE')
    assert result['host_enforcement'] == 'NOT_TESTED'


def test_unchanged_conditions_do_not_clear_refusal():
    entry = item(['git', 'branch', '-d', 'maintain/example'])
    digest = diagnose(ROOT, 'never')['rules_sha256']
    old = {'source': 'PROJECT_PROMPT', 'mode': 'never', 'rules_sha256': digest,
           'raw_error': 'synthetic prior refusal', 'command': entry['command']}
    result = review_actions([entry], [entry], mode='never', known_approval_block=True,
                            prior_blocks={'one': old}, loaded_rules_sha256=digest)
    assert result['items'][0]['status'] == 'BLOCKED_EXECUTION_ROUTE'


def batch_items():
    command = ['git', 'push', 'origin', '--delete', 'maintain/one', 'maintain/two']
    return [{'id': name, 'kind': 'remote_delete', 'command': command,
             'scope': {'repo': 'synthetic/repo', 'remote': 'origin',
                       'ref': 'refs/heads/maintain/' + name, 'tip': 'a' * 40}}
            for name in ('one', 'two')]


def test_batch_missing_revoked_changed_or_reconciled_member_pauses_other_refs():
    entries = batch_items()
    assert all(row['status'] == 'READY_FOR_REVIEW'
               for row in review_actions(entries, entries, mode='never')['items'])
    assert review_actions(entries[:1], entries[:1], mode='never')['items'][0]['status'] == 'BATCH_PAUSED'
    result = review_actions(entries, entries, mode='never', revoked={'two'})
    assert [row['status'] for row in result['items']] == ['BATCH_PAUSED', 'REVOKED']
    changed = copy.deepcopy(entries)
    changed[1]['scope']['tip'] = 'b' * 40
    assert [row['status'] for row in review_actions(entries, changed, mode='never')['items']] == ['BATCH_PAUSED', 'CHANGED']
    result = review_actions(entries, entries, mode='never',
                            progress={'one': {'result': 'DELETED', 'reconciled': 'MATCH'}})
    assert [row['status'] for row in result['items']] == ['COMPLETE', 'BATCH_PAUSED']


def test_action_cli_filter_does_not_inherit_remove_item_conflict(capsys):
    from scripts.check_codex_approvals import main
    assert main(['--root', str(ROOT), '--effective-approval-policy', 'never', '--action', 'commit']) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(report['commands']) == 1
    assert report['commands'][0]['status'] == 'NO_PROJECT_RULE_REQUIREMENT'


def test_exact_remaining_project_rules():
    from scripts.sdd.check_codex_native import RULES
    assert RULES == {('Remove-Item',): 'prompt', ('psql',): 'forbidden',
                     ('pg_dump',): 'forbidden', ('pg_restore',): 'forbidden'}


@pytest.mark.parametrize('command', [
    'git commit -m "psql"', "git commit -m 'literal $value'",
    ['git', 'commit', '-m', 'literal | ; $() arguments'],
])
def test_message_content_is_not_an_executable(command):
    assert state(command) == 'TASK_AUTHORIZATION_CONTEXT'


@pytest.mark.parametrize('command', [
    'git commit -m title # hidden suffix',
    'git commit -m @parameters',
    "git commit -m 'it''s shell dependent'",
    'git push origin refs/heads/.hidden:maintain/example',
    'git push origin maintain/a.lock/child',
    'git push origin refs/tags/tag:maintain/example',
])
def test_unlisted_expansion_and_ref_shapes_remain_unknown(command):
    assert state(command) == 'UNKNOWN'


def test_exact_command_change_is_reported():
    old = item(['git', 'branch', '-d', 'maintain/example'])
    new = copy.deepcopy(old)
    new['command'] = ['Remove-Item', '-LiteralPath', 'maintain/example']
    result = review_actions([old], [new], mode='never')
    assert result['items'][0]['status'] == 'CHANGED'
    assert result['items'][0]['changed_fields'] == ['command']
