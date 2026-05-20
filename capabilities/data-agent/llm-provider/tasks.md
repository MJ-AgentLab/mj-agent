---
type: capability-tasks
capability: data-agent.llm-provider
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Tasks: LLM Provider Abstraction

> Phase M1 baseline. **Zero existing unit tests** — all REQ tasks reference TBD-M3 test paths.

## Backlog

### T-001 — Phase M1 capability artifact suite
- **Phase**：M1 / **Priority**：critical (meta) / **Linked REQ**：N/A
- **Status**：in-progress (this PR)

### T-002 — REQ-001 ark provider behavior
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：high / **Linked REQ**：REQ-001
- **Contract changed?**：no (frozen anchor; ADR-027 stable)
- **HITL trigger**：none for documentation; modifying llm.py ark branch does NOT trigger 4 项必停 but cross-cap impact on docker-compose env vars
- **Status**：done (M1 contract); TBD-M3 all tests
- **TDD test_list**：
  - **TBD-M3** `tests/unit/test_llm.py::test_ark_missing_creds_raises_llm_config_error` — monkeypatch settings.ark_api_key + llm_api_key to empty; assert LLMConfigError raised with ARK_API_KEY mention
  - **TBD-M3** `tests/unit/test_llm.py::test_ark_constructs_chatopenai_with_thinking_param` — set ARK_API_KEY; assert returned instance has extra_body.thinking.type
  - **TBD-M3** `tests/unit/test_llm.py::test_ark_prefers_llm_api_key_over_legacy` — set both; assert llm_api_key wins

### T-003 — REQ-002 local-openai-compat provider behavior
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：high / **Linked REQ**：REQ-002
- **Contract changed?**：no
- **HITL trigger**：none for documentation
- **Status**：done (M1 contract); TBD-M3 all tests
- **TDD test_list**：
  - **TBD-M3** `tests/unit/test_llm.py::test_local_openai_compat_no_thinking_param` — set LLM_PROVIDER=local-openai-compat + LLM_BASE_URL; assert returned instance.extra_body has no "thinking" key
  - **TBD-M3** `tests/unit/test_llm.py::test_local_missing_base_url_raises` — empty LLM_BASE_URL; assert LLMConfigError mentions LLM_BASE_URL + vLLM example
  - **TBD-M3** `tests/unit/test_llm.py::test_local_uses_empty_sentinel_for_empty_api_key` — empty LLM_API_KEY; assert instance.api_key.get_secret_value() == "EMPTY"

### T-004 — REQ-003 provider switch + config schema + CLI awareness
- **Phase**：M1 (contract) / M3 (tests)
- **Priority**：high / **Linked REQ**：REQ-003
- **Contract changed?**：no
- **HITL trigger**：none
- **Status**：done (M1 contract); TBD-M3 all tests
- **TDD test_list**：
  - **TBD-M3** `tests/unit/test_config_llm_fields.py::test_effective_api_key_returns_empty_sentinel_for_local` — settings.llm_provider=local + empty llm_api_key; assert effective_llm_api_key returns "EMPTY"
  - **TBD-M3** `tests/unit/test_config_llm_fields.py::test_effective_base_url_ark_fallback` — settings.llm_provider=ark + empty llm_base_url; assert effective_llm_base_url == ark_base_url
  - **TBD-M3** `tests/unit/test_config_llm_fields.py::test_settings_rejects_invalid_provider_value` — set LLM_PROVIDER=invalid; assert pydantic ValidationError at Settings construction
  - **TBD-M3** `tests/unit/test_cli_check_provider_aware.py::test_check_ark_missing_key_failure_message` — invoke check via Typer test client; provider=ark, no key; assert failure msg
  - **TBD-M3** `tests/unit/test_cli_check_provider_aware.py::test_check_local_missing_url_failure_message` — provider=local, no url; assert failure msg + vLLM example
  - **TBD-M3** `tests/unit/test_cli_check_provider_aware.py::test_check_success_output_includes_provider_and_endpoint` — both creds set; assert "llm provider = <name> (endpoint=<url>)" in stdout

### T-005 — Cross-capability documentation: LLM env vars in docker-compose
- **Phase**：M2+ (cross-capability evolve)
- **Priority**：medium
- **Linked REQ**：REQ-003
- **HITL trigger**：cross-capability — sync env var declaration between llm-provider contract and docker-compose contract
- **Status**：TBD
- **Description**：Ensure docker-compose.*.yml `env_file: ../../.env` LLM-related vars (LLM_PROVIDER / LLM_BASE_URL / LLM_API_KEY / ARK_API_KEY) match this capability's contract. Phase M2+ cross-cap evolve.

## In-Progress
(none beyond T-001)

## Anti-Backlog
- **Add 3rd provider (e.g. Anthropic, Gemini)** — out of scope for M1; would require new ADR + plugin-style refactor (per design §4 tradeoff B).
- **Endpoint reachability monitoring** — owned by `/mj-agent-infra-llm-endpoint-probe` skill, not this capability.
- **Eager validation at Settings construction** — rejected per design §4 tradeoff D (breaks test fixtures).

---

> Phase M1 baseline. 0 existing unit tests; **12 TBD-M3 test entries** across REQ-001/002/003.
> This is the biggest test gap among 5 pilots — Phase M3 will create 3 new test files.
