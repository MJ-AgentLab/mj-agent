"""scripts/sdd/check_claude_skill_contracts.py — Phase M2 implementation.

Validates `.claude/skills/*/SKILL.md` against ADR-013 native 2-field schema +
ADR-016 namespace pattern + ADR-013 description quality bar.

Per blueprint §6 Phase M2 §3 + ADR-031 §5 claude-code-skill adapter. Phase M2
warning mode; M3 strict.

Mode A only (ADR-013 schema linter): scan ALL `.claude/skills/*/SKILL.md`
regardless of capability contracts, enforcing the ADR-013 native 2-field schema
(surfaced ≥5 natural WARN across 34 SKILLs per the Subagent C survey).

The proposed "Mode B" — read `capabilities/*/contracts/claude-skill.contract.yml`
to validate the contract's `skill_path` resolves + matches spec — was WITHDRAWN
(M4-FU-V4-MODE-B-IMPL): Mode-A schema-linting is canonical + adequate, and the
locked infra SKILLs' content_hash/description_hash freeze is enforced separately
via the `mcp-server-trust-posture-change` HITL, not by this linter.

Validates (per user augmentation + ADR-013 + ADR-016):
  - **Schema (ADR-013 native; 2-field)**: ONLY `name` + `description`; any
    extra frontmatter key → WARN (ADR-013 native style is non-strict).
  - **Description quality**: `len(description) >= 200` chars → WARN if less.
  - **Reverse-trigger present**: description contains `"Do not use for:"`
    (anti-over-broad triggering) → WARN if missing.
  - **Namespace pattern** (ADR-016): `name` matches `mj-agent-<group>-<verb>`
    where `<group>` ∈ {flow, git, doc, runtime, infra} → WARN on mismatch
    (NOT FAIL — RD3=C 不重命名 stance).

All findings are WARN (not FAIL) because ADR-013 native style is intentionally
non-strict; per RD3=C the existing 34 SKILLs are preserved as-is and any
deviations from ADR-013 ideal are tracked as improvement backlog.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.sdd._common import (  # noqa: E402
    Severity,
    Summary,
    build_argparser,
    parse_native_frontmatter,
    resolve_display_path,
)

_ADR_013_REQUIRED_KEYS = frozenset({"name", "description"})
_ADR_013_DESCRIPTION_MIN_CHARS = 200
_ADR_013_REVERSE_TRIGGER = "Do not use for:"
_ADR_016_NAMESPACE_PATTERN = re.compile(r"^mj-agent-(flow|git|doc|runtime|infra)-[a-z][a-z0-9-]*$")


def _validate_skill_md(skill_path: Path, repo_root: Path) -> Summary:
    """Validate one .claude/skills/<name>/SKILL.md against ADR-013 + ADR-016."""
    summary = Summary()
    display = resolve_display_path(skill_path, repo_root)

    text = skill_path.read_text(encoding="utf-8")
    fm, _body = parse_native_frontmatter(text)
    if fm is None:
        summary.add(Severity.WARN, f"{display}: no frontmatter block (ADR-013 requires `name` + `description`)")
        return summary

    fm_keys = set(fm.keys())
    extra_keys = fm_keys - _ADR_013_REQUIRED_KEYS
    if extra_keys:
        summary.add(Severity.WARN, f"{display}: frontmatter has extra ADR-013 keys (deviation): {sorted(extra_keys)}")

    missing = _ADR_013_REQUIRED_KEYS - fm_keys
    if missing:
        summary.add(Severity.WARN, f"{display}: frontmatter missing required ADR-013 keys: {sorted(missing)}")

    name = fm.get("name")
    description = fm.get("description")

    if isinstance(description, str):
        if len(description) < _ADR_013_DESCRIPTION_MIN_CHARS:
            summary.add(Severity.WARN, f"{display}: description length {len(description)} < {_ADR_013_DESCRIPTION_MIN_CHARS} (ADR-013 quality bar)")
        if _ADR_013_REVERSE_TRIGGER not in description:
            summary.add(Severity.WARN, f"{display}: description missing reverse-trigger block ({_ADR_013_REVERSE_TRIGGER!r}; ADR-013 anti-over-broad triggering)")
    elif description is not None:
        summary.add(Severity.WARN, f"{display}: description is not a string (got {type(description).__name__})")

    if isinstance(name, str):
        if not _ADR_016_NAMESPACE_PATTERN.match(name):
            summary.add(Severity.WARN, f"{display}: name {name!r} does not match ADR-016 pattern mj-agent-<group>-<verb> where group in {{flow,git,doc,runtime,infra}} (RD3=C — not renamed; backlog)")
        dirname = skill_path.parent.name
        if dirname != name:
            summary.add(Severity.WARN, f"{display}: name {name!r} != directory {dirname!r} (ADR-013 convention: name matches dirname)")

    if summary.warn_count == 0:
        summary.add_aggregate_pass(n=1, message=f"{display}: ADR-013 schema + ADR-016 namespace + description quality all PASS")

    return summary


def _discover_skills(repo_root: Path) -> list[Path]:
    """Discover all .claude/skills/<name>/SKILL.md files."""
    skills_dir = repo_root / ".claude" / "skills"
    if not skills_dir.exists():
        return []
    return sorted(skills_dir.glob("*/SKILL.md"))


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser(
        script_name="check_claude_skill_contracts.py",
        description=(
            "Validate .claude/skills/*/SKILL.md against ADR-013 native schema "
            "(name + description only) + description quality bar (≥200 chars + "
            "'Do not use for:' reverse-trigger) + ADR-016 namespace pattern. "
            "Phase M2 warning mode (all findings WARN; RD3=C preserves existing). "
            "Phase M3 --strict for blocking."
        ),
        contract_filename="SKILL.md",
    )
    args = parser.parse_args(argv)
    repo_root = Path.cwd()
    skill_files = _discover_skills(repo_root)

    if args.dry_run:
        print(f"[dry-run] check_claude_skill_contracts.py — Phase M2 impl; found {len(skill_files)} SKILL.md in .claude/skills/")
        return 0

    if not skill_files:
        print("no .claude/skills/*/SKILL.md found")
        return 0

    print(f"check_claude_skill_contracts.py — validating {len(skill_files)} SKILL.md (ADR-013 native + ADR-016 namespace)")

    total = Summary()
    for skill_path in skill_files:
        sub = _validate_skill_md(skill_path, repo_root)
        sub.print_messages()
        total.merge(sub)

    print("\n=== Summary ===")
    print(f"PASS skills: {total.pass_count} / WARN findings: {total.warn_count} / FAIL: {total.fail_count}")
    return total.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
