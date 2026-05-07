"""Unit tests verifying analysis tools are wired into ``ALL_TOOLS``."""

from __future__ import annotations

from mj_agent.tools import ALL_TOOLS


def test_analysis_tools_in_all_tools() -> None:
    names = [t.__name__ for t in ALL_TOOLS]
    for expected in (
        "estimate_tokens",
        "aggregate",
        "drill_down",
        "compare_periods",
        "detect_anomaly",
    ):
        assert expected in names, f"{expected} missing from ALL_TOOLS"


def test_analysis_tools_after_sql_tools() -> None:
    """Catalog + SQL group is registered before analysis post-processors.

    Stable ordering matters because LangChain serializes the tool list in
    `ALL_TOOLS` order into the LLM's tool-choice prompt; we want
    `find_biz_context` / `execute_sql` to appear before the post-processors.
    """
    names = [t.__name__ for t in ALL_TOOLS]
    sql_idx = names.index("execute_sql")
    for tool_name in ("estimate_tokens", "aggregate", "drill_down"):
        assert names.index(tool_name) > sql_idx
