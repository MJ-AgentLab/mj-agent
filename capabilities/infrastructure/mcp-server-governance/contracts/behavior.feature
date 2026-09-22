@cap:infrastructure.mcp-server-governance @adapter:development-skill
Feature: Native project MCP governance
  # File-only assertions; actual Owner review and live services are not simulated.
  Background:
    Given native config declares only the eight retained project servers
    And the native A14 template defines trust and credential review

  @REQ-001 @CTR-mcp-server @risk:medium
  Scenario: Adding a new MCP server triggers A14 PR gate body declaration
    When the A14 declaration template is inspected
    Then trust posture, credential mode and rationale are required
    And actual Owner review remains required before changing native MCP

  @REQ-002 @CTR-mcp-server @risk:medium
  Scenario: All 5 memory pg entries reference the same native wrapper script
    When native wrapper references are inspected
    Then all five memory entries have canonical wrappers and env names
