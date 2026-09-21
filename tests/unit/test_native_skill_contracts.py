"""Native skill/contract checks using public, synthetic fixtures only."""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('native_skills', ROOT / 'scripts/sdd/check_native_skills.py')
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class NativeSkills(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.name = 'mj-agent-infra-fixture'
        self.relative = f'.agents/skills/{self.name}/SKILL.md'
        self.description = 'A controlled fixture with clear steps. ' * 6 + 'Do not use for: production.'
        self.body = '\n# Fixture\n\n## Workflow\n\nRead [boundary](../../references/execution-boundaries.md).\n'
        self.write(self.relative, '---\n' + yaml.safe_dump({'name':self.name, 'description':self.description}) + '---\n' + self.body)
        self.write('.agents/skills/SKILL_INDEX.md', f'# Skills\n\n- [{self.name}]({self.name}/SKILL.md)\n')
        self.write('.agents/references/execution-boundaries.md', '# Boundary\nOWNER_APPROVAL_REQUIRED; BLOCKED_EXECUTION_ROUTE\n')
        self.contract = {'contract_id':'development-skill', 'schema_version':1,
            'adapter':'development-skill', 'covers_requirements':['REQ-001','REQ-002'],
            'namespace_pattern':'^mj-agent-infra-[a-z-]+$', 'family':'infra',
            'schema_compliance':'native-name-description-v1',
            'hitl_required':['mcp-server-trust-posture-change'],
            'skills':[{'name':self.name,'file':self.relative,
                'description_hash':'sha256:'+hashlib.sha256(self.description.encode()).hexdigest(),
                'body_content_hash':'sha256:'+hashlib.sha256(self.body.encode()).hexdigest(),
                'body_section_heads':['## Workflow'], 'frozen_at':'2026-09-18T00:00:00Z'}]}
        self.save_contract()

    def write(self, relative, text):
        p=self.root/relative
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text,encoding='utf-8')

    def save_contract(self):
        self.write(checker.CONTRACT, yaml.safe_dump(self.contract,allow_unicode=True))

    def test_native_only_fixture_passes(self):
        self.assertEqual(checker.check(self.root), [])
        self.assertFalse((self.root/'.claude').exists())

    def test_empty_root_fails(self):
        self.assertTrue(checker.check(self.root/'missing'))

    def test_boolean_contract_version_rejected(self):
        self.contract['schema_version'] = True
        self.save_contract()
        self.assertTrue(checker.check(self.root))

    def test_native_repository_resource(self):
        self.write('policies/example.md', '# Public')
        p = self.root / self.relative
        p.write_text(p.read_text() + '\n`repo:policies/example.md`\n')
        self.assertEqual(checker.resources(self.root), [])
        (self.root / 'policies/example.md').unlink()
        self.assertTrue(checker.resources(self.root))

    def test_resource_escape(self):
        p = self.root / self.relative
        p.write_text(p.read_text() + '\n`repo:../outside.md`\n')
        self.assertTrue(checker.resources(self.root))

    def test_unresolved_peer_invocation(self):
        p = self.root / self.relative
        p.write_text(p.read_text() + '\n$ mj-agent-not-a-call\n$ mj-agent-*\n$mj-agent-flow-missing\n')
        self.assertTrue(checker.resources(self.root))

    def test_missing_skill_fails(self):
        (self.root/self.relative).unlink()
        self.assertTrue(checker.check(self.root))

    def test_duplicate_yaml_key_rejected(self):
        p=self.root/self.relative
        p.write_text(p.read_text().replace('name: ', 'name: duplicate\nname: '),encoding='utf-8')
        self.assertTrue(checker.check(self.root))

    def test_wrong_name_rejected(self):
        p=self.root/self.relative
        p.write_text(p.read_text().replace(self.name,'mj-agent-infra-other'),encoding='utf-8')
        self.assertTrue(checker.check(self.root))

    def test_missing_local_reference_rejected(self):
        (self.root/'.agents/references/execution-boundaries.md').unlink()
        self.assertTrue(checker.check(self.root))

    def test_outside_reference_rejected(self):
        p=self.root/self.relative
        p.write_text(p.read_text()+'\n[escape](../../../../outside.md)\n',encoding='utf-8')
        self.assertTrue(checker.check(self.root))

    def test_legacy_active_dependency_rejected(self):
        p=self.root/self.relative
        p.write_text(p.read_text()+'\nRun scripts/sdd/agents_sync.py sync\n',encoding='utf-8')
        self.assertTrue(checker.check(self.root))

    def test_body_drift_rejected(self):
        p=self.root/self.relative
        p.write_text(p.read_text()+'\nChanged behavior\n',encoding='utf-8')
        self.assertTrue(checker.check(self.root))

    def test_description_drift_rejected(self):
        p=self.root/self.relative
        p.write_text(p.read_text().replace('A controlled','Another controlled'),encoding='utf-8')
        self.assertTrue(checker.check(self.root))

    def test_missing_frozen_member_rejected(self):
        self.contract['skills']=[]
        self.save_contract()
        self.assertTrue(checker.check(self.root))

    def test_unknown_contract_field_rejected(self):
        self.contract['ignored']='must fail'
        self.save_contract()
        self.assertTrue(checker.check(self.root))

    def test_contract_escape_rejected_without_read(self):
        self.contract['skills'][0]['file']='../../private.env'
        self.save_contract()
        self.assertTrue(checker.check(self.root))

    def test_invalid_yaml_does_not_echo_values(self):
        sentinel='SYNTHETIC_SECRET_DO_NOT_ECHO'
        self.write(checker.CONTRACT, 'broken: [ '+sentinel)
        errors=checker.check(self.root)
        self.assertTrue(errors)
        self.assertNotIn(sentinel,repr(errors))

    def test_windows_newlines_preserve_freeze(self):
        p=self.root/self.relative
        p.write_bytes(p.read_text(encoding='utf-8').replace('\n','\r\n').encode('utf-8'))
        self.assertEqual(checker.check(self.root),[])


if __name__ == '__main__':
    unittest.main()
