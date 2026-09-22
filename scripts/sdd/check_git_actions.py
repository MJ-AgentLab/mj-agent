"""Read-only Git action review; comparison data is never an approval receipt.

Remote inspection queries refs without fetching or deleting. Recovery reviews
caller observations only, never authenticates approvals or executes/retries work.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

if __package__:
    from .check_deletion_targets import ReviewStop, _absolute, _chain, _git
    from .git_command_review import CONTEXT, publication, tokenize
    from .git_command_review import ref as branch_ref
else:
    from check_deletion_targets import ReviewStop, _absolute, _chain, _git  # type: ignore[no-redef]
    from git_command_review import CONTEXT, publication, tokenize  # type: ignore[no-redef]
    from git_command_review import ref as branch_ref  # type: ignore[no-redef]

REQUIRED = {
    'local_delete': {'root', 'target', 'snapshot_sha256'},
    'remote_delete': {'repo', 'remote', 'ref', 'tip'},
    'commit': {'repo', 'branch', 'head', 'files', 'staged_diff_sha256'},
    'push': {'repo', 'branch', 'remote', 'from_tip', 'tip'},
    'pr_create': {'repo', 'head', 'head_sha', 'base', 'title', 'body_sha256'},
}
RESULTS = {'SUCCESS', 'DELETED', 'ALREADY_ABSENT', 'REJECTED', 'FAILED', 'NOT_EXECUTED', 'UNKNOWN'}


def _report() -> dict[str, Any]:
    return {'schema': 1, 'owner_approval': 'NOT_ASSESSED', 'execution': 'NOT_ATTEMPTED',
            'host_enforcement': 'NOT_TESTED', 'items': []}


def _sha(value: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value))


def _ref(value: str) -> bool:
    return (bool(re.fullmatch(r'refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*', value))
            and not any(part.startswith('.') or part.endswith(('.', '.lock'))
                        for part in value.split('/'))
            and '..' not in value and '//' not in value and not value.endswith('/'))


def _ancestor(root: Path, tip: str, base: str) -> bool:
    # rev-list succeeds for divergent commits too, keeping query errors distinct.
    return not _git(root, 'rev-list', '--max-count=1', tip, '--not', base, '--').strip()


def _merged(root: Path, tip: str, base: str, proof: dict[str, str] | None) -> str:
    if proof is None:
        return 'READY_FOR_REVIEW' if _ancestor(root, tip, base) else 'NOT_MERGED'
    if (proof.get('method') not in {'merge', 'squash', 'rebase'}
            or proof.get('state') != 'MERGED' or proof.get('head') != tip
            or not _sha(proof.get('merge_commit', ''))):
        return 'MERGE_EVIDENCE_MISMATCH'
    if not _ancestor(root, proof['merge_commit'], base):
        return 'NOT_MERGED'
    if proof['method'] == 'merge' and not _ancestor(root, tip, base):
        return 'NOT_MERGED'
    # Squash/rebase PR facts are caller observations, not inferred from ancestry.
    return 'READY_FOR_REVIEW'


def inspect_remote_deletion(
    root: Path, ref: str, expected_tips: dict[str, str], *,
    base_ref: str = 'refs/heads/develop', protected_refs: set[str] | None = None,
    merge_evidence: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compare exact refs/tips with a reviewed inventory; never delete or fetch.

    Use a legal existing worktree even if the cleanup target worktree is absent.
    Missing local commit objects and failed queries stay UNKNOWN. PR evidence and
    additional protected refs must be independently observed by the caller.
    """
    report = _report()
    report.update(root=str(root), ref=ref, base_ref=base_ref,
                  merge_evidence_source='CALLER_OBSERVATION' if merge_evidence else 'LOCAL_ANCESTRY',
                  server_protection='NOT_TESTED', remote_identity='NOT_ASSESSED')
    protected = {'refs/heads/main', 'refs/heads/develop'} | (protected_refs or set())
    context_error = None
    try:
        _absolute(root)
        _chain(root)
        if Path(_git(root, 'rev-parse', '--show-toplevel').strip()) != root:
            raise ReviewStop('OUT_OF_SCOPE')
        base = _git(root, 'rev-parse', '--verify', '--end-of-options', base_ref + '^{commit}').strip()
        if not _sha(base):
            raise ReviewStop('UNKNOWN')
        report['base_sha'] = base
    except (OSError, ValueError, ReviewStop) as exc:
        context_error = str(exc) if isinstance(exc, ReviewStop) else 'UNKNOWN'
        base = ''
    for remote in sorted(expected_tips, key=lambda key: ({'gitee': 0, 'origin': 1}.get(key, 2), key)):
        tip = expected_tips[remote]
        row = {'remote': remote, 'ref': ref, 'expected_tip': tip,
               'query': 'NOT_EXECUTED', 'status': 'UNKNOWN'}
        report['items'].append(row)
        if remote not in {'gitee', 'origin'} or not _ref(ref) or not _sha(tip):
            row['status'] = 'OUT_OF_SCOPE'
            continue
        if ref in protected:
            row['status'] = 'PROTECTED'
            continue
        if context_error:
            row['status'] = context_error
            continue
        try:
            output = _git(root, 'ls-remote', '--refs', '--heads', remote, ref)
            records = [line.split('\t') for line in output.splitlines() if line]
            if records and (len(records) != 1 or len(records[0]) != 2
                            or records[0][1] != ref or not _sha(records[0][0])):
                raise ReviewStop('UNKNOWN')
            row['query'] = 'SUCCESS'
            if not records:
                row['status'] = 'ALREADY_ABSENT'
                continue
            row['observed_tip'] = records[0][0]
            if row['observed_tip'] != tip:
                row['status'] = 'CHANGED'
                continue
            row['status'] = _merged(root, tip, base, merge_evidence)
        except (OSError, ValueError, ReviewStop):
            row['status'] = 'UNKNOWN'
            if row['query'] != 'SUCCESS':
                row['query'] = 'FAILED'
    observed = {row['observed_tip'] for row in report['items'] if 'observed_tip' in row}
    if len(observed) > 1:
        for row in report['items']:
            if row['status'] == 'READY_FOR_REVIEW':
                row['status'] = 'REMOTE_TIPS_DIFFER'
    return report


