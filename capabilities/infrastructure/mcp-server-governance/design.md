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

`.codex/config.toml`, `scripts/mcp/` and `.codex/mcp/` are maintained directly. Nine services include the Owner-approved SSH B addition. GitHub uses its named token; memory PG ×5 uses its named URL; Playwright and Serena require no secret injection. App environment and MCP environment remain separate.

The PowerShell bootstrap resolves the Git root, calls the native startup script, and propagates failure. The Node wrapper receives only the required environment name and sanitizes child diagnostics. Unknown/missing inputs fail without printing values. This design does not attest that services are currently reachable.

SSH uses the project's small SDK/ssh2 server, not the historical 3.1.0 package's dotenv/personal config and permissive host-key loader. The nine fixed aliases and five password names match Owner B; cloud retains root and production remains enabled. Only two tools are exposed, including general shell with write capability. Strict public known_hosts comparison happens before authentication; missing credentials/keys, mismatches and revoked records fail closed. No private key reading, auto-add, retry or LAN/WAN fallback. Task authorization governs actual commands; shell is not a read-only sandbox. Output is bounded and known password literals are redacted, not arbitrary remote secrets. Timeout/cancel leaves remote state unknown.

## Review and verification

A14 applies to inventory, trust, credential mode and wrapper changes. The PR reviewer checks the A14 declaration in the PR body, and protected changes require Owner approval. No CI step parses or blocks on the A14 PR body. V11 checks native config shape and exact arguments only; tests use synthetic values. Owner approval does not unlock an actual host restriction. Missing execution route returns BLOCKED_EXECUTION_ROUTE. The current MCP-only project registers no hooks/rules. Normal MCP trust, actual credential platform and live service checks remain separately evidenced; policies/codex-development.md governs the profile.

## Contracts

`mcp-server.contract.yml`: inventory and wrapper; `governance.contract.yml`: declaration and manual audit; `development-skill.contract.yml`: eight infra skills with description/body freezes. Non-client adapters retain their original locations. Historical ADRs and evidence remain unchanged.
