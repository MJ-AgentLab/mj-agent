"""Validate ``evidence/ai-context-audit/`` quarterly A6 audit entries against SCHEMA.md §2.

Closes the durability gap disclosed in ``evidence/ai-context-audit/SCHEMA.md`` §2.1
(registered as #347 §三.2): the ``evidence/ai-context-audit/`` directory is OUTSIDE
``scripts/check_frontmatter.py``'s ``SCAN_ROOTS``, so nothing CI-enforces the §2
frontmatter schema of the quarterly A6 audit snapshots. Those entries use SCHEMA §2's
own schema (``type: ai-context-audit`` + ``cycle`` / ``auditor`` / ``scope`` /
``findings_summary`` / ``content_hash_snapshot``), NOT the canonical base schema
(``summary``/``owner``/``created``/``updated``/``state``/``track``), so they cannot be
folded into ``check_frontmatter.py`` — hence this dedicated §2 validator, exactly what
SCHEMA §2.1 prescribes ("若将来硬化，应加一支 evidence/ai-context-audit/ 专属 §2 validator").

Cycle entries are selected by the ``<cycle>.md`` FILENAME convention (SCHEMA §1/§3:
``YYYY-QN.md``), NOT by the ``type`` field's value — so a real cycle entry that omits or
mistypes ``type`` (or carries a UTF-8 BOM) is still validated and FAILED, rather than
silently skipped. Non-cycle ``.md`` (``SCHEMA.md``, ``*-investigation.md``) are reported
as skipped, honoring the Gate-5 investigation-(a) decision (validate ai-context-audit only).

Deliberate NON-goals (these are the drift the NEXT quarterly audit detects, not gate
violations — see SCHEMA §2.1 durability boundary + §1 quarterly-not-cron design):

- Does NOT recompute ``content_hash_snapshot`` hashes vs current files.
- Does NOT check that snapshot key-paths exist in the CURRENT repo (past write-once
  entries legitimately reference renamed paths, e.g. Q2's ``infra/docker/CLAUDE.md``).
- Does NOT do a blocking §2.1 face-set derivation match — the face-set is time-varying
  (15 surfaces in Q2, 23 in Q3), so a blocking match would false-fail on any
  skill/CLAUDE.md change and force a re-audit every commit.

The §2.1 face-set derivation IS machine-formed via ``--derive`` (a manual authoring aid
for the next auditor; NOT a CI gate), closing the other half of the disclosed gap: the
derivation previously had no machine form, so a future auditor could hard-code a stale
face-set — exactly the #304 -> Q2-15-stale failure that motivated §2.1's rewrite.

Usage::

    uv run python scripts/check_ai_context_audit.py            # validate (exit 0 ok / 1 violations)
    uv run python scripts/check_ai_context_audit.py --derive    # print current §2.1 face-set
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import frontmatter  # type: ignore[import-untyped]
import yaml

# Directory holding the write-once quarterly audit entries.
AUDIT_DIR = Path("evidence/ai-context-audit")
# Frozen infra-skill contract (single source for the §2.1 frozen-infra track).
FROZEN_CONTRACT = Path(
    "capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml"
)
SETTINGS = Path(".claude/settings.json")

AUDIT_TYPE = "ai-context-audit"
CYCLE_RE = re.compile(r"^\d{4}-Q[1-4]$")
# Cycle-entry filename convention (SCHEMA §1/§3): YYYY-QN.md.
CYCLE_FILE_RE = re.compile(r"^\d{4}-Q[1-4]\.md$")
# content_hash_snapshot values: lowercase sha256, 16-char truncated (current entries)
# or full 64-char. Canonical algo is lowercase hex (SCHEMA §2.1).
HEX_RE = re.compile(r"^([0-9a-f]{16}|[0-9a-f]{64})$")
# `permissions.ask` entries look like "Edit(./path/glob)".
ASK_PATH_RE = re.compile(r"^Edit\(\./(?P<path>.+)\)$")

REQUIRED_AUDIT_FIELDS: tuple[str, ...] = (
    "type",
    "cycle",
    "auditor",
    "scope",
    "findings_summary",
    "content_hash_snapshot",
)


def validate_audit_entry(meta: dict[str, Any]) -> list[str]:
    """Return violation messages for one ai-context-audit entry (empty = passes).

    Validates the SCHEMA.md §2 schema only (structure); see the module docstring
    for the deliberate non-goals (no hash recompute / no path-existence / no
    blocking derivation match).
    """
    violations: list[str] = []

    for field in REQUIRED_AUDIT_FIELDS:
        if field not in meta:
            violations.append(f"missing required field `{field}`")

    if meta.get("type") != AUDIT_TYPE:
        violations.append(f"type must be {AUDIT_TYPE!r} (got {meta.get('type')!r})")

    if "cycle" in meta:
        cycle = meta["cycle"]
        if not (isinstance(cycle, str) and CYCLE_RE.match(cycle)):
            violations.append(f"cycle={cycle!r} not YYYY-QN (e.g. 2026-Q2)")

    if "auditor" in meta:
        auditor = meta["auditor"]
        if not (isinstance(auditor, str) and auditor.strip()):
            violations.append("auditor must be a non-empty string")

    if "scope" in meta:
        scope = meta["scope"]
        if not (
            isinstance(scope, list)
            and len(scope) > 0
            and all(isinstance(s, str) and s.strip() for s in scope)
        ):
            violations.append("scope must be a non-empty list of non-empty strings")

    if "findings_summary" in meta:
        summary = meta["findings_summary"]
        if not (isinstance(summary, str) and summary.strip()):
            violations.append("findings_summary must be a non-empty string")

    if "content_hash_snapshot" in meta:
        snapshot = meta["content_hash_snapshot"]
        if not (isinstance(snapshot, dict) and len(snapshot) > 0):
            violations.append("content_hash_snapshot must be a non-empty mapping")
        else:
            for key, val in snapshot.items():
                if not (isinstance(key, str) and key.strip()):
                    violations.append(
                        f"content_hash_snapshot key {key!r} must be a non-empty path string"
                    )
                # An unquoted all-digit hash is YAML-coerced to int; coerce back to
                # str so a legitimately-computed all-digit hex still validates (a
                # leading-zero value still needs quoting in YAML — unrecoverable here).
                val_str = val if isinstance(val, str) else str(val)
                if not HEX_RE.match(val_str):
                    violations.append(
                        f"content_hash_snapshot[{key!r}]={val!r} not a "
                        f"16- or 64-char lowercase hex sha256"
                    )

    return violations


def _load_meta(path: Path) -> dict[str, Any]:
    """BOM-tolerant frontmatter metadata load (Windows editors may emit a UTF-8 BOM,
    which a plain utf-8 read leaves as a U+FEFF prefix that hides the leading ``---``)."""
    text = path.read_text(encoding="utf-8-sig")
    return frontmatter.loads(text).metadata


def find_cycle_entries(repo_root: Path) -> tuple[list[Path], list[Path]]:
    """Return ``(cycle_entries, other_md)`` split by the ``<cycle>.md`` filename
    convention (SCHEMA §1/§3). Filename-based selection (not ``type``-based) ensures a
    real cycle entry with a missing/mistyped ``type`` — or a UTF-8 BOM — is still
    validated (and failed), while investigation / SCHEMA files (non-cycle names) are
    reported as skipped.
    """
    audit_dir = repo_root / AUDIT_DIR
    cycle: list[Path] = []
    other: list[Path] = []
    if not audit_dir.exists():
        return cycle, other
    for md in sorted(audit_dir.glob("*.md")):
        rel = md.relative_to(repo_root)
        (cycle if CYCLE_FILE_RE.match(md.name) else other).append(rel)
    return cycle, other


def check(repo_root: Path) -> dict[Path, list[str]]:
    """Return ``{rel: violations}`` for every cycle entry with §2 schema violations."""
    cycle, _other = find_cycle_entries(repo_root)
    bad: dict[Path, list[str]] = {}
    for rel in cycle:
        try:
            meta = _load_meta(repo_root / rel)
        except Exception as exc:  # noqa: BLE001 — yaml errors are user-facing
            bad[rel] = [f"frontmatter parse error: {exc}"]
            continue
        violations = validate_audit_entry(meta)
        if violations:
            bad[rel] = violations
    return bad


def run(repo_root: Path) -> int:
    """Validate all cycle entries; print a report; return exit code (0 ok / 1 violations)."""
    cycle, other = find_cycle_entries(repo_root)
    for rel in other:
        print(f"skip (not a <cycle>.md entry): {rel}")
    bad = check(repo_root)
    if not bad:
        print(f"OK: {len(cycle)} cycle audit entries pass SCHEMA §2 schema check")
        return 0
    print(
        f"FAIL: {len(bad)} of {len(cycle)} cycle audit entries have schema violations\n",
        file=sys.stderr,
    )
    for rel, violations in sorted(bad.items()):
        print(f"  {rel}", file=sys.stderr)
        for violation in violations:
            print(f"    - {violation}", file=sys.stderr)
    print(
        "\nFix per evidence/ai-context-audit/SCHEMA.md §2 (ai-context-audit frontmatter schema).",
        file=sys.stderr,
    )
    return 1


# ---- §2.1 face-set derivation (machine form; `--derive` aid, NOT a CI gate) ----


def _git_tracked_claude_md(repo_root: Path) -> set[str]:
    """CLAUDE.md track: git-tracked ``**/CLAUDE.md`` (root + each subdir)."""
    proc = subprocess.run(
        ["git", "ls-files", "*CLAUDE.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip() == "CLAUDE.md" or line.strip().endswith("/CLAUDE.md")
    }


def _ask_glob_md(repo_root: Path) -> set[str]:
    """必停 markdown (settings) track: ``.md`` files matched by ``permissions.ask`` globs.

    Data-boundary ``.py`` / ``.yaml`` ask entries are excluded (not markdown; the
    regex-strip hash algo does not apply to them) — see SCHEMA §2.1.
    """
    settings = json.loads((repo_root / SETTINGS).read_text(encoding="utf-8"))
    faces: set[str] = set()
    for entry in settings.get("permissions", {}).get("ask", []):
        match = ASK_PATH_RE.match(entry)
        if not match:
            continue
        pattern = match.group("path")
        if not pattern.endswith(".md"):
            continue
        for path in repo_root.glob(pattern):
            if path.is_file():
                faces.add(path.relative_to(repo_root).as_posix())
    return faces


def _frozen_infra(repo_root: Path) -> set[str]:
    """Frozen-infra track: ``.claude/skills/mj-agent-infra-*/SKILL.md`` per contract ``skills[]``."""
    contract = yaml.safe_load((repo_root / FROZEN_CONTRACT).read_text(encoding="utf-8"))
    return {s["file"] for s in contract.get("skills", []) if isinstance(s, dict) and "file" in s}


def derive_face_set(repo_root: Path) -> list[str]:
    """Derive the §2.1 ``content_hash_snapshot`` face-set from current repo state.

    Union of the CLAUDE.md track and the 必停 markdown track (ask ``.md`` globs ∪
    frozen infra). Returns a sorted list. The count is an OBSERVED value, not a
    spec — it changes as the repo changes (that is why this is an authoring aid,
    not a blocking gate; see module docstring).
    """
    faces = _git_tracked_claude_md(repo_root)
    faces |= _ask_glob_md(repo_root)
    faces |= _frozen_infra(repo_root)
    return sorted(faces)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate evidence/ai-context-audit/ ai-context-audit entries (SCHEMA §2)."
    )
    parser.add_argument(
        "--derive",
        action="store_true",
        help="Print the current §2.1 face-set (manual authoring aid; NOT a gate).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent

    if args.derive:
        faces = derive_face_set(repo_root)
        print(f"§2.1 derived content_hash_snapshot face-set ({len(faces)} surfaces):")
        for face in faces:
            print(f"  {face}")
        return 0

    return run(repo_root)


if __name__ == "__main__":
    sys.exit(main())
