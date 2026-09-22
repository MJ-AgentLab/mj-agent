"""Finite Git/gh recognizer. No execution, shell evaluation or authorization."""
from __future__ import annotations

import re
from typing import Any

CONTEXT = 'TASK_AUTHORIZATION_CONTEXT'


def tokenize(command: Any) -> list[str]:
    """Accept literal argv or a conservative common PowerShell/shell subset.

    Quotes can occur after '='; backslashes in Windows paths are preserved.
    Expansion/escaping outside literal single quotes is intentionally unsupported.
    This is not a general shell parser and must not execute the returned tokens.
    """
    if isinstance(command, list):
        if not command or not all(isinstance(t, str) and '\0' not in t for t in command):
            raise ValueError('invalid argv')
        return list(command)
    if not isinstance(command, str):
        raise ValueError('missing command')
    tokens: list[str] = []
    token = ''
    quote = ''
    started = False
    for index, char in enumerate(command):
        if char == '\0':
            raise ValueError('invalid character')
        if quote:
            if char == quote:
                if char == "'" and command[index:index + 2] == "''":
                    raise ValueError('shell-dependent doubled quote requires review')
                if token.endswith('\\'):
                    raise ValueError('ambiguous quote escape')
                quote = ''
            elif quote == '"' and char in '$`':
                raise ValueError('expansion requires review')
            else:
                token += char
        elif char in '\"\'':
            quote = char
            started = True
        elif char in ';|&<>`$(){}#@\n\r':
            raise ValueError('compound or expanding command requires review')
        elif char.isspace():
            if started:
                tokens.append(token)
                token, started = '', False
        else:
            token += char
            started = True
    if quote:
        raise ValueError('unclosed quote')
    if started:
        tokens.append(token)
    if not tokens:
        raise ValueError('missing command')
    return tokens


def branch(value: str) -> bool:
    if value.startswith('refs/') and not value.startswith('refs/heads/'):
        return False
    return (bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', value))
            and value != 'HEAD' and '..' not in value and '//' not in value
            and all(part and not part.startswith('.') and not part.endswith(('.', '.lock'))
                    for part in value.split('/')))


def ref(value: str) -> str:
    return value if value.startswith('refs/heads/') else 'refs/heads/' + value


def _value(args: list[str], index: int) -> tuple[str, str, int]:
    flag = args[index]
    if flag.startswith('--') and '=' in flag:
        flag, value = flag.split('=', 1)
        index += 1
    else:
        if index + 1 >= len(args):
            raise ValueError('missing option value')
        value = args[index + 1]
        index += 2
    if not value.strip() or value.startswith('-'):
        raise ValueError('missing or ambiguous option value')
    return flag, value, index


def publication(tokens: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {'status': 'UNKNOWN', 'reason': 'unrecognized publication form',
                              'kind': None, 'scope': {}}
    args: list[str]
    try:
        if tokens[:2] == ['git', 'commit']:
            args = tokens[2:]
            messages: list[str] = []
            file = None
            index = 0
            while index < len(args):
                flag, value, index = _value(args, index)
                if flag in {'-m', '--message'} and file is None:
                    messages.append(value)
                elif flag in {'-F', '--file'} and file is None and not messages:
                    if any(c in value for c in '*?[]'):
                        raise ValueError('message file must be literal')
                    file = value
                else:
                    raise ValueError('unknown or conflicting commit options')
            result.update(kind='commit', scope={'messages': messages, 'message_file': file})
        elif tokens[:2] == ['git', 'push']:
            args = tokens[2:]
            positional = []
            upstream = delete = False
            for value in args:
                if value in {'-u', '--set-upstream'} and not upstream:
                    upstream = True
                elif value == '--delete' and not delete:
                    delete = True
                elif value.startswith('-'):
                    raise ValueError('unsupported or repeated push option')
                else:
                    positional.append(value)
            if len(positional) < 2 or positional[0] not in {'gitee', 'origin'}:
                raise ValueError('explicit known remote and branch required')
            remote, *targets = positional
            if delete:
                if upstream or not all(branch(value) for value in targets):
                    raise ValueError('invalid deletion options or refs')
                refs = [ref(value) for value in targets]
                if len(set(refs)) != len(refs):
                    raise ValueError('duplicate deletion target')
                if {'refs/heads/main', 'refs/heads/develop'} & set(refs):
                    return dict(result, status='FORBIDDEN', reason='protected remote branch')
                result.update(kind='remote_delete', scope={'remote': remote, 'refs': refs})
            else:
                if len(targets) != 1:
                    raise ValueError('one explicit push refspec required')
                value = targets[0]
                source, target = value.split(':') if value.count(':') == 1 else (value, value)
                if not (source == 'HEAD' or branch(source)) or not branch(target):
                    raise ValueError('explicit non-force source and heads target required')
                result.update(kind='push', scope={'remote': remote, 'source': source,
                                                  'ref': ref(target), 'upstream': upstream})
        elif tokens[:3] == ['gh', 'pr', 'create']:
            args = tokens[3:]
            aliases = {'-R': '--repo', '-H': '--head', '-B': '--base', '-t': '--title',
                       '-F': '--body-file', '-d': '--draft'}
            values: dict[str, str] = {}
            index = 0
            while index < len(args):
                flag = aliases.get(args[index], args[index])
                if flag == '--draft':
                    value = 'true'
                    index += 1
                else:
                    raw, value, index = _value(args, index)
                    flag = aliases.get(raw, raw)
                if flag not in {'--repo', '--head', '--base', '--title', '--body-file', '--draft'}:
                    raise ValueError('unknown PR option')
                if flag in values:
                    raise ValueError('duplicate PR option')
                values[flag] = value
            if '--base' not in values:
                return dict(result, status='FORBIDDEN', reason='G2 explicit base required')
            head = values.get('--head')
            if head and values['--base'] != ('main' if head.removeprefix('refs/heads/').startswith('hotfix/') else 'develop'):
                return dict(result, status='FORBIDDEN', reason='G2 base does not match head type')
            required = {'--repo', '--head', '--base', '--title', '--body-file'}
            if not required.issubset(values) or not head or not branch(head):
                raise ValueError('explicit repo/head/base/title/body-file required')
            if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', values['--repo']):
                raise ValueError('explicit owner/repository required')
            if any(c in values['--body-file'] for c in '*?[]'):
                raise ValueError('body file must be literal')
            result.update(kind='pr_create', scope={key[2:].replace('-', '_'): value
                                                   for key, value in values.items()})
        else:
            return result
    except ValueError as exc:
        return dict(result, status='UNKNOWN', reason=str(exc), kind=None, scope={})
    return dict(result, status=CONTEXT,
                reason=f"{result['kind']}; verify exact task authorization and current objects")
