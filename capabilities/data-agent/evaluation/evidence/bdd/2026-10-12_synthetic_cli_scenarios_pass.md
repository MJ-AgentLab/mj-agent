# #582 synthetic-only CLI BDD PASS record

- Date: 2026-10-12, Asia/Taipei; implementation and same-agent SWE verification: Codex.
- Base: 5b8833c523f4401de7b70deb5a82b908f3a9c763; current candidate is UNCOMMITTED.
- Formal source: contracts/behavior.feature; bindings: tests/bdd/data_agent/evaluation/test_evaluation_bdd.py.
- Original six core scenarios plus four approved CLI scenarios = ten automated scenarios; six carry @risk:critical, all ten are high/critical.
- Windows fixed NTFS: full hardened offline execution recorded in [transcript](2026-10-12_synthetic_cli_pytest.txt).
- CLI scenarios: identical report pairs/process3 and fixed22-case labels; actual manifest early2 without replay/other reads/output; unsafe paths/hardlinks without payload echo; existing artifact/partial write2 with old bytes preserved and no cleanup.
- Native directory rename, reparse/OFFLINE/RECALL, descriptor, network/device/alias and IO fault details are additionally covered by the CLI unit suite.
- Synthetic output is SELFTEST_ONLY, metrics=null, baseline_eligible=false. Original core actual branches remain explicitly fictional unit conditions, not sampled runtime evidence.
- Linux/macOS native file entry is DEFERRED_FS_CAPABILITY, not executed successfully; the four CLI BDD scenarios explicitly skip there. Original six memory-core scenarios remain portable.
- Source provenance and independent checks are same-agent rounds, not external review or Owner acceptance.
- Old cli_scenarios_pass.md/145-case acceptance apply to the prior parallel candidate only; immutable historical record.
