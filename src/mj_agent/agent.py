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
from mj_agent.middleware import handle_sql_tool_errors
from mj_agent.prompts import load_prompt
from mj_agent.skills import load_skill
from mj_agent.tools import ALL_TOOLS

_ACTIVE_SKILLS: tuple[str, ...] = (
    # Recall + entity (前置)
    "biz-schema-exploration",
    "biz-domain-context",
    # Metric & query authoring (中段)
    "mj-ddd-semantics",
    "qcm-analysis",
    "query-writing",
    "monthly-report",
    # Execute / optimize / discipline (后段)
    "safe-sql-analysis",
    "query-optimization",
)


def _build_system_prompt() -> str:
    """Compose the system prompt from the base identity + active skills.

    Phase 1 sub 1.E rounds out the skill set to **8 active skills**
    organized in three bands:

      1. Recall & entity (前置):
         - ``biz-schema-exploration`` — meta-question routing
         - ``biz-domain-context``     — catalog recall via find_biz_context
      2. Metric & query authoring (中段):
         - ``mj-ddd-semantics``       — DDD layer; column choice
         - ``qcm-analysis``           — QCM 5 templates
         - ``query-writing``          — ad-hoc SQL outside QCM templates
                                        (revived v1.0; scope narrowed)
         - ``monthly-report``         — composite "monthly report" (E4)
      3. Execute / optimize / discipline (后段):
         - ``safe-sql-analysis``      — execute discipline
         - ``query-optimization``     — rewrite on timeout / truncated /
                                        budget overflow

    Token-budget watchpoint (plan §5 risk): 8 active skills bring the
    composed prompt close to ~8k tokens. Phase 1.5 / Phase 2 introduces
    a dynamic skill selector (ADR-003 progressive disclosure).
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
        "middleware": [handle_sql_tool_errors],
    }
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
    return create_agent(**kwargs)
