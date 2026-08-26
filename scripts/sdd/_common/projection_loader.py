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

Since Epic #499 PR-B the lock concern spans BOTH schemas (plan §2.6, dormant
until the PR-C1 cutover): the legacy v1 flat map (`verify_lock`) and the v2
envelope (`verify_lock_v2` — 7-kind closed entry union, canonical-JSON wire,
owner-ledger semantics inherited from PR-A1). `classify_lock` is the version
dispatch; anything that is neither strict v1 nor strict v2 is malformed/mixed
and proves nothing about ownership (zero delete/write, AC-06). All JSON parsing
here rejects duplicate keys at any level (a duplicate-key ledger is hand-made
by construction — fail closed before canonicalization, §2.6).

Read-only; no secrets; no network; ASCII-only messages.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

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


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise LockVerificationError(
                f"duplicate JSON key {key!r} (malformed ledger; zero delete/write)"
            )
        out[key] = value
    return out


def parse_lock_json(text: str) -> Any:
    """JSON parse with duplicate-key rejection at every level (plan §2.6)."""
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise LockVerificationError(
            f"lock is not valid JSON: {exc} (zero delete/write)"
        ) from exc


def read_lock(repo_root: Path) -> dict[str, object] | None:
    """Raw lock mapping, or None when the file is absent (no owner ledger —
    owned-only reconcile then has nothing it may delete). Duplicate keys at
    any level are malformed (PR-B tightening: a generated lock never carries
    them, so their presence proves a hand edit — fail closed)."""
    path = repo_root / LOCK_RELPATH
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LockVerificationError(
            f"{LOCK_RELPATH.as_posix()} unreadable: {exc} (zero delete/write)"
        ) from exc
    try:
        data = parse_lock_json(text)
    except LockVerificationError as exc:
        # Keep the file-path context of the pre-PR-B diagnosis (Stage 11 #30).
        raise LockVerificationError(
            f"{LOCK_RELPATH.as_posix()} unreadable: {exc}"
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


# ---------------------------------------------------------------------------
# Lock v2 envelope (Epic #499 plan §2.6 / §2.8.1 / §2.8.3 — dormant until the
# PR-C1 cutover; the real tree stays legacy v1). Everything below is a CLOSED
# schema: extra, missing, wrong-type, unknown-enum and cross-kind combinations
# all raise LockVerificationError, and callers must then delete/write nothing.
# ---------------------------------------------------------------------------

LOCK_SCHEMA_VERSION = 2
KNOWN_GENERATOR_PROTOCOLS = frozenset({1})
SURFACES = frozenset({"skills", "mcp", "enforcement"})

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
SKILLS_README_KEY = ".agents/README.md"
CODEX_HOOKS_KEY = ".codex/hooks.json"
CODEX_RULES_PREFIX = ".codex/rules/"
CODEX_RULES_SUFFIX = ".rules"

_RENDERER_INPUT_KEYS = ("renderer_module", "renderer_module_sha256", "renderer_version")
# §2.8.3: the two wildcard keys extend skill-translated inputs beyond the §2.6 table.
_WILDCARD_KEYS = ("wildcard_expansions", "wildcard_expansions_sha256")


def canonical_json_text(obj: Any) -> str:
    """Canonical JSON per plan §2.8.1: LF, 2-space indent, `ensure_ascii=false`,
    object keys sorted by Unicode code point, exactly one final newline. Arrays
    keep their schema-specified order (the caller sorts set-like arrays)."""
    return (
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    )


def sha256_of_canonical(obj: Any) -> str:
    """Lowercase 64-hex SHA-256 over the canonical JSON bytes of `obj`."""
    return hashlib.sha256(canonical_json_text(obj).encode("utf-8")).hexdigest()


def safe_output_path(key: str) -> PurePosixPath:
    """Validate a v2 entry key as an NFC, POSIX-slash, repo-relative,
    case-preserving normalized output path (plan §2.6/§2.8.1). Filesystem
    hazards (symlink/reparse ancestors, on-disk casefold squats, file-type
    collisions) are the sync-time preflight battery's job — this is the pure
    wire-shape half."""
    if not key or not isinstance(key, str):
        raise LockVerificationError("entry key must be a non-empty string")
    if unicodedata.normalize("NFC", key) != key:
        raise LockVerificationError(f"entry key {key!r} is not NFC-normalized")
    if "\\" in key:
        raise LockVerificationError(f"entry key {key!r} must use POSIX slashes")
    if key.startswith("/") or key.startswith("//"):
        raise LockVerificationError(f"entry key {key!r} must be repo-relative")
    if re.match(r"^[A-Za-z]:", key):
        raise LockVerificationError(f"entry key {key!r} carries a drive prefix")
    parts = key.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise LockVerificationError(
            f"entry key {key!r} has an empty/'.'/'..' path segment"
        )
    return PurePosixPath(key)


@dataclass(frozen=True)
class _KindSpec:
    surface_members: tuple[str, ...]
    strategy: str
    normalization_policy: str
    input_keys: tuple[str, ...] | None  # None => composite member fields instead


# §2.6 closed entry union. `input_keys` are EXACT (no optional key).
KIND_SPECS: dict[str, _KindSpec] = {
    "skill-byte-copy": _KindSpec(
        ("skills",), "byte-copy", "raw-bytes-v1",
        ("source_path", "source_sha256", "manifest_slice_sha256") + _RENDERER_INPUT_KEYS,
    ),
    "skill-translated": _KindSpec(
        ("skills",), "translated", "translated-utf8-lf-v1",
        ("source_path", "source_sha256", "manifest_slice_sha256",
         "workflow_slice_sha256", "translation_map_sha256", "preface_sha256")
        + _RENDERER_INPUT_KEYS + _WILDCARD_KEYS,
    ),
    "skills-readme": _KindSpec(
        ("skills",), "rendered", "generated-utf8-lf-v1",
        ("manifest_slice_sha256", "template_path", "template_sha256",
         "template_version") + _RENDERER_INPUT_KEYS,
    ),
    "codex-config-mcp": _KindSpec(
        ("mcp",), "rendered", "canonical-toml-v1",
        ("mcp_source_path", "mcp_source_sha256", "manifest_mcp_slice_sha256",
         "codex_posture_slice_sha256") + _RENDERER_INPUT_KEYS,
    ),
    "codex-config-composite": _KindSpec(
        ("enforcement", "mcp"), "rendered", "canonical-toml-v1", None,
    ),
    "codex-hook": _KindSpec(
        ("enforcement",), "rendered", "canonical-json-v1",
        ("enforcement_source_sha256", "policy_refs_sha256") + _RENDERER_INPUT_KEYS,
    ),
    "codex-rule": _KindSpec(
        ("enforcement",), "rendered", "generated-utf8-lf-v1",
        ("enforcement_source_sha256", "policy_refs_sha256") + _RENDERER_INPUT_KEYS,
    ),
}

_COMMON_ENTRY_KEYS = frozenset(
    {"entry_kind", "owner", "surface_members", "strategy",
     "normalization_policy", "output_sha256"}
)
_COMPOSITE_ONLY_KEYS = ("member_inputs", "member_input_sha256", "member_output_sha256")
# §2.6 composite wire: three exact member objects.
_MEMBER_INPUT_KEYS: dict[str, tuple[str, ...]] = {
    "enforcement": ("binding_slice_sha256", "enforcement_source_sha256"),
    "mcp": ("codex_posture_slice_sha256", "manifest_mcp_slice_sha256",
            "mcp_source_path", "mcp_source_sha256"),
    "shared": _RENDERER_INPUT_KEYS,
}


@dataclass(frozen=True)
class LockEntryV2:
    """One verified v2 entry (closed union member)."""

    entry_kind: str
    owner: str
    surface_members: tuple[str, ...]
    strategy: str
    normalization_policy: str
    output_sha256: str
    inputs: dict[str, Any] | None
    member_inputs: dict[str, dict[str, Any]] | None
    member_input_sha256: dict[str, str] | None
    member_output_sha256: dict[str, str] | None


@dataclass(frozen=True)
class VerifiedLockV2:
    """Schema-verified v2 envelope as a per-path ownership ledger (AC-05)."""

    generator_protocol_version: int
    entries: dict[str, LockEntryV2]  # key = normalized repo-relative output path

    def surface_owned_keys(self, surface: str) -> tuple[str, ...]:
        """Orphan detection runs per `surface -> owned lock keys` (plan §2.6),
        not an if/else over a skills/mcp dichotomy."""
        return tuple(
            sorted(k for k, e in self.entries.items() if surface in e.surface_members)
        )


def _require_hex64(value: Any, where: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise LockVerificationError(
            f"{where} must be a lowercase 64-hex SHA-256 string (got {value!r})"
        )
    return value


def _require_version(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LockVerificationError(f"{where} must be a JSON integer >= 1")
    return value


def _require_str(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise LockVerificationError(f"{where} must be a non-empty JSON string")
    return value


def _verify_input_value(key: str, value: Any, where: str) -> None:
    if key in ("wildcard_expansions", "wildcard_expansions_sha256"):
        return  # verified structurally by _verify_wildcards
    if key.endswith("_sha256"):
        _require_hex64(value, f"{where}.{key}")
    elif key.endswith("_version"):
        _require_version(value, f"{where}.{key}")
    elif key.endswith("_path"):
        safe_output_path(_require_str(value, f"{where}.{key}"))
    else:
        _require_str(value, f"{where}.{key}")


def _verify_wildcards(inputs: dict[str, Any], where: str) -> None:
    """§2.8.3 wildcard expansion wire: sorted patterns, non-empty sorted deduped
    resolved_ids, digest over the canonical array — recomputed, never trusted."""
    expansions = inputs.get("wildcard_expansions")
    if not isinstance(expansions, list):
        raise LockVerificationError(f"{where}.wildcard_expansions must be an array")
    seen_patterns: list[str] = []
    for item in expansions:
        if not isinstance(item, dict) or set(item) != {"pattern", "resolved_ids"}:
            raise LockVerificationError(
                f"{where}.wildcard_expansions items need exact keys"
                " {pattern, resolved_ids}"
            )
        pattern = _require_str(item["pattern"], f"{where}.wildcard_expansions.pattern")
        ids = item["resolved_ids"]
        if (
            not isinstance(ids, list)
            or not ids
            or any(not isinstance(i, str) or not i for i in ids)
            or ids != sorted(set(ids))
        ):
            raise LockVerificationError(
                f"{where}.wildcard_expansions[{pattern!r}].resolved_ids must be a"
                " non-empty sorted deduplicated string array"
            )
        seen_patterns.append(pattern)
    if seen_patterns != sorted(set(seen_patterns)):
        raise LockVerificationError(
            f"{where}.wildcard_expansions patterns must be sorted and unique"
        )
    declared = _require_hex64(
        inputs.get("wildcard_expansions_sha256"),
        f"{where}.wildcard_expansions_sha256",
    )
    if declared != sha256_of_canonical(expansions):
        raise LockVerificationError(
            f"{where}.wildcard_expansions_sha256 does not match the canonical"
            " array digest (expansion set changed without a re-render)"
        )


def _verify_owner_for_key(kind: str, key: str, owner: str) -> None:
    """Owner and entry key must be mutually reconstructible (plan §2.6)."""
    skills_prefix = SKILLS_RELDIR.as_posix() + "/"
    if kind in ("skill-byte-copy", "skill-translated"):
        expected_prefix = "capability:"
        if not owner.startswith(expected_prefix):
            raise LockVerificationError(
                f"{kind} owner must be 'capability:<id>' (got {owner!r})"
            )
        cap_id = owner[len(expected_prefix):]
        if _SKILL_KEY.fullmatch(cap_id) is None:
            raise LockVerificationError(f"owner capability id {cap_id!r} invalid")
        if key != f"{skills_prefix}{cap_id}/SKILL.md":
            raise LockVerificationError(
                f"entry key {key!r} does not derive from owner {owner!r}"
                f" (expected {skills_prefix}{cap_id}/SKILL.md)"
            )
    elif kind == "skills-readme":
        if owner != "system:skills-readme" or key != SKILLS_README_KEY:
            raise LockVerificationError(
                f"skills-readme requires owner 'system:skills-readme' at"
                f" {SKILLS_README_KEY!r} (got owner {owner!r}, key {key!r})"
            )
    elif kind in ("codex-config-mcp", "codex-config-composite"):
        if owner != "system:codex-config" or key != CODEX_LOCK_KEY:
            raise LockVerificationError(
                f"{kind} requires owner 'system:codex-config' at"
                f" {CODEX_LOCK_KEY!r} (got owner {owner!r}, key {key!r})"
            )
    elif kind == "codex-hook":
        if owner != "system:codex-hooks" or key != CODEX_HOOKS_KEY:
            raise LockVerificationError(
                f"codex-hook requires owner 'system:codex-hooks' at"
                f" {CODEX_HOOKS_KEY!r} (got owner {owner!r}, key {key!r})"
            )
    elif kind == "codex-rule":
        if not key.startswith(CODEX_RULES_PREFIX) or not key.endswith(CODEX_RULES_SUFFIX):
            raise LockVerificationError(
                f"codex-rule key {key!r} must live under {CODEX_RULES_PREFIX!r}"
                f" with the {CODEX_RULES_SUFFIX!r} suffix"
            )
        if owner != f"system:codex-rules:{key}":
            raise LockVerificationError(
                f"codex-rule owner {owner!r} must be 'system:codex-rules:{key}'"
            )


def _verify_composite_members(entry: dict[str, Any], where: str) -> None:
    member_inputs = entry.get("member_inputs")
    if not isinstance(member_inputs, dict) or set(member_inputs) != set(_MEMBER_INPUT_KEYS):
        raise LockVerificationError(
            f"{where}.member_inputs needs exact members"
            " {enforcement, mcp, shared}"
        )
    for member, keys in _MEMBER_INPUT_KEYS.items():
        node = member_inputs[member]
        if not isinstance(node, dict) or set(node) != set(keys):
            raise LockVerificationError(
                f"{where}.member_inputs.{member} needs exact keys {sorted(keys)}"
            )
        for k, v in node.items():
            _verify_input_value(k, v, f"{where}.member_inputs.{member}")
    input_hashes = entry.get("member_input_sha256")
    if not isinstance(input_hashes, dict) or set(input_hashes) != set(_MEMBER_INPUT_KEYS):
        raise LockVerificationError(
            f"{where}.member_input_sha256 needs exact members"
            " {enforcement, mcp, shared}"
        )
    for member in _MEMBER_INPUT_KEYS:
        declared = _require_hex64(
            input_hashes[member], f"{where}.member_input_sha256.{member}"
        )
        if declared != sha256_of_canonical(member_inputs[member]):
            raise LockVerificationError(
                f"{where}.member_input_sha256.{member} does not match the canonical"
                " serialization of member_inputs (member drift without re-render)"
            )
    output_hashes = entry.get("member_output_sha256")
    if not isinstance(output_hashes, dict) or set(output_hashes) != {"enforcement", "mcp"}:
        raise LockVerificationError(
            f"{where}.member_output_sha256 needs exact members {{enforcement, mcp}}"
        )
    for member, value in output_hashes.items():
        _require_hex64(value, f"{where}.member_output_sha256.{member}")


def verify_lock_v2_entry(key: str, raw: Any) -> LockEntryV2:
    """Verify one v2 entry against the closed union (plan §2.6)."""
    where = f"entries[{key!r}]"
    safe_output_path(key)
    if not isinstance(raw, dict):
        raise LockVerificationError(f"{where} must be an object")
    kind = raw.get("entry_kind")
    spec = KIND_SPECS.get(kind) if isinstance(kind, str) else None
    if spec is None:
        raise LockVerificationError(
            f"{where}.entry_kind {kind!r} is not in the closed union"
            f" {sorted(KIND_SPECS)}"
        )
    expected_keys = set(_COMMON_ENTRY_KEYS)
    if spec.input_keys is None:
        expected_keys |= set(_COMPOSITE_ONLY_KEYS)
    else:
        expected_keys.add("inputs")
    if set(raw) != expected_keys:
        raise LockVerificationError(
            f"{where} keys {sorted(raw)} do not match the exact {kind} set"
            f" {sorted(expected_keys)} (closed union — no optional key,"
            " no cross-kind combination)"
        )
    owner = _require_str(raw.get("owner"), f"{where}.owner")
    surfaces = raw.get("surface_members")
    if (
        not isinstance(surfaces, list)
        or tuple(surfaces) != spec.surface_members
    ):
        raise LockVerificationError(
            f"{where}.surface_members must be exactly"
            f" {list(spec.surface_members)} for {kind}"
        )
    if raw.get("strategy") != spec.strategy:
        raise LockVerificationError(
            f"{where}.strategy must be {spec.strategy!r} for {kind}"
        )
    if raw.get("normalization_policy") != spec.normalization_policy:
        raise LockVerificationError(
            f"{where}.normalization_policy must be {spec.normalization_policy!r}"
            f" for {kind}"
        )
    output_sha = _require_hex64(raw.get("output_sha256"), f"{where}.output_sha256")
    _verify_owner_for_key(kind, key, owner)

    inputs: dict[str, Any] | None = None
    member_inputs: dict[str, dict[str, Any]] | None = None
    member_input_sha: dict[str, str] | None = None
    member_output_sha: dict[str, str] | None = None
    if spec.input_keys is None:
        _verify_composite_members(raw, where)
        member_inputs = raw["member_inputs"]
        member_input_sha = raw["member_input_sha256"]
        member_output_sha = raw["member_output_sha256"]
    else:
        node = raw.get("inputs")
        if not isinstance(node, dict) or set(node) != set(spec.input_keys):
            raise LockVerificationError(
                f"{where}.inputs keys must be exactly {sorted(spec.input_keys)}"
                f" for {kind} (closed object)"
            )
        for k, v in node.items():
            _verify_input_value(k, v, f"{where}.inputs")
        if "wildcard_expansions" in spec.input_keys:
            _verify_wildcards(node, f"{where}.inputs")
        inputs = node
    return LockEntryV2(
        entry_kind=kind,
        owner=owner,
        surface_members=spec.surface_members,
        strategy=spec.strategy,
        normalization_policy=spec.normalization_policy,
        output_sha256=output_sha,
        inputs=inputs,
        member_inputs=member_inputs,
        member_input_sha256=member_input_sha,
        member_output_sha256=member_output_sha,
    )


def verify_lock_v2(raw: dict[str, Any]) -> VerifiedLockV2:
    """Verify the v2 envelope and derive per-path ownership (AC-05/AC-06).

    Any single malformed entry fails the WHOLE lock — a mixed ledger proves
    nothing about ownership; callers must then delete/write nothing.
    """
    if set(raw) != {"schema_version", "generator_protocol_version", "entries"}:
        raise LockVerificationError(
            "v2 lock top level must have exactly"
            " {schema_version, generator_protocol_version, entries}"
        )
    version = raw.get("schema_version")
    # JSON integers ONLY: bool is an int subclass and 2.0 == 2, so both would
    # slip through an equality check (Stage 11 #8).
    if isinstance(version, bool) or not isinstance(version, int) \
            or version != LOCK_SCHEMA_VERSION:
        raise LockVerificationError(
            f"lock schema_version {version!r} is not the JSON integer"
            f" {LOCK_SCHEMA_VERSION}"
        )
    protocol = raw.get("generator_protocol_version")
    if isinstance(protocol, bool) or not isinstance(protocol, int) \
            or protocol not in KNOWN_GENERATOR_PROTOCOLS:
        raise LockVerificationError(
            f"unknown generator_protocol_version {protocol!r}; known:"
            f" {sorted(KNOWN_GENERATOR_PROTOCOLS)} (zero delete/write)"
        )
    entries_raw = raw.get("entries")
    if not isinstance(entries_raw, dict):
        raise LockVerificationError("v2 lock 'entries' must be an object")
    entries: dict[str, LockEntryV2] = {}
    casefolded: dict[str, str] = {}
    for key, value in entries_raw.items():
        entry = verify_lock_v2_entry(key, value)
        folded = key.casefold()
        if folded in casefolded:
            raise LockVerificationError(
                f"entry key {key!r} casefold-collides with"
                f" {casefolded[folded]!r} — one owner per physical path"
            )
        casefolded[folded] = key
        entries[key] = entry
    return VerifiedLockV2(generator_protocol_version=int(protocol), entries=entries)


def classify_lock(raw: dict[str, Any]) -> str:
    """Version dispatch for the compatibility matrix (plan §2.6): returns
    'v1' (strict legacy flat map) or 'v2' (envelope discriminator present);
    anything else — envelope/flat-map hybrids, bare 64-hex values, wrong
    prefix/case, path-style skill keys — raises (malformed/mixed; zero
    delete/write). NOTE: this only picks the branch; each branch still runs
    its own full verifier."""
    if "schema_version" in raw:
        version = raw.get("schema_version")
        if not isinstance(version, bool) and isinstance(version, int) \
                and version == LOCK_SCHEMA_VERSION:
            return "v2"
        raise LockVerificationError(
            f"lock schema_version {version!r} unknown (known: legacy flat map"
            f" without the key, or {LOCK_SCHEMA_VERSION}); zero delete/write"
        )
    for key, value in raw.items():
        if key != CODEX_LOCK_KEY and _SKILL_KEY.fullmatch(key) is None:
            raise LockVerificationError(
                f"lock key {key!r} is neither a skill name, the reserved"
                f" {CODEX_LOCK_KEY!r} key, nor a v2 envelope field"
                " (malformed/mixed; zero delete/write)"
            )
        if not isinstance(value, str) or _LOCK_HASH.fullmatch(value) is None:
            raise LockVerificationError(
                f"lock entry {key!r} is not a 'sha256:<64 hex>' string"
                " (malformed owner ledger; zero delete/write)"
            )
    return "v1"


def lock_v2_canonical_text(raw: dict[str, Any]) -> str:
    """Canonical serialization of a VERIFIED v2 envelope (plan §2.6 wire):
    any on-disk bytes differing from this are drift."""
    verify_lock_v2(raw)
    return canonical_json_text(raw)


# ---------------------------------------------------------------------------
# Unified desired-artifact oracle normalization (plan §2.6):
#   canonicalize(actual, policy) == canonicalize(render_desired(inputs), policy)
# ---------------------------------------------------------------------------

NORMALIZATION_POLICIES = frozenset(
    {"raw-bytes-v1", "translated-utf8-lf-v1", "generated-utf8-lf-v1",
     "canonical-toml-v1", "canonical-json-v1"}
)


def canonicalize(data: bytes, normalization_policy: str) -> bytes:
    """Comparison normalization per entry class. `raw-bytes-v1` is the
    identity (byte-copy identity includes BOM/EOL — plan §2.4); every
    generated class is UTF-8 text compared LF-normalized so a checkout EOL
    filter cannot fabricate drift."""
    if normalization_policy == "raw-bytes-v1":
        return data
    if normalization_policy not in NORMALIZATION_POLICIES:
        raise LockVerificationError(
            f"unknown normalization_policy {normalization_policy!r}"
        )
    return data.replace(b"\r\n", b"\n")


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def module_source_sha256(module_file: Path) -> str:
    """Renderer module digest (v2 lock inputs): over LF-normalized module
    source bytes, so the digest is stable across checkout EOL filters
    (`* text=auto` makes raw working-tree bytes machine-dependent)."""
    return sha256_of_bytes(module_file.read_bytes().replace(b"\r\n", b"\n"))


# ------------------------------------------------------- §2.8.2 slice builders


def manifest_capability_slice(cap: dict[str, Any]) -> dict[str, Any]:
    """`manifest_slice_sha256` projection: the capability's exact
    id/required/projection/codex_carrier/carrier_binding/codex.support_mode/
    approval/enforcement fields (plan §2.8.2) — comments/mtime never enter."""
    codex = cap.get("codex") if isinstance(cap.get("codex"), dict) else {}
    return {
        "id": cap.get("id"),
        "required": cap.get("required"),
        "projection": cap.get("projection"),
        "codex_carrier": cap.get("codex_carrier"),
        "carrier_binding": cap.get("carrier_binding"),
        "codex.support_mode": codex.get("support_mode"),
        "approval": codex.get("approval"),
        "enforcement": codex.get("enforcement"),
    }


def manifest_mcp_slice(servers: dict[str, Any]) -> list[dict[str, Any]]:
    """`manifest_mcp_slice_sha256` projection: server records sorted by id."""
    out: list[dict[str, Any]] = []
    for name in sorted(servers):
        node = servers[name] if isinstance(servers[name], dict) else {}
        out.append({"id": name, **{k: node[k] for k in sorted(node)}})
    return out


def codex_posture_slice(posture: dict[str, Any]) -> dict[str, Any]:
    """`codex_posture_slice_sha256` projection: declared keys only."""
    return {k: posture[k] for k in sorted(posture)}
