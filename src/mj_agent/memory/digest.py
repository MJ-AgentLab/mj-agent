"""Deterministic per-column count digest for at-rest checkpoint redaction.

Capability ``data-agent.memory-checkpointer`` (REQ-001; ADR-038 mechanism B). Pure — no LLM
call, no I/O. Replaces the verbatim ``execute_sql`` ``rows`` payload with per-column
``{non_null, distinct}`` COUNTS so a persisted checkpoint keeps analytic shape without any
customer / institution / metric cell value.

Counts only, on purpose: ``min`` / ``max`` would themselves be verbatim biz cell values, which
REQ-001 ("persisted checkpoints SHALL NOT contain verbatim biz cell values") forbids — so the
digest never stores an actual value, only statistics derived from them.
"""

from __future__ import annotations

from typing import Any


def digest_rows(
    rows: list[dict[str, Any]], columns: list[str]
) -> dict[str, dict[str, int]]:
    """Per-column ``{non_null, distinct}`` counts over ``rows``.

    Deterministic and value-free: ``distinct`` is counted via ``repr(value)`` (so any cell type
    — ``Decimal`` / ``datetime`` / ``date`` / unhashable — counts stably) but only the *count*
    ``len(...)`` is returned, never the ``repr`` strings themselves. Columns present in ``rows``
    but absent from the ``columns`` argument are still counted (append-order deterministic).
    """
    keys: list[str] = list(columns)
    for row in rows:
        if isinstance(row, dict):
            for k in row:
                if k not in keys:
                    keys.append(k)

    digest: dict[str, dict[str, int]] = {}
    for key in keys:
        non_null = 0
        distinct: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or key not in row:
                continue
            value = row[key]
            if value is None:
                continue
            non_null += 1
            distinct.add(repr(value))
        digest[key] = {"non_null": non_null, "distinct": len(distinct)}
    return digest
