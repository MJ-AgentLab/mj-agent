"""Top-level agent graph — LangGraph Studio entry point.

Kept deliberately thin. All intelligence lives in the system prompt and
the skills it loads; runtime behavior is pure LangChain 1.x `create_agent`.

The graph is built lazily via ``make_graph()`` so that simply importing
this module does not force LLM provider instantiation — matters for
tests, type-checking, and environments where the LLM endpoint is not
yet reachable.
"""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

from mj_agent.llm import make_llm
from mj_agent.prompts import load_prompt
from mj_agent.skills import load_skill
from mj_agent.tools import ALL_TOOLS

_ACTIVE_SKILLS: tuple[str, ...] = (
    "biz-domain-context",
    "qcm-analysis",
    "safe-sql-analysis",
)


def _build_system_prompt() -> str:
    """Compose the system prompt from the base identity + active skills.

    MVP PR3 splits the legacy ``query-writing`` monolith into three
    cooperating skills, statically loaded in order:

      1. ``biz-domain-context`` — catalog recall via find_biz_context
      2. ``qcm-analysis`` — QCM-domain SQL templates + curated examples
      3. ``safe-sql-analysis`` — write/execute/interpret discipline

    A dynamic selector (ADR-003 progressive disclosure) is deferred; if
    token budget pressure surfaces, swap this with a selector that picks
    1-2 skills per turn.
    """
    parts = [load_prompt("system"), *(load_skill(name) for name in _ACTIVE_SKILLS)]
    return "\n\n".join(parts)


def make_graph(checkpointer: Any | None = None) -> Any:
    """Build and return the compiled LangGraph agent.

    Args:
        checkpointer: optional ``BaseCheckpointSaver`` for thread persistence
            (used by the Chainlit UI in Phase 1; left ``None`` for Studio
            and unit tests so no DB is required at import time).

    ``make_llm()`` raises ``LLMConfigError`` if ``ARK_API_KEY`` is missing,
    so this call site naturally fails fast on misconfiguration.
    """
    kwargs: dict[str, Any] = {
        "model": make_llm(),
        "tools": ALL_TOOLS,
        "system_prompt": _build_system_prompt(),
    }
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
    return create_agent(**kwargs)
