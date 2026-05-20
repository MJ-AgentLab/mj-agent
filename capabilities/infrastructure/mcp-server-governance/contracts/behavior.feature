# capabilities/infrastructure/mcp-server-governance/contracts/behavior.feature
#
# 2 @risk:medium scenarios (REQ-001 / REQ-002). Per blueprint §3.3 (mcp-server-governance: 2 scenarios @risk:medium).

@adapter:claude-code-skill
Feature: MCP Server Inventory + Governance (A14 PR Gate + Wrapper Consistency)
  As an mj-agent operator
  I want any .mcp.json change to be reviewed against the A14 PR gate template
  and pg-* entries to be consistent in their wrapper script
  So that trust posture is audited at every change and pg connection logic
  stays centralized

  Background:
    Given .mcp.json declares exactly 13 server entries
    And 10 of those 13 entries are pg-* wrapper-based (5 mj-agent memory + 5 mj-system biz)
    And the A14 PR gate template lives at `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md §4`

  # ---------- REQ-001 — 14th server triggers A14 gate ----------

  @REQ-001 @CTR-mcp-server @risk:medium @adapter:claude-code-skill @meta-gate:A14
  Scenario: Adding a 14th MCP server triggers A14 PR gate body declaration
    Given a PR is submitted that adds a 14th entry to .mcp.json (e.g. a hypothetical "redis-server" MCP)
    When the reviewer parses the PR body
    Then the body MUST contain a "MCP Server Governance (A14)" block
    And the block lists the new entry with trust_posture + credential_mode + rationale
    And a PR that lacks this block fails A14 gate review (Phase M3+ blocking; warning at M1)

  # ---------- REQ-002 — All pg-* entries route through same wrapper ----------

  @REQ-002 @CTR-mcp-server @risk:medium @adapter:claude-code-skill
  Scenario: All 10 pg-* entries reference the same wrapper script
    Given .mcp.json is loaded
    When the wrapper-script reference is inspected for each pg-* server entry
    Then all 10 pg-* entries reference `.claude\scripts\pg-server-start.cmd`
    And any entry referencing a different wrapper (e.g. directly invoking npx for a different pg MCP)
    triggers the A14 "credential mode changed" sub-check (PR body MUST justify why per-entry deviation is needed)

# Gherkin tag convention:
#   @REQ-NNN @CTR-mcp-server @risk:medium @adapter:claude-code-skill @meta-gate:A14
# Step definitions: Phase M3 lands tests/bdd/infrastructure/mcp_governance/steps/.
# Phase M1 informational only; Phase M2 warning via check_a14_gate.py; Phase M3 blocking.
