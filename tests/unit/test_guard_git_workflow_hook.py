"""Native protocol successors for the old shell-hook safety cases (no host activation)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / 'scripts/sdd/codex_hook_guard.py'


class NativeWire(unittest.TestCase):
    def run_wire(self, raw):
        proc = subprocess.run([sys.executable, '-I', '-B', str(GUARD)], input=raw,
                              text=True, encoding='utf-8', capture_output=True, check=True)
        self.assertEqual(proc.stderr, '')
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def command(self, command):
        return self.run_wire(json.dumps({'hook_event_name':'PreToolUse', 'tool_name':'exec_command',
                                        'tool_input':{'cmd':command}}, ensure_ascii=False))

    def test_guard_blocks(self):
        for command in ['git checkout -b feature/x', 'git switch -c feature/x',
                        'gh pr create --title t --body-file b.md', 'git checkout -q -b feature/x',
                        'git -C ../elsewhere checkout -b feature/x', 'git checkout main -b feature/x',
                        'cd sub && git checkout -b feature/x', 'git checkout -b feature/x && echo "中文"']:
            with self.subTest(command=command):
                self.assertEqual(self.command(command)['decision'], 'block')

    def test_guard_allows_ordinary_commands(self):
        for command in ['git status', 'git checkout main', 'echo git checkout -b nope']:
            self.assertIsNone(self.command(command))

    def test_owner_actions_defer_without_claiming_approval(self):
        for command in ['gh pr create --base develop --title t',
                        'git commit -m "docs: mention checkout -b in guide"', 'git commit -m "docs: 中文提交说明"']:
            output = self.command(command)
            self.assertEqual(set(output), {'hookSpecificOutput'})
            self.assertTrue(output['hookSpecificOutput']['additionalContext'].startswith('HOST_APPROVAL_REQUIRED:'))
        self.assertTrue(self.command('gh pr create --base=main --title t')['reason'].startswith('UNKNOWN:'))

    def test_unparsed_compound_is_explicit_unknown(self):
        self.assertTrue(self.command('echo 中文 && git status')['reason'].startswith('UNKNOWN:'))

    def test_fail_closed_input_protocol(self):
        for raw in ['this is not json', '', '{}', '{"tool_name":"Bash","hook_event_name":"PreToolUse"}',
                    '{"tool_name":"Edit","hook_event_name":"PreToolUse","tool_input":{"command":"git status"}}']:
            self.assertEqual(self.run_wire(raw)['decision'], 'block')


if __name__ == '__main__':
    unittest.main()
