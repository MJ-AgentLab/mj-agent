"""Validate canonical doc frontmatter against the v2.1 trio schema.

Purpose: locks down the Phase 1 末 治理 collapse — every canonical doc
under `docs/`, `plans/`, `src/mj_agent/skills/`, and
`src/mj_agent/prompts/` must declare `track ∈ {code, agent,
engineering-workflow, shared}` explicitly (per Meta_Framework v2.1
§4.3.1; v2.0 only allowed code/agent/shared) plus the required base
fields (per Code_Side §7.1 A2 + Agent_Side §7.1).

Usage::

    uv run python scripts/check_frontmatter.py
    # exit 0 if all docs valid; non-zero with per-doc reasons otherwise

Run as a CI gate alongside ruff / mypy / pytest (`.github/workflows/ci.yml`)
to catch frontmatter regressions at PR time instead of relying on the
honor system.

Scope:
- Cross-cutting requirements only (type, summary, owner, created,
  updated, state, track). Per-type rules (e.g. SPEC needs version,
  ADR needs decision, EVAL needs dataset_path) are left for Phase 2
  expansion when the team wants stricter enforcement.
- Templates under `docs/_templates/` are skipped — they're placeholder
  scaffolds, not real canonical docs.
- Markdown files without YAML frontmatter are skipped (not canonical).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import frontmatter  # type: ignore[import-untyped]

# Roots scanned for canonical docs.
SCAN_ROOTS = (
    Path("docs"),
    Path("plans"),
    Path("src/mj_agent/skills"),
    Path("src/mj_agent/prompts"),
)

# Path fragments to skip even within scanned roots.
SKIP_PATH_PARTS = (
    ("docs", "_templates"),  # template scaffolds
)

# Required base fields on every canonical doc (Code_Side §7.1 A2 + Agent_Side §7.1).
REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"type", "summary", "owner", "created", "updated", "state", "track"}
)

# Allowed enum values.
TRACK_VALUES: frozenset[str] = frozenset(
    {"code", "agent", "engineering-workflow", "shared"}
)
STATE_VALUES: frozenset[str] = frozenset({"draft", "active", "deprecated", "completed"})


def is_skipped(rel_path: Path) -> bool:
    parts = rel_path.parts
    return any(
        len(parts) >= len(skip) and parts[: len(skip)] == skip
        for skip in SKIP_PATH_PARTS
    )


def validate(meta: dict[str, Any], rel_path: Path) -> list[str]:
    """Return a list of violation messages for one doc. Empty = passes."""
    violations: list[str] = []

    # 1. Required fields presence (skipped if frontmatter is empty — that means
    # the file is non-canonical; caller filters those out before calling here).
    missing = REQUIRED_FIELDS - meta.keys()
    for field in sorted(missing):
        violations.append(f"missing required field `{field}`")

    # 2. Enum value checks (only when the field is present; missing reported above).
    track = meta.get("track")
    if track is not None and track not in TRACK_VALUES:
        violations.append(
            f"track={track!r} not in {sorted(TRACK_VALUES)}"
        )
    state = meta.get("state")
    if state is not None and state not in STATE_VALUES:
        violations.append(
            f"state={state!r} not in {sorted(STATE_VALUES)}"
        )

    # 3. Type-specific required fields (ADR-022 C.3.1).
    # Active or completed docs must declare type-specific frontmatter
    # (e.g., RUNBOOK last-verified, POSTMORTEM severity etc.). Draft and
    # deprecated states are lenient — fields can be absent during early
    # authoring or after archival.
    type_specific_required: dict[str, tuple[str, ...]] = {
        "runbook": ("last-verified",),
        "postmortem": ("severity", "incident-date", "resolved-at"),
        "assessment": ("dimensions", "period"),
        "issue": ("priority", "risk-level"),
    }
    type_value = meta.get("type")
    if state in ("active", "completed") and isinstance(type_value, str):
        for field in type_specific_required.get(type_value, ()):
            if field not in meta:
                violations.append(
                    f"missing type-specific field `{field}` "
                    f"(required for type={type_value!r} when state={state!r}; ADR-022)"
                )

    return violations


def find_canonical_docs(repo_root: Path) -> list[Path]:
    """Return relative paths of all .md files under the scan roots that have
    YAML frontmatter (i.e. start with `---`).
    """
    out: list[Path] = []
    for root in SCAN_ROOTS:
        abs_root = repo_root / root
        if not abs_root.exists():
            continue
        for md in abs_root.rglob("*.md"):
            rel = md.relative_to(repo_root)
            if is_skipped(rel):
                continue
            try:
                first_chars = md.read_text(encoding="utf-8").lstrip()[:4]
            except (OSError, UnicodeDecodeError):
                continue
            if first_chars.startswith("---"):
                out.append(rel)
    return sorted(out)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    docs = find_canonical_docs(repo_root)

    total = len(docs)
    bad: dict[Path, list[str]] = {}

    for rel in docs:
        try:
            post = frontmatter.load(repo_root / rel)
        except Exception as exc:  # noqa: BLE001 — yaml errors are user-facing
            bad[rel] = [f"frontmatter parse error: {exc}"]
            continue
        violations = validate(post.metadata, rel)
        if violations:
            bad[rel] = violations

    if not bad:
        print(f"OK: {total} canonical docs all pass frontmatter schema check")
        return 0

    print(
        f"FAIL: {len(bad)} of {total} canonical docs have frontmatter violations\n",
        file=sys.stderr,
    )
    for rel, violations in sorted(bad.items()):
        print(f"  {rel}", file=sys.stderr)
        for v in violations:
            print(f"    - {v}", file=sys.stderr)
    print(
        "\nFix per Meta_Framework v2.1 §4.3.1 (track field; "
        "code/agent/engineering-workflow/shared) + Code_Side v1.1 §7.1 A2 "
        "(required base fields) + Agent_Side v1.1 §7.1.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
