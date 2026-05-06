"""LangChain-compatible tools exposed to the agent."""

from collections.abc import Callable
from typing import Any

from mj_agent.tools.biz_context import find_biz_context
from mj_agent.tools.sql.execute import execute_sql
from mj_agent.tools.sql.introspect import describe_biz_table, list_biz_tables

ALL_TOOLS: list[Callable[..., Any]] = [
    find_biz_context,
    list_biz_tables,
    describe_biz_table,
    execute_sql,
]

__all__ = [
    "ALL_TOOLS",
    "describe_biz_table",
    "execute_sql",
    "find_biz_context",
    "list_biz_tables",
]
