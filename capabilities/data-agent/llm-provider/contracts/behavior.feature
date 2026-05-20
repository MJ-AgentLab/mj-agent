# capabilities/data-agent/llm-provider/contracts/behavior.feature
#
# 3 @risk:high scenarios (REQ-001 / REQ-002 / REQ-003).
# All 3 scenarios drive NEW test code in Phase M3 (zero existing unit tests; survey §B.4).

@adapter:python
Feature: LLM Provider Abstraction
  As an mj-agent operator
  I want LLM_PROVIDER switching between Ark (default cloud) and DGX-Spark (local-openai-compat)
  to be configuration-driven, with provider-specific credential validation and
  no leakage of Ark-private params (extra_body.thinking) to local endpoints
  So that I can switch providers for data-sensitive scenarios without touching
  code, and so that local endpoints don't 422 on Ark's private params

  Background:
    Given mj-agent supports two providers per ADR-027: ark (default) + local-openai-compat
    And LLM_PROVIDER env defaults to "ark" when unset

  # ---------- REQ-001 — ark provider ----------

  @REQ-001 @CTR-provider @risk:high @adapter:python @adr:ADR-027
  Scenario: Ark provider raises clear LLMConfigError when both ARK_API_KEY and LLM_API_KEY are empty
    Given LLM_PROVIDER is "ark" (default)
    And both ARK_API_KEY and LLM_API_KEY env vars are unset (or set to empty string)
    When make_llm() is invoked
    Then it raises LLMConfigError (subclass of RuntimeError)
    And the error message contains the string "ARK_API_KEY"
    And the error message contains a suggestion to run setup-env.ps1
    And the error message mentions LLM_API_KEY as the new generic alternative

  # ---------- REQ-002 — local-openai-compat provider ----------

  @REQ-002 @CTR-provider @risk:high @adapter:python @adr:ADR-027
  Scenario: Local provider constructs ChatOpenAI without extra_body.thinking
    Given LLM_PROVIDER is "local-openai-compat"
    And LLM_BASE_URL is set to "http://192.168.0.189:8000/v1" (DGX-Spark vLLM)
    And LLM_API_KEY is set to "dgx-test-key"
    When make_llm() is invoked
    Then it returns a ChatOpenAI instance (no exception raised)
    And the instance's extra_body does NOT contain the key "thinking"
    And the instance's base_url equals "http://192.168.0.189:8000/v1"
    And the instance's api_key SecretStr value equals "dgx-test-key"

  # ---------- REQ-003 — provider switch + config schema + CLI awareness ----------

  @REQ-003 @CTR-provider @risk:high @adapter:python
  Scenario: effective_llm_api_key returns "EMPTY" sentinel for local provider when LLM_API_KEY is empty
    Given LLM_PROVIDER is "local-openai-compat"
    And LLM_API_KEY is empty (unset or empty string)
    When settings.effective_llm_api_key is read
    Then it returns the literal string "EMPTY" (not None, not empty string)
    And downstream ChatOpenAI construction does NOT raise its own "api_key client option must be set" error
    And mj-agent check (provider=local) succeeds on the api_key check (since "EMPTY" is non-empty)

# Gherkin tag convention:
#   @REQ-NNN @CTR-provider @risk:high @adapter:python @adr:ADR-027
# Step definitions: Phase M3 lands tests/bdd/data_agent/llm_provider/steps/.
# Existing automation: NONE — survey §B.4 confirmed zero unit tests touch make_llm / LLMConfigError / effective_*.
