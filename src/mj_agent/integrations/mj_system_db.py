"""Read-only PostgreSQL access to the mj-system biz domain.

ADR-006 fail-safe reads: combines four layers of protection —
  L3 connection: default_transaction_read_only=on
  L4 role:       analyst GRANTs (DB-side authoritative, managed by
                 mj-system/sql/migrations/repeatable/R__analyst_permissions.sql)

Layers L1 (guardrail) and L2 (skill semantics) live elsewhere.
"""

from __future__ import annotations

import atexit
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from psycopg import Cursor
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from mj_agent.config import settings

_pool: ConnectionPool | None = None


def _dsn() -> str:
    """Build a psycopg DSN pinned to analyst credentials + read-only flags.

    Notes:
      - `default_transaction_read_only=on` rejects any non-SELECT (belt &
        suspenders with the analyst role's SELECT-only GRANT).
      - `statement_timeout` is NOT overridden here — the analyst role is
        `ALTER ROLE ... SET statement_timeout='60s'` on the DB side.
      - `lock_timeout` and `idle_in_transaction_session_timeout` guard the
        client against rogue hangs.
    """
    pwd = settings.postgres_analyst_password.get_secret_value()
    opts = (
        "-c default_transaction_read_only=on "
        "-c lock_timeout=5000 "
        "-c idle_in_transaction_session_timeout=10000"
    )
    return (
        f"host={settings.biz_pg_host} "
        f"port={settings.biz_pg_port} "
        f"dbname={settings.postgres_biz_db} "
        f"user={settings.postgres_analyst_user} "
        f"password={pwd} "
        f"application_name=mj-agent "
        f"options='{opts}'"
    )


def get_pool() -> ConnectionPool:
    """Lazy singleton pool. Closed automatically at interpreter shutdown."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=_dsn(),
            min_size=1,
            max_size=4,
            kwargs={"autocommit": False, "row_factory": dict_row},
            open=True,
        )
        atexit.register(_pool.close)
    return _pool


@contextmanager
def readonly_cursor() -> Iterator[Cursor[dict[str, Any]]]:
    """Yield a cursor bound to a read-only transaction.

    The `finally` rollback ensures no dangling transactions remain in the
    pool if a caller raises. We intentionally do NOT `SET search_path`:
    table references must be schema-qualified (`biz_dws.*` / `biz_dwd.*`),
    enforced by the guardrail.
    """
    with (
        get_pool().connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        try:
            yield cur
        finally:
            conn.rollback()
