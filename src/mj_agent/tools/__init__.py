"""LangChain-compatible tools exposed to the agent."""

from collections.abc import Callable
from typing import Any

from mj_agent.entity.tools import entity_lookup
from mj_agent.tools.analysis import (
    aggregate,
    compare_periods,
    detect_anomaly,
    drill_down,
    estimate_tokens,
)
from mj_agent.tools.biz_context import find_biz_context
from mj_agent.tools.sql.execute import execute_sql
from mj_agent.tools.sql.introspect import describe_biz_table, list_biz_tables

ALL_TOOLS: list[Callable[..., Any]] = [
    # Catalog recall + entity resolution (call before writing SQL)
    find_biz_context,
    entity_lookup,
    # SQL plan + execute
    list_biz_tables,
    describe_biz_table,
    execute_sql,
    # Phase 1 sub 1.B: ADR-012 row-set post-processors
    estimate_tokens,
    aggregate,
    drill_down,
    compare_periods,
    detect_anomaly,
]

__all__ = [
    "ALL_TOOLS",
    "aggregate",
    "compare_periods",
    "describe_biz_table",
    "detect_anomaly",
    "drill_down",
    "entity_lookup",
    "estimate_tokens",
    "execute_sql",
    "find_biz_context",
    "list_biz_tables",
]
