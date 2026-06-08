---
type: capability-tasks
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Tasks: MCP Server Inventory + Governance

> Phase M1 baseline. medium-risk REQs; A14 gate manual at M1, automated at M3.

## Backlog

### T-001 — Phase M1 capability artifact suite
- **Phase**：M1 / **Priority**：critical (meta) / **Linked REQ**：N/A
- **Status**：in-progress

### T-002 — REQ-001 13-server inventory + A14 PR gate declaration
- **Phase**：M1 (contract; informational) / M2 (CI warning) / M3 (CI blocking)
- **Priority**：medium / **Linked REQ**：REQ-001
- **Contract changed?**：no
- **HITL trigger**：any .mcp.json modification → A14 gate per `contracts/governance.contract.yml §a14_pr_gate` (former MCP STANDARD §4, archived M6 X5)
- **Status**：done (M1 contract); TBD-M3 tests + automation
- **TDD test_list**：
  - **TBD-M3** `tests/contract/test_mcp_inventory.py::test_thirteen_server_entries`
  - **TBD-M3** `tests/contract/test_mcp_inventory.py::test_per_entry_trust_posture_declared` — assert each entry's trust posture matches mcp-server.contract.yml
  - **TBD-M3** `tests/contract/test_mcp_inventory.py::test_credential_mode_per_entry`
  - **TBD-M3** `scripts/sdd/check_a14_gate.py` — PR body parser; warning at M2 / blocking at M3
  - **TBD-M3** `tests/contract/test_a14_gate.py::test_pr_body_contains_mcp_block_when_mcp_json_changed`

### T-003 — REQ-002 wrapper consistency
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：medium / **Linked REQ**：REQ-002
- **Contract changed?**：no
- **HITL trigger**：.claude/scripts/pg-server-* modifications → baseline diff against `docs/_baselines/pg_server_baseline.md`
- **Status**：done (M1 contract); TBD-M3 tests
- **TDD test_list**：
  - **TBD-M3** `tests/contract/test_mcp_pg_wrapper_consistency.py::test_all_pg_entries_use_same_wrapper` — load .mcp.json; iterate pg-* entries; assert all invoke `.claude\scripts\pg-server-start.cmd`
  - **TBD-M3** `tests/contract/test_mcp_pg_wrapper_consistency.py::test_pg_wrapper_baseline_aligned` — diff `.claude/scripts/pg-server-wrapper.mjs` against `docs/_baselines/pg_server_baseline.md` (warn on drift; fail on major change)

### T-004 — Quarterly audit cycle (cron-driven)
- **Phase**：M4+ (automation; not blocking M1)
- **Priority**：low
- **Linked REQ**：REQ-001 (governance §6)
- **HITL trigger**：cycle lapse > 1 month
- **Status**：TBD-M4+
- **TDD test_list**：
  - **TBD-M4** `scripts/sdd/check_mcp_quarterly_audit.py` — cron-friendly; checks last audit date; flags overdue
  - **TBD-M4** evidence/runtime/<YYYY-Q>_mcp_trust_audit.md template

### T-005 — Cross-capability sync with secrets-pipeline (Phase 2+)
- **Phase**：M2+ (depends on infrastructure.secrets-pipeline being defined)
- **Priority**：medium
- **Linked REQ**：REQ-001 (cross-cap)
- **HITL trigger**：none in M1; secrets-pipeline ADR-030 cross-cap impact
- **Status**：TBD-M2
- **Description**：when `infrastructure.secrets-pipeline` capability lands (Phase 2+), sync `setup-mcp-secrets.ps1` env var coverage with this capability's mcp-server.contract.yml env_secrets fields.

## In-Progress
(none beyond T-001)

## Anti-Backlog
- **Per-entry separate config files** — rejected per design §4 tradeoff B (convention is single .mcp.json)
- **Empty defaults for all entries** — rejected per design §4 tradeoff F (first-clone friction)
- **Per-host enumeration of ssh-manager's 9 hosts as separate MCP servers** — rejected per REQ-001 (counts as 1 server matching .mcp.json structure; quarterly audit enumerates internally)

---

> Phase M1 baseline. 5 TBD-M3 test entries + 1 TBD-M4 cron + 1 TBD-M2 cross-cap.
