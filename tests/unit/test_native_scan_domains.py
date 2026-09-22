"""Retired-client exclusions must preserve unrelated live governance coverage."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.check_frontmatter import find_scanned_docs  # noqa: E402
from scripts.check_loop_section_refs import iter_scanned_files  # noqa: E402
from scripts.check_wikilinks import iter_target_files  # noqa: E402
from scripts.sdd._common.native_assets import retired_client_asset  # noqa: E402


class NativeScanDomains(unittest.TestCase):
    def test_explicit_retired_client_assets(self):
        for rel in ['.claude/skills/x/SKILL.md', 'sdd/adapters/codex-skill-preface.md',
                    'sdd/development-agent.yml', 'policies/claude-code-skill.md']:
            self.assertTrue(retired_client_asset(rel))

    def test_nonclient_adapters_and_unknown_neighbors_remain_live(self):
        for rel in ['sdd/adapters/python.md', 'sdd/adapters/runtime-skill.md',
                    'sdd/adapters/new-adapter.md', 'policies/data-boundary.md',
                    '.agents/skills/new/SKILL.md']:
            self.assertFalse(retired_client_asset(rel))

    def test_live_scanners_do_not_read_retired_client_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = ['docs/rule/live.md', 'sdd/adapters/python.md', 'sdd/adapters/codex-skill-preface.md',
                     'policies/data-boundary.md', 'policies/claude-code-skill.md',
                     '.agents/skills/native/SKILL.md', '.claude/skills/old/SKILL.md']
            for rel in files:
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('SYNTHETIC', encoding='utf-8')
            lists = [set(p.as_posix() for p in find_scanned_docs(root)),
                     set(p.relative_to(root).as_posix() for p in iter_scanned_files(root)),
                     set(rel.as_posix() for _, rel in iter_target_files(root))]
            for found in lists:
                self.assertIn('docs/rule/live.md', found)
                self.assertNotIn('sdd/adapters/codex-skill-preface.md', found)
                self.assertNotIn('policies/claude-code-skill.md', found)
                self.assertNotIn('.claude/skills/old/SKILL.md', found)
            for found in lists[1:]:
                self.assertIn('sdd/adapters/python.md', found)
                self.assertIn('policies/data-boundary.md', found)
            self.assertIn('.agents/skills/native/SKILL.md', lists[1])


if __name__ == '__main__':
    unittest.main()
