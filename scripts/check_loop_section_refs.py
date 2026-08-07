#!/usr/bin/env python3
"""Kernel section-reference integrity gate (#453).

``sdd/workflows/execution-loop.md`` is the kernel home of the 17-stage loop.
Its ``§4`` **changed meaning** during the M6 PR4 refactor: in the historical
source (HITL_Prompt STANDARD, now under ``archive/rule/``) ``§4.1``-``§4.15``
were the *per-stage prompts*; in the live kernel ``§4`` is the *Stage → Skill
映射表* (ported from HITL_Prompt ``§5``). The kernel explicitly does **not**
re-port the per-stage prompts -- they are owned by ``.claude/skills/mj-agent-*``.

Cross-references written before / across that rename therefore point at
sections that do not exist (``§4.3`` ``§4.4`` ``§4.5`` ``§4.6`` ``§4.7``
``§4.13`` ``§6.6`` ``§11`` ``§12``). No existing gate sees this:
``check_wikilinks.py`` deliberately skips ``#anchor`` fragments and these are
not wikilinks at all but plain prose; ``find_stale_docs.py`` matches only
backtick-quoted *paths*; ``check_frontmatter.py`` reads only frontmatter.

This gate closes that hole with two machine-checkable rules:

``dangling-section``
    A ``§N.M`` token on a line that names ``execution-loop``, where ``N.M`` is
    absent from the heading set **parsed out of the kernel file itself**.
``positional-hitl-index``
    A ``必停 <n>`` positional index (e.g. ``必停 10/11``). The ``§3.1`` list is
    re-orderable -- general items already grew 9 → 12, silently shifting the
    mj-agent-specific four from 10-13 to 13-16. Reference the named enum
    (``runtime-skill-content-change`` etc., ``policies/ai-agent.md`` §4) instead.
    A *count* (``必停 4 项`` / ``通用必停 12 项``) is not an index, and is not
    flagged -- the possessive quantifier stops the digit run from backtracking
    into a shorter match that would slip past the ``项`` guard.

Two exemptions keep the signal honest:

1. **Archived-source attribution** -- a line naming any ``ARCHIVED_SOURCE_MARKERS``
   entry is skipped whole. ``原 HITL_Prompt §4.7`` is a correct historical
   citation, not a defect (this is what keeps the 5 frozen ``infra-*`` skills
   out of the report, so they never need a content-hash re-freeze).
2. **Self-reference** -- a ``§N`` that resolves against the *containing*
   document's own heading set is skipped. ``policies/ai-agent.md`` saying
   "详 §9 + ``execution-loop.md`` §3.0" means *its own* §9.
3. **Explicit attribution** -- ``policies/documentation.md §5.3`` names its own
   document, so it is not a kernel citation. Naming the document is the
   authoring behaviour this gate wants to encourage, so it must not be
   punished. A ref attributed to the kernel itself stays checked.

**Known limitation (deliberate; recorded in ``sdd/gates.md`` §2)**: this gate
answers "does the cited section exist", not "does it still mean the same
thing". ``§4.1（Stage 0 Intake prompt）`` resolves cleanly yet is semantically
wrong, because ``§4.1`` is the orchestrator map. Semantic drift stays a human
duty -- open the target section before citing it.

**Scan face** covers *living instruction surfaces* only. ``CHANGELOG.md``,
``plans/``, ``evidence/`` and ``archive/`` are historical ledgers: they record
what the numbering was at the time and must not be rewritten, so flagging them
would produce permanent un-fixable noise.

Usage::

    python scripts/check_loop_section_refs.py

Output: human-readable findings to stdout; JSON summary to stderr.
Exit code: 0 clean, 1 on any violation, 2 on a self-check failure.

Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Scan face -- living instruction surfaces. ``.claude`` carries the in-tree
# workflow skills where these cross-references live; the rest mirrors
# check_wikilinks.py WALK_DIRS / find_stale_docs.py so the gates share one
# mental model. ``plans`` is deliberately ABSENT (see module docstring).
WALK_DIRS = (
    ".claude",
    "capabilities",
    "decisions",
    "docs",
    "policies",
    "sdd",
)
# Root files minus CHANGELOG.md -- an append-only ledger whose past entries
# legitimately quote the numbering in force when they were written.
WALK_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "GLOSSARY.md",
    "CLAUDE.md",
    "AGENTS.md",
)

# ``archive/`` is frozen by policies/archive.md -- its section numbers describe
# the archived documents themselves. ``.agents/`` holds byte-identical
# projections of whitelisted sources, so scanning it would double-report.
SKIP_PATH_PARTS = frozenset(
    {".venv", ".git", "archive", "node_modules", ".agents", "__pycache__"}
)

# A line naming any of these plausibly cites that (archived) document's own
# numbering rather than the live kernel's.
ARCHIVED_SOURCE_MARKERS = (
    "HITL_Prompt",
    "Meta §",
    "Meta v2.0",
    "Meta v2.1",
    "Meta v2.2",
    "Code_Side",
    "Agent_Side",
)

KERNEL_REL = Path("sdd/workflows/execution-loop.md")
KERNEL_NAME = "execution-loop"

_HEADING_RE = re.compile(r"^#{1,6}\s+§?(\d+(?:\.\d+)*)\s")
_SECTION_REF_RE = re.compile(r"§(\d+(?:\.\d+)*)")
# An explicitly attributed reference -- ``policies/documentation.md §5.3``.
# The document is named right there, so it is not a kernel citation at all
# (unless the document named IS the kernel, which stays checked). Wikilinks
# such as ``[[.../execution-loop|execution-loop]] §4.7`` do NOT match: they end
# in ``]]``, not ``.md``.
_ATTRIBUTED_REF_RE = re.compile(r"(?P<doc>[^\s`|\[\]]+\.md)\s*§(?P<sec>\d+(?:\.\d+)*)")
# ``必停 10`` / ``必停 10/11`` but NOT ``必停 4 项`` (a count). The possessive
# ``++`` / ``*+`` forbid backtracking, so ``必停 12 项`` cannot degrade into a
# spurious ``必停 1`` match that satisfies the ``(?!\s*项)`` guard.
_POSITIONAL_RE = re.compile(r"必停\s*(\d++(?:\s*/\s*\d++)*+)(?!\s*项)")


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_sections(path: Path) -> set[str]:
    """Parse the ``§N.M`` heading set out of a document body.

    Deliberately content-derived: hard-coding the list is exactly the failure
    this gate exists to prevent.
    """
    text = path.read_text(encoding="utf-8-sig")
    return {m.group(1) for line in text.splitlines() if (m := _HEADING_RE.match(line)) is not None}


def parse_kernel_sections(kernel_path: Path) -> set[str]:
    """Kernel heading set, with a fail-closed guard.

    Raises on an empty parse so the gate can never pass vacuously by reading
    nothing -- the ``check_frontmatter`` fail-open precedent (#429).
    """
    sections = parse_sections(kernel_path)
    if not sections:
        raise ValueError(
            f"parsed zero section headings from {kernel_path} -- "
            "refusing to run (would pass vacuously)"
        )
    return sections


def iter_scanned_files(repo_root: Path) -> list[Path]:
    """Every markdown file on the scan face, content-blind."""
    found: list[Path] = []
    for rel_dir in WALK_DIRS:
        base = repo_root / rel_dir
        if not base.is_dir():
            continue
        for path in base.rglob("*.md"):
            if SKIP_PATH_PARTS & set(path.relative_to(repo_root).parts):
                continue
            found.append(path)
    for rel_file in WALK_FILES:
        candidate = repo_root / rel_file
        if candidate.is_file():
            found.append(candidate)
    return sorted(set(found))


def check_line(
    line: str, kernel_sections: set[str], own_sections: frozenset[str] = frozenset()
) -> list[tuple[str, str]]:
    """Return ``(rule, detail)`` violations for one line."""
    findings: list[tuple[str, str]] = []

    if KERNEL_NAME in line and not any(m in line for m in ARCHIVED_SOURCE_MARKERS):
        # Positions of §refs that name their own (non-kernel) document.
        attributed_elsewhere = {
            m.start("sec") - 1
            for m in _ATTRIBUTED_REF_RE.finditer(line)
            if not m.group("doc").endswith(f"{KERNEL_NAME}.md")
        }
        for m in _SECTION_REF_RE.finditer(line):
            ref = m.group(1)
            if ref in kernel_sections or ref in own_sections or m.start() in attributed_elsewhere:
                continue
            findings.append(
                (
                    "dangling-section",
                    f"§{ref} is cited as {KERNEL_NAME} but that section does not exist",
                )
            )

    for idx in _POSITIONAL_RE.findall(line):
        findings.append(
            (
                "positional-hitl-index",
                f"必停 {idx} is a positional index; cite the named enum instead",
            )
        )

    return findings


def _sort_key(section: str) -> list[int]:
    return [int(part) for part in section.split(".")]


def main(argv: list[str] | None = None, repo_root: Path | None = None) -> int:
    _ = argv
    root = default_repo_root() if repo_root is None else repo_root

    kernel_path = root / KERNEL_REL
    if not kernel_path.is_file():
        print(f"ERROR: kernel document not found: {kernel_path}", file=sys.stderr)
        return 2
    try:
        kernel_sections = parse_kernel_sections(kernel_path)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    violations: list[dict[str, object]] = []
    for path in iter_scanned_files(root):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError) as exc:
            print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        own = frozenset(parse_sections(path))
        for lineno, line in enumerate(text.splitlines(), 1):
            for rule, detail in check_line(line, kernel_sections, own):
                violations.append(
                    {
                        "file": path.relative_to(root).as_posix(),
                        "line": lineno,
                        "rule": rule,
                        "detail": detail,
                        "text": line.strip()[:200],
                    }
                )

    if violations:
        print(f"Kernel section-reference violations: {len(violations)}\n")
        current = ""
        for v in violations:
            if v["file"] != current:
                current = str(v["file"])
                print(f"-- {current}")
            print(f"   :{v['line']}  [{v['rule']}] {v['detail']}")
            print(f"      | {v['text']}")
        print(
            f"\nLive {KERNEL_NAME} sections: "
            f"{', '.join('§' + s for s in sorted(kernel_sections, key=_sort_key))}"
        )
    else:
        print(f"Kernel section-reference check: OK ({len(kernel_sections)} live sections parsed)")

    json.dump(
        {"violations": len(violations), "sections": len(kernel_sections), "findings": violations},
        sys.stderr,
    )
    sys.stderr.write("\n")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
