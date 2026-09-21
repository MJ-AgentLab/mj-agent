---
type: capability-runbook
capability: infrastructure.mcp-server-governance
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-23
last_verified: 2026-05-20
---

# Runbook: Native project MCP governance

## §1 Static startup prerequisites

Run `python scripts/sdd/check_codex_native.py --surface mcp` from the project root.
It checks the eight retained services, exact commands and by-name environment allowlists,
without reading secrets or starting services. STATIC_PASS is not a successful host load.
The config uses Windows launchers; other platforms need explicit validation, not assumed parity.

## §2 Credential and host setup

The Owner separately authorizes real credential setup. `scripts/mcp/setup-mcp-secrets.ps1`
accepts only GitHub's token name and the five memory URL names. The existing bundle may
contain other names; those are not imported. `-Reload` reports presence only, not service health.
Never log values. Application secrets remain separate. Project trust and hooks activation are
manual review steps; no project script edits personal config or activates hooks.

## §3 Failure handling

Missing/empty memory values fail startup without fallback URLs. Invalid native config,
unknown services and inline credentials fail the static check. Owner actions remain hard
blocked in the hook; an approved manual application route does not unlock it.
Return BLOCKED_EXECUTION_ROUTE when a requested automatic protected action cannot execute.
Do not switch tools, modes or encoding. Service health, background lifecycle and platform
credential checks retain NOT_TESTED until separately evidenced.

## §4 Related artifacts

`spec.yml`, `trace.yml`, `contracts/mcp-server.contract.yml`, `contracts/governance.contract.yml`,
`contracts/development-skill.contract.yml`, the two structural BDD scenarios and `scripts/mcp/`.
Quarterly trust review covers the retained eight entries. Historical baselines remain provenance.

## §5 Post-mortem triggers

Escalate silent trust expansion, missing A14 review, wrapper deviation, secret disclosure,
upstream compromise or quarterly audit lapse over two quarters. Retention remains permanent
under `policies/archive.md`. No new issue or external probe is automatic in this migration.