def _valid_scope(item: dict[str, Any]) -> bool:
    kind, scope = item.get('kind'), item.get('scope')
    if (not isinstance(kind, str) or kind not in REQUIRED or not isinstance(scope, dict)
            or not REQUIRED[kind].issubset(scope)
            or not all(scope[key] for key in REQUIRED[kind])):
        return False
    if kind == 'pr_create':
        return bool(scope['base'] == ('main' if str(scope['head']).startswith('hotfix/') else 'develop'))
    if kind == 'remote_delete':
        return (isinstance(scope['ref'], str) and _ref(scope['ref'])
                and scope['ref'] not in {'refs/heads/main', 'refs/heads/develop'}
                and scope['remote'] in {'gitee', 'origin'})
    return True


def inspect_remote_batch(root: Path, targets: list[dict[str, Any]], *,
                         base_ref: str = 'refs/heads/develop',
                         protected_refs: set[str] | None = None) -> dict[str, Any]:
    """Read every ref; one invalid/changed target pauses its complete batch."""
    report = _report()
    refs = [target.get('ref') for target in targets]
    if not refs or not all(isinstance(value, str) for value in refs) or len(set(refs)) != len(refs):
        report['status'] = 'INVALID_BATCH'
        return report
    for target in targets:
        evidence = inspect_remote_deletion(root, target['ref'], target.get('expected_tips', {}),
            base_ref=base_ref, protected_refs=protected_refs, merge_evidence=target.get('merge_evidence'))
        report['items'].extend(evidence['items'])
        if not evidence['items']:
            report['items'].append({'ref': target['ref'], 'status': 'INVALID_SCOPE'})
    report['status'] = ('READY_FOR_REVIEW' if all(row['status'] in {'READY_FOR_REVIEW', 'ALREADY_ABSENT'}
                        for row in report['items']) else 'BATCH_PAUSED')
    return report


def inspect_push(root: Path, remote: str, source: str, target: str, *,
                 expected_source_tip: str, expected_target_tip: str | None) -> dict[str, Any]:
    """Resolve an explicit source and exact destination without fetch or push.

    None for expected_target_tip means the reviewed destination was absent.
    Missing target objects are UNKNOWN, never treated as fast-forward evidence.
    """
    report = _report()
    report.update(status='UNKNOWN', remote=remote, source=source, ref=target,
                  remote_identity='NOT_ASSESSED', server_protection='NOT_TESTED')
    parsed = publication(['git', 'push', remote, source + ':' + target])
    if (parsed['status'] != CONTEXT or not _ref(target) or not _sha(expected_source_tip)
            or (expected_target_tip is not None and not _sha(expected_target_tip))):
        report['status'] = 'INVALID_SCOPE'
        return report
    try:
        _absolute(root)
        _chain(root)
        if Path(_git(root, 'rev-parse', '--show-toplevel').strip()) != root:
            raise ReviewStop('OUT_OF_SCOPE')
        tip = _git(root, 'rev-parse', '--verify', '--end-of-options', source + '^{commit}').strip()
        if not _sha(tip):
            raise ReviewStop('UNKNOWN')
        report['source_tip'] = tip
        if tip != expected_source_tip:
            report['status'] = 'SOURCE_CHANGED'
            return report
        output = _git(root, 'ls-remote', '--refs', '--heads', remote, target)
        records = [line.split('\t') for line in output.splitlines() if line]
        if records and (len(records) != 1 or len(records[0]) != 2
                        or records[0][1] != target or not _sha(records[0][0])):
            raise ReviewStop('UNKNOWN')
        observed = records[0][0] if records else None
        report['target_tip'] = observed
        if observed != expected_target_tip:
            report['status'] = 'TARGET_CHANGED'
        elif observed is not None and not _ancestor(root, observed, tip):
            report['status'] = 'NOT_FAST_FORWARD'
        else:
            report['status'] = 'READY_FOR_REVIEW'
    except (OSError, ValueError, ReviewStop):
        report['status'] = 'UNKNOWN'
    return report


