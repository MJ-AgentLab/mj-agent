"""Forward guard against cross-repo references drift back into mj-agent docs.

Purpose: after the 2026-05 cross-repo decoupling cleanup (PR #118, #121, plus
the PR landing this script), mj-agent docs should not reintroduce `mj-system`
or `派生自` markers in active prose. This script scans `docs/**/*.md` and
`CLAUDE.md` for forbidden patterns, with a narrow allow-list for legitimate
code-layer literals (Docker network names, env var namespaces, MCP server
identifiers) and the glossary file (which intentionally defines the
upstream-system relationship).

**Mode**: WARNING by default (exit 0 + print findings to stderr). This matches
the find_stale_docs.py warning-mode pattern: 4-week observation window before
upgrading to strict (blocking) mode. Set `MJ_AGENT_CHECK_REFS_STRICT=1` to
fail-fast (exit 1) on any forbidden pattern; flip the workflow gate to require
this once cleanup tail is complete.

Scope:
- Scans `docs/**/*.md` + repo-root `CLAUDE.md` + `README.md`
- **Skips** `docs/archive/**` (frozen snapshots per ADR-019)
- **Skips** `plans/**` (working docs; historical references preserved)
- **Skips** `CHANGELOG.md` (Keep-a-Changelog: do not rewrite history)
- **Skips** in-source canonical (`src/mj_agent/skills/**/SKILL.md`,
  `src/mj_agent/prompts/*.md`) — those are runtime LLM context, governed
  by Agent_Side framework instead

Allow-list (legitimate code-layer literals; matched verbatim):
- `mj-system-backend-network`  (Docker network name)
- `mj-postgres`                 (Docker container name in upstream stack)
- `MJ_SYS_*`                    (env var namespace literal; mentioned as
                                 disambiguation against `MJ_AGENT_*`)
- `pg-mj-system-biz-*`          (MCP server name literal)

Glossary exemption: `docs/glossary/upstream_business_warehouse.md` defines
the term and necessarily references `mj-system` patterns. Entire file
exempt.

Usage::

    uv run python scripts/check_no_cross_repo_refs.py
    # exit 0 if clean (or only allow-list matches);
    # exit 1 if any forbidden bare `mj-system` or `派生自` outside allow-list

Run as a CI gate after scripts/check_frontmatter.py + check_wikilinks.py.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Roots to scan.
SCAN_ROOTS = (
    Path("docs"),
    Path("CLAUDE.md"),
    Path("README.md"),
)

# Path fragments to skip even within scanned roots.
SKIP_PATH_PARTS = (
    ("docs", "archive"),
)

# Specific file paths to skip (full glossary file).
SKIP_FILES = (
    Path("docs/glossary/upstream_business_warehouse.md"),
)

# Forbidden patterns (literal strings; case-sensitive).
FORBIDDEN_PATTERNS = (
    "mj-system",
    "派生自",
)

# Allow-list: lines containing ANY of these literal substrings are exempt
# from the forbidden-pattern check. These are real code-layer identifiers
# preserved per the D2 keep-runtime-fact decision, plus intra-mj-agent
# archive references (legitimate version-evolution lineage).
ALLOW_LITERAL_SUBSTRINGS = (
    # Code-layer literals (real deployment identifiers)
    "mj-system-backend-network",  # Docker network name
    "pg-mj-system-biz",            # MCP server name (5 variants)
    "MJ_SYS_",                     # env var namespace prefix
    # Glossary cross-refs (definition + onward references)
    "glossary/upstream_business_warehouse",
    # Intra-mj-agent archive references (legitimate version lineage)
    "[DEPRECATED]_",               # any wikilink/path to an archive file
    "archive/adr/",                # archive ADR path prefix
    "archive/rule/",               # archive STANDARD path prefix
    # Cross-repo cleanup PR descriptions (PR/issue body text)
    "cross-repo decoupling",
    "cross-repo cleanup",
    # Keep-a-Changelog historical entries are auto-skipped via SKIP_FILES
    # (see CHANGELOG.md exclusion); plans/ historical likewise.
)


def is_skipped(rel_path: Path) -> bool:
    parts = rel_path.parts
    if any(
        len(parts) >= len(skip) and parts[: len(skip)] == skip
        for skip in SKIP_PATH_PARTS
    ):
        return True
    return rel_path in SKIP_FILES


def line_has_allowed_literal(line: str) -> bool:
    return any(allowed in line for allowed in ALLOW_LITERAL_SUBSTRINGS)


def scan_file(file_path: Path, rel_path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, matched_pattern, line_content) for violations."""
    violations: list[tuple[int, str, str]] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    for line_no, line in enumerate(content.splitlines(), start=1):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in line and not line_has_allowed_literal(line):
                violations.append((line_no, pattern, line.strip()))
                break  # one violation per line is enough
    return violations


def find_target_files(repo_root: Path) -> list[Path]:
    """Collect all target files (rel paths) per SCAN_ROOTS + skip rules."""
    out: list[Path] = []
    for root in SCAN_ROOTS:
        abs_root = repo_root / root
        if not abs_root.exists():
            continue
        if abs_root.is_file():
            if abs_root.suffix in (".md", ""):
                rel = abs_root.relative_to(repo_root)
                if not is_skipped(rel):
                    out.append(rel)
            continue
        for md in abs_root.rglob("*.md"):
            rel = md.relative_to(repo_root)
            if is_skipped(rel):
                continue
            out.append(rel)
    return sorted(out)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    files = find_target_files(repo_root)

    bad: dict[Path, list[tuple[int, str, str]]] = {}
    for rel in files:
        violations = scan_file(repo_root / rel, rel)
        if violations:
            bad[rel] = violations

    if not bad:
        print(f"OK: scanned {len(files)} files; no forbidden cross-repo refs")
        return 0

    strict = os.environ.get("MJ_AGENT_CHECK_REFS_STRICT") == "1"
    total_violations = sum(len(v) for v in bad.values())
    severity = "FAIL" if strict else "WARN"

    print(
        f"{severity}: {total_violations} forbidden cross-repo refs in {len(bad)} of "
        f"{len(files)} scanned files\n",
        file=sys.stderr,
    )
    for rel, violations in sorted(bad.items()):
        print(f"  {rel}", file=sys.stderr)
        for line_no, pattern, content in violations:
            content_excerpt = content[:120] + ("..." if len(content) > 120 else "")
            print(
                f"    line {line_no}: `{pattern}` — {content_excerpt}",
                file=sys.stderr,
            )
    print(
        "\nFix: replace prose `mj-system` → `上游业务系统` (see "
        "`docs/glossary/upstream_business_warehouse.md`); strip `派生自 ...` "
        "frontmatter / prose markers. Allow-list literals are in this script "
        "(`ALLOW_LITERAL_SUBSTRINGS`). Set MJ_AGENT_CHECK_REFS_STRICT=1 to "
        "fail-fast in CI (currently warning-mode; 4-week observation window).",
        file=sys.stderr,
    )
    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main())
