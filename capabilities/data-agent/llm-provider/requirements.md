---
type: capability-requirements
capability: data-agent.llm-provider
state: drafting
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
---

# Requirements: LLM Provider Abstraction

> Phase M1 baseline. 3 REQs (all @risk:high). Per ADR-027. Survey §B. **Zero existing unit tests** — all M3+ TBD.

## REQ-001 — ark provider (default; back-compat with legacy ARK_* env vars)

**Priority**：high

**Statement**：When `LLM_PROVIDER=ark` (default), `make_llm()` SHALL construct `ChatOpenAI` with `extra_body.thinking.type` set from `LLM_THINKING_ENABLED`; SHALL prefer `llm_api_key` over legacy `ark_api_key`; SHALL raise `LLMConfigError` if neither is set.

**Rationale**：Default provider for Volcengine Ark + DeepSeek V3. The `thinking` param is Ark-specific (DeepSeek V3 chain-of-thought toggle). Back-compat with legacy `ARK_BASE_URL` / `ARK_API_KEY` env vars preserved via fallback chain.

**Acceptance**：

- `make_llm()` reads `settings.llm_provider`; if "ark", enters ark branch
- API key derivation: `effective_llm_api_key` = `llm_api_key` (new generic) if non-empty, else `ark_api_key` (legacy)
- Base URL derivation: `effective_llm_base_url` = `llm_base_url` if set, else `ark_base_url` (default `https://ark.cn-beijing.volces.com/api/v3`)
- ChatOpenAI constructor args:
  - `model=settings.llm_model_id` (default `deepseek-v3-2-251201`)
  - `api_key=<SecretStr from effective_llm_api_key derivation>`
  - `base_url=<effective_llm_base_url>`
  - `timeout=settings.llm_timeout_sec` (default 120)
  - `max_retries=2`
  - `temperature=0.7`
  - `extra_body={"thinking": {"type": <"enabled"|"disabled">}}` — type from `LLM_THINKING_ENABLED`
- `LLMConfigError` raise when `effective_llm_api_key` empty: message must mention `ARK_API_KEY` + suggest `setup-env.ps1` + mention `LLM_API_KEY` generic fallback

**BDD Examples**：

- **Given** `LLM_PROVIDER=ark` and both `ARK_API_KEY` and `LLM_API_KEY` are unset / empty
- **When** `make_llm()` is invoked
- **Then** `LLMConfigError` raised; message names `ARK_API_KEY` + suggests `setup-env.ps1` + mentions `LLM_API_KEY` fallback

**Trace**：REQ-001 → `contracts/provider.contract.yml` (ark branch) + `contracts/python.contract.yml` (make_llm signature) + `behavior.feature` Scenario 1 + **TBD-M3** `tests/unit/test_llm.py::test_ark_missing_creds_raises_llm_config_error`

---

## REQ-002 — local-openai-compat provider (DGX-Spark vLLM/SGLang/Ollama)

**Priority**：high

**Statement**：When `LLM_PROVIDER=local-openai-compat`, `make_llm()` SHALL construct `ChatOpenAI` WITHOUT `extra_body.thinking`; SHALL substitute literal `"EMPTY"` for missing `llm_api_key`; SHALL raise `LLMConfigError` if `llm_base_url` is not set.

**Rationale**：DGX-Spark (192.168.0.189) hosts vLLM/SGLang/Ollama OpenAI-compatible endpoints. These do NOT accept Ark's private `extra_body.thinking` (would 422). `"EMPTY"` is the vLLM/Ollama-recognized sentinel for "no api key required" — empty string would cause ChatOpenAI's own `api_key client option must be set` error.

**Acceptance**：