def _command_matches(item: dict[str, Any]) -> bool:
    try:
        command = tokenize(item.get('command'))
    except ValueError:
        return False
    scope = item['scope']
    if item['kind'] == 'local_delete':
        return ((command[:2] == ['Remove-Item', '-LiteralPath'] and len(command) == 3
                 and command[2] == scope['target'])
                or (command[:3] in (['git', 'branch', '-d'], ['git', 'worktree', 'remove'])
                    and len(command) == 4 and command[3] == scope['target']))
    parsed = publication(command)
    if parsed['status'] != CONTEXT or parsed['kind'] != item['kind']:
        return False
    objects = parsed['scope']
    if item['kind'] == 'remote_delete':
        return bool(objects['remote'] == scope['remote'] and scope['ref'] in objects['refs'])
    if item['kind'] == 'push':
        return bool(objects['remote'] == scope['remote']
                and objects['source'] == scope.get('source', scope['branch'])
                and objects['ref'] == scope.get('ref', branch_ref(scope['branch'])))
    if item['kind'] == 'pr_create':
        return all(objects[key] == scope[key] for key in ('repo', 'head', 'base', 'title'))
    return True


def _conditions(root: Path, command: Any, mode: str | None) -> dict[str, Any]:
    # Script invocation and package import both use the same read-only diagnostic.
    if __package__:
        from scripts.check_codex_approvals import diagnose
    else:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from check_codex_approvals import diagnose  # type: ignore[no-redef]
    return diagnose(root, mode, commands=[command])


def _block_reassessed(previous: dict[str, Any], diagnostic: dict[str, Any],
                      command: Any, loaded_rules_sha256: str | None) -> bool:
    """Compare caller-observed recovery evidence; never authenticate its source."""
    digest = diagnostic['rules_sha256']
    mode = diagnostic['effective_approval_policy']
    old_digest = previous.get('rules_sha256', '')
    return bool(previous.get('source') == 'PROJECT_PROMPT' and previous.get('raw_error')
                and previous.get('command') == command
                and isinstance(old_digest, str) and re.fullmatch(r'[0-9a-f]{64}', old_digest)
                and previous.get('mode') in {'never', 'on-request'}
                and loaded_rules_sha256 == digest and digest is not None
                and mode in {'never', 'on-request'}
                and (old_digest != digest or previous['mode'] != mode)
                and diagnostic['commands'][0]['status'] in {
                    'NO_PROJECT_RULE_REQUIREMENT', 'APPROVAL_REQUIRED'})


