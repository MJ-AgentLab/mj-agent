"""Execute a read-only SQL against the mj-system biz domain.

Exposed as a LangChain tool via its type hints and docstring — no @tool
decorator required; LangChain 1.x introspects these signatures directly.

The execution path is layered:

  1. L1 hybrid guardrail (``guardrail.is_safe_select``) — blocks DML/DDL,
     multi-statement, schema/table allowlist breaches.
  2. L1b sqlglot precheck (``precheck.precheck_sql``) — Component-Judge-
     aligned static rules: no_select_star, require_time_range, advisory
     LIMIT checks. P0 errors become ``ValueError``; P1 warnings travel
     in the response envelope.
  3. Read-only psycopg cursor with DB-side ``statement_timeout = 60s``
     (set by the analyst role).

Returned envelope (per MVP plan v2 PR2):
  - ``executed_sql`` — verbatim echo so the analyst can audit
  - ``columns`` / ``rows`` / ``row_count`` / ``truncated``
  - ``statement_timeout_hit`` (bool, false unless caller catches timeout)
  - ``business_summary`` — heuristic placeholder; LLM is expected to
    rewrite this in its response using both the rows and the hint
  - ``precheck_warnings`` — list of P1 advisory strings
"""

from __future__ import annotations

from typing import Any

import psycopg

from mj_agent.config import settings
from mj_agent.integrations.mj_system_db import readonly_cursor
from mj_agent.tools.sql.guardrail import is_safe_select
from mj_agent.tools.sql.precheck import precheck_sql


def _heuristic_summary(
    sql: str,
    row_count: int,
    truncated: bool,
    timeout_hit: bool,
) -> str:
    if timeout_hit:
        return (
            "查询触发 60s 超时；建议改用聚合或限定更窄的时间范围后重试。"
        )
    if row_count == 0:
        return "查询成功执行但没有返回行；请检查时间范围或过滤条件。"
    head = f"查询返回 {row_count} 行"
    if truncated:
        head += f"（已被截断到 {settings.sql_max_rows}，仍有更多）"
    return head + "；请基于这些行向用户给出业务化结论。"


def execute_sql(sql: str) -> dict[str, Any]:
    """Run a read-only SELECT against the biz domain and return rows as JSON.

    Only SELECT (or WITH ... SELECT) statements are allowed. All table
    references MUST be schema-qualified; currently accepted schemas are
    `biz_dws` (all tables) and `biz_dwd` (dimension tables only —
    `dwd_dim_product_interface`, `dwd_dim_institution`; other biz_dwd
    tables are denied by the L1 guardrail and the database).

    Args:
        sql: the SQL statement. Single statement only. Trailing `;` optional.

    Returns:
        A dict with keys:
          - executed_sql (str): the SQL that ran
          - columns (list[str]): column names in result order
          - rows (list[dict]): up to SQL_MAX_ROWS rows; each row is a
            {column_name: value} mapping
          - row_count (int): number of rows returned (<= SQL_MAX_ROWS)
          - truncated (bool): True if the result was capped at SQL_MAX_ROWS
          - statement_timeout_hit (bool): True only if the call raised the
            timeout error (the function itself raises RuntimeError; this
            flag is reserved for callers that catch and recover)
          - business_summary (str): heuristic 1-line summary; the LLM is
            expected to rewrite this in its response
          - precheck_warnings (list[str]): P1 advisory observations from
            the AST precheck (e.g. missing LIMIT on detail queries)

    Raises:
        ValueError: the L1 guardrail or the L1b precheck rejected the SQL.
        RuntimeError: the database returned an error. ``statement_timeout``
            (60s) raises ``RuntimeError`` with a friendly hint.
    """
    ok, reason = is_safe_select(
        sql,
        settings.biz_allowed_schemas,
        allowed_tables_per_schema={"biz_dwd": settings.biz_allowed_dwd_tables},
    )
    if not ok:
        raise ValueError(f"SQL rejected by guardrail: {reason}")

    precheck = precheck_sql(sql)
    if not precheck.ok:
        raise ValueError("SQL rejected by precheck: " + "; ".join(precheck.errors))

    try:
        with readonly_cursor() as cur:
            cur.execute(sql)
            columns = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchmany(settings.sql_max_rows + 1)
    except psycopg.errors.QueryCanceled as exc:
        raise RuntimeError(
            "查询触发 statement_timeout=60s；请改用聚合（GROUP BY）、加上更窄的时间范围、"
            "或减少 JOIN 数量后重试。"
        ) from exc
    except Exception as exc:  # noqa: BLE001 — surface DB errors verbatim
        raise RuntimeError(f"database error: {exc}") from exc

    truncated = len(rows) > settings.sql_max_rows
    if truncated:
        rows = rows[: settings.sql_max_rows]

    return {
        "executed_sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "statement_timeout_hit": False,
        "business_summary": _heuristic_summary(sql, len(rows), truncated, False),
        "precheck_warnings": list(precheck.warnings),
    }
