#!/usr/bin/env python3
"""Commit-message gate — validates a PR's own commits against the commit STANDARD.

Checks ``<type>(<scope>): <summary>`` headers of the commits a PR *adds*
(``<base>..<head>``, merge commits excluded) against
``docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md``.

Scope of this phase (#444): **type + scope only**. The §5.2 branch x type matrix,
and the §2.2 cosmetic rules that are independent of those two lists (one space
after ``:``, no trailing period, 72-char header), are deliberately NOT enforced
yet -- enforcing everything at once makes the warning output unreadable. The
parser is tolerant of them, so ``feat(skill):no-space`` is still judged on its
type and scope and never masquerades as an unparseable header.

**Letter case is the exception: it IS enforced, unavoidably.** The derived
type/scope sets are lowercase because the STANDARD's tables are, so
``Feat(agent)`` and ``feat(AGENT)`` fail membership and are reported (as
``unknown-type`` / ``unknown-scope``, with a hint naming the lowercase form).
That falls out of deriving rather than being a separate rule, and §2.2 lists
case first among its requirements -- so it is enforcement the STANDARD already
asked for, not scope creep. Do not describe this gate as "case not judged".

Known judged-surface boundaries, stated rather than silently absorbed:

- ``merge`` -- §3.1 defines it in the blockquote BELOW the type table, not in the
  table, so it is not in the derived type set. Real merge commits never reach the
  checker (``git log --no-merges``); only a hand-written ``merge:`` subject on a
  NON-merge commit would be flagged. Zero occurrences in 465 commits. Teaching
  the parser to read that blockquote means parsing prose, which is what design
  constraint 1 forbids -- if it ever bites, move ``merge`` into the §3.1 table.
- ``Revert "..."`` -- git's default revert subject does not match §2.1 and is
  reported as ``header-format``. Zero occurrences. The STANDARD is silent on
  reverts; granting the gate an exemption the STANDARD does not is the same
  copy-not-derive sin in reverse. Amend §3 if reverts should be exempt.
- **Partial** parse degradation -- the fail-closed guard fires on an EMPTY
  whitelist, so losing one of the four §4 scope tables would yield a truncated
  but non-empty one. What guards that is the real-tree pin in
  ``tests/unit/test_check_commit_messages.py`` (the blocking ``pytest tests/unit``
  step asserts exactly 35 scopes / 7 types / 23 aliases), backed by the derived
  counts this script prints on every run.

Design constraints (#444, all three derived from this repo's own incidents):

1. **Derived, never copied.** The scope whitelist, the type list and the
   historical-alias map are parsed out of the STANDARD's own tables at runtime.
   There is no scope literal anywhere in this file. Adding a scope to the
   STANDARD makes this gate accept it with no code change. Precedent: ADR-020
   moved ``check_wikilinks.py`` off hardcoded needles for the same reason;
   counter-example: #440 found ``check-stale-docs`` reciting a stale promise
   precisely because it was a *copy*.

   Tables are located by their **header row**, not by section number or title:
   a scope table is one whose first header cell is ``scope``; the alias table's
   is ``历史写法``; the type table's is ``类型``. That survives renumbering and
   re-titling, and it structurally excludes §4.6 (alias) from the whitelist --
   its left column holds *illegal* historical spellings.

2. **Fail-closed on unusable input -- but only for verdict inputs.** If the
   scope whitelist or the type list comes back empty (section renamed, table
   restructured, file moved), the gate exits ``2`` with a diagnostic. It never
   degrades into "empty whitelist -> everything is a violation" nor into
   "cannot parse -> pass". Precedent: #429, where ``check_frontmatter.py``
   defined "is canonical" as "has frontmatter" and silently dropped the files
   that needed checking most.

   The **diagnostic** layer (alias hints, type-as-scope hints) is explicitly
   best-effort: if §4.3 / §4.6 are reworded, hints degrade to the generic
   "not in the whitelist" message and the verdict is unchanged. Fail-closed
   protects what decides; it must not make prose edits break the gate.

3. **Registered at birth.** ``sdd/gates.md`` §2 row ``check-commit-messages``;
   posture ``warning@ci`` with a *registered* observation window aiming at a
   blocking flip (``plans/[PLAN]_m-fu-commit-message-gate-flip.md``, per
   ``policies/ci-gates.md`` §4.1.1). A flip is a separate Owner
   ``ci-blocking-gate-toggle`` decision.

Usage::

    python scripts/check_commit_messages.py [base_ref [head_ref]]
    python scripts/check_commit_messages.py --dry-run -n 100 origin/develop

- ``base_ref`` defaults to ``origin/develop``, ``head_ref`` to ``HEAD``
- ``--dry-run`` reports a baseline over the last ``-n`` non-merge commits
  reachable from a single ref and always exits 0 (it is a measuring tool, not
  the gate; CI never passes it)

Exit codes: ``0`` clean / ``1`` violations found / ``2`` the gate could not run
(fail-closed). Output: human-readable report on stdout, JSON summary on stderr
(same split as ``scripts/find_stale_docs.py``).

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

# Path constant, not a rule copy: the STANDARD is the single source of truth and
# this only says where it lives. NB the filename contains `[STANDARD]` -- never
# reach it with Path.glob(), which reads `[...]` as a character class.
STANDARD_REL = Path("docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md")

# Table identity = first header cell (see design constraint 1).
SCOPE_TABLE_HEADER = "scope"
TYPE_TABLE_HEADER = "类型"
ALIAS_TABLE_HEADER = "历史写法"

# Section numbers used only to narrow the search area; table headers do the
# actual selecting, so a renumber degrades to "table not found" -> fail-closed.
TYPE_SECTION = "3"
SCOPE_SECTION = "4"

HEADING_RE = re.compile(r"^(#{1,6})\s+(\S+)")
BACKTICK_RE = re.compile(r"`([^`]+)`")
SCOPE_TOKEN_RE = re.compile(r"[a-z][a-z0-9_-]*")
# Historical bad scopes may carry a dot (`phase-0.5`), so example extraction is
# laxer than the whitelist token shape.
EXAMPLE_TOKEN_RE = re.compile(r"[a-z][a-z0-9._-]*")

# `- **<bold lead>**...` bullets in §4 that state a "must not be used as scope"
# rule. The predicate deliberately excludes "一次 commit 只能有一个 scope"
# (no 作/作为), whose evidence parenthetical cites a commit SHA and a YAML key
# that would otherwise be mistaken for forbidden scope names.
BULLET_RE = re.compile(r"^\s*[-*]\s+\*\*(?P<lead>.+?)\*\*(?P<rest>.*)$")
FORBIDS_AS_SCOPE_RE = re.compile(r"作(?:为)?\s*scope")

# `type(scope): summary`. Case-tolerant and space-tolerant on purpose (see the
# phase note above); `(?:\([^()]*\))*` captures the illegal `type(a)(b):` form
# so it can be reported as such instead of as an unparseable header. `!` is the
# Conventional Commits 1.0.0 breaking-change marker -- the STANDARD §1 declares
# itself based on that spec, so accept it (zero occurrences in history so far).
HEADER_RE = re.compile(
    r"^(?P<type>[A-Za-z][A-Za-z0-9]*)"
    r"(?P<scopes>(?:\([^()]*\))*)"
    r"!?"
    r":\s*(?P<summary>.*)$"
)
SCOPE_GROUP_RE = re.compile(r"\(([^()]*)\)")
# All three git autosquash markers, including `amend!` (git >= 2.32, from
# `git commit --fixup=amend:<sha>`) -- the issue names fixup!/squash! but the
# class it means is "autosquash marker that must not survive to merge".
AUTOSQUASH_RE = re.compile(r"^(?P<kind>fixup|squash|amend)!\s")

GIT_RECORD_SEP = "\x1f"


class StandardParseError(RuntimeError):
    """The STANDARD could not be read, or yielded no verdict inputs."""


class GitRangeError(RuntimeError):
    """The requested commit range could not be resolved."""


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str

    @property
    def short(self) -> str:
        return self.sha[:8]


@dataclass(frozen=True)
class Finding:
    sha: str
    subject: str
    rule: str
    message: str


@dataclass(frozen=True)
class Rules:
    """Everything derived from the STANDARD, split by how failure is handled."""

    # Verdict inputs -- empty means fail-closed.
    scopes: frozenset[str]
    types: frozenset[str]
    # Diagnostic enrichment -- empty just means less helpful messages.
    aliases: Mapping[str, str]
    forbidden: Mapping[str, str]


# --------------------------------------------------------------------------
# STANDARD parsing
# --------------------------------------------------------------------------


def section_lines(text: str, number: str) -> list[str]:
    """Lines of the section headed ``<#...> <number> ...``, subsections included.

    Collection stops at the next heading of the same or shallower level, so
    ``section_lines(text, "4")`` spans §4 through §4.6 but not §5.
    """
    lines = text.splitlines()
    out: list[str] = []
    depth: int | None = None
    in_fence = False
    for line in lines:
        # Fence-aware: a `# ...` line inside a ``` block is content, not a heading.
        # The repo has hit this naive-scan bug before (#304, skill body_section_heads);
        # the STANDARD has no fenced headings today, so this is prophylactic.
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if depth is not None:
                out.append(line)
            continue
        m = None if in_fence else HEADING_RE.match(line)
        if m is None:
            if depth is not None:
                out.append(line)
            continue
        level = len(m.group(1))
        if depth is None:
            if m.group(2) == number:
                depth = level
            continue
        if level <= depth:
            break
        out.append(line)
    return out


def iter_tables(lines: Sequence[str]) -> list[list[list[str]]]:
    """Split lines into markdown tables; each table is a list of cell-rows.

    Row 0 is the header. The separator row (``|---|---|``) is dropped. A block
    of ``|``-prefixed lines only counts as a table when its second line is a
    separator, so pipe-leading prose cannot be mistaken for one.
    """
    tables: list[list[list[str]]] = []
    block: list[str] = []

    def flush() -> None:
        if len(block) >= 2 and _is_separator_row(block[1]):
            rows = [_split_row(block[0])]
            rows.extend(_split_row(line) for line in block[2:])
            tables.append(rows)
        block.clear()

    for line in lines:
        if line.lstrip().startswith("|"):
            block.append(line)
        else:
            flush()
    flush()
    return tables


def _split_row(line: str) -> list[str]:
    cells = line.strip().split("|")
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_separator_row(line: str) -> bool:
    cells = _split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def _header_is(table: Sequence[Sequence[str]], expected: str) -> bool:
    header = table[0] if table else []
    return bool(header) and header[0].strip("` ") == expected


def _first_backtick_token(cell: str, pattern: re.Pattern[str]) -> str | None:
    m = BACKTICK_RE.search(cell)
    if m is None:
        return None
    token = m.group(1).strip()
    return token if pattern.fullmatch(token) else None


def parse_scope_whitelist(text: str) -> frozenset[str]:
    """Scope whitelist = first column of every §4 table headed ``scope``."""
    scopes: set[str] = set()
    for table in iter_tables(section_lines(text, SCOPE_SECTION)):
        if not _header_is(table, SCOPE_TABLE_HEADER):
            continue
        for row in table[1:]:
            if not row:
                continue
            token = _first_backtick_token(row[0], SCOPE_TOKEN_RE)
            if token:
                scopes.add(token)
    return frozenset(scopes)


def parse_type_whitelist(text: str) -> frozenset[str]:
    """Type list = first column of every §3 table headed ``类型``."""
    types: set[str] = set()
    for table in iter_tables(section_lines(text, TYPE_SECTION)):
        if not _header_is(table, TYPE_TABLE_HEADER):
            continue
        for row in table[1:]:
            if not row:
                continue
            token = _first_backtick_token(row[0], SCOPE_TOKEN_RE)
            if token:
                types.add(token)
    return frozenset(types)


def parse_alias_map(text: str) -> dict[str, str]:
    """Historical alias -> formal scope text, from the §4 table headed ``历史写法``.

    Best-effort (diagnostic only). The left cell may list several aliases
    separated by ``、``; the right cell is kept as prose because one alias
    (``workflow``) legitimately maps to two scopes and another (``changelog``)
    maps to "omit the scope".
    """
    aliases: dict[str, str] = {}
    for table in iter_tables(section_lines(text, SCOPE_SECTION)):
        if not _header_is(table, ALIAS_TABLE_HEADER):
            continue
        for row in table[1:]:
            if len(row) < 2:
                continue
            formal = BACKTICK_RE.sub(r"\1", row[1]).replace("**", "").strip()
            for m in BACKTICK_RE.finditer(row[0]):
                token = m.group(1).strip()
                if EXAMPLE_TOKEN_RE.fullmatch(token) and formal:
                    aliases[token] = formal
    return aliases


def parse_forbidden_examples(text: str, whitelist: frozenset[str]) -> dict[str, str]:
    """Named-and-shamed scope spellings -> the §4.3 rule that forbids them.

    Best-effort (diagnostic only). Reads the bullets in §4 whose bold lead
    states a "must not be used as scope" rule and harvests their backticked
    examples. Whitelisted tokens are dropped, so ``infra`` -- a legal scope that
    is also a type -- can never be shamed by this map.
    """
    forbidden: dict[str, str] = {}
    for line in section_lines(text, SCOPE_SECTION):
        m = BULLET_RE.match(line)
        if m is None:
            continue
        lead = m.group("lead").strip()
        if not FORBIDS_AS_SCOPE_RE.search(lead):
            continue
        rule = BACKTICK_RE.sub(r"\1", lead).strip()
        for token_match in BACKTICK_RE.finditer(line):
            token = token_match.group(1).strip()
            if EXAMPLE_TOKEN_RE.fullmatch(token) and token not in whitelist:
                forbidden.setdefault(token, rule)
    return forbidden


def load_rules(repo_root: Path) -> Rules:
    """Parse the STANDARD into Rules, failing closed on unusable verdict inputs."""
    path = repo_root / STANDARD_REL
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StandardParseError(
            f"cannot read the commit STANDARD at {STANDARD_REL.as_posix()}: {exc}. "
            "The gate refuses to run without its source of truth "
            "(see the module docstring, design constraint 2)."
        ) from exc

    scopes = parse_scope_whitelist(text)
    if not scopes:
        raise StandardParseError(
            f"parsed 0 scopes from {STANDARD_REL.as_posix()} -- expected the §4 tables "
            f"whose first header cell is `{SCOPE_TABLE_HEADER}`. The section was probably "
            "renamed or the tables restructured; fix the parser alongside the STANDARD "
            "rather than letting the gate run on an empty whitelist."
        )
    types = parse_type_whitelist(text)
    if not types:
        raise StandardParseError(
            f"parsed 0 types from {STANDARD_REL.as_posix()} -- expected the §3 table "
            f"whose first header cell is `{TYPE_TABLE_HEADER}`. Same remedy as above."
        )
    return Rules(
        scopes=scopes,
        types=types,
        aliases=parse_alias_map(text),
        forbidden=parse_forbidden_examples(text, scopes),
    )


# --------------------------------------------------------------------------
# Commit collection
# --------------------------------------------------------------------------


def _git_log(repo_root: Path, args: Sequence[str]) -> list[Commit]:
    cmd = ["git", "log", "--no-merges", f"--format=%H{GIT_RECORD_SEP}%s", *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(repo_root), check=False
        )
    except OSError as exc:  # git missing / cwd unusable
        raise GitRangeError(f"could not run {' '.join(cmd)}: {exc}") from exc
    if proc.returncode != 0:
        raise GitRangeError(
            f"`{' '.join(cmd)}` failed (exit {proc.returncode}): "
            f"{proc.stderr.strip() or '<no stderr>'}"
        )
    commits: list[Commit] = []
    for line in proc.stdout.splitlines():
        sha, _, subject = line.partition(GIT_RECORD_SEP)
        if sha:
            commits.append(Commit(sha=sha, subject=subject))
    return commits


def collect_range(repo_root: Path, base_ref: str, head_ref: str) -> list[Commit]:
    """Non-merge commits the head adds on top of the base (``base..head``)."""
    return _git_log(repo_root, [f"{base_ref}..{head_ref}"])


def collect_recent(repo_root: Path, ref: str, limit: int) -> list[Commit]:
    """The most recent ``limit`` non-merge commits reachable from ``ref``."""
    return _git_log(repo_root, [f"-n{limit}", ref])


# --------------------------------------------------------------------------
# Checking
# --------------------------------------------------------------------------


def _unknown_scope_message(scope: str, rules: Rules) -> str:
    base = f"scope `{scope}` 不在 §4 的 {len(rules.scopes)} 项闭合白名单中"
    if scope in rules.forbidden:
        return f"{base} —— {rules.forbidden[scope]}（§4.3）"
    if scope in rules.aliases:
        return (
            f"{base} —— `{scope}` 是历史写法，正式 scope 为 {rules.aliases[scope]}（§4.6）；"
            "别名表仅供阅读历史，不放行新提交"
        )
    return f"{base}。改用白名单内的 scope，或在真正跨区域时省略 scope（§4.4）"


def check_commit(commit: Commit, rules: Rules) -> tuple[list[Finding], list[Finding]]:
    """Return ``(violations, warnings)`` for one commit subject."""
    violations: list[Finding] = []
    warnings: list[Finding] = []

    def add(bucket: list[Finding], rule: str, message: str) -> None:
        bucket.append(Finding(commit.sha, commit.subject, rule, message))

    autosquash = AUTOSQUASH_RE.match(commit.subject)
    if autosquash is not None:
        add(
            warnings,
            "autosquash-commit",
            f"`{autosquash.group('kind')}!` 提交不应存活到 merge —— "
            "合并前用 `git rebase --autosquash` 压平",
        )
        return violations, warnings

    header = HEADER_RE.match(commit.subject)
    if header is None:
        add(
            violations,
            "header-format",
            "header 不符合 `<type>(<scope>): <summary>`（§2.1）",
        )
        return violations, warnings

    commit_type = header.group("type")
    if commit_type not in rules.types:
        hint = ""
        if commit_type.lower() in rules.types:
            hint = f" —— type 必须小写，应为 `{commit_type.lower()}`（§2.2）"
        add(
            violations,
            "unknown-type",
            f"type `{commit_type}` 不在 §3 的 {len(rules.types)} 项列表中{hint}",
        )

    scopes = SCOPE_GROUP_RE.findall(header.group("scopes"))
    if len(scopes) > 1:
        rendered = "".join(f"({s})" for s in scopes)
        add(
            violations,
            "multiple-scopes",
            f"一次 commit 只能有一个 scope，`{rendered}` 是多括号形式（§4.3）",
        )
    elif len(scopes) == 1:
        scope = scopes[0].strip()
        if not scope:
            add(
                violations,
                "empty-scope",
                "scope 括号为空 —— 省略 scope 时不要写 `()`（§2.2 / §4.4）",
            )
        elif scope not in rules.scopes:
            add(violations, "unknown-scope", _unknown_scope_message(scope, rules))

    return violations, warnings


def check_commits(
    commits: Sequence[Commit], rules: Rules
) -> tuple[list[Finding], list[Finding]]:
    violations: list[Finding] = []
    warnings: list[Finding] = []
    for commit in commits:
        v, w = check_commit(commit, rules)
        violations.extend(v)
        warnings.extend(w)
    return violations, warnings


# --------------------------------------------------------------------------
# Reporting / CLI
# --------------------------------------------------------------------------


def _print_findings(commits: Sequence[Commit], findings: Sequence[Finding], marker: str) -> None:
    by_sha: dict[str, list[Finding]] = {}
    for f in findings:
        by_sha.setdefault(f.sha, []).append(f)
    for commit in commits:
        entries = by_sha.get(commit.sha)
        if not entries:
            continue
        print(f"  {commit.short}  {commit.subject}")
        for f in entries:
            print(f"    {marker} {f.rule}: {f.message}")


def _emit_json(
    stream: TextIO,
    *,
    checked: int,
    rules: Rules,
    violations: Sequence[Finding],
    warnings: Sequence[Finding],
) -> None:
    payload = {
        "checked": checked,
        "scopes": len(rules.scopes),
        "types": len(rules.types),
        "aliases": len(rules.aliases),
        "violations": len(violations),
        "warnings": len(warnings),
        "findings": [
            {"sha": f.sha, "subject": f.subject, "rule": f.rule, "message": f.message}
            for f in [*violations, *warnings]
        ],
    }
    print(json.dumps(payload, ensure_ascii=False), file=stream)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate commit-message headers against "
            "docs/rule/[STANDARD]_MJ_Agent_Commit_Message_Convention.md"
        )
    )
    parser.add_argument(
        "base_ref",
        nargs="?",
        default="origin/develop",
        help="base ref (default: origin/develop); with --dry-run this is the single ref to walk",
    )
    parser.add_argument("head_ref", nargs="?", default="HEAD", help="head ref (default: HEAD)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "baseline mode: walk the last -n non-merge commits of base_ref and always exit 0. "
            "A measuring tool, not the gate -- CI never passes this."
        ),
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=100,
        help="number of commits to walk in --dry-run mode (default: 100)",
    )
    return parser


def run(argv: Sequence[str] | None = None, repo_root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root if repo_root is not None else Path(__file__).resolve().parent.parent

    try:
        rules = load_rules(root)
    except StandardParseError as exc:
        print(f"GATE ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        if args.dry_run:
            commits = collect_recent(root, args.base_ref, args.limit)
            rev_label = f"{args.base_ref} (last {args.limit} non-merge)"
        else:
            commits = collect_range(root, args.base_ref, args.head_ref)
            rev_label = f"{args.base_ref}..{args.head_ref}"
    except GitRangeError as exc:
        # Fail CLOSED: an unresolvable range must not read as "nothing wrong".
        print(f"GATE ERROR: {exc}", file=sys.stderr)
        return 2

    print("== mj-agent commit message gate ==")
    print(f"Standard: {STANDARD_REL.as_posix()}")
    print(
        f"Derived:  {len(rules.scopes)} scopes / {len(rules.types)} types / "
        f"{len(rules.aliases)} aliases / {len(rules.forbidden)} named-bad examples"
    )
    print(f"Range:    {rev_label} -> {len(commits)} commit(s)")
    if args.dry_run:
        print("Mode:     DRY-RUN (baseline; exit code suppressed)")
    print()

    if not commits:
        # The range RESOLVED and is empty -- that is valid input, not a failure
        # to read input, so it is not the fail-closed case.
        print("NOTE: 0 non-merge commits in range — nothing to check.")
        _emit_json(sys.stderr, checked=0, rules=rules, violations=[], warnings=[])
        return 0

    violations, warnings = check_commits(commits, rules)
    _emit_json(sys.stderr, checked=len(commits), rules=rules, violations=violations, warnings=warnings)

    if violations:
        print(f"FAIL: {len(violations)} violation(s) across {len(commits)} commit(s)")
        _print_findings(commits, violations, "x")
        print()
    if warnings:
        print(f"WARN: {len(warnings)} warning(s) (counted separately from violations)")
        _print_findings(commits, warnings, "!")
        print()
    if not violations and not warnings:
        print(f"OK: {len(commits)} commit(s) conform to the STANDARD")
        return 0
    if not violations:
        print(f"OK: {len(commits)} commit(s) conform on type/scope; see warnings above")
        return 0

    print(f"Fix: rewrite the offending messages (`git rebase -i {args.base_ref}` on your branch),")
    print("     or amend the STANDARD if the scope is genuinely missing — §4.5 assigns that")
    print(f"     to the PR introducing the area. Full rules: {STANDARD_REL.as_posix()}")
    return 0 if args.dry_run else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
