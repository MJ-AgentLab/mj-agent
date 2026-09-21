"""Gate-scope isolation, native inventory contract and no-secret diagnostics."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('native_check', ROOT / 'scripts/sdd/check_codex_native.py')
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class NativeMcpScopes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in checker.REQUIRED:
            source = ROOT / rel
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def test_valid_native_public_fixture(self):
        self.assertEqual(checker.check(self.root), [])

    def test_enforcement_drift_does_not_become_v11_failure(self):
        (self.root / '.codex/hooks.json').write_text('{}')
        self.assertEqual(checker.check_mcp(self.root), [])
        self.assertTrue(checker.check_enforcement(self.root))

    def test_missing_enforcement_is_not_a_neutral_skip(self):
        (self.root / '.codex/hooks.json').unlink()
        self.assertTrue(checker.check_enforcement(self.root))

    def test_mcp_drift_is_blocking_independently(self):
        (self.root / '.codex/config.toml').write_text('invalid TOML [')
        self.assertTrue(checker.check_mcp(self.root))
        self.assertEqual(checker.check_enforcement(self.root), [])

    def test_malformed_input_does_not_echo_secret(self):
        (self.root / '.codex/config.toml').write_text('token = "SYNTHETIC_SECRET_CANARY"')
        errors = checker.check_mcp(self.root)
        self.assertTrue(errors)
        self.assertNotIn('SYNTHETIC_SECRET_CANARY', json.dumps(errors))


if __name__ == '__main__':
    unittest.main()