- `make_llm()` reads `settings.llm_provider`; if "local-openai-compat", enters local branch
- API key derivation: `effective_llm_api_key` = `llm_api_key` if non-empty, else literal `"EMPTY"` sentinel
- Base URL derivation: `effective_llm_base_url` = `llm_base_url` (required; **NO** ark fallback)
- ChatOpenAI constructor args:
  - `model=settings.llm_model_id`
  - `api_key=<SecretStr from llm_api_key or 'EMPTY' sentinel>`
  - `base_url=<llm_base_url>`
  - `timeout=settings.llm_timeout_sec`
  - `max_retries=2`
  - `temperature=0.7`
  - **NO `extra_body`** (deliberate; vLLM/SGLang/Ollama compatibility)
- `LLMConfigError` raise when `llm_base_url` empty: message includes example endpoints (vLLM port 8000, Ollama port 11434)

**BDD Examples**：

- **Given** `LLM_PROVIDER=local-openai-compat` and `LLM_BASE_URL=http://192.168.0.189:8000/v1`
- **When** `make_llm()` is invoked
- **Then** returned `ChatOpenAI` instance has no `thinking` key under `extra_body` (vLLM/SGLang/Ollama compatibility)

**Trace**：REQ-002 → `contracts/provider.contract.yml` (local-openai-compat branch) + `contracts/python.contract.yml` + `behavior.feature` Scenario 2 + **TBD-M3** `tests/unit/test_llm.py::test_local_openai_compat_no_thinking_param`

---

## REQ-003 — provider switch + config schema validation + CLI awareness

**Priority**：high

**Statement**：Settings SHALL accept only `LLM_PROVIDER ∈ {ark, local-openai-compat}`; `effective_llm_base_url` + `effective_llm_api_key` SHALL implement provider-specific fallback chains; `mj-agent check` SHALL emit `llm provider = <name> (endpoint=<url>)` on success and provider-specific failure message on missing creds.

**Rationale**：Provider switch should be a single env var change (no code path branching at the call site). Settings-level validation (pydantic) catches typos at boot time (LLMConfigError lazy validation deferred to make_llm call time per ADR-027). CLI healthcheck must be provider-aware so operators get actionable error messages.

**Acceptance**：

- `settings.llm_provider: Literal["ark", "local-openai-compat"]` — any other value raises pydantic ValidationError at Settings construction time
- `effective_llm_base_url` cached_property:
  - ark provider → `llm_base_url or ark_base_url`
  - local provider → `llm_base_url` (empty stays empty; make_llm raises LLMConfigError)
- `effective_llm_api_key` cached_property:
  - ark provider → `llm_api_key.get_secret_value() or ark_api_key.get_secret_value()`
  - local provider → `llm_api_key.get_secret_value() or "EMPTY"` sentinel
- `mj-agent check` (cli.py) provider-aware:
  - ark missing key: failures.append `"ARK_API_KEY not set"`
  - local missing base url: failures.append `"LLM_BASE_URL not set (required when ...; e.g. http://192.168.0.189:8000/v1 for DGX vLLM)"`
  - success output: `llm provider = <name> (endpoint=<url>)`
- `mj-agent check` NEVER calls `make_llm()` directly (no LLM endpoint contact); endpoint reachability delegated to `/mj-agent-infra-llm-endpoint-probe` skill

**BDD Examples**：

- **Given** `LLM_PROVIDER=local-openai-compat` and `LLM_API_KEY` empty
- **When** `settings.effective_llm_api_key` is read
- **Then** it returns literal string `"EMPTY"` (NOT empty string) so downstream ChatOpenAI does not raise its own `api_key client option must be set` error

**Trace**：REQ-003 → `contracts/provider.contract.yml` (effective_* helpers) + `contracts/python.contract.yml` + `behavior.feature` Scenario 3 + **TBD-M3** `tests/unit/test_config_llm_fields.py::test_effective_api_key_returns_empty_sentinel_for_local_provider`

---

> Phase M1 baseline. 0 existing unit tests for `make_llm` / `LLMConfigError` / `effective_*` helpers
> (per survey §B.4). Every BDD scenario will drive NEW test code in Phase M3 — explicit gap.
