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

## REQ-001 — Native inventory and A14

The project config declares exactly GitHub, Playwright, Serena and memory PG ×5. Trust posture and credential mode live in `contracts/mcp-server.contract.yml`. Changes require the declaration in `contracts/governance.contract.yml` and Owner review. Business PG and ssh-manager remain excluded; user/plugin services are not imported.

Acceptance: native config parses, exact service names/commands/env names match, inline credentials and foreign entries fail. The BDD asserts the declaration structure only; actual review is human, not an implemented PR parser.

## REQ-002 — One native memory wrapper

All five memory entries use `scripts/mcp/pg-server-start.ps1` → `scripts/mcp/pg-server-wrapper.mjs`; only the matching variable name is passed. All five require a nonempty value and have no fallback URL. Neither startup arguments nor errors may expose values. No direct business database access is introduced.

Trace: `trace.yml`, the two native BDD scenarios and `scripts/sdd/check_codex_native.py`. Live services, credentials/platform setup and background lifecycle need separate evidence. Historical wrapper baseline is retained as provenance, not a second maintained implementation.
