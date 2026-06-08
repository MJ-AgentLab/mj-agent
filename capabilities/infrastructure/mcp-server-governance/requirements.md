---
type: capability-requirements
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Requirements: MCP Server Inventory + Governance

> Phase M1 baseline. 2 REQs @risk:medium. Per ADR-028 + ADR-030.

## REQ-001 — 13-server inventory + trust posture declaration

**Priority**：medium

**Statement**：`.mcp.json` SHALL declare 13 server entries with trust posture + credential mode per entry; any modification SHALL trigger A14 PR gate declaration block in PR body per the template in `contracts/governance.contract.yml §a14_pr_gate.pr_body_required_block` (former MCP STANDARD §4, archived M6 X5).

**Rationale**：

`.mcp.json` defines what Claude Code can talk to. Each MCP server is a trust-boundary expansion. Trust posture (first-party / third-party / community) + credential mode (none / OAuth / API key / wrapped script) must be reviewed at every modification because:

1. Third-party MCP could exfiltrate via tool calls
2. Community MCP may be unmaintained
3. Wrapped first-party (10/13 pg entries) requires baseline integrity check
4. Quarterly audit (§6 of MCP STANDARD) re-evaluates trust posture as upstream MCP servers evolve

**Acceptance**：

13 server entries by category:

| Category | Count | Notes |
|---|---|---|
| first-party (Anthropic) | 1 | github |
| third-party | 2 | serena (LSP), ssh-manager |
| first-party wrapper | 10 | pg-server wrapper around community pg MCP (5 mj-agent memory + 5 mj-system biz; DEV/TEST-LAN/TEST-WAN/PROD-LAN/PROD-WAN matrix) |

Per-entry attributes (each entry MUST have these declarable):

- `name`: server identifier (per .mcp.json key)
- `type`: stdio / sse / http (currently all 13 are stdio)
- `trust_posture`: first-party / third-party / first-party-wrapper / community
- `credential_mode`: none / OAuth / API key via env / wrapped script + env URL
- `wrapper_script`: path (for first-party-wrapper) OR null
- `env_secrets`: list of env var names this entry reads

A14 PR gate (CI gate per Meta v2.1 §7.7):

- Any `.mcp.json` modification → PR body MUST contain per-server posture declaration block per §4 template
- Block lists each added / removed / changed server with trust_posture + credential_mode + rationale
- PR lacking the block: PR gate fails (Phase M3+ blocking; warning at M1)

Quarterly audit (per §6 of MCP STANDARD; out of scope for this REQ but referenced)：

- Every 3 months, DRI re-evaluates trust_posture of each server
- Sync wrapper script baseline against community pg MCP upstream (per `docs/_baselines/pg_server_baseline.md`)

**BDD Examples**：

- **Given** the PR body declares `.mcp.json` changed (added a 14th server)
- **When** CI reviewer parses the PR
- **Then** the body MUST contain the per-server posture declaration block matching the §4 template; PR lacking the block fails A14 gate review

**Trace**：REQ-001 → `contracts/mcp-server.contract.yml` (13-entry inventory) + `contracts/governance.contract.yml` (A14 gate logic) + `behavior.feature` Scenario 1 + **TBD-M3** `tests/contract/test_mcp_inventory.py`

---

## REQ-002 — All pg entries route through same wrapper script

**Priority**：medium

**Statement**：All 10 pg-* entries SHALL route through the same wrapper script (`.claude/scripts/pg-server-start.cmd`); deviation from this wrapper triggers A14 "credential mode changed" sub-check.

**Rationale**：

Wrapper script centralizes pg MCP connection handling: timeout config, error format normalization, credential read from env (NOT from .mcp.json literal). Per-entry deviation:

1. Multiplies maintenance surface (one wrapper → 10 wrappers)
2. Breaks centralized credential read pattern
3. Could leak `REPLACE_WITH_*_PASSWORD` sentinels if env override not set

Baseline tracked at `docs/_baselines/pg_server_baseline.md` (per ADR-028 + CLAUDE.md §A14 narrative; quarterly sync against community pg MCP upstream).

**Acceptance**：

- All 10 pg-* entries in `.mcp.json` invoke `.claude/scripts/pg-server-start.cmd` (with appropriate args)
- The wrapper script in turn invokes `pg-server-wrapper.mjs` (Node-based; allows URL override via env)
- 5 entries use `MJ_AGENT_PG_MEMORY_*_URL` env overrides (DEV / TEST-LAN / TEST-WAN / PROD-LAN / PROD-WAN)
- 5 entries use `MJ_AGENT_PG_BIZ_*_URL` env overrides (same matrix)
- 4 WAN entries have NO default URL (entire URL from env; missing env → empty arg → startup error; intentional fail-loud)
- 6 LAN/DEV entries have sentinel defaults: `REPLACE_WITH_TEAM_TEST_PASSWORD` / `REPLACE_WITH_TEAM_PROD_PASSWORD` / `REPLACE_WITH_ANALYST_PASSWORD` — silently auth-fail if env override not set (intentional dev experience: setup-mcp-secrets.ps1 sets the overrides via `setup-mcp-env.ps1`)
- Wrapper baseline (`docs/_baselines/pg_server_baseline.md`) is the SOR for wrapper script behavior; quarterly diff against community pg MCP

**BDD Examples**：

- **Given** `.mcp.json` is loaded
- **When** the wrapper-script reference is inspected for each `pg-*` server
- **Then** all 10 entries reference `.claude/scripts/pg-server-start.cmd`; any entry referencing a different wrapper triggers the A14 "credential mode changed" sub-check

**Trace**：REQ-002 → `contracts/mcp-server.contract.yml` (wrapper script section) + `behavior.feature` Scenario 2 + **TBD-M3** `tests/contract/test_mcp_pg_wrapper_consistency.py`

---

> Phase M1 baseline. ADR-028 + ADR-030 + cross-cap to docker-compose (pg endpoints) + llm-provider (DGX host).
