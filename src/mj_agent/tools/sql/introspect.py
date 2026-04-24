"""Schema introspection tools — what tables can the analyst actually see?

Both tools honor the DB-side permission model: they reflect what
`CURRENT_USER` is granted SELECT on, so the LLM never attempts to query
a table that would 42501 at execute time.
"""

from __future__ import annotations

from typing import Any

from mj_agent.config import settings
from mj_agent.integrations.mj_system_db import readonly_cursor

_LIST_TABLES_SQL = """
SELECT
    t.table_schema,
    t.table_name,
    obj_description(c.oid, 'pg_class') AS comment,
    c.reltuples::BIGINT AS row_estimate
FROM information_schema.table_privileges tp
JOIN information_schema.tables t
    ON tp.table_schema = t.table_schema
   AND tp.table_name = t.table_name
JOIN pg_namespace n ON n.nspname = t.table_schema
JOIN pg_class c ON c.relname = t.table_name AND c.relnamespace = n.oid
WHERE tp.grantee = CURRENT_USER
  AND tp.privilege_type = 'SELECT'
  AND t.table_schema = ANY(%s)
ORDER BY t.table_schema, t.table_name
"""

_DESCRIBE_TABLE_SQL = """
SELECT
    a.attname AS name,
    format_type(a.atttypid, a.atttypmod) AS type,
    NOT a.attnotnull AS nullable,
    col_description(c.oid, a.attnum) AS comment
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = %s
  AND c.relname = %s
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY a.attnum
"""

_TABLE_COMMENT_SQL = """
SELECT obj_description(c.oid, 'pg_class') AS comment
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = %s AND c.relname = %s
"""


def list_biz_tables() -> list[dict[str, Any]]:
    """List all biz-domain tables the analyst role has SELECT on.

    Returns:
        A list of dicts, one per visible table:
          - schema (str): e.g. "biz_dws" or "biz_dwd"
          - table (str): table name
          - comment (str | None): PostgreSQL table comment, if any
          - row_estimate (int): pg_class.reltuples approximation (cheap, no
            COUNT(*) scan; may be stale shortly after ETL)

    The result is filtered by the analyst role's GRANTs, so it always
    reflects what is actually queryable — never lists a table that would
    fail with 42501 at execute time.
    """
    with readonly_cursor() as cur:
        cur.execute(_LIST_TABLES_SQL, (list(settings.biz_allowed_schemas),))
        rows = cur.fetchall()

    return [
        {
            "schema": r["table_schema"],
            "table": r["table_name"],
            "comment": r["comment"],
            "row_estimate": int(r["row_estimate"]) if r["row_estimate"] is not None else 0,
        }
        for r in rows
    ]


def describe_biz_table(name: str) -> dict[str, Any]:
    """Describe columns of a biz-domain table.

    Args:
        name: either a schema-qualified name (`biz_dws.dws_qcm_qrynum_daily_total`)
            or an unqualified table name (resolved against the first allowed
            schema).

    Returns:
        A dict with keys:
          - schema (str)
          - table (str)
          - comment (str | None): table-level comment
          - columns (list[dict]): each column has name/type/nullable/comment

    Raises:
        ValueError: the schema is not in the allowlist or the table has no
            visible columns (likely permission denied or non-existent).
    """
    if "." in name:
        schema, table = name.split(".", 1)
    else:
        schema, table = settings.biz_allowed_schemas[0], name

    if schema.lower() not in {s.lower() for s in settings.biz_allowed_schemas}:
        raise ValueError(
            f"schema '{schema}' not in allowlist {settings.biz_allowed_schemas}"
        )

    with readonly_cursor() as cur:
        cur.execute(_TABLE_COMMENT_SQL, (schema, table))
        comment_row = cur.fetchone()
        cur.execute(_DESCRIBE_TABLE_SQL, (schema, table))
        columns = cur.fetchall()

    if not columns:
        raise ValueError(
            f"no visible columns for {schema}.{table} "
            "(permission denied, table missing, or not readable by the analyst role)"
        )

    return {
        "schema": schema,
        "table": table,
        "comment": comment_row["comment"] if comment_row else None,
        "columns": [
            {
                "name": c["name"],
                "type": c["type"],
                "nullable": bool(c["nullable"]),
                "comment": c["comment"],
            }
            for c in columns
        ],
    }
