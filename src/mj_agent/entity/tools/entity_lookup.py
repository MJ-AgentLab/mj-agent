"""LLM-facing tool wrapping ``entity.resolver.resolve``.

The LLM calls this **before** writing SQL whenever the user mentions a
customer / institution / product by short name or alias, so the SQL
plan uses canonical DB keys (tenant_id / pcat_l1) instead of guessing.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mj_agent.entity.resolver import EntityKind, resolve


def entity_lookup(
    name: str,
    kind: str = "institution",
    fuzzy_threshold: int = 85,
    top_n: int = 3,
) -> dict[str, Any]:
    """Resolve a short / alias / typo'd entity name to canonical candidates.

    Use **before** writing SQL when the user mentions a customer /
    institution / product by short name (e.g. "上海银行" / "京东小贷" /
    "百云"). Returns canonical name + DB key (tenant_id / pcat_l1) so
    the SQL filter pins the right entity instead of guessing.

    Args:
        name: user-typed name (短名 / 别名 / 拼音缩写 OK).
        kind: ``"institution"`` (机构 / 客户) or ``"product"`` (产品系列).
        fuzzy_threshold: 0-100 minimum rapidfuzz score for L2 hits
            (default 85). Lower → more permissive but more false positives.
        top_n: max candidates returned when L2 fuzzy yields multiple
            possibilities (default 3).

    Returns:
        Dict envelope:
          - ``query``: echoed input
          - ``kind``: echoed input
          - ``candidates``: list of dicts, each containing
            ``canonical / aliases / matched_via (L1_exact|L2_fuzzy) /
            score (0..1) / db_key {tenant_id|pcat_l1} / metadata``
          - ``notes``: human-readable diagnostics (e.g. "L1 exact match"
            or "L2 fuzzy: 2 candidates above threshold")

        Disambiguation:
          - len(candidates) == 0 → ask the user to clarify
          - len(candidates) == 1 with L1_exact → use directly
          - len(candidates) >= 2 → ask the user to pick (or surface
            top-1 with explicit caveat in the reply)
    """
    result = resolve(
        query=name,
        kind=EntityKind(kind),
        fuzzy_threshold=fuzzy_threshold,
        top_n=top_n,
    )
    return {
        "query": result.query,
        "kind": result.kind.value,
        "candidates": [
            {
                "canonical": c.canonical,
                "aliases": list(c.aliases),
                "matched_via": c.matched_via,
                "score": c.score,
                "db_key": c.db_key,
                "metadata": c.metadata,
            }
            for c in result.candidates
        ],
        "notes": list(result.notes),
        "_debug": {"raw": [asdict(c) for c in result.candidates]} if False else {},
    }
