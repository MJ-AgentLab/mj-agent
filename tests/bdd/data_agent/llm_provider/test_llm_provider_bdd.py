"""BDD step definitions for data-agent.llm-provider capability.

Binds all 3 scenarios from
`capabilities/data-agent/llm-provider/contracts/behavior.feature`:

- REQ-001 (OFFLINE) — ark provider raises LLMConfigError on empty creds
- REQ-002 (OFFLINE) — local-openai-compat constructs ChatOpenAI without `extra_body.thinking`
- REQ-003 (OFFLINE) — effective_llm_api_key returns "EMPTY" for local with empty key

All 3 are OFFLINE (config-only, no external LLM endpoint contacted).
Pattern: use monkeypatch.setenv + fresh Settings() instance + override
mj_agent.config.settings + mj_agent.llm.settings to isolate scenario state.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

_FEATURE_FILE = "../../../../capabilities/data-agent/llm-provider/contracts/behavior.feature"


# -------- Background --------

@given(parsers.re(re.escape(
    "mj-agent supports two providers per ADR-027: ark (default) + local-openai-compat"
)))
def two_providers() -> None:
    """Background — ADR-027 declares the dual-provider design."""


@given(parsers.re(re.escape(
    'LLM_PROVIDER env defaults to "ark" when unset'
)))
def llm_provider_defaults_to_ark() -> None:
    """Background — verified by config.py Settings default."""


# -------- Scenarios --------


@scenario(_FEATURE_FILE, "Ark provider raises clear LLMConfigError when both ARK_API_KEY and LLM_API_KEY are empty")
def test_req_001_ark_empty_creds() -> None:
    pass


@scenario(_FEATURE_FILE, "Local provider constructs ChatOpenAI without extra_body.thinking")
def test_req_002_local_no_thinking() -> None:
    pass


@scenario(_FEATURE_FILE, "effective_llm_api_key returns \"EMPTY\" sentinel for local provider when LLM_API_KEY is empty")
def test_req_003_local_empty_sentinel() -> None:
    pass


# -------- Helper: fresh-settings injection --------


def _install_settings_with_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    provider: str,
    ark_api_key: str = "",
    llm_api_key: str = "",
    llm_base_url: str = "",
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
) -> Any:
    """Construct a fresh Settings with the desired env and replace the
    module-level singletons (mj_agent.config.settings + mj_agent.llm.settings).
    """
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("ARK_API_KEY", ark_api_key)
    monkeypatch.setenv("LLM_API_KEY", llm_api_key)
    monkeypatch.setenv("LLM_BASE_URL", llm_base_url)
    monkeypatch.setenv("ARK_BASE_URL", ark_base_url)
    from mj_agent.config import Settings
    fresh = Settings()  # type: ignore[call-arg]
    import mj_agent.config
    import mj_agent.llm
    monkeypatch.setattr(mj_agent.config, "settings", fresh)
    monkeypatch.setattr(mj_agent.llm, "settings", fresh)
    return fresh


# -------- REQ-001 step defs --------


@given(parsers.parse('LLM_PROVIDER is "{provider}" (default)'), target_fixture="provider_env")
def given_provider_ark(provider: str) -> str:
    return provider


@given(parsers.re(re.escape(
    "both ARK_API_KEY and LLM_API_KEY env vars are unset (or set to empty string)"
)))
def given_both_keys_empty(
    monkeypatch: pytest.MonkeyPatch, provider_env: str,
) -> None:
    _install_settings_with_env(monkeypatch, provider=provider_env)


@when("make_llm() is invoked", target_fixture="make_llm_outcome")
def when_make_llm_invoked(
    monkeypatch: pytest.MonkeyPatch,
    provider_env: str,
    request: pytest.FixtureRequest,
) -> dict[str, Any]:
    """Single @when for both REQ-001 (expected exception) and REQ-002
    (expected success). Reinstall settings using whatever fixtures the
    scenario has set up via earlier @given steps (base_url / api_key).
    """
    base_url = ""
    api_key = ""
    if "base_url" in request.fixturenames:
        base_url = request.getfixturevalue("base_url")
    if "api_key" in request.fixturenames:
        api_key = request.getfixturevalue("api_key")
    _install_settings_with_env(
        monkeypatch,
        provider=provider_env,
        llm_base_url=base_url,
        llm_api_key=api_key,
    )
    from mj_agent.llm import make_llm
    try:
        return {"instance": make_llm(), "exception": None}
    except BaseException as exc:  # noqa: BLE001
        return {"instance": None, "exception": exc}


@then("it raises LLMConfigError (subclass of RuntimeError)")
def then_llm_config_error(make_llm_outcome: dict[str, Any]) -> None:
    from mj_agent.llm import LLMConfigError
    exc = make_llm_outcome["exception"]
    assert exc is not None, "make_llm did not raise"
    assert isinstance(exc, LLMConfigError), (
        f"expected LLMConfigError, got {type(exc).__name__}: {exc}"
    )
    assert isinstance(exc, RuntimeError), (
        "LLMConfigError must be a RuntimeError subclass"
    )


@then(parsers.parse('the error message contains the string "{snippet}"'))
def then_error_message_contains(make_llm_outcome: dict[str, Any], snippet: str) -> None:
    exc = make_llm_outcome["exception"]
    assert exc is not None and snippet in str(exc), (
        f"expected {snippet!r} in exception message; got {exc!r}"
    )


@then("the error message contains a suggestion to run setup-env.ps1")
def then_error_suggests_setup_env(make_llm_outcome: dict[str, Any]) -> None:
    exc = make_llm_outcome["exception"]
    assert exc is not None and "setup-env.ps1" in str(exc)


@then("the error message mentions LLM_API_KEY as the new generic alternative")
def then_error_mentions_llm_api_key(make_llm_outcome: dict[str, Any]) -> None:
    exc = make_llm_outcome["exception"]
    assert exc is not None and "LLM_API_KEY" in str(exc)


# -------- REQ-002 step defs --------


@given(parsers.parse('LLM_PROVIDER is "{provider}"'), target_fixture="provider_env")
def given_provider_named(provider: str) -> str:
    return provider


@given(parsers.parse('LLM_BASE_URL is set to "{base_url}" (DGX-Spark vLLM)'),
       target_fixture="base_url")
def given_base_url(base_url: str) -> str:
    return base_url


@given(parsers.parse('LLM_API_KEY is set to "{api_key}"'), target_fixture="api_key")
def given_api_key(api_key: str) -> str:
    return api_key


@then("it returns a ChatOpenAI instance (no exception raised)")
def then_chat_openai_returned(make_llm_outcome: dict[str, Any]) -> None:
    from langchain_openai import ChatOpenAI
    assert make_llm_outcome["exception"] is None, (
        f"unexpected exception: {make_llm_outcome['exception']}"
    )
    assert isinstance(make_llm_outcome["instance"], ChatOpenAI)


@then(parsers.parse('the instance\'s extra_body does NOT contain the key "{key}"'))
def then_extra_body_does_not_contain(make_llm_outcome: dict[str, Any], key: str) -> None:
    instance = make_llm_outcome["instance"]
    extra = getattr(instance, "extra_body", None) or {}
    assert key not in extra, (
        f"local provider must not pass {key!r} in extra_body; got {extra!r}"
    )


@then(parsers.parse('the instance\'s base_url equals "{base_url}"'))
def then_base_url_equals(make_llm_outcome: dict[str, Any], base_url: str) -> None:
    instance = make_llm_outcome["instance"]
    actual = str(instance.openai_api_base or getattr(instance, "base_url", ""))
    assert actual == base_url, f"expected base_url {base_url!r}, got {actual!r}"


@then(parsers.parse('the instance\'s api_key SecretStr value equals "{api_key}"'))
def then_api_key_equals(make_llm_outcome: dict[str, Any], api_key: str) -> None:
    instance = make_llm_outcome["instance"]
    actual_secret = instance.openai_api_key
    actual = (
        actual_secret.get_secret_value()
        if hasattr(actual_secret, "get_secret_value")
        else str(actual_secret)
    )
    assert actual == api_key, f"expected api_key {api_key!r}, got {actual!r}"


# -------- REQ-003 step defs --------


@given("LLM_API_KEY is empty (unset or empty string)")
def given_llm_api_key_empty(
    monkeypatch: pytest.MonkeyPatch,
    provider_env: str,
) -> None:
    _install_settings_with_env(
        monkeypatch,
        provider=provider_env,
        llm_api_key="",
        llm_base_url="http://dummy-local-endpoint/v1",
    )


@when("settings.effective_llm_api_key is read", target_fixture="effective_key")
def when_read_effective_api_key() -> str:
    from mj_agent.config import settings
    return settings.effective_llm_api_key


@then(parsers.parse('it returns the literal string "{value}" (not None, not empty string)'))
def then_effective_key_equals(effective_key: str, value: str) -> None:
    assert effective_key == value, f"expected {value!r}, got {effective_key!r}"


@then(parsers.re(re.escape(
    'downstream ChatOpenAI construction does NOT raise its own '
    '"api_key client option must be set" error'
)))
def then_chat_openai_construction_does_not_raise(
    monkeypatch: pytest.MonkeyPatch, provider_env: str,
) -> None:
    _install_settings_with_env(
        monkeypatch,
        provider=provider_env,
        llm_api_key="",
        llm_base_url="http://dummy-local-endpoint/v1",
    )
    from mj_agent.llm import make_llm
    make_llm()  # should not raise; "EMPTY" sentinel satisfies langchain_openai


@then(parsers.re(re.escape(
    'mj-agent check (provider=local) succeeds on the api_key check '
    '(since "EMPTY" is non-empty)'
)))
def then_check_api_key_satisfied(effective_key: str) -> None:
    """`mj-agent check` reads `effective_llm_api_key`; "EMPTY" is truthy
    string so the check passes.
    """
    assert bool(effective_key), "effective_llm_api_key must be truthy"
