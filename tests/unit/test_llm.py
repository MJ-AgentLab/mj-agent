"""make_llm() provider factory — offline unit tests (llm-provider REQ-001/002/003).

No network, no DB: ChatOpenAI construction is local; assertions read back the
constructed instance's extra_body / api_key / base_url. Settings are built
fresh per test from monkeypatched env (`_env_file=None` opts out of `.env`
discovery — same isolation contract as test_phase1_skeleton.py) and installed
on BOTH module-level singletons (mj_agent.config.settings + mj_agent.llm.settings),
mirroring tests/bdd/data_agent/llm_provider/_install_settings_with_env.
"""

from __future__ import annotations

import pytest

from mj_agent.config import Settings
from mj_agent.llm import LLMConfigError, make_llm


def _install_settings(
    monkeypatch: pytest.MonkeyPatch,
    *,
    provider: str,
    ark_api_key: str = "",
    llm_api_key: str = "",
    llm_base_url: str = "",
    thinking_enabled: bool | None = None,
) -> Settings:
    """Build a fresh Settings from explicit env and install it on the consumers."""
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("ARK_API_KEY", ark_api_key)
    monkeypatch.setenv("LLM_API_KEY", llm_api_key)
    monkeypatch.setenv("LLM_BASE_URL", llm_base_url)
    if thinking_enabled is not None:
        monkeypatch.setenv("LLM_THINKING_ENABLED", "true" if thinking_enabled else "false")
    fresh = Settings(_env_file=None)
    import mj_agent.config
    import mj_agent.llm
    monkeypatch.setattr(mj_agent.config, "settings", fresh)
    monkeypatch.setattr(mj_agent.llm, "settings", fresh)
    return fresh


# -------- REQ-001: ark provider --------


def test_ark_missing_creds_raises_llm_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """ark + both ARK_API_KEY / LLM_API_KEY empty → LLMConfigError with guidance."""
    _install_settings(monkeypatch, provider="ark")
    with pytest.raises(LLMConfigError) as excinfo:
        make_llm()
    message = str(excinfo.value)
    assert "ARK_API_KEY" in message
    assert "setup-env.ps1" in message
    assert "LLM_API_KEY" in message


@pytest.mark.parametrize(
    ("thinking_enabled", "expected_type"),
    [(True, "enabled"), (False, "disabled")],
)
def test_ark_thinking_flag_shapes_extra_body(
    monkeypatch: pytest.MonkeyPatch,
    thinking_enabled: bool,
    expected_type: str,
) -> None:
    """LLM_THINKING_ENABLED drives extra_body.thinking.type (DeepSeek knob, ADR-027)."""
    _install_settings(
        monkeypatch,
        provider="ark",
        ark_api_key="test-ark-key",
        thinking_enabled=thinking_enabled,
    )
    instance = make_llm()
    assert instance.extra_body == {"thinking": {"type": expected_type}}


def test_ark_falls_back_to_llm_api_key_when_ark_key_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ark with only the new generic LLM_API_KEY set still constructs (back-compat)."""
    _install_settings(monkeypatch, provider="ark", llm_api_key="generic-key")
    instance = make_llm()
    secret = instance.openai_api_key
    assert secret is not None
    assert secret.get_secret_value() == "generic-key"


# -------- REQ-002: local-openai-compat provider --------


def test_local_constructs_without_extra_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """local provider must NOT pass Ark's extra_body.thinking (vLLM/SGLang would 422)."""
    _install_settings(
        monkeypatch,
        provider="local-openai-compat",
        llm_api_key="dgx-test-key",
        llm_base_url="http://192.168.0.189:8000/v1",
    )
    instance = make_llm()
    extra = instance.extra_body or {}
    assert "thinking" not in extra
    assert str(instance.openai_api_base) == "http://192.168.0.189:8000/v1"


def test_local_missing_base_url_raises_llm_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """local provider without LLM_BASE_URL → LLMConfigError naming the missing var."""
    _install_settings(monkeypatch, provider="local-openai-compat", llm_api_key="k")
    with pytest.raises(LLMConfigError) as excinfo:
        make_llm()
    assert "LLM_BASE_URL" in str(excinfo.value)


def test_local_empty_api_key_constructs_via_empty_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """local provider with empty LLM_API_KEY constructs without raising.

    Mirrors the REQ-003 BDD step `then_chat_openai_construction_does_not_raise`:
    unauthenticated vLLM/Ollama endpoints are a supported deployment shape.
    """
    _install_settings(
        monkeypatch,
        provider="local-openai-compat",
        llm_base_url="http://dummy-local-endpoint/v1",
    )
    instance = make_llm()
    assert instance is not None


# -------- REQ-003: provider switch / "EMPTY" sentinel --------


def test_local_effective_api_key_empty_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """effective_llm_api_key returns the literal "EMPTY" sentinel for local + no key."""
    fresh = _install_settings(
        monkeypatch,
        provider="local-openai-compat",
        llm_base_url="http://dummy-local-endpoint/v1",
    )
    assert fresh.effective_llm_api_key == "EMPTY"
