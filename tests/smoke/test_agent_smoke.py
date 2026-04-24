"""Smoke tests — agent + live biz + live LLM, end to end.

Run with: ``uv run pytest tests/smoke -m smoke``. Gated by the live_db
fixture (credentials present) and by an LLM provider being reachable.

Phase 0 ships smoke #1 only; cases #2–#6 land in later PRs per the plan.
"""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.usefixtures("live_db")]


def _tool_calls(messages: list[Any]) -> list[str]:
    """Flatten names of every tool called anywhere in the message stream."""
    names: list[str] = []
    for msg in messages:
        calls = getattr(msg, "tool_calls", None) or []
        for call in calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                names.append(name)
    return names


def test_smoke_01_list_biz_tables(agent: Any) -> None:
    """#1: introspection path — 'what tables exist in biz_dws'."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "biz_dws 里有哪些日度总量表？"}]}
    )
    messages = result["messages"]
    called = _tool_calls(messages)
    assert "list_biz_tables" in called, f"agent did not call list_biz_tables (called: {called})"

    # Final assistant content should reference at least one real table name.
    final = messages[-1]
    final_text = getattr(final, "content", "") or ""
    if isinstance(final_text, list):
        final_text = " ".join(
            part.get("text", "") for part in final_text if isinstance(part, dict)
        )
    assert "dws_qcm" in final_text or "daily_total" in final_text
