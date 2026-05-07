"""LangChain-compatible wrapper around ``find_biz_context``.

Exposed to the agent as a tool so the LLM can call
``find_biz_context(question="<analyst question>")`` before reaching for
``list_biz_tables`` or ``describe_biz_table``.
"""

from __future__ import annotations

from typing import Any

from mj_agent.biz_catalog import find_biz_context as _find


def find_biz_context(question: str) -> dict[str, Any]:
    """Return the QCM catalog slice relevant to ``question``.

    Call this **first** when the analyst asks a metric question — it
    surfaces candidate metrics, periods, dimensions, time columns,
    period-over-period column patterns, signal tables, and dimension
    join keys, plus best-guess fact table names. Use the result to
    pick targeted tables for ``describe_biz_table``.

    Args:
        question: the analyst's natural-language question.

    Returns:
        A dict; see ``mj_agent.biz_catalog.finder.find_biz_context`` for
        the full schema. Always returns a non-empty dict — when keywords
        do not match, sensible defaults are returned (with rationale in
        ``notes``).
    """
    return _find(question)
