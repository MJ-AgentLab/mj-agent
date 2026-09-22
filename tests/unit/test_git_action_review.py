"""Synthetic observations and local bare remotes; no real approval or publication."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from scripts.sdd.check_git_actions import inspect_remote_deletion
from scripts.sdd.check_git_actions import review_actions as _review_actions


def review_actions(baseline, current, **kwargs):
    """Supply explicit synthetic commands for the legacy scope fixtures."""
    def with_command(item):
        scope = item['scope']
        kind = item['kind']
        if kind == 'local_delete':
            command = ['Remove-Item', '-LiteralPath', scope.get('target', '')]
        elif kind == 'commit':
            command = ['git', 'commit']
        elif kind == 'push':
            command = ['git', 'push', scope.get('remote', ''), scope.get('branch', '')]
        elif kind == 'remote_delete':
            command = ['git', 'push', scope.get('remote', ''), '--delete', scope.get('ref', '')]
        elif kind == 'pr_create':
            command = ['gh', 'pr', 'create', '--repo', scope.get('repo', ''),
                       '--head', scope.get('head', ''), '--base', scope.get('base', ''),
                       '--title', scope.get('title', ''), '--body-file', 'synthetic-body.md']
        else:
            command = []
        return dict(item, command=command)
    return _review_actions([with_command(i) for i in baseline],
                           [with_command(i) for i in current], **kwargs)


def git(root: Path, *args: str) -> str:
    env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT')
           if k in os.environ}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', GIT_AUTHOR_NAME='Synthetic',
               GIT_AUTHOR_EMAIL='synthetic@example.invalid', GIT_COMMITTER_NAME='Synthetic',
               GIT_COMMITTER_EMAIL='synthetic@example.invalid')
    return subprocess.run(['git', '-c', 'core.hooksPath=', '-C', str(root), *args],
                          env=env, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / 'review repo'
    root.mkdir()
    git(root, 'init', '-b', 'develop')
    (root / 'public.txt').write_text('synthetic')
    git(root, 'add', 'public.txt')
    git(root, 'commit', '-m', 'synthetic baseline')
    tip = git(root, 'rev-parse', 'HEAD')
    for remote in ('gitee', 'origin'):
        bare = tmp_path / remote
        bare.mkdir()
        git(bare, 'init', '--bare')
        git(root, 'remote', 'add', remote, str(bare))
        git(root, 'push', remote, 'HEAD:refs/heads/maintain/example')
    return root, tip


def inspect(repo, **kwargs):
    root, tip = repo
    return inspect_remote_deletion(root, 'refs/heads/maintain/example',
                                   {'gitee': tip, 'origin': tip}, **kwargs)


def states(report):
    return {item['remote']: item['status'] for item in report['items']}


def test_remote_review_does_not_need_deleted_local_branch(repo) -> None:
    root, _ = repo
    assert git(root, 'branch', '--list', 'maintain/example') == ''
    result = inspect(repo)
    assert states(result) == {'gitee': 'READY_FOR_REVIEW', 'origin': 'READY_FOR_REVIEW'}
    assert result['owner_approval'] == 'NOT_ASSESSED'
    assert result['execution'] == 'NOT_ATTEMPTED'
    assert git(root, 'ls-remote', '--heads', 'origin', 'refs/heads/maintain/example')


@pytest.mark.parametrize('ref', ['refs/heads/main', 'refs/heads/develop', 'refs/heads/release'])
def test_protected_refs(repo, ref) -> None:
    root, tip = repo
    result = inspect_remote_deletion(root, ref, {'gitee': tip},
                                    protected_refs={'refs/heads/release'})
    assert states(result) == {'gitee': 'PROTECTED'}


def test_changed_tip_and_cross_remote_disagreement(repo) -> None:
    root, old = repo
    (root / 'public.txt').write_text('new synthetic commit')
    git(root, 'commit', '-am', 'new')
    new = git(root, 'rev-parse', 'HEAD')
    git(root, 'push', 'origin', 'HEAD:refs/heads/maintain/example')
    assert states(inspect(repo)) == {'gitee': 'REMOTE_TIPS_DIFFER', 'origin': 'CHANGED'}
    result = inspect_remote_deletion(root, 'refs/heads/maintain/example',
                                    {'gitee': old, 'origin': new})
    assert states(result) == {'gitee': 'REMOTE_TIPS_DIFFER', 'origin': 'REMOTE_TIPS_DIFFER'}


def test_query_failure_is_not_absence_and_does_not_hide_other_end(repo) -> None:
    root, _ = repo
    git(root, 'remote', 'set-url', 'gitee', str(root / 'nonexistent-bare'))
    result = inspect(repo)
    assert states(result) == {'gitee': 'UNKNOWN', 'origin': 'READY_FOR_REVIEW'}
    assert result['items'][0]['query'] == 'FAILED'


def test_already_absent_and_unmerged(repo) -> None:
    root, _ = repo
    git(root.parent / 'gitee', 'update-ref', '-d', 'refs/heads/maintain/example')
    assert states(inspect(repo)) == {'gitee': 'ALREADY_ABSENT', 'origin': 'READY_FOR_REVIEW'}
    (root / 'public.txt').write_text('not yet merged')
    git(root, 'commit', '-am', 'unmerged')
    new = git(root, 'rev-parse', 'HEAD')
    git(root, 'push', 'origin', 'HEAD:refs/heads/maintain/example')
    result = inspect_remote_deletion(root, 'refs/heads/maintain/example', {'origin': new},
                                    base_ref='HEAD~1')
    assert states(result) == {'origin': 'NOT_MERGED'}


@pytest.mark.parametrize('method', ['squash', 'rebase'])
def test_rewritten_merge_needs_exact_pr_head_and_reachable_merge_commit(repo, method) -> None:
    root, old = repo
    # A distinct commit with the same parent is not an ancestor of develop.
    tree = git(root, 'rev-parse', 'HEAD^{tree}')
    rewritten_head = git(root, 'commit-tree', tree, '-m', 'synthetic PR head')
    git(root, 'push', 'origin', rewritten_head + ':refs/heads/maintain/rewritten')
    kwargs = dict(root=root, ref='refs/heads/maintain/rewritten', expected_tips={'origin': rewritten_head})
    assert states(inspect_remote_deletion(**kwargs)) == {'origin': 'NOT_MERGED'}
    proof = {'method': method, 'state': 'MERGED', 'head': rewritten_head, 'merge_commit': old}
    assert states(inspect_remote_deletion(**kwargs, merge_evidence=proof)) == {'origin': 'READY_FOR_REVIEW'}
    proof['head'] = old
    assert states(inspect_remote_deletion(**kwargs, merge_evidence=proof)) == {'origin': 'MERGE_EVIDENCE_MISMATCH'}
    proof.update(head=rewritten_head, merge_commit=rewritten_head)
    assert states(inspect_remote_deletion(**kwargs, merge_evidence=proof)) == {'origin': 'NOT_MERGED'}


@pytest.mark.parametrize('ref', ['main', 'refs/tags/v1', 'refs/heads/*', 'refs/heads/../other'])
def test_invalid_ref_is_out_of_scope(repo, ref) -> None:
    root, tip = repo
    assert states(inspect_remote_deletion(root, ref, {'origin': tip})) == {'origin': 'OUT_OF_SCOPE'}


def action(kind='push', remote='gitee'):
    scope = {'repo': 'synthetic/repo', 'branch': 'maintain/example', 'remote': remote,
             'tip': 'a' * 40, 'from_tip': 'b' * 40}
    return {'id': remote, 'kind': kind, 'scope': scope}


def reviewed(items, **kwargs):
    return review_actions(items, items, mode='on-request', **kwargs)


def test_action_scope_never_implies_other_actions_or_trusted_approval() -> None:
    before = [action()]
    remote_delete = {'id': 'delete', 'kind': 'remote_delete', 'scope': {
        'repo': 'synthetic/repo', 'remote': 'gitee', 'ref': 'refs/heads/maintain/example', 'tip': 'a' * 40}}
    result = review_actions(before, [*before, remote_delete], mode='on-request')
    assert states_by_id(result) == {'gitee': 'READY_FOR_REVIEW', 'delete': 'NOT_IN_SCOPE'}
    assert result['owner_approval'] == 'NOT_ASSESSED'
    assert states_by_id(reviewed([*before, remote_delete]))['delete'] == 'READY_FOR_REVIEW'


def states_by_id(result):
    return {item['id']: item['status'] for item in result['items']}


def test_revocation_and_changes_only_pause_affected_actions() -> None:
    before = [action(), action(remote='origin')]
    after = [action(), action(remote='origin')]
    after[0]['scope']['tip'] = 'c' * 40
    result = review_actions(before, after, mode='on-request')
    assert states_by_id(result) == {'gitee': 'CHANGED', 'origin': 'READY_FOR_REVIEW'}
    assert result['items'][0]['changed_fields'] == ['tip']
    assert states_by_id(reviewed(before, revoked={'gitee'})) == {
        'gitee': 'REVOKED', 'origin': 'READY_FOR_REVIEW'}


@pytest.mark.parametrize('mode', ['never', None, 'on-request'])
def test_known_block_is_not_cleared_by_mode_alone(mode) -> None:
    result = review_actions([action()], [action()], mode=mode, known_approval_block=True)
    assert result['items'][0]['status'] == 'BLOCKED_EXECUTION_ROUTE'


@pytest.mark.parametrize('kind,scope', [
    ('local_delete', {'root': 'synthetic-root', 'target': 'synthetic-target',
                      'snapshot_sha256': 'a' * 64}),
    ('commit', {'repo': 'synthetic/repo', 'branch': 'maintain/example', 'head': 'a' * 40,
                'files': ['public.txt'], 'staged_diff_sha256': 'b' * 64}),
    ('push', {'repo': 'synthetic/repo', 'branch': 'maintain/example', 'remote': 'gitee',
              'tip': 'a' * 40, 'from_tip': 'b' * 40}),
    ('pr_create', {'repo': 'synthetic/repo', 'head': 'maintain/example', 'head_sha': 'a' * 40,
                   'base': 'develop', 'title': 'Synthetic PR', 'body_sha256': 'b' * 64}),
    ('remote_delete', {'repo': 'synthetic/repo', 'remote': 'gitee',
                       'ref': 'refs/heads/maintain/example', 'tip': 'a' * 40}),
])
def test_never_is_evaluated_per_actual_command_before_first_attempt(kind, scope) -> None:
    items = [{'id': 'first-attempt', 'kind': kind, 'scope': scope}]
    # Matching comparison inputs are not trusted authorization. Repeated review
    # cannot authenticate Owner approval or prove host execution.
    for _ in range(2):
        report = review_actions(items, items, mode='never')
        assert report['known_approval_block'] is False
        assert report['items'][0]['status'] == ('BLOCKED_EXECUTION_ROUTE' if kind == 'local_delete' else 'READY_FOR_REVIEW')
        assert report['items'][0]['last_result'] == 'NOT_EXECUTED'
        assert report['execution'] == 'NOT_ATTEMPTED'
        assert report['owner_approval'] == 'NOT_ASSESSED'
        assert report['host_enforcement'] == 'NOT_TESTED'


def test_recovery_preserves_partial_success_and_requires_reconciliation() -> None:
    items = [action(), action(remote='origin')]
    evidence = {'gitee': {'result': 'SUCCESS', 'reconciled': 'MATCH'},
                'origin': {'result': 'FAILED', 'reconciled': 'ABSENT'}}
    result = reviewed(items, progress=evidence)
    assert states_by_id(result) == {'gitee': 'COMPLETE', 'origin': 'READY_FOR_REVIEW'}
    evidence['gitee']['reconciled'] = 'UNKNOWN'
    assert states_by_id(reviewed(items, progress=evidence))['gitee'] == 'RECONCILE_FIRST'


@pytest.mark.parametrize('kind,scope', [
    ('commit', {'repo': 'synthetic/repo', 'branch': 'maintain/example', 'head': 'a' * 40,
                'files': ['public.txt'], 'staged_diff_sha256': 'b' * 64}),
    ('pr_create', {'repo': 'synthetic/repo', 'head': 'maintain/example', 'head_sha': 'a' * 40,
                   'base': 'develop', 'title': 'Synthetic PR', 'body_sha256': 'b' * 64}),
])
def test_lost_commit_or_pr_response_is_reconciled_before_retry(kind, scope) -> None:
    items = [{'id': kind, 'kind': kind, 'scope': scope}]
    progress = {kind: {'result': 'UNKNOWN', 'reconciled': 'UNKNOWN'}}
    assert reviewed(items, progress=progress)['items'][0]['status'] == 'RECONCILE_FIRST'
    progress[kind]['reconciled'] = 'MATCH'
    assert reviewed(items, progress=progress)['items'][0]['status'] == 'COMPLETE'


def test_known_never_block_cannot_probe_other_remote_or_be_cleared_by_network() -> None:
    items = [action(), action(remote='origin')]
    result = review_actions(items, items, mode='never', known_approval_block=True,
        progress={'gitee': {'result': 'REJECTED', 'reconciled': 'ABSENT'}})
    assert states_by_id(result) == {'gitee': 'BLOCKED_EXECUTION_ROUTE', 'origin': 'BLOCKED_EXECUTION_ROUTE'}
    assert [row['last_result'] for row in result['items']] == ['REJECTED', 'NOT_EXECUTED']


def test_plan_completed_and_uncommitted_do_not_complete_remote_cleanup() -> None:
    items = [{'id': remote, 'kind': 'remote_delete', 'scope': {
        'repo': 'synthetic/repo', 'remote': remote, 'ref': 'refs/heads/maintain/example', 'tip': 'a' * 40}}
        for remote in ('gitee', 'origin')]
    report = review_actions(items, items, mode='never', known_approval_block=True,
        progress={'gitee': {'result': 'REJECTED', 'reconciled': 'ABSENT'}},
        delivery={'base_sha': '7446e73', 'local_cleanup': 'COMPLETE', 'plan_state': 'completed',
                  'plan_commit': 'UNCOMMITTED', 'issue_552': 'OUT_OF_SCOPE'})
    assert report['delivery']['plan_commit'] == 'UNCOMMITTED'
    assert report['delivery']['issue_552'] == 'OUT_OF_SCOPE'
    assert states_by_id(report)['origin'] == 'BLOCKED_EXECUTION_ROUTE'


def test_delete_response_lost_reconciles_and_skips_successful_end() -> None:
    items = [{'id': remote, 'kind': 'remote_delete', 'scope': {
        'repo': 'synthetic/repo', 'remote': remote, 'ref': 'refs/heads/maintain/example', 'tip': 'a' * 40}}
        for remote in ('gitee', 'origin')]
    progress = {'gitee': {'result': 'UNKNOWN', 'reconciled': 'UNKNOWN'},
                'origin': {'result': 'NOT_EXECUTED'}}
    assert states_by_id(reviewed(items, progress=progress))['gitee'] == 'RECONCILE_FIRST'
    # MATCH for deletion requires an actual successful query proving absence.
    progress['gitee']['reconciled'] = 'MATCH'
    progress['origin'] = {'result': 'FAILED', 'reconciled': 'ABSENT'}
    assert states_by_id(reviewed(items, progress=progress)) == {
        'gitee': 'COMPLETE', 'origin': 'READY_FOR_REVIEW'}
    progress['gitee']['result'] = 'DELETED'
    assert states_by_id(reviewed(items, progress=progress))['gitee'] == 'COMPLETE'


def test_scope_matrix_does_not_promote_local_cleanup_to_publication() -> None:
    local = {'id': 'local', 'kind': 'local_delete', 'scope': {
        'root': 'synthetic-root', 'target': 'synthetic-target', 'snapshot_sha256': 'a' * 64}}
    commit = {'id': 'commit', 'kind': 'commit', 'scope': {
        'repo': 'synthetic/repo', 'branch': 'maintain/example', 'head': 'a' * 40,
        'files': ['public.txt'], 'staged_diff_sha256': 'b' * 64}}
    pr = {'id': 'pr', 'kind': 'pr_create', 'scope': {
        'repo': 'synthetic/repo', 'head': 'maintain/example', 'head_sha': 'a' * 40,
        'base': 'develop', 'title': 'Synthetic PR', 'body_sha256': 'b' * 64}}
    current = [local, commit, action(), pr]
    assert states_by_id(review_actions([local], current, mode='on-request')) == {
        'local': 'READY_FOR_REVIEW', 'commit': 'NOT_IN_SCOPE', 'gitee': 'NOT_IN_SCOPE', 'pr': 'NOT_IN_SCOPE'}
    assert set(states_by_id(reviewed(current)).values()) == {'READY_FOR_REVIEW'}


def test_remote_cli_emits_review_only(repo, capsys) -> None:
    from scripts.sdd.check_git_actions import main
    root, tip = repo
    assert main(['--root', str(root), '--ref', 'refs/heads/maintain/example',
                 '--expected-tip', 'origin', tip]) == 0
    assert 'NOT_ATTEMPTED' in capsys.readouterr().out
    assert git(root, 'ls-remote', '--heads', 'origin', 'refs/heads/maintain/example')


def test_missing_scope_and_merge_are_never_ready() -> None:
    for item in ({'id': 'bad', 'kind': 'commit', 'scope': {}},
                 {'id': 'bad', 'kind': 'merge', 'scope': {}}):
        assert reviewed([item])['items'][0]['status'] == 'INVALID_SCOPE'


def test_explicit_push_resolves_source_and_destination_without_writing(repo):
    from scripts.sdd.check_git_actions import inspect_push
    root, tip = repo
    args = dict(root=root, remote='origin', source='HEAD', target='refs/heads/maintain/example',
                expected_source_tip=tip, expected_target_tip=tip)
    report = inspect_push(**args)
    assert report['status'] == 'READY_FOR_REVIEW'
    assert report['source_tip'] == report['target_tip'] == tip
    assert report['execution'] == 'NOT_ATTEMPTED'
    assert inspect_push(**dict(args, expected_source_tip='f' * 40))['status'] == 'SOURCE_CHANGED'
    assert inspect_push(**dict(args, expected_target_tip=None))['status'] == 'TARGET_CHANGED'
    assert inspect_push(**dict(args, source='+HEAD'))['status'] == 'INVALID_SCOPE'
    assert inspect_push(**dict(args, target='refs/tags/example'))['status'] == 'INVALID_SCOPE'
    assert git(root, 'ls-remote', '--heads', 'origin', 'refs/heads/maintain/example').startswith(tip)


def test_multi_ref_remote_review_pauses_whole_batch_on_protected_or_changed_target(repo):
    from scripts.sdd.check_git_actions import inspect_remote_batch
    root, tip = repo
    targets = [{'ref': 'refs/heads/maintain/example', 'expected_tips': {'gitee': tip, 'origin': tip}},
               {'ref': 'refs/heads/maintain/absent', 'expected_tips': {'gitee': tip, 'origin': tip}}]
    report = inspect_remote_batch(root, targets)
    assert report['status'] == 'READY_FOR_REVIEW'
    assert [row['status'] for row in report['items']] == [
        'READY_FOR_REVIEW', 'READY_FOR_REVIEW', 'ALREADY_ABSENT', 'ALREADY_ABSENT']
    targets[1]['ref'] = 'refs/heads/develop'
    assert inspect_remote_batch(root, targets)['status'] == 'BATCH_PAUSED'
    targets[1]['ref'] = 'refs/heads/maintain/other'
    targets[0]['expected_tips']['origin'] = 'f' * 40
    assert inspect_remote_batch(root, targets)['status'] == 'BATCH_PAUSED'


def test_push_non_fast_forward_and_failed_query_remain_distinct(repo):
    from scripts.sdd.check_git_actions import inspect_push
    root, old = repo
    (root / 'public.txt').write_text('new remote content')
    git(root, 'commit', '-am', 'synthetic remote advancement')
    new = git(root, 'rev-parse', 'HEAD')
    git(root, 'push', 'origin', 'HEAD:refs/heads/maintain/example')
    git(root, 'branch', 'maintain/source', old)
    args = dict(root=root, remote='origin', source='maintain/source', target='refs/heads/maintain/example',
                expected_source_tip=old, expected_target_tip=new)
    assert inspect_push(**args)['status'] == 'NOT_FAST_FORWARD'
    git(root, 'remote', 'set-url', 'origin', str(root / 'missing-bare'))
    assert inspect_push(**args)['status'] == 'UNKNOWN'