def review_actions(
    baseline: list[dict[str, Any]], current: list[dict[str, Any]], *, mode: str | None,
    revoked: set[str] | None = None, known_approval_block: bool = False,
    progress: dict[str, dict[str, str]] | None = None, delivery: dict[str, str] | None = None,
    root: Path | None = None, prior_blocks: dict[str, dict[str, Any]] | None = None,
    loaded_rules_sha256: str | None = None,
) -> dict[str, Any]:
    """Review synthetic or independently collected scope/progress observations.

    MATCH means the intended result has been independently reconciled, including
    its exact content/remote/ref. ABSENT means a successful query found no result
    (for deletion, MATCH instead means successful query proves target absence).
    These caller observations are not authenticated and cannot authorize actions.
    A known refusal needs observed changes to its actual source, not mode alone.
    Loaded-rule hashes and prior refusals are caller observations, never receipts.
    """
    result = _report()
    result.update(effective_mode=mode if mode in {'never', 'on-request'} else 'UNKNOWN',
                  mode_source='CALLER_OBSERVATION', known_approval_block=known_approval_block,
                  delivery=copy.deepcopy(delivery or {}))
    old = {item.get('id'): item for item in baseline}
    ids = [item.get('id') for item in current]
    duplicate = len(old) != len(baseline) or len(set(ids)) != len(ids)
    for item in current:
        key = item.get('id')
        evidence = (progress or {}).get(key, {}) if isinstance(key, str) else {}
        recorded = evidence.get('result', 'NOT_EXECUTED')
        row: dict[str, Any] = {'id': key, 'kind': item.get('kind'), 'status': 'INVALID_SCOPE',
                               'last_result': recorded if recorded in RESULTS else 'UNKNOWN'}
        result['items'].append(row)
        if not isinstance(key, str) or not key or duplicate or not _valid_scope(item):
            continue
        if key in (revoked or set()):
            row['status'] = 'REVOKED'
        elif key not in old:
            row['status'] = 'NOT_IN_SCOPE'
        elif old[key] != item:
            row['status'] = 'CHANGED'
            before, after = old[key].get('scope', {}), item['scope']
            row['changed_fields'] = sorted(k for k in before.keys() | after.keys()
                                          if before.get(k) != after.get(k))
            if old[key].get('kind') != item.get('kind'):
                row['changed_fields'].append('kind')
            if old[key].get('command') != item.get('command'):
                row['changed_fields'].append('command')
        elif evidence.get('reconciled') == 'MATCH':
            row['status'] = 'COMPLETE'
        elif evidence.get('reconciled') == 'DIFFERENT':
            row['status'] = 'CHANGED'
        elif recorded in {'SUCCESS', 'DELETED', 'ALREADY_ABSENT', 'UNKNOWN'} or (
                recorded != 'NOT_EXECUTED' and evidence.get('reconciled') != 'ABSENT'):
            row['status'] = 'RECONCILE_FIRST'
        else:
            previous = (prior_blocks or {}).get(key, {})
            known = known_approval_block or recorded == 'REJECTED' or bool(previous)
            diagnostic = _conditions(root or Path(__file__).resolve().parents[2], item.get('command'), mode)
            row['conditions'] = diagnostic
            if known and not _block_reassessed(previous, diagnostic, item.get('command'), loaded_rules_sha256):
                row['status'] = 'BLOCKED_EXECUTION_ROUTE'
            elif not _command_matches(item):
                row['status'] = 'UNKNOWN_COMMAND'
            elif diagnostic['errors']:
                row['status'] = 'UNKNOWN_RULES'
            elif (diagnostic['commands'][0]['status'] in {'INCOMPATIBLE', 'FORBIDDEN'}
                  or diagnostic['commands'][0]['hook_result'] not in {'ALLOW', CONTEXT}):
                row['status'] = 'BLOCKED_EXECUTION_ROUTE'
            elif mode not in {'never', 'on-request'}:
                row['status'] = 'UNKNOWN_MODE'
            else:
                row['status'] = 'READY_FOR_REVIEW'
    # A multi-ref command is one execution batch, but evidence remains per ref.
    # All refs must be explicitly represented; any changed/revoked item pauses
    # the batch, including a ready sibling. Completed refs remain completed.
    for item in current:
        try:
            command = tokenize(item.get('command'))
        except ValueError:
            continue
        parsed = publication(command)
        if parsed['kind'] != 'remote_delete' or len(parsed['scope']['refs']) < 2:
            continue
        members = [i for i, value in enumerate(current) if value.get('command') == item['command']]
        scoped_refs = [current[i].get('scope', {}).get('ref') for i in members]
        complete_scope = (set(scoped_refs) == set(parsed['scope']['refs'])
                          and len(scoped_refs) == len(set(scoped_refs)))
        ready = complete_scope and all(result['items'][i]['status'] == 'READY_FOR_REVIEW' for i in members)
        if not ready:
            for index in members:
                if result['items'][index]['status'] == 'READY_FOR_REVIEW':
                    result['items'][index]['status'] = 'BATCH_PAUSED'
                    result['items'][index]['batch_reason'] = 'reconcile, validate and authorize every ref before rebuilding a remaining batch'
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--ref', required=True, help='exact refs/heads/<branch>')
    parser.add_argument('--expected-tip', nargs=2, action='append', required=True,
                        metavar=('REMOTE', 'SHA'), help='comparison data, never authorization')
    parser.add_argument('--base-ref', default='refs/heads/develop')
    parser.add_argument('--protected-ref', action='append', default=[])
    args = parser.parse_args(argv)
    if len(dict(args.expected_tip)) != len(args.expected_tip):
        parser.error('duplicate remote')
    report = inspect_remote_deletion(args.root, args.ref, dict(args.expected_tip),
        base_ref=args.base_ref, protected_refs=set(args.protected_ref))
    print(json.dumps(report, indent=2))
    return 0 if all(item['status'] in {'READY_FOR_REVIEW', 'ALREADY_ABSENT'}
                    for item in report['items']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
