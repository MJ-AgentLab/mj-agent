---
type: capability-design
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-09-23
---

# Design: MCP Server Inventory + Governance

## Native ownership and boundaries

`.codex/config.toml` and `scripts/mcp/` are maintained directly. The eight services remain within the existing project scope. GitHub uses its named token; memory PG ×5 uses its named URL; Playwright and Serena require no secret injection. App environment and MCP environment remain separate.

The PowerShell bootstrap resolves the Git root, calls the native startup script, and propagates failure. The Node wrapper receives only the required environment name and sanitizes child diagnostics. Unknown/missing inputs fail without printing values. This design does not attest that services are currently reachable.

## Review and verification

A14 applies to inventory, trust, credential mode and wrapper changes. The PR reviewer checks the A14 declaration in the PR body, and protected changes require Owner approval. No CI step parses or blocks on the A14 PR body. V11 checks native config shape and exact arguments only; tests use synthetic values. Owner approval does not unlock a blocked hook. Missing execution route returns BLOCKED_EXECUTION_ROUTE. Manual host trust, hook loading, model canary, actual credential platform and live service checks are separately evidenced.

## Contracts

`mcp-server.contract.yml`: inventory and wrapper; `governance.contract.yml`: declaration and manual audit; `development-skill.contract.yml`: eight infra skills with description/body freezes. Non-client adapters retain their original locations. Historical ADRs and evidence remain unchanged.
