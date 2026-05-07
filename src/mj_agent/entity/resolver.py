"""Entity resolver — user-typed names → canonical entity + DB key.

Two-layer matcher:

  L1 exact: query (case-folded, whitespace-stripped) is one of
            {canonical, aliases[i]}; score = 1.0
  L2 fuzzy: rapidfuzz.process.extract on (canonical + aliases),
            score ≥ DEFAULT_FUZZY_THRESHOLD (0.85)

L1 hits never trigger L2; the highest-scoring L1 hit wins. L2 may
return multiple candidates above threshold; the top-N (default 3)
are surfaced for the LLM to disambiguate.

The codebook (``config/customer_codebook.yaml``) is loaded alongside
aliases. Phase 1 the codename is just attached to the result envelope
(anonymization off); Phase 2 the LLM Gateway will substitute on the
egress path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from pathlib import Path
from typing import Any, Literal

import yaml
from rapidfuzz import fuzz, process

DEFAULT_FUZZY_THRESHOLD = 85  # rapidfuzz returns 0-100; this maps to 0.85


class EntityKind(StrEnum):
    institution = "institution"
    product = "product"


@dataclass(frozen=True)
class ResolveCandidate:
    canonical: str
    aliases: tuple[str, ...]
    matched_via: Literal["L1_exact", "L2_fuzzy"]
    score: float  # 0.0 – 1.0
    db_key: dict[str, Any]  # {tenant_id: ...} or {pcat_l1: ...}
    metadata: dict[str, Any]  # industry / codename / etc.


@dataclass(frozen=True)
class ResolveResult:
    query: str
    kind: EntityKind
    candidates: list[ResolveCandidate]
    notes: list[str]


def _aliases_path() -> Path:
    return Path(__file__).resolve().parent / "aliases.yaml"


def _codebook_path() -> Path:
    # config/ is at project root, two levels above this module
    return Path(__file__).resolve().parents[3] / "config" / "customer_codebook.yaml"


@cache
def load_aliases() -> dict[str, Any]:
    """Load aliases.yaml once per process; cached."""
    with _aliases_path().open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"aliases.yaml top-level must be a mapping, got {type(data)}")
    return data


@cache
def load_codebook() -> dict[str, str]:
    """Return {canonical_name: codename} mapping; empty if file missing."""
    path = _codebook_path()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {m["canonical"]: m["codename"] for m in data.get("mappings", [])}


def _normalize(s: str) -> str:
    return s.strip().casefold()


def _entity_table(kind: EntityKind) -> list[dict[str, Any]]:
    aliases = load_aliases()
    if kind is EntityKind.institution:
        return list(aliases.get("institutions", []))
    return list(aliases.get("products", []))


def _db_key_for(kind: EntityKind, entry: dict[str, Any]) -> dict[str, Any]:
    if kind is EntityKind.institution:
        return {"tenant_id": entry.get("tenant_id", "")}
    return {"pcat_l1": entry.get("pcat_l1", "")}


def _metadata_for(kind: EntityKind, entry: dict[str, Any]) -> dict[str, Any]:
    codebook = load_codebook()
    canonical = entry["canonical"]
    md: dict[str, Any] = {"codename": codebook.get(canonical, "")}
    if kind is EntityKind.institution:
        md["industry"] = entry.get("industry", "")
    return md


def resolve(
    query: str,
    kind: EntityKind | str = EntityKind.institution,
    fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
    top_n: int = 3,
) -> ResolveResult:
    """Resolve ``query`` to entity candidates.

    Args:
        query: user-typed name (e.g. "上海银行" / "京东小贷").
        kind: ``EntityKind.institution`` or ``EntityKind.product`` (string
            also accepted for LLM tool ergonomics).
        fuzzy_threshold: 0-100 minimum rapidfuzz score for L2 hits
            (default 85).
        top_n: max candidates to return for L2 fuzzy hits (default 3).

    Returns:
        ``ResolveResult`` with 0..N candidates. ``notes`` carries
        human-readable diagnostics (e.g. "matched via L1_exact alias
        '京东小贷'" or "no L1 hit; top-3 L2 candidates …").
    """
    if isinstance(kind, str):
        kind = EntityKind(kind)
    notes: list[str] = []
    norm_query = _normalize(query)
    entries = _entity_table(kind)

    # L1: exact match on canonical or any alias
    for entry in entries:
        names = [entry["canonical"], *entry.get("aliases", [])]
        if any(_normalize(n) == norm_query for n in names):
            notes.append(f"L1 exact match on '{query}'")
            return ResolveResult(
                query=query,
                kind=kind,
                candidates=[
                    ResolveCandidate(
                        canonical=entry["canonical"],
                        aliases=tuple(entry.get("aliases", [])),
                        matched_via="L1_exact",
                        score=1.0,
                        db_key=_db_key_for(kind, entry),
                        metadata=_metadata_for(kind, entry),
                    )
                ],
                notes=notes,
            )

    # L2: rapidfuzz extract over flattened (alias, entry) pairs
    flat: list[tuple[str, dict[str, Any]]] = []
    for entry in entries:
        for name in (entry["canonical"], *entry.get("aliases", [])):
            flat.append((name, entry))

    if not flat:
        notes.append("no entries in entity table; check aliases.yaml")
        return ResolveResult(query=query, kind=kind, candidates=[], notes=notes)

    matches = process.extract(
        query,
        [pair[0] for pair in flat],
        scorer=fuzz.WRatio,
        limit=max(top_n * 3, 10),  # over-fetch then dedupe by entry
    )
    seen: set[int] = set()
    candidates: list[ResolveCandidate] = []
    for matched_name, score, idx in matches:
        if score < fuzzy_threshold:
            break
        entry = flat[idx][1]
        eid = id(entry)
        if eid in seen:
            continue
        seen.add(eid)
        candidates.append(
            ResolveCandidate(
                canonical=entry["canonical"],
                aliases=tuple(entry.get("aliases", [])),
                matched_via="L2_fuzzy",
                score=round(score / 100.0, 4),
                db_key=_db_key_for(kind, entry),
                metadata={**_metadata_for(kind, entry), "matched_alias": matched_name},
            )
        )
        if len(candidates) >= top_n:
            break

    if not candidates:
        notes.append(
            f"no L1 or L2 hit (threshold={fuzzy_threshold}); "
            f"consider asking the user to clarify or to use the full canonical name"
        )
    else:
        notes.append(
            f"L2 fuzzy: {len(candidates)} candidate(s) ≥ threshold {fuzzy_threshold}"
        )

    return ResolveResult(query=query, kind=kind, candidates=candidates, notes=notes)
