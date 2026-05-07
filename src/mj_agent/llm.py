"""LLM provider factory.

mj-agent talks to a single external provider — Volcengine Ark's OpenAI-
compatible Chat Completions endpoint — with DeepSeek V3 as the default
model. The factory isolates `ChatOpenAI` construction details from
`agent.py` so provider-specific knobs (base_url, `extra_body.thinking`,
timeouts) stay in one place.

If new providers are ever added, branch here — do NOT leak provider
selection logic into `agent.py` or callers.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from mj_agent.config import settings


class LLMConfigError(RuntimeError):
    """Raised when required LLM credentials are missing."""


def make_llm() -> BaseChatModel:
    """Construct the single supported chat model.

    Raises:
        LLMConfigError: ARK_API_KEY is not configured. The agent cannot
            start without it — there is no silent fallback.
    """
    api_key = settings.ark_api_key.get_secret_value()
    if not api_key:
        raise LLMConfigError(
            "ARK_API_KEY is not set. Put it in .env (or have setup-env.ps1 "
            "inject it from config/secrets.enc)."
        )

    thinking_mode = "enabled" if settings.llm_thinking_enabled else "disabled"

    return ChatOpenAI(
        model=settings.llm_model_id,
        api_key=settings.ark_api_key,
        base_url=settings.ark_base_url,
        timeout=settings.llm_timeout_sec,
        max_retries=2,
        temperature=0.7,
        extra_body={"thinking": {"type": thinking_mode}},
    )
