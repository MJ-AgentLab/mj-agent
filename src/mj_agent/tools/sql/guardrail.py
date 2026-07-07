"""Application-level SQL guardrail (L1 of the four-layer defense).

Phase 0 used a deliberately thin regex check; PR1 of the MVP plan adds
table-level allowlist enforcement so that ``biz_dwd.<other_table>`` is
rejected at L1 even though ``biz_dwd`` is in the schema allowlist (the
mj-system contract exposes exactly two ``biz_dwd`` dimension tables).

Defense layering rationale:
  - DB-side GRANTs (L4) remain the authoritative defense.
  - Schema/table allowlist extraction is sqlglot AST-based (see
    ``_qualified_refs``), so quoted / mixed-quoted identifiers, comma joins
    and UNION legs cannot slip a forbidden schema past L1 (#280). Because the
    allowlist is a security boundary, a statement sqlglot cannot parse is
    rejected fail-closed — an un-vouchable statement does not proceed (unlike
    the L1b precheck *quality* rules, which degrade gracefully because the DB
    is their ultimate validator).

What this layer catches:
  - multi-statement SQL (no `;` chaining)
  - non-SELECT statements
  - dangerous keywords (DML/DDL/DCL/maintenance)
  - schema references outside the allowlist (quoting-agnostic via the AST)
  - table references outside the per-schema allowlist (e.g. biz_dwd
    fact tables that are not the two exposed dimensions)
  - SQL that cannot be parsed for static validation (fail-closed reject)

What this layer does NOT catch (intentionally, deferred to L3/L4):
  - dangerous keywords hidden in comments or string literals (the keyword
    scan is still regex-based)
  - CTE alias shadowing a schema name
  - function calls that return sensitive data
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

import sqlglot
from sqlglot import expressions as exp

# Accept either plain SELECT or a WITH ... SELECT pipeline.
_STMT_START = re.compile(r"^\s*(WITH\b.*?\bSELECT\b|SELECT\b)", re.IGNORECASE | re.DOTALL)

# Any occurrence of these as whole words rejects the statement.
_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|GRANT|REVOKE|CREATE|"
    r"COPY|VACUUM|REINDEX|CLUSTER|ANALYZE|LOCK|CALL)\b|\bSET\s+SESSION\b",
    re.IGNORECASE,
)


def _qualified_refs(sql: str) -> list[tuple[str, str]] | None:
    """Return ``(schema, table)`` for every schema-qualified table reference.

    Extraction is AST-based (sqlglot) so that quoted / mixed-quoted
    identifiers, comma joins, UNION legs, sub-queries and CTE base tables are
    all seen — quoting-agnostic, closing #280 (the earlier regex silently
    missed quoted refs, letting ``FROM "biz_ods"."t"`` reach the DB where only
    the L4 GRANT stopped it). sqlglot normalizes the quoting, so ``table.db`` /
    ``table.name`` are the plain identifier text regardless of how the analyst
    wrote them. Unqualified references (``table.db`` empty) are left to the DB /
    search_path, matching prior behavior.

    Returns ``None`` when sqlglot cannot parse the statement (parse error, or
    ``RecursionError`` on pathological nesting). The caller treats ``None`` as
    fail-closed: the allowlist is a security boundary, so a statement that
    cannot be statically validated is rejected rather than trusted.
    """
    try:
        tree = sqlglot.parse_one(sql, read="postgres")
    except (sqlglot.errors.SqlglotError, RecursionError):
        return None
    if tree is None:
        return None
    return [
        (table.db, table.name) for table in tree.find_all(exp.Table) if table.db
    ]


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
        # When a DDL/DML keyword caused the non-SELECT start, surface it in
        # the reason so error messages help analyst self-correction
        # (capabilities/data-agent/safe-sql/contracts/behavior.feature REQ-001).
        blocked = _BLOCKED.search(stripped)
        if blocked:
            return False, f"blocked keyword {blocked.group(0).upper()} detected"
        return False, "only SELECT or WITH ... SELECT is allowed"

    if _BLOCKED.search(stripped):
        blocked = _BLOCKED.search(stripped)
        keyword = blocked.group(0).upper() if blocked else "DDL/DML/DCL/maintenance"
        return False, f"blocked keyword {keyword} detected"

    allowed = {s.lower() for s in allowed_schemas}
    table_whitelist: dict[str, set[str]] = {}
    if allowed_tables_per_schema is not None:
        for s, ts in allowed_tables_per_schema.items():
            table_whitelist[s.lower()] = {t.lower() for t in ts}

    refs = _qualified_refs(stripped)
    if refs is None:
        return (
            False,
            "could not parse SQL for allowlist validation; "
            "simplify or rephrase the query",
        )

    for schema, table in refs:
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
