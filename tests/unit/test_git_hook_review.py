"""Bounded hook routing, no approval token or host execution claim."""
import io
import json

import pytest
from scripts.sdd import codex_hook_guard as guard


@pytest.mark.parametrize(('command', 'expected'), [
    ('git commit -F message.txt', 'HOST_APPROVAL_REQUIRED'),
    ('git push -u gitee maintain/example', 'HOST_APPROVAL_REQUIRED'),
    ('git push origin --delete maintain/example', 'HOST_APPROVAL_REQUIRED'),
    ('git push gitee --delete refs/heads/maintain/example', 'HOST_APPROVAL_REQUIRED'),
    ('git push origin --delete main', 'FORBIDDEN'),
    ('git push gitee --delete refs/heads/develop', 'FORBIDDEN'),
    ('git push origin --force maintain/example', 'UNKNOWN'),
    ('git push origin :maintain/example', 'UNKNOWN'),
    ('git push unknown maintain/example', 'UNKNOWN'),
    ('git commit --amend', 'UNKNOWN'),
    ('git commit -am test', 'UNKNOWN'),
    ('git commit -m test; git status', 'UNKNOWN'),
    (['git', 'push', 'origin', 'maintain/example;git'], 'UNKNOWN'),
    ('git commit -m $(Get-Content x)', 'UNKNOWN'),
    ('gh pr create --base main --head maintain/example', 'FORBIDDEN'),
    ('gh pr create --base develop --head hotfix/example', 'FORBIDDEN'),
    ('gh pr create --repo synthetic/repo --head hotfix/example --base main --title test --body-file body.md',
     'HOST_APPROVAL_REQUIRED'),
    ('gh pr create --base develop --base main', 'UNKNOWN'),
    ('gh pr create --base develop --unknown x', 'UNKNOWN'),
])
def test_bounded_publication_spellings(command, expected) -> None:
    payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
               'tool_input': {'cmd': command}, 'owner_approved': True}
    assert guard.classify(guard.project_payload(payload))[0] == expected


def test_hook_emits_context_only_and_keeps_other_blocks(monkeypatch, capsys) -> None:
    for command, blocked in [('git push origin maintain/example', False),
                              ('git push origin --force maintain/example', True)]:
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
                   'tool_input': {'cmd': command}}
        monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(payload)))
        assert guard.main() == 0
        output = json.loads(capsys.readouterr().out)
        if blocked:
            assert output['decision'] == 'block'
        else:
            assert set(output) == {'hookSpecificOutput'}
            assert set(output['hookSpecificOutput']) == {'hookEventName', 'additionalContext'}
            assert 'does not authenticate Owner authorization' in output['hookSpecificOutput']['additionalContext']


@pytest.mark.parametrize('remote', ['gitee', 'origin'])
@pytest.mark.parametrize('qualified', [False, True])
@pytest.mark.parametrize('as_argv', [False, True])
@pytest.mark.parametrize('batch', [False, True])
def test_remote_deletion_single_ref_context_and_batch_unknown(
    remote, qualified, as_argv, batch, monkeypatch, capsys,
) -> None:
    """Exercise the hook protocol without invoking Git or a real host approval."""
    prefix = 'refs/heads/' if qualified else ''
    branches = [prefix + 'maintain/example']
    if batch:
        branches.append(prefix + 'documentation/example')
    argv = ['git', 'push', remote, '--delete', *branches]
    payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'exec_command',
               'tool_input': {'cmd': argv if as_argv else ' '.join(argv)},
               'owner_approved': True}
    expected = 'UNKNOWN' if batch else 'HOST_APPROVAL_REQUIRED'
    assert guard.classify(guard.project_payload(payload))[0] == expected
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(payload)))
    assert guard.main() == 0
    output = json.loads(capsys.readouterr().out)
    if batch:
        assert set(output) == {'decision', 'reason'}
        assert output['decision'] == 'block'
        assert output['reason'].startswith('UNKNOWN:')
    else:
        assert set(output) == {'hookSpecificOutput'}
        assert set(output['hookSpecificOutput']) == {'hookEventName', 'additionalContext'}
        assert output['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
        assert output['hookSpecificOutput']['additionalContext'].startswith('HOST_APPROVAL_REQUIRED:')
