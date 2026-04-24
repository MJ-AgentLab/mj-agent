"""LangChain-compatible tools exposed to the agent."""

from collections.abc import Callable
from typing import Any

from mj_agent.tools.sql.execute import execute_sql
from mj_agent.tools.sql.introspect import describe_biz_table, list_biz_tables

ALL_TOOLS: list[Callable[..., Any]] = [execute_sql, list_biz_tables, describe_biz_table]

__all__ = ["ALL_TOOLS", "describe_biz_table", "execute_sql", "list_biz_tables"]
