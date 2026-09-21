"""Validate directly maintained development skills and frozen infra contracts.

Reads only native public files. No source projection, services, host activation,
credentials or approval authentication. All diagnostics omit input values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

import yaml

CONTRACT = 'capabilities/infrastructure/mcp-server-governance/contracts/development-skill.contract.yml'
NAME = re.compile(r'^mj-agent-(doc|flow|git|infra|runtime)-[a-z][a-z0-9-]*$')
OLD = re.compile(r'\.claude(?:/|\\)|CLAUDE\.md|\.mcp\.json|agents_sync\.py|\.agents\.lock\.json|\.migration/|codex-route:')
FM = re.compile(r'\A---\n(.*?)\n---\n', re.S)
LINK = re.compile(r'(?<!!)\[[^\]\n]+\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)')


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently taking the last value."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError('invalid mapping key')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_public(root: Path, relative: str) -> str:
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('outside root')
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError('indirect input')
    return path.read_text('utf-8')


def digest(value: str) -> str:
    return 'sha256:' + hashlib.sha256(value.encode('utf-8')).hexdigest()


def resources(root: Path) -> list[str]:
    """Check explicit native repository references and peer invocations."""
    errors = []
    paths = sorted((root / '.agents/skills').glob('*/SKILL.md'))
    if not paths:
        return ['no native skill resource roots']
    names = {p.parent.name for p in paths}
    for path in paths:
        rel = path.relative_to(root).as_posix()
        try:
            text = read_public(root, rel)
            for target in re.findall(r'`repo:([^`\n]+)`', text):
                target = target.split('#', 1)[0]
                resolved = (root / target).resolve()
                if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                    errors.append('missing or escaping repository resource: ' + rel)
            for name in re.findall(r'\$(mj-agent-[a-z]+-[a-z0-9-]+)(?![a-z0-9*{-])', text):
                if name not in names:
                    errors.append('unresolved native peer invocation: ' + rel)
        except (OSError, ValueError):
            errors.append('unreadable native resource owner: ' + rel)
    return errors


def check(root: Path) -> list[str]:
    errors: list[str] = []
    roster: dict[str, tuple[str, str]] = {}
    skills = sorted((root / '.agents/skills').glob('*/SKILL.md'))
    if not skills:
        errors.append('no native development skills')
    for path in skills:
        relative = path.relative_to(root).as_posix()
        try:
            text = read_public(root, relative)
            match = FM.match(text)
            if not match:
                raise ValueError('frontmatter')
            fm = yaml.load(match[1], Loader=UniqueLoader)
            if not isinstance(fm, dict) or set(fm) != {'name', 'description'}:
                raise ValueError('schema')
            name, description = fm['name'], fm['description']
            if not isinstance(name, str) or not NAME.fullmatch(name) or name != path.parent.name:
                raise ValueError('name')
            if (not isinstance(description, str) or len(description) < 200 or
                    len(description) > 1024 or not re.search(r'Do not use for[:：]', description)):
                raise ValueError('description')
            body = text[match.end():]
            if not body.strip():
                raise ValueError('empty body')
            roster[name] = (description, body)
            if OLD.search(text):
                errors.append(f'legacy dependency in native skill: {relative}')
            for link in LINK.finditer(text):
                target = unquote(link[1].strip('<>')).split('#', 1)[0]
                if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                    errors.append(f'missing or escaping local resource: {relative}')
        except (OSError, ValueError, TypeError, yaml.YAMLError):
            errors.append(f'invalid native skill: {relative}')
    try:
        index = read_public(root, '.agents/skills/SKILL_INDEX.md')
        names = re.findall(r'^- \[(mj-agent-[^\]]+)\]\(', index, re.M)
        if len(names) != len(set(names)) or set(names) != set(roster):
            errors.append('native skill index and discovery differ')
        boundary = read_public(root, '.agents/references/execution-boundaries.md')
        if not all(token in boundary for token in ('OWNER_APPROVAL_REQUIRED', 'BLOCKED_EXECUTION_ROUTE')):
            errors.append('shared execution boundaries incomplete')
        if OLD.search(boundary):
            errors.append('shared execution boundaries depend on legacy input')
    except (OSError, ValueError):
        errors.append('native skill index or shared boundaries missing')
    try:
        contract = yaml.load(read_public(root, CONTRACT), Loader=UniqueLoader)
        top = {'contract_id', 'schema_version', 'adapter', 'covers_requirements', 'namespace_pattern',
               'family', 'schema_compliance', 'hitl_required', 'skills'}
        if (not isinstance(contract, dict) or set(contract) != top
                or contract.get('contract_id') != 'development-skill' or type(contract.get('schema_version')) is not int
                or contract.get('schema_version') != 1
                or not isinstance(contract.get('skills'), list) or not contract['skills']):
            raise ValueError('contract schema')
        if (contract['adapter'] != 'development-skill' or contract['family'] != 'infra'
                or contract['namespace_pattern'] != '^mj-agent-infra-[a-z-]+$'
                or contract['schema_compliance'] != 'native-name-description-v1'
                or contract['covers_requirements'] != ['REQ-001', 'REQ-002']
                or contract['hitl_required'] != ['mcp-server-trust-posture-change']):
            raise ValueError('contract scope/approval metadata')
        seen = set()
        for entry in contract['skills']:
            required = {'name', 'file', 'description_hash', 'body_content_hash', 'body_section_heads', 'frozen_at'}
            if not isinstance(entry, dict) or set(entry) != required:
                raise ValueError('entry schema')
            name = entry['name']
            if (not isinstance(name, str) or name in seen or not name.startswith('mj-agent-infra-')
                    or name not in roster or entry['file'] != f'.agents/skills/{name}/SKILL.md'):
                raise ValueError('entry path/name')
            seen.add(name)
            description, body = roster[name]
            if (entry['description_hash'] != digest(description) or entry['body_content_hash'] != digest(body)
                    or entry['body_section_heads'] != re.findall(r'^## .+$', body, re.M)):
                errors.append(f'frozen native skill drift: {name}')
            # Strict timestamp syntax, independent of YAML implicit date typing.
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', str(entry['frozen_at'])):
                raise ValueError('freeze timestamp')
        if seen != {name for name in roster if name.startswith('mj-agent-infra-')}:
            errors.append('infra contract and native family coverage differ')
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError):
        errors.append('invalid or missing native infra contract')
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--surface', choices=('skills', 'resources'), default='skills')
    args = parser.parse_args(argv)
    errors = (check if args.surface == 'skills' else resources)(args.root)
    print(json.dumps({'result': 'FAIL' if errors else 'STATIC_PASS', 'errors': errors,
                      'host': 'NOT_TESTED', 'services': 'NOT_TESTED'}, ensure_ascii=False))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
