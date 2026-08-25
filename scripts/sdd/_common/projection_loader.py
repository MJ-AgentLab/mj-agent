"""projection_loader.py — shared lock/Handoff loader for the projection domain.

This module is the "PR-A1 extracted lock/Handoff loader" enumerated in
`policies/ai-agent.md` §4 (A14 row, D-017 extended adjacency; ADR-039): a
loader-class `_common` module consumed by `scripts/sdd/agents_sync.py`
(owned-only reconcile) and `scripts/sdd/check_agents_projection.py` (V9), so
the generator and the checker read ONE implementation. The other `_common`
modules are generic validator helpers and deliberately stay OUTSIDE the D-017
surface — do not fold them in here, and do not re-export this module from
`_common/__init__.py` (the D-017 boundary stays visible at import sites).

Two concerns only (Epic #499 plan §5.5, PR-A1):

- Handoff parser — the V9 `## Handoff*` section semantics (`^(#{2,})\\s*Handoff`
  prefix match + heading-level exit) collecting `/mj-agent-*` slash-form refs,
  extracted verbatim from `check_agents_projection.py` so the PR-B dependency
  scanner reads the same implementation (plan §2.5 layer A region 1).
- Lock loader/verifier — `.agents.lock.json` is the owner ledger for managed
  artifacts. `verify_lock()` turns the raw mapping into per-path verified
  ownership (AC-05: one owner per path). Owned-only reconcile (ADR-039 D-012
  revised) may delete ONLY a path with a verified lock owner + safe path +
  absence from the desired set; an unknown/malformed/mixed lock means zero
  delete/write (AC-06) — carried here as `LockVerificationError`.

Read-only; no secrets; no network; ASCII-only messages.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

LOCK_RELPATH = Path(".agents.lock.json")
CODEX_CONFIG_RELPATH = Path(".codex/config.toml")
# Reserved path-shaped lock key (Owner 拍板 2026-07-14): cannot collide with
# skill names, which never contain "/" or ".".
CODEX_LOCK_KEY = ".codex/config.toml"
SKILLS_RELDIR = PurePosixPath(".agents/skills")

# Handoff parser (V9 semantics; moved verbatim from check_agents_projection.py).
HANDOFF_HEADING = re.compile(r"^(#{2,})\s*Handoff", flags=re.IGNORECASE)
HEADING = re.compile(r"^(#{2,})\s")
SKILL_REF = re.compile(r"/(mj-agent-[a-z0-9-]+\*?)")

# Lock schema (v1): skill-name keys + the single reserved path key.
_SKILL_KEY = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_LOCK_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")


class LockVerificationError(ValueError):
    """The lock cannot prove ownership — owned-only reconcile must not delete/write."""


def handoff_refs(skill_text: str) -> set[str]:
    """Collect /mj-agent-* refs that appear inside `## Handoff*` sections only."""
    refs: set[str] = set()
    in_handoff = False
    handoff_level = 0
    for line in skill_text.splitlines():
        m = HEADING.match(line)
        if m:
            hm = HANDOFF_HEADING.match(line)
            if hm:
                in_handoff = True
                handoff_level = len(hm.group(1))
                continue
            if in_handoff and len(m.group(1)) <= handoff_level:
                in_handoff = False
            continue
        if in_handoff:
            refs.update(SKILL_REF.findall(line))
    return refs


@dataclass(frozen=True)
class VerifiedLock:
    """Schema-verified `.agents.lock.json` as a per-path ownership ledger."""

    entries: dict[str, str]  # raw key -> "sha256:<64 hex>" (verbatim)
    owned_paths: dict[str, PurePosixPath]  # raw key -> managed artifact relpath


def artifact_relpath(key: str) -> PurePosixPath:
    """Managed artifact path a verified lock key owns (one owner per path)."""
    if key == CODEX_LOCK_KEY:
        return PurePosixPath(CODEX_LOCK_KEY)
    return SKILLS_RELDIR / key / "SKILL.md"


def read_lock(repo_root: Path) -> dict[str, object] | None:
    """Raw lock mapping, or None when the file is absent (no owner ledger —
    owned-only reconcile then has nothing it may delete)."""
    path = repo_root / LOCK_RELPATH
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LockVerificationError(
            f"{LOCK_RELPATH.as_posix()} unreadable: {exc} (zero delete/write)"
        ) from exc
    if not isinstance(data, dict):
        raise LockVerificationError(
            f"{LOCK_RELPATH.as_posix()} top level must be a mapping (zero delete/write)"
        )
    return data


def verify_lock(raw: dict[str, object]) -> VerifiedLock:
    """Verify the lock schema and derive per-path ownership (AC-05/AC-06).

    Any single unknown/malformed entry fails the WHOLE lock (a mixed ledger
    proves nothing about ownership) — callers must then delete/write nothing.
    """
    entries: dict[str, str] = {}
    owned: dict[str, PurePosixPath] = {}
    for key, value in raw.items():
        if key != CODEX_LOCK_KEY and _SKILL_KEY.fullmatch(key) is None:
            raise LockVerificationError(
                f"lock key {key!r} is neither a skill name nor the reserved"
                f" {CODEX_LOCK_KEY!r} key (unknown schema; zero delete/write)"
            )
        if not isinstance(value, str) or _LOCK_HASH.fullmatch(value) is None:
            raise LockVerificationError(
                f"lock entry {key!r} is not a 'sha256:<64 hex>' string"
                " (malformed owner ledger; zero delete/write)"
            )
        entries[key] = value
        owned[key] = artifact_relpath(key)
    return VerifiedLock(entries=entries, owned_paths=owned)


def load_verified_lock(repo_root: Path) -> VerifiedLock | None:
    """read_lock + verify_lock; None when no lock file exists."""
    raw = read_lock(repo_root)
    return None if raw is None else verify_lock(raw)
