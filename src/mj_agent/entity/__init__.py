"""Entity resolution: user-typed names → canonical name + DB key.

Phase 1 sub 1.C — minimal L1 (exact alias match) + L2 (rapidfuzz fuzzy)
resolver. Codebook integration is structural (Phase 2 ADR-014 flips
anonymization on without changing this API).
"""

from mj_agent.entity.resolver import (
    DEFAULT_FUZZY_THRESHOLD,
    EntityKind,
    ResolveCandidate,
    ResolveResult,
    load_aliases,
    load_codebook,
    resolve,
)

__all__ = [
    "DEFAULT_FUZZY_THRESHOLD",
    "EntityKind",
    "ResolveCandidate",
    "ResolveResult",
    "load_aliases",
    "load_codebook",
    "resolve",
]
