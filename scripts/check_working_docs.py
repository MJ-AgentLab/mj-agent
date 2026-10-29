#!/usr/bin/env python3
"""Validate new task folders and their actual document-relative links.

Legacy root files remain readable in place. This checks structure, not the
existence/primacy of a GitHub association, source fidelity, or Owner acceptance.
Those decisions require the real task record and platform evidence.
"""
from __future__ import annotations

import argparse
import re
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_wikilinks import scan_links  # noqa: E402

TOPIC_RE = re.compile(
    r"(?:I[1-9][0-9]*-(?:P[1-9][0-9]*-)?|P[1-9][0-9]*-)?"
    r"[a-z0-9]+(?:-[a-z0-9]+)*\Z"
)
MAX_DEPTH = 8
MAX_DOCUMENTS = 4096
MAX_DOCUMENT_BYTES = 1024 * 1024


def valid_topic(topic: str) -> bool:
    """Recognize four topic forms; a number in a slug is never inferred as an ID."""
    return TOPIC_RE.fullmatch(topic) is not None


def _no_reparse(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        raise ValueError(f"symlink/reparse path rejected: {path.name}")


def _documents(directory: Path, depth: int = 0) -> list[Path]:
    """Read a bounded tree without traversing links or ignoring unreadable entries."""
    _no_reparse(directory)
    if depth > MAX_DEPTH:
        raise ValueError(f"working document nesting exceeds {MAX_DEPTH}")
    result: list[Path] = []
    for entry in sorted(directory.iterdir()):
        _no_reparse(entry)
        if entry.is_dir():
            result.extend(_documents(entry, depth + 1))
        elif entry.suffix == ".md" and entry.is_file():
            if entry.stat().st_size > MAX_DOCUMENT_BYTES:
                raise ValueError(f"working document exceeds size limit: {entry.name}")
            result.append(entry)
        if len(result) > MAX_DOCUMENTS:
            raise ValueError("too many working documents in one task directory")
    return result


def _association_problems(topic: str, text: str) -> list[str]:
    """Reject contradictions with an explicitly labelled primary link, without guessing."""
    problems: list[str] = []
    for tag, label, endpoint in (("I", "Issue", "issues"), ("P", "PR", "pull")):
        segment = re.search(rf"(?:^|-){tag}([1-9][0-9]*)(?:-|$)", topic)
        if segment is None:
            continue
        for line in text.splitlines():
            if not re.search(rf"(?:主要\s*{label}|Primary\s+{label})\s*[:：]", line, re.IGNORECASE):
                continue
            links = re.findall(rf"https://github\.com/MJ-AgentLab/mj-agent/{endpoint}/([1-9][0-9]*)(?![0-9])", line)
            any_links = re.findall(rf"https://github\.com/[^/\s]+/[^/\s]+/{endpoint}/[1-9][0-9]*", line)
            if any_links and not links:
                problems.append(f"primary {label} must refer to this repository")
            if links and set(links) != {segment[1]}:
                problems.append(f"topic {tag}{segment[1]} contradicts explicitly declared primary {label} link")
    return problems


def check(repo_root: Path) -> dict[Path, list[str]]:
    """Return layout/link violations for task folders, leaving legacy root files alone."""
    bad: dict[Path, list[str]] = {}
    plans = repo_root / "plans"
    if not plans.exists() and not plans.is_symlink():
        return bad
    try:
        _no_reparse(plans)
        directories = []
        for entry in sorted(plans.iterdir()):
            _no_reparse(entry)
            if entry.is_dir():
                directories.append(entry)
    except (OSError, ValueError) as exc:
        return {Path("plans"): [f"working collection failed: {exc}"]}
    for directory in directories:
        rel_dir = directory.relative_to(repo_root)
        if not valid_topic(directory.name):
            bad.setdefault(rel_dir, []).append("invalid task topic; expected optional uppercase I/P numbers and lowercase slug")
        try:
            documents = _documents(directory)
            main_plans = [doc for doc in documents if doc.name.startswith("[PLAN]")]
            if len(main_plans) > 1:
                bad.setdefault(rel_dir, []).append("a task directory may contain only one main Plan; child Plans need their own task directory")
            for document in main_plans:
                if document.parent != directory or document.name != f"[PLAN]_{directory.name}.md":
                    bad.setdefault(document.relative_to(repo_root), []).append("main Plan topic and location must exactly match its task directory")
            for document in documents:
                rel = document.relative_to(repo_root)
                text = document.read_text(encoding="utf-8")
                for _, lineno, kind, target in scan_links(repo_root, rel, text):
                    bad.setdefault(rel, []).append(f"line {lineno}: unresolved {kind} link -> {target}")
                if document in main_plans:
                    bad.setdefault(rel, []).extend(_association_problems(directory.name, text))
                    if not bad[rel]:
                        del bad[rel]
        except (OSError, UnicodeError, ValueError) as exc:
            bad.setdefault(rel_dir, []).append(f"working collection failed: {exc}")
    return bad


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    root = repo_root if repo_root is not None else Path(__file__).resolve().parent.parent
    bad = check(root)
    for rel, problems in sorted(bad.items()):
        for problem in problems:
            print(f"{rel.as_posix()}: {problem}", file=sys.stderr)
    if bad:
        print(f"FAIL: {len(bad)} working document paths have violations", file=sys.stderr)
        return 1
    print("OK: working task folders and document-relative links; legacy root files retained")
    print("Structure only: real primary associations, source fidelity and Owner acceptance require task evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
