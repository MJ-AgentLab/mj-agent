"""Offline negative tests for native entry and consumer closure; no host loading."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('native_governance', ROOT / 'scripts/sdd/check_native_governance.py')
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class NativeGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in guard.ENTRIES:
            self.put(rel, 'policies/ai-agent.md OWNER_APPROVAL_REQUIRED BLOCKED_EXECUTION_ROUTE')
        self.put('policies/ai-agent.md', '## §4 Owner\n' + '\n'.join(f'| `{x}` | required |' for x in guard.CANONICAL))
        self.put('.github/PULL_REQUEST_TEMPLATE.md', '## HITL Trigger Inventory\n' + '\n'.join(f'- [ ] {x}' for x in guard.CANONICAL))

    def put(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def test_native_entries(self):
        self.assertEqual(guard.entries(self.root), [])

    def test_missing_local_entry(self):
        (self.root / 'tests/AGENTS.md').unlink()
        self.assertTrue(guard.entries(self.root))

    def test_policy_enum_drift(self):
        self.put('policies/ai-agent.md', '## §4 Owner\n| `invented` | required |')
        self.assertTrue(guard.entries(self.root))

    def test_template_duplicate_not_hidden_by_set(self):
        path = self.root / '.github/PULL_REQUEST_TEMPLATE.md'
        path.write_text(path.read_text() + '\n- [ ] ' + guard.CANONICAL[0])
        self.assertTrue(guard.entries(self.root))

    def test_missing_policy_section(self):
        self.put('policies/ai-agent.md', ' '.join(guard.CANONICAL))
        self.assertTrue(guard.entries(self.root))

    def test_missing_boundary(self):
        self.put('AGENTS.md', 'policies/ai-agent.md')
        self.assertTrue(guard.entries(self.root))

    def test_script_legacy_dependency(self):
        self.put('scripts/current.py', "from scripts.sdd import agents_sync\n")
        self.assertTrue(guard.dependencies(self.root, ['scripts/current.py']))

    def test_native_script_allowed(self):
        self.put('scripts/current.py', "from pathlib import Path\np = Path('scripts/mcp/start.ps1')\n")
        self.assertEqual(guard.dependencies(self.root, ['scripts/current.py']), [])

    def test_old_path_literal_is_rejected(self):
        self.put('scripts/current.py', "source = '.claude/skills/x/SKILL.md'\n")
        self.assertTrue(guard.dependencies(self.root, ['scripts/current.py']))

    def test_missing_consumer_fails(self):
        self.assertTrue(guard.dependencies(self.root, ['scripts/missing.py']))

    def test_transitive_local_import_is_inspected(self):
        self.put('scripts/current.py', 'from scripts import helper\n')
        self.put('scripts/helper.py', "path = '.mcp.json'\n")
        self.assertTrue(guard.dependencies(self.root, ['scripts/current.py']))

    def test_new_workflow_command_requires_registration(self):
        self.put('.github/workflows/new.yml', 'steps:\n  - run: python scripts/new.py\n')
        self.assertTrue(guard.inventory_errors(self.root, ['.github/workflows/new.yml']))
        self.assertEqual(guard.inventory_errors(self.root, ['.github/workflows/new.yml', 'scripts/new.py']), [])

    def test_unknown_neighbor_is_not_protection_vocabulary(self):
        self.put('scripts/neighbor.py', "protected = '.mcp.json'\n")
        self.assertTrue(guard.dependencies(self.root, ['scripts/neighbor.py']))

    def test_diagnostics_do_not_echo_values(self):
        self.put('scripts/current.py', "password = 'SYNTHETIC_CANARY .mcp.json'\n")
        self.assertNotIn('SYNTHETIC_CANARY', str(guard.dependencies(self.root, ['scripts/current.py'])))


if __name__ == '__main__':
    unittest.main()
