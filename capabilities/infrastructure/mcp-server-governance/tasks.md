---
type: capability-tasks
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-23
---

# Tasks: MCP Server Inventory + Governance

> Codex-only native ownership: A14 PR-body declaration is reviewed manually; V11 checks the native config in CI, not the PR body.

## Backlog

### T-001 — Phase M1 capability artifact suite
- **Phase**：M1 / **Priority**：critical (meta) / **Linked REQ**：N/A
- **Status**：in-progress

### T-002 — REQ-001 8-server inventory + A14 PR gate declaration
- **Phase**：current native ownership (manual A14 declaration; V11 static config check)
- **Priority**：medium / **Linked REQ**：REQ-001
- **Contract changed?**：yes (#495 corrects the automation claim; Owner approval required)
- **HITL trigger**：any .codex/config.toml modification → A14 gate per `contracts/governance.contract.yml §a14_pr_gate` (former MCP STANDARD §4, archived M6 X5)
- **Status**：done (native inventory check and A14 declaration template); PR-body automation declined
- **Verification**：`scripts/sdd/check_codex_native.py --surface mcp` (V11, config only); `tests/unit/test_native_mcp_scopes.py` (positive and negative config cases); `tests/bdd/infrastructure/mcp_governance/test_mcp_governance_bdd.py` (template structure only)
- **Declined**：`scripts/sdd/check_a14_gate.py` and the old `.mcp.json` PR-body parser test. Revive only if Owner separately approves PR-body automation for current `.codex/config.toml`/native MCP triggers and decides its CI posture; V11 must not be relabeled as that parser.

### T-003 — REQ-002 wrapper consistency
- **Phase**：current native ownership
- **Priority**：medium / **Linked REQ**：REQ-002
- **Contract changed?**：no
- **HITL trigger**：scripts/mcp/pg-server-* modifications → baseline diff against `docs/_baselines/pg_server_baseline.md`
- **Status**：done (native V11 and BDD verify all five wrapper references and env names)
- **Verification**：`scripts/sdd/check_codex_native.py --surface mcp`; `tests/bdd/infrastructure/mcp_governance/test_mcp_governance_bdd.py::test_req_002_pg_wrapper_consistency`
- **Declined**：the separate historical-baseline drift gate; `docs/_baselines/pg_server_baseline.md` remains provenance, with quarterly manual comparison under T-004.

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
- **Per-entry separate config files** — rejected per design §4 tradeoff B (convention is single .codex/config.toml)
- **Empty defaults for all entries** — rejected per design §4 tradeoff F (first-clone friction)
- **Per-host enumeration of ssh-manager's 9 hosts as separate MCP servers** — rejected per REQ-001 (counts as 1 server matching .codex/config.toml structure; quarterly audit enumerates internally)

---

> T-002/T-003 use current native checks and BDD bindings in trace.yml. T-004 quarterly automation and T-005 cross-capability sync remain separate backlog items; native service/host execution remains separately evidenced.
