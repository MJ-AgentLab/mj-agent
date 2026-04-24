"""Application-level SQL guardrail (L1 of the four-layer defense).

Phase 0 uses a deliberately thin regex check. Rationale:
  - DB-side GRANTs (L4) are the authoritative defense.
  - Phase 2 will upgrade to sqlglot AST-level validation.

What this layer catches:
  - multi-statement SQL (no `;` chaining)
  - non-SELECT statements
  - dangerous keywords (DML/DDL/DCL/maintenance)
  - unqualified schema references outside the allowlist

What this layer does NOT catch (intentionally, deferred to L3/L4):
  - dangerous keywords hidden in comments or string literals
  - CTE alias shadowing a schema name
  - function calls that return sensitive data
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Accept either plain SELECT or a WITH ... SELECT pipeline.
_STMT_START = re.compile(r"^\s*(WITH\b.*?\bSELECT\b|SELECT\b)", re.IGNORECASE | re.DOTALL)

# Any occurrence of these as whole words rejects the statement.
_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|GRANT|REVOKE|CREATE|"
    r"COPY|VACUUM|REINDEX|CLUSTER|ANALYZE|LOCK|CALL)\b|\bSET\s+SESSION\b",
    re.IGNORECASE,
)

# Matches `FROM schema.table` or `JOIN schema.table`.
_QUAL_REF = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-zA-Z_][\w]*)\.[a-zA-Z_][\w]*",
    re.IGNORECASE,
)


def is_safe_select(sql: str, allowed_schemas: Iterable[str]) -> tuple[bool, str]:
    """Return (ok, reason) for a candidate SQL string.

    Args:
        sql: the statement text.
        allowed_schemas: whitelist of allowed schema names (case-insensitive).

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
    for schema in _QUAL_REF.findall(stripped):
        if schema.lower() not in allowed:
            return False, f"schema '{schema}' is not in the allowlist"

    return True, ""
