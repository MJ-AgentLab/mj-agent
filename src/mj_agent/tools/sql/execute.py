"""Execute a read-only SQL against the mj-system biz domain.

Exposed as a LangChain tool via its type hints and docstring — no @tool
decorator required; LangChain 1.x introspects these signatures directly.
"""

from __future__ import annotations

from typing import Any

from mj_agent.config import settings
from mj_agent.integrations.mj_system_db import readonly_cursor
from mj_agent.tools.sql.guardrail import is_safe_select


def execute_sql(sql: str) -> dict[str, Any]:
    """Run a read-only SELECT against the biz domain and return rows as JSON.

    Only SELECT (or WITH ... SELECT) statements are allowed. All table
    references MUST be schema-qualified; currently accepted schemas are
    `biz_dws` (all tables) and `biz_dwd` (dimension tables only —
    `dwd_dim_product_interface`, `dwd_dim_institution`; other biz_dwd
    tables are denied by the database).

    Args:
        sql: the SQL statement. Single statement only. Trailing `;` optional.

    Returns:
        A dict with keys:
          - columns (list[str]): column names in result order
          - rows (list[dict]): up to SQL_MAX_ROWS rows; each row is a
            {column_name: value} mapping
          - row_count (int): number of rows returned (<= SQL_MAX_ROWS)
          - truncated (bool): True if the result was capped at SQL_MAX_ROWS

    Raises:
        ValueError: the guardrail rejected the SQL (unsafe pattern).
        RuntimeError: the database returned an error (timeout, syntax,
            permission denied, etc.).
    """
    ok, reason = is_safe_select(
        sql,
        settings.biz_allowed_schemas,
        allowed_tables_per_schema={"biz_dwd": settings.biz_allowed_dwd_tables},
    )
    if not ok:
        raise ValueError(f"SQL rejected by guardrail: {reason}")

    try:
        with readonly_cursor() as cur:
            cur.execute(sql)
            columns = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchmany(settings.sql_max_rows + 1)
    except Exception as exc:  # noqa: BLE001 — surface DB errors verbatim
        raise RuntimeError(f"database error: {exc}") from exc

    truncated = len(rows) > settings.sql_max_rows
    if truncated:
        rows = rows[: settings.sql_max_rows]

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
    }
