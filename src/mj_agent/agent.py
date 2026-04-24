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


def _build_system_prompt() -> str:
    """Compose the system prompt from the base identity + active skills.

    Phase 0 statically concatenates the active skills. Phase 1 will split
    this into a dynamic selector (ADR-003 progressive disclosure).
    """
    return "\n\n".join(
        [
            load_prompt("system"),
            load_skill("query-writing"),
        ]
    )


def make_graph() -> Any:
    """Build and return the compiled LangGraph agent.

    ``make_llm()`` raises ``LLMConfigError`` if ``ARK_API_KEY`` is missing,
    so this call site naturally fails fast on misconfiguration.
    """
    return create_agent(
        model=make_llm(),
        tools=ALL_TOOLS,
        system_prompt=_build_system_prompt(),
    )
