"""LLM provider factory.

mj-agent supports two providers (selected by `LLM_PROVIDER` env, ADR-027):

- **ark** (default) — Volcengine Ark's OpenAI-compatible Chat Completions
  endpoint, DeepSeek V3 model, with `extra_body.thinking` knob driven by
  `LLM_THINKING_ENABLED`. Credentials read from `ARK_API_KEY` (or new
  generic `LLM_API_KEY` if set; back-compat preserved).
- **local-openai-compat** — any OpenAI-compatible local endpoint hosted on
  DGX-Spark (vLLM / SGLang / Ollama / TGI / llama.cpp). Reads the new
  generic `LLM_BASE_URL` + `LLM_API_KEY` (often "EMPTY" for unauthenticated
  vLLM). **No `extra_body.thinking`** — vLLM/SGLang/Ollama do not accept
  Ark's DeepSeek-private parameter and will raise.

The factory keeps `ChatOpenAI` construction details out of `agent.py` so
provider-specific knobs stay in one place. Adding a new provider = adding
a branch here, never threading provider selection through callers.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from mj_agent.config import settings


class LLMConfigError(RuntimeError):
    """Raised when required LLM credentials are missing."""


def make_llm() -> BaseChatModel:
    """Construct a chat model based on `settings.llm_provider`.

    Raises:
        LLMConfigError: required credentials are missing for the selected
            provider. `ark` requires `ARK_API_KEY` (or `LLM_API_KEY`).
            `local-openai-compat` requires `LLM_BASE_URL`. The agent
            cannot start without these — there is no silent fallback.
    """
    provider = settings.llm_provider

    if provider == "ark":
        api_key_str = settings.effective_llm_api_key
        if not api_key_str:
            raise LLMConfigError(
                "ARK_API_KEY is not set. Put it in .env (or have "
                "setup-env.ps1 inject it from config/secrets.enc). "
                "Alternatively set LLM_API_KEY for the new generic name."
            )
        thinking_mode = "enabled" if settings.llm_thinking_enabled else "disabled"
        # Pass the SecretStr directly when available (back-compat); falls
        # back to the new generic field otherwise.
        api_key_obj = (
            settings.ark_api_key
            if settings.ark_api_key.get_secret_value()
            else settings.llm_api_key
        )
        return ChatOpenAI(
            model=settings.llm_model_id,
            api_key=api_key_obj,
            base_url=settings.effective_llm_base_url,
            timeout=settings.llm_timeout_sec,
            max_retries=2,
            temperature=0.7,
            extra_body={"thinking": {"type": thinking_mode}},
        )

    # provider == "local-openai-compat"
    base_url = settings.effective_llm_base_url
    if not base_url:
        raise LLMConfigError(
            "LLM_BASE_URL is not set. For DGX-Spark deployment, point at "
            "the local inference endpoint, e.g. "
            "http://192.168.0.189:8000/v1 (vLLM with --port 8000) or "
            "http://192.168.0.189:11434/v1 (Ollama with OPENAI_API_BASE)."
        )
    return ChatOpenAI(
        model=settings.llm_model_id,
        api_key=settings.llm_api_key,
        base_url=base_url,
        timeout=settings.llm_timeout_sec,
        max_retries=2,
        temperature=0.7,
        # NO extra_body: vLLM/SGLang/Ollama do not accept Ark's `thinking`
        # parameter and will raise on it.
    )
