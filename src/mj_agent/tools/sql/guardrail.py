"""Application-level SQL guardrail (L1 of the four-layer defense).

Phase 0 used a deliberately thin regex check; PR1 of the MVP plan adds
table-level allowlist enforcement so that ``biz_dwd.<other_table>`` is
rejected at L1 even though ``biz_dwd`` is in the schema allowlist (the
mj-system contract exposes exactly two ``biz_dwd`` dimension tables).

Defense layering rationale:
  - DB-side GRANTs (L4) remain the authoritative defense.
  - Phase 2 will upgrade to sqlglot AST-level validation (PR2 of the MVP
    plan, sharing rule sources with the eval Component Judge).

What this layer catches:
  - multi-statement SQL (no `;` chaining)
  - non-SELECT statements
  - dangerous keywords (DML/DDL/DCL/maintenance)
  - schema references outside the allowlist
  - table references outside the per-schema allowlist (e.g. biz_dwd
    fact tables that are not the two exposed dimensions)

What this layer does NOT catch (intentionally, deferred to L3/L4):
  - dangerous keywords hidden in comments or string literals
  - CTE alias shadowing a schema name
  - function calls that return sensitive data
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

# Accept either plain SELECT or a WITH ... SELECT pipeline.
_STMT_START = re.compile(r"^\s*(WITH\b.*?\bSELECT\b|SELECT\b)", re.IGNORECASE | re.DOTALL)

# Any occurrence of these as whole words rejects the statement.
_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|GRANT|REVOKE|CREATE|"
    r"COPY|VACUUM|REINDEX|CLUSTER|ANALYZE|LOCK|CALL)\b|\bSET\s+SESSION\b",
    re.IGNORECASE,
)

# Matches `FROM schema.table` or `JOIN schema.table` — captures both parts.
_QUAL_REF = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)",
    re.IGNORECASE,
)


def is_safe_select(
    sql: str,
    allowed_schemas: Iterable[str],
    allowed_tables_per_schema: Mapping[str, Iterable[str]] | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason) for a candidate SQL string.

    Args:
        sql: the statement text.
        allowed_schemas: whitelist of allowed schema names (case-insensitive).
        allowed_tables_per_schema: optional per-schema table whitelist. When
            a schema appears here, only the listed tables are accepted; when
            omitted, every table within the schema is accepted (wildcard).
            Schemas not present in this map (but present in
            ``allowed_schemas``) remain wildcard.

    Returns:
        (True, "") if accepted.
        (False, reason) with a human-readable reason for rejection.
    """
    stripped = sql.strip()
    # Drop a single trailing ';' but reject multiple statements.
    if stripped.endswith(";"):
        stripped = stripped[:-1].rstrip()
    if ";" in stripped:
        return False, "multi-statement SQL is not allowed"

    if not stripped:
        return False, "empty SQL"

    if not _STMT_START.match(stripped):
        return False, "only SELECT or WITH ... SELECT is allowed"

    if _BLOCKED.search(stripped):
        return False, "blocked keyword detected (DDL/DML/DCL/maintenance)"

    allowed = {s.lower() for s in allowed_schemas}
    table_whitelist: dict[str, set[str]] = {}
    if allowed_tables_per_schema is not None:
        for s, ts in allowed_tables_per_schema.items():
            table_whitelist[s.lower()] = {t.lower() for t in ts}

    for schema, table in _QUAL_REF.findall(stripped):
        s_lower = schema.lower()
        if s_lower not in allowed:
            return False, f"schema '{schema}' is not in the allowlist"
        if s_lower in table_whitelist and table.lower() not in table_whitelist[s_lower]:
            allowed_list = sorted(table_whitelist[s_lower])
            return (
                False,
                f"table '{schema}.{table}' is not in the allowlist for schema "
                f"'{schema}' (only {allowed_list} are exposed)",
            )

    return True, ""
