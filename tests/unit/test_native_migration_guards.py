"""Synthetic P3 regression cases; runnable with unittest, collectable by pytest."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('native_guard', ROOT / 'scripts/sdd/codex_hook_guard.py')
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class NativeGuards(unittest.TestCase):
    def state(self, command):
        return guard.classify({'hook_event_name':'PreToolUse', 'tool_name':'exec_command',
                               'tool_input':{'cmd':command}})[0]

    def test_git_global_options_cannot_bypass_g1(self):
        for command in ['git -C ../elsewhere checkout -b feature/x',
                        'git --git-dir=elsewhere switch -c feature/x']:
            with self.subTest(command=command):
                self.assertIn(self.state(command), ('FORBIDDEN','UNKNOWN'))

    def test_git_owner_actions_stay_blocked(self):
        for command in ['git commit -m test', 'git push origin branch',
                        'gh pr create --base develop --title test']:
            self.assertEqual(self.state(command), 'OWNER_APPROVAL_REQUIRED')

    def test_known_forbidden_routes(self):
        for command in ['git checkout -q -b feature/x','git switch -c feature/x',
                        'gh pr create --title test', 'gh pr merge 1', 'psql placeholder',
                        'pg_dump placeholder', 'pg_restore placeholder']:
            self.assertEqual(self.state(command),'FORBIDDEN')

    def test_readonly_route(self):
        self.assertEqual(self.state('git status --short'), 'ALLOW')

    def test_native_ownership_and_gate_surfaces_require_owner(self):
        for path in ['AGENTS.md', 'tests/AGENTS.md', 'policies/ai-agent.md',
                     'sdd/gates.md', '.github/workflows/ci.yml',
                     'scripts/sdd/codex_hook_guard.py', 'scripts/sdd/check_codex_native.py',
                     'scripts/mcp/pg-server-wrapper.mjs',
                     'capabilities/infrastructure/mcp-server-governance/contracts/development-skill.contract.yml']:
            with self.subTest(path=path):
                self.assertEqual(guard.classify({'hook_event_name': 'PreToolUse',
                    'tool_name': 'Edit', 'tool_input': {'file_path': path}})[0], 'OWNER_APPROVAL_REQUIRED')

    def test_ordinary_doc_edit_is_not_new_owner_surface(self):
        self.assertEqual(guard.classify({'hook_event_name': 'PreToolUse',
            'tool_name': 'Edit', 'tool_input': {'file_path': 'docs/guide/example.md'}})[0], 'ALLOW')

    def test_apply_patch_command_wrapper_preserves_path_protection(self):
        for path, expected in [('.codex/synthetic.txt', 'OWNER_APPROVAL_REQUIRED'),
                               ('.env', 'FORBIDDEN'),
                               ('docs/guide/synthetic.md', 'ALLOW')]:
            with self.subTest(path=path):
                patch = f'*** Begin Patch\n*** Delete File: {path}\n*** End Patch'
                self.assertEqual(guard.classify({'hook_event_name': 'PreToolUse',
                    'tool_name': 'apply_patch', 'tool_input': {'command': patch}})[0], expected)

    def test_apply_patch_command_wrapper_rejects_ambiguous_payload(self):
        patch = '*** Begin Patch\n*** Delete File: .codex/synthetic.txt\n*** End Patch'
        for data in [{'command': patch, 'path': 'docs/guide/ordinary.md'},
                     {'command': patch, 'extra': True}, {'command': None},
                     {'command': 1}, {'command': []}, {'command': {}},
                     {'command': ''}, {'command': 'not a patch'}]:
            with self.subTest(data=data):
                self.assertEqual(guard.classify({'hook_event_name': 'PreToolUse',
                    'tool_name': 'apply_patch', 'tool_input': data})[0], 'UNKNOWN')

    def test_apply_patch_command_wrapper_checks_move_destination(self):
        patch = ('*** Begin Patch\n*** Update File: docs/guide/synthetic.md\n'
                 '*** Move to: .codex/synthetic.txt\n@@\n-a\n+b\n*** End Patch')
        self.assertEqual(guard.classify({'hook_event_name': 'PreToolUse',
            'tool_name': 'apply_patch', 'tool_input': {'command': patch}})[0],
            'OWNER_APPROVAL_REQUIRED')

    def test_invalid_payload_is_closed(self):
        for value in [{}, {'hook_event_name':'PreToolUse'},
                      {'hook_event_name':'PreToolUse','tool_name':'apply_patch','tool_input':{}}]:
            self.assertEqual(guard.classify(value)[0], 'UNKNOWN')

    def test_payload_projection_drops_untrusted_fields(self):
        self.assertEqual(guard.project_payload({'transcript':'synthetic-do-not-echo',
                                               'hook_event_name':'PreToolUse'}),
                         {'hook_event_name':'PreToolUse'})


if __name__ == '__main__':
    unittest.main()
